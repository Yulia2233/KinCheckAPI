"""CADIR E01 source; run with the explicit 2.1.3b3 SDK environment.

All assembly relations reference leaf connectors; no exported geometry is patched.
"""

from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path

import simplecadapi as scad
from simplecadapi import ql
from common import finish
from payload import height_for_mass

HERE = Path(__file__).resolve().parent
IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
PLUS_Y = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
MINUS_Y = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
PLUS_X = ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
# Interface records contain immutable geometry requirements for this design;
# the verifier independently queries the captured BREP rather than this source.


def placement(origin=(0, 0, 0), axes=IDENTITY):
    return scad.make_placement_rplacement(origin=origin, x_axis=axes[0], y_axis=axes[1])


def build(variant="rated", fault=None):
    mass = {"empty": 0.0, "rated": 2.0, "overload": 3.0}[variant]
    specs = {}
    connections = []
    regions = []

    def add(name, module, *, args=None, origin=(0, 0, 0), axes=IDENTITY):
        specs[name] = {
            "module": module,
            "args": args or {},
            "origin": origin,
            "axes": axes,
            "connectors": {},
        }

    def frame_local(name, world, axes):
        p = placement(specs[name]["origin"], specs[name]["axes"])
        # SDK relative placement preserves the rigid frame convention.
        from simplecadapi.product.placement import relative_placement

        return relative_placement(p, placement(world, axes))

    def connect(parent, child, point, *, axis=IDENTITY, kind="fixed"):
        conn = "to_" + child
        specs[parent]["connectors"][conn] = frame_local(parent, point, axis)
        specs[child]["connectors"]["mount"] = frame_local(child, point, axis)
        connections.append((parent, child, conn, kind))

    def region(
        a,
        b,
        lo,
        hi,
        *,
        maximum=0.00021,
        minimum=0,
        purpose="local mating faces",
        required_connection=True,
    ):
        # All region boxes are defined in world at the authored pose; convert
        # to the explicitly named occurrence's local coordinate system.
        p = placement(specs[a]["origin"], specs[a]["axes"])
        from simplecadapi.product.placement import inverse_placement

        inv = inverse_placement(p)
        corners = [
            inv.transform_point((x, y, z))
            for x in (lo[0], hi[0])
            for y in (lo[1], hi[1])
            for z in (lo[2], hi[2])
        ]
        lower = [(min(p[i] for p in corners) - 0.2) * 0.001 for i in range(3)]
        upper = [(max(p[i] for p in corners) + 0.2) * 0.001 for i in range(3)]
        regions.append(
            {
                "occurrence_a": "node/dynamics_loaded_arm/" + a,
                "occurrence_b": "node/dynamics_loaded_arm/" + b,
                "interface_a": "interface.contact",
                "interface_b": "interface.contact",
                "lower_m": lower,
                "upper_m": upper,
                "minimum_gap_m": minimum,
                "maximum_gap_m": maximum,
                "purpose": purpose,
                "required_connection": required_connection,
            }
        )

    add("base", "base")
    for side, name in ((1, "left"), (-1, "right")):
        add("support_" + name, "support", args={"side": side})
        connect("base", "support_" + name, (0, 50 * side, 16))
        region(
            "base",
            "support_" + name,
            (-40, 50 * side - 25, 15.99),
            (40, 50 * side + 25, 16.01),
        )
        add(
            "bushing_" + name,
            "bushing",
            origin=(0, 34 * side, 260),
            axes=IDENTITY if side == 1 else ((-1, 0, 0), (0, -1, 0)),
        )
        connect("support_" + name, "bushing_" + name, (0, 66 * side, 260), axis=PLUS_Y)
        region(
            "support_" + name,
            "bushing_" + name,
            (-15.1, min(34 * side, 69 * side) - 0.1, 244.9),
            (15.1, max(34 * side, 69 * side) + 0.1, 275.1),
            purpose="bore plus flange; ideal bonded bushing",
        )
    for name in (
        "shaft",
        "arm",
        "platform",
        "key",
        "lock_ring",
        "motor_mount",
        "motor_stator",
        "motor_rotor",
        "coupling",
        "guard",
        "load_ear",
    ):
        add(name, "load_platform" if name == "platform" else name)
    connect("support_left", "arm", (0, 0, 260), axis=MINUS_Y, kind="revolute")
    connect("arm", "shaft", (0, 0, 260), axis=MINUS_Y)
    connect("shaft", "key", (8, 0, 260))
    connect("shaft", "lock_ring", (0, 71, 260), axis=PLUS_Y)
    connect("arm", "platform", (288, 0, 290))
    connect("platform", "load_ear", (300, 35, 300))
    connect("base", "motor_mount", (10, -90, 16))
    connect("motor_mount", "motor_stator", (0, -107, 260), axis=PLUS_Y)
    connect("shaft", "coupling", (0, -81, 260), axis=PLUS_Y)
    connect("coupling", "motor_rotor", (0, -94, 260), axis=PLUS_Y)
    connect("motor_mount", "guard", (20, -103, 280), axis=PLUS_Y)
    region(
        "arm",
        "shaft",
        (-8.2, -14.1, 251.8),
        (8.2, 14.1, 268.2),
        purpose="keyed ideal hub bore",
    )
    region(
        "arm", "key", (5.9, -12.3, 257.7), (10.1, 12.3, 262.3), purpose="keyway flanks"
    )
    region(
        "shaft", "key", (5.9, -12.3, 257.7), (10.1, 12.3, 262.3), purpose="shaft keyway"
    )
    region("arm", "platform", (259.9, -20.1, 289.99), (300.1, 20.1, 290.01))
    region("platform", "load_ear", (283.9, 30.1, 299.99), (316.1, 40.1, 300.01))
    region("base", "motor_mount", (-40.1, -108.1, 15.99), (60.1, -76.9, 16.01))
    region(
        "motor_mount", "motor_stator", (-26.1, -107.01, 233.9), (26.1, -106.99, 286.1)
    )
    region("motor_mount", "guard", (-28.1, -103.01, 231.9), (28.1, -102.99, 288.1))
    region("shaft", "coupling", (-8.2, -85.1, 251.8), (8.2, -77.9, 268.2))
    region("coupling", "motor_rotor", (-8.2, -98.1, 251.8), (8.2, -89.9, 268.2))
    region("shaft", "lock_ring", (-8.2, 70.9, 251.8), (8.2, 76.1, 268.2))
    for side, name in ((1, "right"), (-1, "left")):
        origin = (0, 69 if side == 1 else -71, 260)
        add("thrust_" + name, "washer", origin=origin, axes=PLUS_Y)
        connect("shaft", "thrust_" + name, origin, axis=PLUS_Y)
        by = "bushing_left" if side == 1 else "bushing_right"
        region(
            by,
            "shaft",
            (-8.2, min(34 * side, 69 * side) - 0.1, 251.8),
            (8.2, max(34 * side, 69 * side) + 0.1, 268.2),
            purpose="journal clearance fit",
        )
        region(
            by,
            "thrust_" + name,
            (-11.1, 69 * side - 0.01, 248.9),
            (11.1, 69 * side + 0.01, 271.1),
            purpose="axial bushing/thrust face",
        )
        region(
            "shaft",
            "thrust_" + name,
            (-11.1, origin[1] - 0.01, 248.9),
            (11.1, origin[1] + 2.01, 271.1),
        )
    region("lock_ring", "thrust_right", (-11.1, 70.99, 248.9), (11.1, 71.01, 271.1))
    for index, y in enumerate((-153, -115)):
        name = f"motor_bearing_{index}"
        add(
            name,
            "washer",
            args={"outer": 10, "inner": 8.1, "thickness": 5},
            origin=(0, y, 260),
            axes=PLUS_Y,
        )
        connect("motor_stator", name, (0, y, 260), axis=PLUS_Y)
        region(
            "motor_stator",
            name,
            (-10.1, y - 0.1, 249.9),
            (10.1, y + 5.1, 270.1),
            purpose="motor bearing outer seat",
        )
        region(
            name,
            "motor_rotor",
            (-8.2, y - 0.1, 251.8),
            (8.2, y + 5.1, 268.2),
            purpose="motor journal clearance",
        )
    if mass:
        add("payload", "payload", args={"mass": mass})
        connect("platform", "payload", (300, 0, 300))
        region("platform", "payload", (259.9, -30.1, 299.99), (340.1, 30.1, 300.01))

    # Fastener envelopes, placements and local contact regions are explicit.
    def screw(
        name,
        host,
        point,
        d,
        length,
        *,
        axes=IDENTITY,
        countersunk=False,
        other_hosts=(),
    ):
        add(
            name,
            "fastener",
            args={"diameter": d, "length": length, "countersunk": countersunk},
            origin=point,
            axes=axes,
        )
        connect(host, name, point, axis=axes)
        p = placement(point, axes)
        r = d if countersunk else d * 0.81
        pts = [
            p.transform_point((x, y, z))
            for x in (-r, r)
            for y in (-r, r)
            for z in (-length - 0.1, d * 0.6 + 0.1)
        ]
        lo = tuple(min(p[i] for p in pts) for i in range(3))
        hi = tuple(max(p[i] for p in pts) for i in range(3))
        for h in (host, *other_hosts):
            region(
                h,
                name,
                lo,
                hi,
                maximum=0.0005,
                purpose="fastener bore/head; declared tapped engagement",
                required_connection=h == host,
            )

    def washer(name, host, point, d):
        add(
            name,
            "washer",
            args={"outer": d, "inner": d / 2 + 0.5, "thickness": 2},
            origin=point,
        )
        connect(host, name, point)
        region(
            host,
            name,
            (point[0] - d - 0.1, point[1] - d - 0.1, point[2] - 0.01),
            (point[0] + d + 0.1, point[1] + d + 0.1, point[2] + 0.01),
        )

    for x in (-25, 300):
        for y in (-85, 85):
            name = f"foundation_{x}_{y}".replace("-", "n")
            w = name + "_washer"
            washer(w, "base", (x, y, 16), 8)
            screw(name, w, (x, y, 18), 8, 30, other_hosts=("base",))
    for side, name in ((1, "left"), (-1, "right")):
        for x in (-33, 33):
            for dy in (-18, 18):
                y = 50 * side + dy
                n = f"foot_{name}_{x}_{dy}".replace("-", "n")
                w = n + "_washer"
                washer(w, "support_" + name, (x, y, 28), 8)
                screw(n, w, (x, y, 30), 8, 24, other_hosts=("support_" + name, "base"))
    for x in (-36, 50):
        for y in (-100, -84):
            n = f"motor_foot_{x}_{y}".replace("-", "n")
            w = n + "_washer"
            washer(w, "motor_mount", (x, y, 28), 6)
            screw(n, w, (x, y, 30), 6, 24, other_hosts=("motor_mount", "base"))
    for x in (282, 294):
        for y in (-10, 10):
            screw(
                f"platform_screw_{x}_{y}".replace("-", "n"),
                "platform",
                (x, y, 300),
                6,
                18,
                countersunk=True,
                other_hosts=("arm", "payload") if mass else ("arm",),
            )
    for x in (290, 310):
        screw(
            f"ear_screw_{x}", "load_ear", (x, 35, 304), 6, 10, other_hosts=("platform",)
        )
    if mass:
        h = height_for_mass(mass)
        for x in (275, 325):
            for y in (-20, 20):
                n = f"payload_screw_{x}_{y}".replace("-", "n")
                w = n + "_washer"
                washer(w, "payload", (x, y, 300 + h), 6)
                screw(
                    n, w, (x, y, 302 + h), 6, h + 9, other_hosts=("payload", "platform")
                )
    screw("hub_clamp", "arm", (-26, 0, 268), 6, 22)
    add("hub_nut", "nut", origin=(-26, 0, 246))
    connect("arm", "hub_nut", (-26, 0, 252))
    region("arm", "hub_nut", (-31.1, -5.1, 251.99), (-20.9, 5.1, 252.01))
    region(
        "hub_nut",
        "hub_clamp",
        (-29.2, -3.2, 245.9),
        (-22.8, 3.2, 252.1),
        maximum=0.0003,
    )
    for x in (-20, 20):
        for z in (240, 280):
            screw(
                f"motor_guard_{x}_{z}".replace("-", "n"),
                "guard",
                (x, -100, z),
                4,
                12,
                axes=PLUS_Y,
                other_hosts=("motor_mount", "motor_stator"),
            )
    for y in (-94, -81):
        screw(
            f"coupling_screw_{y}".replace("-", "n"),
            "coupling",
            (14, y, 260),
            4,
            6,
            axes=PLUS_X,
            other_hosts=("motor_rotor" if y == -94 else "shaft",),
        )
    screw(
        "ring_screw",
        "lock_ring",
        (13, 73.5, 260),
        4,
        5,
        axes=PLUS_X,
        other_hosts=("shaft",),
    )
    if fault == "isolated_ring":
        connections = [c for c in connections if c[:2] != ("shaft", "lock_ring")]
    definitions = []
    part_by_occ = {}
    built = {}
    for name, spec in specs.items():
        # Share fastener/washer definitions only when their local interfaces
        # agree. Host parts remain distinct to retain all attachment datums.
        key = json.dumps(
            {
                "module": spec["module"],
                "args": spec["args"],
                "connectors": {k: v.to_dict() for k, v in spec["connectors"].items()},
            },
            sort_keys=True,
        )
        if key not in built:
            factory = importlib.import_module(spec["module"]).build
            args = spec["args"]
            connectors = spec["connectors"]
            did = name

            def builder():
                body = factory(**args)
                material = scad.make_material_rmaterial(
                    material_id="aluminum" if did == "guard" else "steel",
                    density=2.7e-6 if did == "guard" else 7.85e-6,
                    density_unit="kg/mm^3",
                    color=(0.4, 0.6, 0.75) if did == "guard" else (0.6, 0.62, 0.65),
                )
                part = scad.assign_material_rpart(
                    part=scad.make_part_rpart(part_id=did, body=body), material=material
                )
                for cid, pose in connectors.items():
                    part = scad.add_connector_rpart(
                        part=part,
                        connector=scad.make_placement_connector_rconnector(
                            connector_id=cid, placement=pose
                        ),
                    )
                return part

            decorated = scad.part(
                id=did, revision="0.6.0", cache="off", project_root=HERE
            )(builder)
            built[key] = decorated()
            definitions.append(built[key])
        part_by_occ[name] = built[key]

    @scad.assemble(
        id="dynamics_loaded_arm",
        revision="0.6.0",
        definitions=tuple(definitions),
        cache="off",
        project_root=HERE,
    )
    def assemble():
        assembly = scad.make_assembly_rassembly(
            assembly_id="dynamics_loaded_arm", name="E01 loaded swing arm — " + variant
        )
        for name, spec in specs.items():
            assembly = scad.add_component_rassembly(
                assembly=assembly,
                item=part_by_occ[name].part,
                component_id=name,
                placement=placement(spec["origin"], spec["axes"]),
            )
        assembly = scad.ground_component_rassembly(
            assembly=assembly, component_id="base"
        )
        for parent, child, conn, kind in connections:
            kwargs = {
                "assembly": assembly,
                "constraint_id": parent + "_to_" + child,
                "connector_a": scad.make_connector_ref_rconnectorref(
                    component_id=parent, connector_id=conn
                ),
                "connector_b": scad.make_connector_ref_rconnectorref(
                    component_id=child, connector_id="mount"
                ),
            }
            assembly = (
                scad.add_revolute_constraint_rassembly(
                    **kwargs,
                    angle_limit=scad.make_scalar_limit_rscalarlimit(
                        lower_value=-20, upper_value=60
                    ),
                )
                if kind == "revolute"
                else scad.add_fixed_constraint_rassembly(**kwargs)
            )
        return scad.solve_assembly_constraints_rassembly(assembly=assembly, strict=True)

    result = assemble()
    target = (
        (HERE / "faults" / fault)
        if fault
        else (HERE if variant == "rated" else HERE / "variants" / variant)
    )
    target.mkdir(parents=True, exist_ok=True)
    package = target / "product.scadpkg"
    scad.capture(result, package, include_scene=False)
    if fault:
        print("CAPTURED NEGATIVE CAD VARIANT", fault, package)
        return target
    from simplecadapi.exporter.mjcf import export_product_package_to_mjcf

    export_product_package_to_mjcf(
        data=package,
        output_path=target / "scene.xml",
        mapping_path=target / "scene.mapping.json",
        mesh_directory=target / "meshes",
        linear_deflection=0.02,
        angular_deflection_degrees=8,
    )
    mapping = json.loads((target / "scene.mapping.json").read_text())
    ground = mapping["grounded_group_id"]
    support = [
        {
            "support_id": f"foundation_{i}",
            "component_id": ground,
            "occurrence_id": "node/dynamics_loaded_arm/base",
            "interface_name": "interface.mount",
            "point_m": [x * 0.001, y * 0.001, 0.0],
            "normal": [0.0, 0.0, 1.0],
            "kind": "fixed",
        }
        for i, (x, y) in enumerate([(x, y) for x in (-25, 300) for y in (-85, 85)])
    ]
    (target / "interfaces.json").write_text(
        json.dumps(
            {
                "variant": variant,
                "supports": support,
                "contacts": regions,
                "bom": sorted(specs),
                "environment": "ideal fixed plane Z=0; four foundation bolt holes",
                "fastener_thread_model": "nominal screw envelopes plus declared blind tap depth; no screw drive",
            },
            indent=2,
        )
    )
    print("E01 CAPTURED", len(specs), len(definitions), package)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant", choices=("empty", "rated", "overload"), default="rated"
    )
    parser.add_argument("--fault", choices=("isolated_ring",))
    args = parser.parse_args()
    build(args.variant, args.fault)
