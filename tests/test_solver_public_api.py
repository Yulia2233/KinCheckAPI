from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi import checks, kinematics, scenario
from kincheckapi.assembly import Joint, JointType
from kincheckapi.errors import BackendCapabilityError, BackendUnavailableError, MotionSolveError, ScenarioValidationError


INPUT_JOINT = "joint.ex3.ground_crank"
OUTPUT_JOINT = "joint.ex3.ground_rocker"


def _constant_speed_scenario(assembly, *, input_joint_id=INPUT_JOINT, output_joint_id=OUTPUT_JOINT):
    value = scenario.create_scenario(scenario_id=f"motion.{assembly.assembly_id}", assembly=assembly)
    value = scenario.add_joint_speed_driver(scenario=value, joint_id=input_joint_id, speed_rad_s_or_m_s=0.1, start_time_s=0.0, end_time_s=0.1)
    value = scenario.set_run_duration(scenario=value, duration_s=0.1)
    value = scenario.set_sample_period(scenario=value, period_s=0.1)
    value = scenario.request_joint_result(scenario=value, joint_id=input_joint_id)
    return scenario.request_joint_result(scenario=value, joint_id=output_joint_id)


def test_mjcf_to_motion_uses_only_public_api(ex3_assembly):
    condition = _constant_speed_scenario(ex3_assembly)
    motion = kinematics.solve_motion(scenario=condition)
    assert motion.status in {"completed", "completed_with_warnings", "partial"}
    assert motion.assembly_id == ex3_assembly.assembly_id
    assert motion.backend_id == "solver"
    assert motion.get_joint_trajectory(joint_id=INPUT_JOINT) is not None


def test_speed_profile_is_propagated_to_requested_output_joint(ex3_assembly):
    value = scenario.create_scenario(scenario_id="motion.ex3.variable-speed", assembly=ex3_assembly)
    value = scenario.add_joint_speed_profile(scenario=value, joint_id=INPUT_JOINT, profile=((0.0, 0.02), (0.05, 0.08), (0.1, 0.04)))
    value = scenario.set_run_duration(scenario=value, duration_s=0.1)
    value = scenario.set_sample_period(scenario=value, period_s=0.05)
    value = scenario.request_joint_result(scenario=value, joint_id=INPUT_JOINT)
    value = scenario.request_joint_result(scenario=value, joint_id=OUTPUT_JOINT)
    motion = kinematics.solve_motion(scenario=value)
    assert motion.get_joint_trajectory(joint_id=OUTPUT_JOINT) is not None
    assert motion.status in {"completed", "completed_with_warnings", "partial"}


def test_try_solve_motion_returns_completed_attempt(ex3_assembly):
    attempt = kinematics.try_solve_motion(scenario=_constant_speed_scenario(ex3_assembly))
    assert attempt.status in {"completed", "completed_with_warnings", "succeeded", "partial"}
    assert attempt.last_valid_result is not None or attempt.motion_result is not None
    assert attempt.report is not None


def test_invalid_scenario_has_public_exception_and_attempt_status(ex3_assembly):
    invalid = scenario.create_scenario(scenario_id="motion.invalid-missing-time", assembly=ex3_assembly)
    with pytest.raises(ScenarioValidationError) as caught:
        kinematics.solve_motion(scenario=invalid)
    attempt = kinematics.try_solve_motion(scenario=invalid)
    assert caught.value.code == "KINCHECK-SCENARIO-VALIDATION-FAILED"
    assert attempt.status == "validation_failed"
    assert not attempt.succeeded
    assert isinstance(attempt.failure, ScenarioValidationError)


def test_unsupported_driven_joint_is_classified_as_backend_capability_error(ex3_assembly):
    source = ex3_assembly.get_joint(joint_id=INPUT_JOINT)
    assert source is not None
    unsupported = Joint(joint_id=source.joint_id, joint_type=JointType.SPHERICAL, connector_a=source.connector_a, connector_b=source.connector_b, metadata=source.metadata)
    assembly = replace(ex3_assembly, joints=tuple(unsupported if item.joint_id == INPUT_JOINT else item for item in ex3_assembly.joints))
    condition = _constant_speed_scenario(assembly)
    with pytest.raises(BackendCapabilityError) as caught:
        kinematics.solve_motion(scenario=condition)
    attempt = kinematics.try_solve_motion(scenario=condition)
    assert caught.value.missing_capabilities
    assert attempt.status == "capability_failed"
    assert isinstance(attempt.failure, BackendCapabilityError)


def test_backend_unavailable_is_wrapped_without_exposing_native_exception(monkeypatch, ex3_assembly):
    from kincheckapi._backends import BackendUnavailable

    condition = _constant_speed_scenario(ex3_assembly)

    def unavailable(*, scenario):
        raise BackendUnavailable("runtime missing")

    monkeypatch.setattr("kincheckapi._backends.solve_scenario", unavailable)
    with pytest.raises(BackendUnavailableError) as caught:
        kinematics.solve_motion(scenario=condition)
    attempt = kinematics.try_solve_motion(scenario=condition)
    assert caught.value.code == "KINCHECK-BACKEND-UNAVAILABLE"
    assert caught.value.backend_failure.backend_id == "solver"
    assert attempt.status == "capability_failed"


@pytest.mark.parametrize("failure_kind", ["compile", "solve"])
def test_native_backend_failures_become_motion_solve_errors(monkeypatch, ex3_assembly, failure_kind):
    from kincheckapi._backends import BackendCompileFailure, BackendSolveFailure

    condition = _constant_speed_scenario(ex3_assembly)
    native = BackendCompileFailure("bad generated model") if failure_kind == "compile" else BackendSolveFailure("non-finite state", time_s=0.02)

    def fail(*, scenario):
        raise native

    monkeypatch.setattr("kincheckapi._backends.solve_scenario", fail)
    with pytest.raises(MotionSolveError) as caught:
        kinematics.solve_motion(scenario=condition)
    attempt = kinematics.try_solve_motion(scenario=condition)
    assert caught.value.backend_failure.native_error_type == type(native).__name__
    assert caught.value.__cause__ is native
    assert attempt.status == "failed"


def test_backend_specific_options_are_rejected_by_public_capability_error(ex3_assembly):
    with pytest.raises(BackendCapabilityError) as caught:
        kinematics.solve_motion(scenario=_constant_speed_scenario(ex3_assembly), options={"native": True})
    assert caught.value.code == "KINCHECK-KIN-OPTIONS-UNSUPPORTED"


def test_public_transmission_checker_reports_missing_joint(ex3_assembly):
    motion = kinematics.solve_motion(scenario=_constant_speed_scenario(ex3_assembly))
    report = checks.check_transmission_ratio(motion_result=motion, input_joint_id=INPUT_JOINT, output_joint_id="joint.missing", expected_ratio=1.0, expected_direction="same")
    assert not report.passed
    assert report.issues
