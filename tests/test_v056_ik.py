from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi import IKOptions, IKSolutionSet, backend_capabilities, solve_inverse_kinematics
from kincheckapi.assembly import JointType
from kincheckapi.kinematics import PoseTarget
from kincheckapi.motion_contracts import PosePoint, PoseTrajectory
from kincheckapi.pose import Pose


def _rocker_target(ex3_assembly):
    component = ex3_assembly.get_component(component_id="cmp.ex3.rocker")
    return PoseTarget(component_id=component.component_id, pose=component.initial_pose)


def test_capabilities_distinguish_scalar_ik_from_general_6d_ik():
    capabilities = backend_capabilities()
    assert capabilities.analysis_capabilities["scalar_inverse_kinematics"] is True
    assert capabilities.analysis_capabilities["general_inverse_kinematics"] is False


def test_scalar_ik_solves_target_and_returns_verified_solution(ex3_assembly):
    result = solve_inverse_kinematics(
        assembly=ex3_assembly,
        target=_rocker_target(ex3_assembly),
        initial_joint_positions={"joint.ex3.ground_crank": 0.2},
        options=IKOptions(max_iterations=40),
    )
    assert result.status == "solved"
    assert result.passed
    assert result.selected_solution is not None
    assert result.selected_solution.passed
    assert result.selected_solution.position_error_m <= 1e-6
    assert result.selected_solution.orientation_error_rad <= 1e-6
    assert result.metadata["search_complete"] is False


def test_scalar_ik_multistart_is_deterministic_and_deduplicated(ex3_assembly):
    options = IKOptions(max_iterations=40, multi_start_count=3, random_seed=7)
    first = solve_inverse_kinematics(
        assembly=ex3_assembly, target=_rocker_target(ex3_assembly),
        joint_limits={
            "joint.ex3.crank_coupler": (-3.14, 3.14),
            "joint.ex3.ground_crank": (-3.14, 3.14),
            "joint.ex3.ground_rocker": (-3.14, 3.14),
        }, options=options,
    )
    second = solve_inverse_kinematics(
        assembly=ex3_assembly, target=_rocker_target(ex3_assembly),
        joint_limits={
            "joint.ex3.crank_coupler": (-3.14, 3.14),
            "joint.ex3.ground_crank": (-3.14, 3.14),
            "joint.ex3.ground_rocker": (-3.14, 3.14),
        }, options=options,
    )
    assert first.to_dict() == second.to_dict()
    assert first.status == "solved"
    assert len(first.solutions) <= 3
    assert all(solution.passed for solution in first.solutions)


def test_ik_proves_unreachable_when_effective_ranges_have_no_free_coordinate(ex3_assembly):
    target = PoseTarget(
        component_id="cmp.ex3.rocker",
        pose=Pose(position_m=(10.0, 10.0, 10.0)),
    )
    limits = {
        "joint.ex3.crank_coupler": (0.0, 0.0),
        "joint.ex3.ground_crank": (0.0, 0.0),
        "joint.ex3.ground_rocker": (0.0, 0.0),
    }
    result = solve_inverse_kinematics(
        assembly=ex3_assembly, target=target, joint_limits=limits,
    )
    assert result.status == "unreachable"
    assert not result.passed
    assert result.metadata["infeasibility_proven"] is True
    assert result.issues[0].code == "KINCHECK-KIN-TARGET-UNREACHABLE"


def test_ik_invalid_target_is_structured():
    result = solve_inverse_kinematics(
        assembly=object(), target={"component_id": "missing", "pose": Pose()}
    )
    assert result.status == "invalid"
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-IK-ASSEMBLY-INVALID"


def test_ik_pose_trajectory_is_an_explicit_capability_boundary(ex3_assembly):
    target = PoseTrajectory(
        target="cmp.ex3.rocker",
        points=(PosePoint(time_s=0.0, pose=Pose()), PosePoint(time_s=1.0, pose=Pose())),
    )
    result = solve_inverse_kinematics(assembly=ex3_assembly, target=target)
    assert result.status == "capability_failed"
    assert result.issues[0].code == "KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED"
    assert result.issues[0].evidence[0].actual == "trajectory_inverse_kinematics"


def test_ik_spherical_joint_is_an_explicit_capability_boundary(ex3_assembly):
    spherical = replace(
        ex3_assembly.joints[0], joint_type=JointType.SPHERICAL
    )
    assembly = replace(
        ex3_assembly,
        joints=(spherical, *ex3_assembly.joints[1:]),
    )
    result = solve_inverse_kinematics(
        assembly=assembly, target=_rocker_target(assembly)
    )
    assert result.status == "capability_failed"
    assert result.issues[0].code == "KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED"
    assert result.issues[0].object_ids == (spherical.joint_id,)
    assert result.issues[0].evidence[0].key == "missing_capability"


def test_ik_round_trip_preserves_solution_and_diagnostics(ex3_assembly):
    result = solve_inverse_kinematics(
        assembly=ex3_assembly, target=_rocker_target(ex3_assembly),
    )
    restored = IKSolutionSet.from_dict(result.to_dict())
    assert restored.to_dict() == result.to_dict()
    assert restored.selected_solution is not None
