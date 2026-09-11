# `check_trajectory`

## API 定义

```python
check_trajectory(*, motion_result: MotionResult, component_id: str | None = None, connector_id: str | None = None, max_speed_m_s: float | None = None, max_angular_speed_rad_s: float | None = None, max_acceleration_m_s2: float | None = None, max_angular_acceleration_rad_s2: float | None = None, max_position_residual_m: float | None = None, max_orientation_residual_rad: float | None = None, min_path_length_m: float | None = None, max_path_length_m: float | None = None, position_bounds_m: Optional[Mapping[str, Sequence[float]]] = None, limit_joint_ids: Optional[Sequence[str]] = None, maximum_limit_event_count: int | None = None, maximum_exceeded_limit_event_count: int | None = 0, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'trajectory') -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_trajectory
```

## 用途

执行结构化检查：`check_trajectory`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_id` | `str | None` | `None` | 稳定且可解析的 component ID。 |
| `connector_id` | `str | None` | `None` | 稳定且可解析的 connector ID。 |
| `max_speed_m_s` | `float | None` | `None` | `max_speed_m_s`，单位 m/s，必须为有限值。 |
| `max_angular_speed_rad_s` | `float | None` | `None` | `max_angular_speed_rad_s`，单位 rad/s，必须为有限值。 |
| `max_acceleration_m_s2` | `float | None` | `None` | `max_acceleration_m_s2`，单位 m/s^2，必须为有限值。 |
| `max_angular_acceleration_rad_s2` | `float | None` | `None` | `max_angular_acceleration_rad_s2` 的公开输入或数据字段。 |
| `max_position_residual_m` | `float | None` | `None` | `max_position_residual_m`，单位 m，必须为有限值。 |
| `max_orientation_residual_rad` | `float | None` | `None` | `max_orientation_residual_rad`，单位 rad，必须为有限值。 |
| `min_path_length_m` | `float | None` | `None` | `min_path_length_m`，单位 m，必须为有限值。 |
| `max_path_length_m` | `float | None` | `None` | `max_path_length_m`，单位 m，必须为有限值。 |
| `position_bounds_m` | `Optional[Mapping[str, Sequence[float]]]` | `None` | `position_bounds_m`，单位 m，必须为有限值。 |
| `limit_joint_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `limit_joint_ids` 集合。 |
| `maximum_limit_event_count` | `int | None` | `None` | `maximum_limit_event_count` 的公开输入或数据字段。 |
| `maximum_exceeded_limit_event_count` | `int | None` | `0` | `maximum_exceeded_limit_event_count` 的公开输入或数据字段。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `check_id` | `str` | `'trajectory'` | 调用方提供的稳定检查 ID，用于结果追溯。 |

## 返回与失败

返回 `CheckReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 检查必须对应明确的对象、时间窗、期望值、阈值和单位。
- 检查对象为空、证据为空或 MotionResult 不完整时不得通过。
- `CheckReport.passed` 是最终布尔结论；同时保留 evidence、issues 和 metadata。
- 装配体整体性检查支持任意数量的 Component；`component_ids=None` 检查整个装配体。
- 机械、容纳/导向和几何连接共同形成连接图；几何连接必须记录米制容差。

## 相关文档

- [`验收检查`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
