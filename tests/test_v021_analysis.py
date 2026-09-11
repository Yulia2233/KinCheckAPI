from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi import kinematics
from kincheckapi.kinematics_analysis import (
    ReachabilityOptions,
    SingularityOptions,
    SingularitySample,
    TargetReference,
    WorkspaceOptions,
)
from kincheckapi.kinematics_geometry import PoseTarget
from kincheckapi.result import JointTrajectory, MotionResult


def _ex3_target(ex3_assembly):
    component = ex3_assembly.get_component(component_id="cmp.ex3.crank")
    return PoseTarget(component_id=component.component_id, pose=component.initial_pose)


def _motion(ex3_assembly, *, times=(0.0, 1.0), value=(0.0, 0.1)):
    joints = tuple(
        JointTrajectory(
            joint_id=joint.joint_id,
            times_s=times,
            positions=value,
            velocities=(0.0,) * len(times),
            accelerations=(0.0,) * len(times),
        )
        for joint in ex3_assembly.joints
        if joint.joint_type.value != "fixed"
    )
    return MotionResult(
        scenario_id="analysis.motion",
        assembly_id=ex3_assembly.assembly_id,
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        joint_trajectories=joints,
    )


def test_singularity_options_reject_invalid_order():
    with pytest.raises(ValueError):
        SingularityOptions(tolerance=1e-3, near_tolerance=1e-4)


def test_singularity_sample_is_json_stable():
    sample = SingularitySample(
        time_s=0.0,
        status="regular",
        rank=1,
        minimum_singular_value=2.0,
        condition_number=1.0,
        joint_positions={"joint.b": 2.0, "joint.a": 1.0},
    )
    assert list(sample.to_dict()["joint_positions"]) == ["joint.a", "joint.b"]


def test_find_singularities_returns_one_record_per_motion_sample(ex3_assembly):
    report = kinematics.find_singularities(motion_result=_motion(ex3_assembly), assembly=ex3_assembly)
    assert len(report.samples) == 2
    assert report.samples[0].time_s == 0.0
    assert report.to_dict()["samples"][1]["time_s"] == 1.0


def test_find_singularities_is_deterministic(ex3_assembly):
    motion = _motion(ex3_assembly)
    first = kinematics.find_singularities(motion_result=motion, assembly=ex3_assembly).to_dict()
    second = kinematics.find_singularities(motion_result=motion, assembly=ex3_assembly).to_dict()
    assert first == second


def test_find_singularities_can_report_near_singular_warning(ex3_assembly):
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly),
        assembly=ex3_assembly,
        options=SingularityOptions(tolerance=1e-12, near_tolerance=2.0),
    )
    assert all(sample.status in {"near_singular", "singular"} for sample in report.samples)
    assert report.issues
    assert all(issue.code == "KINCHECK-KIN-SINGULAR" for issue in report.issues)


def test_reachability_accepts_authored_pose(ex3_assembly):
    result = kinematics.check_reachability(
        assembly=ex3_assembly,
        target=_ex3_target(ex3_assembly),
        joint_positions={"joint.ex3.ground_crank": 0.0},
    )
    assert result.reachable
    assert result.position_result is not None


def test_reachability_accepts_mapping_options(ex3_assembly):
    result = kinematics.check_reachability(
        assembly=ex3_assembly,
        target=_ex3_target(ex3_assembly),
        options={"position_tolerance_m": 1e-5, "orientation_tolerance_rad": 1e-5},
    )
    assert result.passed


def test_reachability_rejects_unknown_component(ex3_assembly):
    target = PoseTarget(component_id="cmp.missing", pose=_ex3_target(ex3_assembly).pose)
    result = kinematics.check_reachability(assembly=ex3_assembly, target=target)
    assert not result.reachable
    assert any(issue.code == "KINCHECK-KIN-TARGET-NOT-FOUND" for issue in result.issues)


def test_reachability_rejects_unknown_connector(ex3_assembly):
    base = _ex3_target(ex3_assembly)
    target = PoseTarget(component_id=base.component_id, connector_id="conn.missing", pose=base.pose)
    result = kinematics.check_reachability(assembly=ex3_assembly, target=target)
    assert not result.reachable


def test_reachability_result_round_trips_to_dict(ex3_assembly):
    result = kinematics.check_reachability(assembly=ex3_assembly, target=_ex3_target(ex3_assembly))
    payload = result.to_dict()
    assert payload["reachable"] is True
    assert payload["position_result"]["passed"] is True


def test_workspace_requires_explicit_ranges(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target=TargetReference(component_id="cmp.ex3.crank"),
        options=WorkspaceOptions(),
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-WORKSPACE-RANGE-REQUIRED"


def test_workspace_samples_a_deterministic_grid(ex3_assembly):
    options = WorkspaceOptions(
        joint_ranges={"joint.ex3.ground_crank": (0.0, 1.0)},
        samples_per_joint=4,
    )
    first = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    second = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    assert len(first.samples) == 4
    assert first.to_dict() == second.to_dict()


def test_workspace_preserves_failed_samples(ex3_assembly):
    options = WorkspaceOptions(
        joint_ranges={"joint.unknown": (0.0, 1.0)},
        samples_per_joint=2,
    )
    result = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    assert len(result.samples) == 2
    assert all(not sample.reachable for sample in result.samples)
    assert all(sample.issues for sample in result.samples)


def test_workspace_truncates_large_grid_with_warning(ex3_assembly):
    options = WorkspaceOptions(
        joint_ranges={"joint.ex3.ground_crank": (0.0, 1.0), "joint.ex3.crank_coupler": (0.0, 1.0)},
        samples_per_joint=5,
        max_samples=3,
    )
    result = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    assert len(result.samples) == 3
    assert any(issue.code == "KINCHECK-KIN-WORKSPACE-SAMPLE-TRUNCATED" for issue in result.issues)


def test_workspace_reports_position_bounds(ex3_assembly):
    options = WorkspaceOptions(
        joint_ranges={"joint.ex3.ground_crank": (0.0, 0.5)},
        samples_per_joint=3,
    )
    result = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    assert result.reachable_fraction == 1.0
    assert set(result.bounds_m) == {"x_m", "y_m", "z_m"}


def test_workspace_unknown_target_is_not_passed(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target="cmp.missing",
        options=WorkspaceOptions(
            joint_ranges={"joint.ex3.ground_crank": (0.0, 0.1)},
            samples_per_joint=2,
        ),
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-TARGET-NOT-FOUND"


def test_workspace_unknown_connector_is_not_passed(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target=TargetReference(component_id="cmp.ex3.crank", connector_id="missing"),
        options=WorkspaceOptions(
            joint_ranges={"joint.ex3.ground_crank": (0.0, 0.1)},
            samples_per_joint=2,
        ),
    )
    assert not result.passed
    assert result.samples[0].singularity_status == "unavailable"


def test_workspace_unknown_joint_is_not_passed(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target="cmp.ex3.crank",
        options=WorkspaceOptions(joint_ranges={"joint.missing": (0.0, 1.0)}, samples_per_joint=2),
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-WORKSPACE-JOINT-NOT-FOUND"


def test_workspace_samples_include_residual_and_singularity_evidence(ex3_assembly):
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target="cmp.ex3.crank",
        options=WorkspaceOptions(
            joint_ranges={"joint.ex3.ground_crank": (0.0, 0.2)},
            samples_per_joint=3,
        ),
    )
    assert all(sample.residual_m is not None for sample in result.samples)
    assert all(sample.singularity_status is not None for sample in result.samples)
    assert all(sample.jacobian_rank is not None for sample in result.samples)


def test_workspace_seed_controls_truncated_sample_order(ex3_assembly):
    options = WorkspaceOptions(
        joint_ranges={
            "joint.ex3.ground_crank": (-0.2, 0.2),
            "joint.ex3.crank_coupler": (-0.2, 0.2),
        },
        samples_per_joint=4,
        max_samples=4,
        seed=17,
    )
    first = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    second = kinematics.compute_workspace(assembly=ex3_assembly, target="cmp.ex3.crank", options=options)
    assert [sample.joint_positions for sample in first.samples] == [sample.joint_positions for sample in second.samples]
