"""Optional, hash-indexed physics member for backward-compatible .kincheck files."""

from __future__ import annotations
import math

from .physics_types import (
    DynamicsModel,
    Payload,
    PhysicsManifest,
    RigidBodyProperties,
    StaticResult,
    fail,
    plain,
)
from .physics_mass import build_dynamics_model, check_mass_properties
from ._static_validation import (
    validate_bound_static_result,
    validate_bound_static_check,
)


def physics_document(model, results, checks=()):
    op = "motion_package"
    if not isinstance(model, DynamicsModel) or not results:
        fail(
            "PACKAGE-INVALID",
            "Physics export requires a physical model and nonempty static cases.",
            operation=op,
        )
    checked = check_mass_properties(model=model)
    if not checked.passed:
        fail(
            "PHYSICS-SOURCE-CONFLICT",
            "Physics conversion has not passed.",
            operation=op,
            evidence=checked.to_dict(),
        )
    if any(
        r.status
        not in ("completed", "completed_with_warnings", "failed", "indeterminate")
        or not r.body_residuals
        for r in results
    ):
        fail(
            "PACKAGE-INCOMPLETE",
            "Only complete static experiments with actual balance evidence may be archived.",
            operation=op,
        )
    for result in results:
        validate_bound_static_result(model=model, result=result, operation=op)
    for check in checks:
        validate_bound_static_check(
            model=model, results=tuple(results), check=check, operation=op
        )
    return {
        "schema_version": "kincheck.static/1.1",
        "model_sha256": model.content_hash,
        "base_component_properties": {
            k: v.to_dict() for k, v in model.base_component_properties.items()
        },
        "assembly_id": model.assembly.assembly_id,
        "manifest": None if model.manifest is None else model.manifest.to_dict(),
        "component_properties": {
            k: v.to_dict() for k, v in model.component_properties.items()
        },
        "body_properties": {k: v.to_dict() for k, v in model.body_properties.items()},
        "occurrence_components": dict(model.occurrence_components),
        "payloads": plain(model.payloads),
        "static_results": [r.to_dict() for r in results],
        "units": {
            "mass": "kg",
            "length": "m",
            "inertia": "kg*m2",
            "force": "N",
            "moment": "N*m",
        },
        "capabilities": ["mass_properties", "tree_static_equilibrium"],
        "checks": [r.to_dict() for r in checks],
        "acceptance_scope": "equilibrium and explicitly supplied checks only",
        "acceptance_passed": all(r.passed for r in results)
        and all(r.passed for r in checks),
    }


def read_physics_document(assembly, document):
    op = "read_physics_document"
    if (
        document.get("schema_version") != "kincheck.static/1.1"
        or document.get("assembly_id") != assembly.assembly_id
    ):
        fail(
            "PACKAGE-INVALID",
            "Physics schema/assembly identity mismatch.",
            operation=op,
        )
    manifest = (
        None
        if document["manifest"] is None
        else PhysicsManifest.from_dict(document["manifest"])
    )
    payloads = tuple(
        Payload(
            **{
                **p,
                "properties": None
                if p["properties"] is None
                else RigidBodyProperties.from_dict(p["properties"]),
            }
        )
        for p in document["payloads"]
    )
    # Rebuild from pre-payload measurements, applying each retained payload once.
    base_props = {
        k: RigidBodyProperties.from_dict(v)
        for k, v in document["base_component_properties"].items()
    }
    model = build_dynamics_model(
        assembly=assembly,
        manifest=manifest,
        component_properties=base_props if manifest is None else None,
        occurrence_components=document["occurrence_components"],
        payloads=payloads,
    )
    if document.get("model_sha256") != model.content_hash:
        fail(
            "RESULT-MODEL-MISMATCH",
            "Archived model digest differs from reconstructed physical inputs.",
            operation=op,
        )
    from .physics_mass import compare_properties

    for name, actual in [
        ("base_component_properties", model.base_component_properties),
        ("component_properties", model.component_properties),
        ("body_properties", model.body_properties),
    ]:
        if set(document[name]) != set(actual):
            fail(
                "OCCURRENCE-COVERAGE-INCOMPLETE",
                "Archived physics identities differ.",
                operation=op,
            )
        for cid, p in actual.items():
            if compare_properties(
                RigidBodyProperties.from_dict(document[name][cid]),
                p,
                operation=op,
                object_id=cid,
            ):
                fail(
                    "PHYSICS-SOURCE-CONFLICT",
                    "Archived aggregation differs from source.",
                    operation=op,
                    objects=(cid,),
                )
    results = tuple(StaticResult.from_dict(v) for v in document["static_results"])
    ids = {c.component_id for c in assembly.components}
    jids = {j.joint_id for j in assembly.joints}
    for raw, r in zip(document["static_results"], results):
        if raw.get("passed") is not r.passed:
            fail(
                "RESULT-INCONSISTENT",
                "Stored result pass flag contradicts its status and issues.",
                operation=op,
            )
        if (
            set(r.component_poses) != ids
            or not set(r.generalized_holding) <= jids
            or set(r.body_residuals) != set(model.body_properties)
        ):
            fail(
                "PACKAGE-INVALID",
                "Static result references or coverage are invalid.",
                operation=op,
            )
        for load in r.load_wrenches:
            if load["component_id"] not in ids or load["frame_id"] != "world":
                fail(
                    "PACKAGE-INVALID",
                    "Static load receiver/frame is invalid.",
                    operation=op,
                )
            for key in ("point_m", "force_n", "moment_nm"):
                if len(load[key]) != 3 or any(not math.isfinite(x) for x in load[key]):
                    fail(
                        "PACKAGE-INVALID",
                        "Static load has nonfinite or malformed vectors.",
                        operation=op,
                    )
    from .physics_types import PhysicsReport
    from .diagnostics import SimIssue, Evidence

    checks = tuple(
        PhysicsReport(
            operation=c["operation"],
            status=c["status"],
            evidence=c["evidence"],
            model_sha256=c.get("model_sha256"),
            result_index=c.get("result_index"),
            issues=tuple(
                SimIssue(
                    **{**i, "evidence": tuple(Evidence(**e) for e in i["evidence"])}
                )
                for i in c["issues"]
            ),
        )
        for c in document.get("checks", ())
    )
    for raw_check, check in zip(document.get("checks", ()), checks):
        if raw_check.get("passed") is not check.passed:
            fail(
                "CHECK-INCONSISTENT",
                "Stored static-check pass flag contradicts its status and issues.",
                operation=op,
            )
    if not results or document["acceptance_passed"] != (
        all(r.passed for r in results) and all(r.passed for r in checks)
    ):
        fail(
            "PACKAGE-INVALID", "Physics acceptance flag is inconsistent.", operation=op
        )
    # Also validates accepted experiment completeness; failed complete cases stay failed.
    for result in results:
        if (
            result.status
            not in ("completed", "completed_with_warnings", "failed", "indeterminate")
            or not result.body_residuals
        ):
            fail("PACKAGE-INCOMPLETE", "Static experiment is incomplete.", operation=op)
        validate_bound_static_result(model=model, result=result, operation=op)
    for check in checks:
        validate_bound_static_check(
            model=model, results=results, check=check, operation=op
        )
    return model, results, checks
