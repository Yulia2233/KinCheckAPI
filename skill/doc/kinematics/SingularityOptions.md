# `SingularityOptions`

## API Definition

```python
@dataclass(frozen=True)
class SingularityOptions:
    tolerance: float
    near_tolerance: float
    target_component_id: str | None
    target_connector_id: str | None
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import SingularityOptions
```

## Purpose

Thresholds used by :func:`find_singularities`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `tolerance` | `float` | `1e-08` | Public input or data field `tolerance`. |
| `near_tolerance` | `float` | `0.0001` | Public input or data field `near_tolerance`. |
| `target_component_id` | `str | None` | `None` | Component ID used as a geometric or kinematic target. |
| `target_connector_id` | `str | None` | `None` | Optional target connector ID; omission targets the component frame. |

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
