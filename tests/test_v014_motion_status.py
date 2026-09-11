from __future__ import annotations

import pytest

from kincheckapi import checks, kinematics, scenario
from kincheckapi._backends.solver_backend import (
    BackendSample,
    BackendSolveResult,
)
from kincheckapi.assembly import (
    AssemblyModel,
    Closure,
    Component,
    Connector,
    ConnectorRef,
    Constraint,
    Coupling,
    Ground,
    Part,
)
from kincheckapi.result import MotionResult


def _assembly(*, kind: str = "gear", closure: bool = False) -> AssemblyModel:
    connector = Connector("axis")
    reference = ConnectorRef("ground", "axis")
    constraint = Constraint(
        constraint_id="relation",
        connector_a=reference,
        connector_b=reference,
        constraint_type=kind,
    )
    closures = (Closure(closure_id="loop", constraint=constraint),) if closure else ()
    constraints = () if closure or kind == "coupling" else (constraint,)
    couplings = (
        Coupling(
            coupling_id="relation",
            coupling_type="gear",
            joint_a_id="joint.a",
            joint_b_id="joint.b",
            ratio=1.0,
        ),
    ) if kind == "coupling" else ()
    return AssemblyModel(
        assembly_id=f"v014.status.{kind}",
        parts=(Part("part", connectors=(connector,)),),
        components=(Component("ground", "part"),),
        constraints=constraints,
        couplings=couplings,
        closures=closures,
        grounds=(Ground("ground"),),
    )


def _motion(
    *,
    kind: str = "gear",
    equation_value: float = 0.0,
    position_residual_m: float = 0.0,
    orientation_residual_rad: float = 0.0,
    warnings: tuple[str, ...] = (),
    closure: bool = False,
) -> MotionResult:
    assembly = _assembly(kind=kind, closure=closure)
    condition = scenario.create_scenario(scenario_id=f"status.{kind}", assembly=assembly)
    condition = scenario.set_run_duration(scenario=condition, duration_s=0.1)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.1)
    residual_id = "loop" if closure else "relation"
    samples = tuple(
        BackendSample(
            time_s=time_s,
            joint_positions={},
            joint_velocities={},
            component_poses={},
            connector_poses={},
            constraint_residuals={},
            constraint_position_residuals={residual_id: position_residual_m},
            constraint_orientation_residuals={residual_id: orientation_residual_rad},
            constraint_equation_residuals=(
                {} if closure else {"relation": equation_value}
            ),
        )
        for time_s in (0.0, 0.1)
    )
    backend_result = BackendSolveResult(
        backend_name="test",
        backend_version="1",
        assembly_id=assembly.assembly_id,
        scenario_id=condition.scenario_id,
        samples=samples,
        warnings=warnings,
    )
    return kinematics._motion_from_backend(
        scenario=condition, backend_result=backend_result
    )


def test_all_solve_residuals_within_tolerance_complete():
    motion = _motion(equation_value=5e-7, position_residual_m=5e-7)

    assert motion.status == "completed"
    assert not motion.issues


def test_backend_warning_without_error_completes_with_warnings():
    motion = _motion(warnings=("small integration warning",))

    assert motion.status == "completed_with_warnings"
    assert {item.severity for item in motion.issues} == {"warning"}


@pytest.mark.parametrize("kind", ("gear", "belt"))
def test_linear_equation_residual_marks_result_partial(kind):
    motion = _motion(kind=kind, equation_value=-2e-6)

    assert motion.status == "partial"
    issue = motion.issues[0]
    assert issue.code == "KINCHECK-CONSTRAINT-EQUATION-RESIDUAL-EXCEEDED"
    assert issue.evidence[0].unit == "m"
    assert motion.constraint_equation_residuals[0].value == pytest.approx(-2e-6)


def test_coupling_residual_uses_radians_and_marks_partial():
    motion = _motion(kind="coupling", equation_value=2e-6)

    assert motion.status == "partial"
    assert motion.constraint_equation_residuals[0].unit == "rad"
    assert motion.issues[0].evidence[0].unit == "rad"


def test_ordinary_geometric_residual_marks_result_partial():
    motion = _motion(position_residual_m=2e-6)

    assert motion.status == "partial"
    assert motion.issues[0].code == "KINCHECK-CONSTRAINT-GEOMETRIC-RESIDUAL-EXCEEDED"


def test_try_solve_motion_keeps_partial_result(monkeypatch):
    motion = _motion(equation_value=2e-6)
    condition = scenario.create_scenario(
        scenario_id=motion.scenario_id, assembly=_assembly()
    )
    monkeypatch.setattr(kinematics, "solve_motion", lambda **_: motion)

    attempt = kinematics.try_solve_motion(scenario=condition)

    assert attempt.status == "partial"
    assert not attempt.succeeded
    assert attempt.motion_result is None
    assert attempt.last_valid_result is motion
    assert attempt.failure is None


def test_engineering_check_can_be_stricter_than_solve_status():
    motion = _motion(equation_value=5e-7)
    report = checks.check_constraint_equation_residuals(
        motion_result=motion, linear_tolerance_m=1e-8
    )

    assert motion.status == "completed"
    assert not report.passed


def test_legacy_backend_equation_field_maps_only_known_relation_ids():
    assembly = _assembly(kind="gear")
    condition = scenario.create_scenario(scenario_id="status.legacy", assembly=assembly)
    condition = scenario.set_run_duration(scenario=condition, duration_s=0.1)
    condition = scenario.set_sample_period(scenario=condition, period_s=0.1)
    sample = BackendSample(
        time_s=0.0,
        joint_positions={},
        joint_velocities={},
        component_poses={},
        connector_poses={},
        constraint_residuals={"relation": -2e-6, "unknown.geometry": 7.0},
    )
    backend = BackendSolveResult(
        backend_name="legacy",
        backend_version="0",
        assembly_id=assembly.assembly_id,
        scenario_id=condition.scenario_id,
        samples=(sample,),
    )

    motion = kinematics._motion_from_backend(
        scenario=condition, backend_result=backend
    )

    assert tuple(item.constraint_id for item in motion.constraint_equation_residuals) == (
        "relation",
    )
    assert motion.constraint_equation_residuals[0].value == pytest.approx(-2e-6)
