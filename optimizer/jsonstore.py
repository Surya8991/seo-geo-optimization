#!/usr/bin/env python3
"""
Tiny cross-platform file lock for the append-only JSON logs (ledger.py, verify.py).

Each CLI invocation does load -> mutate -> save. Without a lock, two concurrent
invocations (two terminals, or an automated caller) can race: both load the same
old state, and whichever saves last silently overwrites the other's entry with no
error. The lock file is created with O_CREAT|O_EXCL, which is atomic on both
Windows and POSIX, so only one process holds it at a time.
"""
import contextlib
import os
import time


class LockTimeout(RuntimeError):
    pass


STALE_LOCK_SECONDS = 60


def _break_if_stale(lock_path):
    """A hard-killed process leaves its lock behind forever; a lock this old cannot
    belong to a live add (each holds it for milliseconds), so remove it."""
    try:
        if time.time() - os.path.getmtime(lock_path) > STALE_LOCK_SECONDS:
            os.remove(lock_path)
    except OSError:
        pass


@contextlib.contextmanager
def locked(path, timeout=10, poll=0.05):
    lock_path = path + ".lock"
    # data/ may not exist yet on the first add (save() creates it, but only after the lock).
    os.makedirs(os.path.dirname(os.path.abspath(lock_path)), exist_ok=True)
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            _break_if_stale(lock_path)
            if time.time() > deadline:
                raise LockTimeout(
                    f"Could not acquire {lock_path} within {timeout}s. If no other "
                    "ledger/verify command is actually running, delete the .lock file."
                ) from None
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
