from pathlib import Path
import json
import runpy
import shutil

import pytest

from kincheckapi.cadir import convert_mjcf
from kincheckapi.errors import MJCFAdapterError


ROOT = Path(__file__).resolve().parents[1]
CASES = (("compact_two_stage_planetary_reducer", 20.0, 12),)


@pytest.mark.parametrize("name,ratio,mesh_count", CASES)
def test_repaired_reducer_verifies_actual_motion_and_every_mesh(name, ratio, mesh_count):
    case = ROOT / "examples" / name
    namespace = runpy.run_path(str(case / "verification/verify.py"))
    assembly, motion, suite, summary = namespace["evaluate"](case / "model_after")
    assert suite.passed, str(suite)
    assert summary["measured_ratio"] == pytest.approx(ratio, rel=1e-3)
    assert summary["output_speed_rad_s"] == pytest.approx(8.0 / ratio, rel=1e-3)
    assert summary["sample_count"] == 51
    assert len(assembly.constraints) == mesh_count
    assert assembly.closures == ()
    assert motion.status == "completed"
    # Independently check the emitted MJCF equations against the actual API
    # trajectories; the expected ratio is never used to construct the model.
    mapping = json.loads((case / "model_after/scene.mapping.json").read_text())
    source_for_xml = {item["joint_name"]: item["joint_id"] for item in mapping["tree_joints"]}
    trajectories = {item.joint_id: item for item in motion.joint_trajectories}
    for equation in mapping["equalities"]:
        for index, time in enumerate(motion.sample_times_s):
            residual = sum(float(value) * trajectories[source_for_xml[name]].positions[index] for name, value in equation["coefficients"].items())
            assert abs(residual) < 1e-5, (equation["equality_id"], time, residual)


@pytest.mark.parametrize("mutation", ["missing_mesh", "coefficient", "endpoint"])
def test_native_mesh_mapping_cannot_silently_drop_or_mismatch_relations(tmp_path, mutation):
    source = ROOT / "examples/compact_two_stage_planetary_reducer/model_after"
    shutil.copy2(source / "scene.xml", tmp_path / "scene.xml")
    shutil.copytree(source / "meshes", tmp_path / "meshes")
    mapping = json.loads((source / "scene.mapping.json").read_text())
    if mutation == "missing_mesh":
        mapping["mesh_constraints"].pop()
    elif mutation == "coefficient":
        record = next(item for item in mapping["equalities"] if item["independent"])
        record["coefficients"][next(iter(record["coefficients"]))] *= 2
    else:
        mapping["mesh_constraints"][0]["connector_a"]["site"] = "absent.site"
    (tmp_path / "scene.mapping.json").write_text(json.dumps(mapping))
    with pytest.raises(MJCFAdapterError):
        convert_mjcf(xml_path=tmp_path / "scene.xml", mapping_path=tmp_path / "scene.mapping.json", asset_root=tmp_path)
