from __future__ import annotations

import argparse
import time

from sphero_vicon_swarm.config import load_config
from sphero_vicon_swarm.drivers.spherov2_driver import SpheroV2Driver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/robot_setup.toml")
    parser.add_argument("--speed", type=int, default=70)
    parser.add_argument("--seconds", type=float, default=0.7)
    args = parser.parse_args()

    cfg = load_config(args.config)
    robot = cfg.robots[0]
    driver = SpheroV2Driver.connect(robot.sphero_name)
    try:
        print(f"Connected {robot.label}. Commanding a short forward motion.")
        driver.command(0.0, max(0, min(100, args.speed)))
        time.sleep(max(0.1, min(1.5, args.seconds)))
    finally:
        driver.close()


if __name__ == "__main__":
    main()
