"""v0.6.0 real physical properties and tree static equilibrium.

Time integration, inverse dynamics, contact response and structural analysis
are intentionally outside this version's capability contract.
"""

from .physics_types import (
    DynamicsModel,
    GravityField,
    Payload,
    PhysicsError,
    PhysicsManifest,
    PhysicsMaterial,
    PhysicsOccurrence,
    PhysicsReport,
    RigidBodyProperties,
    StaticRequest,
    StaticResult,
    SupportSpec,
    WrenchLoad,
)
from .physics_mass import (
    aggregate_mass_properties,
    build_dynamics_model,
    check_mass_properties,
    measure_mass_properties,
    transform_mass_properties,
)
from .physics_cadir import (
    measure_package_physics,
    read_mjcf_mass_properties,
    measure_interface_centers,
)
from .physics_backend import (
    DynamicsCompilation,
    compile_dynamics_model,
    validate_physics_conversion,
)
from .statics import (
    check_static_load_limits,
    check_support,
    check_wrench_balance,
    probe_dynamics_capabilities,
    solve_static_equilibrium,
)

from .physics_geometry import (
    ContactRegion,
    check_static_geometry,
    check_occurrence_support,
)

__all__ = [
    "ContactRegion",
    "check_static_geometry",
    "check_occurrence_support",
    "read_mjcf_mass_properties",
    "measure_interface_centers",
    "DynamicsModel",
    "GravityField",
    "Payload",
    "PhysicsError",
    "PhysicsManifest",
    "PhysicsMaterial",
    "PhysicsOccurrence",
    "PhysicsReport",
    "RigidBodyProperties",
    "StaticRequest",
    "StaticResult",
    "SupportSpec",
    "WrenchLoad",
    "aggregate_mass_properties",
    "build_dynamics_model",
    "check_mass_properties",
    "measure_mass_properties",
    "transform_mass_properties",
    "measure_package_physics",
    "DynamicsCompilation",
    "compile_dynamics_model",
    "validate_physics_conversion",
    "check_static_load_limits",
    "check_support",
    "check_wrench_balance",
    "probe_dynamics_capabilities",
    "solve_static_equilibrium",
]
