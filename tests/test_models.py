import pytest

from sphero_vicon_swarm.models import ControllerConfig, RobotSpec, RuntimeConfig, ViconConfig, Workspace


def make_runtime(name: str = "DEVICE") -> RuntimeConfig:
    return RuntimeConfig(
        vicon=ViconConfig("127.0.0.1:801"),
        workspace=Workspace(-1000, 1000, -1000, 1000, 100),
        controller=ControllerConfig(),
        robots=(RobotSpec("robot-1", name, "Robot 1", "Robot 1"),),
    )


def test_runtime_validation_accepts_valid_config() -> None:
    make_runtime().validate(expected_robots=1)


def test_runtime_validation_rejects_placeholder() -> None:
    with pytest.raises(ValueError):
        make_runtime("YOUR_DEVICE_NAME").validate()


def test_runtime_validation_rejects_duplicate_labels() -> None:
    cfg = make_runtime()
    bad = RuntimeConfig(cfg.vicon, cfg.workspace, cfg.controller, cfg.robots + (cfg.robots[0],))
    with pytest.raises(ValueError):
        bad.validate()


def test_workspace_validation_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError):
        Workspace(1, 0, -1, 1).validate()


def test_expected_robot_count_is_checked() -> None:
    with pytest.raises(ValueError):
        make_runtime().validate(expected_robots=3)
