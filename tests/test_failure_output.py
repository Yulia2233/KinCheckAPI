from __future__ import annotations

import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest

from kincheckapi.diagnostics import (
    DiagnosticReport,
    Evidence,
    SimIssue,
    ValidationResult,
    format_report_for_agent,
    format_result_for_agent,
)
from kincheckapi.errors import KinCheckError, VerificationError
from kincheckapi.result import MotionResult


ROOT = Path(__file__).resolve().parents[1]


def _issue(code: str = "KINCHECK-TEST-FAILURE") -> SimIssue:
    return SimIssue(
        code=code,
        severity="error",
        stage="test.failure-output",
        message="A test validation failed.",
        evidence=(Evidence(key="actual", actual=2, expected=1),),
        suggested_actions=("Correct the test input and retry.",),
    )


def test_formatting_api_has_no_style_parameter() -> None:
    assert "style" not in inspect.signature(format_result_for_agent).parameters
    assert "style" not in inspect.signature(format_report_for_agent).parameters
    assert tuple(inspect.signature(ValidationResult.format_for_agent).parameters) == (
        "self",
    )
    assert tuple(inspect.signature(KinCheckError.format_for_agent).parameters) == (
        "self",
    )


def test_structured_records_are_json_safe_and_contain_no_traceback() -> None:
    report = DiagnosticReport(
        issues=(_issue(),),
        operation="validate_test",
        status="validation_failed",
        metadata={"path": Path("model.xml")},
    )
    error = KinCheckError(code="KINCHECK-TEST-FAILURE", report=report)
    for value in (report.to_dict(), error.to_dict()):
        serialized = json.dumps(value, sort_keys=True)
        assert "traceback" not in serialized.lower()
    assert "traceback" not in report.format_for_agent().lower()
    assert "traceback" not in error.format_for_agent().lower()


def test_partial_motion_report_uses_result_serializer_before_dataclass_deepcopy() -> None:
    partial = MotionResult(
        scenario_id="scenario.partial",
        assembly_id="assembly.partial",
        status="partial",
        start_time_s=0.0,
        end_time_s=0.0,
        sample_times_s=(0.0,),
        metadata={"nested": {"readonly": True}},
        issues=(_issue(),),
    )
    report = DiagnosticReport(
        issues=partial.issues,
        last_valid_result=partial,
        status="partial",
    )
    assert report.to_dict()["last_valid_result"] == partial.to_dict()
    json.dumps(report.to_dict())


def test_verification_error_reuses_original_report_text() -> None:
    result = ValidationResult(issues=(_issue(),), operation="validate_test")
    with pytest.raises(VerificationError) as caught:
        result.raise_if_failed()
    assert caught.value.check is result
    assert caught.value.report.issues == result.issues
    assert str(caught.value) == str(result)


def test_fail_emit_writes_object_owned_agent_output() -> None:
    completed = subprocess.run(
        [sys.executable, "fail/04_empty_component_pairs.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["status"] == "validation_failed"
    assert payload["result"]["passed"] is False
    assert payload["agent_output"].startswith("KinCheckAPI validation: failed")
    assert payload["result"]["issues"][0]["code"] in payload["agent_output"]


def test_examples_do_not_hand_format_structured_failures() -> None:
    offenders: list[str] = []
    for directory in ("examples", "instances", "fail"):
        for path in (ROOT / directory).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "raise RuntimeError(check.to_dict())" in text:
                offenders.append(str(path.relative_to(ROOT)))
            if "RuntimeError(json.dumps(" in text:
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders
