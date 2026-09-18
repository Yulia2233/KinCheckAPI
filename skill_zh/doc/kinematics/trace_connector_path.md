# `trace_connector_path`

## API 定义

```python
trace_connector_path(*, motion_result: Any, component_id: str, connector_id: str) -> Any
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import trace_connector_path
```

## 用途

从已记录 connector 轨迹计算时间序列、路径长度、起终点和世界坐标 bounds。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `motion_result` | `Any` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `connector_id` | `str` | 必填 | 稳定且可解析的 connector ID。 |

## 返回与失败

返回 `Any`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
