# `KinematicCapabilities`

## API Definition

```python
@dataclass(frozen=True)
class KinematicCapabilities:
    joint_types: Mapping[str, bool]
    driver_modes: tuple[str, ...]
    output_channels: tuple[str, ...]
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import KinematicCapabilities
```

## Purpose

KinematicCapabilities(*, joint_types: 'Mapping[str, bool]', driver_modes: 'tuple[str, ...]' = ('position', 'speed'), output_channels: 'tuple[str, ...]' = ('joint', 'component', 'connector', 'residuals'))

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_types` | `Mapping[str, bool]` | required | Public input or data field `joint_types`. |
| `driver_modes` | `tuple[str, ...]` | `('position', 'speed')` | Public input or data field `driver_modes`. |
| `output_channels` | `tuple[str, ...]` | `('joint', 'component', 'connector', 'residuals')` | Public input or data field `output_channels`. |

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
