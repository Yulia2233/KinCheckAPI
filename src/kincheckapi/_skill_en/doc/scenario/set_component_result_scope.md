# `set_component_result_scope`

## API Definition

```python
set_component_result_scope(*, scenario: Scenario, scope: ComponentResultScope | str) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import set_component_result_scope
```

## Purpose

Select component trajectory recording scope. `all` always records all components; `requested` records requested objects when the list is non-empty and preserves the historical all-components behavior when empty.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `scope` | `ComponentResultScope | str` | required | Public input or data field `scope`. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.
- `requested` with an empty request list expands to all components as an explicit compatibility exception.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
