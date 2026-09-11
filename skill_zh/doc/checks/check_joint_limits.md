# `check_joint_limits`

## API 定义

```python
check_joint_limits(*, assembly: AssemblyModel, motion_result: MotionResult, joint_ids: Optional[Sequence[str]] = None, tolerance: float = 0.0, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'joint_limits') -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_joint_limits
```

## 用途

执行结构化检查：`check_joint_limits`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `joint_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `joint_ids` 集合。 |
| `tolerance` | `float` | `0.0` | `tolerance` 的公开输入或数据字段。 |
| `start_time_s` | `float | None` | `None` | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | `None` | 时间窗终点，单位 s。 |
| `check_id` | `str` | `'joint_limits'` | 调用方提供的稳定检查 ID，用于结果追溯。 |

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
