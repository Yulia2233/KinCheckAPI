# Compact two-stage planetary reducer: before and after repair

English | [简体中文](README_zh.md)

The case uses the same directory structure as the four-bar example:

```text
compact_two_stage_planetary_reducer/
  verification/        verify.py, recording scripts and documentation
  model_before/        archived MJCF, mapping, meshes, product package and source/
  model_after/         corrected MJCF, mapping, meshes, product package and source/
  output/
    before/            expected-failure report and recorded motion package
    after/             passing report and recorded motion package
```

The `scene.xml`, `scene.mapping.json`, and `meshes/` filenames retain the existing
KinCheckAPI directory-input contract. Each model directory includes its own
`compact_two_stage_planetary_reducer.scadpkg` and modeling sources under `source/`.

## Acceptance and repair

Both versions run the same 8 rad/s input for one second, sampled every 0.02 s.
The expected ratio is **20:1**, same direction, with relative tolerance
`1e-3` over 0.1-1.0 s. The corrected verifier additionally requires all **12
explicit mesh equations** and checks their residuals over the entire simulated
window with `1e-8 m` tolerance. Missing equations fail explicitly.

The archived runtime export lost its gear/belt transmission equations. The fixed
version preserves endpoint connector frames, SI pitch radii and all source
relations. The exporter evaluates both mesh members relative to the same carrier;
coaxial duplicate joints become explicit coordinate aliases rather than duplicate
parents or artificial fixed connections. No expected ratio is injected into the
model or solver. Teeth, dimensions and authored geometry remain unchanged.

The compact reducer additionally assigns its previously unmaterialized bearing
parts nominal steel density 7850 kg/m3, consistently with the source's steel
materials; the exporter uses no default-density fallback. This is an explicit
modeling assumption, not a measured material-property claim.

## Run verification

From the KinCheckAPI repository, in the analysis environment:

```bash
.venv-addon/bin/python examples/compact_two_stage_planetary_reducer/verification/simulate_and_record.py
.venv-addon/bin/python examples/compact_two_stage_planetary_reducer/verification/simulate_before_optimization.py
.venv-addon/bin/kincheck verify examples/compact_two_stage_planetary_reducer/model_after --script examples/compact_two_stage_planetary_reducer/verification/verify.py --format json
```

`verify(model_dir)` is independent of modeling modules and returns the public
`CheckSuiteReport`. The after recording command fails if acceptance fails. The
before recording command requires the known failure and marks its evidence
`expected_failure: true`; that is not a mechanism acceptance pass.

Reports and portable native-trajectory packages are written as
`output/<variant>/compact_two_stage_planetary_reducer.verification.json` and
`output/<variant>/compact_two_stage_planetary_reducer.kincheck`. The packages can be opened with
`viewer/kincheck_viewer.py ... --serve`. These are actual solver trajectories,
not an animation generated from the target ratio.

## Rebuild and consume the product package

Use the separate modeling environment with sibling CADIR 2.1.3b3 or later within
the declared compatible range:

```bash
uv run --isolated --no-project --with-editable ../CADIR --python 3.12 python examples/compact_two_stage_planetary_reducer/model_after/source/main.py
.venv-addon/bin/python examples/compact_two_stage_planetary_reducer/model_after/source/export_mjcf.py
.venv-addon/bin/kincheck verify-package examples/compact_two_stage_planetary_reducer/model_after/compact_two_stage_planetary_reducer.scadpkg --work-dir examples/compact_two_stage_planetary_reducer/output/package-work --script examples/compact_two_stage_planetary_reducer/verification/verify.py --format json
```

The archived before package uses the older frame encoding and is intentionally
preserved byte-for-byte; current SDK package consumption rejects it. Rebuild from
the corrected sources instead of editing its archive members. `verify_original.py`
and `README_legacy.md` retain the original acceptance implementation and source
notes. Kinematic acceptance does not establish tooth-contact forces, strength,
lifetime, or continuous-time collision freedom.
