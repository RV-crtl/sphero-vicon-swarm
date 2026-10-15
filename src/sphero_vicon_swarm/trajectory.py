from __future__ import annotations

from dataclasses import dataclass

from .geometry import norm, project_point_to_segment, unit


@dataclass(frozen=True, slots=True)
class SquarePath:
    side_mm: float
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0

    @property
    def corners(self) -> tuple[tuple[float, float], ...]:
        h = self.side_mm / 2.0
        cx, cy = self.center_x_mm, self.center_y_mm
        return ((cx-h, cy-h), (cx+h, cy-h), (cx+h, cy+h), (cx-h, cy+h))

    def segment(self, index: int) -> tuple[tuple[float, float], tuple[float, float]]:
        corners = self.corners
        return corners[index % 4], corners[(index + 1) % 4]

    def nearest_segment(self, x_mm: float, y_mm: float) -> tuple[int, float, float, float]:
        best: tuple[int, float, float, float] | None = None
        best_dist = float("inf")
        for index in range(4):
            (ax, ay), (bx, by) = self.segment(index)
            qx, qy, t = project_point_to_segment(x_mm, y_mm, ax, ay, bx, by)
            distance = norm(x_mm - qx, y_mm - qy)
            if distance < best_dist:
                best_dist = distance
                best = (index, qx, qy, t)
        assert best is not None
        return best

    def tangent(self, segment_index: int) -> tuple[float, float]:
        (ax, ay), (bx, by) = self.segment(segment_index)
        return unit(bx - ax, by - ay)
