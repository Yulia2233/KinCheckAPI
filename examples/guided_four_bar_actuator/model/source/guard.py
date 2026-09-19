"""Fixed guard rails surrounding the linkage as separate physical parts."""
from __future__ import annotations

import simplecadapi as scad
from dimensions import GUARD_SEAT_OFFSET_Z


def make_guard_part(*, material=None) -> scad.Part:
    # ---- feature: guard-rail (build, profile=geometry) ----
    rail = scad.make_box_rsolid(width=64.0, height=3.0, depth=14.0, bottom_face_center=(18.0, -18.0, -6.0))
    # ---- feature: guard-posts (add, profile=geometry) ----
    posts = [
        scad.make_box_rsolid(width=5.0, height=5.0, depth=20.0, bottom_face_center=(x, -19.0, -8.0))
        for x in (0.0, 36.0)
    ]
    body = scad.union_rsolid(rail, posts)
    # ---- feature: service-clearance (subtract, profile=geometry) ----
    window = scad.make_box_rsolid(width=50.0, height=5.0, depth=10.0, bottom_face_center=(5.0, -19.5, -3.0))
    body = scad.cut_rsolid(body, window)
    # ---- feature: seat-on-base (modify) ----
    body = scad.translate_shape(body, vector=(0.0, 0.0, GUARD_SEAT_OFFSET_Z))
    body = scad.apply_tag(shape=body, tag="role.guided_actuator.guard")
    part = scad.make_part_rpart(part_id="guard", body=body, name="Linkage guard rail")
    if material is not None:
        part = scad.assign_material_rpart(part=part, material=material)
    return scad.add_connector_rpart(
        part=part,
        connector=scad.make_placement_connector_rconnector(
            connector_id="mount",
            placement=scad.make_placement_rplacement(origin=(18.0, -18.0, -6.0)),
        ),
    )
