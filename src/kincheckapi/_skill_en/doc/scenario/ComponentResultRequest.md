# `ComponentResultRequest`

## API Definition

```python
@dataclass(frozen=True)
class ComponentResultRequest:
    component_id: str
    connector_id: str | None
```

Source: `src/kincheckapi/scenario.py`.

## Import

```python
from kincheckapi.scenario import ComponentResultRequest
```

## Purpose

ComponentResultRequest(*, component_id: 'str', connector_id: 'str | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Scenario is immutable; every configuration function returns a new object.
- Use rad/rad/s for rotation, m/m/s for translation, and s for time; all numeric inputs must be finite.
- Run `validate_scenario()` before solving; do not continue with conflicting drivers, invalid windows, or unknown IDs.

## Related Documentation

- [`Scenarios and Drivers`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
