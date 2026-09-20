"""Independent E01 orchestration; only public APIs and standard library.

Reference moment is supplied by verify.py, never by the statics implementation.
"""

from dataclasses import replace
import json
import math
from pathlib import Path

from kincheckapi.cadir import convert_mjcf
from kincheckapi.dynamics import (
    GravityField,
    PhysicsReport,
    StaticRequest,
    SupportSpec,
    WrenchLoad,
    build_dynamics_model,
    check_static_load_limits,
    check_wrench_balance,
    compile_dynamics_model,
    measure_package_physics,
    solve_static_equilibrium,
    transform_mass_properties,
    validate_physics_conversion,
)
from kincheckapi.diagnostics import Evidence, SimIssue
from kincheckapi.pose import relative_pose, compose_pose, transform_point


def verify_loaded_arm(
    *,
    model_dir,
    angles_deg,
    reference_moment,
    force_tolerance_n,
    moment_tolerance_nm,
    free_clearance_m,
    guard_clearance_m,
    moment_absolute_tolerance_nm,
    moment_relative_tolerance,
    rated_torque_nm,
    short_term_torque_nm,
):
    from kincheckapi.dynamics import (
        check_static_geometry,
        ContactRegion,
        measure_interface_centers,
    )

    root = Path(model_dir)
    adapter = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    manifest = measure_package_physics(package_path=root / "product.scadpkg")
    model = build_dynamics_model(assembly=adapter.assembly, manifest=manifest)
    contract = json.loads((root / "interfaces.json").read_text())
    oid = lambda short: "node/dynamics_loaded_arm/" + short
    # Required physical roles cannot disappear when a relation is deleted.
    mandatory = {
        "base",
        "support_left",
        "support_right",
        "bushing_left",
        "bushing_right",
        "shaft",
        "arm",
        "platform",
        "motor_mount",
        "motor_stator",
        "motor_rotor",
        "coupling",
        "guard",
        "load_ear",
        "key",
        "lock_ring",
        "thrust_left",
        "thrust_right",
    }
    expected_mass = {"empty": 0.0, "rated": 2.0, "overload": 3.0}[contract["variant"]]
    if expected_mass:
        mandatory.add("payload")
    present = {o.occurrence_id.rsplit("/", 1)[-1] for o in manifest.occurrences}
    problems = []
    cases = []

    def reject(code, msg, objects=(), actual=None, expected=None, unit=None):
        problems.append(
            SimIssue(
                code="KINCHECK-E01-" + code,
                severity="error",
                stage="verify_loaded_arm",
                message=msg,
                object_ids=tuple(objects),
                evidence=(
                    Evidence(key=code, actual=actual, expected=expected, unit=unit),
                ),
                suggested_actions=(
                    "Repair the owning CAD part/connection and re-capture; keep the frozen verifier.",
                ),
            )
        )

    if not mandatory <= present:
        reject(
            "BOM-MISSING",
            "Required physical entities are missing.",
            mandatory - present,
        )
    if expected_mass:
        p = next(
            (o for o in manifest.occurrences if o.occurrence_id == oid("payload")), None
        )
        if (
            p is None
            or abs(p.properties.mass_kg - expected_mass) > expected_mass * 0.001
        ):
            reject(
                "PAYLOAD-MASS",
                "Measured payload mass is outside ±0.1%.",
                (oid("payload"),),
                None if p is None else p.properties.mass_kg,
                expected_mass,
                "kg",
            )
    moving = model.occurrence_components.get(oid("arm"))
    joints = [
        j.joint_id for j in model.assembly.joints if j.joint_type.value != "fixed"
    ]
    if len(joints) != 1:
        reject("TOPOLOGY", "Exactly one scalar swing axis is required.", joints)
    if problems:
        return PhysicsReport(
            operation="verify_loaded_arm", status="failed", issues=tuple(problems)
        )
    joint = joints[0]
    compiled = compile_dynamics_model(model=model)
    conversion = validate_physics_conversion(model=model, compilation=compiled)
    problems.extend(conversion.issues)
    supports = tuple(SupportSpec(**s) for s in contract["supports"])
    contacts = tuple(ContactRegion(**c) for c in contract["contacts"])
    moving_occ = [
        o
        for o in manifest.occurrences
        if model.occurrence_components[o.occurrence_id] == moving
    ]
    initial = model.assembly.get_component(component_id=moving).initial_pose
    load_interface = measure_interface_centers(
        package_path=root / "product.scadpkg",
        occurrence_id=oid("load_ear"),
        interface_name="interface.load",
    )
    if len(load_interface["centers_m"]) != 1:
        reject(
            "LOAD-INTERFACE",
            "Exactly one physical loading face is required.",
            (oid("load_ear"),),
        )
        return PhysicsReport(
            operation="verify_loaded_arm", status="failed", issues=tuple(problems)
        )
    ear = next(o for o in manifest.occurrences if o.occurrence_id == oid("load_ear"))
    load_point_initial = transform_point(
        pose=ear.pose_world, point_m=load_interface["centers_m"][0]
    )
    for angle in angles_deg:
        req = StaticRequest(
            gravity=GravityField(acceleration_m_s2=(0, 0, -9.81)),
            supports=supports,
            joint_positions={joint: math.radians(angle)},
            joint_modes={joint: "hold"},
            force_tolerance_n=force_tolerance_n,
            moment_tolerance_nm=moment_tolerance_nm,
        )
        base_result = solve_static_equilibrium(model=model, request=req)
        if not base_result.passed:
            problems.extend(base_result.issues)
            continue
        delta = relative_pose(parent=initial, child=base_result.component_poses[moving])
        # The imported group frame is the moving body's frame; transfer each
        # world occurrence through initial group-local into current world.
        pose_delta = compose_pose(
            parent=base_result.component_poses[moving],
            child=__import__(
                "kincheckapi.pose", fromlist=["inverse_pose"]
            ).inverse_pose(pose=initial),
        )
        measured = [
            transform_mass_properties(
                properties=o.properties, pose=pose_delta, frame_id="world"
            )
            for o in moving_occ
        ]
        geometry = check_static_geometry(
            package_path=root / "product.scadpkg",
            manifest=manifest,
            occurrence_components=model.occurrence_components,
            component_initial_poses={
                c.component_id: c.initial_pose for c in model.assembly.components
            },
            component_poses=base_result.component_poses,
            contacts=contacts,
            free_clearance_m=free_clearance_m,
            guard_clearance_m=guard_clearance_m,
            guard_occurrence_ids=(oid("guard"),),
        )
        problems.extend(geometry.issues)
        point = transform_point(pose=pose_delta, point_m=load_point_initial)
        for eccentric in (False, True):
            loads = (
                (
                    WrenchLoad(
                        load_id="eccentric100N",
                        component_id=moving,
                        force_n=(0, 0, -100),
                        moment_nm=(0, 0, 0),
                        point_m=point,
                        frame_id="world",
                        applied_by="rigid load ear fixture",
                    ),
                )
                if eccentric
                else ()
            )
            result = solve_static_equilibrium(
                model=model, request=replace(req, loads=loads)
            )
            balance = check_wrench_balance(
                result=result,
                force_tolerance_n=force_tolerance_n,
                moment_tolerance_nm=moment_tolerance_nm,
            )
            problems.extend(balance.issues)
            expected = reference_moment(measured, point if eccentric else None)
            actual = result.generalized_holding.get(joint)
            tolerance = max(
                moment_absolute_tolerance_nm, moment_relative_tolerance * abs(expected)
            )
            if actual is None or abs(actual - expected) > tolerance:
                reject(
                    "MOMENT-MISMATCH",
                    "Holding torque differs from independently summed CAD masses.",
                    (joint,),
                    actual,
                    expected,
                    "N*m",
                )
            rating = check_static_load_limits(
                result=result, limits={joint: rated_torque_nm}
            )
            short = check_static_load_limits(
                result=result, limits={joint: short_term_torque_nm}
            )
            cases.append(
                {
                    "angle_deg": angle,
                    "eccentric": eccentric,
                    "reference_nm": expected,
                    "result": result.to_dict(),
                    "balance": balance.to_dict(),
                    "rated_limit": rating.to_dict(),
                    "short_term_static_limit": short.to_dict(),
                    "geometry": geometry.to_dict(),
                }
            )
    return PhysicsReport(
        operation="verify_loaded_arm",
        status="failed" if problems else "passed",
        issues=tuple(problems),
        evidence={
            "variant": contract["variant"],
            "cases": cases,
            "conversion": conversion.to_dict(),
            "scope": "three static poses; ratings reported separately; no dynamic/strength/contact stability claim",
        },
    )
