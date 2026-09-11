"""Closed-form reference motion for the four-bar example.

This module only constructs the historical geometry reference used for package
replay and clearance comparisons. It does not run MuJoCo or independently
measure closure residuals. The recorded zero residuals are reference values.
The entry script supplies the example's modeling-module import path.
"""

from __future__ import annotations

import math

from kincheckapi.pose import Pose
from kincheckapi.result import ConstraintResidual, JointTrajectory, MotionResult, Trajectory

from dimensions import (
    COUPLER_LENGTH,
    CRANK_LENGTH,
    GROUND_LENGTH,
    ROCKER_LENGTH,
    ROCKER_ASSEMBLED_ANGLE_DEG,
)


ROOT_ID = "node/four_bar_linkage"
COUPLER_ID = f"{ROOT_ID}/coupler"
CRANK_ID = f"{ROOT_ID}/crank"
ROCKER_ID = f"{ROOT_ID}/rocker"
CRANK_JOINT = "joint/four_bar_linkage/crank_to_ground"
COUPLER_JOINT = "joint/four_bar_linkage/coupler_to_crank"
ROCKER_JOINT = "joint/four_bar_linkage/rocker_to_ground"
CLOSURE_JOINT = "joint/four_bar_linkage/coupler_to_rocker"


def _z_quaternion(angle_rad: float) -> tuple[float, float, float, float]:
    return (0.0, 0.0, math.sin(angle_rad / 2.0), math.cos(angle_rad / 2.0))


def _four_bar_points(theta: float) -> tuple[tuple[float, float], tuple[float, float], float, float]:
    """Return B, C, coupler angle, and rocker angle in millimetres/radians."""

    dx, dy = GROUND_LENGTH, 0.0
    bx = CRANK_LENGTH * math.cos(theta)
    by = CRANK_LENGTH * math.sin(theta)
    vx, vy = dx - bx, dy - by
    center_distance = math.hypot(vx, vy)
    ux, uy = vx / center_distance, vy / center_distance
    along = (COUPLER_LENGTH**2 - ROCKER_LENGTH**2 + center_distance**2) / (
        2.0 * center_distance
    )
    height = math.sqrt(max(0.0, COUPLER_LENGTH**2 - along**2))
    cx = bx + along * ux - height * uy
    cy = by + along * uy + height * ux
    coupler_angle = math.atan2(cy - by, cx - bx)
    rocker_angle = math.atan2(cy - dy, cx - dx)
    return (bx, by), (cx, cy), coupler_angle, rocker_angle


def _derivatives(values: tuple[float, ...], times: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    velocities: list[float] = []
    for index, _value in enumerate(values):
        if index == 0:
            velocities.append((values[1] - values[0]) / (times[1] - times[0]))
        elif index == len(values) - 1:
            velocities.append((values[-1] - values[-2]) / (times[-1] - times[-2]))
        else:
            velocities.append((values[index + 1] - values[index - 1]) / (times[index + 1] - times[index - 1]))
    accelerations: list[float] = []
    for index, _value in enumerate(velocities):
        if index == 0:
            accelerations.append((velocities[1] - velocities[0]) / (times[1] - times[0]))
        elif index == len(velocities) - 1:
            accelerations.append((velocities[-1] - velocities[-2]) / (times[-1] - times[-2]))
        else:
            accelerations.append((velocities[index + 1] - velocities[index - 1]) / (times[index + 1] - times[index - 1]))
    return tuple(velocities), tuple(accelerations)


def _joint_trajectory(joint_id: str, times: tuple[float, ...], positions: tuple[float, ...]) -> JointTrajectory:
    velocities, accelerations = _derivatives(positions, times)
    return JointTrajectory(
        joint_id=joint_id,
        times_s=times,
        positions=positions,
        velocities=velocities,
        accelerations=accelerations,
    )


def build_reference_motion(assembly_id: str) -> MotionResult:
    sample_count = 301
    duration_s = 10.0
    times = tuple(duration_s * index / (sample_count - 1) for index in range(sample_count))
    crank_positions: list[float] = []
    coupler_positions: list[float] = []
    rocker_positions: list[float] = []
    trajectories: dict[str, list[Pose]] = {
        ROOT_ID: [],
        COUPLER_ID: [],
        CRANK_ID: [],
        ROCKER_ID: [],
    }
    closure_residuals: list[ConstraintResidual] = []
    initial_coupler_angle = _four_bar_points(0.0)[2]
    initial_rocker_angle = math.radians(ROCKER_ASSEMBLED_ANGLE_DEG)
    for time_s in times:
        theta = 2.0 * math.pi * time_s / duration_s
        (bx, by), (cx, cy), coupler_angle, rocker_angle = _four_bar_points(theta)
        bx_m, by_m, cx_m, cy_m = bx / 1000.0, by / 1000.0, cx / 1000.0, cy / 1000.0
        crank_positions.append(theta)
        coupler_positions.append(coupler_angle - theta - initial_coupler_angle)
        rocker_positions.append(rocker_angle - initial_rocker_angle)
        trajectories[ROOT_ID].append(Pose())
        trajectories[COUPLER_ID].append(
            Pose(position_m=(bx_m, by_m, 0.0), orientation_xyzw=_z_quaternion(coupler_angle))
        )
        trajectories[CRANK_ID].append(
            Pose(position_m=(bx_m, by_m, 0.0), orientation_xyzw=_z_quaternion(theta))
        )
        trajectories[ROCKER_ID].append(
            Pose(
                position_m=(cx_m, cy_m, 0.0),
                orientation_xyzw=_z_quaternion(rocker_angle - initial_rocker_angle),
            )
        )
        closure_residuals.append(
            ConstraintResidual(
                constraint_id=CLOSURE_JOINT,
                time_s=time_s,
                position_residual_m=0.0,
                orientation_residual_rad=0.0,
            )
        )
    return MotionResult(
        scenario_id="four_bar_full_revolution_closed_form",
        assembly_id=assembly_id,
        status="completed",
        start_time_s=times[0],
        end_time_s=times[-1],
        sample_times_s=times,
        joint_trajectories=(
            _joint_trajectory(CRANK_JOINT, times, tuple(crank_positions)),
            _joint_trajectory(COUPLER_JOINT, times, tuple(coupler_positions)),
            _joint_trajectory(ROCKER_JOINT, times, tuple(rocker_positions)),
            _joint_trajectory(CLOSURE_JOINT, times, tuple(0.0 for _ in times)),
        ),
        trajectories=tuple(
            Trajectory(component_id=component_id, times_s=times, poses=tuple(poses))
            for component_id, poses in trajectories.items()
        ),
        closure_residuals=tuple(closure_residuals),
        closure_statuses={CLOSURE_JOINT: "passed"},
        backend_id="closed-form-kinematics",
        backend_version="four-bar-circle-intersection-v1",
        metadata={
            "trajectory_source": "exact_planar_four_bar_loop_closure",
            "crank_revolutions": 1.0,
            "sample_count": sample_count,
            "sample_rate_hz": (sample_count - 1) / duration_s,
        },
    )

