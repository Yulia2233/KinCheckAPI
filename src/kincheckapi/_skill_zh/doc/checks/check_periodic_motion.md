# `check_periodic_motion`

## API 定义

```python
check_periodic_motion(*, motion_result: MotionResult, joint_id: str, period_s: float, periods: int = 1, position_tolerance: float = 1e-06, velocity_tolerance: float = 1e-06, check_id: str = 'periodic_motion') -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_periodic_motion
```

## 用途

执行结构化检查：`check_periodic_motion`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `period_s` | `float` | 必填 | 采样周期，单位 s，必须为有限正数。 |
| `periods` | `int` | `1` | `periods` 的公开输入或数据字段。 |
| `position_tolerance` | `float` | `1e-06` | `position_tolerance` 的公开输入或数据字段。 |
| `velocity_tolerance` | `float` | `1e-06` | `velocity_tolerance` 的公开输入或数据字段。 |
| `check_id` | `str` | `'periodic_motion'` | 调用方提供的稳定检查 ID，用于结果追溯。 |

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
