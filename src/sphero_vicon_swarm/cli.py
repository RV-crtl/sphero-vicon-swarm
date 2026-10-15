from __future__ import annotations

import argparse
import time
from .config import load_config
from .diagnostics import doctor
from .simulation import default_three_robot_simulation


def cmd_validate_config(path: str) -> int:
    cfg = load_config(path, allow_placeholders=True)
    print(f"Configuration parsed: {len(cfg.robots)} robot(s), Vicon plane {cfg.vicon.floor_plane}.")
    if any(robot.sphero_name.startswith("YOUR_") for robot in cfg.robots):
        print("Placeholders are present; replace them before hardware use.")
    return 0


def cmd_simulate(seconds: float) -> int:
    robots = default_three_robot_simulation()
    dt = 0.02
    print("Running hardware-free robot-motion smoke simulation...")
    for index, robot in enumerate(robots):
        robot.command(20.0 + index * 70.0, 150)
    start = time.monotonic()
    next_print = start
    while time.monotonic() - start < seconds:
        for robot in robots:
            robot.step(dt)
        now = time.monotonic()
        if now >= next_print:
            print(" | ".join(f"{r.label}: ({r.x_mm:7.1f},{r.y_mm:7.1f}) yaw={r.yaw_deg:6.1f}" for r in robots))
            next_print = now + 0.5
        time.sleep(dt)
    for robot in robots:
        robot.stop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sphero-vicon", description="Sphero + Vicon swarm utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="report optional hardware backends and local environment")
    validate = sub.add_parser("validate-config", help="parse and sanity-check a TOML configuration")
    validate.add_argument("--config", default="config/robot_setup.toml")
    simulate = sub.add_parser("simulate", help="run a hardware-free motion smoke simulation")
    simulate.add_argument("--seconds", type=float, default=5.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "doctor":
        return doctor()
    if args.command == "validate-config":
        return cmd_validate_config(args.config)
    if args.command == "simulate":
        return cmd_simulate(max(0.1, args.seconds))
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
