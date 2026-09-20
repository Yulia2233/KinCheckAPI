# `check_wrench_balance`

## API Definition

```python
check_wrench_balance(*, result: kincheckapi.physics_types.StaticResult, force_tolerance_n: float = 0.01, moment_tolerance_nm: float = 0.001) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/statics.py`.

## Import

```python
from kincheckapi.dynamics import check_wrench_balance
```

## Purpose

Accept only complete per-body force AND moment evidence.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.physics_types.StaticResult` | required | Public input or data field `result`. |
| `force_tolerance_n` | `float` | `0.01` | Public input or data field `force_tolerance_n`. |
| `moment_tolerance_nm` | `float` | `0.001` | Public input or data field `moment_tolerance_nm`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
