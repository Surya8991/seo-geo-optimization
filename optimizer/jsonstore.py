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


@contextlib.contextmanager
def locked(path, timeout=10, poll=0.05):
    lock_path = path + ".lock"
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise LockTimeout(
                    f"Could not acquire {lock_path} within {timeout}s. If no other "
                    "ledger/verify command is actually running, delete the .lock file."
                )
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
