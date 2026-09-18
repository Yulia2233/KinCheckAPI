# `trace_connector_path`

## API Definition

```python
trace_connector_path(*, motion_result: Any, component_id: str, connector_id: str) -> Any
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import trace_connector_path
```

## Purpose

Compute times, path length, endpoints, and world-coordinate bounds from a recorded connector trajectory.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `Any` | required | The public `MotionResult` to query or check. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `connector_id` | `str` | required | Stable, resolvable connector ID. |

## Returns and Failures

Returns `Any`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
