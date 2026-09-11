from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from kincheckapi.diagnostics import (
    BackendFailure,
    DiagnosticReport,
    Evidence,
    Fix,
    SimIssue,
    ValidationResult,
    apply_assembly_fix,
    apply_scenario_fix,
    assert_check_passed,
    collect_issues,
    create_backend_failure_report,
    create_report,
    explain_issue,
    format_report_for_agent,
    format_result_for_agent,
    list_executable_fixes,
    write_report,
)
from kincheckapi.errors import (
    AssemblyValidationError,
    BackendCapabilityError,
    BackendUnavailableError,
    KinCheckError,
    GeometryCheckError,
    MotionSolveError,
    ScenarioValidationError,
    VerificationError,
)


def _issue(
    *, code: str = "KINCHECK-TEST-ERROR", severity: str = "error", object_id: str = "joint.1"
) -> SimIssue:
    return SimIssue(
        code=code,
        severity=severity,
        stage="test",
        message=f"Message for {code}.",
        object_ids=(object_id,),
        source_paths=("assembly.json",),
        evidence=(
            Evidence(
                key="ratio", actual=3.0, expected=4.0, unit="1", description="ratio"
            ),
        ),
        suggested_actions=("Correct the input.",),
        failure_time_s=0.5,
    )


def test_evidence_and_issue_to_dict_are_json_compatible():
    evidence = Evidence(
        key="payload",
        actual={"path": Path("assembly.json"), "items": {1, 2}},
        expected=(1, 2),
    )
    value = evidence.to_dict()
    assert value["actual"]["path"] == "assembly.json"
    assert sorted(value["actual"]["items"]) == [1, 2]
    assert value["expected"] == [1, 2]
    assert _issue().to_dict()["evidence"][0]["description"] == "ratio"
    json.dumps(value)


def test_validation_result_aliases_and_partitions():
    warning = _issue(code="KINCHECK-WARN", severity="warning", object_id="joint.2")
    passing = ValidationResult(issues=(warning,))
    assert passing.passed and passing.valid and passing.is_valid
    assert passing.errors == ()
    assert passing.warnings == (warning,)
    failing = ValidationResult(issues=(warning, _issue()))
    assert not failing.passed
    assert failing.to_dict()["passed"] is False


def test_backend_failure_and_report_serialize_partial_state_and_metadata():
    backend = BackendFailure(
        backend_id="backend.test",
        operation="solve_motion",
        native_error_type="ConvergenceError",
        native_message="no convergence",
        backend_version="1.2",
        native_error_code=17,
        failure_time_s=0.5,
    )

    @dataclass(frozen=True)
    class Partial:
        end_time_s: float

    report = DiagnosticReport(
        issues=(_issue(),),
        failure_time_s=0.5,
        last_valid_result=Partial(end_time_s=0.4),
        backend_failure=backend,
        metadata={"path": Path("result.json")},
    )
    value = report.to_dict()
    assert not report.passed
    assert value["last_valid_result"] == {"end_time_s": 0.4}
    assert value["backend_failure"]["native_error_code"] == 17
    assert value["metadata"] == {"path": "result.json"}
    assert report.format_for_agent() == format_report_for_agent(report=report)


def test_collect_issues_accepts_issue_results_and_deduplicates():
    first = _issue()
    same_key = _issue()
    warning = _issue(code="KINCHECK-WARN", severity="warning", object_id="joint.2")
    result = ValidationResult(issues=(same_key, warning))
    assert collect_issues(results=(None, first, result, object())) == (first, warning)


@pytest.mark.parametrize(
    ("severity", "impact"),
    [
        ("error", "cannot complete"),
        ("warning", "reduced confidence"),
    ],
)
def test_explain_issue_preserves_actionable_context(severity, impact):
    issue = _issue(severity=severity)
    explanation = explain_issue(issue=issue)
    assert explanation.cause == issue.message
    assert impact in explanation.impact
    assert explanation.evidence == issue.evidence
    assert explanation.object_ids == issue.object_ids
    assert explanation.source_paths == issue.source_paths
    assert explanation.suggested_actions == issue.suggested_actions


def test_create_report_collects_each_result_and_identity_metadata():
    assembly = type(
        "AssemblyResult", (), {"assembly_id": "assembly.1", "issues": (_issue(),)}
    )()
    scenario = type(
        "ScenarioResult",
        (),
        {
            "scenario_id": "scenario.1",
            "issues": (_issue(code="KINCHECK-SCENARIO-WARN", severity="warning"),),
        },
    )()
    motion = ValidationResult(issues=(_issue(code="KINCHECK-MOTION-ERROR"),))
    report = create_report(assembly=assembly, scenario=scenario, motion_result=motion)
    assert [item.code for item in report.issues] == [
        "KINCHECK-TEST-ERROR",
        "KINCHECK-SCENARIO-WARN",
        "KINCHECK-MOTION-ERROR",
    ]
    assert report.metadata == {
        "assembly_id": "assembly.1",
        "scenario_id": "scenario.1",
        "check_ids": (),
    }


def test_fix_api_current_contract_is_explicitly_unsupported():
    fix = Fix(operation="set_value", target_id="joint.1", parameters={"value": 1.0})
    report = DiagnosticReport(issues=(_issue(),))
    assert fix.confidence == 1.0
    assert list_executable_fixes(report=report) == ()
    with pytest.raises(BackendCapabilityError):
        apply_assembly_fix(assembly="assembly", fix=fix)
    with pytest.raises(BackendCapabilityError):
        apply_scenario_fix(scenario="scenario", fix=fix)


def test_agent_formatter_covers_empty_and_actionable_reports():
    assert format_report_for_agent(report=DiagnosticReport()) == (
        "KinCheckAPI validation: passed\n"
        "Operation: diagnose\n"
        "No issues.\n"
        "Technical details: DiagnosticReport"
    )
    formatted = format_report_for_agent(report=DiagnosticReport(issues=(_issue(),)))
    assert "Issue: KINCHECK-TEST-ERROR" in formatted
    assert "Stage: test" in formatted
    assert "What happened: Message for KINCHECK-TEST-ERROR." in formatted
    assert "Objects: joint.1" in formatted
    assert "Sources: assembly.json" in formatted
    assert "- ratio: actual=3.0, expected=4.0 1" in formatted
    assert "How to fix:\n- Correct the input." in formatted
    assert formatted.endswith("Technical details: DiagnosticReport")


def test_single_agent_formatter_has_no_style_branch_and_preserves_issue_order():
    result = ValidationResult(
        issues=(
            _issue(code="KINCHECK-FIRST"),
            _issue(code="KINCHECK-SECOND"),
        )
    )
    assert str(result) == result.format_for_agent()
    assert result.format_for_agent().index("Issue 1: KINCHECK-FIRST") < result.format_for_agent().index(
        "Issue 2: KINCHECK-SECOND"
    )
    with pytest.raises(TypeError):
        result.format_for_agent("compact")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        format_result_for_agent(result, style="compact")  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "status",
    ["passed", "failed", "partial", "capability_failed", "validation_failed"],
)
def test_diagnostic_status_is_not_collapsed(status):
    issues = () if status == "passed" else (_issue(),)
    report = DiagnosticReport(issues=issues, status=status)
    assert report.format_for_agent().startswith(f"KinCheckAPI validation: {status}")


def test_raise_if_failed_reuses_original_result_output():
    result = ValidationResult(issues=(_issue(),), operation="validate_test")
    with pytest.raises(VerificationError) as caught:
        result.raise_if_failed()
    assert caught.value.check is result
    assert str(caught.value) == str(result)


def test_create_backend_failure_report_preserves_partial_result_time():
    scenario = type("Scenario", (), {"scenario_id": "scenario.1"})()
    partial = type("Partial", (), {"end_time_s": 0.75})()
    report = create_backend_failure_report(
        scenario=scenario, cause=RuntimeError("native details"), partial_result=partial
    )
    assert report.failure_time_s == 0.75
    assert report.last_valid_result is partial
    assert report.backend_failure.failure_time_s == 0.75
    assert report.backend_failure.native_message == "native details"
    assert report.issues[0].object_ids == ("scenario.1",)


def test_assert_check_passed_accepts_success_and_synthesizes_missing_issue():
    assert assert_check_passed(check=type("Check", (), {"passed": True})()) is None
    failed = type("Check", (), {"passed": False})()
    with pytest.raises(VerificationError) as caught:
        assert_check_passed(check=failed)
    assert caught.value.report.issues[0].code == "KINCHECK-VERIFY-FAILED"
    assert caught.value.check is failed


def test_write_report_creates_parent_and_deterministic_json(tmp_path):
    report = DiagnosticReport(issues=(_issue(),), metadata={"z": 1, "a": 2})
    path = tmp_path / "nested" / "report.json"
    write_report(report=report, path=path)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index('"a"') < text.index('"z"')
    assert json.loads(text) == report.to_dict()


@pytest.mark.parametrize(
    "error_type",
    [
        AssemblyValidationError,
        ScenarioValidationError,
        BackendUnavailableError,
        BackendCapabilityError,
        MotionSolveError,
        GeometryCheckError,
        VerificationError,
    ],
)
def test_public_error_classes_share_stable_base_contract(error_type):
    error = error_type(code="KINCHECK-TEST", message="failed")
    assert isinstance(error, KinCheckError)
    assert str(error) == error.format_for_agent()
    assert str(error).startswith("KinCheckAPI error: KINCHECK-TEST\nOperation: ")
    assert "What happened: failed" in str(error)
    assert "How to fix:" in str(error)
    assert str(error).endswith(f"Technical details: {error_type.__name__}")
    with pytest.raises(TypeError):
        error.format_for_agent("compact")  # type: ignore[call-arg]
    assert error.to_dict()["error_type"] == error_type.__name__


def test_base_error_can_derive_message_ids_and_actions_from_report():
    report = DiagnosticReport(
        issues=(
            _issue(object_id="joint.1"),
            _issue(code="KINCHECK-SECOND", object_id="joint.2"),
        )
    )
    error = KinCheckError(code="KINCHECK-WRAPPED", report=report, details={"retry": False})
    assert error.message == report.issues[0].message
    assert error.object_ids == ("joint.1", "joint.2")
    assert error.source_paths == ("assembly.json",)
    assert error.suggested_actions == ("Correct the input.",)
    assert error.to_dict()["details"] == {"retry": False}


def test_validation_result_report_is_normalized_by_error():
    result = ValidationResult(issues=(_issue(),))
    error = KinCheckError(code="KINCHECK-VALIDATION", report=result)
    assert isinstance(error.report, DiagnosticReport)
    assert error.report.issues == result.issues


def test_backend_specialized_errors_add_typed_context():
    failure = BackendFailure(
        backend_id="backend.test",
        operation="solve_motion",
        native_error_type="RuntimeError",
        native_message="failed",
    )
    unavailable = BackendUnavailableError(
        code="KINCHECK-BACKEND-MISSING",
        message="backend missing",
        backend_failure=failure,
    )
    capability = BackendCapabilityError(
        code="KINCHECK-BACKEND-CAPABILITY",
        message="unsupported",
        missing_capabilities=("closure", "contact"),
    )
    assert unavailable.to_dict()["backend_failure"]["backend_id"] == "backend.test"
    assert capability.to_dict()["missing_capabilities"] == ["closure", "contact"]


def test_motion_error_inherits_context_from_report_and_serializes_result_object():
    failure = BackendFailure(
        backend_id="backend.test",
        operation="solve_motion",
        native_error_type="RuntimeError",
        native_message="failed",
    )

    class Partial:
        def to_dict(self):
            return {"status": "partial"}

    partial = Partial()
    report = DiagnosticReport(
        issues=(_issue(),),
        failure_time_s=0.25,
        last_valid_result=partial,
        backend_failure=failure,
    )
    error = GeometryCheckError(code="KINCHECK-GEOMETRY", message="failed", report=report)
    value = error.to_dict()
    assert error.failure_time_s == 0.25
    assert error.last_valid_result is partial
    assert error.backend_failure is failure
    assert value["last_valid_result"] == {"status": "partial"}


def test_verification_error_serializes_plain_check_payload():
    error = VerificationError(
        code="KINCHECK-VERIFY",
        message="failed",
        check={"passed": False, "actual": 3.0},
    )
    assert error.to_dict()["check"] == {"passed": False, "actual": 3.0}
