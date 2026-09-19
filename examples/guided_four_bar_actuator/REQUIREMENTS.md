# Requirements: Guided Four-Bar Actuator

- Model: complete mechanism assembly with fixed housing, crank, coupler, rocker, pivot hardware, guide cover and service fasteners.
- Inputs: new parametric SimpleCADAPI/CADIR source; no external reference geometry.
- Units: millimetres in CADIR/SimpleCADAPI; metres, radians and seconds in KinCheckAPI.
- Coordinate convention: XY is the mechanism plane, Z is the common pivot-axis direction; ground pivot A is the assembly origin.
- Geometry targets: base plate with mounting holes and raised pivot bosses; three forged links with bearing eyes, bores, lightening cuts and named pivot connectors; hex-head pivot pins; fixed guide/guard geometry around the swept linkage envelope.
- Motion: planar crank-rocker loop, ground span 40 mm, crank 20 mm, coupler 50 mm, rocker 35 mm; crank completes a controlled partial revolution without violating closure or pivot limits.
- Positioning: explicit connector frames at all pivot axes; ground is fixed; four revolute constraints close the loop; hardware and guard are fixed to ground or their host link.
- Parameters: all link lengths, eye radii, bore radii, plate thickness, hole pitch, guard clearance, bolt dimensions and drive bounds are named in source modules.
- Outputs: CADIR source files, `.scadpkg`, MJCF, mapping, meshes, independent KinCheckAPI verifier, structured JSON report and optional `.kincheck` replay package.
- Validation targets: source builds; assembly solver residuals pass; topology is valid; 201 motion samples are complete; closure residuals, driver tracking, limits, rocker trajectory, mesh interference, minimum clearance and assembly connectivity pass.
- Assumptions: this is a dimensioned concept example, not a strength or manufacturing certification. The guard is fixed geometry with a declared clearance envelope; fastener threads are intentionally represented as smooth pins for kinematics.

## Collision review acceptance

- Keep the original 0–2 s motion and 201 output samples. Check every pair of the four exported rigid groups (6 pairs), including revolute-connected groups, with no pair exclusions and the existing 0.1 mm minimum gap.
- Also check all nine physical occurrences (36 pairs), including hardware and guard parts inside each rigid group, using source-exported leaf meshes and the same recorded group motion. The 28 relative-moving pairs are covered by all 6 complete group-mesh pairs; the 8 rigid-relative pairs are checked at the initial state, which is invariant throughout motion. Fixed mating surfaces may touch; no positive-volume penetration is allowed. Moving physical pairs must have at least 0.1 mm clearance.
- Freeze a deliberately colliding motion regression with the real coupler mesh, and require both sampled and continuous checks to detect it. Retain object IDs, times and geometric evidence in JSON.
- Repair geometry in CAD source: stagger crank/rocker and coupler axial layers, give each pin a shank/head stack matching its host, and seat the fixed guard on the base rather than embedding it. The pin axes remain parallel and linkage center distances remain unchanged.
- Assumptions: use 1 mm axial separation between link layers, radial bore clearance exceeding 0.1 mm, pin heads on +Z and shanks toward -Z. This remains a low-load kinematic concept; no new strength claim.
