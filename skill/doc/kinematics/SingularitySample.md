# `SingularitySample`

## API Definition

```python
@dataclass(frozen=True)
class SingularitySample:
    time_s: float
    status: str
    rank: int
    minimum_singular_value: float | None
    condition_number: float | None
    singular_values: tuple[float, ...]
    joint_positions: Mapping[str, float]
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import SingularitySample
```

## Purpose

SingularitySample(*, time_s: 'float', status: 'str', rank: 'int', minimum_singular_value: 'float | None', condition_number: 'float | None', singular_values: 'tuple[float, ...]' = (), joint_positions: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `status` | `str` | required | Structured status interpreted according to the stable values for the result type. |
| `rank` | `int` | required | Public input or data field `rank`. |
| `minimum_singular_value` | `float | None` | required | Public input or data field `minimum_singular_value`. |
| `condition_number` | `float | None` | required | Public input or data field `condition_number`. |
| `singular_values` | `tuple[float, ...]` | `()` | Public input or data field `singular_values`. |
| `joint_positions` | `Mapping[str, float]` | default_factory | Joint positions keyed by stable ID; radians for rotation and metres for translation. |

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
