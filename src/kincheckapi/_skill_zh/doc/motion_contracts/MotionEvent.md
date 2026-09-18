# `MotionEvent`

## API 定义

```python
@dataclass(frozen=True)
class MotionEvent:
    event_type: str
    time_s: float
    joint_id: str
    value: float | None
```

源码：`src/kincheckapi/motion_contracts.py`。

## 导入

```python
from kincheckapi.motion_contracts import MotionEvent
```

## 用途

表示 `MotionEvent` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `event_type` | `str` | 必填 | `event_type` 的公开输入或数据字段。 |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `value` | `float | None` | `None` | `value` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.

## 相关文档

- [`运动工况契约`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
