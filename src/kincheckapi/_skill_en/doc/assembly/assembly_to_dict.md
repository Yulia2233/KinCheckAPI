# `assembly_to_dict`

## API Definition

```python
assembly_to_dict(*, assembly: AssemblyModel) -> dict[str, typing.Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import assembly_to_dict
```

## Purpose

Convert AssemblyModel into a deterministic JSON-compatible dictionary.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |

## Returns and Failures

Returns `dict[str, Any]`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
