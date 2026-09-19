"""Detailed fixed base plate with mounting pattern and pivot bosses."""
from __future__ import annotations

import simplecadapi as scad


def make_base_part(*, material=None) -> scad.Part:
    # ---- feature: base-plate (build, profile=geometry) ----
    body = scad.make_box_rsolid(
        width=76.0, height=42.0, depth=8.0,
        bottom_face_center=(20.0, 0.0, -12.0),
    )
    # ---- feature: mounting-holes (subtract, profile=geometry) ----
    holes = [
        scad.make_cylinder_rsolid(radius=2.25, height=12.0, bottom_face_center=(x, y, -14.0))
        for x in (0.0, 40.0)
        for y in (-15.0, 15.0)
    ]
    body = scad.cut_rsolid(body, holes)
    # ---- feature: pivot-bosses (add, profile=geometry) ----
    bosses = [
        scad.make_cylinder_rsolid(radius=8.0, height=7.0, bottom_face_center=(x, 0.0, -5.0))
        for x in (0.0, 40.0)
    ]
    body = scad.union_rsolid(body, bosses)
    # ---- feature: pivot-bores (subtract, profile=geometry) ----
    bores = [
        scad.make_cylinder_rsolid(radius=2.2, height=16.0, bottom_face_center=(x, 0.0, -13.0))
        for x in (0.0, 40.0)
    ]
    body = scad.cut_rsolid(body, bores)
    body = scad.apply_tag(shape=body, tag="role.guided_actuator.base")
    part = scad.make_part_rpart(part_id="base", body=body, name="Machined base plate")
    if material is not None:
        part = scad.assign_material_rpart(part=part, material=material)
    for connector_id, origin in (("pivot_a", (0.0, 0.0, 0.0)), ("pivot_d", (40.0, 0.0, 0.0))):
        part = scad.add_connector_rpart(
            part=part,
            connector=scad.make_placement_connector_rconnector(
                connector_id=connector_id,
                placement=scad.make_placement_rplacement(origin=origin),
            ),
        )
    part = scad.add_connector_rpart(
        part=part,
        connector=scad.make_placement_connector_rconnector(
            connector_id="guard_mount",
            placement=scad.make_placement_rplacement(origin=(18.0, -18.0, -6.0)),
        ),
    )
    return part
