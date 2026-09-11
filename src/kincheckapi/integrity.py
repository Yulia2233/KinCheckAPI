"""Whole-assembly connectivity checks over static or solved motion states."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

from ._clearance_fcl import load_mesh, query_pair, require_backend
from .assembly import AssemblyModel, Component, Constraint, Joint, validate_assembly
from .diagnostics import AgentReadableResult, Evidence, SimIssue, collect_issues
from .errors import BackendCapabilityError
from .pose import Pose, relative_pose
from .result import MotionResult


IntegrityStatus = Literal["passed", "failed", "partial", "capability_failed", "validation_failed"]
SamplingScope = Literal["initial", "motion_result"]


def _finite(value: float, name: str, *, non_negative: bool = False) -> float:
    number = float(value)
    if not math.isfinite(number) or (non_negative and number < 0.0):
        qualifier = "finite and non-negative" if non_negative else "finite"
        raise ValueError(f"{name} must be {qualifier}")
    return number


def _vector(value: Sequence[float], name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{name} must contain three values")
    result = tuple(_finite(item, name) for item in value)
    norm = math.sqrt(sum(item * item for item in result))
    if norm <= 0.0:
        raise ValueError(f"{name} must be non-zero")
    return tuple(item / norm for item in result)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContainmentRelation:
    """A declared relative-axis interval that keeps one component contained."""

    relation_id: str
    contained_component_id: str
    container_component_id: str
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    min_position_m: float = 0.0
    max_position_m: float = 0.0
    allowed_escape_tolerance_m: float = 1e-4

    def __post_init__(self) -> None:
        for name in ("relation_id", "contained_component_id", "container_component_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.contained_component_id == self.container_component_id:
            raise ValueError("Containment relation requires two distinct Components")
        object.__setattr__(self, "axis", _vector(self.axis, "axis"))
        minimum = _finite(self.min_position_m, "min_position_m")
        maximum = _finite(self.max_position_m, "max_position_m")
        tolerance = _finite(self.allowed_escape_tolerance_m, "allowed_escape_tolerance_m", non_negative=True)
        if minimum > maximum:
            raise ValueError("min_position_m must not exceed max_position_m")
        object.__setattr__(self, "min_position_m", minimum)
        object.__setattr__(self, "max_position_m", maximum)
        object.__setattr__(self, "allowed_escape_tolerance_m", tolerance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "contained_component_id": self.contained_component_id,
            "container_component_id": self.container_component_id,
            "axis": list(self.axis),
            "min_position_m": self.min_position_m,
            "max_position_m": self.max_position_m,
            "allowed_escape_tolerance_m": self.allowed_escape_tolerance_m,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class IntegrityRelationResult:
    """One relation observation at one checked state."""

    relation_id: str
    relation_type: Literal["mechanical", "geometric", "containment"]
    component_a_id: str
    component_b_id: str
    time_s: float
    passed: bool
    measurement_m: float | None = None
    tolerance_m: float | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "component_a_id": self.component_a_id,
            "component_b_id": self.component_b_id,
            "time_s": self.time_s,
            "passed": self.passed,
            "measurement_m": self.measurement_m,
            "tolerance_m": self.tolerance_m,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class AssemblyIntegrityReport(AgentReadableResult):
    """Structured result for whole-assembly connectivity over checked states."""

    passed: bool
    status: IntegrityStatus
    checked_component_ids: tuple[str, ...]
    connected_component_ids: tuple[str, ...] = ()
    disconnected_component_ids: tuple[str, ...] = ()
    detached_component_ids: tuple[str, ...] = ()
    out_of_bounds_component_ids: tuple[str, ...] = ()
    failed_relation_ids: tuple[str, ...] = ()
    failed_sample_times_s: tuple[float, ...] = ()
    connected_network_count_by_sample: tuple[tuple[float, int], ...] = ()
    geometric_connections: tuple[IntegrityRelationResult, ...] = ()
    containment_results: tuple[IntegrityRelationResult, ...] = ()
    mechanical_relation_results: tuple[IntegrityRelationResult, ...] = ()
    checked_sample_count: int = 0
    geometric_connection_tolerance_m: float = 0.0
    penetration_tolerance_m: float = 0.0
    containment_escape_tolerance_m: float = 0.0
    sampling_scope: SamplingScope = "initial"
    issues: tuple[SimIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    operation: str = "check_assembly_integrity"

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "partial", "capability_failed", "validation_failed"}:
            raise ValueError("Invalid assembly-integrity status")
        if self.sampling_scope not in {"initial", "motion_result"}:
            raise ValueError("sampling_scope must be initial or motion_result")
        if self.checked_sample_count < 0:
            raise ValueError("checked_sample_count must be non-negative")
        object.__setattr__(self, "checked_component_ids", tuple(sorted(self.checked_component_ids)))
        for name in (
            "connected_component_ids",
            "disconnected_component_ids",
            "detached_component_ids",
            "out_of_bounds_component_ids",
            "failed_relation_ids",
            "failed_sample_times_s",
        ):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)))))
        object.__setattr__(self, "connected_network_count_by_sample", tuple(self.connected_network_count_by_sample))
        object.__setattr__(self, "geometric_connections", tuple(self.geometric_connections))
        object.__setattr__(self, "containment_results", tuple(self.containment_results))
        object.__setattr__(self, "mechanical_relation_results", tuple(self.mechanical_relation_results))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        for name in (
            "geometric_connection_tolerance_m",
            "penetration_tolerance_m",
            "containment_escape_tolerance_m",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name, non_negative=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "passed": self.passed,
            "status": self.status,
            "checked_component_ids": list(self.checked_component_ids),
            "connected_component_ids": list(self.connected_component_ids),
            "disconnected_component_ids": list(self.disconnected_component_ids),
            "detached_component_ids": list(self.detached_component_ids),
            "out_of_bounds_component_ids": list(self.out_of_bounds_component_ids),
            "failed_relation_ids": list(self.failed_relation_ids),
            "failed_sample_times_s": list(self.failed_sample_times_s),
            "connected_network_count_by_sample": [list(item) for item in self.connected_network_count_by_sample],
            "geometric_connections": [item.to_dict() for item in self.geometric_connections],
            "containment_results": [item.to_dict() for item in self.containment_results],
            "mechanical_relation_results": [item.to_dict() for item in self.mechanical_relation_results],
            "checked_sample_count": self.checked_sample_count,
            "geometric_connection_tolerance_m": self.geometric_connection_tolerance_m,
            "penetration_tolerance_m": self.penetration_tolerance_m,
            "containment_escape_tolerance_m": self.containment_escape_tolerance_m,
            "sampling_scope": self.sampling_scope,
            "issues": [item.to_dict() for item in self.issues],
            "metadata": dict(self.metadata),
        }


def _issue(*, code: str, message: str, object_ids: Sequence[str] = (), time_s: float | None = None, evidence: Sequence[Evidence] = ()) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="assembly.integrity",
        message=message,
        object_ids=tuple(object_ids),
        failure_time_s=time_s,
        evidence=tuple(evidence),
        suggested_actions=("Correct the assembly relation, geometry, or motion range and validate again.",),
    )


def _component_pairs(component_ids: tuple[str, ...], pairs: Sequence[Sequence[str]] | None) -> tuple[tuple[str, str], ...]:
    known = set(component_ids)
    if pairs is None:
        return tuple((left, right) for index, left in enumerate(component_ids) for right in component_ids[index + 1:])
    result: set[tuple[str, str]] = set()
    for raw in pairs:
        if isinstance(raw, (str, bytes)) or len(raw) != 2:
            raise ValueError("Each geometric connection pair must contain two Component IDs")
        left, right = str(raw[0]), str(raw[1])
        if left == right or left not in known or right not in known:
            raise ValueError(f"Invalid geometric connection pair: {raw!r}")
        result.add(tuple(sorted((left, right))))
    return tuple(sorted(result))


def _samples(*, assembly: AssemblyModel, motion_result: MotionResult | None, component_ids: tuple[str, ...], sampling_scope: SamplingScope) -> tuple[tuple[float, Mapping[str, Pose]], ...]:
    if sampling_scope == "initial":
        return ((0.0, {component.component_id: component.initial_pose for component in assembly.components if component.component_id in component_ids}),)
    if motion_result is None:
        raise ValueError("motion_result is required when sampling_scope='motion_result'")
    if motion_result.assembly_id != assembly.assembly_id:
        raise ValueError("Assembly and MotionResult IDs do not match")
    if motion_result.status == "partial":
        raise RuntimeError("MotionResult is partial and cannot establish whole-assembly integrity")
    by_component: dict[str, dict[float, Pose]] = {item: {} for item in component_ids}
    for trajectory in motion_result.trajectories:
        if trajectory.connector_id is None and trajectory.component_id in by_component:
            by_component[trajectory.component_id] = {
                float(time_s): pose for time_s, pose in zip(trajectory.times_s, trajectory.poses)
            }
    if any(not values for values in by_component.values()):
        missing = tuple(item for item, values in by_component.items() if not values)
        raise ValueError(f"MotionResult lacks Component trajectories: {missing}")
    result: list[tuple[float, Mapping[str, Pose]]] = []
    for time_s in motion_result.sample_times_s:
        poses: dict[str, Pose] = {}
        for component_id in component_ids:
            pose = by_component[component_id].get(float(time_s))
            if pose is None:
                raise ValueError(f"MotionResult lacks Component {component_id} at time {time_s}")
            poses[component_id] = pose
        result.append((float(time_s), poses))
    return tuple(result)


def _mechanical_edges(assembly: AssemblyModel, component_ids: tuple[str, ...], relation_ids: Sequence[str] | None) -> tuple[tuple[str, str, str], ...]:
    selected = None if relation_ids is None else {str(item) for item in relation_ids}
    known = set(component_ids)
    edges: list[tuple[str, str, str]] = []
    relations: list[tuple[str, str, str]] = []
    relations.extend((joint.joint_id, joint.connector_a.component_id, joint.connector_b.component_id) for joint in assembly.joints)
    relations.extend((constraint.constraint_id, constraint.connector_a.component_id, constraint.connector_b.component_id) for constraint in assembly.constraints)
    relations.extend((closure.closure_id, closure.constraint.connector_a.component_id, closure.constraint.connector_b.component_id) for closure in assembly.closures)
    for relation_id, left, right in relations:
        if selected is not None and relation_id not in selected:
            continue
        if left in known and right in known and left != right:
            edges.append((relation_id, *tuple(sorted((left, right)))))
    return tuple(sorted(set(edges)))


def _network_count(component_ids: tuple[str, ...], edges: Sequence[tuple[str, str]]) -> tuple[int, set[str]]:
    parent = {item: item for item in component_ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in edges:
        if left not in parent or right not in parent:
            continue
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root
    roots = {find(item) for item in component_ids}
    return len(roots), roots


def check_assembly_integrity(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult | None = None,
    asset_root: str | Path | None = None,
    component_ids: Sequence[str] | None = None,
    geometric_connection_pairs: Sequence[Sequence[str]] | None = None,
    containment_relations: Sequence[ContainmentRelation] = (),
    mechanical_relation_ids: Sequence[str] | None = None,
    geometric_connection_tolerance_m: float = 1e-4,
    penetration_tolerance_m: float = 0.0,
    containment_escape_tolerance_m: float = 1e-4,
    sampling_scope: SamplingScope = "motion_result",
    require_single_network: bool = True,
) -> AssemblyIntegrityReport:
    """Verify that all selected Components remain one connected assembly.

    Mechanical relations are graph edges, geometric pairs are state-dependent
    edges, and containment relations are state-dependent guide/retention edges.
    Every motion-result sample must satisfy the same connectivity policy.
    """

    issues: list[SimIssue] = []
    all_components = {item.component_id: item for item in assembly.components}
    selected = tuple(sorted(all_components)) if component_ids is None else tuple(sorted({str(item) for item in component_ids}))
    if not selected:
        return AssemblyIntegrityReport(
            passed=False,
            status="validation_failed",
            checked_component_ids=(),
            sampling_scope=sampling_scope,
            issues=(_issue(code="KINCHECK-INTEGRITY-COMPONENT-SCOPE-EMPTY", message="At least one Component must be selected."),),
        )
    unknown = tuple(item for item in selected if item not in all_components)
    if unknown:
        issues.append(_issue(code="KINCHECK-INTEGRITY-COMPONENT-NOT-FOUND", message="A selected Component does not exist in the AssemblyModel.", object_ids=unknown))
    selected = tuple(item for item in selected if item in all_components)
    explicit_geometric_pairs = geometric_connection_pairs is not None
    try:
        geometric_pairs = _component_pairs(selected, geometric_connection_pairs)
        geometric_tol = _finite(geometric_connection_tolerance_m, "geometric_connection_tolerance_m", non_negative=True)
        penetration_tol = _finite(penetration_tolerance_m, "penetration_tolerance_m", non_negative=True)
        escape_tol = _finite(containment_escape_tolerance_m, "containment_escape_tolerance_m", non_negative=True)
        samples = _samples(assembly=assembly, motion_result=motion_result, component_ids=selected, sampling_scope=sampling_scope)
    except RuntimeError as cause:
        return AssemblyIntegrityReport(
            passed=False,
            status="partial",
            checked_component_ids=selected,
            sampling_scope=sampling_scope,
            issues=(*issues, _issue(code="KINCHECK-INTEGRITY-MOTION-PARTIAL", message=str(cause))),
        )
    except (TypeError, ValueError) as cause:
        return AssemblyIntegrityReport(
            passed=False,
            status="validation_failed",
            checked_component_ids=selected,
            sampling_scope=sampling_scope,
            issues=(*issues, _issue(code="KINCHECK-INTEGRITY-INPUT-INVALID", message=str(cause))),
        )

    validation = collect_issues(results=(validate_assembly(assembly=assembly),))
    issues.extend(validation)
    if any(item.severity == "error" for item in validation):
        return AssemblyIntegrityReport(
            passed=False,
            status="validation_failed",
            checked_component_ids=selected,
            checked_sample_count=len(samples),
            geometric_connection_tolerance_m=geometric_tol,
            penetration_tolerance_m=penetration_tol,
            containment_escape_tolerance_m=escape_tol,
            sampling_scope=sampling_scope,
            issues=tuple(issues),
        )

    try:
        mechanical_edges = _mechanical_edges(assembly, selected, mechanical_relation_ids)
        containment_by_id = {item.relation_id: item for item in containment_relations}
        if len(containment_by_id) != len(tuple(containment_relations)):
            raise ValueError("Containment relation IDs must be unique")
        for relation in containment_relations:
            if relation.contained_component_id not in selected or relation.container_component_id not in selected:
                raise ValueError(f"Containment relation references an unselected or unknown Component: {relation.relation_id}")
        meshes = {}
        if geometric_pairs:
            require_backend()
            parts = {item.part_id: item for item in assembly.parts}
            available_pairs: list[tuple[str, str]] = []
            for left, right in geometric_pairs:
                left_component = all_components[left]
                right_component = all_components[right]
                left_part = parts.get(left_component.part_id)
                right_part = parts.get(right_component.part_id)
                if geometric_connection_pairs is None and (
                    left_part is None
                    or right_part is None
                    or not left_part.asset_paths.get("stl")
                    or not right_part.asset_paths.get("stl")
                ):
                    # Automatic geometric discovery is opportunistic.  A model
                    # without mesh assets can still be checked through its
                    # declared mechanical/containment relations.
                    continue
                available_pairs.append((left, right))
            geometric_pairs = tuple(available_pairs)
            for component_id in sorted({item for pair in geometric_pairs for item in pair}):
                component = all_components[component_id]
                part = parts.get(component.part_id)
                if part is None:
                    raise ValueError(f"Component {component_id} references unknown Part {component.part_id}")
                meshes[component_id] = load_mesh(assembly=assembly, part=part, asset_root=asset_root)
    except BackendCapabilityError as cause:
        return AssemblyIntegrityReport(
            passed=False,
            status="capability_failed",
            checked_component_ids=selected,
            checked_sample_count=len(samples),
            geometric_connection_tolerance_m=geometric_tol,
            penetration_tolerance_m=penetration_tol,
            containment_escape_tolerance_m=escape_tol,
            sampling_scope=sampling_scope,
            issues=(*issues, _issue(code="KINCHECK-INTEGRITY-BACKEND-UNAVAILABLE", message=str(cause))),
        )
    except (TypeError, ValueError, FileNotFoundError, OSError) as cause:
        return AssemblyIntegrityReport(
            passed=False,
            status="validation_failed",
            checked_component_ids=selected,
            checked_sample_count=len(samples),
            geometric_connection_tolerance_m=geometric_tol,
            penetration_tolerance_m=penetration_tol,
            containment_escape_tolerance_m=escape_tol,
            sampling_scope=sampling_scope,
            issues=(*issues, _issue(code="KINCHECK-INTEGRITY-GEOMETRY-INVALID", message=str(cause))),
        )

    geometric_results: list[IntegrityRelationResult] = []
    containment_results: list[IntegrityRelationResult] = []
    mechanical_results: list[IntegrityRelationResult] = []
    failed_components: set[str] = set()
    failed_relations: set[str] = set()
    failed_times: set[float] = set()
    network_counts: list[tuple[float, int]] = []
    connected_at_last: set[str] = set()

    for time_s, poses in samples:
        edges: list[tuple[str, str]] = [(left, right) for _, left, right in mechanical_edges]
        for relation_id, left, right in mechanical_edges:
            mechanical_results.append(IntegrityRelationResult(relation_id=relation_id, relation_type="mechanical", component_a_id=left, component_b_id=right, time_s=time_s, passed=True, reason="Mechanical relation is present in AssemblyModel."))
        for relation in containment_relations:
            relative = relative_pose(parent=poses[relation.container_component_id], child=poses[relation.contained_component_id])
            scalar = sum(relative.position_m[index] * relation.axis[index] for index in range(3))
            lower_error = relation.min_position_m - scalar
            upper_error = scalar - relation.max_position_m
            escape = max(0.0, lower_error, upper_error)
            passed = escape <= max(escape_tol, relation.allowed_escape_tolerance_m)
            containment_results.append(IntegrityRelationResult(relation_id=relation.relation_id, relation_type="containment", component_a_id=relation.contained_component_id, component_b_id=relation.container_component_id, time_s=time_s, passed=passed, measurement_m=scalar, tolerance_m=max(escape_tol, relation.allowed_escape_tolerance_m), reason="Within declared containment interval." if passed else "Component is outside the declared containment interval."))
            if passed:
                edges.append((relation.contained_component_id, relation.container_component_id))
            else:
                failed_components.add(relation.contained_component_id)
                failed_relations.add(relation.relation_id)
                failed_times.add(time_s)
                issues.append(_issue(code="KINCHECK-INTEGRITY-CONTAINMENT-ESCAPED", message="A Component left its declared containment or guide interval.", object_ids=(relation.contained_component_id, relation.container_component_id, relation.relation_id), time_s=time_s, evidence=(Evidence(key="position_m", actual=scalar, expected=(relation.min_position_m, relation.max_position_m), unit="m"), Evidence(key="escape_tolerance_m", actual=max(escape_tol, relation.allowed_escape_tolerance_m), unit="m"))))
        for left, right in geometric_pairs:
            try:
                collided, signed_distance, point_a, point_b = query_pair(meshes[left], meshes[right], poses[left], poses[right])
            except Exception as cause:
                raise RuntimeError(f"Geometric connection query failed for {left}/{right}: {cause}") from cause
            penetration = max(0.0, -signed_distance) if collided else 0.0
            passed = (not collided or penetration <= penetration_tol) and signed_distance <= geometric_tol
            relation_id = f"geometric:{left}:{right}"
            geometric_results.append(IntegrityRelationResult(relation_id=relation_id, relation_type="geometric", component_a_id=left, component_b_id=right, time_s=time_s, passed=passed, measurement_m=signed_distance, tolerance_m=geometric_tol, reason="Gap is within geometric connection tolerance." if passed else ("Penetration exceeds tolerance." if penetration > penetration_tol else "Gap exceeds geometric connection tolerance.")))
            if passed:
                edges.append((left, right))
            else:
                if explicit_geometric_pairs:
                    failed_components.update((left, right))
                    failed_relations.add(relation_id)
                    failed_times.add(time_s)
                    issues.append(_issue(code="KINCHECK-INTEGRITY-GEOMETRIC-CONNECTION-FAILED", message="A declared geometric connection is not maintained at this sample.", object_ids=(left, right), time_s=time_s, evidence=(Evidence(key="signed_distance_m", actual=signed_distance, expected=f"<= {geometric_tol}", unit="m"), Evidence(key="penetration_m", actual=penetration, expected=f"<= {penetration_tol}", unit="m"), Evidence(key="nearest_point_a_m", actual=point_a, unit="m"), Evidence(key="nearest_point_b_m", actual=point_b, unit="m"))))
        count, roots = _network_count(selected, edges)
        network_counts.append((time_s, count))
        if count == 1:
            connected_at_last = set(selected)
        if require_single_network and count != 1:
            failed_times.add(time_s)
            disconnected = set(selected)
            for left, right in edges:
                disconnected.discard(left)
                disconnected.discard(right)
            failed_components.update(disconnected or set(selected))
            issues.append(_issue(code="KINCHECK-INTEGRITY-DISCONNECTED", message="The selected Components do not form one connected assembly at this sample.", object_ids=tuple(sorted(disconnected or set(selected))), time_s=time_s, evidence=(Evidence(key="connected_network_count", actual=count, expected=1),)))

    status: IntegrityStatus = "failed" if any(item.severity == "error" for item in issues) else "passed"
    return AssemblyIntegrityReport(
        passed=status == "passed",
        status=status,
        checked_component_ids=selected,
        connected_component_ids=tuple(sorted(connected_at_last)),
        disconnected_component_ids=tuple(sorted(failed_components)),
        detached_component_ids=tuple(sorted(failed_components)),
        out_of_bounds_component_ids=tuple(sorted({item.component_a_id for item in containment_results if not item.passed})),
        failed_relation_ids=tuple(sorted(failed_relations)),
        failed_sample_times_s=tuple(sorted(failed_times)),
        connected_network_count_by_sample=tuple(network_counts),
        geometric_connections=tuple(geometric_results),
        containment_results=tuple(containment_results),
        mechanical_relation_results=tuple(mechanical_results),
        checked_sample_count=len(samples),
        geometric_connection_tolerance_m=geometric_tol,
        penetration_tolerance_m=penetration_tol,
        containment_escape_tolerance_m=escape_tol,
        sampling_scope=sampling_scope,
        issues=tuple(issues),
        metadata={"assembly_id": assembly.assembly_id, "geometric_connection_pairs": geometric_pairs, "mechanical_relation_count": len(mechanical_edges), "containment_relation_count": len(tuple(containment_relations)), "require_single_network": require_single_network},
    )


__all__ = ["AssemblyIntegrityReport", "ContainmentRelation", "IntegrityRelationResult", "check_assembly_integrity"]
