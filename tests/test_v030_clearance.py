from __future__ import annotations

from pathlib import Path
from dataclasses import replace
import json
import math

import pytest
import trimesh
import kincheckapi.clearance as clearance_module

from kincheckapi.assembly import AssemblyModel, Component, Part
from kincheckapi import kinematics, scenario
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.errors import ScenarioValidationError
from kincheckapi.clearance import (
    check_envelope_interference,
    check_interference,
    create_motion_envelope,
    measure_minimum_clearance,
    write_motion_envelope,
)
from kincheckapi.clearance_result import ClearanceReport
from kincheckapi.pose import Pose
from kincheckapi.result import MotionResult, Trajectory


def _fixture(tmp_path: Path, *, second_positions=((0.4, 0.0, 0.0), (2.0, 0.0, 0.0))):
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    assembly = AssemblyModel(
        assembly_id="clearance-assembly",
        parts=(
            Part(part_id="part-a", asset_paths={"stl": "a.stl"}),
            Part(part_id="part-b", asset_paths={"stl": "b.stl"}),
        ),
        components=(
            Component(component_id="a", part_id="part-a"),
            Component(component_id="b", part_id="part-b"),
        ),
        metadata={"asset_root": str(tmp_path)},
    )
    times = (0.0, 1.0)
    motion = MotionResult(
        scenario_id="clearance-scenario",
        assembly_id=assembly.assembly_id,
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        trajectories=(
            Trajectory(component_id="a", times_s=times, poses=(Pose(), Pose())),
            Trajectory(
                component_id="b",
                times_s=times,
                poses=tuple(Pose(position_m=position) for position in second_positions),
            ),
        ),
    )
    return assembly, motion


def test_interference_reports_collision_event_and_failure(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = check_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),)
    )
    assert not report.passed
    assert report.status == "failed"
    assert report.events[0].time_s == 0.0
    assert report.events[0].penetration_depth_m > 0.0
    assert report.first_failure_time_s == 0.0


def test_interference_passes_for_separated_meshes(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2.0, 0, 0), (3.0, 0, 0)))
    report = check_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),)
    )
    assert report.passed
    assert not report.events


def test_interference_fails_when_exclusions_remove_every_pair(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = check_interference(
        assembly=assembly,
        motion_result=motion,
        excluded_pairs=(("a", "b"),),
    )
    assert not report.passed
    assert report.checked_component_pair_count == 0
    assert any(item.code == "KINCHECK-CLEARANCE-COMPONENT-PAIRS-EMPTY" for item in report.issues)


def test_interference_honors_penetration_tolerance(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((0.99, 0, 0), (2, 0, 0)))
    report = check_interference(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(("a", "b"),),
        penetration_tolerance_m=2.0,
    )
    assert report.passed
    assert not report.events


def test_interference_honors_time_window(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = check_interference(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(("a", "b"),),
        start_time_s=1.0,
        end_time_s=1.0,
    )
    assert report.passed
    assert report.checked_sample_count == 1


def test_minimum_clearance_returns_signed_separation(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2.0, 0, 0), (3.0, 0, 0)))
    report = measure_minimum_clearance(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),)
    )
    assert report.passed
    assert report.measurements[0].minimum_clearance_m == pytest.approx(1.0)
    assert report.measurements[0].closest_point_a_m is not None
    assert report.measurements[0].closest_point_b_m is not None


def test_minimum_clearance_fails_for_negative_signed_distance(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = measure_minimum_clearance(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),)
    )
    assert not report.passed
    assert report.measurements[0].minimum_clearance_m < 0.0


def test_minimum_clearance_honors_safety_threshold(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((1.6, 0, 0), (2, 0, 0)))
    report = measure_minimum_clearance(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(("a", "b"),),
        minimum_allowed_clearance_m=0.7,
    )
    assert not report.passed
    assert any(item.code == "KINCHECK-CLEARANCE-MINIMUM-BELOW-THRESHOLD" for item in report.issues)


def test_minimum_clearance_reports_coarse_sampling(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = measure_minimum_clearance(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(("a", "b"),),
        max_sample_period_s=0.5,
    )
    assert not report.passed
    assert any(item.code == "KINCHECK-CLEARANCE-SAMPLING-TOO-COARSE" for item in report.issues)


def test_minimum_clearance_rejects_unknown_pair(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = measure_minimum_clearance(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "missing"),)
    )
    assert not report.passed
    assert any(item.code == "KINCHECK-CLEARANCE-COMPONENT-PAIR-NOT-FOUND" for item in report.issues)


def test_empty_component_pairs_cannot_pass_without_checks(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2.0, 0, 0), (3.0, 0, 0)))
    interference = check_interference(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(),
    )
    clearance = measure_minimum_clearance(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(),
        minimum_allowed_clearance_m=0.1,
    )

    for report in (interference, clearance):
        assert not report.passed
        assert report.checked_component_pair_count == 0
        assert report.checked_sample_count == 0
        assert any(item.code == "KINCHECK-CLEARANCE-COMPONENT-PAIRS-EMPTY" for item in report.issues)
    assert not clearance.measurements


def test_motion_envelope_contains_transformed_mesh_bounds(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("a",))
    envelope = report.envelopes[0]
    assert report.passed
    assert envelope.world_min_position_m == pytest.approx((-0.5, -0.5, -0.5))
    assert envelope.world_max_position_m == pytest.approx((0.5, 0.5, 0.5))
    assert envelope.mesh_vertex_count > 0


def test_motion_envelope_rejects_unknown_component(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("missing",))
    assert not report.passed
    assert report.status == "failed"


def test_motion_envelope_rejects_explicit_empty_component_selection(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = create_motion_envelope(
        assembly=assembly,
        motion_result=motion,
        component_ids=(),
    )

    assert not report.passed
    assert not report.envelopes
    assert report.metadata["component_ids"] == ()
    assert report.issues[0].code == "KINCHECK-CLEARANCE-COMPONENT-SELECTION-EMPTY"


def test_motion_envelope_uses_requested_time_window(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = create_motion_envelope(
        assembly=assembly,
        motion_result=motion,
        component_ids=("b",),
        start_time_s=1.0,
        end_time_s=1.0,
    )
    assert report.passed
    assert report.envelopes[0].sample_times_s == (1.0,)


def test_envelope_overlap_is_only_a_precheck(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    first = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("a",))
    second = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("b",))
    report = check_envelope_interference(first=first, second=second)
    assert not report.passed
    assert report.metadata["confirmed_mesh_interference"] is False


def test_clearance_fails_without_mesh_instead_of_falling_back(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    broken = AssemblyModel(
        assembly_id=assembly.assembly_id,
        parts=(Part(part_id="part-a", asset_paths={"stl": "does-not-exist.stl"}), assembly.parts[1]),
        components=assembly.components,
        metadata=assembly.metadata,
    )
    report = check_interference(assembly=broken, motion_result=motion, component_pairs=(("a", "b"),))
    assert not report.passed
    assert any(item.code == "KINCHECK-CLEARANCE-MESH-NOT-FOUND" for item in report.issues)


def test_solver_step_scope_requires_recorded_backend_samples(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    report = check_interference(
        assembly=assembly,
        motion_result=motion,
        component_pairs=(("a", "b"),),
        sampling_scope="solver_steps",
    )
    assert not report.passed
    assert "integration-step" in report.issues[0].message


def test_solver_step_scope_reads_recorded_backend_samples(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    raw = tuple(
        {
            "time_s": time,
            "component_poses": {
                "a": {"position_m": list(Pose().position_m), "orientation_xyzw": list(Pose().orientation_xyzw)},
                "b": {"position_m": list(pose.position_m), "orientation_xyzw": list(pose.orientation_xyzw)},
            },
        }
        for time, pose in ((0.0, Pose(position_m=(2, 0, 0))), (0.5, Pose(position_m=(3, 0, 0))))
    )
    motion_with_steps = MotionResult(
        scenario_id=motion.scenario_id,
        assembly_id=motion.assembly_id,
        status="completed",
        start_time_s=motion.start_time_s,
        end_time_s=motion.end_time_s,
        sample_times_s=motion.sample_times_s,
        trajectories=motion.trajectories,
        metadata={"integration_samples": raw},
    )
    report = check_interference(
        assembly=assembly,
        motion_result=motion_with_steps,
        component_pairs=(("a", "b"),),
        sampling_scope="solver_steps",
    )
    assert report.passed
    assert report.checked_sample_count == 2


def test_run_checks_dispatches_all_geometry_checks(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    suite = run_checks(
        assembly=assembly,
        motion_result=motion,
        checks=(
            CheckSpec(check_id="collision", check_type="interference", parameters={"component_pairs": (("a", "b"),)}),
            CheckSpec(check_id="gap", check_type="minimum_clearance", parameters={"component_pairs": (("a", "b"),)}),
            CheckSpec(check_id="sweep", check_type="motion_envelope", parameters={"component_ids": ("a",)}),
        ),
    )
    assert suite.passed
    assert [item.check_type for item in suite.reports] == ["interference", "minimum_clearance", "motion_envelope"]


def test_run_checks_rejects_partial_motion_result(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    partial = replace(motion, status="partial")
    suite = run_checks(
        assembly=assembly,
        motion_result=partial,
        checks=(
            CheckSpec(
                check_id="collision",
                check_type="interference",
                parameters={"component_pairs": (("a", "b"),)},
            ),
        ),
    )

    assert not suite.passed
    assert not suite.reports[0].passed
    assert suite.reports[0].metadata["status"] == "partial"
    assert any(
        item.code == "KINCHECK-CLEARANCE-MOTION-RESULT-INCOMPLETE"
        for item in suite.reports[0].issues
    )


def test_geometry_checks_require_motion_result(tmp_path: Path):
    assembly, _ = _fixture(tmp_path)
    suite = run_checks(
        assembly=assembly,
        checks=(CheckSpec(check_id="collision", check_type="interference"),),
    )
    assert not suite.passed
    assert suite.reports[0].issues[0].code == "KINCHECK-CHECK-MOTION-RESULT-REQUIRED"


def test_report_roundtrips_to_json_shape(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = measure_minimum_clearance(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),)
    )
    payload = report.to_dict()
    assert payload["backend_id"] == "python-fcl"
    assert payload["measurements"][0]["component_a_id"] == "a"


def test_motion_envelope_json_records_schema_units_and_mesh_hash(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("a",))
    path = tmp_path / "envelope.json"
    write_motion_envelope(report=report, path=path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "kincheck.motion-envelope/1.0"
    assert payload["units"]["length"] == "m"
    assert len(payload["report"]["envelopes"][0]["mesh_sha256"]) == 64


def test_solve_motion_records_real_integration_step_poses(ex3_assembly):
    condition = scenario.create_scenario(
        scenario_id="v030-integration-samples",
        assembly=ex3_assembly,
    )
    condition = scenario.add_joint_speed_driver(
        scenario=condition,
        joint_id="joint.ex3.ground_crank",
        speed_rad_s_or_m_s=1e-4,
        start_time_s=0.0,
        end_time_s=1e-3,
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=1e-3)
    condition = scenario.set_sample_period(scenario=condition, period_s=1e-3)
    condition = scenario.set_capture_integration_steps(scenario=condition, enabled=True)
    motion = kinematics.solve_motion(scenario=condition)
    samples = motion.metadata["integration_samples"]
    assert len(samples) == motion.metadata["integration_sample_count"]
    assert len(samples) > len(motion.sample_times_s)
    assert tuple(item["time_s"] for item in samples) == pytest.approx(
        tuple(index * 2e-5 for index in range(51))
    )
    assert set(samples[0]["component_poses"]) == {
        component.component_id for component in ex3_assembly.components
    }


def _nested_fixture(tmp_path: Path, *, outer_first: bool = True):
    assembly, motion = _fixture(tmp_path, second_positions=((0, 0, 0), (0, 0, 0)))
    outer = trimesh.creation.box(extents=(2.0, 2.0, 2.0))
    inner = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    if outer_first:
        outer.export(tmp_path / "a.stl")
        inner.export(tmp_path / "b.stl")
        return assembly, motion
    outer.export(tmp_path / "b.stl")
    inner.export(tmp_path / "a.stl")
    return assembly, motion


@pytest.mark.parametrize("outer_first", (True, False))
def test_closed_solid_containment_is_interference_in_both_directions(tmp_path: Path, outer_first: bool):
    assembly, motion = _nested_fixture(tmp_path, outer_first=outer_first)
    report = check_interference(assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),))
    assert not report.passed
    assert len(report.events) == 2
    assert report.events[0].penetration_depth_m == pytest.approx(0.5)


def test_closed_solid_containment_has_negative_signed_clearance(tmp_path: Path):
    assembly, motion = _nested_fixture(tmp_path)
    report = measure_minimum_clearance(assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),))
    assert report.measurements[0].minimum_clearance_m == pytest.approx(-0.5)


@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf, -1.0))
def test_interference_rejects_invalid_penetration_tolerance(tmp_path: Path, value: float):
    assembly, motion = _fixture(tmp_path)
    report = check_interference(assembly=assembly, motion_result=motion, penetration_tolerance_m=value)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CLEARANCE-PARAMETER-INVALID"


@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf, -1.0))
def test_minimum_clearance_rejects_invalid_threshold(tmp_path: Path, value: float):
    assembly, motion = _fixture(tmp_path)
    report = measure_minimum_clearance(assembly=assembly, motion_result=motion, minimum_allowed_clearance_m=value)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CLEARANCE-PARAMETER-INVALID"


def test_fcl_runtime_error_becomes_failed_report(tmp_path: Path, monkeypatch):
    assembly, motion = _fixture(tmp_path)
    monkeypatch.setattr(clearance_module, "query_pair", lambda *args: (_ for _ in ()).throw(RuntimeError("FCL failed")))
    report = check_interference(assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),))
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CLEARANCE-QUERY-FAILED"


def test_partial_motion_result_cannot_produce_a_complete_geometry_pass(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    partial = replace(motion, status="partial")
    reports = (
        check_interference(
            assembly=assembly,
            motion_result=partial,
            component_pairs=(("a", "b"),),
        ),
        measure_minimum_clearance(
            assembly=assembly,
            motion_result=partial,
            component_pairs=(("a", "b"),),
        ),
        create_motion_envelope(
            assembly=assembly,
            motion_result=partial,
            component_ids=("a",),
        ),
    )

    for report in reports:
        assert not report.passed
        assert report.status == "partial"
        assert report.checked_sample_count == 2
        assert any(
            item.code == "KINCHECK-CLEARANCE-MOTION-RESULT-INCOMPLETE"
            for item in report.issues
        )
    assert reports[1].measurements
    assert reports[2].envelopes


def test_malformed_assembly_collision_exclusion_is_a_structured_failure(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    malformed = replace(assembly, collision_exclusions=(("a",),))
    report = check_interference(
        assembly=malformed,
        motion_result=motion,
        component_pairs=(("a", "b"),),
    )

    assert not report.passed
    assert report.checked_component_pair_count == 1
    assert any(
        item.code == "KINCHECK-CLEARANCE-COMPONENT-PAIR-INVALID"
        for item in report.issues
    )


@pytest.mark.parametrize("field", ("component_pairs", "excluded_pairs"))
def test_malformed_requested_pair_is_a_structured_failure(tmp_path: Path, field: str):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    parameters = {
        "assembly": assembly,
        "motion_result": motion,
        "component_pairs": (("a", "b"),),
        field: (("a",),),
    }
    report = check_interference(**parameters)

    assert not report.passed
    assert any(
        item.code == "KINCHECK-CLEARANCE-COMPONENT-PAIR-INVALID"
        for item in report.issues
    )


@pytest.mark.parametrize("raw", (
    ({"component_poses": {"a": {"position_m": [0, 0, 0], "orientation_xyzw": [0, 0, 0, 1]}}},),
    ({"time_s": 0.0, "component_poses": {"a": {"orientation_xyzw": [0, 0, 0, 1]}}},),
    ({"time_s": 0.0, "component_poses": {"a": {"position_m": [0, 0], "orientation_xyzw": [0, 0, 0, 1]}}},),
))
def test_malformed_solver_samples_become_failed_report(tmp_path: Path, raw):
    assembly, motion = _fixture(tmp_path)
    malformed = replace(motion, metadata={"integration_samples": raw})
    report = check_interference(assembly=assembly, motion_result=malformed, component_pairs=(("a", "b"),), sampling_scope="solver_steps")
    assert not report.passed
    assert report.issues[0].code.startswith("KINCHECK-CLEARANCE-")


def test_failed_envelope_cannot_become_a_pass(tmp_path: Path):
    assembly, motion = _fixture(tmp_path)
    failed = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("missing",))
    valid = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("a",))
    report = check_envelope_interference(first=failed, second=valid)
    assert not report.passed
    assert any(item.code == "KINCHECK-CLEARANCE-ENVELOPE-INPUT-FAILED" for item in report.issues)


def test_empty_envelope_cannot_become_a_pass():
    empty = ClearanceReport(operation="motion_envelope", passed=True, status="passed")
    report = check_envelope_interference(first=empty, second=empty)
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CLEARANCE-ENVELOPE-EMPTY"


def test_explicit_pair_does_not_load_unrelated_missing_mesh(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    unrelated = Part(part_id="part-c", asset_paths={"stl": "missing.stl"})
    expanded = AssemblyModel(
        assembly_id=assembly.assembly_id,
        parts=(*assembly.parts, unrelated),
        components=(*assembly.components, Component(component_id="c", part_id="part-c")),
        metadata=assembly.metadata,
    )
    report = check_interference(assembly=expanded, motion_result=motion, component_pairs=(("a", "b"),))
    assert report.passed


def test_motion_envelope_records_bounds_for_each_sample(tmp_path: Path):
    assembly, motion = _fixture(tmp_path, second_positions=((2, 0, 0), (3, 0, 0)))
    report = create_motion_envelope(assembly=assembly, motion_result=motion, component_ids=("b",))
    bounds = report.envelopes[0].sample_bounds
    assert tuple(item.time_s for item in bounds) == (0.0, 1.0)
    assert bounds[0].world_min_position_m == pytest.approx((1.5, -0.5, -0.5))
    assert bounds[1].world_max_position_m == pytest.approx((3.5, 0.5, 0.5))


def test_solve_motion_does_not_capture_integration_steps_by_default(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-no-step-capture", assembly=ex3_assembly)
    condition = scenario.add_joint_speed_driver(scenario=condition, joint_id="joint.ex3.ground_crank", speed_rad_s_or_m_s=1e-4, start_time_s=0.0, end_time_s=1e-3)
    condition = scenario.set_run_duration(scenario=condition, duration_s=1e-3)
    condition = scenario.set_sample_period(scenario=condition, period_s=1e-3)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.metadata["integration_samples"] == ()
    assert motion.metadata["integration_sample_count"] == 0


def test_solver_step_capture_can_select_components(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-selected-step-capture", assembly=ex3_assembly)
    condition = scenario.add_joint_speed_driver(scenario=condition, joint_id="joint.ex3.ground_crank", speed_rad_s_or_m_s=1e-4, start_time_s=0.0, end_time_s=1e-3)
    condition = scenario.set_run_duration(scenario=condition, duration_s=1e-3)
    condition = scenario.set_sample_period(scenario=condition, period_s=1e-3)
    condition = scenario.set_capture_integration_steps(scenario=condition, enabled=True, component_ids=("cmp.ex3.coupler",))
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.metadata["integration_samples"]
    assert set(motion.metadata["integration_samples"][0]["component_poses"]) == {"cmp.ex3.coupler"}


def test_solver_step_capture_is_immutable_and_defaults_off(ex3_assembly):
    original = scenario.create_scenario(scenario_id="v030-capture-default", assembly=ex3_assembly)
    changed = scenario.set_capture_integration_steps(scenario=original, enabled=True)
    assert original.capture_integration_steps is False
    assert changed.capture_integration_steps is True


def test_solver_step_capture_rejects_unknown_component(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-capture-unknown", assembly=ex3_assembly)
    with pytest.raises(ScenarioValidationError) as caught:
        scenario.set_capture_integration_steps(scenario=condition, enabled=True, component_ids=("missing",))
    assert getattr(caught.value, "code", None) == "KINCHECK-SCENARIO-COMPONENT-NOT-FOUND"


def test_solver_step_capture_rejects_empty_component_selection(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-capture-empty", assembly=ex3_assembly)
    with pytest.raises(ScenarioValidationError) as caught:
        scenario.set_capture_integration_steps(scenario=condition, enabled=True, component_ids=())
    assert getattr(caught.value, "code", None) == "KINCHECK-SCENARIO-CAPTURE-INVALID"


def test_solver_step_capture_round_trips_scenario_json(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-capture-roundtrip", assembly=ex3_assembly)
    condition = scenario.set_capture_integration_steps(scenario=condition, enabled=True, component_ids=("cmp.ex3.coupler",))
    restored = scenario.scenario_from_dict(assembly=ex3_assembly, data=scenario.scenario_to_dict(scenario=condition))
    assert scenario.scenario_to_dict(scenario=restored) == scenario.scenario_to_dict(scenario=condition)


def test_disabling_solver_step_capture_clears_component_filter(ex3_assembly):
    condition = scenario.create_scenario(scenario_id="v030-capture-disable", assembly=ex3_assembly)
    condition = scenario.set_capture_integration_steps(scenario=condition, enabled=True, component_ids=("cmp.ex3.coupler",))
    disabled = scenario.set_capture_integration_steps(scenario=condition, enabled=False, component_ids=("cmp.ex3.crank",))
    assert disabled.capture_integration_steps is False
    assert disabled.integration_component_ids is None


@pytest.mark.parametrize("offset, expected", ((0.0, True), (0.4, False), (2.0, False)))
def test_containment_batches_match_complete_vertex_query(tmp_path, monkeypatch, offset, expected):
    import numpy as np
    from kincheckapi import _clearance_fcl as backend
    assembly, _ = _fixture(tmp_path)
    sphere = trimesh.creation.icosphere(subdivisions=3, radius=0.2)
    sphere.apply_translation((offset, 0, 0))
    sphere.export(tmp_path / "b.stl")
    outer, candidate = [backend.load_mesh(assembly=assembly, part=p, asset_root=tmp_path) for p in assembly.parts]
    surface = trimesh.Trimesh(vertices=outer.vertices, faces=outer.faces, process=False)
    reference = bool(np.all(surface.contains(candidate.vertices)))
    assert reference is expected
    original = trimesh.Trimesh.contains
    counts = []

    def counted(self, points):
        counts.append(len(points))
        return original(self, points)

    monkeypatch.setattr(trimesh.Trimesh, "contains", counted)
    assert backend._contains_any_closed_component(outer, Pose(), candidate, Pose()) is expected
    if expected:
        assert sum(counts) == len(candidate.vertices)
    if offset == 2.0:
        assert sum(counts) < len(candidate.vertices)


def test_containment_still_checks_later_disconnected_solids(tmp_path):
    from kincheckapi import _clearance_fcl as backend
    assembly, _ = _fixture(tmp_path)
    outside = trimesh.creation.icosphere(subdivisions=2, radius=0.1)
    outside.apply_translation((2, 0, 0))
    inside = trimesh.creation.icosphere(subdivisions=2, radius=0.1)
    trimesh.util.concatenate((outside, inside)).export(tmp_path / "b.stl")
    outer, candidate = [backend.load_mesh(assembly=assembly, part=p, asset_root=tmp_path) for p in assembly.parts]
    assert len(candidate.component_vertex_indices) == 2
    assert backend._contains_any_closed_component(outer, Pose(), candidate, Pose())
