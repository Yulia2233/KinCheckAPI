from __future__ import annotations

import math

import pytest

import kincheckapi
from kincheckapi.assembly import Pose as AssemblyPose
from kincheckapi.pose import (
    Pose,
    compose_pose,
    inverse_pose,
    orientation_error_rad,
    relative_pose,
    rotate_vector,
    transform_point,
)


def _axis_angle(axis: tuple[float, float, float], degrees: float) -> tuple[float, ...]:
    radians = math.radians(degrees) / 2.0
    scale = math.sin(radians)
    return (
        axis[0] * scale,
        axis[1] * scale,
        axis[2] * scale,
        math.cos(radians),
    )


def _assert_same_pose(actual: Pose, expected: Pose) -> None:
    assert actual.position_m == pytest.approx(expected.position_m, abs=1e-12)
    assert orientation_error_rad(actual=actual, expected=expected) == pytest.approx(
        0.0, abs=1e-12
    )


@pytest.mark.parametrize(
    ("position", "orientation", "expected"),
    [
        ((0, 0, 0), (0, 0, 0, 1), (0.0, 0.0, 0.0, 1.0)),
        ((1, 2, 3), (0, 0, 3, 4), (0.0, 0.0, 0.6, 0.8)),
        ((0, 0, 0), (0, 0, -3, -4), (0.0, 0.0, -0.6, -0.8)),
        ((0, 0, 0), (1e308, 0, 0, 0), (1.0, 0.0, 0.0, 0.0)),
        ((0, 0, 0), (1e-300, 0, 0, 0), (1.0, 0.0, 0.0, 0.0)),
        ([1, 2, 3], [1, 1, 1, 1], (0.5, 0.5, 0.5, 0.5)),
    ],
)
def test_pose_normalizes_and_freezes_numeric_inputs(position, orientation, expected):
    pose = Pose(position_m=position, orientation_xyzw=orientation)

    assert pose.position_m == tuple(float(item) for item in position)
    assert pose.orientation_xyzw == pytest.approx(expected)
    assert isinstance(pose.position_m, tuple)
    assert isinstance(pose.orientation_xyzw, tuple)


def test_pose_is_reexported_without_changing_legacy_type_identity():
    assert AssemblyPose is Pose
    assert kincheckapi.Pose is Pose


@pytest.mark.parametrize(
    ("pose", "vector", "expected"),
    [
        (Pose(), (1, 2, 3), (1, 2, 3)),
        (Pose(position_m=(5, 6, 7)), (1, 2, 3), (1, 2, 3)),
        (Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)), (1, 0, 0), (0, 1, 0)),
        (Pose(orientation_xyzw=_axis_angle((1, 0, 0), 180)), (0, 1, 0), (0, -1, 0)),
        (Pose(orientation_xyzw=_axis_angle((0, 1, 0), 90)), (0, 0, 1), (1, 0, 0)),
        (Pose(orientation_xyzw=(0, 0, -3, -3)), (1, 0, 0), (0, 1, 0)),
    ],
)
def test_rotate_vector_applies_orientation_only(pose, vector, expected):
    assert rotate_vector(pose=pose, vector=vector) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    ("pose", "point", "expected"),
    [
        (Pose(), (1, 2, 3), (1, 2, 3)),
        (Pose(position_m=(5, -2, 1)), (1, 2, 3), (6, 0, 4)),
        (Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)), (1, 0, 0), (0, 1, 0)),
        (
            Pose(position_m=(2, 3, 4), orientation_xyzw=_axis_angle((0, 0, 1), 90)),
            (1, 0, 0),
            (2, 4, 4),
        ),
        (
            Pose(position_m=(1, 1, 1), orientation_xyzw=_axis_angle((1, 0, 0), 180)),
            (0, 2, 3),
            (1, -1, -2),
        ),
        (
            Pose(position_m=(-1, 0, 2), orientation_xyzw=_axis_angle((0, 1, 0), 90)),
            (0, 0, 2),
            (1, 0, 2),
        ),
    ],
)
def test_transform_point_applies_rotation_then_translation(pose, point, expected):
    assert transform_point(pose=pose, point_m=point) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    ("parent", "child", "expected"),
    [
        (Pose(), Pose(), Pose()),
        (Pose(position_m=(1, 2, 3)), Pose(), Pose(position_m=(1, 2, 3))),
        (Pose(), Pose(position_m=(4, 5, 6)), Pose(position_m=(4, 5, 6))),
        (
            Pose(position_m=(1, 0, 0), orientation_xyzw=_axis_angle((0, 0, 1), 90)),
            Pose(position_m=(2, 0, 0)),
            Pose(position_m=(1, 2, 0), orientation_xyzw=_axis_angle((0, 0, 1), 90)),
        ),
        (
            Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)),
            Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)),
            Pose(orientation_xyzw=_axis_angle((0, 0, 1), 180)),
        ),
        (
            Pose(position_m=(0, 1, 0), orientation_xyzw=_axis_angle((1, 0, 0), 180)),
            Pose(position_m=(0, 2, 3)),
            Pose(position_m=(0, -1, -3), orientation_xyzw=_axis_angle((1, 0, 0), 180)),
        ),
    ],
)
def test_compose_pose_combines_parent_and_child_transforms(parent, child, expected):
    _assert_same_pose(compose_pose(parent=parent, child=child), expected)


@pytest.mark.parametrize(
    "pose",
    [
        Pose(),
        Pose(position_m=(1, 2, 3)),
        Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)),
        Pose(position_m=(1, 0, 0), orientation_xyzw=_axis_angle((0, 0, 1), 90)),
        Pose(position_m=(-3, 2, 7), orientation_xyzw=(1, 2, 3, 4)),
    ],
)
def test_inverse_pose_cancels_pose_from_both_sides(pose):
    inverse = inverse_pose(pose=pose)

    _assert_same_pose(compose_pose(parent=pose, child=inverse), Pose())
    _assert_same_pose(compose_pose(parent=inverse, child=pose), Pose())


@pytest.mark.parametrize(
    ("parent", "local"),
    [
        (Pose(), Pose()),
        (Pose(position_m=(1, 2, 3)), Pose(position_m=(4, 5, 6))),
        (Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)), Pose(position_m=(1, 0, 0))),
        (
            Pose(position_m=(3, -2, 1), orientation_xyzw=_axis_angle((1, 0, 0), 180)),
            Pose(position_m=(0, 2, 4), orientation_xyzw=_axis_angle((0, 1, 0), 45)),
        ),
        (
            Pose(position_m=(-5, 4, 3), orientation_xyzw=(1, 2, 3, 4)),
            Pose(position_m=(2, -1, 6), orientation_xyzw=(4, -3, 2, -1)),
        ),
    ],
)
def test_relative_pose_recovers_child_local_transform(parent, local):
    child_world = compose_pose(parent=parent, child=local)

    _assert_same_pose(relative_pose(parent=parent, child=child_world), local)


@pytest.mark.parametrize(
    ("actual", "expected", "degrees"),
    [
        (Pose(), Pose(), 0.0),
        (Pose(orientation_xyzw=(0, 0, 0, -1)), Pose(), 0.0),
        (Pose(), Pose(orientation_xyzw=_axis_angle((0, 0, 1), 45)), 45.0),
        (
            Pose(orientation_xyzw=_axis_angle((0, 0, 1), 45)),
            Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)),
            45.0,
        ),
        (Pose(orientation_xyzw=_axis_angle((0, 0, 1), 90)), Pose(), 90.0),
        (Pose(), Pose(orientation_xyzw=_axis_angle((1, 0, 0), 180)), 180.0),
        (
            Pose(orientation_xyzw=_axis_angle((1, 0, 0), 90)),
            Pose(orientation_xyzw=_axis_angle((0, 1, 0), 90)),
            120.0,
        ),
    ],
)
def test_orientation_error_returns_shortest_unsigned_angle(actual, expected, degrees):
    assert orientation_error_rad(actual=actual, expected=expected) == pytest.approx(
        math.radians(degrees), abs=1e-12
    )


@pytest.mark.parametrize(
    ("operation", "argument"),
    [
        (rotate_vector, (1, 2)),
        (rotate_vector, (1, 2, math.inf)),
        (transform_point, (1, 2)),
        (transform_point, (1, math.nan, 3)),
    ],
)
def test_vector_and_point_operations_reject_malformed_inputs(operation, argument):
    keyword = "vector" if operation is rotate_vector else "point_m"
    with pytest.raises(ValueError):
        operation(pose=Pose(), **{keyword: argument})
