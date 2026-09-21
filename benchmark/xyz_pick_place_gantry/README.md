# XYZ pick-and-place gantry benchmark

`prompt.md` is the proposed modeling contract for a three-axis payload gantry.
The benchmark now includes a captured CADIR package generated from the prompt:
`output/xyz_pick_place_gantry.scadpkg`.  `verification/verify.py` remains a
fixed partial-capability evaluator: it reports unsupported electromagnetic,
guide-reaction, Cartesian-path, and structural claims explicitly instead of
turning them into false passes.

The prompt is frozen as a three-axis direct-drive rigid-body model with dual
rails, seated guide blocks, host-mounted fasteners, finite linear actuators,
payload and guard geometry. The verifier runs kinematics, joint limits,
payload workspace bounds, single-network assembly integrity, sampled mesh
interference/clearance (while exempting declared guide contact pairs), explicit
mass/inertia compilation, inverse/forward effort and supplied-force contact
capacity checks. It cannot independently prove electromagnetic stator/forcer
binding, guide reaction sharing, Cartesian coordination or structural
deformation; those claims remain `capability_failed` in the evaluator.

Run the fixed evaluator through the common adapter after capturing a package:

```bash
python benchmark/adapter.py \
  /path/to/xyz_pick_place_gantry.scadpkg \
  benchmark/xyz_pick_place_gantry/verification/verify.py \
  --work-dir /tmp/benchmark-xyz-gantry
```

The evaluator returns `benchmark_ready=false` only for those unsupported
capability claims; all model-backed kinematic, geometry and dynamics checks are
reported separately in the structured result.

The reproducible build source and execution evidence are:

- `model/source/build_xyz_pick_place_gantry.py`
- `output/build.log`
- `output/adapter-result.json`

The current run establishes CADIR conversion, topology, occurrence support,
seated fastener/guide geometry, sampled interference and clearance, mass/inertia
inputs, finite scalar dynamics, and all four declared contact capacity cases.
