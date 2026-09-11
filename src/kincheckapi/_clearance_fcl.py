"""Mandatory python-fcl triangle-mesh backend for clearance checks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np

try:
    import trimesh
except (ImportError, OSError):  # pragma: no cover - environment dependent
    trimesh = None  # type: ignore[assignment]

try:
    import rtree  # noqa: F401
except (ImportError, OSError):  # pragma: no cover - environment dependent
    rtree = None  # type: ignore[assignment]

try:
    import fcl
except (ImportError, OSError):  # pragma: no cover - environment dependent
    fcl = None  # type: ignore[assignment]

from .assembly import AssemblyModel, Part
from .clearance_result import _vector
from .errors import BackendCapabilityError
from .pose import Pose, rotate_vector


@dataclass(frozen=True, slots=True)
class MeshModel:
    part_id: str
    path: Path
    model: Any
    vertices: np.ndarray
    faces: np.ndarray
    component_vertex_indices: tuple[np.ndarray, ...]
    watertight: bool
    scale_to_m: float
    vertex_count: int
    triangle_count: int
    sha256: str


_CACHE: dict[tuple[str, int, int, float], MeshModel] = {}


def _connected_component_vertices(faces: np.ndarray, vertex_count: int) -> tuple[np.ndarray, ...]:
    """Group faces by shared vertices without an optional graph dependency."""
    parents = list(range(len(faces)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    first_face_by_vertex: list[int | None] = [None] * vertex_count
    for face_index, face in enumerate(faces):
        for vertex_index in face:
            previous = first_face_by_vertex[int(vertex_index)]
            if previous is None:
                first_face_by_vertex[int(vertex_index)] = face_index
            else:
                union(face_index, previous)
    vertices_by_root: dict[int, set[int]] = {}
    for face_index, face in enumerate(faces):
        vertices_by_root.setdefault(find(face_index), set()).update(int(item) for item in face)
    return tuple(
        np.asarray(sorted(indices), dtype=np.int32)
        for _, indices in sorted(vertices_by_root.items())
    )


def require_backend() -> tuple[Any, str]:
    if fcl is None or trimesh is None or rtree is None:
        missing = tuple(name for name, value in (("python-fcl", fcl), ("trimesh", trimesh), ("rtree", rtree)) if value is None)
        raise BackendCapabilityError(
            code="KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE",
            message="python-fcl, trimesh, and rtree are required for v0.3.0 clearance checks.",
            suggested_actions=("Install the mandatory python-fcl, trimesh, and rtree dependencies.",),
            missing_capabilities=missing,
        )
    return fcl, str(getattr(fcl, "__version__", "unknown"))


def _asset_path(*, assembly: AssemblyModel, part: Part, asset_root: str | Path | None) -> Path | None:
    raw = part.asset_paths.get("stl")
    if not raw:
        return None
    candidate = Path(str(raw)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    roots: list[Path] = []
    if asset_root is not None:
        roots.append(Path(asset_root).expanduser().resolve())
    if assembly.metadata.get("asset_root"):
        roots.append(Path(str(assembly.metadata["asset_root"])).expanduser().resolve())
    for root in roots:
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _mesh_scale(*, assembly: AssemblyModel, part: Part) -> float:
    scale = float(part.metadata.get("mesh_scale_to_m", assembly.metadata.get("mesh_scale_to_m", 1.0)))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("mesh_scale_to_m must be finite and positive")
    return scale


def load_mesh(*, assembly: AssemblyModel, part: Part, asset_root: str | Path | None) -> MeshModel:
    fcl_api, _ = require_backend()
    path = _asset_path(assembly=assembly, part=part, asset_root=asset_root)
    if path is None:
        raise FileNotFoundError(f"STL asset not found for Part {part.part_id}")
    stat = path.stat()
    scale = _mesh_scale(assembly=assembly, part=part)
    cache_key = (str(path), int(stat.st_mtime_ns), int(stat.st_size), scale)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    try:
        # STL files commonly repeat shared vertices per triangle.  Let
        # trimesh merge identical vertices so watertightness is checked on
        # the actual solid topology, while retaining every triangle face.
        loaded = trimesh.load_mesh(path, file_type="stl", process=True)
    except Exception as cause:
        raise ValueError(f"Cannot read STL mesh {path}: {cause}") from cause
    if not isinstance(loaded, trimesh.Trimesh):
        raise ValueError(f"STL asset {path} did not produce one triangle mesh")
    vertices = np.asarray(loaded.vertices, dtype=np.float64)
    faces = np.asarray(loaded.faces, dtype=np.int32)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices):
        raise ValueError(f"STL asset {path} has no valid vertices")
    if faces.ndim != 2 or faces.shape[1] != 3 or not len(faces):
        raise ValueError(f"STL asset {path} has no valid triangles")
    if not np.isfinite(vertices).all():
        raise ValueError(f"STL asset {path} contains non-finite vertices")
    if not bool(loaded.is_watertight) or not bool(loaded.is_winding_consistent) or float(loaded.volume) <= 0.0:
        raise ValueError(
            f"STL asset {path} must be a closed, consistently oriented solid with positive volume"
        )
    scaled = vertices * scale
    model = fcl_api.BVHModel()
    model.beginModel(int(len(scaled)), int(len(faces)))
    model.addSubModel(scaled, faces)
    model.endModel()
    result = MeshModel(
        part_id=part.part_id,
        path=path,
        model=model,
        vertices=scaled,
        faces=faces,
        component_vertex_indices=_connected_component_vertices(faces, len(scaled)),
        watertight=True,
        scale_to_m=scale,
        vertex_count=int(len(scaled)),
        triangle_count=int(len(faces)),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    _CACHE[cache_key] = result
    return result


def _transform(pose: Pose):
    fcl_api, _ = require_backend()
    rotation = np.column_stack([np.asarray(rotate_vector(pose=pose, vector=axis), dtype=np.float64) for axis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))])
    return fcl_api.Transform(rotation, np.asarray(pose.position_m, dtype=np.float64))


def _world_vertices(mesh: MeshModel, pose: Pose) -> np.ndarray:
    rotation = np.column_stack([
        np.asarray(rotate_vector(pose=pose, vector=axis), dtype=np.float64)
        for axis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ])
    return mesh.vertices @ rotation.T + np.asarray(pose.position_m, dtype=np.float64)


def _contains_any_closed_component(container: MeshModel, container_pose: Pose, candidate: MeshModel, candidate_pose: Pose) -> bool:
    """Detect a closed solid fully inside another closed solid.

    FCL reports triangle intersections, but two closed surfaces can have no
    intersecting triangles when one solid is completely enclosed by the other.
    Every candidate vertex is checked with trimesh's ray/triangle containment
    query, so this is still a real mesh test rather than an AABB approximation.
    """
    if not container.watertight or not candidate.watertight:
        raise ValueError("Containment requires watertight meshes")
    container_world = trimesh.Trimesh(
        vertices=_world_vertices(container, container_pose),
        faces=container.faces,
        process=False,
    )
    points = _world_vertices(candidate, candidate_pose)
    try:
        for indices in candidate.component_vertex_indices:
            contained = np.asarray(container_world.contains(points[indices]), dtype=bool)
            if len(contained) and np.all(contained):
                return True
    except Exception as cause:
        raise RuntimeError(f"KINCHECK-CLEARANCE-CONTAINMENT-QUERY-FAILED: {cause}") from cause
    return False


def query_pair(mesh_a: MeshModel, mesh_b: MeshModel, pose_a: Pose, pose_b: Pose) -> tuple[bool, float, tuple[float, float, float] | None, tuple[float, float, float] | None]:
    fcl_api, _ = require_backend()
    object_a = fcl_api.CollisionObject(mesh_a.model, _transform(pose_a))
    object_b = fcl_api.CollisionObject(mesh_b.model, _transform(pose_b))
    collision_result = fcl_api.CollisionResult()
    fcl_api.collide(object_a, object_b, fcl_api.CollisionRequest(num_max_contacts=100, enable_contact=True), collision_result)
    if collision_result.is_collision:
        contacts = tuple(collision_result.contacts)
        positive_depths = tuple(
            float(item.penetration_depth)
            for item in contacts
            if float(item.penetration_depth) > 0.0
        )
        depth = min(positive_depths, default=0.0)
        position = _vector(contacts[0].pos, "contact_position") if contacts else None
        return True, -depth, position, position
    distance_result = fcl_api.DistanceResult()
    fcl_api.distance(object_a, object_b, fcl_api.DistanceRequest(enable_nearest_points=True, enable_signed_distance=True), distance_result)
    nearest: Sequence[Any] = tuple(distance_result.nearest_points or ())
    point_a = _vector(nearest[0], "nearest_point_a") if len(nearest) >= 1 else None
    point_b = _vector(nearest[1], "nearest_point_b") if len(nearest) >= 2 else None
    distance = float(distance_result.min_distance)
    if not math.isfinite(distance) or distance < 0.0:
        raise RuntimeError("KINCHECK-CLEARANCE-DISTANCE-QUERY-INVALID: FCL returned a non-finite distance")
    if _contains_any_closed_component(mesh_a, pose_a, mesh_b, pose_b) or _contains_any_closed_component(mesh_b, pose_b, mesh_a, pose_a):
        return True, -distance, point_a, point_b
    return False, distance, point_a, point_b


__all__ = ["MeshModel", "load_mesh", "query_pair", "require_backend"]
