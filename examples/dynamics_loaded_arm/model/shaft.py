"""Ø16 shaft with integral axial shoulder and real driving keyway."""

import simplecadapi as scad
from common import cylinder, box, finish


def build():
    # ---- feature: shaft-stock (build) ----
    body = cylinder(8, 170, (0, -85, 260), (0, 1, 0))
    # ---- feature: thrust-shoulder (add) ----
    body = scad.union_rsolid(body, cylinder(10, 2, (0, -73, 260), (0, 1, 0)))
    # ---- feature: hub-keyway (subtract) ----
    body = scad.cut_rsolid(
        body, box(6, 10, -12.2, 12.2, 257.8, 262.2), skip_non_intersecting=False
    )
    return finish(body)
