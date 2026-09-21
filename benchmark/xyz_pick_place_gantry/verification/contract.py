"""Frozen XYZ contract facts for a future private evaluator.

This file is a non-scoring contract ledger until a positive captured package,
independent evaluator, and negative controls exist. It keeps exact IDs and SI
requirements in one place so a later verifier cannot silently invent them.
"""

from __future__ import annotations

CASE_ID = "xyz_pick_place_gantry"
ROOT = "node/xyz_pick_place_gantry"
MOVABLE_JOINTS = (
    "joint/xyz_pick_place_gantry/x_carriage_to_base",
    "joint/xyz_pick_place_gantry/y_carriage_to_y_bridge",
    "joint/xyz_pick_place_gantry/z_carriage_to_y_bridge",
)
HOME_M = (0.655, 0.000, 0.477)
WORKSPACE_M = {"x": (0.300, 0.680), "y": (-0.150, 0.150), "z": (0.080, 0.550)}
PAYLOAD_MASS_KG = 5.0
GRAVITY_M_S2 = (0.0, 0.0, -9.81)
ACTUATOR_LIMITS = {"x": 180.0, "y": 150.0, "z": 300.0}
CONTACT_CASES = {
    "payload_support": {"normal": (0.0, 0.0, 1.0), "force_n": (0.0, 0.0, 49.05), "mu": 0.12, "area_m2": 0.0192, "normal_limit_n": 100.0, "pressure_limit_pa": 200000.0},
    "x_guide_envelope": {"normal": (0.0, 1.0, 0.0), "force_n": (0.0, 100.0, 0.0), "mu": 0.12, "area_m2": 0.0008, "normal_limit_n": 400.0, "pressure_limit_pa": 200000.0},
    "y_guide_envelope": {"normal": (1.0, 0.0, 0.0), "force_n": (100.0, 0.0, 0.0), "mu": 0.12, "area_m2": 0.0008, "normal_limit_n": 400.0, "pressure_limit_pa": 200000.0},
    "z_guide_envelope": {"normal": (1.0, 0.0, 0.0), "force_n": (100.0, 0.0, 0.0), "mu": 0.12, "area_m2": 0.0008, "normal_limit_n": 500.0, "pressure_limit_pa": 200000.0},
}
MAX_SPEED_M_S = {"x": 0.8, "y": 0.6, "z": 0.3}
MAX_ACCEL_M_S2 = {"x": 2.0, "y": 2.0, "z": 1.0}
MIN_FREE_CLEARANCE_M = 0.0002
GUARD_CLEARANCE_M = 0.050

REQUIRED_PROMPT_CLAIMS = (
    "cad_source_and_occurrence_registry",
    "mass_com_inertia_and_payload_mass",
    "scalar_prismatic_motion_and_limits",
    "finite_actuator_inverse_forward_dynamics",
    "sampled_and_continuous_geometry",
    "direct_drive_actuator_binding",
    "guide_reaction_sharing",
    "coordinated_cartesian_path",
    "structural_strength",
)
