"""Semantic archive boundary: replay the exact request against the bound model."""

from __future__ import annotations

import math
from collections.abc import Mapping

from .physics_types import DynamicsModel, StaticResult, fail, plain


def _first_difference(actual, expected, path="static_result"):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            return path
        for key in expected:
            difference = _first_difference(actual[key], expected[key], f"{path}.{key}")
            if difference:
                return difference
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return path
        for index, (a, e) in enumerate(zip(actual, expected)):
            difference = _first_difference(a, e, f"{path}[{index}]")
            if difference:
                return difference
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if (
            isinstance(actual, bool)
            or not isinstance(actual, (int, float))
            or not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
        ):
            return path
    elif actual != expected:
        return path
    return None


def validate_bound_static_result(
    *, model: DynamicsModel, result: StaticResult, operation: str
) -> None:
    """Reject inconsistent evidence while retaining truthful failed experiments.

    The digest is a consistency check, not a digital signature. Replaying the
    request prevents merely re-signing an archive or editing the digest from
    concealing stale forces, torques, poses or reactions.
    """
    from .statics import check_wrench_balance, solve_static_equilibrium

    if result.request is None or result.model_sha256 is None:
        fail(
            "RESULT-UNBOUND",
            "Static result has no model binding or replayable request.",
            operation=operation,
            fix="Solve the case again with v0.6.0 and archive the resulting bound StaticResult.",
        )
    if result.model_sha256 != model.content_hash:
        fail(
            "RESULT-MODEL-MISMATCH",
            "Static result was produced for a different physical model.",
            operation=operation,
            objects=(model.assembly.assembly_id,),
            evidence={"actual": result.model_sha256, "expected": model.content_hash},
            fix="Re-run this static request against the exact model being archived.",
        )
    balance = check_wrench_balance(
        result=result,
        force_tolerance_n=result.request.force_tolerance_n,
        moment_tolerance_nm=result.request.moment_tolerance_nm,
    )
    if result.passed and not balance.passed:
        fail(
            "RESULT-INCONSISTENT",
            "A completed passing result fails wrench balance.",
            operation=operation,
            evidence=balance.to_dict(),
            fix="Preserve the solver output and recompute the static case; do not edit its acceptance status.",
        )
    replayed = solve_static_equilibrium(model=model, request=result.request)
    difference = _first_difference(plain(result), plain(replayed))
    if difference:
        fail(
            "RESULT-INCONSISTENT",
            "Stored static evidence differs from re-solving its request.",
            operation=operation,
            objects=(difference,),
            evidence={"different_field": difference},
            fix="Recompute the result for its recorded model and request, retaining failures and nonunique reactions.",
        )


def validate_bound_static_check(
    *, model: DynamicsModel, results: tuple[StaticResult, ...], check, operation: str
) -> None:
    """Recompute the supported check type at its bound static-result index."""
    from .statics import check_static_load_limits, check_wrench_balance

    if (
        check.model_sha256 != model.content_hash
        or check.result_index is None
        or not 0 <= check.result_index < len(results)
    ):
        fail(
            "CHECK-UNBOUND",
            "Static check has no valid model/result binding.",
            operation=operation,
            fix="Recompute the check for a static result and archive its model digest and result index.",
        )
    result = results[check.result_index]
    if check.operation == "check_static_load_limits":
        limits = {}
        for joint_id, record in check.evidence.items():
            if not isinstance(record, Mapping) or "limit" not in record:
                fail(
                    "CHECK-INVALID",
                    "Static load-limit evidence lacks a numeric limit.",
                    operation=operation,
                )
            limits[joint_id] = float(record["limit"])
        recomputed = check_static_load_limits(result=result, limits=limits)
    elif check.operation == "check_wrench_balance":
        recomputed = check_wrench_balance(
            result=result,
            force_tolerance_n=float(
                check.evidence.get(
                    "force_tolerance_n",
                    result.request.force_tolerance_n if result.request else 0.01,
                )
            ),
            moment_tolerance_nm=float(
                check.evidence.get(
                    "moment_tolerance_nm",
                    result.request.moment_tolerance_nm if result.request else 0.001,
                )
            ),
        )
    else:
        fail(
            "CHECK-UNSUPPORTED",
            f"Cannot replay static check {check.operation!r}.",
            operation=operation,
            fix="Archive only supported, bound static checks or leave the check outside acceptance_passed.",
        )
    expected = check.to_dict()
    actual = recomputed.to_dict()
    for key in ("operation", "status", "passed", "evidence", "issues"):
        difference = _first_difference(
            actual.get(key), expected.get(key), f"check.{key}"
        )
        if difference:
            fail(
                "CHECK-INCONSISTENT",
                "Stored static check differs from recomputing its bound result.",
                operation=operation,
                objects=(difference,),
                fix="Recompute the check for the recorded result and retain its actual status/evidence.",
            )
