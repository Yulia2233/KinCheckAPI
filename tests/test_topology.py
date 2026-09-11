from __future__ import annotations

from kincheckapi.assembly import (
    AssemblyModel,
    Closure,
    Component,
    Connector,
    ConnectorRef,
    Constraint,
    Ground,
    Joint,
    Part,
    build_kinematic_tree,
    validate_topology,
)


def _assembly(component_ids: tuple[str, ...], joints: tuple[Joint, ...] = (), *, grounds=("a",)):
    part = Part(part_id="part", connectors=(Connector(connector_id="axis"),))
    return AssemblyModel(
        assembly_id="topology.test",
        parts=(part,),
        components=tuple(Component(component_id=item, part_id=part.part_id) for item in component_ids),
        joints=joints,
        grounds=tuple(Ground(component_id=item) for item in grounds),
    )


def _joint(joint_id: str, left: str, right: str, *, metadata=None) -> Joint:
    return Joint(
        joint_id=joint_id,
        joint_type="revolute",
        connector_a=ConnectorRef(component_id=left, connector_id="axis"),
        connector_b=ConnectorRef(component_id=right, connector_id="axis"),
        metadata=metadata or {},
    )


def test_build_tree_reports_ground_root_and_parent_depths():
    assembly = _assembly(("a", "b", "c"), (_joint("j2", "b", "c"), _joint("j1", "a", "b")))

    tree = build_kinematic_tree(assembly=assembly)

    assert tree.root_group_ids == ("a",)
    assert tree.parent_group_id == {"a": None, "b": "a", "c": "b"}
    assert tree.parent_component_id == {"a": None, "b": "a", "c": "b"}
    assert tree.depth_by_component_id == {"a": 0, "b": 1, "c": 2}
    assert tuple(edge.joint_id for edge in tree.tree_edges) == ("j1", "j2")


def test_fixed_joint_components_form_one_rigid_group():
    assembly = _assembly(
        ("a", "b", "c"),
        (_joint("fixed", "a", "b"), _joint("move", "b", "c")),
    )
    fixed = assembly.joints[0]
    assembly = AssemblyModel(
        assembly_id=assembly.assembly_id,
        parts=assembly.parts,
        components=assembly.components,
        joints=(
            Joint(
                joint_id=fixed.joint_id,
                joint_type="fixed",
                connector_a=fixed.connector_a,
                connector_b=fixed.connector_b,
            ),
            assembly.joints[1],
        ),
        grounds=assembly.grounds,
    )

    tree = build_kinematic_tree(assembly=assembly)

    assert tree.component_groups["a"] == tree.component_groups["b"] == "a"
    assert tree.group_components["a"] == ("a", "b")
    assert tree.parent_group_id["c"] == "a"
    assert not tree.disconnected_group_ids


def test_four_bar_marks_non_tree_edge_as_closure():
    joints = (
        _joint("j1", "a", "b"),
        _joint("j2", "b", "c"),
        _joint("j3", "c", "d"),
        _joint("j4", "d", "a"),
    )
    tree = build_kinematic_tree(assembly=_assembly(("a", "b", "c", "d"), joints))

    assert tuple(edge.joint_id for edge in tree.tree_edges) == ("j1", "j2", "j4")
    assert tuple(edge.joint_id for edge in tree.closure_edges) == ("j3",)
    assert tree.disconnected_group_ids == ()


def test_four_bar_requires_and_accepts_matching_closure_definition():
    joints = (
        _joint("j1", "a", "b"),
        _joint("j2", "b", "c"),
        _joint("j3", "c", "d"),
        _joint("j4", "d", "a"),
    )
    base = _assembly(("a", "b", "c", "d"), joints)
    closure = Closure(
        closure_id="close.j3",
        constraint=Constraint(
            constraint_id="close.constraint",
            connector_a=ConnectorRef(component_id="c", connector_id="axis"),
            connector_b=ConnectorRef(component_id="d", connector_id="axis"),
        ),
    )
    assembly = AssemblyModel(
        assembly_id=base.assembly_id,
        parts=base.parts,
        components=base.components,
        joints=base.joints,
        closures=(closure,),
        grounds=base.grounds,
    )

    result = validate_topology(assembly=assembly)

    assert result.passed
    assert not result.issues


def test_explicit_closure_endpoints_choose_the_authored_loop_edge():
    joints = (
        _joint("j1", "a", "b"),
        _joint("j2", "b", "c"),
        _joint("j3", "c", "d"),
        _joint("j4", "d", "a"),
    )
    base = _assembly(("a", "b", "c", "d"), joints)
    assembly = AssemblyModel(
        assembly_id=base.assembly_id,
        parts=base.parts,
        components=base.components,
        joints=base.joints,
        closures=(
            Closure(
                closure_id="close.j4",
                constraint=Constraint(
                    constraint_id="close.j4.constraint",
                    connector_a=joints[3].connector_a,
                    connector_b=joints[3].connector_b,
                ),
            ),
        ),
        grounds=base.grounds,
    )

    tree = build_kinematic_tree(assembly=assembly)
    result = validate_topology(assembly=assembly)

    assert tuple(edge.joint_id for edge in tree.closure_edges) == ("j4",)
    assert result.passed
    assert not result.issues


def test_explicit_closure_role_is_preserved_and_not_used_as_tree_edge():
    joint = _joint("j1", "a", "b", metadata={"topology_role": "closure_edge"})
    base = _assembly(("a", "b"), (joint,))
    closure = Closure(
        closure_id="close.j1",
        constraint=Constraint(
            constraint_id="close.constraint",
            connector_a=joint.connector_a,
            connector_b=joint.connector_b,
        ),
    )
    assembly = AssemblyModel(
        assembly_id=base.assembly_id,
        parts=base.parts,
        components=base.components,
        joints=base.joints,
        closures=(closure,),
        grounds=base.grounds,
    )

    tree = build_kinematic_tree(assembly=assembly)
    result = validate_topology(assembly=assembly)

    assert not tree.tree_edges
    assert tuple(edge.joint_id for edge in tree.closure_edges) == ("j1",)
    assert tree.disconnected_group_ids == ("b",)
    assert "topology.disconnected_island" in {issue.code for issue in result.issues}


def test_no_ground_is_reported_and_no_group_is_promoted_to_root():
    assembly = _assembly(("a", "b"), (_joint("j1", "a", "b"),), grounds=())

    tree = build_kinematic_tree(assembly=assembly)
    result = validate_topology(assembly=assembly)

    assert tree.root_group_ids == ()
    assert tree.disconnected_group_ids == ("a", "b")
    assert {"topology.no_ground", "topology.disconnected_island"} <= {
        issue.code for issue in result.issues
    }


def test_multiple_ground_groups_are_reported_as_multiple_roots():
    assembly = _assembly(("a", "b"), grounds=("a", "b"))

    result = validate_topology(assembly=assembly)

    assert "topology.multiple_roots" in {issue.code for issue in result.issues}
    assert "topology.disconnected_island" not in {issue.code for issue in result.issues}


def test_disconnected_island_is_explicitly_reported():
    assembly = _assembly(("a", "b", "c", "d"), (_joint("j1", "a", "b"), _joint("j2", "c", "d")))

    tree = build_kinematic_tree(assembly=assembly)
    result = validate_topology(assembly=assembly)

    assert tree.disconnected_group_ids == ("c", "d")
    assert "topology.disconnected_island" in {issue.code for issue in result.issues}


def test_parallel_joints_report_duplicate_parent_and_missing_closure():
    assembly = _assembly(("a", "b"), (_joint("j1", "a", "b"), _joint("j2", "a", "b")))

    tree = build_kinematic_tree(assembly=assembly)
    result = validate_topology(assembly=assembly)
    codes = {issue.code for issue in result.issues}

    assert len(tree.tree_edges) == 1
    assert len(tree.closure_edges) == 1
    assert {"topology.duplicate_parent", "topology.missing_closure"} <= codes
