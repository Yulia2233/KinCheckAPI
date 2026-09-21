# `measure_interface_centers`

## API Definition

```python
measure_interface_centers(*, package_path: str | pathlib.Path, occurrence_id: str, interface_name: str)
```

Source: `src/kincheckapi/physics_cadir.py`.

## Import

```python
from kincheckapi.dynamics import measure_interface_centers
```

## Purpose

Resolve named CAD faces and return their measured definition-frame centres. Used for load attachment evidence, never to infer a missing interface by name or appearance. Coordinates are SI and topology IDs remain in the response.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | required | Public input or data field `package_path`. |
| `occurrence_id` | `str` | required | Stable, resolvable `occurrence_id`. |
| `interface_name` | `str` | required | Public input or data field `interface_name`. |

## Returns and Failures

Returns `未标注`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
