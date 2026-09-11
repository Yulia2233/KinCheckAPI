# `check_constraint_equation_residuals`

## API 定义

```python
check_constraint_equation_residuals(*, motion_result: MotionResult, constraint_ids: Optional[Sequence[str]] = None, equation_types: Optional[Sequence[Literal['gear', 'belt', 'rack_pinion', 'coupling']]] = None, linear_tolerance_m: float = 1e-08, angular_tolerance_rad: float = 1e-08, start_time_s: float | None = None, end_time_s: float | None = None, disabled_constraint_ids: Sequence[str] = (), check_id: str = 'constraint_equation_residuals') -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_constraint_equation_residuals
```

## 用途

执行结构化检查：`check_constraint_equation_residuals`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `constraint_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `constraint_ids` 集合。 |
| `equation_types` | `Optional[Sequence[Literal['gear', 'belt', 'rack_pinion', 'coupling']]]` | `None` | `equation_types` 的公开输入或数据字段。 |
| `linear_tolerance_m` | `float` | `1e-08` | `linear_tolerance_m`，单位 m，必须为有限值。 |
| `angular_tolerance_rad` | `float` | `1e-08` | `angular_tolerance_rad`，单位 rad，必须为有限值。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `disabled_constraint_ids` | `Sequence[str]` | `()` | 显式指定的 `disabled_constraint_ids` 集合。 |
| `check_id` | `str` | `'constraint_equation_residuals'` | 调用方提供的稳定检查 ID，用于结果追溯。 |

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
