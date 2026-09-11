"""Reproduce the pre-optimization four-bar interference failure.

This intentionally uses the archived CADIR baseline geometry: all links share
the same axial layer, the old bolt layout is retained, and no collision
exclusions are applied.  It is a failure demonstration, not a replacement for
the optimized case.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
KINCHECKAPI_SRC = Path(
    os.environ.get("KINCHECKAPI_SRC", str(CASE_DIR.parents[1] / "src"))
)
sys.path.insert(0, str(KINCHECKAPI_SRC))
sys.path.insert(0, str(CASE_DIR / "verification"))

from kincheckapi.cadir import convert_mjcf  # noqa: E402
from kincheckapi.clearance import check_interference  # noqa: E402
from kincheckapi import export  # noqa: E402
from simulate_and_record import (  # noqa: E402
    _closed_form_motion,
    _clearance_summary,
)


OUT_DIR = CASE_DIR / "output" / "before"
MJCF_DIR = CASE_DIR / "model_before"
XML_PATH = MJCF_DIR / "four_bar_linkage.xml"
MAPPING_PATH = MJCF_DIR / "four_bar_linkage.mapping.json"
PACKAGE_PATH = OUT_DIR / "four_bar_linkage_before_optimization.kincheck"
EVIDENCE_PATH = OUT_DIR / "four_bar_linkage.before_optimization.json"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    converted = convert_mjcf(
        xml_path=XML_PATH,
        mapping_path=MAPPING_PATH,
        asset_root=MJCF_DIR,
    )
    motion = _closed_form_motion(converted.assembly.assembly_id)
    package = export.motion_package(
        assembly=converted.assembly,
        motion_result=motion,
        output_path=PACKAGE_PATH,
        asset_root=MJCF_DIR,
        title="CADIR four-bar linkage before optimization (expected failure)",
        require_meshes=True,
        metadata={
            "case": "before_optimization",
            "failure_reason": "same axial geometry layer and no collision exclusions",
            "source_snapshot": "CADIR baseline commit 34ea0f7",
        },
    )
    roundtrip_motion = export.read_package(path=PACKAGE_PATH).motion_result
    report = check_interference(
        assembly=converted.assembly,
        motion_result=roundtrip_motion,
        asset_root=MJCF_DIR,
    )
    evidence = {
        "source": {
            "model": str(XML_PATH),
            "mapping": str(MAPPING_PATH),
            "kincheck": str(PACKAGE_PATH),
            "package_bytes": package.path.stat().st_size,
            "package_sha256": package.sha256,
        },
        "motion": {
            "status": motion.status,
            "sample_count": len(motion.sample_times_s),
            "max_closure_position_residual_m": max(
                (item.position_residual_m for item in motion.closure_residuals),
                default=0.0,
            ),
        },
        "clearance": _clearance_summary(report),
        "expected_failure": True,
    }
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
