"""E01 v0.6.1/v0.6.2 dynamic acceptance on the captured CADIR package.

The script consumes the exported package and MJCF through the public adapter;
it never imports model-generation parameters.  The static verifier remains the
source of the complete geometry and interface checks.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from kincheckapi.cadir import convert_mjcf
from kincheckapi.dynamics import (
    ActuatorProfile,
    ActuatorSpec,
    DynamicRequest,
    DynamicState,
    ForwardDynamicsRequest,
    build_dynamics_model,
    check_dynamic_load_limits,
    check_dynamic_tracking,
    measure_package_physics,
    solve_forward_dynamics,
    solve_inverse_dynamics,
)


def verify(model_dir: str | Path):
    root = Path(model_dir).resolve()
    adapter = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    model = build_dynamics_model(
        assembly=adapter.assembly,
        manifest=measure_package_physics(package_path=root / "product.scadpkg"),
    )
    movable = tuple(
        j.joint_id for j in model.assembly.joints if j.joint_type.value != "fixed"
    )
    if len(movable) != 1:
        raise ValueError(f"E01 dynamic example requires one scalar joint, got {movable}")
    joint_id = movable[0]
    inverse = solve_inverse_dynamics(
        model=model,
        request=DynamicRequest(
            states=(
                DynamicState(
                    joint_id=joint_id,
                    position=math.radians(30.0),
                    velocity=0.0,
                    acceleration=2.0,
                ),
            )
        ),
    )
    limit = check_dynamic_load_limits(
        result=inverse,
        limits={joint_id: 35.0},
    )
    forward_request = ForwardDynamicsRequest(
        initial_states=(DynamicState(joint_id=joint_id, position=math.radians(30.0)),),
        actuators=(ActuatorSpec(actuator_id="arm_motor", joint_id=joint_id, max_effort=35.0, max_speed=10.0),),
        profiles=(ActuatorProfile(actuator_id="arm_motor", points=((0.0, 35.0), (0.2, 35.0))),),
        duration_s=0.2,
        sample_period_s=0.05,
    )
    forward = solve_forward_dynamics(model=model, request=forward_request)
    tracking = check_dynamic_tracking(
        result=forward,
        targets={joint_id: forward.samples[-1].joint_positions[joint_id]},
        tolerance=1e-12,
    ) if forward.samples else None
    return {
        "operation": "verify_e01_dynamic",
        "passed": inverse.passed and limit.passed and forward.passed and (tracking is None or tracking.passed),
        "inverse_dynamics": inverse.to_dict(),
        "effort_limit": limit.to_dict(),
        "forward_dynamics": forward.to_dict(),
        "tracking": None if tracking is None else tracking.to_dict(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["passed"] else 1
    except Exception as exc:
        print(json.dumps({"operation": "verify_e01_dynamic", "passed": False, "status": "validation_failed", "what_happened": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
