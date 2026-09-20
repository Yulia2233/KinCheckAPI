"""Coupler sleeve bridging separate rotor and main shaft, with clamp taps."""

from common import cylinder, bore, finish


def build():
    # ---- feature: coupling-stock (build) ----
    body = cylinder(14, 20, (0, -98, 260), (0, 1, 0))
    # ---- feature: through-bore (subtract) ----
    body = bore(body, 8.1, 22, (0, -99, 260), (0, 1, 0))
    # ---- feature: clamp-taps (subtract) ----
    for y in (-94, -81):
        body = bore(body, 2.1, 8, (7, y, 260), (1, 0, 0))
    return finish(body)
