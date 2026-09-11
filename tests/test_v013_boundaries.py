from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi import kinematics, scenario
from kincheckapi.assembly import AssemblyModel, Component
from kincheckapi.errors import AssemblyValidationError, ScenarioValidationError


def _invalid_assembly() -> AssemblyModel:
    return AssemblyModel(
        assembly_id="assembly.invalid",
        components=(Component(component_id="component.a", part_id="part.missing"),),
    )


def test_solve_motion_validates_assembly_before_backend_compile():
    condition = scenario.create_scenario(
        scenario_id="scenario.invalid-assembly", assembly=_invalid_assembly()
    )
    with pytest.raises(AssemblyValidationError) as caught:
        kinematics.solve_motion(scenario=condition)
    assert caught.value.code == "KINCHECK-ASSEMBLY-VALIDATION-FAILED"
    assert "assembly.missing_part" in {item.code for item in caught.value.report.issues}


def test_assembly_validation_failure_keeps_object_ids_in_report():
    condition = scenario.create_scenario(
        scenario_id="scenario.invalid-assembly-ids", assembly=_invalid_assembly()
    )
    with pytest.raises(AssemblyValidationError) as caught:
        kinematics.solve_motion(scenario=condition)
    issue = next(item for item in caught.value.report.issues if item.code == "assembly.missing_part")
    assert issue.object_ids == ("component.a", "part.missing")


def test_try_solve_motion_maps_assembly_validation_to_validation_failed():
    condition = scenario.create_scenario(
        scenario_id="scenario.invalid-assembly-attempt", assembly=_invalid_assembly()
    )
    attempt = kinematics.try_solve_motion(scenario=condition)
    assert attempt.status == "validation_failed"
    assert not attempt.succeeded
    assert attempt.motion_result is None
    assert isinstance(attempt.failure, AssemblyValidationError)


def test_scenario_validation_remains_a_distinct_second_gate(ex1_assembly):
    condition = scenario.create_scenario(
        scenario_id="scenario.invalid-time", assembly=ex1_assembly
    )
    invalid = replace(condition, duration_s=-1.0)
    with pytest.raises(ScenarioValidationError) as caught:
        kinematics.solve_motion(scenario=invalid)
    assert caught.value.code == "KINCHECK-SCENARIO-VALIDATION-FAILED"


def test_valid_example_reaches_backend_after_assembly_gate(ex1_assembly):
    condition = scenario.create_scenario(
        scenario_id="scenario.valid-gate", assembly=ex1_assembly
    )
    condition = scenario.set_run_duration(scenario=condition, duration_s=0.02)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.02)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status in {"completed", "completed_with_warnings"}
