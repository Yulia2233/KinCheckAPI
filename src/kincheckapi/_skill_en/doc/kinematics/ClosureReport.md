# `ClosureReport`

## API Definition

```python
@dataclass(frozen=True)
class ClosureReport:
    passed: bool
    residuals: tuple[Any, ...]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import ClosureReport
```

## Purpose

ClosureReport(*, passed: 'bool', residuals: 'tuple[Any, ...]' = (), issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `passed` | `bool` | required | Structured Boolean conclusion; read it together with issues and actual evidence. |
| `residuals` | `tuple[Any, ...]` | `()` | Public input or data field `residuals`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |

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
