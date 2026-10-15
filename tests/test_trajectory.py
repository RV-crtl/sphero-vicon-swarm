from sphero_vicon_swarm.trajectory import SquarePath


def test_square_nearest_segment() -> None:
    path = SquarePath(1000)
    index, qx, qy, t = path.nearest_segment(0, -600)
    assert index == 0
    assert qy == -500
    assert 0 <= t <= 1


def test_tangent() -> None:
    path = SquarePath(1000)
    assert path.tangent(0) == (1.0, 0.0)
