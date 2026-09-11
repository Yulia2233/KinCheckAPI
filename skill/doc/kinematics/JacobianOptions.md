# `JacobianOptions`

## API Definition

```python
@dataclass(frozen=True)
class JacobianOptions:
    finite_difference_step: float
    rank_tolerance: float
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics import JacobianOptions
```

## Purpose

JacobianOptions(*, finite_difference_step: 'float' = 1e-07, rank_tolerance: 'float' = 1e-09)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `finite_difference_step` | `float` | `1e-07` | Public input or data field `finite_difference_step`. |
| `rank_tolerance` | `float` | `1e-09` | Public input or data field `rank_tolerance`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
