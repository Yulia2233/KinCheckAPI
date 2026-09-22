# `transfer_loads`

## API Definition

```python
transfer_loads(*, model: kincheckapi.structural.StructuralModel, loads: Sequence[kincheckapi.structural.StructuralLoad] = (), maps: Sequence[kincheckapi.structural.LoadTransferMap] = ()) -> tuple[numpy.ndarray, kincheckapi.physics_types.PhysicsReport]
```

Source: `src/kincheckapi/structural.py`.

## Import

```python
from kincheckapi.dynamics import transfer_loads
```

## Purpose

Assemble loads into the model vector and prove force bookkeeping.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.structural.StructuralModel` | required | Public input or data field `model`. |
| `loads` | `Sequence[kincheckapi.structural.StructuralLoad]` | `()` | Public input or data field `loads`. |
| `maps` | `Sequence[kincheckapi.structural.LoadTransferMap]` | `()` | Public input or data field `maps`. |

## Returns and Failures

Returns `tuple[np.ndarray, PhysicsReport]`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
