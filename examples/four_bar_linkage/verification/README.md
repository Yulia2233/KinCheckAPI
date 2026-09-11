# Four-bar linkage: before and after optimization

English | [简体中文](README_zh.md)

![Four-bar linkage before and after optimization](../output/comparison.gif)

*Both actual model meshes replay the same closed-form reference trajectory in sync.*

The example root contains exactly four directories:

```text
four_bar_linkage/
├── verification/             # Verification, STEP export, GIF rendering, and documentation
├── model_before/             # Original MJCF, mapping, meshes, scadpkg, and source/
├── model_after/              # Optimized MJCF, mapping, meshes, scadpkg, and source/
└── output/
    ├── four_bar_before.step  # Original complete assembly, AP242
    ├── four_bar_after.step   # Optimized complete assembly, AP242
    ├── comparison.gif        # Synchronized motion with the same camera and scale
    ├── comparison.png        # First comparison frame
    ├── step_export.json      # STEP export and re-import inspection
    ├── before/               # Original motion package, evidence, and screenshots
    └── after/                # Optimized motion package, evidence, and screenshots
```

Both model versions retain their geometry and assembly relationships. The original has coplanar links and the original pin layout; the optimized version has axial offsets, adjusted pins, and explicit interface exclusions. Each model directory contains editable modeling code in `source/`, a complete CAD package named `four_bar_linkage.scadpkg`, and the MJCF and meshes used for motion verification. STEP files are exported from these two CAD packages. Re-import inspection must confirm valid geometry and eight bodies: four links and four pins.

## Run verification

Run from the KinCheckAPI repository root. Both scripts also support absolute-path invocation from another working directory:

```bash
.venv/bin/python examples/four_bar_linkage/verification/simulate_and_record.py
.venv/bin/python examples/four_bar_linkage/verification/simulate_before_optimization.py
```

- `simulate_and_record.py`: load the optimized model → run native undriven and full-revolution solves → export and reload the reference trajectory → perform three clearance checks → write `output/after/four_bar_linkage.optimization.json`.
- `simulate_before_optimization.py`: check the original model using the same reference trajectory and write `output/before/four_bar_linkage.before_optimization.json`.
- `four_bar_reference.py`: two-circle intersection, pose conversion, numerical differentiation, and reference trajectory construction.
- `test/convert_mjcf_to_assemblymodel.py`: inspect optimized-model conversion and stable object IDs.
- `OPTIMIZATION_LOG.md`: the model's optimization history.

Expected results: the optimized native full-revolution solve is `completed`, with zero interference events across the reference trajectory's 301 frames. The original remains an expected failure: six component pairs, 301 frames, 1,358 interference events, and approximately 0.600000 mm maximum penetration. Verification scope, drivers, sampling, result fields, and reference calculations retain their original meanings; paths follow the directory layout above.

These are example recording scripts. Native trajectories provide closure-error and crank-travel evidence; reference trajectories supply the motion packages and clearance checks. Zero residuals in the reference trajectory are constructed values, not measured solver evidence. For an independent, strict `verify(model_dir)`, see the [Skill skeleton](../../../skill/SKILL.md) and [verification procedure](../../../skill/doc/guides/verification-procedure.md).

## STEP files and comparison GIF

Export STEP using a Python environment with SimpleCADAPI and OpenCASCADE:

```bash
python examples/four_bar_linkage/verification/export_steps.py
```

Run both verification scripts first, then generate the animation using an environment with VTK, NumPy, Pillow, and a CJK font:

```bash
python examples/four_bar_linkage/verification/render_comparison.py
```

Use `--preview` to render only the first PNG frame. The full GIF is 1200 × 660 pixels, with 100 frames in a ten-second loop. It renders the actual meshes from both motion packages on the same closed-form reference trajectory, using identical camera settings and scale. Interference counts come from the 301-frame verification reports; the animation is not proof of continuous-time collision freedom.

## Rebuild the models (optional)

Existing CAD packages can be exported directly to STEP. To change geometry, run each model's source entry points in a compatible SimpleCADAPI environment:

```bash
python examples/four_bar_linkage/model_before/source/main.py
python examples/four_bar_linkage/model_before/source/export_mjcf.py
python examples/four_bar_linkage/model_after/source/main.py
python examples/four_bar_linkage/model_after/source/export_mjcf.py
```

Each entry writes its CAD package and MJCF into its own `model_before/` or `model_after/` directory. Then rerun verification, STEP export, and GIF generation. Only path resolution changed in the modeling scripts; geometry construction remains unchanged.

## View motion packages

```bash
.venv/bin/python viewer/kincheck_viewer.py \
  examples/four_bar_linkage/output/after/four_bar_linkage_full_cycle.kincheck --serve
.venv/bin/python viewer/kincheck_viewer.py \
  examples/four_bar_linkage/output/before/four_bar_linkage_before_optimization.kincheck --serve --port 8768
```

## Native closed-loop solver tuning (v0.5.1)

Models containing a `Closure` use a maximum internal integration step of 0.02 ms, previously 0.5 ms, and a solver iteration limit of 200, previously 100. Closure-point, axis-alignment, and fixed-closure soft constraints use `solref="0.0001 1"` and `solimp="0.9999 0.9999 0.001"`. The 0.1 ms response time constant and critical damping provide at least five integration steps per time constant. These settings follow [MuJoCo's constraint parameter definitions](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters). Models without closures retain their previous step and iteration limits; Scenario controls output sampling independently.

On MuJoCo 3.11.0, driving this example at `2π/10 rad/s` for ten seconds with a 0.01 s output period produced:

- Original settings: `partial`, with approximately `5.95e-4 m` maximum sampled closure-position residual.
- Tuned settings: `completed`, with approximately `3.94e-11 m` maximum sampled residual and `6.283154 rad` actual crank travel.
- A separate startup check sampled every 0.02 ms integration step over the first 0.005 s and measured approximately `4.77e-7 m` maximum residual, below the `1e-6 m` tolerance.

The maximum over sparse full-revolution samples is not the maximum over all internal steps. Run the simulation script and inspect `native_driven_probe` for local results. Its default output period is 0.1 s, so sampled maxima may differ from the 0.01 s comparison above.

Internal integration steps increase by roughly 25 times, increasing closed-loop simulation cost. Enabling `set_capture_integration_steps()` also increases stored pose data. MuJoCo soft constraints, declared closure tolerances, and `partial` classification remain in place. High speeds, abrupt drives, or stricter tolerances can still exceed thresholds; smooth animation or passing samples do not establish success at every instant. The independent closed-form trajectory remains a reproducible reference for full-revolution geometry checks.

Declare smooth startup and shutdown explicitly through the existing API:

```python
condition = scenario.add_joint_speed_profile(
    scenario=condition,
    joint_id=CRANK_JOINT,
    profile=[(0.0, 0.0), (0.1, 0.5), (0.9, 0.5), (1.0, 0.0)],
)
```

This profile requests 0.45 rad of travel over one second. The backend preserves the authored drive curve; it does not automatically reduce speed, extend duration, or add a startup ramp.
