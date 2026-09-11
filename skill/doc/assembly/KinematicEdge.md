# `KinematicEdge`

## API Definition

```python
@dataclass(frozen=True)
class KinematicEdge:
    edge_id: str
    joint_id: str
    parent_group_id: str
    child_group_id: str
    parent_component_id: str
    child_component_id: str
    joint_type: JointType | str
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import KinematicEdge
```

## Purpose

One directed movable-joint edge in an analyzed kinematic graph.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `edge_id` | `str` | required | Stable, resolvable `edge_id`. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `parent_group_id` | `str` | required | Stable, resolvable `parent_group_id`. |
| `child_group_id` | `str` | required | Stable, resolvable `child_group_id`. |
| `parent_component_id` | `str` | required | Stable, resolvable `parent_component_id`. |
| `child_component_id` | `str` | required | Stable, resolvable `child_component_id`. |
| `joint_type` | `JointType | str` | required | Public input or data field `joint_type`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
