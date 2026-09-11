# `add_component`

## API Definition

```python
add_component(*, assembly: AssemblyModel, component: Component) -> AssemblyModel
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import add_component
```

## Purpose

Add data and return the updated immutable object: `add_component`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `component` | `Component` | required | Public input or data field `component`. |

## Returns and Failures

Returns `AssemblyModel`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
