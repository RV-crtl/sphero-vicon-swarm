from pathlib import Path

from sphero_vicon_swarm.config import load_config


def test_example_config_parses() -> None:
    path = Path("config/robot_setup.example.toml")
    cfg = load_config(path, allow_placeholders=True)
    assert len(cfg.robots) == 3
    assert cfg.vicon.floor_plane == "XY"
    assert cfg.controller.max_speed_cmd == 160
