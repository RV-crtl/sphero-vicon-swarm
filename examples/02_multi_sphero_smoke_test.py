from __future__ import annotations

import argparse
import time

from sphero_vicon_swarm.config import load_config
from sphero_vicon_swarm.drivers.spherov2_driver import SpheroV2Driver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/robot_setup.toml")
    args = parser.parse_args()
    cfg = load_config(args.config)

    drivers: list[SpheroV2Driver] = []
    try:
        for spec in cfg.robots:
            print(f"Connecting {spec.label}...")
            drivers.append(SpheroV2Driver.connect(spec.sphero_name))
        print(f"Connected {len(drivers)} robots. Sending zero-speed heading-identification commands only.")
        for index, driver in enumerate(drivers):
            driver.command(index * 90.0, 0)
            time.sleep(0.2)
    finally:
        for driver in reversed(drivers):
            driver.close()


if __name__ == "__main__":
    main()
