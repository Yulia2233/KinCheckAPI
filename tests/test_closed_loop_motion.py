from __future__ import annotations

from dataclasses import replace
import math
import xml.etree.ElementTree as ET

import pytest

from kincheckapi import cadir, kinematics, result, scenario
from kincheckapi._backends.solver_backend import BackendCapabilityFailure, compile_assembly
from kincheckapi.export import _motion_from_dict
from kincheckapi.pose import Pose


def _scenario(assembly, *, scenario_id: str, joint_id: str, speed: float = 1e-4):
    value = scenario.create_scenario(scenario_id=scenario_id, assembly=assembly)
    value = scenario.add_joint_speed_driver(
        scenario=value,
        joint_id=joint_id,
        speed_rad_s_or_m_s=speed,
        start_time_s=0.0,
        end_time_s=1e-3,
    )
    value = scenario.set_run_duration(scenario=value, duration_s=1e-3)
    value = scenario.set_sample_period(scenario=value, period_s=1e-3)
    return value


def test_ex3_conversion_restores_one_closure(ex3_assembly):
    assert len(ex3_assembly.closures) == 1
    assert ex3_assembly.closures[0].closure_id == "closure.ex3.coupler_rocker"


def test_ex3_closure_endpoints_are_stable(ex3_assembly):
    closure = ex3_assembly.closures[0]
    assert closure.constraint.connector_a.component_id == "cmp.ex3.coupler"
    assert closure.constraint.connector_b.component_id == "cmp.ex3.rocker"
    assert closure.position_tolerance_m == pytest.approx(1e-6)


def test_ex4_closure_source_joint_ids_are_preserved(ex4_assembly):
    source_ids = {
        item.constraint.metadata["source_joint_id"] for item in ex4_assembly.closures
    }
    assert len(source_ids) == 3
    assert all(item.startswith("joint.jansen.closure.") for item in source_ids)


def test_ex4_conversion_restores_three_closures(ex4_assembly):
    assert len(ex4_assembly.closures) == 3
    assert all(item.constraint.constraint_type == "connect" for item in ex4_assembly.closures)


def test_ex3_topology_separates_tree_and_closure_edges(ex3_assembly):
    tree = kinematics.build_kinematic_tree(assembly=ex3_assembly)
    assert len(tree.root_group_ids) == 1
    assert len(tree.tree_edges) == 3
    assert tuple(edge.joint_id for edge in tree.closure_edges) == ("closure.ex3.coupler_rocker",)
    assert not tree.disconnected_group_ids


def test_ex4_topology_keeps_all_three_closure_edges(ex4_assembly):
    tree = kinematics.build_kinematic_tree(assembly=ex4_assembly)
    assert len(tree.tree_edges) == 7
    assert len(tree.closure_edges) == 3
    assert len(tree.parent_component_id) == len(ex4_assembly.components)
    assert not kinematics.validate_topology(assembly=ex4_assembly).issues


def test_ex3_authored_pose_closure_residual_is_zero(ex3_assembly):
    report = kinematics.validate_closures(assembly=ex3_assembly)
    assert report is not None and report.passed
    assert report.residuals[0].position_residual_m < 1e-9
    assert report.residuals[0].orientation_residual_rad < 1e-9


def test_ex4_authored_pose_has_three_zero_closures(ex4_assembly):
    report = kinematics.validate_closures(assembly=ex4_assembly)
    assert report is not None and report.passed
    assert len(report.residuals) == 3
    assert max(item.position_residual_m for item in report.residuals) < 1e-9


def test_empty_validate_closures_call_keeps_compatibility_contract():
    assert kinematics.validate_closures(sentinel="ignored") is None


def test_motion_closure_report_matches_recorded_status(ex3_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex3_assembly,
            scenario_id="test.ex3.report",
            joint_id="joint.ex3.ground_crank",
        )
    )
    report = kinematics.validate_closures(motion_result=motion)
    assert report is not None and report.passed
    assert len(report.residuals) == len(motion.closure_residuals)


def test_ex3_xml_contains_tree_bodies_and_two_point_hinge_closure(ex3_assembly):
    compiled = compile_assembly(assembly=ex3_assembly)
    root = ET.fromstring(compiled.model_xml)
    assert len(root.findall(".//worldbody//body")) >= 4
    assert root.find(".//equality/connect[@name='closure.ex3.coupler_rocker']") is not None
    assert root.find(".//equality/connect[@name='closure.ex3.coupler_rocker__axis']") is not None
    assert compiled.model.neq == 2


def test_ex3_xml_has_no_weld_for_revolute_closure(ex3_assembly):
    compiled = compile_assembly(assembly=ex3_assembly)
    root = ET.fromstring(compiled.model_xml)
    assert not root.findall(".//equality/weld")


def test_ex4_xml_contains_six_constraint_rows(ex4_assembly):
    compiled = compile_assembly(assembly=ex4_assembly)
    assert compiled.model.neq == 6


def test_ex4_xml_contains_one_primary_and_one_axis_constraint_per_closure(ex4_assembly):
    compiled = compile_assembly(assembly=ex4_assembly)
    root = ET.fromstring(compiled.model_xml)
    closure_names = {item.closure_id for item in ex4_assembly.closures}
    assert {
        node.attrib["name"]
        for node in root.findall(".//equality/connect")
        if "__axis" not in node.attrib["name"]
    } == closure_names
    assert compiled.model.neq == 6


def test_ex3_motion_returns_closure_residuals_and_tree_metadata(ex3_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex3_assembly,
            scenario_id="test.ex3.motion",
            joint_id="joint.ex3.ground_crank",
        )
    )
    assert motion.status == "completed"
    assert len(motion.closure_residuals) == 2
    assert motion.closure_statuses["closure.ex3.coupler_rocker"] == "passed"
    assert len(motion.metadata["kinematic_tree"]["tree_edges"]) == 3


def test_ex4_motion_returns_all_closure_residuals(ex4_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex4_assembly,
            scenario_id="test.ex4.motion",
            joint_id="joint.jansen.frame_to_crank",
        )
    )
    assert motion.status == "completed"
    assert len(motion.closure_residuals) == 6
    assert set(motion.closure_statuses.values()) == {"passed"}


def test_ex4_motion_has_two_samples_per_closure(ex4_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex4_assembly,
            scenario_id="test.ex4.residual-count",
            joint_id="joint.jansen.frame_to_crank",
        )
    )
    assert len(motion.closure_residuals) == 3 * len(motion.sample_times_s)


def test_ex4_closure_result_round_trips_through_json(ex4_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex4_assembly,
            scenario_id="test.ex4.roundtrip",
            joint_id="joint.jansen.frame_to_crank",
        )
    )
    restored = _motion_from_dict(motion.to_dict())
    assert restored.closure_statuses == motion.closure_statuses
    assert restored.closure_residuals == motion.closure_residuals


def test_ex4_motion_tree_metadata_has_single_ground_root(ex4_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex4_assembly,
            scenario_id="test.ex4.tree-metadata",
            joint_id="joint.jansen.frame_to_crank",
        )
    )
    assert len(motion.metadata["kinematic_tree"]["root_group_ids"]) == 1
    assert not motion.metadata["kinematic_tree"]["disconnected_group_ids"]


def test_ex3_component_world_trajectory_is_recorded(ex3_assembly):
    condition = _scenario(
        ex3_assembly,
        scenario_id="test.ex3.pose",
        joint_id="joint.ex3.ground_crank",
    )
    condition = scenario.request_component_result(
        scenario=condition, component_id="cmp.ex3.coupler"
    )
    motion = kinematics.solve_motion(scenario=condition)
    pose = result.read_component_pose(
        motion_result=motion, component_id="cmp.ex3.coupler", time_s=0.001
    )
    assert isinstance(pose, Pose)
    assert pose.position_m != pytest.approx((0.0, 0.0, 0.0))


def test_ex3_result_exposes_local_and_world_pose_maps(ex3_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex3_assembly,
            scenario_id="test.ex3.pose-maps",
            joint_id="joint.ex3.ground_crank",
        )
    )
    local = motion.metadata["component_local_poses"]
    world = motion.metadata["component_world_poses"]
    assert set(local) == {item.component_id for item in ex3_assembly.components}
    assert set(world) == set(local)


def test_ex4_foot_world_trajectory_is_recorded(ex4_assembly):
    condition = _scenario(
        ex4_assembly,
        scenario_id="test.ex4.pose",
        joint_id="joint.jansen.frame_to_crank",
    )
    condition = scenario.request_component_result(
        scenario=condition, component_id="cmp.jansen.foot.01"
    )
    motion = kinematics.solve_motion(scenario=condition)
    pose = result.read_component_pose(
        motion_result=motion, component_id="cmp.jansen.foot.01", time_s=0.001
    )
    assert isinstance(pose, Pose)


def test_ex4_driven_closures_stay_within_tolerance(ex4_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex4_assembly,
            scenario_id="test.ex4.drift",
            joint_id="joint.jansen.frame_to_crank",
            speed=0.1,
        )
    )
    assert motion.status == "completed"
    assert set(motion.closure_statuses.values()) == {"passed"}


def test_ex3_initial_pose_mismatch_is_rejected(ex3_assembly):
    changed = tuple(
        replace(
            item,
            initial_pose=Pose(
                position_m=(item.initial_pose.position_m[0] + 1e-3, *item.initial_pose.position_m[1:]),
                orientation_xyzw=item.initial_pose.orientation_xyzw,
            ),
        )
        if item.component_id == "cmp.ex3.coupler"
        else item
        for item in ex3_assembly.components
    )
    broken = replace(ex3_assembly, components=changed)
    report = kinematics.validate_closures(assembly=broken)
    assert report is not None and not report.passed
    with pytest.raises(BackendCapabilityFailure):
        compile_assembly(assembly=broken)


def test_ex3_driven_closure_stays_within_tolerance(ex3_assembly):
    motion = kinematics.solve_motion(
        scenario=_scenario(
            ex3_assembly,
            scenario_id="test.ex3.drift",
            joint_id="joint.ex3.ground_crank",
            speed=0.01,
        )
    )
    assert motion.status == "completed"
    assert set(motion.closure_statuses.values()) == {"passed"}


@pytest.mark.parametrize(
    ("fixture_name", "joint_id"),
    [
        ("ex3_assembly", "joint.ex3.ground_crank"),
        ("ex4_assembly", "joint.jansen.frame_to_crank"),
    ],
)
def test_closed_loop_completes_full_crank_rotation(request, fixture_name, joint_id):
    assembly = request.getfixturevalue(fixture_name)
    duration_s = 10.0
    speed = 2.0 * math.pi / duration_s
    condition = scenario.create_scenario(scenario_id="test.closure.full-turn", assembly=assembly)
    condition = scenario.add_joint_speed_driver(
        scenario=condition, joint_id=joint_id, speed_rad_s_or_m_s=speed,
        start_time_s=0.0, end_time_s=duration_s,
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=duration_s)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.02)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status == "completed"
    report = kinematics.validate_closures(motion_result=motion)
    assert report is not None and report.passed
    crank = next(item for item in motion.joint_trajectories if item.joint_id == joint_id)
    assert crank.positions[-1] - crank.positions[0] == pytest.approx(2.0 * math.pi, abs=2e-4)
    assert crank.velocities[-1] == pytest.approx(speed, abs=1e-4)
    assert all(b > a for a, b in zip(crank.positions, crank.positions[1:]))


@pytest.mark.parametrize("speed", [-0.5, 0.5])
@pytest.mark.parametrize(
    ("fixture_name", "joint_id"),
    [
        ("ex3_assembly", "joint.ex3.ground_crank"),
        ("ex4_assembly", "joint.jansen.frame_to_crank"),
    ],
)
def test_closed_loop_startup_at_every_integration_step(request, fixture_name, joint_id, speed):
    assembly = request.getfixturevalue(fixture_name)
    condition = scenario.create_scenario(scenario_id="test.closure.startup", assembly=assembly)
    condition = scenario.add_joint_speed_driver(
        scenario=condition, joint_id=joint_id, speed_rad_s_or_m_s=speed,
        start_time_s=0.0, end_time_s=0.005,
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=0.005)
    condition = scenario.set_sample_period(scenario=condition, period_s=2e-5)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status == "completed"
    assert len(motion.sample_times_s) == 251
    report = kinematics.validate_closures(motion_result=motion)
    assert report is not None and report.passed
    crank = next(item for item in motion.joint_trajectories if item.joint_id == joint_id)
    assert crank.positions[-1] == pytest.approx(speed * 0.005, abs=5e-5)


def test_closed_loop_still_reports_partial_when_declared_tolerance_is_exceeded(ex3_assembly):
    strict = replace(
        ex3_assembly,
        closures=tuple(replace(item, position_tolerance_m=1e-9) for item in ex3_assembly.closures),
    )
    condition = _scenario(
        strict, scenario_id="test.closure.strict", joint_id="joint.ex3.ground_crank", speed=0.5,
    )
    condition = scenario.set_sample_period(scenario=condition, period_s=2e-5)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status == "partial"
    assert any(item.position_residual_m > 1e-9 for item in motion.closure_residuals)
    assert any(issue.code == "KINCHECK-CLOSURE-RESIDUAL-EXCEEDED" for issue in motion.issues)


@pytest.mark.parametrize("has_closure", [False, True])
def test_integration_step_cap_survives_short_sample_remainders(ex1_assembly, ex3_assembly, has_closure):
    assembly = ex3_assembly if has_closure else ex1_assembly
    assert bool(assembly.closures) is has_closure
    condition = scenario.create_scenario(scenario_id="test.closure.step-cap", assembly=assembly)
    condition = scenario.set_run_duration(scenario=condition, duration_s=0.0023)
    # Neither cap divides this output period; each interval ends in a short step.
    condition = scenario.set_sample_period(scenario=condition, period_s=0.00073)
    condition = scenario.set_capture_integration_steps(scenario=condition, enabled=True)
    motion = kinematics.solve_motion(scenario=condition)
    times = [item["time_s"] for item in motion.metadata["integration_samples"]]
    cap = 2e-5 if has_closure else 5e-4
    assert times[-1] == pytest.approx(0.0023)
    for start, end in zip(motion.sample_times_s, motion.sample_times_s[1:]):
        steps = [b - a for a, b in zip(times, times[1:]) if a >= start - 1e-12 and b <= end + 1e-12]
        assert all(0.0 < dt <= cap + 1e-12 for dt in steps)
        assert max(steps) == pytest.approx(min(cap, end - start))


def test_closed_loop_respects_authored_smooth_speed_profile(ex3_assembly):
    joint_id = "joint.ex3.ground_crank"
    condition = scenario.create_scenario(scenario_id="test.closure.smooth", assembly=ex3_assembly)
    condition = scenario.add_joint_speed_profile(
        scenario=condition, joint_id=joint_id,
        profile=[(0.0, 0.0), (0.1, 0.5), (0.9, 0.5), (1.0, 0.0)],
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=1.0)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.01)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status == "completed"
    crank = next(item for item in motion.joint_trajectories if item.joint_id == joint_id)
    # The area under the requested speed profile is 0.45 radians.
    assert crank.positions[-1] == pytest.approx(0.45, abs=1e-4)
    assert abs(crank.velocities[-1]) < 1e-3


def test_closed_loop_respects_position_driver(ex3_assembly):
    joint_id = "joint.ex3.ground_crank"
    condition = scenario.create_scenario(scenario_id="test.closure.position", assembly=ex3_assembly)
    condition = scenario.add_joint_position_driver(
        scenario=condition, joint_id=joint_id, profile=[(0.0, 0.0), (1.0, 0.5)],
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=1.0)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.01)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status == "completed"
    crank = next(item for item in motion.joint_trajectories if item.joint_id == joint_id)
    assert crank.positions[-1] == pytest.approx(0.5, abs=1e-4)
