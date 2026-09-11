# `Ground`

## API Definition

```python
@dataclass(frozen=True)
class Ground:
    component_id: str
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Ground
```

## Purpose

Ground(component_id: 'str')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
