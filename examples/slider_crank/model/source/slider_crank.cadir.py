"""Detailed slider-crank mechanism generated with SimpleCADAPI/CADIR.

All dimensions are millimetres. The mechanism is intentionally modeled as four
manufactured parts with real bearing/guide interfaces:
- ground: base plate, bored crank pedestal and two guide rails;
- crank: shaft, flywheel and eccentric crank pin;
- connecting rod: capsule profile with two reamed pin bores;
- slider: carriage with an integral pin boss running between the rails.
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import simplecadapi as scad
from simplecadapi import (
    add_component_rassembly, add_connector_rpart,
    add_prismatic_constraint_rassembly, add_revolute_constraint_rassembly,
    capture, cut_rsolid, ground_component_rassembly,
    make_assembly_rassembly, make_box_rsolid, make_cylinder_rsolid,
    make_connector_ref_rconnectorref, make_placement_connector_rconnector,
    make_placement_rplacement, make_part_rpart, part, assemble, union_rsolid,
)
from simplecadapi.exporter import export_product_package_to_mjcf

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT
PACKAGE = ROOT / "slider_crank.scadpkg"

# ---- design parameters ----
BASE_W, BASE_H, BASE_T = 280.0, 120.0, 20.0
PIVOT_X, CENTER_Y = 60.0, 60.0
CRANK_RADIUS, CRANK_ECCENTRICITY = 30.0, 20.0
ROD_LENGTH, ROD_WIDTH, ROD_T = 100.0, 18.0, 10.0
PIN_RADIUS, PIN_BORE_RADIUS = 7.0, 8.0
SLIDER_BODY_W, SLIDER_BODY_H, SLIDER_BODY_T = 40.0, 34.0, 24.0
GUIDE_LENGTH, GUIDE_RAIL_W, GUIDE_RAIL_H = 160.0, 7.0, 12.0

def _normalize_legacy_b1_mjcf(path: Path) -> None:
    """Normalize b1 placement ticks when a compatible exporter is unavailable."""
    tree = ET.parse(path)
    changed = False
    for element in tree.iter():
        raw = element.get("pos")
        if raw is None:
            continue
        values = tuple(float(item) for item in raw.split())
        if len(values) == 3 and any(abs(item) > 1.0e3 for item in values):
            element.set("pos", " ".join(f"{item * 1.0e-9:.12g}" for item in values))
            changed = True
    if changed:
        tree.write(path, encoding="utf-8", xml_declaration=True)

def _part(part_id: str, body, connector_frames):
    value = make_part_rpart(part_id=part_id, body=body, name=part_id)
    for connector_id, frame in connector_frames.items():
        if isinstance(frame, tuple) and len(frame) == 3 and isinstance(frame[0], tuple):
            origin, x_axis, y_axis = frame
        else:
            origin, x_axis, y_axis = frame, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        value = add_connector_rpart(
            part=value,
            connector=make_placement_connector_rconnector(
                connector_id=connector_id,
                placement=make_placement_rplacement(
                    origin=origin, x_axis=x_axis, y_axis=y_axis
                ),
            ),
        )
    return value

@part(id="part.ground", revision="2.0.0", project_root=ROOT)
def ground_part():
    # ---- feature: base-plate (build, profile=geometry) ----
    base = make_box_rsolid(
        width=BASE_W, height=BASE_H, depth=BASE_T,
        bottom_face_center=(BASE_W / 2.0, BASE_H / 2.0, 0.0),
    )
    # ---- feature: crank-pedestal (add) ----
    pedestal = make_cylinder_rsolid(
        radius=36.0, height=11.0,
        bottom_face_center=(PIVOT_X, CENTER_Y, 19.0),
    )
    body = union_rsolid(base, pedestal)
    # ---- feature: guide-rails (add) ----
    rail_x = 100.0 + GUIDE_LENGTH / 2.0
    upper = make_box_rsolid(
        width=GUIDE_LENGTH, height=GUIDE_RAIL_W, depth=GUIDE_RAIL_H,
        bottom_face_center=(rail_x, CENTER_Y - 21.5, 19.0),
    )
    lower = make_box_rsolid(
        width=GUIDE_LENGTH, height=GUIDE_RAIL_W, depth=GUIDE_RAIL_H,
        bottom_face_center=(rail_x, CENTER_Y + 21.5, 19.0),
    )
    body = union_rsolid(body, upper, lower)
    # ---- feature: crank-bore (subtract, profile=geometry) ----
    crank_bore = make_cylinder_rsolid(
        radius=11.0, height=34.0,
        bottom_face_center=(PIVOT_X, CENTER_Y, 0.0),
    )
    body = cut_rsolid(body, crank_bore)
    return _part("part.ground", body, {
        "axis.crank": ((PIVOT_X, CENTER_Y, 20.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        "axis.slider": ((180.0, CENTER_Y, 30.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    })

@part(id="part.crank", revision="2.0.0", project_root=ROOT)
def crank_part():
    # ---- feature: shaft (build, profile=geometry) ----
    shaft = make_cylinder_rsolid(
        radius=9.0, height=26.0, bottom_face_center=(0.0, 0.0, 0.0)
    )
    # ---- feature: flywheel (add, profile=geometry) ----
    flywheel = make_cylinder_rsolid(
        radius=CRANK_RADIUS, height=10.0,
        bottom_face_center=(0.0, 0.0, 12.0),
    )
    body = union_rsolid(shaft, flywheel)
    # ---- feature: eccentric-pin (add, profile=geometry) ----
    pin = make_cylinder_rsolid(
        radius=PIN_RADIUS, height=18.0,
        bottom_face_center=(CRANK_ECCENTRICITY, 0.0, 20.0),
    )
    body = union_rsolid(body, pin)
    return _part("part.crank", body, {
        "axis.crank": (0.0, 0.0, 0.0),
        "pin.crank": (CRANK_ECCENTRICITY, 0.0, 32.0),
    })

@part(id="part.connecting_rod", revision="2.0.0", project_root=ROOT)
def connecting_rod_part():
    # ---- feature: rod-web (build, profile=geometry) ----
    web = make_box_rsolid(
        width=ROD_LENGTH, height=ROD_WIDTH, depth=ROD_T,
        bottom_face_center=(ROD_LENGTH / 2.0, 0.0, 0.0),
    )
    # ---- feature: rod-eyes (add, profile=geometry) ----
    left_eye = make_cylinder_rsolid(
        radius=14.0, height=ROD_T, bottom_face_center=(0.0, 0.0, 0.0)
    )
    right_eye = make_cylinder_rsolid(
        radius=14.0, height=ROD_T,
        bottom_face_center=(ROD_LENGTH, 0.0, 0.0),
    )
    body = union_rsolid(web, left_eye, right_eye)
    # ---- feature: reamed-pin-bores (subtract, profile=geometry) ----
    left_bore = make_cylinder_rsolid(
        radius=PIN_BORE_RADIUS, height=ROD_T + 2.0,
        bottom_face_center=(0.0, 0.0, -1.0),
    )
    right_bore = make_cylinder_rsolid(
        radius=PIN_BORE_RADIUS, height=ROD_T + 2.0,
        bottom_face_center=(ROD_LENGTH, 0.0, -1.0),
    )
    body = cut_rsolid(body, left_bore, right_bore)
    return _part("part.connecting_rod", body, {
        "pin.crank": (0.0, 0.0, ROD_T / 2.0),
        "pin.slider": (ROD_LENGTH, 0.0, ROD_T / 2.0),
    })

@part(id="part.slider", revision="2.0.0", project_root=ROOT)
def slider_part():
    # ---- feature: carriage (build, profile=geometry) ----
    carriage = make_box_rsolid(
        width=SLIDER_BODY_W, height=SLIDER_BODY_H, depth=SLIDER_BODY_T,
        bottom_face_center=(44.0, 0.0, 0.0),
    )
    # ---- feature: pin-boss (add, profile=geometry) ----
    boss = make_cylinder_rsolid(
        radius=12.0, height=5.0,
        bottom_face_center=(0.0, 0.0, 8.0),
    )
    pin_shaft = make_cylinder_rsolid(
        radius=7.0, height=18.0,
        bottom_face_center=(0.0, 0.0, 10.0),
    )
    support = make_box_rsolid(
        width=28.0, height=24.0, depth=5.0,
        bottom_face_center=(14.0, 0.0, 8.0),
    )
    body = union_rsolid(carriage, boss, pin_shaft, support)
    # ---- feature: guide-shoes (add) ----
    shoe_a = make_box_rsolid(
        width=SLIDER_BODY_W - 4.0, height=2.0, depth=4.0,
        bottom_face_center=(44.0, -15.0, -4.0),
    )
    shoe_b = make_box_rsolid(
        width=SLIDER_BODY_W - 4.0, height=2.0, depth=4.0,
        bottom_face_center=(44.0, 15.0, -4.0),
    )
    body = union_rsolid(body, shoe_a, shoe_b)
    return _part("part.slider", body, {
        "pin.slider": (0.0, 0.0, 19.0),
        "guide.slider": ((0.0, 0.0, -3.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    })

GROUND, CRANK, ROD, SLIDER = ground_part(), crank_part(), connecting_rod_part(), slider_part()

@assemble(
    id="slider_crank", revision="2.0.0",
    definitions=(GROUND, CRANK, ROD, SLIDER), project_root=ROOT,
)
def slider_crank_assembly():
    assembly = make_assembly_rassembly(assembly_id="slider_crank")
    for component_id, item, placement in (
        ("ground.base", GROUND.value, make_placement_rplacement(origin=(0.0, 0.0, 0.0))),
        ("crank", CRANK.value, make_placement_rplacement(origin=(PIVOT_X, CENTER_Y, 20.0))),
        ("connecting_rod", ROD.value, make_placement_rplacement(origin=(PIVOT_X + CRANK_ECCENTRICITY, CENTER_Y, 47.0))),
        ("slider", SLIDER.value, make_placement_rplacement(origin=(PIVOT_X + CRANK_ECCENTRICITY + ROD_LENGTH, CENTER_Y, 33.0))),
    ):
        assembly = add_component_rassembly(
            assembly=assembly, item=item, component_id=component_id, placement=placement
        )
    assembly = ground_component_rassembly(assembly=assembly, component_id="ground.base")
    ref = lambda component_id, connector_id: make_connector_ref_rconnectorref(
        component_id=component_id, connector_id=connector_id
    )
    assembly = add_revolute_constraint_rassembly(
        assembly=assembly, constraint_id="joint.crank",
        connector_a=ref("ground.base", "axis.crank"), connector_b=ref("crank", "axis.crank")
    )
    assembly = add_revolute_constraint_rassembly(
        assembly=assembly, constraint_id="joint.rod",
        connector_a=ref("crank", "pin.crank"), connector_b=ref("connecting_rod", "pin.crank")
    )
    assembly = add_revolute_constraint_rassembly(
        assembly=assembly, constraint_id="joint.slider_pin",
        connector_a=ref("connecting_rod", "pin.slider"), connector_b=ref("slider", "pin.slider")
    )
    return add_prismatic_constraint_rassembly(
        assembly=assembly, constraint_id="joint.slider",
        connector_a=ref("ground.base", "axis.slider"), connector_b=ref("slider", "guide.slider")
    )

def build():
    """Build, solve, capture, and export the KinCheck model."""
    result = slider_crank_assembly()
    capture_result = capture(result, PACKAGE, include_scene=True)
    export_report = export_product_package_to_mjcf(
        data=PACKAGE, output_path=MODEL / "scene.xml",
        mesh_directory=MODEL / "meshes", mapping_path=MODEL / "scene.mapping.json",
        default_density_kg_m3=7800.0,
    )
    _normalize_legacy_b1_mjcf(MODEL / "scene.xml")
    return capture_result, export_report

if __name__ == "__main__":
    build()
