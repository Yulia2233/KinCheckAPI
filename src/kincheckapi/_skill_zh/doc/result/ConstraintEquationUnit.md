# `ConstraintEquationUnit`

## API 定义

```python
ConstraintEquationUnit = Literal
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import ConstraintEquationUnit
```

## 用途

定义 `ConstraintEquationUnit` 使用的公开类型约定。

## 返回与失败

这是类型约定，不是可调用函数。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
