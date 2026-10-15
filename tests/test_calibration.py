import pytest

from sphero_vicon_swarm.calibration import HeadingBasis


def test_identity_basis() -> None:
    basis = HeadingBasis.from_displacements(100, 0, 0, 100)
    assert basis.world_vector_to_heading(1, 0) == pytest.approx(0)
    assert basis.world_vector_to_heading(0, 1) == pytest.approx(90)


def test_rotated_basis() -> None:
    basis = HeadingBasis.from_displacements(0, 100, -100, 0)
    assert basis.world_vector_to_heading(0, 1) == pytest.approx(0)
    assert basis.world_vector_to_heading(-1, 0) == pytest.approx(90)


def test_rejects_short_displacement() -> None:
    with pytest.raises(ValueError):
        HeadingBasis.from_displacements(1, 0, 0, 1)
