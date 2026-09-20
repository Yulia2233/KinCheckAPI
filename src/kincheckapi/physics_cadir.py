"""Read-only CADIR bridge. SDK-specific decoding stays behind this boundary."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from .addon import _blob_bytes, _interface_index, _read_package
from .physics_mass import measure_mass_properties, transform_mass_properties
from .physics_types import (
    PhysicsError,
    PhysicsManifest,
    PhysicsMaterial,
    PhysicsOccurrence,
    fail,
)
from .pose import Pose


def _quat(matrix):
    # Stable proper-matrix -> xyzw conversion, including rotations near pi.
    m = np.asarray(matrix)
    candidates = [
        1 + m[0, 0] - m[1, 1] - m[2, 2],
        1 - m[0, 0] + m[1, 1] - m[2, 2],
        1 - m[0, 0] - m[1, 1] + m[2, 2],
        1 + np.trace(m),
    ]
    i = int(np.argmax(candidates))
    q = np.zeros(4)
    q[i] = np.sqrt(max(0, candidates[i])) / 2
    k = 4 * q[i]
    if i == 3:
        q[:3] = [
            (m[2, 1] - m[1, 2]) / k,
            (m[0, 2] - m[2, 0]) / k,
            (m[1, 0] - m[0, 1]) / k,
        ]
    else:
        j, l = (i + 1) % 3, (i + 2) % 3
        q[j] = (m[j, i] + m[i, j]) / k
        q[l] = (m[l, i] + m[i, l]) / k
        q[3] = (m[l, j] - m[j, l]) / k
    return tuple(q)


def measure_package_physics(
    *, package_path: str | Path, sdk_python: str | Path | None = None
) -> PhysicsManifest:
    """Validate .scadpkg, integrate definitions and expand every leaf occurrence.

    sdk_python explicitly opts into an isolated legacy SDK reader. It never tries
    another interpreter after failure; actual SDK and encoding enter provenance.
    Supported tested readers: 2.1.3b3 canonical ticks; 2.0.4b3 legacy millimeters.
    """
    op = "measure_package_physics"
    source = Path(package_path).resolve()
    if sdk_python is not None:
        runner = "import sys;sys.path.insert(0,sys.argv[1]);from kincheckapi.physics_cadir import _worker;_worker(sys.argv[2])"
        env = {
            k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")
        }
        try:
            result = subprocess.run(
                [
                    str(sdk_python),
                    "-c",
                    runner,
                    str(Path(__file__).resolve().parents[1]),
                    str(source),
                ],
                capture_output=True,
                text=True,
                timeout=180,
                env=env,
            )
            payload = json.loads(result.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            fail(
                "BACKEND-UNAVAILABLE",
                str(exc),
                operation=op,
                status="capability_failed",
                objects=(str(sdk_python),),
            )
        if result.returncode:
            raise PhysicsError(
                code=payload["code"],
                message=payload["message"],
                operation=op,
                status=payload["status"],
                object_ids=payload.get("object_ids", ()),
                details=payload.get("details"),
                suggested_actions=payload.get("suggested_actions", ()),
            )
        manifest = PhysicsManifest.from_dict(payload)
        if manifest.source_sha256 != hashlib.sha256(source.read_bytes()).hexdigest():
            fail(
                "PHYSICS-SOURCE-CONFLICT",
                "Source changed during isolated measurement.",
                operation=op,
            )
        return manifest
    try:
        version = importlib.metadata.version("simplecadapi")
        if version not in ("2.0.4b3", "2.1.3b3"):
            fail(
                "SDK-UNSUPPORTED",
                f"Untested CADIR SDK {version}.",
                operation=op,
                status="capability_failed",
            )
        raw = source.read_bytes()
        package = _read_package(raw, source)
        index = _interface_index(package)
        graph = json.loads(
            package.objects[package.manifest["occurrence_graph"]["path"]]
        )
        # The package reader validates identities/hash/frame schema before the
        # SDK's own decoder is allowed to interpret placement components.
        from simplecadapi.exporter.mjcf import _world_placements

        if version == "2.0.4b3":
            for node in graph["nodes"]:
                f = node["transform"]
                r = np.asarray(
                    [f[k] for k in ("x_axis", "y_axis", "z_axis")], dtype=float
                ).T
                if not np.allclose(
                    r.T @ r, np.eye(3), atol=1e-8, rtol=0
                ) or not np.isclose(np.linalg.det(r), 1, atol=1e-8):
                    fail(
                        "FRAME-INCOMPATIBLE",
                        "Legacy placement is not a proper rigid frame.",
                        operation=op,
                        objects=(node["node_id"],),
                    )
        world = _world_placements(graph)
        properties = {}
        for record in package.manifest["definitions"]:
            if record["definition_kind"] != "single_solid":
                continue
            definition = json.loads(package.objects[record["path"]])
            did = record["definition_id"]
            if did in properties:
                fail(
                    "PHYSICS-SOURCE-CONFLICT",
                    "Ambiguous definition ID across revisions.",
                    operation=op,
                    objects=(did,),
                )
            ref = definition.get("material_ref")
            if not ref:
                fail(
                    "DENSITY-MISSING",
                    "CAD definition has no material.",
                    operation=op,
                    objects=(did,),
                )
            mat = json.loads(_blob_bytes(package, ref))
            if mat.get("density") is None:
                fail(
                    "DENSITY-MISSING",
                    "CAD material has no density.",
                    operation=op,
                    objects=(did, str(mat.get("material_id"))),
                )
            material = PhysicsMaterial(
                material_id=mat["material_id"],
                density=mat["density"],
                density_unit=mat.get("density_unit", ""),
                source=f"{source}#{ref['sha256']}",
            )
            p = measure_mass_properties(
                brep=_blob_bytes(package, definition["solid_cache"]["body_ref"]),
                material=material,
                definition_id=did,
            )
            properties[did] = replace(
                p,
                provenance={
                    **p.provenance,
                    "revision": record["revision"],
                    "definition_content_hash": record["content_hash"],
                },
            )
        occurrences = []
        for node in graph["nodes"]:
            if node["definition_kind"] != "single_solid":
                continue
            oid = node["node_id"]
            w = world[oid]
            r = np.asarray([w.x_axis, w.y_axis, w.z_axis]).T
            if not np.allclose(r.T @ r, np.eye(3), atol=1e-8, rtol=0) or not np.isclose(
                np.linalg.det(r), 1, atol=1e-8
            ):
                fail(
                    "FRAME-INCOMPATIBLE",
                    "Decoded placement is not rigid.",
                    operation=op,
                    objects=(oid,),
                )
            pose = Pose(
                position_m=tuple(v * 1e-3 for v in w.origin), orientation_xyzw=_quat(r)
            )
            p = transform_mass_properties(
                properties=properties[node["definition_id"]],
                pose=pose,
                frame_id="world",
            )
            p = replace(p, source_ids=(oid,))
            occurrences.append(
                PhysicsOccurrence(
                    occurrence_id=oid,
                    definition_id=node["definition_id"],
                    revision=node["properties"]["revision"],
                    content_hash=node["properties"]["content_hash"],
                    pose_world=pose,
                    properties=p,
                    interfaces=index[oid]["interfaces"],
                )
            )
        return PhysicsManifest(
            definitions=properties,
            occurrences=tuple(occurrences),
            source_path=str(source),
            source_sha256=hashlib.sha256(raw).hexdigest(),
            producer={
                "root_definition_id": package.manifest["root"]["definition_id"],
                "simplecadapi": version,
                "cadquery-ocp": importlib.metadata.version("cadquery-ocp"),
                "placement_encoding": "legacy-mm"
                if version == "2.0.4b3"
                else "canonical-ticks",
            },
        )
    except PhysicsError:
        raise
    except Exception as exc:
        message = str(exc)
        code = (
            "FRAME-INCOMPATIBLE"
            if any(
                s in message for s in ("frame", "placement", "tick", "unit direction")
            )
            else "PACKAGE-INVALID"
        )
        fail(
            code,
            message,
            operation=op,
            objects=(str(source),),
            fix="Use an explicitly supported SDK matching this package schema, or re-capture the owning CAD source. Do not rescale or skip invalid frames.",
        )


def _worker(path):
    try:
        print(
            json.dumps(
                measure_package_physics(package_path=path).to_dict(), allow_nan=False
            )
        )
    except PhysicsError as exc:
        print(json.dumps(exc.to_dict(), allow_nan=False))
        raise SystemExit(1)


def read_mjcf_mass_properties(
    *, xml_path: str | Path, mapping_path: str | Path, ground_properties=None
):
    """Compatibility import of explicit MJCF inertials, labeled mjcf_explicit.

    Density-only meshes, shell assumptions and unspecified triangulation error
    have no strict acceptance path in v0.6.0. World mass must be supplied
    explicitly because MuJoCo worldbody does not retain physical ground mass.
    """
    import xml.etree.ElementTree as ET
    from .physics_types import RigidBodyProperties
    from .physics_mass import rotation

    op = "read_mjcf_mass_properties"
    try:
        xml = Path(xml_path).resolve()
        mapping = json.loads(Path(mapping_path).read_text())
        root = ET.parse(xml).getroot()
        if root.get("model") != mapping["root_definition_id"]:
            fail(
                "PHYSICS-SOURCE-CONFLICT",
                "MJCF and mapping root identities differ.",
                operation=op,
            )
        bodies = {b.get("name"): b for b in root.iter("body")}
        missing = [
            g["group_id"]
            for g in mapping["groups"]
            if g["body_name"] is not None
            and (
                g["body_name"] not in bodies
                or bodies[g["body_name"]].find("inertial") is None
            )
        ]
        if missing:
            fail(
                "MESH-INERTIA-UNVERIFIED",
                "MJCF groups have no explicit inertial. Default density/mesh inference is not mass truth.",
                operation=op,
                status="capability_failed",
                objects=tuple(missing),
                fix="Supply BREP/material properties or explicit measured inertials; density-only meshes need a separately validated integration/error contract.",
            )
        ground = mapping["grounded_group_id"]
        if ground_properties is None or ground_properties.frame_id != ground:
            fail(
                "OCCURRENCE-COVERAGE-INCOMPLETE",
                "Explicit ground properties in the world group frame are required.",
                operation=op,
                objects=(ground,),
            )
        import mujoco

        compiled = mujoco.MjModel.from_xml_path(str(xml))
        props = {ground: ground_properties}
        for g in mapping["groups"]:
            if g["body_name"] is None:
                continue
            bid = mujoco.mj_name2id(compiled, mujoco.mjtObj.mjOBJ_BODY, g["body_name"])
            w, x, y, z = compiled.body_iquat[bid]
            r = rotation(Pose(orientation_xyzw=(x, y, z, w)))
            props[g["group_id"]] = RigidBodyProperties(
                mass_kg=float(compiled.body_mass[bid]),
                com_m=tuple(compiled.body_ipos[bid]),
                inertia_com_kg_m2=r @ np.diag(compiled.body_inertia[bid]) @ r.T,
                frame_id=g["group_id"],
                source_kind="mjcf_explicit",
                source_ids=tuple(g["members"]),
                provenance={
                    "xml_sha256": hashlib.sha256(xml.read_bytes()).hexdigest(),
                    "mapping_sha256": hashlib.sha256(
                        Path(mapping_path).read_bytes()
                    ).hexdigest(),
                    "backend_version": mujoco.__version__,
                    "source_quality": "explicit MJCF, not BREP truth",
                },
            )
        return props
    except PhysicsError:
        raise
    except Exception as exc:
        fail("PACKAGE-INVALID", str(exc), operation=op)


def measure_interface_centers(
    *, package_path: str | Path, occurrence_id: str, interface_name: str
):
    """Resolve named CAD faces and return their measured definition-frame centres.

    Used for load attachment evidence, never to infer a missing interface by name
    or appearance. Coordinates are SI and topology IDs remain in the response.
    """
    from simplecadapi.artifacts.brep import read_brep_solid
    from simplecadapi.artifacts.topology_snapshot import restore_topology_snapshot
    from simplecadapi import ql

    op = "measure_interface_centers"
    source = Path(package_path).resolve()
    package = _read_package(source.read_bytes(), source)
    index = _interface_index(package)
    if occurrence_id not in index or not index[occurrence_id]["interfaces"].get(
        interface_name
    ):
        fail(
            "CONTACT-INTERFACE-MISSING",
            "Exact occurrence/interface is missing.",
            operation=op,
            objects=(occurrence_id, interface_name),
        )
    did = index[occurrence_id]["definition_id"]
    record = next(
        r for r in package.manifest["definitions"] if r["definition_id"] == did
    )
    definition = json.loads(package.objects[record["path"]])
    solid = read_brep_solid(_blob_bytes(package, definition["solid_cache"]["body_ref"]))
    restored = restore_topology_snapshot(
        solid, _blob_bytes(package, definition["topology_snapshot_ref"])
    )
    faces = ql.faces().where(ql.tag(interface_name)).resolve(restored)
    if not faces:
        fail(
            "CONTACT-INTERFACE-MISSING",
            "Interface has no resolved face.",
            operation=op,
            objects=(occurrence_id, interface_name),
        )
    return {
        "occurrence_id": occurrence_id,
        "interface_name": interface_name,
        "frame_id": did,
        "centers_m": tuple(
            (
                f.get_center().x * 0.001,
                f.get_center().y * 0.001,
                f.get_center().z * 0.001,
            )
            for f in faces
        ),
        "entities": index[occurrence_id]["interfaces"][interface_name],
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
