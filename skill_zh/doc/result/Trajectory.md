# `Trajectory`

## API 定义

```python
@dataclass(frozen=True)
class Trajectory:
    component_id: str
    times_s: tuple[float, ...]
    poses: tuple[Pose, ...]
    connector_id: str | None
    linear_velocities_m_s: tuple[tuple[float, float, float], ...] | None
    angular_velocities_rad_s: tuple[tuple[float, float, float], ...] | None
    linear_accelerations_m_s2: tuple[tuple[float, float, float], ...] | None
    angular_accelerations_rad_s2: tuple[tuple[float, float, float], ...] | None
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import Trajectory
```

## 用途

表示 `Trajectory` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `times_s` | `tuple[float, ...]` | 必填 | `times_s`，单位 s，必须为有限值。 |
| `poses` | `tuple[Pose, ...]` | 必填 | `poses` 的公开输入或数据字段。 |
| `connector_id` | `str | None` | `None` | 稳定且可解析的 connector ID。 |
| `linear_velocities_m_s` | `tuple[tuple[float, float, float], ...] | None` | `None` | `linear_velocities_m_s`，单位 m/s，必须为有限值。 |
| `angular_velocities_rad_s` | `tuple[tuple[float, float, float], ...] | None` | `None` | `angular_velocities_rad_s`，单位 rad/s，必须为有限值。 |
| `linear_accelerations_m_s2` | `tuple[tuple[float, float, float], ...] | None` | `None` | `linear_accelerations_m_s2`，单位 m/s^2，必须为有限值。 |
| `angular_accelerations_rad_s2` | `tuple[tuple[float, float, float], ...] | None` | `None` | `angular_accelerations_rad_s2` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
