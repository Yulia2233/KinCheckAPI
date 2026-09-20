"""Footed motor bracket with shaft pass-through and real bolt holes."""

import simplecadapi as scad
from common import box, bore, finish


def build():
    # ---- feature: vertical-motor-plate (build) ----
    body = box(-27, 27, -107, -103, 16, 287, chamfer=True)
    # ---- feature: motor-foot (add) ----
    body = scad.union_rsolid(body, box(-43, 60, -108, -77, 16, 28, chamfer=True))
    # ---- feature: shaft-opening (subtract) ----
    body = bore(body, 9, 6, (0, -108, 260), (0, 1, 0))
    # ---- feature: base-fasteners (subtract) ----
    for x in (-36, 50):
        for y in (-100, -84):
            body = bore(body, 3.3, 14, (x, y, 15))
    # ---- feature: motor-and-guard-taps (subtract) ----
    for x in (-20, 20):
        for z in (240, 280):
            body = bore(body, 2.1, 6, (x, -108, z), (0, 1, 0))
    # ---- feature: foundation-head-service-pocket (subtract) ----
    body = bore(body, 8.3, 9, (-25, -85, 15))
    return finish(body)
