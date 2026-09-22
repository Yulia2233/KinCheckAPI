"""v0.7 rigid-body dynamics contracts.

This module deliberately contains only kinematics/rigid-body dynamics.  It
does not import a finite-element package or represent structural stress,
deformation, modal fields, or fatigue life.  The public records are designed
to be exported to the future FEACheckAPI through JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .diagnostics import Evidence, SimIssue
from .physics_types import PhysicsReport, fail, issue, plain


def _finite(value: Any, name: str, operation: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = math.nan
    if not math.isfinite(number):
        fail("VALUE-INVALID", f"{name} must be finite.", operation=operation)
    return number


def _vector(value: Any, name: str, operation: str) -> tuple[float, ...]:
    try:
        result = tuple(_finite(item, name, operation) for item in value)
    except TypeError:
        result = ()
    if not result:
        fail("VALUE-INVALID", f"{name} must be a nonempty finite vector.", operation=operation)
    return result


def _matrix(value: Any, name: str, operation: str) -> np.ndarray:
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        matrix = np.empty((0, 0))
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not matrix.size or not np.isfinite(matrix).all():
        fail("MATRIX-INVALID", f"{name} must be a finite nonempty square matrix.", operation=operation)
    if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        fail("MATRIX-INVALID", f"{name} must be symmetric.", operation=operation)
    return matrix


def _parse_issues(value: Mapping[str, Any]) -> tuple[SimIssue, ...]:
    return tuple(
        SimIssue(
            **{
                **item,
                "evidence": tuple(Evidence(**entry) for entry in item.get("evidence", ())),
            }
        )
        for item in value.get("issues", ())
    )


def _issue(code: str, message: str, operation: str, objects: Sequence[str] = (), **kwargs: Any) -> SimIssue:
    return issue(code, message, operation, tuple(objects), **kwargs)


@dataclass(frozen=True, slots=True, kw_only=True)
class GeneralizedJointState:
    """A typed multi-DOF state for one rigid joint."""

    joint_id: str
    position: tuple[float, ...] | float
    velocity: tuple[float, ...] | float = ()
    acceleration: tuple[float, ...] | float = ()
    coordinate_frame: str = "joint"

    def __post_init__(self) -> None:
        if not self.joint_id or not self.coordinate_frame:
            fail("STATE-INVALID", "joint_id and coordinate_frame are required.", operation="GeneralizedJointState")
        position = (self.position,) if isinstance(self.position, (int, float)) else tuple(self.position)
        velocity = (self.velocity,) if isinstance(self.velocity, (int, float)) else tuple(self.velocity)
        acceleration = (self.acceleration,) if isinstance(self.acceleration, (int, float)) else tuple(self.acceleration)
        position = _vector(position, "position", "GeneralizedJointState")
        if not velocity:
            velocity = (0.0,) * len(position)
        if not acceleration:
            acceleration = (0.0,) * len(position)
        velocity = _vector(velocity, "velocity", "GeneralizedJointState")
        acceleration = _vector(acceleration, "acceleration", "GeneralizedJointState")
        if len(velocity) != len(position) or len(acceleration) != len(position):
            fail("STATE-INVALID", "position, velocity and acceleration must have equal dimensions.", operation="GeneralizedJointState", objects=(self.joint_id,))
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "velocity", velocity)
        object.__setattr__(self, "acceleration", acceleration)

    @property
    def dof_count(self) -> int:
        return len(self.position)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GeneralizedJointState":
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstraintSpec:
    """One linearized scalar constraint Jq=target for a declared state basis."""

    constraint_id: str
    coefficients: Mapping[str, float]
    target: float = 0.0
    velocity_target: float = 0.0
    acceleration_target: float = 0.0
    tolerance: float = 1e-8
    source: str = "declared"

    def __post_init__(self) -> None:
        op = "ConstraintSpec"
        if not self.constraint_id or not self.coefficients or not self.source:
            fail("CONSTRAINT-INVALID", "constraint_id, coefficients and source are required.", operation=op)
        object.__setattr__(self, "coefficients", {str(k): _finite(v, "coefficient", op) for k, v in self.coefficients.items()})
        for name in ("target", "velocity_target", "acceleration_target"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, op))
        tolerance = _finite(self.tolerance, "tolerance", op)
        if tolerance <= 0:
            fail("CONSTRAINT-INVALID", "tolerance must be positive.", operation=op, objects=(self.constraint_id,))
        object.__setattr__(self, "tolerance", tolerance)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConstraintSpec":
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReactionRequest:
    object_ids: tuple[str, ...]
    mode: str = "identifiable"
    reference_frame: str = "world"

    def __post_init__(self) -> None:
        if not self.object_ids or self.mode not in ("identifiable", "model_allocation", "aggregate"):
            fail("REACTION-INVALID", "Reaction request needs object IDs and a supported mode.", operation="ReactionRequest")
        object.__setattr__(self, "object_ids", tuple(self.object_ids))


@dataclass(frozen=True, slots=True, kw_only=True)
class RigidDynamicsScenario:
    states: tuple[GeneralizedJointState, ...]
    mass_matrix: tuple[tuple[float, ...], ...]
    force_vector: tuple[float, ...]
    duration_s: float
    sample_period_s: float
    damping_matrix: tuple[tuple[float, ...], ...] | None = None
    stiffness_matrix: tuple[tuple[float, ...], ...] | None = None
    constraints: tuple[ConstraintSpec, ...] = ()
    model_sha256: str | None = None
    scenario_id: str = ""

    def __post_init__(self) -> None:
        op = "RigidDynamicsScenario"
        states = tuple(self.states)
        if not states:
            fail("STATE-INVALID", "At least one generalized joint state is required.", operation=op)
        if len({state.joint_id for state in states}) != len(states):
            fail("STATE-INVALID", "Generalized joint IDs must be unique.", operation=op)
        object.__setattr__(self, "states", states)
        mass = _matrix(self.mass_matrix, "mass_matrix", op)
        if np.min(np.linalg.eigvalsh(mass)) <= 0:
            fail("MATRIX-INVALID", "mass_matrix must be positive definite.", operation=op)
        dimension = sum(state.dof_count for state in states)
        if len(mass) != dimension or len(self.force_vector) != dimension:
            fail("STATE-INVALID", "mass_matrix and force_vector must cover every generalized DOF.", operation=op)
        object.__setattr__(self, "mass_matrix", tuple(tuple(float(v) for v in row) for row in mass))
        object.__setattr__(self, "force_vector", _vector(self.force_vector, "force_vector", op))
        for name in ("damping_matrix", "stiffness_matrix"):
            matrix = getattr(self, name)
            if matrix is not None:
                value = _matrix(matrix, name, op)
                if len(value) != dimension:
                    fail("MATRIX-INVALID", f"{name} must match generalized DOF count.", operation=op)
                object.__setattr__(self, name, tuple(tuple(float(v) for v in row) for row in value))
        duration = _finite(self.duration_s, "duration_s", op)
        period = _finite(self.sample_period_s, "sample_period_s", op)
        if duration <= 0 or period <= 0:
            fail("TIME-INVALID", "duration_s and sample_period_s must be positive.", operation=op)
        object.__setattr__(self, "duration_s", duration)
        object.__setattr__(self, "sample_period_s", period)
        object.__setattr__(self, "constraints", tuple(self.constraints))

    @property
    def dof_ids(self) -> tuple[str, ...]:
        return tuple(f"{state.joint_id}[{index}]" for state in self.states for index in range(state.dof_count))

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RigidDynamicsScenario":
        return cls(
            **{
                **value,
                "states": tuple(GeneralizedJointState.from_dict(item) for item in value["states"]),
                "constraints": tuple(ConstraintSpec.from_dict(item) for item in value.get("constraints", ())),
            }
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class MultibodySample:
    time_s: float
    positions: Mapping[str, float]
    velocities: Mapping[str, float]
    accelerations: Mapping[str, float]
    generalized_forces: Mapping[str, float]
    constraint_reactions: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", "MultibodySample"))
        for name in ("positions", "velocities", "accelerations", "generalized_forces", "constraint_reactions"):
            object.__setattr__(self, name, {str(k): _finite(v, name, "MultibodySample") for k, v in getattr(self, name).items()})

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MultibodySample":
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class MultibodyResult(PhysicsReport):
    operation: str = "solve_multibody_dynamics"
    model_sha256: str | None = None
    scenario_id: str = ""
    samples: tuple[MultibodySample, ...] = ()
    reaction_mode: str = "identifiable"
    constraint_residual_max: float = 0.0
    energy_residual_j: float = 0.0

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        samples = tuple(self.samples)
        if any(b.time_s <= a.time_s for a, b in zip(samples, samples[1:])):
            fail("RESULT-INVALID", "Multibody samples must be strictly time ordered.", operation=self.operation)
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "constraint_residual_max", _finite(self.constraint_residual_max, "constraint_residual_max", self.operation))
        object.__setattr__(self, "energy_residual_j", _finite(self.energy_residual_j, "energy_residual_j", self.operation))

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "passed": self.passed}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MultibodyResult":
        return cls(
            operation=value.get("operation", "solve_multibody_dynamics"),
            status=value.get("status", "failed"),
            issues=_parse_issues(value),
            evidence=value.get("evidence", {}),
            model_sha256=value.get("model_sha256"),
            result_index=value.get("result_index"),
            scenario_id=value.get("scenario_id", ""),
            samples=tuple(MultibodySample.from_dict(item) for item in value.get("samples", ())),
            reaction_mode=value.get("reaction_mode", "identifiable"),
            constraint_residual_max=value.get("constraint_residual_max", 0.0),
            energy_residual_j=value.get("energy_residual_j", 0.0),
        )


def probe_multibody_capabilities(*, scenario: RigidDynamicsScenario | None, operation: str = "solve_multibody_dynamics") -> PhysicsReport:
    if not isinstance(scenario, RigidDynamicsScenario):
        return PhysicsReport(operation=operation, status="validation_failed", issues=(_issue("SCENARIO-INVALID", "A typed RigidDynamicsScenario is required.", operation),))
    return PhysicsReport(operation=operation, status="passed", evidence={"backend": "kincheck-rigid-generalized-reference", "supports": ["linear_constraints", "multi_dof_state", "reaction_history"], "fea_dependency": False})


def solve_multibody_dynamics(*, scenario: RigidDynamicsScenario, reaction_request: ReactionRequest | None = None) -> MultibodyResult:
    op = "solve_multibody_dynamics"
    probe = probe_multibody_capabilities(scenario=scenario, operation=op)
    if not probe.passed:
        return MultibodyResult(status=probe.status, issues=probe.issues, evidence=probe.evidence, model_sha256=getattr(scenario, "model_sha256", None))
    dimension = len(scenario.force_vector)
    q = np.array([value for state in scenario.states for value in state.position], dtype=float)
    v = np.array([value for state in scenario.states for value in state.velocity], dtype=float)
    a = np.array([value for state in scenario.states for value in state.acceleration], dtype=float)
    M = np.asarray(scenario.mass_matrix, dtype=float)
    C = np.zeros_like(M) if scenario.damping_matrix is None else np.asarray(scenario.damping_matrix, dtype=float)
    K = np.zeros_like(M) if scenario.stiffness_matrix is None else np.asarray(scenario.stiffness_matrix, dtype=float)
    key_to_index = {key: index for index, key in enumerate(scenario.dof_ids)}
    constraint_rows = []
    for constraint in scenario.constraints:
        row = np.zeros(dimension, dtype=float)
        for key, coefficient in constraint.coefficients.items():
            if key not in key_to_index:
                return MultibodyResult(status="validation_failed", issues=(_issue("CONSTRAINT-REFERENCE-MISSING", "Constraint references an unknown generalized DOF.", op, (constraint.constraint_id, key)),), model_sha256=scenario.model_sha256)
            row[key_to_index[key]] = coefficient
        constraint_rows.append((constraint, row))
    times = np.arange(0.0, scenario.duration_s + scenario.sample_period_s * 0.5, scenario.sample_period_s)
    samples: list[MultibodySample] = []
    max_residual = 0.0
    reaction_records: dict[str, float] = {}
    for time_s in times:
        force = np.asarray(scenario.force_vector, dtype=float) - C @ v - K @ q
        if constraint_rows:
            J = np.vstack([row for _, row in constraint_rows])
            rhs_constraint = np.array([constraint.acceleration_target for constraint, _ in constraint_rows], dtype=float)
            kkt = np.block([[M, -J.T], [J, np.zeros((len(constraint_rows), len(constraint_rows)))]])
            rhs = np.concatenate((force, rhs_constraint))
            try:
                solution = np.linalg.solve(kkt, rhs)
            except np.linalg.LinAlgError as exc:
                return MultibodyResult(status="indeterminate", issues=(_issue("CONSTRAINT-SOLVE-FAILED", str(exc), op),), evidence={"dof_ids": list(scenario.dof_ids)}, model_sha256=scenario.model_sha256)
            a = solution[:dimension]
            lambdas = solution[dimension:]
            for (constraint, _), reaction in zip(constraint_rows, lambdas):
                reaction_records[constraint.constraint_id] = float(reaction)
            residual = J @ q - np.array([constraint.target for constraint, _ in constraint_rows])
            max_residual = max(max_residual, float(np.max(np.abs(residual))))
        else:
            try:
                a = np.linalg.solve(M, force)
            except np.linalg.LinAlgError as exc:
                return MultibodyResult(status="indeterminate", issues=(_issue("DYNAMICS-SOLVE-FAILED", str(exc), op),), model_sha256=scenario.model_sha256)
        samples.append(MultibodySample(time_s=float(time_s), positions=dict(zip(scenario.dof_ids, q)), velocities=dict(zip(scenario.dof_ids, v)), accelerations=dict(zip(scenario.dof_ids, a)), generalized_forces=dict(zip(scenario.dof_ids, scenario.force_vector)), constraint_reactions=dict(reaction_records)))
        v = v + scenario.sample_period_s * a
        q = q + scenario.sample_period_s * v
    status = "completed" if max_residual <= max((constraint.tolerance for constraint, _ in constraint_rows), default=1e-8) else "indeterminate"
    issues = () if status == "completed" else (_issue("CONSTRAINT-RESIDUAL-EXCEEDED", "Constraint residual exceeded its declared tolerance.", op, actual=max_residual),)
    return MultibodyResult(status=status, issues=issues, model_sha256=scenario.model_sha256, scenario_id=scenario.scenario_id, samples=tuple(samples), reaction_mode=reaction_request.mode if reaction_request else "identifiable", constraint_residual_max=max_residual, evidence={"backend": "kincheck-rigid-generalized-reference", "dof_ids": list(scenario.dof_ids), "fea_dependency": False})


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactInterface:
    contact_id: str
    normal: tuple[float, float, float]
    gap_m: float
    friction_coefficient: float = 0.0
    normal_stiffness_n_m: float | None = None
    normal_damping_n_s_m: float = 0.0
    restitution: float | None = None
    source: str = "declared"

    def __post_init__(self) -> None:
        normal = _vector(self.normal, "normal", "ContactInterface")
        if len(normal) != 3:
            fail("CONTACT-INVALID", "normal must be a 3-vector.", operation="ContactInterface")
        norm = math.sqrt(sum(value * value for value in normal))
        if abs(norm - 1.0) > 1e-9:
            fail("CONTACT-INVALID", "normal must be unit length.", operation="ContactInterface")
        object.__setattr__(self, "normal", tuple(normal))
        gap = _finite(self.gap_m, "gap_m", "ContactInterface")
        mu = _finite(self.friction_coefficient, "friction_coefficient", "ContactInterface")
        damping = _finite(self.normal_damping_n_s_m, "normal_damping_n_s_m", "ContactInterface")
        if mu < 0 or damping < 0:
            fail("CONTACT-INVALID", "friction and damping cannot be negative.", operation="ContactInterface", objects=(self.contact_id,))
        object.__setattr__(self, "gap_m", gap)
        object.__setattr__(self, "friction_coefficient", mu)
        object.__setattr__(self, "normal_damping_n_s_m", damping)
        if self.normal_stiffness_n_m is not None:
            stiffness = _finite(self.normal_stiffness_n_m, "normal_stiffness_n_m", "ContactInterface")
            if stiffness <= 0:
                fail("CONTACT-INVALID", "normal_stiffness_n_m must be positive.", operation="ContactInterface")
            object.__setattr__(self, "normal_stiffness_n_m", stiffness)
        if self.restitution is not None and not 0 <= _finite(self.restitution, "restitution", "ContactInterface") <= 1:
            fail("CONTACT-INVALID", "restitution must lie in [0, 1].", operation="ContactInterface")


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactEvent:
    time_s: float
    contact_id: str
    state: str
    normal_force_n: float
    tangential_force_n: tuple[float, float, float]
    penetration_m: float
    normal_impulse_ns: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", "ContactEvent"))
        object.__setattr__(self, "normal_force_n", _finite(self.normal_force_n, "normal_force_n", "ContactEvent"))
        object.__setattr__(self, "penetration_m", _finite(self.penetration_m, "penetration_m", "ContactEvent"))
        object.__setattr__(self, "normal_impulse_ns", _finite(self.normal_impulse_ns, "normal_impulse_ns", "ContactEvent"))
        object.__setattr__(self, "tangential_force_n", tuple(_finite(value, "tangential_force_n", "ContactEvent") for value in self.tangential_force_n))

    def to_dict(self) -> dict[str, Any]:
        return plain(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactDynamicsResult(PhysicsReport):
    operation: str = "solve_contact_dynamics"
    contact_id: str = ""
    events: tuple[ContactEvent, ...] = ()
    impulse_ns: float = 0.0
    momentum_residual_n_s: float = 0.0
    energy_dissipation_j: float = 0.0

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "impulse_ns", _finite(self.impulse_ns, "impulse_ns", self.operation))
        object.__setattr__(self, "momentum_residual_n_s", _finite(self.momentum_residual_n_s, "momentum_residual_n_s", self.operation))
        object.__setattr__(self, "energy_dissipation_j", _finite(self.energy_dissipation_j, "energy_dissipation_j", self.operation))

    def to_dict(self) -> dict[str, Any]:
        return plain(self) | {"passed": self.passed}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ContactDynamicsResult":
        return cls(operation=value.get("operation", "solve_contact_dynamics"), status=value.get("status", "failed"), issues=_parse_issues(value), evidence=value.get("evidence", {}), model_sha256=value.get("model_sha256"), result_index=value.get("result_index"), contact_id=value.get("contact_id", ""), events=tuple(ContactEvent(**item) for item in value.get("events", ())), impulse_ns=value.get("impulse_ns", 0.0), momentum_residual_n_s=value.get("momentum_residual_n_s", 0.0), energy_dissipation_j=value.get("energy_dissipation_j", 0.0))


def solve_contact_dynamics(*, interface: ContactInterface, times_s: Sequence[float], relative_gap_m: Sequence[float], relative_normal_velocity_m_s: Sequence[float]) -> ContactDynamicsResult:
    op = "solve_contact_dynamics"
    times = tuple(_finite(value, "time_s", op) for value in times_s)
    gaps = tuple(_finite(value, "relative_gap_m", op) for value in relative_gap_m)
    velocities = tuple(_finite(value, "relative_normal_velocity_m_s", op) for value in relative_normal_velocity_m_s)
    if len(times) < 2 or len(times) != len(gaps) or len(times) != len(velocities) or any(b <= a for a, b in zip(times, times[1:])):
        return ContactDynamicsResult(status="validation_failed", issues=(_issue("TIME-INVALID", "Contact times and samples must be aligned and strictly increasing.", op),), contact_id=interface.contact_id)
    if interface.normal_stiffness_n_m is None:
        return ContactDynamicsResult(status="capability_failed", issues=(_issue("CONTACT-LAW-MISSING", "A finite normal stiffness is required for finite contact-force response.", op, (interface.contact_id,)),), contact_id=interface.contact_id)
    forces = []
    events = []
    for time_s, gap, velocity in zip(times, gaps, velocities):
        penetration = max(0.0, -gap)
        normal_force = max(0.0, interface.normal_stiffness_n_m * penetration - interface.normal_damping_n_s_m * velocity)
        state = "contact" if penetration > 0 else "separated"
        forces.append(normal_force)
        events.append(ContactEvent(time_s=time_s, contact_id=interface.contact_id, state=state, normal_force_n=normal_force, tangential_force_n=(0.0, 0.0, 0.0), penetration_m=penetration))
    integral = float(np.trapezoid(forces, times) if hasattr(np, "trapezoid") else np.trapz(forces, times))
    return ContactDynamicsResult(status="completed", contact_id=interface.contact_id, events=tuple(events), impulse_ns=integral, momentum_residual_n_s=0.0, energy_dissipation_j=float(sum(max(0.0, interface.normal_damping_n_s_m * velocity * velocity) for velocity in velocities) * (times[-1] - times[0]) / len(times)), evidence={"law": "normal penalty-damper", "feacore": False, "convergence": {"time_samples": len(times)}})


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicsLoadHistory:
    history_id: str
    model_sha256: str | None
    scenario_id: str
    times_s: tuple[float, ...]
    records: tuple[Mapping[str, Any], ...]
    schema_version: str = "kincheck.dynamics-history/1.0"
    status: str = "completed"
    issues: tuple[SimIssue, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema_version != "kincheck.dynamics-history/1.0" or not self.history_id:
            fail("HISTORY-INVALID", "history_id and supported schema_version are required.", operation="DynamicsLoadHistory")
        times = tuple(_finite(value, "time_s", "DynamicsLoadHistory") for value in self.times_s)
        if any(b <= a for a, b in zip(times, times[1:])) or len(times) != len(self.records):
            fail("HISTORY-INVALID", "times_s and records must be aligned and strictly ordered.", operation="DynamicsLoadHistory")
        object.__setattr__(self, "times_s", times)
        object.__setattr__(self, "records", tuple(dict(record) for record in self.records))
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "issues": [item.to_dict() for item in self.issues], "passed": self.status == "completed" and not self.issues}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DynamicsLoadHistory":
        return cls(schema_version=value.get("schema_version", ""), history_id=value.get("history_id", ""), model_sha256=value.get("model_sha256"), scenario_id=value.get("scenario_id", ""), times_s=tuple(value.get("times_s", ())), records=tuple(value.get("records", ())), status=value.get("status", "failed"), issues=_parse_issues(value), evidence=value.get("evidence", {}))


def history_from_multibody_result(*, result: MultibodyResult, history_id: str = "dynamics-history") -> DynamicsLoadHistory:
    records = tuple({"positions": sample.positions, "velocities": sample.velocities, "accelerations": sample.accelerations, "generalized_forces": sample.generalized_forces, "constraint_reactions": sample.constraint_reactions, "source": "solve_multibody_dynamics"} for sample in result.samples)
    return DynamicsLoadHistory(history_id=history_id, model_sha256=result.model_sha256, scenario_id=result.scenario_id, times_s=tuple(sample.time_s for sample in result.samples), records=records, status=result.status, issues=result.issues, evidence={"result_operation": result.operation})


def export_load_history(*, history: DynamicsLoadHistory, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(json.dumps(history.to_dict(), sort_keys=True, indent=2, allow_nan=False), encoding="utf-8")
    return output


def read_load_history(*, path: str | Path) -> DynamicsLoadHistory:
    return DynamicsLoadHistory.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


__all__ = ["GeneralizedJointState", "ConstraintSpec", "ReactionRequest", "RigidDynamicsScenario", "MultibodySample", "MultibodyResult", "probe_multibody_capabilities", "solve_multibody_dynamics", "ContactInterface", "ContactEvent", "ContactDynamicsResult", "solve_contact_dynamics", "DynamicsLoadHistory", "history_from_multibody_result", "export_load_history", "read_load_history"]
