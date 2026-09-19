from __future__ import annotations

import pytest

from kincheckapi import checks, kinematics, scenario
from kincheckapi.diagnostics import diagnostic_trace
from kincheckapi.motion_contracts import (
    CoordinatedMotionProfile,
    PathTarget,
    PlanarPose,
    PosePoint,
    PoseTrajectory,
)
from kincheckapi.pose import Pose
from kincheckapi.result import JointTrajectory, MotionResult, Trajectory


def _motion() -> MotionResult:
    component = Trajectory(
        component_id="tool",
        times_s=(0.0, 1.0, 2.0),
        poses=(
            Pose(position_m=(0.0, 0.0, 0.0)),
            Pose(position_m=(0.5, 0.0, 0.0)),
            Pose(position_m=(1.0, 0.0, 0.0)),
        ),
    )
    joint = JointTrajectory(
        joint_id="j",
        times_s=(0.0, 1.0, 2.0),
        positions=(0.0, 1.0, 0.0),
        velocities=(0.0, 1.0, -1.0),
        accelerations=(0.0, 0.0, 0.0),
    )
    return MotionResult(
        scenario_id="s", assembly_id="a", status="completed",
        start_time_s=0.0, end_time_s=2.0, sample_times_s=(0.0, 1.0, 2.0),
        trajectories=(component,), joint_trajectories=(joint,),
    )


def test_path_and_planar_checks_use_recorded_samples():
    motion = _motion()
    path = checks.check_path_tracking(
        motion_result=motion, component_id="tool",
        path_target=PathTarget(points_m=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))),
    )
    assert path.passed
    planar = checks.check_planar_tracking(
        motion_result=motion, component_id="tool",
        target=PoseTrajectory(
            target="tool",
            points=tuple(
                PosePoint(time_s=time_s, pose=pose)
                for time_s, pose in zip(motion.sample_times_s, motion.trajectories[0].poses)
            ),
        ),
    )
    assert planar.passed
    pose_report = checks.check_pose_trajectory(
        motion_result=motion, target=PoseTrajectory(
            target="tool",
            points=tuple(PosePoint(time_s=time_s, pose=pose) for time_s, pose in zip(motion.sample_times_s, motion.trajectories[0].poses)),
        ),
    )
    assert pose_report.passed


def test_planar_tracking_accepts_mapping_sequence_and_structures_invalid_targets():
    trajectory = _motion().trajectories[0]
    report = checks.check_planar_tracking(
        trajectory=trajectory,
        target=(
            {"time_s": 0.0, "x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0},
            {"time_s": 1.0, "x_m": 0.5, "y_m": 0.0, "yaw_rad": 0.0},
            {"time_s": 2.0, "x_m": 1.0, "y_m": 0.0, "yaw_rad": 0.0},
        ),
    )
    assert report.passed

    invalid = checks.check_planar_tracking(
        trajectory=trajectory,
        target=({"time_s": 0.0, "x_m": 0.0},),
    )
    assert not invalid.passed
    assert invalid.issues[0].code == "KINCHECK-CHECK-PLANAR-TARGET-INVALID"


def test_run_checks_structures_planar_parameter_errors():
    from kincheckapi.assembly import AssemblyModel

    suite = checks.run_checks(
        assembly=AssemblyModel(assembly_id="a", parts=(), components=()),
        motion_result=_motion(),
        checks=(
            checks.CheckSpec(
                check_id="planar",
                check_type="planar_tracking",
                parameters={
                    "trajectory": _motion().trajectories[0],
                    "target": ({"time_s": 0.0, "x_m": 0.0},),
                },
            ),
        ),
    )
    assert not suite.passed
    assert suite.reports[0].issues[0].code == "KINCHECK-CHECK-PLANAR-TARGET-INVALID"


def test_path_failure_reports_first_time_and_json():
    report = checks.check_path_tracking(
        trajectory=_motion().trajectories[0],
        path_target=PathTarget(points_m=((0.0, 1.0, 0.0), (1.0, 1.0, 0.0))),
        position_tolerance_m=0.01,
    )
    payload = report.to_dict()
    assert not report.passed
    assert payload["failure_time_s"] == 0.0
    assert payload["issues"][0]["code"] == "KINCHECK-CHECK-PATH-TRACKING-FAILED"
    assert "traceback" not in payload


def test_start_stop_reversal_does_not_call_initial_zero_a_stop():
    report = checks.check_start_stop_reversal(motion_result=_motion(), joint_id="j")
    assert not report.passed
    assert report.metadata["reversal_count"] == 1
    assert any(issue.code == "KINCHECK-CHECK-STOP-NOT-DETECTED" for issue in report.issues)


def test_periodic_check_requires_the_requested_number_of_periods():
    report = checks.check_periodic_motion(
        motion_result=_motion(), joint_id="j", period_s=2.0, periods=2
    )
    assert not report.passed
    assert any(issue.code == "KINCHECK-CHECK-PERIODIC-TIME-WINDOW-TOO-SHORT" for issue in report.issues)
    periodic = _motion()
    periodic = MotionResult(
        scenario_id=periodic.scenario_id, assembly_id=periodic.assembly_id,
        status=periodic.status, start_time_s=periodic.start_time_s,
        end_time_s=periodic.end_time_s, sample_times_s=periodic.sample_times_s,
        trajectories=periodic.trajectories,
        joint_trajectories=(JointTrajectory(
            joint_id="j", times_s=(0.0, 1.0, 2.0), positions=(0.0, 1.0, 0.0),
            velocities=(0.0, 1.0, 0.0), accelerations=(0.0, 0.0, 0.0),
        ),),
    )
    assert checks.check_periodic_motion(
        motion_result=periodic, joint_id="j", period_s=2.0
    ).passed


def test_synchronization_requires_explicit_target():
    target = CoordinatedMotionProfile(
        axes={"j": (0.0, 1.0, 0.0)}, times_s=(0.0, 1.0, 2.0)
    )
    report = checks.check_synchronization(
        motion_result=_motion(), joint_ids=("j",), target=target
    )
    assert report.passed
    missing = checks.check_synchronization(
        motion_result=_motion(), joint_ids=("j", "missing"), target=target
    )
    assert not missing.passed


def test_error_boundary_is_validated_before_solving(ex3_assembly):
    value = scenario.create_scenario(scenario_id="boundary", assembly=ex3_assembly)
    value = scenario.set_run_duration(scenario=value, duration_s=1.0)
    value = scenario.set_sample_period(scenario=value, period_s=0.1)
    value = scenario.add_joint_speed_profile(
        scenario=value, joint_id="joint.ex3.ground_crank", profile=((0.2, 1.0), (1.0, 1.0))
    )
    value = scenario.set_profile_boundary(scenario=value, behavior="error")
    result = scenario.validate_scenario(scenario=value)
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-SCENARIO-PROFILE-DOES-NOT-START-AT-ZERO"


def test_pose_target_and_coordinated_profile_round_trip(ex3_assembly):
    value = scenario.create_scenario(scenario_id="roundtrip", assembly=ex3_assembly)
    target = PoseTrajectory(
        target="cmp.ex3.rocker",
        points=(
            PosePoint(time_s=0.0, pose=Pose()),
            PosePoint(time_s=1.0, pose=Pose(position_m=(0.1, 0.0, 0.0))),
        ),
    )
    value = scenario.add_pose_trajectory_target(scenario=value, target=target)
    value = scenario.add_coordinated_motion_profile(
        scenario=value,
        profile=CoordinatedMotionProfile(
            axes={"joint.ex3.ground_crank": (0.0, 0.1)},
            times_s=(0.0, 1.0),
        ),
    )
    restored = scenario.scenario_from_dict(
        assembly=ex3_assembly, data=scenario.scenario_to_dict(scenario=value)
    )
    assert restored.pose_trajectory_targets[0].target.component_id == "cmp.ex3.rocker"
    assert restored.coordinated_profiles[0].axes["joint.ex3.ground_crank"] == (0.0, 0.1)


def test_cartesian_driver_and_pose_trajectory_ik_are_explicit_capability_failures(ex3_assembly):
    from kincheckapi.errors import BackendCapabilityError
    target = PoseTrajectory(
        target="cmp.ex3.rocker",
        points=(PosePoint(time_s=0.0, pose=Pose()), PosePoint(time_s=1.0, pose=Pose())),
    )
    value = scenario.create_scenario(scenario_id="capability", assembly=ex3_assembly)
    with pytest.raises(BackendCapabilityError) as driver_error:
        scenario.add_component_pose_driver(scenario=value, target=target)
    assert "CAPABILITY" in driver_error.value.code
    assert driver_error.value.operation == "add_component_pose_driver"
    assert driver_error.value.report.status == "capability_failed"
    ik_result = kinematics.solve_inverse_kinematics(assembly=ex3_assembly, target=target)
    assert ik_result.status == "capability_failed"
    assert ik_result.issues[0].code == "KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED"


def test_diagnostic_trace_has_four_answer_fields():
    value = diagnostic_trace(ValueError("bad input"))
    assert value["passed"] is False
    assert value["what_happened"]
    assert value["cause"]
    assert value["how_to_fix"]
    assert "traceback" not in value

def test_continuous_interference_invalid_input_is_structured():
    report = checks.check_continuous_interference(
        assembly=object(), motion_result=object(), component_pairs=()
    )
    assert report.status == "validation_failed"
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-INPUT-INVALID"

def test_diagnostic_trace_can_opt_in_to_native_traceback_text():
    try:
        raise ValueError("bad input")
    except ValueError as error:
        payload = diagnostic_trace(error, include_traceback=True)
    assert payload["code"] == "KINCHECK-UNEXPECTED-ERROR"
    assert payload["native_error_type"] == "ValueError"
    assert "ValueError: bad input" in payload["traceback"]

def test_motion_package_rejects_partial_result(tmp_path):
    from dataclasses import replace
    from kincheckapi import export
    from kincheckapi.assembly import AssemblyModel, Component, Part
    assembly = AssemblyModel(assembly_id="a", parts=(Part("p"),), components=(Component("c", "p"),))
    partial = replace(_motion(), assembly_id="a", status="partial")
    with pytest.raises(Exception) as error:
        export.motion_package(assembly=assembly, motion_result=partial, output_path=tmp_path / "partial.kincheck")
    assert error.value.code == "KINCHECK-PACKAGE-MOTION-INCOMPLETE"


def test_validate_package_rejects_tampered_partial_result(tmp_path):
    from dataclasses import replace
    import hashlib
    import json
    import zipfile
    from kincheckapi import export
    from kincheckapi.assembly import AssemblyModel, Part

    assembly = AssemblyModel(assembly_id="a", parts=(Part("p"),), components=())
    source = tmp_path / "complete.kincheck"
    export.motion_package(
        assembly=assembly, motion_result=replace(_motion(), assembly_id="a"), output_path=source
    )
    with zipfile.ZipFile(source) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    motion_payload = json.loads(members["motion.json"])
    motion_payload["motion_result"]["status"] = "partial"
    members["motion.json"] = json.dumps(
        motion_payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    manifest = json.loads(members["manifest.json"])
    for entry in manifest["files"]:
        if entry["path"] == "motion.json":
            entry["bytes"] = len(members["motion.json"])
            entry["sha256"] = hashlib.sha256(members["motion.json"]).hexdigest()
    members["manifest.json"] = json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    tampered = tmp_path / "partial.kincheck"
    with zipfile.ZipFile(tampered, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    result = export.validate_package(path=tampered)
    assert not result.passed
    assert any(issue.code == "KINCHECK-PACKAGE-MOTION-INCOMPLETE" for issue in result.issues)
