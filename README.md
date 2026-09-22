# KinCheckAPI

Current released version: **0.7.0**. KinCheckAPI covers kinematics and rigid-body dynamics. Structural FEA, stress, deformation, structural vibration and fatigue belong to the independent FEACheckAPI; the historical v0.6.4–v0.6.6 reference modules were removed from the v0.7 core.

English | [简体中文](README_zh.md)

![Four-bar linkage before and after optimization](examples/four_bar_linkage/output/comparison.gif)

*Actual model meshes replaying the same closed-form reference trajectory. [Four-bar example](examples/four_bar_linkage/verification/README.md).*

KinCheckAPI reads CAD assembly relationships, builds mechanism motion models, runs kinematic simulation, and exports results as standalone-viewable `.kincheck` packages. The public API never exposes solver-internal objects — callers only deal with assemblies, scenarios, motion results, and check reports.

## Requirements

- Python >= 3.10
- Install the original MJCF-only API in its own environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python .
```

## Addon development: v0.5.7

The optional SimpleCADAPI addon adds validated `.scadpkg` preparation while
preserving `convert_mjcf()`, `verify(model_dir)`, and all assembly, scenario,
solver and check APIs. The CLI now rejects missing or arbitrary verifier results.

Install the addon runtime in a dedicated environment, separate from modeling:

```bash
uv venv --python 3.12 "$HOME/.local/share/kincheckapi/venv"
uv pip install --python "$HOME/.local/share/kincheckapi/venv/bin/python" -e '.[addon]' -e ../CADIR
export PATH="$HOME/.local/share/kincheckapi/venv/bin:$PATH"
kincheck doctor --addon --format json
```

This development version uses the sibling CADIR 2.1.3b3 checkout, which fixes
canonical-frame decoding in MJCF export. Use the paired source checkouts until
the compatible SDK release is published.
Stop on a failed probe and repair the named dependency in this environment.
The addon currently declares macOS arm64 and SDK `>=2.1.3b3,<2.1.4`.

```bash
python scripts/package_addon.py dist/sca-kincheckapi-0.5.7
sca addon init
sca addon add ./dist/sca-kincheckapi-0.5.7
sca addon list
kincheck verify-package product.scadpkg --work-dir analysis-work --script verification/verify.py --format json
```

The skill installs as `sca-kincheckapi`. Package commands enforce the runtime
probe, validate the source package and keep derived assets in a separate work
directory. The source is never modified. Geometry changes return to the main
SimpleCADAPI skill and require a new capture. See the
[addon consumption contract](skill/doc/guides/addon-contract.md) for interface
requirements, units, coordinate conventions and release checks.

## Release history

- **[v0.5.7](doc/updates/v0.5.7.en.md)** adds conservative continuous collision checking, auditable first-contact brackets, rotating contact-point velocities, and persistent failure evidence. The guided four-bar example covers all 36 physical pairs and includes a real-mesh collision negative control.
- **[v0.5.6](doc/updates/v0.5.6.en.md)** adds bounded static numerical IK for supported scalar joints, deterministic multistart search, candidate validation, and structured failure states.
- **[v0.5.5](doc/updates/v0.5.5.en.md)** adds path/pose tracking, start/stop/reversal, periodic and coordination checks with structured diagnostics.
- **[v0.5.4](doc/updates/v0.5.4.en.md)** adds motion segments, driver tracking, integration samples, and the detailed slider-crank example.
- **[v0.5.1](doc/updates/v0.5.1.md)** adds whole-state assembly integrity checking through mechanical, containment/guide, and geometric relations.

- **v0.5.0** unified agent-facing error and verification output: every public error and result provides `format_for_agent()`, `str()` renders the same canonical body, and `raise_if_failed()` converts failures into a same-source `VerificationError`. Structured fields remain available through `to_dict()`.
- **v0.4.1** removed the legacy Artifact input path; conversion now accepts only CADIR MJCF + mapping + mesh directories. AssemblyModel → Scenario → `solve_motion()` and all downstream behavior are unchanged.
- **v0.3.1** unified failure semantics across motion results, checks, and analysis: `partial` results keep recorded evidence but can never pass integrity acceptance; position and orientation residuals use metre and radian tolerances; public thresholds reject NaN, infinities, and illegal ranges.

See the [v0.5.1 update report](doc/updates/v0.5.1.md), the [kinematic verification failure-mode matrix](doc/kinematic-verification-failure-modes.md), and the [empty-pair failure example](fail/04_empty_component_pairs.py). Full history in [doc/updates](doc/updates).

The compact two-stage reducer and [four-bar example](examples/four_bar_linkage/verification/README.md) share `verification/`, `model_before/`, `model_after/`, and `output/`; modeling sources live under each model directory.

## What it can do

- Read and validate CADIR MJCF, mapping, and mesh directories into an immutable `AssemblyModel`;
- Express Components, Connectors, Joints, Grounds, transmission relations, motion trees, and Closures;
- Validate assembly references, topology, and scenarios before invoking the backend, with errors returned as structured diagnostics;
- Solve explicit scenarios with the built-in physics backend and return a backend-neutral `MotionResult`;
- Check closed-loop and general constraint residuals, transmission-equation residuals, joint limits, and measured transmission ratios;
- Compute Jacobians, effective degrees of freedom, singularities, reachability, and workspaces;
- Check target poses, trajectories, and connector paths, with joint locking support;
- Check interference, signed minimum clearance, and motion envelopes against real STL meshes;
- Check explicit component pairs continuously between trajectory samples under a declared pose interpolation, with bracketed TOI evidence and an `indeterminate` result when safety cannot be proved;
- Run interference, clearance, envelope, transmission, limit, and trajectory acceptance uniformly through `run_checks()`;
- Export, validate, and read `.kincheck` result packages containing trajectories and meshes;
- Ship four examples: a compact two-stage planetary reducer, a four-bar linkage, a slider-crank mechanism, and a detailed guided four-bar actuator.

## Current boundaries

- No guarantee that arbitrary closed-loop mechanisms complete time-varying position solving stably; model errors, inconsistent initial states, or unsupported mechanisms raise explicit errors or return `partial` — never a disguised success;
- A `partial` MotionResult preserves recorded trajectories, residuals, and geometric evidence, which may include samples that violate constraints; it can never produce a pass conclusion;
- Discrete geometric checks use real triangle meshes at explicit sample times. `check_continuous_interference()` adds a conditional conservative interval proof for the declared piecewise rigid interpolation and velocity bound; it never claims arbitrary deformable or dynamic collision freedom, nor exact BREP/NURBS surface distances;
- The v0.6 inverse/forward APIs retain their scalar revolute/prismatic tree contract. The v0.7 rigid core adds declared generalized multi-DOF states, linear/KKT constraints, source-mapped reactions, coupled penalty contact with Coulomb tangential response, controller/actuator limits, scenario matrices, and replayable load histories. Automatic Assembly-to-constraint discovery, instantaneous restitution, real-geometry collision search, and arbitrary backend-specific joint families remain explicit capability boundaries;
- Structural meshes, stress, deformation, structural vibration and fatigue are outside KinCheckAPI. Use the independent FEACheckAPI design for those capabilities; KinCheckAPI exports versioned rigid motion, loads, reactions, contact events and impulses;
- `.scadpkg` is the persistent product source. The optional addon prepares validated packages for the unchanged MJCF conversion entry; raw CADIR XML is not an input.

## Running tests

```bash
uv run --extra test pytest -q
```

## CLI and Agent Skill

After installing KinCheckAPI, `kincheck` is the shared runtime entry for all harnesses:

```bash
kincheck doctor --format json
kincheck validate-model path/to/model --format json
kincheck verify path/to/model --script verification/verify.py --format json
```

`verification/verify.py` must expose `verify(model_dir)`, and the model directory must contain `scene.xml`, `scene.mapping.json`, and `meshes/` exported by the same SimpleCADAPI build. Consume verification results through the JSON `status`/`issues` and the process exit code — never by parsing free text.

Generate Skills installable into Codex, Gemini, Cursor, OpenCode, or Claude Code:

```bash
kincheck-skill-pack --language both --archive --adapters --output-root dist
```

The output includes `kincheckapi.tar.gz`, `kincheckapi-zh.tar.gz`, and the `dist/adapters/claude-code/`, `codex/`, `gemini/`, `cursor-opencode/` adapter directories. Skills contain only workflows, public API references, and scripts — never KinCheckAPI source; the Python runtime is provided by the `kincheckapi` wheel.

## Examples

The compact two-stage planetary reducer checks its transmission ratio from simulated time series:

```bash
uv run python examples/compact_two_stage_planetary_reducer/verification/simulate_and_record.py
```

The [four-bar example](examples/four_bar_linkage/verification/README.md) includes both model versions, their STEP exports, and the comparison GIF shown above:

```bash
uv run python examples/four_bar_linkage/verification/simulate_and_record.py
uv run python examples/four_bar_linkage/verification/simulate_before_optimization.py
```

The [slider-crank example](examples/slider_crank/verification/verify.py) is a detailed four-part CADIR mechanism: a bored crank pedestal, shaft and flywheel with eccentric pin, bored capsule connecting rod, and guided slider carriage. Its verifier checks segmented crank tracking, closure residuals, joint limits, trajectory bounds, mesh interference, a 0.5 mm minimum clearance over all component pairs, and guide containment at every sample:

The simulation can be exported as a `.kincheck` package and replayed by the standalone viewer:

```bash
uv run --extra addon python examples/slider_crank/model/source/slider_crank.cadir.py
uv run python examples/slider_crank/verification/verify.py examples/slider_crank/model
uv run python examples/slider_crank/verification/export_motion_package.py
python viewer/kincheck_viewer.py examples/slider_crank/output/slider_crank.kincheck --serve
```

The [guided four-bar actuator](examples/guided_four_bar_actuator/README.md) adds a detailed CADIR assembly with machined hardware, an independent verifier, sampled clearance, and the v0.5.7 continuous interference/TOI check. All six rigid-group pairs are checked, including joint neighbors; their meshes cover 28 moving physical pairs, while eight fixed physical pairs are checked separately using invariant relative placement. See the [verification scope](examples/guided_four_bar_actuator/verification/README.md) and [collision review](examples/guided_four_bar_actuator/output/collision_review.md). Its exported package and JSON evidence are under `examples/guided_four_bar_actuator/output/`:

```bash
uv run python examples/guided_four_bar_actuator/verification/verify.py examples/guided_four_bar_actuator/model --report examples/guided_four_bar_actuator/output/collision_verification.json
uv run python examples/guided_four_bar_actuator/verification/export_motion_package.py
python viewer/kincheck_viewer.py examples/guided_four_bar_actuator/output/guided_four_bar_actuator.kincheck --serve
```

The standalone viewer replays any exported `.kincheck` package without re-running the solver:

```bash
python viewer/kincheck_viewer.py path/to/result.kincheck --serve
```

Then open `http://127.0.0.1:8767/`. The viewer only reads recorded meshes and trajectories.

The E01 loaded-arm package also has staged dynamics verifiers:

```bash
uv run python examples/dynamics_loaded_arm/verification/verify_dynamic.py examples/dynamics_loaded_arm/model
uv run python examples/dynamics_loaded_arm/verification/verify_contact.py examples/dynamics_loaded_arm/model
```

## Result packages

`.kincheck` is KinCheckAPI's motion-result format: result data and displayable meshes, without HTML, JavaScript, or solver runtime objects. Write, validate, and read through `kincheckapi.export`:

```python
from kincheckapi import export

package = export.motion_package(
    assembly=assembly,
    motion_result=motion_result,
    output_path="result.kincheck",
    asset_root="examples/four_bar_linkage/model_after",
)
loaded = export.read_package(path=package.path)
```

## v0.7 rigid-body dynamics

The v0.7 core line adds general multi-DOF states, declared linear constraints,
rigid contact/impulse evidence, driving scenarios and replayable
`DynamicsLoadHistory` records. These APIs preserve units, frames, model hashes,
time coverage, reactions, contact events and convergence evidence.
`motion_package()` can archive a validated `dynamics.json` member and the
standalone Viewer replays its rigid-body records. The v0.7 reference solver
supports declared generalized linear constraints and penalty contact; an
unsupported backend or unmodelled impact law is reported explicitly.

## v0.6.1–v0.6.3 dynamics

`kincheckapi.dynamics` exposes `solve_inverse_dynamics()` for prescribed
scalar joint states, `solve_forward_dynamics()` for finite actuator profiles,
`check_dynamic_load_limits()` and `check_dynamic_tracking()`, and
`check_contact_capacity()` for supplied-force Coulomb/pressure capacity. Every
operation records model hashes, SI units, backend evidence, and structured
failure guidance. The v0.7 APIs extend this scalar compatibility layer with
explicit multi-DOF scenarios and contact histories.

## v0.6.0 physical statics

This release added the [E01 loaded-arm physical/static workflow](examples/dynamics_loaded_arm/README.md): CADIR density and closed-BREP integration, occurrence-preserving tensors, explicit backend inertials, tree static equilibrium, local BREP contact regions, and hash-indexed physics result packages. The dynamic capabilities and boundaries are defined by v0.6.1-v0.6.3 above.

See [physical statics](skill/doc/guides/physical-statics.md), the [E01 requirements](examples/dynamics_loaded_arm/requirements.md), [verification program](examples/dynamics_loaded_arm/verification/verify.py), and [static evidence](examples/dynamics_loaded_arm/output/verification.json).
