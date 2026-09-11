# `Component`

## API Definition

```python
@dataclass(frozen=True)
class Component:
    component_id: str
    part_id: str
    initial_pose: Pose
    connectors: tuple[Connector, ...]
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Component
```

## Purpose

Component(component_id: 'str', part_id: 'str', initial_pose: 'Pose' = <factory>, connectors: 'tuple[Connector, ...]' = (), display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `part_id` | `str` | required | Stable, resolvable `part_id`. |
| `initial_pose` | `Pose` | default_factory | Public input or data field `initial_pose`. |
| `connectors` | `tuple[Connector, ...]` | `()` | Public input or data field `connectors`. |
| `display_name` | `str | None` | `None` | Public input or data field `display_name`. |
| `source_path` | `str | None` | `None` | Public input or data field `source_path`. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
