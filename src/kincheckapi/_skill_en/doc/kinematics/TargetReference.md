# `TargetReference`

## API Definition

```python
@dataclass(frozen=True)
class TargetReference:
    component_id: str
    connector_id: str | None
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import TargetReference
```

## Purpose

TargetReference(*, component_id: 'str', connector_id: 'str | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |

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
