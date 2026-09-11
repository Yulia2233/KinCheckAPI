# `exclude_collision_pair`

## API Definition

```python
exclude_collision_pair(*, assembly: AssemblyModel, component_a_id: str, component_b_id: str) -> AssemblyModel
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import exclude_collision_pair
```

## Purpose

Add two distinct existing components to the collision exclusion set; this changes later geometric acceptance scope.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `component_a_id` | `str` | required | Stable, resolvable `component_a_id`. |
| `component_b_id` | `str` | required | Stable, resolvable `component_b_id`. |

## Returns and Failures

Returns `AssemblyModel`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
