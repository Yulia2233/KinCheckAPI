"""Custom flanged sliding bushing; Ø24/Ø16.2 barrel 32, flange 3."""

import simplecadapi as scad
from common import cylinder, bore, finish


def build():
    # ---- feature: bearing-barrel (build) ----
    body = cylinder(12, 32, (0, 0, 0), (0, 1, 0))
    # ---- feature: axial-retaining-flange (add) ----
    body = scad.union_rsolid(body, cylinder(15, 3, (0, 32, 0), (0, 1, 0)))
    # ---- feature: journal-bore (subtract) ----
    body = bore(body, 8.1, 37, (0, -1, 0), (0, 1, 0))
    return finish(body)
