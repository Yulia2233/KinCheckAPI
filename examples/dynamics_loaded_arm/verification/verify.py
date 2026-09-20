"""Frozen E01 acceptance program; never imports model/build_cadir.py.

The input directory contains product.scadpkg, scene.xml, scene.mapping.json,
interfaces.json (explicit CAD occurrence/region bindings), and meshes/.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


ANGLES_DEG = (0, 30, 60)
FORCE_TOLERANCE_N = 0.01
MOMENT_TOLERANCE_NM = 0.001
FREE_CLEARANCE_M = 0.0001
GUARD_CLEARANCE_M = 0.005


def independent_holding_moment(occurrences, force_point_world_m=None):
    """Scalar sum about -Y through (0,0,0.260), without solver helpers."""
    moment = sum(p.mass_kg * 9.81 * p.com_m[0] for p in occurrences)
    if force_point_world_m is not None:
        moment += 100.0 * force_point_world_m[0]
    return moment


def verify(model_dir: str | Path):
    root = Path(model_dir).resolve()
    # Input errors are checked before importing any optional CAD dependency.
    for member in (
        "product.scadpkg",
        "scene.xml",
        "scene.mapping.json",
        "interfaces.json",
    ):
        if not (root / member).is_file():
            raise ValueError(f"E01 input missing: {root / member}")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from checks import verify_loaded_arm

    return verify_loaded_arm(
        model_dir=root,
        angles_deg=ANGLES_DEG,
        reference_moment=independent_holding_moment,
        force_tolerance_n=FORCE_TOLERANCE_N,
        moment_tolerance_nm=MOMENT_TOLERANCE_NM,
        free_clearance_m=FREE_CLEARANCE_M,
        guard_clearance_m=GUARD_CLEARANCE_M,
        moment_absolute_tolerance_nm=0.02,
        moment_relative_tolerance=0.01,
        rated_torque_nm=20.0,
        short_term_torque_nm=35.0,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0 if result.passed else 1
    except Exception as exc:
        payload = (
            exc.to_dict()
            if hasattr(exc, "to_dict")
            else {
                "operation": "verify_loaded_arm",
                "passed": False,
                "status": "validation_failed",
                "what_happened": str(exc),
                "cause": "Invalid or incomplete E01 input",
                "how_to_fix": "Build and export the complete E01 package before verification.",
            }
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
