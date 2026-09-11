# `ReachabilityOptions`

## API Definition

```python
@dataclass(frozen=True)
class ReachabilityOptions:
    position_tolerance_m: float
    orientation_tolerance_rad: float
    initial_joint_positions: Mapping[str, float]
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import ReachabilityOptions
```

## Purpose

ReachabilityOptions(*, position_tolerance_m: 'float' = 1e-06, orientation_tolerance_rad: 'float' = 1e-06, initial_joint_positions: 'Mapping[str, float]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad` in radians; finite. |
| `initial_joint_positions` | `Mapping[str, float]` | default_factory | Public input or data field `initial_joint_positions`. |

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
