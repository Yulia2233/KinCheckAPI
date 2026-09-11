from __future__ import annotations

import pytest

from kincheckapi import checks
from kincheckapi.pose import Pose
from kincheckapi.result import ConstraintResidual, LimitEvent, MotionResult, Trajectory


def _motion(*, residuals=(), events=()):
    times = (0.0, 1.0, 2.0)
    trajectory = Trajectory(
        component_id="component.tool",
        connector_id="connector.tip",
        times_s=times,
        poses=(Pose(position_m=(0.0, 0.0, 0.0)), Pose(position_m=(1.0, 0.0, 0.0)), Pose(position_m=(1.0, 1.0, 0.0))),
        linear_velocities_m_s=((0.0, 0.0, 0.0),) * 3,
        angular_velocities_rad_s=((0.0, 0.0, 0.0),) * 3,
        linear_accelerations_m_s2=((0.0, 0.0, 0.0),) * 3,
        angular_accelerations_rad_s2=((0.0, 0.0, 0.0),) * 3,
    )
    return MotionResult(
        scenario_id="trajectory.review",
        assembly_id="assembly.review",
        status="completed",
        start_time_s=0.0,
        end_time_s=2.0,
        sample_times_s=times,
        trajectories=(trajectory,),
        constraint_residuals=tuple(residuals),
        limit_events=tuple(events),
    )


def test_trajectory_path_length_passes_requested_range():
    report = checks.check_trajectory(motion_result=_motion(), min_path_length_m=1.9, max_path_length_m=2.1)
    assert report.passed


def test_trajectory_path_length_failure_is_structured():
    report = checks.check_trajectory(motion_result=_motion(), max_path_length_m=1.5)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TRAJECTORY-PATH-LENGTH-OUT-OF-RANGE"


def test_trajectory_coordinate_bounds_pass():
    report = checks.check_trajectory(motion_result=_motion(), position_bounds_m={"x": (0.0, 1.0), "y_m": (0.0, 1.0)})
    assert report.passed


def test_trajectory_coordinate_bounds_fail():
    report = checks.check_trajectory(motion_result=_motion(), position_bounds_m={"x_m": (0.0, 0.5)})
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TRAJECTORY-POSITION-OUT-OF-RANGE"


def test_trajectory_residual_outside_time_window_is_ignored():
    residuals = (ConstraintResidual(constraint_id="closure", time_s=2.0, position_residual_m=1.0, orientation_residual_rad=0.0),)
    report = checks.check_trajectory(motion_result=_motion(residuals=residuals), max_position_residual_m=0.1, end_time_s=1.0)
    assert report.passed


def test_trajectory_residual_inside_time_window_fails():
    residuals = (ConstraintResidual(constraint_id="closure", time_s=1.0, position_residual_m=1.0, orientation_residual_rad=0.0),)
    report = checks.check_trajectory(motion_result=_motion(residuals=residuals), max_position_residual_m=0.1, end_time_s=1.0)
    assert not report.passed


def test_trajectory_limit_event_count_is_checked():
    event = LimitEvent(joint_id="joint.a", time_s=1.0, side="upper", event_type="reached", position=1.0, limit_position=1.0)
    report = checks.check_trajectory(motion_result=_motion(events=(event,)), maximum_limit_event_count=0)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TRAJECTORY-LIMIT-EVENTS-EXCEEDED"


def test_trajectory_exceeded_limit_event_is_checked():
    event = LimitEvent(joint_id="joint.a", time_s=1.0, side="upper", event_type="exceeded", position=1.1, limit_position=1.0)
    report = checks.check_trajectory(motion_result=_motion(events=(event,)), maximum_exceeded_limit_event_count=0)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TRAJECTORY-LIMIT-EXCEEDED-EVENTS"


def test_trajectory_rejects_exceeded_event_by_default():
    event = LimitEvent(joint_id="joint.a", time_s=1.0, side="upper", event_type="exceeded", position=1.1, limit_position=1.0)
    report = checks.check_trajectory(motion_result=_motion(events=(event,)))
    assert not report.passed


def test_trajectory_limit_events_respect_time_window():
    event = LimitEvent(joint_id="joint.a", time_s=2.0, side="upper", event_type="exceeded", position=1.1, limit_position=1.0)
    report = checks.check_trajectory(motion_result=_motion(events=(event,)), maximum_limit_event_count=0, end_time_s=1.0)
    assert report.passed


def test_trajectory_invalid_bounds_are_structured():
    report = checks.check_trajectory(motion_result=_motion(), position_bounds_m={"bad": (0.0, 1.0)})
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TRAJECTORY-BOUNDS-INVALID"
