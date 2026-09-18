# KinCheckAPI

Current development version: **0.5.5**. See [the v0.5.5 update](doc/updates/v0.5.5.en.md) for curve, planar, event, periodic, synchronization, and structured failure diagnostics.

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

## Addon development: v0.5.5

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
python scripts/package_addon.py dist/sca-kincheckapi-0.5.5
sca addon init
sca addon add ./dist/sca-kincheckapi-0.5.5
sca addon list
kincheck verify-package product.scadpkg --work-dir analysis-work --script verification/verify.py --format json
```

The skill installs as `sca-kincheckapi`. Package commands enforce the runtime
probe, validate the source package and keep derived assets in a separate work
directory. The source is never modified. Geometry changes return to the main
SimpleCADAPI skill and require a new capture. See the
[addon consumption contract](skill/doc/guides/addon-contract.md) for interface
requirements, units, coordinate conventions and release checks.

## Previous release: v0.5.1

v0.5.1 adds whole-state assembly integrity checking: across the static initial pose or every sample of a complete MotionResult, verify that Components always remain one valid connected network — through mechanical relations, containment/guide relations, geometric connections, and explicit metric connection tolerances.

Recent releases:

- **v0.5.0** unified agent-facing error and verification output: every public error and result provides `format_for_agent()`, `str()` renders the same canonical body, and `raise_if_failed()` converts failures into a same-source `VerificationError`. Structured fields remain available through `to_dict()`.
- **v0.4.1** removed the legacy Artifact input path; conversion now accepts only CADIR MJCF + mapping + mesh directories. AssemblyModel → Scenario → `solve_motion()` and all downstream behavior are unchanged.
- **v0.3.1** unified failure semantics across motion results, checks, and analysis: `partial` results keep recorded evidence but can never pass integrity acceptance; position and orientation residuals use metre and radian tolerances; public thresholds reject NaN, infinities, and illegal ranges.

See the [v0.5.1 update report](doc/updates/v0.5.1.md), the [kinematic verification failure-mode matrix](doc/kinematic-verification-failure-modes.md), and the [reproducible failure cases](fail/README.md). Full history in [doc/updates](doc/updates).

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
- Run interference, clearance, envelope, transmission, limit, and trajectory acceptance uniformly through `run_checks()`;
- Export, validate, and read `.kincheck` result packages containing trajectories and meshes;
- Ship three examples: a compact two-stage planetary reducer, a four-bar linkage, and a slider-crank mechanism.

## Current boundaries

- No guarantee that arbitrary closed-loop mechanisms complete time-varying position solving stably; model errors, inconsistent initial states, or unsupported mechanisms raise explicit errors or return `partial` — never a disguised success;
- A `partial` MotionResult preserves recorded trajectories, residuals, and geometric evidence, which may include samples that violate constraints; it can never produce a pass conclusion;
- Geometric checks use real triangle meshes at explicit discrete time points; they are not continuous-time absolute collision-freedom proofs, nor exact BREP/NURBS surface distances;
- Full dynamics, contact forces, friction, and impact are not implemented; multi-dof joints (`cylindrical`, `spherical`, `planar`, `free`) are still outside backend support;
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

The standalone viewer replays any exported `.kincheck` package without re-running the solver:

```bash
python viewer/kincheck_viewer.py path/to/result.kincheck --serve
```

Then open `http://127.0.0.1:8767/`. The viewer only reads recorded meshes and trajectories.

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
