"""physics backend implementation hidden behind KinCheckAPI's backend boundary.

The compiler consumes stable AssemblyModel IDs and explicit relationships.  It
does not inspect display names or infer gear roles from naming conventions.
physics backend objects never cross the result boundary: callers receive immutable
records containing only Python scalars, tuples, and mappings.

The current compiler supports the one-coordinate joint subset used by the CAD
examples: fixed, revolute, and prismatic joints.  Gear and belt constraints are
compiled from their explicit endpoint components and radius metadata.  A
moving mesh frame (for example a planetary carrier) is inferred from the joint
topology shared by the constrained components, not from component names.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET

try:
    import mujoco
except (ImportError, OSError) as error:  # pragma: no cover - environment dependent
    mujoco = None  # type: ignore[assignment]
    _BACKEND_IMPORT_ERROR: BaseException | None = error
else:
    _BACKEND_IMPORT_ERROR = None

from ..assembly import (
    AssemblyModel,
    Connector,
    ConnectorRef,
    Joint,
    JointType,
    build_kinematic_tree,
    validate_topology,
)
from ..pose import Pose, compose_pose, orientation_error_rad, relative_pose, rotate_vector
from ..scenario import (
    ComponentResultScope,
    Interpolation,
    JointValue,
    MotionProfile,
    Scenario,
)


_SUPPORTED_JOINT_TYPES = {JointType.FIXED, JointType.REVOLUTE, JointType.PRISMATIC}
_MESH_TYPES = {"gear", "belt", "rack_pinion"}
_POSITION_KP = 10000.0
_POSITION_KV = 200.0
_INITIAL_STATE_TOLERANCE = 1e-9
_DEFAULT_TIMESTEP_S = 5e-4
_CLOSURE_TIMESTEP_S = 2e-5
# A critically damped, short response replaces the overdamped direct-format
# closure springs. Keep at least five integration steps per time constant,
# including during startup; coarse output sampling can hide that transient.
_CLOSURE_SOLREF = "0.0001 1"
_CLOSURE_SOLIMP = "0.9999 0.9999 0.001"
_CLOSURE_SOLVER_ITERATIONS = 200


class BackendUnavailable(RuntimeError):
    """The optional physics backend runtime cannot be loaded."""


class BackendCapabilityFailure(RuntimeError):
    """An Assembly relationship cannot be represented by this backend."""

    def __init__(
        self,
        message: str,
        *,
        object_ids: Iterable[str] = (),
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.object_ids = tuple(object_ids)
        self.details = dict(details or {})


class BackendCompileFailure(RuntimeError):
    """physics backend rejected a generated model."""

    def __init__(self, message: str, *, model_xml: str | None = None) -> None:
        super().__init__(message)
        self.model_xml = model_xml


class BackendSolveFailure(RuntimeError):
    """physics backend failed or produced non-finite state while stepping."""

    def __init__(self, message: str, *, time_s: float | None = None, last_valid_samples: Sequence[BackendSample] = ()) -> None:
        super().__init__(message)
        self.time_s = time_s
        self.last_valid_samples = tuple(last_valid_samples)


class BackendInitialStateFailure(RuntimeError):
    """The requested public Joint initial state is internally inconsistent."""

    def __init__(
        self,
        message: str,
        *,
        object_ids: Iterable[str] = (),
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.object_ids = tuple(object_ids)
        self.details = dict(details or {})


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendPose:
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendSample:
    time_s: float
    joint_positions: Mapping[str, float]
    joint_velocities: Mapping[str, float]
    component_poses: Mapping[str, BackendPose]
    connector_poses: Mapping[tuple[str, str], BackendPose]
    constraint_residuals: Mapping[str, float]
    component_linear_velocities: Mapping[str, tuple[float, float, float]] = field(default_factory=dict)
    component_angular_velocities: Mapping[str, tuple[float, float, float]] = field(default_factory=dict)
    component_linear_accelerations: Mapping[str, tuple[float, float, float]] = field(default_factory=dict)
    component_angular_accelerations: Mapping[str, tuple[float, float, float]] = field(default_factory=dict)
    connector_linear_velocities: Mapping[tuple[str, str], tuple[float, float, float]] = field(default_factory=dict)
    connector_angular_velocities: Mapping[tuple[str, str], tuple[float, float, float]] = field(default_factory=dict)
    connector_linear_accelerations: Mapping[tuple[str, str], tuple[float, float, float]] = field(default_factory=dict)
    connector_angular_accelerations: Mapping[tuple[str, str], tuple[float, float, float]] = field(default_factory=dict)
    constraint_equation_residuals: Mapping[str, float] = field(default_factory=dict)
    constraint_position_residuals: Mapping[str, float] = field(default_factory=dict)
    constraint_orientation_residuals: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "joint_positions",
            "joint_velocities",
            "component_poses",
            "connector_poses",
            "component_linear_velocities",
            "component_angular_velocities",
            "component_linear_accelerations",
            "component_angular_accelerations",
            "connector_linear_velocities",
            "connector_angular_velocities",
            "connector_linear_accelerations",
            "connector_angular_accelerations",
            "constraint_residuals",
            "constraint_equation_residuals",
            "constraint_position_residuals",
            "constraint_orientation_residuals",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendIntegrationSample:
    """Minimal world-pose snapshot retained after one physics backend integration step."""

    time_s: float
    component_poses: Mapping[str, BackendPose]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", float(self.time_s))
        object.__setattr__(self, "component_poses", MappingProxyType(dict(self.component_poses)))


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendSolveResult:
    backend_name: str
    backend_version: str
    assembly_id: str
    scenario_id: str
    samples: tuple[BackendSample, ...]
    # Internal mj_step samples are retained only when the Scenario opts in.
    integration_samples: tuple[BackendIntegrationSample, ...] = ()
    warnings: tuple[str, ...] = ()
    model_summary: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "samples", tuple(self.samples))
        object.__setattr__(self, "integration_samples", tuple(self.integration_samples))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "model_summary", MappingProxyType(dict(self.model_summary)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class _LinearExpression:
    coefficients: Mapping[str, float]

    def evaluate(self, values: Mapping[str, float]) -> float:
        return sum(coefficient * values.get(group_id, 0.0) for group_id, coefficient in self.coefficients.items())


@dataclass(frozen=True, slots=True)
class _ConstraintExpression:
    constraint_id: str
    expression: _LinearExpression
    offset: float = 0.0
    equation_type: str = "coupling"
    equation_unit: str = "rad"


@dataclass(frozen=True, slots=True)
class _GeometricResidualDefinition:
    """Expected geometric relationship for a pair of connector sites."""

    constraint_id: str
    endpoint_a: tuple[str, str]
    endpoint_b: tuple[str, str]
    expected_distance_m: float
    expected_relative_pose: Pose
    axis_only: bool = False


@dataclass(frozen=True, slots=True)
class _ComponentSite:
    component_id: str
    site_name: str


@dataclass(frozen=True, slots=True)
class _ConnectorSite:
    component_id: str
    connector_id: str
    site_name: str
    body_name: str


@dataclass(slots=True)
class _CompiledAssembly:
    assembly: AssemblyModel
    model: Any
    model_xml: str
    component_groups: Mapping[str, str]
    group_joint_names: Mapping[str, str]
    group_modes: Mapping[str, JointType]
    group_parents: Mapping[str, str | None]
    group_depths: Mapping[str, int]
    closure_joints: Mapping[str, Joint]
    group_world_expressions: Mapping[str, _LinearExpression]
    joint_expressions: Mapping[str, _LinearExpression]
    constraint_expressions: tuple[_ConstraintExpression, ...]
    geometric_residuals: tuple[_GeometricResidualDefinition, ...]
    component_sites: tuple[_ComponentSite, ...]
    connector_sites: tuple[_ConnectorSite, ...]
    warnings: tuple[str, ...]


class _DisjointSet:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        # Stable roots make generated XML deterministic across runs.
        first, second = sorted((root_left, root_right))
        self.parent[second] = first


def _require_backend() -> Any:
    if mujoco is None:
        raise BackendUnavailable(
            "physics backend is not installed or could not be loaded"
        ) from _BACKEND_IMPORT_ERROR
    return mujoco


def _fmt(values: Iterable[float]) -> str:
    return " ".join(f"{float(value):.17g}" for value in values)


def _quat_normalize_xyzw(value: Sequence[float]) -> tuple[float, float, float, float]:
    norm = math.sqrt(sum(float(item) ** 2 for item in value))
    if norm <= 0.0:
        return (0.0, 0.0, 0.0, 1.0)
    return tuple(float(item) / norm for item in value)  # type: ignore[return-value]


def _backend_quat(value_xyzw: Sequence[float]) -> tuple[float, float, float, float]:
    x, y, z, w = _quat_normalize_xyzw(value_xyzw)
    return (w, x, y, z)


def _add_coefficients(
    destination: dict[str, float], source: Mapping[str, float], scale: float = 1.0
) -> None:
    for key, value in source.items():
        destination[key] = destination.get(key, 0.0) + scale * value
        if abs(destination[key]) < 1e-15:
            destination.pop(key)


def _relative_expression(
    component_a_id: str,
    component_b_id: str,
    *,
    component_groups: Mapping[str, str],
    moving_groups: set[str],
    group_world_expressions: Mapping[str, _LinearExpression] | None = None,
) -> _LinearExpression:
    values: dict[str, float] = {}
    group_a = component_groups[component_a_id]
    group_b = component_groups[component_b_id]
    expression_a = (
        group_world_expressions[group_a].coefficients
        if group_world_expressions is not None
        else ({group_a: 1.0} if group_a in moving_groups else {})
    )
    expression_b = (
        group_world_expressions[group_b].coefficients
        if group_world_expressions is not None
        else ({group_b: 1.0} if group_b in moving_groups else {})
    )
    _add_coefficients(values, expression_a, -1.0)
    _add_coefficients(values, expression_b)
    return _LinearExpression(MappingProxyType(values))


def _component_expression(
    component_id: str,
    *,
    component_groups: Mapping[str, str],
    moving_groups: set[str],
    group_world_expressions: Mapping[str, _LinearExpression] | None = None,
) -> Mapping[str, float]:
    group_id = component_groups[component_id]
    if group_world_expressions is not None:
        return group_world_expressions[group_id].coefficients
    return {group_id: 1.0} if group_id in moving_groups else {}


def _connector_for_ref(assembly: AssemblyModel, reference: ConnectorRef) -> Connector:
    connector = assembly.get_connector(
        component_id=reference.component_id,
        connector_id=reference.connector_id,
    )
    if connector is None:
        raise BackendCapabilityFailure(
            "A Joint or Constraint references an unknown Connector",
            object_ids=(reference.component_id, reference.connector_id),
        )
    return connector


def _radius(metadata: Mapping[str, Any], *, kind: str, endpoint: str, owner_id: str) -> float:
    prefix = "pitch_radius" if kind in {"gear", "rack_pinion"} else "pulley_radius"
    raw_value = metadata.get(f"{prefix}_{endpoint}")
    if raw_value is None:
        raw_value = metadata.get(prefix)
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as cause:
        raise BackendCapabilityFailure(
            f"{kind} constraint requires explicit positive {prefix}_{endpoint} metadata",
            object_ids=(owner_id,),
            details={"metadata_key": f"{prefix}_{endpoint}", "actual": raw_value},
        ) from cause
    if not math.isfinite(value) or value <= 0.0:
        raise BackendCapabilityFailure(
            f"{kind} constraint radius must be finite and positive",
            object_ids=(owner_id,),
            details={"metadata_key": f"{prefix}_{endpoint}", "actual": raw_value},
        )
    return value


def _connector_world_pose(*, assembly: AssemblyModel, reference: ConnectorRef) -> Pose:
    component = assembly.get_component(component_id=reference.component_id)
    if component is None:  # pragma: no cover - validated before compilation
        raise BackendCapabilityFailure(
            "A Constraint references an unknown Component",
            object_ids=(reference.component_id,),
        )
    connector = _connector_for_ref(assembly, reference)
    return compose_pose(parent=component.initial_pose, child=connector.pose)


def _geometric_residual_definition(
    *, assembly: AssemblyModel, constraint: Any
) -> _GeometricResidualDefinition:
    """Build a stable geometric baseline from the imported CAD placement.

    Mesh constraints use their authored center distance when one is supplied;
    otherwise the imported distance is the reference.  Connector axes are
    compared without their spin for gear and belt meshes because spinning a
    gear does not change its axis alignment.
    """

    endpoint_a = constraint.connector_a
    endpoint_b = constraint.connector_b
    pose_a = _connector_world_pose(assembly=assembly, reference=endpoint_a)
    pose_b = _connector_world_pose(assembly=assembly, reference=endpoint_b)
    initial_distance_m = math.dist(pose_a.position_m, pose_b.position_m)
    kind = str(constraint.constraint_type).lower()
    raw_distance = constraint.metadata.get("distance_m")
    if raw_distance is None:
        raw_distance = constraint.metadata.get("center_distance_m")
    # Imported sources historically store pitch radii in design units while
    # connector poses are already in metres.  Unless a value explicitly uses
    # the public ``*_m`` key, use the imported center distance as the baseline
    # instead of mixing units.
    if raw_distance is None:
        expected_distance_m = initial_distance_m
    else:
        try:
            expected_distance_m = float(raw_distance)
        except (TypeError, ValueError) as cause:
            raise BackendCapabilityFailure(
                "Constraint distance metadata must be numeric",
                object_ids=(constraint.constraint_id,),
                details={"distance_m": raw_distance},
            ) from cause
        if not math.isfinite(expected_distance_m) or expected_distance_m < 0.0:
            raise BackendCapabilityFailure(
                "Constraint distance metadata must be finite and non-negative",
                object_ids=(constraint.constraint_id,),
                details={"distance_m": raw_distance},
            )
    return _GeometricResidualDefinition(
        constraint_id=constraint.constraint_id,
        endpoint_a=(endpoint_a.component_id, endpoint_a.connector_id),
        endpoint_b=(endpoint_b.component_id, endpoint_b.connector_id),
        expected_distance_m=expected_distance_m,
        expected_relative_pose=relative_pose(parent=pose_a, child=pose_b),
        axis_only=kind in {"gear", "belt", "parallel", "concentric"},
    )


def _joint_groups(
    assembly: AssemblyModel,
) -> tuple[Mapping[str, str], Mapping[str, tuple[str, ...]]]:
    component_ids = tuple(component.component_id for component in assembly.components)
    disjoint = _DisjointSet(component_ids)
    for joint in assembly.joints:
        if joint.joint_type == JointType.FIXED:
            disjoint.union(joint.connector_a.component_id, joint.connector_b.component_id)
    groups: dict[str, list[str]] = {}
    component_groups: dict[str, str] = {}
    for component_id in component_ids:
        root = disjoint.find(component_id)
        component_groups[component_id] = root
        groups.setdefault(root, []).append(component_id)
    return MappingProxyType(component_groups), MappingProxyType(
        {key: tuple(sorted(values)) for key, values in groups.items()}
    )


def _group_tree(
    assembly: AssemblyModel,
    *,
    component_groups: Mapping[str, str],
    groups: Mapping[str, tuple[str, ...]],
    grounded_groups: set[str],
) -> tuple[
    Mapping[str, str | None],
    Mapping[str, int],
    Mapping[str, JointType],
    Mapping[str, Joint],
    Mapping[str, Joint],
]:
    """Choose the tree and retain non-tree movable edges as closures.

    The public graph analyzer owns the deterministic traversal.  The backend
    consumes its result instead of silently turning a loop edge into a tree
    coordinate or promoting a disconnected island to a world-root body.
    """

    tree = build_kinematic_tree(assembly=assembly)
    parents = dict(tree.parent_group_id)
    depths: dict[str, int] = {}
    for group_id, members in groups.items():
        depths[group_id] = min(
            (tree.depth_by_component_id.get(component_id, 0) for component_id in members),
            default=0,
        )
    tree_joints: dict[str, Joint] = {}
    for edge in tree.tree_edges:
        joint = assembly.get_joint(joint_id=edge.joint_id)
        if joint is None:
            raise BackendCapabilityFailure(
                "Kinematic tree references an unknown Joint",
                object_ids=(edge.joint_id,),
            )
        if joint.joint_type not in _SUPPORTED_JOINT_TYPES:
            raise BackendCapabilityFailure(
                f"backend does not yet support {joint.joint_type.value} Joint observables",
                object_ids=(joint.joint_id,),
                details={"joint_type": joint.joint_type.value},
            )
        tree_joints[edge.child_group_id] = joint
    closure_joints: dict[str, Joint] = {}
    for edge in tree.closure_edges:
        joint = assembly.get_joint(joint_id=edge.joint_id)
        if joint is not None:
            closure_joints[edge.joint_id] = joint
    modes = {
        group_id: joint.joint_type
        for group_id, joint in tree_joints.items()
        if group_id not in grounded_groups
    }
    return (
        MappingProxyType(parents),
        MappingProxyType(depths),
        MappingProxyType(modes),
        MappingProxyType(tree_joints),
        MappingProxyType(closure_joints),
    )


def _world_expressions(
    *, parents: Mapping[str, str | None], grounded_groups: set[str], modes: Mapping[str, JointType]
) -> Mapping[str, _LinearExpression]:
    expressions: dict[str, _LinearExpression] = {}

    def visit(group_id: str) -> _LinearExpression:
        if group_id in expressions:
            return expressions[group_id]
        parent = parents.get(group_id)
        values: dict[str, float] = {}
        if parent is not None:
            _add_coefficients(values, visit(parent).coefficients)
        if group_id not in grounded_groups:
            values[group_id] = values.get(group_id, 0.0) + 1.0
        result = _LinearExpression(MappingProxyType(values))
        expressions[group_id] = result
        return result

    for group_id in parents:
        visit(group_id)
    return MappingProxyType(expressions)


def _mesh_expression(
    *,
    assembly: AssemblyModel,
    constraint: Any,
    component_groups: Mapping[str, str],
    moving_groups: set[str],
    supports: Mapping[str, str | None],
    group_world_expressions: Mapping[str, _LinearExpression] | None = None,
) -> _ConstraintExpression:
    component_a_id = constraint.connector_a.component_id
    component_b_id = constraint.connector_b.component_id
    group_a = component_groups[component_a_id]
    group_b = component_groups[component_b_id]
    frame = supports.get(constraint.constraint_id)
    kind = constraint.constraint_type
    radius_a = _radius(constraint.metadata, kind=kind, endpoint="a", owner_id=constraint.constraint_id)
    radius_b = _radius(constraint.metadata, kind=kind, endpoint="b", owner_id=constraint.constraint_id)
    direction_b = 1.0 if kind == "gear" else -1.0
    coefficient_a = radius_a
    coefficient_b = direction_b * radius_b
    if kind == "rack_pinion":
        mode_a, mode_b = _constraint_endpoint_modes(
            assembly=assembly,
            constraint=constraint,
            component_groups=component_groups,
        )
        coefficient_a = 1.0 if mode_a == JointType.PRISMATIC else radius_a
        coefficient_b = direction_b if mode_b == JointType.PRISMATIC else direction_b * radius_b
    values: dict[str, float] = {}
    _add_coefficients(
        values,
        _component_expression(
            component_a_id,
            component_groups=component_groups,
            moving_groups=moving_groups,
            group_world_expressions=group_world_expressions,
        ),
        coefficient_a,
    )
    _add_coefficients(
        values,
        _component_expression(
            component_b_id,
            component_groups=component_groups,
            moving_groups=moving_groups,
            group_world_expressions=group_world_expressions,
        ),
        coefficient_b,
    )
    if frame is not None and frame in moving_groups:
        values[frame] = values.get(frame, 0.0) - coefficient_a - coefficient_b
        if abs(values[frame]) < 1e-15:
            values.pop(frame)
    if not values:
        raise BackendCapabilityFailure(
            "A mesh constraint has no movable coordinate",
            object_ids=(constraint.constraint_id,),
        )
    # Coordinates describe displacement from the imported CAD pose.  The
    # source phase is already present in that pose, so the displacement offset
    # is zero even when the source records an absolute tooth phase.
    return _ConstraintExpression(
        constraint_id=constraint.constraint_id,
        expression=_LinearExpression(MappingProxyType(values)),
        equation_type=kind,
        equation_unit="m",
    )


def _constraint_endpoint_modes(
    *,
    assembly: AssemblyModel,
    constraint: Any,
    component_groups: Mapping[str, str],
) -> tuple[JointType, JointType]:
    """Resolve the scalar tree coordinate type supporting each endpoint."""

    tree = build_kinematic_tree(assembly=assembly)
    modes: list[JointType] = []
    for reference in (constraint.connector_a, constraint.connector_b):
        group_id = component_groups.get(reference.component_id)
        edge = next(
            (item for item in tree.tree_edges if item.child_group_id == group_id),
            None,
        )
        modes.append(edge.joint_type if edge is not None else JointType.REVOLUTE)
    if constraint.constraint_type == "rack_pinion" and {
        modes[0], modes[1]
    } != {JointType.REVOLUTE, JointType.PRISMATIC}:
        raise BackendCapabilityFailure(
            "A rack_pinion relation requires one revolute and one prismatic endpoint",
            object_ids=(constraint.constraint_id,),
            details={"endpoint_joint_types": tuple(mode.value for mode in modes)},
        )
    return modes[0], modes[1]


def _mesh_support_frames(
    assembly: AssemblyModel,
    *,
    component_groups: Mapping[str, str],
    group_parents: Mapping[str, str | None],
    group_depths: Mapping[str, int],
) -> Mapping[str, str | None]:
    """Map each explicit mesh relation to its topological moving frame."""

    frames: dict[str, str | None] = {}
    for constraint in assembly.constraints:
        if constraint.constraint_type not in _MESH_TYPES:
            continue
        group_a = component_groups[constraint.connector_a.component_id]
        group_b = component_groups[constraint.connector_b.component_id]
        depth_a = group_depths.get(group_a, 0)
        depth_b = group_depths.get(group_b, 0)
        if depth_a == depth_b:
            frames[constraint.constraint_id] = None
            continue
        child = group_a if depth_a > depth_b else group_b
        frames[constraint.constraint_id] = group_parents.get(child)
    return MappingProxyType(frames)


def _coupling_expression(
    coupling: Any, *, joint_expressions: Mapping[str, _LinearExpression]
) -> _ConstraintExpression:
    try:
        expression_a = joint_expressions[coupling.joint_a_id]
        expression_b = joint_expressions[coupling.joint_b_id]
    except KeyError as cause:
        raise BackendCapabilityFailure(
            "A Coupling references an unknown Joint",
            object_ids=(coupling.coupling_id, str(cause.args[0])),
        ) from cause
    values: dict[str, float] = {}
    _add_coefficients(values, expression_a.coefficients)
    _add_coefficients(values, expression_b.coefficients, -float(coupling.ratio))
    return _ConstraintExpression(
        constraint_id=coupling.coupling_id,
        expression=_LinearExpression(MappingProxyType(values)),
        offset=float(coupling.phase_offset),
        equation_type="coupling",
        equation_unit="rad",
    )


def _group_joint_limits(
    *,
    assembly: AssemblyModel,
    joint_expressions: Mapping[str, _LinearExpression],
    movable_group_ids: set[str],
) -> Mapping[str, tuple[float, float]]:
    """Project authored public Joint limits onto physics backend scalar coordinates."""

    result: dict[str, tuple[float, float]] = {}
    owners: dict[str, list[str]] = {}
    for joint in assembly.joints:
        if joint.limit is None:
            continue
        expression = joint_expressions.get(joint.joint_id)
        coefficients = {} if expression is None else expression.coefficients
        if len(coefficients) != 1:
            raise BackendCapabilityFailure(
                "A limited public Joint must map to exactly one physics backend coordinate",
                object_ids=(joint.joint_id,),
                details={"coordinate_count": len(coefficients)},
            )
        group_id, coefficient = next(iter(coefficients.items()))
        if group_id not in movable_group_ids or not math.isfinite(coefficient) or abs(coefficient) < 1e-15:
            raise BackendCapabilityFailure(
                "A limited public Joint does not map to a movable physics backend coordinate",
                object_ids=(joint.joint_id,),
                details={"group_id": group_id, "coefficient": coefficient},
            )
        projected = sorted(
            (joint.limit.lower / coefficient, joint.limit.upper / coefficient)
        )
        lower, upper = projected[0], projected[1]
        if group_id in result:
            previous_lower, previous_upper = result[group_id]
            lower = max(lower, previous_lower)
            upper = min(upper, previous_upper)
            if lower > upper:
                raise BackendCapabilityFailure(
                    "Public Joint limits mapped to the same physics backend coordinate have an empty intersection",
                    object_ids=tuple((*owners[group_id], joint.joint_id)),
                    details={
                        "group_id": group_id,
                        "previous_range": (previous_lower, previous_upper),
                        "incoming_range": tuple(projected),
                    },
                )
        result[group_id] = (lower, upper)
        owners.setdefault(group_id, []).append(joint.joint_id)
    return MappingProxyType(result)


def _add_fixed_tendon(
    parent: ET.Element,
    *,
    name: str,
    expression: _LinearExpression,
    group_joint_names: Mapping[str, str],
) -> None:
    tendon = ET.SubElement(parent, "fixed", {"name": name})
    for group_id, coefficient in sorted(expression.coefficients.items()):
        ET.SubElement(
            tendon,
            "joint",
            {"joint": group_joint_names[group_id], "coef": f"{coefficient:.17g}"},
        )


def _all_component_connectors(assembly: AssemblyModel, component_id: str) -> tuple[Connector, ...]:
    component = assembly.get_component(component_id=component_id)
    if component is None:
        return ()
    values: dict[str, Connector] = {}
    part = assembly.get_part(part_id=component.part_id)
    if part is not None:
        values.update({item.connector_id: item for item in part.connectors})
    values.update({item.connector_id: item for item in component.connectors})
    return tuple(values[key] for key in sorted(values))


def _build_xml(
    *,
    assembly: AssemblyModel,
    component_groups: Mapping[str, str],
    groups: Mapping[str, tuple[str, ...]],
    grounded_groups: set[str],
    group_modes: Mapping[str, JointType],
    group_parents: Mapping[str, str | None],
    tree_joints: Mapping[str, Joint],
    group_joint_limits: Mapping[str, tuple[float, float]],
    joint_expressions: Mapping[str, _LinearExpression],
    constraint_expressions: tuple[_ConstraintExpression, ...],
    solver_iterations: int | None = None,
    solver_tolerance: float | None = None,
    rigid_body_properties: Mapping[str, Any] | None = None,
) -> tuple[str, Mapping[str, str], tuple[_ComponentSite, ...], tuple[_ConnectorSite, ...]]:
    root = ET.Element("mujoco", {"model": "kincheckapi"})
    ET.SubElement(root, "compiler", {"angle": "radian", "autolimits": "true"})
    # Carrier-relative mesh equations need the same startup integration
    # resolution as geometric closures. Output sampling and drive curves stay
    # exactly as authored by the Scenario.
    precise_constraints = bool(assembly.closures) or any(
        item.equation_type in {"gear", "belt"} for item in constraint_expressions
    )
    ET.SubElement(
        root,
        "option",
        {
            "timestep": str(_CLOSURE_TIMESTEP_S if precise_constraints else _DEFAULT_TIMESTEP_S),
            "gravity": "0 0 0",
            "integrator": "implicitfast",
            "iterations": str(solver_iterations if solver_iterations is not None else (_CLOSURE_SOLVER_ITERATIONS if precise_constraints else 100)),
            "tolerance": str(solver_tolerance if solver_tolerance is not None else 1e-12),
        },
    )
    ET.SubElement(root, "size", {"njmax": "10000", "nconmax": "1000"})
    world = ET.SubElement(root, "worldbody")
    group_joint_names: dict[str, str] = {}
    component_sites: list[_ComponentSite] = []
    connector_sites: list[_ConnectorSite] = []
    connector_relative_poses: dict[tuple[str, str], Pose] = {}
    body_elements: dict[str, ET.Element] = {}
    group_indices = {group_id: index for index, group_id in enumerate(sorted(groups))}
    representatives: dict[str, Any] = {}
    for group_id, member_ids in groups.items():
        representative = assembly.get_component(component_id=member_ids[0])
        if representative is not None:
            representatives[group_id] = representative
    children: dict[str, list[str]] = {}
    for group_id, parent_group_id in group_parents.items():
        if parent_group_id is not None:
            children.setdefault(parent_group_id, []).append(group_id)

    def add_group_body(parent_element: ET.Element, group_id: str) -> None:
        group_index = group_indices[group_id]
        member_ids = groups[group_id]
        representative = representatives.get(group_id)
        if representative is None:  # pragma: no cover - AssemblyModel invariant
            return
        parent_group_id = group_parents.get(group_id)
        body_pose = representative.initial_pose
        if parent_group_id is not None:
            parent_representative = representatives[parent_group_id]
            body_pose = relative_pose(
                parent=parent_representative.initial_pose,
                child=representative.initial_pose,
            )
        body_name = f"body_{group_index}"
        body = ET.SubElement(
            parent_element,
            "body",
            {
                "name": body_name,
                "pos": _fmt(body_pose.position_m),
                "quat": _fmt(_backend_quat(body_pose.orientation_xyzw)),
            },
        )
        body_elements[body_name] = body
        if rigid_body_properties is not None:
            physical = rigid_body_properties[group_id]
            from ..physics_backend import _principal_inertial_attributes
            ET.SubElement(body, "inertial", _principal_inertial_attributes(physical))
        if group_id in group_modes and group_id not in grounded_groups:
            mode = group_modes[group_id]
            joint_name = f"group_joint_{group_index}"
            group_joint_names[group_id] = joint_name
            tree_joint = tree_joints[group_id]
            endpoint = (
                tree_joint.connector_a
                if component_groups[tree_joint.connector_a.component_id] == group_id
                else tree_joint.connector_b
            )
            endpoint_component = assembly.get_component(component_id=endpoint.component_id)
            endpoint_connector = _connector_for_ref(assembly, endpoint)
            if endpoint_component is None:  # pragma: no cover - AssemblyModel invariant
                raise BackendCapabilityFailure(
                    "A tree Joint references an unknown Component",
                    object_ids=(tree_joint.joint_id, endpoint.component_id),
                )
            endpoint_world_pose = compose_pose(
                parent=endpoint_component.initial_pose,
                child=endpoint_connector.pose,
            )
            endpoint_group_pose = relative_pose(
                parent=representative.initial_pose,
                child=endpoint_world_pose,
            )
            axis = rotate_vector(
                pose=endpoint_group_pose,
                vector=(0.0, 0.0, 1.0),
            )
            joint_attributes = {
                "name": joint_name,
                "type": "hinge" if mode == JointType.REVOLUTE else "slide",
                "pos": _fmt(endpoint_group_pose.position_m),
                "axis": _fmt(axis),
                "damping": "0",
                "armature": "0" if rigid_body_properties is not None else "1e-8",
            }
            if group_id in group_joint_limits:
                joint_attributes["limited"] = "true"
                joint_attributes["range"] = _fmt(group_joint_limits[group_id])
            ET.SubElement(body, "joint", joint_attributes)
            if rigid_body_properties is None:
                ET.SubElement(
                    body,
                    "inertial",
                    {"pos": "0 0 0", "mass": "1", "diaginertia": "0.001 0.001 0.001"},
                )
        for component_id in member_ids:
            component = assembly.get_component(component_id=component_id)
            if component is None:  # pragma: no cover - AssemblyModel invariant
                continue
            relative = relative_pose(
                parent=representative.initial_pose,
                child=component.initial_pose,
            )
            site_name = f"component_site_{len(component_sites)}"
            ET.SubElement(
                body,
                "site",
                {
                    "name": site_name,
                    "pos": _fmt(relative.position_m),
                    "quat": _fmt(_backend_quat(relative.orientation_xyzw)),
                    "type": "sphere",
                    "size": "0.0001",
                },
            )
            component_sites.append(_ComponentSite(component_id=component_id, site_name=site_name))
            for connector in _all_component_connectors(assembly, component_id):
                connector_pose = compose_pose(parent=component.initial_pose, child=connector.pose)
                connector_relative = relative_pose(
                    parent=representative.initial_pose,
                    child=connector_pose,
                )
                connector_site_name = f"connector_site_{len(connector_sites)}"
                ET.SubElement(
                    body,
                    "site",
                    {
                        "name": connector_site_name,
                        "pos": _fmt(connector_relative.position_m),
                        "quat": _fmt(_backend_quat(connector_relative.orientation_xyzw)),
                        "type": "sphere",
                        "size": "0.0001",
                    },
                )
                connector_sites.append(
                    _ConnectorSite(
                        component_id=component_id,
                        connector_id=connector.connector_id,
                        site_name=connector_site_name,
                        body_name=body_name,
                    )
                )
                connector_relative_poses[(component_id, connector.connector_id)] = connector_relative

        for child_group_id in sorted(children.get(group_id, ())):
            add_group_body(body, child_group_id)

    for root_group_id in sorted(
        group_id for group_id, parent_group_id in group_parents.items() if parent_group_id is None
    ):
        add_group_body(world, root_group_id)

    tendon_root = ET.SubElement(root, "tendon")
    equality_root = ET.SubElement(root, "equality")
    for index, constraint in enumerate(constraint_expressions):
        tendon_name = f"constraint_tendon_{index}"
        _add_fixed_tendon(
            tendon_root,
            name=tendon_name,
            expression=constraint.expression,
            group_joint_names=group_joint_names,
        )
        ET.SubElement(
            equality_root,
            "tendon",
            {
                "name": f"constraint_equality_{index}",
                "tendon1": tendon_name,
                "polycoef": f"{constraint.offset:.17g} 0 0 0 0",
                "solref": "0.001 1",
                "solimp": "0.99 0.9999 0.001",
            },
        )

    connector_site_by_ref = {
        (item.component_id, item.connector_id): item for item in connector_sites
    }
    for closure in assembly.closures:
        endpoint_a = (closure.constraint.connector_a.component_id, closure.constraint.connector_a.connector_id)
        endpoint_b = (closure.constraint.connector_b.component_id, closure.constraint.connector_b.connector_id)
        site_a = connector_site_by_ref.get(endpoint_a)
        site_b = connector_site_by_ref.get(endpoint_b)
        if site_a is None or site_b is None:
            raise BackendCapabilityFailure(
                "A Closure references a Connector that is not present in the generated model",
                object_ids=(closure.closure_id, *endpoint_a, *endpoint_b),
            )
        constraint_type = str(closure.constraint.constraint_type).lower()
        if constraint_type in {"weld", "fixed"}:
            ET.SubElement(
                equality_root,
                "weld",
                {
                    "name": closure.closure_id,
                    "body1": site_a.body_name,
                    "body2": site_b.body_name,
                    "torquescale": "0.001",
                    "solref": _CLOSURE_SOLREF,
                    "solimp": _CLOSURE_SOLIMP,
                },
            )
        elif constraint_type in {"connect", "coincident", "revolute"}:
            ET.SubElement(
                equality_root,
                "connect",
                {
                    "name": closure.closure_id,
                    "site1": site_a.site_name,
                    "site2": site_b.site_name,
                    "solref": _CLOSURE_SOLREF,
                    "solimp": _CLOSURE_SOLIMP,
                },
            )
            if closure.constraint.metadata.get("axis_alignment_required"):
                axis_offset_m = 1e-3
                axis_sites: list[str] = []
                for endpoint, site in ((endpoint_a, site_a), (endpoint_b, site_b)):
                    pose = connector_relative_poses[endpoint]
                    offset = rotate_vector(pose=pose, vector=(0.0, 0.0, axis_offset_m))
                    axis_site_name = f"{closure.closure_id}__axis__{len(axis_sites)}"
                    ET.SubElement(
                        body_elements[site.body_name],
                        "site",
                        {
                            "name": axis_site_name,
                            "pos": _fmt(
                                tuple(pose.position_m[index] + offset[index] for index in range(3))
                            ),
                            "quat": _fmt(_backend_quat(pose.orientation_xyzw)),
                            "type": "sphere",
                            "size": "0.0001",
                        },
                    )
                    axis_sites.append(axis_site_name)
                ET.SubElement(
                    equality_root,
                    "connect",
                    {
                        "name": f"{closure.closure_id}__axis",
                        "site1": axis_sites[0],
                        "site2": axis_sites[1],
                        "solref": _CLOSURE_SOLREF,
                        "solimp": _CLOSURE_SOLIMP,
                    },
                )
        else:
            raise BackendCapabilityFailure(
                "backend cannot compile this Closure type",
                object_ids=(closure.closure_id,),
                details={"constraint_type": constraint_type},
            )

    # Add one reusable fixed tendon per movable public Joint.  Scenario-specific
    # actuators are enabled through model parameters in solve_scenario().
    for index, (joint_id, expression) in enumerate(sorted(joint_expressions.items())):
        if not expression.coefficients:
            continue
        _add_fixed_tendon(
            tendon_root,
            name=f"observable_tendon_{index}",
            expression=expression,
            group_joint_names=group_joint_names,
        )
    return (
        ET.tostring(root, encoding="unicode"),
        MappingProxyType(group_joint_names),
        tuple(component_sites),
        tuple(connector_sites),
    )


def compile_assembly(
    *, assembly: AssemblyModel, disabled_constraint_ids: Iterable[str] = (),
    solver_iterations: int | None = None, solver_tolerance: float | None = None,
    rigid_body_properties: Mapping[str, Any] | None = None,
) -> _CompiledAssembly:
    """Compile an AssemblyModel into a private physics backend model.

    The returned handle is deliberately private and must not be exposed by a
    public KinCheckAPI function.
    """

    topology = validate_topology(assembly=assembly)
    if not topology.passed:
        raise BackendCapabilityFailure(
            "Assembly topology is invalid for compilation",
            object_ids=tuple(
                dict.fromkeys(
                    object_id
                    for issue in topology.issues
                    for object_id in issue.object_ids
                )
            ),
            details={"issues": [issue.to_dict() for issue in topology.issues]},
        )
    runtime = _require_backend()
    disabled = set(disabled_constraint_ids)
    component_ids = {component.component_id for component in assembly.components}
    for joint in assembly.joints:
        for reference in (joint.connector_a, joint.connector_b):
            if reference.component_id not in component_ids:
                raise BackendCapabilityFailure(
                    "A Joint references an unknown Component",
                    object_ids=(joint.joint_id, reference.component_id),
                )
            _connector_for_ref(assembly, reference)
    for closure in assembly.closures:
        definition = _geometric_residual_definition(
            assembly=assembly, constraint=closure.constraint
        )
        pose_a = _connector_world_pose(assembly=assembly, reference=closure.constraint.connector_a)
        pose_b = _connector_world_pose(assembly=assembly, reference=closure.constraint.connector_b)
        position_residual = (
            math.dist(pose_a.position_m, pose_b.position_m)
            if str(closure.constraint.constraint_type).lower()
            in {"connect", "coincident", "revolute", "weld", "fixed"}
            else abs(math.dist(pose_a.position_m, pose_b.position_m) - definition.expected_distance_m)
        )
        orientation_residual = (
            _axis_alignment_error_rad(actual_a=pose_a, actual_b=pose_b)
            if closure.constraint.metadata.get("axis_alignment_required")
            else orientation_error_rad(
                actual=relative_pose(parent=pose_a, child=pose_b),
                expected=definition.expected_relative_pose,
            )
        )
        if (
            position_residual > closure.position_tolerance_m
            or orientation_residual > closure.orientation_tolerance_rad
        ):
            raise BackendCapabilityFailure(
                "The authored initial pose does not satisfy a Closure tolerance",
                object_ids=(closure.closure_id,),
                details={
                    "position_residual_m": position_residual,
                    "orientation_residual_rad": orientation_residual,
                },
            )
    for constraint in assembly.constraints:
        for reference in (constraint.connector_a, constraint.connector_b):
            if reference.component_id not in component_ids:
                raise BackendCapabilityFailure(
                    "A Constraint references an unknown Component",
                    object_ids=(constraint.constraint_id, reference.component_id),
                )
            _connector_for_ref(assembly, reference)
    for closure in assembly.closures:
        for reference in (
            closure.constraint.connector_a,
            closure.constraint.connector_b,
        ):
            if reference.component_id not in component_ids:
                raise BackendCapabilityFailure(
                    "A Closure references an unknown Component",
                    object_ids=(closure.closure_id, reference.component_id),
                )
            _connector_for_ref(assembly, reference)
    component_groups, groups = _joint_groups(assembly)
    grounded_groups = {
        component_groups[ground.component_id]
        for ground in assembly.grounds
        if ground.component_id in component_groups
    }
    group_parents, group_depths, group_modes, tree_joints, closure_joints = _group_tree(
        assembly,
        component_groups=component_groups,
        groups=groups,
        grounded_groups=grounded_groups,
    )
    group_world_expressions = _world_expressions(
        parents=group_parents,
        grounded_groups=grounded_groups,
        modes=group_modes,
    )
    moving_groups = set(group_modes) - grounded_groups
    joint_expressions: dict[str, _LinearExpression] = {}
    for joint in assembly.joints:
        joint_expressions[joint.joint_id] = _relative_expression(
            joint.connector_a.component_id,
            joint.connector_b.component_id,
            component_groups=component_groups,
            moving_groups=moving_groups,
            group_world_expressions=group_world_expressions,
        )
    group_joint_limits = _group_joint_limits(
        assembly=assembly,
        joint_expressions=joint_expressions,
        movable_group_ids=moving_groups,
    )

    mesh_constraints = tuple(
        constraint
        for constraint in assembly.constraints
        if constraint.constraint_id not in disabled and constraint.constraint_type in _MESH_TYPES
    )
    unsupported_constraints = tuple(
        constraint
        for constraint in assembly.constraints
        if constraint.constraint_id not in disabled and constraint.constraint_type not in _MESH_TYPES
    )
    if unsupported_constraints:
        raise BackendCapabilityFailure(
            "backend cannot compile one or more general Constraint types",
            object_ids=tuple(item.constraint_id for item in unsupported_constraints),
            details={
                "constraint_types": sorted({item.constraint_type for item in unsupported_constraints})
            },
        )
    supports = _mesh_support_frames(
        assembly,
        component_groups=component_groups,
        group_parents=group_parents,
        group_depths=group_depths,
    )
    expressions = [
        _mesh_expression(
            assembly=assembly,
            constraint=constraint,
            component_groups=component_groups,
            moving_groups=moving_groups,
            supports=supports,
            group_world_expressions=group_world_expressions,
        )
        for constraint in mesh_constraints
    ]
    geometric_residuals = tuple(
        _geometric_residual_definition(assembly=assembly, constraint=constraint)
        for constraint in mesh_constraints
        if constraint.constraint_type in {"gear", "belt"}
    )
    geometric_residuals += tuple(
        _GeometricResidualDefinition(
            constraint_id=closure.closure_id,
            endpoint_a=definition.endpoint_a,
            endpoint_b=definition.endpoint_b,
            expected_distance_m=(
                0.0
                if str(closure.constraint.constraint_type).lower()
                in {"connect", "coincident", "revolute", "weld", "fixed"}
                else definition.expected_distance_m
            ),
            expected_relative_pose=definition.expected_relative_pose,
            axis_only=bool(
                closure.constraint.metadata.get("axis_alignment_required", False)
            ),
        )
        for closure in assembly.closures
        for definition in (
            _geometric_residual_definition(assembly=assembly, constraint=closure.constraint),
        )
    )
    expressions.extend(
        _coupling_expression(coupling, joint_expressions=joint_expressions)
        for coupling in assembly.couplings
        if coupling.coupling_id not in disabled
    )
    warnings: list[str] = []
    ignored_phase_ids = tuple(
        constraint.constraint_id
        for constraint in mesh_constraints
        if constraint.metadata.get("phase_offset") not in (None, 0, 0.0)
    )
    if ignored_phase_ids:
        warnings.append(
            "Mesh phase offsets are treated as part of the imported initial CAD pose; "
            "the backend solves displacement from that pose."
        )
    model_xml, group_joint_names, component_sites, connector_sites = _build_xml(
        assembly=assembly,
        component_groups=component_groups,
        groups=groups,
        grounded_groups=grounded_groups,
        group_modes=group_modes,
        group_parents=group_parents,
        tree_joints=tree_joints,
        group_joint_limits=group_joint_limits,
        joint_expressions=joint_expressions,
        constraint_expressions=tuple(expressions),
        solver_iterations=solver_iterations,
        solver_tolerance=solver_tolerance,
        rigid_body_properties=rigid_body_properties,
    )
    try:
        model = runtime.MjModel.from_xml_string(model_xml)
    except Exception as cause:
        raise BackendCompileFailure(
            f"physics backend could not compile the generated Assembly model: {cause}",
            model_xml=model_xml,
        ) from cause
    return _CompiledAssembly(
        assembly=assembly,
        model=model,
        model_xml=model_xml,
        component_groups=component_groups,
        group_joint_names=group_joint_names,
        group_modes=group_modes,
        group_parents=group_parents,
        group_depths=group_depths,
        group_world_expressions=group_world_expressions,
        joint_expressions=MappingProxyType(joint_expressions),
        constraint_expressions=tuple(expressions),
        geometric_residuals=geometric_residuals,
        closure_joints=closure_joints,
        component_sites=component_sites,
        connector_sites=connector_sites,
        warnings=tuple(warnings),
    )


def _profile_value(profile: MotionProfile, time_s: float, boundary: str = "hold") -> float:
    boundary = getattr(boundary, "value", boundary)
    points = profile.points
    if boundary == "error" and (time_s < points[0].time_s or time_s > points[-1].time_s):
        raise BackendSolveFailure("profile evaluated outside its declared range", time_s=float(time_s))
    if time_s <= points[0].time_s:
        return 0.0 if boundary == "zero" and time_s < points[0].time_s else float(points[0].value)
    if time_s >= points[-1].time_s:
        return 0.0 if boundary == "zero" and time_s > points[-1].time_s else float(points[-1].value)
    for left, right in zip(points, points[1:]):
        if left.time_s <= time_s < right.time_s:
            if profile.interpolation == Interpolation.STEP:
                return float(left.value)
            fraction = (time_s - left.time_s) / (right.time_s - left.time_s)
            return float(left.value + fraction * (right.value - left.value))
    return float(points[-1].value)  # pragma: no cover - bounded above


def _profile_slope(profile: MotionProfile, time_s: float) -> float:
    if profile.interpolation == Interpolation.STEP or len(profile.points) < 2:
        return 0.0
    for left, right in zip(profile.points, profile.points[1:]):
        if left.time_s <= time_s <= right.time_s:
            return float((right.value - left.value) / (right.time_s - left.time_s))
    return 0.0


def _speed_driver_value(driver: Any, time_s: float, boundary: str = "hold") -> float:
    boundary = getattr(boundary, "value", boundary)
    if driver.active_interval_s is not None:
        start_time_s, end_time_s = driver.active_interval_s
        if time_s < start_time_s or time_s > end_time_s:
            return 0.0
    return _profile_value(driver.profile, time_s, boundary)


def _group_values(compiled: _CompiledAssembly, data: Any) -> tuple[dict[str, float], dict[str, float]]:
    runtime = _require_backend()
    positions: dict[str, float] = {}
    velocities: dict[str, float] = {}
    for group_id, joint_name in compiled.group_joint_names.items():
        joint_id = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, joint_name)
        positions[group_id] = float(data.qpos[int(compiled.model.jnt_qposadr[joint_id])])
        velocities[group_id] = float(data.qvel[int(compiled.model.jnt_dofadr[joint_id])])
    return positions, velocities


def _joint_values(
    compiled: _CompiledAssembly, group_values: Mapping[str, float]
) -> dict[str, float]:
    return {
        joint_id: expression.evaluate(group_values)
        for joint_id, expression in compiled.joint_expressions.items()
    }


def _site_pose(model: Any, data: Any, site_name: str) -> BackendPose:
    runtime = _require_backend()
    site_id = runtime.mj_name2id(model, runtime.mjtObj.mjOBJ_SITE, site_name)
    import numpy as np

    quaternion_wxyz = np.zeros(4, dtype=float)
    runtime.mju_mat2Quat(quaternion_wxyz, np.asarray(data.site_xmat[site_id], dtype=float))
    w, x, y, z = (float(value) for value in quaternion_wxyz)
    return BackendPose(
        position_m=tuple(float(value) for value in data.site_xpos[site_id]),  # type: ignore[arg-type]
        orientation_xyzw=(x, y, z, w),
    )


def _site_spatial_motion(
    model: Any,
    data: Any,
    site_name: str,
    *,
    include_acceleration: bool,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float] | None,
    tuple[float, float, float] | None,
]:
    """Return site linear/angular motion in world orientation and SI units."""

    runtime = _require_backend()
    import numpy as np

    site_id = runtime.mj_name2id(model, runtime.mjtObj.mjOBJ_SITE, site_name)
    velocity = np.zeros(6, dtype=float)
    runtime.mj_objectVelocity(
        model, data, runtime.mjtObj.mjOBJ_SITE, site_id, velocity, 0
    )
    angular_velocity = tuple(float(value) for value in velocity[:3])
    linear_velocity = tuple(float(value) for value in velocity[3:])
    if not include_acceleration:
        return linear_velocity, angular_velocity, None, None

    acceleration = np.zeros(6, dtype=float)
    runtime.mj_objectAcceleration(
        model, data, runtime.mjtObj.mjOBJ_SITE, site_id, acceleration, 0
    )
    angular_acceleration = tuple(float(value) for value in acceleration[:3])
    linear_acceleration = tuple(float(value) for value in acceleration[3:])
    return linear_velocity, angular_velocity, linear_acceleration, angular_acceleration


def _as_pose(value: BackendPose) -> Pose:
    return Pose(position_m=value.position_m, orientation_xyzw=value.orientation_xyzw)


def _axis_alignment_error_rad(*, actual_a: Pose, actual_b: Pose) -> float:
    axis_a = rotate_vector(pose=actual_a, vector=(0.0, 0.0, 1.0))
    axis_b = rotate_vector(pose=actual_b, vector=(0.0, 0.0, 1.0))
    dot = abs(sum(axis_a[index] * axis_b[index] for index in range(3)))
    return math.acos(max(-1.0, min(1.0, dot)))


def _sample(
    compiled: _CompiledAssembly,
    data: Any,
    *,
    requested_component_ids: set[str] | None,
    include_acceleration: bool,
) -> BackendSample:
    group_positions, group_velocities = _group_values(compiled, data)
    residual_component_ids = {
        component_id
        for definition in compiled.geometric_residuals
        for component_id, _connector_id in (definition.endpoint_a, definition.endpoint_b)
    }
    connector_sample_ids = (
        None
        if requested_component_ids is None
        else requested_component_ids | residual_component_ids
    )
    component_measurements = {
        item.component_id: (
            _site_pose(compiled.model, data, item.site_name),
            _site_spatial_motion(
                compiled.model,
                data,
                item.site_name,
                include_acceleration=include_acceleration,
            ),
        )
        for item in compiled.component_sites
        if requested_component_ids is None or item.component_id in requested_component_ids
    }
    connector_measurements = {
        (item.component_id, item.connector_id): (
            _site_pose(compiled.model, data, item.site_name),
            _site_spatial_motion(
                compiled.model,
                data,
                item.site_name,
                include_acceleration=include_acceleration,
            ),
        )
        for item in compiled.connector_sites
        if connector_sample_ids is None or item.component_id in connector_sample_ids
    }
    component_poses = {key: value[0] for key, value in component_measurements.items()}
    component_linear_velocities = {
        key: value[1][0] for key, value in component_measurements.items()
    }
    component_angular_velocities = {
        key: value[1][1] for key, value in component_measurements.items()
    }
    component_linear_accelerations = {
        key: value[1][2]
        for key, value in component_measurements.items()
        if value[1][2] is not None
    }
    component_angular_accelerations = {
        key: value[1][3]
        for key, value in component_measurements.items()
        if value[1][3] is not None
    }
    returned_connector_measurements = {
        key: value
        for key, value in connector_measurements.items()
        if requested_component_ids is None or key[0] in requested_component_ids
    }
    connector_poses = {
        key: value[0] for key, value in returned_connector_measurements.items()
    }
    connector_linear_velocities = {
        key: value[1][0] for key, value in returned_connector_measurements.items()
    }
    connector_angular_velocities = {
        key: value[1][1] for key, value in returned_connector_measurements.items()
    }
    connector_linear_accelerations = {
        key: value[1][2]
        for key, value in returned_connector_measurements.items()
        if value[1][2] is not None
    }
    connector_angular_accelerations = {
        key: value[1][3]
        for key, value in returned_connector_measurements.items()
        if value[1][3] is not None
    }
    equation_residuals = {
        item.constraint_id: item.expression.evaluate(group_positions) - item.offset
        for item in compiled.constraint_expressions
    }
    position_residuals: dict[str, float] = {}
    orientation_residuals: dict[str, float] = {}
    for definition in compiled.geometric_residuals:
        measurement_a = connector_measurements.get(definition.endpoint_a)
        measurement_b = connector_measurements.get(definition.endpoint_b)
        endpoint_a = None if measurement_a is None else measurement_a[0]
        endpoint_b = None if measurement_b is None else measurement_b[0]
        if endpoint_a is None or endpoint_b is None:
            # Requested component filtering may omit one endpoint.  A missing
            # site cannot be treated as a zero residual or as a violation.
            continue
        pose_a = _as_pose(endpoint_a)
        pose_b = _as_pose(endpoint_b)
        position_residuals[definition.constraint_id] = abs(
            math.dist(pose_a.position_m, pose_b.position_m)
            - definition.expected_distance_m
        )
        if definition.axis_only:
            orientation_residuals[definition.constraint_id] = _axis_alignment_error_rad(
                actual_a=pose_a,
                actual_b=pose_b,
            )
        else:
            orientation_residuals[definition.constraint_id] = orientation_error_rad(
                actual=relative_pose(parent=pose_a, child=pose_b),
                expected=definition.expected_relative_pose,
            )
    return BackendSample(
        time_s=float(data.time),
        joint_positions=_joint_values(compiled, group_positions),
        joint_velocities=_joint_values(compiled, group_velocities),
        component_poses=component_poses,
        connector_poses=connector_poses,
        component_linear_velocities=component_linear_velocities,
        component_angular_velocities=component_angular_velocities,
        component_linear_accelerations=component_linear_accelerations,
        component_angular_accelerations=component_angular_accelerations,
        connector_linear_velocities=connector_linear_velocities,
        connector_angular_velocities=connector_angular_velocities,
        connector_linear_accelerations=connector_linear_accelerations,
        connector_angular_accelerations=connector_angular_accelerations,
        constraint_residuals=equation_residuals,
        constraint_equation_residuals=equation_residuals,
        constraint_position_residuals=position_residuals,
        constraint_orientation_residuals=orientation_residuals,
    )


def _integration_sample(
    compiled: _CompiledAssembly,
    data: Any,
    *,
    requested_component_ids: set[str] | None,
) -> BackendIntegrationSample:
    return BackendIntegrationSample(
        time_s=float(data.time),
        component_poses={
            item.component_id: _site_pose(compiled.model, data, item.site_name)
            for item in compiled.component_sites
            if requested_component_ids is None
            or item.component_id in requested_component_ids
        },
    )


def _solve_initial_state_system(
    *,
    compiled: _CompiledAssembly,
    entries: Sequence[Any],
    system: str,
) -> tuple[dict[str, float], dict[str, Any]]:
    import numpy as np

    group_ids = tuple(sorted(compiled.group_joint_names))
    ordered_entries = tuple(sorted(entries, key=lambda item: item.joint_id))
    if not ordered_entries:
        return (
            {group_id: 0.0 for group_id in group_ids},
            {
                "source": "default_zero",
                "status": "default_zero",
                "rank": 0,
                "row_count": 0,
                "column_count": len(group_ids),
                "residual_norm": 0.0,
                "maximum_absolute_error": 0.0,
                "joint_ids": [],
                "redundant": False,
                "verification": [],
            },
        )

    rows: list[list[float]] = []
    targets: list[float] = []
    joint_ids: list[str] = []
    for entry in ordered_entries:
        expression = compiled.joint_expressions.get(entry.joint_id)
        if expression is None:
            raise BackendCapabilityFailure(
                "Initial state references an unknown Joint",
                object_ids=(entry.joint_id,),
            )
        rows.append([float(expression.coefficients.get(group_id, 0.0)) for group_id in group_ids])
        targets.append(float(entry.value))
        joint_ids.append(entry.joint_id)

    matrix = np.asarray(rows, dtype=float)
    target_vector = np.asarray(targets, dtype=float)
    if group_ids:
        solution, _lstsq_residuals, rank, _singular_values = np.linalg.lstsq(
            matrix, target_vector, rcond=None
        )
    else:
        solution = np.zeros(0, dtype=float)
        rank = 0
    residual_vector = matrix @ solution - target_vector
    residual_norm = float(np.linalg.norm(residual_vector))
    maximum_absolute_error = float(
        np.max(np.abs(residual_vector)) if residual_vector.size else 0.0
    )
    rank_value = int(rank)
    redundant = len(rows) > rank_value
    if residual_norm > _INITIAL_STATE_TOLERANCE:
        status = "inconsistent"
    elif rank_value < len(group_ids):
        status = "underconstrained"
    elif redundant:
        status = "overconstrained_consistent"
    else:
        status = "unique"
    return (
        {group_id: float(solution[index]) for index, group_id in enumerate(group_ids)},
        {
            "source": "scenario",
            "system": system,
            "status": status,
            "rank": rank_value,
            "row_count": len(rows),
            "column_count": len(group_ids),
            "residual_norm": residual_norm,
            "maximum_absolute_error": maximum_absolute_error,
            "tolerance": _INITIAL_STATE_TOLERANCE,
            "joint_ids": joint_ids,
            "redundant": redundant,
            "verification": [
                {
                    "joint_id": joint_id,
                    "target": targets[index],
                    "actual": float(targets[index] + residual_vector[index]),
                    "error": float(residual_vector[index]),
                }
                for index, joint_id in enumerate(joint_ids)
            ],
        },
    )


def _verify_initial_state_system(
    *,
    compiled: _CompiledAssembly,
    entries: Sequence[Any],
    actual_group_values: Mapping[str, float],
    diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    if not entries:
        return dict(diagnostics)
    verification = []
    for entry in sorted(entries, key=lambda item: item.joint_id):
        expression = compiled.joint_expressions[entry.joint_id]
        actual = float(expression.evaluate(actual_group_values))
        target = float(entry.value)
        verification.append(
            {
                "joint_id": entry.joint_id,
                "target": target,
                "actual": actual,
                "error": actual - target,
            }
        )
    residual_norm = math.sqrt(sum(item["error"] ** 2 for item in verification))
    maximum_absolute_error = max((abs(item["error"]) for item in verification), default=0.0)
    result = dict(diagnostics)
    result.update(
        {
            "post_write_residual_norm": residual_norm,
            "post_write_maximum_absolute_error": maximum_absolute_error,
            "verification": verification,
        }
    )
    if residual_norm > _INITIAL_STATE_TOLERANCE:
        result["status"] = "inconsistent"
    return result


def _write_group_state(compiled: _CompiledAssembly, data: Any, values: Mapping[str, float], *, velocity: bool) -> None:
    runtime = _require_backend()
    for group_id, value in values.items():
        joint_name = compiled.group_joint_names.get(group_id)
        if joint_name is None:
            continue
        joint_id = runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_JOINT, joint_name)
        if velocity:
            data.qvel[int(compiled.model.jnt_dofadr[joint_id])] = value
        else:
            data.qpos[int(compiled.model.jnt_qposadr[joint_id])] = value


def _write_lock_state(
    *, compiled: _CompiledAssembly, data: Any, lock_values: Mapping[str, float]
) -> None:
    """Project locked public Joint values onto the single backend coordinate."""

    if not lock_values:
        return
    runtime = _require_backend()
    for joint_id, target in lock_values.items():
        expression = compiled.joint_expressions.get(joint_id)
        if expression is None or len(expression.coefficients) != 1:
            continue
        group_id, coefficient = next(iter(expression.coefficients.items()))
        joint_name = compiled.group_joint_names.get(group_id)
        if joint_name is None or abs(float(coefficient)) <= 1e-15:
            continue
        backend_joint_id = runtime.mj_name2id(
            compiled.model, runtime.mjtObj.mjOBJ_JOINT, joint_name
        )
        data.qpos[int(compiled.model.jnt_qposadr[backend_joint_id])] = (
            float(target) / float(coefficient)
        )
        data.qvel[int(compiled.model.jnt_dofadr[backend_joint_id])] = 0.0
    runtime.mj_forward(compiled.model, data)


def _finite_difference_vectors(
    *,
    samples: Sequence[BackendSample],
    field_name: str,
) -> tuple[dict[Any, tuple[float, float, float]], ...]:
    if len(samples) < 2:
        return tuple({} for _sample_value in samples)
    mappings = tuple(getattr(sample, field_name) for sample in samples)
    keys = set(mappings[0])
    for mapping in mappings[1:]:
        keys.intersection_update(mapping)
    results: list[dict[Any, tuple[float, float, float]]] = []
    for index, sample in enumerate(samples):
        if index == 0:
            left, right = 0, 1
        elif index == len(samples) - 1:
            left, right = len(samples) - 2, len(samples) - 1
        else:
            left, right = index - 1, index + 1
        elapsed = float(samples[right].time_s - samples[left].time_s)
        results.append(
            {
                key: tuple(
                    (float(mappings[right][key][axis]) - float(mappings[left][key][axis]))
                    / elapsed
                    for axis in range(3)
                )
                for key in keys
            }
        )
    return tuple(results)


def _add_finite_difference_accelerations(
    samples: Sequence[BackendSample],
) -> tuple[BackendSample, ...]:
    component_linear = _finite_difference_vectors(
        samples=samples, field_name="component_linear_velocities"
    )
    component_angular = _finite_difference_vectors(
        samples=samples, field_name="component_angular_velocities"
    )
    connector_linear = _finite_difference_vectors(
        samples=samples, field_name="connector_linear_velocities"
    )
    connector_angular = _finite_difference_vectors(
        samples=samples, field_name="connector_angular_velocities"
    )
    return tuple(
        replace(
            sample,
            component_linear_accelerations=component_linear[index],
            component_angular_accelerations=component_angular[index],
            connector_linear_accelerations=connector_linear[index],
            connector_angular_accelerations=connector_angular[index],
        )
        for index, sample in enumerate(samples)
    )


def _add_scenario_controls(
    compiled: _CompiledAssembly,
    scenario: Scenario,
    *,
    lock_values: Mapping[str, float] | None = None,
) -> Mapping[str, int]:
    """Mutate only the private compiled model by rebuilding it with actuators."""

    root = ET.fromstring(compiled.model_xml)
    tendon_root = root.find("tendon")
    if tendon_root is None:  # pragma: no cover - generated XML invariant
        tendon_root = ET.SubElement(root, "tendon")
    actuator_root = ET.SubElement(root, "actuator")
    equality_root = root.find("equality")
    if equality_root is None:  # pragma: no cover - generated XML invariant
        equality_root = ET.SubElement(root, "equality")
    for joint_id, target in sorted(dict(lock_values or {}).items()):
        expression = compiled.joint_expressions.get(joint_id)
        if expression is None:
            raise BackendCapabilityFailure(
                "A Scenario lock references an unknown Joint",
                object_ids=(scenario.scenario_id, joint_id),
            )
        if len(expression.coefficients) != 1:
            raise BackendCapabilityFailure(
                "A locked Joint must map to one backend coordinate",
                object_ids=(scenario.scenario_id, joint_id),
                details={"coordinate_count": len(expression.coefficients)},
            )
        group_id, coefficient = next(iter(expression.coefficients.items()))
        joint_name = compiled.group_joint_names.get(group_id)
        if joint_name is None or abs(float(coefficient)) <= 1e-15:
            raise BackendCapabilityFailure(
                "A locked Joint must map to a movable backend coordinate",
                object_ids=(scenario.scenario_id, joint_id),
            )
        ET.SubElement(
            equality_root,
            "joint",
            {
                "name": f"lock_{joint_id}",
                "joint1": joint_name,
                "polycoef": f"{float(target) / float(coefficient):.17g} 0 0 0 0",
                "solref": "0.001 1",
                "solimp": "0.99 0.9999 0.001",
            },
        )
    actuator_names: dict[str, str] = {}
    for driver_kind, drivers in (
        ("position", scenario.position_drivers),
        ("speed", scenario.speed_drivers),
    ):
        for index, driver in enumerate(drivers):
            expression = compiled.joint_expressions.get(driver.joint_id)
            if expression is None:
                raise BackendCapabilityFailure(
                    "A Scenario driver references an unknown Joint",
                    object_ids=(scenario.scenario_id, driver.joint_id),
                )
            if not expression.coefficients:
                raise BackendCapabilityFailure(
                    "A fixed Joint cannot be driven",
                    object_ids=(scenario.scenario_id, driver.joint_id),
                )
            tendon_name = f"driver_tendon_{driver_kind}_{index}"
            actuator_name = f"driver_actuator_{driver_kind}_{index}"
            _add_fixed_tendon(
                tendon_root,
                name=tendon_name,
                expression=expression,
                group_joint_names=compiled.group_joint_names,
            )
            attributes = {
                "name": actuator_name,
                "tendon": tendon_name,
            }
            if driver_kind == "position":
                attributes.update({"kp": str(_POSITION_KP), "kv": str(_POSITION_KV)})
            else:
                attributes.update({"kv": "100"})
            ET.SubElement(
                actuator_root,
                "position" if driver_kind == "position" else "velocity",
                attributes,
            )
            actuator_names[f"{driver_kind}:{driver.joint_id}"] = actuator_name
    model_xml = ET.tostring(root, encoding="unicode")
    runtime = _require_backend()
    try:
        compiled.model = runtime.MjModel.from_xml_string(model_xml)
    except Exception as cause:
        raise BackendCompileFailure(
            f"physics backend could not compile Scenario actuators: {cause}", model_xml=model_xml
        ) from cause
    return MappingProxyType(
        {
            key: runtime.mj_name2id(compiled.model, runtime.mjtObj.mjOBJ_ACTUATOR, value)
            for key, value in actuator_names.items()
        }
    )


def solve_scenario(*, scenario: Scenario, options: Any = None) -> BackendSolveResult:
    """Run a Scenario with physics backend and return backend-independent samples."""

    runtime = _require_backend()
    if scenario.duration_s is None or scenario.sample_period_s is None:
        raise BackendCapabilityFailure(
            "Scenario duration and sample period must be set before solving",
            object_ids=(scenario.scenario_id,),
        )
    duration_s = float(scenario.duration_s)
    sample_period_s = float(scenario.sample_period_s)
    if not math.isfinite(duration_s) or duration_s <= 0.0:
        raise BackendCapabilityFailure("Scenario duration must be finite and positive", object_ids=(scenario.scenario_id,))
    if not math.isfinite(sample_period_s) or sample_period_s <= 0.0:
        raise BackendCapabilityFailure("Scenario sample period must be finite and positive", object_ids=(scenario.scenario_id,))
    compiled = compile_assembly(
        assembly=scenario.assembly,
        disabled_constraint_ids=scenario.disabled_constraint_ids,
        solver_iterations=(int(options.max_constraint_iterations) if options is not None else None),
        solver_tolerance=(min(float(options.position_residual_tolerance_m), float(options.orientation_residual_tolerance_rad)) if options is not None else None),
    )
    initial_source = getattr(scenario, "initial_state_source", "explicit")
    source_positions = scenario.joint_home_positions if initial_source == "home" else scenario.initial_joint_positions
    initial_lock_values = {item.joint_id: float(item.value) for item in source_positions}
    lock_values = {
        lock.joint_id: (
            initial_lock_values.get(lock.joint_id, 0.0)
            if lock.position_rad_or_m is None
            else float(lock.position_rad_or_m)
        )
        for lock in scenario.locked_joints
    }
    initial_position_entries = tuple(
        JointValue(joint_id=joint_id, value=value)
        for joint_id, value in sorted(
            (
                {
                    item.joint_id: float(item.value)
                    for item in source_positions
                }
                | lock_values
            ).items()
        )
    )
    actuator_ids = _add_scenario_controls(compiled, scenario, lock_values=lock_values)
    # Save the configured cap before shortening individual steps to land on
    # output timestamps. A short remainder must not shrink subsequent steps.
    max_timestep_s = float(compiled.model.opt.timestep)
    if options is not None and getattr(options, "max_integration_step_s", None) is not None:
        max_timestep_s = min(max_timestep_s, float(options.max_integration_step_s))
        compiled.model.opt.timestep = max_timestep_s
    if options is not None and bool(getattr(options, "adaptive_sampling", False)):
        # Adaptive mode refines the internal step cap relative to the requested
        # output period while preserving the authored output timestamps.
        max_timestep_s = min(max_timestep_s, sample_period_s / 4.0)
        compiled.model.opt.timestep = max_timestep_s
    max_substeps = int(getattr(options, "max_integration_substeps", 1000000))
    integration_step_count = 0
    runtime_warnings: list[str] = []
    partial_due_nonfinite = False
    data = runtime.MjData(compiled.model)

    group_positions, position_diagnostics = _solve_initial_state_system(
        compiled=compiled,
        entries=initial_position_entries,
        system="position",
    )
    group_velocities, velocity_diagnostics = _solve_initial_state_system(
        compiled=compiled,
        entries=scenario.initial_joint_velocities,
        system="velocity",
    )
    initial_state_diagnostics = {
        "position": position_diagnostics,
        "velocity": velocity_diagnostics,
    }
    inconsistent_systems = tuple(
        name
        for name, diagnostics in initial_state_diagnostics.items()
        if diagnostics["status"] == "inconsistent"
    )
    if inconsistent_systems:
        joint_ids = tuple(
            joint_id
            for name in inconsistent_systems
            for joint_id in initial_state_diagnostics[name]["joint_ids"]
        )
        raise BackendInitialStateFailure(
            "Initial Joint states form an inconsistent linear system",
            object_ids=(scenario.scenario_id, *joint_ids),
            details={"initial_state": initial_state_diagnostics},
        )
    _write_group_state(compiled, data, group_positions, velocity=False)
    _write_group_state(compiled, data, group_velocities, velocity=True)

    runtime.mj_forward(compiled.model, data)
    _write_lock_state(compiled=compiled, data=data, lock_values=lock_values)
    actual_group_positions, actual_group_velocities = _group_values(compiled, data)
    position_diagnostics = _verify_initial_state_system(
        compiled=compiled,
        entries=initial_position_entries,
        actual_group_values=actual_group_positions,
        diagnostics=position_diagnostics,
    )
    velocity_diagnostics = _verify_initial_state_system(
        compiled=compiled,
        entries=scenario.initial_joint_velocities,
        actual_group_values=actual_group_velocities,
        diagnostics=velocity_diagnostics,
    )
    initial_state_diagnostics = {
        "position": position_diagnostics,
        "velocity": velocity_diagnostics,
    }
    inconsistent_systems = tuple(
        name
        for name, diagnostics in initial_state_diagnostics.items()
        if diagnostics["status"] == "inconsistent"
    )
    if inconsistent_systems:
        joint_ids = tuple(
            joint_id
            for name in inconsistent_systems
            for joint_id in initial_state_diagnostics[name]["joint_ids"]
        )
        raise BackendInitialStateFailure(
            "Initial Joint state changed after it was written to the backend",
            object_ids=(scenario.scenario_id, *joint_ids),
            details={"initial_state": initial_state_diagnostics},
        )
    requested_component_ids = (
        None
        if scenario.component_result_scope is ComponentResultScope.ALL
        else (
            {request.component_id for request in scenario.component_result_requests}
            if scenario.component_result_requests
            else None
        )
    )
    integration_component_ids = (
        None
        if scenario.integration_component_ids is None
        else set(scenario.integration_component_ids)
    )
    acceleration_available = callable(getattr(runtime, "mj_objectAcceleration", None))
    initial_sample = _sample(
        compiled,
        data,
        requested_component_ids=requested_component_ids,
        include_acceleration=acceleration_available,
    )
    samples = [initial_sample]
    integration_samples = (
        [
            _integration_sample(
                compiled,
                data,
                requested_component_ids=integration_component_ids,
            )
        ]
        if scenario.capture_integration_steps else []
    )
    sample_count = int(math.floor(duration_s / sample_period_s + 1e-12))
    sample_times = [index * sample_period_s for index in range(1, sample_count + 1)]
    if not sample_times or sample_times[-1] < duration_s - 1e-12:
        sample_times.append(duration_s)
    for target_time in sample_times:
        while data.time < target_time - 1e-12:
            integration_step_count += 1
            if integration_step_count > max_substeps:
                raise BackendSolveFailure(
                    "maximum integration substeps exceeded",
                    time_s=float(data.time),
                    last_valid_samples=tuple(samples),
                )
            remaining = target_time - float(data.time)
            compiled.model.opt.timestep = min(max_timestep_s, remaining)
            for driver in scenario.position_drivers:
                time_s = float(data.time)
                data.ctrl[actuator_ids[f"position:{driver.joint_id}"]] = (
                    _profile_value(driver.profile, time_s, getattr(scenario, "profile_boundary", "hold"))
                    + (_POSITION_KV / _POSITION_KP)
                    * _profile_slope(driver.profile, time_s)
                )
            for driver in scenario.speed_drivers:
                data.ctrl[actuator_ids[f"speed:{driver.joint_id}"]] = _speed_driver_value(
                    driver, float(data.time), getattr(scenario, "profile_boundary", "hold")
                )
            previous_qpos = data.qpos.copy()
            previous_qvel = data.qvel.copy()
            try:
                runtime.mj_step(compiled.model, data)
            except Exception as cause:
                raise BackendSolveFailure(
                    f"physics backend failed while stepping the Scenario: {cause}",
                    time_s=float(data.time),
                    last_valid_samples=tuple(samples),
                ) from cause
            _write_lock_state(compiled=compiled, data=data, lock_values=lock_values)
            if not all(math.isfinite(float(value)) for value in (*data.qpos, *data.qvel)):
                if options is not None and options.non_finite_state_policy == "warn":
                    data.qpos[:] = previous_qpos
                    data.qvel[:] = previous_qvel
                    runtime.mj_forward(compiled.model, data)
                    runtime_warnings.append(
                        f"Non-finite state encountered at t={float(data.time):.12g}s; retained the last finite state."
                    )
                    partial_due_nonfinite = True
                    break
                raise BackendSolveFailure(
                    "physics backend produced non-finite joint state",
                    time_s=float(data.time),
                    last_valid_samples=tuple(samples),
                )
            if scenario.capture_integration_steps:
                integration_samples.append(
                    _integration_sample(
                        compiled,
                        data,
                        requested_component_ids=integration_component_ids,
                    )
                )
        if partial_due_nonfinite:
            break
        samples.append(
            _sample(
                compiled,
                data,
                requested_component_ids=requested_component_ids,
                include_acceleration=acceleration_available,
            )
        )

    if not acceleration_available:
        samples = list(_add_finite_difference_accelerations(samples))

    initial_state_warnings = tuple(
        f"Initial {name} state is {diagnostics['status']}."
        for name, diagnostics in initial_state_diagnostics.items()
        if diagnostics["status"] in {"underconstrained", "overconstrained_consistent"}
    )

    return BackendSolveResult(
        backend_name="solver",
        backend_version=str(runtime.__version__),
        assembly_id=scenario.assembly_id,
        scenario_id=scenario.scenario_id,
        samples=tuple(samples),
        integration_samples=tuple(integration_samples),
        warnings=(*compiled.warnings, *runtime_warnings, *initial_state_warnings),
        model_summary={
            "components": len(scenario.assembly.components),
            "joints": len(scenario.assembly.joints),
            "degrees_of_freedom": int(compiled.model.nv),
            "constraints": int(compiled.model.neq),
            "actuators": int(compiled.model.nu),
        },
        metadata={
            "solve_options": (options.to_dict() if hasattr(options, "to_dict") else dict(options or {})),
            "effective_integration_step_s": max_timestep_s,
            "effective_max_integration_substeps": max_substeps,
            "effective_constraint_iterations": int(options.max_constraint_iterations) if options is not None else int(_CLOSURE_SOLVER_ITERATIONS if scenario.assembly.closures else 100),
            "effective_solver_tolerance": float(compiled.model.opt.tolerance),
            "partial_due_nonfinite": partial_due_nonfinite,
            "non_finite_state_policy": getattr(options, "non_finite_state_policy", "fail"),
            "initial_state_source": initial_source,
            "initial_state": initial_state_diagnostics,
            "spatial_kinematics": {
                "reference_frame": "world",
                "velocity_source": "solver_object_velocity",
                "acceleration_source": (
                    "solver_object_acceleration"
                    if acceleration_available
                    else "finite_difference_of_spatial_velocity"
                ),
            },
        },
    )


__all__ = [
    "BackendCapabilityFailure",
    "BackendCompileFailure",
    "BackendInitialStateFailure",
    "BackendIntegrationSample",
    "BackendPose",
    "BackendSample",
    "BackendSolveFailure",
    "BackendSolveResult",
    "BackendUnavailable",
    "compile_assembly",
    "solve_scenario",
]
