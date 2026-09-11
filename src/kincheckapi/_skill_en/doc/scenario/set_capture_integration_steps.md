# `set_capture_integration_steps`

## API Definition

```python
set_capture_integration_steps(*, scenario: Scenario, enabled: bool, component_ids: Optional[Sequence[str]] = None) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import set_capture_integration_steps
```

## Purpose

Opt into retaining every internal physics backend integration-step pose. The default is off to keep long MotionResults compact. Clearance checks using ``sampling_scope='solver_steps'`` require this explicit capture.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `enabled` | `bool` | required | Public input or data field `enabled`. |
| `component_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `component_ids` collection. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
