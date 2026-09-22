# `WrenchSample`

## API Definition

```python
@dataclass(frozen=True)
class WrenchSample:
    time_s: float
    force_n: tuple[float, float, float]
    moment_nm: tuple[float, float, float]
    point_m: tuple[float, float, float]
    frame_id: str
    source: str
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import WrenchSample
```

## Purpose

WrenchSample(*, time_s: 'float', force_n: 'tuple[float, float, float]', moment_nm: 'tuple[float, float, float]', point_m: 'tuple[float, float, float]', frame_id: 'str' = 'world', source: 'str' = 'declared')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `force_n` | `tuple[float, float, float]` | required | Public input or data field `force_n`. |
| `moment_nm` | `tuple[float, float, float]` | required | Public input or data field `moment_nm`. |
| `point_m` | `tuple[float, float, float]` | required | `point_m` in metres; finite. |
| `frame_id` | `str` | `'world'` | Stable, resolvable `frame_id`. |
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
