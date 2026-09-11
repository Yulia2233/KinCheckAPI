from __future__ import annotations

import json

import pytest

from kincheckapi.assembly import (
    AssemblyModel,
    ConnectorRef,
    Joint,
    JointLimit,
    JointType,
)
from kincheckapi.checks import (
    CheckReport,
    CheckSpec,
    check_constraint_residuals,
    check_joint_limits,
    check_pose_target,
    check_trajectory,
    check_transmission_ratio,
    run_checks,
)
from kincheckapi.errors import BackendCapabilityError
from kincheckapi.pose import Pose
from kincheckapi.result import Trajectory
from kincheckapi.result import ConstraintResidual, JointTrajectory, MotionResult


def _joint_trajectory(
    joint_id: str,
    *,
    times: tuple[float, ...] = (0.0, 1.0, 2.0, 3.0),
    positions: tuple[float, ...] = (0.0, 1.0, 2.0, 3.0),
    velocities: tuple[float, ...] = (1.0, 1.0, 1.0, 1.0),
) -> JointTrajectory:
    return JointTrajectory(
        joint_id=joint_id,
        times_s=times,
        positions=positions,
        velocities=velocities,
        accelerations=(0.0,) * len(times),
    )


def _motion(
    *,
    trajectories: tuple[JointTrajectory, ...] = (),
    residuals: tuple[ConstraintResidual, ...] = (),
    closures: tuple[ConstraintResidual, ...] = (),
    assembly_id: str = "assembly.checks",
) -> MotionResult:
    return MotionResult(
        scenario_id="scenario.checks",
        assembly_id=assembly_id,
        status="completed",
        start_time_s=0.0,
        end_time_s=3.0,
        sample_times_s=(0.0, 1.0, 2.0, 3.0),
        joint_trajectories=trajectories,
        constraint_residuals=residuals,
        closure_residuals=closures,
    )


def _residual(
    constraint_id: str,
    time_s: float,
    position: float,
    orientation: float = 0.0,
) -> ConstraintResidual:
    return ConstraintResidual(
        constraint_id=constraint_id,
        time_s=time_s,
        position_residual_m=position,
        orientation_residual_rad=orientation,
    )


def _joint(
    joint_id: str,
    *,
    limit: JointLimit | None,
) -> Joint:
    return Joint(
        joint_id=joint_id,
        joint_type=JointType.REVOLUTE,
        connector_a=ConnectorRef(component_id="component.a", connector_id="axis"),
        connector_b=ConnectorRef(component_id="component.b", connector_id="axis"),
        limit=limit,
    )


def _assembly(*joints: Joint, assembly_id: str = "assembly.checks") -> AssemblyModel:
    return AssemblyModel(assembly_id=assembly_id, joints=tuple(joints))


def _evidence(report: CheckReport) -> dict[str, object]:
    return {item.key: item.actual for item in report.evidence}


# Constraint residual checks: 7 behavior cases.


def test_constraint_residuals_pass_and_emit_aggregate_evidence():
    motion = _motion(
        residuals=(
            _residual("constraint.a", 0.0, 1e-7, 2e-7),
            _residual("constraint.a", 1.0, 2e-7, 3e-7),
        )
    )
    report = check_constraint_residuals(motion_result=motion)
    assert report.passed
    assert _evidence(report)["sample_count"] == 2
    assert _evidence(report)["maximum_orientation_residual_rad"] == 3e-7


def test_constraint_residuals_include_closures_by_default():
    motion = _motion(closures=(_residual("closure.a", 1.0, 2e-6),))
    report = check_constraint_residuals(motion_result=motion)
    assert not report.passed
    assert report.issues[-1].object_ids == ("closure.a",)


def test_constraint_residual_violation_reports_first_failure_and_maxima():
    motion = _motion(
        residuals=(
            _residual("constraint.a", 1.0, 3e-6, 1e-7),
            _residual("constraint.a", 2.0, 2e-7, 4e-6),
        )
    )
    report = check_constraint_residuals(motion_result=motion)
    issue = next(
        item
        for item in report.issues
        if item.code == "KINCHECK-CHECK-CONSTRAINT-RESIDUAL-EXCEEDED"
    )
    assert issue.failure_time_s == 1.0
    assert {item.key: item.actual for item in issue.evidence} == {
        "maximum_position_residual_m": 3e-6,
        "maximum_orientation_residual_rad": 4e-6,
        "violating_sample_count": 2,
    }


def test_constraint_residual_selection_reports_unknown_id():
    motion = _motion(residuals=(_residual("constraint.a", 0.0, 0.0),))
    report = check_constraint_residuals(
        motion_result=motion, constraint_ids=("constraint.missing",)
    )
    assert not report.passed
    assert "KINCHECK-CHECK-CONSTRAINT-NOT-FOUND" in {
        item.code for item in report.issues
    }


def test_constraint_residual_window_uses_only_selected_times():
    motion = _motion(
        residuals=(
            _residual("constraint.a", 0.0, 5e-6),
            _residual("constraint.a", 2.0, 0.0),
        )
    )
    report = check_constraint_residuals(
        motion_result=motion, start_time_s=1.0, end_time_s=3.0
    )
    assert report.passed
    assert _evidence(report)["sample_count"] == 1


@pytest.mark.parametrize(
    "kwargs, code",
    [
        ({"position_tolerance_m": -1.0}, "KINCHECK-CHECK-CONSTRAINT-TOLERANCE-INVALID"),
        ({"start_time_s": 2.0, "end_time_s": 1.0}, "KINCHECK-CHECK-TIME-WINDOW-INVALID"),
    ],
)
def test_constraint_residuals_reject_invalid_settings(kwargs, code):
    report = check_constraint_residuals(
        motion_result=_motion(residuals=(_residual("constraint.a", 1.0, 0.0),)),
        **kwargs,
    )
    assert not report.passed
    assert code in {item.code for item in report.issues}


def test_constraint_report_is_deterministic_json_and_metadata_is_frozen():
    report = check_constraint_residuals(
        motion_result=_motion(residuals=(_residual("constraint.a", 1.0, 0.0),)),
        constraint_ids=("constraint.a",),
        check_id="check.constraint.a",
    )
    assert json.dumps(report.to_dict(), sort_keys=True) == json.dumps(
        report.to_dict(), sort_keys=True
    )
    with pytest.raises(TypeError):
        report.metadata["start_time_s"] = 2.0


# Joint limit checks: 7 behavior cases.


def test_joint_limits_accept_boundary_samples():
    assembly = _assembly(_joint("joint.a", limit=JointLimit(lower=-1.0, upper=1.0)))
    motion = _motion(
        trajectories=(
            _joint_trajectory(
                "joint.a", positions=(-1.0, -0.5, 0.5, 1.0)
            ),
        )
    )
    report = check_joint_limits(assembly=assembly, motion_result=motion)
    assert report.passed
    assert _evidence(report)["checked_joint_count"] == 1


def test_joint_limits_report_first_exceeded_sample():
    assembly = _assembly(_joint("joint.a", limit=JointLimit(lower=-1.0, upper=1.0)))
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.a", positions=(0.0, 1.1, -1.2, 0.0)),
        )
    )
    report = check_joint_limits(assembly=assembly, motion_result=motion)
    issue = report.issues[0]
    assert issue.code == "KINCHECK-CHECK-JOINT-LIMIT-EXCEEDED"
    assert issue.failure_time_s == 1.0


def test_joint_limit_tolerance_is_applied_to_both_sides():
    assembly = _assembly(_joint("joint.a", limit=JointLimit(lower=-1.0, upper=1.0)))
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.a", positions=(0.0, 1.01, -1.01, 0.0)),
        )
    )
    report = check_joint_limits(
        assembly=assembly, motion_result=motion, tolerance=0.02
    )
    assert report.passed


@pytest.mark.parametrize(
    "joint_ids, expected_code",
    [
        (("joint.missing",), "KINCHECK-CHECK-JOINT-NOT-FOUND"),
        (("joint.free",), "KINCHECK-CHECK-JOINT-LIMIT-NOT-AUTHORED"),
    ],
)
def test_joint_limit_selection_reports_uncheckable_joints(joint_ids, expected_code):
    assembly = _assembly(_joint("joint.free", limit=None))
    report = check_joint_limits(
        assembly=assembly, motion_result=_motion(), joint_ids=joint_ids
    )
    assert expected_code in {item.code for item in report.issues}


def test_joint_limits_fail_when_requested_trajectory_is_missing():
    assembly = _assembly(_joint("joint.a", limit=JointLimit(lower=-1.0, upper=1.0)))
    report = check_joint_limits(assembly=assembly, motion_result=_motion())
    assert report.issues[0].code == "KINCHECK-CHECK-JOINT-TRAJECTORY-NOT-FOUND"


def test_joint_limit_window_can_exclude_an_earlier_violation():
    assembly = _assembly(_joint("joint.a", limit=JointLimit(lower=-1.0, upper=1.0)))
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.a", positions=(2.0, 0.0, 0.0, 0.0)),
        )
    )
    report = check_joint_limits(
        assembly=assembly, motion_result=motion, start_time_s=1.0
    )
    assert report.passed


def test_joint_limits_detect_assembly_mismatch_and_allow_no_authored_limits():
    mismatch = check_joint_limits(
        assembly=_assembly(assembly_id="assembly.other"), motion_result=_motion()
    )
    assert "KINCHECK-CHECK-ASSEMBLY-MISMATCH" in {
        item.code for item in mismatch.issues
    }
    no_limits = check_joint_limits(
        assembly=_assembly(_joint("joint.free", limit=None)),
        motion_result=_motion(),
    )
    assert no_limits.passed
    assert _evidence(no_limits)["limited_joint_count"] == 0


# Transmission ratio checks: 10 behavior cases.


def test_velocity_ratio_passes_and_reports_all_statistics():
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", velocities=(20.0,) * 4),
            _joint_trajectory("joint.output", velocities=(1.0,) * 4),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=20.0,
        expected_direction="same",
    )
    evidence = _evidence(report)
    assert report.passed
    assert evidence["median_ratio"] == 20.0
    assert evidence["p95_relative_error"] == 0.0
    assert evidence["ratio_standard_deviation"] == 0.0
    assert evidence["direction_consistency"] == 1.0


def test_opposite_direction_ratio_passes_when_explicitly_expected():
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", velocities=(4.0,) * 4),
            _joint_trajectory("joint.output", velocities=(-2.0,) * 4),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=2.0,
        expected_direction="opposite",
    )
    assert report.passed
    assert _evidence(report)["measured_direction"] == "opposite"


def test_ratio_interpolates_different_time_axes():
    input_curve = _joint_trajectory(
        "joint.input",
        times=(0.0, 1.0, 2.0, 3.0),
        velocities=(10.0, 10.0, 10.0, 10.0),
    )
    output_curve = _joint_trajectory(
        "joint.output",
        times=(0.0, 0.5, 1.5, 2.5, 3.0),
        positions=(0.0, 0.25, 0.75, 1.25, 1.5),
        velocities=(2.0, 2.0, 2.0, 2.0, 2.0),
    )
    report = check_transmission_ratio(
        motion_result=_motion(trajectories=(input_curve, output_curve)),
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=5.0,
        expected_direction="same",
    )
    assert report.passed
    assert _evidence(report)["candidate_sample_count"] == 7


def test_displacement_ratio_removes_initial_position_offsets():
    input_curve = _joint_trajectory(
        "joint.input", positions=(100.0, 110.0, 120.0, 130.0)
    )
    output_curve = _joint_trajectory(
        "joint.output", positions=(-50.0, -48.0, -46.0, -44.0)
    )
    report = check_transmission_ratio(
        motion_result=_motion(trajectories=(input_curve, output_curve)),
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=5.0,
        expected_direction="same",
        measurement="angular_displacement",
    )
    assert report.passed
    assert _evidence(report)["median_ratio"] == 5.0


@pytest.mark.parametrize(
    "measurement",
    ["linear_velocity", "linear_displacement"],
)
def test_linear_measurement_aliases_use_the_same_scalar_curve(measurement):
    motion = _motion(
        trajectories=(
            _joint_trajectory(
                "joint.input",
                positions=(5.0, 7.0, 9.0, 11.0),
                velocities=(2.0,) * 4,
            ),
            _joint_trajectory(
                "joint.output",
                positions=(8.0, 9.0, 10.0, 11.0),
                velocities=(1.0,) * 4,
            ),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=2.0,
        expected_direction="same",
        measurement=measurement,
    )
    assert report.passed


def test_ratio_variation_fails_p95_even_when_median_is_correct():
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", velocities=(10.0, 10.0, 10.0, 20.0)),
            _joint_trajectory("joint.output", velocities=(1.0,) * 4),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=10.0,
        expected_direction="same",
        relative_tolerance=0.01,
    )
    assert not report.passed
    assert "KINCHECK-CHECK-RATIO-MISMATCH" in {item.code for item in report.issues}


def test_direction_reversal_fails_consistency_requirement():
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", velocities=(4.0,) * 4),
            _joint_trajectory("joint.output", velocities=(2.0, 2.0, -2.0, -2.0)),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=2.0,
        expected_direction="same",
    )
    assert not report.passed
    assert "KINCHECK-CHECK-RATIO-DIRECTION-MISMATCH" in {
        item.code for item in report.issues
    }


def test_near_zero_samples_are_rejected_and_can_fail_valid_fraction():
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", velocities=(2.0,) * 4),
            _joint_trajectory("joint.output", velocities=(1.0, 0.0, 0.0, 1.0)),
        )
    )
    report = check_transmission_ratio(
        motion_result=motion,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=2.0,
        expected_direction="same",
        minimum_sample_count=2,
        minimum_valid_fraction=0.75,
    )
    assert not report.passed
    assert _evidence(report)["rejected_sample_count"] == 2
    assert "KINCHECK-CHECK-RATIO-INSUFFICIENT-SAMPLES" in {
        item.code for item in report.issues
    }


def test_ratio_reports_missing_trajectory_and_nonoverlapping_curves():
    missing = check_transmission_ratio(
        motion_result=_motion(
            trajectories=(_joint_trajectory("joint.input"),)
        ),
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=1.0,
        expected_direction="same",
    )
    assert missing.issues[0].code == "KINCHECK-CHECK-RATIO-TRAJECTORY-NOT-FOUND"
    nonoverlap = check_transmission_ratio(
        motion_result=_motion(
            trajectories=(
                _joint_trajectory(
                    "joint.input",
                    times=(0.0, 0.5, 1.0),
                    positions=(0.0, 0.5, 1.0),
                    velocities=(1.0, 1.0, 1.0),
                ),
                _joint_trajectory(
                    "joint.output",
                    times=(2.0, 2.5, 3.0),
                    positions=(2.0, 2.5, 3.0),
                    velocities=(1.0, 1.0, 1.0),
                ),
            )
        ),
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=1.0,
        expected_direction="same",
    )
    assert "KINCHECK-CHECK-RATIO-NO-TIME-OVERLAP" in {
        item.code for item in nonoverlap.issues
    }


@pytest.mark.parametrize(
    "kwargs, expected_code",
    [
        ({"expected_ratio": 0.0}, "KINCHECK-CHECK-RATIO-PARAMETER-INVALID"),
        ({"expected_direction": "sideways"}, "KINCHECK-CHECK-RATIO-DIRECTION-INVALID"),
        ({"measurement": "angular_acceleration"}, "KINCHECK-CHECK-RATIO-MEASUREMENT-UNSUPPORTED"),
        ({"minimum_sample_count": 0}, "KINCHECK-CHECK-RATIO-PARAMETER-INVALID"),
        ({"minimum_valid_fraction": 2.0}, "KINCHECK-CHECK-RATIO-PARAMETER-INVALID"),
    ],
)
def test_ratio_rejects_invalid_explicit_configuration(kwargs, expected_code):
    arguments = {
        "motion_result": _motion(
            trajectories=(
                _joint_trajectory("joint.input"),
                _joint_trajectory("joint.output"),
            )
        ),
        "input_joint_id": "joint.input",
        "output_joint_id": "joint.output",
        "expected_ratio": 1.0,
        "expected_direction": "same",
    }
    arguments.update(kwargs)
    report = check_transmission_ratio(**arguments)
    assert not report.passed
    assert expected_code in {item.code for item in report.issues}


# Unified execution: 5 behavior cases.


def test_run_checks_aggregates_reports_and_failure_issues_in_order():
    assembly = _assembly(_joint("joint.input", limit=JointLimit(lower=-2.0, upper=2.0)))
    motion = _motion(
        trajectories=(
            _joint_trajectory("joint.input", positions=(0.0, 0.0, 0.0, 0.0), velocities=(2.0,) * 4),
            _joint_trajectory("joint.output", velocities=(1.0,) * 4),
        ),
        residuals=(_residual("constraint.a", 1.0, 2e-6),),
    )
    suite = run_checks(
        assembly=assembly,
        motion_result=motion,
        checks=(
            CheckSpec(check_id="limits", check_type="joint_limits"),
            CheckSpec(check_id="residuals", check_type="constraint_residuals"),
            CheckSpec(
                check_id="ratio",
                check_type="transmission_ratio",
                parameters={
                    "input_joint_id": "joint.input",
                    "output_joint_id": "joint.output",
                    "expected_ratio": 2.0,
                    "expected_direction": "same",
                },
            ),
        ),
    )
    assert [item.check_id for item in suite.reports] == ["limits", "residuals", "ratio"]
    assert not suite.passed
    assert len(suite.issues) == 1


def test_run_checks_records_context_and_has_deterministic_json():
    suite = run_checks(assembly=_assembly(), motion_result=_motion(), checks=())
    assert suite.passed
    assert suite.metadata["assembly_id"] == "assembly.checks"
    assert suite.metadata["check_count"] == 0
    json.dumps(suite.to_dict(), sort_keys=True)


def test_run_checks_reports_missing_motion_result_without_throwing():
    suite = run_checks(
        assembly=_assembly(),
        checks=(CheckSpec(check_id="limits", check_type="joint_limits"),),
    )
    assert not suite.passed
    assert suite.issues[0].code == "KINCHECK-CHECK-MOTION-RESULT-REQUIRED"


def test_run_checks_reports_unsupported_type_without_guessing():
    suite = run_checks(
        assembly=_assembly(),
        motion_result=_motion(),
        checks=(CheckSpec(check_id="mystery", check_type="guess_me"),),
    )
    assert not suite.passed
    assert suite.issues[0].code == "KINCHECK-CHECK-TYPE-UNSUPPORTED"


def test_run_checks_rejects_duplicate_ids_and_non_specs():
    with pytest.raises(ValueError, match="unique"):
        run_checks(
            assembly=_assembly(),
            checks=(
                CheckSpec(check_id="duplicate", check_type="joint_limits"),
                CheckSpec(check_id="duplicate", check_type="constraint_residuals"),
            ),
        )
    with pytest.raises(TypeError, match="CheckSpec"):
        run_checks(assembly=_assembly(), checks=(object(),))


# Pose and trajectory checks: the v0.2.1 implementations use explicit result data.


def _component_motion() -> MotionResult:
    return MotionResult(
        scenario_id="scenario.pose",
        assembly_id="assembly.checks",
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=(0.0, 1.0),
        trajectories=(
            Trajectory(
                component_id="component.a",
                times_s=(0.0, 1.0),
                poses=(Pose(), Pose()),
                linear_velocities_m_s=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                angular_velocities_rad_s=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                linear_accelerations_m_s2=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                angular_accelerations_rad_s2=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            ),
        ),
    )


def test_pose_target_check_passes_for_matching_recorded_pose():
    report = check_pose_target(
        motion_result=_component_motion(),
        target={"component_id": "component.a", "pose": Pose()},
    )
    assert report.passed


def test_pose_target_check_rejects_mismatch():
    report = check_pose_target(
        motion_result=_component_motion(),
        target={"component_id": "component.a", "pose": Pose(position_m=(1.0, 0.0, 0.0))},
    )
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-POSE-TARGET-MISMATCH"


def test_pose_target_check_requires_target():
    report = check_pose_target(motion_result=_component_motion())
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-POSE-TARGET-EMPTY"


def test_trajectory_check_passes_for_recorded_space_fields():
    report = check_trajectory(
        motion_result=_component_motion(), component_id="component.a", max_speed_m_s=1.0
    )
    assert report.passed


def test_trajectory_check_reports_missing_object():
    report = check_trajectory(
        motion_result=_component_motion(), component_id="component.missing"
    )
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-RESULT-TRAJECTORY-MISSING"


def test_trajectory_check_reports_invalid_time_window():
    report = check_trajectory(
        motion_result=_component_motion(), start_time_s=1.0, end_time_s=0.0
    )
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CHECK-TIME-WINDOW-INVALID"
