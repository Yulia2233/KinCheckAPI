"""Geometry construction helpers; all dimensions are millimetres."""

import simplecadapi as scad
from simplecadapi import ql


def box(x0, x1, y0, y1, z0, z1, *, chamfer=False):
    body = scad.make_box_rsolid(
        width=x1 - x0,
        height=y1 - y0,
        depth=z1 - z0,
        bottom_face_center=((x0 + x1) / 2, (y0 + y1) / 2, z0),
    )
    if chamfer:
        # ---- feature: external-edge-break (modify) ----
        edges = ql.edges().exactly(12)
        card = edges.resolve(body)
        print(
            "C0.5 box edges",
            [
                (
                    round(e.get_length(), 3),
                    tuple(
                        round(v, 3)
                        for v in (e.get_center().x, e.get_center().y, e.get_center().z)
                    ),
                )
                for e in card
            ],
        )
        body = scad.chamfer_rsolid(solid=body, edges=edges, distance=0.5)
    return body


def cylinder(radius, length, origin, axis=(0, 0, 1)):
    return scad.make_cylinder_rsolid(
        radius=radius, height=length, bottom_face_center=origin, axis=axis
    )


def bore(body, radius, length, origin, axis=(0, 0, 1)):
    return scad.cut_rsolid(
        body, cylinder(radius, length, origin, axis), skip_non_intersecting=False
    )


def tag_faces(body, name, selector):
    faces = selector.resolve(body)
    if not faces:
        raise ValueError("No faces for " + name)
    return scad.apply_tag_rselection(scope=body, targets=faces, tag=name)


def finish(body):
    # ---- feature: physical-interface-regions (annotate) ----
    planes = ql.faces().where(ql.prop("geom.type", "==", "PLANE"))
    body = tag_faces(body, "interface.contact", ql.faces())
    body = tag_faces(body, "interface.mount", planes)
    body = tag_faces(body, "interface.fastener", planes)
    cylinders = ql.faces().where(ql.prop("geom.type", "==", "CYLINDER"))
    if cylinders.resolve(body):
        body = tag_faces(body, "interface.axis", cylinders)
        body = tag_faces(body, "interface.bearing", cylinders)
    print("part facts", len(ql.faces().resolve(body)), round(body.get_volume(), 6))
    return body
