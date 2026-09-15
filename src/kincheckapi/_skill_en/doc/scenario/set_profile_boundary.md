# `set_profile_boundary`

## API Definition

```python
set_profile_boundary(*, scenario: Scenario, behavior: ProfileBoundary | str) -> Scenario
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import set_profile_boundary
```

## Purpose

Set a field and return the updated immutable object: `set_profile_boundary`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `behavior` | `ProfileBoundary | str` | required | Public input or data field `behavior`. |

## Returns and Failures

Returns `Scenario`.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
