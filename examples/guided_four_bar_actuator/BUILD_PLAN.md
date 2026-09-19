# Build plan: Guided Four-Bar Actuator

## S1 — verification contract

Verifier: `verification/verify.py`.
It consumes only `model/scene.xml`, `model/scene.mapping.json`, `model/meshes/`, and the same-build `model/collision_meshes/`; it does not import SimpleCADAPI.
Known-good criteria: valid assembly/topology; completed motion; closure and equation residuals within tolerance; crank driver error within tolerance; rocker pose stays inside the authored guard envelope; every requested component pair has no sampled penetration and maintains the minimum clearance; the selected mechanism is one connected network.
Known-bad criteria: missing model path, shortened run, invalid pair, partial result, and a deliberately tightened clearance threshold must return structured failure or non-zero CLI status.

## S2 — parametric parts

Files: `model/source/dimensions.py`, `base_plate.py`, `link_bar.py`, `pivot_bolt.py`, `guard.py`.
Each physical part is a separate `@scad.part` result. Parts contain named base, subtractive and finishing features and named connectors.

## S3 — assembly and CADIR export

Files: `model/source/assembly.py`, `model/source/main.py`, `model/source/export_mjcf.py`.
The assembly grounds the base, places three moving links at a closed reference pose, fixes hardware/guard, adds four revolute constraints, solves strictly, captures `.scadpkg`, and exports MJCF + mapping + meshes.

## S4 — KinCheckAPI verification

`verification/verify.py` converts CADIR output, validates the assembly and topology, runs the motion scenario, executes independent checks, and emits compact JSON. `export_motion_package.py` produces the viewer package only after verification inputs are complete.

## S5 — evidence

Record build output, component/joint/equality counts, check statuses, residual extrema, sample counts, clearance extrema, integrity status and output paths in `output/verification.json`.

## Collision review revision

The original two-pair selection missed four initial overlap pairs. The verifier
now checks all six rigid-group pairs, including joint neighbors, for the full
2-second trajectory. Nine physical occurrences and all 36 pairs are accounted
for: 28 relative-moving pairs by the complete group meshes and 8 rigid-relative
pairs by initial mesh tests plus transform invariance. No pair is excluded.
An independent initial test also checks all moving leaf pairs. A real-mesh
negative control introduces a 5 mm coupler displacement at 1 second and must
be rejected by both the sampled and continuous detectors.

The CAD repair staggers lower links (Z=5 mm) and coupler (Z=10 mm), matches
separate ground/link pin stacks, opens link bores to radius 2.30 mm, and seats
the guard feet on the base top. Motion range and the 0.1 mm moving-clearance
threshold are retained. Source validation, per-definition STL exports and the
full acceptance evidence accompany the regenerated package.
