"""Stable public exception hierarchy for KinCheckAPI."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .diagnostics import (
    BackendFailure,
    DiagnosticReport,
    SimIssue,
    ValidationResult,
    _json_value,
    format_error_for_agent,
    diagnostic_trace,
)


_ERROR_OPERATION = {
    "MJCFAdapterError": "convert_mjcf",
    "AssemblyValidationError": "validate_assembly",
    "ScenarioValidationError": "validate_scenario",
    "BackendUnavailableError": "solve_motion",
    "BackendCapabilityError": "solve_motion",
    "MotionSolveError": "solve_motion",
    "GeometryCheckError": "check_geometry",
    "VerificationError": "verify",
    "VisualizationExportError": "export_viewer",
    "MotionPackageError": "motion_package",
}

_ERROR_STATUS = {
    "AssemblyValidationError": "validation_failed",
    "ScenarioValidationError": "validation_failed",
    "BackendUnavailableError": "capability_failed",
    "BackendCapabilityError": "capability_failed",
}


def _ids_from_report(report: DiagnosticReport | None, field: str) -> tuple[str, ...]:
    if report is None:
        return ()
    values: list[str] = []
    for issue in report.issues:
        for value in getattr(issue, field):
            if value not in values:
                values.append(value)
    return tuple(values)


class KinCheckError(Exception):
    """Base class for all expected KinCheckAPI domain failures."""

    def __init__(
        self,
        *,
        code: str,
        message: str | None = None,
        report: DiagnosticReport | ValidationResult | None = None,
        object_ids: Sequence[str] = (),
        source_paths: Sequence[str] = (),
        suggested_actions: Sequence[str] = (),
        details: Mapping[str, Any] | None = None,
        operation: str | None = None,
        status: str | None = None,
        stage: str | None = None,
    ) -> None:
        if message is None:
            if report and report.issues:
                message = report.issues[0].message
            else:
                message = "KinCheckAPI operation failed."
        operation = operation or _ERROR_OPERATION.get(type(self).__name__, "api")
        status = status or _ERROR_STATUS.get(type(self).__name__, "failed")
        self.code = code
        self.message = message
        if isinstance(report, ValidationResult):
            report = DiagnosticReport(
                issues=report.issues,
                operation=report.operation,
                status="validation_failed" if not report.passed else "passed",
            )
        if report is None:
            report = DiagnosticReport(
                issues=(
                    SimIssue(
                        code=code,
                        severity="error",
                        stage=stage or "api",
                        message=message,
                        object_ids=tuple(object_ids),
                        source_paths=tuple(source_paths),
                        suggested_actions=tuple(suggested_actions),
                    ),
                ),
                operation=operation,
                status=status,
            )
        self.report = report
        self.operation = operation
        self.status = status
        self.object_ids = tuple(object_ids) or _ids_from_report(self.report, "object_ids")
        self.source_paths = tuple(source_paths) or _ids_from_report(self.report, "source_paths")
        report_actions: list[str] = []
        for issue in self.report.issues:
            for action in issue.suggested_actions:
                if action not in report_actions:
                    report_actions.append(action)
        self.suggested_actions = tuple(suggested_actions) or tuple(report_actions)
        self.details = dict(details or {})
        super().__init__(f"{code}: {message}")

    def __str__(self) -> str:
        return self.format_for_agent()

    def to_dict(self, *, include_traceback: bool = False) -> dict[str, Any]:
        return {
            **diagnostic_trace(self, include_traceback=include_traceback),
            "error_type": type(self).__name__,
            "code": self.code,
            "message": self.message,
            "operation": self.operation,
            "status": self.status,
            "object_ids": list(self.object_ids),
            "source_paths": list(self.source_paths),
            "suggested_actions": list(self.suggested_actions),
            "details": _json_value(self.details),
            "report": self.report.to_dict(),
        }

    def format_for_agent(self) -> str:
        return format_error_for_agent(error=self)


class MJCFAdapterError(KinCheckError):
    """A CADIR MJCF source cannot be converted into an AssemblyModel."""


class AssemblyValidationError(KinCheckError):
    """The assembly model is invalid or contains broken references."""


class ScenarioValidationError(KinCheckError):
    """The scenario contains invalid time, state, driver, or object data."""


class BackendUnavailableError(KinCheckError):
    """The requested calculation backend cannot be loaded."""

    def __init__(self, *, backend_failure: BackendFailure | None = None, **kwargs: Any) -> None:
        self.backend_failure = backend_failure
        super().__init__(**kwargs)

    def to_dict(self, *, include_traceback: bool = False) -> dict[str, Any]:
        value = super().to_dict(include_traceback=include_traceback)
        value["backend_failure"] = (
            self.backend_failure.to_dict() if self.backend_failure else None
        )
        return value


class BackendCapabilityError(KinCheckError):
    """The backend cannot represent an explicitly requested capability."""

    def __init__(self, *, missing_capabilities: Sequence[str] = (), **kwargs: Any) -> None:
        self.missing_capabilities = tuple(missing_capabilities)
        super().__init__(**kwargs)

    def to_dict(self, *, include_traceback: bool = False) -> dict[str, Any]:
        value = super().to_dict(include_traceback=include_traceback)
        value["missing_capabilities"] = list(self.missing_capabilities)
        return value


class MotionSolveError(KinCheckError):
    """Motion solving started but failed before producing a complete result."""

    def __init__(
        self,
        *,
        failure_time_s: float | None = None,
        last_valid_result: Any = None,
        backend_failure: BackendFailure | None = None,
        **kwargs: Any,
    ) -> None:
        report = kwargs.get("report")
        self.failure_time_s = (
            failure_time_s
            if failure_time_s is not None
            else getattr(report, "failure_time_s", None)
        )
        self.last_valid_result = (
            last_valid_result
            if last_valid_result is not None
            else getattr(report, "last_valid_result", None)
        )
        self.backend_failure = (
            backend_failure
            if backend_failure is not None
            else getattr(report, "backend_failure", None)
        )
        super().__init__(**kwargs)

    def to_dict(self, *, include_traceback: bool = False) -> dict[str, Any]:
        value = super().to_dict(include_traceback=include_traceback)
        value.update(
            {
                "failure_time_s": self.failure_time_s,
                "last_valid_result": (
                    self.last_valid_result.to_dict()
                    if hasattr(self.last_valid_result, "to_dict")
                    else _json_value(self.last_valid_result)
                ),
                "backend_failure": (
                    self.backend_failure.to_dict() if self.backend_failure else None
                ),
            }
        )
        return value


class GeometryCheckError(MotionSolveError):
    """A geometry interference, clearance, or envelope operation failed."""


class VerificationError(KinCheckError):
    """A caller explicitly required a structured check to pass."""

    def __init__(self, *, check: Any = None, **kwargs: Any) -> None:
        self.check = check
        super().__init__(**kwargs)

    def to_dict(self, *, include_traceback: bool = False) -> dict[str, Any]:
        value = super().to_dict(include_traceback=include_traceback)
        value["check"] = (
            self.check.to_dict() if hasattr(self.check, "to_dict") else _json_value(self.check)
        )
        return value

    def format_for_agent(self) -> str:
        # A strict validation failure is the same diagnostic, not a newly
        # interpreted error.  This keeps direct and raised output identical.
        if self.check is not None and hasattr(self.check, "format_for_agent"):
            return self.check.format_for_agent()
        if self.check is not None and self.report is not None:
            return self.report.format_for_agent()
        return super().format_for_agent()


class VisualizationExportError(KinCheckError):
    """A motion viewer could not be exported from public assembly/result data."""


class MotionPackageError(KinCheckError):
    """A portable .kincheck package could not be written, read, or validated."""


__all__ = [
    "KinCheckError",
    "MJCFAdapterError",
    "AssemblyValidationError",
    "ScenarioValidationError",
    "BackendUnavailableError",
    "BackendCapabilityError",
    "MotionSolveError",
    "GeometryCheckError",
    "VerificationError",
    "VisualizationExportError",
    "MotionPackageError",
]
