# `list_constraint_residuals`

## API 定义

```python
list_constraint_residuals(*, motion_result: MotionResult, constraint_id: str | None = None) -> tuple[ConstraintResidual, ...]
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import list_constraint_residuals
```

## 用途

筛选并返回已记录的结构化证据：`list_constraint_residuals`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `constraint_id` | `str | None` | `None` | 稳定且可解析的 constraint ID。 |

## 返回与失败

返回 `tuple[ConstraintResidual, ...]`。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
