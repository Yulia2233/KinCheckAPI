# `list_interference_events`

## API 定义

```python
list_interference_events(*, interference_result: InterferenceResult) -> tuple[InterferenceEvent, ...]
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import list_interference_events
```

## 用途

筛选并返回已记录的结构化证据：`list_interference_events`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `interference_result` | `InterferenceResult` | 必填 | `interference_result` 的公开输入或数据字段。 |

## 返回与失败

返回 `tuple[InterferenceEvent, ...]`。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
