from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import math
import xml.etree.ElementTree as ET

import pytest

from kincheckapi._backends.solver_backend import (
    BackendCapabilityFailure,
    _LinearExpression,
    _group_joint_limits,
    compile_assembly,
)
from kincheckapi.assembly import (
    AssemblyModel,
    Component,
    Connector,
    ConnectorRef,
    Ground,
    Joint,
    JointLimit,
    JointType,
    Part,
    assembly_from_dict,
    assembly_to_dict,
)
from kincheckapi.cadir import convert_mjcf


ROOT = Path(__file__).resolve().parents[1]


def _two_body_assembly(
    *, joint_type: JointType, limit: JointLimit, reverse: bool = False
) -> AssemblyModel:
    ground_ref = ConnectorRef("ground", "axis")
    child_ref = ConnectorRef("child", "axis")
    return AssemblyModel(
        assembly_id=f"limit.{joint_type.value}",
        parts=(Part("part", connectors=(Connector("axis"),)),),
        components=(Component("ground", "part"), Component("child", "part")),
        joints=(
            Joint(
                "joint",
                joint_type,
                child_ref if reverse else ground_ref,
                ground_ref if reverse else child_ref,
                limit=limit,
            ),
        ),
        grounds=(Ground("ground"),),
    )


def _compiled_joint(assembly: AssemblyModel):
    compiled = compile_assembly(assembly=assembly)
    child_group = compiled.component_groups["child"]
    root = ET.fromstring(compiled.model_xml)
    element = root.find(f".//joint[@name='{compiled.group_joint_names[child_group]}']")
    assert element is not None
    return root, element


def test_mjcf_lengths_and_angles_are_normalized_to_si(ex3_mjcf_path):
    converted = convert_mjcf(
        xml_path=ex3_mjcf_path / "scene.xml",
        mapping_path=ex3_mjcf_path / "scene.mapping.json",
        asset_root=ex3_mjcf_path,
    )
    assembly = converted.assembly
    assert assembly.metadata["units"] == {
        "length": "m",
        "angle": "rad",
        "mass": "kg",
        "time": "s",
    }
    assert converted.source_map["units"]["mjcf_length"] == "m"
    assert all(math.isfinite(value) for item in assembly.components for value in item.initial_pose.position_m)


def test_joint_limit_serialization_round_trip_preserves_si_values():
    assembly = _two_body_assembly(
        joint_type=JointType.REVOLUTE,
        limit=JointLimit(-math.pi / 4, math.pi / 2),
    )
    restored = assembly_from_dict(data=assembly_to_dict(assembly=assembly))
    assert restored.get_joint(joint_id="joint").limit == assembly.get_joint(joint_id="joint").limit


def test_solver_hinge_uses_radians_and_authored_range():
    root, joint = _compiled_joint(
        _two_body_assembly(
            joint_type=JointType.REVOLUTE,
            limit=JointLimit(-math.pi / 4, math.pi / 2),
        )
    )
    compiler = root.find("compiler")
    assert compiler is not None and compiler.attrib["angle"] == "radian"
    assert joint.attrib["type"] == "hinge"
    assert tuple(float(item) for item in joint.attrib["range"].split()) == pytest.approx(
        (-math.pi / 4, math.pi / 2)
    )


def test_solver_slide_reverses_range_for_negative_public_expression():
    _, joint = _compiled_joint(
        _two_body_assembly(
            joint_type=JointType.PRISMATIC,
            limit=JointLimit(0.01, 0.03),
            reverse=True,
        )
    )
    assert joint.attrib["type"] == "slide"
    assert tuple(float(item) for item in joint.attrib["range"].split()) == pytest.approx(
        (-0.03, -0.01)
    )


def test_limits_sharing_one_coordinate_use_their_intersection():
    assembly = _two_body_assembly(
        joint_type=JointType.REVOLUTE, limit=JointLimit(-2.0, 2.0)
    )
    source = assembly.joints[0]
    assembly = replace(
        assembly,
        joints=(source, replace(source, joint_id="joint.narrow", limit=JointLimit(-1.0, 0.5))),
    )
    limits = _group_joint_limits(
        assembly=assembly,
        joint_expressions={
            item.joint_id: _LinearExpression(MappingProxyType({"coordinate": 1.0}))
            for item in assembly.joints
        },
        movable_group_ids={"coordinate"},
    )
    assert limits["coordinate"] == pytest.approx((-1.0, 0.5))


def test_conflicting_limits_on_one_coordinate_are_rejected():
    assembly = _two_body_assembly(
        joint_type=JointType.REVOLUTE, limit=JointLimit(-2.0, -1.0)
    )
    source = assembly.joints[0]
    assembly = replace(
        assembly,
        joints=(source, replace(source, joint_id="joint.other", limit=JointLimit(1.0, 2.0))),
    )
    with pytest.raises(BackendCapabilityFailure) as error:
        _group_joint_limits(
            assembly=assembly,
            joint_expressions={
                item.joint_id: _LinearExpression(MappingProxyType({"coordinate": 1.0}))
                for item in assembly.joints
            },
            movable_group_ids={"coordinate"},
        )
    assert error.value.object_ids == ("joint", "joint.other")


def test_multi_coordinate_joint_limit_is_rejected_instead_of_ignored():
    part = Part("part", connectors=(Connector("axis"),))
    assembly = AssemblyModel(
        assembly_id="limit.multi",
        parts=(part,),
        components=(Component("ground", "part"), Component("middle", "part"), Component("end", "part")),
        joints=(
            Joint("a", JointType.REVOLUTE, ConnectorRef("ground", "axis"), ConnectorRef("middle", "axis")),
            Joint("b", JointType.REVOLUTE, ConnectorRef("middle", "axis"), ConnectorRef("end", "axis")),
            Joint(
                "closure.limit", JointType.REVOLUTE,
                ConnectorRef("ground", "axis"), ConnectorRef("end", "axis"),
                limit=JointLimit(-1.0, 1.0), metadata={"topology_role": "closure_edge"},
            ),
        ),
        grounds=(Ground("ground"),),
    )
    with pytest.raises(BackendCapabilityFailure) as error:
        _group_joint_limits(
            assembly=assembly,
            joint_expressions={"closure.limit": _LinearExpression(MappingProxyType({"middle": 1.0, "end": 1.0}))},
            movable_group_ids={"middle", "end"},
        )
    assert error.value.object_ids == ("closure.limit",)
