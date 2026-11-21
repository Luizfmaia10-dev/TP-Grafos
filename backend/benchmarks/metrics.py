"""Portable RSS snapshots and external worker monitoring."""
import os
import subprocess
from tempfile import TemporaryFile
from time import monotonic, sleep

import psutil

SAMPLE_INTERVAL_SECONDS = 0.01


class MemoryLimitExceeded(RuntimeError):
    """A sampled worker RSS exceeded the configured byte limit."""


def memory():
    """Current process resident memory, in bytes, on Linux, Windows and macOS."""
    return {'rss_bytes': psutil.Process().memory_info().rss}


def monitor(process, *, timeout, sample_memory, memory_limit_bytes=None):
    """Sample aggregate RSS of unique process IDs, including launcher descendants."""
    if not sample_memory and memory_limit_bytes is None:
        process.wait(timeout=timeout)
        return None, 0
    deadline = monotonic() + timeout
    peak, count = None, 0
    try:
        probe = psutil.Process(process.pid)
    except psutil.NoSuchProcess:
        process.wait(timeout=timeout)
        return peak, count
    while process.poll() is None:
        if monotonic() >= deadline:
            error = subprocess.TimeoutExpired(process.args, timeout)
            error.sampled_peak_rss_bytes, error.memory_sample_count = peak, count
            raise error
        try:
            targets = {item.pid: item for item in [probe, *probe.children(recursive=True)]}
        except psutil.NoSuchProcess:
            break
        rss = None
        for target in targets.values():
            try:
                value = target.memory_info().rss
            except psutil.NoSuchProcess:
                continue
            rss = value if rss is None else rss + value
        if rss is None:
            break
        peak = rss if peak is None else max(peak, rss)
        count += 1
        if memory_limit_bytes is not None and rss > memory_limit_bytes:
            error = MemoryLimitExceeded(
                f'Worker sampled RSS {rss} bytes exceeds limit {memory_limit_bytes} bytes')
            error.sampled_peak_rss_bytes, error.memory_sample_count = peak, count
            raise error
        sleep(min(SAMPLE_INTERVAL_SECONDS, max(0, deadline - monotonic())))
    process.wait(timeout=max(0, deadline - monotonic()))
    return peak, count


def stop_process_tree(process):
    """Stop descendants first so waiting launchers can reap them before parent cleanup."""
    try:
        children = psutil.Process(process.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    for child in reversed(children):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    if children:
        psutil.wait_procs(children, timeout=1)
    if process.poll() is None:
        process.kill()
    process.wait()


def execute_process(command, *, input, cwd, timeout, sample_memory,
                    memory_limit_bytes=None):
    """Use temporary streams to avoid pipe deadlocks while monitoring a worker."""
    with (TemporaryFile(mode='w+', encoding='utf-8') as source,
          TemporaryFile(mode='w+', encoding='utf-8') as output,
          TemporaryFile(mode='w+', encoding='utf-8') as errors):
        source.write(input)
        source.seek(0)
        process = subprocess.Popen(
            command, stdin=source, stdout=output, stderr=errors, cwd=cwd,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        )
        try:
            peak, count = monitor(process, timeout=timeout, sample_memory=sample_memory,
                                  memory_limit_bytes=memory_limit_bytes)
        finally:
            stop_process_tree(process)
        output.seek(0)
        errors.seek(0)
        completed = subprocess.CompletedProcess(
            command, process.returncode, output.read(), errors.read())
        return completed, peak, count
