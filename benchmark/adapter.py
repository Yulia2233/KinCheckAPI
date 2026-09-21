"""Prepare one .scadpkg and run a fixed KinCheckAPI verifier.

The adapter is benchmark infrastructure, not part of the Agent prompt. It
never edits the source package; all exported files and temporary collision
meshes live below ``--work-dir``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


_DENSITY_FACTORS_TO_KG_M3 = {
    "kg/m3": 1.0,
    "kg/m^3": 1.0,
    "kg/mm3": 1.0e9,
    "kg/mm^3": 1.0e9,
    "g/cm3": 1.0e3,
    "g/cm^3": 1.0e3,
    "g/mm3": 1.0e9,
    "g/mm^3": 1.0e9,
    "kg/cm3": 1.0e6,
    "kg/cm^3": 1.0e6,
}


def _install_density_normalizer() -> dict[str, Any]:
    """Normalize extra CAD density units inside this adapter process only."""

    import simplecadapi.exporter.mjcf as mjcf

    original = mjcf._density_kg_m3
    statistics: dict[str, Any] = {"units": {}, "total_materials": 0}

    def normalized(material: Any, *, default_density_kg_m3: float | None):
        unit = str(getattr(material, "density_unit", "") or "")
        factor = _DENSITY_FACTORS_TO_KG_M3.get(unit)
        if factor is None or getattr(material, "density", None) is None:
            return original(
                material,
                default_density_kg_m3=default_density_kg_m3,
            )
        if unit not in {"kg/m3", "kg/m^3"}:
            entry = statistics["units"].setdefault(
                unit,
                {"factor_to_kg_m3": factor, "count": 0},
            )
            entry["count"] += 1
            statistics["total_materials"] += 1

        class MaterialView:
            density = float(material.density) * factor
            density_unit = "kg/m3"

            def __getattr__(self, name: str):
                return getattr(material, name)

        return original(MaterialView(), default_density_kg_m3=default_density_kg_m3)

    mjcf._density_kg_m3 = normalized
    return statistics


def _collision_meshes(model_dir: Path) -> list[str]:
    """Convert the same-build exported meshes to verifier leaf STL files."""

    import trimesh

    mapping = json.loads((model_dir / "scene.mapping.json").read_text())
    source_dir = model_dir / "meshes"
    target_dir = model_dir / "collision_meshes"
    target_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for part_id, mesh_name in sorted(mapping.get("meshes", {}).items()):
        candidates = [
            source_dir / f"{mesh_name}.obj",
            source_dir / f"{mesh_name}.stl",
            source_dir / str(mesh_name),
        ]
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise FileNotFoundError(
                f"No exported mesh for {part_id!r} ({mesh_name!r}) in {source_dir}"
            )
        loaded = trimesh.load(source, force="mesh", process=False)
        if not isinstance(loaded, trimesh.Trimesh) or loaded.is_empty:
            raise ValueError(f"Exported mesh is empty or unsupported: {source}")
        target = target_dir / f"{part_id}.stl"
        loaded.export(target)
        created.append(str(target))
    return created


def _refresh_high_resolution_export(package_path: Path, model_dir: Path) -> None:
    """Use the benchmark's fixed CAD tessellation before collision checks."""

    import simplecadapi as scad

    from kincheckapi.cadir import convert_mjcf

    scad.exporter.export_product_package_to_mjcf(
        data=package_path,
        output_path=model_dir / "scene.xml",
        mapping_path=model_dir / "scene.mapping.json",
        mesh_directory=model_dir / "meshes",
        linear_deflection=0.02,
        angular_deflection_degrees=10.0,
    )
    convert_mjcf(
        xml_path=model_dir / "scene.xml",
        mapping_path=model_dir / "scene.mapping.json",
        asset_root=model_dir,
    )


def adapt_and_verify(
    *,
    package_path: Path,
    verify_script: Path,
    work_dir: Path,
    verify_args: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Prepare a package, run the verifier, and return execution evidence."""

    from kincheckapi.addon import prepare_package

    package_path = package_path.expanduser().resolve()
    verify_script = verify_script.expanduser().resolve()
    work_dir = work_dir.expanduser().resolve()
    density_normalization = _install_density_normalizer()
    prepared = prepare_package(package_path=package_path, work_dir=work_dir)
    _refresh_high_resolution_export(package_path, prepared.model_dir)
    collision_meshes = _collision_meshes(prepared.model_dir)
    # Freeze derived inputs after the benchmark tessellation refresh. Generated
    # analysis caches are not input files and are deliberately outside this set.
    provenance = json.loads((prepared.model_dir / "package-provenance.json").read_text())
    files = {}
    for path in sorted(prepared.model_dir.rglob("*")):
        rel = path.relative_to(prepared.model_dir)
        if path.is_file() and (path.name in ("scene.xml", "scene.mapping.json", "package-provenance.json")
                               or rel.parts[0] in ("meshes", "collision_meshes")):
            files[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (prepared.model_dir / "benchmark-input.json").write_text(json.dumps({
        "schema_version": "benchmark.input/1.0", "source_sha256": provenance["source_sha256"],
        "files": files, "density_normalization": density_normalization,
    }, indent=2) + "\n")
    command = [
        sys.executable,
        str(verify_script),
        str(prepared.model_dir),
        *verify_args,
    ]
    completed = subprocess.run(
        command,
        cwd=verify_script.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        verification = json.loads(completed.stdout, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        explicit = isinstance(verification, dict) and type(verification.get("passed")) is bool
        if not explicit:
            raise ValueError("Verifier must emit an object with a boolean passed field")
        strict = verification.get("schema_version") == "benchmark.verification/1.0"
        if strict and (type(verification.get("hard_pass")) is not bool or verification["passed"] != verification["hard_pass"]):
            raise ValueError("Verifier passed/hard_pass disagree")
        passed = completed.returncode == 0 and verification["passed"]
        protocol_error = None if (completed.returncode == 0) == verification["passed"] else "Verifier exit code and JSON verdict disagree"
    except (ValueError, TypeError) as exc:
        verification, passed, protocol_error = None, False, str(exc)
    return {
        "operation": "benchmark_adapter",
        "status": "protocol_violation" if protocol_error else ("passed" if passed else "failed"),
        "passed": passed and protocol_error is None,
        "verification": verification,
        "protocol_error": protocol_error,
        "scadpkg_path": str(package_path),
        "verify_script_path": str(verify_script),
        "prepared_model_dir": str(prepared.model_dir),
        "density_normalization": density_normalization,
        "collision_meshes": collision_meshes,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scadpkg", type=Path, help="Agent-generated .scadpkg")
    parser.add_argument("verify_script", type=Path, help="Fixed verifier script")
    parser.add_argument(
        "--work-dir", type=Path, required=True, help="Adapter-owned temporary output root"
    )
    parser.add_argument(
        "--verify-arg",
        action="append",
        default=[],
        help="Extra argument passed to the verifier; repeat for multiple arguments",
    )
    args = parser.parse_args(argv)
    try:
        result = adapt_and_verify(
            package_path=args.scadpkg,
            verify_script=args.verify_script,
            work_dir=args.work_dir,
            verify_args=tuple(args.verify_arg),
        )
    except Exception as exc:
        result = {
            "operation": "benchmark_adapter",
            "status": "failed",
            "passed": False,
            "scadpkg_path": str(args.scadpkg.expanduser().resolve()),
            "verify_script_path": str(args.verify_script.expanduser().resolve()),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
