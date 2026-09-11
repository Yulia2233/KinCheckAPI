from __future__ import annotations

from pathlib import Path

import pytest

from kincheckapi import cadir, kinematics, scenario
from kincheckapi._backends.solver_backend import (
    BackendCapabilityFailure,
    compile_assembly,
)
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
from kincheckapi.errors import AssemblyValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _joint(joint_id: str, left: str, right: str) -> Joint:
    return Joint(
        joint_id=joint_id,
        joint_type="revolute",
        connector_a=ConnectorRef(left, "axis"),
        connector_b=ConnectorRef(right, "axis"),
    )


def _assembly(
    component_ids: tuple[str, ...],
    joints: tuple[Joint, ...] = (),
    *,
    grounds: tuple[str, ...] = ("a",),
    closures: tuple[Closure, ...] = (),
) -> AssemblyModel:
    part = Part("part", connectors=(Connector("axis"),))
    return AssemblyModel(
        assembly_id="v014.topology",
        parts=(part,),
        components=tuple(Component(item, part.part_id) for item in component_ids),
        joints=joints,
        closures=closures,
        grounds=tuple(Ground(item) for item in grounds),
    )


def _four_bar(*, with_closure: bool) -> AssemblyModel:
    joints = (
        _joint("j1", "a", "b"),
        _joint("j2", "b", "c"),
        _joint("j3", "c", "d"),
        _joint("j4", "d", "a"),
    )
    closures = (
        Closure(
            closure_id="close.j3",
            constraint=Constraint(
                constraint_id="close.j3.constraint",
                connector_a=joints[2].connector_a,
                connector_b=joints[2].connector_b,
            ),
        ),
    ) if with_closure else ()
    return _assembly(("a", "b", "c", "d"), joints, closures=closures)


def test_solve_rejects_missing_ground_before_calling_backend(monkeypatch):
    assembly = _assembly(("a", "b"), (_joint("j1", "a", "b"),), grounds=())
    condition = scenario.create_scenario(scenario_id="v014.no-ground", assembly=assembly)
    called = False

    def unexpected_backend_call(*, scenario):
        nonlocal called
        called = True
        raise AssertionError("backend must not be called")

    monkeypatch.setattr("kincheckapi._backends.solve_scenario", unexpected_backend_call)
    with pytest.raises(AssemblyValidationError) as captured:
        kinematics.solve_motion(scenario=condition)

    assert not called
    assert captured.value.code == "KINCHECK-ASSEMBLY-TOPOLOGY-VALIDATION-FAILED"
    assert "topology.no_ground" in {item.code for item in captured.value.report.issues}


def test_direct_backend_compile_uses_the_same_topology_gate():
    assembly = _assembly(("a", "b"), grounds=("a",))

    with pytest.raises(BackendCapabilityFailure) as captured:
        compile_assembly(assembly=assembly)

    issues = captured.value.details["issues"]
    assert any(item["code"] == "topology.disconnected_island" for item in issues)


def test_loop_without_explicit_closure_is_rejected():
    result = validate_topology(assembly=_four_bar(with_closure=False))

    assert not result.passed
    assert "topology.missing_closure" in {item.code for item in result.issues}


def test_matching_closure_makes_the_same_loop_valid():
    assembly = _four_bar(with_closure=True)

    assert validate_topology(assembly=assembly).passed
    assert tuple(item.joint_id for item in build_kinematic_tree(assembly=assembly).closure_edges) == (
        "j3",
    )


def test_disconnected_island_is_reported_with_its_group_ids():
    assembly = _assembly(
        ("a", "b", "c", "d"),
        (_joint("j1", "a", "b"), _joint("j2", "c", "d")),
    )

    issue = next(
        item
        for item in validate_topology(assembly=assembly).issues
        if item.code == "topology.disconnected_island"
    )
    assert issue.object_ids == ("c", "d")


def test_multiple_world_fixed_groups_are_a_warning_not_a_compile_error():
    assembly = _assembly(("a", "b"), grounds=("a", "b"))
    result = validate_topology(assembly=assembly)

    issue = next(item for item in result.issues if item.code == "topology.multiple_roots")
    assert issue.severity == "warning"
    assert result.passed


def test_unmapped_joint_endpoint_is_structured():
    assembly = _assembly(("a",), (_joint("bad", "a", "missing"),))
    result = validate_topology(assembly=assembly)

    issue = next(item for item in result.issues if item.code == "topology.unmapped_joint")
    assert issue.object_ids == ("bad", "a", "missing")


def test_mjcf_adapter_promotes_every_detected_loop_edge_to_closure():
    root = PROJECT_ROOT / "tests" / "fixtures" / "closed_loop_four_bar"
    assembly = cadir.convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    ).assembly
    tree = build_kinematic_tree(assembly=assembly)

    assert tree.closure_edges
    assert validate_topology(assembly=assembly).passed
    assert len(assembly.closures) == len(tree.closure_edges)
