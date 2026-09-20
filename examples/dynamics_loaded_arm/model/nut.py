"""Captive clamping nut with through tapped bore."""

from common import box, bore, finish


def build():
    # ---- feature: captive-nut-stock (build) ----
    body = box(-5, 5, -5, 5, 0, 6, chamfer=True)
    # ---- feature: tapped-hole (subtract) ----
    return finish(bore(body, 3.1, 8, (0, 0, -1)))
