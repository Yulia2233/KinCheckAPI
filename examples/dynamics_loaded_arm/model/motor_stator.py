"""Illustrative motor housing, separate rotor cavity and mounting flange."""

from common import box, bore, finish


def build():
    # ---- feature: motor-housing (build) ----
    body = box(-26, 26, -157, -107, 234, 286, chamfer=True)
    # ---- feature: rotor-cavity (subtract) ----
    body = bore(body, 10, 52, (0, -158, 260), (0, 1, 0))
    # ---- feature: flange-blind-taps (subtract) ----
    for x in (-20, 20):
        for z in (240, 280):
            body = bore(body, 2.1, 9, (x, -115, z), (0, 1, 0))
    return finish(body)
