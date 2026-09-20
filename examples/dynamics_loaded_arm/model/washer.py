"""Thrust/fastener washer, one definition can have repeated occurrences."""

from common import cylinder, bore, finish


def build(*, outer=11, inner=8.1, thickness=2):
    # ---- feature: washer-blank (build) ----
    body = cylinder(outer, thickness, (0, 0, 0))
    # ---- feature: washer-hole (subtract) ----
    body = bore(body, inner, thickness + 2, (0, 0, -1))
    return finish(body)
