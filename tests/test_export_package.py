from __future__ import annotations

from dataclasses import replace
import json
from importlib.metadata import PackageNotFoundError
from pathlib import Path
import zipfile

import pytest

from kincheckapi import export
from kincheckapi.assembly import AssemblyModel, Component, Part, Pose
from kincheckapi.errors import MotionPackageError
from kincheckapi.result import JointTrajectory, MotionResult, Trajectory


ASCII_STL = b"""solid gear
facet normal 0 0 1
outer loop
vertex 0 0 0
vertex 1 0 0
vertex 0 1 0
endloop
endfacet
endsolid gear
"""


def test_source_checkout_package_version_fallback(monkeypatch):
    def missing_distribution(_name):
        raise PackageNotFoundError

    monkeypatch.setattr(export, "version", missing_distribution)
    assert export._package_version() == "0.5.0"


def _fixture_data(tmp_path: Path, *, second_part: bool = False, with_mesh: bool = True):
    artifact = tmp_path / "artifact"
    parts_dir = artifact / "parts"
    parts_dir.mkdir(parents=True)
    if with_mesh:
        (parts_dir / "gear.stl").write_bytes(ASCII_STL)
    asset_paths = {"stl": "parts/gear.stl"} if with_mesh else {}
    parts = [Part("part.gear", asset_paths=asset_paths)]
    components = [Component("component.gear", "part.gear")]
    if second_part:
        parts.append(Part("part.gear.copy", asset_paths=asset_paths))
        components.append(Component("component.gear.copy", "part.gear.copy"))
    assembly = AssemblyModel(
        assembly_id="assembly.package",
        parts=tuple(parts),
        components=tuple(components),
        metadata={"units": {"length": "mm"}},
    )
    times = (0.0, 0.5, 1.0)
    trajectories = tuple(
        Trajectory(
            component_id=component.component_id,
            times_s=times,
            poses=(
                Pose(),
                Pose(position_m=(0.001, 0.0, 0.0)),
                Pose(position_m=(0.002, 0.0, 0.0)),
            ),
        )
        for component in components
    )
    motion = MotionResult(
        scenario_id="scenario.package",
        assembly_id=assembly.assembly_id,
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=times,
        joint_trajectories=(
            JointTrajectory(
                joint_id="joint.input",
                times_s=times,
                positions=(0.0, 1.0, 2.0),
                velocities=(2.0, 2.0, 2.0),
                accelerations=(0.0, 0.0, 0.0),
            ),
        ),
        trajectories=trajectories,
        backend_id="test",
        backend_version="1",
    )
    return assembly, motion, artifact


def _make_package(tmp_path: Path, **fixture_options):
    assembly, motion, artifact = _fixture_data(tmp_path, **fixture_options)
    result = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=tmp_path / "result.kincheck",
        asset_root=artifact,
    )
    return result, assembly, motion


def _entries(path: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(path, "r") as archive:
        return [(item.filename, archive.read(item)) for item in archive.infolist()]


def _write_entries(path: Path, entries: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in entries:
            archive.writestr(name, value)


def _replace_manifest(path: Path, mutate) -> None:
    entries = _entries(path)
    rewritten = []
    for name, content in entries:
        if name == export.MANIFEST_MEMBER:
            manifest = json.loads(content)
            mutate(manifest)
            content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        rewritten.append((name, content))
    _write_entries(path, rewritten)


# motion_package(): eight export cases.
def test_motion_package_writes_required_data_members(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    with zipfile.ZipFile(artifact.path) as archive:
        assert set((export.MANIFEST_MEMBER, export.ASSEMBLY_MEMBER, export.MOTION_MEMBER, export.VALIDATION_MEMBER)) <= set(archive.namelist())
        manifest = json.loads(archive.read(export.MANIFEST_MEMBER))
    assert manifest["schema_version"] == export.PACKAGE_SCHEMA_VERSION
    assert artifact.mesh_count == 1


def test_motion_package_is_byte_deterministic(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    first = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=tmp_path / "first.kincheck",
        asset_root=asset_root,
    )
    second = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=tmp_path / "second.kincheck",
        asset_root=asset_root,
    )
    assert first.sha256 == second.sha256
    assert first.path.read_bytes() == second.path.read_bytes()


def test_motion_package_deduplicates_identical_part_meshes(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path, second_part=True)
    loaded = export.read_package(path=artifact.path)
    assert artifact.mesh_count == 1
    assert len(loaded.mesh_members) == 2
    assert len(set(loaded.mesh_members.values())) == 1


def test_motion_package_records_optional_missing_meshes(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path, with_mesh=False)
    assert artifact.mesh_count == 0
    assert artifact.missing_mesh_part_ids == ("part.gear",)


def test_motion_package_can_require_complete_meshes(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path, with_mesh=False)
    with pytest.raises(MotionPackageError) as caught:
        export.motion_package(
            assembly=assembly,
            motion_result=motion,
            output_path=tmp_path / "strict.kincheck",
            asset_root=asset_root,
            require_meshes=True,
        )
    assert caught.value.code == "KINCHECK-PACKAGE-MESH-MISSING"


def test_motion_package_rejects_mismatched_assembly_id(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    with pytest.raises(MotionPackageError) as caught:
        export.motion_package(
            assembly=assembly,
            motion_result=replace(motion, assembly_id="assembly.other"),
            output_path=tmp_path / "bad.kincheck",
            asset_root=asset_root,
        )
    assert caught.value.code == "KINCHECK-PACKAGE-ASSEMBLY-MISMATCH"


def test_motion_package_requires_kincheck_extension(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    with pytest.raises(MotionPackageError) as caught:
        export.motion_package(
            assembly=assembly,
            motion_result=motion,
            output_path=tmp_path / "result.zip",
            asset_root=asset_root,
        )
    assert caught.value.code == "KINCHECK-PACKAGE-EXTENSION-INVALID"


def test_motion_package_preserves_title_metadata_and_counts(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    artifact = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=tmp_path / "metadata.kincheck",
        asset_root=asset_root,
        title="Package title",
        metadata={"purpose": "test"},
    )
    loaded = export.read_package(path=artifact.path)
    assert loaded.manifest["title"] == "Package title"
    assert loaded.manifest["metadata"] == {"purpose": "test"}
    assert artifact.component_count == 1
    assert artifact.trajectory_count == 1


# read_package(): six typed read cases.
def test_read_package_reconstructs_public_types(tmp_path):
    artifact, assembly, motion = _make_package(tmp_path)
    loaded = export.read_package(path=artifact.path)
    assert isinstance(loaded.assembly, AssemblyModel)
    assert isinstance(loaded.motion_result, MotionResult)
    assert loaded.assembly.assembly_id == assembly.assembly_id
    assert loaded.motion_result.scenario_id == motion.scenario_id


def test_read_package_returns_original_mesh_bytes(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    loaded = export.read_package(path=artifact.path)
    assert loaded.read_mesh(part_id="part.gear") == ASCII_STL


def test_read_package_reports_absent_part_mesh(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path, with_mesh=False)
    loaded = export.read_package(path=artifact.path)
    with pytest.raises(KeyError):
        loaded.read_mesh(part_id="part.gear")


def test_read_package_preserves_joint_and_pose_samples(tmp_path):
    artifact, _assembly, motion = _make_package(tmp_path)
    loaded = export.read_package(path=artifact.path)
    assert loaded.motion_result.joint_trajectories[0].positions == (0.0, 1.0, 2.0)
    assert loaded.motion_result.trajectories[0].poses[2].position_m == (0.002, 0.0, 0.0)
    assert loaded.motion_result.to_dict() == motion.to_dict()


def test_read_package_exposes_read_only_top_level_mappings(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    loaded = export.read_package(path=artifact.path)
    with pytest.raises(TypeError):
        loaded.manifest["title"] = "changed"
    with pytest.raises(TypeError):
        loaded.mesh_members["new"] = "meshes/new.stl"


def test_read_package_wraps_validation_failure(tmp_path):
    path = tmp_path / "broken.kincheck"
    path.write_bytes(b"not a zip")
    with pytest.raises(MotionPackageError) as caught:
        export.read_package(path=path)
    assert caught.value.code == "KINCHECK-PACKAGE-VALIDATION-FAILED"
    assert caught.value.report.issues[0].code == "KINCHECK-PACKAGE-ZIP-INVALID"


# validate_package(): eight integrity and safety cases.
def test_validate_package_accepts_valid_package(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    assert export.validate_package(path=artifact.path).passed


def test_validate_package_detects_tampered_payload(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    entries = [
        (name, content + b" ") if name == export.MOTION_MEMBER else (name, content)
        for name, content in _entries(artifact.path)
    ]
    _write_entries(artifact.path, entries)
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-HASH-MISMATCH" in codes


def test_validate_package_rejects_future_schema(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    _replace_manifest(artifact.path, lambda value: value.update(schema_version="future/9"))
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-SCHEMA-UNSUPPORTED" in codes


def test_validate_package_requires_manifest(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    _write_entries(
        artifact.path,
        [(name, content) for name, content in _entries(artifact.path) if name != export.MANIFEST_MEMBER],
    )
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-MANIFEST-MISSING" in codes


def test_validate_package_rejects_unsafe_member_path(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    _write_entries(artifact.path, [*_entries(artifact.path), ("../escape.txt", b"unsafe")])
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-PATH-UNSAFE" in codes


def test_validate_package_rejects_duplicate_members(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    entries = _entries(artifact.path)
    assembly_content = next(content for name, content in entries if name == export.ASSEMBLY_MEMBER)
    with pytest.warns(UserWarning, match="Duplicate name"):
        _write_entries(artifact.path, [*entries, (export.ASSEMBLY_MEMBER, assembly_content)])
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-DUPLICATE-MEMBER" in codes


def test_validate_package_rejects_unindexed_member(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    _write_entries(artifact.path, [*_entries(artifact.path), ("extra.json", b"{}")])
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-FILE-UNINDEXED" in codes


def test_validate_package_detects_cross_document_id_mismatch(tmp_path):
    artifact, _assembly, _motion = _make_package(tmp_path)
    _replace_manifest(artifact.path, lambda value: value.update(assembly_id="other"))
    codes = {item.code for item in export.validate_package(path=artifact.path).issues}
    assert "KINCHECK-PACKAGE-ID-MISMATCH" in codes
