"""Illustrative calibrated steel payload with four real mounting bores."""

import math
from common import box, bore, finish


def height_for_mass(mass):
    # No chamfer: the exact independent prismatic volume is the frozen formula.
    return mass / (7.85e-6 * (80 * 60 - 4 * math.pi * 3.3**2))


def build(*, mass):
    h = height_for_mass(mass)
    # ---- feature: calibrated-mass-stock (build) ----
    body = box(260, 340, -30, 30, 300, 300 + h, chamfer=True)
    # ---- feature: payload-through-holes (subtract) ----
    for x in (275, 325):
        for y in (-20, 20):
            body = bore(body, 3.3, h + 2, (x, y, 299))
    return finish(body)
