from __future__ import annotations

import warnings

import pytest

import kincheckapi
from kincheckapi import checks, kinematics, result
from kincheckapi.result import JointTrajectory, MotionResult


def _ratio_motion() -> MotionResult:
    times = (0.0, 1.0, 2.0, 3.0)
    return MotionResult(
        scenario_id="scenario.compat",
        assembly_id="assembly.compat",
        status="completed",
        start_time_s=0.0,
        end_time_s=3.0,
        sample_times_s=times,
        joint_trajectories=(
            JointTrajectory(
                joint_id="joint.input",
                times_s=times,
                positions=(0.0, 20.0, 40.0, 60.0),
                velocities=(20.0,) * 4,
                accelerations=(0.0,) * 4,
            ),
            JointTrajectory(
                joint_id="joint.output",
                times_s=times,
                positions=(0.0, 1.0, 2.0, 3.0),
                velocities=(1.0,) * 4,
                accelerations=(0.0,) * 4,
            ),
        ),
    )


def _ratio_arguments() -> dict[str, object]:
    return {
        "motion_result": _ratio_motion(),
        "input_joint_id": "joint.input",
        "output_joint_id": "joint.output",
        "expected_ratio": 20.0,
        "expected_direction": "same",
    }


def test_theoretical_planetary_ratio_is_not_a_public_kinematics_api():
    assert not hasattr(kinematics, "verify_planetary_ratio_definition")


def test_planetary_stage_evidence_is_not_a_public_result_type():
    assert not hasattr(result, "PlanetaryStageEvidence")


def test_transmission_ratio_type_is_not_exported_from_package_root():
    assert not hasattr(kincheckapi, "TransmissionRatioCheck")


def test_deprecated_ratio_wrapper_forwards_to_checks():
    with pytest.warns(DeprecationWarning, match="kincheckapi.checks"):
        legacy = kinematics.verify_transmission_ratio(**_ratio_arguments())
    current = checks.check_transmission_ratio(**_ratio_arguments())
    assert legacy.to_dict() == current.to_dict()


def test_deprecated_ratio_wrapper_emits_one_warning_per_call():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        kinematics.verify_transmission_ratio(**_ratio_arguments())
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning


def test_new_ratio_check_does_not_emit_a_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        report = checks.check_transmission_ratio(**_ratio_arguments())
    assert report.passed
    assert caught == []
