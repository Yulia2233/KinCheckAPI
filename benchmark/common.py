"""Shared private evaluation protocol. Only stdlib and public KinCheckAPI APIs."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import time

from kincheckapi.diagnostics import Evidence, SimIssue
from kincheckapi.errors import KinCheckError
from kincheckapi.physics_types import PhysicsReport


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_safe(value):
    if hasattr(value, "to_dict"):
        return json_safe(value.to_dict())
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def report(operation, *, passed, actual=None, expected=None, unit=None,
           objects=(), status=None, code="CLAIM-FAILED", message="Claim differs from its requirement.",
           fix="Correct the owning CAD source and recapture; keep the verifier fixed."):
    return PhysicsReport(
        operation=operation, status=status or ("passed" if passed else "failed"),
        evidence={"actual": actual, "expected": expected, "unit": unit},
        issues=() if passed else (SimIssue(
            code="BENCHMARK-" + code, severity="error", stage=operation,
            message=message, object_ids=tuple(objects),
            evidence=(Evidence(key=operation, actual=actual, expected=expected, unit=unit),),
            suggested_actions=(fix,),
        ),),
    )


class Evaluation:
    def __init__(self, case_dir, required):
        self.case_dir = Path(case_dir)
        self.required = tuple(required)
        self.checks = []
        self.started = time.monotonic()
        self.artifacts = {}

    def run(self, check_id, function, **kwargs):
        start = time.monotonic()
        try:
            with redirect_stdout(sys.stderr):
                value = function(**kwargs)
            raw = value.to_dict() if hasattr(value, "to_dict") else value
            if not isinstance(raw, dict) or type(raw.get("passed")) is not bool:
                raise ValueError("Verifier operation did not return an explicit boolean verdict")
            raw = dict(raw)
            raw.setdefault("status", "passed" if raw["passed"] else "failed")
            raw.setdefault("operation", check_id)
            raw.setdefault("issues", [])
            raw.setdefault("evidence", {})
        except Exception as exc:
            value = None
            raw = report(
                check_id, passed=False, status=getattr(exc, "status", "validation_failed"),
                code="INPUT-OR-OPERATION-FAILED", message=str(exc),
                actual=exc.to_dict() if isinstance(exc, KinCheckError) else {"type": type(exc).__name__, "message": str(exc)},
            ).to_dict()
        raw.update(check_id=check_id, elapsed_s=time.monotonic()-start)
        self.checks.append(json_safe(raw))
        return value

    def unresolved(self, check_id, message, *, status="capability_failed", objects=()):
        self.run(check_id, report, operation=check_id, passed=False, status=status,
                 code="EVIDENCE-UNAVAILABLE", message=message, objects=objects,
                 fix="Complete the evaluator capability or resolve the benchmark contract; do not weaken the model requirement.")

    def finish(self, *, ready):
        seen = {c["check_id"] for c in self.checks}
        for name in self.required:
            if name not in seen:
                self.unresolved(name, "Prerequisite failed; this required claim was not executed.", status="indeterminate")
        coverage = {key: next(c["status"] for c in self.checks if c["check_id"] == key) for key in self.required}
        passed = ready and bool(self.required) and all(c["passed"] and c["status"] in ("passed", "completed", "completed_with_warnings") for c in self.checks)
        bad = [c for c in self.checks if not c["passed"]]
        status = "passed" if passed else next((s for s in ("validation_failed", "failed", "capability_failed", "indeterminate", "partial") if any(c["status"] == s for c in bad)), "indeterminate")
        versions = {}
        for package in ("kincheckapi", "simplecadapi", "mujoco", "python-fcl"):
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = None
        files = sorted((self.case_dir / "verification").glob("*.py"))
        files += [Path(__file__), Path(__file__).with_name("adapter.py")]
        return json_safe({
            "operation": "benchmark_verify", "case_id": self.case_dir.name,
            "schema_version": "benchmark.verification/1.0", "benchmark_ready": ready,
            "passed": passed, "hard_pass": passed, "status": status,
            "what_happened": "All required claims passed." if passed else "Required claims failed or remain unproved.",
            "cause": [c["check_id"] for c in bad],
            "how_to_fix": list(dict.fromkeys(a for c in bad for i in c["issues"] for a in i.get("suggested_actions", []))),
            "issues": [i for c in bad for i in c["issues"]], "checks": self.checks,
            "coverage": coverage, "artifacts": self.artifacts,
            "prompt_sha256": sha256(self.case_dir / "prompt.md"),
            "verifier_files": {str(p.relative_to(self.case_dir.parent)): sha256(p) for p in files},
            "versions": versions, "python": sys.version, "elapsed_s": time.monotonic()-self.started,
        })


def prepared_input(model_dir):
    """Validate the adapter-owned link from source bytes to derived files."""
    root = Path(model_dir).expanduser().resolve()
    seal = json.loads((root / "benchmark-input.json").read_text())
    provenance = json.loads((root / "package-provenance.json").read_text())
    source = Path(provenance["source_package"])
    if not source.is_absolute() or sha256(source) != provenance["source_sha256"] or sha256(source) != seal["source_sha256"]:
        raise ValueError("Source package does not match the prepared-input fingerprint")
    declared = seal["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and (
        p.name in ("scene.xml", "scene.mapping.json", "package-provenance.json") or
        p.relative_to(root).parts[0] in ("meshes", "collision_meshes"))}
    if actual != set(declared):
        raise ValueError("Prepared assets were added or removed")
    for rel, expected in declared.items():
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or sha256(path) != expected:
            raise ValueError(f"Derived file fingerprint mismatch: {rel}")
    return source, seal


def input_report(model_dir):
    source, seal = prepared_input(model_dir)
    return report("prepared_input", passed=True, actual={"source": str(source), **seal})


def cli(verify):
    parser = argparse.ArgumentParser(description=verify.__doc__)
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        with redirect_stdout(sys.stderr):
            result = verify(args.model_dir)
        body = json.dumps(json_safe(result), ensure_ascii=False, indent=2, allow_nan=False)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(body + "\n")
    except Exception as exc:
        result = {"operation": "benchmark_verify", "passed": False, "hard_pass": False,
                  "benchmark_ready": False, "status": "validation_failed", "what_happened": str(exc),
                  "cause": type(exc).__name__, "how_to_fix": ["Repair the input or evaluation environment and rerun."],
                  "issues": [], "checks": [], "coverage": {}}
        body = json.dumps(result, ensure_ascii=False, allow_nan=False)
    print(body)
    return 0 if result.get("hard_pass") is True else 1
