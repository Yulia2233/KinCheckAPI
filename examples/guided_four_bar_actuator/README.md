# Guided four-bar actuator

This is a complete CADIR-to-KinCheckAPI mechanism example. It is intentionally more detailed than a kinematic-only sketch: the package contains a machined base plate with mounting holes and pivot bosses, three forged link bodies with bearing eyes and lightening holes, four physical pivot pins, and a fixed service guard.

The mechanism is a planar crank-rocker loop:

- ground span: 40 mm;
- crank: 20 mm;
- coupler: 50 mm;
- rocker: 35 mm;
- common pivot axis: Z;
- drive: crank, 0.8 rad/s after a 0.2 s hold, then stop at 1.8 s;
- samples: 201 over 2 s.

The CAD source lives under `model/source/`. It uses separate `@scad.part` definitions, explicit connectors, fixed hardware relations, a grounded base, four revolute constraints, and a strict assembly solve. The exporter writes the canonical `.scadpkg`, then CADIR MJCF, mapping and mesh files are written to `model/`.

Run the full flow with the CADIR environment followed by the independent KinCheckAPI environment:

```bash
/Users/liuyu/Documents/cadir/repo/.venv/bin/python model/source/guided_four_bar_actuator.cadir.py
/Users/liuyu/Documents/cadir/repo/.venv/bin/python model/source/export_mjcf.py
/Users/liuyu/Documents/mypapers/CADJ/KinCheckAPI-dynamics/.venv/bin/python verification/verify.py model
/Users/liuyu/Documents/mypapers/CADJ/KinCheckAPI-dynamics/.venv/bin/python verification/export_motion_package.py
```

The verifier checks assembly and topology validity, closed-loop residuals, driver tracking, authored joint limits, rocker angular trajectory, all six rigid-group collision pairs (including joint neighbors), sampled minimum clearance, conservative continuous interference between trajectory samples, and whole-network integrity. All nine physical occurrences (36 pairs) are covered: 28 moving pairs by the complete group meshes and 8 fixed pairs by independent leaf checks plus rigid-relative-transform invariance. No joint-connected pair is excluded. A deliberate mid-motion coupler overlap must be detected by both collision APIs. A successful run returns JSON with `passed: true` and writes the compact evidence summary to `output/verification.json`.

The `.kincheck` artifact in `output/` can be opened with the KinCheckAPI viewer. Its stored verification metadata includes all acceptance reports, all physical/group pair IDs, continuous options and bounds, plus the separately labeled detector negative control. The model is a kinematic verification example; it does not claim strength, fatigue, tolerance compliance, deformable-body safety, or dynamic contact behavior.

The corrected physical stack places crank/rocker at Z=5 mm and the coupler at Z=10 mm (4 mm link thickness, 1 mm between link faces). Ground pins and moving pins use separate shank/head dimensions and seating collars on their host faces; link bores have a 2.30 mm radius around 2.00 mm pins. Guard feet seat on the base top at Z=-4 mm. Projected joint-axis datums and the planar linkage lengths remain unchanged. The source exports individual collision STLs as well as the rigid-group MJCF meshes.
