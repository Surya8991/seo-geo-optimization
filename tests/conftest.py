"""Put optimizer/ on sys.path so tests can import the modules the same way the
scripts do when run as `python optimizer/<script>.py`.

Also pin the config to a fixed test fixture via SEO_GEO_CONFIG, so the suite is
deterministic regardless of which brand the project-root config.json currently holds.
This must run before any module imports config_loader (conftest loads first)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIMIZER = os.path.join(ROOT, "optimizer")

os.environ["SEO_GEO_CONFIG"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "config.test.json")

for p in (OPTIMIZER, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
