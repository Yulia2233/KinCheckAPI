"""U guard and mounting feet outside the rotating coupling envelope."""

import simplecadapi as scad
from common import box, bore, finish


def build():
    # ---- feature: guard-roof (build) ----
    body = box(-28, 28, -103, -76, 285, 288, chamfer=True)
    # ---- feature: guard-sides (add) ----
    body = scad.union_rsolid(
        body, box(-28, -25, -103, -76, 232, 287), box(25, 28, -103, -76, 232, 287)
    )
    # ---- feature: guard-mounting-tabs (add) ----
    for side in (-1, 1):
        for z in (240, 280):
            body = scad.union_rsolid(
                body,
                box(
                    17 if side == 1 else -28,
                    28 if side == 1 else -17,
                    -103,
                    -100,
                    z - 4,
                    z + 4,
                ),
            )
    # ---- feature: guard-fastener-holes (subtract) ----
    for x in (-20, 20):
        for z in (240, 280):
            body = bore(body, 2.3, 5, (x, -104, z), (0, 1, 0))
    return finish(body)
