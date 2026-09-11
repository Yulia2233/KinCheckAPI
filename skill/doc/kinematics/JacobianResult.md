# `JacobianResult`

## API Definition

```python
@dataclass(frozen=True)
class JacobianResult:
    target_component_id: str
    target_connector_id: str | None
    joint_ids: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    rank: int
    singular_values: tuple[float, ...]
    condition_number: float | None
    units: tuple[str, ...]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics import JacobianResult
```

## Purpose

JacobianResult(*, target_component_id: 'str', target_connector_id: 'str | None', joint_ids: 'tuple[str, ...]', matrix: 'tuple[tuple[float, ...], ...]', rank: 'int', singular_values: 'tuple[float, ...]', condition_number: 'float | None', units: 'tuple[str, ...]' = ('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)'), issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `target_component_id` | `str` | required | Component ID used as a geometric or kinematic target. |
| `target_connector_id` | `str | None` | required | Optional target connector ID; omission targets the component frame. |
| `joint_ids` | `tuple[str, ...]` | required | Explicitly specified `joint_ids` collection. |
| `matrix` | `tuple[tuple[float, ...], ...]` | required | Public input or data field `matrix`. |
| `rank` | `int` | required | Public input or data field `rank`. |
| `singular_values` | `tuple[float, ...]` | required | Public input or data field `singular_values`. |
| `condition_number` | `float | None` | required | Public input or data field `condition_number`. |
| `units` | `tuple[str, ...]` | `('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)')` | Public input or data field `units`. |
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
