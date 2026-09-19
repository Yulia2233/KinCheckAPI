"""Deterministic, bounded numerical IK over KinCheckAPI scalar tree coordinates.

Initial positions are seeds, never locked coordinates. Candidate solutions are
independently checked against the target, authored constraints and joint limits.
A finite multistart search does not enumerate or disprove all possible solutions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import math
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from .assembly import (
    AssemblyModel, JointType, _freeze_mapping, build_kinematic_tree,
    validate_assembly, validate_topology,
)
from .diagnostics import AgentReadableResult, DiagnosticReport, Evidence, SimIssue, _json_value
from .kinematics_geometry import (
    PoseTarget, PositionSolveOptions, _constraint_vector, _residual_records,
    _residual_tolerances, _residuals_within_tolerance, _target_pose,
    _transmission_issues, _qmul, _qconj,
)
from .pose import Pose, orientation_error_rad
from .result import ConstraintResidual


def _number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, str, bytes)):
        raise TypeError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class IKOptions:
    """Controls for numerical IK; every search and convergence limit is recorded.

task_mode='position' leaves orientation unconstrained but still reports its error.
Joint limits always gate acceptance. enforce_joint_limits controls projection
during iteration only; disabling projection never accepts an out-of-range answer.
"""

    position_tolerance_m: float = 1e-6
    orientation_tolerance_rad: float = 1e-6
    max_iterations: int = 100
    damping: float = 1e-4
    step_tolerance: float = 1e-9
    residual_tolerance: float = 1e-9
    multi_start_count: int = 1
    random_seed: int = 0
    enforce_joint_limits: bool = True
    singular_value_tolerance: float = 1e-8
    finite_difference_step: float = 1e-7
    max_step_rad: float = 0.5
    max_step_m: float = 0.05
    solution_tolerance_rad: float = 1e-5
    solution_tolerance_m: float = 1e-7
    task_mode: Literal["pose", "position"] = "pose"

    def __post_init__(self) -> None:
        for name in ("max_iterations", "multi_start_count", "random_seed"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < (0 if name == "random_seed" else 1):
                raise ValueError(f"{name} must be an integer >= {0 if name == 'random_seed' else 1}")
        for name in (
            "position_tolerance_m", "orientation_tolerance_rad", "damping",
            "step_tolerance", "residual_tolerance", "singular_value_tolerance",
            "finite_difference_step", "max_step_rad", "max_step_m",
            "solution_tolerance_rad", "solution_tolerance_m",
        ):
            object.__setattr__(self, name, _number(getattr(self, name), name, positive=True))
        if self.singular_value_tolerance >= 1:
            raise ValueError("singular_value_tolerance must be less than one (relative SVD cutoff)")
        if not isinstance(self.enforce_joint_limits, bool):
            raise TypeError("enforce_joint_limits must be boolean")
        if self.task_mode not in {"pose", "position"}:
            raise ValueError("task_mode must be pose or position")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class IKSolution(AgentReadableResult):
    """One evaluated seed, including the last state of an unsuccessful search."""

    joint_positions: Mapping[str, float]
    initial_joint_positions: Mapping[str, float]
    position_error_m: float
    orientation_error_rad: float
    residual_norm: float
    iterations: int
    seed_index: int
    status: Literal["converged", "limit_hit", "singular", "stalled", "iteration_limit"]
    within_limits: bool
    jacobian_rank: int
    reference_rank: int
    singular_values: tuple[float, ...] = ()
    residuals: tuple[ConstraintResidual, ...] = ()
    issues: tuple[SimIssue, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"converged", "limit_hit", "singular", "stalled", "iteration_limit"}:
            raise ValueError("invalid IK candidate status")
        for name in ("position_error_m", "orientation_error_rad", "residual_norm"):
            number = _number(getattr(self, name), name)
            if number < 0:
                raise ValueError(f"{name} cannot be negative")
            object.__setattr__(self, name, number)
        for name in ("joint_positions", "initial_joint_positions"):
            object.__setattr__(self, name, _freeze_mapping({
                key: _number(value, key) for key, value in sorted(getattr(self, name).items())
            }))
        if not isinstance(self.within_limits, bool):
            raise TypeError("within_limits must be boolean")
        for name in ("iterations", "seed_index", "jacobian_rank", "reference_rank"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        values = tuple(_number(v, "singular_values") for v in self.singular_values)
        if any(v < 0 for v in values):
            raise ValueError("singular values cannot be negative")
        object.__setattr__(self, "singular_values", values)
        object.__setattr__(self, "residuals", tuple(self.residuals))
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.status == "converged" and (not self.within_limits or any(i.severity == "error" for i in self.issues)):
            raise ValueError("a converged IK solution must satisfy limits and have no error issues")

    @property
    def operation(self) -> str:
        return "solve_inverse_kinematics"

    @property
    def passed(self) -> bool:
        return self.status == "converged" and self.within_limits and not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(), "operation": self.operation,
            "status": self.status, "passed": self.passed,
            "joint_positions": dict(self.joint_positions),
            "initial_joint_positions": dict(self.initial_joint_positions),
            "position_error_m": self.position_error_m, "orientation_error_rad": self.orientation_error_rad,
            "residual_norm": self.residual_norm, "iterations": self.iterations,
            "seed_index": self.seed_index, "within_limits": self.within_limits,
            "jacobian_rank": self.jacobian_rank, "reference_rank": self.reference_rank,
            "singular_values": list(self.singular_values),
            "residuals": [r.to_dict() for r in self.residuals],
            "issues": [i.to_dict() for i in self.issues],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> IKSolution:
        data = {name: value[name] for name in cls.__dataclass_fields__}
        data["residuals"] = tuple(ConstraintResidual(**r) for r in data["residuals"])
        data["issues"] = tuple(_read_issue(i) for i in data["issues"])
        return cls(**data)


def _read_issue(value: Mapping[str, Any]) -> SimIssue:
    return SimIssue(**{**value, "evidence": tuple(Evidence(**e) for e in value.get("evidence", ()))})


@dataclass(frozen=True, slots=True, kw_only=True)
class IKSolutionSet(AgentReadableResult):
    """Verified distinct solutions and all attempts; no claim of exhaustive search."""

    status: Literal["solved", "unreachable", "nonconverged", "singular", "invalid", "capability_failed"]
    target: PoseTarget | None = None
    options: IKOptions | None = None
    solutions: tuple[IKSolution, ...] = ()
    selected_solution: IKSolution | None = None
    attempts: tuple[IKSolution, ...] = ()
    issues: tuple[SimIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {"solved", "unreachable", "nonconverged", "singular", "invalid", "capability_failed"}:
            raise ValueError("invalid IK result status")
        for name in ("solutions", "attempts", "issues"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        if any(not s.passed for s in self.solutions):
            raise ValueError("solutions can contain only converged, verified candidates")
        if self.status == "solved":
            if not self.solutions or self.selected_solution not in self.solutions or any(i.severity == "error" for i in self.issues):
                raise ValueError("a solved IK result requires an accepted selected solution")
        elif self.solutions or self.selected_solution is not None:
            raise ValueError("an unsolved IK result cannot expose accepted solutions")

    @property
    def operation(self) -> str:
        return "solve_inverse_kinematics"

    @property
    def passed(self) -> bool:
        return self.status == "solved" and self.selected_solution is not None

    @property
    def report(self) -> DiagnosticReport:
        status = "passed" if self.passed else "validation_failed" if self.status == "invalid" else "capability_failed" if self.status == "capability_failed" else "failed"
        return DiagnosticReport(operation=self.operation, status=status, issues=self.issues, metadata=self.metadata)

    @property
    def diagnostics(self) -> DiagnosticReport:
        return self.report

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(), "schema_version": "kincheck.ik/1.0",
            "operation": self.operation, "status": self.status, "passed": self.passed,
            "target": self.target.to_dict() if self.target else None,
            "options": self.options.to_dict() if self.options else None,
            "solutions": [s.to_dict() for s in self.solutions],
            "selected_solution": self.selected_solution.to_dict() if self.selected_solution else None,
            "attempts": [s.to_dict() for s in self.attempts],
            "issues": [i.to_dict() for i in self.issues],
            "diagnostics": self.report.to_dict(), "metadata": _json_value(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> IKSolutionSet:
        if value.get("schema_version") != "kincheck.ik/1.0":
            raise ValueError("unsupported IK schema_version")
        return cls(
            status=value["status"], target=_target(value["target"]) if value.get("target") else None,
            options=IKOptions(**value["options"]) if value.get("options") else None,
            solutions=tuple(IKSolution.from_dict(s) for s in value["solutions"]),
            selected_solution=IKSolution.from_dict(value["selected_solution"]) if value.get("selected_solution") else None,
            attempts=tuple(IKSolution.from_dict(s) for s in value["attempts"]),
            issues=tuple(_read_issue(i) for i in value["issues"]), metadata=value["metadata"],
        )


def _target(value: Any) -> PoseTarget:
    if isinstance(value, Mapping):
        data = dict(value)
        if isinstance(data.get("pose"), Mapping):
            data["pose"] = Pose(**data["pose"])
        value = PoseTarget(**data)
    if not isinstance(value, PoseTarget) or not isinstance(value.pose, Pose):
        raise TypeError("target must be a PoseTarget or its mapping, with an explicit Pose")
    if not isinstance(value.component_id, str) or not value.component_id.strip():
        raise ValueError("target component_id must be a non-empty string")
    if value.connector_id is not None and (not isinstance(value.connector_id, str) or not value.connector_id.strip()):
        raise ValueError("target connector_id must be a non-empty string or None")
    for name in ("position_tolerance_m", "orientation_tolerance_rad"):
        if getattr(value, name) is not None:
            _number(getattr(value, name), name, positive=True)
    return value


def _issue(code: str, message: str, ids: Sequence[str], *, evidence: Sequence[Evidence] = (), action: str = "Inspect the evidence and revise the target, seed, or IK options.") -> SimIssue:
    return SimIssue(code=code, severity="error", stage="kinematics.ik", message=message,
                    object_ids=tuple(ids), evidence=tuple(evidence), suggested_actions=(action,))


class _IKInputError(ValueError):
    def __init__(self, issue: SimIssue, status: str = "invalid") -> None:
        self.issue, self.status = issue, status
        super().__init__(issue.message)


def _reject(code: str, message: str, ids: Sequence[str], *, status: str = "invalid", evidence: Sequence[Evidence] = ()) -> None:
    raise _IKInputError(_issue(code, message, ids, evidence=evidence), status)


def _rotation_error(actual: Pose, expected: Pose, reference: np.ndarray | None = None) -> np.ndarray:
    q = np.asarray(_qmul(expected.orientation_xyzw, _qconj(actual.orientation_xyzw)))
    if q[3] < 0:
        q = -q
    norm = float(np.linalg.norm(q[:3]))
    vector = q[:3] * (2 * math.atan2(norm, q[3]) / norm) if norm > 1e-15 else 2 * q[:3]
    # Keep numerical derivatives on the same logarithm branch at a half turn.
    angle = float(np.linalg.norm(vector))
    if reference is not None and angle > math.pi - 1e-3 and np.dot(vector, reference) < 0:
        vector *= 1 - 2 * math.pi / angle
    return vector


class _Problem:
    def __init__(self, assembly: AssemblyModel, target: PoseTarget, options: IKOptions,
                 ids: tuple[str, ...], bounds: Mapping[str, tuple[float, float] | None]) -> None:
        self.assembly, self.target, self.options, self.ids, self.bounds = assembly, target, options, ids, bounds
        self.kinds = {j.joint_id: j.joint_type for j in assembly.joints}
        self.free = tuple(i for i in ids if bounds[i] is None or bounds[i][0] < bounds[i][1])
        self.scales = np.asarray([options.max_step_rad if self.kinds[i] == JointType.REVOLUTE else options.max_step_m for i in self.free])
        self.position_tolerance = target.position_tolerance_m or options.position_tolerance_m
        self.orientation_tolerance = target.orientation_tolerance_rad or options.orientation_tolerance_rad
        self.solve_options = PositionSolveOptions(position_tolerance_m=options.position_tolerance_m, orientation_tolerance_rad=options.orientation_tolerance_rad)

    def evaluate(self, state: Mapping[str, float], orientation_reference: np.ndarray | None = None):
        vector, row_ids, norms = _constraint_vector(self.assembly, state)
        scales: list[float] = []
        for residual_id in dict.fromkeys(row_ids):
            pt, ot, _ = _residual_tolerances(assembly=self.assembly, pose_targets=(), options=self.solve_options, residual_id=residual_id)
            scales.extend([pt] * 3 + [ot] * 3 if row_ids.count(residual_id) == 6 else [pt])
        actual = _target_pose(self.assembly, self.target.component_id, self.target.connector_id, state)
        position = np.asarray(self.target.pose.position_m) - np.asarray(actual.position_m)
        rotation = _rotation_error(actual, self.target.pose, orientation_reference)
        task = position if self.options.task_mode == "position" else np.concatenate((position, rotation))
        weights = [self.position_tolerance] * 3 + ([] if self.options.task_mode == "position" else [self.orientation_tolerance] * 3)
        vector = np.concatenate((vector, task)) / np.asarray([*scales, *weights])
        if not np.all(np.isfinite(vector)):
            raise ValueError("IK residual contains non-finite values")
        pe, oe = float(np.linalg.norm(position)), orientation_error_rad(actual=actual, expected=self.target.pose)
        within = all(b is None or b[0] <= state[i] <= b[1] for i, b in self.bounds.items())
        constraints_ok = _residuals_within_tolerance(assembly=self.assembly, pose_targets=(), options=self.solve_options, norms=norms)
        satisfied = pe <= self.position_tolerance and (self.options.task_mode == "position" or oe <= self.orientation_tolerance) and constraints_ok and within
        return vector, rotation, pe, oe, within, satisfied, _residual_records(norms)

    def jacobian(self, state: Mapping[str, float]) -> np.ndarray:
        base, rotation, *_ = self.evaluate(state)
        matrix = np.zeros((len(base), len(self.free)))
        for col, jid in enumerate(self.free):
            h = self.options.finite_difference_step * self.scales[col]
            plus, minus = dict(state), dict(state)
            plus[jid] += h
            minus[jid] -= h
            matrix[:, col] = (self.evaluate(plus, rotation)[0] - self.evaluate(minus, rotation)[0]) / (2 * h) * self.scales[col]
        return matrix

    def svd(self, matrix: np.ndarray):
        u, s, vt = np.linalg.svd(matrix, full_matrices=False)
        cutoff = self.options.singular_value_tolerance * max(float(s[0]) if s.size else 0, 1.0)
        return u, s, vt, int(np.sum(s > cutoff))

    def iterate(self, seed: Mapping[str, float], seed_index: int) -> IKSolution:
        state = dict(seed)
        status = "iteration_limit"
        reference_rank = 0
        for iteration in range(self.options.max_iterations + 1):
            vector, _, _, _, within, satisfied, _ = self.evaluate(state)
            matrix = self.jacobian(state)
            u, singular, vt, rank = self.svd(matrix)
            reference_rank = max(reference_rank, rank)
            if satisfied:
                status = "converged"
                break
            if iteration == self.options.max_iterations:
                break
            if not self.free:
                status = "limit_hit" if self.ids else "stalled"
                break
            if rank == 0:
                status = "singular"
                break
            damping = self.options.damping * max(float(singular[0]), 1.0)
            step = -(vt.T @ ((singular / (singular**2 + damping**2)) * (u.T @ vector)))
            step /= max(1.0, float(np.max(np.abs(step))))
            old_cost = float(np.dot(vector, vector))
            accepted = False
            projected = False
            for backtrack in range(20):
                candidate = dict(state)
                for col, jid in enumerate(self.free):
                    value = state[jid] + float(step[col] * self.scales[col]) * 0.5**backtrack
                    bounds = self.bounds[jid]
                    if self.options.enforce_joint_limits and bounds is not None:
                        clipped = min(bounds[1], max(bounds[0], value))
                        projected |= clipped != value
                        value = clipped
                    candidate[jid] = value
                trial = self.evaluate(candidate)
                cost = float(np.dot(trial[0], trial[0]))
                if trial[5] or cost < old_cost:
                    accepted = True
                    break
            if not accepted:
                status = "limit_hit" if projected or not within else "stalled"
                break
            distance = max(abs(candidate[j] - state[j]) / self.scales[col] for col, j in enumerate(self.free))
            state = candidate
            if not trial[5] and (distance <= self.options.step_tolerance or (old_cost - cost) / max(old_cost, 1.0) <= self.options.residual_tolerance):
                status = "limit_hit" if projected or not trial[4] else "stalled"
                iteration += 1
                break
        vector, _, pe, oe, within, satisfied, residuals = self.evaluate(state)
        _, singular, _, rank = self.svd(self.jacobian(state))
        reference_rank = max(reference_rank, rank)
        if satisfied:
            status = "converged"
        elif not within:
            status = "limit_hit"
        return IKSolution(joint_positions=state, initial_joint_positions=seed,
                          position_error_m=pe, orientation_error_rad=oe,
                          residual_norm=float(np.linalg.norm(vector)), iterations=iteration,
                          seed_index=seed_index, status=status, within_limits=within,
                          jacobian_rank=rank, reference_rank=reference_rank,
                          singular_values=tuple(float(s) for s in singular), residuals=residuals)


def _prepare(assembly: AssemblyModel, target: PoseTarget, initial: Any, limits: Any, options: IKOptions):
    if not isinstance(assembly, AssemblyModel):
        _reject("KINCHECK-KIN-IK-ASSEMBLY-INVALID", "assembly must be an AssemblyModel.", ())
    validation = (*validate_assembly(assembly=assembly).issues, *validate_topology(assembly=assembly).issues)
    errors = tuple(i for i in validation if i.severity == "error")
    if errors:
        raise _IKInputError(errors[0])
    joints = {j.joint_id: j for j in assembly.joints}
    unsupported = tuple(j.joint_id for j in assembly.joints if j.joint_type not in {JointType.FIXED, JointType.REVOLUTE, JointType.PRISMATIC})
    if unsupported:
        _reject("KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED", "IK supports fixed, revolute and prismatic joints.", unsupported, status="capability_failed", evidence=(Evidence(key="missing_capability", actual="multi_coordinate_ik"),))
    tree = build_kinematic_tree(assembly=assembly)
    ids = tuple(sorted(e.joint_id for e in tree.tree_edges if e.joint_type in {JointType.REVOLUTE, JointType.PRISMATIC}))
    for j in assembly.joints:
        if j.joint_id not in ids and j.joint_type != JointType.FIXED and j.limit is not None:
            _reject("KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED", "A limit on a closure coordinate cannot be ignored by IK.", (j.joint_id,), status="capability_failed", evidence=(Evidence(key="missing_capability", actual="closure_joint_limit_ik"),))
    unsupported_constraints = tuple(c.constraint_id for c in assembly.constraints if c.constraint_type not in {"gear", "belt", "rack_pinion"})
    if unsupported_constraints:
        _reject("KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED", "IK cannot evaluate these standalone constraint types.", unsupported_constraints, status="capability_failed", evidence=(Evidence(key="missing_capability", actual="ik_constraint_evaluation"),))
    for coupling in assembly.couplings:
        if coupling.joint_a_id not in ids or coupling.joint_b_id not in ids:
            _reject("KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED", "Coupling must reference scalar tree coordinates.", (coupling.coupling_id,), status="capability_failed", evidence=(Evidence(key="missing_capability", actual="closure_coordinate_coupling_ik"),))
    transmission_issues = _transmission_issues(assembly, tree, stage="kinematics.ik")
    if transmission_issues:
        raise _IKInputError(transmission_issues[0])
    if assembly.get_component(component_id=target.component_id) is None or (target.connector_id is not None and assembly.get_connector(component_id=target.component_id, connector_id=target.connector_id) is None):
        _reject("KINCHECK-KIN-TARGET-INVALID", "IK target does not reference an existing component/connector.", tuple(i for i in (target.component_id, target.connector_id) if i))
    if initial is None:
        initial = {}
    if limits is None:
        limits = {}
    if not isinstance(initial, Mapping) or not isinstance(limits, Mapping):
        _reject("KINCHECK-KIN-IK-INPUT-INVALID", "Seeds and joint limits must be mappings keyed by scalar tree joint IDs.", (assembly.assembly_id,))
    for jid in (*initial, *limits):
        if jid not in ids:
            _reject("KINCHECK-KIN-IK-JOINT-INVALID", "IK seeds and limits must name an independent scalar tree joint.", (str(jid),))
    bounds, seed = {}, {}
    for jid in ids:
        authored = joints[jid].limit
        bound = (float(authored.lower), float(authored.upper)) if authored else None
        if jid in limits:
            raw = limits[jid]
            if isinstance(raw, (str, bytes, Mapping)):
                raise TypeError(f"joint_limits[{jid}] must be (lower, upper)")
            supplied = tuple(_number(v, f"joint_limits[{jid}]") for v in raw)
            if len(supplied) != 2 or supplied[0] > supplied[1]:
                _reject("KINCHECK-KIN-IK-LIMIT-INVALID", "Joint limit must be a finite (lower, upper) pair with lower <= upper.", (jid,))
            bound = supplied if bound is None else (max(bound[0], supplied[0]), min(bound[1], supplied[1]))
        if bound and bound[0] > bound[1]:
            _reject("KINCHECK-KIN-IK-LIMIT-INVALID", "Requested and authored joint ranges do not intersect.", (jid,))
        bounds[jid] = bound
        seed[jid] = _number(initial[jid], f"initial_joint_positions[{jid}]") if jid in initial else min(bound[1], max(bound[0], 0.0)) if bound else 0.0
        if bound and not bound[0] <= seed[jid] <= bound[1]:
            _reject("KINCHECK-KIN-IK-SEED-OUT-OF-LIMIT", "Initial guess lies outside the effective joint range.", (jid,), evidence=(Evidence(key="seed", actual=seed[jid], expected=bound),))
    if options.multi_start_count > 1 and any(b is None for b in bounds.values()):
        _reject("KINCHECK-KIN-IK-SEARCH-RANGE-REQUIRED", "Multiple starts require finite search ranges for every independent joint.", tuple(j for j,b in bounds.items() if b is None))
    return _Problem(assembly, target, options, ids, bounds), seed


def solve_inverse_kinematics(
    *, assembly: AssemblyModel, target: PoseTarget | Mapping[str, Any],
    initial_joint_positions: Mapping[str, float] | None = None,
    joint_limits: Mapping[str, Sequence[float]] | None = None,
    solution_selection: Literal["first", "lowest_residual", "closest_to_initial"] = "first",
    options: IKOptions | Mapping[str, Any] | None = None,
) -> IKSolutionSet:
    """Find verified scalar-joint configurations for one world-frame Pose target.

    Multistart is deterministic and finite, not exhaustive. Unsupported trajectory
    drivers and joint/constraint types return capability_failed with evidence.
    Invalid input and numerical failures are structured results, not empty passes.
    """
    normalized_target = None
    normalized_options = None
    target_ids = (str(getattr(target, "component_id", "")),)
    stage_code = "KINCHECK-KIN-IK-OPTIONS-INVALID"
    try:
        normalized_options = IKOptions(**options) if isinstance(options, Mapping) else IKOptions() if options is None else options
        if not isinstance(normalized_options, IKOptions):
            raise TypeError("options must be IKOptions or a mapping of its documented fields")
        if solution_selection not in {"first", "lowest_residual", "closest_to_initial"}:
            raise ValueError("solution_selection must be first, lowest_residual, or closest_to_initial")
        stage_code = "KINCHECK-KIN-TARGET-INVALID"
        from .motion_contracts import PoseTrajectory
        if isinstance(target, PoseTrajectory):
            _reject("KINCHECK-KIN-IK-CAPABILITY-UNSUPPORTED", "IK solves one static target; PoseTrajectory driving is not supported.", (target.target.component_id,), status="capability_failed", evidence=(Evidence(key="missing_capability", actual="trajectory_inverse_kinematics"),))
        normalized_target = _target(target)
        target_ids = tuple(i for i in (normalized_target.component_id, normalized_target.connector_id) if i)
        stage_code = "KINCHECK-KIN-IK-INPUT-INVALID"
        problem, seed = _prepare(assembly, normalized_target, initial_joint_positions, joint_limits, normalized_options)
    except _IKInputError as error:
        return IKSolutionSet(status=error.status, target=normalized_target, options=normalized_options, issues=(error.issue,))
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as error:
        return IKSolutionSet(status="invalid", target=normalized_target,
                             options=normalized_options if isinstance(normalized_options, IKOptions) else None,
                             issues=(_issue(stage_code, str(error), tuple(i for i in target_ids if i), evidence=(Evidence(key="native_error_type", actual=type(error).__name__),)),))

    options = normalized_options
    rng = np.random.default_rng(options.random_seed)
    seeds = [seed]
    seeds.extend({jid: float(rng.uniform(*problem.bounds[jid])) for jid in problem.ids} for _ in range(options.multi_start_count - 1))
    metadata: dict[str, Any] = {
        "assembly_id": assembly.assembly_id, "operation": "solve_inverse_kinematics",
        "solution_selection": solution_selection, "joint_ids": problem.ids,
        "effective_joint_limits": problem.bounds, "initial_joint_positions": seed,
        "search_complete": False, "infeasibility_proven": False,
        "rank_basis": "maximum observed rank at seeds, bounded probes and iterates",
        "residual_norm_units": "dimensionless; residual rows divided by effective tolerances",
    }
    attempts: list[IKSolution] = []
    try:
        # Distinguish structural underactuation from loss of rank at a posture.
        reference_rank = 0
        for state in seeds:
            reference_rank = max(reference_rank, problem.svd(problem.jacobian(state))[3])
        for sign in (-1, 1):
            probe = dict(seed)
            for col, jid in enumerate(problem.free):
                probe[jid] += sign * (0.2 + 0.1 * (col % 3)) * problem.scales[col]
                b = problem.bounds[jid]
                if b:
                    probe[jid] = min(b[1], max(b[0], probe[jid]))
            reference_rank = max(reference_rank, problem.svd(problem.jacobian(probe))[3])
        for index, initial in enumerate(seeds):
            attempt = problem.iterate(initial, index)
            reference_rank = max(reference_rank, attempt.reference_rank)
            attempts.append(attempt)
        finalized = []
        for attempt in attempts:
            status = attempt.status
            if attempt.jacobian_rank < reference_rank and status != "limit_hit":
                status = "singular"
            if status == "converged":
                # Re-evaluate the final state; never trust the optimizer exit alone.
                if not problem.evaluate(attempt.joint_positions)[5]:
                    status = "stalled"
            evidence = (
                Evidence(key="position_error_m", actual=attempt.position_error_m, expected=f"<= {problem.position_tolerance}", unit="m"),
                Evidence(key="orientation_error_rad", actual=attempt.orientation_error_rad, expected=f"<= {problem.orientation_tolerance}" if options.task_mode == "pose" else "unconstrained", unit="rad"),
                Evidence(key="jacobian_rank", actual=attempt.jacobian_rank, expected=reference_rank),
                Evidence(key="iterations", actual=attempt.iterations),
                Evidence(key="within_limits", actual=attempt.within_limits, expected=True),
            )
            codes = {"singular": "KINCHECK-KIN-IK-SINGULAR", "limit_hit": "KINCHECK-KIN-IK-LIMIT-HIT", "stalled": "KINCHECK-KIN-IK-STALLED", "iteration_limit": "KINCHECK-KIN-IK-ITERATION-LIMIT"}
            issues = () if status == "converged" else (_issue(codes[status], f"IK attempt ended with {status}; no verified solution from this seed.", target_ids, evidence=evidence),)
            finalized.append(replace(attempt, status=status, reference_rank=reference_rank, issues=issues))
        attempts = finalized
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, FloatingPointError, np.linalg.LinAlgError) as error:
        return IKSolutionSet(status="nonconverged", target=normalized_target, options=options, attempts=tuple(attempts), metadata=metadata,
                             issues=(_issue("KINCHECK-KIN-IK-NUMERICAL-FAILED", "IK could not evaluate a finite numerical state.", target_ids, evidence=(Evidence(key="native_error_type", actual=type(error).__name__), Evidence(key="native_message", actual=str(error))),),))

    def differences(a: Mapping[str, float], b: Mapping[str, float], *, normalize: bool) -> list[float]:
        values = []
        coupled = {j for c in assembly.couplings for j in (c.joint_a_id, c.joint_b_id)}
        for jid in problem.ids:
            d = abs(a[jid] - b[jid])
            rotational = problem.kinds[jid] == JointType.REVOLUTE
            if rotational and problem.bounds[jid] is None and jid not in coupled:
                d = abs((d + math.pi) % (2 * math.pi) - math.pi)
            scale = (options.solution_tolerance_rad if rotational else options.solution_tolerance_m) if normalize else (options.max_step_rad if rotational else options.max_step_m)
            values.append(d / scale)
        return values

    solutions: list[IKSolution] = []
    for attempt in attempts:
        if attempt.passed and not any(max(differences(attempt.joint_positions, other.joint_positions, normalize=True), default=0) <= 1 for other in solutions):
            solutions.append(attempt)
    selected = None
    if solutions:
        selected = solutions[0] if solution_selection == "first" else min(solutions, key=lambda a: (a.residual_norm, a.seed_index)) if solution_selection == "lowest_residual" else min(solutions, key=lambda a: (sum(d*d for d in differences(a.joint_positions, seed, normalize=False)), a.residual_norm, a.seed_index))
        status, issues = "solved", ()
    else:
        status = "singular" if attempts and all(a.status == "singular" for a in attempts) else "nonconverged"
        # With no free coordinates there is exactly one permitted configuration.
        if not problem.free:
            status = "unreachable"
            metadata["infeasibility_proven"] = True
        code = "KINCHECK-KIN-TARGET-UNREACHABLE" if status == "unreachable" else "KINCHECK-KIN-IK-SINGULAR" if status == "singular" else "KINCHECK-KIN-IK-NOT-CONVERGED"
        best = min(attempts, key=lambda a: a.residual_norm) if attempts else None
        issues = (_issue(code, "No candidate passed IK acceptance. A finite search does not prove global unreachability." if status != "unreachable" else "The only allowed configuration does not satisfy the target.", target_ids,
                         evidence=(Evidence(key="attempt_count", actual=len(attempts)), Evidence(key="best_candidate", actual=best.to_dict() if best else None), Evidence(key="infeasibility_proven", actual=metadata["infeasibility_proven"]))),)
    metadata.update(attempt_count=len(attempts), solution_count=len(solutions), reference_rank=reference_rank)
    return IKSolutionSet(status=status, target=normalized_target, options=options, solutions=tuple(solutions), selected_solution=selected, attempts=tuple(attempts), issues=issues, metadata=metadata)


__all__ = ["IKOptions", "IKSolution", "IKSolutionSet", "solve_inverse_kinematics"]
