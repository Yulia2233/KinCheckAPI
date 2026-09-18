"""Structured diagnostics shared by KinCheckAPI public modules.

The types in this module deliberately contain only JSON-serializable facts.  An
Agent can therefore inspect a failed operation without parsing exception text.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping
import json


Severity = Literal["info", "warning", "error"]
ResultStatus = Literal[
    "passed",
    "failed",
    "partial",
    "capability_failed",
    "validation_failed",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class AgentGuidance:
    """Stable repair guidance associated with one public error code."""

    operation: str
    what_happened: str | None = None
    possible_causes: tuple[str, ...] = ()
    how_to_fix: tuple[str, ...] = ()
    documentation_hint: str | None = None


_GUIDANCE_BY_CODE: dict[str, AgentGuidance] = {
    "KINCHECK-INTEGRITY-DISCONNECTED": AgentGuidance(
        operation="check_assembly_integrity",
        possible_causes=("The selected Components do not form one connected network at the reported sample.",),
        how_to_fix=("Add or correct the declared mechanical, containment, guide, or geometric relation.", "Check the reported sample time and repeat the integrity check over the full required window."),
    ),
    "KINCHECK-INTEGRITY-CONTAINMENT-ESCAPED": AgentGuidance(
        operation="check_assembly_integrity",
        possible_causes=("A Component crossed the declared containment or guide boundary.",),
        how_to_fix=("Correct the motion range or containment boundary in the model and verify again.",),
    ),
    "KINCHECK-INTEGRITY-GEOMETRIC-CONNECTION-FAILED": AgentGuidance(
        operation="check_assembly_integrity",
        possible_causes=("A declared geometric connection exceeded its gap or penetration tolerance.",),
        how_to_fix=("Correct the component placement or use a justified geometric connection tolerance.",),
    ),
    "KINCHECK-MJCF-FILE-MISSING": AgentGuidance(
        operation="convert_mjcf",
        possible_causes=(
            "The XML, mapping, or asset directory does not exist at the supplied path.",
        ),
        how_to_fix=(
            "Provide XML, mapping, and mesh assets generated from the same export.",
        ),
    ),
    "KINCHECK-MJCF-MAPPING-INVALID": AgentGuidance(
        operation="convert_mjcf",
        possible_causes=(
            "The XML and mapping were generated from different model revisions.",
        ),
        how_to_fix=("Regenerate the XML and mapping from the same model revision.",),
    ),
    "KINCHECK-ASSEMBLY-VALIDATION-FAILED": AgentGuidance(
        operation="validate_assembly",
        how_to_fix=("Correct every reported assembly issue and validate the assembly again.",),
    ),
    "KINCHECK-ASSEMBLY-TOPOLOGY-VALIDATION-FAILED": AgentGuidance(
        operation="validate_topology",
        how_to_fix=("Correct the reported graph references or topology and validate again.",),
    ),
    "KINCHECK-SCENARIO-VALIDATION-FAILED": AgentGuidance(
        operation="validate_scenario",
        how_to_fix=("Correct the reported scenario fields and validate the scenario again.",),
    ),
    "KINCHECK-BACKEND-UNAVAILABLE": AgentGuidance(
        operation="solve_motion",
        how_to_fix=("Install the declared calculation backend and retry.",),
    ),
    "KINCHECK-KIN-SOLVE-FAILED": AgentGuidance(
        operation="solve_motion",
        how_to_fix=(
            "Inspect the failure time and model constraints, correct the input, and solve again.",
        ),
    ),
    "KINCHECK-CLEARANCE-INTERFERENCE-DETECTED": AgentGuidance(
        operation="check_interference",
        how_to_fix=(
            "Revise the component geometry or motion path, then run the interference check again.",
        ),
    ),
    "KINCHECK-CLEARANCE-MINIMUM-BELOW-THRESHOLD": AgentGuidance(
        operation="check_minimum_clearance",
        how_to_fix=("Increase the component separation or change the motion path, then check again.",),
    ),
    "KINCHECK-CLEARANCE-TRAJECTORY-MISSING": AgentGuidance(
        operation="check_clearance",
        how_to_fix=("Record trajectories for every requested component and run the check again.",),
    ),
    "KINCHECK-CHECK-POSE-TARGET-MISMATCH": AgentGuidance(
        operation="check_pose_target",
        how_to_fix=("Correct the target pose or motion and run the pose check again.",),
    ),
    "KINCHECK-CHECK-CONSTRAINT-RESIDUAL-EXCEEDED": AgentGuidance(
        operation="check_constraint_residuals",
        how_to_fix=("Correct the affected constraint or solver inputs and run the check again.",),
    ),
    "KINCHECK-CHECK-EQUATION-RESIDUAL-EXCEEDED": AgentGuidance(
        operation="check_constraint_equation_residuals",
        how_to_fix=("Correct the affected equation parameters and run the check again.",),
    ),
    "KINCHECK-RESULT-TRAJECTORY-MISSING": AgentGuidance(
        operation="read_motion_result",
        how_to_fix=("Use a recorded object ID and a time within the motion result range.",),
    ),
    "KINCHECK-PACKAGE-VALIDATION-FAILED": AgentGuidance(
        operation="read_package",
        how_to_fix=("Regenerate the .kincheck package and validate it again.",),
    ),
}


def _json_value(value: Any) -> Any:
    """Return a deterministic JSON-compatible representation."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return _json_value(value.to_dict())
    if is_dataclass(value):
        return _json_value(asdict(value))
    return repr(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class Evidence:
    """One machine-readable fact supporting a diagnostic conclusion."""

    key: str
    actual: Any = None
    expected: Any = None
    unit: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "actual": _json_value(self.actual),
            "expected": _json_value(self.expected),
            "unit": self.unit,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class SimIssue:
    """A stable, actionable issue produced by validation or verification."""

    code: str
    severity: Severity
    stage: str
    message: str
    object_ids: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    suggested_actions: tuple[str, ...] = ()
    failure_time_s: float | None = None

    def __post_init__(self) -> None:
        # Every error is actionable even when a lower-level producer omitted
        # guidance.  Keep this fallback generic rather than inferring a cause.
        if self.severity == "error" and not self.suggested_actions:
            object.__setattr__(
                self,
                "suggested_actions",
                ("Inspect the reported evidence, correct the input, and retry the operation.",),
            )
        object.__setattr__(self, "object_ids", tuple(self.object_ids))
        object.__setattr__(self, "source_paths", tuple(self.source_paths))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "suggested_actions", tuple(self.suggested_actions))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "stage": self.stage,
            "message": self.message,
            "object_ids": list(self.object_ids),
            "source_paths": list(self.source_paths),
            "evidence": [item.to_dict() for item in self.evidence],
            "suggested_actions": list(self.suggested_actions),
            "failure_time_s": self.failure_time_s,
        }


class AgentReadableResult:
    """Shared outward-facing behavior for public diagnostic result objects."""

    def format_for_agent(self) -> str:
        return format_result_for_agent(result=self)

    def __str__(self) -> str:
        return self.format_for_agent()

    def raise_if_failed(self) -> None:
        assert_check_passed(check=self)

    def diagnostic_trace(self) -> dict[str, Any]:
        return diagnostic_trace(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationResult(AgentReadableResult):
    """Aggregated validation outcome; validation itself never fails fast."""

    issues: tuple[SimIssue, ...] = ()
    operation: str = "validate"

    @property
    def status(self) -> Literal["passed", "failed"]:
        return "passed" if self.passed else "failed"

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def valid(self) -> bool:
        return self.passed

    @property
    def is_valid(self) -> bool:
        return self.passed

    @property
    def errors(self) -> tuple[SimIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[SimIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "passed": self.passed,
            "operation": self.operation,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendFailure:
    """Sanitized evidence copied from a private calculation backend."""

    backend_id: str
    operation: str
    native_error_type: str
    native_message: str
    backend_version: str | None = None
    native_error_code: str | int | None = None
    failure_time_s: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticReport(AgentReadableResult):
    """Complete diagnostic context attached to a public KinCheckAPI error."""

    issues: tuple[SimIssue, ...] = ()
    failure_time_s: float | None = None
    last_valid_result: Any = None
    backend_failure: BackendFailure | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    operation: str = "diagnose"
    status: ResultStatus | None = None
    traceback: str | None = None

    def __post_init__(self) -> None:
        allowed_statuses = {
            "passed",
            "failed",
            "partial",
            "capability_failed",
            "validation_failed",
        }
        if self.status is not None and self.status not in allowed_statuses:
            raise ValueError(
                "status must be passed, failed, partial, capability_failed, or validation_failed"
            )
        object.__setattr__(self, "issues", tuple(self.issues))
        metadata = dict(self.metadata)
        object.__setattr__(self, "metadata", metadata)
        status = self.status
        if status is None:
            declared = metadata.get("status")
            if declared in {"partial", "capability_failed", "validation_failed", "failed", "passed"}:
                status = declared
            elif self.backend_failure is not None and not self.issues:
                status = "failed"
            else:
                status = "failed" if any(item.severity == "error" for item in self.issues) else "passed"
            object.__setattr__(self, "status", status)

    @property
    def passed(self) -> bool:
        return self.status == "passed" and not any(
            issue.severity == "error" for issue in self.issues
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.diagnostic_trace(),
            "passed": self.passed,
            "operation": self.operation,
            "status": _result_status(self),
            "issues": [issue.to_dict() for issue in self.issues],
            "failure_time_s": diagnostic_trace(self)["failure_time_s"],
            "last_valid_result": _json_value(self.last_valid_result),
            "backend_failure": (
                self.backend_failure.to_dict() if self.backend_failure else None
            ),
            "metadata": _json_value(self.metadata),
        }

@dataclass(frozen=True, slots=True, kw_only=True)
class IssueExplanation:
    """Agent-facing explanation without depending on free-form exception text."""

    cause: str
    impact: str
    evidence: tuple[Evidence, ...]
    object_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    suggested_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Fix:
    """A deliberately small mechanical patch description."""

    operation: str
    target_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


def collect_issues(*, results: Iterable[Any]) -> tuple[SimIssue, ...]:
    """Collect and de-duplicate issues from structured result objects."""

    collected: list[SimIssue] = []
    seen: set[tuple[Any, ...]] = set()
    for result in results:
        if result is None:
            continue
        candidates = result if isinstance(result, SimIssue) else getattr(result, "issues", ())
        if isinstance(candidates, SimIssue):
            candidates = (candidates,)
        for issue in candidates:
            if not isinstance(issue, SimIssue):
                continue
            key = (issue.code, issue.stage, issue.object_ids, issue.source_paths, issue.message)
            if key not in seen:
                seen.add(key)
                collected.append(issue)
    return tuple(collected)


def explain_issue(*, issue: SimIssue) -> IssueExplanation:
    return IssueExplanation(
        cause=issue.message,
        impact=(
            "The requested operation cannot complete."
            if issue.severity == "error"
            else "The operation may complete with reduced confidence."
        ),
        evidence=issue.evidence,
        object_ids=issue.object_ids,
        source_paths=issue.source_paths,
        suggested_actions=issue.suggested_actions,
    )


def create_report(
    *,
    assembly: Any,
    scenario: Any = None,
    motion_result: Any = None,
    clearance_result: Any = None,
    check_results: Iterable[Any] = (),
) -> DiagnosticReport:
    checks = tuple(check_results)
    results = (
        *(item for item in (assembly, scenario, motion_result, clearance_result) if item is not None),
        *checks,
    )
    return DiagnosticReport(
        issues=collect_issues(results=results),
        operation="create_report",
        metadata={
            "assembly_id": getattr(assembly, "assembly_id", None),
            "scenario_id": getattr(scenario, "scenario_id", None),
            "check_ids": tuple(
                check_id
                for item in checks
                if (check_id := getattr(item, "check_id", None)) is not None
            ),
        },
    )


def list_executable_fixes(*, report: DiagnosticReport) -> tuple[Fix, ...]:
    """Return no speculative edits until an issue provides a typed fix payload."""

    return ()


def apply_assembly_fix(*, assembly: Any, fix: Fix) -> Any:
    """Reject automatic edits until typed fix preconditions are implemented."""

    _raise_fix_capability(target_id=fix.target_id)


def apply_scenario_fix(*, scenario: Any, fix: Fix) -> Any:
    """Reject automatic edits until typed fix preconditions are implemented."""

    _raise_fix_capability(target_id=fix.target_id)


def _raise_fix_capability(*, target_id: str) -> None:
    message = "Automatic diagnostic fixes are not implemented in the current release."
    action = "Apply the reported correction explicitly and validate the model again."
    report = DiagnosticReport(
        issues=(
            SimIssue(
                code="KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED",
                severity="error",
                stage="diagnostics.capability",
                message=message,
                object_ids=(target_id,),
                suggested_actions=(action,),
            ),
        )
    )
    from .errors import BackendCapabilityError

    raise BackendCapabilityError(
        code="KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED",
        message=message,
        report=report,
        missing_capabilities=("typed_automatic_fix",),
    )


def _result_issues(result: Any) -> tuple[SimIssue, ...]:
    issues = tuple(getattr(result, "issues", ()) or ())
    if issues:
        return tuple(item for item in issues if isinstance(item, SimIssue))
    report = getattr(result, "report", None)
    return tuple(
        item for item in getattr(report, "issues", ()) if isinstance(item, SimIssue)
    )


def _result_passed(result: Any) -> bool:
    passed = getattr(result, "passed", None)
    if isinstance(passed, bool):
        return passed
    succeeded = getattr(result, "succeeded", None)
    if isinstance(succeeded, bool):
        return succeeded
    status = str(getattr(result, "status", ""))
    reachable = getattr(result, "reachable", None)
    if isinstance(reachable, bool):
        return reachable and not any(
            issue.severity == "error" for issue in _result_issues(result)
        )
    return status in {"passed", "completed", "completed_with_warnings", "succeeded"}


def _result_status(result: Any) -> str:
    raw = str(getattr(result, "status", "") or "")
    if isinstance(result, DiagnosticReport) and result.status:
        raw = result.status
    if raw == "partial":
        return "partial"
    if raw == "capability_failed":
        return "capability_failed"
    if raw == "validation_failed":
        return "validation_failed"
    if raw == "failed":
        return "failed"
    if raw in {"passed", "completed", "completed_with_warnings", "succeeded"}:
        return "passed"
    if getattr(result, "last_valid_result", None) is not None and not _result_passed(result):
        return "partial"
    return "passed" if _result_passed(result) else "failed"


def _result_operation(result: Any, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    operation = getattr(result, "operation", None) or getattr(result, "check_type", None)
    if operation:
        return str(operation)
    metadata = getattr(result, "metadata", {})
    if isinstance(metadata, Mapping) and metadata.get("operation"):
        return str(metadata["operation"])
    names = {
        "ValidationResult": "validate",
        "DiagnosticReport": "diagnose",
        "CheckReport": "run_check",
        "CheckSuiteReport": "run_checks",
        "MotionResult": "solve_motion",
        "SolveAttempt": "try_solve_motion",
        "DofReport": "analyze_dofs",
        "ClosureReport": "analyze_closure",
        "PositionResult": "solve_position",
        "ReachabilityResult": "check_reachability",
        "SingularityReport": "find_singularities",
        "WorkspaceResult": "compute_workspace",
        "ConnectorPathResult": "trace_connector_path",
        "JacobianResult": "compute_jacobian",
        "MobilityReport": "analyze_mobility",
        "MotionSummary": "summarize_motion",
        "TransmissionRatioCheck": "verify_transmission_ratio",
    }
    if isinstance(result, BaseException):
        return "api"
    return names.get(type(result).__name__, type(result).__name__)


def diagnostic_trace(result_or_error: Any, *, include_traceback: bool = False) -> dict[str, Any]:
    """Return stable semantic diagnostics without parsing human-readable output.

    Native traceback capture is opt-in. A previously captured trace is retained
    on serialization; a missing trace is represented by null. Causes are facts
    from the native exception or issue, never guessed from an error code.
    """
    value = result_or_error
    report = getattr(value, "report", None)
    issues = _result_issues(value)
    primary = next((item for item in issues if item.severity == "error"), None)
    passed = _result_passed(value) and not isinstance(value, BaseException)
    operation = _result_operation(value)
    backend = getattr(value, "backend_failure", None) or getattr(report, "backend_failure", None)
    native = getattr(value, "__cause__", None)
    while getattr(native, "__cause__", None) is not None:
        native = native.__cause__
    facts = [*_result_evidence(value), *(fact for item in issues for fact in item.evidence)]
    exception_message = str(value) if isinstance(value, BaseException) else None
    native_type = type(native).__name__ if native is not None else getattr(backend, "native_error_type", None)
    if native_type is None and isinstance(value, BaseException):
        native_type = type(value).__name__
    if native_type is None:
        native_type = next((fact.actual for fact in facts if fact.key == "native_error_type"), None)
    message = getattr(value, "message", None) or (primary.message if primary else None)
    message = message or exception_message or ("The requested operation passed." if passed else "The requested operation did not pass.")
    actions = tuple(dict.fromkeys((*getattr(value, "suggested_actions", ()), *(action for item in issues for action in _issue_actions(item)))))
    if not passed and not actions:
        actions = ("Inspect the recorded evidence and resolve the reported failure before retrying.",)
    ids = tuple(dict.fromkeys((*getattr(value, "object_ids", ()), *(oid for item in issues for oid in item.object_ids))))
    failure_time = getattr(value, "failure_time_s", None)
    if failure_time is None:
        failure_time = getattr(report, "failure_time_s", None)
    if failure_time is None:
        failure_time = min((item.failure_time_s for item in issues if item.failure_time_s is not None), default=None)
    last_valid = getattr(value, "last_valid_result", None)
    if last_valid is None:
        last_valid = getattr(report, "last_valid_result", None)
    trace = getattr(value, "traceback", None) or getattr(report, "traceback", None)
    if include_traceback and isinstance(value, BaseException) and value.__traceback__ is not None:
        import traceback as traceback_module
        trace = "".join(traceback_module.format_exception(type(value), value, value.__traceback__))
    payload = {
        "passed": passed,
        "what_happened": message,
        "cause": str(native) if native is not None else getattr(backend, "native_message", None) or exception_message or (primary.message if primary else message),
        "how_to_fix": list(actions),
        "code": getattr(value, "code", None) or (primary.code if primary else "KINCHECK-OK" if passed else "KINCHECK-UNEXPECTED-ERROR" if isinstance(value, BaseException) else "KINCHECK-RESULT-FAILED"),
        "stage": primary.stage if primary else getattr(value, "stage", None) or operation,
        "object_ids": list(ids),
        "source_paths": list(dict.fromkeys(path for item in issues for path in item.source_paths)),
        "failure_time_s": failure_time,
        "evidence": [fact.to_dict() for fact in facts],
        "last_valid_result": _json_value(last_valid) if last_valid is not value else None,
        "suggested_actions": list(actions),
        "native_error_type": native_type,
    }
    if trace is not None:
        payload["traceback"] = trace
    return payload


def _result_evidence(result: Any) -> tuple[Evidence, ...]:
    values = list(
        item for item in getattr(result, "evidence", ()) if isinstance(item, Evidence)
    )
    name = type(result).__name__
    if name == "ClearanceReport":
        values.extend(
            (
                Evidence(key="event_count", actual=len(getattr(result, "events", ()))),
                Evidence(
                    key="checked_component_pair_count",
                    actual=getattr(result, "checked_component_pair_count", 0),
                ),
                Evidence(
                    key="checked_sample_count",
                    actual=getattr(result, "checked_sample_count", 0),
                ),
                Evidence(
                    key="maximum_penetration_depth_m",
                    actual=getattr(result, "maximum_penetration_depth_m", 0.0),
                    expected=0.0,
                    unit="m",
                ),
                Evidence(
                    key="first_failure_time_s",
                    actual=getattr(result, "first_failure_time_s", None),
                    unit="s",
                ),
                Evidence(
                    key="sampling_scope",
                    actual=getattr(result, "sampling_scope", None),
                ),
                Evidence(
                    key="sampling_period_s",
                    actual=getattr(result, "sampling_period_s", None),
                    unit="s",
                ),
            )
        )
        measurements = tuple(getattr(result, "measurements", ()))
        if measurements:
            values.append(
                Evidence(
                    key="minimum_clearance_m",
                    actual=min(item.minimum_clearance_m for item in measurements),
                    expected=">= 0",
                    unit="m",
                )
            )
    elif name in {"MotionResult", "SolveAttempt"}:
        motion = result
        if name == "SolveAttempt":
            motion = getattr(result, "motion_result", None) or getattr(
                result, "last_valid_result", None
            )
        if motion is not None:
            values.extend(
                (
                    Evidence(key="motion_status", actual=getattr(motion, "status", None)),
                    Evidence(
                        key="sample_count",
                        actual=len(getattr(motion, "sample_times_s", ())),
                    ),
                    Evidence(
                        key="time_range_s",
                        actual=(
                            getattr(motion, "start_time_s", None),
                            getattr(motion, "end_time_s", None),
                        ),
                        unit="s",
                    ),
                    Evidence(
                        key="closure_statuses",
                        actual=getattr(motion, "closure_statuses", None),
                    ),
                )
            )
    elif name == "CheckSuiteReport":
        values.extend(
            Evidence(
                key=f"check.{item.check_id}",
                actual="passed" if item.passed else "failed",
            )
            for item in getattr(result, "reports", ())
        )
    elif name == "SingularityReport":
        values.extend(
            (
                Evidence(
                    key="singular_times_s",
                    actual=getattr(result, "singular_times_s", ()),
                    unit="s",
                ),
                Evidence(key="tolerance", actual=getattr(result, "tolerance", None)),
            )
        )
    elif name == "WorkspaceResult":
        values.extend(
            (
                Evidence(key="sample_count", actual=len(getattr(result, "samples", ()))),
                Evidence(
                    key="reachable_fraction",
                    actual=getattr(result, "reachable_fraction", None),
                ),
            )
        )
    elif name == "AssemblyIntegrityReport":
        values.extend(
            (
                Evidence(
                    key="checked_sample_count",
                    actual=getattr(result, "checked_sample_count", 0),
                ),
                Evidence(
                    key="connected_network_count_by_sample",
                    actual=getattr(result, "connected_network_count_by_sample", ()),
                ),
                Evidence(
                    key="geometric_connection_tolerance_m",
                    actual=getattr(result, "geometric_connection_tolerance_m", None),
                    unit="m",
                ),
                Evidence(
                    key="containment_escape_tolerance_m",
                    actual=getattr(result, "containment_escape_tolerance_m", None),
                    unit="m",
                ),
            )
        )
    elif name == "ConnectorPathResult":
        values.extend(
            (
                Evidence(key="sample_count", actual=len(getattr(result, "times_s", ()))),
                Evidence(
                    key="path_length_m",
                    actual=getattr(result, "path_length_m", None),
                    unit="m",
                ),
            )
        )
    return tuple(values)


def _format_evidence(item: Evidence) -> str:
    fact = f"{item.key}: actual={item.actual!r}"
    if item.expected is not None:
        fact += f", expected={item.expected!r}"
    if item.unit:
        fact += f" {item.unit}"
    return fact


def _guidance_for(code: str) -> AgentGuidance | None:
    return _GUIDANCE_BY_CODE.get(code)


def _issue_actions(issue: SimIssue) -> tuple[str, ...]:
    guidance = _guidance_for(issue.code)
    values = (*issue.suggested_actions, *(guidance.how_to_fix if guidance else ()))
    return tuple(dict.fromkeys(value for value in values if value))


def _append_issue_details(lines: list[str], issue: SimIssue) -> None:
    if issue.object_ids:
        lines.append(f"Objects: {', '.join(issue.object_ids)}")
    if issue.source_paths:
        lines.append(f"Sources: {', '.join(issue.source_paths)}")
    if issue.evidence:
        lines.append("Evidence:")
        lines.extend(f"- {_format_evidence(item)}" for item in issue.evidence)
    if issue.failure_time_s is not None:
        lines.append(f"Failure time: {issue.failure_time_s!r} s")
    guidance = _guidance_for(issue.code)
    if guidance and guidance.possible_causes:
        lines.append("Possible causes:")
        lines.extend(f"- {cause}" for cause in guidance.possible_causes)
    actions = _issue_actions(issue)
    if actions:
        lines.append("How to fix:")
        lines.extend(f"- {action}" for action in actions)


def _append_issue(lines: list[str], issue: SimIssue, *, numbered: bool, index: int) -> None:
    if numbered:
        lines.append(f"Issue {index}: {issue.code}")
    else:
        lines.append(f"Issue: {issue.code}")
    lines.append(f"Stage: {issue.stage}")
    lines.append(f"What happened: {issue.message}")
    _append_issue_details(lines, issue)


def format_result_for_agent(result: Any, operation: str | None = None) -> str:
    """Render the one public Agent-facing representation for a result object."""

    status = _result_status(result)
    issues = _result_issues(result)
    lines = [f"KinCheckAPI validation: {status}", f"Operation: {_result_operation(result, operation)}"]
    if hasattr(result, "check_id"):
        lines.append(f"Check: {getattr(result, 'check_id')}")
    # Suites carry ordered child reports; retain that structure in the text.
    reports = getattr(result, "reports", None)
    if reports is not None and type(result).__name__ == "CheckSuiteReport":
        if not reports:
            lines.append("No issues.")
        for child_index, child in enumerate(reports, start=1):
            child_status = "passed" if getattr(child, "passed", False) else "failed"
            lines.append(f"Check {child_index}: {child.check_id} ({child_status})")
            child_issues = tuple(getattr(child, "issues", ()))
            for issue_index, issue in enumerate(child_issues, start=1):
                _append_issue(lines, issue, numbered=len(child_issues) > 1, index=issue_index)
        evidence = _result_evidence(result)
        if evidence:
            lines.append("Result evidence:")
            lines.extend(f"- {_format_evidence(item)}" for item in evidence)
        lines.append(f"Technical details: {type(result).__name__}")
        return "\n".join(lines)
    if not issues:
        if status == "passed":
            lines.append("No issues.")
        else:
            lines.append("What happened: The operation did not produce a passing result.")
            lines.append("How to fix:")
            lines.append("- Inspect the structured result fields, correct the input, and run the operation again.")
    else:
        for index, issue in enumerate(issues, start=1):
            _append_issue(lines, issue, numbered=len(issues) > 1, index=index)
    evidence = _result_evidence(result)
    if evidence:
        lines.append("Result evidence:")
        lines.extend(f"- {_format_evidence(item)}" for item in evidence)
    failure_time_s = getattr(result, "failure_time_s", None)
    if failure_time_s is not None and not any(
        issue.failure_time_s is not None for issue in issues
    ):
        lines.append(f"Failure time: {failure_time_s!r} s")
    lines.append(f"Technical details: {type(result).__name__}")
    return "\n".join(lines)


def format_report_for_agent(report: DiagnosticReport) -> str:
    """Compatibility name for the single result renderer."""

    return format_result_for_agent(report)


def format_error_for_agent(*, error: Any) -> str:
    """Render one expected KinCheckAPI exception without requiring caller assembly."""

    code = str(getattr(error, "code", type(error).__name__))
    report = getattr(error, "report", None)
    issues = _result_issues(report) if report is not None else ()
    guidance = _guidance_for(code)
    operation = getattr(error, "operation", None)
    if not operation and guidance:
        operation = guidance.operation
    if not operation and report is not None:
        operation = _result_operation(report)
    lines = [f"KinCheckAPI error: {code}", f"Operation: {operation or 'unknown'}"]
    lines.append(f"What happened: {getattr(error, 'message', 'KinCheckAPI operation failed.')}")
    if len(issues) == 1 and issues[0].code == code:
        lines.append(f"Stage: {issues[0].stage}")
        _append_issue_details(lines, issues[0])
    else:
        for index, issue in enumerate(issues, start=1):
            _append_issue(lines, issue, numbered=len(issues) > 1, index=index)
    if not issues:
        object_ids = tuple(getattr(error, "object_ids", ()))
        source_paths = tuple(getattr(error, "source_paths", ()))
        if object_ids:
            lines.append(f"Objects: {', '.join(object_ids)}")
        if source_paths:
            lines.append(f"Sources: {', '.join(source_paths)}")
        actions = tuple(getattr(error, "suggested_actions", ()))
        if guidance:
            actions = (*actions, *guidance.how_to_fix)
        actions = tuple(dict.fromkeys(item for item in actions if item))
        if guidance and guidance.possible_causes:
            lines.append("Possible causes:")
            lines.extend(f"- {cause}" for cause in guidance.possible_causes)
        if actions:
            lines.append("How to fix:")
            lines.extend(f"- {action}" for action in actions)
    backend = getattr(error, "backend_failure", None)
    if backend is not None:
        lines.append(
            "Backend: "
            f"{backend.backend_id}, operation={backend.operation}, "
            f"native_error_type={backend.native_error_type}"
        )
    failure_time_s = getattr(error, "failure_time_s", None)
    if failure_time_s is not None and not any(
        issue.failure_time_s is not None for issue in issues
    ):
        lines.append(f"Failure time: {failure_time_s!r} s")
    last_valid = getattr(error, "last_valid_result", None)
    if last_valid is not None:
        summary = {
            "type": type(last_valid).__name__,
            "status": getattr(last_valid, "status", None),
            "scenario_id": getattr(last_valid, "scenario_id", None),
            "assembly_id": getattr(last_valid, "assembly_id", None),
            "start_time_s": getattr(last_valid, "start_time_s", None),
            "end_time_s": getattr(last_valid, "end_time_s", None),
            "sample_count": len(getattr(last_valid, "sample_times_s", ())),
            "issue_codes": [
                item.code
                for item in getattr(last_valid, "issues", ())
                if isinstance(item, SimIssue)
            ],
        }
        lines.append(f"Last valid result: {_json_value(summary)!r}")
    details = getattr(error, "details", None)
    if details:
        lines.append(f"Details: {_json_value(details)!r}")
    lines.append(f"Technical details: {type(error).__name__}")
    return "\n".join(lines)


def create_backend_failure_report(
    *, scenario: Any, cause: BaseException, partial_result: Any = None
) -> DiagnosticReport:
    """Wrap an unknown backend failure in a stable diagnostic schema."""

    backend_failure = BackendFailure(
        backend_id="unknown",
        operation="solve_motion",
        native_error_type=type(cause).__name__,
        native_message=str(cause),
        failure_time_s=getattr(partial_result, "end_time_s", None),
    )
    scenario_id = getattr(scenario, "scenario_id", "unknown")
    issue = SimIssue(
        code="KINCHECK-BACKEND-UNEXPECTED",
        severity="error",
        stage="backend",
        message="The calculation backend failed during motion solving.",
        object_ids=(scenario_id,),
        evidence=(Evidence(key="native_error_type", actual=type(cause).__name__),),
        suggested_actions=(
            "Inspect the backend installation and retry with the same scenario.",
        ),
        failure_time_s=backend_failure.failure_time_s,
    )
    return DiagnosticReport(
        issues=(issue,),
        failure_time_s=backend_failure.failure_time_s,
        last_valid_result=partial_result,
        backend_failure=backend_failure,
    )


def assert_check_passed(*, check: Any) -> None:
    """Raise :class:`VerificationError` when a structured check failed."""

    if _result_passed(check):
        return
    issues = tuple(getattr(check, "issues", ()))
    existing_report = getattr(check, "report", None)
    if not issues and isinstance(existing_report, DiagnosticReport):
        issues = existing_report.issues
    if not issues:
        evidence = tuple(
            item for item in getattr(check, "evidence", ()) if isinstance(item, Evidence)
        )
        issues = (
            SimIssue(
                code="KINCHECK-VERIFY-FAILED",
                severity="error",
                stage="verification",
                message="The requested structured verification did not pass.",
                evidence=evidence,
                suggested_actions=("Inspect the verification result evidence.",),
            ),
        )
    if isinstance(check, DiagnosticReport) and check.issues == issues:
        report = check
    elif isinstance(existing_report, DiagnosticReport) and existing_report.issues == issues:
        report = existing_report
    else:
        report = DiagnosticReport(
            issues=issues,
            operation=_result_operation(check),
            status=("partial" if _result_status(check) == "partial" else "validation_failed"),
            metadata={"source_result_type": type(check).__name__},
        )
    # Local import prevents the diagnostics/error type dependency becoming cyclic.
    from .errors import VerificationError

    raise VerificationError(
        code="KINCHECK-VERIFY-FAILED",
        message="The requested verification did not pass.",
        report=report,
        check=check,
        operation=_result_operation(check),
    )


def write_report(*, report: DiagnosticReport, path: str | Path) -> None:
    """Write a deterministic JSON diagnostic report."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AgentGuidance",
    "AgentReadableResult",
    "BackendFailure",
    "DiagnosticReport",
    "Evidence",
    "Fix",
    "IssueExplanation",
    "Severity",
    "SimIssue",
    "ValidationResult",
    "apply_assembly_fix",
    "apply_scenario_fix",
    "assert_check_passed",
    "collect_issues",
    "create_backend_failure_report",
    "create_report",
    "explain_issue",
    "format_report_for_agent",
    "format_result_for_agent",
    "format_error_for_agent",
    "list_executable_fixes",
    "write_report",
]
