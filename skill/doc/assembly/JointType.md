# `JointType`

## API Definition

```python
class JointType(str, Enum): ...
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import JointType
```

## Purpose

Define the stable enum values accepted by `JointType`.

## Enum Values

| Member | Value |
| --- | --- |
| `FIXED` | `fixed` |
| `REVOLUTE` | `revolute` |
| `PRISMATIC` | `prismatic` |
| `CYLINDRICAL` | `cylindrical` |
| `SPHERICAL` | `spherical` |
| `PLANAR` | `planar` |
| `FREE` | `free` |

## Returns and Failures

Use enum members or their stable string values; do not invent undefined states.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
