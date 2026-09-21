# `LoadTransferMap`

## API Definition

```python
@dataclass(frozen=True)
class LoadTransferMap:
    source_id: str
    target_dofs: tuple[int, ...]
    force_components: tuple[float, ...]
    reference_point_m: tuple[float, float, float]
    coordinate_frame: str
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import LoadTransferMap
```

## Purpose

LoadTransferMap(*, source_id: 'str', target_dofs: 'tuple[int, ...]', force_components: 'tuple[float, ...]', reference_point_m: 'tuple[float, float, float]' = (0.0, 0.0, 0.0), coordinate_frame: 'str' = 'world')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `source_id` | `str` | required | Stable, resolvable `source_id`. |
| `target_dofs` | `tuple[int, ...]` | required | Public input or data field `target_dofs`. |
| `force_components` | `tuple[float, ...]` | required | Public input or data field `force_components`. |
| `reference_point_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `reference_point_m` in metres; finite. |
| `coordinate_frame` | `str` | `'world'` | Public input or data field `coordinate_frame`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
