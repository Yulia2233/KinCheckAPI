# `RatioMeasurement`

## API 定义

```python
RatioMeasurement = Literal
```

源码：`src/kincheckapi/checks.py`。

## 导入

```python
from kincheckapi.checks import RatioMeasurement
```

## 用途

定义 `RatioMeasurement` 使用的公开类型约定。

## 返回与失败

这是类型约定，不是可调用函数。

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
