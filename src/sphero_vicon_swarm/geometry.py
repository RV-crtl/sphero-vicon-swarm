from __future__ import annotations

import math


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wrap360(degrees: float) -> float:
    return degrees % 360.0


def wrap180(degrees: float) -> float:
    return (degrees + 180.0) % 360.0 - 180.0


def norm(x: float, y: float) -> float:
    return math.hypot(x, y)


def unit(x: float, y: float) -> tuple[float, float]:
    magnitude = norm(x, y)
    if magnitude <= 1e-12:
        return 0.0, 0.0
    return x / magnitude, y / magnitude


def dot(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * bx + ay * by


def project_point_to_segment(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> tuple[float, float, float]:
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return ax, ay, 0.0
    t = clamp(((px - ax) * dx + (py - ay) * dy) / denom, 0.0, 1.0)
    return ax + t * dx, ay + t * dy, t


def rotate(x: float, y: float, degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return c * x - s * y, s * x + c * y
