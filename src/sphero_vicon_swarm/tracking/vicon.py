from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from ..geometry import wrap360
from ..models import Pose2D, RobotSpec, ViconConfig


class ViconTracker:
    """Context-managed adapter around the Vicon DataStream SDK."""

    def __init__(self, config: ViconConfig, robots: Iterable[RobotSpec]) -> None:
        self.config = config
        self.robots = tuple(robots)
        self._client: Any | None = None

    def __enter__(self) -> "ViconTracker":
        try:
            from vicon_dssdk import ViconDataStream
        except ImportError as exc:
            raise RuntimeError(
                "vicon_dssdk is unavailable. Install the Vicon DataStream SDK Python bindings."
            ) from exc
        client = ViconDataStream.Client()
        client.Connect(self.config.server)
        try:
            client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)
        except Exception:
            pass
        try:
            client.SetBufferSize(1)
        except Exception:
            pass
        client.EnableSegmentData()
        self._client = client
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._client is not None:
            try:
                self._client.Disconnect()
            except Exception:
                pass
            self._client = None

    @staticmethod
    def _values(result: Any) -> tuple[tuple[float, ...], bool]:
        values = tuple(float(v) for v in result[0])
        occluded = bool(result[1]) if len(result) > 1 else False
        return values, occluded

    def read_all(self) -> dict[str, Pose2D]:
        if self._client is None:
            raise RuntimeError("Use ViconTracker as a context manager.")
        client = self._client
        client.GetFrame()
        poses: dict[str, Pose2D] = {}
        for robot in self.robots:
            translation, t_occ = self._values(
                client.GetSegmentGlobalTranslation(robot.vicon_subject, robot.vicon_segment)
            )
            rotation, r_occ = self._values(
                client.GetSegmentGlobalRotationEulerXYZ(robot.vicon_subject, robot.vicon_segment)
            )
            if self.config.floor_plane == "XY":
                x_mm, y_mm = translation[0], translation[1]
            else:
                x_mm, y_mm = translation[0], translation[2]
            yaw = math.degrees(rotation[self.config.yaw_euler_index])
            yaw = wrap360(self.config.yaw_sign * yaw + self.config.yaw_offset_deg)
            poses[robot.label] = Pose2D(x_mm, y_mm, yaw, t_occ or r_occ)
        return poses
