from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..geometry import clamp


@dataclass(slots=True)
class SpheroV2Driver:
    """Thin adapter around the public ``spherov2`` SpheroEduAPI."""

    name: str
    _api: Any
    _context: Any

    @classmethod
    def connect(cls, name: str, timeout_s: float = 15.0) -> "SpheroV2Driver":
        try:
            from spherov2 import scanner
            from spherov2.sphero_edu import SpheroEduAPI
        except ImportError as exc:
            raise RuntimeError(
                "The optional spherov2 backend is not installed. Run: "
                "python -m pip install -e '.[sphero]'"
            ) from exc
        toy = scanner.find_toy(toy_name=name, timeout=timeout_s)
        context = SpheroEduAPI(toy)
        api = context.__enter__()
        try:
            api.set_stabilization(True)
        except Exception:
            pass
        return cls(name=name, _api=api, _context=context)

    def command(self, heading_deg: float, speed_cmd: int) -> None:
        self._api.set_heading(int(round(heading_deg)) % 360)
        self._api.set_speed(int(round(clamp(float(speed_cmd), 0.0, 255.0))))

    def stop(self) -> None:
        try:
            self._api.stop_roll()
        except Exception:
            self._api.set_speed(0)

    def close(self) -> None:
        try:
            self.stop()
        finally:
            self._context.__exit__(None, None, None)
