"""v0.7 rigid-body dynamics contracts.

This module deliberately contains only kinematics/rigid-body dynamics.  It
does not import a finite-element package or represent structural stress,
deformation, modal fields, or fatigue life.  The public records are designed
to be exported to the future FEACheckAPI through JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .diagnostics import Evidence, SimIssue
from .physics_types import PhysicsReport, digest, fail, issue, plain


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
    relation: str = "linear"
    receiver_ids: tuple[str, ...] = ()
    source_map: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        op = "ConstraintSpec"
        if not self.constraint_id or not self.coefficients or not self.source:
            fail("CONSTRAINT-INVALID", "constraint_id, coefficients and source are required.", operation=op)
        if self.relation not in ("linear", "transmission", "closure", "support"):
            fail("CONSTRAINT-INVALID", "relation must be linear, transmission, closure or support.", operation=op)
        object.__setattr__(self, "coefficients", {str(k): _finite(v, "coefficient", op) for k, v in self.coefficients.items()})
        for name in ("target", "velocity_target", "acceleration_target"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, op))
        tolerance = _finite(self.tolerance, "tolerance", op)
        if tolerance <= 0:
            fail("CONSTRAINT-INVALID", "tolerance must be positive.", operation=op, objects=(self.constraint_id,))
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "receiver_ids", tuple(str(item) for item in self.receiver_ids))
        object.__setattr__(self, "source_map", dict(self.source_map))

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
    require_unique: bool = True

    def __post_init__(self) -> None:
        if not self.object_ids or self.mode not in ("identifiable", "model_allocation", "aggregate"):
            fail("REACTION-INVALID", "Reaction request needs object IDs and a supported mode.", operation="ReactionRequest")
        if not self.reference_frame:
            fail("REACTION-INVALID", "reference_frame is required.", operation="ReactionRequest")
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
    contacts: tuple[Any, ...] = ()
    controllers: tuple[Any, ...] = ()
    brake_policy: Any | None = None

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
        object.__setattr__(self, "contacts", tuple(self.contacts))
        object.__setattr__(self, "controllers", tuple(self.controllers))

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
                "contacts": tuple(
                    ContactInterface.from_dict(item) if isinstance(item, Mapping) else item
                    for item in value.get("contacts", ())
                ),
                "controllers": tuple(value.get("controllers", ())),
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
    reaction_rank: int = 0
    reaction_constraint_count: int = 0
    contact_events: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        samples = tuple(self.samples)
        if any(b.time_s <= a.time_s for a, b in zip(samples, samples[1:])):
            fail("RESULT-INVALID", "Multibody samples must be strictly time ordered.", operation=self.operation)
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "constraint_residual_max", _finite(self.constraint_residual_max, "constraint_residual_max", self.operation))
        object.__setattr__(self, "energy_residual_j", _finite(self.energy_residual_j, "energy_residual_j", self.operation))
        if self.reaction_rank < 0 or self.reaction_constraint_count < 0:
            fail("RESULT-INVALID", "Reaction rank/count cannot be negative.", operation=self.operation)
        object.__setattr__(self, "contact_events", tuple(self.contact_events))

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
            reaction_rank=value.get("reaction_rank", 0),
            reaction_constraint_count=value.get("reaction_constraint_count", 0),
            contact_events=tuple(
                ContactEvent(**item) if isinstance(item, Mapping) else item
                for item in value.get("contact_events", ())
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicsScenarioCase:
    """One independently identifiable rigid-body operating case."""

    case_id: str
    scenario: RigidDynamicsScenario
    reaction_request: ReactionRequest | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id or not isinstance(self.scenario, RigidDynamicsScenario):
            fail("CASE-INVALID", "case_id and a typed RigidDynamicsScenario are required.", operation="DynamicsScenarioCase")
        object.__setattr__(self, "tags", tuple(str(tag) for tag in self.tags))

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DynamicsScenarioCase":
        return cls(
            case_id=str(value["case_id"]),
            scenario=RigidDynamicsScenario.from_dict(value["scenario"]),
            reaction_request=(
                None
                if value.get("reaction_request") is None
                else ReactionRequest(**value["reaction_request"])
            ),
            tags=tuple(value.get("tags", ())),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicsScenarioMatrix:
    """A finite, auditable set of cases; an empty matrix is never acceptance-passed."""

    matrix_id: str
    cases: tuple[DynamicsScenarioCase, ...]
    requested_case_ids: tuple[str, ...] | None = None
    source: str = "declared"

    def __post_init__(self) -> None:
        if not self.matrix_id or not self.source:
            fail("MATRIX-INVALID", "matrix_id and source are required.", operation="DynamicsScenarioMatrix")
        cases = tuple(self.cases)
        if any(not isinstance(case, DynamicsScenarioCase) for case in cases):
            fail("MATRIX-INVALID", "cases must contain DynamicsScenarioCase values.", operation="DynamicsScenarioMatrix")
        ids = tuple(case.case_id for case in cases)
        if len(set(ids)) != len(ids):
            fail("MATRIX-INVALID", "Scenario case IDs must be unique.", operation="DynamicsScenarioMatrix")
        requested = ids if self.requested_case_ids is None else tuple(str(item) for item in self.requested_case_ids)
        if len(set(requested)) != len(requested) or any(item not in ids for item in requested):
            fail("MATRIX-INVALID", "requested_case_ids must identify declared cases exactly once.", operation="DynamicsScenarioMatrix")
        object.__setattr__(self, "cases", cases)
        object.__setattr__(self, "requested_case_ids", requested)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DynamicsScenarioMatrix":
        return cls(
            matrix_id=str(value["matrix_id"]),
            cases=tuple(DynamicsScenarioCase.from_dict(item) for item in value.get("cases", ())),
            requested_case_ids=tuple(value["requested_case_ids"]) if value.get("requested_case_ids") is not None else None,
            source=str(value.get("source", "declared")),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicsScenarioSuite(PhysicsReport):
    operation: str = "run_dynamics_cases"
    matrix_id: str = ""
    case_results: tuple[MultibodyResult, ...] = ()
    requested_case_ids: tuple[str, ...] = ()
    evaluated_case_ids: tuple[str, ...] = ()
    missing_case_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        PhysicsReport.__post_init__(self)
        object.__setattr__(self, "case_results", tuple(self.case_results))
        object.__setattr__(self, "requested_case_ids", tuple(self.requested_case_ids))
        object.__setattr__(self, "evaluated_case_ids", tuple(self.evaluated_case_ids))
        object.__setattr__(self, "missing_case_ids", tuple(self.missing_case_ids))

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "case_results": [item.to_dict() for item in self.case_results], "passed": self.passed}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DynamicsScenarioSuite":
        return cls(
            operation=value.get("operation", "run_dynamics_cases"),
            status=value.get("status", "failed"),
            issues=_parse_issues(value),
            evidence=value.get("evidence", {}),
            model_sha256=value.get("model_sha256"),
            result_index=value.get("result_index"),
            matrix_id=value.get("matrix_id", ""),
            case_results=tuple(MultibodyResult.from_dict(item) for item in value.get("case_results", ())),
            requested_case_ids=tuple(value.get("requested_case_ids", ())),
            evaluated_case_ids=tuple(value.get("evaluated_case_ids", ())),
            missing_case_ids=tuple(value.get("missing_case_ids", ())),
        )


def probe_multibody_capabilities(*, scenario: RigidDynamicsScenario | None, operation: str = "solve_multibody_dynamics") -> PhysicsReport:
    if not isinstance(scenario, RigidDynamicsScenario):
        return PhysicsReport(operation=operation, status="validation_failed", issues=(_issue("SCENARIO-INVALID", "A typed RigidDynamicsScenario is required.", operation),))
    if any(getattr(contact, "restitution", None) is not None for contact in scenario.contacts):
        return PhysicsReport(operation=operation, status="capability_failed", issues=(_issue("CONTACT-IMPACT-LAW-UNSUPPORTED", "The reference integrator supports penalty contact but not instantaneous restitution impulses.", operation),), evidence={"backend": "kincheck-rigid-generalized-reference", "fea_dependency": False})
    if any(getattr(contact, "dof_coefficients", {}) and getattr(contact, "normal_stiffness_n_m", None) is None for contact in scenario.contacts):
        return PhysicsReport(operation=operation, status="capability_failed", issues=(_issue("CONTACT-LAW-MISSING", "A coupled contact requires normal_stiffness_n_m for the reference penalty response.", operation),), evidence={"backend": "kincheck-rigid-generalized-reference", "fea_dependency": False})
    return PhysicsReport(operation=operation, status="passed", evidence={"backend": "kincheck-rigid-generalized-reference", "supports": ["linear_constraints", "multi_dof_state", "reaction_history", "declared_contact_penalty", "contact_friction"], "fea_dependency": False})


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
    source_map: dict[str, Any] = {}
    for constraint in scenario.constraints:
        row = np.zeros(dimension, dtype=float)
        for key, coefficient in constraint.coefficients.items():
            if key not in key_to_index:
                return MultibodyResult(status="validation_failed", issues=(_issue("CONSTRAINT-REFERENCE-MISSING", "Constraint references an unknown generalized DOF.", op, (constraint.constraint_id, key)),), model_sha256=scenario.model_sha256)
            row[key_to_index[key]] = coefficient
        constraint_rows.append((constraint, row))
        source_map[constraint.constraint_id] = {
            "relation": constraint.relation,
            "source": constraint.source,
            "receiver_ids": list(constraint.receiver_ids),
            "coefficients": dict(constraint.coefficients),
            "source_map": dict(constraint.source_map),
        }
    reaction_rank = 0
    reaction_count = len(constraint_rows)
    J = np.vstack([row for _, row in constraint_rows]) if constraint_rows else np.zeros((0, dimension))
    if constraint_rows:
        reaction_rank = int(np.linalg.matrix_rank(J, tol=1e-10))
        if reaction_request is not None and reaction_request.require_unique and reaction_request.mode != "aggregate" and reaction_rank < reaction_count:
            return MultibodyResult(status="indeterminate", issues=(_issue("REACTION-NONUNIQUE", "Constraint reactions are redundant and cannot be uniquely allocated without a declared compliance or allocation model.", op, actual=reaction_rank, expected=reaction_count),), model_sha256=scenario.model_sha256, reaction_mode=reaction_request.mode, reaction_rank=reaction_rank, reaction_constraint_count=reaction_count, evidence={"dof_ids": list(scenario.dof_ids), "constraint_rank": reaction_rank, "constraint_count": reaction_count, "source_map": source_map, "allocation": "aggregate-only"})
        if reaction_rank < reaction_count:
            return MultibodyResult(status="indeterminate", issues=(_issue("CONSTRAINT-SOLVE-SINGULAR", "Constraint rows are linearly dependent; only an aggregate reaction can be reported.", op, actual=reaction_rank, expected=reaction_count),), model_sha256=scenario.model_sha256, reaction_mode="aggregate", reaction_rank=reaction_rank, reaction_constraint_count=reaction_count, evidence={"dof_ids": list(scenario.dof_ids), "constraint_rank": reaction_rank, "constraint_count": reaction_count, "source_map": source_map})
        if not np.all(np.isfinite(J)):
            return MultibodyResult(status="validation_failed", issues=(_issue("CONSTRAINT-MATRIX-INVALID", "The constraint Jacobian contains nonfinite values.", op),), model_sha256=scenario.model_sha256, evidence={"source_map": source_map})
        initial_residual = J @ q - np.array([constraint.target for constraint, _ in constraint_rows], dtype=float)
        initial_tolerance = max((constraint.tolerance for constraint, _ in constraint_rows), default=1e-8)
        if float(np.max(np.abs(initial_residual))) > initial_tolerance:
            return MultibodyResult(status="validation_failed", issues=(_issue("INITIAL-CONSTRAINT-VIOLATION", "Initial generalized positions do not satisfy the declared constraints.", op, actual=float(np.max(np.abs(initial_residual))), expected=initial_tolerance),), model_sha256=scenario.model_sha256, reaction_rank=reaction_rank, reaction_constraint_count=reaction_count, evidence={"initial_residual": initial_residual.tolist(), "source_map": source_map})
    times = np.arange(0.0, scenario.duration_s + scenario.sample_period_s * 0.5, scenario.sample_period_s)
    samples: list[MultibodySample] = []
    contact_events: list[Any] = []
    max_residual = 0.0
    reaction_records: dict[str, float] = {}
    work_j = 0.0
    controller_violations: list[str] = []
    for time_s in times:
        force = np.asarray(scenario.force_vector, dtype=float) - C @ v - K @ q
        for controller in scenario.controllers:
            limits = getattr(controller, "dof_limits", {})
            for dof, limit in limits.items():
                if dof in key_to_index and abs(float(force[key_to_index[dof]])) > float(limit):
                    controller_violations.append(dof)
            stop_time = getattr(controller, "emergency_stop_time_s", None)
            if stop_time is not None and float(time_s) >= float(stop_time):
                for dof in limits:
                    if dof in key_to_index:
                        force[key_to_index[dof]] = 0.0
        brake = scenario.brake_policy
        if brake is not None and float(time_s) >= float(getattr(brake, "trigger_time_s", math.inf)) + float(getattr(brake, "delay_s", 0.0)):
            for dof, limit in getattr(brake, "braking_limits", {}).items():
                if dof in key_to_index and abs(v[key_to_index[dof]]) > 1e-12:
                    force[key_to_index[dof]] -= math.copysign(float(limit), v[key_to_index[dof]])
        for contact in scenario.contacts:
            if not isinstance(contact, ContactInterface):
                return MultibodyResult(status="validation_failed", issues=(_issue("CONTACT-INVALID", "Scenario contacts must contain ContactInterface values.", op),), model_sha256=scenario.model_sha256)
            coefficients = getattr(contact, "dof_coefficients", {})
            if not coefficients:
                continue
            row = np.zeros(dimension, dtype=float)
            for dof, coefficient in coefficients.items():
                if dof not in key_to_index:
                    return MultibodyResult(status="validation_failed", issues=(_issue("CONTACT-REFERENCE-MISSING", "Contact references an unknown generalized DOF.", op, (contact.contact_id, str(dof))),), model_sha256=scenario.model_sha256)
                row[key_to_index[dof]] = float(coefficient)
            gap = float(contact.gap_m + row @ q)
            normal_velocity = float(row @ v)
            penetration = max(0.0, -gap)
            normal_force = max(0.0, float(contact.normal_stiffness_n_m or 0.0) * penetration - float(contact.normal_damping_n_s_m) * normal_velocity)
            force += row * normal_force
            tangent_force_vector = np.zeros(3, dtype=float)
            for tangent_row_map in getattr(contact, "tangential_coefficients", ()):
                tangent_row = np.zeros(dimension, dtype=float)
                for dof, coefficient in tangent_row_map.items():
                    if dof not in key_to_index:
                        return MultibodyResult(status="validation_failed", issues=(_issue("CONTACT-REFERENCE-MISSING", "Contact tangent references an unknown generalized DOF.", op, (contact.contact_id, str(dof))),), model_sha256=scenario.model_sha256)
                    tangent_row[key_to_index[dof]] = float(coefficient)
                tangent_velocity = float(tangent_row @ v)
                if abs(tangent_velocity) > 1e-12 and normal_force > 0:
                    tangent_force = -float(contact.friction_coefficient) * normal_force * math.copysign(1.0, tangent_velocity)
                    force += tangent_row * tangent_force
                    if len(tangent_force_vector) > 0:
                        tangent_force_vector[0] += tangent_force
            contact_events.append(ContactEvent(time_s=float(time_s), contact_id=contact.contact_id, state="contact" if penetration > 0 else "separated", normal_force_n=normal_force, tangential_force_n=tuple(float(value) for value in tangent_force_vector), penetration_m=penetration, normal=contact.normal, contact_point_m=contact.contact_point_m))
        if controller_violations:
            return MultibodyResult(status="failed", issues=(_issue("ACTUATOR-LIMIT-EXCEEDED", "A declared controller force limit was exceeded.", op, actual=sorted(set(controller_violations)), expected="controller limit"),), model_sha256=scenario.model_sha256, scenario_id=scenario.scenario_id, reaction_rank=reaction_rank, reaction_constraint_count=reaction_count, evidence={"source_map": source_map})
        if constraint_rows:
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
        samples.append(MultibodySample(time_s=float(time_s), positions=dict(zip(scenario.dof_ids, q)), velocities=dict(zip(scenario.dof_ids, v)), accelerations=dict(zip(scenario.dof_ids, a)), generalized_forces=dict(zip(scenario.dof_ids, force)), constraint_reactions=dict(reaction_records)))
        if len(samples) > 1:
            work_j += float(np.dot(force, v)) * scenario.sample_period_s
        v = v + scenario.sample_period_s * a
        q = q + scenario.sample_period_s * v
    status = "completed" if max_residual <= max((constraint.tolerance for constraint, _ in constraint_rows), default=1e-8) else "indeterminate"
    issues = () if status == "completed" else (_issue("CONSTRAINT-RESIDUAL-EXCEEDED", "Constraint residual exceeded its declared tolerance.", op, actual=max_residual),)
    return MultibodyResult(status=status, issues=issues, model_sha256=scenario.model_sha256, scenario_id=scenario.scenario_id, samples=tuple(samples), reaction_mode=reaction_request.mode if reaction_request else "identifiable", constraint_residual_max=max_residual, energy_residual_j=work_j, reaction_rank=reaction_rank, reaction_constraint_count=reaction_count, contact_events=tuple(contact_events), evidence={"backend": "kincheck-rigid-generalized-reference", "dof_ids": list(scenario.dof_ids), "fea_dependency": False, "constraint_rank": reaction_rank, "constraint_count": reaction_count, "source_map": source_map, "contact_event_count": len(contact_events), "controller_count": len(scenario.controllers), "energy": {"work_j": work_j, "integration": "sampled-generalized-power"}})


def run_dynamics_cases(*, matrix: DynamicsScenarioMatrix) -> DynamicsScenarioSuite:
    """Solve every declared rigid-body case and report explicit coverage."""

    op = "run_dynamics_cases"
    if not isinstance(matrix, DynamicsScenarioMatrix):
        return DynamicsScenarioSuite(
            status="validation_failed",
            issues=(_issue("MATRIX-INVALID", "A typed DynamicsScenarioMatrix is required.", op),),
        )
    by_id = {case.case_id: case for case in matrix.cases}
    results: list[MultibodyResult] = []
    evaluated_ids: list[str] = []
    for index, case_id in enumerate(matrix.requested_case_ids):
        case = by_id.get(case_id)
        if case is None:
            continue
        result = solve_multibody_dynamics(
            scenario=case.scenario,
            reaction_request=case.reaction_request,
        )
        results.append(replace(result, result_index=index))
        evaluated_ids.append(case_id)
    missing = tuple(case_id for case_id in matrix.requested_case_ids if case_id not in by_id)
    failed = tuple(result for result in results if not result.passed)
    if not matrix.requested_case_ids:
        status = "validation_failed"
        issues = (_issue("MATRIX-EMPTY", "At least one requested dynamics case is required.", op),)
    elif missing:
        status = "indeterminate"
        issues = (_issue("MATRIX-COVERAGE-INCOMPLETE", "One or more requested dynamics cases were not evaluated.", op, actual=list(missing), expected=list(matrix.requested_case_ids)),)
    elif failed:
        status = "failed" if any(result.status == "failed" for result in failed) else "indeterminate"
        issues = tuple(issue_item for result in failed for issue_item in result.issues)
    else:
        status = "completed"
        issues = ()
    return DynamicsScenarioSuite(
        status=status,
        issues=issues,
        matrix_id=matrix.matrix_id,
        case_results=tuple(results),
        requested_case_ids=tuple(matrix.requested_case_ids),
        evaluated_case_ids=tuple(evaluated_ids),
        missing_case_ids=missing,
        evidence={
            "source": matrix.source,
            "requested_count": len(matrix.requested_case_ids),
            "evaluated_count": len(results),
            "coverage_complete": not missing and bool(matrix.requested_case_ids),
            "fea_dependency": False,
        },
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactInterface:
    contact_id: str
    normal: tuple[float, float, float]
    gap_m: float
    body_a: str = ""
    body_b: str = ""
    contact_point_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    coordinate_frame: str = "world"
    dof_coefficients: Mapping[str, float] = field(default_factory=dict)
    tangential_coefficients: tuple[Mapping[str, float], ...] = ()
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
        point = tuple(_finite(value, "contact_point_m", "ContactInterface") for value in self.contact_point_m)
        if len(point) != 3 or not self.coordinate_frame:
            fail("CONTACT-INVALID", "contact_point_m must be a 3-vector and coordinate_frame is required.", operation="ContactInterface")
        object.__setattr__(self, "contact_point_m", point)
        object.__setattr__(self, "dof_coefficients", {str(key): _finite(value, "dof_coefficient", "ContactInterface") for key, value in self.dof_coefficients.items()})
        tangent_maps = tuple({str(key): _finite(value, "tangent_coefficient", "ContactInterface") for key, value in mapping.items()} for mapping in self.tangential_coefficients)
        if len(tangent_maps) > 2:
            fail("CONTACT-INVALID", "At most two tangential coefficient rows are supported.", operation="ContactInterface")
        object.__setattr__(self, "tangential_coefficients", tangent_maps)
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

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ContactInterface":
        return cls(**value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContactEvent:
    time_s: float
    contact_id: str
    state: str
    normal_force_n: float
    tangential_force_n: tuple[float, float, float]
    penetration_m: float
    normal_impulse_ns: float = 0.0
    normal: tuple[float, float, float] = (0.0, 0.0, 1.0)
    contact_point_m: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", "ContactEvent"))
        object.__setattr__(self, "normal_force_n", _finite(self.normal_force_n, "normal_force_n", "ContactEvent"))
        object.__setattr__(self, "penetration_m", _finite(self.penetration_m, "penetration_m", "ContactEvent"))
        object.__setattr__(self, "normal_impulse_ns", _finite(self.normal_impulse_ns, "normal_impulse_ns", "ContactEvent"))
        tangent = tuple(_finite(value, "tangential_force_n", "ContactEvent") for value in self.tangential_force_n)
        if len(tangent) != 3:
            fail("CONTACT-INVALID", "tangential_force_n must be a 3-vector.", operation="ContactEvent")
        object.__setattr__(self, "tangential_force_n", tangent)
        normal = tuple(_finite(value, "normal", "ContactEvent") for value in self.normal)
        point = tuple(_finite(value, "contact_point_m", "ContactEvent") for value in self.contact_point_m)
        if len(normal) != 3 or len(point) != 3:
            fail("CONTACT-INVALID", "normal and contact_point_m must be 3-vectors.", operation="ContactEvent")
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "contact_point_m", point)

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


def solve_contact_dynamics(*, interface: ContactInterface, times_s: Sequence[float], relative_gap_m: Sequence[float], relative_normal_velocity_m_s: Sequence[float], relative_tangential_velocity_m_s: Sequence[Sequence[float]] | None = None) -> ContactDynamicsResult:
    op = "solve_contact_dynamics"
    times = tuple(_finite(value, "time_s", op) for value in times_s)
    gaps = tuple(_finite(value, "relative_gap_m", op) for value in relative_gap_m)
    velocities = tuple(_finite(value, "relative_normal_velocity_m_s", op) for value in relative_normal_velocity_m_s)
    if relative_tangential_velocity_m_s is None:
        tangential_velocities = tuple((0.0, 0.0, 0.0) for _ in times)
    else:
        try:
            tangential_velocities = tuple(
                tuple(_finite(component, "relative_tangential_velocity_m_s", op) for component in value)
                for value in relative_tangential_velocity_m_s
            )
        except TypeError:
            tangential_velocities = ()
    if any(len(value) != 3 for value in tangential_velocities):
        return ContactDynamicsResult(status="validation_failed", issues=(_issue("CONTACT-VELOCITY-INVALID", "Tangential velocities must be 3-vectors.", op),), contact_id=interface.contact_id)
    if len(times) < 2 or len(times) != len(gaps) or len(times) != len(velocities) or len(times) != len(tangential_velocities) or any(b <= a for a, b in zip(times, times[1:])):
        return ContactDynamicsResult(status="validation_failed", issues=(_issue("TIME-INVALID", "Contact times and samples must be aligned and strictly increasing.", op),), contact_id=interface.contact_id)
    if interface.normal_stiffness_n_m is None:
        return ContactDynamicsResult(status="capability_failed", issues=(_issue("CONTACT-LAW-MISSING", "A finite normal stiffness is required for finite contact-force response.", op, (interface.contact_id,)),), contact_id=interface.contact_id)
    if interface.restitution is not None:
        return ContactDynamicsResult(status="capability_failed", issues=(_issue("CONTACT-IMPACT-LAW-UNSUPPORTED", "The reference time-history solver does not implement instantaneous restitution impulses; provide a calibrated penalty law without restitution.", op, (interface.contact_id,)),), contact_id=interface.contact_id)
    forces = []
    tangent_forces = []
    events = []
    cumulative_impulse = 0.0
    for index, (time_s, gap, velocity, tangent_velocity) in enumerate(zip(times, gaps, velocities, tangential_velocities)):
        penetration = max(0.0, -gap)
        normal_force = max(0.0, interface.normal_stiffness_n_m * penetration - interface.normal_damping_n_s_m * velocity)
        state = "contact" if penetration > 0 else "separated"
        tangent = np.asarray(tangent_velocity, dtype=float) - np.dot(tangent_velocity, interface.normal) * np.asarray(interface.normal, dtype=float)
        tangent_norm = float(np.linalg.norm(tangent))
        tangent_force = tuple(float(value) for value in (-interface.friction_coefficient * normal_force * tangent / tangent_norm)) if tangent_norm > 1e-12 and normal_force > 0 else (0.0, 0.0, 0.0)
        forces.append(normal_force)
        tangent_forces.append(tangent_force)
        if index:
            dt = times[index] - times[index - 1]
            cumulative_impulse += 0.5 * (forces[index - 1] + normal_force) * dt
        events.append(ContactEvent(time_s=time_s, contact_id=interface.contact_id, state=state, normal_force_n=normal_force, tangential_force_n=tangent_force, penetration_m=penetration, normal=interface.normal, contact_point_m=interface.contact_point_m, normal_impulse_ns=cumulative_impulse))
    integral = float(np.trapezoid(forces, times) if hasattr(np, "trapezoid") else np.trapz(forces, times))
    tangential_work = float(sum(np.linalg.norm(force) * np.linalg.norm(velocity) for force, velocity in zip(tangent_forces, tangential_velocities)) * (times[-1] - times[0]) / len(times))
    damping_work = float(sum(max(0.0, interface.normal_damping_n_s_m * velocity * velocity) for velocity in velocities) * (times[-1] - times[0]) / len(times))
    return ContactDynamicsResult(status="completed", contact_id=interface.contact_id, events=tuple(events), impulse_ns=integral, momentum_residual_n_s=0.0, energy_dissipation_j=damping_work + tangential_work, evidence={"law": "normal penalty-damper", "friction_law": "coulomb", "friction_coefficient": interface.friction_coefficient, "feacore": False, "convergence": {"time_samples": len(times), "time_step_min_s": min(b - a for a, b in zip(times, times[1:]))}})


def check_contact_convergence(*, results_by_step: Mapping[float, ContactDynamicsResult], relative_tolerance: float = 0.05) -> PhysicsReport:
    """Compare contact impulse and penetration across declared time-step runs."""

    op = "check_contact_convergence"
    if len(results_by_step) < 2:
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("CONVERGENCE-INPUT-INVALID", "At least two time-step results are required.", op),))
    try:
        tolerance = _finite(relative_tolerance, "relative_tolerance", op)
    except Exception:
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("CONVERGENCE-INPUT-INVALID", "relative_tolerance must be finite.", op),))
    if tolerance < 0:
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("CONVERGENCE-INPUT-INVALID", "relative_tolerance cannot be negative.", op),))
    ordered = sorted(((float(step), result) for step, result in results_by_step.items()), key=lambda item: item[0])
    if any(not result.passed for _, result in ordered):
        return PhysicsReport(operation=op, status="indeterminate", issues=(_issue("CONVERGENCE-RESULT-INCOMPLETE", "Every contact run must complete before convergence can be claimed.", op),), evidence={"steps_s": [step for step, _ in ordered]})
    impulses = np.asarray([result.impulse_ns for _, result in ordered], dtype=float)
    penetrations = np.asarray([max((event.penetration_m for event in result.events), default=0.0) for _, result in ordered], dtype=float)
    impulse_scale = max(float(np.max(np.abs(impulses))), 1e-12)
    penetration_scale = max(float(np.max(np.abs(penetrations))), 1e-12)
    impulse_error = float((np.max(impulses) - np.min(impulses)) / impulse_scale)
    penetration_error = float((np.max(penetrations) - np.min(penetrations)) / penetration_scale)
    passed = max(impulse_error, penetration_error) <= tolerance
    return PhysicsReport(
        operation=op,
        status="passed" if passed else "indeterminate",
        issues=() if passed else (_issue("CONVERGENCE-NOT-REACHED", "Contact impulse or penetration changed beyond the declared tolerance.", op, actual=max(impulse_error, penetration_error), expected=tolerance),),
        evidence={"steps_s": [step for step, _ in ordered], "relative_impulse_spread": impulse_error, "relative_penetration_spread": penetration_error, "relative_tolerance": tolerance},
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ControllerSpec:
    """Finite rigid-joint controller limits; no hidden ideal position servo."""

    controller_id: str
    dof_limits: Mapping[str, float]
    velocity_limits: Mapping[str, float] = field(default_factory=dict)
    rate_limits: Mapping[str, float] = field(default_factory=dict)
    gain: float = 1.0
    saturation_enabled: bool = True
    emergency_stop_time_s: float | None = None
    source: str = "declared"

    def __post_init__(self) -> None:
        op = "ControllerSpec"
        if not self.controller_id or not self.source:
            fail("CONTROLLER-INVALID", "controller_id and source are required.", operation=op)
        for field_name in ("dof_limits", "velocity_limits", "rate_limits"):
            values = {str(key): _finite(value, field_name, op) for key, value in getattr(self, field_name).items()}
            if any(value <= 0 for value in values.values()):
                fail("CONTROLLER-INVALID", f"{field_name} must contain positive limits.", operation=op)
            object.__setattr__(self, field_name, values)
        gain = _finite(self.gain, "gain", op)
        if gain < 0:
            fail("CONTROLLER-INVALID", "gain cannot be negative.", operation=op)
        object.__setattr__(self, "gain", gain)
        if self.emergency_stop_time_s is not None:
            stop = _finite(self.emergency_stop_time_s, "emergency_stop_time_s", op)
            if stop < 0:
                fail("CONTROLLER-INVALID", "emergency_stop_time_s cannot be negative.", operation=op)
            object.__setattr__(self, "emergency_stop_time_s", stop)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ActuatorEnvelope:
    """Force/velocity envelope used for post-solve rigid-body acceptance checks."""

    envelope_id: str
    dof_limits: Mapping[str, float]
    velocity_limits: Mapping[str, float] = field(default_factory=dict)
    power_limit_w: float | None = None
    source: str = "declared"

    def __post_init__(self) -> None:
        op = "ActuatorEnvelope"
        if not self.envelope_id or not self.source:
            fail("ENVELOPE-INVALID", "envelope_id and source are required.", operation=op)
        for name in ("dof_limits", "velocity_limits"):
            values = {str(key): _finite(value, name, op) for key, value in getattr(self, name).items()}
            if any(value <= 0 for value in values.values()):
                fail("ENVELOPE-INVALID", f"{name} must contain positive limits.", operation=op)
            object.__setattr__(self, name, values)
        if self.power_limit_w is not None:
            power = _finite(self.power_limit_w, "power_limit_w", op)
            if power <= 0:
                fail("ENVELOPE-INVALID", "power_limit_w must be positive.", operation=op)
            object.__setattr__(self, "power_limit_w", power)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class JointFriction:
    joint_id: str
    coulomb_coefficient: float = 0.0
    viscous_coefficient: float = 0.0
    stiction_force: float = 0.0
    zero_velocity_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        op = "JointFriction"
        if not self.joint_id:
            fail("FRICTION-INVALID", "joint_id is required.", operation=op)
        for name in ("coulomb_coefficient", "viscous_coefficient", "stiction_force"):
            value = _finite(getattr(self, name), name, op)
            if value < 0:
                fail("FRICTION-INVALID", f"{name} cannot be negative.", operation=op)
            object.__setattr__(self, name, value)
        tolerance = _finite(self.zero_velocity_tolerance, "zero_velocity_tolerance", op)
        if tolerance <= 0:
            fail("FRICTION-INVALID", "zero_velocity_tolerance must be positive.", operation=op)
        object.__setattr__(self, "zero_velocity_tolerance", tolerance)


@dataclass(frozen=True, slots=True, kw_only=True)
class BrakePolicy:
    policy_id: str
    trigger_time_s: float
    braking_limits: Mapping[str, float]
    delay_s: float = 0.0
    hold_after_stop: bool = True

    def __post_init__(self) -> None:
        op = "BrakePolicy"
        if not self.policy_id:
            fail("BRAKE-INVALID", "policy_id is required.", operation=op)
        trigger = _finite(self.trigger_time_s, "trigger_time_s", op)
        delay = _finite(self.delay_s, "delay_s", op)
        if trigger < 0 or delay < 0:
            fail("BRAKE-INVALID", "trigger_time_s and delay_s cannot be negative.", operation=op)
        object.__setattr__(self, "trigger_time_s", trigger)
        object.__setattr__(self, "delay_s", delay)
        limits = {str(key): _finite(value, "braking_limit", op) for key, value in self.braking_limits.items()}
        if not limits or any(value <= 0 for value in limits.values()):
            fail("BRAKE-INVALID", "braking_limits must contain positive values.", operation=op)
        object.__setattr__(self, "braking_limits", limits)


def check_actuator_limits(*, result: MultibodyResult, envelope: ActuatorEnvelope) -> PhysicsReport:
    op = "check_actuator_limits"
    if not isinstance(result, MultibodyResult) or not isinstance(envelope, ActuatorEnvelope):
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("INPUT-INVALID", "A MultibodyResult and ActuatorEnvelope are required.", op),))
    force_peaks: dict[str, float] = {}
    velocity_peaks: dict[str, float] = {}
    violations: list[str] = []
    for sample in result.samples:
        for dof, value in sample.generalized_forces.items():
            force_peaks[dof] = max(force_peaks.get(dof, 0.0), abs(value))
            limit = envelope.dof_limits.get(dof)
            if limit is not None and abs(value) > limit:
                violations.append(f"force:{dof}")
        for dof, value in sample.velocities.items():
            velocity_peaks[dof] = max(velocity_peaks.get(dof, 0.0), abs(value))
            limit = envelope.velocity_limits.get(dof)
            if limit is not None and abs(value) > limit:
                violations.append(f"velocity:{dof}")
    return PhysicsReport(
        operation=op,
        status="failed" if violations else "passed",
        issues=() if not violations else (_issue("ACTUATOR-LIMIT-EXCEEDED", "Rigid-body drive limits were exceeded.", op, actual=sorted(set(violations))),),
        model_sha256=result.model_sha256,
        evidence={"force_peak": force_peaks, "velocity_peak": velocity_peaks, "violations": sorted(set(violations)), "envelope_id": envelope.envelope_id},
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class WrenchSample:
    time_s: float
    force_n: tuple[float, float, float]
    moment_nm: tuple[float, float, float]
    point_m: tuple[float, float, float]
    frame_id: str = "world"
    source: str = "declared"

    def __post_init__(self) -> None:
        op = "WrenchSample"
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s", op))
        for name in ("force_n", "moment_nm", "point_m"):
            vector = tuple(_finite(value, name, op) for value in getattr(self, name))
            if len(vector) != 3:
                fail("WRENCH-INVALID", f"{name} must be a 3-vector.", operation=op)
            object.__setattr__(self, name, vector)
        if not self.frame_id or not self.source:
            fail("WRENCH-INVALID", "frame_id and source are required.", operation=op)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class WrenchProfile:
    profile_id: str
    samples: tuple[WrenchSample, ...]
    interpolation: str = "linear"
    source: str = "declared"

    def __post_init__(self) -> None:
        if not self.profile_id or self.interpolation not in ("linear", "zoh") or not self.source:
            fail("WRENCH-PROFILE-INVALID", "profile_id, supported interpolation and source are required.", operation="WrenchProfile")
        samples = tuple(self.samples)
        if any(not isinstance(sample, WrenchSample) for sample in samples):
            fail("WRENCH-PROFILE-INVALID", "samples must contain WrenchSample values.", operation="WrenchProfile")
        if any(b.time_s <= a.time_s for a, b in zip(samples, samples[1:])):
            fail("WRENCH-PROFILE-INVALID", "Wrench samples must be strictly time ordered.", operation="WrenchProfile")
        object.__setattr__(self, "samples", samples)

    def to_dict(self) -> dict[str, Any]:
        return plain(self)

    def at(self, time_s: float) -> WrenchSample:
        """Return a deterministic interpolated wrench sample at ``time_s``."""
        time = _finite(time_s, "time_s", "WrenchProfile")
        if not self.samples:
            fail("WRENCH-PROFILE-INVALID", "Cannot sample an empty wrench profile.", operation="WrenchProfile")
        if time <= self.samples[0].time_s:
            return self.samples[0]
        if time >= self.samples[-1].time_s:
            return self.samples[-1]
        for left, right in zip(self.samples, self.samples[1:]):
            if left.time_s <= time <= right.time_s:
                if self.interpolation == "zoh":
                    return left
                weight = (time - left.time_s) / (right.time_s - left.time_s)
                blend = lambda a, b: a + weight * (b - a)
                return WrenchSample(
                    time_s=time,
                    force_n=tuple(blend(a, b) for a, b in zip(left.force_n, right.force_n)),
                    moment_nm=tuple(blend(a, b) for a, b in zip(left.moment_nm, right.moment_nm)),
                    point_m=tuple(blend(a, b) for a, b in zip(left.point_m, right.point_m)),
                    frame_id=left.frame_id,
                    source=f"{self.source}:interpolated",
                )
        return self.samples[-1]


@dataclass(frozen=True, slots=True, kw_only=True)
class RandomExcitation:
    excitation_id: str
    seed: int
    sample_rate_hz: float
    bandwidth_hz: float
    samples: tuple[float, ...]
    algorithm: str = "declared-samples"
    source: str = "declared"

    def __post_init__(self) -> None:
        op = "RandomExcitation"
        if not self.excitation_id or not self.algorithm or not self.source:
            fail("EXCITATION-INVALID", "excitation_id, algorithm and source are required.", operation=op)
        sample_rate = _finite(self.sample_rate_hz, "sample_rate_hz", op)
        bandwidth = _finite(self.bandwidth_hz, "bandwidth_hz", op)
        if sample_rate <= 0 or bandwidth <= 0 or bandwidth > sample_rate / 2:
            fail("EXCITATION-INVALID", "sample rate and bandwidth must be positive and obey Nyquist.", operation=op)
        object.__setattr__(self, "sample_rate_hz", sample_rate)
        object.__setattr__(self, "bandwidth_hz", bandwidth)
        object.__setattr__(self, "samples", tuple(_finite(value, "sample", op) for value in self.samples))

    @classmethod
    def generate(cls, *, excitation_id: str, seed: int, duration_s: float, sample_rate_hz: float, bandwidth_hz: float, scale: float = 1.0) -> "RandomExcitation":
        op = "RandomExcitation.generate"
        duration = _finite(duration_s, "duration_s", op)
        scale_value = _finite(scale, "scale", op)
        if duration <= 0 or scale_value < 0:
            fail("EXCITATION-INVALID", "duration_s must be positive and scale cannot be negative.", operation=op)
        count = max(1, int(math.floor(duration * sample_rate_hz)) + 1)
        rng = np.random.default_rng(int(seed))
        samples = tuple(float(value) for value in rng.normal(0.0, scale_value, count))
        return cls(excitation_id=excitation_id, seed=int(seed), sample_rate_hz=sample_rate_hz, bandwidth_hz=bandwidth_hz, samples=samples, algorithm="numpy.default_rng.normal/1", source="generated")


@dataclass(frozen=True, slots=True, kw_only=True)
class DutyCycle:
    duty_id: str
    case_ids: tuple[str, ...]
    repetitions: tuple[int, ...] = ()
    source: str = "declared"

    def __post_init__(self) -> None:
        if not self.duty_id or not self.case_ids or not self.source:
            fail("DUTY-INVALID", "duty_id, case_ids and source are required.", operation="DutyCycle")
        reps = tuple(self.repetitions) if self.repetitions else (1,) * len(self.case_ids)
        if len(reps) != len(self.case_ids) or any(not isinstance(value, int) or value <= 0 for value in reps):
            fail("DUTY-INVALID", "repetitions must be positive integers aligned with case_ids.", operation="DutyCycle")
        object.__setattr__(self, "case_ids", tuple(str(value) for value in self.case_ids))
        object.__setattr__(self, "repetitions", reps)


def summarize_drive_duty(*, history: "DynamicsLoadHistory") -> PhysicsReport:
    op = "summarize_drive_duty"
    if not isinstance(history, DynamicsLoadHistory):
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("HISTORY-INVALID", "A DynamicsLoadHistory is required.", op),))
    force_samples = [record.get("generalized_forces", {}) for record in history.records]
    keys = sorted({str(key) for sample in force_samples for key in sample})
    duration = history.times_s[-1] - history.times_s[0] if len(history.times_s) > 1 else 0.0
    peaks = {key: max((abs(float(sample.get(key, 0.0))) for sample in force_samples), default=0.0) for key in keys}
    rms = {}
    for key in keys:
        values = [float(sample.get(key, 0.0)) for sample in force_samples]
        rms[key] = float(math.sqrt(sum(value * value for value in values) / max(1, len(values))))
    return PhysicsReport(operation=op, status="passed" if history.status in ("completed", "completed_with_warnings") else "indeterminate", issues=history.issues, model_sha256=history.model_sha256, evidence={"duration_s": duration, "force_peak": peaks, "force_rms": rms, "sample_count": len(history.times_s), "rms_weighting": "uniform-output-samples"})


def summarize_energy(*, history: "DynamicsLoadHistory") -> PhysicsReport:
    op = "summarize_energy"
    if not isinstance(history, DynamicsLoadHistory):
        return PhysicsReport(operation=op, status="validation_failed", issues=(_issue("HISTORY-INVALID", "A DynamicsLoadHistory is required.", op),))
    work = 0.0
    for index in range(1, len(history.times_s)):
        previous, current = history.records[index - 1], history.records[index]
        dt = history.times_s[index] - history.times_s[index - 1]
        p0 = sum(float(value) * float(previous.get("velocities", {}).get(key, 0.0)) for key, value in previous.get("generalized_forces", {}).items())
        p1 = sum(float(value) * float(current.get("velocities", {}).get(key, 0.0)) for key, value in current.get("generalized_forces", {}).items())
        work += 0.5 * (p0 + p1) * dt
    return PhysicsReport(operation=op, status="passed" if history.status in ("completed", "completed_with_warnings") else "indeterminate", issues=history.issues, model_sha256=history.model_sha256, evidence={"work_j": work, "integration": "trapezoidal-power", "sample_count": len(history.times_s)})


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
    source_operations: tuple[str, ...] = ()
    units: Mapping[str, str] = field(default_factory=lambda: {"time": "s", "force": "N", "moment": "N*m", "position": "m", "velocity": "SI"})

    @property
    def passed(self) -> bool:
        return self.status in ("completed", "completed_with_warnings") and not any(item.severity == "error" for item in self.issues)

    def __post_init__(self) -> None:
        if self.schema_version != "kincheck.dynamics-history/1.0" or not self.history_id:
            fail("HISTORY-INVALID", "history_id and supported schema_version are required.", operation="DynamicsLoadHistory")
        if self.status not in ("completed", "completed_with_warnings", "failed", "indeterminate", "validation_failed", "capability_failed"):
            fail("HISTORY-INVALID", "Unsupported dynamics history status.", operation="DynamicsLoadHistory")
        times = tuple(_finite(value, "time_s", "DynamicsLoadHistory") for value in self.times_s)
        if any(b <= a for a, b in zip(times, times[1:])) or len(times) != len(self.records):
            fail("HISTORY-INVALID", "times_s and records must be aligned and strictly ordered.", operation="DynamicsLoadHistory")
        object.__setattr__(self, "times_s", times)
        object.__setattr__(self, "records", tuple(dict(record) for record in self.records))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "source_operations", tuple(str(item) for item in self.source_operations))
        object.__setattr__(self, "units", {str(key): str(value) for key, value in self.units.items()})
        records_digest = digest({"times_s": times, "records": tuple(self.records)})
        evidence = dict(self.evidence)
        if evidence.get("records_sha256") not in (None, records_digest):
            fail("HISTORY-INTEGRITY", "Dynamics history records differ from their archived digest.", operation="DynamicsLoadHistory")
        evidence["records_sha256"] = records_digest
        object.__setattr__(self, "evidence", evidence)

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "issues": [item.to_dict() for item in self.issues], "passed": self.passed}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DynamicsLoadHistory":
        return cls(schema_version=value.get("schema_version", ""), history_id=value.get("history_id", ""), model_sha256=value.get("model_sha256"), scenario_id=value.get("scenario_id", ""), times_s=tuple(value.get("times_s", ())), records=tuple(value.get("records", ())), status=value.get("status", "failed"), issues=_parse_issues(value), evidence=value.get("evidence", {}), source_operations=tuple(value.get("source_operations", ())), units=value.get("units", {"time": "s", "force": "N", "moment": "N*m", "position": "m", "velocity": "SI"}))


def history_from_multibody_result(*, result: MultibodyResult, history_id: str = "dynamics-history") -> DynamicsLoadHistory:
    events_by_time: dict[float, list[dict[str, Any]]] = {}
    for event in result.contact_events:
        events_by_time.setdefault(float(event.time_s), []).append(event.to_dict() if hasattr(event, "to_dict") else dict(event))
    records = tuple({"positions": sample.positions, "velocities": sample.velocities, "accelerations": sample.accelerations, "generalized_forces": sample.generalized_forces, "constraint_reactions": sample.constraint_reactions, "contact_events": events_by_time.get(float(sample.time_s), []), "source": "solve_multibody_dynamics"} for sample in result.samples)
    return DynamicsLoadHistory(history_id=history_id, model_sha256=result.model_sha256, scenario_id=result.scenario_id, times_s=tuple(sample.time_s for sample in result.samples), records=records, status=result.status, issues=result.issues, source_operations=(result.operation,), evidence={"result_operation": result.operation, "record_scope": "multibody_state_reactions_and_contact_events", "source_map": result.evidence.get("source_map", {})})


def record_dynamics_history(*, result: MultibodyResult | ContactDynamicsResult, history_id: str = "dynamics-history") -> DynamicsLoadHistory:
    """Convert a rigid-body result into a portable load/event history."""

    if isinstance(result, MultibodyResult):
        return history_from_multibody_result(result=result, history_id=history_id)
    if isinstance(result, ContactDynamicsResult):
        records = tuple({"contact_id": event.contact_id, "state": event.state, "normal_force_n": event.normal_force_n, "tangential_force_n": event.tangential_force_n, "penetration_m": event.penetration_m, "normal_impulse_ns": event.normal_impulse_ns, "source": result.operation} for event in result.events)
        return DynamicsLoadHistory(history_id=history_id, model_sha256=getattr(result, "model_sha256", None), scenario_id=result.contact_id, times_s=tuple(event.time_s for event in result.events), records=records, status=result.status, issues=result.issues, source_operations=(result.operation,), evidence={"record_scope": "contact_event_history", "contact_id": result.contact_id})
    raise TypeError("result must be MultibodyResult or ContactDynamicsResult")


def export_load_history(*, history: DynamicsLoadHistory, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(json.dumps(history.to_dict(), sort_keys=True, indent=2, allow_nan=False), encoding="utf-8")
    return output


def read_load_history(*, path: str | Path) -> DynamicsLoadHistory:
    return DynamicsLoadHistory.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


__all__ = [
    "GeneralizedJointState", "ConstraintSpec", "ReactionRequest", "RigidDynamicsScenario",
    "MultibodySample", "MultibodyResult", "DynamicsScenarioCase", "DynamicsScenarioMatrix",
    "DynamicsScenarioSuite", "probe_multibody_capabilities", "solve_multibody_dynamics",
    "run_dynamics_cases", "ContactInterface", "ContactEvent", "ContactDynamicsResult",
    "solve_contact_dynamics", "check_contact_convergence", "ControllerSpec", "ActuatorEnvelope",
    "JointFriction", "BrakePolicy", "check_actuator_limits", "WrenchSample", "WrenchProfile",
    "RandomExcitation", "DutyCycle", "DynamicsLoadHistory", "history_from_multibody_result",
    "record_dynamics_history", "summarize_drive_duty", "summarize_energy", "export_load_history",
    "read_load_history",
]
