"""Regression tests for the v0.7 KinCheckAPI rigid-body core."""

import json

import pytest

from kincheckapi.assembly import AssemblyModel, Component, Part, Pose
from kincheckapi.dynamics import (
    ActuatorEnvelope,
    DynamicsScenarioCase,
    DynamicsScenarioMatrix,
    ContactInterface,
    ConstraintSpec,
    DynamicsLoadHistory,
    GeneralizedJointState,
    ReactionRequest,
    RigidDynamicsScenario,
    export_load_history,
    history_from_multibody_result,
    read_load_history,
    solve_contact_dynamics,
    solve_multibody_dynamics,
    check_actuator_limits,
    run_dynamics_cases,
    summarize_drive_duty,
    summarize_energy,
    RandomExcitation,
    WrenchProfile,
    WrenchSample,
)
from kincheckapi.export import motion_package, read_package, validate_package
from kincheckapi.result import MotionResult, Trajectory


def scenario(*, constrained=False):
    constraints = ()
    if constrained:
        constraints = (ConstraintSpec(constraint_id="equal", coefficients={"a[0]": 1.0, "b[0]": -1.0}),)
    return RigidDynamicsScenario(
        states=(
            GeneralizedJointState(joint_id="a", position=(0.0,)),
            GeneralizedJointState(joint_id="b", position=(0.0,)),
        ),
        mass_matrix=((1.0, 0.0), (0.0, 1.0)),
        force_vector=(1.0, 0.0),
        duration_s=0.1,
        sample_period_s=0.05,
        constraints=constraints,
        scenario_id="two-body",
        model_sha256="model-hash",
    )


def test_v070_generalized_multibody_and_reaction_history_round_trip(tmp_path):
    result = solve_multibody_dynamics(scenario=scenario(constrained=True), reaction_request=ReactionRequest(object_ids=("equal",)))
    assert result.status == "completed", result.to_dict()
    assert result.samples[-1].positions["a[0]"] > 0
    assert result.constraint_residual_max <= 1e-8
    history = history_from_multibody_result(result=result, history_id="h")
    encoded = json.dumps(history.to_dict(), allow_nan=False)
    assert DynamicsLoadHistory.from_dict(json.loads(encoded)).times_s == history.times_s
    path = export_load_history(history=history, path=tmp_path / "history.json")
    assert read_load_history(path=path).history_id == "h"
    assert result.evidence["constraint_rank"] == 1
    assert result.evidence["source_map"]["equal"]["relation"] == "linear"


def test_v070_unknown_constraint_reference_is_structured_failure():
    result = solve_multibody_dynamics(
        scenario=RigidDynamicsScenario(
            states=(GeneralizedJointState(joint_id="a", position=0.0),),
            mass_matrix=((1.0,),),
            force_vector=(0.0,),
            duration_s=0.1,
            sample_period_s=0.1,
            constraints=(ConstraintSpec(constraint_id="bad", coefficients={"missing[0]": 1.0}),),
        )
    )
    assert result.status == "validation_failed"
    assert result.issues[0].code.endswith("CONSTRAINT-REFERENCE-MISSING")


def test_v071_rigid_contact_requires_declared_law_and_reports_impulse():
    interface = ContactInterface(contact_id="floor", normal=(0.0, 0.0, 1.0), gap_m=0.0, normal_stiffness_n_m=1000.0, normal_damping_n_s_m=1.0)
    result = solve_contact_dynamics(interface=interface, times_s=(0.0, 0.1, 0.2), relative_gap_m=(0.01, -0.01, 0.0), relative_normal_velocity_m_s=(-1.0, 0.0, 0.0))
    assert result.status == "completed"
    assert result.impulse_ns > 0
    assert any(event.state == "contact" for event in result.events)
    unsupported = solve_contact_dynamics(interface=ContactInterface(contact_id="missing-law", normal=(0.0, 0.0, 1.0), gap_m=0.0), times_s=(0.0, 0.1), relative_gap_m=(0.0, 0.0), relative_normal_velocity_m_s=(0.0, 0.0))
    assert unsupported.status == "capability_failed"


def test_v071_contact_is_applied_during_multibody_integration_and_records_events():
    interface = ContactInterface(
        contact_id="floor",
        normal=(0.0, 0.0, 1.0),
        gap_m=-0.01,
        normal_stiffness_n_m=100.0,
        dof_coefficients={"a[0]": 1.0},
        contact_point_m=(0.0, 0.0, 0.2),
    )
    result = solve_multibody_dynamics(
        scenario=RigidDynamicsScenario(
            states=(GeneralizedJointState(joint_id="a", position=0.0),),
            mass_matrix=((1.0,),),
            force_vector=(0.0,),
            duration_s=0.1,
            sample_period_s=0.05,
            contacts=(interface,),
        )
    )
    assert result.status == "completed", result.to_dict()
    assert result.contact_events
    assert result.contact_events[0].normal_force_n == pytest.approx(1.0)


def test_v071_redundant_reaction_requires_allocation_model():
    redundant = RigidDynamicsScenario(
        states=(GeneralizedJointState(joint_id="a", position=0.0),),
        mass_matrix=((1.0,),), force_vector=(0.0,), duration_s=0.1, sample_period_s=0.1,
        constraints=(
            ConstraintSpec(constraint_id="c1", coefficients={"a[0]": 1.0}),
            ConstraintSpec(constraint_id="c2", coefficients={"a[0]": 2.0}),
        ),
    )
    result = solve_multibody_dynamics(scenario=redundant, reaction_request=ReactionRequest(object_ids=("c1", "c2")))
    assert result.status == "indeterminate"
    assert result.issues[0].code.endswith("REACTION-NONUNIQUE")


def test_v072_scenario_matrix_and_drive_summaries():
    first = DynamicsScenarioCase(case_id="nominal", scenario=scenario())
    second = DynamicsScenarioCase(case_id="hold", scenario=scenario(constrained=True))
    suite = run_dynamics_cases(matrix=DynamicsScenarioMatrix(matrix_id="duty", cases=(first, second)))
    assert suite.passed, suite.to_dict()
    history = history_from_multibody_result(result=suite.case_results[0], history_id="duty-history")
    assert summarize_drive_duty(history=history).passed
    assert summarize_energy(history=history).passed
    assert check_actuator_limits(result=suite.case_results[0], envelope=ActuatorEnvelope(envelope_id="drive", dof_limits={"a[0]": 2.0, "b[0]": 2.0})).passed
    profile = WrenchProfile(profile_id="load", samples=(WrenchSample(time_s=0.0, force_n=(0, 0, 0), moment_nm=(0, 0, 0), point_m=(0, 0, 0)), WrenchSample(time_s=1.0, force_n=(2, 0, 0), moment_nm=(0, 0, 0), point_m=(0, 0, 0))))
    assert profile.at(0.5).force_n == pytest.approx((1.0, 0.0, 0.0))
    assert RandomExcitation.generate(excitation_id="noise", seed=7, duration_s=0.1, sample_rate_hz=20.0, bandwidth_hz=5.0).samples == RandomExcitation.generate(excitation_id="noise", seed=7, duration_s=0.1, sample_rate_hz=20.0, bandwidth_hz=5.0).samples


def test_v073_dynamics_history_is_hash_indexed_in_motion_package(tmp_path):
    assembly = AssemblyModel(assembly_id="dynamics.package", parts=(Part("part"),), components=(Component("component", "part"),))
    motion = MotionResult(
        scenario_id="motion",
        assembly_id=assembly.assembly_id,
        status="completed",
        start_time_s=0.0,
        end_time_s=0.1,
        sample_times_s=(0.0, 0.1),
        trajectories=(Trajectory(component_id="component", times_s=(0.0, 0.1), poses=(Pose(), Pose(position_m=(0.1, 0.0, 0.0)))),),
    )
    history = history_from_multibody_result(result=solve_multibody_dynamics(scenario=scenario()), history_id="package-history")
    artifact = motion_package(assembly=assembly, motion_result=motion, output_path=tmp_path / "dynamics.kincheck", dynamics_history=history)
    assert validate_package(path=artifact.path).passed
    restored = read_package(path=artifact.path)
    assert restored.dynamics_history.history_id == "package-history"
    assert restored.manifest["dynamics_path"] == "dynamics.json"
    from viewer.kincheck_viewer import unpack_package
    unpack_package(package_path=artifact.path, output_dir=tmp_path / "viewer")
    viewer_manifest = json.loads((tmp_path / "viewer" / "viewer.json").read_text())
    assert viewer_manifest["dynamics"]["history_id"] == "package-history"
    assert viewer_manifest["dynamics_sample_count"] == len(history.times_s)
