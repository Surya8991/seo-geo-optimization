"""Put optimizer/ on sys.path so tests can import the modules the same way the
scripts do when run as `python optimizer/<script>.py`."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIMIZER = os.path.join(ROOT, "optimizer")
for p in (OPTIMIZER, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
