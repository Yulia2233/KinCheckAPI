from __future__ import annotations

from kincheckapi import checks, kinematics
from kincheckapi.assembly import AssemblyModel, ConnectorRef, Joint, JointLimit
from kincheckapi.diagnostics import DiagnosticReport
from kincheckapi.pose import Pose
from kincheckapi.result import (
    ConstraintEquationResidual,
    ConstraintResidual,
    JointTrajectory,
    MotionResult,
    Trajectory,
)


TIMES = (0.0, 1.0, 2.0)


def _assembly() -> AssemblyModel:
    return AssemblyModel(
        assembly_id="assembly.v031.partial",
        joints=(
            Joint(
                joint_id="joint.a",
                joint_type="revolute",
                connector_a=ConnectorRef(component_id="base", connector_id="axis"),
                connector_b=ConnectorRef(component_id="moving", connector_id="axis"),
                limit=JointLimit(lower=-1.0, upper=1.0),
            ),
        ),
    )


def _motion() -> MotionResult:
    return MotionResult(
        scenario_id="scenario.v031.partial",
        assembly_id="assembly.v031.partial",
        status="partial",
        start_time_s=TIMES[0],
        end_time_s=TIMES[-1],
        sample_times_s=TIMES,
        joint_trajectories=(
            JointTrajectory(
                joint_id="joint.a",
                times_s=TIMES,
                positions=(0.0, 0.1, 0.2),
                velocities=(0.1, 0.1, 0.1),
                accelerations=(0.0, 0.0, 0.0),
            ),
        ),
        trajectories=(
            Trajectory(
                component_id="moving",
                connector_id="tip",
                times_s=TIMES,
                poses=(
                    Pose(position_m=(0.0, 0.0, 0.0)),
                    Pose(position_m=(0.1, 0.0, 0.0)),
                    Pose(position_m=(0.2, 0.0, 0.0)),
                ),
                linear_velocities_m_s=((0.1, 0.0, 0.0),) * 3,
                angular_velocities_rad_s=((0.0, 0.0, 0.0),) * 3,
                linear_accelerations_m_s2=((0.0, 0.0, 0.0),) * 3,
                angular_accelerations_rad_s2=((0.0, 0.0, 0.0),) * 3,
            ),
        ),
        constraint_residuals=(
            ConstraintResidual(
                constraint_id="constraint.a",
                time_s=1.0,
                position_residual_m=1e-8,
                orientation_residual_rad=1e-8,
            ),
        ),
        constraint_equation_residuals=(
            ConstraintEquationResidual(
                constraint_id="equation.a",
                time_s=1.0,
                value=1e-10,
                unit="m",
                equation_type="gear",
            ),
        ),
        closure_residuals=(
            ConstraintResidual(
                constraint_id="closure.a",
                time_s=1.0,
                position_residual_m=1e-8,
                orientation_residual_rad=1e-8,
            ),
        ),
        closure_statuses={"closure.a": "passed"},
    )


def _assert_incomplete(report) -> None:
    assert not report.passed
    assert report.severity == "error"
    assert any(
        issue.code == "KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE"
        for issue in report.issues
    )


def test_partial_pose_check_fails_but_keeps_pose_samples():
    report = checks.check_pose_target(
        motion_result=_motion(),
        target={
            "component_id": "moving",
            "connector_id": "tip",
            "pose": Pose(position_m=(0.1, 0.0, 0.0)),
            "time_s": 1.0,
        },
    )
    _assert_incomplete(report)
    assert {item.key: item.actual for item in report.evidence}["sample_count"] == 1


def test_partial_trajectory_check_fails_but_keeps_range_evidence():
    report = checks.check_trajectory(
        motion_result=_motion(), component_id="moving", connector_id="tip"
    )
    _assert_incomplete(report)
    evidence = {item.key: item.actual for item in report.evidence}
    assert evidence["sample_count"] == 3
    assert evidence["maximum_path_length_m"] == 0.2


def test_partial_residual_equation_and_limit_checks_all_fail_with_evidence():
    motion = _motion()
    reports = (
        checks.check_constraint_residuals(motion_result=motion),
        checks.check_constraint_equation_residuals(motion_result=motion),
        checks.check_joint_limits(assembly=_assembly(), motion_result=motion),
    )
    for report in reports:
        _assert_incomplete(report)
        assert any(item.key == "sample_count" for item in report.evidence)


def test_partial_transmission_check_still_measures_recorded_prefix():
    motion = _motion()
    report = checks.check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.a",
        output_joint_id="joint.a",
        expected_ratio=1.0,
        expected_direction="same",
    )
    _assert_incomplete(report)
    evidence = {item.key: item.actual for item in report.evidence}
    assert evidence["valid_sample_count"] == 3
    assert evidence["median_ratio"] == 1.0


def test_run_checks_aggregates_partial_failures_in_order():
    motion = _motion()
    suite = checks.run_checks(
        assembly=_assembly(),
        motion_result=motion,
        checks=(
            checks.CheckSpec(check_id="residual", check_type="constraint_residuals"),
            checks.CheckSpec(
                check_id="trajectory",
                check_type="trajectory",
                parameters={"component_id": "moving", "connector_id": "tip"},
            ),
        ),
    )
    assert not suite.passed
    assert [item.check_id for item in suite.reports] == ["residual", "trajectory"]
    assert all(not item.passed for item in suite.reports)


def test_partial_closure_and_path_results_keep_recorded_evidence():
    motion = _motion()
    closure = kinematics.validate_closures(motion_result=motion)
    path = kinematics.trace_connector_path(
        motion_result=motion, component_id="moving", connector_id="tip"
    )
    assert closure is not None and not closure.passed
    assert len(closure.residuals) == 1
    assert not path.passed
    assert path.times_s == TIMES
    assert path.path_length_m == 0.2


def test_partial_solve_attempt_uses_last_valid_result_only():
    motion = _motion()
    attempt = kinematics.SolveAttempt(
        status="partial",
        succeeded=False,
        motion_result=None,
        last_valid_result=motion,
        report=DiagnosticReport(last_valid_result=motion),
        failure=None,
    )
    assert not attempt.succeeded
    assert attempt.motion_result is None
    assert attempt.last_valid_result is motion


def test_partial_checks_are_deterministic():
    first = checks.check_trajectory(
        motion_result=_motion(), component_id="moving", connector_id="tip"
    ).to_dict()
    second = checks.check_trajectory(
        motion_result=_motion(), component_id="moving", connector_id="tip"
    ).to_dict()
    assert first == second
