from __future__ import annotations

import pytest

from kincheckapi import checks, kinematics
from kincheckapi.result import ComponentState, JointTrajectory, MotionResult, Trajectory
from kincheckapi.pose import Pose


def _motion(ex3_assembly, *, moved: bool = False) -> MotionResult:
    times = (0.0, 1.0)
    joint_trajectories = tuple(
        JointTrajectory(
            joint_id=joint_id,
            times_s=times,
            positions=(0.0, 0.1 if moved else 0.0),
            velocities=(0.0, 0.1 if moved else 0.0),
            accelerations=(0.0, 0.0),
        )
        for joint_id in (
            "joint.ex3.ground_crank",
            "joint.ex3.crank_coupler",
            "joint.ex3.ground_rocker",
        )
    )
    component = ex3_assembly.get_component(component_id="cmp.ex3.coupler")
    assert component is not None
    poses = (component.initial_pose, component.initial_pose)
    trajectory = Trajectory(
        component_id=component.component_id,
        connector_id=None,
        times_s=times,
        poses=poses,
        linear_velocities_m_s=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        angular_velocities_rad_s=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        linear_accelerations_m_s2=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        angular_accelerations_rad_s2=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    )
    return MotionResult(
        scenario_id="scenario.test",
        assembly_id=ex3_assembly.assembly_id,
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=times,
        joint_trajectories=joint_trajectories,
        trajectories=(trajectory,),
    )


def test_singularity_report_has_one_sample_per_motion_sample(ex3_assembly):
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly), assembly=ex3_assembly
    )
    assert len(report.samples) == 2
    assert report.to_dict()["samples"]


def test_singularity_report_is_deterministic(ex3_assembly):
    motion = _motion(ex3_assembly)
    first = kinematics.find_singularities(motion_result=motion, assembly=ex3_assembly).to_dict()
    second = kinematics.find_singularities(motion_result=motion, assembly=ex3_assembly).to_dict()
    assert first == second


def test_reachability_missing_component_is_false(ex3_assembly):
    report = kinematics.check_reachability(
        assembly=ex3_assembly,
        target={"component_id": "missing", "pose": Pose()},
    )
    assert not report.reachable
    assert any(issue.code == "KINCHECK-KIN-TARGET-NOT-FOUND" for issue in report.issues)


def test_workspace_requires_finite_joint_ranges(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target="cmp.ex3.coupler",
        options=kinematics.WorkspaceOptions(),
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-WORKSPACE-RANGE-REQUIRED"


def test_workspace_sampling_is_deterministic(ex3_assembly):
    options = kinematics.WorkspaceOptions(
        joint_ranges={"joint.ex3.ground_crank": (0.0, 0.1)},
        samples_per_joint=3,
    )
    first = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.coupler", options=options).to_dict()
    second = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.coupler", options=options).to_dict()
    assert first == second
    assert len(first["samples"]) == 3


def test_pose_check_passes_at_authored_pose(ex3_assembly):
    motion = _motion(ex3_assembly)
    component = ex3_assembly.get_component(component_id="cmp.ex3.coupler")
    assert component is not None
    report = checks.check_pose_target(
        motion_result=motion,
        target={"component_id": component.component_id, "pose": component.initial_pose},
    )
    assert report.passed


def test_pose_check_reports_missing_trajectory(ex3_assembly):
    report = checks.check_pose_target(
        motion_result=_motion(ex3_assembly),
        target={"component_id": "cmp.ex3.rocker", "pose": Pose()},
    )
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-RESULT-TRAJECTORY-MISSING"


def test_pose_check_reports_mismatch(ex3_assembly):
    report = checks.check_pose_target(
        motion_result=_motion(ex3_assembly),
        target={"component_id": "cmp.ex3.coupler", "pose": Pose(position_m=(2.0, 0.0, 0.0))},
    )
    assert not report.passed
    assert any(issue.code == "KINCHECK-CHECK-POSE-TARGET-MISMATCH" for issue in report.issues)


def test_trajectory_check_passes_with_available_space_data(ex3_assembly):
    report = checks.check_trajectory(
        motion_result=_motion(ex3_assembly),
        component_id="cmp.ex3.coupler",
        max_speed_m_s=1.0,
        max_angular_speed_rad_s=1.0,
    )
    assert report.passed


def test_trajectory_check_rejects_speed_limit(ex3_assembly):
    report = checks.check_trajectory(
        motion_result=_motion(ex3_assembly),
        component_id="cmp.ex3.coupler",
        max_speed_m_s=-1.0,
    )
    assert not report.passed
    assert any(issue.code == "KINCHECK-CHECK-TRAJECTORY-LIMIT-INVALID" for issue in report.issues)


def test_run_checks_dispatches_pose_and_trajectory(ex3_assembly):
    motion = _motion(ex3_assembly)
    component = ex3_assembly.get_component(component_id="cmp.ex3.coupler")
    assert component is not None
    suite = checks.run_checks(
        assembly=ex3_assembly,
        motion_result=motion,
        checks=(
            checks.CheckSpec(
                check_id="pose",
                check_type="pose_target",
                parameters={"target": {"component_id": component.component_id, "pose": component.initial_pose}},
            ),
            checks.CheckSpec(
                check_id="trajectory",
                check_type="trajectory",
                parameters={"component_id": component.component_id},
            ),
        ),
    )
    assert suite.passed
    assert [item.check_id for item in suite.reports] == ["pose", "trajectory"]


def test_connector_path_missing_record_is_structured(ex3_assembly):
    result = kinematics.trace_connector_path(
        motion_result=_motion(ex3_assembly),
        component_id="cmp.ex3.coupler",
        connector_id="conn.output",
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-RESULT-TRAJECTORY-MISSING"
