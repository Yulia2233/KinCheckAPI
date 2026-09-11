# `AdapterResult`

## API Definition

```python
@dataclass(frozen=True)
class AdapterResult:
    assembly: Any
    source_map: Mapping[str, Any]
```

Source: `src/kincheckapi/cadir.py`.

## Import

```python
from kincheckapi.cadir import AdapterResult
```

## Purpose

AdapterResult(assembly: 'Any', source_map: 'Mapping[str, Any]')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `Any` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `source_map` | `Mapping[str, Any]` | required | Public input or data field `source_map`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The XML root `model` must be non-empty and equal the mapping `root_definition_id`.
- XML, mapping, and meshes must come from the same export batch; asset resolution must not escape `asset_root`.
- Conversion returns an assembly model and source map; it does not replace assembly, topology, or Scenario validation.
- Use `assembly` as the downstream verification input and retain `source_map` to trace CADIR source IDs.

## Related Documentation

- [`CADIR Input Conversion`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
