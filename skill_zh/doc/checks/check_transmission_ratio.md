# `check_transmission_ratio`

## API 定义

```python
check_transmission_ratio(*, motion_result: MotionResult, input_joint_id: str, output_joint_id: str, expected_ratio: float, expected_direction: Literal['same', 'opposite'], measurement: Literal['angular_velocity', 'linear_velocity', 'angular_displacement', 'linear_displacement', 'angular_to_linear_velocity', 'angular_to_linear_displacement'] = 'angular_velocity', start_time_s: float | None = None, end_time_s: float | None = None, relative_tolerance: float = 0.001, minimum_sample_count: int = 3, minimum_valid_fraction: float = 0.8, minimum_input_magnitude: float = 1e-09, minimum_output_magnitude: float = 1e-12, check_id: str = 'transmission_ratio') -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_transmission_ratio
```

## 用途

执行结构化检查：`check_transmission_ratio`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `input_joint_id` | `str` | 必填 | 稳定且可解析的 `input_joint_id`。 |
| `output_joint_id` | `str` | 必填 | 稳定且可解析的 `output_joint_id`。 |
| `expected_ratio` | `float` | 必填 | 期望传动比的正幅值；方向由 `expected_direction` 单独表达。 |
| `expected_direction` | `Literal['same', 'opposite']` | 必填 | 期望输出与输入同向 `same` 或反向 `opposite`。 |
| `measurement` | `Literal['angular_velocity', 'linear_velocity', 'angular_displacement', 'linear_displacement', 'angular_to_linear_velocity', 'angular_to_linear_displacement']` | `'angular_velocity'` | `measurement` 的公开输入或数据字段。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `relative_tolerance` | `float` | `0.001` | `relative_tolerance` 的公开输入或数据字段。 |
| `minimum_sample_count` | `int` | `3` | `minimum_sample_count` 的公开输入或数据字段。 |
| `minimum_valid_fraction` | `float` | `0.8` | `minimum_valid_fraction` 的公开输入或数据字段。 |
| `minimum_input_magnitude` | `float` | `1e-09` | `minimum_input_magnitude` 的公开输入或数据字段。 |
| `minimum_output_magnitude` | `float` | `1e-12` | `minimum_output_magnitude` 的公开输入或数据字段。 |
| `check_id` | `str` | `'transmission_ratio'` | 调用方提供的稳定检查 ID，用于结果追溯。 |

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
