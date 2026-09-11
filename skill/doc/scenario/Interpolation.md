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

str(object='') -> str str(bytes_or_buffer[, encoding[, errors]]) -> str Create a new string object from the given object. If encoding or errors is specified, then the object must expose a data buffer that will be decoded using the given encoding and error handler. Otherwise, returns the result of object.__str__() (if defined) or repr(object). encoding defaults to sys.getdefaultencoding(). errors defaults to 'strict'.

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
