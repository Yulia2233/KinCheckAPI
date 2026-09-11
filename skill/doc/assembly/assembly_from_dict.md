# `assembly_from_dict`

## API Definition

```python
assembly_from_dict(*, data: Mapping[str, Any]) -> AssemblyModel
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import assembly_from_dict
```

## Purpose

Reconstruct AssemblyModel from a parsed mapping; assembly and topology validation are still required.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `data` | `Mapping[str, Any]` | required | Public input or data field `data`. |

## Returns and Failures

Returns `AssemblyModel`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
