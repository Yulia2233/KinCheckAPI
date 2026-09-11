"""Small, backend-independent geometry helpers for kinematics.

The physics backend is intentionally not used here.  A single authored pose is
enough to propagate a tree, and doing that in Python makes Jacobian and
position-solve diagnostics deterministic and testable without simulator state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from .assembly import AssemblyModel, Closure, Joint, JointType, build_kinematic_tree
from .diagnostics import AgentReadableResult, Evidence, SimIssue
from .kinematics_conventions import child_motion_sign
from .pose import Pose, compose_pose, inverse_pose, relative_pose, rotate_vector
from .result import ConstraintResidual


def _qmul(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float, float]:
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return (
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
        lw * rw - lx * rx - ly * ry - lz * rz,
    )


def _qconj(value: Sequence[float]) -> tuple[float, float, float, float]:
    x, y, z, w = value
    return (-x, -y, -z, w)


def _axis_angle(axis: Sequence[float], angle: float) -> Pose:
    norm = math.sqrt(sum(float(value) ** 2 for value in axis))
    if norm <= 1e-15 or abs(angle) <= 1e-15:
        return Pose()
    x, y, z = (float(value) / norm for value in axis)
    half = angle * 0.5
    scale = math.sin(half)
    return Pose(orientation_xyzw=(x * scale, y * scale, z * scale, math.cos(half)))


def _orientation_vector(actual: Pose, expected: Pose) -> tuple[float, float, float]:
    """Return a signed, small-angle orientation residual in world coordinates."""

    qa = actual.orientation_xyzw
    qe = expected.orientation_xyzw
    # q_expected * q_actual^-1 is the left/world rotation that maps the
    # actual orientation to the expected orientation.  Its vector part is
    # therefore already expressed in world coordinates.
    q = _qmul(qe, _qconj(qa))
    if q[3] < 0.0:
        q = tuple(-value for value in q)  # type: ignore[assignment]
    vector = np.asarray(q[:3], dtype=float)
    scale = 2.0
    if abs(q[3]) > 1e-12:
        scale = 2.0 * math.atan2(float(np.linalg.norm(vector)), q[3]) / float(np.linalg.norm(vector)) if np.linalg.norm(vector) > 1e-15 else 2.0
    return tuple(float(value * scale) for value in vector)


def _axis_cross(actual_a: Pose, actual_b: Pose) -> tuple[float, float, float]:
    axis_a = np.asarray(rotate_vector(pose=actual_a, vector=(0.0, 0.0, 1.0)), dtype=float)
    axis_b = np.asarray(rotate_vector(pose=actual_b, vector=(0.0, 0.0, 1.0)), dtype=float)
    return tuple(float(value) for value in np.cross(axis_a, axis_b))


@dataclass(frozen=True, slots=True, kw_only=True)
class JacobianOptions:
    finite_difference_step: float = 1e-7
    rank_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        if not math.isfinite(self.finite_difference_step) or self.finite_difference_step <= 0.0:
            raise ValueError("finite_difference_step must be finite and positive")
        if not math.isfinite(self.rank_tolerance) or self.rank_tolerance <= 0.0:
            raise ValueError("rank_tolerance must be finite and positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class JacobianResult(AgentReadableResult):
    target_component_id: str
    target_connector_id: str | None
    joint_ids: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    rank: int
    singular_values: tuple[float, ...]
    condition_number: float | None
    units: tuple[str, ...] = ("m/(rad|m)",) * 3 + ("rad/(rad|m)",) * 3
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(item.severity == "error" for item in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "compute_jacobian",
            "status": "passed" if self.passed else "failed",
            "target_component_id": self.target_component_id,
            "target_connector_id": self.target_connector_id,
            "joint_ids": list(self.joint_ids),
            "matrix": [list(row) for row in self.matrix],
            "rank": self.rank,
            "singular_values": list(self.singular_values),
            "condition_number": self.condition_number,
            "units": list(self.units),
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class MobilityReport(AgentReadableResult):
    nominal_dofs: int
    effective_dofs: int
    joint_dofs: Mapping[str, int]
    constraint_rank: int
    constraint_ids: tuple[str, ...] = ()
    singular_values: tuple[float, ...] = ()
    issues: tuple[SimIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(item.severity == "error" for item in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "operation": "analyze_mobility",
            "status": "passed" if self.passed else "failed",
            "nominal_dofs": self.nominal_dofs,
            "effective_dofs": self.effective_dofs,
            "joint_dofs": dict(self.joint_dofs),
            "constraint_rank": self.constraint_rank,
            "constraint_ids": list(self.constraint_ids),
            "singular_values": list(self.singular_values),
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class PoseTarget:
    component_id: str
    pose: Pose
    connector_id: str | None = None
    position_tolerance_m: float | None = None
    orientation_tolerance_rad: float | None = None

    def __post_init__(self) -> None:
        if not self.component_id:
            raise ValueError("PoseTarget component_id must not be empty")
        for name in ("position_tolerance_m", "orientation_tolerance_rad"):
            value = getattr(self, name)
            if value is not None and (
                not math.isfinite(value) or value <= 0.0
            ):
                raise ValueError(
                    "PoseTarget tolerances must be positive finite numbers"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "connector_id": self.connector_id,
            "pose": {
                "position_m": list(self.pose.position_m),
                "orientation_xyzw": list(self.pose.orientation_xyzw),
            },
            "position_tolerance_m": self.position_tolerance_m,
            "orientation_tolerance_rad": self.orientation_tolerance_rad,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class PositionSolveOptions:
    max_iterations: int = 100
    position_tolerance_m: float = 1e-7
    orientation_tolerance_rad: float = 1e-7
    step_tolerance: float = 1e-9
    damping: float = 1e-6
    finite_difference_step: float = 1e-7
    rank_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        if (
            not isinstance(self.max_iterations, int)
            or isinstance(self.max_iterations, bool)
            or self.max_iterations < 1
        ):
            raise ValueError("max_iterations must be positive")
        for name in ("position_tolerance_m", "orientation_tolerance_rad", "step_tolerance", "damping", "finite_difference_step", "rank_tolerance"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")


def _group_representatives(assembly: AssemblyModel, tree: Any) -> Mapping[str, Pose]:
    return MappingProxyType({
        group_id: assembly.get_component(component_id=members[0]).initial_pose
        for group_id, members in tree.group_components.items()
        if assembly.get_component(component_id=members[0]) is not None
    })


def _forward_group_poses(assembly: AssemblyModel, joint_positions: Mapping[str, float]) -> Mapping[str, Pose]:
    tree = build_kinematic_tree(assembly=assembly)
    reps = _group_representatives(assembly, tree)
    joints = {joint.joint_id: joint for joint in assembly.joints}
    children: dict[str, list[Any]] = {}
    for edge in tree.tree_edges:
        children.setdefault(edge.parent_group_id, []).append(edge)
    current: dict[str, Pose] = {}
    def visit(group_id: str, pose: Pose) -> None:
        if group_id in current:
            return
        current[group_id] = pose
        for edge in sorted(children.get(group_id, ()), key=lambda item: item.joint_id):
            joint = joints[edge.joint_id]
            child_initial = reps[edge.child_group_id]
            parent_initial = reps[edge.parent_group_id]
            base_child = compose_pose(parent=pose, child=relative_pose(parent=parent_initial, child=child_initial))
            endpoint = joint.connector_a if tree.component_groups[joint.connector_a.component_id] == edge.parent_group_id else joint.connector_b
            endpoint_component = assembly.get_component(component_id=endpoint.component_id)
            endpoint_connector = assembly.get_connector(component_id=endpoint.component_id, connector_id=endpoint.connector_id)
            if endpoint_component is None or endpoint_connector is None:
                continue
            endpoint_initial = compose_pose(parent=endpoint_component.initial_pose, child=endpoint_connector.pose)
            endpoint_relative = relative_pose(parent=parent_initial, child=endpoint_initial)
            endpoint_current = compose_pose(parent=pose, child=endpoint_relative)
            axis = rotate_vector(pose=endpoint_current, vector=(0.0, 0.0, 1.0))
            value = float(joint_positions.get(joint.joint_id, 0.0))
            value *= child_motion_sign(
                joint=joint,
                child_group_id=edge.child_group_id,
                component_groups=tree.component_groups,
            )
            if joint.joint_type == JointType.REVOLUTE:
                rotation = _axis_angle(axis, value)
                pivot = Pose(position_m=endpoint_current.position_m)
                delta = compose_pose(parent=pivot, child=compose_pose(parent=rotation, child=inverse_pose(pose=pivot)))
            elif joint.joint_type == JointType.PRISMATIC:
                delta = Pose(position_m=tuple(axis[index] * value for index in range(3)))
            else:
                delta = Pose()
            visit(edge.child_group_id, compose_pose(parent=delta, child=base_child))
    roots = tree.root_group_ids or tuple(sorted(tree.group_components))
    for root in sorted(roots):
        visit(root, reps[root])
    for group_id in sorted(reps):
        visit(group_id, reps[group_id])
    return MappingProxyType(current)


def forward_component_poses(assembly: AssemblyModel, joint_positions: Mapping[str, float]) -> Mapping[str, Pose]:
    tree = build_kinematic_tree(assembly=assembly)
    groups = _forward_group_poses(assembly, joint_positions)
    reps = _group_representatives(assembly, tree)
    return MappingProxyType({
        component.component_id: compose_pose(
            parent=groups[tree.component_groups[component.component_id]],
            child=relative_pose(parent=reps[tree.component_groups[component.component_id]], child=component.initial_pose),
        )
        for component in assembly.components
    })


def forward_connector_poses(assembly: AssemblyModel, joint_positions: Mapping[str, float]) -> Mapping[tuple[str, str], Pose]:
    component_poses = forward_component_poses(assembly, joint_positions)
    result: dict[tuple[str, str], Pose] = {}
    for component in assembly.components:
        for connector in tuple(assembly.get_part(part_id=component.part_id).connectors if assembly.get_part(part_id=component.part_id) else ()) + tuple(component.connectors):
            result[(component.component_id, connector.connector_id)] = compose_pose(parent=component_poses[component.component_id], child=connector.pose)
    return MappingProxyType(result)


def _constraint_endpoint_joint_types(
    assembly: AssemblyModel, constraint: Any, tree: Any
) -> tuple[JointType, JointType]:
    """Return the scalar tree type supporting each transmission endpoint."""

    modes: list[JointType] = []
    for reference in (constraint.connector_a, constraint.connector_b):
        group_id = tree.component_groups.get(reference.component_id)
        edge = next(
            (item for item in tree.tree_edges if item.child_group_id == group_id),
            None,
        )
        modes.append(edge.joint_type if edge is not None else JointType.REVOLUTE)
    return modes[0], modes[1]


def _transmission_issues(
    assembly: AssemblyModel, tree: Any, *, stage: str
) -> tuple[SimIssue, ...]:
    issues: list[SimIssue] = []
    for constraint in assembly.constraints:
        if constraint.constraint_type not in {"gear", "belt", "rack_pinion"}:
            continue
        radius_keys = (
            ("pitch_radius_a", "pitch_radius_b", "pitch_radius")
            if constraint.constraint_type in {"gear", "rack_pinion"}
            else ("pulley_radius_a", "pulley_radius_b", "pulley_radius")
        )
        endpoint_keys = radius_keys[:2]
        generic_key = radius_keys[2]
        for key in endpoint_keys:
            raw_value = constraint.metadata.get(key)
            if raw_value is None:
                raw_value = constraint.metadata.get(generic_key)
            if raw_value is None:
                issues.append(
                    SimIssue(
                        code="KINCHECK-KIN-COUPLING-RADIUS-INVALID",
                        severity="error",
                        stage=stage,
                        message="A transmission relation requires a radius for each endpoint.",
                        object_ids=(constraint.constraint_id,),
                        evidence=(Evidence(key=key, actual=None, expected="> 0"),),
                        suggested_actions=("Provide endpoint radii or one shared positive SI radius.",),
                    )
                )
                continue
            try:
                radius = float(raw_value)
            except (TypeError, ValueError):
                radius = math.nan
            if not math.isfinite(radius) or radius <= 0.0:
                issues.append(
                    SimIssue(
                        code="KINCHECK-KIN-COUPLING-RADIUS-INVALID",
                        severity="error",
                        stage=stage,
                        message="A transmission relation requires a finite positive radius.",
                        object_ids=(constraint.constraint_id,),
                        evidence=(Evidence(key=key, actual=raw_value, expected="> 0"),),
                        suggested_actions=("Provide a positive SI radius in the relation metadata.",),
                    )
                )
        if constraint.constraint_type == "rack_pinion":
            mode_a, mode_b = _constraint_endpoint_joint_types(assembly, constraint, tree)
            if {mode_a, mode_b} != {JointType.REVOLUTE, JointType.PRISMATIC}:
                issues.append(
                    SimIssue(
                        code="KINCHECK-KIN-COUPLING-ENDPOINT-TYPE-MISMATCH",
                        severity="error",
                        stage=stage,
                        message="A rack_pinion relation requires one revolute and one prismatic endpoint.",
                        object_ids=(constraint.constraint_id,),
                        evidence=(Evidence(key="endpoint_joint_types", actual=(mode_a.value, mode_b.value), expected=("revolute", "prismatic")),),
                        suggested_actions=("Connect rack_pinion to one rotational and one linear Joint.",),
                    )
                )
    return tuple(issues)


def _target_pose(assembly: AssemblyModel, target_component_id: str, target_connector_id: str | None, joint_positions: Mapping[str, float]) -> Pose:
    if target_connector_id is None:
        return forward_component_poses(assembly, joint_positions)[target_component_id]
    return forward_connector_poses(assembly, joint_positions)[(target_component_id, target_connector_id)]


def _constraint_vector(assembly: AssemblyModel, joint_positions: Mapping[str, float], pose_targets: Sequence[PoseTarget] = ()) -> tuple[np.ndarray, tuple[str, ...], Mapping[str, tuple[float, float]]]:
    connectors = forward_connector_poses(assembly, joint_positions)
    initial_connectors = forward_connector_poses(assembly, {})
    tree = build_kinematic_tree(assembly=assembly)
    component_poses = forward_component_poses(assembly, joint_positions)
    initial_component_poses = forward_component_poses(assembly, {})
    values: list[float] = []
    ids: list[str] = []
    norms: dict[str, tuple[float, float]] = {}
    for closure in sorted(assembly.closures, key=lambda item: item.closure_id):
        ref_a, ref_b = closure.constraint.connector_a, closure.constraint.connector_b
        pose_a, pose_b = connectors.get((ref_a.component_id, ref_a.connector_id)), connectors.get((ref_b.component_id, ref_b.connector_id))
        if pose_a is None or pose_b is None:
            continue
        position = tuple(pose_b.position_m[index] - pose_a.position_m[index] for index in range(3))
        orientation = _axis_cross(pose_a, pose_b) if closure.constraint.metadata.get("axis_alignment_required") else _orientation_vector(pose_b, pose_a)
        values.extend((*position, *orientation))
        ids.extend((closure.closure_id,) * 6)
        norms[closure.closure_id] = (math.dist(pose_a.position_m, pose_b.position_m), float(np.linalg.norm(orientation)))
    # Gear and belt rows are expressed as signed angular displacement from
    # the authored pose.  This is the same displacement convention used by
    # the backend compiler and keeps imported phase offsets out of the residual.
    for constraint in sorted(assembly.constraints, key=lambda item: item.constraint_id):
        if constraint.constraint_type not in {"gear", "belt", "rack_pinion"}:
            continue
        ref_a, ref_b = constraint.connector_a, constraint.connector_b
        current_a = connectors.get((ref_a.component_id, ref_a.connector_id))
        current_b = connectors.get((ref_b.component_id, ref_b.connector_id))
        initial_a = initial_connectors.get((ref_a.component_id, ref_a.connector_id))
        initial_b = initial_connectors.get((ref_b.component_id, ref_b.connector_id))
        if current_a is None or current_b is None or initial_a is None or initial_b is None:
            continue
        def signed_turn(initial: Pose, current: Pose) -> float:
            # ``relative_pose`` expresses the rotation in the initial
            # Connector frame. Its local Z component is therefore the signed
            # rotation about the authored joint axis, regardless of world
            # orientation.
            x, y, z, w = relative_pose(parent=initial, child=current).orientation_xyzw
            vector = np.asarray((x, y, z), dtype=float)
            signed = float(vector[2])
            return 2.0 * math.atan2(signed, w)
        def signed_translation(initial: Pose, current: Pose) -> float:
            # A prismatic connector's local z axis is the declared motion axis.
            # Project the world displacement onto that authored axis instead of
            # assuming the axis is always world Z (rack guides commonly use X).
            axis = np.asarray(
                rotate_vector(pose=initial, vector=(0.0, 0.0, 1.0)),
                dtype=float,
            )
            displacement = np.asarray(
                tuple(
                    current.position_m[index] - initial.position_m[index]
                    for index in range(3)
                ),
                dtype=float,
            )
            return float(np.dot(displacement, axis))
        radius_a = float(constraint.metadata.get("pitch_radius_a") or constraint.metadata.get("pulley_radius_a") or constraint.metadata.get("pitch_radius") or 1.0)
        radius_b = float(constraint.metadata.get("pitch_radius_b") or constraint.metadata.get("pulley_radius_b") or constraint.metadata.get("pitch_radius") or 1.0)
        direction_b = 1.0 if constraint.constraint_type == "gear" else -1.0
        group_a = tree.component_groups.get(ref_a.component_id)
        group_b = tree.component_groups.get(ref_b.component_id)
        mode_a, mode_b = _constraint_endpoint_joint_types(assembly, constraint, tree)
        if constraint.constraint_type == "rack_pinion":
            if {mode_a, mode_b} != {JointType.REVOLUTE, JointType.PRISMATIC}:
                continue
            value = (
                signed_translation(initial_a, current_a)
                if mode_a == JointType.PRISMATIC
                else radius_a * signed_turn(initial_a, current_a)
            )
            value += direction_b * (
                signed_translation(initial_b, current_b)
                if mode_b == JointType.PRISMATIC
                else radius_b * signed_turn(initial_b, current_b)
            )
        else:
            value = radius_a * signed_turn(initial_a, current_a) + direction_b * radius_b * signed_turn(initial_b, current_b)
        depth_a = tree.depth_by_component_id.get(ref_a.component_id, 0)
        depth_b = tree.depth_by_component_id.get(ref_b.component_id, 0)
        child_group = group_a if depth_a > depth_b else group_b
        support_group = tree.parent_group_id.get(child_group) if child_group is not None else None
        if support_group is not None:
            support_component_id = tree.group_components[support_group][0]
            support_component = assembly.get_component(component_id=support_component_id)
            if support_component is not None:
                current_support = component_poses[support_component_id]
                initial_support = initial_component_poses[support_component_id]
                support_turn = signed_turn(initial_support, current_support)
                value -= (radius_a + direction_b * radius_b) * support_turn
        values.append(value)
        ids.append(constraint.constraint_id)
        norms[constraint.constraint_id] = (abs(value), 0.0)
    for coupling in sorted(assembly.couplings, key=lambda item: item.coupling_id):
        value = float(joint_positions.get(coupling.joint_a_id, 0.0)) - float(coupling.ratio) * float(joint_positions.get(coupling.joint_b_id, 0.0)) - float(coupling.phase_offset)
        values.append(value)
        ids.append(coupling.coupling_id)
        norms[coupling.coupling_id] = (abs(value), 0.0)
    for index, target in enumerate(pose_targets):
        actual = _target_pose(assembly, target.component_id, target.connector_id, joint_positions)
        position = tuple(target.pose.position_m[i] - actual.position_m[i] for i in range(3))
        orientation = _orientation_vector(actual, target.pose)
        values.extend((*position, *orientation))
        ids.extend((f"pose_target:{index}",) * 6)
        norms[f"pose_target:{index}"] = (math.dist(actual.position_m, target.pose.position_m), float(np.linalg.norm(orientation)))
    return np.asarray(values, dtype=float), tuple(ids), MappingProxyType(norms)


def _constraint_jacobian(assembly: AssemblyModel, joint_positions: Mapping[str, float], joint_ids: Sequence[str], step: float, pose_targets: Sequence[PoseTarget] = ()) -> tuple[np.ndarray, tuple[str, ...]]:
    base, ids, _ = _constraint_vector(assembly, joint_positions, pose_targets)
    matrix = np.zeros((len(base), len(joint_ids)), dtype=float)
    for column, joint_id in enumerate(joint_ids):
        plus = dict(joint_positions); plus[joint_id] = plus.get(joint_id, 0.0) + step
        minus = dict(joint_positions); minus[joint_id] = minus.get(joint_id, 0.0) - step
        p, _, _ = _constraint_vector(assembly, plus, pose_targets)
        m, _, _ = _constraint_vector(assembly, minus, pose_targets)
        if len(p) == len(base) and len(m) == len(base):
            matrix[:, column] = (p - m) / (2.0 * step)
    return matrix, ids


def _algebraic_constraint_rows(assembly: AssemblyModel, joint_ids: Sequence[str]) -> Mapping[str, np.ndarray]:
    """Build exact rows for mesh and coupling equations from the kinematic tree."""

    tree = build_kinematic_tree(assembly=assembly)
    variable_by_group = {edge.child_group_id: edge.joint_id for edge in tree.tree_edges}
    parents = dict(tree.parent_group_id)
    grounded = set(tree.grounded_group_ids)
    world: dict[str, dict[str, float]] = {}
    def visit(group_id: str) -> dict[str, float]:
        if group_id in world:
            return world[group_id]
        values: dict[str, float] = {}
        parent = parents.get(group_id)
        if parent is not None:
            values.update(visit(parent))
        if group_id not in grounded and group_id in variable_by_group:
            values[variable_by_group[group_id]] = values.get(variable_by_group[group_id], 0.0) + 1.0
        world[group_id] = values
        return values
    for group_id in sorted(tree.group_components):
        visit(group_id)
    joint_expr: dict[str, dict[str, float]] = {}
    for joint in assembly.joints:
        group_a = tree.component_groups.get(joint.connector_a.component_id)
        group_b = tree.component_groups.get(joint.connector_b.component_id)
        if group_a is None or group_b is None:
            continue
        values: dict[str, float] = {}
        for key, value in visit(group_b).items():
            values[key] = values.get(key, 0.0) + value
        for key, value in visit(group_a).items():
            values[key] = values.get(key, 0.0) - value
        joint_expr[joint.joint_id] = values
    rows: dict[str, np.ndarray] = {}
    for constraint in assembly.constraints:
        if constraint.constraint_type not in {"gear", "belt", "rack_pinion"}:
            continue
        group_a = tree.component_groups.get(constraint.connector_a.component_id)
        group_b = tree.component_groups.get(constraint.connector_b.component_id)
        if group_a is None or group_b is None:
            continue
        radius_a = float(constraint.metadata.get("pitch_radius_a") or constraint.metadata.get("pulley_radius_a") or constraint.metadata.get("pitch_radius") or 1.0)
        radius_b = float(constraint.metadata.get("pitch_radius_b") or constraint.metadata.get("pulley_radius_b") or constraint.metadata.get("pitch_radius") or 1.0)
        direction_b = 1.0 if constraint.constraint_type == "gear" else -1.0
        mode_a, mode_b = _constraint_endpoint_joint_types(assembly, constraint, tree)
        if constraint.constraint_type == "rack_pinion" and {mode_a, mode_b} != {JointType.REVOLUTE, JointType.PRISMATIC}:
            continue
        coefficient_a = 1.0 if constraint.constraint_type == "rack_pinion" and mode_a == JointType.PRISMATIC else radius_a
        coefficient_b = direction_b if constraint.constraint_type == "rack_pinion" and mode_b == JointType.PRISMATIC else direction_b * radius_b
        values: dict[str, float] = {}
        for key, value in world[group_a].items():
            values[key] = values.get(key, 0.0) + coefficient_a * value
        for key, value in world[group_b].items():
            values[key] = values.get(key, 0.0) + coefficient_b * value
        # A mesh attached to a child group is measured in the moving support
        # frame, matching the backend's carrier-relative expression.
        child = group_a if tree.depth_by_component_id.get(constraint.connector_a.component_id, 0) > tree.depth_by_component_id.get(constraint.connector_b.component_id, 0) else group_b
        support = parents.get(child)
        if support is not None:
            for key, value in world.get(support, {}).items():
                values[key] = values.get(key, 0.0) - (coefficient_a + coefficient_b) * value
        rows[constraint.constraint_id] = np.asarray([values.get(joint_id, 0.0) for joint_id in joint_ids], dtype=float)
    for coupling in assembly.couplings:
        values: dict[str, float] = {}
        for key, value in joint_expr.get(coupling.joint_a_id, {}).items():
            values[key] = values.get(key, 0.0) + value
        for key, value in joint_expr.get(coupling.joint_b_id, {}).items():
            values[key] = values.get(key, 0.0) - float(coupling.ratio) * value
        rows[coupling.coupling_id] = np.asarray([values.get(joint_id, 0.0) for joint_id in joint_ids], dtype=float)
    return MappingProxyType(rows)


def compute_jacobian(*, assembly: AssemblyModel, joint_positions: Mapping[str, float], target_component_id: str | None = None, target_connector_id: str | None = None, options: JacobianOptions | None = None) -> JacobianResult:
    options = options or JacobianOptions()
    if not target_component_id:
        raise ValueError("target_component_id is required")
    if assembly.get_component(component_id=target_component_id) is None:
        raise ValueError(f"Unknown target Component: {target_component_id}")
    if target_connector_id is not None and (target_component_id, target_connector_id) not in forward_connector_poses(assembly, {}).keys():
        raise ValueError(f"Unknown target Connector: {target_component_id}/{target_connector_id}")
    tree = build_kinematic_tree(assembly=assembly)
    joint_ids = tuple(sorted(edge.joint_id for edge in tree.tree_edges))
    matrix = np.zeros((6, len(joint_ids)), dtype=float)
    for column, joint_id in enumerate(joint_ids):
        plus = dict(joint_positions); plus[joint_id] = plus.get(joint_id, 0.0) + options.finite_difference_step
        minus = dict(joint_positions); minus[joint_id] = minus.get(joint_id, 0.0) - options.finite_difference_step
        p = _target_pose(assembly, target_component_id, target_connector_id, plus)
        m = _target_pose(assembly, target_component_id, target_connector_id, minus)
        matrix[:3, column] = (np.asarray(p.position_m) - np.asarray(m.position_m)) / (2.0 * options.finite_difference_step)
        matrix[3:, column] = np.asarray(_orientation_vector(m, p)) / (2.0 * options.finite_difference_step)
    singular_values = tuple(float(value) for value in np.linalg.svd(matrix, compute_uv=False))
    rank = int(np.linalg.matrix_rank(matrix, tol=options.rank_tolerance)) if matrix.size else 0
    condition = None
    if singular_values and singular_values[-1] > options.rank_tolerance:
        condition = float(singular_values[0] / singular_values[-1])
    return JacobianResult(target_component_id=target_component_id, target_connector_id=target_connector_id, joint_ids=joint_ids, matrix=tuple(tuple(float(value) for value in row) for row in matrix), rank=rank, singular_values=singular_values, condition_number=condition)


def analyze_mobility(*, assembly: AssemblyModel, joint_positions: Mapping[str, float] | None = None) -> MobilityReport:
    state = dict(joint_positions or {})
    tree = build_kinematic_tree(assembly=assembly)
    joint_dofs = {edge.joint_id: (0 if edge.joint_type == JointType.FIXED else 1) for edge in tree.tree_edges}
    joint_ids = tuple(sorted(joint_dofs))
    nominal = sum(joint_dofs.values())
    matrix, constraint_ids = _constraint_jacobian(assembly, state, joint_ids, 1e-7)
    algebraic_rows = _algebraic_constraint_rows(assembly, joint_ids)
    if algebraic_rows and matrix.size:
        row_offset = 0
        for constraint_id in constraint_ids:
            if constraint_id in algebraic_rows:
                matrix[row_offset, :] = algebraic_rows[constraint_id]
            row_offset += 1
    singular_values = tuple(float(value) for value in np.linalg.svd(matrix, compute_uv=False)) if matrix.size else ()
    rank = int(np.linalg.matrix_rank(matrix, tol=1e-9)) if matrix.size else 0
    issues: list[SimIssue] = list(
        _transmission_issues(assembly, tree, stage="kinematics.mobility")
    )
    if tree.disconnected_group_ids:
        issues.append(SimIssue(code="KINCHECK-KIN-MOBILITY-DISCONNECTED", severity="error", stage="kinematics.mobility", message="The assembly contains a disconnected component island.", object_ids=tree.disconnected_group_ids, suggested_actions=("Connect the island to Ground before using the mobility result.",)))
    return MobilityReport(nominal_dofs=nominal, effective_dofs=max(0, nominal - rank), joint_dofs=joint_dofs, constraint_rank=rank, constraint_ids=tuple(sorted(set(constraint_ids))), singular_values=singular_values, issues=tuple(issues))


def _residual_tolerances(
    *,
    assembly: AssemblyModel,
    pose_targets: Sequence[PoseTarget],
    options: PositionSolveOptions,
    residual_id: str,
) -> tuple[float, float, tuple[str, ...]]:
    if residual_id.startswith("pose_target:"):
        index = int(residual_id.partition(":")[2])
        target = pose_targets[index]
        return (
            target.position_tolerance_m
            if target.position_tolerance_m is not None
            else options.position_tolerance_m,
            target.orientation_tolerance_rad
            if target.orientation_tolerance_rad is not None
            else options.orientation_tolerance_rad,
            tuple(
                item
                for item in (target.component_id, target.connector_id)
                if item is not None
            ),
        )
    closure = next(
        (item for item in assembly.closures if item.closure_id == residual_id),
        None,
    )
    if closure is not None:
        return (
            closure.position_tolerance_m,
            closure.orientation_tolerance_rad,
            (closure.closure_id,),
        )
    return (
        options.position_tolerance_m,
        options.orientation_tolerance_rad,
        (residual_id,),
    )


def _residuals_within_tolerance(
    *,
    assembly: AssemblyModel,
    pose_targets: Sequence[PoseTarget],
    options: PositionSolveOptions,
    norms: Mapping[str, tuple[float, float]],
) -> bool:
    for residual_id, (position_residual, orientation_residual) in norms.items():
        position_tolerance, orientation_tolerance, _ = _residual_tolerances(
            assembly=assembly,
            pose_targets=pose_targets,
            options=options,
            residual_id=residual_id,
        )
        if (
            not math.isfinite(position_residual)
            or not math.isfinite(orientation_residual)
            or position_residual > position_tolerance
            or orientation_residual > orientation_tolerance
        ):
            return False
    return True


def _residual_failure_issues(
    *,
    assembly: AssemblyModel,
    pose_targets: Sequence[PoseTarget],
    options: PositionSolveOptions,
    norms: Mapping[str, tuple[float, float]],
) -> tuple[SimIssue, ...]:
    issues: list[SimIssue] = []
    for residual_id in sorted(norms):
        position_residual, orientation_residual = norms[residual_id]
        position_tolerance, orientation_tolerance, object_ids = _residual_tolerances(
            assembly=assembly,
            pose_targets=pose_targets,
            options=options,
            residual_id=residual_id,
        )
        common_evidence = (Evidence(key="residual_id", actual=residual_id),)
        if not math.isfinite(position_residual):
            issues.append(SimIssue(
                code="KINCHECK-KIN-POSITION-RESIDUAL-INVALID",
                severity="error",
                stage="kinematics.position",
                message="A position residual is not finite.",
                object_ids=object_ids,
                evidence=(*common_evidence, Evidence(key="position_residual_m", actual=position_residual, expected="finite", unit="m")),
            ))
        elif position_residual > position_tolerance:
            issues.append(SimIssue(
                code="KINCHECK-KIN-POSITION-RESIDUAL-EXCEEDED",
                severity="error",
                stage="kinematics.position",
                message="A position residual exceeds its effective metre tolerance.",
                object_ids=object_ids,
                evidence=(*common_evidence, Evidence(key="position_residual_m", actual=position_residual, expected=f"<= {position_tolerance}", unit="m"), Evidence(key="position_tolerance_m", actual=position_tolerance, unit="m")),
                suggested_actions=("Revise the target position, initial state, or position tolerance.",),
            ))
        if not math.isfinite(orientation_residual):
            issues.append(SimIssue(
                code="KINCHECK-KIN-ORIENTATION-RESIDUAL-INVALID",
                severity="error",
                stage="kinematics.position",
                message="An orientation residual is not finite.",
                object_ids=object_ids,
                evidence=(*common_evidence, Evidence(key="orientation_residual_rad", actual=orientation_residual, expected="finite", unit="rad")),
            ))
        elif orientation_residual > orientation_tolerance:
            issues.append(SimIssue(
                code="KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED",
                severity="error",
                stage="kinematics.position",
                message="An orientation residual exceeds its effective radian tolerance.",
                object_ids=object_ids,
                evidence=(*common_evidence, Evidence(key="orientation_residual_rad", actual=orientation_residual, expected=f"<= {orientation_tolerance}", unit="rad"), Evidence(key="orientation_tolerance_rad", actual=orientation_tolerance, unit="rad")),
                suggested_actions=("Revise the target orientation, initial state, or orientation tolerance.",),
            ))
    return tuple(issues)


def _residual_records(
    norms: Mapping[str, tuple[float, float]],
) -> tuple[ConstraintResidual, ...]:
    return tuple(
        ConstraintResidual(
            constraint_id=residual_id,
            time_s=0.0,
            position_residual_m=position_residual,
            orientation_residual_rad=orientation_residual,
        )
        for residual_id, (position_residual, orientation_residual) in sorted(norms.items())
        if math.isfinite(position_residual) and math.isfinite(orientation_residual)
    )


def solve_position_core(*, assembly: AssemblyModel, joint_positions: Mapping[str, float] | None = None, pose_targets: Sequence[PoseTarget] = (), options: PositionSolveOptions | None = None) -> tuple[str, Mapping[str, float], Mapping[str, Pose], tuple[ConstraintResidual, ...], tuple[SimIssue, ...]]:
    """Solve one authored assembly pose and return backend-neutral records."""

    options = options or PositionSolveOptions()
    supplied = {str(key): float(value) for key, value in (joint_positions or {}).items()}
    tree = build_kinematic_tree(assembly=assembly)
    joints = {joint.joint_id: joint for joint in assembly.joints}
    movable_ids = tuple(sorted(edge.joint_id for edge in tree.tree_edges if edge.joint_type in {JointType.REVOLUTE, JointType.PRISMATIC}))
    unknown_ids = tuple(item for item in movable_ids if item not in supplied)
    issues: list[SimIssue] = list(
        _transmission_issues(assembly, tree, stage="kinematics.position")
    )
    for joint_id in supplied:
        joint = joints.get(joint_id)
        if not math.isfinite(supplied[joint_id]):
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-VALUE-INVALID", severity="error", stage="kinematics.position", message="A supplied Joint position must be finite.", object_ids=(joint_id,), evidence=(Evidence(key="joint_position", actual=supplied[joint_id], expected="finite"),)))
        elif joint is None:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-JOINT-NOT-FOUND", severity="error", stage="kinematics.position", message="The requested position references an unknown Joint.", object_ids=(joint_id,), suggested_actions=("Use a Joint ID from the AssemblyModel.",)))
        elif joint.joint_type not in {JointType.REVOLUTE, JointType.PRISMATIC}:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-JOINT-UNSUPPORTED", severity="error", stage="kinematics.position", message="Only revolute and prismatic tree Joints can be solved.", object_ids=(joint_id,), suggested_actions=("Use a supported scalar Joint type.",)))
        elif joint.limit is not None and not (joint.limit.lower - 1e-12 <= supplied[joint_id] <= joint.limit.upper + 1e-12):
            issues.append(SimIssue(code="KINCHECK-KIN-TARGET-OUT-OF-LIMIT", severity="error", stage="kinematics.position", message="A requested Joint position is outside its limit.", object_ids=(joint_id,), evidence=(Evidence(key="position", actual=supplied[joint_id], expected=(joint.limit.lower, joint.limit.upper)),), suggested_actions=("Choose a Joint position inside the authored limit.",)))
    for target in pose_targets:
        component = assembly.get_component(component_id=target.component_id)
        if component is None:
            issues.append(SimIssue(code="KINCHECK-KIN-TARGET-NOT-FOUND", severity="error", stage="kinematics.position", message="The requested Pose target references an unknown Component.", object_ids=(target.component_id,), suggested_actions=("Use a Component ID from the AssemblyModel.",)))
        elif target.connector_id is not None and assembly.get_connector(
            component_id=target.component_id,
            connector_id=target.connector_id,
        ) is None:
            issues.append(
                SimIssue(
                    code="KINCHECK-KIN-TARGET-NOT-FOUND",
                    severity="error",
                    stage="kinematics.position",
                    message="The requested Pose target references an unknown Connector.",
                    object_ids=(target.component_id, target.connector_id),
                    suggested_actions=(
                        "Use a Connector ID defined by the target Component or Part.",
                    ),
                )
            )
    state: dict[str, float] = {joint_id: supplied.get(joint_id, 0.0) for joint_id in movable_ids}
    if any(issue.severity == "error" for issue in issues):
        poses = forward_component_poses(assembly, state)
        return "infeasible", MappingProxyType(state), poses, (), tuple(issues)
    if not unknown_ids:
        _, _, norms = _constraint_vector(assembly, state, pose_targets)
        issues.extend(_residual_failure_issues(assembly=assembly, pose_targets=pose_targets, options=options, norms=norms))
        status = "infeasible" if issues else "converged"
        poses = forward_component_poses(assembly, state)
        residuals = _residual_records(norms)
        return status, MappingProxyType(state), poses, residuals, tuple(issues)
    status = "nonconverged"
    residuals: tuple[ConstraintResidual, ...] = ()
    previous_norm = math.inf
    for _iteration in range(options.max_iterations):
        vector, constraint_ids, norms = _constraint_vector(assembly, state, pose_targets)
        residuals = _residual_records(norms)
        max_residual = float(np.max(np.abs(vector))) if vector.size else 0.0
        if _residuals_within_tolerance(assembly=assembly, pose_targets=pose_targets, options=options, norms=norms):
            status = "converged"
            break
        matrix, _ = _constraint_jacobian(assembly, state, unknown_ids, options.finite_difference_step, pose_targets)
        if matrix.size == 0:
            break
        singular_values = np.linalg.svd(matrix, compute_uv=False)
        rank = int(np.linalg.matrix_rank(matrix, tol=options.rank_tolerance))
        # A rank-deficient rectangular system is often simply underconstrained
        # (for example bearing rollers may spin freely).  Damped least
        # squares can still produce a valid state, so only a zero-rank system
        # is an immediate singular failure here.
        if rank == 0:
            issues.append(SimIssue(code="KINCHECK-KIN-SINGULAR", severity="error", stage="kinematics.position", message="The position constraint Jacobian is singular at the current state.", object_ids=tuple(sorted(set(constraint_ids))), evidence=(Evidence(key="rank", actual=rank, expected=f"> 0; singular_values={tuple(float(item) for item in singular_values)}"),), suggested_actions=("Choose a different initial posture or avoid the mechanism dead point.",)))
            status = "singular"
            break
        # Damped least squares minimizes the residual while remaining stable
        # near a nearly dependent Closure row.
        normal = matrix.T @ matrix + options.damping * np.eye(matrix.shape[1])
        try:
            step = np.linalg.solve(normal, -(matrix.T @ vector))
        except np.linalg.LinAlgError:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-NONCONVERGED", severity="error", stage="kinematics.position", message="The damped position system could not be solved.", object_ids=(assembly.assembly_id,), suggested_actions=("Provide a better initial state or increase damping.",)))
            break
        step_norm = float(np.linalg.norm(step, ord=np.inf))
        if step_norm <= options.step_tolerance:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-NONCONVERGED", severity="error", stage="kinematics.position", message="Position iteration stopped before reaching the requested residual tolerance.", object_ids=(assembly.assembly_id,), evidence=(Evidence(key="residual", actual=max_residual, expected="within solve tolerances"),), suggested_actions=("Increase max_iterations or provide a closer initial posture.",)))
            break
        for index, joint_id in enumerate(unknown_ids):
            value = state[joint_id] + float(step[index])
            joint = joints[joint_id]
            if joint.limit is not None:
                value = min(joint.limit.upper, max(joint.limit.lower, value))
            state[joint_id] = value
        if max_residual >= previous_norm - options.step_tolerance and step_norm <= 10.0 * options.step_tolerance:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-NONCONVERGED", severity="error", stage="kinematics.position", message="Position residual stopped improving.", object_ids=(assembly.assembly_id,), evidence=(Evidence(key="residual", actual=max_residual, expected="decreasing"),), suggested_actions=("Change the initial branch or relax the requested target.",)))
            break
        previous_norm = max_residual
    if status != "converged":
        if 'norms' in locals():
            existing_codes = {item.code for item in issues}
            issues.extend(
                item
                for item in _residual_failure_issues(assembly=assembly, pose_targets=pose_targets, options=options, norms=norms)
                if item.code not in existing_codes
            )
        if not issues:
            issues.append(SimIssue(code="KINCHECK-KIN-POSITION-NONCONVERGED", severity="error", stage="kinematics.position", message="The position solver reached its iteration limit without converging.", object_ids=(assembly.assembly_id,), evidence=(Evidence(key="max_iterations", actual=options.max_iterations),), suggested_actions=("Increase max_iterations or provide a closer initial posture.",)))
    poses = forward_component_poses(assembly, state)
    return status, MappingProxyType(state), poses, residuals, tuple(issues)


__all__ = ["JacobianOptions", "JacobianResult", "MobilityReport", "PoseTarget", "PositionSolveOptions", "analyze_mobility", "compute_jacobian", "forward_component_poses", "forward_connector_poses", "solve_position_core", "_constraint_vector", "_constraint_jacobian"]
