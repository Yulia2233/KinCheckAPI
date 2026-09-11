# `build_kinematic_tree`

## API Definition

```python
build_kinematic_tree(*, assembly: AssemblyModel) -> KinematicTree
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import build_kinematic_tree
```

## Purpose

Analyze rigid groups, motion-tree edges, closure edges, ground, and disconnected islands; this is topology analysis, not motion solving.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |

## Returns and Failures

Returns `KinematicTree`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
