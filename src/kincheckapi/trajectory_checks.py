"""Reusable trajectory-window statistics for public result checks."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping, Sequence

from .result import LimitEvent, Trajectory


@dataclass(frozen=True, slots=True, kw_only=True)
class TrajectoryWindowMetrics:
    indices: tuple[int, ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "indices", tuple(self.indices))
        object.__setattr__(self, "bounds_m", MappingProxyType(dict(self.bounds_m)))


def trajectory_window_metrics(
    *,
    trajectory: Trajectory,
    start_time_s: float | None,
    end_time_s: float | None,
) -> TrajectoryWindowMetrics:
    indices = tuple(
        index
        for index, time_s in enumerate(trajectory.times_s)
        if (start_time_s is None or time_s >= start_time_s)
        and (end_time_s is None or time_s <= end_time_s)
    )
    positions = tuple(trajectory.poses[index].position_m for index in indices)
    path_length = sum(
        math.dist(left, right) for left, right in zip(positions, positions[1:])
    )
    bounds = (
        {
            axis: (
                min(position[index] for position in positions),
                max(position[index] for position in positions),
            )
            for index, axis in enumerate(("x_m", "y_m", "z_m"))
        }
        if positions
        else {}
    )
    return TrajectoryWindowMetrics(
        indices=indices,
        path_length_m=path_length,
        bounds_m=bounds,
    )


def normalize_position_bounds(
    value: Mapping[str, Sequence[float]] | None,
) -> Mapping[str, tuple[float, float]]:
    normalized: dict[str, tuple[float, float]] = {}
    aliases = {"x": "x_m", "y": "y_m", "z": "z_m", "x_m": "x_m", "y_m": "y_m", "z_m": "z_m"}
    for raw_axis, raw_bounds in (value or {}).items():
        if raw_axis not in aliases:
            raise ValueError(f"unsupported position bound axis: {raw_axis}")
        bounds = tuple(float(item) for item in raw_bounds)
        if len(bounds) != 2 or not all(math.isfinite(item) for item in bounds) or bounds[0] > bounds[1]:
            raise ValueError(f"position bound for {raw_axis} must be finite (lower, upper)")
        normalized[aliases[raw_axis]] = bounds
    return MappingProxyType(dict(sorted(normalized.items())))


def limit_events_in_window(
    *,
    events: Sequence[LimitEvent],
    joint_ids: Sequence[str] | None,
    start_time_s: float | None,
    end_time_s: float | None,
) -> tuple[LimitEvent, ...]:
    selected_ids = None if joint_ids is None else set(joint_ids)
    return tuple(
        event
        for event in events
        if (selected_ids is None or event.joint_id in selected_ids)
        and (start_time_s is None or event.time_s >= start_time_s)
        and (end_time_s is None or event.time_s <= end_time_s)
    )


__all__ = [
    "TrajectoryWindowMetrics",
    "limit_events_in_window",
    "normalize_position_bounds",
    "trajectory_window_metrics",
]
