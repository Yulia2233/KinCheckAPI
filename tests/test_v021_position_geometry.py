from __future__ import annotations

import math

import pytest

from kincheckapi import kinematics
from kincheckapi.pose import Pose


def test_ex3_mobility_is_one_effective_dof(ex3_assembly):
    report = kinematics.analyze_mobility(assembly=ex3_assembly)
    assert report.nominal_dofs == 3
    assert report.effective_dofs == 1
    assert report.constraint_rank == 2


def test_ex4_mobility_accounts_for_three_closures(ex4_assembly):
    report = kinematics.analyze_mobility(assembly=ex4_assembly)
    assert report.effective_dofs == 1
    assert report.constraint_rank == 6
    assert len(report.constraint_ids) == 3


def test_mobility_is_deterministic(ex3_assembly):
    left = kinematics.analyze_mobility(assembly=ex3_assembly).to_dict()
    right = kinematics.analyze_mobility(assembly=ex3_assembly).to_dict()
    assert left == right


def test_jacobian_has_six_rows_and_sorted_columns(ex3_assembly):
    target = "cmp.ex3.rocker"
    result = kinematics.compute_jacobian(
        assembly=ex3_assembly, joint_positions={}, target_component_id=target
    )
    assert len(result.matrix) == 6
    assert result.joint_ids == tuple(sorted(result.joint_ids))
    assert len(result.matrix[0]) == len(result.joint_ids)


def test_jacobian_reports_rank_and_singular_values(ex4_assembly):
    result = kinematics.compute_jacobian(
        assembly=ex4_assembly,
        joint_positions={},
        target_component_id="cmp.jansen.foot_triangle.01",
    )
    assert result.rank >= 1
    assert len(result.singular_values) == min(6, len(result.joint_ids))
    assert result.condition_number is None or result.condition_number >= 1.0


def test_jacobian_unknown_target_is_rejected(ex3_assembly):
    with pytest.raises(ValueError, match="Unknown target Component"):
        kinematics.compute_jacobian(
            assembly=ex3_assembly,
            joint_positions={},
            target_component_id="missing",
        )


def test_ex3_position_solver_converges_for_multiple_input_angles(ex3_assembly):
    joint_id = "joint.ex3.ground_crank"
    for value in (0.0, 0.1, -0.2):
        result = kinematics.solve_position(
            assembly=ex3_assembly, joint_positions={joint_id: value}
        )
        assert result.passed
        assert result.joint_positions[joint_id] == pytest.approx(value)
        assert result.residuals


def test_ex4_position_solver_converges_with_three_closures(ex4_assembly):
    result = kinematics.solve_position(
        assembly=ex4_assembly,
        joint_positions={"joint.jansen.frame_to_crank": 0.2},
    )
    assert result.passed
    assert len(result.residuals) == 3
    assert max(item.position_residual_m for item in result.residuals) < 1e-6


def test_position_solver_rejects_unknown_joint(ex3_assembly):
    result = kinematics.solve_position(
        assembly=ex3_assembly, joint_positions={"missing.joint": 0.0}
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-POSITION-JOINT-NOT-FOUND"


def test_position_solver_rejects_joint_outside_limit(ex3_assembly):
    from dataclasses import replace
    from kincheckapi.assembly import JointLimit

    joint = ex3_assembly.get_joint(joint_id="joint.ex3.ground_crank")
    assert joint is not None
    limited = replace(ex3_assembly, joints=tuple(
        replace(item, limit=JointLimit(lower=-0.1, upper=0.1))
        if item.joint_id == joint.joint_id else item
        for item in ex3_assembly.joints
    ))
    result = kinematics.solve_position(
        assembly=limited,
        joint_positions={joint.joint_id: 1.0},
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-TARGET-OUT-OF-LIMIT"


def test_position_solver_pose_target_is_supported(ex3_assembly):
    target = kinematics.PoseTarget(
        component_id="cmp.ex3.rocker",
        pose=ex3_assembly.get_component(component_id="cmp.ex3.rocker").initial_pose,
    )
    result = kinematics.solve_position(assembly=ex3_assembly, pose_targets=(target,))
    assert result.passed
