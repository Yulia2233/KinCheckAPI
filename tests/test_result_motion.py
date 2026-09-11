from __future__ import annotations

from dataclasses import FrozenInstanceError
import json

import pytest

from kincheckapi.assembly import Pose
from kincheckapi.diagnostics import SimIssue
from kincheckapi.errors import KinCheckError
from kincheckapi.result import (
    ConstraintResidual,
    InterferenceEvent,
    InterferenceResult,
    JointState,
    JointTrajectory,
    LimitEvent,
    MotionResult,
    Trajectory,
    list_constraint_residuals,
    list_interference_events,
    list_limit_events,
    read_component_pose,
    read_connector_state,
    read_joint_state,
    read_trajectory,
    summarize_motion,
    write_motion_result,
)


def _trajectory(*, connector_id: str | None = None) -> Trajectory:
    return Trajectory(
        component_id="component.output",
        connector_id=connector_id,
        times_s=(0.0, 1.0, 2.0),
        poses=(
            Pose(position_m=(0.0, 0.0, 0.0)),
            Pose(position_m=(1.0, 2.0, 3.0)),
            Pose(position_m=(2.0, 4.0, 6.0)),
        ),
        linear_velocities_m_s=((1.0, 2.0, 3.0),) * 3,
        angular_velocities_rad_s=((0.0, 0.0, 2.0),) * 3,
        linear_accelerations_m_s2=((0.0, 0.0, 0.0),) * 3,
        angular_accelerations_rad_s2=((0.0, 0.0, 1.0),) * 3,
    )


def _result(*, warning: bool = False) -> MotionResult:
    issue = SimIssue(
        code="KINCHECK-MOTION-WARNING",
        severity="warning",
        stage="kinematics.solve",
        message="A non-blocking condition was detected.",
    )
    return MotionResult(
        scenario_id="scenario.test",
        assembly_id="assembly.test",
        status="completed_with_warnings" if warning else "completed",
        start_time_s=0.0,
        end_time_s=2.0,
        sample_times_s=(0.0, 1.0, 2.0),
        joint_trajectories=(
            JointTrajectory(
                joint_id="joint.output",
                times_s=(0.0, 1.0, 2.0),
                positions=(0.0, 2.0, 4.0),
                velocities=(2.0, 2.0, 2.0),
                accelerations=(0.0, 1.0, 0.0),
            ),
        ),
        trajectories=(_trajectory(), _trajectory(connector_id="axis")),
        constraint_residuals=(
            ConstraintResidual(
                constraint_id="closure.1",
                time_s=1.0,
                position_residual_m=2e-6,
                orientation_residual_rad=3e-6,
            ),
            ConstraintResidual(
                constraint_id="closure.2",
                time_s=2.0,
                position_residual_m=1e-6,
                orientation_residual_rad=1e-6,
            ),
        ),
        limit_events=(
            LimitEvent(
                joint_id="joint.output",
                time_s=2.0,
                side="upper",
                event_type="reached",
                position=4.0,
                limit_position=4.0,
            ),
        ),
        issues=(issue,) if warning else (),
        backend_id="backend.private",
        backend_version="1.0",
        metadata={"z": 2, "a": {"kind": "motion"}},
    )


def test_joint_reader_returns_exact_and_interpolated_samples():
    result = _result()
    exact = read_joint_state(motion_result=result, joint_id="joint.output", time_s=1.0)
    middle = read_joint_state(motion_result=result, joint_id="joint.output", time_s=1.5)
    assert exact == JointState(
        joint_id="joint.output",
        time_s=1.0,
        position=2.0,
        velocity=2.0,
        acceleration=1.0,
    )
    assert middle.position == 3.0
    assert middle.velocity == 2.0
    assert middle.acceleration == 0.5
    assert exact.position_rad_or_m == exact.position
    assert exact.velocity_rad_s_or_m_s == exact.velocity
    assert exact.acceleration_rad_s2_or_m_s2 == exact.acceleration
    assert exact.to_dict()["position"] == 2.0
    trajectory = result.get_joint_trajectory(joint_id="joint.output")
    assert trajectory is not None
    assert trajectory.samples[1] == exact
    assert result.get_joint_trajectory(joint_id="joint.missing") is None


def test_joint_reader_rejects_unknown_joint_and_out_of_range_time():
    result = _result()
    with pytest.raises(KinCheckError) as missing:
        read_joint_state(motion_result=result, joint_id="joint.missing", time_s=1.0)
    assert missing.value.code == "KINCHECK-RESULT-TRAJECTORY-MISSING"
    assert missing.value.report.issues[0].object_ids == ("joint.missing",)
    with pytest.raises(KinCheckError) as outside:
        read_joint_state(motion_result=result, joint_id="joint.output", time_s=3.0)
    assert outside.value.operation == "read_joint_state"


def test_component_and_connector_readers_interpolate_rigid_state():
    result = _result()
    pose = read_component_pose(
        motion_result=result, component_id="component.output", time_s=0.5
    )
    connector = read_connector_state(
        motion_result=result,
        component_id="component.output",
        connector_id="axis",
        time_s=0.5,
    )
    assert pose.position_m == (0.5, 1.0, 1.5)
    assert pose.orientation_xyzw == (0.0, 0.0, 0.0, 1.0)
    assert connector.pose == pose
    assert connector.linear_velocity_m_s == (1.0, 2.0, 3.0)
    assert connector.angular_velocity_rad_s == (0.0, 0.0, 2.0)
    assert connector.angular_acceleration_rad_s2 == (0.0, 0.0, 1.0)
    assert connector.to_dict()["pose"]["position_m"] == [0.5, 1.0, 1.5]


def test_pose_interpolation_uses_short_quaternion_arc_and_normalizes():
    trajectory = Trajectory(
        component_id="component.rotating",
        times_s=(0.0, 1.0),
        poses=(
            Pose(orientation_xyzw=(0.0, 0.0, 0.0, 1.0)),
            Pose(orientation_xyzw=(0.0, 0.0, -0.6, -0.8)),
        ),
    )
    result = MotionResult(
        scenario_id="scenario.rotation",
        assembly_id="assembly.rotation",
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=(0.0, 1.0),
        trajectories=(trajectory,),
    )
    pose = read_component_pose(
        motion_result=result, component_id="component.rotating", time_s=0.5
    )
    assert pose.orientation_xyzw == pytest.approx(
        (0.0, 0.0, 0.31622776601683794, 0.9486832980505138)
    )


def test_trajectory_reader_distinguishes_component_and_connector():
    result = _result()
    assert read_trajectory(
        motion_result=result, component_id="component.output"
    ).connector_id is None
    assert read_trajectory(
        motion_result=result,
        component_id="component.output",
        connector_id="axis",
    ).connector_id == "axis"
    with pytest.raises(KinCheckError) as missing:
        read_trajectory(
            motion_result=result,
            component_id="component.missing",
            connector_id="axis",
        )
    assert missing.value.report.issues[0].object_ids == ("component.missing/axis",)


def test_event_and_residual_readers_filter_without_losing_order():
    result = _result()
    assert len(list_constraint_residuals(motion_result=result)) == 2
    assert list_constraint_residuals(
        motion_result=result, constraint_id="closure.2"
    )[0].position_residual_m == 1e-6
    assert list_constraint_residuals(
        motion_result=result, constraint_id="closure.missing"
    ) == ()
    assert list_limit_events(motion_result=result)[0].joint_id == "joint.output"
    assert list_limit_events(motion_result=result, joint_id="joint.missing") == ()


def test_interference_events_are_typed_sorted_and_backend_independent():
    later = InterferenceEvent(
        component_a_id="a",
        component_b_id="b",
        time_s=2.0,
        penetration_depth_m=0.001,
    )
    earlier = InterferenceEvent(
        component_a_id="c",
        component_b_id="d",
        time_s=1.0,
        penetration_depth_m=0.002,
        position_m=(1.0, 2.0, 3.0),
    )
    result = InterferenceResult(events=(later, earlier))
    assert list_interference_events(interference_result=result) == (earlier, later)
    assert result.to_dict()["events"][0]["position_m"] == [1.0, 2.0, 3.0]
    with pytest.raises(KinCheckError) as invalid:
        list_interference_events(interference_result=object())
    assert invalid.value.code == "KINCHECK-RESULT-QUERY-INVALID"


def test_summary_reports_extrema_residuals_limits_and_warnings():
    summary = summarize_motion(motion_result=_result(warning=True))
    assert summary.status == "completed_with_warnings"
    assert summary.duration_s == 2.0
    assert summary.sample_count == 3
    assert summary.joint_extrema[0].minimum_position == 0.0
    assert summary.joint_extrema[0].maximum_position == 4.0
    assert summary.joint_extrema[0].maximum_absolute_velocity == 2.0
    assert summary.joint_extrema[0].maximum_absolute_acceleration == 1.0
    assert summary.maximum_position_residual_m == 2e-6
    assert summary.maximum_orientation_residual_rad == 3e-6
    assert summary.limit_event_count == 1
    assert summary.warning_count == 1
    assert summary.to_dict()["joint_extrema"][0]["joint_id"] == "joint.output"


def test_motion_result_serializes_deterministically_and_is_immutable(tmp_path):
    result = _result()
    path = tmp_path / "nested" / "motion.json"
    write_motion_result(motion_result=result, path=path)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == result.to_dict()
    assert text.index('"a"') < text.index('"z"')
    with pytest.raises(FrozenInstanceError):
        result.status = "partial"
    with pytest.raises(TypeError):
        result.metadata["a"] = 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"status": "invalid"},
        {"start_time_s": 1.0},
        {"end_time_s": 1.0},
        {"sample_times_s": (0.0, 0.0, 2.0)},
    ],
)
def test_motion_result_rejects_invalid_lifecycle_and_time_axis(kwargs):
    arguments = {
        "scenario_id": "scenario.test",
        "assembly_id": "assembly.test",
        "status": "completed",
        "start_time_s": 0.0,
        "end_time_s": 2.0,
        "sample_times_s": (0.0, 1.0, 2.0),
        **kwargs,
    }
    with pytest.raises(ValueError):
        MotionResult(**arguments)


def test_motion_result_enforces_success_warning_protocol():
    warning = SimIssue(
        code="KINCHECK-WARN",
        severity="warning",
        stage="solve",
        message="warning",
    )
    error = SimIssue(
        code="KINCHECK-ERROR",
        severity="error",
        stage="solve",
        message="error",
    )
    common = {
        "scenario_id": "scenario.test",
        "assembly_id": "assembly.test",
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "sample_times_s": (0.0, 1.0),
    }
    with pytest.raises(ValueError, match="cannot contain"):
        MotionResult(status="completed", issues=(warning,), **common)
    with pytest.raises(ValueError, match="requires warnings"):
        MotionResult(status="completed_with_warnings", issues=(), **common)
    with pytest.raises(ValueError, match="cannot contain errors"):
        MotionResult(status="completed_with_warnings", issues=(warning, error), **common)
    assert MotionResult(status="partial", issues=(error,), **common).status == "partial"


@pytest.mark.parametrize(
    "constructor,kwargs",
    [
        (
            JointTrajectory,
            {
                "joint_id": "joint.1",
                "times_s": (0.0, 1.0),
                "positions": (0.0,),
                "velocities": (0.0, 0.0),
                "accelerations": (0.0, 0.0),
            },
        ),
        (
            Trajectory,
            {
                "component_id": "component.1",
                "times_s": (0.0, 1.0),
                "poses": (Pose(),),
            },
        ),
        (
            ConstraintResidual,
            {
                "constraint_id": "constraint.1",
                "time_s": 0.0,
                "position_residual_m": -1.0,
                "orientation_residual_rad": 0.0,
            },
        ),
        (
            LimitEvent,
            {
                "joint_id": "joint.1",
                "time_s": 0.0,
                "side": "middle",
                "event_type": "reached",
                "position": 0.0,
                "limit_position": 0.0,
            },
        ),
    ],
)
def test_result_models_reject_malformed_samples(constructor, kwargs):
    with pytest.raises(ValueError):
        constructor(**kwargs)


def test_trajectory_preserves_missing_vector_channels_as_unknown():
    trajectory = Trajectory(
        component_id="component.1",
        times_s=(0.0, 1.0),
        poses=(Pose(), Pose()),
    )
    assert trajectory.linear_velocities_m_s is None
    assert trajectory.angular_accelerations_rad_s2 is None


@pytest.mark.parametrize(
    "constructor,kwargs,error",
    [
        (
            JointState,
            {
                "joint_id": "",
                "time_s": 0.0,
                "position": 0.0,
                "velocity": 0.0,
                "acceleration": 0.0,
            },
            ValueError,
        ),
        (
            JointState,
            {
                "joint_id": "joint.1",
                "time_s": float("nan"),
                "position": 0.0,
                "velocity": 0.0,
                "acceleration": 0.0,
            },
            ValueError,
        ),
        (
            Trajectory,
            {"component_id": "component.1", "times_s": (), "poses": ()},
            ValueError,
        ),
        (
            Trajectory,
            {
                "component_id": "component.1",
                "times_s": (0.0, 1.0),
                "poses": (Pose(), Pose()),
                "linear_velocities_m_s": ((0.0, 0.0, 0.0),),
            },
            ValueError,
        ),
        (
            Trajectory,
            {
                "component_id": "component.1",
                "times_s": (0.0,),
                "poses": (Pose(),),
                "linear_velocities_m_s": ((0.0, 0.0),),
            },
            ValueError,
        ),
        (
            InterferenceEvent,
            {
                "component_a_id": "same",
                "component_b_id": "same",
                "time_s": 0.0,
                "penetration_depth_m": 0.0,
            },
            ValueError,
        ),
        (
            InterferenceEvent,
            {
                "component_a_id": "a",
                "component_b_id": "b",
                "time_s": -1.0,
                "penetration_depth_m": 0.0,
            },
            ValueError,
        ),
        (
            InterferenceResult,
            {"events": (object(),)},
            TypeError,
        ),
    ],
)
def test_result_models_reject_nonfinite_misaligned_and_ambiguous_data(
    constructor, kwargs, error
):
    with pytest.raises(error):
        constructor(**kwargs)


def test_motion_result_accepts_backend_mapping_and_rejects_duplicate_ids():
    trajectory = JointTrajectory(
        joint_id="joint.1",
        times_s=(0.0, 1.0),
        positions=(0.0, 1.0),
        velocities=(1.0, 1.0),
        accelerations=(0.0, 0.0),
    )
    common = {
        "scenario_id": "scenario.1",
        "assembly_id": "assembly.1",
        "status": "completed",
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "sample_times_s": (0.0, 1.0),
    }
    result = MotionResult(joint_trajectories={"joint.1": trajectory}, **common)
    assert result.joint_trajectories.get("joint.1") is trajectory
    with pytest.raises(ValueError, match="unique Joint"):
        MotionResult(joint_trajectories=(trajectory, trajectory), **common)
    with pytest.raises(TypeError, match="JointTrajectory"):
        MotionResult(joint_trajectories=(object(),), **common)


def test_motion_result_rejects_duplicate_component_connector_trajectories():
    trajectory = _trajectory()
    with pytest.raises(ValueError, match="unique component"):
        MotionResult(
            scenario_id="scenario.1",
            assembly_id="assembly.1",
            status="completed",
            start_time_s=0.0,
            end_time_s=2.0,
            sample_times_s=(0.0, 1.0, 2.0),
            trajectories=(trajectory, trajectory),
        )
