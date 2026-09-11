from __future__ import annotations

import json

import pytest

from kincheckapi import visualization
from kincheckapi.assembly import AssemblyModel, Component, Ground, Part, Pose
from kincheckapi.errors import VisualizationExportError
from kincheckapi.result import JointTrajectory, MotionResult, Trajectory


ASCII_STL = """solid part
facet normal 0 0 1
outer loop
vertex 0 0 0
vertex 1 0 0
vertex 0 1 0
endloop
endfacet
endsolid part
"""


def _fixture_data(tmp_path):
    parts_dir = tmp_path / "artifact" / "parts"
    parts_dir.mkdir(parents=True)
    (parts_dir / "part.gear.stl").write_text(ASCII_STL, encoding="ascii")
    assembly = AssemblyModel(
        assembly_id="assembly.viewer",
        parts=(Part(part_id="part.gear", display_name="Gear"),),
        components=(
            Component(
                component_id="component.gear",
                part_id="part.gear",
                display_name="Driven gear",
            ),
        ),
        grounds=(Ground(component_id="component.gear"),),
        metadata={"units": {"length": "mm"}},
    )
    times = (0.0, 0.5, 1.0)
    motion = MotionResult(
        scenario_id="scenario.viewer",
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
            JointTrajectory(
                joint_id="joint.output",
                times_s=times,
                positions=(0.0, 0.25, 0.5),
                velocities=(0.5, 0.5, 0.5),
                accelerations=(0.0, 0.0, 0.0),
            ),
        ),
        trajectories=(
            Trajectory(
                component_id="component.gear",
                times_s=times,
                poses=(
                    Pose(),
                    Pose(orientation_xyzw=(0.0, 0.0, 0.24740396, 0.96891242)),
                    Pose(orientation_xyzw=(0.0, 0.0, 0.47942554, 0.87758256)),
                ),
            ),
        ),
        backend_id="test",
        backend_version="1",
        metadata={
            "workspace": {
                "path_m": [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]],
                "path_closed": False,
            }
        },
    )
    return assembly, motion, tmp_path / "artifact"


def test_export_motion_viewer_writes_replay_and_local_runtime(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    viewer = visualization.export_motion_viewer(
        assembly=assembly,
        motion_result=motion,
        output_dir=tmp_path / "viewer",
        asset_root=asset_root,
        input_joint_id="joint.input",
        output_joint_id="joint.output",
        expected_ratio=4.0,
    )

    manifest = json.loads(viewer.manifest_path.read_text(encoding="utf-8"))
    assert viewer.index_path.is_file()
    assert (viewer.root / "static" / "app.js").is_file()
    assert (viewer.root / "static" / "vendor" / "three.module.min.js").is_file()
    assert (viewer.root / "static" / "vendor" / "three.core.min.js").is_file()
    assert viewer.component_count == 1
    assert viewer.asset_count == 1
    assert viewer.missing_asset_component_ids == ()
    assert manifest["schema_version"] == visualization.VIEWER_SCHEMA_VERSION
    assert manifest["component_result_scope"] == "requested"
    assert manifest["asset_length_scale_m"] == 1e-3
    assert manifest["metrics"]["expected_ratio"] == 4.0
    assert manifest["components"][0]["trajectory"]["positions_m"][1] == [0.0, 0.0, 0.0]
    assert manifest["workspace"]["path_m"][-1] == [0.1, 0.0, 0.0]
    assert (viewer.root / manifest["components"][0]["asset_url"]).is_file()
    assert viewer.to_dict()["asset_count"] == 1


def test_export_reports_missing_mesh_without_dropping_component(tmp_path):
    assembly, motion, _asset_root = _fixture_data(tmp_path)
    viewer = visualization.export_motion_viewer(
        assembly=assembly,
        motion_result=motion,
        output_dir=tmp_path / "viewer",
    )
    manifest = json.loads(viewer.manifest_path.read_text(encoding="utf-8"))
    assert viewer.asset_count == 0
    assert viewer.missing_asset_component_ids == ("component.gear",)
    assert manifest["components"][0]["asset_url"] is None


def test_export_rejects_result_for_another_assembly(tmp_path):
    assembly, motion, asset_root = _fixture_data(tmp_path)
    mismatched = MotionResult(
        scenario_id=motion.scenario_id,
        assembly_id="assembly.other",
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=(0.0, 1.0),
    )
    with pytest.raises(VisualizationExportError) as caught:
        visualization.export_motion_viewer(
            assembly=assembly,
            motion_result=mismatched,
            output_dir=tmp_path / "viewer",
            asset_root=asset_root,
        )
    assert caught.value.code == "KINCHECK-VIEWER-ASSEMBLY-MISMATCH"
