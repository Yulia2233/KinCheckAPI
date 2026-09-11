from __future__ import annotations

import pytest

from kincheckapi import kinematics
from kincheckapi.errors import BackendUnavailableError


def test_missing_backend_helper_preserves_original_import_error(monkeypatch):
    backend = pytest.importorskip("kincheckapi._backends.solver_backend")
    monkeypatch.setattr(backend, "mujoco", None)
    original = RuntimeError("optional runtime missing")
    monkeypatch.setattr(backend, "_BACKEND_IMPORT_ERROR", original)
    with pytest.raises(backend.BackendUnavailable) as caught:
        backend._require_backend()
    assert caught.value.__cause__ is original


def test_backend_unavailable_error_type_is_stable_when_runtime_is_missing(ex3_assembly, monkeypatch):
    backend = pytest.importorskip("kincheckapi._backends.solver_backend")
    from kincheckapi.scenario import Scenario

    scenario = Scenario(
        scenario_id="scenario.backend",
        assembly=ex3_assembly,
        duration_s=0.1,
        sample_period_s=0.1,
    )
    def unavailable(*, scenario):
        raise backend.BackendUnavailable("test runtime unavailable")

    import kincheckapi._backends as backend_package

    monkeypatch.setattr(backend_package, "solve_scenario", unavailable)
    with pytest.raises(BackendUnavailableError) as caught:
        kinematics.solve_motion(scenario=scenario)
    assert caught.value.code == "KINCHECK-BACKEND-UNAVAILABLE"
