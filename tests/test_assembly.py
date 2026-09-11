from __future__ import annotations

from dataclasses import replace

import pytest

from kincheckapi.assembly import (
    Component,
    Connector,
    ConnectorRef,
    Constraint,
    Coupling,
    Joint,
    Part,
    add_closure_constraint,
    add_component,
    add_coupling,
    add_joint,
    add_part,
    create_assembly,
    exclude_collision_pair,
    ground_component,
    read_assembly,
    set_joint_limits,
    validate_assembly,
    write_assembly,
)
from kincheckapi.errors import AssemblyValidationError


def test_converted_examples_have_explicit_valid_topology(ex1_assembly, ex2_assembly):
    assert validate_assembly(assembly=ex1_assembly).passed
    assert (len(ex1_assembly.parts), len(ex1_assembly.components)) == (20, 20)
    assert validate_assembly(assembly=ex2_assembly).passed
    assert len(ex2_assembly.components) == 106
    assert ex2_assembly.metadata["source_map"]["schema_version"] == "1.0"


def test_assembly_round_trip(ex1_assembly, tmp_path):
    path = tmp_path / "assembly.json"
    write_assembly(assembly=ex1_assembly, path=path)
    loaded = read_assembly(path=path)
    assert loaded.assembly_id == ex1_assembly.assembly_id
    assert len(loaded.components) == len(ex1_assembly.components)
    assert validate_assembly(assembly=loaded).passed


def test_assembly_validation_aggregates_duplicate_and_dangling_ids(ex1_assembly):
    duplicate = replace(ex1_assembly.components[0], part_id="part.missing")
    invalid = replace(ex1_assembly, components=(*ex1_assembly.components, duplicate))
    check = validate_assembly(assembly=invalid)
    codes = {issue.code for issue in check.issues}
    assert "assembly.duplicate_id" in codes
    assert "assembly.missing_part" in codes


def _small_assembly():
    part = Part(part_id="part.test", connectors=(Connector(connector_id="axis"),))
    assembly = add_part(assembly=create_assembly(assembly_id="asm.test"), part=part)
    assembly = add_component(
        assembly=assembly,
        component=Component(component_id="cmp.a", part_id=part.part_id),
    )
    assembly = add_component(
        assembly=assembly,
        component=Component(component_id="cmp.b", part_id=part.part_id),
    )
    assembly = add_joint(
        assembly=assembly,
        joint=Joint(
            joint_id="joint.a",
            joint_type="revolute",
            connector_a=ConnectorRef(component_id="cmp.a", connector_id="axis"),
            connector_b=ConnectorRef(component_id="cmp.b", connector_id="axis"),
        ),
    )
    assembly = add_joint(
        assembly=assembly,
        joint=Joint(
            joint_id="joint.b",
            joint_type="revolute",
            connector_a=ConnectorRef(component_id="cmp.a", connector_id="axis"),
            connector_b=ConnectorRef(component_id="cmp.b", connector_id="axis"),
        ),
    )
    return assembly


def test_imperative_updates_are_immutable_and_cover_relationship_types():
    original = _small_assembly()
    updated = set_joint_limits(
        assembly=original, joint_id="joint.a", lower=-1.0, upper=2.0
    )
    updated = add_coupling(
        assembly=updated,
        coupling=Coupling(
            coupling_id="coupling.test",
            coupling_type="gear",
            joint_a_id="joint.a",
            joint_b_id="joint.b",
            ratio=-2.0,
        ),
    )
    updated = add_closure_constraint(
        assembly=updated,
        constraint=Constraint(
            constraint_id="closure.test",
            connector_a=ConnectorRef(component_id="cmp.a", connector_id="axis"),
            connector_b=ConnectorRef(component_id="cmp.b", connector_id="axis"),
        ),
    )
    updated = ground_component(assembly=updated, component_id="cmp.a")
    updated = exclude_collision_pair(
        assembly=updated, component_a_id="cmp.a", component_b_id="cmp.b"
    )

    assert original.get_joint(joint_id="joint.a").limit is None
    assert updated.get_joint(joint_id="joint.a").limit.lower == -1.0
    assert updated.couplings[0].ratio == -2.0
    assert updated.closures[0].closure_id == "closure.test"
    assert updated.collision_exclusions == (("cmp.a", "cmp.b"),)
    assert validate_assembly(assembly=updated).passed


def test_duplicate_add_and_invalid_collision_reference_raise_structured_errors():
    assembly = _small_assembly()
    with pytest.raises(AssemblyValidationError) as duplicate:
        add_part(assembly=assembly, part=Part(part_id="part.test"))
    assert duplicate.value.code == "assembly.duplicate_id"
    with pytest.raises(AssemblyValidationError) as dangling:
        exclude_collision_pair(
            assembly=assembly, component_a_id="cmp.a", component_b_id="cmp.missing"
        )
    assert dangling.value.code == "assembly.missing_component"


def test_json_write_is_byte_deterministic(ex1_assembly, tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_assembly(assembly=ex1_assembly, path=first)
    write_assembly(assembly=read_assembly(path=first), path=second)
    assert first.read_bytes() == second.read_bytes()
