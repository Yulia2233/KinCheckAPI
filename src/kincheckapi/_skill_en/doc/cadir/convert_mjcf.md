# `convert_mjcf`

## API Definition

```python
convert_mjcf(*, xml_path: str | pathlib.Path, mapping_path: str | pathlib.Path, asset_root: str | pathlib.Path | None = None) -> kincheckapi.cadir.AdapterResult
```

Source: `src/kincheckapi/cadir.py`.

## Import

```python
from kincheckapi.cadir import convert_mjcf
```

## Purpose

Convert CADIR MJCF XML, mapping JSON, and mesh assets into an `AdapterResult`. Canonical `mesh_constraints` preserve gear/belt endpoint frames and SI radii as existing native Constraints, including carrier-relative multi-coordinate equations. Explicit coaxial joint aliases are retained in the source map. Legacy two-joint Coupling conversion remains supported; optional product-package preparation is provided by `kincheckapi.addon`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `xml_path` | `str | pathlib.Path` | required | Path to the CADIR-exported MJCF XML. |
| `mapping_path` | `str | pathlib.Path` | required | Path to the mapping JSON from the same export batch as the XML. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |

## Returns and Failures

Returns `AdapterResult`.

## Module Constraints

- The XML root `model` must be non-empty and equal the mapping `root_definition_id`.
- XML, mapping, and meshes must come from the same export batch; asset resolution must not escape `asset_root`.
- Conversion returns an assembly model and source map; it does not replace assembly, topology, or Scenario validation.

## Related Documentation

- [`CADIR Input Conversion`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
