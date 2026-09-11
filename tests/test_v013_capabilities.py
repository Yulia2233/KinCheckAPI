from __future__ import annotations

import pytest

from kincheckapi import clearance
from kincheckapi import _clearance_fcl
from kincheckapi.assembly import AssemblyModel
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.result import MotionResult
from kincheckapi.errors import BackendCapabilityError


def test_clearance_requires_all_exact_mesh_dependencies(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    monkeypatch.setattr(_clearance_fcl, "trimesh", None)
    monkeypatch.setattr(_clearance_fcl, "rtree", None)
    with pytest.raises(BackendCapabilityError) as caught:
        clearance.check_interference(assembly=object(), motion_result=object())
    error = caught.value
    assert error.code == "KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE"
    assert set(error.missing_capabilities) == {"python-fcl", "trimesh", "rtree"}
    assert error.report.issues[0].stage == "api"


def test_minimum_clearance_requires_fcl(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    with pytest.raises(BackendCapabilityError):
        clearance.measure_minimum_clearance(assembly=object(), motion_result=object())


def test_motion_envelope_requires_fcl(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    with pytest.raises(BackendCapabilityError):
        clearance.create_motion_envelope(assembly=object(), motion_result=object())


def test_mesh_backend_is_not_replaced_by_aabb(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    with pytest.raises(BackendCapabilityError) as caught:
        clearance.create_motion_envelope(assembly=object(), motion_result=object())
    assert "python-fcl" in caught.value.missing_capabilities


def test_backend_error_is_machine_serializable(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    with pytest.raises(BackendCapabilityError) as caught:
        clearance.check_interference(assembly=object(), motion_result=object())
    payload = caught.value.to_dict()
    assert payload["code"] == "KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE"
    assert payload["suggested_actions"]


def test_run_checks_turns_missing_backend_into_failed_report(monkeypatch):
    monkeypatch.setattr(_clearance_fcl, "fcl", None)
    assembly = AssemblyModel(assembly_id="assembly")
    motion = MotionResult(
        scenario_id="scenario",
        assembly_id="assembly",
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=(0.0, 1.0),
    )
    suite = run_checks(
        assembly=assembly,
        motion_result=motion,
        checks=(CheckSpec(check_id="collision", check_type="interference"),),
    )
    assert not suite.passed
    assert suite.reports[0].metadata["error"]["code"] == "KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE"
