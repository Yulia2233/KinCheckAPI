# `validate_scenario`

## API Definition

```python
validate_scenario(*, scenario: Scenario) -> ValidationResult
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import validate_scenario
```

## Purpose

Aggregate time, reference, limit, and driver conflict errors.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |

## Returns and Failures

Returns `ValidationResult`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
