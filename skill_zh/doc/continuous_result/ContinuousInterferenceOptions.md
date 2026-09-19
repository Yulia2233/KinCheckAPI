# `ContinuousInterferenceOptions`

## API 定义

```python
@dataclass(frozen=True)
class ContinuousInterferenceOptions:
    time_tolerance_s: float
    distance_tolerance_m: float
    minimum_clearance_m: float
    max_iterations: int
    max_subdivisions: int
    max_queries: int
    require_velocity_bound: bool
    interpolation: Optional[Literal['linear_pose', 'slerp_pose']]
    report_contact_normal: bool
```

源码：`src/kincheckapi/continuous_result.py`。

## 导入

```python
from kincheckapi.continuous_result import ContinuousInterferenceOptions
```

## 用途

表示 `ContinuousInterferenceOptions` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `time_tolerance_s` | `float` | `1e-05` | `time_tolerance_s`，单位 s，必须为有限值。 |
| `distance_tolerance_m` | `float` | `1e-06` | `distance_tolerance_m`，单位 m，必须为有限值。 |
| `minimum_clearance_m` | `float` | `0.0` | `minimum_clearance_m`，单位 m，必须为有限值。 |
| `max_iterations` | `int` | `64` | `max_iterations` 的公开输入或数据字段。 |
| `max_subdivisions` | `int` | `4096` | `max_subdivisions` 的公开输入或数据字段。 |
| `max_queries` | `int` | `100000` | `max_queries` 的公开输入或数据字段。 |
| `require_velocity_bound` | `bool` | `True` | `require_velocity_bound` 的公开输入或数据字段。 |
| `interpolation` | `Optional[Literal['linear_pose', 'slerp_pose']]` | `'slerp_pose'` | `interpolation` 的公开输入或数据字段。 |
| `report_contact_normal` | `bool` | `True` | `report_contact_normal` 的公开输入或数据字段。 |

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
