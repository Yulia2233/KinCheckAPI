# `read_component_state`

## API 定义

```python
read_component_state(*, motion_result: MotionResult, component_id: str, time_s: float) -> ComponentState
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import read_component_state
```

## 用途

读取组件世界姿态以及结果中可用的线/角速度和加速度。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |

## 返回与失败

返回 `ComponentState`。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
