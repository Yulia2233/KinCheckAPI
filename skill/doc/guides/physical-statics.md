# Physical properties and statics (v0.6.0)

This release adds `kincheckapi.dynamics`. The existing motion compiler retains
its kinematic contract. Never use its placeholder masses or servo forces as
physical evidence.

1. Freeze requirements and independent expectations before modeling.
2. `measure_package_physics(package_path=...)` validates the CADIR package and
   integrates every uniform-density closed BREP. Density is explicit, never a
   material-name guess. `measure_mass_properties` also accepts one BREP plus a
   `PhysicsMaterial`.
3. `build_dynamics_model(assembly=..., manifest=...)` checks one-to-one leaf
   occurrence coverage. Definitions may be shared; every bolt occurrence counts.
   Ground parts stay in the BOM, total mass, static loads and compiled evidence.
4. `compile_dynamics_model` supplies explicit inertials, reconstructs the full
   tensor from compiled `body_iquat`/principal values, and rejects mismatches.
   `validate_physics_conversion` audits the complete source/aggregation chain.
5. Probe the specific operation with `probe_dynamics_capabilities`. A backend
   import succeeding does not imply closed-loop reaction or contact capability.
6. Supply `StaticRequest` with explicit gravity (including an explicit zero),
   all movable joint coordinates, `free`/`locked`/`hold` modes, actual supports,
   and any `WrenchLoad`s. Solve and run `check_wrench_balance` and
   `check_static_load_limits`; completion alone is not an engineering pass.
7. `check_static_geometry` checks every BREP leaf pair at the supplied pose,
   including fixed-group internals. Named `ContactRegion`s permit only local
   functional contact; solid overlap still fails. This does not prove a path
   between poses or frictional contact stability.
8. `motion_package(..., dynamics_model=model, static_results=(result, ...))`
   adds hash-indexed `physics.json`. `read_package` restores the typed physical
   model and static cases. Older packages still load with `dynamics_model=None`.
   Viewer arrows are illustrative lengths; inspect the numerical forces,
   reference points, expression frames, source hash and acceptance status.

## Units and frames

All public quantities use m, kg, s, rad, N, N*m and kg*m2. Tensors are symmetric
row-major 3×3 matrices **about COM**, expressed in `frame_id`. Poses use xyzw;
MuJoCo uses wxyz. For CAD lengths in mm, the unit-density inertia integral has
units mm^5: multiply by density in kg/m3 and 1e-15 (mass uses 1e-9).
Transport with R I Rᵀ, then aggregate with the parallel-axis theorem. A rigid
translation alone does not change COM inertia. No mirroring or scaling is
accepted as a rigid placement.

A load's point and vectors use its expression frame. Force acts on
`component_id`, exerted by `applied_by`. A moment at reference o is
R M + (p−o)×R F. Generalized holding effort is conjugate to the public coordinate
B−A. Joint wrenches say which child group receives the force; the parent receives
the opposite wrench. Ground totals are world-expressed about the world origin.

## Sources and compatibility

The tested native package reader is SimpleCADAPI 2.1.3b3 (canonical tick frames).
Legacy 2.0.4b3 packages may contain integer-valued millimetre frames and fail that
reader. An **explicit** `sdk_python=...` selects an isolated 2.0.4b3 reader and
records its actual version/encoding. There is no fallback, guessed rescaling,
validation bypass or source-package modification. Unknown SDK versions fail.

`read_mjcf_mass_properties` supports explicit MJCF inertials with explicitly
supplied ground properties. Density-only mesh inference is rejected as
`MESH-INERTIA-UNVERIFIED`; it is not BREP mass truth. A CAD payload is an
identity-only `Payload(cad_occurrence_id=...)`. Additional measured mass uses
`properties=...`; supplying both or repeating physical identities fails.

`PhysicsManifest` retains BREP/material/revision hashes, raw volume, density,
mm^5 integrals, occurrence transforms, SDK/kernel versions and integration
budget. Its JSON hash catches modifications; numeric revalidation independently
checks frame transport and rigid-group conservation.

## Limits and interpretation

Static solving covers rigid trees with fixed, revolute and prismatic joints,
valid given poses and ideal fixed supports. A nonzero demand on a free joint
fails. Multiple mounting points identify a total wrench, not individual bearing
loads; requesting individual reactions returns `indeterminate`. Unilateral or
frictional supports return `capability_failed`.

No inverse/forward dynamics, finite actuator response, impact/contact-force
response, stress, deformation, vibration or fatigue is implemented here. A static
rating failure is retained even when mass conversion and equilibrium succeed.
Illustrative material density is not certified material data.

`static_checks=(...)` archives rating/check verdicts alongside static results; failed ratings keep physics acceptance false.

## Static archive integrity

`kincheck.static/1.1` records `DynamicsModel.base_component_properties` before payload addition, the exact payload records, and a model digest. Each `StaticResult` retains its `model_sha256` and typed `request`. Export and read both re-solve that request and compare poses, generalized holding effort, applied loads, joint/support reactions, residuals and status. A passing result must also pass `check_wrench_balance`. Truthful complete failed/indeterminate experiments remain archivable with their failure status. Updating a ZIP member hash alone cannot conceal inconsistent physics.

The digest is a consistency binding, not a digital signature. Earlier unbound `kincheck.static/1.0` development results must be re-solved and re-exported; old motion-only packages remain readable. To extend a restored model, use its `base_component_properties` and existing `payloads` plus the new payload, so additions are counted once and provenance is retained.

Viewer manifests keep `sample_count` for motion and `physics_case_count` for static cases. The static selector uses each result's exact component poses, independently of motion sample times or counts. Direct and package viewers report explicit ratio units, with a `:1` fallback for older manifests.

Static acceptance reports are bound to a model digest and result index. v0.6.0 replays load-limit and wrench-balance reports at read/write boundaries; unknown or unbound reports cannot contribute to `acceptance_passed`.

The serialized `static_checks[i].passed` flag is checked against the reconstructed report before acceptance is computed.
