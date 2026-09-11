# `run_checks`

## API 定义

```python
run_checks(*, assembly: 'AssemblyModel', scenario: 'Scenario | None' = None, motion_result: 'MotionResult | None' = None, checks: 'Sequence[CheckSpec]') -> 'CheckSuiteReport'
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import run_checks
```

## 用途

按 `CheckSpec` 顺序执行显式验收命题，返回 `CheckSuiteReport`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `scenario` | `Scenario | None` | `None` | 已绑定装配定义的不可变 `Scenario`。 |
| `motion_result` | `MotionResult | None` | `None` | 待查询或检查的公开 `MotionResult`。 |
| `checks` | `Sequence[CheckSpec]` | 必填 | `checks` 的公开输入或数据字段。 |

## 返回与失败

返回 `CheckSuiteReport`。

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
