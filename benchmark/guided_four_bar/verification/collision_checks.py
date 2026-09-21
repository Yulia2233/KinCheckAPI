"""Complete collision scope and a real-mesh, mid-motion negative control."""
from dataclasses import replace
from pathlib import Path

from kincheckapi.clearance import check_continuous_interference, check_interference, measure_minimum_clearance
from kincheckapi.continuous_result import ContinuousInterferenceOptions
from kincheckapi.pose import Pose

if __package__:
    from .collision_scope import physical_motion
else:
    from collision_scope import physical_motion


def check_fixed_hardware(model_dir: Path, assembly, motion, group_pairs):
    physical, recorded, moving_pairs, fixed_pairs = physical_motion(model_dir, assembly, motion)
    # Rigidly attached leaves have invariant relative placement. Checking their
    # full geometry once covers the entire recorded motion of that rigid group.
    fixed = check_interference(
        assembly=physical, motion_result=recorded, component_pairs=fixed_pairs,
        start_time_s=motion.start_time_s, end_time_s=motion.start_time_s,
        penetration_tolerance_m=0.0, asset_root=model_dir,
    )
    gap = measure_minimum_clearance(
        assembly=physical, motion_result=recorded, component_pairs=fixed_pairs,
        start_time_s=motion.start_time_s, end_time_s=motion.start_time_s,
        minimum_allowed_clearance_m=0.0, asset_root=model_dir,
    )
    leaf_initial = check_interference(
        assembly=physical, motion_result=recorded, component_pairs=moving_pairs,
        start_time_s=motion.start_time_s, end_time_s=motion.start_time_s,
        penetration_tolerance_m=0.0, asset_root=model_dir,
    )
    # Every moving leaf pair belongs to one of the six checked aggregate mesh
    # pairs. Aggregate clearance bounds apply to every constituent mesh pair.
    return (
        fixed.as_check_report(check_id="fixed_hardware_interference"),
        gap.as_check_report(check_id="fixed_hardware_minimum_clearance"),
        leaf_initial.as_check_report(check_id="physical_initial_interference"),
    ), {
        "physical_component_count": len(physical.components),
        "physical_components": tuple(c.component_id for c in physical.components),
        "physical_pair_count": len(moving_pairs) + len(fixed_pairs),
        "moving_physical_pairs": moving_pairs,
        "fixed_physical_pairs": fixed_pairs,
        "continuous_rigid_group_pairs": group_pairs,
        "fixed_scope": "initial mesh queries plus exact rigid-relative-placement invariance",
        "moving_scope": "all constituent meshes covered by all six continuous rigid-group pairs",
        "excluded_pairs": (),
    }


def detector_negative_control(model_dir: Path, assembly, motion, *, crank_id: str, coupler_id: str):
    """Push the real coupler down 5 mm at t=1 s; nominal CAD is never modified.

    This is a detector test, not a valid linkage solve: the injected pose
    deliberately violates the linkage constraint. Its collision reports MUST
    fail, and their events must identify crank/coupler during the chosen window.
    """
    target_time = 1.0
    traces = []
    for trajectory in motion.trajectories:
        if trajectory.component_id == coupler_id and trajectory.connector_id is None:
            poses = tuple(
                Pose(position_m=(p.position_m[0], p.position_m[1], p.position_m[2] - 0.005), orientation_xyzw=p.orientation_xyzw)
                if abs(time - target_time) < 1e-10 else p
                for time, p in zip(trajectory.times_s, trajectory.poses)
            )
            trajectory = replace(trajectory, poses=poses)
        traces.append(trajectory)
    faulty = replace(motion, trajectories=tuple(traces), integration_samples=(),
                     metadata={"fault_injection": "coupler -5 mm Z at 1.0 s; invalid linkage pose used only to test detection"})
    pairs = ((crank_id, coupler_id),)
    arguments = dict(assembly=assembly, motion_result=faulty, component_pairs=pairs,
                     asset_root=model_dir, start_time_s=0.99, end_time_s=1.01)
    sampled = check_interference(**arguments)
    continuous = check_continuous_interference(
        **arguments, options=ContinuousInterferenceOptions(time_tolerance_s=1e-4, max_subdivisions=20000),
    )
    expected_ids = {crank_id, coupler_id}
    detected = (
        sampled.status == "failed" and continuous.status == "failed"
        and any({e.component_a_id, e.component_b_id} == expected_ids and 0.99 < e.time_s < 1.01 for e in sampled.events)
        and any(e.confirmed and {e.component_a_id, e.component_b_id} == expected_ids
                and 0.99 < e.state_time_s < 1.01 for e in continuous.events)
    )
    return {
        "passed": detected,
        "operation": "collision_detector_negative_control",
        "description": "Real coupler mesh lowered 5 mm at t=1 s; a deliberate invalid pose, not the nominal assembly.",
        "expected_detector_status": "failed", "sampled": sampled.to_dict(), "continuous": continuous.to_dict(),
    }
