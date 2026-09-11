"""Backend-independent rigid-pose types and coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]


def _vector3(value: Sequence[float], *, name: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{name} must contain three values")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"{name} values must be finite")
    return result  # type: ignore[return-value]


def _quaternion(value: Sequence[float]) -> Quaternion:
    if len(value) != 4:
        raise ValueError("Pose orientation must be an xyzw quaternion")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError("Pose values must be finite")
    norm = math.hypot(*result)
    if norm <= 0.0:
        raise ValueError("Pose quaternion must be non-zero")
    return tuple(item / norm for item in result)  # type: ignore[return-value]


def _multiply_quaternions(left: Quaternion, right: Quaternion) -> Quaternion:
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return _quaternion(
        (
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
            lw * rw - lx * rx - ly * ry - lz * rz,
        )
    )


def _conjugate_quaternion(value: Quaternion) -> Quaternion:
    x, y, z, w = value
    return (-x, -y, -z, w)


def _rotate_vector(quaternion: Quaternion, vector: Vector3) -> Vector3:
    x, y, z, w = quaternion
    vx, vy, vz = vector
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


@dataclass(frozen=True, slots=True)
class Pose:
    """Rigid transform expressed in SI units with an xyzw quaternion."""

    position_m: Vector3 = (0.0, 0.0, 0.0)
    orientation_xyzw: Quaternion = (0.0, 0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        if len(self.position_m) != 3 or len(self.orientation_xyzw) != 4:
            raise ValueError("Pose requires a 3-vector and an xyzw quaternion")
        position = _vector3(self.position_m, name="Pose position")
        orientation = _quaternion(self.orientation_xyzw)
        object.__setattr__(self, "position_m", position)
        object.__setattr__(self, "orientation_xyzw", orientation)


def rotate_vector(*, pose: Pose, vector: Sequence[float]) -> Vector3:
    """Rotate a vector by a pose orientation without applying translation."""

    return _rotate_vector(
        pose.orientation_xyzw,
        _vector3(vector, name="vector"),
    )


def transform_point(*, pose: Pose, point_m: Sequence[float]) -> Vector3:
    """Transform a local point into the coordinate system containing ``pose``."""

    rotated = rotate_vector(pose=pose, vector=point_m)
    return tuple(
        pose.position_m[index] + rotated[index] for index in range(3)
    )  # type: ignore[return-value]


def compose_pose(*, parent: Pose, child: Pose) -> Pose:
    """Compose a parent pose with a child pose expressed in the parent frame."""

    return Pose(
        position_m=transform_point(pose=parent, point_m=child.position_m),
        orientation_xyzw=_multiply_quaternions(
            parent.orientation_xyzw,
            child.orientation_xyzw,
        ),
    )


def inverse_pose(*, pose: Pose) -> Pose:
    """Return the rigid transform that reverses ``pose``."""

    inverse_orientation = _conjugate_quaternion(pose.orientation_xyzw)
    inverse_position = _rotate_vector(
        inverse_orientation,
        tuple(-item for item in pose.position_m),  # type: ignore[arg-type]
    )
    return Pose(
        position_m=inverse_position,
        orientation_xyzw=inverse_orientation,
    )


def relative_pose(*, parent: Pose, child: Pose) -> Pose:
    """Return the child pose expressed in the parent coordinate frame."""

    return compose_pose(parent=inverse_pose(pose=parent), child=child)


def orientation_error_rad(*, actual: Pose, expected: Pose) -> float:
    """Return the shortest unsigned angular difference between two orientations."""

    dot = abs(
        sum(
            actual.orientation_xyzw[index] * expected.orientation_xyzw[index]
            for index in range(4)
        )
    )
    return 2.0 * math.acos(max(-1.0, min(1.0, dot)))


__all__ = [
    "Pose",
    "Quaternion",
    "Vector3",
    "compose_pose",
    "inverse_pose",
    "orientation_error_rad",
    "relative_pose",
    "rotate_vector",
    "transform_point",
]
