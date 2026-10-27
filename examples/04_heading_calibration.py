from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sphero_vicon_swarm.calibration import HeadingBasis
from sphero_vicon_swarm.config import load_config
from sphero_vicon_swarm.drivers.spherov2_driver import SpheroV2Driver
from sphero_vicon_swarm.models import Pose2D, RobotSpec
from sphero_vicon_swarm.tracking.vicon import ViconTracker


def visible_pose(tracker: ViconTracker, label: str) -> Pose2D:
    pose = tracker.read_all()[label]
    if pose.occluded:
        raise RuntimeError(
            f"{label} is occluded in Vicon. Restore reliable tracking before calibration."
        )
    return pose


def measure(
    driver: SpheroV2Driver,
    tracker: ViconTracker,
    heading: float,
    speed: int,
    seconds: float,
    label: str,
) -> tuple[float, float]:
    start = visible_pose(tracker, label)
    driver.command(heading, speed)
    try:
        time.sleep(seconds)
    finally:
        driver.stop()
    time.sleep(0.35)
    end = visible_pose(tracker, label)
    return end.x_mm - start.x_mm, end.y_mm - start.y_mm


def calibrate_robot(
    spec: RobotSpec,
    *,
    vicon_config,
    speed: int,
    seconds: float,
) -> dict[str, object]:
    driver = SpheroV2Driver.connect(spec.sphero_name)
    try:
        with ViconTracker(vicon_config, [spec]) as tracker:
            print(f"\n[{spec.label}] Verify the physical chariot has clear space.")
            dx0, dy0 = measure(driver, tracker, 0.0, speed, seconds, spec.label)
            dx90, dy90 = measure(driver, tracker, 90.0, speed, seconds, spec.label)
            basis = HeadingBasis.from_displacements(dx0, dy0, dx90, dy90)
            world_x_heading = basis.world_vector_to_heading(1.0, 0.0)
            world_y_heading = basis.world_vector_to_heading(0.0, 1.0)

            print(f"  heading 0 displacement : ({dx0:.1f}, {dy0:.1f}) mm")
            print(f"  heading 90 displacement: ({dx90:.1f}, {dy90:.1f}) mm")
            print(
                "  basis: "
                f"e0=({basis.e0_x:.4f},{basis.e0_y:.4f}) "
                f"e90=({basis.e90_x:.4f},{basis.e90_y:.4f})"
            )
            print(f"  Vicon +X -> Sphero heading {world_x_heading:.1f} deg")
            print(f"  Vicon +Y -> Sphero heading {world_y_heading:.1f} deg")

            return {
                "label": spec.label,
                "sphero_name": spec.sphero_name,
                "vicon_subject": spec.vicon_subject,
                "vicon_segment": spec.vicon_segment,
                "heading_0_displacement_mm": [dx0, dy0],
                "heading_90_displacement_mm": [dx90, dy90],
                "basis": {
                    "e0_x": basis.e0_x,
                    "e0_y": basis.e0_y,
                    "e90_x": basis.e90_x,
                    "e90_y": basis.e90_y,
                },
                "vicon_plus_x_sphero_heading_deg": world_x_heading,
                "vicon_plus_y_sphero_heading_deg": world_y_heading,
            }
    finally:
        driver.close()


def select_robots(configured: tuple[RobotSpec, ...], labels: list[str]) -> list[RobotSpec]:
    if not labels:
        return list(configured)
    by_label = {robot.label: robot for robot in configured}
    missing = [label for label in labels if label not in by_label]
    if missing:
        known = ", ".join(sorted(by_label))
        raise ValueError(f"Unknown robot label(s): {', '.join(missing)}. Known labels: {known}")
    return [by_label[label] for label in labels]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Measure the Sphero-heading to Vicon-world mapping for one or more configured robots. "
            "Robots are calibrated sequentially so only one chariot moves at a time."
        )
    )
    parser.add_argument("--config", default="config/robot_setup.toml")
    parser.add_argument(
        "--robot",
        action="append",
        default=[],
        help="robot label to calibrate; repeat for multiple robots; default: all configured robots",
    )
    parser.add_argument("--speed", type=int, default=90)
    parser.add_argument("--seconds", type=float, default=0.8)
    parser.add_argument(
        "--output",
        default="artifacts/heading_calibration.json",
        help="JSON file for measured calibration results",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="do not pause for operator confirmation before each robot",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    robots = select_robots(cfg.robots, args.robot)
    speed = max(1, min(255, args.speed))
    seconds = max(0.2, min(5.0, args.seconds))

    print("Per-robot Vicon displacement calibration")
    print(f"Configured robots: {', '.join(robot.label for robot in robots)}")
    print(f"Motion command: speed={speed}, duration={seconds:.2f} s per axis")
    print("Only one robot moves at a time. Keep the operating area clear and keep Ctrl+C available.")

    results: dict[str, object] = {
        "config": str(Path(args.config)),
        "speed_cmd": speed,
        "seconds_per_axis": seconds,
        "robots": {},
    }

    for index, spec in enumerate(robots, start=1):
        if not args.no_prompt:
            input(
                f"\n[{index}/{len(robots)}] Place {spec.label} with clear space for two short moves, "
                "confirm its Vicon object is visible, then press Enter..."
            )
        result = calibrate_robot(
            spec,
            vicon_config=cfg.vicon,
            speed=speed,
            seconds=seconds,
        )
        robots_result = results["robots"]
        assert isinstance(robots_result, dict)
        robots_result[spec.label] = result

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nCalibration complete for {len(robots)} robot(s).")
    print(f"Saved measured results to: {output.resolve()}")
    print(
        "These measurements are diagnostic/reference data. "
        "The feature-rich three-chariot controller performs its own startup calibration."
    )


if __name__ == "__main__":
    main()
