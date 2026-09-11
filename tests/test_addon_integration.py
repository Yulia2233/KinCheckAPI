"""Run in the independent addon environment; the core API needs no SDK extra."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time
import zipfile

import pytest

pytest.importorskip("simplecadapi", reason="Install the addon extra in its own environment for package integration")

from simplecadapi.addon.cli import run as sca_run
from simplecadapi.addon.descriptor import load_descriptor
from simplecadapi.addon.platforms import detect_platform

from kincheckapi.addon import SCA_COMPAT, PackageInputError, _read_package, prepare_package
from kincheckapi.cadir import convert_mjcf
from kincheckapi.cli import main
from kincheckapi.errors import VerificationError
from scripts.package_addon import stage_addon


ROOT = Path(__file__).resolve().parents[1]
CASES = ("compact_two_stage_planetary_reducer",)


@pytest.fixture(params=CASES)
def example(request):
    return ROOT / "examples" / request.param


def test_existing_example_verifier_preserves_baseline_failure(example, tmp_path):
    # Run the original, unmodified example against a copy of its original model.
    # These are baseline failures, not successful mechanism acceptance tests.
    shutil.copytree(example / "model_before", tmp_path / "model_before")
    namespace = runpy.run_path(str(example / "verification/verify_original.py"))
    original_main = namespace["main"]
    original_main.__globals__["CASE_DIR"] = tmp_path
    expected = {
        "compact_two_stage_planetary_reducer": "KINCHECK-CHECK-RATIO-MISMATCH",
    }[example.name]
    with pytest.raises(VerificationError) as error:
        original_main()
    assert error.value.check.passed is False
    assert expected in {issue.code for issue in error.value.check.issues}


def test_historical_example_package_is_rejected_without_modification(example, tmp_path):
    # The stored packages use pre-tick assembly frames. Current SDK validation
    # rejects them; the addon must not rewrite/re-sign them to force acceptance.
    source = example / "model_before" / f"{example.name}.scadpkg"
    before = hashlib.sha256(source.read_bytes()).digest()
    with pytest.raises(PackageInputError) as error:
        prepare_package(package_path=source, work_dir=tmp_path / "work")
    assert error.value.code == "KINCHECK-PACKAGE-INVALID"
    assert "tick form" in error.value.message
    assert hashlib.sha256(source.read_bytes()).digest() == before
    assert not (tmp_path / "work").exists()


def test_source_directory_cannot_be_output_directory(example):
    source = example / "model_before" / f"{example.name}.scadpkg"
    with pytest.raises(PackageInputError) as error:
        prepare_package(package_path=source, work_dir=source.parent)
    assert error.value.code == "KINCHECK-PACKAGE-WORKDIR-INVALID"


@pytest.mark.parametrize("member_type", ["definition", "blob", "occurrence"])
def test_real_package_tampered_members_are_rejected(tmp_path, member_type, example):
    target = tmp_path / "tampered.scadpkg"
    source = example / "model_before" / f"{example.name}.scadpkg"
    with zipfile.ZipFile(source) as original:
        manifest = json.loads(original.read("package.json"))
        member = {
            "definition": manifest["definitions"][0]["path"],
            "blob": next(blob["storage"]["path"] for blob in manifest["blobs"] if blob["storage"]["kind"] == "member"),
            "occurrence": manifest["occurrence_graph"]["path"],
        }[member_type]
        with zipfile.ZipFile(target, "w") as modified:
            for info in original.infolist():
                payload = original.read(info.filename)
                modified.writestr(info.filename, payload + b" " if info.filename == member else payload)
    with pytest.raises(PackageInputError):
        _read_package(target.read_bytes(), target)


def test_package_cli_stops_before_verifier_for_invalid_example(example, tmp_path, capsys):
    script = tmp_path / "verify.py"
    script.write_text("def verify(model_dir):\n    raise AssertionError('invalid package must not reach verifier')\n")
    source = example / "model_before" / f"{example.name}.scadpkg"
    result = main(["verify-package", str(source), "--work-dir", str(tmp_path / "work"), "--script", str(script), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result != 0
    assert payload["code"] == "KINCHECK-PACKAGE-INVALID"


@pytest.mark.parametrize("variant", ["model_before", "model_after"])
def test_four_bar_historical_package_needs_recapture(variant, tmp_path):
    source = ROOT / "examples/four_bar_linkage" / variant / "four_bar_linkage.scadpkg"
    with pytest.raises(PackageInputError) as error:
        prepare_package(package_path=source, work_dir=tmp_path / "work")
    assert error.value.code == "KINCHECK-PACKAGE-INVALID"
    assert "tick form" in error.value.message


def test_recaptured_four_bar_package_runs_original_native_solver(tmp_path):
    source = os.environ.get("KINCHECK_TEST_SCADPKG")
    if not source:
        pytest.skip("Set KINCHECK_TEST_SCADPKG to a four-bar example re-captured by the current SDK")
    before = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    prepared = prepare_package(package_path=source, work_dir=tmp_path / "work")
    converted = convert_mjcf(xml_path=prepared.model_dir / "scene.xml", mapping_path=prepared.model_dir / "scene.mapping.json", asset_root=prepared.model_dir)
    namespace = runpy.run_path(str(ROOT / "examples/four_bar_linkage/verification/simulate_and_record.py"))
    motion = namespace["_native_driven_solve"](converted.assembly)
    assert motion.status == "completed"
    crank = next(item for item in motion.joint_trajectories if item.joint_id == namespace["CRANK_JOINT"])
    assert crank.positions[-1] - crank.positions[0] == pytest.approx(6.283185307179586, abs=1e-4)
    assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == before
    provenance = json.loads((prepared.model_dir / "package-provenance.json").read_text())
    assert provenance["source_sha256"] == before
    assert provenance["content_hash"] == prepared.content_hash


def test_descriptor_compatibility_and_release_versions():
    import tomllib
    from kincheckapi import __version__

    descriptor = load_descriptor(ROOT)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert descriptor.version == project["project"]["version"] == __version__
    assert descriptor.sca_compat == SCA_COMPAT
    assert "simplecadapi" + SCA_COMPAT in project["project"]["optional-dependencies"]["addon"]
    assert descriptor.check_cmd == "kincheck doctor --addon --format json"
    assert descriptor.license == "Apache-2.0"


def test_descriptor_probe_as_fresh_process():
    descriptor = load_descriptor(ROOT)
    env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""))
    start = time.perf_counter()
    completed = subprocess.run(["sh", "-c", descriptor.check_cmd], env=env, capture_output=True, text=True, timeout=3)
    elapsed = time.perf_counter() - start
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["passed"] is True
    assert elapsed < 3, f"Probe exceeded the approximately two-second budget: {elapsed:.3f}s"


@pytest.mark.parametrize("probe_passes", [True, False])
def test_actual_sca_lifecycle_with_distributable_repository(tmp_path, monkeypatch, probe_passes):
    descriptor = load_descriptor(ROOT)
    if detect_platform() not in descriptor.platforms:
        pytest.skip("The addon does not yet declare this platform")
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "user")
    monkeypatch.delenv("SCA_ADDON_HOME", raising=False)
    monkeypatch.delenv("SCA_SKILLS_DIR", raising=False)
    runtime_path = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    if not probe_passes:
        runtime_path = "/usr/bin:/bin"
    monkeypatch.setenv("PATH", runtime_path)
    source = stage_addon(source=ROOT, destination=tmp_path / "release")
    assert not (source / ".venv").exists()
    flags = ["--home", str(tmp_path / "home"), "--skills-dir", str(tmp_path / "skills")]
    assert sca_run(["addon", "init", *flags])[1] == 0
    added, code = sca_run(["addon", "add", str(source), *flags])
    assert code == 0
    assert added["runtime_check"]["passed"] is probe_passes
    skill = tmp_path / "skills/sca-kincheckapi/SKILL.md"
    assert "name: sca-kincheckapi\n" in skill.read_text()
    listed, code = sca_run(["addon", "list", *flags])
    assert code == 0
    assert listed["addons"] and all(not entry["drift"] for entry in listed["addons"])
    updated, code = sca_run(["addon", "update", "kincheckapi", *flags])
    assert code == 0
    assert updated["runtime_check"]["passed"] is probe_passes
    assert sca_run(["addon", "remove", "kincheckapi", *flags])[1] == 0
    assert not skill.exists()
