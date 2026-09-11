# `Closure`

## API Definition

```python
@dataclass(frozen=True)
class Closure:
    closure_id: str
    constraint: Constraint
    position_tolerance_m: float
    orientation_tolerance_rad: float
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import Closure
```

## Purpose

Closure(closure_id: 'str', constraint: 'Constraint', position_tolerance_m: 'float' = 1e-06, orientation_tolerance_rad: 'float' = 1e-06)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `closure_id` | `str` | required | Stable, resolvable `closure_id`. |
| `constraint` | `Constraint` | required | Public input or data field `constraint`. |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
