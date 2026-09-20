"""Keyed split hub, connected transition, 4 mm hollow arm and solid end block."""

import simplecadapi as scad
from simplecadapi import ql
from common import box, cylinder, bore, finish


def build():
    # ---- feature: hub-stock (build) ----
    body = cylinder(24, 28, (0, -14, 260), (0, 1, 0))
    # ---- feature: clamping-lugs (add) ----
    body = scad.union_rsolid(body, box(-32, -18, -14, 14, 252, 268))
    # ---- feature: connected-arm-tube (add) ----
    body = scad.union_rsolid(body, box(18, 276, -20, 20, 230, 290), clean=False)
    # ---- feature: hub-tube-root-blend (modify) ----
    seam = (
        ql.edges()
        .incident_to(
            ql.faces().where(ql.origin_role("body")),
            ql.faces().where(ql.origin_role("tool")),
            distinct=True,
        )
        .exactly(4)
    )
    print(
        "root R1 seam",
        [
            (e.get_length(), (e.get_center().x, e.get_center().y, e.get_center().z))
            for e in seam.resolve(body)
        ],
    )
    body = scad.fillet_rsolid(
        solid=body, edges=seam, radius=1.0, generated_faces_tag="interface.root_blend"
    )
    # ---- feature: end-connection-block (add) ----
    body = scad.union_rsolid(body, box(276, 300, -20, 20, 230, 290))
    # ---- feature: hollow-tube (subtract) ----
    body = scad.cut_rsolid(
        body, box(24, 276, -16, 16, 234, 286), skip_non_intersecting=False
    )
    # ---- feature: journal-and-key (subtract) ----
    body = bore(body, 8.1, 30, (0, -15, 260), (0, 1, 0))
    body = scad.cut_rsolid(
        body, box(6, 10, -15, 15, 257.8, 262.2), skip_non_intersecting=False
    )
    # ---- feature: clamp-split (subtract) ----
    body = scad.cut_rsolid(
        body, box(-33, -7.5, -15, 15, 259.7, 260.3), skip_non_intersecting=False
    )
    body = bore(body, 3.3, 22, (-26, 0, 249))
    # ---- feature: clamp-fastener-seats (subtract) ----
    body = bore(body, 5.0, 20, (-26, 0, 268))
    body = scad.cut_rsolid(
        body, box(-31.2, -20.8, -5.2, 5.2, 238, 252), skip_non_intersecting=False
    )
    # ---- feature: platform-blind-taps (subtract) ----
    for x in (282, 294):
        for y in (-10, 10):
            body = bore(body, 3.1, 11, (x, y, 280))
    return finish(body)
