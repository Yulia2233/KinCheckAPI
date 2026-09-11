# `validate_topology`

## API Definition

```python
validate_topology(*, assembly: AssemblyModel) -> ValidationResult
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import validate_topology
```

## Purpose

Validate motion-graph boundaries, connectivity, ground, tree edges, and closure edges before solving.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |

## Returns and Failures

Returns `ValidationResult`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
