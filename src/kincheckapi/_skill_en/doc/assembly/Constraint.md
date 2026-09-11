# `Constraint`

## API Definition

```python
@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    connector_a: ConnectorRef
    connector_b: ConnectorRef
    constraint_type: str
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Constraint
```

## Purpose

Constraint(constraint_id: 'str', connector_a: 'ConnectorRef', connector_b: 'ConnectorRef', constraint_type: 'str' = 'coincident', display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `constraint_id` | `str` | required | Stable, resolvable constraint ID. |
| `connector_a` | `ConnectorRef` | required | Public input or data field `connector_a`. |
| `connector_b` | `ConnectorRef` | required | Public input or data field `connector_b`. |
| `constraint_type` | `str` | `'coincident'` | Public input or data field `constraint_type`. |
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
