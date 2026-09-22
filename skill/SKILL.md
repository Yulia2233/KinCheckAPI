---
name: sca-kincheckapi
description: Verify CAD mechanism topology, motion, transmission, poses, limits and geometric safety with KinCheckAPI. Consume a finished .scadpkg assembly's definitions, occurrence graph, geometry and claim-required interface.* tags; produce an independent Python verifier and structured acceptance results. Use for verification-first design iteration or checking an existing package. Existing MJCF model-directory verifiers remain supported.
---

# KinCheckAPI Verification Program Skill (v0.7.0-dev)

Turn the user's mechanism requirements into an executable acceptance program, then build and iterate the model against that program. Always follow this order:

```text
User acceptance claims
    -> write verification/ Python program first
    -> statically check the verifier and its input contract
    -> delegate modeling to the main SimpleCADAPI skill
    -> capture(result, "product.scadpkg") in the modeling environment
    -> this addon validates the package and prepares MJCF in its own work directory
    -> verification.verify(model_dir)
    -> return failure evidence to the main skill for any geometry changes
    -> re-capture and rerun until the original claims are satisfied
```

Read this file first, then open `doc/<module>/<api>.md` for the modules actually used. The API index is [`doc/README.md`](doc/README.md).

Before first use, follow the runtime gate and package contract below. For an existing
package, keep the declared acceptance claim and start at consumption; no modeling
is required. This addon never edits source geometry, package members, or modeling
modules. Geometry changes belong to the main `simplecadapi` skill and require a new
`capture` before analysis resumes.

## Default Deliverable

The primary deliverable is an independent Python verification directory, not a report, `.kincheck` file, or modeling source:

```text
verification/
├── __init__.py
├── verify.py              # required: Python API and CLI entry point
└── checks.py              # optional: split out when checks are extensive
```

The smallest deliverable may contain only `verification/verify.py`. The verifier must:

- depend only on public KinCheckAPI APIs and the Python standard library;
- accept `model_dir` as its model input and never import SimpleCADAPI modeling modules;
- encode acceptance object IDs, drivers, time windows, sampling, thresholds, units, and scope in code;
- return a structured KinCheckAPI result and use a non-zero CLI exit code for an unmet condition;
- be repeatable on any other model satisfying the same input contract.

Generate `.kincheck`, JSON, images, or visualization only when the user explicitly requests debugging, archiving, or playback.

## Assembly Integrity

After solving the declared time window, verify that the selected Components remain one connected assembly:

```python
from kincheckapi import check_assembly_integrity

integrity = check_assembly_integrity(
    assembly=assembly,
    motion_result=motion,
    asset_root=model_dir,
    geometric_connection_pairs=(("component.a", "component.b"),),
    geometric_connection_tolerance_m=1e-4,
)
integrity.raise_if_failed()
```

Two Components that are far apart with no declared relation are a failed assembly even when no collision is detected. A sliding part may have a gap while it remains inside a declared guide or containment interval; leaving that interval is a failure. Every geometric connection must declare a finite, non-negative metre tolerance. `sampling_scope="motion_result"` checks every recorded sample; `sampling_scope="initial"` is static-only.

## Runtime CLI

Before the first import, verifier execution, or package preparation, run the
descriptor's exact runtime probe in the addon-owned environment:

```bash
kincheck doctor --addon --format json
```

Only exit code 0 opens the gate. On failure, name the missing runtime from `checks`
and stop; do not skip analysis, use another Python, or install into the modeling
environment. The probe performs local dependency imports without network, license
checkout, or GUI launch. An install-time probe failure is a warning from `sca`; it
does not authorize first use. Installation and repair commands are in
[`doc/guides/addon-contract.md`](doc/guides/addon-contract.md).

The addon API and package CLI also enforce this probe. Existing MJCF-only users
can use `kincheck doctor --format json` without installing the optional SDK.

The verifier must expose `verify(model_dir)` and return an explicit structured
verdict; `None` and arbitrary return values are input errors. Consume JSON status
and process exit code; do not parse human-readable stdout. Build portable Skill artifacts with
`kincheck-skill-pack --language en --archive --adapters`.

## Model Input Contract

The addon consumes an assembly-rooted `.scadpkg`. Read
[`doc/guides/addon-contract.md`](doc/guides/addon-contract.md) before consumption.
The normative format pointer is the main `simplecadapi` skill's
`references/scadpkg-format.md`; a bundled copy is
[`doc/guides/scadpkg-format.md`](doc/guides/scadpkg-format.md). Without that skill,
the installed `simplecadapi/contracts/` JSON Schemas are authoritative.

Declare required `interface.*` tags by exact part occurrence ID before preparation.
The default is no required tags for checks expressed entirely using joint and
connector IDs. Missing required names must fail with their exact name and
occurrence; never infer them from geometry. Preserve all entities under a name.

Package lengths are millimeters. The SDK exporter converts positions and mesh
scales to meters; do not rescale the resulting MJCF again. Package occurrence
transforms are relative to their parent; use the exported assembly frames, never
assume definition-local frames are world frames. MJCF quaternions are `wxyz`,
KinCheckAPI Pose is `xyzw`; `convert_mjcf()` performs that conversion. Public joint
direction is `component_b - component_a`; use the documented kinematic sign rules.

Package preparation produces the following directory. The existing verifier
continues to accept exactly one model directory:

```text
model/
├── scene.xml
├── scene.mapping.json
└── meshes/                # assets referenced by XML/mapping
```

Build these three paths explicitly in `verify.py` and pass them to `convert_mjcf()`. Do not scan the directory or guess relationships from names. Require:

- a non-empty XML root `model` equal to mapping `root_definition_id`;
- XML, mapping, and meshes from the same SimpleCADAPI/CADIR export;
- normalized mesh paths that remain inside `model_dir`;
- bidirectionally resolvable source IDs, XML names, joints, sites, equalities, and mesh references;
- no use of removed `read_artifact()`, `validate_artifact()`, `convert_artifact()`, or `convert_live_assembly()` APIs.

When an exporter uses different filenames, adjust the SimpleCADAPI export target to satisfy this contract instead of adding fuzzy discovery to the verifier.

## Verification First

### 1. Freeze the acceptance claim

Before modeling, define:

- the mechanism fact to prove;
- stable joint, component, connector, and component-pair IDs;
- initial state, drivers, time window, and sampling period;
- expected range, direction, transmission, trajectory, or pose;
- residual, limit, interference, or clearance thresholds in SI units;
- what constitutes pass, failure, and incomplete verification.

Treat missing information as a model interface requirement. Never infer relationships from display names, gear counts, filenames, or geometry appearance.

### 2. Write the verifier first

`verify.py` should expose at least:

```python
from pathlib import Path


def verify(model_dir: str | Path):
    """Verify an exported model satisfying the fixed directory contract."""
    ...


def main() -> int:
    ...


if __name__ == "__main__":
    raise SystemExit(main())
```

The stable CLI form is:

```bash
python verification/verify.py path/to/model
```

Before a model exists, run syntax/import checks and invalid-path or invalid-parameter tests. Do not create a temporary model and infer the acceptance conditions afterward.

### 3. Build the model with SimpleCADAPI

After the verifier is complete, delegate to the main `simplecadapi` skill in its
modeling environment to create geometry, assembly relationships, stable IDs and
required public tags. Capture a `.scadpkg`, then use `prepare_package()` or
`kincheck verify-package` in the separate addon environment to produce the
directory contract. A useful layout is:

```text
project/
├── verification/          # written first: KinCheckAPI acceptance program
├── simplecadapi/          # written second: model implementation
└── model/                 # SimpleCADAPI/CADIR export consumed by verifier
```

The KinCheckAPI verification directory must not depend on `simplecadapi/` Python modules. The model implementation may change, but verifier thresholds and scope remain fixed while the acceptance claim remains unchanged.

### 4. Run and iterate on the model

Pass the prepared `model_dir` to the verifier. On failure, inspect error codes,
object IDs, source paths, Evidence, failure time, and suggested actions; return to
the main `simplecadapi` skill to change the owning modeling source and re-capture.
Consume that new package and rerun the same verifier. Never edit geometry or repair
missing interfaces inside this addon.

Never make the current model pass by:

- relaxing thresholds or shortening the required motion range;
- reducing sampling to skip a failure time;
- deleting checks or interpreting an explicit empty set as all objects;
- adding collision exclusions without physical justification;
- wrapping partial, empty-sample, capability-missing, or interrupted results as a pass.

Change the verifier only when the user explicitly changes the acceptance claim.

## Standard `verify.py` Skeleton

```python
import argparse
from pathlib import Path

from kincheckapi.assembly import validate_assembly, validate_topology
from kincheckapi.cadir import convert_mjcf
from kincheckapi.checks import CheckSpec, run_checks
from kincheckapi.errors import KinCheckError
from kincheckapi.kinematics import solve_motion
from kincheckapi.scenario import (
    add_joint_speed_driver,
    create_scenario,
    request_joint_result,
    set_run_duration,
    set_sample_period,
    validate_scenario,
)

INPUT_JOINT_ID = "joint.input"
RUN_DURATION_S = 1.0
SAMPLE_PERIOD_S = 0.01


def verify(model_dir: str | Path):
    root = Path(model_dir).expanduser().resolve()
    converted = convert_mjcf(
        xml_path=root / "scene.xml",
        mapping_path=root / "scene.mapping.json",
        asset_root=root,
    )
    assembly = converted.assembly
    validate_assembly(assembly=assembly).raise_if_failed()
    validate_topology(assembly=assembly).raise_if_failed()

    condition = create_scenario(scenario_id="verification.nominal", assembly=assembly)
    condition = add_joint_speed_driver(
        scenario=condition,
        joint_id=INPUT_JOINT_ID,
        speed_rad_s_or_m_s=1.0,
        start_time_s=0.0,
        end_time_s=RUN_DURATION_S,
    )
    condition = set_run_duration(scenario=condition, duration_s=RUN_DURATION_S)
    condition = set_sample_period(scenario=condition, period_s=SAMPLE_PERIOD_S)
    condition = request_joint_result(scenario=condition, joint_id=INPUT_JOINT_ID)
    validate_scenario(scenario=condition).raise_if_failed()

    motion = solve_motion(scenario=condition)
    motion.raise_if_failed()
    suite = run_checks(
        assembly=assembly,
        scenario=condition,
        motion_result=motion,
        checks=(CheckSpec(
            check_id="constraint-residuals",
            check_type="constraint_residuals",
            parameters={"position_tolerance_m": 1e-6},
        ),),
    )
    suite.raise_if_failed()
    return suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.model_dir)
    except KinCheckError as error:
        print(error)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Replace the skeleton IDs, drivers, and checks with the user's claim. Do not treat the example values as universal acceptance conditions. Scenario setters return new immutable objects; capture every return value.

## Pass Rules

1. An operation that did not raise is not an acceptance claim; run the checks corresponding to the user's requirements.
2. `MotionResult.status == "partial"`, `capability_failed`, empty samples, empty measurements, and empty component pairs cannot pass.
3. Accept only `completed` or `completed_with_warnings`; review warnings and issues for the latter.
4. `completed` covers only the requested time window, not automatically a full revolution, full stroke, or complete workspace.
5. Specify check objects explicitly; an explicit `()` never means “all”.
6. Use SI units: m, rad, s, m/s, and rad/s.
7. Mesh safety checks establish results only at discrete samples, not continuous-time collision freedom.
8. Kinematic evidence does not establish dynamics, strength, manufacturing, or regulatory compliance.

## API Selection by Claim

| Claim | Preferred API documentation |
| --- | --- |
| Model conversion | [`convert_mjcf`](doc/cadir/convert_mjcf.md) |
| Assembly references, ground, topology | [`validate_assembly`](doc/assembly/validate_assembly.md), [`validate_topology`](doc/assembly/validate_topology.md) |
| Whole assembly remains connected | [`check_assembly_integrity`](doc/checks/check_assembly_integrity.md), [`ContainmentRelation`](doc/checks/ContainmentRelation.md) |
| Motion tree and DOFs | [`build_kinematic_tree`](doc/assembly/build_kinematic_tree.md), [`analyze_dofs`](doc/kinematics/analyze_dofs.md), [`analyze_mobility`](doc/kinematics/analyze_mobility.md) |
| Pose or continuous motion | [`solve_position`](doc/kinematics/solve_position.md), [`solve_motion`](doc/kinematics/solve_motion.md) |
| Pre-failure motion evidence | [`try_solve_motion`](doc/kinematics/try_solve_motion.md) |
| Closures and constraints | [`validate_closures`](doc/kinematics/validate_closures.md), [`check_constraint_residuals`](doc/checks/check_constraint_residuals.md) |
| Transmission | [`check_transmission_ratio`](doc/checks/check_transmission_ratio.md) |
| Poses, trajectories, limits | Corresponding `check_*.md` pages under `doc/checks/` |
| Singularities, reachability, workspace | Corresponding analysis pages under `doc/kinematics/` |
| Interference, clearance, envelopes | `doc/clearance/` and `doc/checks/` |
| Result queries and optional export | `doc/result/` and `doc/export/` |
| Errors and diagnostics | [`diagnostics`](doc/diagnostics/README.md) and [`errors`](doc/errors/README.md) |

## Failure Output

Use the same no-argument output protocol for public errors and results: `print(error)` or `print(result)`. In strict CLI mode, call `raise_if_failed()` and return a non-zero exit code. For machine consumption, use `to_dict()`; do not hand-build a second error format from `issues`.

On partial or failed solving, retain `last_valid_result`, failure time, and diagnostics, but never claim a pass. Report unavailable backend capabilities instead of substituting an unverified calculation.

## References

- [`doc/guides/verification-procedure.md`](doc/guides/verification-procedure.md): verification-first execution order.
- [`doc/guides/evidence-and-pass-rules.md`](doc/guides/evidence-and-pass-rules.md): evidence and acceptance rules.
- [`doc/guides/kinematic-correctness.md`](doc/guides/kinematic-correctness.md): layered kinematic evidence.
- [`doc/guides/failure-diagnosis.md`](doc/guides/failure-diagnosis.md): failures, partial results, and diagnostics.
- [`doc/guides/analysis-procedure.md`](doc/guides/analysis-procedure.md): analysis-specific procedure.
- [`doc/README.md`](doc/README.md): API index by module.

## v0.7 rigid-body dynamics acceptance

KinCheckAPI v0.7 covers general rigid-body states, constraints, contact/impact,
driving scenarios, reactions, energy, and replayable load histories. Preserve
units, frames, source IDs, time coverage, convergence and structured failure
evidence. Structural meshes, stress, deformation, structural vibration and
fatigue belong to FEACheckAPI and must not be imported or inferred here.

## v0.6.1-v0.6.3 dynamic acceptance

Read [physical properties and statics](doc/guides/physical-statics.md) for density/BREP conversion and tree statics. Read the v0.6.1-v0.6.3 update notes for scalar-tree inverse dynamics, finite-actuator forward dynamics, and supplied-force contact/friction capacity. Probe each operation and preserve structured failure evidence. Closed-loop dynamics and contact response/impact remain capability boundaries.
