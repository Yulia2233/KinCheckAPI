"""Physical rotor/shaft, BREP inertia only, no overlaid manufacturer inertia."""

from common import cylinder, finish


def build():
    # ---- feature: rotor-shaft (build) ----
    return finish(cylinder(8, 66, (0, -156, 260), (0, 1, 0)))
