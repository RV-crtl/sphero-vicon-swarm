from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from .models import ControllerConfig, RobotSpec, RuntimeConfig, ViconConfig, Workspace


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"[{key}] must be a TOML table.")
    return value


def load_config(path: str | Path, *, allow_placeholders: bool = False) -> RuntimeConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    v = _section(data, "vicon")
    w = _section(data, "workspace")
    c = _section(data, "controller")
    robots_raw = data.get("robots", [])
    if not isinstance(robots_raw, list):
        raise ValueError("[[robots]] entries are required.")

    vicon = ViconConfig(
        server=os.getenv("VICON_SERVER", str(v.get("server", "127.0.0.1:801"))),
        floor_plane=os.getenv("VICON_FLOOR_PLANE", str(v.get("floor_plane", "XY"))).upper(),
        yaw_euler_index=int(v.get("yaw_euler_index", 2)),
        yaw_sign=float(v.get("yaw_sign", 1.0)),
        yaw_offset_deg=float(v.get("yaw_offset_deg", 0.0)),
    )
    workspace = Workspace(
        x_min_mm=float(w.get("x_min_mm", -2000.0)),
        x_max_mm=float(w.get("x_max_mm", 2000.0)),
        y_min_mm=float(w.get("y_min_mm", -2000.0)),
        y_max_mm=float(w.get("y_max_mm", 2000.0)),
        soft_margin_mm=float(w.get("soft_margin_mm", 300.0)),
    )
    controller = ControllerConfig(
        control_hz=float(c.get("control_hz", 50.0)),
        command_hz=float(c.get("command_hz", 20.0)),
        max_speed_cmd=int(c.get("max_speed_cmd", 160)),
        formation_radius_mm=float(c.get("formation_radius_mm", 220.0)),
        square_side_mm=float(c.get("square_side_mm", 1500.0)),
    )
    robots: list[RobotSpec] = []
    for index, raw in enumerate(robots_raw, start=1):
        if not isinstance(raw, dict):
            raise ValueError("Each [[robots]] entry must be a TOML table.")
        suffix = str(index)
        robots.append(
            RobotSpec(
                label=str(raw.get("label", f"robot-{index}")),
                sphero_name=os.getenv(f"SPHERO_{suffix}_NAME", str(raw.get("sphero_name", "YOUR_DEVICE_NAME"))),
                vicon_subject=os.getenv(f"VICON_{suffix}_SUBJECT", str(raw.get("vicon_subject", f"Robot {index}"))),
                vicon_segment=os.getenv(f"VICON_{suffix}_SEGMENT", str(raw.get("vicon_segment", raw.get("vicon_subject", f"Robot {index}")))),
                body_length_mm=float(raw.get("body_length_mm", 200.0)),
                body_width_mm=float(raw.get("body_width_mm", 140.0)),
            )
        )

    result = RuntimeConfig(vicon=vicon, workspace=workspace, controller=controller, robots=tuple(robots))
    if allow_placeholders:
        result.workspace.validate()
        if result.vicon.floor_plane not in {"XY", "XZ"}:
            raise ValueError("vicon.floor_plane must be 'XY' or 'XZ'.")
    else:
        result.validate()
    return result
