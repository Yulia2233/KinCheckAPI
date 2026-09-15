# `Interpolation`

## API Definition

```python
class Interpolation(str, Enum): ...
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import Interpolation
```

## Purpose

Define the stable enum values accepted by `Interpolation`.

## Enum Values

| Member | Value |
| --- | --- |
| `STEP` | `step` |
| `LINEAR` | `linear` |

## Returns and Failures

Use enum members or their stable string values; do not invent undefined states.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
