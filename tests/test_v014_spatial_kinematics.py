from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from kincheckapi import export, kinematics, result, scenario
from kincheckapi._backends.solver_backend import (
    BackendPose,
    BackendSample,
    _add_finite_difference_accelerations,
)
from kincheckapi.assembly import (
    AssemblyModel,
    Component,
    Connector,
    ConnectorRef,
    Ground,
    Joint,
    JointType,
    Part,
    Pose,
)


def _assembly(*, joint_type: JointType = JointType.REVOLUTE) -> AssemblyModel:
    part = Part(
        "part",
        connectors=(
            Connector("axis"),
            Connector("offset", pose=Pose(position_m=(0.2, 0.0, 0.0))),
        ),
    )
    return AssemblyModel(
        assembly_id=f"spatial.{joint_type.value}",
        parts=(part,),
        components=(Component("ground", "part"), Component("moving", "part")),
        joints=(
            Joint(
                "joint",
                joint_type,
                ConnectorRef("ground", "axis"),
                ConnectorRef("moving", "axis"),
            ),
        ),
        grounds=(Ground("ground"),),
    )


def _motion(*, joint_type: JointType = JointType.REVOLUTE, velocity: float = 2.0):
    assembly = _assembly(joint_type=joint_type)
    value = scenario.create_scenario(scenario_id="spatial.test", assembly=assembly)
    value = scenario.set_initial_joint_velocity(
        scenario=value, joint_id="joint", velocity_rad_s_or_m_s=velocity
    )
    value = scenario.set_run_duration(scenario=value, duration_s=0.05)
    value = scenario.set_sample_period(scenario=value, period_s=0.05)
    value = scenario.request_component_result(
        scenario=value, component_id="moving", connector_id="offset"
    )
    return kinematics.solve_motion(scenario=value)


def test_rotating_component_has_world_angular_velocity():
    motion = _motion()
    state = result.read_component_state(
        motion_result=motion, component_id="moving", time_s=0.0
    )

    assert state.angular_velocity_rad_s == pytest.approx((0.0, 0.0, 2.0))
    assert state.linear_velocity_m_s == pytest.approx((0.0, 0.0, 0.0))
    assert motion.metadata["spatial_kinematics"]["reference_frame"] == "world"


def test_offset_connector_has_tangential_velocity_and_angular_velocity():
    motion = _motion()
    state = result.read_connector_state(
        motion_result=motion,
        component_id="moving",
        connector_id="offset",
        time_s=0.0,
    )

    assert state.angular_velocity_rad_s == pytest.approx((0.0, 0.0, 2.0))
    assert state.linear_velocity_m_s == pytest.approx((0.0, 0.4, 0.0))


def test_prismatic_component_has_linear_but_no_angular_velocity():
    motion = _motion(joint_type=JointType.PRISMATIC, velocity=0.3)
    state = result.read_component_state(
        motion_result=motion, component_id="moving", time_s=0.0
    )

    assert state.linear_velocity_m_s == pytest.approx((0.0, 0.0, 0.3))
    assert state.angular_velocity_rad_s == pytest.approx((0.0, 0.0, 0.0))


def test_offset_connector_reports_nonzero_centripetal_acceleration():
    motion = _motion()
    state = result.read_connector_state(
        motion_result=motion,
        component_id="moving",
        connector_id="offset",
        time_s=0.0,
    )

    assert state.linear_acceleration_m_s2 == pytest.approx((-0.8, 0.0, 0.0))
    assert motion.metadata["spatial_kinematics"]["acceleration_source"] in {
        "solver_object_acceleration",
        "finite_difference_of_spatial_velocity",
    }


def test_backend_confirmed_stationary_motion_is_zero_not_none():
    motion = _motion(velocity=0.0)
    state = result.read_component_state(
        motion_result=motion, component_id="moving", time_s=0.0
    )

    assert state.linear_velocity_m_s == (0.0, 0.0, 0.0)
    assert state.angular_velocity_rad_s == (0.0, 0.0, 0.0)
    assert state.linear_velocity_m_s is not None


def test_old_backend_sample_and_result_keep_spatial_motion_unknown(tmp_path):
    sample = BackendSample(
        time_s=0.0,
        joint_positions={},
        joint_velocities={},
        component_poses={"moving": BackendPose(position_m=(0.0, 0.0, 0.0), orientation_xyzw=(0.0, 0.0, 0.0, 1.0))},
        connector_poses={},
        constraint_residuals={},
    )
    backend = SimpleNamespace(
        samples=(sample,),
        warnings=(),
        model_summary={},
        metadata={},
        backend_name="legacy",
        backend_version="0",
    )
    value = scenario.create_scenario(scenario_id="legacy", assembly=_assembly())
    value = scenario.set_run_duration(scenario=value, duration_s=1.0)
    value = scenario.set_sample_period(scenario=value, period_s=1.0)
    motion = kinematics._motion_from_backend(scenario=value, backend_result=backend)
    trajectory = result.read_trajectory(motion_result=motion, component_id="moving")

    assert trajectory.linear_velocities_m_s is None
    assert result.read_component_state(
        motion_result=motion, component_id="moving", time_s=0.0
    ).angular_acceleration_rad_s2 is None
    path = tmp_path / "legacy.kincheck"
    export.motion_package(assembly=value.assembly, motion_result=motion, output_path=path)
    restored = export.read_package(path=path).motion_result
    assert result.read_trajectory(
        motion_result=restored, component_id="moving"
    ).linear_velocities_m_s is None


def test_requested_scope_does_not_export_residual_only_components():
    motion = _motion()

    assert {trajectory.component_id for trajectory in motion.trajectories} == {"moving"}
    assert all(trajectory.linear_velocities_m_s is not None for trajectory in motion.trajectories)


def test_spatial_channels_round_trip_and_interpolate(tmp_path):
    motion = _motion()
    path = tmp_path / "motion.kincheck"
    export.motion_package(assembly=_assembly(), motion_result=motion, output_path=path)
    restored = export.read_package(path=path).motion_result
    state = result.read_connector_state(
        motion_result=restored,
        component_id="moving",
        connector_id="offset",
        time_s=0.025,
    )

    assert state.linear_velocity_m_s is not None
    assert math.hypot(*state.linear_velocity_m_s[:2]) == pytest.approx(0.4, rel=2e-3)
    assert state.angular_velocity_rad_s == pytest.approx((0.0, 0.0, 2.0))
    assert state.linear_acceleration_m_s2 is not None


def test_acceleration_fallback_uses_actual_nonuniform_sample_times():
    pose = BackendPose(position_m=(0.0, 0.0, 0.0), orientation_xyzw=(0.0, 0.0, 0.0, 1.0))
    samples = tuple(
        BackendSample(
            time_s=time_s,
            joint_positions={},
            joint_velocities={},
            component_poses={"moving": pose},
            connector_poses={},
            constraint_residuals={},
            component_linear_velocities={"moving": (time_s * time_s, 0.0, 0.0)},
            component_angular_velocities={"moving": (0.0, 0.0, time_s)},
        )
        for time_s in (0.0, 0.5, 2.0)
    )

    accelerated = _add_finite_difference_accelerations(samples)

    assert accelerated[1].component_linear_accelerations["moving"] == pytest.approx((2.0, 0.0, 0.0))
    assert accelerated[1].component_angular_accelerations["moving"] == pytest.approx((0.0, 0.0, 1.0))
