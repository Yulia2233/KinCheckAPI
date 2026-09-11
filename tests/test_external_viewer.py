from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

VIEWER_PATH = Path(__file__).resolve().parents[1] / "viewer" / "kincheck_viewer.py"
VIEWER_SPEC = importlib.util.spec_from_file_location("external_kincheck_viewer", VIEWER_PATH)
assert VIEWER_SPEC is not None and VIEWER_SPEC.loader is not None
kincheck_viewer = importlib.util.module_from_spec(VIEWER_SPEC)
VIEWER_SPEC.loader.exec_module(kincheck_viewer)


ASCII_STL = b"""solid part
facet normal 0 0 1
outer loop
vertex 0 0 0
vertex 1 0 0
vertex 0 1 0
endloop
endfacet
endsolid part
"""


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")


def _make_package(
    path: Path,
    *,
    include_mesh: bool = True,
    bad_hash: bool = False,
    assembly_id: str = "assembly.viewer",
    unsafe_member: bool = False,
    joint_types: tuple[str, str] | None = None,
) -> Path:
    assembly = {
        "schema_version": "kincheck.assembly/1.0",
        "assembly_id": assembly_id,
        "display_name": "Viewer fixture",
        "parts": [
            {
                "part_id": "part.gear",
                "display_name": "Gear",
                "metadata": {"material": {"color": [0.1, 0.5, 0.8]}},
            }
        ],
        "components": [
            {
                "component_id": "component.gear",
                "part_id": "part.gear",
                "display_name": "Driven gear",
                "initial_pose": {
                    "position_m": [0.0, 0.0, 0.0],
                    "orientation_xyzw": [0.0, 0.0, 0.0, 1.0],
                },
            }
        ],
        "grounds": [{"component_id": "component.gear"}],
    }
    if joint_types is not None:
        assembly["joints"] = [
            {"joint_id": "joint.input", "joint_type": joint_types[0]},
            {"joint_id": "joint.output", "joint_type": joint_types[1]},
        ]
    times = [0.0, 1.0]
    joint = {
        "joint_id": "joint.input",
        "times_s": times,
        "positions": [0.0, 2.0],
        "velocities": [2.0, 2.0],
        "accelerations": [0.0, 0.0],
    }
    motion = {
        "schema_version": "kincheck.motion/1.0",
        "motion_result": {
            "assembly_id": "assembly.viewer",
            "scenario_id": "scenario.viewer",
            "status": "completed",
            "start_time_s": 0.0,
            "end_time_s": 1.0,
            "sample_times_s": times,
            "backend_id": "fixture",
            "backend_version": "1",
            "joint_trajectories": [joint],
            "trajectories": [
                {
                    "component_id": "component.gear",
                    "connector_id": None,
                    "times_s": times,
                    "poses": [
                        {
                            "position_m": [0.0, 0.0, 0.0],
                            "orientation_xyzw": [0.0, 0.0, 0.0, 1.0],
                        },
                        {
                            "position_m": [0.1, 0.0, 0.0],
                            "orientation_xyzw": [0.0, 0.0, 0.5, 0.8660254],
                        },
                    ],
                }
            ],
            "constraint_residuals": [],
            "issues": [],
            "metadata": {
                "workspace": {
                    "path_m": [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]],
                    "path_closed": False,
                }
            },
        },
    }
    validation = {"schema_version": "kincheck.validation/1.0", "status": "completed"}
    payloads = {
        "assembly.json": _json_bytes(assembly),
        "motion.json": _json_bytes(motion),
        "validation.json": _json_bytes(validation),
    }
    meshes = []
    if include_mesh:
        payloads["meshes/gear.stl"] = ASCII_STL
        meshes.append(
            {
                "part_id": "part.gear",
                "path": "meshes/gear.stl",
                "format": "stl",
                "scale_to_m": 0.001,
            }
        )
    files = []
    for name, content in sorted(payloads.items()):
        digest = hashlib.sha256(content).hexdigest()
        if bad_hash and name == "motion.json":
            digest = "0" * 64
        files.append({"path": name, "bytes": len(content), "sha256": digest})
    manifest = {
        "schema_version": kincheck_viewer.PACKAGE_SCHEMA_VERSION,
        "title": "Fixture package",
        "assembly_id": "assembly.viewer",
        "scenario_id": "scenario.viewer",
        "motion_status": "completed",
        "meshes": meshes,
        "files": files,
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", _json_bytes(manifest))
        for name, content in payloads.items():
            archive.writestr(name, content)
        if unsafe_member:
            archive.writestr("../escape.txt", b"unsafe")
    return path


def _open_viewer(path: Path):
    return json.loads((path / "viewer.json").read_text(encoding="utf-8"))


def test_unpack_creates_standalone_web_application(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck")
    index = kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
    assert index.is_file()
    assert (index.parent / "viewer.json").is_file()
    assert (index.parent / "static" / "app.js").is_file()
    assert (index.parent / "static" / "vendor" / "three.module.min.js").is_file()


def test_unpack_converts_package_poses_to_viewer_trajectory(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck")
    kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
    trajectory = _open_viewer(tmp_path / "viewer")["components"][0]["trajectory"]
    assert trajectory["positions_m"] == [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]]
    assert trajectory["orientations_xyzw"][1] == [0.0, 0.0, 0.5, 0.8660254]


def test_unpack_forwards_workspace_path_to_viewer(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck")
    kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
    workspace = _open_viewer(tmp_path / "viewer")["workspace"]
    assert workspace["path_m"][-1] == [0.1, 0.0, 0.0]
    assert workspace["path_closed"] is False


def test_unpack_extracts_mesh_and_preserves_scale(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck")
    kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
    manifest = _open_viewer(tmp_path / "viewer")
    asset = tmp_path / "viewer" / manifest["components"][0]["asset_url"]
    assert asset.read_bytes() == ASCII_STL
    assert manifest["asset_length_scale_m"] == 0.001


def test_unpack_selects_joint_metrics_without_solving_again(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck")
    kincheck_viewer.unpack_package(
        package_path=package,
        output_dir=tmp_path / "viewer",
        input_joint_id="joint.input",
        expected_ratio=4.0,
    )
    metrics = _open_viewer(tmp_path / "viewer")["metrics"]
    assert metrics["input"]["velocities"] == [2.0, 2.0]
    assert metrics["expected_ratio"] == 4.0
    assert metrics["input_unit"] == "rad/s"
    assert metrics["output_unit"] == "rad/s"
    assert metrics["ratio_mode"] == "input_over_output"


def test_unpack_marks_prismatic_output_as_linear_transmission(tmp_path):
    package = _make_package(
        tmp_path / "fixture.kincheck",
        joint_types=("revolute", "prismatic"),
    )
    kincheck_viewer.unpack_package(
        package_path=package,
        output_dir=tmp_path / "viewer",
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=0.02,
    )
    metrics = _open_viewer(tmp_path / "viewer")["metrics"]
    assert metrics["input_unit"] == "rad/s"
    assert metrics["output_unit"] == "m/s"
    assert metrics["ratio_mode"] == "output_over_input"
    assert metrics["ratio_unit"] == "m/rad"


def test_unpack_keeps_component_when_mesh_is_missing(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck", include_mesh=False)
    kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
    manifest = _open_viewer(tmp_path / "viewer")
    assert manifest["components"][0]["asset_url"] is None
    assert manifest["missing_asset_component_ids"] == ["component.gear"]


def test_unpack_rejects_tampered_indexed_content(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck", bad_hash=True)
    with pytest.raises(kincheck_viewer.ViewerPackageError, match="hash check failed"):
        kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")


def test_unpack_rejects_unsafe_member_path(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck", unsafe_member=True)
    with pytest.raises(kincheck_viewer.ViewerPackageError, match="unsafe package member"):
        kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")


def test_unpack_rejects_cross_document_assembly_id_mismatch(tmp_path):
    package = _make_package(tmp_path / "fixture.kincheck", assembly_id="assembly.other")
    with pytest.raises(kincheck_viewer.ViewerPackageError, match="assembly ID differs"):
        kincheck_viewer.unpack_package(package_path=package, output_dir=tmp_path / "viewer")
