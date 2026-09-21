# `check_occurrence_support`

## API Definition

```python
check_occurrence_support(*, package_path: str | pathlib.Path) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/physics_geometry.py`.

## Import

```python
from kincheckapi.dynamics import check_occurrence_support
```

## Purpose

Check the actual CAD joint/fastener graph, including every hardware leaf. Hierarchy placement alone is never a mounting relation. This topological gate complements, and cannot replace, geometric mounting/clearance checks.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | required | Public input or data field `package_path`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
