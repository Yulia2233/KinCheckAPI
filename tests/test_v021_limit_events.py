from __future__ import annotations

import pytest

from kincheckapi import scenario
from kincheckapi._backends.solver_backend import BackendSample, BackendSolveResult
from kincheckapi.assembly import AssemblyModel, Component, Connector, ConnectorRef, Ground, Joint, JointLimit, JointType, Part
from kincheckapi.kinematics import _motion_from_backend
from kincheckapi.kinematics_limits import detect_limit_events
from kincheckapi.result import JointTrajectory


@pytest.fixture
def limited_assembly():
    return AssemblyModel(
        assembly_id="review.limit-events",
        parts=(Part("ground", connectors=(Connector("axis"),)), Part("child", connectors=(Connector("axis"),))),
        components=(Component("ground", "ground"), Component("child", "child")),
        joints=(Joint("joint.limited", JointType.REVOLUTE, ConnectorRef("ground", "axis"), ConnectorRef("child", "axis"), limit=JointLimit(-1.0, 1.0)),),
        grounds=(Ground("ground"),),
    )


def _trajectory(positions):
    times = tuple(float(index) for index in range(len(positions)))
    return JointTrajectory(
        joint_id="joint.limited",
        times_s=times,
        positions=tuple(positions),
        velocities=(0.0,) * len(times),
        accelerations=(0.0,) * len(times),
    )


def test_limit_events_empty_inside_range(limited_assembly):
    assert detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((0.0, 0.5)),)) == ()


def test_limit_events_record_upper_reached(limited_assembly):
    events = detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((0.0, 1.0)),))
    assert [(item.side, item.event_type) for item in events] == [("upper", "reached")]
    assert events[0].time_s == pytest.approx(1.0)


def test_limit_events_interpolate_first_upper_contact(limited_assembly):
    events = detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((0.0, 2.0)),))
    assert [(item.side, item.event_type) for item in events] == [("upper", "reached"), ("upper", "exceeded")]
    assert events[0].time_s == pytest.approx(0.5)
    assert events[1].position == pytest.approx(2.0)


def test_limit_events_record_lower_contact_and_exceed(limited_assembly):
    events = detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((0.0, -2.0)),))
    assert [(item.side, item.event_type) for item in events] == [("lower", "reached"), ("lower", "exceeded")]


def test_limit_events_record_initial_exceeded_state(limited_assembly):
    events = detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((1.5, 0.0)),))
    assert events[0].event_type == "exceeded"
    assert events[0].time_s == 0.0


def test_limit_events_only_record_first_event_of_each_kind(limited_assembly):
    events = detect_limit_events(assembly=limited_assembly, joint_trajectories=(_trajectory((0.0, 1.0, 0.0, 1.2, 1.3)),))
    assert sum(item.event_type == "reached" for item in events) == 1
    assert sum(item.event_type == "exceeded" for item in events) == 1


def test_limit_events_skip_unrecorded_limited_joint(limited_assembly):
    assert detect_limit_events(assembly=limited_assembly, joint_trajectories=()) == ()


def test_limit_events_reject_invalid_tolerance(limited_assembly):
    with pytest.raises(ValueError):
        detect_limit_events(assembly=limited_assembly, joint_trajectories=(), tolerance=-1.0)


def test_backend_samples_are_converted_to_motion_limit_events(limited_assembly):
    condition = scenario.create_scenario(scenario_id="review.limit-motion", assembly=limited_assembly)
    condition = scenario.set_run_duration(scenario=condition, duration_s=1.0)
    condition = scenario.set_sample_period(scenario=condition, period_s=1.0)
    backend = BackendSolveResult(
        backend_name="test",
        backend_version="1",
        assembly_id=limited_assembly.assembly_id,
        scenario_id=condition.scenario_id,
        samples=(
            BackendSample(time_s=0.0, joint_positions={"joint.limited": 0.0}, joint_velocities={"joint.limited": 1.0}, component_poses={}, connector_poses={}, constraint_residuals={}),
            BackendSample(time_s=1.0, joint_positions={"joint.limited": 1.0}, joint_velocities={"joint.limited": 1.0}, component_poses={}, connector_poses={}, constraint_residuals={}),
        ),
    )
    motion = _motion_from_backend(scenario=condition, backend_result=backend)
    assert len(motion.limit_events) == 1
    assert motion.limit_events[0].side == "upper"
    assert motion.limit_events[0].event_type == "reached"
