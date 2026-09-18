# `find_singularities`

## API Definition

```python
find_singularities(*, motion_result: Any, assembly: AssemblyModel, options: Any = None) -> SingularityReport
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import find_singularities
```

## Purpose

Compute Jacobian rank, minimum singular value, and condition number at actual MotionResult samples and report singular or near-singular samples.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `Any` | required | The public `MotionResult` to query or check. |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `options` | `Any` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `SingularityReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
