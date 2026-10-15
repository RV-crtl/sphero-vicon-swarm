from sphero_vicon_swarm.geometry import clamp, project_point_to_segment, rotate, unit, wrap180, wrap360


def test_angle_wrapping() -> None:
    assert wrap360(-10) == 350
    assert wrap180(190) == -170


def test_projection() -> None:
    x, y, t = project_point_to_segment(5, 3, 0, 0, 10, 0)
    assert (x, y, t) == (5, 0, 0.5)


def test_unit_and_rotate() -> None:
    x, y = unit(3, 4)
    assert round(x, 6) == 0.6 and round(y, 6) == 0.8
    x, y = rotate(1, 0, 90)
    assert abs(x) < 1e-9 and abs(y - 1) < 1e-9


def test_clamp() -> None:
    assert clamp(5, 0, 3) == 3
