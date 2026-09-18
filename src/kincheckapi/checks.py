"""Backend-independent checks for assembly and motion results.

Checks consume already-authored models and already-solved motion facts.  They
never start a backend, mutate an input, or infer intent from display names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from statistics import median, pstdev
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence, TYPE_CHECKING

from .assembly import AssemblyModel
from .diagnostics import AgentReadableResult, DiagnosticReport, Evidence, Severity, SimIssue
from .errors import BackendCapabilityError
from .result import ConstraintEquationResidual, ConstraintResidual, JointTrajectory, MotionResult
from .pose import Pose, orientation_error_rad
from .trajectory_checks import (
    limit_events_in_window,
    normalize_position_bounds,
    trajectory_window_metrics,
)
from .integrity import (
    AssemblyIntegrityReport,
    ContainmentRelation,
    IntegrityRelationResult,
    check_assembly_integrity,
)

if TYPE_CHECKING:
    from .scenario import Scenario


CheckType = Literal[
    "constraint_residuals",
    "constraint_equation_residuals",
    "joint_limits",
    "transmission_ratio",
    "pose_target",
    "trajectory",
    "interference",
    "minimum_clearance",
    "motion_envelope",
    "driver_tracking",
    "path_tracking",
    "planar_tracking",
    "start_stop_reversal",
    "periodic_motion",
    "synchronization",
    "continuous_interference",
]
RatioMeasurement = Literal[
    "angular_velocity",
    "linear_velocity",
    "angular_displacement",
    "linear_displacement",
    "angular_to_linear_velocity",
    "angular_to_linear_displacement",
]
Direction = Literal["same", "opposite"]


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        return [_json_value(item) for item in sorted(value, key=repr)]
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return _json_value(value.to_dict())
    return repr(value)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    def freeze_item(item: Any) -> Any:
        if isinstance(item, Mapping):
            return MappingProxyType(
                {str(key): freeze_item(child) for key, child in item.items()}
            )
        if isinstance(item, (tuple, list)):
            return tuple(freeze_item(child) for child in item)
        if isinstance(item, (set, frozenset)):
            return frozenset(freeze_item(child) for child in item)
        return item

    return MappingProxyType({str(key): freeze_item(item) for key, item in value.items()})


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckReport(AgentReadableResult):
    """One deterministic, machine-readable verification outcome."""

    check_id: str
    check_type: str
    passed: bool
    severity: Severity
    evidence: tuple[Evidence, ...] = ()
    issues: tuple[SimIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise ValueError("check_id must be a non-empty string")
        if not isinstance(self.check_type, str) or not self.check_type.strip():
            raise ValueError("check_type must be a non-empty string")
        if self.severity not in {"info", "warning", "error"}:
            raise ValueError("severity must be info, warning, or error")
        evidence = tuple(self.evidence)
        issues = tuple(self.issues)
        if any(not isinstance(item, Evidence) for item in evidence):
            raise TypeError("evidence must contain Evidence values")
        if any(not isinstance(item, SimIssue) for item in issues):
            raise TypeError("issues must contain SimIssue values")
        if self.passed and any(item.severity == "error" for item in issues):
            raise ValueError("a passed check cannot contain an error issue")
        if self.passed and self.severity == "error":
            raise ValueError("a passed check cannot have error severity")
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def status(self) -> str:
        value = self.metadata.get("status")
        if value == "capability_failed":
            return "capability_failed"
        return "passed" if self.passed else "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "check_id": self.check_id,
            "check_type": self.check_type,
            "operation": self.check_type,
            "status": self.status,
            "passed": self.passed,
            "severity": self.severity,
            "evidence": [item.to_dict() for item in self.evidence],
            "issues": [item.to_dict() for item in self.issues],
            "metadata": _json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckSpec:
    """Explicit instruction consumed by :func:`run_checks`."""

    check_id: str
    check_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise ValueError("check_id must be a non-empty string")
        if not isinstance(self.check_type, str) or not self.check_type.strip():
            raise ValueError("check_type must be a non-empty string")
        object.__setattr__(self, "parameters", _freeze(self.parameters))

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_type": self.check_type,
            "parameters": _json_value(self.parameters),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckSuiteReport(AgentReadableResult):
    """Ordered aggregate returned by :func:`run_checks`."""

    reports: tuple[CheckReport, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        reports = tuple(self.reports)
        if any(not isinstance(item, CheckReport) for item in reports):
            raise TypeError("reports must contain CheckReport values")
        if len({item.check_id for item in reports}) != len(reports):
            raise ValueError("reports must have unique check IDs")
        object.__setattr__(self, "reports", reports)
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.reports)

    @property
    def status(self) -> str:
        if any(item.status == "capability_failed" for item in self.reports):
            return "capability_failed"
        return "passed" if self.passed else "failed"

    @property
    def issues(self) -> tuple[SimIssue, ...]:
        return tuple(issue for report in self.reports for issue in report.issues)

    @property
    def check_results(self) -> tuple[CheckReport, ...]:
        """Compatibility alias for callers using the design terminology."""

        return self.reports

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "passed": self.passed,
            "operation": "run_checks",
            "status": self.status,
            "reports": [item.to_dict() for item in self.reports],
            "issues": [item.to_dict() for item in self.issues],
            "metadata": _json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class DriverTrackingReport(AgentReadableResult):
    """Acceptance evidence comparing declared driver targets with actual samples."""
    passed: bool
    joint_id: str
    mode: str
    maximum_absolute_error: float
    mean_absolute_error: float
    rms_error: float
    overshoot: float
    undertracking: float = 0.0
    settling_time_s: float | None
    valid_sample_count: int
    first_failure_time_s: float | None
    tolerance: float
    issues: tuple[SimIssue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {**self.diagnostic_trace(), "operation": "check_driver_tracking", "status": "passed" if self.passed else "failed", "passed": self.passed, "joint_id": self.joint_id, "mode": self.mode, "maximum_absolute_error": self.maximum_absolute_error, "mean_absolute_error": self.mean_absolute_error, "rms_error": self.rms_error, "overshoot": self.overshoot, "undertracking": self.undertracking, "settling_time_s": self.settling_time_s, "valid_sample_count": self.valid_sample_count, "first_failure_time_s": self.first_failure_time_s, "tolerance": self.tolerance, "issues": [i.to_dict() for i in self.issues]}


def _issue(
    *,
    code: str,
    stage: str,
    message: str,
    object_ids: Sequence[str] = (),
    evidence: Sequence[Evidence] = (),
    failure_time_s: float | None = None,
    suggested_actions: Sequence[str] = (),
) -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage=stage,
        message=message,
        object_ids=tuple(object_ids),
        evidence=tuple(evidence),
        failure_time_s=failure_time_s,
        suggested_actions=tuple(suggested_actions),
    )


def _report(
    *,
    check_id: str,
    check_type: str,
    evidence: Sequence[Evidence] = (),
    issues: Sequence[SimIssue] = (),
    metadata: Mapping[str, Any] | None = None,
) -> CheckReport:
    normalized_issues = tuple(issues)
    passed = not any(item.severity == "error" for item in normalized_issues)
    normalized_metadata = dict(metadata or {})
    if any(item.code == "KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE" for item in normalized_issues):
        normalized_metadata.setdefault("motion_result_status", "partial")
    return CheckReport(
        check_id=check_id,
        check_type=check_type,
        passed=passed,
        severity="info" if passed else "error",
        evidence=tuple(evidence),
        issues=normalized_issues,
        metadata=normalized_metadata,
    )


def _motion_result_issues(motion_result: MotionResult) -> tuple[SimIssue, ...]:
    """Return the common completeness gate for every result consumer."""

    if motion_result.status in {"completed", "completed_with_warnings"}:
        return ()
    return (
        _issue(
            code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE",
            stage="checks.motion_result",
            message=(
                "The MotionResult is partial; recorded evidence may be inspected, "
                "but it cannot produce a complete verification pass."
            ),
            object_ids=(motion_result.scenario_id, motion_result.assembly_id),
            evidence=(
                Evidence(
                    key="motion_result_status",
                    actual=motion_result.status,
                    expected="completed or completed_with_warnings",
                ),
                Evidence(key="sample_count", actual=len(motion_result.sample_times_s)),
                Evidence(
                    key="time_range_s",
                    actual=(motion_result.start_time_s, motion_result.end_time_s),
                    unit="s",
                ),
            ),
            failure_time_s=motion_result.end_time_s,
            suggested_actions=(
                "Resolve the motion failure and rerun the check with a complete MotionResult.",
            ),
        ),
    )


def _valid_window(
    *, start_time_s: float | None, end_time_s: float | None, stage: str
) -> tuple[float | None, float | None, tuple[SimIssue, ...]]:
    issues: list[SimIssue] = []
    for name, value in (("start_time_s", start_time_s), ("end_time_s", end_time_s)):
        if value is not None and not math.isfinite(value):
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-TIME-WINDOW-INVALID",
                    stage=stage,
                    message="Check time bounds must be finite.",
                    evidence=(Evidence(key=name, actual=value, expected="finite"),),
                )
            )
    if (
        not issues
        and start_time_s is not None
        and end_time_s is not None
        and start_time_s > end_time_s
    ):
        issues.append(
            _issue(
                code="KINCHECK-CHECK-TIME-WINDOW-INVALID",
                stage=stage,
                message="Check start time must not be after its end time.",
                evidence=(
                    Evidence(key="start_time_s", actual=start_time_s),
                    Evidence(key="end_time_s", actual=end_time_s),
                ),
            )
        )
    return start_time_s, end_time_s, tuple(issues)


def _in_window(
    time_s: float, *, start_time_s: float | None, end_time_s: float | None
) -> bool:
    return (start_time_s is None or time_s >= start_time_s) and (
        end_time_s is None or time_s <= end_time_s
    )


def check_driver_tracking(
    *, motion_result: MotionResult, scenario: "Scenario", joint_id: str,
    tolerance: float = 1e-3, start_time_s: float | None = None,
    end_time_s: float | None = None, check_id: str = "driver_tracking",
) -> DriverTrackingReport:
    """Compare one declared position/speed driver to the recorded trajectory."""
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    if not math.isfinite(tolerance) or tolerance < 0:
        issues.append(_issue(code="KINCHECK-CHECK-DRIVER-TOLERANCE-INVALID", stage="checks.driver_tracking", message="Driver tolerance must be finite and non-negative.", object_ids=(joint_id,)))
    drivers = [d for d in (*scenario.position_drivers, *scenario.speed_drivers) if d.joint_id == joint_id]
    trajectory = motion_result.get_joint_trajectory(joint_id=joint_id)
    if len(drivers) != 1 or trajectory is None:
        issues.append(_issue(code="KINCHECK-CHECK-DRIVER-NOT-FOUND", stage="checks.driver_tracking", message="Exactly one declared driver and one recorded trajectory are required.", object_ids=(joint_id,)))
        return DriverTrackingReport(passed=False, joint_id=joint_id, mode="unknown", maximum_absolute_error=float("inf"), mean_absolute_error=float("inf"), rms_error=float("inf"), overshoot=float("inf"), undertracking=float("inf"), settling_time_s=None, valid_sample_count=0, first_failure_time_s=None, tolerance=tolerance, issues=tuple(issues))
    driver = drivers[0]
    mode = "position" if hasattr(driver, "profile") and driver in scenario.position_drivers else "speed"
    def target(time: float) -> float:
        pts = driver.profile.points
        interval = getattr(driver, "active_interval_s", None)
        if interval is not None and (time < interval[0] or time > interval[1]):
            return 0.0
        boundary = getattr(getattr(scenario, "profile_boundary", "hold"), "value", getattr(scenario, "profile_boundary", "hold"))
        if time < pts[0].time_s:
            return 0.0 if boundary == "zero" else pts[0].value
        if time == pts[0].time_s:
            return pts[0].value
        if time >= pts[-1].time_s: return 0.0 if boundary == "zero" else pts[-1].value
        for left, right in zip(pts, pts[1:]):
            if left.time_s <= time <= right.time_s:
                if driver.profile.interpolation.value == "step": return left.value
                f = (time-left.time_s)/(right.time_s-left.time_s)
                return left.value + f*(right.value-left.value)
        return pts[-1].value
    actuals = trajectory.positions if mode == "position" else trajectory.velocities
    pairs = [(t, target(t), a) for t, a in zip(trajectory.times_s, actuals) if _in_window(t, start_time_s=start_time_s, end_time_s=end_time_s)]
    errors = [a - b for _, b, a in pairs]
    abs_errors = [abs(e) for e in errors]
    first_failure = next((t for (t, _, _), e in zip(pairs, abs_errors) if e > tolerance), None)
    settling = None
    for index, ((t, _, _), e) in enumerate(zip(pairs, abs_errors)):
        if e <= tolerance and all(later <= tolerance for later in abs_errors[index:]): settling = t; break
    maximum = max(abs_errors, default=float("inf")); mean = sum(abs_errors)/len(abs_errors) if abs_errors else float("inf")
    rms = math.sqrt(sum(e*e for e in errors)/len(errors)) if errors else float("inf")
    overshoot_values = [
        (max(0.0, a - b) if b >= 0.0 else max(0.0, b - a))
        if b != 0.0 else abs(a)
        for _, b, a in pairs
    ]
    undertracking_values = [
        (max(0.0, b - a) if b >= 0.0 else max(0.0, a - b))
        for _, b, a in pairs
    ]
    overshoot = max(overshoot_values, default=float("inf"))
    undertracking = max(undertracking_values, default=float("inf"))
    if not pairs: issues.append(_issue(code="KINCHECK-CHECK-DRIVER-INSUFFICIENT-SAMPLES", stage="checks.driver_tracking", message="No samples exist in the requested interval.", object_ids=(joint_id,)))
    elif first_failure is not None: issues.append(_issue(code="KINCHECK-CHECK-DRIVER-TRACKING-FAILED", stage="checks.driver_tracking", message="Driver tracking error exceeds tolerance.", object_ids=(joint_id,), failure_time_s=first_failure, evidence=(Evidence(key="maximum_absolute_error", actual=maximum, expected=f"<= {tolerance}"),)))
    return DriverTrackingReport(passed=not issues, joint_id=joint_id, mode=mode, maximum_absolute_error=maximum, mean_absolute_error=mean, rms_error=rms, overshoot=overshoot, undertracking=undertracking, settling_time_s=settling, valid_sample_count=len(pairs), first_failure_time_s=first_failure, tolerance=tolerance, issues=tuple(issues))


def check_constraint_residuals(
    *,
    motion_result: MotionResult,
    constraint_ids: Sequence[str] | None = None,
    position_tolerance_m: float = 1e-6,
    orientation_tolerance_rad: float = 1e-6,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    include_closures: bool = True,
    check_id: str = "constraint_residuals",
) -> CheckReport:
    """Check sampled constraint and, by default, closure residuals."""

    stage = "checks.constraint_residuals"
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(
        start_time_s=start_time_s, end_time_s=end_time_s, stage=stage
    )
    issues.extend(window_issues)
    for key, value in (
        ("position_tolerance_m", position_tolerance_m),
        ("orientation_tolerance_rad", orientation_tolerance_rad),
    ):
        if not math.isfinite(value) or value < 0.0:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-CONSTRAINT-TOLERANCE-INVALID",
                    stage=stage,
                    message="Constraint tolerances must be finite and non-negative.",
                    evidence=(Evidence(key=key, actual=value, expected=">= 0"),),
                )
            )
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-CONSTRAINT-TOLERANCE-INVALID",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="constraint_residuals",
            issues=issues,
            metadata={
                "position_tolerance_m": position_tolerance_m,
                "orientation_tolerance_rad": orientation_tolerance_rad,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
            },
        )

    selected_ids = tuple(dict.fromkeys(constraint_ids or ()))
    closure_ids = {item.constraint_id for item in motion_result.closure_residuals}
    base_records = tuple(
        item
        for item in motion_result.constraint_residuals
        if include_closures or item.constraint_id not in closure_ids
    )
    if include_closures:
        records_by_key = {
            (item.constraint_id, item.time_s): item for item in base_records
        }
        records_by_key.update(
            {
                (item.constraint_id, item.time_s): item
                for item in motion_result.closure_residuals
            }
        )
        records: tuple[ConstraintResidual, ...] = tuple(records_by_key.values())
    else:
        records = base_records
    if selected_ids:
        records = tuple(item for item in records if item.constraint_id in selected_ids)
        present = {item.constraint_id for item in records}
        missing = tuple(item for item in selected_ids if item not in present)
        if missing:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-CONSTRAINT-NOT-FOUND",
                    stage=stage,
                    message="No residual samples were found for requested constraints.",
                    object_ids=missing,
                    suggested_actions=("Request residual output for these constraints.",),
                )
            )
    records = tuple(
        item
        for item in records
        if _in_window(
            item.time_s, start_time_s=start_time_s, end_time_s=end_time_s
        )
    )
    if not records:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-CONSTRAINT-INSUFFICIENT-SAMPLES",
                stage=stage,
                message="No constraint residual samples exist in the requested interval.",
                object_ids=selected_ids,
                suggested_actions=("Record residuals or widen the check time window.",),
            )
        )

    by_id: dict[str, list[ConstraintResidual]] = {}
    for item in records:
        by_id.setdefault(item.constraint_id, []).append(item)
    for constraint_id, samples in sorted(by_id.items()):
        violating = tuple(
            item
            for item in samples
            if item.position_residual_m > position_tolerance_m
            or item.orientation_residual_rad > orientation_tolerance_rad
        )
        if not violating:
            continue
        first = min(violating, key=lambda item: item.time_s)
        issues.append(
            _issue(
                code="KINCHECK-CHECK-CONSTRAINT-RESIDUAL-EXCEEDED",
                stage=stage,
                message="A sampled constraint residual exceeds its tolerance.",
                object_ids=(constraint_id,),
                failure_time_s=first.time_s,
                evidence=(
                    Evidence(
                        key="maximum_position_residual_m",
                        actual=max(item.position_residual_m for item in samples),
                        expected=f"<= {position_tolerance_m}",
                        unit="m",
                    ),
                    Evidence(
                        key="maximum_orientation_residual_rad",
                        actual=max(item.orientation_residual_rad for item in samples),
                        expected=f"<= {orientation_tolerance_rad}",
                        unit="rad",
                    ),
                    Evidence(key="violating_sample_count", actual=len(violating)),
                ),
                suggested_actions=("Inspect the constraint and the first failing pose.",),
            )
        )

    evidence = (
        Evidence(key="sample_count", actual=len(records)),
        Evidence(key="constraint_count", actual=len(by_id)),
        Evidence(
            key="maximum_position_residual_m",
            actual=max((item.position_residual_m for item in records), default=0.0),
            expected=f"<= {position_tolerance_m}",
            unit="m",
        ),
        Evidence(
            key="maximum_orientation_residual_rad",
            actual=max((item.orientation_residual_rad for item in records), default=0.0),
            expected=f"<= {orientation_tolerance_rad}",
            unit="rad",
        ),
    )
    return _report(
        check_id=check_id,
        check_type="constraint_residuals",
        evidence=evidence,
        issues=issues,
        metadata={
            "constraint_ids": selected_ids,
            "checked_constraint_ids": tuple(sorted(by_id)),
            "position_tolerance_m": position_tolerance_m,
            "orientation_tolerance_rad": orientation_tolerance_rad,
            "start_time_s": start_time_s,
            "end_time_s": end_time_s,
            "include_closures": include_closures,
        },
    )


def check_constraint_equation_residuals(
    *,
    motion_result: MotionResult,
    constraint_ids: Sequence[str] | None = None,
    equation_types: Sequence[Literal["gear", "belt", "rack_pinion", "coupling"]] | None = None,
    linear_tolerance_m: float = 1e-8,
    angular_tolerance_rad: float = 1e-8,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    disabled_constraint_ids: Sequence[str] = (),
    check_id: str = "constraint_equation_residuals",
) -> CheckReport:
    """Check signed gear, belt, rack-pinion, and coupling residual samples."""

    stage = "checks.constraint_equation_residuals"
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(
        start_time_s=start_time_s, end_time_s=end_time_s, stage=stage
    )
    issues.extend(window_issues)
    tolerances = {"m": linear_tolerance_m, "rad": angular_tolerance_rad}
    for key, value, unit in (
        ("linear_tolerance_m", linear_tolerance_m, "m"),
        ("angular_tolerance_rad", angular_tolerance_rad, "rad"),
    ):
        if not math.isfinite(value) or value < 0.0:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-EQUATION-TOLERANCE-INVALID",
                    stage=stage,
                    message="Equation-residual tolerances must be finite and non-negative.",
                    evidence=(Evidence(key=key, actual=value, expected=">= 0", unit=unit),),
                )
            )
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-EQUATION-TOLERANCE-INVALID",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="constraint_equation_residuals",
            issues=issues,
            metadata={
                "linear_tolerance_m": linear_tolerance_m,
                "angular_tolerance_rad": angular_tolerance_rad,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
            },
        )

    selected_ids = tuple(dict.fromkeys(constraint_ids or ()))
    disabled_ids = tuple(dict.fromkeys(disabled_constraint_ids))
    disabled = set(disabled_ids)
    selected_types = tuple(dict.fromkeys(equation_types or ()))
    invalid_types = tuple(
        item
        for item in selected_types
        if item not in {"gear", "belt", "rack_pinion", "coupling"}
    )
    if invalid_types:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-EQUATION-TYPE-INVALID",
                stage=stage,
                message="Equation type filters must be gear, belt, rack_pinion, or coupling.",
                evidence=(
                    Evidence(
                        key="equation_types",
                        actual=invalid_types,
                        expected=("gear", "belt", "rack_pinion", "coupling"),
                    ),
                ),
            )
        )

    records: tuple[ConstraintEquationResidual, ...] = tuple(
        item
        for item in motion_result.constraint_equation_residuals
        if item.constraint_id not in disabled
        and (not selected_ids or item.constraint_id in selected_ids)
        and (not selected_types or item.equation_type in selected_types)
        and _in_window(
            item.time_s, start_time_s=start_time_s, end_time_s=end_time_s
        )
    )
    if selected_ids:
        present = {item.constraint_id for item in records}
        missing = tuple(
            item for item in selected_ids if item not in present and item not in disabled
        )
        if missing:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-EQUATION-CONSTRAINT-NOT-FOUND",
                    stage=stage,
                    message="No equation residual samples were found for requested constraints.",
                    object_ids=missing,
                    suggested_actions=(
                        "Request equation residual output or check the requested time and type filters.",
                    ),
                )
            )
    if not records and not (selected_ids and set(selected_ids) <= disabled):
        issues.append(
            _issue(
                code="KINCHECK-CHECK-EQUATION-INSUFFICIENT-SAMPLES",
                stage=stage,
                message="No equation residual samples exist in the requested interval.",
                object_ids=selected_ids,
                suggested_actions=(
                    "Record gear, belt, rack-pinion, or coupling residuals, or widen the time window.",
                ),
            )
        )

    by_id: dict[str, list[ConstraintEquationResidual]] = {}
    for item in records:
        by_id.setdefault(item.constraint_id, []).append(item)
    violating_records: list[ConstraintEquationResidual] = []
    for constraint_id, samples in sorted(by_id.items()):
        violating = tuple(
            item for item in samples if item.absolute_value > tolerances[item.unit]
        )
        violating_records.extend(violating)
        if not violating:
            continue
        first = min(violating, key=lambda item: item.time_s)
        maximum = max(samples, key=lambda item: item.absolute_value)
        issues.append(
            _issue(
                code="KINCHECK-CHECK-EQUATION-RESIDUAL-EXCEEDED",
                stage=stage,
                message="A sampled constraint equation residual exceeds its tolerance.",
                object_ids=(constraint_id,),
                failure_time_s=first.time_s,
                evidence=(
                    Evidence(
                        key="maximum_absolute_residual",
                        actual=maximum.absolute_value,
                        expected=f"<= {tolerances[maximum.unit]}",
                        unit=maximum.unit,
                    ),
                    Evidence(
                        key="p95_absolute_residual",
                        actual=_percentile(
                            [item.absolute_value for item in samples], 0.95
                        ),
                        unit=maximum.unit,
                    ),
                    Evidence(key="violating_sample_count", actual=len(violating)),
                    Evidence(key="equation_type", actual=maximum.equation_type),
                ),
                suggested_actions=(
                    "Inspect the compiled equation, SI coefficients, and the first failing sample.",
                ),
            )
        )

    by_unit = {
        unit: tuple(item.absolute_value for item in records if item.unit == unit)
        for unit in ("m", "rad")
    }
    evidence = (
        Evidence(key="sample_count", actual=len(records)),
        Evidence(key="constraint_count", actual=len(by_id)),
        Evidence(key="violating_sample_count", actual=len(violating_records)),
        Evidence(
            key="maximum_linear_residual_m",
            actual=max(by_unit["m"], default=0.0),
            expected=f"<= {linear_tolerance_m}",
            unit="m",
        ),
        Evidence(
            key="p95_linear_residual_m",
            actual=_percentile(by_unit["m"], 0.95) if by_unit["m"] else 0.0,
            unit="m",
        ),
        Evidence(
            key="maximum_angular_residual_rad",
            actual=max(by_unit["rad"], default=0.0),
            expected=f"<= {angular_tolerance_rad}",
            unit="rad",
        ),
        Evidence(
            key="p95_angular_residual_rad",
            actual=_percentile(by_unit["rad"], 0.95) if by_unit["rad"] else 0.0,
            unit="rad",
        ),
    )
    return _report(
        check_id=check_id,
        check_type="constraint_equation_residuals",
        evidence=evidence,
        issues=issues,
        metadata={
            "constraint_ids": selected_ids,
            "checked_constraint_ids": tuple(sorted(by_id)),
            "disabled_constraint_ids": disabled_ids,
            "equation_types": selected_types,
            "linear_tolerance_m": linear_tolerance_m,
            "angular_tolerance_rad": angular_tolerance_rad,
            "start_time_s": start_time_s,
            "end_time_s": end_time_s,
        },
    )


def check_joint_limits(
    *,
    assembly: AssemblyModel,
    motion_result: MotionResult,
    joint_ids: Sequence[str] | None = None,
    tolerance: float = 0.0,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    check_id: str = "joint_limits",
) -> CheckReport:
    """Verify sampled joint positions against authored assembly limits."""

    stage = "checks.joint_limits"
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(
        start_time_s=start_time_s, end_time_s=end_time_s, stage=stage
    )
    issues.extend(window_issues)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-JOINT-LIMIT-TOLERANCE-INVALID",
                stage=stage,
                message="Joint-limit tolerance must be finite and non-negative.",
                evidence=(Evidence(key="tolerance", actual=tolerance, expected=">= 0"),),
            )
        )
    if assembly.assembly_id != motion_result.assembly_id:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-ASSEMBLY-MISMATCH",
                stage=stage,
                message="The assembly and motion result IDs do not match.",
                object_ids=(assembly.assembly_id, motion_result.assembly_id),
            )
        )
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-JOINT-LIMIT-TOLERANCE-INVALID",
            "KINCHECK-CHECK-ASSEMBLY-MISMATCH",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="joint_limits",
            issues=issues,
            metadata={
                "tolerance": tolerance,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
            },
        )

    all_joints = {item.joint_id: item for item in assembly.joints}
    selected_ids = tuple(dict.fromkeys(joint_ids or ()))
    if selected_ids:
        missing = tuple(item for item in selected_ids if item not in all_joints)
        if missing:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-JOINT-NOT-FOUND",
                    stage=stage,
                    message="Requested joints do not exist in the assembly.",
                    object_ids=missing,
                )
            )
        no_limit = tuple(
            item
            for item in selected_ids
            if item in all_joints and all_joints[item].limit is None
        )
        if no_limit:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-JOINT-LIMIT-NOT-AUTHORED",
                    stage=stage,
                    message="Requested joints have no authored limit to check.",
                    object_ids=no_limit,
                )
            )
        limited_joints = tuple(
            all_joints[item]
            for item in selected_ids
            if item in all_joints and all_joints[item].limit is not None
        )
    else:
        limited_joints = tuple(item for item in assembly.joints if item.limit is not None)

    sample_count = 0
    checked_count = 0
    trajectories = {
        item.joint_id: item for item in motion_result.joint_trajectories
    }
    for joint in limited_joints:
        trajectory = trajectories.get(joint.joint_id)
        if trajectory is None:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-JOINT-TRAJECTORY-NOT-FOUND",
                    stage=stage,
                    message="The motion result lacks a requested limited-joint trajectory.",
                    object_ids=(joint.joint_id,),
                    suggested_actions=("Record this joint trajectory during solve_motion().",),
                )
            )
            continue
        samples = tuple(
            (time_s, position)
            for time_s, position in zip(trajectory.times_s, trajectory.positions)
            if _in_window(
                time_s, start_time_s=start_time_s, end_time_s=end_time_s
            )
        )
        if not samples:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-JOINT-LIMIT-INSUFFICIENT-SAMPLES",
                    stage=stage,
                    message="No joint samples exist in the requested interval.",
                    object_ids=(joint.joint_id,),
                )
            )
            continue
        checked_count += 1
        sample_count += len(samples)
        assert joint.limit is not None
        violating = tuple(
            item
            for item in samples
            if item[1] < joint.limit.lower - tolerance
            or item[1] > joint.limit.upper + tolerance
        )
        if violating:
            first_time, _ = min(violating, key=lambda item: item[0])
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-JOINT-LIMIT-EXCEEDED",
                    stage=stage,
                    message="A sampled joint position exceeds its authored limit.",
                    object_ids=(joint.joint_id,),
                    failure_time_s=first_time,
                    evidence=(
                        Evidence(
                            key="minimum_position",
                            actual=min(item[1] for item in samples),
                            expected=f">= {joint.limit.lower - tolerance}",
                        ),
                        Evidence(
                            key="maximum_position",
                            actual=max(item[1] for item in samples),
                            expected=f"<= {joint.limit.upper + tolerance}",
                        ),
                        Evidence(key="violating_sample_count", actual=len(violating)),
                    ),
                    suggested_actions=("Inspect the driver profile or authored joint limits.",),
                )
            )

    return _report(
        check_id=check_id,
        check_type="joint_limits",
        evidence=(
            Evidence(key="limited_joint_count", actual=len(limited_joints)),
            Evidence(key="checked_joint_count", actual=checked_count),
            Evidence(key="sample_count", actual=sample_count),
        ),
        issues=issues,
        metadata={
            "joint_ids": selected_ids,
            "checked_joint_ids": tuple(
                joint.joint_id for joint in limited_joints if joint.joint_id in trajectories
            ),
            "tolerance": tolerance,
            "start_time_s": start_time_s,
            "end_time_s": end_time_s,
        },
    )


def _interpolate(
    *, times: Sequence[float], values: Sequence[float], time_s: float
) -> float:
    if time_s <= times[0]:
        return float(values[0])
    if time_s >= times[-1]:
        return float(values[-1])
    low = 0
    high = len(times) - 1
    while high - low > 1:
        middle = (low + high) // 2
        if times[middle] <= time_s:
            low = middle
        else:
            high = middle
    weight = (time_s - times[low]) / (times[high] - times[low])
    return float(values[low] + (values[high] - values[low]) * weight)


def _percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] + (ordered[high] - ordered[low]) * weight


def check_transmission_ratio(
    *,
    motion_result: MotionResult,
    input_joint_id: str,
    output_joint_id: str,
    expected_ratio: float,
    expected_direction: Direction,
    measurement: RatioMeasurement = "angular_velocity",
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    relative_tolerance: float = 1e-3,
    minimum_sample_count: int = 3,
    minimum_valid_fraction: float = 0.8,
    minimum_input_magnitude: float = 1e-9,
    minimum_output_magnitude: float = 1e-12,
    check_id: str = "transmission_ratio",
) -> CheckReport:
    """Compare two explicit joint curves after deterministic time alignment."""

    stage = "checks.transmission_ratio"
    object_ids = (input_joint_id, output_joint_id)
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(
        start_time_s=start_time_s, end_time_s=end_time_s, stage=stage
    )
    issues.extend(window_issues)
    if measurement not in {
        "angular_velocity",
        "linear_velocity",
        "angular_displacement",
        "linear_displacement",
        "angular_to_linear_velocity",
        "angular_to_linear_displacement",
    }:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-RATIO-MEASUREMENT-UNSUPPORTED",
                stage=stage,
                message="Unsupported transmission-ratio measurement.",
                object_ids=object_ids,
                evidence=(Evidence(key="measurement", actual=measurement),),
            )
        )
    for key, value, valid in (
        ("expected_ratio", expected_ratio, math.isfinite(expected_ratio) and expected_ratio > 0.0),
        (
            "relative_tolerance",
            relative_tolerance,
            math.isfinite(relative_tolerance) and relative_tolerance >= 0.0,
        ),
        (
            "minimum_valid_fraction",
            minimum_valid_fraction,
            math.isfinite(minimum_valid_fraction) and 0.0 <= minimum_valid_fraction <= 1.0,
        ),
        (
            "minimum_input_magnitude",
            minimum_input_magnitude,
            math.isfinite(minimum_input_magnitude) and minimum_input_magnitude >= 0.0,
        ),
        (
            "minimum_output_magnitude",
            minimum_output_magnitude,
            math.isfinite(minimum_output_magnitude) and minimum_output_magnitude >= 0.0,
        ),
    ):
        if not valid:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-RATIO-PARAMETER-INVALID",
                    stage=stage,
                    message="A transmission-ratio check parameter is outside its valid range.",
                    object_ids=object_ids,
                    evidence=(Evidence(key=key, actual=value),),
                )
            )
    if expected_direction not in {"same", "opposite"}:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-RATIO-DIRECTION-INVALID",
                stage=stage,
                message="Expected direction must be 'same' or 'opposite'.",
                object_ids=object_ids,
            )
        )
    if not isinstance(minimum_sample_count, int) or minimum_sample_count < 1:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-RATIO-PARAMETER-INVALID",
                stage=stage,
                message="Minimum sample count must be a positive integer.",
                object_ids=object_ids,
                evidence=(Evidence(key="minimum_sample_count", actual=minimum_sample_count),),
            )
        )
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-RATIO-MEASUREMENT-UNSUPPORTED",
            "KINCHECK-CHECK-RATIO-PARAMETER-INVALID",
            "KINCHECK-CHECK-RATIO-DIRECTION-INVALID",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="transmission_ratio",
            issues=issues,
            metadata={
                "input_joint_id": input_joint_id,
                "output_joint_id": output_joint_id,
                "expected_ratio": expected_ratio,
                "expected_direction": expected_direction,
                "measurement": measurement,
            },
        )

    input_trajectory = motion_result.get_joint_trajectory(joint_id=input_joint_id)
    output_trajectory = motion_result.get_joint_trajectory(joint_id=output_joint_id)
    missing = tuple(
        joint_id
        for joint_id, trajectory in (
            (input_joint_id, input_trajectory),
            (output_joint_id, output_trajectory),
        )
        if trajectory is None
    )
    if missing:
        issues.append(
            _issue(
                code="KINCHECK-CHECK-RATIO-TRAJECTORY-NOT-FOUND",
                stage=stage,
                message="The motion result lacks requested joint trajectories.",
                object_ids=missing,
                suggested_actions=("Request both joint trajectories during solve_motion().",),
            )
        )

    candidate_count = 0
    rejected_count = 0
    ratios: list[float] = []
    directions: list[Direction] = []
    effective_start: float | None = None
    effective_end: float | None = None
    can_measure = (
        not any(
            issue.severity == "error"
            and issue.code != "KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE"
            for issue in issues
        )
        and input_trajectory is not None
        and output_trajectory is not None
    )
    if can_measure:
        assert input_trajectory is not None and output_trajectory is not None
        effective_start = max(
            input_trajectory.times_s[0],
            output_trajectory.times_s[0],
            start_time_s if start_time_s is not None else -math.inf,
        )
        effective_end = min(
            input_trajectory.times_s[-1],
            output_trajectory.times_s[-1],
            end_time_s if end_time_s is not None else math.inf,
        )
        if effective_start > effective_end:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-RATIO-NO-TIME-OVERLAP",
                    stage=stage,
                    message="The requested joint trajectories have no common time interval.",
                    object_ids=object_ids,
                )
            )
        else:
            times = sorted(
                {
                    effective_start,
                    effective_end,
                    *(
                        time_s
                        for time_s in input_trajectory.times_s
                        if effective_start <= time_s <= effective_end
                    ),
                    *(
                        time_s
                        for time_s in output_trajectory.times_s
                        if effective_start <= time_s <= effective_end
                    ),
                }
            )
            displacement = measurement.endswith("displacement")
            angular_to_linear = measurement.startswith("angular_to_linear")
            input_values = (
                input_trajectory.positions
                if displacement
                else input_trajectory.velocities
            )
            output_values = (
                output_trajectory.positions
                if displacement
                else output_trajectory.velocities
            )
            input_origin = _interpolate(
                times=input_trajectory.times_s,
                values=input_values,
                time_s=effective_start,
            )
            output_origin = _interpolate(
                times=output_trajectory.times_s,
                values=output_values,
                time_s=effective_start,
            )
            for time_s in times:
                if displacement and time_s == effective_start:
                    continue
                candidate_count += 1
                input_value = _interpolate(
                    times=input_trajectory.times_s,
                    values=input_values,
                    time_s=time_s,
                )
                output_value = _interpolate(
                    times=output_trajectory.times_s,
                    values=output_values,
                    time_s=time_s,
                )
                if displacement:
                    input_value -= input_origin
                    output_value -= output_origin
                if (
                    abs(input_value) < minimum_input_magnitude
                    or abs(output_value) < minimum_output_magnitude
                ):
                    rejected_count += 1
                    continue
                ratios.append(
                    abs(output_value / input_value)
                    if angular_to_linear
                    else abs(input_value / output_value)
                )
                directions.append(
                    "same" if input_value * output_value >= 0.0 else "opposite"
                )

    valid_count = len(ratios)
    valid_fraction = valid_count / candidate_count if candidate_count else 0.0
    measured_ratio = median(ratios) if ratios else None
    relative_errors = (
        [abs(item - expected_ratio) / expected_ratio for item in ratios]
        if ratios and math.isfinite(expected_ratio) and expected_ratio > 0.0
        else []
    )
    median_relative_error = (
        abs(measured_ratio - expected_ratio) / expected_ratio
        if measured_ratio is not None
        and math.isfinite(expected_ratio)
        and expected_ratio > 0.0
        else None
    )
    max_relative_error = max(relative_errors) if relative_errors else None
    p95_relative_error = _percentile(relative_errors, 0.95) if relative_errors else None
    ratio_standard_deviation = pstdev(ratios) if ratios else None
    expected_direction_count = directions.count(expected_direction)
    direction_consistency = (
        expected_direction_count / valid_count if valid_count else 0.0
    )
    measured_direction: Direction | None = None
    if directions:
        measured_direction = (
            "same"
            if directions.count("same") >= directions.count("opposite")
            else "opposite"
        )

    if input_trajectory is not None and output_trajectory is not None and not any(
        issue.code == "KINCHECK-CHECK-RATIO-NO-TIME-OVERLAP" for issue in issues
    ):
        if valid_count < minimum_sample_count or valid_fraction < minimum_valid_fraction:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-RATIO-INSUFFICIENT-SAMPLES",
                    stage=stage,
                    message="Too few valid aligned samples remain for a reliable ratio check.",
                    object_ids=object_ids,
                    evidence=(
                        Evidence(key="valid_sample_count", actual=valid_count, expected=f">= {minimum_sample_count}"),
                        Evidence(key="valid_fraction", actual=valid_fraction, expected=f">= {minimum_valid_fraction}"),
                        Evidence(key="rejected_sample_count", actual=rejected_count),
                    ),
                    suggested_actions=("Widen the time window or lower the explicit magnitude threshold.",),
                )
            )
        elif (
            median_relative_error is not None
            and p95_relative_error is not None
            and (
                median_relative_error > relative_tolerance
                or p95_relative_error > relative_tolerance
            )
        ):
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-RATIO-MISMATCH",
                    stage=stage,
                    message="The measured transmission ratio or its sample variation exceeds tolerance.",
                    object_ids=object_ids,
                    evidence=(
                        Evidence(key="median_ratio", actual=measured_ratio, expected=expected_ratio),
                        Evidence(key="median_relative_error", actual=median_relative_error, expected=f"<= {relative_tolerance}"),
                        Evidence(key="p95_relative_error", actual=p95_relative_error, expected=f"<= {relative_tolerance}"),
                        Evidence(key="max_relative_error", actual=max_relative_error),
                    ),
                    suggested_actions=("Inspect transmission constraints and the selected time interval.",),
                )
            )
        if valid_count and direction_consistency < minimum_valid_fraction:
            issues.append(
                _issue(
                    code="KINCHECK-CHECK-RATIO-DIRECTION-MISMATCH",
                    stage=stage,
                    message="Input and output direction is not consistently as expected.",
                    object_ids=object_ids,
                    evidence=(
                        Evidence(key="measured_direction", actual=measured_direction, expected=expected_direction),
                        Evidence(key="direction_consistency", actual=direction_consistency, expected=f">= {minimum_valid_fraction}"),
                    ),
                )
            )

    unit = (
        "m/rad"
        if measurement == "angular_to_linear_displacement"
        else "(m/s)/(rad/s)"
        if measurement == "angular_to_linear_velocity"
        else
        "rad/s"
        if measurement == "angular_velocity"
        else "m/s"
        if measurement == "linear_velocity"
        else "rad"
        if measurement == "angular_displacement"
        else "m"
    )
    return _report(
        check_id=check_id,
        check_type="transmission_ratio",
        evidence=(
            Evidence(key="measurement", actual=measurement, unit=unit),
            Evidence(key="median_ratio", actual=measured_ratio, expected=expected_ratio),
            Evidence(key="median_relative_error", actual=median_relative_error, expected=f"<= {relative_tolerance}"),
            Evidence(key="max_relative_error", actual=max_relative_error),
            Evidence(key="p95_relative_error", actual=p95_relative_error),
            Evidence(key="ratio_standard_deviation", actual=ratio_standard_deviation),
            Evidence(key="measured_direction", actual=measured_direction, expected=expected_direction),
            Evidence(key="direction_consistency", actual=direction_consistency),
            Evidence(key="candidate_sample_count", actual=candidate_count),
            Evidence(key="valid_sample_count", actual=valid_count),
            Evidence(key="rejected_sample_count", actual=rejected_count),
            Evidence(key="valid_fraction", actual=valid_fraction),
        ),
        issues=issues,
        metadata={
            "input_joint_id": input_joint_id,
            "output_joint_id": output_joint_id,
            "expected_ratio": expected_ratio,
            "expected_direction": expected_direction,
            "measurement": measurement,
            "requested_start_time_s": start_time_s,
            "requested_end_time_s": end_time_s,
            "effective_start_time_s": effective_start,
            "effective_end_time_s": effective_end,
            "relative_tolerance": relative_tolerance,
            "minimum_sample_count": minimum_sample_count,
            "minimum_valid_fraction": minimum_valid_fraction,
            "minimum_input_magnitude": minimum_input_magnitude,
            "minimum_output_magnitude": minimum_output_magnitude,
        },
    )


def _run_failure(*, spec: CheckSpec, code: str, message: str) -> CheckReport:
    return _report(
        check_id=spec.check_id,
        check_type=spec.check_type,
        issues=(
            _issue(
                code=code,
                stage="checks.run",
                message=message,
                evidence=(Evidence(key="check_type", actual=spec.check_type),),
            ),
        ),
    )


def run_checks(
    *,
    assembly: AssemblyModel,
    scenario: Scenario | None = None,
    motion_result: MotionResult | None = None,
    checks: Sequence[CheckSpec],
) -> CheckSuiteReport:
    """Execute only the explicit checks, in the order supplied."""

    reports: list[CheckReport] = []
    seen: set[str] = set()
    for spec in checks:
        if not isinstance(spec, CheckSpec):
            raise TypeError("checks must contain CheckSpec values")
        if spec.check_id in seen:
            raise ValueError("check specs must have unique check IDs")
        seen.add(spec.check_id)
        parameters = dict(spec.parameters)
        parameters["check_id"] = spec.check_id
        if spec.check_type == "constraint_residuals":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                report = check_constraint_residuals(
                    motion_result=motion_result, **parameters
                )
        elif spec.check_type == "constraint_equation_residuals":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                scenario_disabled = (
                    tuple(scenario.disabled_constraint_ids)
                    if scenario is not None
                    else ()
                )
                requested_disabled = tuple(
                    parameters.pop("disabled_constraint_ids", ())
                )
                parameters["disabled_constraint_ids"] = tuple(
                    dict.fromkeys((*scenario_disabled, *requested_disabled))
                )
                report = check_constraint_equation_residuals(
                    motion_result=motion_result, **parameters
                )
        elif spec.check_type == "joint_limits":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                report = check_joint_limits(
                    assembly=assembly, motion_result=motion_result, **parameters
                )
        elif spec.check_type == "transmission_ratio":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                report = check_transmission_ratio(
                    motion_result=motion_result, **parameters
                )
        elif spec.check_type == "pose_target":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                report = check_pose_target(motion_result=motion_result, **parameters)
        elif spec.check_type == "trajectory":
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This check requires a MotionResult.",
                )
            else:
                report = check_trajectory(motion_result=motion_result, **parameters)
        elif spec.check_type == "continuous_interference":
            try:
                report = check_continuous_interference(
                    assembly=assembly, motion_result=motion_result, **parameters
                )
            except BackendCapabilityError as error:
                report = CheckReport(
                    check_id=spec.check_id, check_type=spec.check_type,
                    passed=False, severity="error", issues=tuple(error.report.issues),
                    metadata=error.to_dict(),
                )
        elif spec.check_type == "driver_tracking":
            if motion_result is None or scenario is None:
                report = _run_failure(spec=spec, code="KINCHECK-CHECK-SCENARIO-REQUIRED", message="Driver tracking requires Scenario and MotionResult.")
            else:
                tracking = check_driver_tracking(motion_result=motion_result, scenario=scenario, **parameters)
                report = CheckReport(check_id=spec.check_id, check_type=spec.check_type, passed=tracking.passed, severity="info" if tracking.passed else "error", evidence=(Evidence(key="maximum_absolute_error", actual=tracking.maximum_absolute_error, expected=f"<= {tracking.tolerance}"), Evidence(key="mean_absolute_error", actual=tracking.mean_absolute_error), Evidence(key="rms_error", actual=tracking.rms_error), Evidence(key="overshoot", actual=tracking.overshoot), Evidence(key="undertracking", actual=tracking.undertracking), Evidence(key="valid_sample_count", actual=tracking.valid_sample_count), Evidence(key="first_failure_time_s", actual=tracking.first_failure_time_s)), issues=tracking.issues, metadata=tracking.to_dict())
        elif spec.check_type in {"path_tracking", "planar_tracking", "start_stop_reversal", "periodic_motion", "synchronization"}:
            if motion_result is None:
                report = _run_failure(spec=spec, code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED", message="This check requires a MotionResult.")
            else:
                try:
                    if spec.check_type == "path_tracking":
                        trajectory = parameters.pop("trajectory", None)
                        if trajectory is None:
                            trajectory = next((item for item in motion_result.trajectories if item.component_id == parameters.pop("component_id", getattr(parameters.get("path_target", None), "component_id", None)) and item.connector_id == parameters.pop("connector_id", None)), None)
                        report = check_path_tracking(trajectory=trajectory, **parameters)
                    elif spec.check_type == "planar_tracking":
                        trajectory = parameters.pop("trajectory", None)
                        if trajectory is None:
                            trajectory = next((item for item in motion_result.trajectories if item.component_id == parameters.pop("component_id", "") and item.connector_id == parameters.pop("connector_id", None)), None)
                        report = check_planar_tracking(trajectory=trajectory, **parameters)
                    elif spec.check_type == "start_stop_reversal": report = check_start_stop_reversal(motion_result=motion_result, **parameters)
                    elif spec.check_type == "periodic_motion": report = check_periodic_motion(motion_result=motion_result, **parameters)
                    else: report = check_synchronization(motion_result=motion_result, **parameters)
                except (AttributeError, TypeError, ValueError, KeyError) as error:
                    report = _run_failure(spec=spec, code="KINCHECK-CHECK-PARAMETERS-INVALID", message=str(error))
        elif spec.check_type in {"interference", "minimum_clearance", "motion_envelope"}:
            if motion_result is None:
                report = _run_failure(
                    spec=spec,
                    code="KINCHECK-CHECK-MOTION-RESULT-REQUIRED",
                    message="This geometric check requires a MotionResult.",
                )
            else:
                from . import clearance as clearance_module

                check_id = parameters.pop("check_id")
                try:
                    if spec.check_type == "interference":
                        clearance_report = clearance_module.check_interference(
                            assembly=assembly, motion_result=motion_result, **parameters
                        )
                    elif spec.check_type == "minimum_clearance":
                        clearance_report = clearance_module.measure_minimum_clearance(
                            assembly=assembly, motion_result=motion_result, **parameters
                        )
                    else:
                        clearance_report = clearance_module.create_motion_envelope(
                            assembly=assembly, motion_result=motion_result, **parameters
                        )
                    report = clearance_report.as_check_report(check_id=check_id)
                except (BackendCapabilityError, KeyError, RuntimeError, TypeError, ValueError, OSError) as cause:
                    if isinstance(cause, BackendCapabilityError):
                        issues = tuple(cause.report.issues)
                        error_payload = cause.to_dict()
                    else:
                        message = str(cause)
                        code = message.partition(":")[0] if message.startswith("KINCHECK-") else "KINCHECK-CLEARANCE-QUERY-FAILED"
                        issues = (
                            SimIssue(
                                code=code,
                                severity="error",
                                stage="clearance",
                                message="The geometry backend could not complete the requested check.",
                                evidence=(
                                    Evidence(
                                        key="native_error_type",
                                        actual=type(cause).__name__,
                                    ),
                                ),
                                suggested_actions=(
                                    "Inspect the geometric-check input and run the check again.",
                                ),
                            ),
                        )
                        error_payload = {"type": type(cause).__name__}
                    report = CheckReport(
                        check_id=spec.check_id,
                        check_type=spec.check_type,
                        passed=False,
                        severity="error",
                        issues=issues,
                        metadata={"error": error_payload},
                    )
        else:
            report = _run_failure(
                spec=spec,
                code="KINCHECK-CHECK-TYPE-UNSUPPORTED",
                message="The requested check type is not implemented.",
            )
        reports.append(report)

    return CheckSuiteReport(
        reports=tuple(reports),
        metadata={
            "assembly_id": assembly.assembly_id,
            "scenario_id": getattr(scenario, "scenario_id", None),
            "motion_scenario_id": (
                motion_result.scenario_id if motion_result is not None else None
            ),
            "check_count": len(reports),
        },
    )


def _raise_check_capability(*, capability: str, operation: str) -> None:
    message = f"{operation} is declared but not implemented in the current release."
    action = "Use the implemented result checks or inspect MotionResult data explicitly."
    issue = SimIssue(
        code="KINCHECK-CAPABILITY-UNIMPLEMENTED",
        severity="error",
        stage="checks.capability",
        message=message,
        evidence=(Evidence(key="missing_capability", actual=capability),),
        suggested_actions=(action,),
    )
    raise BackendCapabilityError(
        code="KINCHECK-CAPABILITY-UNIMPLEMENTED",
        message=message,
        report=DiagnosticReport(
            issues=(issue,), operation=operation, status="capability_failed"
        ),
        operation=operation,
        missing_capabilities=(capability,),
    )


def check_continuous_interference(
    *, assembly: AssemblyModel, motion_result: MotionResult,
    component_pairs: Sequence[Sequence[str]] | None = None,
    **parameters: Any,
) -> CheckReport:
    """Explicit capability boundary for continuous time-of-impact checking."""
    _raise_check_capability(
        capability="continuous_time_of_impact",
        operation="check_continuous_interference",
    )


def _target_value(value: Any) -> tuple[str, str | None, Pose, float, float, float | None]:
    if isinstance(value, Mapping):
        component_id = str(value["component_id"])
        connector_id = value.get("connector_id")
        pose = value["pose"]
        raw_position_tolerance = value.get("position_tolerance_m")
        raw_orientation_tolerance = value.get("orientation_tolerance_rad")
        target_time = value.get("time_s")
    else:
        component_id = str(getattr(value, "component_id"))
        connector_id = getattr(value, "connector_id", None)
        pose = getattr(value, "pose")
        raw_position_tolerance = getattr(value, "position_tolerance_m", None)
        raw_orientation_tolerance = getattr(value, "orientation_tolerance_rad", None)
        target_time = getattr(value, "time_s", None)
    position_tolerance = float(
        1e-6 if raw_position_tolerance is None else raw_position_tolerance
    )
    orientation_tolerance = float(
        1e-6 if raw_orientation_tolerance is None else raw_orientation_tolerance
    )
    if not isinstance(pose, Pose):
        raise TypeError("pose target must contain a Pose")
    if (
        not math.isfinite(position_tolerance)
        or not math.isfinite(orientation_tolerance)
        or position_tolerance <= 0.0
        or orientation_tolerance <= 0.0
    ):
        raise ValueError("pose target tolerances must be positive finite numbers")
    if target_time is not None:
        target_time = float(target_time)
        if not math.isfinite(target_time) or target_time < 0.0:
            raise ValueError("pose target time_s must be finite and non-negative")
    return component_id, connector_id, pose, position_tolerance, orientation_tolerance, target_time


def check_pose_target(
    *,
    motion_result: MotionResult,
    targets: Sequence[Any] | None = None,
    target: Any | None = None,
    position_tolerance_m: float | None = None,
    orientation_tolerance_rad: float | None = None,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    check_id: str = "pose_target",
) -> CheckReport:
    """Check recorded component/Connector poses against explicit targets."""

    stage = "checks.pose_target"
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(start_time_s=start_time_s, end_time_s=end_time_s, stage=stage)
    issues.extend(window_issues)
    requested = tuple(targets or ())
    if target is not None:
        requested = (*requested, target)
    if not requested:
        issues.append(_issue(code="KINCHECK-CHECK-POSE-TARGET-EMPTY", stage=stage, message="At least one Pose target is required."))
    for name, value in (
        ("position_tolerance_m", position_tolerance_m),
        ("orientation_tolerance_rad", orientation_tolerance_rad),
    ):
        if value is not None and (not math.isfinite(value) or value <= 0.0):
            issues.append(_issue(
                code="KINCHECK-CHECK-POSE-TARGET-INVALID",
                stage=stage,
                message=f"{name} must be a positive finite number.",
                evidence=(Evidence(key=name, actual=value, expected="> 0"),),
            ))
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-POSE-TARGET-INVALID",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="pose_target",
            issues=issues,
            metadata={"start_time_s": start_time_s, "end_time_s": end_time_s},
        )
    trajectory_map = {(item.component_id, item.connector_id): item for item in motion_result.trajectories}
    checked = 0
    max_position = 0.0
    max_orientation = 0.0
    for raw_target in requested:
        try:
            component_id, connector_id, expected, target_position_tol, target_orientation_tol, target_time = _target_value(raw_target)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            issues.append(_issue(code="KINCHECK-CHECK-POSE-TARGET-INVALID", stage=stage, message=str(error)))
            continue
        if position_tolerance_m is not None:
            target_position_tol = float(position_tolerance_m)
        if orientation_tolerance_rad is not None:
            target_orientation_tol = float(orientation_tolerance_rad)
        trajectory = trajectory_map.get((component_id, connector_id))
        if trajectory is None:
            issues.append(_issue(code="KINCHECK-RESULT-TRAJECTORY-MISSING", stage=stage, message="The requested Pose target has no recorded trajectory.", object_ids=(component_id, connector_id or "component"), suggested_actions=("Include this Component or Connector in the result scope.",)))
            continue
        samples = [
            (time_s, pose)
            for time_s, pose in zip(trajectory.times_s, trajectory.poses)
            if _in_window(time_s, start_time_s=start_time_s, end_time_s=end_time_s)
        ]
        if target_time is not None:
            samples = [min(samples, key=lambda item: abs(item[0] - target_time))] if samples else []
        if not samples:
            issues.append(_issue(code="KINCHECK-CHECK-POSE-TARGET-NO-SAMPLES", stage=stage, message="No recorded pose sample falls in the requested time window.", object_ids=(component_id, connector_id or "component")))
            continue
        checked += len(samples)
        for time_s, actual in samples:
            position_error = math.dist(actual.position_m, expected.position_m)
            orientation_error = orientation_error_rad(actual=actual, expected=expected)
            max_position = max(max_position, position_error)
            max_orientation = max(max_orientation, orientation_error)
            if position_error > target_position_tol or orientation_error > target_orientation_tol:
                issues.append(_issue(code="KINCHECK-CHECK-POSE-TARGET-MISMATCH", stage=stage, message="A recorded pose is outside the requested target tolerance.", object_ids=(component_id, connector_id or "component"), failure_time_s=time_s, evidence=(Evidence(key="position_error_m", actual=position_error, expected=f"<= {target_position_tol}", unit="m"), Evidence(key="orientation_error_rad", actual=orientation_error, expected=f"<= {target_orientation_tol}", unit="rad")), suggested_actions=("Adjust the target, driver, or position-solver initial state.",)))
    return _report(check_id=check_id, check_type="pose_target", evidence=(Evidence(key="target_count", actual=len(requested)), Evidence(key="sample_count", actual=checked), Evidence(key="maximum_position_error_m", actual=max_position, unit="m"), Evidence(key="maximum_orientation_error_rad", actual=max_orientation, unit="rad")), issues=issues, metadata={"start_time_s": start_time_s, "end_time_s": end_time_s})


def check_trajectory(
    *,
    motion_result: MotionResult,
    component_id: str | None = None,
    connector_id: str | None = None,
    max_speed_m_s: float | None = None,
    max_angular_speed_rad_s: float | None = None,
    max_acceleration_m_s2: float | None = None,
    max_angular_acceleration_rad_s2: float | None = None,
    max_position_residual_m: float | None = None,
    max_orientation_residual_rad: float | None = None,
    min_path_length_m: float | None = None,
    max_path_length_m: float | None = None,
    position_bounds_m: Mapping[str, Sequence[float]] | None = None,
    limit_joint_ids: Sequence[str] | None = None,
    maximum_limit_event_count: int | None = None,
    maximum_exceeded_limit_event_count: int | None = 0,
    start_time_s: float | None = None,
    end_time_s: float | None = None,
    check_id: str = "trajectory",
) -> CheckReport:
    """Check sampled trajectory ranges without modifying the result."""

    stage = "checks.trajectory"
    issues: list[SimIssue] = list(_motion_result_issues(motion_result))
    _, _, window_issues = _valid_window(start_time_s=start_time_s, end_time_s=end_time_s, stage=stage)
    issues.extend(window_issues)
    for name, value, unit in (
        ("max_speed_m_s", max_speed_m_s, "m/s"),
        ("max_angular_speed_rad_s", max_angular_speed_rad_s, "rad/s"),
        ("max_acceleration_m_s2", max_acceleration_m_s2, "m/s^2"),
        ("max_angular_acceleration_rad_s2", max_angular_acceleration_rad_s2, "rad/s^2"),
        ("max_position_residual_m", max_position_residual_m, "m"),
        ("max_orientation_residual_rad", max_orientation_residual_rad, "rad"),
    ):
        if value is not None and (not math.isfinite(value) or value < 0.0):
            issues.append(_issue(
                code="KINCHECK-CHECK-TRAJECTORY-LIMIT-INVALID",
                stage=stage,
                message=f"{name} must be finite and non-negative.",
                evidence=(Evidence(key=name, actual=value, expected=">= 0", unit=unit),),
            ))
    for name, value in (
        ("min_path_length_m", min_path_length_m),
        ("max_path_length_m", max_path_length_m),
    ):
        if value is not None and (not math.isfinite(value) or value < 0.0):
            issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-PATH-LIMIT-INVALID", stage=stage, message=f"{name} must be finite and non-negative.", evidence=(Evidence(key=name, actual=value, expected=">= 0", unit="m"),)))
    if min_path_length_m is not None and max_path_length_m is not None and min_path_length_m > max_path_length_m:
        issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-PATH-LIMIT-INVALID", stage=stage, message="Minimum path length cannot exceed maximum path length."))
    for name, value in (
        ("maximum_limit_event_count", maximum_limit_event_count),
        ("maximum_exceeded_limit_event_count", maximum_exceeded_limit_event_count),
    ):
        if value is not None and (not isinstance(value, int) or value < 0):
            issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-LIMIT-EVENT-COUNT-INVALID", stage=stage, message=f"{name} must be a non-negative integer.", evidence=(Evidence(key=name, actual=value, expected=">= 0"),)))
    try:
        normalized_bounds = normalize_position_bounds(position_bounds_m)
    except (TypeError, ValueError) as error:
        normalized_bounds = {}
        issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-BOUNDS-INVALID", stage=stage, message=str(error)))
    if any(
        item.code in {
            "KINCHECK-CHECK-TIME-WINDOW-INVALID",
            "KINCHECK-CHECK-TRAJECTORY-LIMIT-INVALID",
            "KINCHECK-CHECK-TRAJECTORY-PATH-LIMIT-INVALID",
            "KINCHECK-CHECK-TRAJECTORY-LIMIT-EVENT-COUNT-INVALID",
            "KINCHECK-CHECK-TRAJECTORY-BOUNDS-INVALID",
        }
        for item in issues
    ):
        return _report(
            check_id=check_id,
            check_type="trajectory",
            issues=issues,
            metadata={
                "component_id": component_id,
                "connector_id": connector_id,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
            },
        )
    selected = tuple(item for item in motion_result.trajectories if (component_id is None or item.component_id == component_id) and (connector_id is None or item.connector_id == connector_id))
    if not selected:
        issues.append(_issue(code="KINCHECK-RESULT-TRAJECTORY-MISSING", stage=stage, message="No trajectory matches the requested object.", object_ids=tuple(item for item in (component_id, connector_id) if item)))
    checked = 0
    maxima = {"speed_m_s": 0.0, "angular_speed_rad_s": 0.0, "acceleration_m_s2": 0.0, "angular_acceleration_rad_s2": 0.0}
    path_lengths: list[float] = []
    coordinate_minima = {axis: math.inf for axis in ("x_m", "y_m", "z_m")}
    coordinate_maxima = {axis: -math.inf for axis in ("x_m", "y_m", "z_m")}
    for trajectory in selected:
        metrics = trajectory_window_metrics(
            trajectory=trajectory,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
        )
        indices = metrics.indices
        if not indices:
            continue
        path_lengths.append(metrics.path_length_m)
        for axis, (minimum, maximum) in metrics.bounds_m.items():
            coordinate_minima[axis] = min(coordinate_minima[axis], minimum)
            coordinate_maxima[axis] = max(coordinate_maxima[axis], maximum)
        object_ids = (trajectory.component_id, trajectory.connector_id or "component")
        if min_path_length_m is not None and metrics.path_length_m < min_path_length_m:
            issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-PATH-LENGTH-OUT-OF-RANGE", stage=stage, message="Trajectory path length is shorter than requested.", object_ids=object_ids, evidence=(Evidence(key="path_length_m", actual=metrics.path_length_m, expected=f">= {min_path_length_m}", unit="m"),)))
        if max_path_length_m is not None and metrics.path_length_m > max_path_length_m:
            issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-PATH-LENGTH-OUT-OF-RANGE", stage=stage, message="Trajectory path length is longer than requested.", object_ids=object_ids, evidence=(Evidence(key="path_length_m", actual=metrics.path_length_m, expected=f"<= {max_path_length_m}", unit="m"),)))
        for axis, (lower, upper) in normalized_bounds.items():
            actual_lower, actual_upper = metrics.bounds_m[axis]
            if actual_lower < lower or actual_upper > upper:
                issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-POSITION-OUT-OF-RANGE", stage=stage, message="Trajectory coordinates leave the requested range.", object_ids=object_ids, evidence=(Evidence(key=f"{axis}_range", actual=(actual_lower, actual_upper), expected=(lower, upper), unit="m"),)))
        checked += len(indices)
        for index in indices:
            vectors = {
                "speed_m_s": None if trajectory.linear_velocities_m_s is None else math.sqrt(sum(value * value for value in trajectory.linear_velocities_m_s[index])),
                "angular_speed_rad_s": None if trajectory.angular_velocities_rad_s is None else math.sqrt(sum(value * value for value in trajectory.angular_velocities_rad_s[index])),
                "acceleration_m_s2": None if trajectory.linear_accelerations_m_s2 is None else math.sqrt(sum(value * value for value in trajectory.linear_accelerations_m_s2[index])),
                "angular_acceleration_rad_s2": None if trajectory.angular_accelerations_rad_s2 is None else math.sqrt(sum(value * value for value in trajectory.angular_accelerations_rad_s2[index])),
            }
            limits = {"speed_m_s": max_speed_m_s, "angular_speed_rad_s": max_angular_speed_rad_s, "acceleration_m_s2": max_acceleration_m_s2, "angular_acceleration_rad_s2": max_angular_acceleration_rad_s2}
            for name, value in vectors.items():
                if value is None:
                    if limits[name] is not None:
                        issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-DATA-MISSING", stage=stage, message=f"Trajectory does not contain {name} data.", object_ids=(trajectory.component_id, trajectory.connector_id or "component"), failure_time_s=trajectory.times_s[index]))
                    continue
                maxima[name] = max(maxima[name], value)
                if limits[name] is not None and value > float(limits[name]):
                    issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-LIMIT-EXCEEDED", stage=stage, message=f"Trajectory {name} exceeds its requested limit.", object_ids=(trajectory.component_id, trajectory.connector_id or "component"), failure_time_s=trajectory.times_s[index], evidence=(Evidence(key=name, actual=value, expected=f"<= {limits[name]}"),)))
    if max_position_residual_m is not None or max_orientation_residual_rad is not None:
        for residual in motion_result.constraint_residuals:
            if not _in_window(residual.time_s, start_time_s=start_time_s, end_time_s=end_time_s):
                continue
            if max_position_residual_m is not None and residual.position_residual_m > max_position_residual_m:
                issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-CONSTRAINT-EXCEEDED", stage=stage, message="A trajectory sample contains a position constraint residual above tolerance.", object_ids=(residual.constraint_id,), failure_time_s=residual.time_s, evidence=(Evidence(key="position_residual_m", actual=residual.position_residual_m, expected=f"<= {max_position_residual_m}"),)))
            if max_orientation_residual_rad is not None and residual.orientation_residual_rad > max_orientation_residual_rad:
                issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-CONSTRAINT-EXCEEDED", stage=stage, message="A trajectory sample contains an orientation constraint residual above tolerance.", object_ids=(residual.constraint_id,), failure_time_s=residual.time_s, evidence=(Evidence(key="orientation_residual_rad", actual=residual.orientation_residual_rad, expected=f"<= {max_orientation_residual_rad}"),)))
    limit_events = limit_events_in_window(
        events=motion_result.limit_events,
        joint_ids=limit_joint_ids,
        start_time_s=start_time_s,
        end_time_s=end_time_s,
    )
    exceeded_events = tuple(item for item in limit_events if item.event_type == "exceeded")
    if maximum_limit_event_count is not None and len(limit_events) > maximum_limit_event_count:
        issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-LIMIT-EVENTS-EXCEEDED", stage=stage, message="Trajectory contains more limit events than allowed.", object_ids=tuple(sorted({item.joint_id for item in limit_events})), evidence=(Evidence(key="limit_event_count", actual=len(limit_events), expected=f"<= {maximum_limit_event_count}"),)))
    if maximum_exceeded_limit_event_count is not None and len(exceeded_events) > maximum_exceeded_limit_event_count:
        issues.append(_issue(code="KINCHECK-CHECK-TRAJECTORY-LIMIT-EXCEEDED-EVENTS", stage=stage, message="Trajectory contains more exceeded-limit events than allowed.", object_ids=tuple(sorted({item.joint_id for item in exceeded_events})), evidence=(Evidence(key="exceeded_limit_event_count", actual=len(exceeded_events), expected=f"<= {maximum_exceeded_limit_event_count}"),)))
    finite_minima = {key: value for key, value in coordinate_minima.items() if math.isfinite(value)}
    finite_maxima = {key: value for key, value in coordinate_maxima.items() if math.isfinite(value)}
    return _report(check_id=check_id, check_type="trajectory", evidence=(Evidence(key="trajectory_count", actual=len(selected)), Evidence(key="sample_count", actual=checked), Evidence(key="minimum_path_length_m", actual=min(path_lengths, default=0.0), unit="m"), Evidence(key="maximum_path_length_m", actual=max(path_lengths, default=0.0), unit="m"), Evidence(key="limit_event_count", actual=len(limit_events)), Evidence(key="exceeded_limit_event_count", actual=len(exceeded_events)), *(Evidence(key=key, actual=value) for key, value in maxima.items())), issues=issues, metadata={"component_id": component_id, "connector_id": connector_id, "position_bounds_m": dict(normalized_bounds), "coordinate_minima_m": finite_minima, "coordinate_maxima_m": finite_maxima, "limit_joint_ids": tuple(limit_joint_ids or ()), "start_time_s": start_time_s, "end_time_s": end_time_s})


def check_interference(*, assembly: AssemblyModel, motion_result: MotionResult, check_id: str = "interference", **parameters: Any) -> CheckReport:
    """Run the strict triangle-mesh interference check as a CheckReport."""
    from .clearance import check_interference as _check_interference

    return _check_interference(
        assembly=assembly, motion_result=motion_result, **parameters
    ).as_check_report(check_id=check_id)


def check_minimum_clearance(*, assembly: AssemblyModel, motion_result: MotionResult, check_id: str = "minimum_clearance", **parameters: Any) -> CheckReport:
    """Run the strict signed minimum-clearance check as a CheckReport."""
    from .clearance import measure_minimum_clearance

    return measure_minimum_clearance(
        assembly=assembly, motion_result=motion_result, **parameters
    ).as_check_report(check_id=check_id)


def check_motion_envelope(*, assembly: AssemblyModel, motion_result: MotionResult, check_id: str = "motion_envelope", **parameters: Any) -> CheckReport:
    """Compute a mesh motion envelope and expose it through the check API."""
    from .clearance import create_motion_envelope

    return create_motion_envelope(
        assembly=assembly, motion_result=motion_result, **parameters
    ).as_check_report(check_id=check_id)


def _distance_point_segment(p: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    d = [b[i] - a[i] for i in range(len(a))]; den = sum(x*x for x in d)
    u = 0.0 if den == 0 else max(0.0, min(1.0, sum((p[i]-a[i])*d[i] for i in range(len(a))) / den))
    return math.sqrt(sum((p[i] - (a[i] + u*d[i]))**2 for i in range(len(a))))

def check_path_tracking(*, motion_result: MotionResult | None = None, component_id: str | None = None, connector_id: str | None = None, trajectory: Any = None, path_target: Any, position_tolerance_m: float = 1e-6, curvature_tolerance_1_m: float | None = None, minimum_turn_radius_m: float | None = None, check_id: str = "path_tracking") -> CheckReport:
    """Check sampled component/connector positions against a polyline path."""
    from .motion_contracts import PathTarget
    issues: list[SimIssue] = []
    if motion_result is not None and motion_result.status not in {"completed", "completed_with_warnings"}:
        issues.append(_issue(code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE", stage="checks.path_tracking", message="An incomplete MotionResult cannot establish a complete path pass.", object_ids=(motion_result.scenario_id,), failure_time_s=motion_result.end_time_s))
    if not isinstance(path_target, PathTarget):
        try: path_target = PathTarget(**dict(path_target))
        except (TypeError, ValueError) as error:
            return _report(check_id=check_id, check_type="path_tracking", issues=(_issue(code="KINCHECK-CHECK-PATH-TARGET-INVALID", stage="checks.path_tracking", message=str(error)),))
    if motion_result is not None:
        if component_id is None:
            return _report(check_id=check_id, check_type="path_tracking", issues=(_issue(code="KINCHECK-CHECK-PATH-COMPONENT-REQUIRED", stage="checks.path_tracking", message="component_id is required when checking a MotionResult."),))
        trajectory = next((item for item in motion_result.trajectories if item.component_id == component_id and item.connector_id == connector_id), None)
    points = tuple(getattr(trajectory, "positions_m", ()))
    if not points:
        poses = tuple(getattr(trajectory, "poses", ())); points = tuple(p.position_m for p in poses)
    if not points:
        issue = _issue(code="KINCHECK-CHECK-PATH-TRAJECTORY-MISSING", stage="checks.path_tracking", message="A sampled position trajectory is required.")
        return _report(check_id=check_id, check_type="path_tracking", issues=(issue,))
    segments = tuple(zip(path_target.points_m, (*path_target.points_m[1:], path_target.points_m[0]) if path_target.closed else path_target.points_m[1:]))
    errors = [min(_distance_point_segment(p, a, b) for a,b in segments) for p in points]
    max_error = max(errors); first = next((float(t) for t,e in zip(getattr(trajectory, "times_s", ()), errors) if e > position_tolerance_m), None)
    if first is not None:
        issues.append(_issue(code="KINCHECK-CHECK-PATH-TRACKING-FAILED", stage="checks.path_tracking", message="Path tracking error exceeds tolerance.", object_ids=(getattr(trajectory, "component_id", ""),), failure_time_s=first, evidence=(Evidence(key="maximum_path_error_m", actual=max_error, expected=f"<= {position_tolerance_m}", unit="m"),)))
    curvature = []
    poly = path_target.points_m
    for a,b,c in zip(poly, poly[1:], poly[2:]):
        ab=math.dist(a,b); bc=math.dist(b,c); ac=math.dist(a,c)
        area=math.sqrt(max(0., (ab+bc+ac)*(-ab+bc+ac)*(ab-bc+ac)*(ab+bc-ac)))/4.
        curvature.append(4*area/(ab*bc*ac) if ab*bc*ac else 0.)
    max_curvature=max(curvature, default=0.)
    if curvature_tolerance_1_m is not None and max_curvature > curvature_tolerance_1_m:
        issues.append(_issue(code="KINCHECK-CHECK-PATH-CURVATURE-EXCEEDED", stage="checks.path_tracking", message="Target path curvature exceeds the declared threshold.", evidence=(Evidence(key="maximum_curvature_1_m", actual=max_curvature, expected=f"<= {curvature_tolerance_1_m}", unit="1/m"),)))
    if minimum_turn_radius_m is not None and max_curvature > 0 and 1/max_curvature < minimum_turn_radius_m:
        issues.append(_issue(code="KINCHECK-CHECK-PATH-TURN-RADIUS-FAILED", stage="checks.path_tracking", message="Target path contains a turn radius below the declared minimum.", evidence=(Evidence(key="minimum_turn_radius_m", actual=1/max_curvature, expected=f">= {minimum_turn_radius_m}", unit="m"),)))
    return _report(check_id=check_id, check_type="path_tracking", evidence=(Evidence(key="maximum_path_error_m", actual=max_error, expected=f"<= {position_tolerance_m}", unit="m"), Evidence(key="maximum_curvature_1_m", actual=max_curvature, unit="1/m"), Evidence(key="sample_count", actual=len(points))), issues=issues, metadata={"curvature_supported": True, "path_point_count": len(path_target.points_m)})

def _yaw(q: Sequence[float]) -> float:
    x,y,z,w = q; return math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))

def check_planar_tracking(*, motion_result: MotionResult | None = None, component_id: str | None = None, connector_id: str | None = None, trajectory: Any = None, target: Any, position_tolerance_m: float = 1e-6, yaw_tolerance_rad: float = 1e-6, check_id: str = "planar_tracking") -> CheckReport:
    """Check X/Y/Yaw samples. Target may be PlanarPose points or PoseTrajectory."""
    from .motion_contracts import PlanarPose, PoseTrajectory
    issues: list[SimIssue] = []
    if motion_result is not None and motion_result.status not in {"completed", "completed_with_warnings"}:
        issues.append(_issue(code="KINCHECK-CHECK-MOTION-RESULT-INCOMPLETE", stage="checks.planar_tracking", message="An incomplete MotionResult cannot establish a complete planar pass.", object_ids=(motion_result.scenario_id,), failure_time_s=motion_result.end_time_s))
    target_trajectory = target if isinstance(target, PoseTrajectory) else None
    if target_trajectory is not None:
        targets = target_trajectory.points
    else:
        raw_targets = target.get("points") if isinstance(target, Mapping) else target
        try:
            if isinstance(raw_targets, (str, bytes)):
                raise TypeError("target must be a sequence of planar pose points")
            targets = tuple(
                item if isinstance(item, PlanarPose) else PlanarPose(**dict(item))
                for item in raw_targets
            )
            if not targets:
                raise ValueError("target must contain at least one planar pose point")
        except (AttributeError, TypeError, ValueError, KeyError) as error:
            return _report(
                check_id=check_id,
                check_type="planar_tracking",
                issues=(
                    _issue(
                        code="KINCHECK-CHECK-PLANAR-TARGET-INVALID",
                        stage="checks.planar_tracking",
                        message="Planar tracking target must be a sequence of valid planar pose points.",
                        evidence=(
                            Evidence(key="native_error_type", actual=type(error).__name__),
                            Evidence(key="native_error_message", actual=str(error)),
                        ),
                        suggested_actions=(
                            "Pass PlanarPose values or mappings with time_s, x_m, y_m, and yaw_rad.",
                        ),
                    ),
                ),
            )
    if motion_result is not None:
        if component_id is None:
            return _report(check_id=check_id, check_type="planar_tracking", issues=(_issue(code="KINCHECK-CHECK-PLANAR-COMPONENT-REQUIRED", stage="checks.planar_tracking", message="component_id is required when checking a MotionResult."),))
        trajectory = next((item for item in motion_result.trajectories if item.component_id == component_id and item.connector_id == connector_id), None)
    times = tuple(getattr(trajectory, "times_s", ())); poses = tuple(getattr(trajectory, "poses", ()))
    if not times or not poses or not targets:
        return _report(check_id=check_id, check_type="planar_tracking", issues=(_issue(code="KINCHECK-CHECK-PLANAR-DATA-MISSING", stage="checks.planar_tracking", message="Planar trajectory and target samples are required."),))
    def tv(t):
        return min(targets, key=lambda x: abs(x.time_s-t))
    errors=[]
    for t,p in zip(times, poses):
        q=tv(t); x,y=p.position_m[:2]; yaw=_yaw(p.orientation_xyzw)
        if target_trajectory is not None:
            q_pose = target_trajectory.at(time_s=t)
            qx,qy,qyaw=q_pose.position_m[0],q_pose.position_m[1],_yaw(q_pose.orientation_xyzw)
        else:
            q_pose = q.pose if hasattr(q, "pose") else q
            qx,qy,qyaw=(q.x_m,q.y_m,q.yaw_rad) if hasattr(q,"x_m") else (q_pose.position_m[0],q_pose.position_m[1],_yaw(q_pose.orientation_xyzw))
        pe=math.hypot(x-qx, y-qy); ye=abs((yaw-qyaw+math.pi)%(2*math.pi)-math.pi); errors.append((pe,ye))
        if pe>position_tolerance_m or ye>yaw_tolerance_rad: issues.append(_issue(code="KINCHECK-CHECK-PLANAR-TRACKING-FAILED", stage="checks.planar_tracking", message="Planar translation or heading error exceeds tolerance.", object_ids=(getattr(trajectory,"component_id",""),), failure_time_s=t, evidence=(Evidence(key="position_error_m",actual=pe,expected=f"<= {position_tolerance_m}",unit="m"),Evidence(key="yaw_error_rad",actual=ye,expected=f"<= {yaw_tolerance_rad}",unit="rad"))))
    return _report(check_id=check_id, check_type="planar_tracking", evidence=(Evidence(key="maximum_translation_error_m",actual=max(x[0] for x in errors),unit="m"), Evidence(key="maximum_yaw_error_rad",actual=max(x[1] for x in errors),unit="rad")), issues=issues)

def check_pose_trajectory(*, motion_result: MotionResult, target: Any, position_tolerance_m: float | None = None, orientation_tolerance_rad: float | None = None, check_id: str = "pose_trajectory") -> CheckReport:
    """Check a recorded component/connector trajectory against a PoseTrajectory."""
    from .motion_contracts import PoseTrajectory
    issues = list(_motion_result_issues(motion_result))
    if not isinstance(target, PoseTrajectory):
        issues.append(_issue(code="KINCHECK-CHECK-POSE-TRAJECTORY-TARGET-INVALID", stage="checks.pose_trajectory", message="target must be a PoseTrajectory."))
        return _report(check_id=check_id, check_type="pose_trajectory", issues=issues)
    trajectory = next((item for item in motion_result.trajectories if item.component_id == target.target.component_id and item.connector_id == target.target.connector_id), None)
    if trajectory is None:
        issues.append(_issue(code="KINCHECK-CHECK-POSE-TRAJECTORY-MISSING", stage="checks.pose_trajectory", message="The target trajectory was not recorded.", object_ids=(target.target.component_id, target.target.connector_id or "component")))
        return _report(check_id=check_id, check_type="pose_trajectory", issues=issues)
    position_tolerance_m = target.position_tolerance_m if position_tolerance_m is None else float(position_tolerance_m)
    orientation_tolerance_rad = target.orientation_tolerance_rad if orientation_tolerance_rad is None else float(orientation_tolerance_rad)
    if position_tolerance_m < 0 or orientation_tolerance_rad < 0:
        issues.append(_issue(code="KINCHECK-CHECK-POSE-TRAJECTORY-TOLERANCE-INVALID", stage="checks.pose_trajectory", message="Pose trajectory tolerances must be non-negative."))
        return _report(check_id=check_id, check_type="pose_trajectory", issues=issues)
    position_errors=[]; orientation_errors=[]
    for time_s, actual in zip(trajectory.times_s, trajectory.poses):
        expected = target.at(time_s=time_s)
        position_error = math.dist(actual.position_m, expected.position_m)
        orientation_error = orientation_error_rad(actual=actual, expected=expected)
        position_errors.append(position_error); orientation_errors.append(orientation_error)
        if position_error > position_tolerance_m or orientation_error > orientation_tolerance_rad:
            issues.append(_issue(code="KINCHECK-CHECK-POSE-TRAJECTORY-MISMATCH", stage="checks.pose_trajectory", message="Recorded pose is outside the target trajectory tolerance.", object_ids=(target.target.component_id, target.target.connector_id or "component"), failure_time_s=time_s, evidence=(Evidence(key="position_error_m",actual=position_error,expected=f"<= {position_tolerance_m}",unit="m"), Evidence(key="orientation_error_rad",actual=orientation_error,expected=f"<= {orientation_tolerance_rad}",unit="rad"))))
    return _report(check_id=check_id, check_type="pose_trajectory", issues=issues, evidence=(Evidence(key="maximum_position_error_m",actual=max(position_errors,default=math.inf),unit="m"), Evidence(key="maximum_orientation_error_rad",actual=max(orientation_errors,default=math.inf),unit="rad")))

def check_start_stop_reversal(*, motion_result: MotionResult, joint_id: str, speed_threshold: float = 1e-6, check_id: str = "start_stop_reversal") -> CheckReport:
    traj=motion_result.get_joint_trajectory(joint_id=joint_id); issues=list(_motion_result_issues(motion_result))
    if traj is None: return _report(check_id=check_id, check_type="start_stop_reversal", issues=(*issues,_issue(code="KINCHECK-CHECK-JOINT-TRAJECTORY-MISSING",stage="checks.start_stop_reversal",message="Requested joint trajectory is missing.",object_ids=(joint_id,))))
    if not math.isfinite(speed_threshold) or speed_threshold < 0:
        return _report(check_id=check_id, check_type="start_stop_reversal", issues=(*issues,_issue(code="KINCHECK-CHECK-MOTION-EVENT-OPTIONS-INVALID",stage="checks.start_stop_reversal",message="speed_threshold must be finite and non-negative.",object_ids=(joint_id,))))
    active=[(t,v) for t,v in zip(traj.times_s,traj.velocities) if abs(v)>speed_threshold]
    starts=active[0][0] if active else None
    stops=None
    if starts is not None:
        stops=next((t for t,v in zip(traj.times_s,traj.velocities) if t>starts and abs(v)<=speed_threshold),None)
    reversals=[]
    last_sign=0
    for t, value in zip(traj.times_s, traj.velocities):
        sign=1 if value>speed_threshold else -1 if value < -speed_threshold else 0
        if sign and last_sign and sign != last_sign:
            reversals.append(t)
        if sign:
            last_sign=sign
    if starts is None: issues.append(_issue(code="KINCHECK-CHECK-START-NOT-DETECTED",stage="checks.start_stop_reversal",message="No start event exceeded the speed threshold.",object_ids=(joint_id,)))
    if starts is not None and stops is None:
        issues.append(_issue(code="KINCHECK-CHECK-STOP-NOT-DETECTED",stage="checks.start_stop_reversal",message="No sampled stop event was found after motion started.",object_ids=(joint_id,)))
    return _report(check_id=check_id, check_type="start_stop_reversal", evidence=(Evidence(key="start_time_s",actual=starts,unit="s"),Evidence(key="stop_time_s",actual=stops,unit="s"),Evidence(key="reversal_times_s",actual=tuple(reversals),unit="s")), issues=issues, metadata={"reversal_count":len(reversals)})

def check_periodic_motion(*, motion_result: MotionResult, joint_id: str, period_s: float, periods: int = 1, position_tolerance: float = 1e-6, velocity_tolerance: float = 1e-6, check_id: str = "periodic_motion") -> CheckReport:
    if not math.isfinite(period_s) or period_s<=0 or periods<1 or position_tolerance<0 or velocity_tolerance<0: return _report(check_id=check_id,check_type="periodic_motion",issues=(_issue(code="KINCHECK-CHECK-PERIOD-INVALID",stage="checks.periodic_motion",message="period_s and periods must be positive; tolerances must be non-negative."),))
    tr=motion_result.get_joint_trajectory(joint_id=joint_id); issues=list(_motion_result_issues(motion_result))
    if tr is None: return _report(check_id=check_id,check_type="periodic_motion",issues=(*issues,_issue(code="KINCHECK-CHECK-JOINT-TRAJECTORY-MISSING",stage="checks.periodic_motion",message="Requested joint trajectory is missing.",object_ids=(joint_id,))))
    shift=period_s*periods
    if tr.times_s[-1]-tr.times_s[0] < shift:
        issues.append(_issue(code="KINCHECK-CHECK-PERIODIC-TIME-WINDOW-TOO-SHORT",stage="checks.periodic_motion",message="The MotionResult does not contain the requested number of periods.",object_ids=(joint_id,),evidence=(Evidence(key="duration_s",actual=tr.times_s[-1]-tr.times_s[0],expected=f">= {shift}",unit="s"),)))
        return _report(check_id=check_id,check_type="periodic_motion",issues=issues)
    def interpolate(values, time_s):
        for left,right,left_value,right_value in zip(tr.times_s,tr.times_s[1:],values,values[1:]):
            if left <= time_s <= right:
                fraction=(time_s-left)/(right-left)
                return left_value+fraction*(right_value-left_value)
        return values[-1]
    pairs=[]
    for i,t in enumerate(tr.times_s):
        target=t+shift
        if target<=tr.times_s[-1]+1e-12:
            pairs.append((t,abs(tr.positions[i]-interpolate(tr.positions,target)),abs(tr.velocities[i]-interpolate(tr.velocities,target))))
    if not pairs: issues.append(_issue(code="KINCHECK-CHECK-PERIODIC-SAMPLES-MISSING",stage="checks.periodic_motion",message="No complete period pairs are available.",object_ids=(joint_id,)))
    maxp=max((x[1] for x in pairs),default=float("inf")); maxv=max((x[2] for x in pairs),default=float("inf"))
    if maxp>position_tolerance or maxv>velocity_tolerance: issues.append(_issue(code="KINCHECK-CHECK-PERIODIC-DRIFT-EXCEEDED",stage="checks.periodic_motion",message="Periodic state drift exceeds tolerance.",object_ids=(joint_id,),evidence=(Evidence(key="maximum_position_drift",actual=maxp,expected=f"<= {position_tolerance}"),Evidence(key="maximum_velocity_drift",actual=maxv,expected=f"<= {velocity_tolerance}"))))
    return _report(check_id=check_id,check_type="periodic_motion",evidence=(Evidence(key="period_pair_count",actual=len(pairs)),Evidence(key="maximum_position_drift",actual=maxp),Evidence(key="maximum_velocity_drift",actual=maxv)),issues=issues)

def check_synchronization(*, motion_result: MotionResult, joint_ids: Sequence[str], target: Any, check_id: str = "synchronization") -> CheckReport:
    from .motion_contracts import CoordinatedMotionProfile
    issues=list(_motion_result_issues(motion_result)); arrivals=[]; errors=[]
    if not isinstance(target, CoordinatedMotionProfile) or set(joint_ids) != set(target.axes):
        return _report(check_id=check_id,check_type="synchronization",issues=(*issues,_issue(code="KINCHECK-CHECK-SYNCHRONIZATION-TARGET-INVALID",stage="checks.synchronization",message="target must be a CoordinatedMotionProfile whose axes match joint_ids.",object_ids=tuple(joint_ids))))
    for jid in joint_ids:
        tr=motion_result.get_joint_trajectory(joint_id=jid)
        if tr is None: issues.append(_issue(code="KINCHECK-CHECK-SYNCHRONIZATION-JOINT-MISSING",stage="checks.synchronization",message="A requested synchronization joint is missing.",object_ids=(jid,))); continue
        for time_s, expected in zip(target.times_s,target.axes[jid]):
            if time_s < tr.times_s[0] or time_s > tr.times_s[-1]:
                issues.append(_issue(code="KINCHECK-CHECK-SYNCHRONIZATION-TIME-MISSING",stage="checks.synchronization",message="A coordinated target time is outside a joint trajectory.",object_ids=(jid,),failure_time_s=time_s))
                continue
            actual = next(
                (
                    left_value + (time_s-left_time)/(right_time-left_time)*(right_value-left_value)
                    for left_time,right_time,left_value,right_value in zip(
                        tr.times_s,tr.times_s[1:],tr.positions,tr.positions[1:]
                    ) if left_time <= time_s <= right_time
                ),
                tr.positions[-1],
            )
            error=abs(actual-expected); errors.append(error)
            if error>target.position_tolerance:
                issues.append(_issue(code="KINCHECK-CHECK-SYNCHRONIZATION-POSITION-FAILED",stage="checks.synchronization",message="A coordinated position exceeds tolerance.",object_ids=(jid,),failure_time_s=time_s,evidence=(Evidence(key="position_error",actual=error,expected=f"<= {target.position_tolerance}"),)))
        arrivals.append((jid,target.times_s[-1]))
    return _report(check_id=check_id,check_type="synchronization",evidence=(Evidence(key="maximum_position_error",actual=max(errors,default=math.inf)),Evidence(key="arrival_times_s",actual=dict(arrivals),unit="s")),issues=issues,metadata={"target":target.to_dict()})


__all__ = [
    "CheckReport",
    "CheckSpec",
    "CheckSuiteReport",
    "CheckType",
    "AssemblyIntegrityReport",
    "ContainmentRelation",
    "IntegrityRelationResult",
    "check_path_tracking", "check_planar_tracking", "check_start_stop_reversal", "check_periodic_motion", "check_synchronization", "check_continuous_interference",
    "check_pose_trajectory",
    "Direction",
    "RatioMeasurement",
    "check_constraint_equation_residuals",
    "check_constraint_residuals",
    "check_joint_limits",
    "check_interference",
    "check_assembly_integrity",
    "check_minimum_clearance",
    "check_motion_envelope",
    "DriverTrackingReport",
    "check_driver_tracking",
    "check_pose_target",
    "check_trajectory",
    "check_transmission_ratio",
    "run_checks",
]
