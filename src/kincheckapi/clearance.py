"""Strict triangle-mesh clearance checks backed by python-fcl.

This module deliberately has no geometric fallback.  A clearance result is
valid only when the declared mesh and FCL backends complete the query.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from .assembly import AssemblyModel
from ._clearance_fcl import MeshModel, load_mesh, query_pair, require_backend
from .diagnostics import Evidence, SimIssue
from .errors import BackendCapabilityError, GeometryCheckError
from .pose import Pose, rotate_vector
from .result import InterferenceEvent, MotionResult
from .clearance_result import (
    ClearanceReport,
    EnvelopeSample,
    MinimumClearance,
    MotionEnvelope,
    SamplingScope,
)


def _issue(
    *,
    code: str,
    message: str,
    object_ids: Sequence[str] = (),
    failure_time_s: float | None = None,
    source_paths: Sequence[str] = (),
    evidence: Sequence[Evidence] = (),
    suggested_actions: Sequence[str] = (),
) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="clearance",
        message=message,
        object_ids=tuple(object_ids),
        failure_time_s=failure_time_s,
        source_paths=tuple(source_paths),
        evidence=tuple(evidence),
        suggested_actions=tuple(suggested_actions),
    )


def _component_meshes(*, assembly: AssemblyModel, asset_root: str | Path | None, component_ids: Sequence[str] | None = None) -> tuple[dict[str, MeshModel], tuple[SimIssue, ...]]:
    parts = {part.part_id: part for part in assembly.parts}
    meshes: dict[str, MeshModel] = {}
    issues: list[SimIssue] = []
    requested = None if component_ids is None else {str(item) for item in component_ids}
    for component in assembly.components:
        if requested is not None and component.component_id not in requested:
            continue
        part = parts.get(component.part_id)
        if part is None:
            issues.append(_issue(code="KINCHECK-CLEARANCE-MESH-NOT-FOUND", message="Component references an unknown Part.", object_ids=(component.component_id, component.part_id)))
            continue
        try:
            meshes[component.component_id] = load_mesh(assembly=assembly, part=part, asset_root=asset_root)
        except FileNotFoundError as cause:
            issues.append(
                _issue(
                    code="KINCHECK-CLEARANCE-MESH-NOT-FOUND",
                    message="A checked Component does not have a readable mesh asset.",
                    object_ids=(component.component_id, component.part_id),
                    source_paths=(str(part.source_path or ""),),
                    evidence=(
                        Evidence(key="native_error_type", actual=type(cause).__name__),
                    ),
                    suggested_actions=("Provide a valid STL asset for every checked Component.",),
                )
            )
        except (TypeError, ValueError, OSError) as cause:
            issues.append(
                _issue(
                    code="KINCHECK-CLEARANCE-MESH-INVALID",
                    message="A checked Component mesh asset is not valid for geometric checking.",
                    object_ids=(component.component_id, component.part_id),
                    source_paths=(str(part.source_path or ""),),
                    evidence=(
                        Evidence(key="native_error_type", actual=type(cause).__name__),
                    ),
                    suggested_actions=("Replace the mesh with a valid triangle mesh and run the check again.",),
                )
            )
    return meshes, tuple(issues)


def _normalize_pairs(
    *,
    assembly: AssemblyModel,
    meshes: Mapping[str, MeshModel],
    component_pairs: Sequence[Sequence[str]] | None,
    excluded_pairs: Sequence[Sequence[str]],
) -> tuple[tuple[tuple[str, str], ...], tuple[SimIssue, ...]]:
    available = set(meshes)
    known = {component.component_id for component in assembly.components}
    exclusions: set[tuple[str, str]] = set()
    issues: list[SimIssue] = []

    def normalize_pair(
        raw_pair: Sequence[str],
        *,
        invalid_message: str,
        missing_message: str,
    ) -> tuple[str, str] | None:
        try:
            if isinstance(raw_pair, (str, bytes)) or len(raw_pair) != 2:
                raise ValueError
            left, right = str(raw_pair[0]), str(raw_pair[1])
        except (IndexError, TypeError, ValueError):
            try:
                object_ids = tuple(str(item) for item in raw_pair)
            except TypeError:
                object_ids = (str(raw_pair),)
            issues.append(
                _issue(
                    code="KINCHECK-CLEARANCE-COMPONENT-PAIR-INVALID",
                    message=invalid_message,
                    object_ids=object_ids,
                )
            )
            return None
        if left == right:
            issues.append(
                _issue(
                    code="KINCHECK-CLEARANCE-COMPONENT-PAIR-INVALID",
                    message=invalid_message,
                    object_ids=(left, right),
                )
            )
            return None
        if left not in known or right not in known:
            issues.append(
                _issue(
                    code="KINCHECK-CLEARANCE-COMPONENT-PAIR-NOT-FOUND",
                    message=missing_message,
                    object_ids=(left, right),
                )
            )
            return None
        return tuple(sorted((left, right)))

    for raw_pair in assembly.collision_exclusions:
        pair = normalize_pair(
            raw_pair,
            invalid_message="Assembly contains an invalid collision exclusion pair.",
            missing_message="Assembly collision exclusion references an unknown Component.",
        )
        if pair is not None:
            exclusions.add(pair)
    for pair in excluded_pairs:
        normalized = normalize_pair(
            pair,
            invalid_message="Each excluded pair must contain two distinct Component IDs.",
            missing_message="A requested exclusion pair references an unknown Component.",
        )
        if normalized is not None:
            exclusions.add(normalized)
    if component_pairs is None:
        selected = [(left, right) for index, left in enumerate(sorted(available)) for right in sorted(available)[index + 1:]]
    else:
        selected = []
        for raw in component_pairs:
            pair = normalize_pair(
                raw,
                invalid_message="Each component pair must contain two distinct Component IDs.",
                missing_message="A requested component pair references an unknown Component.",
            )
            if pair is not None:
                selected.append(pair)
    result: set[tuple[str, str]] = set()
    for left, right in selected:
        pair = tuple(sorted((left, right)))
        if pair in exclusions:
            continue
        if pair[0] not in available or pair[1] not in available:
            issues.append(_issue(code="KINCHECK-CLEARANCE-MESH-NOT-FOUND", message="A requested component pair lacks a valid mesh.", object_ids=pair))
            continue
        result.add(pair)
    if not result:
        issues.append(
            _issue(
                code="KINCHECK-CLEARANCE-COMPONENT-PAIRS-EMPTY",
                message="No valid component pairs remain to be checked.",
            )
        )
    return tuple(sorted(result)), tuple(issues)


def _motion_samples(
    *,
    motion_result: MotionResult,
    component_ids: Sequence[str],
    sampling_scope: SamplingScope,
) -> tuple[tuple[float, Mapping[str, Pose]], ...]:
    if sampling_scope == "motion_result":
        by_component: dict[str, dict[float, Pose]] = {item: {} for item in component_ids}
        for trajectory in motion_result.trajectories:
            if trajectory.connector_id is None and trajectory.component_id in by_component:
                by_component[trajectory.component_id] = {
                    float(time): pose for time, pose in zip(trajectory.times_s, trajectory.poses)
                }
        missing = tuple(item for item, values in by_component.items() if not values)
        if missing:
            raise ValueError(f"KINCHECK-CLEARANCE-TRAJECTORY-MISSING: MotionResult lacks Component trajectories: {missing}")
        times = tuple(float(item) for item in motion_result.sample_times_s)
        samples: list[tuple[float, Mapping[str, Pose]]] = []
        for time in times:
            poses: dict[str, Pose] = {}
            for component_id in component_ids:
                pose = by_component[component_id].get(time)
                if pose is None:
                    raise ValueError(f"KINCHECK-CLEARANCE-TRAJECTORY-MISSING: MotionResult lacks Component {component_id} at time {time}")
                poses[component_id] = pose
            samples.append((time, poses))
        return tuple(samples)
    raw = motion_result.metadata.get("integration_samples")
    if not raw and getattr(motion_result, "integration_samples", ()):
        raw = tuple(item.to_dict() for item in motion_result.integration_samples)
    if not isinstance(raw, (tuple, list)) or not raw:
        raise ValueError("KINCHECK-CLEARANCE-INTEGRATION-SAMPLES-MISSING: MotionResult does not contain physics backend integration-step samples")
    result: list[tuple[float, Mapping[str, Pose]]] = []
    previous_time: float | None = None
    for sample_index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} must be a mapping")
        if "time_s" not in entry:
            raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} lacks time_s")
        try:
            time_s = float(entry["time_s"])
        except (TypeError, ValueError) as cause:
            raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} has an invalid time_s") from cause
        if not math.isfinite(time_s) or time_s < 0.0 or (previous_time is not None and time_s <= previous_time):
            raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} time_s must be finite, non-negative, and strictly increasing")
        poses_raw = entry.get("component_poses")
        if not isinstance(poses_raw, Mapping):
            raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} lacks component_poses")
        poses: dict[str, Pose] = {}
        for component_id in component_ids:
            value = poses_raw.get(component_id)
            if not isinstance(value, Mapping):
                raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} lacks Component {component_id}")
            if "position_m" not in value or "orientation_xyzw" not in value:
                raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} Component {component_id} lacks pose fields")
            try:
                poses[component_id] = Pose(
                    position_m=tuple(value["position_m"]),
                    orientation_xyzw=tuple(value["orientation_xyzw"]),
                )
            except (KeyError, TypeError, ValueError) as cause:
                raise ValueError(f"KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID: sample {sample_index} Component {component_id} has an invalid pose") from cause
        result.append((time_s, poses))
        previous_time = time_s
    return tuple(result)


def _validate_window(*, times: Sequence[float], start_time_s: float | None, end_time_s: float | None) -> tuple[tuple[float, float], tuple[SimIssue, ...]]:
    if not times:
        raise ValueError("No geometric samples are available")
    start = float(times[0] if start_time_s is None else start_time_s)
    end = float(times[-1] if end_time_s is None else end_time_s)
    if not math.isfinite(start) or not math.isfinite(end) or start < 0.0 or end < start:
        raise ValueError("Invalid geometric-check time window")
    selected = tuple(time for time in times if start <= time <= end)
    if not selected:
        raise ValueError("Geometric-check time window contains no samples")
    return (start, end), ()


def _select_samples(
    samples: Sequence[tuple[float, Mapping[str, Pose]]],
    *,
    start_time_s: float | None,
    end_time_s: float | None,
) -> tuple[tuple[float, Mapping[str, Pose]], ...]:
    times = tuple(item[0] for item in samples)
    _validate_window(times=times, start_time_s=start_time_s, end_time_s=end_time_s)
    selected = tuple(
        item
        for item in samples
        if (start_time_s is None or item[0] >= float(start_time_s))
        and (end_time_s is None or item[0] <= float(end_time_s))
    )
    if not selected:
        raise ValueError("Invalid time window: no geometric samples are available")
    return selected


def _check_sample_spacing(times: Sequence[float], max_sample_period_s: float | None) -> tuple[SimIssue, ...]:
    if max_sample_period_s is None:
        return ()
    maximum = float(max_sample_period_s)
    if not math.isfinite(maximum) or maximum <= 0.0:
        return (_issue(code="KINCHECK-CLEARANCE-SAMPLING-TOO-COARSE", message="max_sample_period_s must be finite and positive."),)
    actual = max((right - left for left, right in zip(times, times[1:])), default=0.0)
    if actual > maximum + 1e-12:
        return (_issue(code="KINCHECK-CLEARANCE-SAMPLING-TOO-COARSE", message="Geometric-check samples are coarser than the requested maximum period.", evidence=(Evidence(key="maximum_sample_period_s", actual=actual, expected=maximum, unit="s"),)),)
    return ()


def _validate_query_parameters(*, penetration_tolerance_m: float | None = None, minimum_allowed_clearance_m: float | None = None, sampling_scope: SamplingScope) -> None:
    if sampling_scope not in {"motion_result", "solver_steps"}:
        raise ValueError("KINCHECK-CLEARANCE-PARAMETER-INVALID: sampling_scope must be motion_result or solver_steps")
    for name, value in (("penetration_tolerance_m", penetration_tolerance_m), ("minimum_allowed_clearance_m", minimum_allowed_clearance_m)):
        if value is None:
            continue
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0.0:
            raise ValueError(f"KINCHECK-CLEARANCE-PARAMETER-INVALID: {name} must be finite and non-negative")


def _motion_result_issues(motion_result: MotionResult) -> tuple[SimIssue, ...]:
    if motion_result.status in {"completed", "completed_with_warnings"}:
        return ()
    evidence = (
        Evidence(
            key="motion_result_status",
            actual=motion_result.status,
            expected="completed or completed_with_warnings",
        ),
        Evidence(key="sample_count", actual=len(motion_result.sample_times_s)),
        Evidence(key="time_range_s", actual=(motion_result.start_time_s, motion_result.end_time_s), unit="s"),
    )
    return (
        _issue(
            code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE",
            message="The MotionResult is incomplete and cannot produce a complete verification pass.",
            evidence=evidence,
            failure_time_s=motion_result.end_time_s,
        ),
        _issue(
            code="KINCHECK-CLEARANCE-MOTION-RESULT-INCOMPLETE",
            message="The MotionResult is incomplete; sampled geometry may be inspected, but cannot produce a complete safety pass.",
            evidence=evidence,
            failure_time_s=motion_result.end_time_s,
            suggested_actions=(
                "Resolve the motion failure and rerun the geometric check with a completed MotionResult.",
            ),
        ),
    )


def _requested_pair_component_ids(
    component_pairs: Sequence[Sequence[str]] | None,
) -> tuple[str, ...] | None:
    if component_pairs is None:
        return None
    requested: set[str] = set()
    for raw_pair in component_pairs:
        try:
            if isinstance(raw_pair, (str, bytes)) or len(raw_pair) != 2:
                continue
            requested.update((str(raw_pair[0]), str(raw_pair[1])))
        except (IndexError, TypeError, ValueError):
            continue
    return tuple(sorted(requested))


def _query_failure_issue(cause: BaseException) -> SimIssue:
    """Return a stable public issue without promoting native messages to facts."""

    message = str(cause)
    code = (
        message.partition(":")[0]
        if message.startswith("KINCHECK-")
        else "KINCHECK-CLEARANCE-QUERY-FAILED"
    )
    fact_by_code = {
        "KINCHECK-CLEARANCE-TRAJECTORY-MISSING": "Required component trajectories are not recorded in the MotionResult.",
        "KINCHECK-CLEARANCE-INTEGRATION-SAMPLES-MISSING": "The MotionResult has no recorded integration-step samples.",
        "KINCHECK-CLEARANCE-INTEGRATION-SAMPLE-INVALID": "A recorded integration-step sample is not valid for geometric checking.",
        "KINCHECK-CLEARANCE-PARAMETER-INVALID": "A geometric-check parameter is invalid.",
        "KINCHECK-CLEARANCE-TIME-WINDOW-INVALID": "The requested geometric-check time window is invalid.",
    }
    if "time window" in message.lower() and code == "KINCHECK-CLEARANCE-QUERY-FAILED":
        code = "KINCHECK-CLEARANCE-TIME-WINDOW-INVALID"
    return _issue(
        code=code,
        message=fact_by_code.get(code, "The geometry backend could not complete the requested check."),
        evidence=(Evidence(key="technical_error_type", actual=type(cause).__name__),),
        suggested_actions=(
            "Inspect the reported evidence, correct the geometric-check input, and run the check again.",
        ),
    )


def _sampling_period(times: Sequence[float]) -> float:
    return max(
        (right - left for left, right in zip(times, times[1:])),
        default=0.0,
    )


def _base_report(
    *,
    operation: Literal["interference", "minimum_clearance", "motion_envelope"],
    issues: Sequence[SimIssue],
    sampling_scope: SamplingScope,
    sampling_period_s: float,
    checked_pairs: int,
    checked_samples: int,
    events: Sequence[InterferenceEvent] = (),
    measurements: Sequence[MinimumClearance] = (),
    envelopes: Sequence[MotionEnvelope] = (),
    metadata: Mapping[str, Any] | None = None,
    backend_version: str | None = None,
    maximum_penetration_depth_m: float = 0.0,
    minimum_allowed_clearance_m: float | None = None,
) -> ClearanceReport:
    all_issues = tuple(issues)
    if operation == "interference" and events:
        all_issues += tuple(
            _issue(
                code="KINCHECK-CLEARANCE-INTERFERENCE-DETECTED",
                message="Two checked component meshes interpenetrate at a sampled time.",
                object_ids=(event.component_a_id, event.component_b_id),
                failure_time_s=event.time_s,
                evidence=(
                    Evidence(
                        key="penetration_depth_m",
                        actual=event.penetration_depth_m,
                        expected="<= 0",
                        unit="m",
                    ),
                ),
                suggested_actions=(
                    "Inspect the sampled poses and revise the mechanism geometry or motion input.",
                ),
            )
            for event in events
        )
    if operation == "minimum_clearance":
        penetrating = tuple(item for item in measurements if item.minimum_clearance_m < 0.0)
        if penetrating:
            all_issues += tuple(
                _issue(
                    code="KINCHECK-CLEARANCE-INTERFERENCE-DETECTED",
                    message="The minimum signed mesh clearance is negative, indicating interpenetration.",
                    object_ids=(item.component_a_id, item.component_b_id),
                    failure_time_s=item.time_s,
                    evidence=(Evidence(key="minimum_clearance_m", actual=item.minimum_clearance_m, expected=">= 0", unit="m"),),
                )
                for item in penetrating
            )
    if minimum_allowed_clearance_m is not None:
        min_value = min((item.minimum_clearance_m for item in measurements), default=math.inf)
        if min_value < minimum_allowed_clearance_m:
            all_issues += (_issue(code="KINCHECK-CLEARANCE-MINIMUM-BELOW-THRESHOLD", message="The minimum mesh clearance is below the requested safety threshold.", evidence=(Evidence(key="minimum_clearance_m", actual=min_value, expected=minimum_allowed_clearance_m, unit="m"),)),)
    issue_codes = {item.code for item in all_issues}
    status = "passed" if not all_issues else "failed"
    if "KINCHECK-CLEARANCE-BACKEND-UNAVAILABLE" in issue_codes:
        status = "capability_failed"
    elif issue_codes & {
        "KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE",
        "KINCHECK-CLEARANCE-MOTION-RESULT-INCOMPLETE",
    }:
        status = "partial"
    issue_failure_times = tuple(
        float(item.failure_time_s)
        for item in all_issues
        if item.failure_time_s is not None
    )
    event_failure_times = tuple(item.time_s for item in events)
    return ClearanceReport(
        operation=operation,
        passed=not all_issues,
        status=status,
        events=tuple(events),
        measurements=tuple(measurements),
        envelopes=tuple(envelopes),
        checked_component_pair_count=checked_pairs,
        checked_sample_count=checked_samples,
        first_failure_time_s=min((*issue_failure_times, *event_failure_times), default=None),
        maximum_penetration_depth_m=maximum_penetration_depth_m,
        backend_id="python-fcl" if backend_version is not None else None,
        backend_version=backend_version,
        sampling_scope=sampling_scope,
        sampling_period_s=sampling_period_s,
        issues=all_issues,
        metadata={**dict(metadata or {}), "minimum_allowed_clearance_m": minimum_allowed_clearance_m},
    )


def _prepare(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    component_pairs: Sequence[Sequence[str]] | None,
    excluded_pairs: Sequence[Sequence[str]],
    asset_root: str | Path | None,
    sampling_scope: SamplingScope,
    component_ids: Sequence[str] | None = None,
) -> tuple[dict[str, MeshModel], tuple[tuple[str, str], ...], tuple[SimIssue, ...], str]:
    motion_issues = _motion_result_issues(motion_result)
    if assembly.assembly_id != motion_result.assembly_id:
        return {}, (), (*motion_issues, _issue(code="KINCHECK-CHECK-ASSEMBLY-MISMATCH", message="Assembly and MotionResult IDs do not match.", object_ids=(assembly.assembly_id, motion_result.assembly_id))), "unknown"
    _, version = require_backend()
    meshes, mesh_issues = _component_meshes(assembly=assembly, asset_root=asset_root, component_ids=component_ids)
    pairs, pair_issues = _normalize_pairs(assembly=assembly, meshes=meshes, component_pairs=component_pairs, excluded_pairs=excluded_pairs)
    return meshes, pairs, (*motion_issues, *mesh_issues, *pair_issues), version


def _prepare_envelope_components(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    component_ids: Sequence[str],
    asset_root: str | Path | None,
) -> tuple[dict[str, MeshModel], tuple[SimIssue, ...], str]:
    issues = list(_motion_result_issues(motion_result))
    if assembly.assembly_id != motion_result.assembly_id:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-ASSEMBLY-MISMATCH",
                message="Assembly and MotionResult IDs do not match.",
                object_ids=(assembly.assembly_id, motion_result.assembly_id),
            )
        )
        return {}, tuple(issues), "unknown"
    _, version = require_backend()
    known = {component.component_id for component in assembly.components}
    unknown = tuple(sorted(set(component_ids) - known))
    if unknown:
        issues.append(
            _issue(
                code="KINCHECK-CLEARANCE-COMPONENT-NOT-FOUND",
                message="A requested motion-envelope Component does not exist.",
                object_ids=unknown,
            )
        )
    meshes, mesh_issues = _component_meshes(
        assembly=assembly,
        asset_root=asset_root,
        component_ids=component_ids,
    )
    return meshes, (*issues, *mesh_issues), version


def check_interference(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    component_pairs: Sequence[Sequence[str]] | None = None,
    excluded_pairs: Sequence[Sequence[str]] = (),
    penetration_tolerance_m: float = 0.0,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    sampling_scope: SamplingScope = "motion_result",
    max_sample_period_s: float | None = None,
    asset_root: str | Path | None = None,
) -> ClearanceReport:
    try:
        _validate_query_parameters(penetration_tolerance_m=penetration_tolerance_m, sampling_scope=sampling_scope)
        require_backend()
        requested_mesh_ids = _requested_pair_component_ids(component_pairs)
        meshes, pairs, preparation_issues, backend_version = _prepare(assembly=assembly, motion_result=motion_result, component_pairs=component_pairs, excluded_pairs=excluded_pairs, asset_root=asset_root, sampling_scope=sampling_scope, component_ids=requested_mesh_ids)
        if not pairs:
            return _base_report(operation="interference", issues=preparation_issues, sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0, backend_version=backend_version, metadata={"component_pairs": ()})
        component_ids = tuple(sorted({item for pair in pairs for item in pair}))
        samples = _motion_samples(motion_result=motion_result, component_ids=component_ids, sampling_scope=sampling_scope)
        selected = _select_samples(samples, start_time_s=start_time_s, end_time_s=end_time_s)
        spacing_issues = _check_sample_spacing(tuple(item[0] for item in selected), max_sample_period_s)
        events: list[InterferenceEvent] = []
        maximum_depth = 0.0
        for time_s, poses in selected:
            for component_a_id, component_b_id in pairs:
                collided, signed, point_a, point_b = query_pair(meshes[component_a_id], meshes[component_b_id], poses[component_a_id], poses[component_b_id])
                if collided and -signed > penetration_tolerance_m:
                    events.append(InterferenceEvent(component_a_id=component_a_id, component_b_id=component_b_id, time_s=time_s, penetration_depth_m=-signed, position_m=point_a))
                    maximum_depth = max(maximum_depth, -signed)
        selected_times = tuple(item[0] for item in selected)
        return _base_report(operation="interference", issues=(*preparation_issues, *spacing_issues), sampling_scope=sampling_scope, sampling_period_s=_sampling_period(selected_times), checked_pairs=len(pairs), checked_samples=len(selected), events=events, backend_version=backend_version, maximum_penetration_depth_m=maximum_depth, metadata={"component_pairs": pairs, "checked_sample_times_s": selected_times, "checked_start_time_s": selected_times[0], "checked_end_time_s": selected_times[-1]})
    except BackendCapabilityError:
        raise
    except (FileNotFoundError, KeyError, RuntimeError, TypeError, ValueError, OSError) as cause:
        issue = _query_failure_issue(cause)
        return _base_report(operation="interference", issues=(issue,), sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0)


def measure_minimum_clearance(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    component_pairs: Sequence[Sequence[str]] | None = None,
    excluded_pairs: Sequence[Sequence[str]] = (),
    minimum_allowed_clearance_m: float | None = None,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    sampling_scope: SamplingScope = "motion_result",
    max_sample_period_s: float | None = None,
    asset_root: str | Path | None = None,
) -> ClearanceReport:
    try:
        _validate_query_parameters(minimum_allowed_clearance_m=minimum_allowed_clearance_m, sampling_scope=sampling_scope)
        require_backend()
        requested_mesh_ids = _requested_pair_component_ids(component_pairs)
        meshes, pairs, preparation_issues, backend_version = _prepare(assembly=assembly, motion_result=motion_result, component_pairs=component_pairs, excluded_pairs=excluded_pairs, asset_root=asset_root, sampling_scope=sampling_scope, component_ids=requested_mesh_ids)
        if not pairs:
            return _base_report(operation="minimum_clearance", issues=preparation_issues, sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0, backend_version=backend_version, minimum_allowed_clearance_m=minimum_allowed_clearance_m, metadata={"component_pairs": ()})
        component_ids = tuple(sorted({item for pair in pairs for item in pair}))
        samples = _motion_samples(motion_result=motion_result, component_ids=component_ids, sampling_scope=sampling_scope)
        selected = _select_samples(samples, start_time_s=start_time_s, end_time_s=end_time_s)
        spacing_issues = _check_sample_spacing(tuple(item[0] for item in selected), max_sample_period_s)
        records: list[MinimumClearance] = []
        for component_a_id, component_b_id in pairs:
            pair_values = []
            for time_s, poses in selected:
                collided, signed, point_a, point_b = query_pair(meshes[component_a_id], meshes[component_b_id], poses[component_a_id], poses[component_b_id])
                pair_values.append(MinimumClearance(component_a_id=component_a_id, component_b_id=component_b_id, minimum_clearance_m=signed, time_s=time_s, closest_point_a_m=point_a, closest_point_b_m=point_b, sampling_scope=sampling_scope))
            if pair_values:
                records.append(min(pair_values, key=lambda item: (item.minimum_clearance_m, item.time_s)))
        selected_times = tuple(item[0] for item in selected)
        return _base_report(operation="minimum_clearance", issues=(*preparation_issues, *spacing_issues), sampling_scope=sampling_scope, sampling_period_s=_sampling_period(selected_times), checked_pairs=len(pairs), checked_samples=len(selected), measurements=records, backend_version=backend_version, minimum_allowed_clearance_m=minimum_allowed_clearance_m, metadata={"component_pairs": pairs, "checked_sample_times_s": selected_times, "checked_start_time_s": selected_times[0], "checked_end_time_s": selected_times[-1]})
    except BackendCapabilityError:
        raise
    except (FileNotFoundError, KeyError, RuntimeError, TypeError, ValueError, OSError) as cause:
        issue = _query_failure_issue(cause)
        return _base_report(operation="minimum_clearance", issues=(issue,), sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0)


def create_motion_envelope(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    component_ids: Sequence[str] | None = None,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    sampling_scope: SamplingScope = "motion_result",
    asset_root: str | Path | None = None,
) -> ClearanceReport:
    try:
        _validate_query_parameters(sampling_scope=sampling_scope)
        require_backend()
        requested = (
            tuple(sorted(component.component_id for component in assembly.components))
            if component_ids is None
            else tuple(sorted({str(component_id) for component_id in component_ids}))
        )
        if not requested:
            return _base_report(
                operation="motion_envelope",
                issues=(
                    _issue(
                        code="KINCHECK-CLEARANCE-COMPONENT-SELECTION-EMPTY",
                        message="At least one Component must be selected for a motion envelope.",
                    ),
                ),
                sampling_scope=sampling_scope,
                sampling_period_s=0.0,
                checked_pairs=0,
                checked_samples=0,
                metadata={"component_ids": ()},
            )
        meshes, preparation_issues, backend_version = _prepare_envelope_components(
            assembly=assembly,
            motion_result=motion_result,
            component_ids=requested,
            asset_root=asset_root,
        )
        available = tuple(component_id for component_id in requested if component_id in meshes)
        if not available:
            return _base_report(operation="motion_envelope", issues=preparation_issues, sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0, backend_version=backend_version, metadata={"component_ids": (), "requested_component_ids": requested})
        samples = _motion_samples(motion_result=motion_result, component_ids=available, sampling_scope=sampling_scope)
        selected = _select_samples(samples, start_time_s=start_time_s, end_time_s=end_time_s)
        envelopes: list[MotionEnvelope] = []
        for component_id in available:
            mesh = meshes[component_id]
            points = []
            sample_bounds: list[EnvelopeSample] = []
            for time_s, poses in selected:
                pose = poses[component_id]
                rotation = np.column_stack([np.asarray(rotate_vector(pose=pose, vector=axis)) for axis in ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))])
                transformed = mesh.vertices @ rotation.T + np.asarray(pose.position_m)
                points.append(transformed)
                sample_bounds.append(EnvelopeSample(time_s=time_s, world_min_position_m=tuple(np.min(transformed, axis=0)), world_max_position_m=tuple(np.max(transformed, axis=0))))
            all_points = np.vstack(points)
            envelopes.append(MotionEnvelope(component_id=component_id, world_min_position_m=tuple(np.min(all_points, axis=0)), world_max_position_m=tuple(np.max(all_points, axis=0)), sample_times_s=tuple(item[0] for item in selected), sample_bounds=tuple(sample_bounds), mesh_vertex_count=mesh.vertex_count, mesh_path=str(mesh.path), mesh_sha256=mesh.sha256, mesh_triangle_count=mesh.triangle_count, backend_id="python-fcl", sampling_scope=sampling_scope))
        selected_times = tuple(item[0] for item in selected)
        return _base_report(operation="motion_envelope", issues=preparation_issues, sampling_scope=sampling_scope, sampling_period_s=_sampling_period(selected_times), checked_pairs=0, checked_samples=len(selected), envelopes=envelopes, backend_version=backend_version, metadata={"component_ids": available, "requested_component_ids": requested, "checked_sample_times_s": selected_times, "checked_start_time_s": selected_times[0], "checked_end_time_s": selected_times[-1]})
    except BackendCapabilityError:
        raise
    except (FileNotFoundError, KeyError, RuntimeError, TypeError, ValueError, OSError) as cause:
        issue = _query_failure_issue(cause)
        return _base_report(operation="motion_envelope", issues=(issue,), sampling_scope=sampling_scope, sampling_period_s=0.0, checked_pairs=0, checked_samples=0)


def check_envelope_interference(
    *,
    first: ClearanceReport,
    second: ClearanceReport,
) -> ClearanceReport:
    if not isinstance(first, ClearanceReport) or not isinstance(second, ClearanceReport):
        raise GeometryCheckError(
            code="KINCHECK-CLEARANCE-ENVELOPE-INPUT-INVALID",
            message="Envelope interference requires two ClearanceReport inputs.",
            object_ids=(type(first).__name__, type(second).__name__),
            suggested_actions=("Create two motion-envelope reports before comparing them.",),
            operation="check_envelope_interference",
        )
    if first.operation != "motion_envelope" or second.operation != "motion_envelope":
        raise GeometryCheckError(
            code="KINCHECK-CLEARANCE-ENVELOPE-INPUT-INVALID",
            message="Envelope interference requires two motion-envelope reports.",
            evidence=(
                Evidence(key="first_operation", actual=first.operation, expected="motion_envelope"),
                Evidence(key="second_operation", actual=second.operation, expected="motion_envelope"),
            ),
            suggested_actions=("Create two motion-envelope reports before comparing them.",),
            operation="check_envelope_interference",
        )
    issues: list[SimIssue] = []
    if not first.passed or not second.passed:
        issues.extend(first.issues)
        issues.extend(second.issues)
        issues.append(_issue(code="KINCHECK-CLEARANCE-ENVELOPE-INPUT-FAILED", message="An input motion-envelope report failed; envelope comparison cannot produce a safety pass."))
        return _base_report(operation="motion_envelope", issues=tuple(issues), sampling_scope=first.sampling_scope, sampling_period_s=max(first.sampling_period_s, second.sampling_period_s), checked_pairs=0, checked_samples=min(first.checked_sample_count, second.checked_sample_count), metadata={"overlaps": (), "confirmed_mesh_interference": False, "input_reports_failed": True})
    if not first.envelopes or not second.envelopes:
        return _base_report(operation="motion_envelope", issues=(_issue(code="KINCHECK-CLEARANCE-ENVELOPE-EMPTY", message="An input motion-envelope report contains no component envelopes."),), sampling_scope=first.sampling_scope, sampling_period_s=max(first.sampling_period_s, second.sampling_period_s), checked_pairs=0, checked_samples=min(first.checked_sample_count, second.checked_sample_count), metadata={"overlaps": (), "confirmed_mesh_interference": False})
    overlaps: list[dict[str, Any]] = []
    for left in first.envelopes:
        for right in second.envelopes:
            if all(
                left_min <= right_max
                for left_min, right_max in zip(
                    left.world_min_position_m, right.world_max_position_m
                )
            ) and all(
                right_min <= left_max
                for right_min, left_max in zip(
                    right.world_min_position_m, left.world_max_position_m
                )
            ):
                overlaps.append({"component_a_id": left.component_id, "component_b_id": right.component_id, "kind": "envelope_overlap"})
    if overlaps:
        issues.append(_issue(code="KINCHECK-CLEARANCE-ENVELOPE-OVERLAP", message="Motion envelopes overlap; run exact mesh interference for confirmation.", object_ids=tuple(sorted({item["component_a_id"] for item in overlaps} | {item["component_b_id"] for item in overlaps}))))
    return _base_report(operation="motion_envelope", issues=issues, sampling_scope=first.sampling_scope, sampling_period_s=min(first.sampling_period_s, second.sampling_period_s), checked_pairs=0, checked_samples=min(first.checked_sample_count, second.checked_sample_count), metadata={"overlaps": overlaps, "confirmed_mesh_interference": False})


def write_motion_envelope(*, report: ClearanceReport, path: str | Path) -> None:
    if not isinstance(report, ClearanceReport) or report.operation != "motion_envelope":
        raise GeometryCheckError(
            code="KINCHECK-CLEARANCE-ENVELOPE-INPUT-INVALID",
            message="Writing a motion envelope requires a motion-envelope report.",
            evidence=(Evidence(key="report_type", actual=type(report).__name__),),
            suggested_actions=("Pass the ClearanceReport returned by create_motion_envelope().",),
            operation="write_motion_envelope",
        )
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "kincheck.motion-envelope/1.0",
        "units": {"length": "m", "time": "s"},
        "report": report.to_dict(),
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "ClearanceReport",
    "EnvelopeSample",
    "MinimumClearance",
    "MotionEnvelope",
    "SamplingScope",
    "check_envelope_interference",
    "check_interference",
    "create_motion_envelope",
    "measure_minimum_clearance",
    "write_motion_envelope",
]
