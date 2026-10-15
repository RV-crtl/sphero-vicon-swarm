from __future__ import annotations

from typing import Protocol


class RobotDriver(Protocol):
    name: str

    def command(self, heading_deg: float, speed_cmd: int) -> None: ...

    def stop(self) -> None: ...

    def close(self) -> None: ...
