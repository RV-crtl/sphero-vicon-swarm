from __future__ import annotations

import subprocess
import sys
from pathlib import Path


GENERATED = [
    Path("artifacts/logs/release_check.csv"),
    Path("reference_controllers/three_chariot_square_ilc_reference.json"),
    Path("reference_controllers/three_chariot_swarm_learning_reference.json"),
    Path("reference_controllers/three_chariot_vicon_heading_calibration_reference.json"),
]

COMMANDS = [
    [sys.executable, "-m", "compileall", "-q", "src", "examples"],
    [sys.executable, "-m", "pytest", "-q"],
    [sys.executable, "tools/privacy_scan.py", "."],
    [
        sys.executable,
        "reference_controllers/three_chariot_square_swarm.py",
        "--dry-run",
        "--timeout",
        "1",
        "--no-digital-twin",
        "--log",
        "artifacts/logs/release_check.csv",
    ],
]


def cleanup() -> None:
    for path in GENERATED:
        path.unlink(missing_ok=True)


def main() -> int:
    cleanup()
    try:
        for command in COMMANDS:
            print("+", " ".join(command), flush=True)
            completed = subprocess.run(command, check=False)
            if completed.returncode:
                print(f"FAILED with exit code {completed.returncode}")
                return completed.returncode
        print("All release checks passed.")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
