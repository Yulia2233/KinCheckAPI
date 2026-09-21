# `DynamicSample`

## API Definition

```python
@dataclass(frozen=True)
class DynamicSample:
    time_s: float
    joint_positions: Mapping[str, float]
    joint_velocities: Mapping[str, float]
    joint_accelerations: Mapping[str, float]
    actuator_efforts: Mapping[str, float]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import DynamicSample
```

## Purpose

DynamicSample(*, time_s: 'float', joint_positions: 'Mapping[str, float]', joint_velocities: 'Mapping[str, float]', joint_accelerations: 'Mapping[str, float]', actuator_efforts: 'Mapping[str, float]')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `joint_velocities` | `Mapping[str, float]` | required | Public input or data field `joint_velocities`. |
| `joint_accelerations` | `Mapping[str, float]` | required | Public input or data field `joint_accelerations`. |
| `actuator_efforts` | `Mapping[str, float]` | required | Public input or data field `actuator_efforts`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
