"""Separate physical key; 0.1 mm local side clearance."""

from common import box, finish


def build():
    # ---- feature: driving-key (build) ----
    return finish(box(6.1, 9.9, -12, 12, 257.9, 262.1))
