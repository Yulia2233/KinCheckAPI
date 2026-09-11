# `scenario_to_dict`

## API Definition

```python
scenario_to_dict(*, scenario: Scenario) -> dict[str, typing.Any]
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import scenario_to_dict
```

## Purpose

Convert Scenario into a deterministic JSON-compatible dictionary.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |

## Returns and Failures

Returns `dict[str, Any]`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
