from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import pytest

from kincheckapi import checks, kinematics, result, scenario
from kincheckapi._backends.solver_backend import (
    _axis_alignment_error_rad,
    _geometric_residual_definition,
    compile_assembly,
)
from kincheckapi.assembly import (
    AssemblyModel,
    Component,
    Connector,
    ConnectorRef,
    Constraint,
    Ground,
    Joint,
    JointType,
    Part,
    Pose,
)
from kincheckapi.pose import compose_pose


def _motion(assembly):
    value = scenario.create_scenario(scenario_id="hierarchy.ex3", assembly=assembly)
    value = scenario.add_joint_speed_driver(scenario=value, joint_id="joint.ex3.ground_crank", speed_rad_s_or_m_s=0.1, start_time_s=0.0, end_time_s=0.2)
    value = scenario.set_run_duration(scenario=value, duration_s=0.2)
    value = scenario.set_sample_period(scenario=value, period_s=0.1)
    value = scenario.request_joint_result(scenario=value, joint_id="joint.ex3.ground_crank")
    value = scenario.request_component_result(scenario=value, component_id="cmp.ex3.rocker")
    return kinematics.solve_motion(scenario=value)


def test_mjcf_bodies_and_closure_are_compiled(ex3_assembly):
    compiled = compile_assembly(assembly=ex3_assembly)
    root = ET.fromstring(compiled.model_xml)
    assert len(root.findall(".//worldbody//body")) >= 4
    assert root.find(".//equality/connect") is not None
    assert compiled.model.neq >= 1


def test_non_z_connector_axis_is_written_to_mjcf():
    quarter_turn_y = (0.0, math.sqrt(0.5), 0.0, math.sqrt(0.5))
    axis = Connector("axis", pose=Pose(orientation_xyzw=quarter_turn_y))
    assembly = AssemblyModel(
        assembly_id="axis.x",
        parts=(Part("ground", connectors=(Connector("axis"),)), Part("child", connectors=(axis,))),
        components=(Component("ground", "ground"), Component("child", "child")),
        joints=(Joint("joint.x", JointType.REVOLUTE, ConnectorRef("ground", "axis"), ConnectorRef("child", "axis")),),
        grounds=(Ground("ground"),),
    )
    compiled = compile_assembly(assembly=assembly)
    child_group = compiled.component_groups["child"]
    root = ET.fromstring(compiled.model_xml)
    joint = root.find(f".//joint[@name='{compiled.group_joint_names[child_group]}']")
    assert joint is not None
    assert tuple(float(item) for item in joint.attrib["axis"].split()) == pytest.approx((1.0, 0.0, 0.0), abs=1e-12)


def test_tree_joint_observable_is_recorded_relative_to_the_tree(ex3_assembly):
    compiled = compile_assembly(assembly=ex3_assembly)
    assert "joint.ex3.ground_crank" in compiled.joint_expressions
    assert compiled.joint_expressions["joint.ex3.ground_crank"].coefficients


def test_motion_records_component_trajectory_and_joint_state(ex3_assembly):
    motion = _motion(ex3_assembly)
    assert motion.status in {"completed", "completed_with_warnings", "partial"}
    assert result.read_component_pose(motion_result=motion, component_id="cmp.ex3.rocker", time_s=0.1)
    assert motion.get_joint_trajectory(joint_id="joint.ex3.ground_crank") is not None


def test_mesh_closure_residuals_are_kept_when_components_are_filtered(ex3_assembly):
    value = scenario.create_scenario(scenario_id="hierarchy.residual-filter", assembly=ex3_assembly)
    value = scenario.add_joint_speed_driver(scenario=value, joint_id="joint.ex3.ground_crank", speed_rad_s_or_m_s=0.02, start_time_s=0.0, end_time_s=0.1)
    value = scenario.set_run_duration(scenario=value, duration_s=0.1)
    value = scenario.set_sample_period(scenario=value, period_s=0.1)
    value = scenario.request_component_result(scenario=value, component_id="cmp.ex3.rocker")
    motion = kinematics.solve_motion(scenario=value)
    assert motion.constraint_residuals
    assert all(item.position_residual_m >= 0.0 for item in motion.constraint_residuals)


@pytest.mark.parametrize("degrees", [0.0, 45.0, 90.0, 135.0, 180.0])
def test_axis_alignment_residual_ignores_axis_spin(degrees):
    pose_b = Pose(orientation_xyzw=(0.0, 0.0, math.sin(math.radians(degrees) / 2), math.cos(math.radians(degrees) / 2)))
    assert _axis_alignment_error_rad(actual_a=Pose(), actual_b=pose_b) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("degrees", [0.0, 45.0, 90.0])
def test_axis_alignment_residual_reports_axis_tilt(degrees):
    pose_b = Pose(orientation_xyzw=(0.0, math.sin(math.radians(degrees) / 2), 0.0, math.cos(math.radians(degrees) / 2)))
    assert _axis_alignment_error_rad(actual_a=Pose(), actual_b=pose_b) == pytest.approx(math.radians(degrees), abs=1e-12)


def test_geometric_residual_uses_explicit_meter_distance(ex3_assembly):
    source = ex3_assembly.closures[0].constraint
    explicit = type(source)(constraint_id="explicit.distance", connector_a=source.connector_a, connector_b=source.connector_b, constraint_type=source.constraint_type, metadata={**source.metadata, "distance_m": 0.25})
    definition = _geometric_residual_definition(assembly=ex3_assembly, constraint=explicit)
    assert definition.expected_distance_m == pytest.approx(0.25)


def test_geometric_residual_defaults_to_imported_center_distance(ex3_assembly):
    source = ex3_assembly.closures[0].constraint
    definition = _geometric_residual_definition(assembly=ex3_assembly, constraint=source)
    pose_a = compose_pose(parent=ex3_assembly.get_component(component_id=source.connector_a.component_id).initial_pose, child=ex3_assembly.get_connector(component_id=source.connector_a.component_id, connector_id=source.connector_a.connector_id).pose)
    pose_b = compose_pose(parent=ex3_assembly.get_component(component_id=source.connector_b.component_id).initial_pose, child=ex3_assembly.get_connector(component_id=source.connector_b.component_id, connector_id=source.connector_b.connector_id).pose)
    assert definition.expected_distance_m == pytest.approx(math.dist(pose_a.position_m, pose_b.position_m))


def test_transmission_check_reports_missing_trajectory_without_backend_objects(ex3_assembly):
    motion = _motion(ex3_assembly)
    report = checks.check_transmission_ratio(motion_result=motion, input_joint_id="joint.ex3.ground_crank", output_joint_id="joint.missing", expected_ratio=1.0, expected_direction="same")
    assert not report.passed
    assert report.issues
