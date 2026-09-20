"""Density integration, frame transport and occurrence-preserving aggregation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping, Sequence
import hashlib
import importlib.metadata

import numpy as np

from .assembly import AssemblyModel, build_kinematic_tree, validate_assembly
from .pose import (
    Pose,
    relative_pose,
    rotate_vector,
    transform_point,
    orientation_error_rad,
)
from .physics_types import (
    DynamicsModel,
    Payload,
    PhysicsManifest,
    PhysicsMaterial,
    PhysicsReport,
    RigidBodyProperties,
    digest,
    fail,
    issue,
)


def rotation(pose):
    return np.asarray([rotate_vector(pose=pose, vector=v) for v in np.eye(3)]).T


def transform_mass_properties(
    *, properties: RigidBodyProperties, pose: Pose, frame_id: str
) -> RigidBodyProperties:
    """Rigid transport; COM inertia rotates but translation adds no parallel-axis term."""
    r = rotation(pose)
    return replace(
        properties,
        com_m=transform_point(pose=pose, point_m=properties.com_m),
        inertia_com_kg_m2=r @ properties.inertia_com_kg_m2 @ r.T,
        frame_id=frame_id,
    )


def aggregate_mass_properties(
    *, properties: Sequence[RigidBodyProperties], frame_id: str
) -> RigidBodyProperties:
    """Sum every supplied physical instance using the parallel-axis theorem."""
    items = tuple(properties)
    if not items or any(p.frame_id != frame_id for p in items):
        fail(
            "FRAME-INCOMPATIBLE",
            "Aggregation requires nonempty properties in the named common frame.",
            operation="aggregate_mass_properties",
            objects=(frame_id,),
        )
    mass = sum(p.mass_kg for p in items)
    com = sum((p.mass_kg * np.asarray(p.com_m) for p in items), np.zeros(3)) / mass
    inertia = np.zeros((3, 3))
    for p in items:
        d = np.asarray(p.com_m) - com
        inertia += p.inertia_com_kg_m2 + p.mass_kg * (
            np.dot(d, d) * np.eye(3) - np.outer(d, d)
        )
    return RigidBodyProperties(
        mass_kg=mass,
        com_m=com,
        inertia_com_kg_m2=inertia,
        frame_id=frame_id,
        source_kind="aggregate",
        source_ids=tuple(s for p in items for s in p.source_ids),
        provenance={
            "method": "parallel-axis/1",
            "members_sha256": digest([p.to_dict() for p in items]),
        },
    )


def measure_mass_properties(
    *,
    brep: bytes | str | Path,
    material: PhysicsMaterial,
    definition_id: str,
    frame_id: str | None = None,
) -> RigidBodyProperties:
    """Integrate one validated closed BREP solid in mm with uniform explicit density.

    OCCT MatrixOfInertia is already about the volume centroid and has units mm^5.
    CAD is optional until this entry point is called. No mesh/default mass fallback.
    """
    op = "measure_mass_properties"
    try:
        from OCP.BRep import BRep_Tool
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.TopAbs import TopAbs_SHELL
        from OCP.TopExp import TopExp_Explorer
        from simplecadapi.artifacts.brep import read_brep_solid
    except ImportError as exc:
        fail(
            "BACKEND-UNAVAILABLE",
            str(exc),
            operation=op,
            status="capability_failed",
            objects=(definition_id,),
            fix="Install the declared addon extra in the analysis environment.",
        )
    if not isinstance(material, PhysicsMaterial):
        fail(
            "DENSITY-MISSING",
            "A typed explicit material is required.",
            operation=op,
            objects=(definition_id,),
        )
    try:
        raw = brep if isinstance(brep, bytes) else Path(brep).read_bytes()
        shape = read_brep_solid(raw).wrapped
        shells = TopExp_Explorer(shape, TopAbs_SHELL)
        count = 0
        while shells.More():
            if not BRep_Tool.IsClosed_s(shells.Current()):
                raise ValueError("Solid contains an open shell")
            count += 1
            shells.Next()
        if not count:
            raise ValueError("Solid contains no closed shell")
        gp = GProp_GProps()
        # Adaptive exact BREP integration, OnlyClosed=True, SkipShared=False.
        error = BRepGProp.VolumeProperties_s(shape, gp, 1e-11, True, False)
        volume = gp.Mass()
        center = gp.CentreOfMass()
        tensor = gp.MatrixOfInertia()
        j = np.array([[tensor.Value(i + 1, k + 1) for k in range(3)] for i in range(3)])
        if not np.isfinite(volume) or volume <= 0:
            raise ValueError("Closed solid volume must be finite and positive")
    except Exception as exc:
        fail(
            "SOLID-INVALID",
            str(exc),
            operation=op,
            objects=(definition_id,),
            fix="Repair and re-capture one valid, outward-oriented closed solid; shells and line bodies are unsupported.",
        )
    rho = material.density_kg_m3
    com_mm = (center.X(), center.Y(), center.Z())
    source = {
        "brep_sha256": hashlib.sha256(raw).hexdigest(),
        "material": {
            "material_id": material.material_id,
            "density": material.density,
            "density_unit": material.density_unit,
            "source": material.source,
            "data_quality": material.data_quality,
        },
        "volume_mm3": volume,
        "com_mm": com_mm,
        "inertia_volume_mm5": j.tolist(),
        "density_kg_m3": rho,
        "integration_relative_error": float(error),
        "integration_tolerance": 1e-11,
        "algorithm": "occt-volume-com-tensor-si/1",
        "occt_package": importlib.metadata.version("cadquery-ocp"),
    }
    source["cache_key"] = digest(
        {k: source[k] for k in ("brep_sha256", "material", "algorithm")}
    )
    return RigidBodyProperties(
        mass_kg=rho * volume * 1e-9,
        com_m=np.asarray(com_mm) * 1e-3,
        inertia_com_kg_m2=rho * j * 1e-15,
        frame_id=frame_id or definition_id,
        source_kind="brep_integral",
        source_ids=(definition_id,),
        provenance=source,
    )


def build_dynamics_model(
    *,
    assembly: AssemblyModel,
    manifest: PhysicsManifest | None = None,
    component_properties: Mapping[str, RigidBodyProperties] | None = None,
    occurrence_components: Mapping[str, str] | None = None,
    payloads: Sequence[Payload] = (),
) -> DynamicsModel:
    """Bind complete CAD occurrence coverage OR explicit component-frame measurements."""
    op = "build_dynamics_model"
    validation = validate_assembly(assembly=assembly)
    if not validation.passed:
        fail(
            "MODEL-INVALID",
            "Assembly validation failed.",
            operation=op,
            evidence=validation.to_dict(),
        )
    if manifest is not None and component_properties is not None:
        fail(
            "PHYSICS-SOURCE-CONFLICT",
            "Two physical sources require an explicit comparison, never silent priority.",
            operation=op,
        )
    ids = {c.component_id for c in assembly.components}
    mapping = dict(occurrence_components or {})
    props = dict(component_properties or {})
    if manifest is not None:
        if (
            manifest.producer.get("root_definition_id", assembly.assembly_id)
            != assembly.assembly_id
        ):
            fail(
                "PHYSICS-SOURCE-CONFLICT",
                "CAD and assembly root identities differ.",
                operation=op,
            )
        if not mapping:
            for c in assembly.components:
                for member in c.metadata.get("members", (c.component_id,)):
                    if member in mapping:
                        fail(
                            "OCCURRENCE-COVERAGE-INCOMPLETE",
                            "Occurrence belongs to multiple components.",
                            operation=op,
                            objects=(member,),
                        )
                    mapping[member] = c.component_id
            leaf_ids = {o.occurrence_id for o in manifest.occurrences}
            # Structural assembly nodes carry no mass. Only SDK-declared leafs count.
            mapping = {k: v for k, v in mapping.items() if k in leaf_ids}
        actual = {o.occurrence_id for o in manifest.occurrences}
        if set(mapping) != actual or not set(mapping.values()) <= ids:
            fail(
                "OCCURRENCE-COVERAGE-INCOMPLETE",
                "Every physical occurrence must map exactly once to an existing component.",
                operation=op,
                objects=tuple(sorted(actual ^ set(mapping))),
                evidence={"actual": sorted(actual), "mapping": mapping},
            )
        for c in assembly.components:
            part = assembly.get_part(part_id=c.part_id)
            mesh_poses = part.metadata.get("mesh_poses") if part else None
            if mesh_poses is not None:
                expected_by_definition = {}
                for occurrence in manifest.occurrences:
                    if mapping[occurrence.occurrence_id] == c.component_id:
                        expected_by_definition.setdefault(
                            occurrence.definition_id, []
                        ).append(
                            relative_pose(
                                parent=c.initial_pose, child=occurrence.pose_world
                            )
                        )
                if set(mesh_poses) != set(expected_by_definition):
                    fail(
                        "PHYSICS-SOURCE-CONFLICT",
                        "CAD definitions and exported mesh identities differ.",
                        operation=op,
                        objects=(c.component_id,),
                    )
                for did, expected_poses in expected_by_definition.items():
                    actual_poses = [
                        p if isinstance(p, Pose) else Pose(**p) for p in mesh_poses[did]
                    ]
                    for expected_pose in expected_poses:
                        match = next(
                            (
                                i
                                for i, p in enumerate(actual_poses)
                                if np.linalg.norm(
                                    np.asarray(p.position_m) - expected_pose.position_m
                                )
                                <= 1e-8
                                and orientation_error_rad(
                                    actual=p, expected=expected_pose
                                )
                                <= 1e-7
                            ),
                            None,
                        )
                        if match is None:
                            fail(
                                "FRAME-INCOMPATIBLE",
                                "CAD occurrence and exported mesh placement differ.",
                                operation=op,
                                objects=(c.component_id, did),
                            )
                        actual_poses.pop(match)
                    if actual_poses:
                        fail(
                            "OCCURRENCE-COVERAGE-INCOMPLETE",
                            "Export contains extra geometry instances.",
                            operation=op,
                            objects=(c.component_id, did),
                        )
            members = [
                transform_mass_properties(
                    properties=o.properties,
                    pose=relative_pose(parent=c.initial_pose, child=Pose()),
                    frame_id=c.component_id,
                )
                for o in manifest.occurrences
                if mapping[o.occurrence_id] == c.component_id
            ]
            if members:
                props[c.component_id] = aggregate_mass_properties(
                    properties=members, frame_id=c.component_id
                )
    if set(props) != ids:
        fail(
            "OCCURRENCE-COVERAGE-INCOMPLETE",
            "All components, including ground and hardware, need physical properties.",
            operation=op,
            objects=tuple(sorted(ids ^ set(props))),
            fix="Supply CAD BREP/material coverage or explicit measured component-frame properties; kinematic placeholder mass is not a source.",
        )
    for cid, p in props.items():
        if p.frame_id != cid:
            fail(
                "FRAME-INCOMPATIBLE",
                "Component properties must use its local frame.",
                operation=op,
                objects=(cid, p.frame_id),
            )
    base_props = dict(props)
    seen = set()
    occupied_sources = {s for p in props.values() for s in p.source_ids}
    for payload in payloads:
        if payload.payload_id in seen or payload.component_id not in ids:
            fail(
                "PAYLOAD-DUPLICATED",
                "Payload identity is duplicated or receiver is absent.",
                operation=op,
                objects=(payload.payload_id,),
            )
        seen.add(payload.payload_id)
        if payload.cad_occurrence_id:
            if (
                mapping.get(payload.cad_occurrence_id) != payload.component_id
                or payload.cad_occurrence_id in seen
            ):
                fail(
                    "PAYLOAD-DUPLICATED",
                    "CAD payload must identify one existing occurrence on its declared receiver.",
                    operation=op,
                    objects=(payload.payload_id, payload.cad_occurrence_id),
                )
            seen.add(payload.cad_occurrence_id)
        else:
            p = payload.properties
            if (
                any(s in mapping or s in occupied_sources for s in p.source_ids)
                or p.frame_id != payload.component_id
            ):
                fail(
                    "PAYLOAD-DUPLICATED",
                    "Additional payload overlaps CAD identity or uses the wrong frame.",
                    operation=op,
                    objects=(payload.payload_id,),
                )
            occupied_sources.update(p.source_ids)
            props[payload.component_id] = aggregate_mass_properties(
                properties=(props[payload.component_id], p),
                frame_id=payload.component_id,
            )
    tree = build_kinematic_tree(assembly=assembly)
    bodies = {}
    for gid, members in tree.group_components.items():
        parent = assembly.get_component(component_id=members[0]).initial_pose
        bodies[gid] = aggregate_mass_properties(
            properties=[
                transform_mass_properties(
                    properties=props[cid],
                    pose=relative_pose(
                        parent=parent,
                        child=assembly.get_component(component_id=cid).initial_pose,
                    ),
                    frame_id=gid,
                )
                for cid in members
            ],
            frame_id=gid,
        )
    return DynamicsModel(
        assembly=assembly,
        component_properties=props,
        body_properties=bodies,
        occurrence_components=mapping,
        manifest=manifest,
        payloads=tuple(payloads),
        base_component_properties=base_props,
    )


def compare_properties(
    actual, expected, *, operation, object_id, relative_tolerance=1e-8
):
    problems = []
    if actual.frame_id != expected.frame_id:
        problems.append(
            issue(
                "FRAME-INCOMPATIBLE",
                "Properties use the wrong frame.",
                operation,
                (object_id,),
                actual=actual.frame_id,
                expected=expected.frame_id,
            )
        )
    for key, unit, atol in [
        ("mass_kg", "kg", 1e-10),
        ("com_m", "m", 1e-10),
        ("inertia_com_kg_m2", "kg*m2", 1e-14),
    ]:
        a, e = np.asarray(getattr(actual, key)), np.asarray(getattr(expected, key))
        if not np.allclose(a, e, rtol=relative_tolerance, atol=atol):
            problems.append(
                issue(
                    "BACKEND-INERTIAL-MISMATCH",
                    f"{key} does not match its source.",
                    operation,
                    (object_id,),
                    actual=a.tolist(),
                    expected=e.tolist(),
                    unit=unit,
                    fix="Correct density scaling, tensor frame or fixed-group membership and recompile.",
                )
            )
    return problems


def check_mass_properties(*, model: DynamicsModel) -> PhysicsReport:
    """Recompute occurrence transport and aggregation to detect frame/source drift."""
    op = "check_mass_properties"
    problems = []
    if model.manifest:
        for o in model.manifest.occurrences:
            definition = model.manifest.definitions.get(o.definition_id)
            if definition is None:
                problems.append(
                    issue(
                        "OCCURRENCE-COVERAGE-INCOMPLETE",
                        "Missing definition properties.",
                        op,
                        (o.occurrence_id,),
                    )
                )
                continue
            provenance = definition.provenance
            if (
                provenance.get("definition_content_hash", o.content_hash)
                != o.content_hash
                or provenance.get("revision", o.revision) != o.revision
            ):
                problems.append(
                    issue(
                        "PHYSICS-SOURCE-CONFLICT",
                        "Occurrence definition hash/revision differs.",
                        op,
                        (o.occurrence_id,),
                    )
                )
            expected = transform_mass_properties(
                properties=definition, pose=o.pose_world, frame_id="world"
            )
            problems.extend(
                compare_properties(
                    o.properties, expected, operation=op, object_id=o.occurrence_id
                )
            )
            p = definition.provenance
            if definition.source_kind == "brep_integral":
                rho = PhysicsMaterial(**dict(p["material"])).density_kg_m3
                if (
                    p["cache_key"]
                    != digest(
                        {k: p[k] for k in ("brep_sha256", "material", "algorithm")}
                    )
                    or not np.isclose(
                        definition.mass_kg,
                        rho * p["volume_mm3"] * 1e-9,
                        rtol=1e-8,
                        atol=1e-10,
                    )
                    or not np.allclose(
                        definition.com_m,
                        np.asarray(p["com_mm"]) * 1e-3,
                        rtol=0,
                        atol=1e-10,
                    )
                    or not np.allclose(
                        definition.inertia_com_kg_m2,
                        rho * np.asarray(p["inertia_volume_mm5"]) * 1e-15,
                        rtol=1e-8,
                        atol=1e-14,
                    )
                ):
                    problems.append(
                        issue(
                            "PHYSICS-SOURCE-CONFLICT",
                            "Density/integral/cache-key mismatch.",
                            op,
                            (o.definition_id,),
                            fix="Remeasure the original BREP with the declared density and units.",
                        )
                    )
        rebuilt = build_dynamics_model(
            assembly=model.assembly,
            manifest=model.manifest,
            occurrence_components=model.occurrence_components,
            payloads=model.payloads,
        )
    else:
        rebuilt = build_dynamics_model(
            assembly=model.assembly,
            component_properties=model.base_component_properties
            or (model.component_properties if not model.payloads else {}),
            payloads=model.payloads,
        )
    for cid, expected in rebuilt.component_properties.items():
        problems.extend(
            compare_properties(
                model.component_properties[cid], expected, operation=op, object_id=cid
            )
        )
    for gid, expected in rebuilt.body_properties.items():
        if gid not in model.body_properties:
            problems.append(
                issue(
                    "OCCURRENCE-COVERAGE-INCOMPLETE", "Missing rigid body.", op, (gid,)
                )
            )
        else:
            problems.extend(
                compare_properties(
                    model.body_properties[gid], expected, operation=op, object_id=gid
                )
            )
    return PhysicsReport(
        operation=op,
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            "component_count": len(model.component_properties),
            "body_count": len(model.body_properties),
            "total_mass_kg": sum(
                p.mass_kg for p in model.component_properties.values()
            ),
            "includes_ground": True,
        },
    )
