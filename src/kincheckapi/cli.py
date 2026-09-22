"""Command line interface for KinCheckAPI verification workflows."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from .cadir import convert_mjcf
from .errors import KinCheckError


EXIT_OK = 0
EXIT_VERIFICATION_FAILED = 2
EXIT_CAPABILITY_FAILED = 3
EXIT_INPUT_ERROR = 4
EXIT_EXECUTION_ERROR = 5


def _version() -> str:
    try:
        return importlib.metadata.version("kincheckapi")
    except importlib.metadata.PackageNotFoundError:
        from . import __version__

        return __version__


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _result_dict(result: Any, *, operation: str) -> dict[str, Any]:
    if isinstance(result, dict):
        payload = dict(result)
    elif hasattr(result, "to_dict"):
        payload = result.to_dict()
        if isinstance(payload, dict):
            payload = dict(payload)
        else:
            raise ValueError("Verifier to_dict() must return a dictionary with an explicit verdict")
    elif isinstance(result, bool):
        payload = {"passed": result, "status": "passed" if result else "failed"}
    else:
        raise ValueError("Verifier must return a structured verdict or bool, not None or an arbitrary value")
    if type(payload.get("passed")) is not bool and payload.get("status") not in {
        "passed", "failed", "partial", "indeterminate", "capability_failed", "validation_failed"
    }:
        raise ValueError("Verifier result needs an explicit passed boolean or recognized verdict status")
    payload.setdefault("operation", operation)
    payload.setdefault("kincheckapi_version", _version())
    return payload


def _status(payload: dict[str, Any]) -> str:
    status = payload.get("status")
    if status == "passed" and payload.get("passed") is False:
        return "failed"
    if status in {"passed", "failed", "partial", "indeterminate", "capability_failed", "validation_failed"}:
        return str(status)
    return "passed" if payload.get("passed") is True else "failed"


def _exit_code(payload: dict[str, Any]) -> int:
    status = _status(payload)
    if status == "passed":
        return EXIT_OK
    if status == "capability_failed":
        return EXIT_CAPABILITY_FAILED
    return EXIT_VERIFICATION_FAILED


def _emit(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=True, indent=2, default=_json_default, sort_keys=True))
        return
    status = _status(payload)
    print(f"KinCheckAPI: {status}")
    print(f"Operation: {payload.get('operation', 'api')}")
    issues = payload.get("issues", ())
    if issues:
        for issue in issues:
            if isinstance(issue, dict):
                print(f"- {issue.get('code', 'KINCHECK-UNKNOWN')}: {issue.get('message', '')}")
            else:
                print(f"- {issue}")
    elif status == "passed":
        print("No issues.")


def _load_script(path: Path) -> ModuleType:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Verifier script does not exist: {path}")
    module_name = f"kincheck_verifier_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load verifier script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_verifier(script: Path, model_dir: Path) -> dict[str, Any]:
    module = _load_script(script)
    verify = getattr(module, "verify", None)
    if verify is None:
        raise AttributeError(f"Verifier must expose verify(model_dir): {script}")
    result = verify(model_dir)
    return _result_dict(result, operation="verify")


def _validate_model(model_dir: Path) -> dict[str, Any]:
    model_dir = model_dir.expanduser().resolve()
    if not model_dir.is_dir():
        raise FileNotFoundError(f"Model directory does not exist: {model_dir}")
    xml_path = model_dir / "scene.xml"
    mapping_path = model_dir / "scene.mapping.json"
    if not xml_path.is_file() or not mapping_path.is_file():
        missing = [str(path) for path in (xml_path, mapping_path) if not path.is_file()]
        raise FileNotFoundError("Model input contract is missing: " + ", ".join(missing))
    adapter = convert_mjcf(xml_path=xml_path, mapping_path=mapping_path, asset_root=model_dir)
    return {
        "operation": "validate_model",
        "status": "passed",
        "passed": True,
        "assembly_id": adapter.assembly.assembly_id,
        "source_map_entries": len(adapter.source_map),
        "model_dir": str(model_dir),
        "kincheckapi_version": _version(),
    }


def _doctor(*, addon: bool = False) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    modules = {"mujoco": "mujoco", "trimesh": "trimesh", "rtree": "rtree", "fcl": "fcl"}
    for label, module_name in modules.items():
        try:
            module = importlib.import_module(module_name)
            checks[label] = {"available": True, "version": getattr(module, "__version__", None)}
        except Exception as exc:  # pragma: no cover - platform-specific native imports
            checks[label] = {"available": False, "error_type": type(exc).__name__, "message": str(exc)}
    if addon:
        from .addon import probe_sdk

        checks["simplecadapi"] = probe_sdk()
    passed = all(item["available"] for item in checks.values())
    return {
        "operation": "doctor",
        "status": "passed" if passed else "capability_failed",
        "passed": passed,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "checks": checks,
        "kincheckapi_version": _version(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kincheck", description="KinCheckAPI verification and Skill tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check Python and native backend availability")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    doctor.add_argument("--addon", action="store_true", help="Also check the optional SimpleCADAPI addon runtime")

    for command in ("prepare-package", "verify-package"):
        package = subparsers.add_parser(command, help="Consume a validated .scadpkg in addon-owned storage")
        package.add_argument("package_path", type=Path)
        package.add_argument("--work-dir", type=Path, required=True)
        package.add_argument("--require-interface", action="append", default=[], metavar="OCCURRENCE=TAG")
        package.add_argument("--format", choices=("text", "json"), default="text")
        if command == "verify-package":
            package.add_argument("--script", type=Path, default=Path("verification/verify.py"))

    validate = subparsers.add_parser("validate-model", help="Validate a CADIR model directory")
    validate.add_argument("model_dir", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")

    verify = subparsers.add_parser("verify", help="Run an independent verifier against one model directory")
    verify.add_argument("model_dir", type=Path)
    verify.add_argument("--script", type=Path, default=Path("verification/verify.py"))
    verify.add_argument("--format", choices=("text", "json"), default="text")

    pack = subparsers.add_parser("skill-pack", help="Build the portable Agent Skill bundle")
    pack.add_argument("--language", choices=("en", "zh", "both"), default="en")
    pack.add_argument("--output-root", type=Path, default=Path("dist"))
    pack.add_argument("--archive", action="store_true")
    pack.add_argument("--adapters", action="store_true")
    pack.add_argument("--source-root", type=Path, default=None)

    gui = subparsers.add_parser("gui", help="Open the native KinCheck scenario workbench")
    gui.add_argument("--scenario", type=Path, default=None, help="Open a saved kincheck.gui-scenario JSON document")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "skill-pack":
        from .auto_tools.skill_pack import build

        build(
            language=args.language,
            output_root=args.output_root,
            archive=args.archive,
            adapters=args.adapters,
            source_root=args.source_root,
        )
        return EXIT_OK

    if args.command == "gui":
        try:
            from .gui.app import launch
            launch(scenario_path=args.scenario)
            return EXIT_OK
        except Exception as exc:
            _emit({"operation": "gui", "status": "capability_failed", "passed": False, "code": "KINCHECK-GUI-LAUNCH-FAILED", "message": str(exc), "error_type": type(exc).__name__}, "json")
            return EXIT_CAPABILITY_FAILED

    try:
        if args.command == "doctor":
            payload = _doctor(addon=args.addon)
        elif args.command in {"prepare-package", "verify-package"}:
            from .addon import prepare_package

            requirements: dict[str, list[str]] = {}
            for value in args.require_interface:
                occurrence, separator, name = value.partition("=")
                if not separator or not occurrence or not name:
                    raise ValueError("--require-interface must be OCCURRENCE=interface.name")
                requirements.setdefault(occurrence, []).append(name)
            prepared = prepare_package(
                package_path=args.package_path,
                work_dir=args.work_dir,
                required_interfaces=requirements,
            )
            if args.command == "verify-package":
                payload = _run_verifier(args.script, prepared.model_dir)
                payload["package_input"] = {
                    "path": str(prepared.package_path),
                    "content_hash": prepared.content_hash,
                    "model_dir": str(prepared.model_dir),
                }
            else:
                payload = prepared.to_dict()
        elif args.command == "validate-model":
            payload = _validate_model(args.model_dir)
        else:
            payload = _run_verifier(args.script, args.model_dir)
    except KinCheckError as exc:
        payload = exc.to_dict()
        payload.setdefault("operation", getattr(exc, "operation", "api"))
        payload.setdefault("kincheckapi_version", _version())
    except (AttributeError, FileNotFoundError, ImportError, OSError, ValueError) as exc:
        payload = {
            "operation": args.command,
            "status": "validation_failed",
            "passed": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "kincheckapi_version": _version(),
        }
        _emit(payload, args.format)
        return EXIT_INPUT_ERROR
    except Exception as exc:  # pragma: no cover - defensive boundary for agent tooling
        payload = {
            "operation": args.command,
            "status": "failed",
            "passed": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "kincheckapi_version": _version(),
        }
        _emit(payload, args.format)
        return EXIT_EXECUTION_ERROR

    _emit(payload, args.format)
    return _exit_code(payload)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
