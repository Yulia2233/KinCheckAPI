from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from kincheckapi import addon, cli
from kincheckapi.errors import BackendUnavailableError


def _archive(manifest: dict) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("package.json", json.dumps(manifest))
    return stream.getvalue()


@pytest.mark.parametrize("version", [None, "1.0", "2.0", "4.0", 3, "30.0"])
def test_package_schema_gate_precedes_sdk_read(version, monkeypatch):
    import sys

    def unexpected_read(**kwargs):
        pytest.fail("SDK reader must not be reached before the major-version gate")

    monkeypatch.setitem(sys.modules, "simplecadapi", SimpleNamespace(read_product_package=unexpected_read))
    with pytest.raises(addon.PackageInputError) as error:
        addon._read_package(_archive({"schema_version": version}), Path("source.scadpkg"))
    assert error.value.code == "KINCHECK-PACKAGE-SCHEMA-UNSUPPORTED"


def test_schema_three_still_uses_full_sdk_validator(monkeypatch):
    import sys

    def reject(*, data):
        raise ValueError("SHA256 mismatch: member-123")

    monkeypatch.setitem(sys.modules, "simplecadapi", SimpleNamespace(read_product_package=reject))
    with pytest.raises(addon.PackageInputError, match="member-123"):
        addon._read_package(_archive({"schema_version": "3.0"}), Path("source.scadpkg"))


def _fake_package():
    entities = [{"kind": "FACE", "topo_id": "face-a"}, {"kind": "FACE", "topo_id": "face-b"}]
    snapshot = json.dumps({"name_index": {"interface.mount": entities}}).encode()
    digest = hashlib.sha256(snapshot).hexdigest()
    reference = {"path": "this-is-not-a-zip-member.json", "sha256": "sha256:" + digest}
    definition = {"units": "mm", "topology_snapshot_ref": reference}
    record = {"path": "custom/definition", "definition_kind": "single_solid", "definition_id": "part", "revision": "1", "content_hash": "hash"}
    nodes = [{
        "node_id": f"node/root/{name}", "parent_node_id": "node/root",
        "definition_kind": "single_solid", "definition_id": "part",
        "properties": {"revision": "1", "content_hash": "hash"},
        "transform": {"x": x},
    } for name, x in (("first", 0), ("second", 100))]
    package = SimpleNamespace(
        manifest={
            "blobs": [{"sha256": "sha256:" + digest, "storage": {"kind": "member", "path": "unusual/payload"}}],
            "definitions": [record],
            "occurrence_graph": {"path": "custom/occurrences"},
        },
        objects={"unusual/payload": snapshot, "custom/definition": json.dumps(definition).encode(), "custom/occurrences": json.dumps({"nodes": nodes}).encode()},
    )
    return package, reference, entities


def test_resolve_payload_by_manifest_sha_not_logical_filename():
    package, ref, entities = _fake_package()
    assert json.loads(addon._blob_bytes(package, ref))["name_index"]["interface.mount"] == entities
    package.objects["unusual/payload"] += b" "
    with pytest.raises(ValueError, match="SHA256"):
        addon._blob_bytes(package, ref)


def test_interface_index_keeps_multiple_entities_and_separate_occurrences():
    package, _, entities = _fake_package()
    index = addon._interface_index(package)
    assert set(index) == {"node/root/first", "node/root/second"}
    assert index["node/root/first"]["interfaces"]["interface.mount"] == entities
    assert index["node/root/second"]["transform"] == {"x": 100}
    assert index["node/root/first"]["revision"] == "1"
    assert addon._check_interfaces(index, {"node/root/second": ("interface.mount",)}) == {"node/root/second": ["interface.mount"]}
    assert addon._check_interfaces(index, {}) == {}
    assert addon._check_interfaces(index, None) == {}


@pytest.mark.parametrize("occurrence,name,code", [
    ("node/root/first", "interface.absent", "KINCHECK-PACKAGE-INTERFACE-MISSING"),
    ("node/root/absent", "interface.mount", "KINCHECK-PACKAGE-OCCURRENCE-MISSING"),
])
def test_missing_interface_is_named_without_geometric_fallback(occurrence, name, code):
    package, _, _ = _fake_package()
    with pytest.raises(addon.PackageInputError) as error:
        addon._check_interfaces(addon._interface_index(package), {occurrence: (name,)})
    assert error.value.code == code
    assert occurrence in error.value.object_ids
    if code.endswith("INTERFACE-MISSING"):
        assert name in error.value.object_ids


@pytest.mark.parametrize("requirements", [[], {"node/root/first": "interface.mount"}, {"node/root/first": ("private.mount",)}, {"node/root/first": ("interface.",)}])
def test_malformed_interface_requirements_are_rejected(requirements):
    package, _, _ = _fake_package()
    with pytest.raises(ValueError):
        addon._check_interfaces(addon._interface_index(package), requirements)


def test_empty_required_tag_does_not_pass():
    index = {"node/root/first": {"interfaces": {"interface.mount": []}}}
    with pytest.raises(addon.PackageInputError, match="interface.mount"):
        addon._check_interfaces(index, {"node/root/first": ("interface.mount",)})


def test_runtime_failure_stops_before_read_or_workdir_creation(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_doctor", lambda **kwargs: {
        "passed": False, "executable": "/addon/python",
        "checks": {"fcl": {"available": False, "message": "not installed"}},
    })
    with pytest.raises(BackendUnavailableError) as error:
        addon.prepare_package(package_path=tmp_path / "absent.scadpkg", work_dir=tmp_path / "work")
    assert "fcl" in error.value.object_ids
    assert not (tmp_path / "work").exists()


def test_addon_doctor_reports_missing_sdk_without_changing_core_probe(monkeypatch):
    monkeypatch.setattr(cli.importlib, "import_module", lambda name: SimpleNamespace(__version__="1"))
    monkeypatch.setattr(addon, "probe_sdk", lambda: {"available": False, "message": "missing SDK"})
    assert cli._doctor()["passed"] is True
    assert cli._doctor(addon=True)["passed"] is False


@pytest.mark.parametrize("body", ["pass", "return None", "return 1", "return 'ok'", "return []", "return {}"])
def test_cli_never_accepts_missing_or_arbitrary_verifier_result(tmp_path, capsys, body):
    script = tmp_path / "verify.py"
    script.write_text(f"def verify(model_dir):\n    {body}\n")
    code = cli.main(["verify", str(tmp_path), "--script", str(script), "--format", "json"])
    result = json.loads(capsys.readouterr().out)
    assert code == cli.EXIT_INPUT_ERROR
    assert result["passed"] is False


@pytest.mark.parametrize("result,expected", [(True, 0), (False, 2), ({"passed": True}, 0), ({"status": "passed"}, 0), ({"status": "partial", "passed": True}, 2), ({"status": "passed", "passed": False}, 2)])
def test_cli_preserves_explicit_verdicts_and_rejects_partial(result, expected):
    assert cli._exit_code(cli._result_dict(result, operation="verify")) == expected


def test_cli_rejects_non_mapping_to_dict():
    with pytest.raises(ValueError, match="dictionary"):
        cli._result_dict(SimpleNamespace(to_dict=lambda: None), operation="verify")
