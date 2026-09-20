"""v0.6.0 historical package regression, with an explicit legacy SDK reader.

Usage: python verify_conversion.py --sdk-python /path/to/2.0.4b3/python
No automatic interpreter/version substitution is permitted.
"""

from pathlib import Path
import argparse
import json
from kincheckapi.cadir import convert_mjcf
from kincheckapi.dynamics import (
    measure_package_physics,
    build_dynamics_model,
    compile_dynamics_model,
    validate_physics_conversion,
    probe_dynamics_capabilities,
    PhysicsError,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "base",
    "guard",
    "crank",
    "coupler",
    "rocker",
    "pin_a",
    "pin_b",
    "pin_c",
    "pin_d",
}


def verify(sdk_python):
    package = ROOT / "model/out/guided_four_bar_actuator.scadpkg"
    try:
        measure_package_physics(package_path=package)
    except PhysicsError as error:
        current = error.to_dict()
        assert error.code == "KINCHECK-PHYSICS-FRAME-INCOMPATIBLE"
    else:
        raise AssertionError(
            "Expected current SDK to explicitly reject the legacy integer frame encoding"
        )
    manifest = measure_package_physics(package_path=package, sdk_python=sdk_python)
    assert {
        o.occurrence_id.rsplit("/", 1)[-1] for o in manifest.occurrences
    } == EXPECTED
    assert abs(manifest.definitions["coupler"].mass_kg - 0.008457569657213554) <= 1e-10
    adapter = convert_mjcf(
        xml_path=ROOT / "model/scene.xml",
        mapping_path=ROOT / "model/scene.mapping.json",
        asset_root=ROOT / "model",
    )
    model = build_dynamics_model(assembly=adapter.assembly, manifest=manifest)
    compiled = compile_dynamics_model(model=model)
    conversion = validate_physics_conversion(model=model, compilation=compiled)
    conversion.raise_if_failed()
    leaf = sum(o.properties.mass_kg for o in manifest.occurrences)
    assert abs(leaf - sum(p.mass_kg for p in model.body_properties.values())) < 1e-10
    pins = {
        o.occurrence_id: o.properties.mass_kg
        for o in manifest.occurrences
        if o.occurrence_id.rsplit("/", 1)[-1].startswith("pin_")
    }
    assert len(pins) == 4
    capability = probe_dynamics_capabilities(
        model=model, operation="solve_static_equilibrium"
    )
    assert capability.status == "capability_failed"
    import mujoco

    native = mujoco.MjModel.from_xml_path(str(ROOT / "model/scene.xml"))
    bid = mujoco.mj_name2id(native, mujoco.mjtObj.mjOBJ_BODY, "body_coupler")
    default_mass = float(native.body_mass[bid])
    assert abs(default_mass - manifest.definitions["coupler"].mass_kg) > 0.01
    output = ROOT / "physics"
    (output / "physics-manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2) + "\n"
    )
    (output / "explicit-inertia.xml").write_text(compiled.model_xml + "\n")
    report = {
        "passed": True,
        "operation": "verify_four_bar_physics_conversion",
        "scope": "all 9 leaf masses and compiled tensors; no closed-loop support reaction claim",
        "current_sdk_expected_failure": current,
        "conversion": conversion.to_dict(),
        "pin_masses_kg": pins,
        "total_mass_kg": leaf,
        "default_mjcf_coupler_mass_kg": default_mass,
        "brep_coupler_mass_kg": manifest.definitions["coupler"].mass_kg,
        "static_capability": capability.to_dict(),
    }
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("conversion", "current_sdk_expected_failure")
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-python", required=True)
    args = parser.parse_args()
    verify(args.sdk_python)
