# `Connector`

## API Definition

```python
@dataclass(frozen=True)
class Connector:
    connector_id: str
    pose: Pose
    display_name: str | None
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Connector
```

## Purpose

Connector(connector_id: 'str', pose: 'Pose' = <factory>, display_name: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `connector_id` | `str` | required | Stable, resolvable connector ID. |
| `pose` | `Pose` | default_factory | Public input or data field `pose`. |
| `display_name` | `str | None` | `None` | Public input or data field `display_name`. |
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
