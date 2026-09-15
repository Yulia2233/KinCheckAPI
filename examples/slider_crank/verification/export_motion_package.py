"""Export the slider-crank simulation for the standalone KinCheck viewer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from kincheckapi import export

CASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = CASE_DIR / "model"
OUTPUT_PATH = CASE_DIR / "output" / "slider_crank.kincheck"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    sys.path.insert(0, str((CASE_DIR / "verification").resolve()))
    import verify  # noqa: E402

    assembly, _scenario, motion = verify.solve(args.model_dir)
    artifact = export.motion_package(
        assembly=assembly,
        motion_result=motion,
        output_path=args.output,
        asset_root=args.model_dir,
        title="KinCheckAPI slider-crank kinematic simulation",
        require_meshes=True,
        metadata={"source": "examples/slider_crank/verification/verify.py"},
    )
    print(json.dumps({
        "status": "passed",
        "package": str(artifact.path),
        "bytes": artifact.bytes,
        "sha256": artifact.sha256,
        "sample_count": len(motion.sample_times_s),
        "trajectory_count": artifact.trajectory_count,
        "mesh_count": artifact.mesh_count,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
