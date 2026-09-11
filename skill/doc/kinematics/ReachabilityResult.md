# `ReachabilityResult`

## API Definition

```python
@dataclass(frozen=True)
class ReachabilityResult:
    reachable: bool
    target: Any
    position_result: PositionResult | None
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import ReachabilityResult
```

## Purpose

ReachabilityResult(*, reachable: 'bool', target: 'Any', position_result: 'PositionResult | None' = None, issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `reachable` | `bool` | required | Public input or data field `reachable`. |
| `target` | `Any` | required | Public input or data field `target`. |
| `position_result` | `PositionResult | None` | `None` | Public input or data field `position_result`. |
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
