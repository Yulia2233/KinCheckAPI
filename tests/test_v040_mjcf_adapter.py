from __future__ import annotations

import json
from pathlib import Path

import pytest

from kincheckapi.cadir import convert_mjcf
from kincheckapi.errors import MJCFAdapterError
from kincheckapi._clearance_fcl import load_mesh
from kincheckapi.kinematics import solve_motion
from kincheckapi.pose import rotate_vector
from kincheckapi.scenario import (
    create_scenario,
    set_run_duration,
    set_sample_period,
)


def _write_fixture(root: Path) -> tuple[Path, Path]:
    (root / "mesh.obj").write_text(
        "\n".join(
            (
                "v 0 0 0",
                "v 0.01 0 0",
                "v 0 0.01 0",
                "v 0 0 0.01",
                "f 1 3 2",
                "f 1 2 4",
                "f 1 4 3",
                "f 2 3 4",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    xml_path = root / "model.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<mujoco model="mjcf_fixture">
  <compiler angle="radian" coordinate="local"/>
  <asset><mesh name="mesh_child" file="mesh.obj"/></asset>
  <worldbody>
    <geom name="ground" type="mesh" mesh="mesh_child" density="1000"/>
    <body name="body_child" pos="0 0 0">
      <joint name="joint_child" type="hinge" pos="0 0 0" axis="0 0 1"/>
      <geom name="child" type="mesh" mesh="mesh_child" density="1000"/>
      <site name="public_site" pos="0 0 0"/>
    </body>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )
    mapping_path = root / "model.mapping.json"
    mapping_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "root_definition_id": "mjcf_fixture",
                "units": {
                    "source": "mm",
                    "mjcf_length": "m",
                    "mjcf_angle": "radian",
                },
                "grounded_group_id": "group_ground",
                "groups": [
                    {
                        "group_id": "group_ground",
                        "members": ["ground"],
                        "grounded": True,
                        "body_name": None,
                        "parent_group": None,
                        "tree_joint": None,
                    },
                    {
                        "group_id": "group_child",
                        "members": ["child"],
                        "grounded": False,
                        "body_name": "body_child",
                        "parent_group": "group_ground",
                        "tree_joint": "joint_child",
                    },
                ],
                "tree_joints": [
                    {
                        "joint_id": "joint/child",
                        "group": "group_child",
                        "parent_group": "group_ground",
                        "joint_name": "joint_child",
                    }
                ],
                "closures": [],
                "equalities": [],
                "sites": [
                    {
                        "name": "public_site",
                        "connector_id": "child_axis",
                        "attached_group": "group_child",
                        "connector_snapshot_id": "connector/child_axis",
                    }
                ],
                "meshes": {"child": "mesh_child"},
                "rigid_edges": [],
                "redundant_movable_joints": [],
                "pruned_structure_nodes": [],
                "default_density_count": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return xml_path, mapping_path


def test_convert_mjcf_builds_existing_assembly_contract(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    converted = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    )
    assembly = converted.assembly
    assert assembly.assembly_id == "mjcf_fixture"
    assert len(assembly.components) == 2
    assert len(assembly.joints) == 1
    assert assembly.get_joint(joint_id="joint/child") is not None
    assert assembly.get_connector(
        component_id="group_child", connector_id="child_axis"
    ) is not None
    assert converted.source_map["provenance_status"] == "structural_only"
    assert converted.source_map["source_joint_id_to_xml_name"] == {
        "joint/child": "joint_child"
    }
    assert all(part.asset_paths["stl"] for part in assembly.parts)
    assert all(Path(part.asset_paths["stl"]).is_file() for part in assembly.parts)
    assert converted.source_map["group_id_to_clearance_stl"]
    for part in assembly.parts:
        mesh = load_mesh(assembly=assembly, part=part, asset_root=tmp_path)
        assert mesh.triangle_count > 0
        assert mesh.scale_to_m == pytest.approx(1.0)


def test_convert_mjcf_preserves_existing_solve_path(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    assembly = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    ).assembly
    scenario = create_scenario(scenario_id="mjcf_fixture_motion", assembly=assembly)
    scenario = set_run_duration(scenario=scenario, duration_s=0.02)
    scenario = set_sample_period(scenario=scenario, period_s=0.01)
    result = solve_motion(scenario=scenario)
    assert result.status == "completed"
    assert result.sample_times_s
    assert result.get_joint_trajectory(joint_id="joint/child") is not None


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.update(schema_version="future/9"), "KINCHECK-MJCF-MAPPING-INVALID"),
        (lambda value: value["tree_joints"][0].update(joint_name="missing"), "KINCHECK-MJCF-NAME-UNRESOLVED"),
        (lambda value: value.update(grounded_group_id="missing"), "KINCHECK-MJCF-MAPPING-INVALID"),
    ],
)
def test_convert_mjcf_rejects_structural_mapping_errors(tmp_path, mutation, code):
    xml_path, mapping_path = _write_fixture(tmp_path)
    value = json.loads(mapping_path.read_text(encoding="utf-8"))
    mutation(value)
    mapping_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == code


def test_convert_mjcf_rejects_missing_model_attribute(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml_path.write_text(
        xml_path.read_text(encoding="utf-8").replace(' model="mjcf_fixture"', ""),
        encoding="utf-8",
    )
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-MODEL-MISSING"


def test_convert_mjcf_rejects_missing_assets(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    (tmp_path / "mesh.obj").unlink()
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-XML-INVALID"


def test_convert_mjcf_normalizes_collision_exclusions(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    value = json.loads(mapping_path.read_text(encoding="utf-8"))
    value["collision_exclusions"] = [
        ["group_child", "group_ground"],
        ["group_ground", "group_child"],
    ]
    mapping_path.write_text(json.dumps(value), encoding="utf-8")
    assembly = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    ).assembly
    assert assembly.collision_exclusions == (("group_child", "group_ground"),)


def test_convert_mjcf_rejects_malformed_collision_exclusion(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    value = json.loads(mapping_path.read_text(encoding="utf-8"))
    value["collision_exclusions"] = [["group_child"]]
    mapping_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-MAPPING-INVALID"


def test_convert_mjcf_preserves_non_z_joint_axis(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml = xml_path.read_text(encoding="utf-8").replace(
        'axis="0 0 1"', 'axis="1 0 0"'
    )
    xml_path.write_text(xml, encoding="utf-8")
    assembly = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    ).assembly
    connector = assembly.get_connector(
        component_id="group_child", connector_id="__mjcf_joint__joint/child__child"
    )
    assert connector is not None
    assert rotate_vector(pose=connector.pose, vector=(0.0, 0.0, 1.0)) == pytest.approx(
        (1.0, 0.0, 0.0)
    )


def test_convert_mjcf_uses_default_joint_axis(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml_path.write_text(
        xml_path.read_text(encoding="utf-8").replace(' axis="0 0 1"', ""),
        encoding="utf-8",
    )
    assembly = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    ).assembly
    connector = assembly.get_connector(
        component_id="group_child", connector_id="__mjcf_joint__joint/child__child"
    )
    assert connector is not None
    assert rotate_vector(pose=connector.pose, vector=(0.0, 0.0, 1.0)) == pytest.approx(
        (0.0, 0.0, 1.0)
    )


def test_convert_mjcf_rejects_invalid_joint_axis(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml_path.write_text(
        xml_path.read_text(encoding="utf-8").replace(
            'axis="0 0 1"', 'axis="0 0 0"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-JOINT-AXIS-INVALID"


def test_convert_mjcf_normalizes_nonzero_coupling_phase(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml = xml_path.read_text(encoding="utf-8").replace(
        "</worldbody>",
        """    <body name="body_second" pos="0.03 0 0" quat="0.9305076219 0 0 0.3662725291">
      <joint name="joint_second" type="hinge" pos="0 0 0" axis="0 0 1"/>
      <geom name="second" type="mesh" mesh="mesh_child" density="1000"/>
    </body>
  </worldbody>
  <tendon><fixed name="coupled"><joint joint="joint_child" coef="1"/><joint joint="joint_second" coef="1"/></fixed></tendon>
  <equality><tendon name="phase_equality" tendon1="coupled" polycoef="0 0 0 0 0"/></equality>""",
    )
    xml_path.write_text(xml, encoding="utf-8")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping["groups"].append(
        {
            "group_id": "group_second",
            "members": ["second"],
            "grounded": False,
            "body_name": "body_second",
            "parent_group": "group_ground",
            "tree_joint": "joint_second",
        }
    )
    mapping["tree_joints"].append(
        {
            "joint_id": "joint/second",
            "group": "group_second",
            "parent_group": "group_ground",
            "joint_name": "joint_second",
        }
    )
    mapping["equalities"] = [
        {
            "equality_id": "coupling/phase",
            "name": "phase_equality",
            "joint_type": "gear",
            "coefficients": {"joint_child": 1.0, "joint_second": 1.0},
            "reference_phase_source_units": 0.75,
            "independent": True,
        }
    ]
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")

    assembly = convert_mjcf(
        xml_path=xml_path,
        mapping_path=mapping_path,
        asset_root=tmp_path,
    ).assembly
    coupling = assembly.couplings[0]
    assert coupling.phase_offset == 0.0
    assert coupling.metadata["source_phase_offset"] == pytest.approx(0.75)
    scenario = create_scenario(scenario_id="coupling_phase", assembly=assembly)
    scenario = set_run_duration(scenario=scenario, duration_s=0.02)
    scenario = set_sample_period(scenario=scenario, period_s=0.01)
    assert solve_motion(scenario=scenario).status == "completed"


def test_convert_mjcf_rejects_unmapped_xml_equality(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml = xml_path.read_text(encoding="utf-8").replace(
        '<site name="public_site" pos="0 0 0"/>',
        '<site name="public_site" pos="0 0 0"/><site name="unmapped_site" pos="0.001 0 0"/>',
    ).replace(
        "</worldbody>",
        "</worldbody>\n  <equality><connect name=\"unmapped\" site1=\"public_site\" site2=\"unmapped_site\"/></equality>",
    )
    xml_path.write_text(xml, encoding="utf-8")
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-MAPPING-INVALID"


def test_convert_mjcf_rejects_empty_movable_mesh_group(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    xml = xml_path.read_text(encoding="utf-8").replace(
        '<geom name="child" type="mesh" mesh="mesh_child" density="1000"/>',
        '<geom name="child" type="box" size="0.01 0.01 0.01" density="1000"/>',
    )
    xml_path.write_text(xml, encoding="utf-8")
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-ASSET-MISSING"


def test_convert_mjcf_rejects_public_site_without_connector_id(tmp_path):
    xml_path, mapping_path = _write_fixture(tmp_path)
    value = json.loads(mapping_path.read_text(encoding="utf-8"))
    value["sites"][0]["connector_id"] = ""
    mapping_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(MJCFAdapterError) as error:
        convert_mjcf(
            xml_path=xml_path,
            mapping_path=mapping_path,
            asset_root=tmp_path,
        )
    assert error.value.code == "KINCHECK-MJCF-INCOMPLETE"
