from __future__ import annotations

import math

import pytest

from kincheckapi import kinematics
from kincheckapi.assembly import (
    AssemblyModel,
    Component,
    Connector,
    ConnectorRef,
    Ground,
    Joint,
    JointType,
    Part,
)
from kincheckapi.pose import Pose
from kincheckapi.kinematics_geometry import forward_component_poses


def _axis_assembly(*, reverse: bool, joint_type: JointType, rotated: bool = False):
    quarter_turn_y = (0.0, math.sqrt(0.5), 0.0, math.sqrt(0.5))
    initial = Pose(orientation_xyzw=quarter_turn_y) if rotated else Pose()
    ground_ref = ConnectorRef("ground", "axis")
    child_ref = ConnectorRef("child", "axis")
    joint = Joint(
        "joint.test",
        joint_type,
        child_ref if reverse else ground_ref,
        ground_ref if reverse else child_ref,
    )
    return AssemblyModel(
        assembly_id=f"review.axis.{joint_type.value}.{reverse}.{rotated}",
        parts=(
            Part("part.ground", connectors=(Connector("axis"),)),
            Part("part.child", connectors=(Connector("axis"),)),
        ),
        components=(
            Component("ground", "part.ground", initial_pose=initial),
            Component("child", "part.child", initial_pose=initial),
        ),
        joints=(joint,),
        grounds=(Ground("ground"),),
    )


def test_jacobian_angular_rows_are_in_world_coordinates():
    assembly = _axis_assembly(reverse=False, joint_type=JointType.REVOLUTE, rotated=True)
    result = kinematics.compute_jacobian(
        assembly=assembly,
        joint_positions={},
        target_component_id="child",
    )
    column = tuple(row[0] for row in result.matrix[3:])
    assert column == pytest.approx((1.0, 0.0, 0.0), abs=1e-7)


@pytest.mark.parametrize(
    ("reverse", "expected"),
    ((False, 0.25), (True, -0.25)),
)
def test_revolute_tree_motion_honors_public_connector_order(reverse, expected):
    assembly = _axis_assembly(reverse=reverse, joint_type=JointType.REVOLUTE)
    result = kinematics.compute_jacobian(
        assembly=assembly,
        joint_positions={},
        target_component_id="child",
    )
    assert result.matrix[5][0] == pytest.approx(1.0 if not reverse else -1.0, abs=1e-7)
    pose = forward_component_poses(
        assembly,
        {"joint.test": 0.25},
    )["child"]
    assert 2.0 * math.atan2(pose.orientation_xyzw[2], pose.orientation_xyzw[3]) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("reverse", "expected"),
    ((False, 0.04), (True, -0.04)),
)
def test_prismatic_tree_motion_honors_public_connector_order(reverse, expected):
    assembly = _axis_assembly(reverse=reverse, joint_type=JointType.PRISMATIC)
    pose = forward_component_poses(
        assembly,
        {"joint.test": 0.04},
    )["child"]
    assert pose.position_m[2] == pytest.approx(expected)


def test_position_solver_unknown_connector_returns_structured_result(ex3_assembly):
    component = ex3_assembly.get_component(component_id="cmp.ex3.rocker")
    assert component is not None
    target = kinematics.PoseTarget(
        component_id=component.component_id,
        connector_id="conn.missing",
        pose=component.initial_pose,
    )
    result = kinematics.solve_position(assembly=ex3_assembly, pose_targets=(target,))
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-TARGET-NOT-FOUND"
    assert result.issues[0].object_ids == (component.component_id, "conn.missing")


def test_position_solver_unknown_connector_does_not_modify_joint_state(ex3_assembly):
    target = kinematics.PoseTarget(
        component_id="cmp.ex3.rocker",
        connector_id="conn.missing",
        pose=Pose(),
    )
    result = kinematics.solve_position(
        assembly=ex3_assembly,
        joint_positions={"joint.ex3.ground_crank": 0.1},
        pose_targets=(target,),
    )
    assert result.joint_positions["joint.ex3.ground_crank"] == pytest.approx(0.1)
