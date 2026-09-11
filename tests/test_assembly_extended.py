from __future__ import annotations

from dataclasses import replace
import math

import pytest

from kincheckapi.assembly import (
    AssemblyModel,
    Closure,
    Component,
    Connector,
    ConnectorRef,
    Constraint,
    Coupling,
    Ground,
    Joint,
    JointLimit,
    Part,
    Pose,
    add_closure_constraint,
    add_constraint,
    assembly_from_dict,
    assembly_to_dict,
    create_assembly,
    exclude_collision_pair,
    ground_component,
    read_assembly,
    set_joint_limits,
    validate_assembly,
)
from kincheckapi.errors import AssemblyValidationError


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"position_m": (0.0, 0.0)}, "3-vector"),
        ({"orientation_xyzw": (0.0, 0.0, 1.0)}, "quaternion"),
        ({"position_m": (0.0, math.inf, 0.0)}, "finite"),
        ({"orientation_xyzw": (0.0, 0.0, 0.0, 0.0)}, "non-zero"),
    ],
)
def test_pose_rejects_invalid_rigid_transforms(kwargs, message):
    with pytest.raises(ValueError, match=message):
        Pose(**kwargs)


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        ((0.0, 0.0, 3.0, 4.0), (0.0, 0.0, 0.6, 0.8)),
        ((1e308, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
    ],
)
def test_pose_normalizes_quaternion_on_construction(orientation, expected):
    pose = Pose(orientation_xyzw=orientation)

    assert pose.orientation_xyzw == pytest.approx(expected)
    assert math.hypot(*pose.orientation_xyzw) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Connector(connector_id=" "),
        lambda: Part(part_id=""),
        lambda: Component(component_id="cmp", part_id=""),
        lambda: ConnectorRef(component_id="", connector_id="axis"),
        lambda: Ground(component_id=""),
        lambda: AssemblyModel(assembly_id=""),
    ],
)
def test_public_model_ids_must_be_explicit(factory):
    with pytest.raises(ValueError, match="non-empty"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: JointLimit(lower=2.0, upper=1.0),
        lambda: JointLimit(lower=-math.inf, upper=1.0),
        lambda: Coupling(
            coupling_id="c", coupling_type="gear", joint_a_id="a", joint_b_id="b", ratio=0
        ),
        lambda: Closure(
            closure_id="c",
            constraint=Constraint(
                constraint_id="x",
                connector_a=ConnectorRef(component_id="a", connector_id="x"),
                connector_b=ConnectorRef(component_id="b", connector_id="x"),
            ),
            position_tolerance_m=0,
        ),
    ],
)
def test_relationship_numeric_invariants(factory):
    with pytest.raises(ValueError):
        factory()


def test_get_connector_prefers_instance_then_falls_back_to_part():
    part = Part(
        part_id="part",
        connectors=(Connector(connector_id="shared", display_name="part"),),
    )
    component = Component(
        component_id="cmp",
        part_id="part",
        connectors=(Connector(connector_id="local", display_name="instance"),),
    )
    assembly = AssemblyModel(assembly_id="asm", parts=(part,), components=(component,))

    assert assembly.get_connector(component_id="cmp", connector_id="local").display_name == "instance"
    assert assembly.get_connector(component_id="cmp", connector_id="shared").display_name == "part"
    assert assembly.get_connector(component_id="missing", connector_id="shared") is None


def test_full_public_assembly_dictionary_round_trip():
    ref_a = ConnectorRef(component_id="a", connector_id="axis")
    ref_b = ConnectorRef(component_id="b", connector_id="axis")
    constraint = Constraint(constraint_id="mate", connector_a=ref_a, connector_b=ref_b)
    assembly = AssemblyModel(
        assembly_id="asm",
        parts=(Part(part_id="part", connectors=(Connector(connector_id="axis"),)),),
        components=(Component(component_id="a", part_id="part"), Component(component_id="b", part_id="part")),
        joints=(Joint(joint_id="j1", joint_type="revolute", connector_a=ref_a, connector_b=ref_b),
                Joint(joint_id="j2", joint_type="prismatic", connector_a=ref_a, connector_b=ref_b)),
        constraints=(constraint,),
        couplings=(Coupling(coupling_id="gear", coupling_type="gear", joint_a_id="j1", joint_b_id="j2", ratio=-2.0),),
        closures=(Closure(closure_id="closure", constraint=replace(constraint, constraint_id="loop")),),
        grounds=(Ground(component_id="a"),),
        collision_exclusions=(("b", "a"),),
        metadata={"nested": {"values": [1, 2]}},
    )

    restored = assembly_from_dict(data=assembly_to_dict(assembly=assembly))
    assert assembly_to_dict(assembly=restored) == assembly_to_dict(assembly=assembly)
    assert validate_assembly(assembly=restored).passed


def test_imperative_commands_are_idempotent_and_report_missing_targets():
    part = Part(part_id="part", connectors=(Connector(connector_id="axis"),))
    components = (Component(component_id="a", part_id="part"), Component(component_id="b", part_id="part"))
    joint = Joint(
        joint_id="joint",
        joint_type="revolute",
        connector_a=ConnectorRef(component_id="a", connector_id="axis"),
        connector_b=ConnectorRef(component_id="b", connector_id="axis"),
    )
    assembly = AssemblyModel(assembly_id="asm", parts=(part,), components=components, joints=(joint,))
    grounded = ground_component(assembly=assembly, component_id="a")
    excluded = exclude_collision_pair(assembly=grounded, component_a_id="b", component_b_id="a")
    assert ground_component(assembly=grounded, component_id="a") is grounded
    assert exclude_collision_pair(assembly=excluded, component_a_id="a", component_b_id="b") is excluded

    with pytest.raises(AssemblyValidationError) as ground_error:
        ground_component(assembly=assembly, component_id="missing")
    with pytest.raises(AssemblyValidationError) as joint_error:
        set_joint_limits(assembly=assembly, joint_id="missing", lower=0, upper=1)
    with pytest.raises(AssemblyValidationError) as pair_error:
        exclude_collision_pair(assembly=assembly, component_a_id="a", component_b_id="a")
    assert ground_error.value.code == "assembly.missing_component"
    assert joint_error.value.code == "assembly.missing_joint"
    assert pair_error.value.code == "assembly.invalid_collision_pair"


def test_add_constraint_and_explicit_closure_have_separate_collections():
    ref = ConnectorRef(component_id="a", connector_id="axis")
    constraint = Constraint(constraint_id="mate", connector_a=ref, connector_b=ref)
    assembly = add_constraint(assembly=create_assembly(assembly_id="asm"), constraint=constraint)
    assembly = add_closure_constraint(
        assembly=assembly,
        constraint=Closure(closure_id="loop", constraint=replace(constraint, constraint_id="loop-mate")),
    )
    assert assembly.constraints == (constraint,)
    assert assembly.closures[0].closure_id == "loop"


def test_validation_aggregates_all_reference_and_topology_failures():
    connector = Connector(connector_id="axis")
    part = Part(part_id="part", connectors=(connector, connector), asset_paths={"step": ""})
    ref = ConnectorRef(component_id="missing", connector_id="none")
    self_ref = ConnectorRef(component_id="a", connector_id="none")
    invalid = AssemblyModel(
        assembly_id="asm",
        parts=(part,),
        components=(Component(component_id="a", part_id="part"),),
        joints=(Joint(joint_id="self", joint_type="fixed", connector_a=self_ref, connector_b=self_ref),),
        constraints=(Constraint(constraint_id="dangling", connector_a=ref, connector_b=self_ref),),
        couplings=(Coupling(coupling_id="gear", coupling_type="gear", joint_a_id="self", joint_b_id="none", ratio=1),),
        grounds=(Ground(component_id="missing"),),
        collision_exclusions=(("a", "missing"),),
    )
    codes = {issue.code for issue in validate_assembly(assembly=invalid).issues}
    assert {
        "assembly.duplicate_id",
        "assembly.invalid_asset",
        "assembly.missing_component",
        "assembly.missing_connector",
        "assembly.self_joint",
        "assembly.missing_joint",
    } <= codes


def test_read_assembly_wraps_invalid_json_and_schema(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(AssemblyValidationError) as parse_error:
        read_assembly(path=malformed)
    assert parse_error.value.code == "assembly.read_failed"

    unsupported = tmp_path / "unsupported.json"
    unsupported.write_text('{"schema_version":"other/1","assembly_id":"asm"}', encoding="utf-8")
    with pytest.raises(AssemblyValidationError) as schema_error:
        read_assembly(path=unsupported)
    assert schema_error.value.code == "assembly.unsupported_schema"
