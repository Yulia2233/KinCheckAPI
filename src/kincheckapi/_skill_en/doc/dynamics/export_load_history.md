# `export_load_history`

## API Definition

```python
export_load_history(*, history: kincheckapi.dynamics_v07.DynamicsLoadHistory, path: str | pathlib.Path) -> pathlib.Path
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import export_load_history
```

## Purpose

Export a public result asset: `export_load_history`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `history` | `kincheckapi.dynamics_v07.DynamicsLoadHistory` | required | Public input or data field `history`. |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `Path`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
