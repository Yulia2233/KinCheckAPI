"""Regression tests for the staged v0.6.1-v0.6.3 dynamic contracts."""

import pytest

from kincheckapi.dynamics import (
    ActuatorProfile,
    ActuatorSpec,
    ContactSpec,
    DynamicRequest,
    DynamicState,
    ForwardDynamicsRequest,
    check_contact_capacity,
    check_dynamic_load_limits,
    check_dynamic_tracking,
    solve_forward_dynamics,
    solve_inverse_dynamics,
)
from kincheckapi.physics_types import WrenchLoad
from kincheckapi.physics_types import PhysicsError

from test_physics_v060 import arm


def inverse_request(*, acceleration=0.0):
    return DynamicRequest(
        states=(DynamicState(joint_id="j", position=0.0, velocity=0.0, acceleration=acceleration),)
    )


def test_v061_inverse_dynamics_includes_gravity_and_inertia():
    model = arm()
    gravity = solve_inverse_dynamics(model=model, request=inverse_request())
    accelerated = solve_inverse_dynamics(model=model, request=inverse_request(acceleration=1.0))
    assert gravity.passed
    assert gravity.generalized_efforts["j"] == pytest.approx(5.886)
    assert accelerated.generalized_efforts["j"] == pytest.approx(6.086)
    assert check_dynamic_load_limits(result=accelerated, limits={"j": 7.0}).passed
    assert not check_dynamic_load_limits(result=accelerated, limits={"j": 6.0}).passed


def test_v061_inverse_dynamics_maps_external_force_at_world_point():
    model = arm()
    load = WrenchLoad(
        load_id="tool",
        component_id="arm",
        force_n=(0.0, 0.0, -100.0),
        moment_nm=(0.0, 0.0, 0.0),
        point_m=(0.4, 0.0, 0.0),
        frame_id="world",
        applied_by="test-rig",
    )
    result = solve_inverse_dynamics(
        model=model,
        request=DynamicRequest(
            states=(DynamicState(joint_id="j", position=0.0),),
            loads=(load,),
        ),
    )
    assert result.passed
    assert result.generalized_efforts["j"] == pytest.approx(45.886)


def test_v061_dynamic_state_coverage_is_structured():
    model = arm()
    result = solve_inverse_dynamics(
        model=model,
        request=DynamicRequest(states=(DynamicState(joint_id="unknown", position=0.0),)),
    )
    assert result.status == "validation_failed"
    assert any(issue.code.endswith("STATE-INVALID") for issue in result.issues)


def test_completed_dynamic_results_require_evidence():
    with pytest.raises(PhysicsError):
        from kincheckapi.dynamics import InverseDynamicsResult
        InverseDynamicsResult(status="completed")
    with pytest.raises(PhysicsError):
        from kincheckapi.dynamics import ForwardDynamicsResult
        ForwardDynamicsResult(status="completed")


def test_v062_forward_dynamics_records_finite_actuator_and_energy():
    model = arm()
    request = ForwardDynamicsRequest(
        initial_states=(DynamicState(joint_id="j", position=0.0),),
        actuators=(ActuatorSpec(actuator_id="motor", joint_id="j", max_effort=20.0),),
        profiles=(ActuatorProfile(actuator_id="motor", points=((0.0, 8.0), (0.1, 8.0))),),
        duration_s=0.1,
        sample_period_s=0.05,
    )
    result = solve_forward_dynamics(model=model, request=request)
    assert result.status == "completed"
    assert len(result.samples) == 3
    assert result.samples[-1].joint_positions["j"] != pytest.approx(0.0)
    assert result.peak_effort["motor"] == pytest.approx(8.0)
    assert result.energy_input_j != 0.0
    tracking = check_dynamic_tracking(result=result, targets={"j": result.samples[-1].joint_positions["j"]}, tolerance=1e-12)
    assert tracking.passed


def test_v063_contact_capacity_checks_friction_and_pressure():
    contact = ContactSpec(
        contact_id="guide",
        normal=(0.0, 0.0, 1.0),
        friction_coefficient=0.25,
        contact_area_m2=1e-3,
        allowable_pressure_pa=5_000.0,
    )
    assert check_contact_capacity(contact=contact, force_n=(1.0, 0.0, 5.0)).passed
    failed = check_contact_capacity(contact=contact, force_n=(4.0, 0.0, 10.0))
    assert not failed.passed
    assert any(issue.code.endswith("FRICTION-LIMIT-EXCEEDED") for issue in failed.issues)
    assert any(issue.code.endswith("CONTACT-PRESSURE-LIMIT-EXCEEDED") for issue in failed.issues)


def test_v062_dynamic_tracking_rejects_nonfinite_and_non_numeric_targets():
    import json
    from kincheckapi.dynamics import DynamicSample, ForwardDynamicsResult

    result = ForwardDynamicsResult(
        status="completed",
        samples=(DynamicSample(time_s=0.0, joint_positions={"j": 0.0}, joint_velocities={"j": 0.0}, joint_accelerations={"j": 0.0}, actuator_efforts={"a": 0.0}),),
    )
    for target in (float("nan"), "not-a-number"):
        report = check_dynamic_tracking(result=result, targets={"j": target})
        assert report.status == "validation_failed"
        assert any(issue.code.endswith("TARGET-INVALID") for issue in report.issues)
        json.dumps(report.to_dict(), allow_nan=False)
