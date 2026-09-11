from __future__ import annotations

import math

import pytest

from kincheckapi import checks, kinematics
from kincheckapi.assembly import (
    AssemblyModel,
    Closure,
    Component,
    ConnectorRef,
    Constraint,
    Coupling,
    Ground,
    JointLimit,
    Part,
)
from kincheckapi.kinematics_analysis import (
    ReachabilityOptions,
    SingularityOptions,
    WorkspaceOptions,
)
from kincheckapi.kinematics_geometry import PoseTarget, PositionSolveOptions
from kincheckapi.pose import Pose
from kincheckapi.result import ConstraintResidual, MotionResult, Trajectory


NONFINITE = (math.nan, math.inf, -math.inf)


def _assembly() -> AssemblyModel:
    return AssemblyModel(
        assembly_id="assembly.v031.finite",
        parts=(Part(part_id="part"),),
        components=(Component(component_id="component", part_id="part"),),
        grounds=(Ground(component_id="component"),),
    )


def _motion() -> MotionResult:
    return MotionResult(
        scenario_id="scenario.v031.finite",
        assembly_id="assembly.v031.finite",
        status="completed",
        start_time_s=0.0,
        end_time_s=1.0,
        sample_times_s=(0.0, 1.0),
        trajectories=(
            Trajectory(
                component_id="component",
                times_s=(0.0, 1.0),
                poses=(Pose(), Pose()),
                linear_velocities_m_s=((0.0, 0.0, 0.0),) * 2,
                angular_velocities_rad_s=((0.0, 0.0, 0.0),) * 2,
                linear_accelerations_m_s2=((0.0, 0.0, 0.0),) * 2,
                angular_accelerations_rad_s2=((0.0, 0.0, 0.0),) * 2,
            ),
        ),
        constraint_residuals=(
            ConstraintResidual(
                constraint_id="constraint",
                time_s=0.0,
                position_residual_m=0.0,
                orientation_residual_rad=0.0,
            ),
        ),
    )


@pytest.mark.parametrize("value", (*NONFINITE, -1.0))
def test_pose_check_rejects_invalid_override_tolerances(value):
    report = checks.check_pose_target(
        motion_result=_motion(),
        target={"component_id": "component", "pose": Pose()},
        position_tolerance_m=value,
    )
    assert not report.passed
    assert any(issue.code == "KINCHECK-CHECK-POSE-TARGET-INVALID" for issue in report.issues)


@pytest.mark.parametrize(
    "field",
    (
        "max_speed_m_s",
        "max_angular_speed_rad_s",
        "max_acceleration_m_s2",
        "max_angular_acceleration_rad_s2",
        "max_position_residual_m",
        "max_orientation_residual_rad",
    ),
)
@pytest.mark.parametrize("value", (*NONFINITE, -1.0))
def test_trajectory_check_rejects_invalid_limits(field, value):
    report = checks.check_trajectory(
        motion_result=_motion(), component_id="component", **{field: value}
    )
    assert not report.passed
    assert any(issue.code == "KINCHECK-CHECK-TRAJECTORY-LIMIT-INVALID" for issue in report.issues)


@pytest.mark.parametrize("value", (*NONFINITE, -1.0))
def test_residual_checks_reject_invalid_tolerances(value):
    geometric = checks.check_constraint_residuals(
        motion_result=_motion(), position_tolerance_m=value
    )
    equation = checks.check_constraint_equation_residuals(
        motion_result=_motion(), linear_tolerance_m=value
    )
    assert not geometric.passed
    assert not equation.passed
    assert any(issue.code == "KINCHECK-CHECK-CONSTRAINT-TOLERANCE-INVALID" for issue in geometric.issues)
    assert any(issue.code == "KINCHECK-CHECK-EQUATION-TOLERANCE-INVALID" for issue in equation.issues)


@pytest.mark.parametrize("value", NONFINITE)
def test_relationship_models_reject_nonfinite_values(value):
    constraint = Constraint(
        constraint_id="constraint",
        connector_a=ConnectorRef(component_id="a", connector_id="axis"),
        connector_b=ConnectorRef(component_id="b", connector_id="axis"),
    )
    factories = (
        lambda: JointLimit(lower=value, upper=1.0),
        lambda: Coupling(
            coupling_id="coupling",
            coupling_type="gear",
            joint_a_id="a",
            joint_b_id="b",
            ratio=value,
        ),
        lambda: Coupling(
            coupling_id="coupling",
            coupling_type="gear",
            joint_a_id="a",
            joint_b_id="b",
            ratio=1.0,
            phase_offset=value,
        ),
        lambda: Closure(
            closure_id="closure",
            constraint=constraint,
            position_tolerance_m=value,
        ),
        lambda: PoseTarget(
            component_id="component", pose=Pose(), orientation_tolerance_rad=value
        ),
    )
    for factory in factories:
        with pytest.raises(ValueError):
            factory()


@pytest.mark.parametrize("value", NONFINITE)
def test_analysis_options_reject_nonfinite_tolerances(value):
    factories = (
        lambda: PositionSolveOptions(position_tolerance_m=value),
        lambda: ReachabilityOptions(orientation_tolerance_rad=value),
        lambda: SingularityOptions(tolerance=value),
        lambda: WorkspaceOptions(position_tolerance_m=value),
        lambda: WorkspaceOptions(singularity_tolerance=value),
    )
    for factory in factories:
        with pytest.raises(ValueError):
            factory()


@pytest.mark.parametrize("value", NONFINITE)
def test_position_solver_mapping_options_return_structured_failure(value):
    result = kinematics.solve_position(
        assembly=_assembly(), options={"position_tolerance_m": value}
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-POSITION-TOLERANCE-INVALID"


@pytest.mark.parametrize(
    "options",
    (
        {"joint_ranges": {"missing": (0.0, math.inf)}},
        {"joint_ranges": {"missing": (1.0, 0.0)}},
        {"joint_ranges": {"missing": (0.0, 1.0)}, "samples_per_joint": 0},
        {"joint_ranges": {"missing": (0.0, 1.0)}, "max_samples": 0},
    ),
)
def test_workspace_invalid_options_return_structured_failure(options):
    result = kinematics.compute_workspace(
        assembly=_assembly(), target="component", options=options
    )
    assert not result.passed
    assert result.issues[0].code == "KINCHECK-KIN-WORKSPACE-OPTIONS-INVALID"


def test_singularity_and_reachability_invalid_mappings_are_structured():
    singularity = kinematics.find_singularities(
        motion_result=_motion(),
        assembly=_assembly(),
        options={"tolerance": math.nan},
    )
    reachability = kinematics.check_reachability(
        assembly=_assembly(),
        target={"component_id": "component", "pose": Pose()},
        options={"orientation_tolerance_rad": math.inf},
    )
    assert not singularity.passed
    assert singularity.issues[0].code == "KINCHECK-KIN-SINGULARITY-OPTIONS-INVALID"
    assert not reachability.reachable
    assert reachability.issues[0].code == "KINCHECK-KIN-REACHABILITY-OPTIONS-INVALID"
