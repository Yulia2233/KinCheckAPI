from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi.assembly import JointLimit
from kincheckapi.kinematics import solve_motion
from kincheckapi.scenario import (
    create_scenario,
    lock_joint,
    request_joint_result,
    scenario_from_dict,
    scenario_to_dict,
    set_initial_joint_position,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)
CARRIER = "cst.pg3.s03.revolute.carrier"


def _timed(assembly):
    scenario = create_scenario(scenario_id="scenario.v021.lock", assembly=assembly)
    scenario = set_run_duration(scenario=scenario, duration_s=0.1)
    return set_sample_period(scenario=scenario, period_s=0.05)


def _solve_locked(assembly, *, value=None, initial=None):
    scenario = _timed(assembly)
    if initial is not None:
        scenario = set_initial_joint_position(
            scenario=scenario, joint_id=CARRIER, position_rad_or_m=initial
        )
    scenario = lock_joint(
        scenario=scenario, joint_id=CARRIER, position_rad_or_m=value
    )
    scenario = request_joint_result(scenario=scenario, joint_id=CARRIER)
    result = solve_motion(scenario=scenario)
    return scenario, result


def _carrier_trajectory(result):
    return next(
        item for item in result.joint_trajectories if item.joint_id == CARRIER
    )


def test_lock_without_value_uses_the_initial_position(ex1_assembly):
    _, result = _solve_locked(ex1_assembly, value=None, initial=0.2)
    trajectory = _carrier_trajectory(result)
    assert trajectory.positions == pytest.approx((0.2, 0.2, 0.2), abs=1e-7)


def test_lock_with_value_holds_the_explicit_position(ex1_assembly):
    _, result = _solve_locked(ex1_assembly, value=0.15)
    trajectory = _carrier_trajectory(result)
    assert trajectory.positions == pytest.approx((0.15, 0.15, 0.15), abs=1e-7)


def test_lock_without_initial_value_defaults_to_zero(ex1_assembly):
    _, result = _solve_locked(ex1_assembly)
    trajectory = _carrier_trajectory(result)
    assert trajectory.positions == pytest.approx((0.0, 0.0, 0.0), abs=1e-7)


def test_lock_is_preserved_by_scenario_round_trip(ex1_assembly):
    scenario, _ = _solve_locked(ex1_assembly, value=0.15)
    restored = scenario_from_dict(
        assembly=ex1_assembly, data=scenario_to_dict(scenario=scenario)
    )
    assert scenario_to_dict(scenario=restored) == scenario_to_dict(scenario=scenario)


def test_lock_conflicting_with_a_driver_is_rejected(ex1_assembly):
    scenario = _timed(ex1_assembly)
    scenario = lock_joint(scenario=scenario, joint_id=CARRIER, position_rad_or_m=0.1)
    from kincheckapi.scenario import add_joint_position_driver

    scenario = add_joint_position_driver(
        scenario=scenario,
        joint_id=CARRIER,
        profile=((0.0, 0.1), (0.1, 0.1)),
    )
    report = validate_scenario(scenario=scenario)
    assert "KINCHECK-SCENARIO-DRIVER-CONFLICT" in {
        issue.code for issue in report.issues
    }


def test_lock_conflicting_with_initial_position_is_rejected(ex1_assembly):
    scenario = _timed(ex1_assembly)
    scenario = set_initial_joint_position(
        scenario=scenario, joint_id=CARRIER, position_rad_or_m=0.1
    )
    scenario = lock_joint(scenario=scenario, joint_id=CARRIER, position_rad_or_m=0.2)
    report = validate_scenario(scenario=scenario)
    assert "KINCHECK-SCENARIO-LOCK-CONFLICT" in {
        issue.code for issue in report.issues
    }


def test_lock_outside_joint_limit_is_rejected(ex1_assembly):
    limited = replace(
        ex1_assembly,
        joints=tuple(
            replace(joint, limit=JointLimit(lower=-0.1, upper=0.1))
            if joint.joint_id == CARRIER
            else joint
            for joint in ex1_assembly.joints
        ),
    )
    scenario = _timed(limited)
    scenario = lock_joint(scenario=scenario, joint_id=CARRIER, position_rad_or_m=0.2)
    report = validate_scenario(scenario=scenario)
    assert "KINCHECK-SCENARIO-JOINT-LIMIT-VIOLATION" in {
        issue.code for issue in report.issues
    }
