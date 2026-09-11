from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from kincheckapi.assembly import JointLimit
from kincheckapi.errors import ScenarioValidationError
from kincheckapi.scenario import (
    MotionProfile,
    ProfilePoint,
    add_joint_position_driver,
    add_joint_speed_driver,
    add_joint_speed_profile,
    create_scenario,
    disable_constraint,
    lock_joint,
    read_scenario,
    request_component_result,
    request_joint_result,
    scenario_to_dict,
    set_initial_joint_position,
    set_initial_joint_velocity,
    set_joint_home_position,
    set_run_duration,
    set_sample_period,
    validate_scenario,
    write_scenario,
)


INPUT_JOINT = "joint.ex3.ground_crank"
ROCKER_JOINT = "joint.ex3.ground_rocker"
FIXED_JOINT = "joint.ex3.hardware.pin.ground_left"
CLOSURE_ID = "closure.ex3.coupler_rocker"
COMPONENT_ID = "cmp.ex3.crank"
CONNECTOR_ID = "__mjcf_joint__joint.ex3.ground_crank__child"


def _valid_scenario(assembly):
    value = create_scenario(scenario_id="scenario.ex3", assembly=assembly)
    value = set_initial_joint_position(scenario=value, joint_id=INPUT_JOINT, position_rad_or_m=0.0)
    value = add_joint_speed_driver(scenario=value, joint_id=INPUT_JOINT, speed_rad_s_or_m_s=1.0, start_time_s=0.0, end_time_s=2.0)
    value = set_run_duration(scenario=value, duration_s=2.0)
    value = set_sample_period(scenario=value, period_s=0.01)
    return request_joint_result(scenario=value, joint_id=INPUT_JOINT)


def test_scenario_build_and_round_trip(ex3_assembly, tmp_path):
    value = _valid_scenario(ex3_assembly)
    assert validate_scenario(scenario=value).passed
    path = tmp_path / "scenario.json"
    write_scenario(scenario=value, path=path)
    loaded = read_scenario(assembly=ex3_assembly, path=path)
    assert scenario_to_dict(scenario=loaded) == scenario_to_dict(scenario=value)


def test_scenario_reports_invalid_time_and_reference(ex3_assembly):
    value = create_scenario(scenario_id="scenario.invalid", assembly=ex3_assembly)
    value = set_initial_joint_position(scenario=value, joint_id="joint.missing", position_rad_or_m=0.0)
    value = set_run_duration(scenario=value, duration_s=-1.0)
    value = set_sample_period(scenario=value, period_s=0.0)
    codes = {issue.code for issue in validate_scenario(scenario=value).issues}
    assert {"KINCHECK-SCENARIO-DURATION-INVALID", "KINCHECK-SCENARIO-SAMPLE-PERIOD-INVALID", "KINCHECK-SCENARIO-JOINT-NOT-FOUND"} <= codes


def test_all_scenario_state_and_request_commands(ex3_assembly):
    value = create_scenario(scenario_id="scenario.commands", assembly=ex3_assembly)
    value = set_initial_joint_velocity(scenario=value, joint_id=INPUT_JOINT, velocity_rad_s_or_m_s=0.0)
    value = set_joint_home_position(scenario=value, joint_id=INPUT_JOINT, position_rad_or_m=0.0)
    value = lock_joint(scenario=value, joint_id=ROCKER_JOINT, position_rad_or_m=0.0)
    value = disable_constraint(scenario=value, constraint_id=CLOSURE_ID)
    value = request_component_result(scenario=value, component_id=COMPONENT_ID, connector_id=CONNECTOR_ID)
    value = set_run_duration(scenario=value, duration_s=1.0)
    value = set_sample_period(scenario=value, period_s=0.1)
    assert validate_scenario(scenario=value).passed


def test_position_and_speed_profile_commands(ex3_assembly):
    profile = MotionProfile(points=(ProfilePoint(time_s=0.0, value=0.0), ProfilePoint(time_s=1.0, value=1.0)))
    position = add_joint_position_driver(scenario=create_scenario(scenario_id="scenario.position", assembly=ex3_assembly), joint_id=INPUT_JOINT, profile=profile)
    position = set_run_duration(scenario=position, duration_s=1.0)
    position = set_sample_period(scenario=position, period_s=0.1)
    assert validate_scenario(scenario=position).passed
    speed = add_joint_speed_profile(scenario=create_scenario(scenario_id="scenario.speed", assembly=ex3_assembly), joint_id=INPUT_JOINT, profile={"points": ((0.0, 0.0), (1.0, 2.0)), "interpolation": "linear"})
    speed = set_run_duration(scenario=speed, duration_s=1.0)
    speed = set_sample_period(scenario=speed, period_s=0.1)
    assert validate_scenario(scenario=speed).passed


def test_scenario_is_immutable(ex3_assembly):
    original = create_scenario(scenario_id="scenario.immutable", assembly=ex3_assembly)
    changed = set_run_duration(scenario=original, duration_s=1.0)
    assert original.duration_s is None and changed.duration_s == 1.0
    with pytest.raises(FrozenInstanceError):
        changed.duration_s = 2.0


def test_validation_aggregates_result_and_constraint_reference_errors(ex3_assembly):
    value = create_scenario(scenario_id="scenario.references", assembly=ex3_assembly)
    value = disable_constraint(scenario=value, constraint_id="cst.missing")
    value = request_component_result(scenario=value, component_id=COMPONENT_ID, connector_id="conn.missing")
    value = set_run_duration(scenario=value, duration_s=1.0)
    value = set_sample_period(scenario=value, period_s=0.1)
    codes = {issue.code for issue in validate_scenario(scenario=value).issues}
    assert {"KINCHECK-SCENARIO-CONSTRAINT-NOT-FOUND", "KINCHECK-SCENARIO-CONNECTOR-NOT-FOUND"} <= codes


def test_conflicting_drivers_and_invalid_profiles_are_structured(ex3_assembly):
    value = create_scenario(scenario_id="scenario.conflict", assembly=ex3_assembly)
    for speed in (1.0, 2.0):
        value = add_joint_speed_driver(scenario=value, joint_id=INPUT_JOINT, speed_rad_s_or_m_s=speed, start_time_s=0.0, end_time_s=1.0)
    value = set_run_duration(scenario=value, duration_s=1.0)
    value = set_sample_period(scenario=value, period_s=0.1)
    assert "KINCHECK-SCENARIO-DRIVER-CONFLICT" in {issue.code for issue in validate_scenario(scenario=value).issues}
    with pytest.raises(ScenarioValidationError) as caught:
        add_joint_position_driver(scenario=value, joint_id=INPUT_JOINT, profile=((1.0, 0.0), (0.5, 1.0)))
    assert caught.value.code == "KINCHECK-SCENARIO-PROFILE-INVALID"


def test_lock_position_respects_joint_limits(ex3_assembly):
    limited = replace(ex3_assembly, joints=tuple(replace(joint, limit=JointLimit(-0.1, 0.1)) if joint.joint_id == INPUT_JOINT else joint for joint in ex3_assembly.joints))
    value = lock_joint(scenario=create_scenario(scenario_id="scenario.lock.limit", assembly=limited), joint_id=INPUT_JOINT, position_rad_or_m=2.0)
    value = set_run_duration(scenario=value, duration_s=1.0)
    value = set_sample_period(scenario=value, period_s=0.1)
    assert "KINCHECK-SCENARIO-JOINT-LIMIT-VIOLATION" in {issue.code for issue in validate_scenario(scenario=value).issues}


def test_read_scenario_rejects_assembly_mismatch(ex3_assembly, tmp_path):
    value = _valid_scenario(ex3_assembly)
    data = scenario_to_dict(scenario=value)
    data["assembly_id"] = "assembly.other"
    path = tmp_path / "mismatch.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ScenarioValidationError) as caught:
        read_scenario(assembly=ex3_assembly, path=path)
    assert caught.value.code == "KINCHECK-SCENARIO-ASSEMBLY-MISMATCH"
