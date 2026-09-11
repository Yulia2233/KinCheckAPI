# `validate_assembly`

## API Definition

```python
validate_assembly(*, assembly: AssemblyModel) -> Any
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import validate_assembly
```

## Purpose

Aggregate consistency checks for assembly IDs, references, endpoints, ground, joints, constraints, closures, and couplings.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |

## Returns and Failures

Returns `Any`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
