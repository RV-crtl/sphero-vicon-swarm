from __future__ import annotations

import argparse
import time

from sphero_vicon_swarm.config import load_config
from sphero_vicon_swarm.tracking.vicon import ViconTracker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/robot_setup.toml")
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    cfg = load_config(args.config)

    with ViconTracker(cfg.vicon, cfg.robots) as tracker:
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            poses = tracker.read_all()
            print(" | ".join(
                f"{label}: ({pose.x_mm:8.1f},{pose.y_mm:8.1f}) yaw={pose.yaw_deg:6.1f} occ={pose.occluded}"
                for label, pose in poses.items()
            ))
            time.sleep(0.1)


if __name__ == "__main__":
    main()
