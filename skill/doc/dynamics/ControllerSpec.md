# `ControllerSpec`

## API Definition

```python
@dataclass(frozen=True)
class ControllerSpec:
    controller_id: str
    dof_limits: Mapping[str, float]
    velocity_limits: Mapping[str, float]
    rate_limits: Mapping[str, float]
    gain: float
    saturation_enabled: bool
    emergency_stop_time_s: float | None
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import ControllerSpec
```

## Purpose

Finite rigid-joint controller limits; no hidden ideal position servo.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `controller_id` | `str` | required | Stable, resolvable `controller_id`. |
| `dof_limits` | `Mapping[str, float]` | required | Public input or data field `dof_limits`. |
| `velocity_limits` | `Mapping[str, float]` | default_factory | Public input or data field `velocity_limits`. |
| `rate_limits` | `Mapping[str, float]` | default_factory | Public input or data field `rate_limits`. |
| `gain` | `float` | `1.0` | Public input or data field `gain`. |
| `saturation_enabled` | `bool` | `True` | Public input or data field `saturation_enabled`. |
| `emergency_stop_time_s` | `float | None` | `None` | `emergency_stop_time_s` in seconds; finite. |
| `source` | `str` | `'declared'` | Public input or data field `source`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
