from sphero_vicon_swarm.control import boundary_recovery, collision_repulsion, slot_velocity, vector_to_speed_cmd
from sphero_vicon_swarm.models import Pose2D, Velocity2D, Workspace


def test_slot_velocity_points_toward_target() -> None:
    v = slot_velocity(Pose2D(0, 0), Velocity2D(), 100, 0, 0, 0)
    assert v.vx_mm_s > 0
    assert abs(v.vy_mm_s) < 1e-9


def test_collision_repulsion_points_away() -> None:
    poses = {"a": Pose2D(0, 0), "b": Pose2D(100, 0)}
    r = collision_repulsion("a", poses)
    assert r.vx_mm_s < 0


def test_boundary_pushes_inward() -> None:
    ws = Workspace(-1000, 1000, -1000, 1000, 200)
    r = boundary_recovery(Pose2D(-950, 0), ws)
    assert r.vx_mm_s > 0


def test_speed_command_bounded() -> None:
    v = slot_velocity(Pose2D(0, 0), Velocity2D(), 10000, 0, 0, 0)
    assert 0 <= vector_to_speed_cmd(v, max_speed_cmd=140) <= 140
