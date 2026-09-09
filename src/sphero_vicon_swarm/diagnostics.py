from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path


def doctor() -> int:
    print("Sphero + Vicon environment doctor")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Working directory: {Path.cwd()}")
    for module, purpose in [
        ("spherov2", "public Sphero BLE backend"),
        ("vicon_dssdk", "Vicon DataStream SDK bindings"),
    ]:
        present = importlib.util.find_spec(module) is not None
        print(f"{module:14s}: {'FOUND' if present else 'not installed'} ({purpose})")
    print("Hardware-free simulation and unit tests do not require either optional backend.")
    return 0
