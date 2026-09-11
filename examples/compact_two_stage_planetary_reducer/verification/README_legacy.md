> Historical snapshot. See [README.md](README.md) for the current paths and verified workflow.

# Compact two-stage planetary reducer

This example is adapted from SimpleCADAPI repository example
`examples/16_compact_two_stage_planetary_reducer`. It retains the validated
source geometry and assembly constraints, then captures the complete product as
a canonical SimpleCADAPI ProductPackage file.

## Functional design

- Two coaxial fixed-ring planetary stages with three planets per stage.
- Involute herringbone gears, module 0.75 mm, 20 degree pressure angle,
  27 degree helix angle, and 0.02 mm backlash.
- Stage 1 has 12/18/48 sun/planet/ring teeth and a 5:1 analytical ratio.
- Stage 2 has 12/12/36 sun/planet/ring teeth and a 4:1 analytical ratio.
- The stage 1 carrier drives the stage 2 sun, giving 20:1 overall reduction.
- The complete product includes housing, input/output flanges, input shaft,
  carriers, gears, and nine reused radial-bearing subassemblies.
- The current envelope is 58.8 mm outside diameter and 30 mm high.

## Output contract

Run from the CadIR repository environment:

```bash
cd /Users/liuyu/Documents/cadir/repo
.venv/bin/python /Users/liuyu/Documents/mypapers/CADJ/KinCheckAPI/examples/compact_two_stage_planetary_reducer/simplecadapi/main.py
```

The script writes one self-contained file:

```text
examples/compact_two_stage_planetary_reducer/output/compact_two_stage_planetary_reducer.scadpkg
```

The package contains the root Assembly definition, all referenced Part and
bearing Assembly definitions, and its Scene 2.0 data. KinCheckAPI runtime
conversion uses the checked-in `examples/compact_two_stage_planetary_reducer/model/` XML, mapping, and meshes.
`main.py` remains a pure ProductPackage source builder; the KinCheckAPI runtime
entry is `examples/compact_two_stage_planetary_reducer/kincheckapi/verify.py`, which calls `convert_mjcf()` with
that directory.

## Validation

- ProductPackage schema, hashes, object closure, and embedded Scene are checked
  by `read_product_package()` and `validate_product_package()`.
- Loading and materializing the package must reconstruct the 25-component,
  45-constraint root Assembly.
- All 45 top-level constraint residuals must pass strict solving.
- Both planetary tooth equations and the 5:1, 4:1, and 20:1 ratios are asserted.
- When the optional `python-fcl` backend is installed, all current-pose
  leaf-component pairs must pass the 0.02 mm static mesh-penetration threshold;
  otherwise the script reports that this optional check was skipped.
- All 17 reusable Part/Assembly definitions must be present in the package;
  component and constraint IDs are checked for uniqueness.

## Scope boundary

SimpleCADAPI's current pairwise gear and belt constraints do not prove the full
planetary equation in a moving carrier reference frame. The ratios are therefore
analytical design intent, while strict constraint and collision results validate
the authored static assembly. Dynamic motion, gear strength, life, lubrication,
thermal behavior, and manufacturing tolerances are not claimed.

See `SOURCE_DESIGN.md` for the upstream design notes.
