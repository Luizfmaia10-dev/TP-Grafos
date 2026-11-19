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
    """Return the observed RSS maximum and sample count, never an OS peak."""
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
            raise subprocess.TimeoutExpired(process.args, timeout)
        try:
            rss = probe.memory_info().rss
        except psutil.NoSuchProcess:
            break
        peak = rss if peak is None else max(peak, rss)
        count += 1
        if memory_limit_bytes is not None and rss > memory_limit_bytes:
            raise MemoryLimitExceeded(
                f'Worker sampled RSS {rss} bytes exceeds limit {memory_limit_bytes} bytes')
        sleep(min(SAMPLE_INTERVAL_SECONDS, max(0, deadline - monotonic())))
    process.wait(timeout=max(0, deadline - monotonic()))
    return peak, count


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
            if process.poll() is None:
                process.kill()
            process.wait()
        output.seek(0)
        errors.seek(0)
        completed = subprocess.CompletedProcess(
            command, process.returncode, output.read(), errors.read())
        return completed, peak, count
