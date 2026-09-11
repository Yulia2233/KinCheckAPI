from __future__ import annotations

import pytest

from kincheckapi import export, scenario
from kincheckapi.assembly import AssemblyModel
from kincheckapi.checks import (
    CheckSpec,
    check_constraint_equation_residuals,
    run_checks,
)
from kincheckapi.result import ConstraintEquationResidual, MotionResult


def _residual(
    constraint_id: str,
    value: float,
    *,
    time_s: float = 0.0,
    equation_type: str = "gear",
) -> ConstraintEquationResidual:
    return ConstraintEquationResidual(
        constraint_id=constraint_id,
        time_s=time_s,
        value=value,
        unit="rad" if equation_type == "coupling" else "m",
        equation_type=equation_type,
    )


def _motion(*records: ConstraintEquationResidual) -> MotionResult:
    times = tuple(sorted({item.time_s for item in records})) or (0.0,)
    return MotionResult(
        scenario_id="scenario.v014.equations",
        assembly_id="assembly.v014.equations",
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        constraint_equation_residuals=records,
    )


def _evidence(report) -> dict[str, object]:
    return {item.key: item.actual for item in report.evidence}


def test_equation_check_passes_linear_and_angular_samples_within_tolerance():
    report = check_constraint_equation_residuals(
        motion_result=_motion(
            _residual("gear.a", 1e-9),
            _residual("coupling.a", -2e-9, equation_type="coupling"),
        ),
        linear_tolerance_m=1e-8,
        angular_tolerance_rad=1e-8,
    )

    assert report.passed
    assert _evidence(report)["constraint_count"] == 2


def test_equation_check_reports_first_failure_and_preserves_units():
    report = check_constraint_equation_residuals(
        motion_result=_motion(
            _residual("gear.a", 2e-7, time_s=0.5),
            _residual("gear.a", -4e-7, time_s=1.0),
        ),
        linear_tolerance_m=1e-8,
    )

    assert not report.passed
    issue = report.issues[0]
    assert issue.code == "KINCHECK-CHECK-EQUATION-RESIDUAL-EXCEEDED"
    assert issue.failure_time_s == 0.5
    assert issue.evidence[0].unit == "m"


def test_equation_check_uses_angular_tolerance_for_couplings():
    report = check_constraint_equation_residuals(
        motion_result=_motion(
            _residual("coupling.a", 2e-4, equation_type="coupling")
        ),
        angular_tolerance_rad=1e-5,
        linear_tolerance_m=1.0,
    )

    assert not report.passed
    assert report.issues[0].evidence[0].unit == "rad"


def test_equation_check_filters_type_and_time_window():
    report = check_constraint_equation_residuals(
        motion_result=_motion(
            _residual("gear.early", 1.0, time_s=0.0),
            _residual("belt.late", 1e-10, time_s=1.0, equation_type="belt"),
        ),
        equation_types=("belt",),
        start_time_s=0.5,
        linear_tolerance_m=1e-8,
    )

    assert report.passed
    assert report.metadata["checked_constraint_ids"] == ("belt.late",)


def test_disabled_requested_constraint_is_not_reported_missing():
    report = check_constraint_equation_residuals(
        motion_result=_motion(),
        constraint_ids=("gear.disabled",),
        disabled_constraint_ids=("gear.disabled",),
    )

    assert report.passed
    assert report.metadata["disabled_constraint_ids"] == ("gear.disabled",)


def test_missing_requested_constraint_is_an_explicit_failure():
    report = check_constraint_equation_residuals(
        motion_result=_motion(_residual("gear.present", 0.0)),
        constraint_ids=("gear.missing",),
    )

    assert not report.passed
    assert "KINCHECK-CHECK-EQUATION-CONSTRAINT-NOT-FOUND" in {
        item.code for item in report.issues
    }


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"linear_tolerance_m": -1.0}, "KINCHECK-CHECK-EQUATION-TOLERANCE-INVALID"),
        ({"equation_types": ("unknown",)}, "KINCHECK-CHECK-EQUATION-TYPE-INVALID"),
    ],
)
def test_invalid_equation_check_parameters_are_structured(kwargs, code):
    report = check_constraint_equation_residuals(
        motion_result=_motion(_residual("gear.a", 0.0)), **kwargs
    )

    assert not report.passed
    assert code in {item.code for item in report.issues}


def test_run_checks_dispatches_equation_residual_specs():
    assembly = AssemblyModel(assembly_id="assembly.v014.equations")
    suite = run_checks(
        assembly=assembly,
        motion_result=_motion(_residual("gear.a", 0.0)),
        checks=(
            CheckSpec(
                check_id="mesh-equations",
                check_type="constraint_equation_residuals",
            ),
        ),
    )

    assert suite.passed
    assert suite.reports[0].check_type == "constraint_equation_residuals"


def test_equation_residuals_survive_motion_package_round_trip(tmp_path):
    motion = _motion(
        _residual("gear.a", -2e-9),
        _residual("coupling.a", 3e-9, equation_type="coupling"),
    )
    path = tmp_path / "equations.kincheck"
    export.motion_package(
        assembly=AssemblyModel(assembly_id=motion.assembly_id),
        motion_result=motion,
        output_path=path,
    )

    restored = export.read_package(path=path).motion_result

    assert restored.constraint_equation_residuals == motion.constraint_equation_residuals


def test_run_checks_inherits_disabled_constraints_from_scenario():
    assembly = AssemblyModel(assembly_id="assembly.v014.disabled")
    condition = scenario.create_scenario(
        scenario_id="scenario.v014.disabled", assembly=assembly
    )
    condition = scenario.disable_constraint(
        scenario=condition, constraint_id="gear.disabled"
    )

    suite = run_checks(
        assembly=assembly,
        scenario=condition,
        motion_result=_motion(),
        checks=(
            CheckSpec(
                check_id="disabled-equation",
                check_type="constraint_equation_residuals",
                parameters={"constraint_ids": ("gear.disabled",)},
            ),
        ),
    )

    assert suite.passed
    assert suite.reports[0].metadata["disabled_constraint_ids"] == (
        "gear.disabled",
    )
