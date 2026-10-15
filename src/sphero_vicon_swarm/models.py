from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pose2D:
    x_mm: float
    y_mm: float
    yaw_deg: float = 0.0
    occluded: bool = False


@dataclass(frozen=True, slots=True)
class Velocity2D:
    vx_mm_s: float = 0.0
    vy_mm_s: float = 0.0

    @property
    def speed_mm_s(self) -> float:
        return (self.vx_mm_s**2 + self.vy_mm_s**2) ** 0.5


@dataclass(frozen=True, slots=True)
class RobotSpec:
    label: str
    sphero_name: str
    vicon_subject: str
    vicon_segment: str
    body_length_mm: float = 200.0
    body_width_mm: float = 140.0


@dataclass(frozen=True, slots=True)
class Workspace:
    x_min_mm: float
    x_max_mm: float
    y_min_mm: float
    y_max_mm: float
    soft_margin_mm: float = 300.0

    def validate(self) -> None:
        if self.x_min_mm >= self.x_max_mm or self.y_min_mm >= self.y_max_mm:
            raise ValueError("Workspace minimums must be smaller than maximums.")
        if self.soft_margin_mm < 0:
            raise ValueError("soft_margin_mm must be non-negative.")


@dataclass(frozen=True, slots=True)
class ViconConfig:
    server: str
    floor_plane: str = "XY"
    yaw_euler_index: int = 2
    yaw_sign: float = 1.0
    yaw_offset_deg: float = 0.0


@dataclass(frozen=True, slots=True)
class ControllerConfig:
    control_hz: float = 50.0
    command_hz: float = 20.0
    max_speed_cmd: int = 160
    formation_radius_mm: float = 220.0
    square_side_mm: float = 1500.0


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    vicon: ViconConfig
    workspace: Workspace
    controller: ControllerConfig
    robots: tuple[RobotSpec, ...]

    def validate(self, expected_robots: int | None = None) -> None:
        self.workspace.validate()
        if self.vicon.floor_plane not in {"XY", "XZ"}:
            raise ValueError("vicon.floor_plane must be 'XY' or 'XZ'.")
        if not self.robots:
            raise ValueError("At least one robot is required.")
        if expected_robots is not None and len(self.robots) != expected_robots:
            raise ValueError(f"Expected {expected_robots} robots, found {len(self.robots)}.")
        labels = [robot.label for robot in self.robots]
        if len(set(labels)) != len(labels):
            raise ValueError("Robot labels must be unique.")
        for robot in self.robots:
            if robot.sphero_name.startswith("YOUR_"):
                raise ValueError(f"Replace placeholder Sphero name for {robot.label} before hardware use.")
            if robot.body_length_mm <= 0 or robot.body_width_mm <= 0:
                raise ValueError(f"Body dimensions must be positive for {robot.label}.")
        if self.controller.control_hz <= 0 or self.controller.command_hz <= 0:
            raise ValueError("Controller frequencies must be positive.")
        if not 0 <= self.controller.max_speed_cmd <= 255:
            raise ValueError("max_speed_cmd must be in the Sphero command range 0..255.")
