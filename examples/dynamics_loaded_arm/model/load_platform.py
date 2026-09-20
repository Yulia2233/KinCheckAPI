"""Platform with countersunk attachment holes and 8 mm blind payload taps."""

import simplecadapi as scad
from common import box, bore, finish


def build():
    # ---- feature: platform-stock (build) ----
    body = box(260, 340, -40, 40, 290, 300, chamfer=True)
    # ---- feature: platform-fasteners (subtract) ----
    for x in (282, 294):
        for y in (-10, 10):
            body = bore(body, 3.3, 12, (x, y, 289))
            tool = scad.make_cone_rsolid(
                bottom_radius=3.2,
                top_radius=5.75,
                height=2.55,
                bottom_face_center=(x, y, 297.45),
            )
            body = scad.cut_rsolid(body, tool, skip_non_intersecting=False)
    # ---- feature: payload-blind-taps (subtract) ----
    for x in (275, 325):
        for y in (-20, 20):
            body = bore(body, 3.1, 9, (x, y, 292))
    # ---- feature: ear-blind-taps (subtract) ----
    for x in (290, 310):
        body = bore(body, 3.1, 9, (x, 35, 292))
    return finish(body)
