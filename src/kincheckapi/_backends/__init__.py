"""Private simulation backends.

Nothing from this package is part of the public KinCheckAPI namespace.  Public
modules consume the pure-Python request and result records exported here and
translate backend failures into :mod:`kincheckapi.errors` exceptions.
"""

from .solver_backend import (
    BackendCapabilityFailure,
    BackendCompileFailure,
    BackendInitialStateFailure,
    BackendPose,
    BackendSample,
    BackendSolveFailure,
    BackendSolveResult,
    BackendUnavailable,
    compile_assembly,
    solve_scenario,
)

__all__ = [
    "BackendCapabilityFailure",
    "BackendCompileFailure",
    "BackendInitialStateFailure",
    "BackendPose",
    "BackendSample",
    "BackendSolveFailure",
    "BackendSolveResult",
    "BackendUnavailable",
    "compile_assembly",
    "solve_scenario",
]
