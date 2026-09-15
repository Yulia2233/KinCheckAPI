# Offline Visualization

Export public motion results and meshes as an offline Three.js viewer.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`VIEWER_SCHEMA_VERSION`](VIEWER_SCHEMA_VERSION.md) | Constant | Expose the public constant `VIEWER_SCHEMA_VERSION`. |
| [`ViewerArtifact`](ViewerArtifact.md) | Type | ViewerArtifact(*, root: 'Path', index_path: 'Path', manifest_path: 'Path', component_count: 'int', asset_count: 'int', missing_asset_component_ids: 'tuple[str, ...]' = ()) |
| [`export_motion_viewer`](export_motion_viewer.md) | Function | Export motion playback assets for an offline Three.js viewer. |

## Module Rules

- Visualization consumes only public AssemblyModel and MotionResult data, not private backend state.
- Inspect motion status, recorded trajectories, and mesh assets before export.
- Use the viewer to review evidence, not as a replacement for numerical acceptance checks.
