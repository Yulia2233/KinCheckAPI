"""Split shaft collar with an explicit retaining screw hole."""

import simplecadapi as scad
from common import box, cylinder, bore, finish


def build():
    # ---- feature: collar-blank (build) ----
    body = cylinder(13, 5, (0, 71, 260), (0, 1, 0))
    # ---- feature: collar-bore (subtract) ----
    body = bore(body, 8.1, 7, (0, 70, 260), (0, 1, 0))
    # ---- feature: radial-retaining-tap (subtract) ----
    body = bore(body, 2.1, 7, (7, 73.5, 260), (1, 0, 0))
    return finish(body)
