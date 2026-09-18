# `PoseTrajectory`

## API 定义

```python
@dataclass(frozen=True)
class PoseTrajectory:
    target: Union[TargetReference, str, Mapping[str, Any]]
    points: tuple[kincheckapi.motion_contracts.PosePoint, ...]
    interpolation: str
    position_tolerance_m: float
    orientation_tolerance_rad: float
```

源码：`src/kincheckapi/motion_contracts.py`。

## 导入

```python
from kincheckapi.motion_contracts import PoseTrajectory
```

## 用途

表示 `PoseTrajectory` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `target` | `Union[TargetReference, str, Mapping[str, Any]]` | 必填 | `target` 的公开输入或数据字段。 |
| `points` | `tuple[kincheckapi.motion_contracts.PosePoint, ...]` | 必填 | `points` 的公开输入或数据字段。 |
| `interpolation` | `str` | `'linear'` | `interpolation` 的公开输入或数据字段。 |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m`，单位 m，必须为有限值。 |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad`，单位 rad，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.

## 相关文档

- [`运动工况契约`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
