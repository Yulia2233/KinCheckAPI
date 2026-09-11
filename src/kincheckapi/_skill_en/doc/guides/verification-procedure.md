# Verification-First Procedure

Write an independent KinCheckAPI Python verification program from the user's requirements before using SimpleCADAPI to build the model. The verifier is the acceptance contract, and the model directory is its runtime input.

## 1. Define the acceptance claim

Record the driver joint, initial state, time window, sampling period, target pose or trajectory, residual thresholds, limits, component pairs, and SI units. Choose stable joint, component, and connector IDs for the verifier; treat missing information as a model interface requirement instead of guessing relationships.

## 2. Create the verification directory first

Create `verification/verify.py` by default, splitting larger checks into `verification/checks.py` only when useful. `verify.py` exposes `verify(model_dir)` and a CLI that accepts one model directory. It may depend only on public KinCheckAPI APIs and the Python standard library, never on SimpleCADAPI modeling modules.

Before a model exists, check syntax, imports, and invalid-path or invalid-parameter branches. Encode drivers, check objects, thresholds, time windows, and sampling rules in the verifier.

## 3. Build and export the model second

Use the main `simplecadapi` skill in the separate modeling environment to create
geometry, relationships, stable IDs and required `interface.*` tags. Capture the
finished `.scadpkg`, then run the addon's runtime gate and `prepare_package()` in
the addon environment. See [addon-contract.md](addon-contract.md). It prepares:

```text
model/
├── scene.xml
├── scene.mapping.json
└── meshes/
```

The verifier accepts this directory and does not depend on the modeling source layout.

## 4. Convert and precheck

Inside `verify(model_dir)`, pass the three input paths explicitly to `convert_mjcf()`. Run `validate_assembly()` and `validate_topology()` in order, then use `build_kinematic_tree()` or `analyze_dofs()` when required. Read issue codes, object IDs, and evidence.

## 5. Build the Scenario and solve

Use `create_scenario()` to set initial joint state, drivers, duration, sampling period, and result requests. Every setter returns a new Scenario and its return value must be captured; call `validate_scenario()` before solving.

Call `solve_motion()`, or `try_solve_motion()` when failure evidence must retain the pre-failure trajectory. Inspect status, `sample_times_s`, constraint residuals, limit events, and issues. A `partial` result exits the pass path immediately.

## 6. Run acceptance checks

Use explicit `CheckSpec` values with `run_checks()`, or call the public check that directly matches the user's claim. Inspect `passed`, issues, evidence, thresholds, and actual sample counts; call `raise_if_failed()` in strict CLI mode.

Run interference, minimum-clearance, or motion-envelope checks only when motion safety is requested. Component pairs, tolerances, asset root, and sampling range must be explicit.

## 7. Modify the model and repeat

Return structured evidence to the main SimpleCADAPI skill to modify the owning
modeling source, then re-capture and prepare the new package before rerunning the
same verifier. Never edit geometry or package members inside the addon. Unless
the user changes the acceptance claim, do not relax thresholds, reduce checks,
skip failure samples, or broaden collision exclusions.

## 8. Deliver

The default deliverable is a repeatable `verification/` Python directory plus its run command. Console output keeps pass status, evidence, and error codes; failures and incomplete runs use a non-zero exit code. Generate `.kincheck`, JSON reports, or visualizations only when explicitly requested for debugging, archiving, or playback.
