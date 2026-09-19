# `ContinuousInterferenceReport`

## API 定义

```python
@dataclass(frozen=True)
class ContinuousInterferenceReport:
    status: Literal['passed', 'failed', 'indeterminate', 'capability_failed', 'validation_failed', 'partial']
    options: ContinuousInterferenceOptions | None
    events: tuple[ContinuousContactEvent, ...]
    checked_component_pair_count: int
    query_count: int
    subdivision_count: int
    minimum_clearance_m: float | None
    clearance_lower_bound_m: float | None
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/continuous_result.py`。

## 导入

```python
from kincheckapi.continuous_result import ContinuousInterferenceReport
```

## 用途

表示 `ContinuousInterferenceReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `status` | `Literal['passed', 'failed', 'indeterminate', 'capability_failed', 'validation_failed', 'partial']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `options` | `ContinuousInterferenceOptions | None` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |
| `events` | `tuple[ContinuousContactEvent, ...]` | `()` | `events` 的公开输入或数据字段。 |
| `checked_component_pair_count` | `int` | `0` | `checked_component_pair_count` 的公开输入或数据字段。 |
| `query_count` | `int` | `0` | `query_count` 的公开输入或数据字段。 |
| `subdivision_count` | `int` | `0` | `subdivision_count` 的公开输入或数据字段。 |
| `minimum_clearance_m` | `float | None` | `None` | `minimum_clearance_m`，单位 m，必须为有限值。 |
| `clearance_lower_bound_m` | `float | None` | `None` | `clearance_lower_bound_m`，单位 m，必须为有限值。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 连续通过只表示声明的位姿插值和速度上界下已取得完整保守证据；不能外推到未记录的非刚体或动力学运动。
- `failed` 记录接触或间隙违规；`indeterminate` 表示预算、时间轴或几何证据不足，不能当作通过。
- 事件中的最早接触时间是上界，`certainty`、查询次数、细分次数和 options 必须随报告保存。

## 相关文档

- [`连续碰撞证据`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
