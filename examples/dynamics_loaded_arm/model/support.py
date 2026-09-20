"""Footed support with a Ø24.2 bearing bore and flange retention taps."""

import simplecadapi as scad
from common import box, bore, finish


def build(*, side):
    cy = 50 * side
    # ---- feature: upright-stock (build) ----
    body = box(-25, 25, cy - 16, cy + 16, 16, 285, chamfer=True)
    # ---- feature: mounting-foot (add) ----
    body = scad.union_rsolid(body, box(-40, 40, cy - 25, cy + 25, 16, 28, chamfer=True))
    # ---- feature: bearing-bore (subtract) ----
    body = bore(body, 12.1, 34, (0, cy - 17, 260), (0, 1, 0))
    # ---- feature: foot-clearance-holes (subtract) ----
    for x in (-33, 33):
        for dy in (-18, 18):
            body = bore(body, 4.5, 14, (x, cy + dy, 15))
    return finish(body)
