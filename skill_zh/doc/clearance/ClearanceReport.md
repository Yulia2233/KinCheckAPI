# `ClearanceReport`

## API 定义

```python
@dataclass(frozen=True)
class ClearanceReport:
    operation: Literal['interference', 'minimum_clearance', 'motion_envelope']
    passed: bool
    status: Literal['passed', 'failed', 'capability_failed', 'partial']
    events: tuple[InterferenceEvent, ...]
    measurements: tuple[MinimumClearance, ...]
    envelopes: tuple[MotionEnvelope, ...]
    checked_component_pair_count: int
    checked_sample_count: int
    first_failure_time_s: float | None
    maximum_penetration_depth_m: float
    backend_id: str | None
    backend_version: str | None
    sampling_scope: Literal['motion_result', 'solver_steps']
    sampling_period_s: float
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/clearance_result.py`。

## 导入

```python
from kincheckapi.clearance import ClearanceReport
```

## 用途

表示 `ClearanceReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `operation` | `Literal['interference', 'minimum_clearance', 'motion_envelope']` | 必填 | `operation` 的公开输入或数据字段。 |
| `passed` | `bool` | 必填 | 结构化布尔结论；必须与 issues 和实际证据一起读取。 |
| `status` | `Literal['passed', 'failed', 'capability_failed', 'partial']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `events` | `tuple[InterferenceEvent, ...]` | `()` | `events` 的公开输入或数据字段。 |
| `measurements` | `tuple[MinimumClearance, ...]` | `()` | `measurements` 的公开输入或数据字段。 |
| `envelopes` | `tuple[MotionEnvelope, ...]` | `()` | `envelopes` 的公开输入或数据字段。 |
| `checked_component_pair_count` | `int` | `0` | `checked_component_pair_count` 的公开输入或数据字段。 |
| `checked_sample_count` | `int` | `0` | `checked_sample_count` 的公开输入或数据字段。 |
| `first_failure_time_s` | `float | None` | `None` | `first_failure_time_s`，单位 s，必须为有限值。 |
| `maximum_penetration_depth_m` | `float` | `0.0` | `maximum_penetration_depth_m`，单位 m，必须为有限值。 |
| `backend_id` | `str | None` | `'python-fcl'` | 稳定且可解析的 `backend_id`。 |
| `backend_version` | `str | None` | `None` | `backend_version` 的公开输入或数据字段。 |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |
| `sampling_period_s` | `float` | `0.0` | `sampling_period_s`，单位 s，必须为有限值。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 结果来自三角网格和离散时间采样，不是连续时间无碰撞证明。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
