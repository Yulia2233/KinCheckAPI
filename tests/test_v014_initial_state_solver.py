from __future__ import annotations

import pytest

from kincheckapi import kinematics, scenario
from kincheckapi._backends.solver_backend import (
    BackendInitialStateFailure,
    _LinearExpression,
    _solve_initial_state_system,
    _verify_initial_state_system,
    compile_assembly,
)
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
from kincheckapi.errors import ScenarioValidationError


def _chain_assembly() -> AssemblyModel:
    part = Part("part", connectors=(Connector("axis"),))
    return AssemblyModel(
        assembly_id="initial.chain",
        parts=(part,),
        components=(
            Component("ground", "part"),
            Component("first", "part"),
            Component("second", "part"),
        ),
        joints=(
            Joint(
                "joint.first",
                JointType.REVOLUTE,
                ConnectorRef("ground", "axis"),
                ConnectorRef("first", "axis"),
            ),
            Joint(
                "joint.second",
                JointType.REVOLUTE,
                ConnectorRef("first", "axis"),
                ConnectorRef("second", "axis"),
            ),
        ),
        grounds=(Ground("ground"),),
    )


def _condition(assembly: AssemblyModel) -> scenario.Scenario:
    value = scenario.create_scenario(scenario_id="initial.test", assembly=assembly)
    value = scenario.set_run_duration(scenario=value, duration_s=0.01)
    return scenario.set_sample_period(scenario=value, period_s=0.01)


def _shared_expression_compiled():
    compiled = compile_assembly(assembly=_chain_assembly())
    first_group = next(iter(compiled.joint_expressions["joint.first"].coefficients))
    compiled.group_joint_names = {
        first_group: compiled.group_joint_names[first_group]
    }
    compiled.joint_expressions = {
        "joint.first": _LinearExpression({first_group: 1.0}),
        "joint.second": _LinearExpression({first_group: 1.0}),
    }
    return compiled


def test_two_independent_joint_initial_positions_are_satisfied_together():
    value = _condition(_chain_assembly())
    value = scenario.set_initial_joint_position(
        scenario=value, joint_id="joint.first", position_rad_or_m=0.3
    )
    value = scenario.set_initial_joint_position(
        scenario=value, joint_id="joint.second", position_rad_or_m=-0.2
    )

    motion = kinematics.solve_motion(scenario=value)

    assert motion.get_joint_trajectory(joint_id="joint.first").positions[0] == pytest.approx(0.3)
    assert motion.get_joint_trajectory(joint_id="joint.second").positions[0] == pytest.approx(-0.2)
    assert motion.metadata["initial_state"]["position"]["status"] == "unique"


def test_consistent_shared_coordinate_is_solved_once_for_both_joints():
    compiled = _shared_expression_compiled()
    entries = (
        scenario.JointValue(joint_id="joint.second", value=0.25),
        scenario.JointValue(joint_id="joint.first", value=0.25),
    )

    values, diagnostics = _solve_initial_state_system(
        compiled=compiled, entries=entries, system="position"
    )

    assert next(iter(values.values())) == pytest.approx(0.25)
    assert diagnostics["status"] == "overconstrained_consistent"
    assert diagnostics["joint_ids"] == ["joint.first", "joint.second"]


def test_conflicting_shared_coordinate_is_reported_as_inconsistent():
    compiled = _shared_expression_compiled()
    entries = (
        scenario.JointValue(joint_id="joint.first", value=0.0),
        scenario.JointValue(joint_id="joint.second", value=1.0),
    )

    _values, diagnostics = _solve_initial_state_system(
        compiled=compiled, entries=entries, system="position"
    )

    assert diagnostics["status"] == "inconsistent"
    assert diagnostics["residual_norm"] > diagnostics["tolerance"]
    assert [item["joint_id"] for item in diagnostics["verification"]] == [
        "joint.first",
        "joint.second",
    ]


def test_one_target_in_two_coordinate_model_is_marked_underconstrained():
    compiled = compile_assembly(assembly=_chain_assembly())
    entries = (scenario.JointValue(joint_id="joint.first", value=0.4),)

    values, diagnostics = _solve_initial_state_system(
        compiled=compiled, entries=entries, system="position"
    )

    assert diagnostics["status"] == "underconstrained"
    assert diagnostics["rank"] < diagnostics["column_count"]
    assert sorted(values.values()) == pytest.approx([0.0, 0.4])


def test_position_and_velocity_system_diagnostics_remain_independent():
    compiled = _shared_expression_compiled()
    position_entries = (
        scenario.JointValue(joint_id="joint.first", value=0.2),
        scenario.JointValue(joint_id="joint.second", value=0.2),
    )
    velocity_entries = (
        scenario.JointValue(joint_id="joint.first", value=0.0),
        scenario.JointValue(joint_id="joint.second", value=1.0),
    )

    _values, position = _solve_initial_state_system(
        compiled=compiled, entries=position_entries, system="position"
    )
    _values, velocity = _solve_initial_state_system(
        compiled=compiled, entries=velocity_entries, system="velocity"
    )

    assert position["status"] == "overconstrained_consistent"
    assert velocity["status"] == "inconsistent"


def test_post_write_verification_detects_a_changed_internal_coordinate():
    compiled = compile_assembly(assembly=_chain_assembly())
    entries = (scenario.JointValue(joint_id="joint.first", value=0.5),)
    values, diagnostics = _solve_initial_state_system(
        compiled=compiled, entries=entries, system="position"
    )
    changed = {key: 0.0 for key in values}

    verified = _verify_initial_state_system(
        compiled=compiled,
        entries=entries,
        actual_group_values=changed,
        diagnostics=diagnostics,
    )

    assert verified["status"] == "inconsistent"
    assert verified["verification"][0] == {
        "joint_id": "joint.first",
        "target": 0.5,
        "actual": 0.0,
        "error": -0.5,
    }


def test_no_explicit_initial_state_records_default_zero_source():
    motion = kinematics.solve_motion(scenario=_condition(_chain_assembly()))

    assert motion.metadata["initial_state"]["position"]["status"] == "default_zero"
    assert motion.metadata["initial_state"]["velocity"]["source"] == "default_zero"
    assert motion.metadata["initial_state"]["position"]["verification"] == ()


def test_backend_initial_state_failure_becomes_stable_scenario_error(monkeypatch):
    value = _condition(_chain_assembly())

    def fail(*, scenario):
        raise BackendInitialStateFailure(
            "conflicting targets",
            object_ids=(scenario.scenario_id, "joint.first", "joint.second"),
            details={"initial_state": {"position": {"status": "inconsistent"}}},
        )

    monkeypatch.setattr("kincheckapi._backends.solve_scenario", fail)
    with pytest.raises(ScenarioValidationError) as caught:
        kinematics.solve_motion(scenario=value)

    assert caught.value.code == "KINCHECK-SCENARIO-INITIAL-STATE-INCONSISTENT"
    assert caught.value.object_ids == (
        value.scenario_id,
        "joint.first",
        "joint.second",
    )
    assert caught.value.report.metadata["initial_state"]["position"]["status"] == "inconsistent"
