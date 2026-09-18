# `record_verification_reports`

## API 定义

```python
record_verification_reports(*, motion_result: MotionResult, reports: Sequence[Any]) -> MotionResult
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import record_verification_reports
```

## 用途

执行公开操作 `record_verification_reports`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `reports` | `Sequence[Any]` | 必填 | `reports` 的公开输入或数据字段。 |

## 返回与失败

返回 `MotionResult`。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
