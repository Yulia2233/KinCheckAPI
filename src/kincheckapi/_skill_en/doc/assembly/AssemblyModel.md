# `AssemblyModel`

## API Definition

```python
@dataclass(frozen=True)
class AssemblyModel:
    assembly_id: str
    parts: tuple[Part, ...]
    components: tuple[Component, ...]
    joints: tuple[Joint, ...]
    constraints: tuple[Constraint, ...]
    couplings: tuple[Coupling, ...]
    closures: tuple[Closure, ...]
    grounds: tuple[Ground, ...]
    collision_exclusions: tuple[tuple[str, str], ...]
    display_name: str | None
    source_path: str | None
    metadata: Mapping[str, Any]
```

Source: `src/kincheckapi/assembly.py`.

## Import

```python
from kincheckapi.assembly import AssemblyModel
```

## Purpose

AssemblyModel(assembly_id: 'str', parts: 'tuple[Part, ...]' = (), components: 'tuple[Component, ...]' = (), joints: 'tuple[Joint, ...]' = (), constraints: 'tuple[Constraint, ...]' = (), couplings: 'tuple[Coupling, ...]' = (), closures: 'tuple[Closure, ...]' = (), grounds: 'tuple[Ground, ...]' = (), collision_exclusions: 'tuple[tuple[str, str], ...]' = (), display_name: 'str | None' = None, source_path: 'str | None' = None, metadata: 'Mapping[str, Any]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly_id` | `str` | required | Stable, resolvable `assembly_id`. |
| `parts` | `tuple[Part, ...]` | `()` | Public input or data field `parts`. |
| `components` | `tuple[Component, ...]` | `()` | Public input or data field `components`. |
| `joints` | `tuple[Joint, ...]` | `()` | Public input or data field `joints`. |
| `constraints` | `tuple[Constraint, ...]` | `()` | Public input or data field `constraints`. |
| `couplings` | `tuple[Coupling, ...]` | `()` | Public input or data field `couplings`. |
| `closures` | `tuple[Closure, ...]` | `()` | Public input or data field `closures`. |
| `grounds` | `tuple[Ground, ...]` | `()` | Public input or data field `grounds`. |
| `collision_exclusions` | `tuple[tuple[str, str], ...]` | `()` | Public input or data field `collision_exclusions`. |
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
