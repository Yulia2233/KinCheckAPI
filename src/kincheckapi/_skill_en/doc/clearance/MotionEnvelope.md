# `MotionEnvelope`

## API Definition

```python
@dataclass(frozen=True)
class MotionEnvelope:
    component_id: str
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]
    sample_times_s: tuple[float, ...]
    mesh_vertex_count: int
    mesh_path: str
    mesh_sha256: str | None
    mesh_triangle_count: int | None
    sample_bounds: tuple[EnvelopeSample, ...]
    backend_id: str
    sampling_scope: Literal['motion_result', 'solver_steps']
```

Source: `src/kincheckapi/clearance_result.py`.

## Import

```python
from kincheckapi.clearance import MotionEnvelope
```

## Purpose

MotionEnvelope(*, component_id: 'str', world_min_position_m: 'tuple[float, float, float]', world_max_position_m: 'tuple[float, float, float]', sample_times_s: 'tuple[float, ...]', mesh_vertex_count: 'int', mesh_path: 'str', mesh_sha256: 'str | None' = None, mesh_triangle_count: 'int | None' = None, sample_bounds: 'tuple[EnvelopeSample, ...]' = (), backend_id: 'str' = 'python-fcl', sampling_scope: 'SamplingScope' = 'motion_result')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `world_min_position_m` | `tuple[float, float, float]` | required | `world_min_position_m` in metres; finite. |
| `world_max_position_m` | `tuple[float, float, float]` | required | `world_max_position_m` in metres; finite. |
| `sample_times_s` | `tuple[float, ...]` | required | Strictly increasing actual sample times in seconds. |
| `mesh_vertex_count` | `int` | required | Public input or data field `mesh_vertex_count`. |
| `mesh_path` | `str` | required | Public input or data field `mesh_path`. |
| `mesh_sha256` | `str | None` | `None` | Public input or data field `mesh_sha256`. |
| `mesh_triangle_count` | `int | None` | `None` | Public input or data field `mesh_triangle_count`. |
| `sample_bounds` | `tuple[EnvelopeSample, ...]` | `()` | Public input or data field `sample_bounds`. |
| `backend_id` | `str` | `'python-fcl'` | Stable, resolvable `backend_id`. |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | Public input or data field `sampling_scope`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Specify component pairs or scope, `asset_root`, time window, and tolerance explicitly.
- Discrete interference, minimum-clearance, and envelope results use sampled states; call `check_continuous_interference()` explicitly for cross-sample evidence.
- Do not interpret empty pairs, empty samples, missing meshes, or partial motion as a safety pass.

## Related Documentation

- [`Geometric Safety`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
