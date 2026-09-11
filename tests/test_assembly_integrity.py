from __future__ import annotations

from pathlib import Path

import pytest
import trimesh

from kincheckapi.assembly import AssemblyModel, Component, Connector, ConnectorRef, Joint, Part
from kincheckapi.checks import AssemblyIntegrityReport, ContainmentRelation, check_assembly_integrity
from kincheckapi.pose import Pose
from kincheckapi.result import MotionResult, Trajectory


def _assembly(*, positions: tuple[float, float] = (0.0, 3.0), with_joint: bool = False) -> AssemblyModel:
    connector = Connector(connector_id="axis")
    parts = (Part(part_id="part.a", connectors=(connector,)), Part(part_id="part.b", connectors=(connector,)))
    components = (
        Component(component_id="a", part_id="part.a", initial_pose=Pose(position_m=(positions[0], 0.0, 0.0))),
        Component(component_id="b", part_id="part.b", initial_pose=Pose(position_m=(positions[1], 0.0, 0.0))),
    )
    joints = ()
    if with_joint:
        joints = (Joint(joint_id="joint.ab", joint_type="fixed", connector_a=ConnectorRef(component_id="a", connector_id="axis"), connector_b=ConnectorRef(component_id="b", connector_id="axis")),)
    return AssemblyModel(assembly_id="integrity", parts=parts, components=components, joints=joints)


def _motion(assembly: AssemblyModel, positions: tuple[tuple[float, float], ...], *, status: str = "completed") -> MotionResult:
    times = tuple(float(index) for index in range(len(positions)))
    return MotionResult(
        scenario_id="integrity-scenario",
        assembly_id=assembly.assembly_id,
        status=status,
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        trajectories=tuple(
            Trajectory(
                component_id=component_id,
                times_s=times,
                poses=tuple(Pose(position_m=(pair[index], 0.0, 0.0)) for pair in positions),
            )
            for index, component_id in enumerate(("a", "b"))
        ),
    )


def test_two_remote_components_are_disconnected() -> None:
    report = check_assembly_integrity(assembly=_assembly(), sampling_scope="initial")
    assert not report.passed
    assert report.status == "failed"
    assert set(report.disconnected_component_ids) == {"a", "b"}
    assert report.connected_network_count_by_sample == ((0.0, 2),)


def test_mechanical_relation_connects_components() -> None:
    report = check_assembly_integrity(assembly=_assembly(with_joint=True), sampling_scope="initial")
    assert report.passed
    assert report.connected_component_ids == ("a", "b")
    assert report.mechanical_relation_results[0].relation_id == "joint.ab"


def test_geometric_connection_accepts_gap_within_tolerance(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    assembly = _assembly(positions=(0.0, 1.00005))
    assembly = AssemblyModel(
        assembly_id=assembly.assembly_id,
        parts=(
            Part(part_id="part.a", connectors=assembly.parts[0].connectors, asset_paths={"stl": "a.stl"}),
            Part(part_id="part.b", connectors=assembly.parts[1].connectors, asset_paths={"stl": "b.stl"}),
        ),
        components=assembly.components,
    )
    report = check_assembly_integrity(
        assembly=assembly,
        asset_root=tmp_path,
        geometric_connection_pairs=(("a", "b"),),
        sampling_scope="initial",
        geometric_connection_tolerance_m=1e-4,
    )
    assert report.passed
    assert report.geometric_connections[0].measurement_m == pytest.approx(0.00005, abs=1e-6)


def test_geometric_connection_rejects_gap_over_tolerance(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    base = _assembly(positions=(0.0, 1.01))
    assembly = AssemblyModel(
        assembly_id=base.assembly_id,
        parts=(Part(part_id="part.a", asset_paths={"stl": "a.stl"}), Part(part_id="part.b", asset_paths={"stl": "b.stl"})),
        components=base.components,
    )
    report = check_assembly_integrity(assembly=assembly, asset_root=tmp_path, geometric_connection_pairs=(("a", "b"),), sampling_scope="initial", geometric_connection_tolerance_m=1e-4)
    assert not report.passed
    assert "a" in report.disconnected_component_ids
    assert report.geometric_connections[0].reason == "Gap exceeds geometric connection tolerance."


def test_containment_passes_inside_interval_and_fails_after_escape() -> None:
    assembly = _assembly(positions=(0.0, 0.0), with_joint=False)
    relation = ContainmentRelation(relation_id="guide", contained_component_id="b", container_component_id="a", axis=(1.0, 0.0, 0.0), min_position_m=0.0, max_position_m=1.0)
    inside = _motion(assembly, ((0.0, 0.2), (0.0, 0.8)))
    inside_report = check_assembly_integrity(assembly=assembly, motion_result=inside, containment_relations=(relation,))
    assert inside_report.passed
    outside = _motion(assembly, ((0.0, 0.2), (0.0, 1.2)))
    outside_report = check_assembly_integrity(assembly=assembly, motion_result=outside, containment_relations=(relation,))
    assert not outside_report.passed
    assert outside_report.failed_sample_times_s == (1.0,)
    assert outside_report.out_of_bounds_component_ids == ("b",)


def test_partial_motion_is_not_a_pass() -> None:
    assembly = _assembly(with_joint=True)
    motion = _motion(assembly, ((0.0, 0.0),), status="partial")
    report = check_assembly_integrity(assembly=assembly, motion_result=motion)
    assert report.status == "partial"
    assert not report.passed


def test_zero_tolerance_requires_actual_contact(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    base = _assembly(positions=(0.0, 1.00001))
    assembly = AssemblyModel(assembly_id=base.assembly_id, parts=(Part(part_id="part.a", asset_paths={"stl": "a.stl"}), Part(part_id="part.b", asset_paths={"stl": "b.stl"})), components=base.components)
    report = check_assembly_integrity(assembly=assembly, asset_root=tmp_path, geometric_connection_pairs=(("a", "b"),), sampling_scope="initial", geometric_connection_tolerance_m=0.0)
    assert not report.passed


def test_invalid_tolerance_returns_validation_failure() -> None:
    report = check_assembly_integrity(assembly=_assembly(with_joint=True), sampling_scope="initial", geometric_connection_tolerance_m=-1.0)
    assert isinstance(report, AssemblyIntegrityReport)
    assert report.status == "validation_failed"
    assert any(item.code == "KINCHECK-INTEGRITY-INPUT-INVALID" for item in report.issues)


def test_report_serializes_ids_tolerances_and_operation() -> None:
    report = check_assembly_integrity(assembly=_assembly(with_joint=True), sampling_scope="initial", geometric_connection_tolerance_m=2e-4)
    payload = report.to_dict()
    assert payload["operation"] == "check_assembly_integrity"
    assert payload["geometric_connection_tolerance_m"] == pytest.approx(2e-4)
    assert payload["checked_component_ids"] == ["a", "b"]
    formatted = report.format_for_agent()
    assert "check_assembly_integrity" in formatted
    assert "checked_sample_count" in formatted


def test_containment_tolerance_accepts_small_escape() -> None:
    assembly = _assembly(positions=(0.0, 0.0))
    relation = ContainmentRelation(relation_id="guide", contained_component_id="b", container_component_id="a", axis=(1.0, 0.0, 0.0), min_position_m=0.0, max_position_m=1.0, allowed_escape_tolerance_m=0.01)
    motion = _motion(assembly, ((0.0, 1.005),))
    report = check_assembly_integrity(assembly=assembly, motion_result=motion, containment_relations=(relation,))
    assert report.passed


def test_containment_relation_rejects_invalid_interval() -> None:
    with pytest.raises(ValueError, match="min_position_m"):
        ContainmentRelation(relation_id="guide", contained_component_id="b", container_component_id="a", min_position_m=2.0, max_position_m=1.0)


def test_containment_relation_rejects_self_pair() -> None:
    with pytest.raises(ValueError, match="distinct"):
        ContainmentRelation(relation_id="guide", contained_component_id="a", container_component_id="a")


def test_unknown_containment_component_is_validation_failure() -> None:
    relation = ContainmentRelation(relation_id="guide", contained_component_id="missing", container_component_id="a")
    report = check_assembly_integrity(assembly=_assembly(), containment_relations=(relation,), sampling_scope="initial")
    assert report.status == "validation_failed"


def test_invalid_geometric_pair_is_validation_failure() -> None:
    report = check_assembly_integrity(assembly=_assembly(), geometric_connection_pairs=(("a", "missing"),), sampling_scope="initial")
    assert report.status == "validation_failed"


def test_missing_geometric_mesh_is_validation_failure() -> None:
    report = check_assembly_integrity(assembly=_assembly(), geometric_connection_pairs=(("a", "b"),), sampling_scope="initial")
    assert report.status == "validation_failed"
    assert any(item.code == "KINCHECK-INTEGRITY-GEOMETRY-INVALID" for item in report.issues)


def test_geometric_penetration_exceeding_tolerance_fails(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    box.export(tmp_path / "a.stl")
    box.export(tmp_path / "b.stl")
    base = _assembly(positions=(0.0, 0.5))
    assembly = AssemblyModel(assembly_id=base.assembly_id, parts=(Part(part_id="part.a", asset_paths={"stl": "a.stl"}), Part(part_id="part.b", asset_paths={"stl": "b.stl"})), components=base.components)
    report = check_assembly_integrity(assembly=assembly, asset_root=tmp_path, geometric_connection_pairs=(("a", "b"),), sampling_scope="initial", penetration_tolerance_m=0.0)
    assert not report.passed
    assert report.geometric_connections[0].reason == "Penetration exceeds tolerance."
