from __future__ import annotations

import argparse
import time

from sphero_vicon_swarm.calibration import HeadingBasis
from sphero_vicon_swarm.config import load_config
from sphero_vicon_swarm.drivers.spherov2_driver import SpheroV2Driver
from sphero_vicon_swarm.tracking.vicon import ViconTracker


def measure(driver: SpheroV2Driver, tracker: ViconTracker, heading: float, speed: int, seconds: float, label: str) -> tuple[float, float]:
    start = tracker.read_all()[label]
    driver.command(heading, speed)
    time.sleep(seconds)
    driver.stop()
    time.sleep(0.35)
    end = tracker.read_all()[label]
    return end.x_mm - start.x_mm, end.y_mm - start.y_mm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/robot_setup.toml")
    parser.add_argument("--speed", type=int, default=90)
    parser.add_argument("--seconds", type=float, default=0.8)
    args = parser.parse_args()
    cfg = load_config(args.config)
    spec = cfg.robots[0]
    driver = SpheroV2Driver.connect(spec.sphero_name)
    try:
        with ViconTracker(cfg.vicon, [spec]) as tracker:
            print("Ensure the robot has clear space for two short calibration moves.")
            dx0, dy0 = measure(driver, tracker, 0.0, args.speed, args.seconds, spec.label)
            dx90, dy90 = measure(driver, tracker, 90.0, args.speed, args.seconds, spec.label)
            basis = HeadingBasis.from_displacements(dx0, dy0, dx90, dy90)
            print(f"heading 0 displacement : ({dx0:.1f}, {dy0:.1f}) mm")
            print(f"heading 90 displacement: ({dx90:.1f}, {dy90:.1f}) mm")
            print(f"calibrated basis: {basis}")
            print(f"Vicon +X corresponds to Sphero heading {basis.world_vector_to_heading(1.0, 0.0):.1f}°")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
