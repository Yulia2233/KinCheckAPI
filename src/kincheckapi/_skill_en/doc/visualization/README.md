# Offline Visualization

Export public motion results and meshes as an offline Three.js viewer.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`VIEWER_SCHEMA_VERSION`](VIEWER_SCHEMA_VERSION.md) | Constant | str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'. |
| [`ViewerArtifact`](ViewerArtifact.md) | Type | ViewerArtifact(*, root: 'Path', index_path: 'Path', manifest_path: 'Path', component_count: 'int', asset_count: 'int', missing_asset_component_ids: 'tuple[str, ...]' = ()) |
| [`export_motion_viewer`](export_motion_viewer.md) | Function | Export motion playback assets for an offline Three.js viewer. |

## Module Rules

- Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.
- Inspect motion status, recorded trajectories, and mesh assets before export.
- Use the viewer to review evidence, not as a replacement for numerical acceptance checks.
