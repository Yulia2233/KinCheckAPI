# `compute_workspace`

## API Definition

```python
compute_workspace(**kwargs: Any) -> Any
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import compute_workspace
```

## Purpose

Enumerate a finite deterministic set of joint configurations.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `kwargs` | `Any` | required | Public input or data field `kwargs`. |

## Returns and Failures

Returns `Any`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
