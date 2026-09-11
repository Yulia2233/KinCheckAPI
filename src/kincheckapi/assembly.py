"""Backend-independent, immutable assembly model for KinCheckAPI."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass, replace
from enum import Enum
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .diagnostics import Evidence, SimIssue, ValidationResult
from .errors import AssemblyValidationError
from .pose import Pose, Quaternion, Vector3, compose_pose


class JointType(str, Enum):
    FIXED = "fixed"
    REVOLUTE = "revolute"
    PRISMATIC = "prismatic"
    CYLINDRICAL = "cylindrical"
    SPHERICAL = "spherical"
    PLANAR = "planar"
    FREE = "free"


class CouplingType(str, Enum):
    GEAR = "gear"
    BELT = "belt"
    RACK_PINION = "rack_pinion"


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in (value or {}).items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _require_id(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class Connector:
    connector_id: str
    pose: Pose = field(default_factory=Pose)
    display_name: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.connector_id, "connector_id")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class Part:
    part_id: str
    connectors: tuple[Connector, ...] = ()
    asset_paths: Mapping[str, str] = field(default_factory=dict)
    asset_hashes: Mapping[str, str] = field(default_factory=dict)
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.part_id, "part_id")
        object.__setattr__(self, "connectors", tuple(self.connectors))
        object.__setattr__(self, "asset_paths", _freeze_mapping(self.asset_paths))
        object.__setattr__(self, "asset_hashes", _freeze_mapping(self.asset_hashes))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def get_connector(self, *, connector_id: str) -> Connector | None:
        return next((item for item in self.connectors if item.connector_id == connector_id), None)


@dataclass(frozen=True, slots=True)
class Component:
    component_id: str
    part_id: str
    initial_pose: Pose = field(default_factory=Pose)
    connectors: tuple[Connector, ...] = ()
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")
        _require_id(self.part_id, "part_id")
        object.__setattr__(self, "connectors", tuple(self.connectors))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def get_connector(self, *, connector_id: str) -> Connector | None:
        return next((item for item in self.connectors if item.connector_id == connector_id), None)


@dataclass(frozen=True, slots=True)
class ConnectorRef:
    component_id: str
    connector_id: str

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")
        _require_id(self.connector_id, "connector_id")


@dataclass(frozen=True, slots=True)
class JointLimit:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.lower) or not math.isfinite(self.upper) or self.lower > self.upper:
            raise ValueError("Joint limits must be finite and lower <= upper")


# Public short name requested by the namespace design.
Limit = JointLimit


@dataclass(frozen=True, slots=True)
class Joint:
    joint_id: str
    joint_type: JointType | str
    connector_a: ConnectorRef
    connector_b: ConnectorRef
    limit: JointLimit | None = None
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.joint_id, "joint_id")
        object.__setattr__(self, "joint_type", JointType(self.joint_type))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class Constraint:
    constraint_id: str
    connector_a: ConnectorRef
    connector_b: ConnectorRef
    constraint_type: str = "coincident"
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.constraint_id, "constraint_id")
        _require_id(self.constraint_type, "constraint_type")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class Coupling:
    coupling_id: str
    coupling_type: CouplingType | str
    joint_a_id: str
    joint_b_id: str
    ratio: float
    phase_offset: float = 0.0
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.coupling_id, "coupling_id")
        _require_id(self.joint_a_id, "joint_a_id")
        _require_id(self.joint_b_id, "joint_b_id")
        object.__setattr__(self, "coupling_type", CouplingType(self.coupling_type))
        if not math.isfinite(self.ratio) or self.ratio == 0.0:
            raise ValueError("Coupling ratio must be finite and non-zero")
        if not math.isfinite(self.phase_offset):
            raise ValueError("Coupling phase_offset must be finite")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class Closure:
    closure_id: str
    constraint: Constraint
    position_tolerance_m: float = 1e-6
    orientation_tolerance_rad: float = 1e-6

    def __post_init__(self) -> None:
        _require_id(self.closure_id, "closure_id")
        if (
            not math.isfinite(self.position_tolerance_m)
            or not math.isfinite(self.orientation_tolerance_rad)
            or self.position_tolerance_m <= 0.0
            or self.orientation_tolerance_rad <= 0.0
        ):
            raise ValueError("Closure tolerances must be positive finite numbers")


@dataclass(frozen=True, slots=True)
class Ground:
    component_id: str

    def __post_init__(self) -> None:
        _require_id(self.component_id, "component_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class KinematicEdge:
    """One directed movable-joint edge in an analyzed kinematic graph."""

    edge_id: str
    joint_id: str
    parent_group_id: str
    child_group_id: str
    parent_component_id: str
    child_component_id: str
    joint_type: JointType | str

    def __post_init__(self) -> None:
        for name in (
            "edge_id",
            "joint_id",
            "parent_group_id",
            "child_group_id",
            "parent_component_id",
            "child_component_id",
        ):
            _require_id(getattr(self, name), name)
        object.__setattr__(self, "joint_type", JointType(self.joint_type))

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "joint_id": self.joint_id,
            "parent_group_id": self.parent_group_id,
            "child_group_id": self.child_group_id,
            "parent_component_id": self.parent_component_id,
            "child_component_id": self.child_component_id,
            "joint_type": self.joint_type.value,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class KinematicTree:
    """Backend-independent analysis of rigid groups and movable joints."""

    root_group_ids: tuple[str, ...]
    component_groups: Mapping[str, str]
    group_components: Mapping[str, tuple[str, ...]]
    parent_component_id: Mapping[str, str | None]
    parent_group_id: Mapping[str, str | None]
    depth_by_component_id: Mapping[str, int]
    tree_edges: tuple[KinematicEdge, ...]
    closure_edges: tuple[KinematicEdge, ...]
    disconnected_group_ids: tuple[str, ...]
    grounded_group_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "root_group_ids",
            "tree_edges",
            "closure_edges",
            "disconnected_group_ids",
            "grounded_group_ids",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for name in (
            "component_groups",
            "parent_component_id",
            "parent_group_id",
            "depth_by_component_id",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_group_ids": list(self.root_group_ids),
            "component_groups": dict(self.component_groups),
            "group_components": {key: list(value) for key, value in self.group_components.items()},
            "parent_component_id": dict(self.parent_component_id),
            "parent_group_id": dict(self.parent_group_id),
            "depth_by_component_id": dict(self.depth_by_component_id),
            "tree_edges": [edge.to_dict() for edge in self.tree_edges],
            "closure_edges": [edge.to_dict() for edge in self.closure_edges],
            "disconnected_group_ids": list(self.disconnected_group_ids),
            "grounded_group_ids": list(self.grounded_group_ids),
        }
        object.__setattr__(
            self,
            "group_components",
            MappingProxyType(
                {
                    str(group_id): tuple(component_ids)
                    for group_id, component_ids in self.group_components.items()
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class AssemblyModel:
    assembly_id: str
    parts: tuple[Part, ...] = ()
    components: tuple[Component, ...] = ()
    joints: tuple[Joint, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    couplings: tuple[Coupling, ...] = ()
    closures: tuple[Closure, ...] = ()
    grounds: tuple[Ground, ...] = ()
    collision_exclusions: tuple[tuple[str, str], ...] = ()
    display_name: str | None = None
    source_path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.assembly_id, "assembly_id")
        for name in ("parts", "components", "joints", "constraints", "couplings", "closures", "grounds"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(
            self,
            "collision_exclusions",
            tuple(tuple(sorted(pair)) for pair in self.collision_exclusions),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def get_part(self, *, part_id: str) -> Part | None:
        return next((item for item in self.parts if item.part_id == part_id), None)

    def get_component(self, *, component_id: str) -> Component | None:
        return next((item for item in self.components if item.component_id == component_id), None)

    def get_joint(self, *, joint_id: str) -> Joint | None:
        return next((item for item in self.joints if item.joint_id == joint_id), None)

    def get_constraint(self, *, constraint_id: str) -> Constraint | None:
        return next((item for item in self.constraints if item.constraint_id == constraint_id), None)

    def get_connector(self, *, component_id: str, connector_id: str) -> Connector | None:
        component = self.get_component(component_id=component_id)
        if component is None:
            return None
        local = component.get_connector(connector_id=connector_id)
        if local is not None:
            return local
        part = self.get_part(part_id=component.part_id)
        return None if part is None else part.get_connector(connector_id=connector_id)


def _topology_groups(
    *, assembly: AssemblyModel
) -> tuple[Mapping[str, str], Mapping[str, tuple[str, ...]]]:
    """Return deterministic rigid groups formed by fixed joints."""

    parent = {component.component_id: component.component_id for component in assembly.components}

    def find(component_id: str) -> str:
        current = parent[component_id]
        while current != parent[current]:
            parent[current] = parent[parent[current]]
            current = parent[current]
        return current

    def union(left: str, right: str) -> None:
        if left not in parent or right not in parent:
            return
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        first, second = sorted((left_root, right_root))
        parent[second] = first

    for joint in assembly.joints:
        if joint.joint_type == JointType.FIXED:
            union(joint.connector_a.component_id, joint.connector_b.component_id)

    component_groups = {
        component_id: find(component_id) for component_id in parent
    }
    groups: dict[str, list[str]] = {}
    for component_id, group_id in component_groups.items():
        groups.setdefault(group_id, []).append(component_id)
    return MappingProxyType(component_groups), MappingProxyType(
        {group_id: tuple(sorted(component_ids)) for group_id, component_ids in sorted(groups.items())}
    )


def _topology_edge(
    *, joint: Joint, component_groups: Mapping[str, str], parent_group_id: str, child_group_id: str
) -> KinematicEdge:
    """Orient an edge and retain the endpoint component IDs used by the joint."""

    if component_groups.get(joint.connector_a.component_id) == parent_group_id:
        parent_component_id = joint.connector_a.component_id
        child_component_id = joint.connector_b.component_id
    else:
        parent_component_id = joint.connector_b.component_id
        child_component_id = joint.connector_a.component_id
    return KinematicEdge(
        edge_id=joint.joint_id,
        joint_id=joint.joint_id,
        parent_group_id=parent_group_id,
        child_group_id=child_group_id,
        parent_component_id=parent_component_id,
        child_component_id=child_component_id,
        joint_type=joint.joint_type,
    )


def build_kinematic_tree(*, assembly: AssemblyModel) -> KinematicTree:
    """Analyze rigid groups, tree edges, closure edges, and disconnected islands.

    This function is intentionally backend-independent.  It never starts a
    solver and does not turn an ungrounded component island into a valid root.
    Joints named by a Closure's ``source_joint_id`` or exact connector pair,
    plus joints with ``metadata["topology_role"] == "closure_edge"``, are
    reserved before traversal.  All other non-tree graph edges are classified
    as closures during the deterministic traversal.
    """

    component_groups, group_components = _topology_groups(assembly=assembly)
    group_ids = tuple(sorted(group_components))
    grounded_groups = {
        component_groups[ground.component_id]
        for ground in assembly.grounds
        if ground.component_id in component_groups
    }
    moving_joints = tuple(
        sorted(
            (joint for joint in assembly.joints if joint.joint_type != JointType.FIXED),
            key=lambda joint: joint.joint_id,
        )
    )
    explicit_closure_ids = {
        joint.joint_id
        for joint in moving_joints
        if joint.metadata.get("topology_role") == "closure_edge"
    }

    def endpoint_key(left: ConnectorRef, right: ConnectorRef) -> frozenset[tuple[str, str]]:
        return frozenset(
            {
                (left.component_id, left.connector_id),
                (right.component_id, right.connector_id),
            }
        )

    moving_by_id = {joint.joint_id: joint for joint in moving_joints}
    joints_by_endpoints: dict[frozenset[tuple[str, str]], list[Joint]] = {}
    for joint in moving_joints:
        joints_by_endpoints.setdefault(
            endpoint_key(joint.connector_a, joint.connector_b), []
        ).append(joint)
    for closure in assembly.closures:
        source_joint_id = closure.constraint.metadata.get("source_joint_id")
        if isinstance(source_joint_id, str) and source_joint_id in moving_by_id:
            explicit_closure_ids.add(source_joint_id)
            continue
        candidates = joints_by_endpoints.get(
            endpoint_key(
                closure.constraint.connector_a, closure.constraint.connector_b
            ),
            (),
        )
        if len(candidates) == 1:
            explicit_closure_ids.add(candidates[0].joint_id)
    adjacency: dict[str, list[tuple[str, Joint]]] = {group_id: [] for group_id in group_ids}
    internal_joints: list[Joint] = []
    for joint in moving_joints:
        left = component_groups.get(joint.connector_a.component_id)
        right = component_groups.get(joint.connector_b.component_id)
        if left is None or right is None:
            continue
        if left == right:
            internal_joints.append(joint)
            continue
        if joint.joint_id in explicit_closure_ids:
            continue
        adjacency[left].append((right, joint))
        adjacency[right].append((left, joint))
    for edges in adjacency.values():
        edges.sort(key=lambda item: (item[0], item[1].joint_id))

    parent_group: dict[str, str | None] = {group_id: None for group_id in group_ids}
    depth_by_group: dict[str, int] = {group_id: 0 for group_id in group_ids}
    visited: set[str] = set(grounded_groups)
    tree_edges: list[KinematicEdge] = []
    closure_edges: list[KinematicEdge] = []
    classified: set[str] = set(explicit_closure_ids)

    def traverse(starts: Iterable[str]) -> None:
        queue = list(sorted(starts))
        while queue:
            parent = queue.pop(0)
            for child, joint in adjacency.get(parent, ()):
                if joint.joint_id in classified:
                    continue
                if child not in visited:
                    visited.add(child)
                    parent_group[child] = parent
                    depth_by_group[child] = depth_by_group[parent] + 1
                    tree_edges.append(
                        _topology_edge(
                            joint=joint,
                            component_groups=component_groups,
                            parent_group_id=parent,
                            child_group_id=child,
                        )
                    )
                    classified.add(joint.joint_id)
                    queue.append(child)
                else:
                    closure_edges.append(
                        _topology_edge(
                            joint=joint,
                            component_groups=component_groups,
                            parent_group_id=parent,
                            child_group_id=child,
                        )
                    )
                    classified.add(joint.joint_id)

    traverse(grounded_groups)
    disconnected_group_ids = tuple(sorted(set(group_ids) - visited))
    # Analyze ungrounded islands as local forests so callers can inspect their
    # internal parent relations, while preserving the explicit disconnected
    # marker and excluding these groups from root_group_ids.
    for group_id in disconnected_group_ids:
        if group_id in visited:
            continue
        visited.add(group_id)
        traverse((group_id,))

    # Explicit closure edges are intentionally not traversed.  Give them a
    # stable orientation based on their authored connector order.
    for joint in moving_joints:
        if joint.joint_id not in explicit_closure_ids:
            continue
        left = component_groups.get(joint.connector_a.component_id)
        right = component_groups.get(joint.connector_b.component_id)
        if left is None or right is None:
            continue
        closure_edges.append(
            _topology_edge(
                joint=joint,
                component_groups=component_groups,
                parent_group_id=left,
                child_group_id=right,
            )
        )
        classified.add(joint.joint_id)
    for joint in internal_joints:
        closure_edges.append(
            _topology_edge(
                joint=joint,
                component_groups=component_groups,
                parent_group_id=component_groups[joint.connector_a.component_id],
                child_group_id=component_groups[joint.connector_b.component_id],
            )
        )
        classified.add(joint.joint_id)

    parent_component: dict[str, str | None] = {
        component_id: None for component_id in component_groups
    }
    parent_edge_by_group = {edge.child_group_id: edge for edge in tree_edges}
    for group_id, components in group_components.items():
        edge = parent_edge_by_group.get(group_id)
        if edge is None:
            continue
        for component_id in components:
            parent_component[component_id] = edge.parent_component_id
    parent_component_depth = {
        component_id: depth_by_group[component_groups[component_id]]
        for component_id in component_groups
    }
    return KinematicTree(
        root_group_ids=tuple(sorted(grounded_groups)),
        component_groups=component_groups,
        group_components=group_components,
        parent_component_id=parent_component,
        parent_group_id=parent_group,
        depth_by_component_id=parent_component_depth,
        tree_edges=tuple(sorted(tree_edges, key=lambda edge: edge.joint_id)),
        closure_edges=tuple(sorted(closure_edges, key=lambda edge: edge.joint_id)),
        disconnected_group_ids=disconnected_group_ids,
        grounded_group_ids=tuple(sorted(grounded_groups)),
    )


def _topology_issue(
    *,
    code: str,
    message: str,
    object_ids: tuple[str, ...] = (),
    severity: str = "error",
) -> SimIssue:
    return SimIssue(
        code=code,
        severity=severity,
        stage="assembly.topology",
        message=message,
        object_ids=object_ids,
        suggested_actions=("Correct the assembly topology and validate again.",),
    )


def validate_topology(*, assembly: AssemblyModel) -> ValidationResult:
    """Validate the graph boundary required before a kinematic solve."""

    tree = build_kinematic_tree(assembly=assembly)
    issues: list[SimIssue] = []
    component_ids = {component.component_id for component in assembly.components}
    invalid_grounds = tuple(
        ground.component_id for ground in assembly.grounds if ground.component_id not in component_ids
    )
    if invalid_grounds:
        issues.append(
            _topology_issue(
                code="topology.ground_missing_component",
                message="Ground references an unknown component.",
                object_ids=invalid_grounds,
            )
        )
    if not assembly.grounds:
        issues.append(
            _topology_issue(
                code="topology.no_ground",
                message="A kinematic assembly requires at least one Ground component.",
            )
        )
    if len(tree.root_group_ids) > 1:
        issues.append(
            _topology_issue(
                code="topology.multiple_roots",
                message="Ground components belong to multiple world-fixed rigid groups.",
                object_ids=tree.root_group_ids,
                severity="warning",
            )
        )
    if tree.disconnected_group_ids:
        issues.append(
            _topology_issue(
                code="topology.disconnected_island",
                message="One or more component groups are not reachable from Ground.",
                object_ids=tree.disconnected_group_ids,
            )
        )

    for joint in assembly.joints:
        endpoint_components = (joint.connector_a.component_id, joint.connector_b.component_id)
        if any(component_id not in component_ids for component_id in endpoint_components):
            issues.append(
                _topology_issue(
                    code="topology.unmapped_joint",
                    message="A movable Joint cannot be mapped because it references an unknown component.",
                    object_ids=(joint.joint_id, *endpoint_components),
                )
            )
            continue
        if any(
            assembly.get_connector(component_id=reference.component_id, connector_id=reference.connector_id)
            is None
            for reference in (joint.connector_a, joint.connector_b)
        ):
            issues.append(
                _topology_issue(
                    code="topology.unmapped_joint",
                    message="A Joint cannot be mapped because it references an unknown connector.",
                    object_ids=(joint.joint_id,),
                )
            )
            continue
        if joint.joint_type == JointType.FIXED:
            continue
        left_group = tree.component_groups.get(joint.connector_a.component_id)
        right_group = tree.component_groups.get(joint.connector_b.component_id)
        if left_group == right_group:
            issues.append(
                _topology_issue(
                    code="topology.internal_movable_joint",
                    message="A movable Joint is contained inside one fixed rigid group.",
                    object_ids=(joint.joint_id, left_group or ""),
                )
            )

    pair_to_joints: dict[tuple[str, str], list[str]] = {}
    for joint in assembly.joints:
        if joint.joint_type == JointType.FIXED:
            continue
        left = tree.component_groups.get(joint.connector_a.component_id)
        right = tree.component_groups.get(joint.connector_b.component_id)
        if left is None or right is None or left == right:
            continue
        pair_to_joints.setdefault(tuple(sorted((left, right))), []).append(joint.joint_id)
    duplicate_pairs = tuple(
        joint_id
        for pair in sorted(pair_to_joints)
        if len(pair_to_joints[pair]) > 1
        for joint_id in sorted(pair_to_joints[pair])
    )
    if duplicate_pairs:
        issues.append(
            _topology_issue(
                code="topology.duplicate_parent",
                message="Multiple movable joints connect the same rigid groups; the parent relation is ambiguous.",
                object_ids=duplicate_pairs,
            )
        )

    closures = tuple(assembly.closures)
    used_closure_ids: set[str] = set()

    def matches(edge: KinematicEdge, closure: Closure) -> bool:
        constraint = closure.constraint
        edge_joint = assembly.get_joint(joint_id=edge.joint_id)
        if edge_joint is None:
            return False
        refs = {
            (edge_joint.connector_a.component_id, edge_joint.connector_a.connector_id),
            (edge_joint.connector_b.component_id, edge_joint.connector_b.connector_id),
        }
        closure_refs = {
            (constraint.connector_a.component_id, constraint.connector_a.connector_id),
            (constraint.connector_b.component_id, constraint.connector_b.connector_id),
        }
        if refs == closure_refs:
            return True
        closure_groups = {
            tree.component_groups.get(constraint.connector_a.component_id),
            tree.component_groups.get(constraint.connector_b.component_id),
        }
        return closure_groups == {edge.parent_group_id, edge.child_group_id}

    for edge in tree.closure_edges:
        matching = next(
            (
                closure
                for closure in closures
                if closure.closure_id not in used_closure_ids and matches(edge, closure)
            ),
            None,
        )
        if matching is None:
            issues.append(
                _topology_issue(
                    code="topology.missing_closure",
                    message=f"Closure edge {edge.joint_id} has no matching Closure definition.",
                    object_ids=(edge.joint_id,),
                )
            )
        else:
            used_closure_ids.add(matching.closure_id)
    orphan_closures = tuple(
        closure.closure_id for closure in closures if closure.closure_id not in used_closure_ids
    )
    if orphan_closures:
        issues.append(
            _topology_issue(
                code="topology.orphan_closure",
                message="A Closure definition does not correspond to a detected closure edge.",
                object_ids=orphan_closures,
            )
        )
    if assembly.source_path:
        issues = [
            issue
            if issue.source_paths
            else replace(issue, source_paths=(assembly.source_path,))
            for issue in issues
        ]
    return ValidationResult(issues=tuple(issues), operation="validate_topology")


def create_assembly(*, assembly_id: str) -> AssemblyModel:
    return AssemblyModel(assembly_id=assembly_id)


def _append_unique(*, assembly: AssemblyModel, field_name: str, item: Any, id_name: str) -> AssemblyModel:
    items = getattr(assembly, field_name)
    item_id = getattr(item, id_name)
    if any(getattr(existing, id_name) == item_id for existing in items):
        _raise_validation(
            code="assembly.duplicate_id",
            message=f"Duplicate {id_name}: {item_id}",
            object_ids=(item_id,),
        )
    return replace(assembly, **{field_name: (*items, item)})


def add_part(*, assembly: AssemblyModel, part: Part) -> AssemblyModel:
    return _append_unique(assembly=assembly, field_name="parts", item=part, id_name="part_id")


def add_component(*, assembly: AssemblyModel, component: Component) -> AssemblyModel:
    return _append_unique(assembly=assembly, field_name="components", item=component, id_name="component_id")


def ground_component(*, assembly: AssemblyModel, component_id: str) -> AssemblyModel:
    if assembly.get_component(component_id=component_id) is None:
        _raise_validation(
            code="assembly.missing_component",
            message=f"Cannot ground unknown component: {component_id}",
            object_ids=(component_id,),
        )
    if any(item.component_id == component_id for item in assembly.grounds):
        return assembly
    return replace(assembly, grounds=(*assembly.grounds, Ground(component_id=component_id)))


def add_joint(*, assembly: AssemblyModel, joint: Joint) -> AssemblyModel:
    return _append_unique(assembly=assembly, field_name="joints", item=joint, id_name="joint_id")


def set_joint_limits(
    *, assembly: AssemblyModel, joint_id: str, lower: float, upper: float
) -> AssemblyModel:
    if assembly.get_joint(joint_id=joint_id) is None:
        _raise_validation(
            code="assembly.missing_joint",
            message=f"Cannot set limits on unknown joint: {joint_id}",
            object_ids=(joint_id,),
        )
    joints = tuple(
        replace(item, limit=JointLimit(lower=lower, upper=upper)) if item.joint_id == joint_id else item
        for item in assembly.joints
    )
    return replace(assembly, joints=joints)


def add_constraint(*, assembly: AssemblyModel, constraint: Constraint) -> AssemblyModel:
    return _append_unique(
        assembly=assembly, field_name="constraints", item=constraint, id_name="constraint_id"
    )


def add_coupling(*, assembly: AssemblyModel, coupling: Coupling) -> AssemblyModel:
    return _append_unique(
        assembly=assembly, field_name="couplings", item=coupling, id_name="coupling_id"
    )


def add_closure_constraint(*, assembly: AssemblyModel, constraint: Closure | Constraint) -> AssemblyModel:
    closure = (
        constraint
        if isinstance(constraint, Closure)
        else Closure(closure_id=constraint.constraint_id, constraint=constraint)
    )
    return _append_unique(
        assembly=assembly, field_name="closures", item=closure, id_name="closure_id"
    )


def exclude_collision_pair(
    *, assembly: AssemblyModel, component_a_id: str, component_b_id: str
) -> AssemblyModel:
    if component_a_id == component_b_id:
        _raise_validation(
            code="assembly.invalid_collision_pair",
            message="A collision exclusion requires two different components",
            object_ids=(component_a_id,),
        )
    missing = tuple(
        item
        for item in (component_a_id, component_b_id)
        if assembly.get_component(component_id=item) is None
    )
    if missing:
        _raise_validation(
            code="assembly.missing_component",
            message=f"Collision exclusion references unknown component(s): {', '.join(missing)}",
            object_ids=missing,
        )
    pair = tuple(sorted((component_a_id, component_b_id)))
    if pair in assembly.collision_exclusions:
        return assembly
    return replace(assembly, collision_exclusions=(*assembly.collision_exclusions, pair))


def _issue(*, code: str, message: str, object_ids: tuple[str, ...] = ()) -> Any:
    return SimIssue(
        code=code,
        severity="error",
        stage="assembly",
        message=message,
        object_ids=object_ids,
        suggested_actions=("Correct the referenced assembly object and validate again.",),
    )


def _validation_result(issues: Iterable[Any]) -> Any:
    return ValidationResult(issues=tuple(issues), operation="validate_assembly")


def validate_assembly(*, assembly: AssemblyModel) -> Any:
    issues: list[Any] = []

    def duplicate_issues(items: Iterable[Any], field_name: str) -> None:
        seen: set[str] = set()
        for item in items:
            value = getattr(item, field_name)
            if value in seen:
                issues.append(
                    _issue(
                        code="assembly.duplicate_id",
                        message=f"Duplicate {field_name}: {value}",
                        object_ids=(value,),
                    )
                )
            seen.add(value)

    duplicate_issues(assembly.parts, "part_id")
    duplicate_issues(assembly.components, "component_id")
    duplicate_issues(assembly.joints, "joint_id")
    duplicate_issues(assembly.constraints, "constraint_id")
    duplicate_issues(assembly.couplings, "coupling_id")
    duplicate_issues(assembly.closures, "closure_id")

    for part in assembly.parts:
        duplicate_issues(part.connectors, "connector_id")
        for kind, path in part.asset_paths.items():
            if not kind or not path:
                issues.append(
                    _issue(
                        code="assembly.invalid_asset",
                        message=f"Part {part.part_id} contains an empty asset reference",
                        object_ids=(part.part_id,),
                    )
                )

    part_ids = {item.part_id for item in assembly.parts}
    component_ids = {item.component_id for item in assembly.components}
    joint_ids = {item.joint_id for item in assembly.joints}
    for component in assembly.components:
        duplicate_issues(component.connectors, "connector_id")
        if component.part_id not in part_ids:
            issues.append(
                _issue(
                    code="assembly.missing_part",
                    message=f"Component {component.component_id} references unknown part {component.part_id}",
                    object_ids=(component.component_id, component.part_id),
                )
            )

    def validate_endpoints(owner_id: str, endpoints: Iterable[ConnectorRef]) -> None:
        for endpoint in endpoints:
            if endpoint.component_id not in component_ids:
                issues.append(
                    _issue(
                        code="assembly.missing_component",
                        message=f"{owner_id} references unknown component {endpoint.component_id}",
                        object_ids=(owner_id, endpoint.component_id),
                    )
                )
            elif assembly.get_connector(
                component_id=endpoint.component_id, connector_id=endpoint.connector_id
            ) is None:
                issues.append(
                    _issue(
                        code="assembly.missing_connector",
                        message=(
                            f"{owner_id} references unknown connector "
                            f"{endpoint.component_id}:{endpoint.connector_id}"
                        ),
                        object_ids=(owner_id, endpoint.component_id, endpoint.connector_id),
                    )
                )

    for joint in assembly.joints:
        validate_endpoints(joint.joint_id, (joint.connector_a, joint.connector_b))
        if joint.connector_a.component_id == joint.connector_b.component_id:
            issues.append(
                _issue(
                    code="assembly.self_joint",
                    message=f"Joint {joint.joint_id} connects a component to itself",
                    object_ids=(joint.joint_id, joint.connector_a.component_id),
                )
            )
    for constraint in assembly.constraints:
        validate_endpoints(constraint.constraint_id, (constraint.connector_a, constraint.connector_b))
    for closure in assembly.closures:
        validate_endpoints(
            closure.closure_id,
            (closure.constraint.connector_a, closure.constraint.connector_b),
        )
    for coupling in assembly.couplings:
        for joint_id in (coupling.joint_a_id, coupling.joint_b_id):
            if joint_id not in joint_ids:
                issues.append(
                    _issue(
                        code="assembly.missing_joint",
                        message=f"Coupling {coupling.coupling_id} references unknown joint {joint_id}",
                        object_ids=(coupling.coupling_id, joint_id),
                    )
                )
    for ground in assembly.grounds:
        if ground.component_id not in component_ids:
            issues.append(
                _issue(
                    code="assembly.missing_component",
                    message=f"Ground references unknown component {ground.component_id}",
                    object_ids=(ground.component_id,),
                )
            )
    for component_a_id, component_b_id in assembly.collision_exclusions:
        missing = tuple(value for value in (component_a_id, component_b_id) if value not in component_ids)
        if missing:
            issues.append(
                _issue(
                    code="assembly.missing_component",
                    message="Collision exclusion references unknown component",
                    object_ids=missing,
                )
            )
    return _validation_result(issues)


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_plain(item) for item in value]
    if is_dataclass(value):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    return value


def assembly_to_dict(*, assembly: AssemblyModel) -> dict[str, Any]:
    return {
        "schema_version": "kincheckapi.assembly/1.0",
        "assembly_id": assembly.assembly_id,
        "display_name": assembly.display_name,
        "source_path": assembly.source_path,
        "parts": [_plain(item) for item in assembly.parts],
        "components": [_plain(item) for item in assembly.components],
        "joints": [_plain(item) for item in assembly.joints],
        "constraints": [_plain(item) for item in assembly.constraints],
        "couplings": [_plain(item) for item in assembly.couplings],
        "closures": [_plain(item) for item in assembly.closures],
        "grounds": [_plain(item) for item in assembly.grounds],
        "collision_exclusions": [_plain(item) for item in assembly.collision_exclusions],
        "metadata": _plain(assembly.metadata),
    }


def _pose_from_dict(data: Mapping[str, Any] | None) -> Pose:
    value = data or {}
    return Pose(
        position_m=tuple(float(item) for item in value.get("position_m", (0.0, 0.0, 0.0))),
        orientation_xyzw=tuple(
            float(item) for item in value.get("orientation_xyzw", (0.0, 0.0, 0.0, 1.0))
        ),
    )


def _connector_from_dict(data: Mapping[str, Any]) -> Connector:
    return Connector(
        connector_id=str(data["connector_id"]),
        pose=_pose_from_dict(data.get("pose")),
        display_name=data.get("display_name"),
        metadata=data.get("metadata", {}),
    )


def _endpoint_from_dict(data: Mapping[str, Any]) -> ConnectorRef:
    return ConnectorRef(component_id=str(data["component_id"]), connector_id=str(data["connector_id"]))


def assembly_from_dict(*, data: Mapping[str, Any]) -> AssemblyModel:
    parts = tuple(
        Part(
            part_id=str(item["part_id"]),
            connectors=tuple(_connector_from_dict(value) for value in item.get("connectors", ())),
            asset_paths=item.get("asset_paths", {}),
            asset_hashes=item.get("asset_hashes", {}),
            display_name=item.get("display_name"),
            source_path=item.get("source_path"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("parts", ())
    )
    components = tuple(
        Component(
            component_id=str(item["component_id"]),
            part_id=str(item["part_id"]),
            initial_pose=_pose_from_dict(item.get("initial_pose")),
            connectors=tuple(_connector_from_dict(value) for value in item.get("connectors", ())),
            display_name=item.get("display_name"),
            source_path=item.get("source_path"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("components", ())
    )
    joints = tuple(
        Joint(
            joint_id=str(item["joint_id"]),
            joint_type=item["joint_type"],
            connector_a=_endpoint_from_dict(item["connector_a"]),
            connector_b=_endpoint_from_dict(item["connector_b"]),
            limit=(
                JointLimit(lower=float(item["limit"]["lower"]), upper=float(item["limit"]["upper"]))
                if item.get("limit") is not None
                else None
            ),
            display_name=item.get("display_name"),
            source_path=item.get("source_path"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("joints", ())
    )
    constraints = tuple(
        Constraint(
            constraint_id=str(item["constraint_id"]),
            connector_a=_endpoint_from_dict(item["connector_a"]),
            connector_b=_endpoint_from_dict(item["connector_b"]),
            constraint_type=str(item.get("constraint_type", "coincident")),
            display_name=item.get("display_name"),
            source_path=item.get("source_path"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("constraints", ())
    )
    couplings = tuple(
        Coupling(
            coupling_id=str(item["coupling_id"]),
            coupling_type=item["coupling_type"],
            joint_a_id=str(item["joint_a_id"]),
            joint_b_id=str(item["joint_b_id"]),
            ratio=float(item["ratio"]),
            phase_offset=float(item.get("phase_offset", 0.0)),
            display_name=item.get("display_name"),
            source_path=item.get("source_path"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("couplings", ())
    )
    closures = tuple(
        Closure(
            closure_id=str(item["closure_id"]),
            constraint=Constraint(
                constraint_id=str(item["constraint"]["constraint_id"]),
                connector_a=_endpoint_from_dict(item["constraint"]["connector_a"]),
                connector_b=_endpoint_from_dict(item["constraint"]["connector_b"]),
                constraint_type=str(item["constraint"].get("constraint_type", "coincident")),
                display_name=item["constraint"].get("display_name"),
                source_path=item["constraint"].get("source_path"),
                metadata=item["constraint"].get("metadata", {}),
            ),
            position_tolerance_m=float(item.get("position_tolerance_m", 1e-6)),
            orientation_tolerance_rad=float(item.get("orientation_tolerance_rad", 1e-6)),
        )
        for item in data.get("closures", ())
    )
    assembly = AssemblyModel(
        assembly_id=str(data["assembly_id"]),
        parts=parts,
        components=components,
        joints=joints,
        constraints=constraints,
        couplings=couplings,
        closures=closures,
        grounds=tuple(Ground(component_id=str(item["component_id"])) for item in data.get("grounds", ())),
        collision_exclusions=tuple(tuple(item) for item in data.get("collision_exclusions", ())),
        display_name=data.get("display_name"),
        source_path=data.get("source_path"),
        metadata=data.get("metadata", {}),
    )
    return assembly


def write_assembly(*, assembly: AssemblyModel, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(assembly_to_dict(assembly=assembly), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_assembly(*, path: str | Path) -> AssemblyModel:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        if data.get("schema_version") != "kincheckapi.assembly/1.0":
            _raise_validation(
                code="assembly.unsupported_schema",
                message=f"Unsupported assembly schema: {data.get('schema_version')!r}",
                source_path=str(source),
            )
        assembly = assembly_from_dict(data=data)
    except AssemblyValidationError:
        raise
    except Exception as error:
        _raise_validation(
            code="assembly.read_failed",
            message="The assembly JSON could not be read or reconstructed.",
            source_path=str(source),
            cause=error,
        )
    result = validate_assembly(assembly=assembly)
    passed = getattr(result, "passed", getattr(result, "valid", bool(result)))
    if not passed:
        _raise_validation(
            code="assembly.validation_failed",
            message="Assembly JSON contains invalid references or topology",
            source_path=str(source),
            report=result,
        )
    return assembly


def _raise_validation(
    *,
    code: str,
    message: str,
    object_ids: tuple[str, ...] = (),
    source_path: str | None = None,
    report: Any = None,
    cause: BaseException | None = None,
) -> None:
    if report is None:
        report = ValidationResult(
            operation="read_assembly" if code == "assembly.read_failed" else "validate_assembly",
            issues=(
                SimIssue(
                    code=code,
                    severity="error",
                    stage="assembly",
                    message=message,
                    object_ids=object_ids,
                    source_paths=(source_path,) if source_path else (),
                    evidence=(
                        (Evidence(key="native_error_type", actual=type(cause).__name__),)
                        if cause is not None
                        else ()
                    ),
                    suggested_actions=(
                        "Correct the referenced assembly object and validate again.",
                    ),
                ),
            ),
        )
    error = AssemblyValidationError(
        code=code,
        message=message,
        object_ids=object_ids,
        source_paths=(source_path,) if source_path else (),
        report=report,
        suggested_actions=("Correct the referenced assembly object and validate again.",),
    )
    if cause is not None:
        raise error from cause
    raise error


__all__ = [
    "AssemblyModel",
    "Closure",
    "Component",
    "Connector",
    "ConnectorRef",
    "Constraint",
    "Coupling",
    "CouplingType",
    "Ground",
    "Joint",
    "JointLimit",
    "JointType",
    "KinematicEdge",
    "KinematicTree",
    "Limit",
    "Part",
    "Pose",
    "add_closure_constraint",
    "add_component",
    "add_constraint",
    "add_coupling",
    "add_joint",
    "add_part",
    "assembly_from_dict",
    "assembly_to_dict",
    "create_assembly",
    "build_kinematic_tree",
    "exclude_collision_pair",
    "ground_component",
    "read_assembly",
    "set_joint_limits",
    "validate_assembly",
    "validate_topology",
    "write_assembly",
]
