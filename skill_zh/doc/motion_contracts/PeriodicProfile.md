# `PeriodicProfile`

## API 定义

```python
@dataclass(frozen=True)
class PeriodicProfile:
    period_s: float
    amplitude: float
    offset: float
    phase_rad: float
```

源码：`src/kincheckapi/motion_contracts.py`。

## 导入

```python
from kincheckapi.motion_contracts import PeriodicProfile
```

## 用途

表示 `PeriodicProfile` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `period_s` | `float` | 必填 | 采样周期，单位 s，必须为有限正数。 |
| `amplitude` | `float` | 必填 | `amplitude` 的公开输入或数据字段。 |
| `offset` | `float` | `0.0` | `offset` 的公开输入或数据字段。 |
| `phase_rad` | `float` | `0.0` | `phase_rad`，单位 rad，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.

## 相关文档

- [`运动工况契约`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
