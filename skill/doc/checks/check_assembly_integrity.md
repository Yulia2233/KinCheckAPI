# `check_assembly_integrity`

## API Definition

```python
check_assembly_integrity(*, assembly: AssemblyModel, motion_result: MotionResult | None = None, asset_root: str | pathlib.Path | None = None, component_ids: Optional[Sequence[str]] = None, geometric_connection_pairs: Optional[Sequence[Sequence[str]]] = None, containment_relations: Sequence[ContainmentRelation] = (), mechanical_relation_ids: Optional[Sequence[str]] = None, geometric_connection_tolerance_m: float = 0.0001, penetration_tolerance_m: float = 0.0, containment_escape_tolerance_m: float = 0.0001, sampling_scope: Literal['initial', 'motion_result'] = 'motion_result', require_single_network: bool = True) -> AssemblyIntegrityReport
```

Source: `src/kincheckapi/integrity.py`.

## Import

```python
from kincheckapi.checks import check_assembly_integrity
```

## Purpose

Check that Components remain one connected assembly at every static or MotionResult sample and report disconnection, detachment, or escape.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `motion_result` | `MotionResult | None` | `None` | The public `MotionResult` to query or check. |
| `asset_root` | `str | pathlib.Path | None` | `None` | Root directory within which meshes and other assets may resolve. |
| `component_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `component_ids` collection. |
| `geometric_connection_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | Public input or data field `geometric_connection_pairs`. |
| `containment_relations` | `Sequence[ContainmentRelation]` | `()` | Public input or data field `containment_relations`. |
| `mechanical_relation_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `mechanical_relation_ids` collection. |
| `geometric_connection_tolerance_m` | `float` | `0.0001` | `geometric_connection_tolerance_m` in metres; finite. |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m` in metres; finite. |
| `containment_escape_tolerance_m` | `float` | `0.0001` | `containment_escape_tolerance_m` in metres; finite. |
| `sampling_scope` | `Literal['initial', 'motion_result']` | `'motion_result'` | Public input or data field `sampling_scope`. |
| `require_single_network` | `bool` | `True` | Public input or data field `require_single_network`. |

## Returns and Failures

Returns `AssemblyIntegrityReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.

## Related Documentation

- [`Acceptance Checks`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
