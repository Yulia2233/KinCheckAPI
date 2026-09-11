from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import kincheckapi.kinematics_analysis as analysis
from kincheckapi import kinematics
from kincheckapi.kinematics_analysis import SingularityOptions
from kincheckapi.result import JointTrajectory, MotionResult


def _motion(ex3_assembly, *, times=(0.0, 1.0)) -> MotionResult:
    trajectories = tuple(
        JointTrajectory(
            joint_id=joint.joint_id,
            times_s=times,
            positions=(0.0,) * len(times),
            velocities=(0.0,) * len(times),
            accelerations=(0.0,) * len(times),
        )
        for joint in ex3_assembly.joints
        if joint.joint_type.value != "fixed"
    )
    return MotionResult(
        scenario_id="scenario.v031.singular",
        assembly_id=ex3_assembly.assembly_id,
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        joint_trajectories=trajectories,
    )


def _jacobian(*, rank, singular_values):
    return SimpleNamespace(rank=rank, singular_values=singular_values)


def test_zero_rank_is_singular_at_every_frame(ex3_assembly, monkeypatch):
    monkeypatch.setattr(
        analysis,
        "_jacobian_for",
        lambda **_: _jacobian(rank=0, singular_values=(0.0,)),
    )
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly), assembly=ex3_assembly
    )
    assert [sample.status for sample in report.samples] == ["singular", "singular"]
    assert report.singular_times_s == (0.0, 1.0)
    assert all(sample.minimum_singular_value is None for sample in report.samples)


def test_first_frame_absolute_singularity_is_not_regular(ex3_assembly, monkeypatch):
    values = iter(
        (
            _jacobian(rank=1, singular_values=(1e-10,)),
            _jacobian(rank=1, singular_values=(1.0,)),
        )
    )
    monkeypatch.setattr(analysis, "_jacobian_for", lambda **_: next(values))
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly),
        assembly=ex3_assembly,
        options=SingularityOptions(tolerance=1e-8, near_tolerance=1e-4),
    )
    assert report.samples[0].status == "singular"
    assert report.samples[1].status == "regular"
    assert report.singular_times_s == (0.0,)


def test_rank_drop_can_only_make_status_more_severe(ex3_assembly, monkeypatch):
    values = iter(
        (
            _jacobian(rank=2, singular_values=(2.0, 1.0)),
            _jacobian(rank=1, singular_values=(2.0, 1.0)),
        )
    )
    monkeypatch.setattr(analysis, "_jacobian_for", lambda **_: next(values))
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly), assembly=ex3_assembly
    )
    assert report.samples[0].status == "regular"
    assert report.samples[1].status == "singular"


def test_near_and_regular_threshold_boundaries(ex3_assembly, monkeypatch):
    values = iter(
        (
            _jacobian(rank=1, singular_values=(1e-5,)),
            _jacobian(rank=1, singular_values=(1e-2,)),
        )
    )
    monkeypatch.setattr(analysis, "_jacobian_for", lambda **_: next(values))
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly),
        assembly=ex3_assembly,
        options=SingularityOptions(tolerance=1e-8, near_tolerance=1e-4),
    )
    assert [sample.status for sample in report.samples] == ["near_singular", "regular"]
    assert report.passed
    assert any(issue.severity == "warning" for issue in report.issues)


def test_unavailable_jacobian_is_an_error_sample(ex3_assembly, monkeypatch):
    monkeypatch.setattr(
        analysis,
        "_jacobian_for",
        lambda **_: (_ for _ in ()).throw(RuntimeError("jacobian failed")),
    )
    report = kinematics.find_singularities(
        motion_result=_motion(ex3_assembly, times=(0.0,)), assembly=ex3_assembly
    )
    assert not report.passed
    assert report.samples[0].status == "unavailable"
    assert report.issues[0].code == "KINCHECK-KIN-SINGULARITY-UNAVAILABLE"


def test_partial_motion_classifies_samples_but_cannot_pass(ex3_assembly, monkeypatch):
    monkeypatch.setattr(
        analysis,
        "_jacobian_for",
        lambda **_: _jacobian(rank=1, singular_values=(1.0,)),
    )
    motion = replace(_motion(ex3_assembly), status="partial")
    report = kinematics.find_singularities(
        motion_result=motion, assembly=ex3_assembly
    )
    assert not report.passed
    assert all(sample.status == "regular" for sample in report.samples)
    assert any(
        issue.code == "KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE"
        for issue in report.issues
    )


def test_singularity_report_serialization_is_repeatable(ex3_assembly, monkeypatch):
    monkeypatch.setattr(
        analysis,
        "_jacobian_for",
        lambda **_: _jacobian(rank=2, singular_values=(2.0, 1.0)),
    )
    motion = _motion(ex3_assembly)
    first = kinematics.find_singularities(
        motion_result=motion, assembly=ex3_assembly
    ).to_dict()
    second = kinematics.find_singularities(
        motion_result=motion, assembly=ex3_assembly
    ).to_dict()
    assert first == second
    assert first["samples"][0]["rank"] == 2
    assert first["samples"][0]["minimum_singular_value"] == 1.0
