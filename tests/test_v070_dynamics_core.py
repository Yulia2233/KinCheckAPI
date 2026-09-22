"""Regression tests for the v0.7 KinCheckAPI rigid-body core."""

import json

import pytest

from kincheckapi.dynamics import (
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
)


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
