from __future__ import annotations

import pytest

from kincheckapi import export, kinematics, scenario
from kincheckapi.errors import ScenarioValidationError


def _motion(assembly, *, scenario_id: str, joint_id: str, scope=None, request=None):
    value = scenario.create_scenario(scenario_id=scenario_id, assembly=assembly)
    value = scenario.add_joint_speed_driver(
        scenario=value,
        joint_id=joint_id,
        speed_rad_s_or_m_s=1.0e-4,
        start_time_s=0.0,
        end_time_s=1.0e-3,
    )
    value = scenario.set_run_duration(scenario=value, duration_s=1.0e-3)
    value = scenario.set_sample_period(scenario=value, period_s=1.0e-3)
    if scope is not None:
        value = scenario.set_component_result_scope(scenario=value, scope=scope)
    if request is not None:
        value = scenario.request_component_result(scenario=value, component_id=request)
    return scenario, kinematics.solve_motion(scenario=value)


def test_component_result_scope_defaults_to_requested(ex1_assembly):
    value = scenario.create_scenario(scenario_id="scope.default", assembly=ex1_assembly)
    assert value.component_result_scope is scenario.ComponentResultScope.REQUESTED


def test_component_result_scope_all_is_immutable(ex1_assembly):
    original = scenario.create_scenario(scenario_id="scope.immutable", assembly=ex1_assembly)
    changed = scenario.set_component_result_scope(scenario=original, scope="all")
    assert original.component_result_scope is scenario.ComponentResultScope.REQUESTED
    assert changed.component_result_scope is scenario.ComponentResultScope.ALL


def test_component_result_scope_rejects_unknown_value(ex1_assembly):
    value = scenario.create_scenario(scenario_id="scope.invalid", assembly=ex1_assembly)
    with pytest.raises(ScenarioValidationError) as caught:
        scenario.set_component_result_scope(scenario=value, scope="dynamic")
    assert caught.value.code == "KINCHECK-SCENARIO-COMPONENT-RESULT-SCOPE-INVALID"


def test_component_result_scope_round_trips_in_scenario_json(ex1_assembly, tmp_path):
    value = scenario.create_scenario(scenario_id="scope.roundtrip", assembly=ex1_assembly)
    value = scenario.set_component_result_scope(scenario=value, scope="all")
    value = scenario.set_run_duration(scenario=value, duration_s=1.0)
    value = scenario.set_sample_period(scenario=value, period_s=0.1)
    path = tmp_path / "scope.json"
    scenario.write_scenario(scenario=value, path=path)
    restored = scenario.read_scenario(assembly=ex1_assembly, path=path)
    assert restored.component_result_scope is scenario.ComponentResultScope.ALL
    assert scenario.scenario_to_dict(scenario=restored) == scenario.scenario_to_dict(scenario=value)


def test_requested_scope_keeps_explicit_component_filter(ex3_assembly):
    _condition, motion = _motion(
        ex3_assembly,
        scenario_id="scope.ex3.requested",
        joint_id="joint.ex3.ground_crank",
        request="cmp.ex3.coupler",
    )
    assert {item.component_id for item in motion.trajectories if item.connector_id is None} == {
        "cmp.ex3.coupler"
    }
    assert motion.metadata["component_result_scope"] == "requested"


def test_all_scope_exports_every_ex3_component(ex3_assembly):
    _condition, motion = _motion(
        ex3_assembly,
        scenario_id="scope.ex3.all",
        joint_id="joint.ex3.ground_crank",
        scope="all",
        request="cmp.ex3.coupler",
    )
    component_ids = {
        item.component_id for item in motion.trajectories if item.connector_id is None
    }
    assert component_ids == {item.component_id for item in ex3_assembly.components}
    assert len(component_ids) == 20
    assert motion.metadata["component_result_scope"] == "all"


def test_all_scope_exports_every_ex4_component(ex4_assembly):
    _condition, motion = _motion(
        ex4_assembly,
        scenario_id="scope.ex4.all",
        joint_id="joint.jansen.frame_to_crank",
        scope=scenario.ComponentResultScope.ALL,
    )
    component_ids = {
        item.component_id for item in motion.trajectories if item.connector_id is None
    }
    assert component_ids == {item.component_id for item in ex4_assembly.components}
    assert len(component_ids) == 33


def test_all_scope_is_recorded_in_motion_result_and_has_world_samples(ex3_assembly):
    _condition, motion = _motion(
        ex3_assembly,
        scenario_id="scope.ex3.world-samples",
        joint_id="joint.ex3.ground_crank",
        scope="all",
    )
    pin = next(
        item
        for item in motion.trajectories
        if item.component_id == "cmp.ex3.pin.crank_coupler" and item.connector_id is None
    )
    assert len(pin.poses) == len(motion.sample_times_s)
    assert pin.poses[0].position_m != pytest.approx((0.0, 0.0, 0.0))
    assert motion.to_dict()["metadata"]["component_result_scope"] == "all"


def test_all_scope_overrides_requested_component_subset(ex3_assembly):
    _condition, motion = _motion(
        ex3_assembly,
        scenario_id="scope.ex3.override",
        joint_id="joint.ex3.ground_crank",
        scope="all",
        request="cmp.ex3.crank",
    )
    assert len(
        [item for item in motion.trajectories if item.connector_id is None]
    ) == len(ex3_assembly.components)


def test_all_scope_survives_kincheck_package_round_trip(ex3_assembly, tmp_path):
    _condition, motion = _motion(
        ex3_assembly,
        scenario_id="scope.ex3.package",
        joint_id="joint.ex3.ground_crank",
        scope="all",
    )
    path = tmp_path / "all-components.kincheck"
    export.motion_package(assembly=ex3_assembly, motion_result=motion, output_path=path)
    restored = export.read_package(path=path).motion_result
    component_ids = {
        item.component_id for item in restored.trajectories if item.connector_id is None
    }
    assert len(component_ids) == len(ex3_assembly.components)
    assert restored.metadata["component_result_scope"] == "all"
