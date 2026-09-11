# `SingularityReport`

## API Definition

```python
@dataclass(frozen=True)
class SingularityReport:
    singular_times_s: tuple[float, ...]
    tolerance: float
    issues: tuple[SimIssue, ...]
    samples: tuple[Any, ...]
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import SingularityReport
```

## Purpose

SingularityReport(*, singular_times_s: 'tuple[float, ...]', tolerance: 'float', issues: 'tuple[SimIssue, ...]' = (), samples: 'tuple[Any, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `singular_times_s` | `tuple[float, ...]` | required | `singular_times_s` in seconds; finite. |
| `tolerance` | `float` | required | Public input or data field `tolerance`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `samples` | `tuple[Any, ...]` | `()` | Public input or data field `samples`. |

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
