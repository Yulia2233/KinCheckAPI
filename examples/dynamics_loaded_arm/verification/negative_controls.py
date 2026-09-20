"""Deliberate bad inputs. Detection passing never makes a bad model pass."""

from dataclasses import replace
from pathlib import Path
import json
import math

from kincheckapi.cadir import convert_mjcf
from kincheckapi.dynamics import *
from kincheckapi.physics_types import digest
from kincheckapi.pose import Pose

ROOT = Path(__file__).resolve().parents[1]


def run():
    root = ROOT / "model"
    manifest = measure_package_physics(package_path=root / "product.scadpkg")
    adapter = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    model = build_dynamics_model(assembly=adapter.assembly, manifest=manifest)
    contract = json.loads((root / "interfaces.json").read_text())
    joint = model.assembly.joints[0].joint_id
    request = StaticRequest(
        gravity=GravityField(acceleration_m_s2=(0, 0, -9.81)),
        supports=tuple(SupportSpec(**s) for s in contract["supports"]),
        joint_positions={joint: 0.0},
        joint_modes={joint: "hold"},
    )
    records = []

    def expect(name, code, fn):
        try:
            result = fn()
            payload = result.to_dict()
            codes = {i.code for i in result.issues}
        except PhysicsError as error:
            payload = error.to_dict()
            codes = {error.code}
        assert not payload["passed"] and any(c.endswith(code) for c in codes), (
            name,
            payload,
        )
        records.append(
            {
                "control": name,
                "detected": True,
                "expected_code_suffix": code,
                "engineering_result": payload,
            }
        )

    expect(
        "missing_density",
        "DENSITY-MISSING",
        lambda: measure_mass_properties(
            brep=b"", material=None, definition_id="payload"
        ),
    )
    expect(
        "unknown_density_unit",
        "DENSITY-UNIT-INVALID",
        lambda: PhysicsMaterial(
            material_id="steel",
            density=7850,
            density_unit="g/banana",
            source="negative",
        ),
    )
    expect(
        "payload_double_count",
        "PAYLOAD-DUPLICATED",
        lambda: Payload(
            payload_id="payload-again",
            component_id=model.occurrence_components[
                "node/dynamics_loaded_arm/payload"
            ],
            cad_occurrence_id="node/dynamics_loaded_arm/payload",
            properties=manifest.definitions["payload"],
        ),
    )
    expect(
        "support_removed",
        "SUPPORT-MISSING",
        lambda: solve_static_equilibrium(
            model=model, request=replace(request, supports=())
        ),
    )
    expect(
        "free_axis_has_no_holding_effort",
        "STATIC-NOT-EQUILIBRIUM",
        lambda: solve_static_equilibrium(
            model=model, request=replace(request, joint_modes={joint: "free"})
        ),
    )
    expect(
        "force_individual_support_split",
        "REACTION-NONUNIQUE",
        lambda: solve_static_equilibrium(
            model=model,
            request=replace(request, request_individual_support_reactions=True),
        ),
    )
    result = solve_static_equilibrium(model=model, request=request)
    expect(
        "motor_rating_insufficient",
        "STATIC-LOAD-LIMIT",
        lambda: check_static_load_limits(result=result, limits={joint: 1.0}),
    )
    # Keep measured values but corrupt their claimed density provenance.
    definitions = dict(manifest.definitions)
    p = definitions["payload"]
    provenance = dict(p.provenance)
    material = dict(provenance["material"])
    material["density"] *= 1e9
    provenance["material"] = material
    definitions["payload"] = replace(p, provenance=provenance)
    corrupted = replace(manifest, definitions=definitions)
    expect(
        "density_factor_1e9",
        "PHYSICS-SOURCE-CONFLICT",
        lambda: check_mass_properties(model=replace(model, manifest=corrupted)),
    )
    occurrences = list(manifest.occurrences)
    i = next(i for i, o in enumerate(occurrences) if o.definition_id == "arm")
    occurrences[i] = replace(
        occurrences[i],
        pose_world=Pose(orientation_xyzw=(0, 0, math.sin(0.2), math.cos(0.2))),
    )
    expect(
        "inertia_placement_frame_corrupted",
        "FRAME-INCOMPATIBLE",
        lambda: build_dynamics_model(
            assembly=model.assembly,
            manifest=replace(manifest, occurrences=tuple(occurrences)),
        ),
    )
    missing = replace(
        manifest,
        occurrences=tuple(
            o
            for o in manifest.occurrences
            if not o.occurrence_id.endswith("bushing_left")
        ),
    )
    expect(
        "bushing_coverage_removed",
        "PHYSICS-SOURCE-CONFLICT",
        lambda: build_dynamics_model(assembly=model.assembly, manifest=missing),
    )
    # Fault injection into physical entity poses, preserving all 2850 pairs.
    initial = {o.occurrence_id: o.pose_world for o in manifest.occurrences}
    changed = dict(initial)
    guard = "node/dynamics_loaded_arm/guard"
    changed[guard] = Pose(position_m=(-0.015, 0, 0))
    expect(
        "guard_intrudes_into_rotating_coupling",
        "GEOMETRY-INTERFERENCE",
        lambda: check_static_geometry(
            package_path=root / "product.scadpkg",
            manifest=manifest,
            occurrence_components={
                o.occurrence_id: o.occurrence_id for o in manifest.occurrences
            },
            component_initial_poses=initial,
            component_poses=changed,
            contacts=tuple(ContactRegion(**c) for c in contract["contacts"]),
            guard_occurrence_ids=(guard,),
        ),
    )
    output = {
        "operation": "E01_negative_controls",
        "passed": all(r["detected"] for r in records),
        "note": "passed means expected rejection was observed; engineering_result remains failed/indeterminate",
        "controls": records,
    }
    (ROOT / "output/negative-controls.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    print(json.dumps({"passed": output["passed"], "controls": len(records)}, indent=2))


if __name__ == "__main__":
    run()
