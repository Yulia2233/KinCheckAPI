"""Optional, read-only SimpleCADAPI product-package input boundary.

The existing MJCF, assembly, scenario, solver and check APIs are unchanged.
Install ``kincheckapi[addon]`` in an environment owned by this addon.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import importlib.metadata
import io
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping, Sequence
import zipfile

from .errors import BackendUnavailableError, KinCheckError


SCA_COMPAT = ">=2.1.3b3,<2.1.4"
_MAX_MANIFEST_BYTES = 8 * 1024 * 1024


class PackageInputError(KinCheckError):
    """A product package or its declared interface cannot be consumed."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("operation", "prepare_package")
        kwargs.setdefault("status", "validation_failed")
        super().__init__(**kwargs)


def probe_sdk() -> dict[str, Any]:
    """Check the optional SDK locally, without a model, GUI or network call."""
    try:
        from packaging.specifiers import SpecifierSet

        version = importlib.metadata.version("simplecadapi")
        if not SpecifierSet(SCA_COMPAT).contains(version, prereleases=True):
            raise RuntimeError(f"simplecadapi {version} is outside {SCA_COMPAT}")
        sdk = importlib.import_module("simplecadapi")
        exporter = importlib.import_module("simplecadapi.exporter.mjcf")
        if not callable(getattr(sdk, "read_product_package", None)):
            raise RuntimeError("simplecadapi.read_product_package is unavailable")
        if not callable(getattr(exporter, "export_product_package_to_mjcf", None)):
            raise RuntimeError("SimpleCADAPI's product-package MJCF exporter is unavailable")
        return {"available": True, "version": version, "compat": SCA_COMPAT}
    except Exception as exc:
        return {
            "available": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "compat": SCA_COMPAT,
        }


def require_runtime() -> None:
    """Enforce the descriptor's probe before any addon package operation."""
    from .cli import _doctor

    report = _doctor(addon=True)
    if not report["passed"]:
        missing = tuple(name for name, item in report["checks"].items() if not item["available"])
        raise BackendUnavailableError(
            code="KINCHECK-ADDON-RUNTIME-UNAVAILABLE",
            message="Addon runtime unavailable: " + ", ".join(missing),
            operation="prepare_package",
            object_ids=missing,
            details={"checks": report["checks"], "executable": report["executable"]},
            suggested_actions=(
                "Install kincheckapi[addon] in its own environment, separate from modeling.",
                "Run kincheck doctor --addon --format json with that environment on PATH.",
            ),
        )


def _read_package(raw: bytes, source: Path) -> Any:
    # Read only package.json until the major-version gate has passed. The SDK
    # then validates all member digests, schemas, manifest hash and graph closure.
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if archive.namelist().count("package.json") != 1:
                raise ValueError("the archive must contain exactly one package.json")
            info = archive.getinfo("package.json")
            if info.file_size > _MAX_MANIFEST_BYTES:
                raise ValueError("package.json exceeds the manifest size limit")
            manifest = json.loads(archive.read(info))
        if not isinstance(manifest, dict):
            raise ValueError("package.json must contain an object")
        version = manifest.get("schema_version")
        if not isinstance(version, str) or version.split(".", 1)[0] != "3":
            raise PackageInputError(
                code="KINCHECK-PACKAGE-SCHEMA-UNSUPPORTED",
                message=f"Unsupported package schema_version {version!r}; supported major is 3.",
                source_paths=(str(source),),
            )
        from simplecadapi import read_product_package

        return read_product_package(data=raw)
    except PackageInputError:
        raise
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        raise PackageInputError(
            code="KINCHECK-PACKAGE-INVALID",
            message=f"Invalid product package {source}: {exc}",
            source_paths=(str(source),),
            suggested_actions=("Re-capture the model with SimpleCADAPI; do not edit archive members.",),
        ) from exc


def _blob_bytes(package: Any, reference: Mapping[str, Any]) -> bytes:
    digest = str(reference["sha256"]).removeprefix("sha256:")
    for blob in package.manifest["blobs"]:
        if str(blob["sha256"]).removeprefix("sha256:") != digest:
            continue
        storage = blob["storage"]
        if storage["kind"] == "member":
            payload = package.objects[str(storage["path"])]
            if hashlib.sha256(payload).hexdigest() != digest:
                raise ValueError(f"SHA256 mismatch for {storage['path']}")
            return payload
    raise ValueError(f"No member blob in manifest for sha256:{digest}")


def _interface_index(package: Any) -> dict[str, dict[str, Any]]:
    definitions: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in package.manifest["definitions"]:
        identity = (record["definition_id"], record["revision"], record["content_hash"])
        definition = json.loads(package.objects[str(record["path"])])
        if record["definition_kind"] == "single_solid":
            if definition.get("units") != "mm":
                raise ValueError(f"Definition {identity[0]!r} must use millimeters")
            ref = definition.get("topology_snapshot_ref")
            snapshot = json.loads(_blob_bytes(package, ref)) if ref is not None else {}
            names = snapshot.get("name_index", {})
            definitions[identity] = {
                name: entries for name, entries in names.items() if name.startswith("interface.")
            }
    graph_ref = package.manifest["occurrence_graph"]
    graph = json.loads(package.objects[str(graph_ref["path"])])
    index: dict[str, dict[str, Any]] = {}
    for node in graph["nodes"]:
        if node["definition_kind"] != "single_solid":
            continue
        properties = node["properties"]
        identity = (node["definition_id"], properties["revision"], properties["content_hash"])
        index[node["node_id"]] = {
            "definition_id": identity[0],
            "revision": identity[1],
            "content_hash": identity[2],
            "parent_node_id": node["parent_node_id"],
            "transform": node["transform"],
            "transform_encoding": "simplecadapi-canonical-ticks",
            "interfaces": definitions[identity],
        }
    return index


def _check_interfaces(
    index: Mapping[str, Any], requirements: Mapping[str, Sequence[str]] | None
) -> dict[str, list[str]]:
    if requirements is None:
        return {}
    if not isinstance(requirements, Mapping):
        raise ValueError("required_interfaces must map occurrence IDs to sequences of interface.* names")
    normalized: dict[str, list[str]] = {}
    for occurrence, names in requirements.items():
        if not isinstance(occurrence, str) or not occurrence:
            raise ValueError("Interface requirements need non-empty occurrence IDs")
        if isinstance(names, (str, bytes)) or not isinstance(names, (list, tuple)):
            raise ValueError(f"Interface names for {occurrence!r} must be a list or tuple")
        if any(not isinstance(name, str) or not name.startswith("interface.") or len(name) == 10 for name in names):
            raise ValueError("Required interface names must be non-empty interface.* tags")
        if occurrence not in index:
            raise PackageInputError(
                code="KINCHECK-PACKAGE-OCCURRENCE-MISSING",
                message=f"Required part occurrence {occurrence!r} is missing.",
                object_ids=(occurrence,),
            )
        available = index[occurrence]["interfaces"]
        for name in names:
            if not available.get(name):
                raise PackageInputError(
                    code="KINCHECK-PACKAGE-INTERFACE-MISSING",
                    message=f"Required tag {name!r} is missing on occurrence {occurrence!r}.",
                    object_ids=(occurrence, name),
                    suggested_actions=(
                        "Return to the SimpleCADAPI skill, declare this interface and capture again.",
                        "Do not approximate a missing interface from geometry or display names.",
                    ),
                )
        normalized[occurrence] = list(names)
    return normalized


@dataclass(frozen=True)
class PreparedPackage:
    """A durable addon-owned MJCF directory and its product-package provenance."""

    model_dir: Path
    package_path: Path
    content_hash: str
    interfaces: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": "prepare_package",
            "status": "passed",
            "passed": True,
            "model_dir": str(self.model_dir),
            "package_path": str(self.package_path),
            "content_hash": self.content_hash,
            "interfaces": dict(self.interfaces),
        }


def prepare_package(
    *,
    package_path: str | Path,
    work_dir: str | Path,
    required_interfaces: Mapping[str, Sequence[str]] | None = None,
) -> PreparedPackage:
    """Prepare a validated .scadpkg for existing ``verify(model_dir)`` scripts.

    Required tag names are scoped by exact part occurrence node IDs. Empty
    requirements mean this claim does not require geometry interface tags.
    The source is read once, never extracted or modified. Each successful call
    owns a new subdirectory of work_dir; keep it while consuming its assets.
    """
    require_runtime()
    source = Path(package_path).expanduser().resolve()
    root = Path(work_dir).expanduser().resolve()
    if source.parent == root or source.is_relative_to(root):
        raise PackageInputError(
            code="KINCHECK-PACKAGE-WORKDIR-INVALID",
            message="work_dir must be separate from the source package directory and must not contain the source.",
            source_paths=(str(source), str(root)),
        )
    try:
        raw = source.read_bytes()
        package = _read_package(raw, source)
        if package.manifest["root"]["definition_kind"] != "assembly":
            raise PackageInputError(
                code="KINCHECK-PACKAGE-ROOT-UNSUPPORTED",
                message="Mechanism verification requires an assembly-rooted .scadpkg.",
                source_paths=(str(source),),
            )
        index = _interface_index(package)
        requirements = _check_interfaces(index, required_interfaces)
    except KinCheckError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageInputError(
            code="KINCHECK-PACKAGE-INPUT-INVALID",
            message=str(exc),
            source_paths=(str(source),),
        ) from exc

    from simplecadapi.exporter.mjcf import export_product_package_to_mjcf

    root.mkdir(parents=True, exist_ok=True)
    model_dir = Path(tempfile.mkdtemp(prefix="kincheck-", dir=root))
    try:
        report = export_product_package_to_mjcf(
            data=package,
            output_path=model_dir / "scene.xml",
            mapping_path=model_dir / "scene.mapping.json",
            mesh_directory=model_dir / "meshes",
        )
        # Export success alone does not establish a usable model directory.
        # Reuse the original compiler/topology gate before reporting readiness.
        from .cadir import convert_mjcf

        convert_mjcf(
            xml_path=model_dir / "scene.xml",
            mapping_path=model_dir / "scene.mapping.json",
            asset_root=model_dir,
        )
        provenance = {
            "schema_version": "1.0",
            "source_package": str(source),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "content_hash": package.manifest["content_hash"],
            "simplecadapi_version": importlib.metadata.version("simplecadapi"),
            "source_units": "mm",
            "mjcf_units": {"length": "m", "angle": "rad"},
            "required_interfaces": requirements,
            "occurrences": index,
            "export_limitations": list(report.limitations),
        }
        (model_dir / "package-provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
        )
    except Exception as exc:
        # This fresh directory contains only outputs created by this invocation.
        shutil.rmtree(model_dir)
        raise PackageInputError(
            code="KINCHECK-PACKAGE-EXPORT-FAILED",
            message=f"The validated package cannot be exported to supported MJCF: {exc}",
            source_paths=(str(source),),
            suggested_actions=("Return to the SimpleCADAPI workflow and re-capture a supported assembly.",),
        ) from exc
    return PreparedPackage(
        model_dir=model_dir,
        package_path=source,
        content_hash=str(package.manifest["content_hash"]),
        interfaces=index,
    )


__all__ = ["PackageInputError", "PreparedPackage", "prepare_package"]
