from __future__ import annotations

import math

from kincheckapi import kinematics
from kincheckapi.assembly import AssemblyModel, Component, Ground, Part
from kincheckapi.diagnostics import Evidence, SimIssue
from kincheckapi.kinematics_analysis import WorkspaceOptions
from kincheckapi.kinematics_geometry import PoseTarget, PositionSolveOptions
from kincheckapi.pose import Pose
from kincheckapi.result import ConstraintResidual


def _fixed_assembly() -> AssemblyModel:
    return AssemblyModel(
        assembly_id="assembly.v031.fixed",
        parts=(Part(part_id="part.fixed"),),
        components=(Component(component_id="fixed", part_id="part.fixed"),),
        grounds=(Ground(component_id="fixed"),),
    )


def _rotated_pose(angle_rad: float, *, x_m: float = 0.0) -> Pose:
    return Pose(
        position_m=(x_m, 0.0, 0.0),
        orientation_xyzw=(0.0, 0.0, math.sin(angle_rad / 2.0), math.cos(angle_rad / 2.0)),
    )


def _solve(target: PoseTarget, *, options: PositionSolveOptions | None = None):
    return kinematics.solve_position(
        assembly=_fixed_assembly(), pose_targets=(target,), options=options
    )


def test_position_pass_orientation_fail_is_not_converged():
    result = _solve(
        PoseTarget(
            component_id="fixed",
            pose=_rotated_pose(5e-4, x_m=5e-4),
            position_tolerance_m=1e-3,
            orientation_tolerance_rad=1e-4,
        )
    )
    assert not result.passed
    assert not any(issue.code == "KINCHECK-KIN-POSITION-RESIDUAL-EXCEEDED" for issue in result.issues)
    assert any(issue.code == "KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED" for issue in result.issues)


def test_orientation_pass_position_fail_is_not_converged():
    result = _solve(
        PoseTarget(
            component_id="fixed",
            pose=_rotated_pose(5e-5, x_m=5e-4),
            position_tolerance_m=1e-4,
            orientation_tolerance_rad=1e-3,
        )
    )
    assert not result.passed
    assert any(issue.code == "KINCHECK-KIN-POSITION-RESIDUAL-EXCEEDED" for issue in result.issues)
    assert not any(issue.code == "KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED" for issue in result.issues)


def test_position_and_orientation_must_both_pass():
    result = _solve(
        PoseTarget(
            component_id="fixed",
            pose=_rotated_pose(5e-5, x_m=5e-5),
            position_tolerance_m=1e-4,
            orientation_tolerance_rad=1e-4,
        )
    )
    assert result.passed
    assert result.residuals[0].position_residual_m < 1e-4
    assert result.residuals[0].orientation_residual_rad < 1e-4


def test_pose_target_tolerance_overrides_looser_solver_default():
    result = _solve(
        PoseTarget(
            component_id="fixed",
            pose=_rotated_pose(5e-4),
            position_tolerance_m=1.0,
            orientation_tolerance_rad=1e-4,
        ),
        options=PositionSolveOptions(
            position_tolerance_m=1.0, orientation_tolerance_rad=1.0
        ),
    )
    assert not result.passed
    issue = next(
        item
        for item in result.issues
        if item.code == "KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED"
    )
    evidence = {item.key: item.actual for item in issue.evidence}
    assert evidence["orientation_tolerance_rad"] == 1e-4


def test_pose_target_without_override_uses_solver_tolerances():
    target = PoseTarget(component_id="fixed", pose=_rotated_pose(5e-4))

    loose = _solve(
        target,
        options=PositionSolveOptions(
            position_tolerance_m=1.0, orientation_tolerance_rad=1e-3
        ),
    )
    strict = _solve(
        target,
        options=PositionSolveOptions(
            position_tolerance_m=1.0, orientation_tolerance_rad=1e-4
        ),
    )

    assert loose.passed
    assert not strict.passed
    issue = next(
        item
        for item in strict.issues
        if item.code == "KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED"
    )
    assert {item.key: item.actual for item in issue.evidence}[
        "orientation_tolerance_rad"
    ] == 1e-4


def test_multiple_pose_targets_use_independent_tolerances():
    pose = Pose(position_m=(5e-4, 0.0, 0.0))
    result = kinematics.solve_position(
        assembly=_fixed_assembly(),
        pose_targets=(
            PoseTarget(
                component_id="fixed",
                pose=pose,
                position_tolerance_m=1e-3,
                orientation_tolerance_rad=1e-3,
            ),
            PoseTarget(
                component_id="fixed",
                pose=pose,
                position_tolerance_m=1e-4,
                orientation_tolerance_rad=1e-3,
            ),
        ),
        options=PositionSolveOptions(
            position_tolerance_m=1.0, orientation_tolerance_rad=1.0
        ),
    )
    assert not result.passed
    failures = [
        issue
        for issue in result.issues
        if issue.code == "KINCHECK-KIN-POSITION-RESIDUAL-EXCEEDED"
    ]
    assert len(failures) == 1
    assert {item.key: item.actual for item in failures[0].evidence}["residual_id"] == "pose_target:1"


def test_reachability_inherits_orientation_tolerance_for_mapping_target():
    result = kinematics.check_reachability(
        assembly=_fixed_assembly(),
        target={"component_id": "fixed", "pose": _rotated_pose(5e-4)},
        options={"position_tolerance_m": 1.0, "orientation_tolerance_rad": 1e-4},
    )
    assert not result.reachable
    assert any(
        issue.code == "KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED"
        for issue in result.issues
    )


def test_workspace_keeps_orientation_failure_reason(ex3_assembly, monkeypatch):
    target_id = "cmp.ex3.crank"

    def failed_position(**_):
        issue = SimIssue(
            code="KINCHECK-KIN-ORIENTATION-RESIDUAL-EXCEEDED",
            severity="error",
            stage="kinematics.position",
            message="orientation exceeded",
            evidence=(Evidence(key="orientation_residual_rad", actual=0.2, expected="<= 0.1", unit="rad"),),
        )
        return kinematics.PositionResult(
            passed=False,
            joint_positions={"joint.ex3.ground_crank": 0.0},
            component_poses={target_id: ex3_assembly.get_component(component_id=target_id).initial_pose},
            residuals=(
                ConstraintResidual(
                    constraint_id="pose_target:0",
                    time_s=0.0,
                    position_residual_m=0.0,
                    orientation_residual_rad=0.2,
                ),
            ),
            issues=(issue,),
        )

    monkeypatch.setattr(kinematics, "solve_position", failed_position)
    result = kinematics.compute_workspace(
        assembly=ex3_assembly,
        target=target_id,
        options=WorkspaceOptions(
            joint_ranges={"joint.ex3.ground_crank": (0.0, 0.0)},
            samples_per_joint=2,
        ),
    )
    assert not result.samples[0].reachable
    assert result.samples[0].orientation_residual_rad == 0.2
    assert result.reachable_fraction == 0.0


def test_failure_evidence_uses_separate_metre_and_radian_units():
    result = _solve(
        PoseTarget(
            component_id="fixed",
            pose=_rotated_pose(5e-4, x_m=5e-4),
            position_tolerance_m=1e-4,
            orientation_tolerance_rad=1e-4,
        )
    )
    units = {
        evidence.key: evidence.unit
        for issue in result.issues
        for evidence in issue.evidence
    }
    assert units["position_residual_m"] == "m"
    assert units["orientation_residual_rad"] == "rad"
