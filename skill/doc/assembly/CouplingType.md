# `CouplingType`

## API Definition

```python
class CouplingType(str, Enum): ...
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import CouplingType
```

## Purpose

Define the stable enum values accepted by `CouplingType`.

## Enum Values

| Member | Value |
| --- | --- |
| `GEAR` | `gear` |
| `BELT` | `belt` |
| `RACK_PINION` | `rack_pinion` |

## Returns and Failures

Use enum members or their stable string values; do not invent undefined states.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
