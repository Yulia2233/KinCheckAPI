"""Convert CADIR MJCF exports into KinCheckAPI assembly models."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET

from .diagnostics import ValidationResult
from .errors import MJCFAdapterError
from .pose import Pose, compose_pose, relative_pose, rotate_vector


@dataclass(frozen=True)
class AdapterResult:
    assembly: Any
    source_map: Mapping[str, Any]


def _mjcf_number_list(
    *,
    value: str | None,
    count: int,
    field: str,
    path: Path,
) -> tuple[float, ...]:
    if value is None:
        values = (0.0,) * count
    else:
        try:
            values = tuple(float(item) for item in value.split())
        except (AttributeError, TypeError, ValueError) as cause:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NONFINITE",
                message=f"MJCF attribute {field!r} must contain numeric values.",
                source_paths=(str(path),),
                suggested_actions=("Regenerate the MJCF export with finite numeric attributes.",),
            ) from cause
    if len(values) != count or not all(math.isfinite(item) for item in values):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-NONFINITE",
            message=f"MJCF attribute {field!r} must contain {count} finite values.",
            source_paths=(str(path),),
            suggested_actions=("Regenerate the MJCF export with finite numeric attributes.",),
        )
    return values


def _mjcf_pose(*, element: ET.Element, path: Path, length_scale: float = 1.0) -> Pose:
    position = _mjcf_number_list(
        value=element.get("pos"), count=3, field="pos", path=path
    )
    raw_quat = (
        (1.0, 0.0, 0.0, 0.0)
        if element.get("quat") is None
        else _mjcf_number_list(
            value=element.get("quat"), count=4, field="quat", path=path
        )
    )
    # MJCF uses wxyz quaternions; KinCheckAPI's Pose uses xyzw.
    return Pose(
        position_m=tuple(value * length_scale for value in position),
        orientation_xyzw=(raw_quat[1], raw_quat[2], raw_quat[3], raw_quat[0]),
    )


def _mjcf_axis_frame(
    *,
    axis: tuple[float, float, float],
    path: Path,
    position_m: tuple[float, float, float],
) -> Pose:
    """Build a frame whose local +Z axis is the supplied MJCF axis."""

    norm = math.sqrt(sum(value * value for value in axis))
    if not math.isfinite(norm) or norm <= 1.0e-15:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-JOINT-AXIS-INVALID",
            message="MJCF joint axis must be a finite non-zero vector.",
            source_paths=(str(path),),
            suggested_actions=(
                "Regenerate the MJCF with a normalized non-zero joint axis.",
            ),
        )
    target = tuple(value / norm for value in axis)
    dot = max(-1.0, min(1.0, target[2]))
    if dot >= 1.0 - 1.0e-12:
        quaternion = (0.0, 0.0, 0.0, 1.0)
    elif dot <= -1.0 + 1.0e-12:
        quaternion = (1.0, 0.0, 0.0, 0.0)
    else:
        # Quaternion from (0, 0, 1) to target: cross(z, target), 1 + dot.
        raw = (-target[1], target[0], 0.0, 1.0 + dot)
        raw_norm = math.sqrt(sum(value * value for value in raw))
        quaternion = tuple(value / raw_norm for value in raw)
    return Pose(position_m=position_m, orientation_xyzw=quaternion)


def _mjcf_validate_finite(value: Any, *, path: Path, field: str = "mapping") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _mjcf_validate_finite(item, path=path, field=f"{field}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _mjcf_validate_finite(item, path=path, field=f"{field}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-NONFINITE",
            message=f"Mapping value {field} must be finite.",
            source_paths=(str(path),),
            suggested_actions=("Regenerate the mapping without NaN or infinite values.",),
        )


def _mjcf_read_mapping(*, path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message=f"Cannot read CADIR MJCF mapping: {path}",
            source_paths=(str(path),),
            suggested_actions=("Regenerate the CADIR MJCF mapping and retry.",),
        ) from cause
    if not isinstance(value, dict):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="CADIR MJCF mapping root must be an object.",
            source_paths=(str(path),),
            suggested_actions=("Export a supported CADIR MJCF mapping schema.",),
        )
    _mjcf_validate_finite(value, path=path)
    if str(value.get("schema_version")) != "1.0":
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message=f"Unsupported CADIR MJCF mapping schema: {value.get('schema_version')!r}.",
            source_paths=(str(path),),
            details={"supported": "1.0"},
            suggested_actions=("Regenerate the mapping with the supported CADIR exporter.",),
        )
    return value


def _mjcf_resolve_asset(
    *,
    xml_path: Path,
    asset_root: Path,
    raw_file: str,
    mesh_name: str,
) -> Path:
    if not isinstance(raw_file, str) or not raw_file.strip():
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message=f"Mesh {mesh_name!r} has no file path.",
            source_paths=(str(xml_path),),
            object_ids=(mesh_name,),
            suggested_actions=("Regenerate the MJCF with a relative mesh file path.",),
        )
    candidate = (xml_path.parent / raw_file).resolve()
    try:
        candidate.relative_to(asset_root)
    except ValueError as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-ASSET-OUTSIDE-ROOT",
            message=f"Mesh path escapes the allowed asset root: {raw_file!r}.",
            source_paths=(str(xml_path), str(asset_root)),
            object_ids=(mesh_name,),
            suggested_actions=("Keep MJCF mesh assets under the declared asset_root.",),
        ) from cause
    if not candidate.is_file():
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-FILE-MISSING",
            message=f"MJCF mesh asset does not exist: {candidate}",
            source_paths=(str(candidate),),
            object_ids=(mesh_name,),
            suggested_actions=("Copy the CADIR exporter mesh directory beside the XML.",),
        )
    return candidate


def _mjcf_make_clearance_stl(
    *,
    mesh_paths: Mapping[str, str],
    mesh_scales: Mapping[str, tuple[float, ...]],
    mesh_poses: Mapping[str, tuple[Pose, ...]],
    asset_root: Path,
    group_id: str,
) -> Path:
    """Normalize an MJCF OBJ mesh set to the existing STL clearance contract."""

    try:
        import trimesh
    except (ImportError, OSError) as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-ASSET-FORMAT-UNSUPPORTED",
            message="OBJ-to-STL normalization requires trimesh.",
            source_paths=tuple(mesh_paths.values()),
            suggested_actions=("Install trimesh or provide STL clearance assets.",),
        ) from cause
    try:
        meshes = []
        for definition_id, raw_path in sorted(mesh_paths.items()):
            loaded = trimesh.load_mesh(raw_path, file_type="obj", process=True)
            if isinstance(loaded, trimesh.Scene):
                loaded = loaded.dump(concatenate=True)
            if not isinstance(loaded, trimesh.Trimesh):
                raise ValueError(f"OBJ asset {raw_path} did not produce one triangle mesh")
            scale = mesh_scales.get(definition_id, (1.0, 1.0, 1.0))
            if len(scale) != 3 or not all(math.isfinite(value) and value > 0.0 for value in scale):
                raise ValueError(f"OBJ asset {raw_path} has an invalid mesh scale")
            transforms = mesh_poses.get(definition_id) or (Pose(),)
            for pose in transforms:
                copied = loaded.copy()
                copied.vertices *= scale
                x, y, z, w = pose.orientation_xyzw
                matrix = trimesh.transformations.quaternion_matrix((w, x, y, z))
                matrix[:3, 3] = pose.position_m
                copied.apply_transform(matrix)
                meshes.append(copied)
        if not meshes:
            raise ValueError("no OBJ meshes were supplied")
        combined = trimesh.util.concatenate(meshes)
        if len(combined.vertices) == 0 or len(combined.faces) == 0:
            raise ValueError("normalized mesh has no vertices or triangles")
        if (
            not bool(combined.is_watertight)
            or not bool(combined.is_winding_consistent)
            or float(combined.volume) <= 0.0
        ):
            raise ValueError(
                "normalized mesh must be a closed, consistently oriented solid"
            )
        digest = hashlib.sha256()
        digest.update(group_id.encode("utf-8"))
        for definition_id, raw_path in sorted(mesh_paths.items()):
            digest.update(definition_id.encode("utf-8"))
            digest.update(Path(raw_path).read_bytes())
            digest.update(repr(mesh_scales.get(definition_id, (1.0, 1.0, 1.0))).encode("ascii"))
            digest.update(repr(mesh_poses.get(definition_id, (Pose(),))).encode("ascii"))
        destination = asset_root / ".kincheckapi-stl" / f"{digest.hexdigest()}.stl"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file():
            combined.export(destination, file_type="stl")
        return destination
    except MJCFAdapterError:
        raise
    except Exception as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-ASSET-FORMAT-UNSUPPORTED",
            message="The OBJ meshes could not be normalized into a valid collision solid.",
            source_paths=tuple(mesh_paths.values()),
            object_ids=(group_id,),
            details={"native_error_type": type(cause).__name__},
            suggested_actions=("Provide valid closed OBJ meshes or pre-exported STL assets.",),
        ) from cause


def _mjcf_xml_records(
    *,
    xml_path: Path,
    asset_root: Path,
) -> tuple[
    ET.Element,
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    try:
        root = ET.parse(xml_path).getroot()
    except (OSError, ET.ParseError) as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-XML-INVALID",
            message=f"Cannot parse MJCF XML: {xml_path}",
            source_paths=(str(xml_path),),
            suggested_actions=("Regenerate the CADIR MJCF export and retry.",),
        ) from cause
    if root.tag != "mujoco":
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-XML-INVALID",
            message="MJCF root element must be <mujoco>.",
            source_paths=(str(xml_path),),
            suggested_actions=("Provide an MJCF document.",),
        )
    # Validate explicit axes before backend compilation so malformed CADIR
    # input receives the adapter's structured axis error instead of a generic
    # XML compilation failure.
    for joint_element in root.iter("joint"):
        raw_axis = joint_element.get("axis")
        axis = (
            (0.0, 0.0, 1.0)
            if raw_axis is None
            else _mjcf_number_list(
                value=raw_axis,
                count=3,
                field="joint.axis",
                path=xml_path,
            )
        )
        _mjcf_axis_frame(
            axis=axis,
            path=xml_path,
            position_m=(0.0, 0.0, 0.0),
        )
    try:
        import mujoco

        mujoco.MjModel.from_xml_path(str(xml_path))
    except Exception as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-XML-INVALID",
            message="The CADIR MJCF could not be compiled.",
            source_paths=(str(xml_path),),
            details={"native_error_type": type(cause).__name__},
            suggested_actions=("Fix the MJCF XML and its mesh assets before conversion.",),
        ) from cause

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="MJCF must contain a worldbody.",
            source_paths=(str(xml_path),),
            suggested_actions=("Export an MJCF with an explicit grounded worldbody.",),
        )
    bodies: dict[str, dict[str, Any]] = {}
    joints: dict[str, dict[str, Any]] = {}
    sites: dict[str, dict[str, Any]] = {}
    geoms: list[dict[str, Any]] = []
    mesh_assets: dict[str, dict[str, Any]] = {}
    equalities: dict[str, dict[str, Any]] = {}
    mesh_root = root.find("asset")
    for mesh in () if mesh_root is None else mesh_root.findall("mesh"):
        name = str(mesh.get("name", ""))
        if not name or name in mesh_assets:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="MJCF mesh names must be non-empty and unique.",
                source_paths=(str(xml_path),),
                object_ids=(name,),
                suggested_actions=("Regenerate the MJCF with unique mesh names.",),
            )
        raw_scale = (
            (1.0, 1.0, 1.0)
            if mesh.get("scale") is None
            else _mjcf_number_list(
                value=mesh.get("scale"), count=3, field="mesh.scale", path=xml_path
            )
        )
        mesh_assets[name] = {
            "path": _mjcf_resolve_asset(
                xml_path=xml_path,
                asset_root=asset_root,
                raw_file=str(mesh.get("file", "")),
                mesh_name=name,
            ),
            "scale": raw_scale,
            "file": str(mesh.get("file", "")),
        }

    def visit_body(
        *,
        element: ET.Element,
        parent_name: str | None,
        parent_pose: Pose,
    ) -> None:
        name = str(element.get("name", ""))
        if not name or name in bodies:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="MJCF body names must be non-empty and unique.",
                source_paths=(str(xml_path),),
                object_ids=(name,),
                suggested_actions=("Regenerate the MJCF with unique body names.",),
            )
        pose = compose_pose(
            parent=parent_pose,
            child=_mjcf_pose(element=element, path=xml_path),
        )
        bodies[name] = {"element": element, "parent": parent_name, "pose": pose}
        for joint in element.findall("joint"):
            joint_name = str(joint.get("name", ""))
            if not joint_name or joint_name in joints:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-MAPPING-INVALID",
                    message="MJCF joint names must be non-empty and unique.",
                    source_paths=(str(xml_path),),
                    object_ids=(joint_name,),
                    suggested_actions=("Regenerate the MJCF with unique joint names.",),
                )
            joints[joint_name] = {"element": joint, "body": name, "pose": pose}
        for site in element.findall("site"):
            site_name = str(site.get("name", ""))
            if not site_name or site_name in sites:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-MAPPING-INVALID",
                    message="MJCF site names must be non-empty and unique.",
                    source_paths=(str(xml_path),),
                    object_ids=(site_name,),
                    suggested_actions=("Regenerate the MJCF with unique site names.",),
                )
            sites[site_name] = {
                "element": site,
                "body": name,
                "pose": compose_pose(
                    parent=pose,
                    child=_mjcf_pose(element=site, path=xml_path),
                ),
            }
        for geom in element.findall("geom"):
            mesh_name = geom.get("mesh")
            if mesh_name is not None and mesh_name not in mesh_assets:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NAME-UNRESOLVED",
                    message=f"MJCF geom references unknown mesh {mesh_name!r}.",
                    source_paths=(str(xml_path),),
                    object_ids=(name, str(mesh_name)),
                    suggested_actions=("Regenerate the MJCF with matching asset mesh names.",),
                )
            geoms.append({"element": geom, "body": name, "mesh": mesh_name})
        for child in element.findall("body"):
            visit_body(element=child, parent_name=name, parent_pose=pose)

    identity = Pose()
    for child in worldbody.findall("body"):
        visit_body(element=child, parent_name=None, parent_pose=identity)
    for geom in worldbody.findall("geom"):
        mesh_name = geom.get("mesh")
        if mesh_name is not None and mesh_name not in mesh_assets:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"MJCF geom references unknown mesh {mesh_name!r}.",
                source_paths=(str(xml_path),),
                object_ids=(str(mesh_name),),
                suggested_actions=("Regenerate the MJCF with matching asset mesh names.",),
            )
        geoms.append({"element": geom, "body": None, "mesh": mesh_name})
    for site in worldbody.findall("site"):
        site_name = str(site.get("name", ""))
        if not site_name or site_name in sites:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="MJCF site names must be non-empty and unique.",
                source_paths=(str(xml_path),),
                object_ids=(site_name,),
                suggested_actions=("Regenerate the MJCF with unique site names.",),
            )
        sites[site_name] = {
            "element": site,
            "body": None,
            "pose": _mjcf_pose(element=site, path=xml_path),
        }
    equality_root = root.find("equality")
    if equality_root is not None:
        for element in list(equality_root):
            name = str(element.get("name", ""))
            if not name or name in equalities:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-MAPPING-INVALID",
                    message="MJCF equality names must be non-empty and unique.",
                    source_paths=(str(xml_path),),
                    object_ids=(name,),
                    suggested_actions=(
                        "Regenerate the MJCF with unique equality names.",
                    ),
                )
            equalities[name] = {
                "type": str(element.tag),
                "attributes": dict(element.attrib),
            }
            if element.tag == "tendon":
                tendon_name = element.get("tendon1")
                tendon = next((item for item in root.findall("./tendon/fixed") if item.get("name") == tendon_name), None)
                if tendon is not None:
                    equalities[name]["joint_coefficients"] = {
                        str(item.get("joint")): float(item.get("coef", "1"))
                        for item in tendon.findall("joint")
                    }
    return root, bodies, joints, sites, geoms, mesh_assets, equalities


def _mjcf_group_records(
    *,
    mapping: Mapping[str, Any],
    bodies: Mapping[str, Mapping[str, Any]],
    xml_path: Path,
) -> tuple[str, dict[str, Mapping[str, Any]], dict[str, str], dict[str, Pose]]:
    raw_groups = mapping.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires a non-empty groups array.",
            source_paths=(str(xml_path),),
            suggested_actions=("Regenerate the MJCF mapping with rigid-group records.",),
        )
    grounded_group = str(mapping.get("grounded_group_id", ""))
    if not grounded_group:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires grounded_group_id.",
            source_paths=(str(xml_path),),
            suggested_actions=("Export an MJCF mapping with one grounded group.",),
        )
    records: dict[str, Mapping[str, Any]] = {}
    group_body: dict[str, str] = {}
    group_pose: dict[str, Pose] = {}
    for raw in raw_groups:
        if not isinstance(raw, Mapping):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Every CADIR MJCF group record must be an object.",
                source_paths=(str(xml_path),),
                suggested_actions=("Regenerate the mapping with valid group records.",),
            )
        group_id = str(raw.get("group_id", ""))
        if not group_id or group_id in records:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="CADIR MJCF group IDs must be non-empty and unique.",
                source_paths=(str(xml_path),),
                object_ids=(group_id,),
                suggested_actions=("Regenerate the mapping with stable group IDs.",),
            )
        body_name = raw.get("body_name")
        if body_name is not None:
            body_name = str(body_name)
            if body_name not in bodies:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NAME-UNRESOLVED",
                    message=f"Mapping group {group_id!r} references missing body {body_name!r}.",
                    source_paths=(str(xml_path),),
                    object_ids=(group_id, body_name),
                    suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
                )
            group_body[group_id] = body_name
            group_pose[group_id] = bodies[body_name]["pose"]
        else:
            group_pose[group_id] = Pose()
        records[group_id] = raw
    if grounded_group not in records or sum(
        1 for group_id in records if bool(records[group_id].get("grounded")) or group_id == grounded_group
    ) != 1:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="CADIR MJCF mapping must identify exactly one grounded group.",
            source_paths=(str(xml_path),),
            object_ids=(grounded_group,),
            suggested_actions=("Regenerate the mapping with one grounded group.",),
        )
    if records[grounded_group].get("body_name") is not None:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="The grounded CADIR MJCF group must map to worldbody, not a movable body.",
            source_paths=(str(xml_path),),
            object_ids=(grounded_group,),
            suggested_actions=("Regenerate the MJCF mapping with body_name=null for ground.",),
        )
    world_groups = [
        group_id for group_id, raw in records.items() if raw.get("body_name") is None
    ]
    if len(world_groups) != 1 or world_groups[0] != grounded_group:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="Exactly one CADIR MJCF group may represent worldbody.",
            source_paths=(str(xml_path),),
            object_ids=tuple(world_groups),
            suggested_actions=("Assign one grounded group to worldbody and all others to MJCF bodies.",),
        )
    return grounded_group, records, group_body, group_pose


def _build_mjcf_assembly(
    *,
    xml_path: Path,
    mapping_path: Path,
    asset_root: Path,
    mapping: Mapping[str, Any],
    bodies: Mapping[str, Mapping[str, Any]],
    joints: Mapping[str, Mapping[str, Any]],
    sites: Mapping[str, Mapping[str, Any]],
    geoms: list[Mapping[str, Any]],
    mesh_assets: Mapping[str, Mapping[str, Any]],
    equalities: Mapping[str, Mapping[str, Any]],
) -> AdapterResult:
    from .assembly import (
        AssemblyModel,
        Closure,
        Component,
        Connector,
        ConnectorRef,
        Constraint,
        Coupling,
        CouplingType,
        Ground,
        Joint,
        JointLimit,
        JointType,
        Part,
        validate_assembly,
        validate_topology,
    )

    (
        grounded_group,
        groups,
        group_body,
        group_pose,
    ) = _mjcf_group_records(mapping=mapping, bodies=bodies, xml_path=xml_path)
    group_by_body = {body_name: group_id for group_id, body_name in group_body.items()}
    raw_meshes = mapping.get("meshes")
    if not isinstance(raw_meshes, Mapping) or not raw_meshes:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires a non-empty meshes object.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with mesh records.",),
        )
    mesh_to_definition = {
        str(mesh_name): str(definition_id)
        for definition_id, mesh_name in raw_meshes.items()
    }
    for mesh_name in mesh_assets:
        if mesh_name not in mesh_to_definition:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message=f"MJCF mesh {mesh_name!r} is missing from mapping.meshes.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(mesh_name,),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
    mesh_ids_by_group: dict[str, list[str]] = {group_id: [] for group_id in groups}
    mesh_poses_by_group: dict[str, dict[str, list[Pose]]] = {
        group_id: {} for group_id in groups
    }
    for geom in geoms:
        mesh_name = geom.get("mesh")
        if mesh_name is None:
            continue
        group_id = (
            group_by_body.get(str(geom.get("body")))
            if geom.get("body") is not None
            else grounded_group
        )
        if group_id is None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Geom body {geom.get('body')!r} is not mapped to a CADIR group.",
                source_paths=(str(xml_path),),
                object_ids=(str(geom.get("body")),),
                suggested_actions=("Regenerate the mapping with every MJCF body assigned to a group.",),
            )
        definition_id = mesh_to_definition[str(mesh_name)]
        if definition_id not in mesh_ids_by_group[group_id]:
            mesh_ids_by_group[group_id].append(definition_id)
        mesh_poses_by_group[group_id].setdefault(definition_id, []).append(
            _mjcf_pose(element=geom["element"], path=xml_path)
        )

    parts: list[Part] = []
    components: list[Component] = []
    for group_id, raw_group in sorted(groups.items()):
        part_id = f"part/{group_id}"
        mesh_ids = tuple(sorted(mesh_ids_by_group[group_id]))
        if not mesh_ids:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-ASSET-MISSING",
                message=f"CADIR group {group_id!r} has no mesh geometry.",
                source_paths=(str(xml_path), str(mapping_path)),
                object_ids=(group_id,),
                suggested_actions=("Export at least one mesh geom for every rigid group.",),
            )
        resolved_meshes: dict[str, str] = {}
        asset_hashes: dict[str, str] = {}
        mesh_scales: dict[str, tuple[float, ...]] = {}
        for definition_id in mesh_ids:
            mesh_name = str(raw_meshes[definition_id])
            asset = mesh_assets[mesh_name]
            path = Path(asset["path"])
            resolved_meshes[definition_id] = str(path)
            asset_hashes[definition_id] = hashlib.sha256(path.read_bytes()).hexdigest()
            mesh_scales[definition_id] = tuple(float(item) for item in asset["scale"])
        scale_values = {
            scale
            for values in mesh_scales.values()
            for scale in values
        }
        uniform_scale = next(iter(scale_values), 1.0)
        mesh_scale_to_m = (
            uniform_scale
            if len(scale_values) == 1 and math.isfinite(uniform_scale)
            else 1.0
        )
        clearance_stl = _mjcf_make_clearance_stl(
            mesh_paths=resolved_meshes,
            mesh_scales=mesh_scales,
            mesh_poses={
                definition_id: tuple(mesh_poses_by_group[group_id][definition_id])
                for definition_id in mesh_ids
            },
            asset_root=asset_root,
            group_id=group_id,
        )
        asset_hashes["stl"] = hashlib.sha256(clearance_stl.read_bytes()).hexdigest()
        parts.append(
            Part(
                part_id=part_id,
                asset_paths={
                    "obj": resolved_meshes[mesh_ids[0]],
                    "stl": str(clearance_stl),
                },
                asset_hashes=asset_hashes,
                display_name=group_id.rsplit("/", 1)[-1],
                source_path=f"{xml_path}#group:{group_id}",
                metadata={
                    "source_group_id": group_id,
                    "mesh_ids": mesh_ids,
                    "mesh_assets": resolved_meshes,
                    "mesh_scales": mesh_scales,
                    "mesh_poses": {
                        definition_id: tuple(mesh_poses_by_group[group_id][definition_id])
                        for definition_id in mesh_ids
                    },
                    # The normalized STL is already in meters. Keep the
                    # source MJCF scales separately for provenance.
                    "mesh_scale_to_m": 1.0,
                    "source_mesh_scale_to_m": mesh_scale_to_m,
                },
            )
        )
        components.append(
            Component(
                component_id=group_id,
                part_id=part_id,
                initial_pose=group_pose[group_id],
                display_name=group_id.rsplit("/", 1)[-1],
                source_path=f"{xml_path}#group:{group_id}",
                metadata={
                    "source_group_id": group_id,
                    "xml_body_name": group_body.get(group_id),
                    "members": tuple(str(item) for item in raw_group.get("members", ())),
                    "grounded": group_id == grounded_group,
                },
            )
        )

    connectors_by_group: dict[str, dict[str, Connector]] = {
        group_id: {} for group_id in groups
    }
    source_map: dict[str, Any] = {
        "schema_version": str(mapping["schema_version"]),
        "xml_path": str(xml_path),
        "mapping_path": str(mapping_path),
        "asset_root": str(asset_root),
        "assembly_id": str(mapping.get("root_definition_id", "")),
        "units": dict(mapping.get("units", {}))
        if isinstance(mapping.get("units"), Mapping)
        else {},
        "provenance_status": "structural_only",
        "xml_sha256": hashlib.sha256(xml_path.read_bytes()).hexdigest(),
        "mesh_id_to_path": {},
        "group_id_to_clearance_stl": {},
        "source_joint_id_to_xml_name": {},
        "source_group_id_to_xml_body": {
            group_id: group_body.get(group_id) for group_id in sorted(groups)
        },
        "source_site_id_to_xml_name": {},
        "source_closure_id_to_xml_equality": {},
    }
    for definition_id, mesh_name in sorted(raw_meshes.items()):
        mesh_name = str(mesh_name)
        asset = mesh_assets.get(mesh_name)
        if asset is None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Mapping references missing MJCF mesh {mesh_name!r}.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(str(definition_id), mesh_name),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
        source_map["mesh_id_to_path"][str(definition_id)] = str(asset["path"])
    for part in parts:
        source_map["group_id_to_clearance_stl"][part.metadata["source_group_id"]] = part.asset_paths["stl"]

    def add_connector(*, group_id: str, connector: Connector) -> None:
        existing = connectors_by_group[group_id].get(connector.connector_id)
        if existing is not None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message=f"Duplicate Connector ID in group {group_id!r}: {connector.connector_id!r}.",
                source_paths=(str(xml_path),),
                object_ids=(group_id, connector.connector_id),
                suggested_actions=("Regenerate the mapping with unique source connector IDs.",),
            )
        connectors_by_group[group_id][connector.connector_id] = connector

    joints_by_source: dict[str, Joint] = {}
    xml_joint_to_source: dict[str, str] = {}
    raw_tree_joints = mapping.get("tree_joints")
    if not isinstance(raw_tree_joints, list):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires tree_joints.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with tree joint records.",),
        )
    for raw in raw_tree_joints:
        if not isinstance(raw, Mapping):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Every tree_joints record must be an object.",
                source_paths=(str(mapping_path),),
                suggested_actions=("Regenerate the mapping with valid tree joint records.",),
            )
        source_id = str(raw.get("joint_id", ""))
        xml_name = str(raw.get("joint_name", ""))
        child_group = str(raw.get("group", ""))
        parent_group = str(raw.get("parent_group", ""))
        if not source_id or not xml_name or child_group not in groups or parent_group not in groups:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-INCOMPLETE",
                message="A tree joint is missing source ID, XML name, or group endpoints.",
                source_paths=(str(mapping_path),),
                object_ids=tuple(item for item in (source_id, xml_name, child_group, parent_group) if item),
                suggested_actions=("Regenerate the mapping with complete tree joint records.",),
            )
        if xml_name in xml_joint_to_source or source_id in joints_by_source:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Tree joint source IDs and XML names must be unique.",
                source_paths=(str(mapping_path),),
                object_ids=(source_id, xml_name),
                suggested_actions=("Regenerate the mapping with stable unique joint IDs.",),
            )
        record = joints.get(xml_name)
        body_name = group_body.get(child_group)
        if record is None or body_name is None or record["body"] != body_name:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Tree joint {source_id!r} does not resolve to its child MJCF body.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(source_id, xml_name, child_group),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
        joint_element = record["element"]
        type_map = {"hinge": JointType.REVOLUTE, "slide": JointType.PRISMATIC}
        joint_type_raw = str(joint_element.get("type", ""))
        mapping_joint_type = str(raw.get("joint_type", ""))
        if mapping_joint_type == "fixed":
            joint_type = JointType.FIXED
        elif joint_type_raw in type_map:
            joint_type = type_map[joint_type_raw]
        else:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message=f"CADIR MJCF joint type {joint_type_raw!r} is not supported by AssemblyModel.",
                source_paths=(str(xml_path),),
                object_ids=(source_id, xml_name),
                suggested_actions=("Export revolute or prismatic tree joints for this adapter.",),
            )
        joint_world = compose_pose(
            parent=record["pose"],
            child=_mjcf_pose(element=joint_element, path=xml_path),
        )
        # The backend defaults an omitted joint axis to the local +Z axis.
        axis_local = (
            (0.0, 0.0, 1.0)
            if joint_element.get("axis") is None
            else _mjcf_number_list(
                value=joint_element.get("axis"),
                count=3,
                field="joint.axis",
                path=xml_path,
            )
        )
        axis_world = compose_pose(
            parent=joint_world,
            child=_mjcf_axis_frame(
                axis=axis_local,
                path=xml_path,
                position_m=(0.0, 0.0, 0.0),
            ),
        )
        connector_a_id = f"__mjcf_joint__{source_id}__parent"
        connector_b_id = f"__mjcf_joint__{source_id}__child"
        add_connector(
            group_id=parent_group,
            connector=Connector(
                connector_id=connector_a_id,
                pose=relative_pose(parent=group_pose[parent_group], child=axis_world),
                display_name=f"{source_id} parent",
                metadata={
                    "source_joint_id": source_id,
                    "xml_joint_name": xml_name,
                    "endpoint": "parent",
                    "axis_local_mjcf": axis_local,
                    "axis_world": rotate_vector(pose=axis_world, vector=(0.0, 0.0, 1.0)),
                },
            ),
        )
        add_connector(
            group_id=child_group,
            connector=Connector(
                connector_id=connector_b_id,
                pose=relative_pose(parent=group_pose[child_group], child=axis_world),
                display_name=f"{source_id} child",
                metadata={
                    "source_joint_id": source_id,
                    "xml_joint_name": xml_name,
                    "endpoint": "child",
                    "axis_local_mjcf": axis_local,
                    "axis_world": rotate_vector(pose=axis_world, vector=(0.0, 0.0, 1.0)),
                },
            ),
        )
        limit = None
        if joint_element.get("range") is not None:
            lower, upper = _mjcf_number_list(
                value=joint_element.get("range"),
                count=2,
                field="joint.range",
                path=xml_path,
            )
            limit = JointLimit(lower=lower, upper=upper)
        joint = Joint(
            joint_id=source_id,
            joint_type=joint_type,
            connector_a=ConnectorRef(parent_group, connector_a_id),
            connector_b=ConnectorRef(child_group, connector_b_id),
            limit=limit,
            display_name=source_id.rsplit("/", 1)[-1],
            source_path=f"{xml_path}#joint:{xml_name}",
            metadata={
                "source_joint_id": source_id,
                "xml_joint_name": xml_name,
                "axis_local_mjcf": axis_local,
                "axis_world": rotate_vector(pose=axis_world, vector=(0.0, 0.0, 1.0)),
            },
        )
        joints_by_source[source_id] = joint
        xml_joint_to_source[xml_name] = source_id
        source_map["source_joint_id_to_xml_name"][source_id] = xml_name

    closure_connectors: dict[str, tuple[ConnectorRef, ConnectorRef]] = {}
    closure_site_world_poses: dict[str, tuple[Pose, Pose]] = {}
    consumed_xml_equalities: set[str] = set()
    raw_closures = mapping.get("closures")
    if not isinstance(raw_closures, list):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires closures.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with closure records.",),
        )
    for raw in raw_closures:
        if not isinstance(raw, Mapping):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Every closure record must be an object.",
                source_paths=(str(mapping_path),),
                suggested_actions=("Regenerate the mapping with valid closure records.",),
            )
        closure_id = str(raw.get("joint_id", ""))
        equality_name = str(raw.get("name", ""))
        raw_sites = raw.get("sites")
        if (
            not closure_id
            or not equality_name
            or not isinstance(raw_sites, list)
            or len(raw_sites) != 2
        ):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-INCOMPLETE",
                message="A closure must contain a source joint ID, equality name, and two sites.",
                source_paths=(str(mapping_path),),
                object_ids=tuple(item for item in (closure_id, equality_name) if item),
                suggested_actions=("Regenerate the mapping with complete closure records.",),
            )
        if not all(isinstance(item, Mapping) for item in raw_sites):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Closure site records must be objects.",
                source_paths=(str(mapping_path),),
                object_ids=(closure_id,),
                suggested_actions=("Regenerate the mapping with valid closure site records.",),
            )
        equality_record = equalities.get(equality_name)
        if equality_record is None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Closure {closure_id!r} references an equality absent from MJCF.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(closure_id, equality_name),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
        if equality_record["type"] != "connect":
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message=f"Closure {closure_id!r} must map to an MJCF equality/connect.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(closure_id, equality_name),
                suggested_actions=("Export loop closures as equality/connect records.",),
            )
        xml_sites = {
            str(equality_record["attributes"].get("site1", "")),
            str(equality_record["attributes"].get("site2", "")),
        }
        mapping_sites = {str(item.get("name", "")) for item in raw_sites}
        if "" in xml_sites or xml_sites != mapping_sites:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message=f"Closure {closure_id!r} site endpoints disagree with MJCF.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(closure_id, equality_name, *sorted(xml_sites | mapping_sites)),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
        if equality_name in consumed_xml_equalities:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message=f"MJCF equality {equality_name!r} is mapped more than once.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(closure_id, equality_name),
                suggested_actions=("Map every MJCF equality to exactly one closure or coupling.",),
            )
        consumed_xml_equalities.add(equality_name)
        refs: list[ConnectorRef] = []
        world_poses: list[Pose] = []
        for raw_site in raw_sites:
            if not isinstance(raw_site, Mapping):
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-MAPPING-INVALID",
                    message="Closure site records must be objects.",
                    source_paths=(str(mapping_path),),
                    object_ids=(closure_id,),
                    suggested_actions=("Regenerate the mapping with valid closure site records.",),
                )
            group_id = str(raw_site.get("group", ""))
            site_name = str(raw_site.get("name", ""))
            site_record = sites.get(site_name)
            if group_id not in groups or site_record is None:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NAME-UNRESOLVED",
                    message=f"Closure {closure_id!r} references an unknown site or group.",
                    source_paths=(str(mapping_path), str(xml_path)),
                    object_ids=(closure_id, group_id, site_name),
                    suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
                )
            if group_body.get(group_id) != site_record["body"]:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-MAPPING-INVALID",
                    message=f"Closure site {site_name!r} is attached to the wrong group.",
                    source_paths=(str(mapping_path), str(xml_path)),
                    object_ids=(closure_id, group_id, site_name),
                    suggested_actions=("Regenerate the mapping with correct closure site ownership.",),
                )
            connector_id = f"__mjcf_site__{site_name}"
            add_connector(
                group_id=group_id,
                connector=Connector(
                    connector_id=connector_id,
                    pose=relative_pose(
                        parent=group_pose[group_id], child=site_record["pose"]
                    ),
                    display_name=site_name,
                    metadata={
                        "source_closure_id": closure_id,
                        "xml_site_name": site_name,
                    },
                ),
            )
            refs.append(ConnectorRef(group_id, connector_id))
            world_poses.append(site_record["pose"])
        closure_connectors[closure_id] = (refs[0], refs[1])
        closure_site_world_poses[closure_id] = (world_poses[0], world_poses[1])
        source_map["source_closure_id_to_xml_equality"][closure_id] = equality_name
        source_map.setdefault("source_closure_id_to_xml_sites", {})[closure_id] = [
            str(item["name"]) for item in raw_sites
        ]

    raw_sites_mapping = mapping.get("sites")
    if not isinstance(raw_sites_mapping, list):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires sites.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with public site records.",),
        )
    for raw in raw_sites_mapping:
        if not isinstance(raw, Mapping):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Every public site record must be an object.",
                source_paths=(str(mapping_path),),
                suggested_actions=("Regenerate the mapping with valid site records.",),
            )
        connector_id = str(raw.get("connector_id", ""))
        site_name = str(raw.get("name", ""))
        group_id = str(raw.get("attached_group", ""))
        if not connector_id:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-INCOMPLETE",
                message="A public CADIR site is missing connector_id.",
                source_paths=(str(mapping_path),),
                object_ids=(site_name, group_id),
                suggested_actions=("Regenerate mapping with stable public connector IDs.",),
            )
        site_record = sites.get(site_name)
        if (
            group_id not in groups
            or site_record is None
            or site_record["body"] != group_body.get(group_id)
        ):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Public connector {connector_id!r} does not resolve to its MJCF site.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(connector_id, group_id, site_name),
                suggested_actions=("Regenerate the mapping and XML from the same CADIR export.",),
            )
        add_connector(
            group_id=group_id,
            connector=Connector(
                connector_id=connector_id,
                pose=relative_pose(
                    parent=group_pose[group_id], child=site_record["pose"]
                ),
                display_name=connector_id,
                metadata={
                    "source_connector_id": connector_id,
                    "connector_snapshot_id": raw.get("connector_snapshot_id"),
                    "xml_site_name": site_name,
                },
            ),
        )
        source_map["source_site_id_to_xml_name"][connector_id] = site_name

    joint_aliases: dict[str, dict[str, Any]] = {}
    for alias in mapping.get("redundant_movable_joints", []):
        if not isinstance(alias, Mapping):
            raise ValueError("A redundant movable joint must be an explicit alias record")
        alias_id = str(alias.get("joint_id", ""))
        canonical = str(alias.get("canonical_joint_id", ""))
        sign = float(alias.get("coordinate_sign", 0.0))
        if not alias_id or alias_id in joints_by_source or alias_id in joint_aliases or canonical not in joints_by_source or sign not in (-1.0, 1.0):
            raise ValueError(f"Invalid movable joint alias {alias_id!r}")
        joint_aliases[alias_id] = {"joint_id": canonical, "coordinate_sign": sign}
    if joint_aliases:
        source_map["joint_aliases"] = joint_aliases

    mesh_constraints: list[Constraint] = []
    mesh_by_id: dict[str, Constraint] = {}
    raw_mesh_constraints = mapping.get("mesh_constraints", [])
    if not isinstance(raw_mesh_constraints, list):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="mesh_constraints must be an array.",
            source_paths=(str(mapping_path),),
        )
    for raw in raw_mesh_constraints:
        if not isinstance(raw, Mapping):
            raise ValueError("Every mesh constraint must be an object")
        constraint_id = str(raw.get("constraint_id", ""))
        kind = str(raw.get("constraint_type", ""))
        if not constraint_id or constraint_id in mesh_by_id or kind not in {"gear", "belt"}:
            raise ValueError("Mesh constraints need unique IDs and a supported gear/belt kind")
        prefix = "pitch_radius" if kind == "gear" else "pulley_radius"
        parameters = raw.get("parameters_m")
        if not isinstance(parameters, Mapping):
            raise ValueError(f"Mesh {constraint_id!r} requires explicit SI radii")
        metadata: dict[str, Any] = {}
        refs: list[ConnectorRef] = []
        for side in ("a", "b"):
            value = float(parameters.get(f"{prefix}_{side}", 0.0))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"Mesh {constraint_id!r} requires positive finite {prefix}_{side}")
            metadata[f"{prefix}_{side}"] = value
            endpoint = raw.get(f"connector_{side}")
            if not isinstance(endpoint, Mapping):
                raise ValueError(f"Mesh {constraint_id!r} is missing connector_{side}")
            group_id, site_name = str(endpoint.get("group", "")), str(endpoint.get("site", ""))
            site_record = sites.get(site_name)
            if group_id not in groups or site_record is None or site_record["body"] != group_body.get(group_id):
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NAME-UNRESOLVED",
                    message=f"Mesh {constraint_id!r} endpoint {side} does not resolve to site {site_name!r}.",
                    object_ids=(constraint_id, site_name, group_id),
                    source_paths=(str(mapping_path), str(xml_path)),
                )
            connector_id = f"mesh/{constraint_id}/{side}"
            add_connector(group_id=group_id, connector=Connector(
                connector_id=connector_id,
                pose=relative_pose(parent=group_pose[group_id], child=site_record["pose"]),
                metadata={"xml_site_name": site_name, "connector_snapshot_id": endpoint.get("connector_snapshot_id")},
            ))
            refs.append(ConnectorRef(group_id, connector_id))
        metadata.update(source_mesh_id=constraint_id, source_phase_offset=raw.get("reference_phase_source_units", 0.0), phase_normalization="initial_pose_encoded", units="m")
        constraint = Constraint(
            constraint_id=constraint_id, constraint_type=kind,
            connector_a=refs[0], connector_b=refs[1],
            source_path=f"{mapping_path}#mesh:{constraint_id}", metadata=metadata,
        )
        mesh_constraints.append(constraint)
        mesh_by_id[constraint_id] = constraint
    source_map["source_mesh_id_to_xml_sites"] = {
        str(raw["constraint_id"]): [raw["connector_a"]["site"], raw["connector_b"]["site"]]
        for raw in raw_mesh_constraints
    }

    joints_list = list(joints_by_source.values())
    closure_values: list[Closure] = []
    for raw in raw_closures:
        closure_id = str(raw["joint_id"])
        refs = closure_connectors[closure_id]
        raw_type = str(raw.get("joint_type", "revolute"))
        joint_type = {
            "revolute": JointType.REVOLUTE,
            "prismatic": JointType.PRISMATIC,
        }.get(raw_type)
        if joint_type is None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message=f"Closure joint type {raw_type!r} cannot be represented.",
                source_paths=(str(mapping_path),),
                object_ids=(closure_id,),
                suggested_actions=("Export revolute or prismatic closure joints.",),
            )
        pose_a, pose_b = closure_site_world_poses[closure_id]
        position_error = math.dist(pose_a.position_m, pose_b.position_m)
        axis_a = rotate_vector(pose=pose_a, vector=(0.0, 0.0, 1.0))
        axis_b = rotate_vector(pose=pose_b, vector=(0.0, 0.0, 1.0))
        axis_dot = abs(sum(axis_a[index] * axis_b[index] for index in range(3)))
        axis_error = math.acos(max(-1.0, min(1.0, axis_dot)))
        position_tolerance_m = float(raw.get("position_tolerance_m", 1.0e-5))
        orientation_tolerance_rad = float(raw.get("orientation_tolerance_rad", 1.0e-5))
        if position_error > position_tolerance_m or (
            joint_type == JointType.REVOLUTE and axis_error > orientation_tolerance_rad
        ):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-TOPOLOGY-INVALID",
                message=f"Closure {closure_id!r} does not satisfy its initial pose tolerances.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(closure_id,),
                details={
                    "position_residual_m": position_error,
                    "axis_alignment_residual_rad": axis_error,
                },
                suggested_actions=("Align the closure sites and axes in the CADIR source model.",),
            )
        joints_list.append(
                Joint(
                joint_id=closure_id,
                joint_type=joint_type,
                connector_a=refs[0],
                connector_b=refs[1],
                display_name=closure_id.rsplit("/", 1)[-1],
                source_path=f"{xml_path}#closure:{closure_id}",
                metadata={
                    "source_closure_id": closure_id,
                    "source_joint_id": raw.get("source_joint_id", closure_id),
                    "xml_equality_name": str(raw["name"]),
                },
            )
        )
        closure_values.append(
            Closure(
                closure_id=closure_id,
                constraint=Constraint(
                    constraint_id=closure_id,
                    connector_a=refs[0],
                    connector_b=refs[1],
                    constraint_type="connect",
                    display_name=closure_id.rsplit("/", 1)[-1],
                    source_path=f"{xml_path}#equality:{raw['name']}",
                    metadata={
                        "source_closure_id": closure_id,
                        "source_joint_id": raw.get("source_joint_id", closure_id),
                        "xml_equality_name": str(raw["name"]),
                        "axis_alignment_required": raw_type == "revolute",
                        "xml_site_names": tuple(
                            str(item["name"]) for item in raw["sites"]
                        ),
                    },
                ),
                position_tolerance_m=position_tolerance_m,
                orientation_tolerance_rad=orientation_tolerance_rad,
            )
        )

    couplings: list[Coupling] = []
    raw_equalities = mapping.get("equalities", [])
    if not isinstance(raw_equalities, list):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="CADIR MJCF equalities must be an array.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with equality records.",),
        )
    declared_mesh_ids = {str(item["mesh_constraint_id"]) for item in raw_equalities if isinstance(item, Mapping) and item.get("mesh_constraint_id") is not None}
    if declared_mesh_ids != set(mesh_by_id):
        raise ValueError("Native mesh constraints and source equality records must resolve bidirectionally")
    for raw in raw_equalities:
        if not isinstance(raw, Mapping) or not bool(raw.get("independent", True)):
            continue
        equality_name = str(raw.get("name", ""))
        if not equality_name:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-INCOMPLETE",
                message="An independent coupling equality is missing its XML name.",
                source_paths=(str(mapping_path),),
                object_ids=(str(raw.get("equality_id", "")),),
                suggested_actions=("Regenerate mapping with the emitted MJCF equality name.",),
            )
        equality_record = equalities.get(equality_name)
        if equality_record is None:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NAME-UNRESOLVED",
                message=f"Coupling equality {equality_name!r} is absent from MJCF.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(str(raw.get("equality_id", "")), equality_name),
                suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
            )
        if equality_record["type"] != "tendon":
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message=f"Coupling equality {equality_name!r} is not an MJCF tendon equality.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(str(raw.get("equality_id", "")), equality_name),
                suggested_actions=("Export gear, belt, or rack-pinion relations as tendon equalities.",),
            )
        if equality_name in consumed_xml_equalities:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message=f"MJCF equality {equality_name!r} is mapped more than once.",
                source_paths=(str(mapping_path), str(xml_path)),
                object_ids=(str(raw.get("equality_id", "")), equality_name),
                suggested_actions=("Map every MJCF equality to exactly one closure or coupling.",),
            )
        consumed_xml_equalities.add(equality_name)
        mesh_id = raw.get("mesh_constraint_id")
        if mesh_id is not None:
            constraint = mesh_by_id.get(str(mesh_id))
            if constraint is None or constraint.constraint_type != str(raw.get("joint_type", "")):
                raise ValueError(f"Equality {equality_name!r} references an absent or mismatched native mesh constraint")
            coefficients = raw.get("coefficients")
            xml_coefficients = equality_record.get("joint_coefficients", {})
            if not isinstance(coefficients, Mapping) or not coefficients or set(coefficients) != set(xml_coefficients):
                raise ValueError(f"Equality {equality_name!r} coefficients do not match its XML tendon")
            for joint_name, value in coefficients.items():
                coefficient = float(value)
                if joint_name not in xml_joint_to_source or not math.isfinite(coefficient) or coefficient == 0.0 or not math.isclose(coefficient, xml_coefficients[joint_name], rel_tol=1e-10, abs_tol=1e-12):
                    raise ValueError(f"Equality {equality_name!r} contains an invalid or mismatched joint coefficient")
            continue
        kind = str(raw.get("joint_type", ""))
        if kind not in {"gear", "belt", "rack_pinion"}:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message=f"Equality type {kind!r} cannot be represented by existing Coupling.",
                source_paths=(str(mapping_path),),
                object_ids=(str(raw.get("equality_id", "")),),
                suggested_actions=("Use a gear, belt, or rack_pinion relation supported by KinCheckAPI.",),
            )
        coefficients = raw.get("coefficients")
        if not isinstance(coefficients, Mapping) or len(coefficients) != 2:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-SEMANTICS-UNSUPPORTED",
                message="Only two-coordinate CADIR equalities can map to an existing Coupling.",
                source_paths=(str(mapping_path),),
                object_ids=(str(raw.get("equality_id", "")),),
                suggested_actions=("Export a two-joint coupling or add a native adapter mapping.",),
            )
        terms: list[tuple[str, float]] = []
        for xml_name, coefficient in coefficients.items():
            source_id = xml_joint_to_source.get(str(xml_name))
            try:
                numeric = float(coefficient)
            except (TypeError, ValueError) as cause:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NONFINITE",
                    message="CADIR equality coefficients must be finite numbers.",
                    source_paths=(str(mapping_path),),
                    object_ids=(str(xml_name),),
                    suggested_actions=("Regenerate mapping with finite equality coefficients.",),
                ) from cause
            if source_id is None or not math.isfinite(numeric) or numeric == 0.0:
                raise MJCFAdapterError(
                    code="KINCHECK-MJCF-NAME-UNRESOLVED",
                    message="CADIR equality coefficient references an unknown or zero joint.",
                    source_paths=(str(mapping_path),),
                    object_ids=(str(xml_name),),
                    suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
                )
            terms.append((source_id, numeric))
        ratio = -terms[1][1] / terms[0][1]
        if not math.isfinite(ratio) or ratio == 0.0:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NONFINITE",
                message="CADIR equality produces an invalid coupling ratio.",
                source_paths=(str(mapping_path),),
                object_ids=(str(raw.get("equality_id", "")),),
                suggested_actions=("Regenerate the coupling with finite non-zero coefficients.",),
            )
        try:
            phase = float(raw.get("reference_phase_source_units", 0.0))
        except (TypeError, ValueError) as cause:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NONFINITE",
                message="CADIR equality phase must be finite.",
                source_paths=(str(mapping_path),),
                suggested_actions=("Regenerate mapping with finite equality phases.",),
            ) from cause
        if not math.isfinite(phase):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-NONFINITE",
                message="CADIR equality phase must be finite.",
                source_paths=(str(mapping_path),),
                object_ids=(str(raw.get("equality_id", "")), equality_name),
                suggested_actions=("Regenerate mapping with finite equality phases.",),
            )
        couplings.append(
            Coupling(
                coupling_id=str(raw.get("equality_id", raw.get("name", ""))),
                coupling_type=CouplingType(kind),
                joint_a_id=terms[0][0],
                joint_b_id=terms[1][0],
                ratio=ratio,
                phase_offset=0.0,
                display_name=str(raw.get("equality_id", raw.get("name", ""))),
                source_path=f"{mapping_path}#equality:{raw.get('name', '')}",
                metadata={
                    "xml_equality_name": raw.get("name"),
                    "coefficients": dict(coefficients),
                    "source_phase_offset": phase,
                    "effective_phase_offset": 0.0,
                    "phase_normalization": "initial_pose_encoded",
                },
            )
        )

    if set(equalities) != consumed_xml_equalities:
        unconsumed = tuple(sorted(set(equalities) - consumed_xml_equalities))
        missing = tuple(sorted(consumed_xml_equalities - set(equalities)))
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="MJCF equalities and mapping relations are not one-to-one.",
            source_paths=(str(mapping_path), str(xml_path)),
            object_ids=(*unconsumed, *missing),
            details={"unmapped_xml_equalities": unconsumed, "missing_xml_equalities": missing},
            suggested_actions=("Regenerate mapping and XML from the same CADIR export.",),
        )

    raw_exclusions = mapping.get("collision_exclusions", ())
    if raw_exclusions is None:
        raw_exclusions = ()
    if not isinstance(raw_exclusions, (list, tuple)):
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="CADIR MJCF collision_exclusions must be an array.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate the mapping with component ID pairs.",),
        )
    collision_exclusions: list[tuple[str, str]] = []
    seen_exclusions: set[tuple[str, str]] = set()
    known_groups = set(groups)
    for raw_pair in raw_exclusions:
        if not isinstance(raw_pair, (list, tuple)) or len(raw_pair) != 2:
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Every collision exclusion must contain exactly two groups.",
                source_paths=(str(mapping_path),),
                suggested_actions=("Regenerate exclusions as two-element group ID pairs.",),
            )
        component_a, component_b = (str(raw_pair[0]), str(raw_pair[1]))
        if (
            not component_a
            or not component_b
            or component_a == component_b
            or component_a not in known_groups
            or component_b not in known_groups
        ):
            raise MJCFAdapterError(
                code="KINCHECK-MJCF-MAPPING-INVALID",
                message="Collision exclusions must reference two distinct known groups.",
                source_paths=(str(mapping_path),),
                object_ids=(component_a, component_b),
                suggested_actions=("Use distinct group IDs present in mapping.groups.",),
            )
        pair = tuple(sorted((component_a, component_b)))
        if pair not in seen_exclusions:
            seen_exclusions.add(pair)
            collision_exclusions.append(pair)

    component_values = tuple(
        Component(
            component_id=component.component_id,
            part_id=component.part_id,
            initial_pose=component.initial_pose,
            connectors=tuple(connectors_by_group[component.component_id].values()),
            display_name=component.display_name,
            source_path=component.source_path,
            metadata=component.metadata,
        )
        for component in components
    )
    assembly_id = str(mapping.get("root_definition_id", ""))
    if not assembly_id:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-INCOMPLETE",
            message="CADIR MJCF mapping requires root_definition_id.",
            source_paths=(str(mapping_path),),
            suggested_actions=("Regenerate mapping with the package root definition ID.",),
        )
    metadata = {
        "units": {"length": "m", "angle": "rad", "mass": "kg", "time": "s"},
        "source_units": dict(mapping.get("units", {}))
        if isinstance(mapping.get("units"), Mapping)
        else {},
        "asset_root": str(asset_root),
        "mesh_scale_to_m": 1.0,
        "mjcf_xml_path": str(xml_path),
        "mjcf_mapping_path": str(mapping_path),
        "mjcf_schema_version": str(mapping.get("schema_version")),
        "provenance_status": "structural_only",
        "source_map": source_map,
    }
    assembly = AssemblyModel(
        assembly_id=assembly_id,
        parts=tuple(parts),
        components=component_values,
        joints=tuple(joints_list),
        constraints=tuple(mesh_constraints),
        couplings=tuple(couplings),
        closures=tuple(closure_values),
        grounds=(Ground(component_id=grounded_group),),
        collision_exclusions=tuple(collision_exclusions),
        display_name=assembly_id,
        source_path=str(xml_path),
        metadata=metadata,
    )
    assembly_validation = validate_assembly(assembly=assembly)
    topology_validation = validate_topology(assembly=assembly)
    validation_issues = tuple((*assembly_validation.issues, *topology_validation.issues))
    if validation_issues:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-TOPOLOGY-INVALID",
            message="CADIR MJCF conversion produced an invalid AssemblyModel.",
            report=ValidationResult(issues=validation_issues),
            source_paths=(str(xml_path), str(mapping_path)),
            suggested_actions=("Fix the CADIR topology or mapping and export again.",),
        )
    return AdapterResult(assembly=assembly, source_map=source_map)


def convert_mjcf(
    *,
    xml_path: str | Path,
    mapping_path: str | Path,
    asset_root: str | Path | None = None,
) -> AdapterResult:
    """Convert a CADIR MJCF export into the existing AssemblyModel.

    This is deliberately a conversion-only entry point. It does not retain a
    backend model and does not change Scenario or solve_motion semantics.
    """

    xml = Path(xml_path).expanduser().resolve()
    mapping = Path(mapping_path).expanduser().resolve()
    if not xml.is_file() or not mapping.is_file():
        missing = tuple(str(path) for path in (xml, mapping) if not path.is_file())
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-FILE-MISSING",
            message="CADIR MJCF XML and mapping files must exist.",
            source_paths=missing,
            suggested_actions=("Provide the XML and mapping generated by CADIR.",),
        )
    assets = (
        Path(asset_root).expanduser().resolve()
        if asset_root is not None
        else xml.parent
    )
    if not assets.is_dir():
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-FILE-MISSING",
            message=f"MJCF asset_root is not a directory: {assets}",
            source_paths=(str(assets),),
            suggested_actions=("Provide the directory containing the CADIR mesh assets.",),
        )
    mapping_data = _mjcf_read_mapping(path=mapping)
    try:
        xml_root = ET.parse(xml).getroot()
        xml_model_name = xml_root.get("model")
    except (OSError, ET.ParseError) as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-XML-INVALID",
            message=f"Cannot inspect MJCF model identity: {xml}",
            source_paths=(str(xml),),
            suggested_actions=("Regenerate the CADIR MJCF export and retry.",),
        ) from cause
    mapping_root_definition_id = str(mapping_data.get("root_definition_id", ""))
    if not xml_model_name:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MODEL-MISSING",
            message="MJCF root element must define a non-empty model attribute.",
            source_paths=(str(xml), str(mapping)),
            object_ids=(mapping_root_definition_id,) if mapping_root_definition_id else (),
            suggested_actions=("Regenerate the CADIR MJCF with model equal to root_definition_id.",),
        )
    if str(xml_model_name) != mapping_root_definition_id:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="MJCF model name and mapping root_definition_id do not match.",
            source_paths=(str(xml), str(mapping)),
            object_ids=(str(xml_model_name), str(mapping_data.get("root_definition_id", ""))),
            suggested_actions=("Regenerate the XML and mapping from the same CADIR package.",),
        )
    (
        _root,
        bodies,
        joints,
        sites,
        geoms,
        mesh_assets,
        equalities,
    ) = _mjcf_xml_records(xml_path=xml, asset_root=assets)
    try:
        return _build_mjcf_assembly(
            xml_path=xml,
            mapping_path=mapping,
            asset_root=assets,
            mapping=mapping_data,
            bodies=bodies,
            joints=joints,
            sites=sites,
            geoms=geoms,
            mesh_assets=mesh_assets,
            equalities=equalities,
        )
    except MJCFAdapterError:
        raise
    except (AttributeError, IndexError, KeyError, OSError, OverflowError, TypeError, ValueError) as cause:
        raise MJCFAdapterError(
            code="KINCHECK-MJCF-MAPPING-INVALID",
            message="The CADIR MJCF and mapping could not be converted into an assembly.",
            source_paths=(str(xml), str(mapping)),
            details={"native_error_type": type(cause).__name__},
            suggested_actions=("Regenerate the CADIR MJCF and mapping from one package revision.",),
        ) from cause
