# `validate_closures`

## API Definition

```python
validate_closures(*, assembly: AssemblyModel | None = None, motion_result: MotionResult | None = None, **_: Any) -> ClosureReport | None
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import validate_closures
```

## Purpose

Validate authored or solved Closure residuals. Calling the compatibility shim without an assembly or result continues to return ``None``. With an assembly, the authored component poses are checked before a solver is started; with a MotionResult, the recorded samples and declared Closure tolerances are checked.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel | None` | `None` | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult | None` | `None` | The public `MotionResult` to query or check. |
| `_` | `Any` | required | Public input or data field `_`. |

## Returns and Failures

Returns `ClosureReport | None`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
