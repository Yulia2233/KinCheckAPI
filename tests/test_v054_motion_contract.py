from __future__ import annotations
import pytest
from kincheckapi.scenario import MotionSegment, add_joint_motion_segments, add_joint_speed_driver, add_joint_speed_profile, create_scenario, set_run_duration, set_sample_period, set_profile_boundary, validate_scenario, set_joint_home_position, set_initial_state_from_home, scenario_to_dict, scenario_from_dict
from kincheckapi.kinematics import KinematicSolveOptions, backend_capabilities, solve_motion
from kincheckapi.result import IntegrationSample, MotionResult, DriverTarget, DriverTrajectory
from kincheckapi.result import JointTrajectory
from kincheckapi.checks import check_driver_tracking
from kincheckapi.pose import Pose
from kincheckapi import export
from kincheckapi.assembly import AssemblyModel, Component, Part
from kincheckapi.errors import ScenarioValidationError

JOINT = "joint.ex3.ground_crank"

def _scenario(assembly):
    s = create_scenario(scenario_id="v054", assembly=assembly)
    s = set_run_duration(scenario=s, duration_s=.02)
    return set_sample_period(scenario=s, period_s=.01)

def test_motion_segments_allow_adjacent_and_reject_overlap(ex3_assembly):
    s = _scenario(ex3_assembly)
    s = add_joint_motion_segments(scenario=s, joint_id=JOINT, segments=(MotionSegment(start_time_s=0,end_time_s=.01,mode="speed",value=1), MotionSegment(start_time_s=.01,end_time_s=.02,mode="speed",value=0)))
    assert len(s.speed_drivers) == 1
    with pytest.raises(ScenarioValidationError):
            add_joint_motion_segments(scenario=s, joint_id=JOINT, segments=(MotionSegment(start_time_s=0,end_time_s=.02,mode="speed",value=1), MotionSegment(start_time_s=.01,end_time_s=.02,mode="speed",value=0)))
    with pytest.raises(ScenarioValidationError):
        add_joint_motion_segments(scenario=s, joint_id=JOINT, segments=(MotionSegment(start_time_s=0,end_time_s=.01,mode="speed",value=1), MotionSegment(start_time_s=.02,end_time_s=.03,mode="speed",value=2)))
    with pytest.raises(ScenarioValidationError):
        add_joint_motion_segments(scenario=s, joint_id=JOINT, segments=(MotionSegment(start_time_s=0,end_time_s=.01,mode="speed",value=1, interpolation="step"), MotionSegment(start_time_s=.01,end_time_s=.02,mode="speed",value=2, interpolation="linear")))

def test_non_mapping_options_fail_structurally(ex3_assembly):
    with pytest.raises(Exception) as caught:
        solve_motion(scenario=_scenario(ex3_assembly), options=object())
    assert caught.value.code == "KINCHECK-KIN-OPTIONS-INVALID"

def test_home_initial_state_round_trip_and_capabilities(ex3_assembly):
    s = _scenario(ex3_assembly)
    s = set_joint_home_position(scenario=s, joint_id=JOINT, position_rad_or_m=.2)
    s = set_initial_state_from_home(scenario=s)
    assert scenario_from_dict(assembly=ex3_assembly, data=scenario_to_dict(scenario=s)).initial_state_source == "home"
    assert backend_capabilities().joint_types["spherical"] is False

def test_options_are_structured_and_recorded(ex3_assembly):
    s = _scenario(ex3_assembly)
    s = add_joint_speed_driver(scenario=s, joint_id=JOINT, speed_rad_s_or_m_s=0.0, start_time_s=0.0, end_time_s=.02)
    result = solve_motion(scenario=s, options=KinematicSolveOptions(max_integration_step_s=.001, adaptive_sampling=True, max_constraint_iterations=17, position_residual_tolerance_m=2e-5, orientation_residual_tolerance_rad=3e-5))
    assert result.metadata["solve_options"]["max_integration_step_s"] == .001
    assert result.metadata["effective_integration_step_s"] <= .001 / 4
    assert result.metadata["effective_constraint_iterations"] == 17
    assert result.metadata["effective_solver_tolerance"] == pytest.approx(2e-5)
    assert result.driver_trajectories[0].samples[0].target == pytest.approx(0.0)

def test_max_substeps_is_enforced_by_backend(ex3_assembly):
    s = _scenario(ex3_assembly)
    with pytest.raises(Exception, match="KINCHECK-KIN-SOLVE-FAILED"):
        solve_motion(scenario=s, options=KinematicSolveOptions(max_integration_substeps=1))

def test_integration_samples_serialize_and_round_trip(tmp_path):
    driver = DriverTrajectory(joint_id="joint.input", mode="speed", samples=(DriverTarget(joint_id="joint.input", time_s=0.0, mode="speed", target=1.0, actual=1.0, error=0.0),))
    motion = MotionResult(scenario_id="s", assembly_id="a", status="completed", start_time_s=0.0, end_time_s=1.0, sample_times_s=(0.0, 1.0), integration_samples=(IntegrationSample(time_s=0.0, component_poses={"c": Pose()}),), driver_trajectories=(driver,))
    payload = motion.to_dict()
    assert payload["integration_samples"][0]["component_poses"]["c"]["orientation_xyzw"] == [0.0, 0.0, 0.0, 1.0]

def test_integration_samples_survive_kincheck_round_trip(tmp_path):
    assembly = AssemblyModel(assembly_id="a", parts=(Part("p"),), components=(Component("c", "p"),))
    driver = DriverTrajectory(joint_id="joint.input", mode="speed", samples=(DriverTarget(joint_id="joint.input", time_s=0.0, mode="speed", target=1.0, actual=1.0, error=0.0),))
    motion = MotionResult(scenario_id="s", assembly_id="a", status="completed", start_time_s=0.0, end_time_s=1.0, sample_times_s=(0.0, 1.0), integration_samples=(IntegrationSample(time_s=0.0, component_poses={"c": Pose()}),), driver_trajectories=(driver,))
    artifact = export.motion_package(assembly=assembly, motion_result=motion, output_path=tmp_path / "motion.kincheck")
    loaded = export.read_package(path=artifact.path)
    assert loaded.motion_result.integration_samples == motion.integration_samples
    assert loaded.motion_result.driver_trajectories == motion.driver_trajectories
    assert loaded.motion_result.driver_trajectories[0].samples[0].actual == 1.0

def test_driver_tracking_reports_overshoot_separately_and_honors_active_interval(ex3_assembly):
    scenario = _scenario(ex3_assembly)
    scenario = add_joint_speed_driver(scenario=scenario, joint_id=JOINT, speed_rad_s_or_m_s=1.0, start_time_s=.01, end_time_s=.03)
    motion = MotionResult(scenario_id="v054", assembly_id=ex3_assembly.assembly_id, status="completed", start_time_s=0.0, end_time_s=.04, sample_times_s=(0.0,.01,.02,.03,.04), joint_trajectories=(JointTrajectory(joint_id=JOINT, times_s=(0.0,.01,.02,.03,.04), positions=(0,0,0,0,0), velocities=(0,.5,.5,.5,0), accelerations=(0,0,0,0,0)),))
    report = check_driver_tracking(motion_result=motion, scenario=scenario, joint_id=JOINT, tolerance=.6)
    assert report.overshoot == 0.0
    assert report.undertracking == .5
    assert report.valid_sample_count == 5

def test_zero_profile_boundary_applies_before_first_profile_point(ex3_assembly):
    scenario = _scenario(ex3_assembly)
    scenario = set_profile_boundary(scenario=scenario, behavior="zero")
    scenario = add_joint_speed_profile(scenario=scenario, joint_id=JOINT, profile=((.01, 1.0), (.02, 1.0)))
    motion = MotionResult(scenario_id="v054", assembly_id=ex3_assembly.assembly_id, status="completed", start_time_s=0.0, end_time_s=.02, sample_times_s=(0.0,.01,.02), joint_trajectories=(JointTrajectory(joint_id=JOINT, times_s=(0.0,.01,.02), positions=(0,0,0), velocities=(0,1,0), accelerations=(0,0,0)),))
    report = check_driver_tracking(motion_result=motion, scenario=scenario, joint_id=JOINT, tolerance=0.0)
    assert report.first_failure_time_s is None
