# `set_joint_limits`

## API Definition

```python
set_joint_limits(*, assembly: AssemblyModel, joint_id: str, lower: float, upper: float) -> AssemblyModel
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import set_joint_limits
```

## Purpose

Set a field and return the updated immutable object: `set_joint_limits`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `lower` | `float` | required | Public input or data field `lower`. |
| `upper` | `float` | required | Public input or data field `upper`. |

## Returns and Failures

Returns `AssemblyModel`.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
