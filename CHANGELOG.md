# Changelog

All notable KinCheckAPI changes are documented here.

## [0.7.0] - 2026-09-22

### Added

- Generalized rigid-body states, linear/KKT constraints, reaction-rank diagnostics, source maps, and explicit non-unique reaction handling.
- Coupled penalty contact with normal and Coulomb tangential response, contact events, impulse history, and time-step convergence checks.
- Finite controller and actuator envelopes, emergency-stop and brake policies, deterministic random excitation, wrench profiles, duty-cycle cases, and drive/energy summaries.
- `DynamicsLoadHistory` as a hash-indexed `dynamics.json` member in `.kincheck` packages, with strict schema, model identity, evidence digest, and read-back validation.
- Viewer replay of rigid loads, constraint reactions, contact events, impulses, energy evidence, and time-aligned history records.

### Changed

- KinCheckAPI now exposes only kinematics and rigid-body dynamics. Structural FEA, deformation, stress, structural vibration, and fatigue remain in the separate FEACheckAPI roadmap.
- Package and skill documentation now target the 0.7.0 rigid-dynamics contract.

### Removed

- Legacy structural, modal/vibration, and fatigue reference modules and their KinCheckAPI exports.
