from __future__ import annotations

import math
from dataclasses import dataclass

from .geometry import dot, norm, wrap360


@dataclass(frozen=True, slots=True)
class HeadingBasis:
    """2-D mapping from Sphero heading axes to Vicon-world motion axes."""

    e0_x: float
    e0_y: float
    e90_x: float
    e90_y: float

    @classmethod
    def from_displacements(
        cls,
        heading0_dx: float,
        heading0_dy: float,
        heading90_dx: float,
        heading90_dy: float,
        *,
        min_displacement_mm: float = 40.0,
        max_axis_dot: float = 0.35,
    ) -> "HeadingBasis":
        mag0 = norm(heading0_dx, heading0_dy)
        mag90 = norm(heading90_dx, heading90_dy)
        if mag0 < min_displacement_mm or mag90 < min_displacement_mm:
            raise ValueError("Calibration displacement is too small to establish a reliable basis.")
        e0 = (heading0_dx / mag0, heading0_dy / mag0)
        e90 = (heading90_dx / mag90, heading90_dy / mag90)
        if abs(dot(*e0, *e90)) > max_axis_dot:
            raise ValueError("Calibration axes are not sufficiently independent.")
        det = e0[0] * e90[1] - e90[0] * e0[1]
        if abs(det) < 0.25:
            raise ValueError("Calibration basis is poorly conditioned.")
        return cls(e0[0], e0[1], e90[0], e90[1])

    def world_vector_to_heading(self, vx: float, vy: float) -> float:
        det = self.e0_x * self.e90_y - self.e90_x * self.e0_y
        if abs(det) < 1e-9:
            raise ValueError("Heading basis is singular.")
        a = (vx * self.e90_y - vy * self.e90_x) / det
        b = (self.e0_x * vy - self.e0_y * vx) / det
        return wrap360(math.degrees(math.atan2(b, a)))

    def heading_to_world_unit(self, heading_deg: float) -> tuple[float, float]:
        angle = math.radians(heading_deg)
        x = math.cos(angle) * self.e0_x + math.sin(angle) * self.e90_x
        y = math.cos(angle) * self.e0_y + math.sin(angle) * self.e90_y
        magnitude = norm(x, y)
        return x / magnitude, y / magnitude
