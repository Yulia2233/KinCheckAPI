# `ContinuousContactEvent`

## API 定义

```python
@dataclass(frozen=True)
class ContinuousContactEvent:
    component_a_id: str
    component_b_id: str
    time_interval_s: tuple[float, float]
    earliest_contact_time_s: float | None
    state_time_s: float
    signed_distance_m: float | None
    confirmed: bool
    certainty: Literal['certified', 'bracketed', 'indeterminate']
    event_type: Literal['contact', 'clearance_violation', 'initial_overlap', 'possible_contact']
    position_a_m: tuple[float, float, float] | None
    position_b_m: tuple[float, float, float] | None
    contact_normal: tuple[float, float, float] | None
    normal_source: str
    relative_velocity_m_s: tuple[float, float, float] | None
    relative_speed_m_s: float | None
    closing_speed_m_s: float | None
    contact_angle_rad: float | None
    pre_contact_time_s: float | None
    pre_contact_relative_velocity_m_s: tuple[float, float, float] | None
    evidence: tuple[Evidence, ...]
```

源码：`src/kincheckapi/continuous_result.py`。

## 导入

```python
from kincheckapi.continuous_result import ContinuousContactEvent
```

## 用途

表示 `ContinuousContactEvent` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `component_a_id` | `str` | 必填 | 稳定且可解析的 `component_a_id`。 |
| `component_b_id` | `str` | 必填 | 稳定且可解析的 `component_b_id`。 |
| `time_interval_s` | `tuple[float, float]` | 必填 | `time_interval_s`，单位 s，必须为有限值。 |
| `earliest_contact_time_s` | `float | None` | 必填 | `earliest_contact_time_s`，单位 s，必须为有限值。 |
| `state_time_s` | `float` | 必填 | `state_time_s`，单位 s，必须为有限值。 |
| `signed_distance_m` | `float | None` | 必填 | `signed_distance_m`，单位 m，必须为有限值。 |
| `confirmed` | `bool` | 必填 | `confirmed` 的公开输入或数据字段。 |
| `certainty` | `Literal['certified', 'bracketed', 'indeterminate']` | 必填 | `certainty` 的公开输入或数据字段。 |
| `event_type` | `Literal['contact', 'clearance_violation', 'initial_overlap', 'possible_contact']` | 必填 | `event_type` 的公开输入或数据字段。 |
| `position_a_m` | `tuple[float, float, float] | None` | `None` | `position_a_m`，单位 m，必须为有限值。 |
| `position_b_m` | `tuple[float, float, float] | None` | `None` | `position_b_m`，单位 m，必须为有限值。 |
| `contact_normal` | `tuple[float, float, float] | None` | `None` | `contact_normal` 的公开输入或数据字段。 |
| `normal_source` | `str` | `'unavailable'` | `normal_source` 的公开输入或数据字段。 |
| `relative_velocity_m_s` | `tuple[float, float, float] | None` | `None` | `relative_velocity_m_s`，单位 m/s，必须为有限值。 |
| `relative_speed_m_s` | `float | None` | `None` | `relative_speed_m_s`，单位 m/s，必须为有限值。 |
| `closing_speed_m_s` | `float | None` | `None` | `closing_speed_m_s`，单位 m/s，必须为有限值。 |
| `contact_angle_rad` | `float | None` | `None` | `contact_angle_rad`，单位 rad，必须为有限值。 |
| `pre_contact_time_s` | `float | None` | `None` | `pre_contact_time_s`，单位 s，必须为有限值。 |
| `pre_contact_relative_velocity_m_s` | `tuple[float, float, float] | None` | `None` | `pre_contact_relative_velocity_m_s`，单位 m/s，必须为有限值。 |
| `evidence` | `tuple[Evidence, ...]` | `()` | 支持结论的机器可读证据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 连续通过只表示声明的位姿插值和速度上界下已取得完整保守证据；不能外推到未记录的非刚体或动力学运动。
- `failed` 记录接触或间隙违规；`indeterminate` 表示预算、时间轴或几何证据不足，不能当作通过。
- 事件中的最早接触时间是上界，`certainty`、查询次数、细分次数和 options 必须随报告保存。

## 相关文档

- [`连续碰撞证据`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
