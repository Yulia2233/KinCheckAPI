"""Validated motion targets. Lengths use metres, angles radians, and time seconds."""
from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .kinematics_analysis import TargetReference
from .pose import Pose


def _finite(value: Any, name: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or (minimum is not None and number < minimum):
        raise ValueError(f"{name} must be finite" + (f" and >= {minimum}" if minimum is not None else ""))
    return number


def _times(values: Sequence[float], *, minimum_count: int = 2) -> tuple[float, ...]:
    times = tuple(_finite(value, "time_s", minimum=0.0) for value in values)
    if len(times) < minimum_count or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError(f"at least {minimum_count} strictly increasing non-negative times are required")
    return times


def _reference(value: Any) -> TargetReference:
    if isinstance(value, TargetReference):
        return value
    if isinstance(value, str):
        return TargetReference(component_id=value)
    if isinstance(value, Mapping):
        return TargetReference(**dict(value))
    raise TypeError("target must be a TargetReference, component ID, or reference mapping")


def _bracket(times: Sequence[float], time_s: float) -> tuple[int, int, float]:
    time_s = _finite(time_s, "time_s", minimum=0.0)
    if time_s < times[0] or time_s > times[-1]:
        raise ValueError("target does not cover the requested time; extrapolation is not allowed")
    right = min(bisect_right(times, time_s), len(times) - 1)
    left = max(0, right - 1)
    fraction = 0.0 if left == right else (time_s - times[left]) / (times[right] - times[left])
    return left, right, fraction


def interpolate_pose(*, first: Pose, second: Pose, fraction: float) -> Pose:
    """Interpolate position linearly and orientation with shortest-arc SLERP."""
    f = _finite(fraction, "fraction", minimum=0.0)
    if f > 1:
        raise ValueError("fraction must not exceed one")
    a, b = first.orientation_xyzw, second.orientation_xyzw
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b = tuple(-x for x in b)
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > 0.9995:
        quaternion = tuple((1 - f) * x + f * y for x, y in zip(a, b))
    else:
        angle = math.acos(dot)
        denominator = math.sin(angle)
        quaternion = tuple(
            (math.sin((1 - f) * angle) * x + math.sin(f * angle) * y) / denominator
            for x, y in zip(a, b)
        )
    return Pose(
        position_m=tuple((1 - f) * x + f * y for x, y in zip(first.position_m, second.position_m)),
        orientation_xyzw=quaternion,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PosePoint:
    time_s: float
    pose: Pose

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", minimum=0.0))
        if not isinstance(self.pose, Pose):
            raise TypeError("pose must be a Pose")

    def to_dict(self) -> dict[str, Any]:
        return {"time_s": self.time_s, "pose": {
            "position_m": list(self.pose.position_m),
            "orientation_xyzw": list(self.pose.orientation_xyzw),
        }}


@dataclass(frozen=True, slots=True, kw_only=True)
class PoseTrajectory:
    """A world-frame, time-indexed acceptance target, not a Cartesian driver."""
    target: TargetReference | str | Mapping[str, Any]
    points: tuple[PosePoint, ...]
    interpolation: str = "linear"
    position_tolerance_m: float = 1e-6
    orientation_tolerance_rad: float = 1e-6

    def __post_init__(self) -> None:
        points = tuple(self.points)
        if any(not isinstance(point, PosePoint) for point in points):
            raise TypeError("points must contain PosePoint values")
        _times(tuple(point.time_s for point in points))
        if self.interpolation != "linear":
            raise ValueError("only linear position / SLERP orientation interpolation is supported")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "target", _reference(self.target))
        for name in ("position_tolerance_m", "orientation_tolerance_rad"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, minimum=0.0))

    def at(self, *, time_s: float) -> Pose:
        left, right, f = _bracket(tuple(p.time_s for p in self.points), time_s)
        return interpolate_pose(first=self.points[left].pose, second=self.points[right].pose, fraction=f)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target.to_dict(), "points": [p.to_dict() for p in self.points],
            "interpolation": self.interpolation,
            "position_tolerance_m": self.position_tolerance_m,
            "orientation_tolerance_rad": self.orientation_tolerance_rad,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> PoseTrajectory:
        data = dict(value)
        data["points"] = tuple(PosePoint(time_s=p["time_s"], pose=Pose(**p["pose"])) for p in data["points"])
        return cls(**data)


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanarPose:
    time_s: float
    x_m: float
    y_m: float
    yaw_rad: float

    def __post_init__(self) -> None:
        for name in ("time_s", "x_m", "y_m", "yaw_rad"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, minimum=0.0 if name == "time_s" else None))

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in ("time_s", "x_m", "y_m", "yaw_rad")}


@dataclass(frozen=True, slots=True, kw_only=True)
class PathTarget:
    """Geometric polyline target. This does not prescribe timing or traversal."""
    points_m: tuple[tuple[float, float, float], ...]
    closed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.closed, bool):
            raise TypeError("closed must be a boolean")
        points = tuple(tuple(_finite(x, "points_m") for x in p) for p in self.points_m)
        if self.closed and len(points) > 1 and points[0] == points[-1]:
            points = points[:-1]
        if len(points) < (3 if self.closed else 2) or any(len(p) != 3 for p in points):
            raise ValueError("a path needs at least two 3D points, or three for a closed path")
        if any(a == b for a, b in zip(points, points[1:])):
            raise ValueError("consecutive path points must be distinct")
        object.__setattr__(self, "points_m", points)

    def to_dict(self) -> dict[str, Any]:
        return {"points_m": [list(p) for p in self.points_m], "closed": self.closed}


@dataclass(frozen=True, slots=True, kw_only=True)
class CoordinatedMotionProfile:
    """Scalar joint position targets sharing one time axis."""
    axes: Mapping[str, tuple[float, ...]]
    times_s: tuple[float, ...]
    position_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        times = _times(self.times_s)
        if not isinstance(self.axes, Mapping) or not self.axes:
            raise ValueError("axes must be a non-empty mapping")
        axes = {}
        for joint_id, values in self.axes.items():
            if not isinstance(joint_id, str) or not joint_id.strip():
                raise ValueError("axis IDs must be non-empty strings")
            axes[joint_id] = tuple(_finite(x, joint_id) for x in values)
            if len(axes[joint_id]) != len(times):
                raise ValueError("each axis must have one value per time")
        object.__setattr__(self, "times_s", times)
        object.__setattr__(self, "axes", MappingProxyType(axes))
        object.__setattr__(self, "position_tolerance", _finite(self.position_tolerance, "position_tolerance", minimum=0.0))

    def to_dict(self) -> dict[str, Any]:
        return {"times_s": list(self.times_s), "axes": {k: list(v) for k, v in self.axes.items()}, "position_tolerance": self.position_tolerance}


@dataclass(frozen=True, slots=True, kw_only=True)
class PeriodicProfile:
    """Sinusoidal scalar target; conversion explicitly samples a finite interval."""
    period_s: float
    amplitude: float
    offset: float = 0.0
    phase_rad: float = 0.0

    def __post_init__(self) -> None:
        for name in ("period_s", "amplitude", "offset", "phase_rad"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.period_s <= 0 or self.amplitude < 0:
            raise ValueError("period_s must be positive and amplitude non-negative")

    def value(self, *, time_s: float) -> float:
        return self.offset + self.amplitude * math.sin(
            2 * math.pi * _finite(time_s, "time_s", minimum=0.0) / self.period_s + self.phase_rad
        )

    def to_motion_profile(self, *, start_time_s: float, end_time_s: float, sample_period_s: float):
        from .scenario import MotionProfile, ProfilePoint
        start, end = _times((start_time_s, end_time_s))
        step = _finite(sample_period_s, "sample_period_s", minimum=0.0)
        if step <= 0 or step > self.period_s / 8:
            raise ValueError("sample_period_s must be positive and no larger than period_s / 8")
        count = math.ceil((end - start) / step)
        if count > 1_000_000:
            raise ValueError("profile exceeds one million intervals")
        times = tuple(start + i * step for i in range(count)) + (end,)
        return MotionProfile(points=tuple(ProfilePoint(time_s=t, value=self.value(time_s=t)) for t in times))

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in ("period_s", "amplitude", "offset", "phase_rad")}


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionEvent:
    """Observed sample event; time_s is a recorded time, not a continuous-time proof."""
    event_type: str
    time_s: float
    joint_id: str
    value: float | None = None

    def __post_init__(self) -> None:
        if self.event_type not in {"start", "stop", "reversal"}:
            raise ValueError("event_type must be start, stop, or reversal")
        if not isinstance(self.joint_id, str) or not self.joint_id.strip():
            raise ValueError("joint_id must be non-empty")
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", minimum=0.0))
        if self.value is not None:
            object.__setattr__(self, "value", _finite(self.value, "value"))

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in ("event_type", "time_s", "joint_id", "value")}


__all__ = [
    "PosePoint", "PoseTrajectory", "PlanarPose", "PathTarget",
    "CoordinatedMotionProfile", "PeriodicProfile", "MotionEvent", "interpolate_pose",
]
