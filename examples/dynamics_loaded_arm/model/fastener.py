"""Captive screw with actual shank, head, socket and declared engagement.

Standard fastening threads use a nominal envelope and explicit tapped depth;
this is not a screw-drive geometry or a thread contact-strength calculation.
"""

import simplecadapi as scad
from common import cylinder, bore, finish


def build(*, diameter, length, countersunk=False):
    r = diameter / 2
    # ---- feature: screw-shank (build) ----
    body = cylinder(r - 0.1, length, (0, 0, -length))
    # ---- feature: screw-head (add) ----
    if countersunk:
        head = scad.make_cone_rsolid(
            bottom_radius=r - 0.1,
            top_radius=diameter - 0.25,
            height=2.85,
            bottom_face_center=(0, 0, -2.85),
        )
    else:
        head = cylinder(diameter * 0.8, diameter * 0.6, (0, 0, 0))
    body = scad.union_rsolid(body, head)
    # ---- feature: tool-socket (subtract) ----
    top = 0 if countersunk else diameter * 0.6
    body = bore(body, r * 0.45, 2.1, (0, 0, top - 2))
    return finish(body)
