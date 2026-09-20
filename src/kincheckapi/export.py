"""Read and write portable KinCheck motion packages.

The ``.kincheck`` format is a deterministic ZIP container containing data and
meshes only. It deliberately carries no viewer code or backend-native object.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from types import MappingProxyType
from typing import Any, Mapping
import zipfile

from .assembly import (
    AssemblyModel,
    Pose,
    assembly_from_dict,
    assembly_to_dict,
    validate_assembly,
)
from .diagnostics import Evidence, SimIssue, ValidationResult
from .physics_types import DynamicsModel, StaticResult, PhysicsReport
from .errors import MotionPackageError
from .result import (
    ConstraintEquationResidual,
    ConstraintResidual,
    JointTrajectory,
    IntegrationSample,
    DriverTarget,
    DriverTrajectory,
    LimitEvent,
    MotionResult,
    Trajectory,
)


PACKAGE_SCHEMA_VERSION = "kincheck.motion-package/1.0"
ASSEMBLY_MEMBER = "assembly.json"
MOTION_MEMBER = "motion.json"
VALIDATION_MEMBER = "validation.json"
MANIFEST_MEMBER = "manifest.json"
_MAX_MEMBER_COUNT = 10_000
_MAX_MEMBER_BYTES = 512 * 1024 * 1024
_MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_LENGTH_SCALES_M = {"m": 1.0, "mm": 1e-3, "cm": 1e-2}


def _package_version() -> str:
    try:
        return version("kincheckapi")
    except PackageNotFoundError:  # pragma: no cover - source-only environment
        return "0.5.0"


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionPackageArtifact:
    path: Path
    sha256: str
    bytes: int
    schema_version: str
    component_count: int
    trajectory_count: int
    mesh_count: int
    missing_mesh_part_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "bytes": self.bytes,
            "schema_version": self.schema_version,
            "component_count": self.component_count,
            "trajectory_count": self.trajectory_count,
            "mesh_count": self.mesh_count,
            "missing_mesh_part_ids": list(self.missing_mesh_part_ids),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class MotionPackage:
    path: Path
    manifest: Mapping[str, Any]
    assembly: AssemblyModel
    motion_result: MotionResult
    validation: Mapping[str, Any]
    mesh_members: Mapping[str, str]
    dynamics_model: DynamicsModel | None = None
    static_results: tuple[StaticResult, ...] = ()
    static_checks: tuple[PhysicsReport, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest", MappingProxyType(dict(self.manifest)))
        object.__setattr__(self, "validation", MappingProxyType(dict(self.validation)))
        object.__setattr__(self, "mesh_members", MappingProxyType(dict(self.mesh_members)))

    def read_mesh(self, *, part_id: str) -> bytes:
        member = self.mesh_members[part_id]
        with zipfile.ZipFile(self.path, "r") as archive:
            return archive.read(member)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fail(
    *,
    code: str,
    message: str,
    object_ids: tuple[str, ...] = (),
    source_paths: tuple[str, ...] = (),
    details: Mapping[str, Any] | None = None,
) -> None:
    raise MotionPackageError(
        code=code,
        message=message,
        object_ids=object_ids,
        source_paths=source_paths,
        details=details,
        suggested_actions=("Correct the package inputs or regenerate the .kincheck file.",),
    )


def _resolve_mesh(*, part: Any, asset_root: Path | None) -> Path | None:
    raw = part.asset_paths.get("stl")
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute() and asset_root is not None:
            candidate = asset_root / candidate
        if candidate.is_file():
            return candidate.resolve()
    if asset_root is None:
        return None
    candidates = [asset_root / "parts" / f"{part.part_id}.stl"]
    if part.source_path and part.source_path.endswith(".part.json"):
        candidates.append(asset_root / f"{part.source_path.removesuffix('.part.json')}.stl")
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)


def _mesh_member_name(*, part_id: str, digest: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", part_id).strip("-.") or "part"
    return f"meshes/{slug}-{digest[:12]}.stl"


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _validation_payload(motion_result: MotionResult) -> dict[str, Any]:
    return {
        "schema_version": "kincheck.validation/1.0",
        "status": motion_result.status,
        "issues": [item.to_dict() for item in motion_result.issues],
        "metrics": {
            "maximum_position_residual_m": max(
                (item.position_residual_m for item in motion_result.constraint_residuals),
                default=0.0,
            ),
            "maximum_orientation_residual_rad": max(
                (item.orientation_residual_rad for item in motion_result.constraint_residuals),
                default=0.0,
            ),
        },
    }


def motion_package(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    output_path: str | Path,
    asset_root: str | Path | None = None,
    title: str | None = None,
    require_meshes: bool = False,
    metadata: Mapping[str, Any] | None = None,
    dynamics_model: DynamicsModel | None = None,
    static_results: tuple[StaticResult, ...] = (),
    static_checks: tuple[PhysicsReport, ...] = (),
) -> MotionPackageArtifact:
    """Export backend-independent motion data and meshes to one ``.kincheck`` file."""

    if not isinstance(assembly, AssemblyModel):
        _fail(code="KINCHECK-PACKAGE-ASSEMBLY-INVALID", message="assembly must be an AssemblyModel")
    if not isinstance(motion_result, MotionResult):
        _fail(
            code="KINCHECK-PACKAGE-MOTION-INVALID",
            message="motion_result must be a MotionResult",
        )
    if motion_result.status not in {"completed", "completed_with_warnings"}:
        _fail(
            code="KINCHECK-PACKAGE-MOTION-INCOMPLETE",
            message="Only completed MotionResult values can be exported as an acceptance package.",
            object_ids=(motion_result.scenario_id, motion_result.assembly_id),
            details={"status": motion_result.status},
        )
    if assembly.assembly_id != motion_result.assembly_id:
        _fail(
            code="KINCHECK-PACKAGE-ASSEMBLY-MISMATCH",
            message="MotionResult assembly_id does not match AssemblyModel.",
            object_ids=(assembly.assembly_id, motion_result.assembly_id),
        )
    destination = Path(output_path).expanduser().resolve()
    if destination.suffix.lower() != ".kincheck":
        _fail(
            code="KINCHECK-PACKAGE-EXTENSION-INVALID",
            message="output_path must use the .kincheck extension.",
            source_paths=(str(destination),),
        )
    if destination.exists() and not destination.is_file():
        _fail(
            code="KINCHECK-PACKAGE-OUTPUT-INVALID",
            message="output_path exists and is not a regular file.",
            source_paths=(str(destination),),
        )
    root = Path(asset_root).expanduser().resolve() if asset_root is not None else None
    if root is not None and not root.is_dir():
        _fail(
            code="KINCHECK-PACKAGE-ASSET-ROOT-INVALID",
            message="asset_root must be an existing directory.",
            source_paths=(str(root),),
        )

    payloads: dict[str, bytes] = {
        ASSEMBLY_MEMBER: _json_bytes(assembly_to_dict(assembly=assembly)),
        MOTION_MEMBER: _json_bytes(
            {
                "schema_version": "kincheck.motion/1.0",
                "motion_result": motion_result.to_dict(),
            }
        ),
        VALIDATION_MEMBER: _json_bytes(_validation_payload(motion_result)),
    }
    meshes: list[dict[str, Any]] = []
    missing: list[str] = []
    member_by_digest: dict[str, str] = {}
    units = assembly.metadata.get("units", {})
    source_length_unit = units.get("length", "m") if isinstance(units, Mapping) else "m"
    mesh_scale_to_m = float(
        assembly.metadata.get(
            "mesh_scale_to_m",
            _LENGTH_SCALES_M.get(str(source_length_unit), 1.0),
        )
    )
    if not math.isfinite(mesh_scale_to_m) or mesh_scale_to_m <= 0.0:
        raise MotionPackageError(
            code="KINCHECK-PACKAGE-MESH-SCALE-INVALID",
            message="Assembly mesh_scale_to_m must be finite and positive.",
            object_ids=(assembly.assembly_id,),
        )
    for part in sorted(assembly.parts, key=lambda item: item.part_id):
        source = _resolve_mesh(part=part, asset_root=root)
        if source is None:
            missing.append(part.part_id)
            continue
        content = source.read_bytes()
        digest = _sha256(content)
        member = member_by_digest.get(digest)
        if member is None:
            member = _mesh_member_name(part_id=part.part_id, digest=digest)
            member_by_digest[digest] = member
            payloads[member] = content
        meshes.append(
            {
                "part_id": part.part_id,
                "path": member,
                "format": "stl",
                "scale_to_m": mesh_scale_to_m,
                "sha256": digest,
            }
        )
    if require_meshes and missing:
        _fail(
            code="KINCHECK-PACKAGE-MESH-MISSING",
            message=f"{len(missing)} Part mesh(es) could not be resolved.",
            object_ids=tuple(missing),
            source_paths=(str(root),) if root else (),
        )

    if dynamics_model is not None or static_results:
        from .physics_package import physics_document
        if dynamics_model is None or dynamics_model.assembly != assembly:
            _fail(code="KINCHECK-PACKAGE-ASSEMBLY-MISMATCH", message="Physics assembly differs from motion assembly.")
        payloads["physics.json"] = _json_bytes(physics_document(dynamics_model, static_results, static_checks))

    files = [
        {
            "path": path,
            "bytes": len(content),
            "sha256": _sha256(content),
            "media_type": (
                "application/json" if path.endswith(".json") else "model/stl"
            ),
        }
        for path, content in sorted(payloads.items())
    ]
    manifest = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "generator": {"package": "kincheckapi", "version": _package_version()},
        "title": title or assembly.display_name or assembly.assembly_id,
        "assembly_id": assembly.assembly_id,
        "scenario_id": motion_result.scenario_id,
        "motion_status": motion_result.status,
        "component_result_scope": motion_result.metadata.get(
            "component_result_scope", "requested"
        ),
        "units": {"length": "m", "angle": "rad", "time": "s"},
        "assembly_path": ASSEMBLY_MEMBER,
        "motion_path": MOTION_MEMBER,
        "validation_path": VALIDATION_MEMBER,
        "component_count": len(assembly.components),
        "trajectory_count": len(motion_result.trajectories),
        "sample_count": len(motion_result.sample_times_s),
        "meshes": meshes,
        "missing_mesh_part_ids": missing,
        "metadata": dict(metadata or {}),
        "files": files,
        **({"physics_path": "physics.json", "capabilities": ["mass_properties", "tree_static_equilibrium"]} if dynamics_model is not None else {}),
    }
    manifest_bytes = _json_bytes(manifest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        with zipfile.ZipFile(
            temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            archive.writestr(_zip_info(MANIFEST_MEMBER), manifest_bytes)
            for member, content in sorted(payloads.items()):
                archive.writestr(_zip_info(member), content)
        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as cause:
        _fail(
            code="KINCHECK-PACKAGE-WRITE-FAILED",
            message="The motion package could not be written.",
            source_paths=(str(destination),),
            details={"native_error_type": type(cause).__name__},
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    package_bytes = destination.read_bytes()
    return MotionPackageArtifact(
        path=destination,
        sha256=_sha256(package_bytes),
        bytes=len(package_bytes),
        schema_version=PACKAGE_SCHEMA_VERSION,
        component_count=len(assembly.components),
        trajectory_count=len(motion_result.trajectories),
        mesh_count=len(member_by_digest),
        missing_mesh_part_ids=tuple(missing),
    )


export_motion_package = motion_package


def _issue(
    *,
    code: str,
    message: str,
    path: Path,
    object_ids: tuple[str, ...] = (),
    evidence: Mapping[str, Any] | None = None,
) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="package",
        message=message,
        object_ids=object_ids,
        source_paths=(str(path),),
        evidence=tuple(
            Evidence(key=str(key), actual=value) for key, value in (evidence or {}).items()
        ),
        suggested_actions=("Regenerate the .kincheck package with a compatible KinCheckAPI version.",),
    )


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/") or name.endswith("/"):
        return False
    path = PurePosixPath(name)
    return ".." not in path.parts and path.as_posix() == name


def _json_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> Mapping[str, Any] | None:
    try:
        value = json.loads(archive.read(info).decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def validate_package(*, path: str | Path) -> ValidationResult:
    """Validate structure, hashes, schemas, references, and safe member paths."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        return ValidationResult(
            operation="validate_package",
            issues=(
                _issue(
                    code="KINCHECK-PACKAGE-PATH-NOT-FOUND",
                    message="Motion package file does not exist.",
                    path=source,
                ),
            )
        )
    issues: list[SimIssue] = []
    try:
        archive = zipfile.ZipFile(source, "r")
    except (OSError, zipfile.BadZipFile):
        return ValidationResult(
            operation="validate_package",
            issues=(
                _issue(
                    code="KINCHECK-PACKAGE-ZIP-INVALID",
                    message="Motion package is not a readable ZIP container.",
                    path=source,
                ),
            )
        )
    with archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(infos) > _MAX_MEMBER_COUNT:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-LIMIT-EXCEEDED",
                    message="Motion package contains too many members.",
                    path=source,
                    evidence={"member_count": len(infos), "maximum": _MAX_MEMBER_COUNT},
                )
            )
        unsafe = tuple(name for name in names if not _safe_member_name(name))
        if unsafe:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-PATH-UNSAFE",
                    message="Motion package contains unsafe member paths.",
                    path=source,
                    object_ids=unsafe,
                )
            )
        duplicates = tuple(sorted({name for name in names if names.count(name) > 1}))
        if duplicates:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-DUPLICATE-MEMBER",
                    message="Motion package contains duplicate member names.",
                    path=source,
                    object_ids=duplicates,
                )
            )
        oversized = tuple(
            item.filename for item in infos if item.file_size > _MAX_MEMBER_BYTES
        )
        total_size = sum(item.file_size for item in infos)
        if oversized or total_size > _MAX_TOTAL_BYTES:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-LIMIT-EXCEEDED",
                    message="Motion package exceeds uncompressed size limits.",
                    path=source,
                    object_ids=oversized,
                    evidence={"total_bytes": total_size, "maximum": _MAX_TOTAL_BYTES},
                )
            )
        info_by_name = {item.filename: item for item in infos}
        manifest_info = info_by_name.get(MANIFEST_MEMBER)
        if manifest_info is None:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-MANIFEST-MISSING",
                    message="Motion package lacks manifest.json.",
                    path=source,
                )
            )
            return ValidationResult(issues=tuple(issues), operation="validate_package")
        manifest = _json_member(archive, manifest_info)
        if manifest is None:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-MANIFEST-INVALID",
                    message="manifest.json must contain a UTF-8 JSON object.",
                    path=source,
                )
            )
            return ValidationResult(issues=tuple(issues), operation="validate_package")
        if manifest.get("schema_version") != PACKAGE_SCHEMA_VERSION:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-SCHEMA-UNSUPPORTED",
                    message=f"Unsupported package schema {manifest.get('schema_version')!r}.",
                    path=source,
                    evidence={"supported": PACKAGE_SCHEMA_VERSION},
                )
            )

        raw_files = manifest.get("files")
        declared: dict[str, Mapping[str, Any]] = {}
        if not isinstance(raw_files, list):
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-FILE-INDEX-INVALID",
                    message="Manifest files must be an array.",
                    path=source,
                )
            )
        else:
            for item in raw_files:
                if not isinstance(item, Mapping) or not all(
                    key in item for key in ("path", "bytes", "sha256")
                ):
                    issues.append(
                        _issue(
                            code="KINCHECK-PACKAGE-FILE-INDEX-INVALID",
                            message="Manifest contains an invalid file entry.",
                            path=source,
                        )
                    )
                    continue
                member = str(item["path"])
                if member in declared:
                    issues.append(
                        _issue(
                            code="KINCHECK-PACKAGE-FILE-INDEX-INVALID",
                            message="Manifest contains a duplicate indexed path.",
                            path=source,
                            object_ids=(member,),
                        )
                    )
                declared[member] = item
        archived_payloads = set(names) - {MANIFEST_MEMBER}
        declared_payloads = set(declared)
        missing_members = tuple(sorted(declared_payloads - archived_payloads))
        unindexed_members = tuple(sorted(archived_payloads - declared_payloads))
        if missing_members:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-FILE-MISSING",
                    message="One or more manifest files are missing from the package.",
                    path=source,
                    object_ids=missing_members,
                )
            )
        if unindexed_members:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-FILE-UNINDEXED",
                    message="Package contains files not declared by the manifest.",
                    path=source,
                    object_ids=unindexed_members,
                )
            )
        for member in sorted(declared_payloads & archived_payloads):
            if member not in info_by_name:
                continue
            content = archive.read(info_by_name[member])
            entry = declared[member]
            try:
                expected_bytes = int(entry["bytes"])
            except (TypeError, ValueError):
                expected_bytes = -1
            expected_hash = str(entry["sha256"])
            if len(content) != expected_bytes:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-SIZE-MISMATCH",
                        message=f"Indexed size differs for {member!r}.",
                        path=source,
                        object_ids=(member,),
                    )
                )
            if _sha256(content) != expected_hash:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-HASH-MISMATCH",
                        message=f"Indexed hash differs for {member!r}.",
                        path=source,
                        object_ids=(member,),
                    )
                )

        required_paths = {
            "assembly_path": ASSEMBLY_MEMBER,
            "motion_path": MOTION_MEMBER,
            "validation_path": VALIDATION_MEMBER,
        }
        for key, expected in required_paths.items():
            if manifest.get(key) != expected or expected not in info_by_name:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-REQUIRED-MEMBER-INVALID",
                        message=f"Manifest {key} must reference {expected!r}.",
                        path=source,
                    )
                )

        assembly_data = (
            _json_member(archive, info_by_name[ASSEMBLY_MEMBER])
            if ASSEMBLY_MEMBER in info_by_name
            else None
        )
        motion_data = (
            _json_member(archive, info_by_name[MOTION_MEMBER])
            if MOTION_MEMBER in info_by_name
            else None
        )
        if assembly_data is None:
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-ASSEMBLY-INVALID",
                    message="assembly.json must contain a valid assembly object.",
                    path=source,
                )
            )
        else:
            try:
                converted_assembly = assembly_from_dict(data=assembly_data)
                issues.extend(validate_assembly(assembly=converted_assembly).issues)
            except (KeyError, TypeError, ValueError) as cause:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-ASSEMBLY-INVALID",
                        message="assembly.json could not be reconstructed.",
                        path=source,
                        evidence={"native_error_type": type(cause).__name__},
                    )
                )
            if assembly_data.get("assembly_id") != manifest.get("assembly_id"):
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-ID-MISMATCH",
                        message="Assembly ID differs between manifest and assembly.json.",
                        path=source,
                    )
                )
        if (
            motion_data is None
            or motion_data.get("schema_version") != "kincheck.motion/1.0"
            or not isinstance(motion_data.get("motion_result"), Mapping)
        ):
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-MOTION-INVALID",
                    message="motion.json must contain a supported motion result.",
                    path=source,
                )
            )
        else:
            raw_motion = motion_data["motion_result"]
            raw_status = raw_motion.get("status")
            if raw_status not in {"completed", "completed_with_warnings"}:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-MOTION-INCOMPLETE",
                        message="A package containing a partial or failed MotionResult cannot validate as an acceptance package.",
                        path=source,
                        object_ids=(str(raw_motion.get("scenario_id", "")),),
                        evidence={"status": raw_status, "expected": ("completed", "completed_with_warnings")},
                    )
                )
            if (
                raw_motion.get("assembly_id") != manifest.get("assembly_id")
                or raw_motion.get("scenario_id") != manifest.get("scenario_id")
            ):
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-ID-MISMATCH",
                        message="Motion IDs differ from the manifest.",
                        path=source,
                    )
                )
            try:
                _motion_from_dict(raw_motion)
            except (KeyError, TypeError, ValueError) as cause:
                issues.append(
                    _issue(
                        code="KINCHECK-PACKAGE-MOTION-INVALID",
                        message="motion.json could not be reconstructed.",
                        path=source,
                        evidence={"native_error_type": type(cause).__name__},
                    )
                )

        mesh_values = manifest.get("meshes", ())
        seen_parts: set[str] = set()
        if not isinstance(mesh_values, list):
            issues.append(
                _issue(
                    code="KINCHECK-PACKAGE-MESH-INDEX-INVALID",
                    message="Manifest meshes must be an array.",
                    path=source,
                )
            )
        else:
            valid_part_ids = {
                str(item.get("part_id"))
                for item in assembly_data.get("parts", ())
                if isinstance(item, Mapping)
            } if assembly_data else set()
            for item in mesh_values:
                if not isinstance(item, Mapping):
                    issues.append(
                        _issue(
                            code="KINCHECK-PACKAGE-MESH-INDEX-INVALID",
                            message="Manifest contains an invalid mesh entry.",
                            path=source,
                        )
                    )
                    continue
                part_id = str(item.get("part_id", ""))
                member = str(item.get("path", ""))
                if (
                    not part_id
                    or part_id in seen_parts
                    or part_id not in valid_part_ids
                    or member not in info_by_name
                    or item.get("format") != "stl"
                ):
                    issues.append(
                        _issue(
                            code="KINCHECK-PACKAGE-MESH-INDEX-INVALID",
                            message=f"Invalid mesh mapping for Part {part_id!r}.",
                            path=source,
                            object_ids=(part_id,) if part_id else (),
                        )
                    )
                seen_parts.add(part_id)
        if "physics_path" in manifest:
            try:
                from .physics_package import read_physics_document
                if manifest["physics_path"] != "physics.json" or "physics.json" not in declared:
                    raise ValueError("Physics member must be explicitly hash-indexed at physics.json")
                read_physics_document(assembly_from_dict(data=assembly_data), json.loads(archive.read("physics.json")))
            except Exception as exc:
                issues.append(_issue(code="KINCHECK-PACKAGE-PHYSICS-INVALID", message=str(exc), path=source))
    return ValidationResult(issues=tuple(issues), operation="validate_package")


def _pose_from_dict(value: Mapping[str, Any]) -> Pose:
    return Pose(
        position_m=tuple(float(item) for item in value["position_m"]),
        orientation_xyzw=tuple(float(item) for item in value["orientation_xyzw"]),
    )


def _optional_vector_series(value: Any) -> tuple[tuple[float, float, float], ...] | None:
    if value is None:
        return None
    return tuple(
        tuple(float(axis) for axis in entry)  # type: ignore[misc]
        for entry in value
    )


def _motion_from_dict(value: Mapping[str, Any]) -> MotionResult:
    issues = tuple(
        SimIssue(
            code=str(item["code"]),
            severity=item["severity"],
            stage=str(item["stage"]),
            message=str(item["message"]),
            object_ids=tuple(str(entry) for entry in item.get("object_ids", ())),
            source_paths=tuple(str(entry) for entry in item.get("source_paths", ())),
            evidence=tuple(
                Evidence(
                    key=str(entry["key"]),
                    actual=entry.get("actual"),
                    expected=entry.get("expected"),
                    unit=entry.get("unit"),
                    description=entry.get("description"),
                )
                for entry in item.get("evidence", ())
            ),
            suggested_actions=tuple(
                str(entry) for entry in item.get("suggested_actions", ())
            ),
            failure_time_s=item.get("failure_time_s"),
        )
        for item in value.get("issues", ())
    )
    return MotionResult(
        scenario_id=str(value["scenario_id"]),
        assembly_id=str(value["assembly_id"]),
        status=value["status"],
        start_time_s=float(value["start_time_s"]),
        end_time_s=float(value["end_time_s"]),
        sample_times_s=tuple(float(item) for item in value["sample_times_s"]),
        joint_trajectories=tuple(
            JointTrajectory(
                joint_id=str(item["joint_id"]),
                times_s=tuple(float(entry) for entry in item["times_s"]),
                positions=tuple(float(entry) for entry in item["positions"]),
                velocities=tuple(float(entry) for entry in item["velocities"]),
                accelerations=tuple(float(entry) for entry in item["accelerations"]),
            )
            for item in value.get("joint_trajectories", ())
        ),
        trajectories=tuple(
            Trajectory(
                component_id=str(item["component_id"]),
                connector_id=item.get("connector_id"),
                times_s=tuple(float(entry) for entry in item["times_s"]),
                poses=tuple(_pose_from_dict(entry) for entry in item["poses"]),
                linear_velocities_m_s=_optional_vector_series(
                    item.get("linear_velocities_m_s")
                ),
                angular_velocities_rad_s=_optional_vector_series(
                    item.get("angular_velocities_rad_s")
                ),
                linear_accelerations_m_s2=_optional_vector_series(
                    item.get("linear_accelerations_m_s2")
                ),
                angular_accelerations_rad_s2=_optional_vector_series(
                    item.get("angular_accelerations_rad_s2")
                ),
            )
            for item in value.get("trajectories", ())
        ),
        constraint_residuals=tuple(
            ConstraintResidual(
                constraint_id=str(item["constraint_id"]),
                time_s=float(item["time_s"]),
                position_residual_m=float(item["position_residual_m"]),
                orientation_residual_rad=float(item["orientation_residual_rad"]),
            )
            for item in value.get("constraint_residuals", ())
        ),
        constraint_equation_residuals=tuple(
            ConstraintEquationResidual(
                constraint_id=str(item["constraint_id"]),
                time_s=float(item["time_s"]),
                value=float(item["value"]),
                absolute_value=(
                    None
                    if item.get("absolute_value") is None
                    else float(item["absolute_value"])
                ),
                unit=item["unit"],
                equation_type=item["equation_type"],
            )
            for item in value.get("constraint_equation_residuals", ())
        ),
        closure_residuals=tuple(
            ConstraintResidual(
                constraint_id=str(item["constraint_id"]),
                time_s=float(item["time_s"]),
                position_residual_m=float(item["position_residual_m"]),
                orientation_residual_rad=float(item["orientation_residual_rad"]),
            )
            for item in value.get("closure_residuals", ())
        ),
        closure_statuses={
            str(key): str(status)
            for key, status in value.get("closure_statuses", {}).items()
        },
        limit_events=tuple(
            LimitEvent(
                joint_id=str(item["joint_id"]),
                time_s=float(item["time_s"]),
                side=item["side"],
                event_type=item["event_type"],
                position=float(item["position"]),
                limit_position=float(item["limit_position"]),
            )
            for item in value.get("limit_events", ())
        ),
        issues=issues,
        backend_id=value.get("backend_id"),
        backend_version=value.get("backend_version"),
        metadata=value.get("metadata", {}),
        integration_samples=tuple(
            IntegrationSample(
                time_s=float(item["time_s"]),
                component_poses={
                    str(component_id): _pose_from_dict(pose)
                    for component_id, pose in item.get("component_poses", {}).items()
                },
            )
            for item in value.get("integration_samples", ())
        ),
        driver_trajectories=tuple(
            DriverTrajectory(
                joint_id=str(item["joint_id"]), mode=item["mode"],
                samples=tuple(
                    DriverTarget(
                        joint_id=str(sample["joint_id"]), time_s=float(sample["time_s"]),
                        mode=sample["mode"], target=float(sample["target"]),
                        actual=float(sample["actual"]), error=float(sample["error"]),
                    ) for sample in item.get("samples", ())
                ),
            ) for item in value.get("driver_trajectories", ())
        ),
        traceback=value.get("traceback"),
    )


def read_package(*, path: str | Path) -> MotionPackage:
    """Read and reconstruct a strictly validated ``.kincheck`` package."""

    source = Path(path).expanduser().resolve()
    check = validate_package(path=source)
    if not check.passed:
        raise MotionPackageError(
            code="KINCHECK-PACKAGE-VALIDATION-FAILED",
            message=f"Motion package validation found {len(check.errors)} error(s).",
            report=check,
            source_paths=(str(source),),
            suggested_actions=("Regenerate the .kincheck package and retry.",),
        )
    with zipfile.ZipFile(source, "r") as archive:
        manifest = json.loads(archive.read(MANIFEST_MEMBER))
        assembly_data = json.loads(archive.read(str(manifest["assembly_path"])))
        motion_data = json.loads(archive.read(str(manifest["motion_path"])))
        validation = json.loads(archive.read(str(manifest["validation_path"])))
        dynamics_model, static_results, static_checks = None, (), ()
        if "physics_path" in manifest:
            from .physics_package import read_physics_document
            dynamics_model, static_results, static_checks = read_physics_document(
                assembly_from_dict(data=assembly_data), json.loads(archive.read(manifest["physics_path"])))
    mesh_members = {
        str(item["part_id"]): str(item["path"]) for item in manifest.get("meshes", ())
    }
    return MotionPackage(
        path=source,
        manifest=manifest,
        assembly=assembly_from_dict(data=assembly_data),
        motion_result=_motion_from_dict(motion_data["motion_result"]),
        validation=validation,
        mesh_members=mesh_members,
        dynamics_model=dynamics_model,
        static_results=static_results,
        static_checks=static_checks,
    )


__all__ = [
    "PACKAGE_SCHEMA_VERSION",
    "MotionPackage",
    "MotionPackageArtifact",
    "export_motion_package",
    "motion_package",
    "read_package",
    "validate_package",
]
