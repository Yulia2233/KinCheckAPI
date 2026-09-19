"""Export the verified actuator motion as a standalone .kincheck package."""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from kincheckapi import export
from kincheckapi.result import record_verification_reports

CASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = CASE_DIR / "model"
DEFAULT_OUTPUT = CASE_DIR / "output" / "guided_four_bar_actuator.kincheck"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    import verify

    _assembly, motion, result = verify.evaluate(args.model_dir)
    if not result["passed"]:
        print(json.dumps({"passed": False, "reason": "verification failed"}, sort_keys=True))
        return 1
    evidence = {key: value for key, value in result.items() if key != "motion"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    (args.output.parent / "collision_verification.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    summary = {
        "passed": result["passed"], "motion_status": motion.status,
        "sample_count": len(motion.sample_times_s),
        "physical_component_count": result["collision_scope"]["physical_component_count"],
        "physical_pair_count": result["collision_scope"]["physical_pair_count"],
        "continuous_group_pair_count": len(verify.COMPONENT_PAIRS),
        "detector_negative_control_passed": result["detector_negative_control"]["passed"],
        "checks": [{"check_id": item.get("check_id", item.get("operation")), "passed": item["passed"]} for item in result["checks"]],
        "assembly_integrity_passed": result["assembly_integrity"]["passed"],
    }
    (args.output.parent / "verification.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    motion = record_verification_reports(
        motion_result=motion, reports=(*result["checks"], result["assembly_integrity"]),
    )
    motion = replace(motion, metadata={
        **dict(motion.metadata), "collision_scope": result["collision_scope"],
        "detector_negative_control": result["detector_negative_control"],
    })
    artifact = export.motion_package(
        assembly=_assembly,
        motion_result=motion,
        output_path=args.output,
        asset_root=args.model_dir,
        title="KinCheckAPI guided four-bar actuator simulation",
        require_meshes=True,
        metadata={"source": "examples/guided_four_bar_actuator/verification/verify.py"},
    )
    payload = {
        "passed": True,
        "package": str(artifact.path),
        "bytes": artifact.bytes,
        "sha256": artifact.sha256,
        "sample_count": len(motion.sample_times_s),
        "trajectory_count": artifact.trajectory_count,
        "mesh_count": artifact.mesh_count,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
