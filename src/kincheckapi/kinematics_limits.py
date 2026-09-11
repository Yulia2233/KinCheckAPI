"""Joint-limit event detection for sampled motion results."""

from __future__ import annotations

import math
from typing import Sequence

from .assembly import AssemblyModel
from .result import JointTrajectory, LimitEvent


def _crossing_time(
    *,
    left_time: float,
    right_time: float,
    left_value: float,
    right_value: float,
    limit: float,
) -> float:
    delta = right_value - left_value
    if abs(delta) <= 1e-15:
        return float(right_time)
    weight = (limit - left_value) / delta
    weight = min(1.0, max(0.0, weight))
    return float(left_time + weight * (right_time - left_time))


def detect_limit_events(
    *,
    assembly: AssemblyModel,
    joint_trajectories: Sequence[JointTrajectory],
    tolerance: float = 1e-9,
) -> tuple[LimitEvent, ...]:
    """Return the first reached/exceeded event for each Joint limit side."""

    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("limit-event tolerance must be finite and non-negative")
    trajectory_by_id = {item.joint_id: item for item in joint_trajectories}
    events: list[LimitEvent] = []
    for joint in sorted(assembly.joints, key=lambda item: item.joint_id):
        if joint.limit is None:
            continue
        trajectory = trajectory_by_id.get(joint.joint_id)
        if trajectory is None:
            continue
        for side, limit, direction in (
            ("lower", float(joint.limit.lower), -1.0),
            ("upper", float(joint.limit.upper), 1.0),
        ):
            reached_recorded = False
            exceeded_recorded = False
            times = trajectory.times_s
            positions = trajectory.positions
            first_distance = direction * (positions[0] - limit)
            if abs(first_distance) <= tolerance:
                events.append(
                    LimitEvent(
                        joint_id=joint.joint_id,
                        time_s=times[0],
                        side=side,
                        event_type="reached",
                        position=positions[0],
                        limit_position=limit,
                    )
                )
                reached_recorded = True
            elif first_distance > tolerance:
                events.append(
                    LimitEvent(
                        joint_id=joint.joint_id,
                        time_s=times[0],
                        side=side,
                        event_type="exceeded",
                        position=positions[0],
                        limit_position=limit,
                    )
                )
                exceeded_recorded = True
            for index in range(1, len(times)):
                previous = float(positions[index - 1])
                current = float(positions[index])
                previous_distance = direction * (previous - limit)
                current_distance = direction * (current - limit)
                crossed_from_inside = (
                    previous_distance < -tolerance
                    and current_distance >= -tolerance
                )
                if crossed_from_inside and not reached_recorded:
                    events.append(
                        LimitEvent(
                            joint_id=joint.joint_id,
                            time_s=_crossing_time(
                                left_time=times[index - 1],
                                right_time=times[index],
                                left_value=previous,
                                right_value=current,
                                limit=limit,
                            ),
                            side=side,
                            event_type="reached",
                            position=limit,
                            limit_position=limit,
                        )
                    )
                    reached_recorded = True
                if current_distance > tolerance and not exceeded_recorded:
                    events.append(
                        LimitEvent(
                            joint_id=joint.joint_id,
                            time_s=times[index],
                            side=side,
                            event_type="exceeded",
                            position=current,
                            limit_position=limit,
                        )
                    )
                    exceeded_recorded = True
                if reached_recorded and exceeded_recorded:
                    break
    return tuple(sorted(events, key=lambda item: (item.time_s, item.joint_id, item.side, item.event_type)))


__all__ = ["detect_limit_events"]
