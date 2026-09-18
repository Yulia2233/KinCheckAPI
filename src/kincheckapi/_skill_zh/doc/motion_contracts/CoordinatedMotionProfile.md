# `CoordinatedMotionProfile`

## API 定义

```python
@dataclass(frozen=True)
class CoordinatedMotionProfile:
    axes: Mapping[str, tuple[float, ...]]
    times_s: tuple[float, ...]
    position_tolerance: float
```

源码：`src/kincheckapi/motion_contracts.py`。

## 导入

```python
from kincheckapi.motion_contracts import CoordinatedMotionProfile
```

## 用途

表示 `CoordinatedMotionProfile` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `axes` | `Mapping[str, tuple[float, ...]]` | 必填 | `axes` 的公开输入或数据字段。 |
| `times_s` | `tuple[float, ...]` | 必填 | `times_s`，单位 s，必须为有限值。 |
| `position_tolerance` | `float` | `1e-06` | `position_tolerance` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.

## 相关文档

- [`运动工况契约`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
