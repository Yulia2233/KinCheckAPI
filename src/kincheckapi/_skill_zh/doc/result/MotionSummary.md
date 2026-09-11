# `MotionSummary`

## API 定义

```python
@dataclass(frozen=True)
class MotionSummary:
    status: Literal['completed', 'completed_with_warnings', 'partial']
    duration_s: float
    sample_count: int
    joint_extrema: tuple[JointExtrema, ...]
    maximum_position_residual_m: float
    maximum_orientation_residual_rad: float
    limit_event_count: int
    warning_count: int
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import MotionSummary
```

## 用途

表示 `MotionSummary` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `status` | `Literal['completed', 'completed_with_warnings', 'partial']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `duration_s` | `float` | 必填 | 运行总时长，单位 s，必须为有限正数。 |
| `sample_count` | `int` | 必填 | `sample_count` 的公开输入或数据字段。 |
| `joint_extrema` | `tuple[JointExtrema, ...]` | 必填 | `joint_extrema` 的公开输入或数据字段。 |
| `maximum_position_residual_m` | `float` | 必填 | `maximum_position_residual_m`，单位 m，必须为有限值。 |
| `maximum_orientation_residual_rad` | `float` | 必填 | `maximum_orientation_residual_rad`，单位 rad，必须为有限值。 |
| `limit_event_count` | `int` | 必填 | `limit_event_count` 的公开输入或数据字段。 |
| `warning_count` | `int` | 必填 | `warning_count` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
