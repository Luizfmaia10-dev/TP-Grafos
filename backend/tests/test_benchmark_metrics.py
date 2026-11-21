"""Portable process monitoring contracts, validated locally without OS simulation."""
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from benchmarks import metrics


def test_memory_snapshot_uses_rss_bytes(monkeypatch):
    process = Mock()
    process.memory_info.return_value = SimpleNamespace(rss=123456)
    monkeypatch.setattr(metrics.psutil, 'Process', lambda: process)
    assert metrics.memory() == {'rss_bytes': 123456}


def test_monitor_records_sampled_peak(monkeypatch):
    child = Mock(pid=123)
    child.poll.side_effect = [None, None, 0]
    probe = Mock()
    probe.children.return_value = []
    probe.memory_info.side_effect = [SimpleNamespace(rss=100), SimpleNamespace(rss=300)]
    monkeypatch.setattr(metrics.psutil, 'Process', lambda pid: probe)
    monkeypatch.setattr(metrics, 'sleep', lambda duration: None)
    peak, count = metrics.monitor(child, timeout=10, sample_memory=True)
    assert (peak, count) == (300, 2)


def test_monitor_allows_process_exit_during_sampling(monkeypatch):
    child = Mock(pid=123)
    child.poll.side_effect = [None, 0]
    probe = Mock()
    probe.children.return_value = []
    probe.memory_info.side_effect = metrics.psutil.NoSuchProcess(123)
    monkeypatch.setattr(metrics.psutil, 'Process', lambda pid: probe)
    monkeypatch.setattr(metrics, 'sleep', lambda duration: None)
    assert metrics.monitor(child, timeout=10, sample_memory=True) == (None, 0)


def test_timing_process_is_not_sampled_without_limit(monkeypatch):
    child = Mock()
    forbidden = Mock(side_effect=AssertionError('Timing worker must not be sampled'))
    monkeypatch.setattr(metrics.psutil, 'Process', forbidden)
    assert metrics.monitor(child, timeout=10, sample_memory=False) == (None, 0)
    child.wait.assert_called_once_with(timeout=10)


def test_execute_process_handles_spaces_unicode_and_large_output(tmp_path):
    directory = tmp_path / 'path with spaces á'
    directory.mkdir()
    process, peak, count = metrics.execute_process(
        [sys.executable, '-c',
         'import sys,time; data=sys.stdin.read(); print(data); print("x"*200000); time.sleep(.05)'],
        input='{"name":"estação"}', cwd=directory, timeout=10, sample_memory=True,
    )
    assert process.returncode == 0
    assert 'estação' in process.stdout
    assert len(process.stdout) > 200000
    assert peak > 0 and count > 0


@pytest.mark.parametrize('failure', ['timeout', 'memory'])
def test_failed_process_is_killed_and_reaped(tmp_path, monkeypatch, failure):
    created = []
    original = metrics.subprocess.Popen
    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        created.append(child)
        return child
    monkeypatch.setattr(metrics.subprocess, 'Popen', capture)
    expected = subprocess.TimeoutExpired if failure == 'timeout' else metrics.MemoryLimitExceeded
    with pytest.raises(expected):
        metrics.execute_process(
            [sys.executable, '-c', 'import time; time.sleep(30)'], input='{}',
            cwd=tmp_path, timeout=.1 if failure == 'timeout' else 10,
            memory_limit_bytes=1 if failure == 'memory' else None,
            sample_memory=True,
        )
    assert len(created) == 1
    assert created[0].poll() is not None


def test_monitor_counts_each_descendant_once(monkeypatch):
    child = Mock(pid=123)
    child.poll.side_effect = [None, 0]
    launcher = Mock(pid=123)
    launcher.memory_info.return_value = SimpleNamespace(rss=100)
    worker = Mock(pid=456)
    worker.memory_info.return_value = SimpleNamespace(rss=300)
    launcher.children.return_value = [worker, worker]
    monkeypatch.setattr(metrics.psutil, 'Process', lambda pid: launcher)
    monkeypatch.setattr(metrics, 'sleep', lambda duration: None)
    assert metrics.monitor(child, timeout=10, sample_memory=True) == (400, 1)


@pytest.mark.parametrize('failure', ['timeout', 'memory'])
def test_limits_terminate_the_actual_worker_below_a_launcher(tmp_path, failure):
    pid_file = tmp_path / 'worker.pid'
    child_code = ('import os,pathlib,time; '
                  f'pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())); '
                  'payload=bytearray(64*1024*1024); time.sleep(10)')
    wrapper = ('import subprocess,sys; '
               f'subprocess.run([sys.executable,"-c",{child_code!r}])')
    expected = subprocess.TimeoutExpired if failure == 'timeout' else metrics.MemoryLimitExceeded
    pid = None
    try:
        with pytest.raises(expected) as captured:
            metrics.execute_process(
                [sys.executable, '-c', wrapper], input='{}', cwd=tmp_path,
                timeout=1 if failure == 'timeout' else 5, sample_memory=True,
                memory_limit_bytes=64*1024*1024 if failure == 'memory' else None)
        assert pid_file.exists(), 'The actual worker must start before the limit is exercised'
        pid = int(pid_file.read_text())
        assert not metrics.psutil.pid_exists(pid)
        assert captured.value.sampled_peak_rss_bytes > 64*1024*1024
    finally:
        if pid is None and pid_file.exists():
            pid = int(pid_file.read_text())
        if pid is not None and metrics.psutil.pid_exists(pid):
            metrics.psutil.Process(pid).kill()
            metrics.psutil.wait_procs([metrics.psutil.Process(pid)], timeout=2)
