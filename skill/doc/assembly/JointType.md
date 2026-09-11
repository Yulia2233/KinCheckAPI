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

str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'.

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
