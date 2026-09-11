# CADIR Input Conversion

Read CADIR-exported MJCF, mapping, and mesh assets and construct a verifiable assembly model.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`AdapterResult`](AdapterResult.md) | Type | AdapterResult(assembly: 'Any', source_map: 'Mapping[str, Any]') |
| [`convert_mjcf`](convert_mjcf.md) | Function | Convert CADIR MJCF XML, mapping JSON, and mesh assets into an `AdapterResult`. Canonical `mesh_constraints` preserve gear/belt endpoint frames and SI radii as existing native Constraints, including carrier-relative multi-coordinate equations. Explicit coaxial joint aliases are retained in the source map. Legacy two-joint Coupling conversion remains supported; optional product-package preparation is provided by `kincheckapi.addon`. |

## Module Rules

- The XML root `model` must be non-empty and equal the mapping `root_definition_id`.
- XML, mapping, and meshes must come from the same export batch; asset resolution must not escape `asset_root`.
- Conversion returns an assembly model and source map; it does not replace assembly, topology, or Scenario validation.
