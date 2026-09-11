# `ground_component`

## API Definition

```python
ground_component(*, assembly: AssemblyModel, component_id: str) -> AssemblyModel
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import ground_component
```

## Purpose

Mark an existing component as fixed in the assembly reference frame and return a new assembly.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `component_id` | `str` | required | Stable, resolvable component ID. |

## Returns and Failures

Returns `AssemblyModel`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
