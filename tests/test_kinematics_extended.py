from __future__ import annotations

import pytest

from kincheckapi import dynamics, kinematics
from kincheckapi.diagnostics import DiagnosticReport, Fix, apply_assembly_fix, apply_scenario_fix
from kincheckapi.errors import BackendCapabilityError


def test_position_solver_returns_structured_invalid_joint_result(ex3_assembly):
    result = kinematics.solve_position(
        assembly=ex3_assembly, joint_positions={"component.a": 0.0}
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-POSITION-JOINT-NOT-FOUND"


def test_reachability_returns_structured_missing_target(ex3_assembly):
    report = kinematics.check_reachability(
        assembly=ex3_assembly,
        target={"component_id": "missing.component", "pose": kinematics.Pose()},
    )
    assert not report.reachable
    assert report.issues


def test_singularity_requires_a_motion_result():
    with pytest.raises(TypeError):
        kinematics.find_singularities(assembly=object())


def test_connector_path_reports_missing_recorded_trajectory():
    result = kinematics.trace_connector_path(
        motion_result=object(), component_id="component.a", connector_id="connector.a"
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-RESULT-TRAJECTORY-MISSING"


@pytest.mark.parametrize("apply_fix", [apply_assembly_fix, apply_scenario_fix])
def test_unimplemented_automatic_fixes_raise_stable_capability_error(apply_fix):
    fix = Fix(operation="set_value", target_id="joint.1", parameters={"value": 1.0})
    argument = {"assembly": "assembly"} if apply_fix is apply_assembly_fix else {"scenario": "scenario"}
    with pytest.raises(BackendCapabilityError) as caught:
        apply_fix(fix=fix, **argument)
    assert caught.value.code == "KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED"
    assert caught.value.object_ids == ("joint.1",)


def test_dynamics_namespace_remains_explicitly_empty():
    public_names = {name for name in vars(dynamics) if not name.startswith("_")}
    assert public_names == set()
