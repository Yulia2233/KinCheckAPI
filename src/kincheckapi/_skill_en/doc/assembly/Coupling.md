# `Coupling`

## API Definition

```python
@dataclass(frozen=True)
class Coupling:
    coupling_id: str
    coupling_type: CouplingType | str
    joint_a_id: str
    joint_b_id: str
    ratio: float
    phase_offset: float
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Coupling
```

## Purpose

Coupling(coupling_id: 'str', coupling_type: 'CouplingType | str', joint_a_id: 'str', joint_b_id: 'str', ratio: 'float', phase_offset: 'float' = 0.0, display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `coupling_id` | `str` | required | Stable, resolvable `coupling_id`. |
| `coupling_type` | `CouplingType | str` | required | Public input or data field `coupling_type`. |
| `joint_a_id` | `str` | required | Stable, resolvable `joint_a_id`. |
| `joint_b_id` | `str` | required | Stable, resolvable `joint_b_id`. |
| `ratio` | `float` | required | Public input or data field `ratio`. |
| `phase_offset` | `float` | `0.0` | Public input or data field `phase_offset`. |
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
