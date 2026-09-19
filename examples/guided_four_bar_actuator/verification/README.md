# Guided four-bar actuator verification

Run in the KinCheckAPI environment after building and exporting the model:

```bash
python verification/verify.py model --report output/collision_verification.json
python verification/export_motion_package.py
```

The scope includes all 9 physical occurrences and all 36 pairs, without excluding revolute neighbors. All 6 rigid-group pairs cover the 28 relative-moving physical pairs through their complete constituent meshes. Sampled interference, minimum clearance and continuous checking cover the full 0–2 s motion (201 samples) with a 0.1 mm required gap. The remaining 8 pairs belong to the same rigid group: their relative transforms are invariant, so an initial penetration/clearance check covers their full motion. The base/guard and pin-shoulder/host seating faces may touch without penetration. All physical pairs also receive an independent initial interference check.

`collision_scope.py` expands the validated MJCF geom transforms using recorded parent trajectories and the CAD-exported `collision_meshes/*.stl`. Missing meshes or missing physical occurrences fail the verifier.

A negative control lowers the real coupler mesh by 5 mm at t=1 s. Both sampled and continuous detectors must return `failed` with the crank/coupler IDs and an in-window event. This intentionally invalid linkage pose tests collision detection; it is separate from nominal assembly acceptance.

The verifier also retains topology, closure, driver tracking, limits, rocker trajectory and integrity checks. The export script saves all acceptance reports, coverage and negative-control evidence from the same solve in the `.kincheck` package. It exits nonzero if nominal acceptance or the detector control fails.
