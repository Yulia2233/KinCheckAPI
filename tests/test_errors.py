from __future__ import annotations

from dataclasses import dataclass

import pytest

from kincheckapi.diagnostics import (
    BackendFailure,
    DiagnosticReport,
    Evidence,
    SimIssue,
    ValidationResult,
    assert_check_passed,
    create_backend_failure_report,
)
from kincheckapi.errors import (
    KinCheckError,
    MotionSolveError,
    VerificationError,
)


def issue():
    return SimIssue(
        code="KINCHECK-TEST-FAILED",
        severity="error",
        stage="test",
        message="A structured check failed.",
        object_ids=("joint.test",),
        source_paths=("assembly.json",),
        evidence=(Evidence(key="ratio", actual=3.0, expected=4.0),),
        suggested_actions=("Correct the expected ratio.",),
    )


def test_error_to_dict_and_agent_format_include_actionable_fields():
    report = DiagnosticReport(issues=(issue(),))
    error = KinCheckError(
        code="KINCHECK-TEST-FAILED", message="Validation failed.", report=report
    )
    value = error.to_dict()
    assert value["code"] == "KINCHECK-TEST-FAILED"
    assert value["object_ids"] == ["joint.test"]
    assert value["source_paths"] == ["assembly.json"]
    assert value["suggested_actions"] == ["Correct the expected ratio."]
    assert value["report"]["issues"][0]["evidence"][0]["actual"] == 3.0
    formatted = error.format_for_agent()
    assert "joint.test" in formatted
    assert "Correct the expected ratio" in formatted


def test_direct_error_builds_a_structured_report():
    error = KinCheckError(
        code="KINCHECK-DIRECT",
        message="Direct failure.",
        object_ids=("cmp.test",),
        suggested_actions=("Repair the component.",),
    )
    assert error.report.issues[0].object_ids == ("cmp.test",)
    assert "Repair the component" in error.format_for_agent()


def test_validation_result_reports_errors_and_warnings():
    warning = SimIssue(
        code="KINCHECK-TEST-WARNING",
        severity="warning",
        stage="test",
        message="Warning.",
    )
    result = ValidationResult(issues=(warning, issue()))
    assert not result.passed
    assert len(result.errors) == 1
    assert len(result.warnings) == 1


def test_motion_solve_error_preserves_partial_and_backend_failure():
    backend = BackendFailure(
        backend_id="test",
        backend_version="1.0",
        operation="solve_motion",
        native_error_type="NativeFailure",
        native_error_code=42,
        native_message="did not converge",
        failure_time_s=0.5,
    )
    error = MotionSolveError(
        code="KINCHECK-KIN-SOLVE-FAILED",
        message="Motion solving failed.",
        report=DiagnosticReport(issues=(issue(),), backend_failure=backend),
        failure_time_s=0.5,
        last_valid_result={"status": "partial", "end_time_s": 0.4},
        backend_failure=backend,
    )
    value = error.to_dict()
    assert value["failure_time_s"] == 0.5
    assert value["last_valid_result"]["status"] == "partial"
    assert value["backend_failure"]["native_error_code"] == 42


@dataclass(frozen=True)
class FailedCheck:
    passed: bool = False
    issues: tuple[SimIssue, ...] = (issue(),)

    def to_dict(self):
        return {"passed": self.passed}


def test_assert_check_passed_raises_verification_error_with_check():
    check = FailedCheck()
    with pytest.raises(VerificationError) as caught:
        assert_check_passed(check=check)
    assert caught.value.check is check
    assert caught.value.report.issues == check.issues
    assert caught.value.to_dict()["check"] == {"passed": False}


def test_backend_failure_report_sanitizes_native_exception():
    scenario = type("ScenarioStub", (), {"scenario_id": "scenario.test"})()
    report = create_backend_failure_report(
        scenario=scenario, cause=RuntimeError("native failure")
    )
    assert report.backend_failure.native_error_type == "RuntimeError"
    assert report.issues[0].code == "KINCHECK-BACKEND-UNEXPECTED"
