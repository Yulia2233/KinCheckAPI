"""Deterministic kinematic analysis built on the position solver.

This module deliberately contains no backend code.  It turns the public
Jacobian and single-position solver into small, inspectable analyses for
singularities, reachability, and workspace sampling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import math
import random
from typing import Any, Mapping, Sequence

from .assembly import AssemblyModel, Pose, build_kinematic_tree
from .diagnostics import AgentReadableResult, Evidence, SimIssue
from .errors import KinCheckError
from .pose import compose_pose


def _pose_dict(value: Pose | None) -> Any:
    if value is None:
        return None
    return {
        "position_m": list(value.position_m),
        "orientation_xyzw": list(value.orientation_xyzw),
    }


def _as_options(value: Any, cls: type[Any]) -> Any:
    if value is None or isinstance(value, cls):
        return value or cls()
    if isinstance(value, Mapping):
        return cls(**dict(value))
    raise TypeError(f"options must be {cls.__name__} or a mapping")


def _finite(value: Any, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _issue(
    *, code: str, message: str, object_ids: Sequence[str] = (),
    severity: str = "error", evidence: Sequence[Evidence] = (),
    failure_time_s: float | None = None,
) -> SimIssue:
    return SimIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        stage="kinematics.analysis",
        message=message,
        object_ids=tuple(object_ids),
        evidence=tuple(evidence),
        suggested_actions=("Inspect the reported state and revise the target or mechanism pose.",),
        failure_time_s=failure_time_s,
    )


def _motion_result_issues(motion_result: Any) -> tuple[SimIssue, ...]:
    status = getattr(motion_result, "status", None)
    if status in {"completed", "completed_with_warnings"}:
        return ()
    if status != "partial":
        return ()
    times = tuple(getattr(motion_result, "sample_times_s", ()))
    return (
        _issue(
            code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE",
            message="A partial MotionResult cannot produce a complete kinematic analysis pass.",
            object_ids=tuple(
                item
                for item in (
                    getattr(motion_result, "scenario_id", None),
                    getattr(motion_result, "assembly_id", None),
                )
                if item
            ),
            evidence=(
                Evidence(key="motion_result_status", actual=status, expected="completed or completed_with_warnings"),
                Evidence(key="sample_count", actual=len(times)),
                Evidence(key="time_range_s", actual=(times[0], times[-1]) if times else None, unit="s"),
            ),
            failure_time_s=times[-1] if times else None,
        ),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SingularityOptions:
    """Thresholds used by :func:`find_singularities`."""

    tolerance: float = 1e-8
    near_tolerance: float = 1e-4
    target_component_id: str | None = None
    target_connector_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.tolerance)
            or not math.isfinite(self.near_tolerance)
            or self.tolerance <= 0.0
            or self.near_tolerance <= 0.0
        ):
            raise ValueError("singularity tolerances must be positive finite numbers")
        if self.tolerance > self.near_tolerance:
            raise ValueError("tolerance must not exceed near_tolerance")


@dataclass(frozen=True, slots=True, kw_only=True)
class SingularitySample:
    time_s: float
    status: str
    rank: int
    minimum_singular_value: float | None
    condition_number: float | None
    singular_values: tuple[float, ...] = ()
    joint_positions: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _finite(self.time_s, "time_s"))
        if self.time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        if self.status not in {"regular", "near_singular", "singular", "unavailable"}:
            raise ValueError("invalid singularity status")
        if self.rank < 0:
            raise ValueError("rank must be non-negative")
        if self.minimum_singular_value is not None:
            minimum = _finite(self.minimum_singular_value, "minimum_singular_value")
            if minimum < 0.0:
                raise ValueError("minimum_singular_value must be non-negative")
            object.__setattr__(self, "minimum_singular_value", minimum)
        if self.condition_number is not None:
            condition = _finite(self.condition_number, "condition_number")
            if condition < 1.0:
                raise ValueError("condition_number must be at least one")
            object.__setattr__(self, "condition_number", condition)
        values = tuple(_finite(item, "singular_values") for item in self.singular_values)
        if any(item < 0.0 for item in values):
            raise ValueError("singular values must be non-negative")
        object.__setattr__(self, "singular_values", values)
        object.__setattr__(self, "joint_positions", dict(sorted(self.joint_positions.items())))

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "status": self.status,
            "rank": self.rank,
            "minimum_singular_value": self.minimum_singular_value,
            "condition_number": self.condition_number,
            "singular_values": list(self.singular_values),
            "joint_positions": dict(self.joint_positions),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ReachabilityOptions:
    position_tolerance_m: float = 1e-6
    orientation_tolerance_rad: float = 1e-6
    initial_joint_positions: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.position_tolerance_m)
            or not math.isfinite(self.orientation_tolerance_rad)
            or self.position_tolerance_m <= 0.0
            or self.orientation_tolerance_rad <= 0.0
        ):
            raise ValueError("reachability tolerances must be positive finite numbers")
        object.__setattr__(
            self, "initial_joint_positions",
            {str(key): _finite(value, "initial_joint_positions") for key, value in self.initial_joint_positions.items()},
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceOptions:
    """Explicit finite ranges for deterministic workspace sampling."""

    joint_ranges: Mapping[str, Sequence[float]] = field(default_factory=dict)
    samples_per_joint: int = 9
    max_samples: int = 4096
    seed: int | None = None
    position_tolerance_m: float = 1e-6
    orientation_tolerance_rad: float = 1e-6
    singularity_tolerance: float = 1e-8
    near_singularity_tolerance: float = 1e-4

    def __post_init__(self) -> None:
        if (
            not isinstance(self.samples_per_joint, int)
            or isinstance(self.samples_per_joint, bool)
            or not isinstance(self.max_samples, int)
            or isinstance(self.max_samples, bool)
            or self.samples_per_joint < 2
            or self.max_samples < 1
        ):
            raise ValueError("workspace sample counts must be positive")
        if (
            not math.isfinite(self.position_tolerance_m)
            or not math.isfinite(self.orientation_tolerance_rad)
            or self.position_tolerance_m <= 0.0
            or self.orientation_tolerance_rad <= 0.0
        ):
            raise ValueError("workspace tolerances must be positive finite numbers")
        if (
            not math.isfinite(self.singularity_tolerance)
            or not math.isfinite(self.near_singularity_tolerance)
            or self.singularity_tolerance <= 0.0
            or self.near_singularity_tolerance <= 0.0
        ):
            raise ValueError("workspace singularity tolerances must be positive finite numbers")
        if self.singularity_tolerance > self.near_singularity_tolerance:
            raise ValueError("singularity_tolerance must not exceed near_singularity_tolerance")
        if self.seed is not None and (
            not isinstance(self.seed, int) or isinstance(self.seed, bool)
        ):
            raise TypeError("workspace seed must be an integer or None")
        normalized: dict[str, tuple[float, ...]] = {}
        for joint_id, bounds in self.joint_ranges.items():
            values = tuple(_finite(item, f"joint_ranges[{joint_id}]") for item in bounds)
            if len(values) != 2 or values[0] > values[1]:
                raise ValueError(f"joint range for {joint_id!r} must be (lower, upper)")
            normalized[str(joint_id)] = values
        object.__setattr__(self, "joint_ranges", dict(sorted(normalized.items())))


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetReference:
    component_id: str
    connector_id: str | None = None

    def __post_init__(self) -> None:
        if not self.component_id:
            raise ValueError("component_id must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {"component_id": self.component_id, "connector_id": self.connector_id}


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceSample:
    joint_positions: Mapping[str, float]
    reachable: bool
    pose: Pose | None = None
    residual_m: float | None = None
    orientation_residual_rad: float | None = None
    singularity_status: str | None = None
    jacobian_rank: int | None = None
    minimum_singular_value: float | None = None
    condition_number: float | None = None
    issues: tuple[SimIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_positions", dict(sorted(self.joint_positions.items())))
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.singularity_status not in {None, "regular", "near_singular", "singular", "unavailable"}:
            raise ValueError("invalid workspace singularity status")
        if self.jacobian_rank is not None and self.jacobian_rank < 0:
            raise ValueError("jacobian_rank must be non-negative")
        for name in ("residual_m", "orientation_residual_rad", "minimum_singular_value"):
            value = getattr(self, name)
            if value is not None:
                number = _finite(value, name)
                if number < 0.0:
                    raise ValueError(f"{name} must be non-negative")
                object.__setattr__(self, name, number)
        if self.condition_number is not None:
            object.__setattr__(self, "condition_number", _finite(self.condition_number, "condition_number"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "joint_positions": dict(self.joint_positions),
            "reachable": self.reachable,
            "pose": _pose_dict(self.pose),
            "residual_m": self.residual_m,
            "orientation_residual_rad": self.orientation_residual_rad,
            "singularity_status": self.singularity_status,
            "jacobian_rank": self.jacobian_rank,
            "minimum_singular_value": self.minimum_singular_value,
            "condition_number": self.condition_number,
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceResult(AgentReadableResult):
    target: TargetReference
    samples: tuple[WorkspaceSample, ...]
    reachable_points: tuple[Pose, ...]
    bounds_m: Mapping[str, tuple[float, float]]
    reachable_fraction: float
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return bool(self.samples) and not any(
            item.severity == "error"
            for item in (
                *self.issues,
                *(issue for sample in self.samples for issue in sample.issues),
            )
        )

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("workspace result requires samples")
        if not 0.0 <= self.reachable_fraction <= 1.0:
            raise ValueError("reachable_fraction must be between 0 and 1")
        object.__setattr__(self, "samples", tuple(self.samples))
        object.__setattr__(self, "reachable_points", tuple(self.reachable_points))
        object.__setattr__(self, "bounds_m", dict(sorted(self.bounds_m.items())))
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "compute_workspace",
            "status": "passed" if self.passed else "failed",
            "target": self.target.to_dict(),
            "samples": [item.to_dict() for item in self.samples],
            "reachable_points": [_pose_dict(item) for item in self.reachable_points],
            "bounds_m": {key: list(value) for key, value in self.bounds_m.items()},
            "reachable_fraction": self.reachable_fraction,
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectorPathResult(AgentReadableResult):
    """Path statistics read from one recorded Connector trajectory."""

    component_id: str
    connector_id: str
    times_s: tuple[float, ...]
    positions_m: tuple[tuple[float, float, float], ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]
    start_position_m: tuple[float, float, float] | None
    end_position_m: tuple[float, float, float] | None
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(item.severity == "error" for item in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "trace_connector_path",
            "status": "passed" if self.passed else "failed",
            "component_id": self.component_id,
            "connector_id": self.connector_id,
            "times_s": list(self.times_s),
            "positions_m": [list(item) for item in self.positions_m],
            "path_length_m": self.path_length_m,
            "bounds_m": {key: list(value) for key, value in self.bounds_m.items()},
            "start_position_m": None if self.start_position_m is None else list(self.start_position_m),
            "end_position_m": None if self.end_position_m is None else list(self.end_position_m),
            "issues": [item.to_dict() for item in self.issues],
        }


def _jacobian_for(*, assembly: AssemblyModel, positions: Mapping[str, float], options: SingularityOptions) -> Any:
    # Lazy import avoids kinematics <-> analysis import cycles.
    from .kinematics_geometry import compute_jacobian

    target_component_id = options.target_component_id
    if target_component_id is None:
        grounded = {item.component_id for item in assembly.grounds}
        target_component_id = next(
            (item.component_id for item in assembly.components if item.component_id not in grounded),
            assembly.components[0].component_id if assembly.components else "",
        )
    return compute_jacobian(
        assembly=assembly,
        joint_positions=positions,
        target_component_id=target_component_id,
        target_connector_id=options.target_connector_id,
    )


def _jacobian_metrics(jacobian: Any) -> tuple[int, tuple[float, ...], float | None]:
    values = tuple(abs(float(item)) for item in getattr(jacobian, "singular_values", ()) or ())
    rank = int(getattr(jacobian, "rank", 0))
    # A target may be on a branch that is unaffected by some joints.  Those
    # structural zero columns are not a singular posture, so only values
    # supported by the reported numerical rank contribute to conditioning.
    positive = [item for item in values[:rank] if item > 0.0]
    condition = None if not values or not positive else max(values) / min(positive)
    return rank, values, condition


def find_singularities(*, motion_result: Any, assembly: AssemblyModel,
                       options: SingularityOptions | Mapping[str, Any] | None = None) -> Any:
    """Classify each recorded state using the Jacobian's rank and singular values."""

    from .kinematics import SingularityReport

    try:
        opts = _as_options(options, SingularityOptions)
    except (TypeError, ValueError) as error:
        issue = _issue(
            code="KINCHECK-KIN-SINGULARITY-OPTIONS-INVALID",
            message="The singularity analysis options are invalid.",
            object_ids=(getattr(motion_result, "scenario_id", ""),),
            evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
        )
        return SingularityReport(singular_times_s=(), tolerance=1e-8, issues=(issue,), samples=())

    samples: list[SingularitySample] = []
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    baseline_rank: int | None = None
    trajectories = tuple(getattr(motion_result, "joint_trajectories", ()))
    times = tuple(getattr(motion_result, "sample_times_s", ()))
    if not times:
        issues.append(_issue(code="KINCHECK-KIN-SINGULARITY-NO-SAMPLES", message="MotionResult has no samples.", object_ids=(getattr(motion_result, "scenario_id", ""),)))
    for index, time_s in enumerate(times):
        positions = {
            item.joint_id: float(item.positions[index])
            for item in trajectories if index < len(item.positions)
        }
        try:
            jacobian = _jacobian_for(assembly=assembly, positions=positions, options=opts)
            rank, values, condition = _jacobian_metrics(jacobian)
            positive_values = tuple(item for item in values[:rank] if item > 0.0)
            min_value = min(positive_values) if positive_values else None
            if baseline_rank is None:
                baseline_rank = rank
            rank_drop = baseline_rank is not None and rank < baseline_rank
            status = (
                "singular"
                if rank <= 0 or not positive_values or min_value <= opts.tolerance
                else "near_singular"
                if min_value <= opts.near_tolerance
                else "regular"
            )
            if rank_drop:
                status = "singular"
            sample = SingularitySample(time_s=time_s, status=status, rank=rank,
                                       minimum_singular_value=min_value, condition_number=condition,
                                       singular_values=values, joint_positions=positions)
            if status != "regular":
                issues.append(_issue(
                    code="KINCHECK-KIN-SINGULAR" if status == "singular" else "KINCHECK-KIN-NEAR-SINGULAR",
                    severity="error" if status == "singular" else "warning",
                    message="The kinematic Jacobian is singular or close to singular.",
                    object_ids=(getattr(motion_result, "scenario_id", ""),),
                    evidence=(Evidence(key="rank", actual=rank, expected=baseline_rank), Evidence(key="minimum_singular_value", actual=min_value, expected=opts.tolerance, unit="SI")),
                    failure_time_s=float(time_s),
                ))
        except Exception as error:
            sample = SingularitySample(time_s=time_s, status="unavailable", rank=0,
                                       minimum_singular_value=None, condition_number=None,
                                       joint_positions=positions)
            issues.append(_issue(
                code="KINCHECK-KIN-SINGULARITY-UNAVAILABLE",
                message="Singularity metrics could not be computed for this recorded sample.",
                object_ids=(getattr(motion_result, "scenario_id", ""),),
                evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
                failure_time_s=float(time_s),
            ))
        samples.append(sample)
    singular_times = tuple(item.time_s for item in samples if item.status == "singular")
    return SingularityReport(singular_times_s=singular_times, tolerance=opts.tolerance,
                             issues=tuple(issues), samples=tuple(samples))


def _pose_from_position_result(*, assembly: AssemblyModel, result: Any, target: TargetReference) -> Pose | None:
    poses = getattr(result, "component_poses", {})
    pose = poses.get(target.component_id) if hasattr(poses, "get") else None
    if pose is None:
        return None
    if target.connector_id is None:
        return pose
    connector = assembly.get_connector(component_id=target.component_id, connector_id=target.connector_id)
    return None if connector is None else compose_pose(parent=pose, child=connector.pose)


def check_reachability(*, assembly: AssemblyModel, target: Any,
                       options: ReachabilityOptions | Mapping[str, Any] | None = None,
                       joint_positions: Mapping[str, float] | None = None,
                       **kwargs: Any) -> Any:
    """Try one target pose and retain a machine-readable reason on failure."""

    from .kinematics import ReachabilityResult, solve_position
    from .kinematics_geometry import PoseTarget, PositionSolveOptions

    try:
        opts = _as_options(options, ReachabilityOptions)
    except (TypeError, ValueError) as error:
        issue = _issue(
            code="KINCHECK-KIN-REACHABILITY-OPTIONS-INVALID",
            message="The reachability options are invalid.",
            object_ids=(assembly.assembly_id,),
            evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
        )
        return ReachabilityResult(reachable=False, target=target, position_result=None, issues=(issue,))
    target_value = target
    if isinstance(target, Mapping):
        target_data = dict(target)
        target_data.setdefault("position_tolerance_m", opts.position_tolerance_m)
        target_data.setdefault("orientation_tolerance_rad", opts.orientation_tolerance_rad)
        target_value = PoseTarget(**target_data)
    elif not isinstance(target, PoseTarget):
        # Accept duck-typed targets while ensuring the solver receives the
        # documented object shape.
        target_position_tolerance = getattr(target, "position_tolerance_m", None)
        target_orientation_tolerance = getattr(
            target, "orientation_tolerance_rad", None
        )
        target_value = PoseTarget(
            component_id=str(getattr(target, "component_id")),
            connector_id=getattr(target, "connector_id", None),
            pose=getattr(target, "pose"),
            position_tolerance_m=(
                opts.position_tolerance_m
                if target_position_tolerance is None
                else float(target_position_tolerance)
            ),
            orientation_tolerance_rad=(
                opts.orientation_tolerance_rad
                if target_orientation_tolerance is None
                else float(target_orientation_tolerance)
            ),
        )
    positions = dict(opts.initial_joint_positions)
    positions.update(joint_positions or {})
    try:
        solver_options = kwargs.pop("solver_options", None)
        if solver_options is None:
            solver_options = PositionSolveOptions(
                position_tolerance_m=opts.position_tolerance_m,
                orientation_tolerance_rad=opts.orientation_tolerance_rad,
            )
        result = solve_position(
            assembly=assembly,
            joint_positions=positions,
            pose_targets=(target_value,),
            options=solver_options,
            **kwargs,
        )
        pose = _pose_from_position_result(assembly=assembly, result=result, target=TargetReference(component_id=getattr(target_value, "component_id"), connector_id=getattr(target_value, "connector_id", None)))
        passed = bool(getattr(result, "passed", False)) and pose is not None
        issues = tuple(getattr(result, "issues", ()))
        if pose is None:
            issues = (*issues, _issue(code="KINCHECK-KIN-TARGET-EVIDENCE-INCOMPLETE", message="The solved target pose could not be reconstructed.", object_ids=(getattr(target_value, "component_id", ""),)))
        return ReachabilityResult(reachable=passed, target=target, position_result=result, issues=issues)
    except KinCheckError as error:
        issue = _issue(code="KINCHECK-KIN-TARGET-INFEASIBLE", message=error.message, object_ids=getattr(error, "object_ids", ()))
        return ReachabilityResult(reachable=False, target=target, position_result=None, issues=(issue,))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        issue = _issue(
            code="KINCHECK-KIN-TARGET-NOT-FOUND",
            message="The reachability target is invalid or cannot be resolved.",
            object_ids=(getattr(target_value, "component_id", ""),),
            evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
        )
        return ReachabilityResult(reachable=False, target=target, position_result=None, issues=(issue,))


def _target_reference(value: Any) -> TargetReference:
    if isinstance(value, TargetReference):
        return value
    if isinstance(value, str):
        return TargetReference(component_id=value)
    if isinstance(value, Mapping):
        return TargetReference(component_id=str(value["component_id"]), connector_id=value.get("connector_id"))
    return TargetReference(component_id=str(getattr(value, "component_id")), connector_id=getattr(value, "connector_id", None))


def compute_workspace(*, assembly: AssemblyModel, target: Any,
                      options: WorkspaceOptions | Mapping[str, Any], **kwargs: Any) -> WorkspaceResult:
    """Enumerate a finite joint grid; every attempted point is retained."""

    from .kinematics import solve_position

    target_ref = _target_reference(target)
    try:
        opts = _as_options(options, WorkspaceOptions)
    except (TypeError, ValueError) as error:
        issue = _issue(
            code="KINCHECK-KIN-WORKSPACE-OPTIONS-INVALID",
            message="The workspace analysis options are invalid.",
            object_ids=(target_ref.component_id,),
            evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
        )
        return WorkspaceResult(
            target=target_ref,
            samples=(WorkspaceSample(joint_positions={}, reachable=False, singularity_status="unavailable", issues=(issue,)),),
            reachable_points=(),
            bounds_m={},
            reachable_fraction=0.0,
            issues=(issue,),
        )
    input_issues: list[SimIssue] = []
    component = assembly.get_component(component_id=target_ref.component_id)
    if component is None:
        input_issues.append(_issue(
            code="KINCHECK-KIN-TARGET-NOT-FOUND",
            message="Workspace target references an unknown Component.",
            object_ids=(target_ref.component_id,),
        ))
    elif target_ref.connector_id is not None and assembly.get_connector(
        component_id=target_ref.component_id,
        connector_id=target_ref.connector_id,
    ) is None:
        input_issues.append(_issue(
            code="KINCHECK-KIN-TARGET-NOT-FOUND",
            message="Workspace target references an unknown Connector.",
            object_ids=(target_ref.component_id, target_ref.connector_id),
        ))
    tree_joint_ids = {
        edge.joint_id for edge in build_kinematic_tree(assembly=assembly).tree_edges
    }
    for joint_id in opts.joint_ranges:
        joint = assembly.get_joint(joint_id=joint_id)
        if joint is None:
            input_issues.append(_issue(
                code="KINCHECK-KIN-WORKSPACE-JOINT-NOT-FOUND",
                message="Workspace range references an unknown Joint.",
                object_ids=(joint_id,),
            ))
        elif joint_id not in tree_joint_ids:
            input_issues.append(_issue(
                code="KINCHECK-KIN-WORKSPACE-JOINT-UNSUPPORTED",
                message="Workspace sampling requires a scalar tree Joint.",
                object_ids=(joint_id,),
            ))
    if not opts.joint_ranges:
        issue = _issue(code="KINCHECK-KIN-WORKSPACE-RANGE-REQUIRED", message="Workspace sampling requires an explicit finite range for each sampled Joint.", object_ids=(target_ref.component_id,))
        all_issues = (*input_issues, issue)
        # Keep the result inspectable without inventing an infinite/default range.
        return WorkspaceResult(target=target_ref, samples=(WorkspaceSample(joint_positions={}, reachable=False, singularity_status="unavailable", issues=all_issues),), reachable_points=(), bounds_m={}, reachable_fraction=0.0, issues=all_issues)
    ids = tuple(sorted(opts.joint_ranges))
    values = tuple(
        tuple(lower + (upper - lower) * index / (opts.samples_per_joint - 1) for index in range(opts.samples_per_joint))
        for lower, upper in (opts.joint_ranges[joint_id] for joint_id in ids)
    )
    combinations = list(itertools.product(*values))
    issues: list[SimIssue] = list(input_issues)
    if opts.seed is not None:
        random.Random(opts.seed).shuffle(combinations)
    if len(combinations) > opts.max_samples:
        combinations = combinations[:opts.max_samples]
        issues.append(_issue(code="KINCHECK-KIN-WORKSPACE-SAMPLE-TRUNCATED", severity="warning", message="Workspace sample grid exceeded max_samples and was truncated.", object_ids=ids))
    if input_issues:
        return WorkspaceResult(
            target=target_ref,
            samples=tuple(
                WorkspaceSample(
                    joint_positions=dict(zip(ids, combination)),
                    reachable=False,
                    singularity_status="unavailable",
                    issues=tuple(input_issues),
                )
                for combination in combinations
            ),
            reachable_points=(),
            bounds_m={},
            reachable_fraction=0.0,
            issues=tuple(issues),
        )
    samples: list[WorkspaceSample] = []
    reachable: list[Pose] = []
    solver_options = kwargs.pop("solver_options", None)
    for combination in combinations:
        positions = dict(zip(ids, combination))
        try:
            current_solver_options = solver_options
            if current_solver_options is None:
                from .kinematics_geometry import PositionSolveOptions
                current_solver_options = PositionSolveOptions(
                    position_tolerance_m=opts.position_tolerance_m,
                    orientation_tolerance_rad=opts.orientation_tolerance_rad,
                )
            result = solve_position(assembly=assembly, joint_positions=positions, options=current_solver_options, **kwargs)
            pose = _pose_from_position_result(assembly=assembly, result=result, target=target_ref)
            ok = bool(getattr(result, "passed", False)) and pose is not None
            sample_issues = list(getattr(result, "issues", ()))
            residual_m = max(
                (float(item.position_residual_m) for item in getattr(result, "residuals", ())),
                default=0.0,
            )
            orientation_residual_rad = max(
                (float(item.orientation_residual_rad) for item in getattr(result, "residuals", ())),
                default=0.0,
            )
            singularity_status = "unavailable"
            jacobian_rank = None
            minimum_singular_value = None
            condition_number = None
            try:
                from .kinematics_geometry import compute_jacobian

                jacobian = compute_jacobian(
                    assembly=assembly,
                    joint_positions=getattr(result, "joint_positions", positions),
                    target_component_id=target_ref.component_id,
                    target_connector_id=target_ref.connector_id,
                )
                jacobian_rank = jacobian.rank
                active_values = tuple(
                    value for value in jacobian.singular_values[: jacobian.rank] if value > 0.0
                )
                minimum_singular_value = min(active_values) if active_values else 0.0
                condition_number = jacobian.condition_number
                singularity_status = (
                    "singular"
                    if jacobian.rank == 0 or minimum_singular_value <= opts.singularity_tolerance
                    else "near_singular"
                    if minimum_singular_value <= opts.near_singularity_tolerance
                    else "regular"
                )
            except (KeyError, TypeError, ValueError, AttributeError) as error:
                sample_issues.append(_issue(
                    code="KINCHECK-KIN-SINGULARITY-UNAVAILABLE",
                    message="Singularity metrics could not be computed for this workspace sample.",
                    object_ids=(target_ref.component_id,),
                    evidence=(Evidence(key="native_error_type", actual=type(error).__name__),),
                ))
            if ok and pose is not None:
                reachable.append(pose)
            samples.append(WorkspaceSample(
                joint_positions=positions,
                reachable=ok,
                pose=pose,
                residual_m=residual_m,
                orientation_residual_rad=orientation_residual_rad,
                singularity_status=singularity_status,
                jacobian_rank=jacobian_rank,
                minimum_singular_value=minimum_singular_value,
                condition_number=condition_number,
                issues=tuple(sample_issues),
            ))
        except KinCheckError as error:
            sample_issue = _issue(code="KINCHECK-KIN-WORKSPACE-SAMPLE-FAILED", message=error.message, object_ids=getattr(error, "object_ids", ()))
            samples.append(WorkspaceSample(joint_positions=positions, reachable=False, singularity_status="unavailable", issues=(sample_issue,)))
    points = [pose.position_m for pose in reachable]
    bounds = {}
    if points:
        bounds = {axis: (min(point[index] for point in points), max(point[index] for point in points)) for index, axis in enumerate(("x_m", "y_m", "z_m"))}
    return WorkspaceResult(target=target_ref, samples=tuple(samples), reachable_points=tuple(reachable), bounds_m=bounds, reachable_fraction=len(reachable) / len(samples), issues=tuple(issues))


def trace_connector_path(*, motion_result: Any, component_id: str, connector_id: str) -> ConnectorPathResult:
    """Read a Connector trajectory and calculate path length and bounds."""

    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    trajectory = next(
        (
            item
            for item in getattr(motion_result, "trajectories", ())
            if item.component_id == component_id and item.connector_id == connector_id
        ),
        None,
    )
    if trajectory is None:
        issues.append(_issue(
            code="KINCHECK-RESULT-TRAJECTORY-MISSING",
            message="The requested Connector trajectory was not recorded.",
            object_ids=(component_id, connector_id),
        ))
        return ConnectorPathResult(
            component_id=component_id,
            connector_id=connector_id,
            times_s=(),
            positions_m=(),
            path_length_m=0.0,
            bounds_m={},
            start_position_m=None,
            end_position_m=None,
            issues=tuple(issues),
        )
    positions = tuple(tuple(float(value) for value in pose.position_m) for pose in trajectory.poses)
    length = sum(math.dist(left, right) for left, right in zip(positions, positions[1:]))
    bounds = {
        axis: (min(point[index] for point in positions), max(point[index] for point in positions))
        for index, axis in enumerate(("x_m", "y_m", "z_m"))
    } if positions else {}
    return ConnectorPathResult(
        component_id=component_id,
        connector_id=connector_id,
        times_s=tuple(trajectory.times_s),
        positions_m=positions,
        path_length_m=length,
        bounds_m=bounds,
        start_position_m=positions[0] if positions else None,
        end_position_m=positions[-1] if positions else None,
        issues=tuple(issues),
    )


__all__ = [
    "ConnectorPathResult", "ReachabilityOptions", "SingularityOptions", "SingularitySample", "TargetReference",
    "WorkspaceOptions", "WorkspaceResult", "WorkspaceSample", "check_reachability",
    "compute_workspace", "find_singularities", "trace_connector_path",
]
