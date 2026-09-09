from __future__ import annotations

import math
from dataclasses import dataclass

from .geometry import clamp, wrap180, wrap360
from .models import Pose2D


@dataclass(slots=True)
class SimRobot:
    label: str
    x_mm: float
    y_mm: float
    yaw_deg: float
    heading_bias_deg: float = 0.0
    speed_scale: float = 1.0
    static_cmd: int = 120
    speed_mm_s: float = 0.0
    command_heading_deg: float = 0.0
    command_speed: int = 0

    def command(self, heading_deg: float, speed_cmd: int) -> None:
        self.command_heading_deg = wrap360(heading_deg + self.heading_bias_deg)
        self.command_speed = int(clamp(speed_cmd, 0, 255))

    def stop(self) -> None:
        self.command_speed = 0

    def step(self, dt_s: float) -> None:
        desired = 0.0 if self.command_speed < self.static_cmd and self.speed_mm_s < 20 else self.command_speed * 5.2 * self.speed_scale
        tau = 0.20 if desired >= self.speed_mm_s else 0.12
        self.speed_mm_s += (desired - self.speed_mm_s) * clamp(dt_s / tau, 0.0, 1.0)
        error = wrap180(self.command_heading_deg - self.yaw_deg)
        self.yaw_deg = wrap360(self.yaw_deg + clamp(error, -240 * dt_s, 240 * dt_s))
        self.x_mm += self.speed_mm_s * math.cos(math.radians(self.yaw_deg)) * dt_s
        self.y_mm += self.speed_mm_s * math.sin(math.radians(self.yaw_deg)) * dt_s

    def pose(self) -> Pose2D:
        return Pose2D(self.x_mm, self.y_mm, self.yaw_deg, False)


def default_three_robot_simulation() -> list[SimRobot]:
    return [
        SimRobot("robot-1", -300.0, -80.0, 10.0, heading_bias_deg=-12.0, speed_scale=0.90, static_cmd=135),
        SimRobot("robot-2", 0.0, -120.0, 80.0, heading_bias_deg=20.0, speed_scale=1.03, static_cmd=120),
        SimRobot("robot-3", 300.0, 40.0, 300.0, heading_bias_deg=-32.0, speed_scale=0.86, static_cmd=145),
    ]
