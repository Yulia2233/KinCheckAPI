from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import trimesh

from kincheckapi.assembly import AssemblyModel, Component, Part
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.clearance import check_continuous_interference
from kincheckapi.continuous_result import (
    ContinuousInterferenceOptions,
    ContinuousInterferenceReport,
)
from kincheckapi.pose import Pose
from kincheckapi.result import MotionResult, Trajectory
from kincheckapi.errors import BackendCapabilityError, VerificationError
from kincheckapi.export import motion_package, read_package
from kincheckapi.result import record_verification_reports


def _scene(tmp_path: Path, *, crossing: bool = True):
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    assembly = AssemblyModel(
        assembly_id="continuous-assembly",
        parts=(Part(part_id="pa", asset_paths={"stl": "a.stl"}), Part(part_id="pb", asset_paths={"stl": "b.stl"})),
        components=(Component(component_id="a", part_id="pa"), Component(component_id="b", part_id="pb")),
        metadata={"asset_root": str(tmp_path)},
    )
    a_positions = ((-2.0, 0.0, 0.0), (2.0, 0.0, 0.0)) if crossing else ((-3.0, 0.0, 0.0), (-2.0, 0.0, 0.0))
    b_positions = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) if crossing else ((3.0, 0.0, 0.0), (2.0, 0.0, 0.0))
    motion = MotionResult(
        scenario_id="continuous-scenario", assembly_id=assembly.assembly_id,
        status="completed", start_time_s=0.0, end_time_s=1.0, sample_times_s=(0.0, 1.0),
        trajectories=(
            Trajectory(component_id="a", times_s=(0.0, 1.0), poses=tuple(Pose(position_m=p) for p in a_positions)),
            Trajectory(component_id="b", times_s=(0.0, 1.0), poses=tuple(Pose(position_m=p) for p in b_positions)),
        ),
    )
    return assembly, motion


def test_continuous_check_finds_collision_between_samples(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=ContinuousInterferenceOptions(time_tolerance_s=1e-3),
    )
    assert report.status == "failed"
    assert not report.passed
    assert report.events[0].confirmed
    assert report.events[0].state_time_s == 0.25
    assert report.events[0].relative_speed_m_s == pytest.approx(4.0)
    assert report.events[0].pre_contact_time_s is not None
    if report.events[0].closing_speed_m_s:
        assert report.events[0].contact_angle_rad is not None
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-TOI-BRACKETED"


def test_continuous_check_certifies_safe_interval(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    assert report.status == "passed"
    assert report.passed
    assert report.clearance_lower_bound_m is not None
    assert report.clearance_lower_bound_m > 0.0
    assert report.events == ()


def test_continuous_check_reports_contact_at_interval_endpoint(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    trajectory = motion.trajectories[0]
    endpoint_motion = replace(
        motion,
        trajectories=(
            replace(trajectory, poses=(Pose(position_m=(-2.0, 0.0, 0.0)), Pose(position_m=(-1.0, 0.0, 0.0)))),
            replace(motion.trajectories[1], poses=(Pose(), Pose())),
        ),
    )
    report = check_continuous_interference(
        assembly=assembly, motion_result=endpoint_motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=ContinuousInterferenceOptions(time_tolerance_s=1e-4),
    )
    assert report.status == "failed"
    assert report.first_failure_time_s == pytest.approx(1.0)


def test_continuous_check_reports_initial_overlap(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    overlap_motion = replace(
        motion,
        trajectories=(
            replace(motion.trajectories[0], poses=(Pose(position_m=(0.0, 0.0, 0.0)), Pose(position_m=(0.0, 0.0, 0.0)))),
            motion.trajectories[1],
        ),
    )
    report = check_continuous_interference(
        assembly=assembly, motion_result=overlap_motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    assert report.status == "failed"
    assert report.events[0].event_type == "initial_overlap"
    assert report.first_failure_time_s == 0.0


def test_linear_pose_rejects_changing_orientation(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    rotating = replace(
        motion,
        trajectories=(
            replace(motion.trajectories[0], poses=(Pose(), Pose(orientation_xyzw=(0.0, 0.0, 1.0, 0.0)))),
            motion.trajectories[1],
        ),
    )
    report = check_continuous_interference(
        assembly=assembly, motion_result=rotating, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=ContinuousInterferenceOptions(interpolation="linear_pose"),
    )
    assert report.status == "validation_failed"
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-INTERPOLATION-INVALID"


def test_continuous_check_backend_failure_is_capability_status(tmp_path, monkeypatch):
    assembly, motion = _scene(tmp_path, crossing=False)

    def unavailable():
        raise BackendCapabilityError(
            code="KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE",
            message="FCL is unavailable",
            missing_capabilities=("python-fcl",),
            operation="check_continuous_interference",
        )

    monkeypatch.setattr("kincheckapi.clearance.require_backend", unavailable)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    assert report.status == "capability_failed"
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-BACKEND-UNSUPPORTED"
    with pytest.raises(VerificationError) as raised:
        report.raise_if_failed()
    assert raised.value.report.status == "capability_failed"


def test_continuous_check_rejects_malformed_component_pair(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a",),), asset_root=tmp_path,
    )
    assert report.status == "validation_failed"
    assert report.issues[0].code == "KINCHECK-CLEARANCE-COMPONENT-PAIR-INVALID"


def test_continuous_check_rejects_invalid_options(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options={"time_tolerance_s": 0.0},
    )
    assert report.status == "validation_failed"
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-PARAMETER-INVALID"


def test_continuous_report_is_indeterminate_when_budget_cannot_prove_safety(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=ContinuousInterferenceOptions(max_subdivisions=1, distance_tolerance_m=100.0),
    )
    assert report.status == "indeterminate"
    assert not report.passed
    assert report.issues[0].code == "KINCHECK-CLEARANCE-CONTINUOUS-TOI-INDETERMINATE"


def test_continuous_check_retains_observed_collision_when_toi_budget_expires(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=ContinuousInterferenceOptions(max_queries=3),
    )
    assert report.status == "failed"
    assert report.events[0].confirmed
    assert report.events[0].time_interval_s == (0.0, 0.5)
    evidence = {item.key: item.actual for item in report.events[0].evidence}
    assert evidence["toi_tolerance_met"] is False
    assert "max_queries" in evidence["budget_limits_reached"]
    assert any(item.code == "KINCHECK-CLEARANCE-CONTINUOUS-TOI-INDETERMINATE" for item in report.issues)


def test_continuous_report_survives_kincheck_package_round_trip(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    motion_with_report = record_verification_reports(motion_result=motion, reports=(report,))
    package_path = tmp_path / "continuous.kincheck"
    motion_package(assembly=assembly, motion_result=motion_with_report, output_path=package_path, asset_root=tmp_path, require_meshes=True)
    restored = read_package(path=package_path)
    stored = restored.motion_result.metadata["verification_reports"][0]
    assert stored["schema_version"] == "kincheck.continuous/1.0"
    assert stored["status"] == "failed"
    assert stored["events"][0]["certainty"] == "bracketed"


def test_continuous_partial_motion_never_passes(tmp_path):
    assembly, motion = _scene(tmp_path)
    partial = replace(motion, status="partial")
    report = check_continuous_interference(
        assembly=assembly, motion_result=partial, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    assert report.status == "partial"
    assert not report.passed


def test_run_checks_exposes_indeterminate_status(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=False)
    suite = run_checks(
        assembly=assembly, motion_result=motion,
        checks=(CheckSpec(check_id="ccd", check_type="continuous_interference", parameters={
            "component_pairs": (("a", "b"),), "asset_root": tmp_path,
            "options": ContinuousInterferenceOptions(max_subdivisions=1, distance_tolerance_m=100.0),
        }),),
    )
    assert suite.status == "indeterminate"
    assert suite.reports[0].status == "indeterminate"
    assert suite.to_dict()["status"] == "indeterminate"


def test_continuous_round_trip_preserves_event_and_options(tmp_path):
    assembly, motion = _scene(tmp_path, crossing=True)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    restored = ContinuousInterferenceReport.from_dict(report.to_dict())
    assert restored.to_dict() == report.to_dict()
    assert restored.events[0].certainty == "bracketed"


def _motion_with_poses(motion, poses_a, poses_b, times=(0.0, 1.0)):
    return replace(
        motion, sample_times_s=times, start_time_s=times[0], end_time_s=times[-1],
        trajectories=(
            Trajectory(component_id="a", times_s=times, poses=poses_a),
            Trajectory(component_id="b", times_s=times, poses=poses_b),
        ),
    )


@pytest.mark.parametrize("second_obstacle_x", (2.2, 3.0))
def test_toi_does_not_skip_first_of_two_disconnected_obstacles(tmp_path, second_obstacle_x):
    assembly, motion = _scene(tmp_path)
    trimesh.creation.box(extents=(0.2, 0.2, 0.2)).export(tmp_path / "a.stl")
    obstacles = [trimesh.creation.box(extents=(0.2, 0.2, 0.2)) for _ in range(2)]
    for obstacle, x in zip(obstacles, (1.0, second_obstacle_x)):
        obstacle.apply_translation((x, 0, 0))
    trimesh.util.concatenate(obstacles).export(tmp_path / "b.stl")
    motion = _motion_with_poses(motion, (Pose(), Pose(position_m=(3, 0, 0))), (Pose(), Pose()))
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    event = next(e for e in report.events if e.confirmed)
    expected_toi = 0.8 / 3
    lower, upper = event.time_interval_s
    assert lower <= expected_toi <= upper
    assert upper - lower <= 2e-5
    assert event.earliest_contact_time_s == pytest.approx(expected_toi, abs=1e-5)


@pytest.mark.parametrize("through_suite", (False, True))
def test_wrapper_rejects_misplaced_safety_threshold(tmp_path, through_suite):
    from kincheckapi import checks
    assembly, motion = _scene(tmp_path)
    motion = _motion_with_poses(motion, (Pose(), Pose()), (Pose(position_m=(1.1, 0, 0)),) * 2)
    parameters = {"component_pairs": (("a", "b"),), "asset_root": tmp_path, "minimum_clearance_m": 0.2}
    if through_suite:
        report = run_checks(assembly=assembly, motion_result=motion, checks=(
            CheckSpec(check_id="ccd", check_type="continuous_interference", parameters=parameters),
        )).reports[0]
    else:
        report = checks.check_continuous_interference(assembly=assembly, motion_result=motion, **parameters)
    assert report.status == "validation_failed"
    assert "minimum_clearance_m" in str(report.issues[0].evidence)
    assert "options" in " ".join(report.issues[0].suggested_actions)
    proper = checks.check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),),
        asset_root=tmp_path, options={"minimum_clearance_m": 0.2},
    )
    assert proper.status == "failed"


@pytest.mark.parametrize("report_normal", (True, False))
def test_contact_velocity_includes_pure_rotation(tmp_path, report_normal):
    import math
    import numpy as np
    assembly, motion = _scene(tmp_path)
    trimesh.creation.box(extents=(4, 0.2, 0.2)).export(tmp_path / "a.stl")
    trimesh.creation.box(extents=(0.2, 0.2, 0.2)).export(tmp_path / "b.stl")
    motion = _motion_with_poses(
        motion, (Pose(), Pose(orientation_xyzw=(0, 0, math.sin(math.pi / 4), math.cos(math.pi / 4)))),
        (Pose(position_m=(0, 1.6, 0)),) * 2,
    )
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options={"report_contact_normal": report_normal},
    )
    event = next(e for e in report.events if e.confirmed)
    expected = -np.cross((0, 0, math.pi / 2), event.position_a_m)
    assert np.linalg.norm(expected) > 2
    assert event.relative_velocity_m_s == pytest.approx(expected)
    assert event.relative_speed_m_s == pytest.approx(np.linalg.norm(expected))
    if event.contact_normal is not None:
        closing = max(0, -float(np.dot(expected, event.contact_normal)))
        assert event.closing_speed_m_s == pytest.approx(closing)
        if closing > 0:
            assert event.contact_angle_rad == pytest.approx(math.acos(closing / np.linalg.norm(expected)))
    else:
        assert event.contact_angle_rad is None
        assert event.closing_speed_m_s is None
    assert event.pre_contact_relative_velocity_m_s is not None
    assert np.linalg.norm(event.pre_contact_relative_velocity_m_s) > 2


@pytest.mark.parametrize("as_mapping", (False, True))
def test_query_budget_preserves_initial_collision_and_options(tmp_path, as_mapping):
    assembly, motion = _scene(tmp_path)
    motion = _motion_with_poses(motion, (Pose(),) * 3, (Pose(),) * 3, (0.0, 0.5, 1.0))
    opts = ContinuousInterferenceOptions(max_queries=1)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options=opts.to_dict() if as_mapping else opts,
    )
    assert report.status == "failed"
    assert report.query_count == 1
    assert report.options == opts
    assert report.events[0].confirmed
    assert report.first_failure_time_s == 0
    assert report.to_dict()["object_ids"] == ["a", "b"]
    assert report.metadata["coverage_complete"] is False
    assert any("query" in str(issue.evidence).lower() for issue in report.issues)


def test_failed_report_does_not_promote_local_safe_bound_to_global(tmp_path):
    assembly, motion = _scene(tmp_path)
    motion = _motion_with_poses(
        motion, tuple(Pose(position_m=(x, 0, 0)) for x in (-4, -3, 0)),
        (Pose(),) * 3, (0.0, 0.5, 1.0),
    )
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
    )
    assert report.status == "failed"
    assert report.clearance_lower_bound_m is None
    assert report.minimum_clearance_m <= 0


def test_query_budget_without_collision_remains_indeterminate(tmp_path):
    assembly, motion = _scene(tmp_path)
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), asset_root=tmp_path,
        options={"max_queries": 1},
    )
    assert report.status == "indeterminate"
    assert report.query_count == 1
    assert report.options.max_queries == 1
    assert not any(e.confirmed for e in report.events)
    assert report.clearance_lower_bound_m is None


@pytest.mark.parametrize("state", ("budget_failed", "safe_then_failed", "indeterminate"))
def test_repaired_evidence_survives_json_and_package_round_trip(tmp_path, state):
    import json
    assembly, motion = _scene(tmp_path)
    options = {"max_queries": 1}
    if state == "budget_failed":
        motion = _motion_with_poses(motion, (Pose(),) * 3, (Pose(),) * 3, (0., 0.5, 1.))
    elif state == "safe_then_failed":
        motion = _motion_with_poses(motion, tuple(Pose(position_m=(x, 0, 0)) for x in (-4, -3, 0)), (Pose(),) * 3, (0., 0.5, 1.))
        options = {}
    report = check_continuous_interference(
        assembly=assembly, motion_result=motion, component_pairs=(("a", "b"),), options=options, asset_root=tmp_path,
    )
    payload = json.loads(json.dumps(report.to_dict()))
    assert ContinuousInterferenceReport.from_dict(payload).to_dict() == payload
    path = tmp_path / "review.kincheck"
    motion_package(assembly=assembly, motion_result=record_verification_reports(motion_result=motion, reports=(report,)), output_path=path, asset_root=tmp_path)
    loaded = read_package(path=path)
    stored = loaded.motion_result.metadata["verification_reports"][0]
    assert ContinuousInterferenceReport.from_dict(stored).to_dict() == payload
    assert stored["clearance_lower_bound_m"] is None
    if state != "indeterminate":
        assert stored["minimum_clearance_m"] <= 0
    else:
        assert stored["status"] == "indeterminate"
