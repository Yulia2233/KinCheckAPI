from __future__ import annotations

import json
import math

import pytest

from kincheckapi.errors import ScenarioValidationError
from kincheckapi.scenario import (
    Interpolation,
    MotionProfile,
    Profile,
    ProfilePoint,
    Scenario,
    add_joint_position_driver,
    add_joint_speed_driver,
    add_joint_speed_profile,
    create_scenario,
    disable_constraint,
    lock_joint,
    read_scenario,
    request_component_result,
    request_joint_result,
    scenario_from_dict,
    scenario_to_dict,
    set_initial_joint_position,
    set_initial_joint_velocity,
    set_joint_home_position,
    set_run_duration,
    set_sample_period,
    validate_scenario,
    write_scenario,
)


JOINT = "joint.ex3.ground_crank"
SECOND_JOINT = "joint.ex3.ground_rocker"
COMPONENT = "cmp.ex3.crank"
CONNECTOR = "__mjcf_joint__joint.ex3.ground_crank__child"
CLOSURE = "closure.ex3.coupler_rocker"


def _timed(assembly, scenario_id="scenario.extended"):
    value = create_scenario(scenario_id=scenario_id, assembly=assembly)
    value = set_run_duration(scenario=value, duration_s=2.0)
    return set_sample_period(scenario=value, period_s=0.1)


@pytest.mark.parametrize(
    ("kwargs", "exception_type"),
    [({"scenario_id": "", "assembly": object()}, ValueError), ({"scenario_id": "scenario.bad", "assembly": object()}, TypeError)],
)
def test_scenario_constructor_rejects_invalid_identity_and_assembly(kwargs, exception_type):
    with pytest.raises(exception_type):
        Scenario(**kwargs)


def test_create_scenario_wraps_constructor_errors(ex3_assembly):
    with pytest.raises(ScenarioValidationError) as caught:
        create_scenario(scenario_id="", assembly=ex3_assembly)
    assert caught.value.code == "KINCHECK-SCENARIO-CREATE-FAILED"


def test_scenario_rejects_an_explicit_mismatched_assembly_id(ex3_assembly):
    with pytest.raises(ValueError, match="assembly_id must match"):
        Scenario(scenario_id="scenario.mismatch", assembly=ex3_assembly, assembly_id="assembly.other")


@pytest.mark.parametrize("time_s,value", [(-0.1, 0.0), (math.inf, 0.0), (0.0, math.nan)])
def test_profile_point_rejects_non_finite_or_negative_values(time_s, value):
    with pytest.raises(ValueError):
        ProfilePoint(time_s=time_s, value=value)


def test_motion_profile_alias_interpolation_and_order_validation():
    profile = Profile(points=(ProfilePoint(time_s=0.0, value=1.0),), interpolation="step")
    assert isinstance(profile, MotionProfile) and profile.interpolation is Interpolation.STEP
    with pytest.raises(ValueError):
        MotionProfile(points=())
    with pytest.raises(ValueError):
        MotionProfile(points=(ProfilePoint(time_s=1.0, value=0.0), ProfilePoint(time_s=1.0, value=1.0)))


def test_state_setters_replace_matching_joint_without_mutating_original(ex3_assembly):
    original = create_scenario(scenario_id="scenario.states", assembly=ex3_assembly)
    changed = set_initial_joint_position(scenario=original, joint_id=JOINT, position_rad_or_m=2.0)
    changed = set_initial_joint_velocity(scenario=changed, joint_id=JOINT, velocity_rad_s_or_m_s=3.0)
    changed = set_joint_home_position(scenario=changed, joint_id=JOINT, position_rad_or_m=4.0)
    assert original.initial_joint_positions == ()
    assert changed.initial_joint_positions[0].value == 2.0
    assert changed.initial_joint_velocities[0].value == 3.0
    assert changed.joint_home_positions[0].value == 4.0


def test_state_setters_report_non_numeric_values(ex3_assembly):
    value = create_scenario(scenario_id="scenario.bad.state", assembly=ex3_assembly)
    for operation in (
        lambda item: set_initial_joint_position(scenario=item, joint_id=JOINT, position_rad_or_m="bad"),
        lambda item: set_initial_joint_velocity(scenario=item, joint_id=JOINT, velocity_rad_s_or_m_s="bad"),
        lambda item: set_joint_home_position(scenario=item, joint_id=JOINT, position_rad_or_m="bad"),
    ):
        with pytest.raises(ScenarioValidationError) as caught:
            operation(value)
        assert caught.value.code == "KINCHECK-SCENARIO-JOINT-VALUE-INVALID"


def test_lock_and_requests_replace_or_deduplicate(ex3_assembly):
    value = create_scenario(scenario_id="scenario.idempotent", assembly=ex3_assembly)
    value = lock_joint(scenario=value, joint_id=JOINT, position_rad_or_m=1.25)
    value = disable_constraint(scenario=value, constraint_id=CLOSURE)
    requested = request_joint_result(scenario=value, joint_id=JOINT)
    assert request_joint_result(scenario=requested, joint_id=JOINT) is requested
    requested = request_component_result(scenario=requested, component_id=COMPONENT, connector_id=CONNECTOR)
    assert request_component_result(scenario=requested, component_id=COMPONENT, connector_id=CONNECTOR) is requested
    assert requested.locked_joints[0].position_rad_or_m == 1.25


def test_profile_commands_accept_all_supported_input_shapes(ex3_assembly):
    value = _timed(ex3_assembly, "scenario.profile.shapes")
    value = add_joint_position_driver(scenario=value, joint_id=JOINT, profile={"interpolation": "linear", "points": ({"time_s": 0.0, "value": 0.0}, {"time_s": 2.0, "value": 1.0})})
    value = add_joint_speed_profile(scenario=value, joint_id=SECOND_JOINT, profile=(ProfilePoint(time_s=0.0, value=0.0), (2.0, 2.0)))
    assert value.position_drivers[0].profile.interpolation is Interpolation.LINEAR
    assert validate_scenario(scenario=value).passed


@pytest.mark.parametrize("speed,start,end,code", [("bad", 0.0, 1.0, "KINCHECK-SCENARIO-DRIVER-VALUE-INVALID"), (math.inf, 0.0, 1.0, "KINCHECK-SCENARIO-DRIVER-VALUE-INVALID"), (1.0, -1.0, 1.0, "KINCHECK-SCENARIO-DRIVER-TIME-INVALID"), (1.0, 1.0, 1.0, "KINCHECK-SCENARIO-DRIVER-TIME-INVALID")])
def test_constant_speed_driver_rejects_invalid_values(ex3_assembly, speed, start, end, code):
    with pytest.raises(ScenarioValidationError) as caught:
        add_joint_speed_driver(scenario=create_scenario(scenario_id="scenario.bad.driver", assembly=ex3_assembly), joint_id=JOINT, speed_rad_s_or_m_s=speed, start_time_s=start, end_time_s=end)
    assert caught.value.code == code


def test_validation_aggregates_missing_component_joint_connector_and_constraint(ex3_assembly):
    value = _timed(ex3_assembly, "scenario.missing.refs")
    value = request_joint_result(scenario=value, joint_id="joint.missing")
    value = request_component_result(scenario=value, component_id="component.missing")
    value = request_component_result(scenario=value, component_id=COMPONENT, connector_id="connector.missing")
    value = disable_constraint(scenario=value, constraint_id="constraint.missing")
    codes = {issue.code for issue in validate_scenario(scenario=value).issues}
    assert {"KINCHECK-SCENARIO-JOINT-NOT-FOUND", "KINCHECK-SCENARIO-COMPONENT-NOT-FOUND", "KINCHECK-SCENARIO-CONNECTOR-NOT-FOUND", "KINCHECK-SCENARIO-CONSTRAINT-NOT-FOUND"} <= codes


def test_time_setters_defer_finite_and_positive_checks_to_validation(ex3_assembly):
    value = set_sample_period(scenario=set_run_duration(scenario=create_scenario(scenario_id="scenario.bad.time", assembly=ex3_assembly), duration_s=1.0), period_s=2.0)
    assert "KINCHECK-SCENARIO-SAMPLE-PERIOD-TOO-LARGE" in {issue.code for issue in validate_scenario(scenario=value).issues}


def test_scenario_dict_round_trip_includes_every_field(ex3_assembly):
    value = _timed(ex3_assembly, "scenario.full.roundtrip")
    value = set_initial_joint_position(scenario=value, joint_id=JOINT, position_rad_or_m=0.1)
    value = set_initial_joint_velocity(scenario=value, joint_id=JOINT, velocity_rad_s_or_m_s=0.2)
    value = set_joint_home_position(scenario=value, joint_id=JOINT, position_rad_or_m=0.3)
    value = lock_joint(scenario=value, joint_id=SECOND_JOINT)
    value = disable_constraint(scenario=value, constraint_id=CLOSURE)
    value = add_joint_position_driver(scenario=value, joint_id=JOINT, profile=((0.0, 0.0), (2.0, 1.0)))
    value = add_joint_speed_profile(scenario=value, joint_id=SECOND_JOINT, profile=((0.0, 0.0), (2.0, 1.0)))
    value = request_joint_result(scenario=value, joint_id=JOINT)
    value = request_component_result(scenario=value, component_id=COMPONENT, connector_id=CONNECTOR)
    data = scenario_to_dict(scenario=value)
    assert scenario_to_dict(scenario=scenario_from_dict(assembly=ex3_assembly, data=data)) == data


def test_scenario_from_dict_requires_matching_assembly(ex3_assembly):
    with pytest.raises(ScenarioValidationError) as caught:
        scenario_from_dict(assembly=ex3_assembly, data={"scenario_id": "scenario.other", "assembly_id": "assembly.other"})
    assert caught.value.code == "KINCHECK-SCENARIO-ASSEMBLY-MISMATCH"


def test_write_scenario_creates_parent_and_deterministic_json(ex3_assembly, tmp_path):
    value = _timed(ex3_assembly, "scenario.write")
    path = tmp_path / "nested" / "scenario.json"
    write_scenario(scenario=value, path=path)
    assert json.loads(path.read_text(encoding="utf-8")) == scenario_to_dict(scenario=value)
