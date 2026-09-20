"""Bolted loading ear, transfers a world -Z force at the lateral interface."""

import simplecadapi as scad
from common import box, bore, finish, tag_faces
from simplecadapi import ql


def build():
    # ---- feature: ear-foot (build) ----
    body = box(284, 316, 30.2, 45, 300, 304, chamfer=True)
    # ---- feature: loading-tab (add) ----
    body = scad.union_rsolid(body, box(297, 303, 35, 45, 303, 316))
    # ---- feature: ear-fasteners (subtract) ----
    for x in (290, 310):
        body = bore(body, 3.3, 6, (x, 35, 299))
    # ---- feature: load-pin-hole (subtract) ----
    body = bore(body, 2.1, 8, (296, 40, 310), (1, 0, 0))
    body = finish(body)
    return tag_faces(
        body,
        "interface.load",
        ql.faces()
        .where(
            ql.and_(
                ql.prop("geom.type", "==", "CYLINDER"),
                ql.prop("geom.center.x", ">=", 299.9),
                ql.prop("geom.center.x", "<=", 300.1),
            )
        )
        .exactly(1),
    )
