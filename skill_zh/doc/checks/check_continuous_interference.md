# `check_continuous_interference`

## API 定义

```python
check_continuous_interference(*, assembly: AssemblyModel, motion_result: MotionResult, component_pairs: Optional[Sequence[Sequence[str]]] = None, **parameters: Any) -> CheckReport
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import check_continuous_interference
```

## 用途

在声明的分段刚体位姿插值下，跨相邻轨迹样本保守地检查显式组件对，并返回 TOI 区间证据。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | `component_pairs` 的公开输入或数据字段。 |
| `parameters` | `Any` | 必填 | 该检查类型的显式参数；不得依赖未记录的隐式默认验收标准。 |

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
