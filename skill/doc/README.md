# KinCheckAPI API Documentation

These pages are organized by source module. The top-level workflow is in [`../SKILL.md`](../SKILL.md); read only the APIs needed for the current verification program.

## Modules

| Module | Purpose |
| --- | --- |
| [`cadir`](cadir/README.md) | CADIR MJCF input conversion |
| [`assembly`](assembly/README.md) | Assembly objects, topology, and serialization |
| [`scenario`](scenario/README.md) | Scenarios, drivers, initial state, and result scope |
| [`kinematics`](kinematics/README.md) | High-level position/motion solving and analysis |
| [`checks`](checks/README.md) | Kinematic acceptance checks |
| [`clearance`](clearance/README.md) | Mesh interference, clearance, and motion envelopes |
| [`result`](result/README.md) | MotionResult types, queries, and JSON output |
| [`diagnostics`](diagnostics/README.md) | Structured issues, evidence, and diagnostics |
| [`errors`](errors/README.md) | Stable public exception hierarchy |
| [`export`](export/README.md) | Optional `.kincheck` result packages |
| [`pose`](pose/README.md) | Backend-independent pose operations |
| [`trajectory_checks`](trajectory_checks/README.md) | Trajectory-window metrics and limit-event filtering |
| [`visualization`](visualization/README.md) | Offline motion playback export |

## Advanced Modules

Use high-level entry points from `kincheckapi.kinematics` for normal work. Read low-level deterministic primitives only when explicitly needed:

- [`kinematics_geometry`](kinematics_geometry/README.md): pose propagation, Jacobians, mobility, and position-solving primitives.
- [`kinematics_conventions`](kinematics_conventions/README.md): sign conventions between joint coordinates and tree propagation.
- [`kinematics_limits`](kinematics_limits/README.md): joint-limit event detection.
- [`dynamics`](dynamics/README.md): reserved namespace with no public dynamics operation in this release.

## Reading Convention

Each public symbol has a same-named page covering its actual signature, import path, fields, return value, and failure constraints. Pages are generated from the public export surface by `scripts/generate_skill_api_docs_en.py`; regenerate and run `--check` after changing the runtime API.

Do not create a public contract for `_backends`, `_clearance_fcl`, or names beginning with an underscore. Source code and regression tests are the final contract; fix the documentation generator when a generated page differs instead of guessing parameters at the call site.
