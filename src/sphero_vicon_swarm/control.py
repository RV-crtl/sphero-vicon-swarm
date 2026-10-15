from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .geometry import clamp, norm, unit
from .models import Pose2D, Velocity2D, Workspace


@dataclass(frozen=True, slots=True)
class MotionVector:
    vx_mm_s: float
    vy_mm_s: float

    @property
    def magnitude_mm_s(self) -> float:
        return norm(self.vx_mm_s, self.vy_mm_s)


@dataclass(frozen=True, slots=True)
class VectorFieldGains:
    slot_kp: float = 1.15
    slot_kd: float = 0.18
    max_slot_correction_mm_s: float = 650.0
    collision_radius_mm: float = 360.0
    collision_gain: float = 90000.0
    boundary_gain: float = 2.2
    max_boundary_correction_mm_s: float = 900.0


def slot_velocity(
    pose: Pose2D,
    velocity: Velocity2D,
    target_x_mm: float,
    target_y_mm: float,
    feedforward_vx_mm_s: float,
    feedforward_vy_mm_s: float,
    gains: VectorFieldGains = VectorFieldGains(),
) -> MotionVector:
    ex = target_x_mm - pose.x_mm
    ey = target_y_mm - pose.y_mm
    cx = gains.slot_kp * ex - gains.slot_kd * velocity.vx_mm_s
    cy = gains.slot_kp * ey - gains.slot_kd * velocity.vy_mm_s
    cmag = norm(cx, cy)
    if cmag > gains.max_slot_correction_mm_s:
        ux, uy = unit(cx, cy)
        cx, cy = ux * gains.max_slot_correction_mm_s, uy * gains.max_slot_correction_mm_s
    return MotionVector(feedforward_vx_mm_s + cx, feedforward_vy_mm_s + cy)


def collision_repulsion(
    label: str,
    poses: Mapping[str, Pose2D],
    *,
    gains: VectorFieldGains = VectorFieldGains(),
) -> MotionVector:
    own = poses[label]
    rx = ry = 0.0
    for other_label, other in poses.items():
        if other_label == label:
            continue
        dx, dy = own.x_mm - other.x_mm, own.y_mm - other.y_mm
        distance = norm(dx, dy)
        if distance <= 1e-6 or distance >= gains.collision_radius_mm:
            continue
        ux, uy = dx / distance, dy / distance
        strength = gains.collision_gain * (1.0 / distance - 1.0 / gains.collision_radius_mm)
        rx += ux * strength
        ry += uy * strength
    return MotionVector(rx, ry)


def boundary_recovery(
    pose: Pose2D,
    workspace: Workspace,
    *,
    gains: VectorFieldGains = VectorFieldGains(),
) -> MotionVector:
    left = pose.x_mm - workspace.x_min_mm
    right = workspace.x_max_mm - pose.x_mm
    bottom = pose.y_mm - workspace.y_min_mm
    top = workspace.y_max_mm - pose.y_mm
    margin = workspace.soft_margin_mm
    rx = ry = 0.0
    if left < margin:
        rx += gains.boundary_gain * (margin - left)
    if right < margin:
        rx -= gains.boundary_gain * (margin - right)
    if bottom < margin:
        ry += gains.boundary_gain * (margin - bottom)
    if top < margin:
        ry -= gains.boundary_gain * (margin - top)
    mag = norm(rx, ry)
    if mag > gains.max_boundary_correction_mm_s:
        ux, uy = unit(rx, ry)
        rx, ry = ux * gains.max_boundary_correction_mm_s, uy * gains.max_boundary_correction_mm_s
    return MotionVector(rx, ry)


def combine(*vectors: MotionVector, max_magnitude_mm_s: float = 2200.0) -> MotionVector:
    x = sum(v.vx_mm_s for v in vectors)
    y = sum(v.vy_mm_s for v in vectors)
    magnitude = norm(x, y)
    if magnitude > max_magnitude_mm_s:
        ux, uy = unit(x, y)
        x, y = ux * max_magnitude_mm_s, uy * max_magnitude_mm_s
    return MotionVector(x, y)


def vector_to_speed_cmd(vector: MotionVector, *, max_speed_cmd: int = 160) -> int:
    # Deliberately simple monotonic map. Real chariots should use measured breakaway
    # and rolling-speed characterisation rather than treating command units as mm/s.
    return int(round(clamp(vector.magnitude_mm_s / 8.0, 0.0, float(max_speed_cmd))))
