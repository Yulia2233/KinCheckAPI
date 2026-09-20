"""Static BREP all-pairs checks with local functional-contact regions.

This is geometric acceptance, not a contact-force solver. It never consumes
AssemblyModel.collision_exclusions and never treats fixed groups as one solid.
"""

from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence
import hashlib
import json
import numpy as np

from .addon import _read_package, _blob_bytes
from .physics_types import PhysicsManifest, PhysicsReport, fail, issue, vector, positive
from .physics_mass import rotation
from .pose import Pose, compose_pose, inverse_pose, transform_point


@dataclass(frozen=True, kw_only=True)
class ContactRegion:
    """Allowed local region in occurrence_a's definition frame, in SI metres.

    Both named interfaces must resolve to recorded topology. Every closest-point
    witness must lie inside the region; interpenetrating solids always fail.
    An ideal clearance fit is a geometric relation, not proof of load sharing.
    """

    occurrence_a: str
    occurrence_b: str
    interface_a: str
    interface_b: str
    lower_m: tuple[float, float, float]
    upper_m: tuple[float, float, float]
    minimum_gap_m: float = 0.0
    maximum_gap_m: float = 0.0002
    normal_a: tuple[float, float, float] = (0.0, 0.0, 1.0)
    purpose: str = "ideal mechanical interface"
    required_connection: bool = True

    def __post_init__(self):
        for name in ("lower_m", "upper_m", "normal_a"):
            object.__setattr__(
                self, name, vector(getattr(self, name), name, "ContactRegion")
            )
        if (
            any(lo > hi for lo, hi in zip(self.lower_m, self.upper_m))
            or self.occurrence_a == self.occurrence_b
        ):
            fail(
                "CONTACT-REGION-INVALID",
                "Contact region bounds or pair are invalid.",
                operation="ContactRegion",
            )
        for name in ("minimum_gap_m", "maximum_gap_m"):
            positive(getattr(self, name), name, "ContactRegion", zero=True)
        if (
            self.minimum_gap_m > self.maximum_gap_m
            or abs(np.linalg.norm(self.normal_a) - 1) > 1e-9
        ):
            fail(
                "CONTACT-REGION-INVALID",
                "Contact gap interval or normal is invalid.",
                operation="ContactRegion",
            )


def check_static_geometry(
    *,
    package_path: str | Path,
    manifest: PhysicsManifest,
    occurrence_components: Mapping[str, str],
    component_initial_poses: Mapping[str, Pose],
    component_poses: Mapping[str, Pose],
    contacts: Sequence[ContactRegion] = (),
    free_clearance_m: float = 0.0001,
    guard_clearance_m: float = 0.005,
    guard_occurrence_ids: Sequence[str] = (),
    query_error_m: float = 1e-9,
) -> PhysicsReport:
    """Check every leaf pair using exact BREP, including fixed-group internals.

    Broad-phase boxes only prove separation; nearby pairs use BREP distances and
    solid intersections. No triangle approximation is used for acceptance.
    """
    op = "check_static_geometry"
    for name, val in [
        ("free_clearance_m", free_clearance_m),
        ("guard_clearance_m", guard_clearance_m),
        ("query_error_m", query_error_m),
    ]:
        positive(val, name, op)
    if query_error_m > min(free_clearance_m, guard_clearance_m) / 3:
        fail(
            "GEOMETRY-BUDGET-INVALID",
            "Query error exceeds one third of the required clearance.",
            operation=op,
        )
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.gp import gp_Pnt
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.Bnd import Bnd_Box
    from OCP.gp import gp_Trsf
    from simplecadapi.artifacts.brep import read_brep_solid

    source = Path(package_path).resolve()
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest.source_sha256:
        fail(
            "PHYSICS-SOURCE-CONFLICT",
            "Geometry source hash differs from mass source.",
            operation=op,
        )
    package = _read_package(raw, source)
    definitions = {}
    for record in package.manifest["definitions"]:
        if record["definition_kind"] == "single_solid":
            d = json.loads(package.objects[record["path"]])
            definitions[record["definition_id"]] = read_brep_solid(
                _blob_bytes(package, d["solid_cache"]["body_ref"])
            ).wrapped
    graph = json.loads(package.objects[package.manifest["occurrence_graph"]["path"]])
    occurrences = {o.occurrence_id: o for o in manifest.occurrences}
    problems = []
    shapes = {}
    boundaries = {}
    boxes = {}
    world = {}
    if set(occurrences) != set(occurrence_components):
        fail(
            "OCCURRENCE-COVERAGE-INCOMPLETE",
            "Geometry requires exactly all physical occurrences.",
            operation=op,
        )
    for oid, o in occurrences.items():
        cid = occurrence_components[oid]
        delta = compose_pose(
            parent=component_poses[cid],
            child=inverse_pose(pose=component_initial_poses[cid]),
        )
        pose = compose_pose(parent=delta, child=o.pose_world)
        world[oid] = pose
        r = rotation(pose)
        t = np.asarray(pose.position_m) * 1000
        tr = gp_Trsf()
        tr.SetValues(*[float(v) for row in np.column_stack((r, t)) for v in row])
        shape = BRepBuilderAPI_Transform(definitions[o.definition_id], tr, True).Shape()
        shapes[oid] = shape
        builder = BRep_Builder()
        boundary = TopoDS_Compound()
        builder.MakeCompound(boundary)
        shells = TopExp_Explorer(shape, TopAbs_SHELL)
        while shells.More():
            builder.Add(boundary, shells.Current())
            shells.Next()
        boundaries[oid] = boundary
        box = Bnd_Box()
        BRepBndLib.AddOptimal_s(shape, box, False, True)
        boxes[oid] = np.asarray(box.Get()) * 0.001
    contact_map = {}
    for contact in contacts:
        key = tuple(sorted((contact.occurrence_a, contact.occurrence_b)))
        for oid, name in (
            (contact.occurrence_a, contact.interface_a),
            (contact.occurrence_b, contact.interface_b),
        ):
            if oid not in occurrences or not occurrences[oid].interfaces.get(name):
                problems.append(
                    issue(
                        "CONTACT-INTERFACE-MISSING",
                        "Named local contact interface is missing.",
                        op,
                        (oid, name),
                    )
                )
        contact_map.setdefault(key, []).append(contact)
    # Real CAD relations, not hierarchy containment, must connect every leaf.
    adjacent = {n["node_id"]: set() for n in graph["nodes"]}
    for edge in graph["ground_edges"]:
        x, y = edge["parent_node_id"], edge["child_node_id"]
        adjacent[x].add(y)
        adjacent[y].add(x)
    for joint in graph["joints"]:
        x, y = joint["connector_a"]["instance_id"], joint["connector_b"]["instance_id"]
        adjacent[x].add(y)
        adjacent[y].add(x)
    visited = set()
    pending = [graph["root_node_id"]]
    while pending:
        x = pending.pop()
        if x not in visited:
            visited.add(x)
            pending.extend(adjacent[x] - visited)
    for oid in sorted(set(occurrences) - visited):
        problems.append(
            issue(
                "SUPPORT-MISSING",
                "Physical entity has no CAD joint/fastener path to ground.",
                op,
                (oid,),
                fix="Add the real mounting interface and its CAD relation.",
            )
        )
    ledger = []
    guards = set(guard_occurrence_ids)
    for a, b in combinations(sorted(occurrences), 2):
        regions = contact_map.get((a, b), [])
        required = (
            guard_clearance_m
            if (a in guards or b in guards)
            and occurrence_components[a] != occurrence_components[b]
            else free_clearance_m
        )
        aa, bb = boxes[a], boxes[b]
        lower = float(
            np.linalg.norm(np.maximum(0, np.maximum(aa[:3] - bb[3:], bb[:3] - aa[3:])))
        )
        record = {
            "occurrences": [a, b],
            "required_clearance_m": required,
            "same_rigid_group": occurrence_components[a] == occurrence_components[b],
            "query_error_m": query_error_m,
        }
        if lower - query_error_m >= required and not regions:
            ledger.append(
                {
                    **record,
                    "status": "passed",
                    "method": "conservative-brep-aabb",
                    "lower_bound_m": lower - query_error_m,
                }
            )
            continue
        solid_distance = BRepExtrema_DistShapeShape(shapes[a], shapes[b])
        solid_distance.Perform()
        # Solid 'inner solution' witnesses can be uninitialized at touching
        # faces in OCCT. Query actual boundary shells for surface witnesses;
        # keep the solid distance for containment/intersection detection.
        distance = BRepExtrema_DistShapeShape(boundaries[a], boundaries[b])
        distance.Perform()
        if not distance.IsDone() or distance.NbSolution() < 1:
            problems.append(
                issue(
                    "GEOMETRY-UNAVAILABLE",
                    "BREP distance has no complete result.",
                    op,
                    (a, b),
                )
            )
            ledger.append({**record, "status": "indeterminate"})
            continue
        gap = float(distance.Value()) * 0.001
        witnesses = []
        for n in range(1, distance.NbSolution() + 1):
            p, q = distance.PointOnShape1(n), distance.PointOnShape2(n)
            witnesses.append(
                (
                    [p.X() * 0.001, p.Y() * 0.001, p.Z() * 0.001],
                    [q.X() * 0.001, q.Y() * 0.001, q.Z() * 0.001],
                )
            )
        intersection_mm3 = 0.0
        if not solid_distance.IsDone():
            fail(
                "GEOMETRY-UNAVAILABLE",
                "Solid distance query failed.",
                operation=op,
                objects=(a, b),
            )
        if solid_distance.Value() * 0.001 <= query_error_m:
            common = BRepAlgoAPI_Common(shapes[a], shapes[b])
            common.Build()
            if not common.IsDone():
                problems.append(
                    issue(
                        "GEOMETRY-UNAVAILABLE", "BREP intersection failed.", op, (a, b)
                    )
                )
                ledger.append({**record, "status": "indeterminate"})
                continue
            props = GProp_GProps()
            BRepGProp.VolumeProperties_s(common.Shape(), props)
            intersection_mm3 = abs(props.Mass())
        local_allowed = False
        for region in regions:
            local = inverse_pose(pose=world[region.occurrence_a])
            lo = np.asarray(region.lower_m)
            hi = np.asarray(region.upper_m)
            if not (
                gap + query_error_m >= region.minimum_gap_m
                and gap - query_error_m <= region.maximum_gap_m
            ):
                continue
            # Prove the complement of the declared local patch remains clear.
            # This also covers non-nearest contacts and avoids OCCT's invalid
            # solid-inner witnesses. No solid overlap is allowed anywhere.
            cutter = BRepPrimAPI_MakeBox(
                gp_Pnt(*(lo * 1000)), gp_Pnt(*(hi * 1000))
            ).Shape()
            rp = world[region.occurrence_a]
            rr = rotation(rp)
            rt = np.asarray(rp.position_m) * 1000
            transform = gp_Trsf()
            transform.SetValues(
                *[float(v) for row in np.column_stack((rr, rt)) for v in row]
            )
            cutter = BRepBuilderAPI_Transform(cutter, transform, True).Shape()
            cut = BRepAlgoAPI_Cut(shapes[region.occurrence_a], cutter)
            cut.Build()
            if not cut.IsDone():
                continue
            remainder = cut.Shape()
            vol = GProp_GProps()
            BRepGProp.VolumeProperties_s(remainder, vol)
            if abs(vol.Mass()) <= 1e-6:
                outside_clear = True
            else:
                other = region.occurrence_b
                outside = BRepExtrema_DistShapeShape(remainder, shapes[other])
                outside.Perform()
                outside_clear = (
                    outside.IsDone()
                    and outside.Value() * 0.001 - query_error_m >= required
                )
            if outside_clear:
                local_allowed = True
                break
        # 1e-6 mm^3 is the frozen absolute kernel sliver budget, independent of
        # intended interface size. Material overlaps are never blanket-allowed.
        passed = intersection_mm3 <= 1e-6 and (
            local_allowed
            or (
                not any(r.required_connection for r in regions)
                and gap - query_error_m >= required
            )
        )
        if not passed:
            code = (
                "GEOMETRY-INTERFERENCE"
                if intersection_mm3 > 1e-6
                else "GEOMETRY-CLEARANCE"
            )
            problems.append(
                issue(
                    code,
                    "Physical pair violates solid overlap or local clearance requirements.",
                    op,
                    (a, b),
                    actual={
                        "gap_m": gap,
                        "intersection_mm3": intersection_mm3,
                        "witnesses_world_m": witnesses,
                    },
                    expected={"free_gap_m": required, "local_contact": local_allowed},
                    unit="m;mm3",
                    fix="Repair holes, mating faces, placement or guard geometry in the CAD source; do not exclude this pair.",
                )
            )
        ledger.append(
            {
                **record,
                "status": "passed" if passed else "failed",
                "method": "exact-brep",
                "gap_m": gap,
                "intersection_mm3": intersection_mm3,
                "functional_contact": local_allowed,
                "witnesses_world_m": witnesses,
                "witnesses_valid": all(
                    abs(np.linalg.norm(np.asarray(p) - q) - gap) <= query_error_m
                    for p, q in witnesses
                ),
                "local_contact_proof": "BREP subtraction complement remains clear"
                if local_allowed
                else None,
            }
        )
    return PhysicsReport(
        operation=op,
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            "source_sha256": manifest.source_sha256,
            "pair_count": len(ledger),
            "required_pair_count": len(occurrences) * (len(occurrences) - 1) // 2,
            "coverage_complete": len(ledger)
            == len(occurrences) * (len(occurrences) - 1) // 2,
            "ledger": ledger,
            "scope": "one static pose; all physical leafs including group internals",
            "geometry_source": "closed BREP",
            "mesh_error_m": 0.0,
            "query_error_m": query_error_m,
            "maximum_intersection_sliver_mm3": 1e-6,
            "mount_graph_connected": set(occurrences) <= visited,
        },
    )


def check_occurrence_support(*, package_path: str | Path) -> PhysicsReport:
    """Check the actual CAD joint/fastener graph, including every hardware leaf.

    Hierarchy placement alone is never a mounting relation. This topological
    gate complements, and cannot replace, geometric mounting/clearance checks.
    """
    op = "check_occurrence_support"
    source = Path(package_path).resolve()
    try:
        raw = source.read_bytes()
        package = _read_package(raw, source)
        graph = json.loads(
            package.objects[package.manifest["occurrence_graph"]["path"]]
        )
        adjacent = {n["node_id"]: set() for n in graph["nodes"]}
        for edge in graph["ground_edges"]:
            a, b = edge["parent_node_id"], edge["child_node_id"]
            adjacent[a].add(b)
            adjacent[b].add(a)
        for joint in graph["joints"]:
            a, b = (
                joint["connector_a"]["instance_id"],
                joint["connector_b"]["instance_id"],
            )
            adjacent[a].add(b)
            adjacent[b].add(a)
        visited = set()
        pending = [graph["root_node_id"]]
        while pending:
            n = pending.pop()
            if n not in visited:
                visited.add(n)
                pending.extend(adjacent[n] - visited)
        leaves = {
            n["node_id"]
            for n in graph["nodes"]
            if n["definition_kind"] == "single_solid"
        }
        missing = tuple(sorted(leaves - visited))
        return PhysicsReport(
            operation=op,
            status="failed" if missing else "passed",
            issues=tuple(
                issue(
                    "SUPPORT-MISSING",
                    "CAD leaf has no declared joint/fastener chain to ground.",
                    op,
                    (oid,),
                    fix="Model and connect its actual mounting interface; placement in the assembly is insufficient.",
                )
                for oid in missing
            ),
            evidence={
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "leaf_count": len(leaves),
                "connected_leaf_count": len(leaves & visited),
                "disconnected_occurrences": missing,
                "scope": "CAD mounting topology; physical mating checked separately",
            },
        )
    except Exception as exc:
        from .physics_types import PhysicsError

        if isinstance(exc, PhysicsError):
            raise
        fail("PACKAGE-INVALID", str(exc), operation=op)
