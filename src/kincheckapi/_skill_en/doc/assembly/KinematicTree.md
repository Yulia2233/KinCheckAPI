# `KinematicTree`

## API Definition

```python
@dataclass(frozen=True)
class KinematicTree:
    root_group_ids: tuple[str, ...]
    component_groups: Mapping[str, str]
    group_components: Mapping[str, tuple[str, ...]]
    parent_component_id: Mapping[str, str | None]
    parent_group_id: Mapping[str, str | None]
    depth_by_component_id: Mapping[str, int]
    tree_edges: tuple[KinematicEdge, ...]
    closure_edges: tuple[KinematicEdge, ...]
    disconnected_group_ids: tuple[str, ...]
    grounded_group_ids: tuple[str, ...]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import KinematicTree
```

## Purpose

Backend-independent analysis of rigid groups and movable joints.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `root_group_ids` | `tuple[str, ...]` | required | Explicitly specified `root_group_ids` collection. |
| `component_groups` | `Mapping[str, str]` | required | Public input or data field `component_groups`. |
| `group_components` | `Mapping[str, tuple[str, ...]]` | required | Public input or data field `group_components`. |
| `parent_component_id` | `Mapping[str, str | None]` | required | Stable, resolvable `parent_component_id`. |
| `parent_group_id` | `Mapping[str, str | None]` | required | Stable, resolvable `parent_group_id`. |
| `depth_by_component_id` | `Mapping[str, int]` | required | Stable, resolvable `depth_by_component_id`. |
| `tree_edges` | `tuple[KinematicEdge, ...]` | required | Public input or data field `tree_edges`. |
| `closure_edges` | `tuple[KinematicEdge, ...]` | required | Public input or data field `closure_edges`. |
| `disconnected_group_ids` | `tuple[str, ...]` | required | Explicitly specified `disconnected_group_ids` collection. |
| `grounded_group_ids` | `tuple[str, ...]` | required | Explicitly specified `grounded_group_ids` collection. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
