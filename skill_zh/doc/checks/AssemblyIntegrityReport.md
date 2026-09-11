# `AssemblyIntegrityReport`

## API 定义

```python
@dataclass(frozen=True)
class AssemblyIntegrityReport:
    passed: bool
    status: Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']
    checked_component_ids: tuple[str, ...]
    connected_component_ids: tuple[str, ...]
    disconnected_component_ids: tuple[str, ...]
    detached_component_ids: tuple[str, ...]
    out_of_bounds_component_ids: tuple[str, ...]
    failed_relation_ids: tuple[str, ...]
    failed_sample_times_s: tuple[float, ...]
    connected_network_count_by_sample: tuple[tuple[float, int], ...]
    geometric_connections: tuple[IntegrityRelationResult, ...]
    containment_results: tuple[IntegrityRelationResult, ...]
    mechanical_relation_results: tuple[IntegrityRelationResult, ...]
    checked_sample_count: int
    geometric_connection_tolerance_m: float
    penetration_tolerance_m: float
    containment_escape_tolerance_m: float
    sampling_scope: Literal['initial', 'motion_result']
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
    operation: str
```

源码：`src/kincheckapi/integrity.py`。

## 导入

```python
from kincheckapi.checks import AssemblyIntegrityReport
```

## 用途

表示 `AssemblyIntegrityReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `passed` | `bool` | 必填 | 结构化布尔结论；必须与 issues 和实际证据一起读取。 |
| `status` | `Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `checked_component_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `checked_component_ids` 集合。 |
| `connected_component_ids` | `tuple[str, ...]` | `()` | 显式指定的 `connected_component_ids` 集合。 |
| `disconnected_component_ids` | `tuple[str, ...]` | `()` | 显式指定的 `disconnected_component_ids` 集合。 |
| `detached_component_ids` | `tuple[str, ...]` | `()` | 显式指定的 `detached_component_ids` 集合。 |
| `out_of_bounds_component_ids` | `tuple[str, ...]` | `()` | 显式指定的 `out_of_bounds_component_ids` 集合。 |
| `failed_relation_ids` | `tuple[str, ...]` | `()` | 显式指定的 `failed_relation_ids` 集合。 |
| `failed_sample_times_s` | `tuple[float, ...]` | `()` | `failed_sample_times_s`，单位 s，必须为有限值。 |
| `connected_network_count_by_sample` | `tuple[tuple[float, int], ...]` | `()` | `connected_network_count_by_sample` 的公开输入或数据字段。 |
| `geometric_connections` | `tuple[IntegrityRelationResult, ...]` | `()` | `geometric_connections` 的公开输入或数据字段。 |
| `containment_results` | `tuple[IntegrityRelationResult, ...]` | `()` | `containment_results` 的公开输入或数据字段。 |
| `mechanical_relation_results` | `tuple[IntegrityRelationResult, ...]` | `()` | `mechanical_relation_results` 的公开输入或数据字段。 |
| `checked_sample_count` | `int` | `0` | `checked_sample_count` 的公开输入或数据字段。 |
| `geometric_connection_tolerance_m` | `float` | `0.0` | `geometric_connection_tolerance_m`，单位 m，必须为有限值。 |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m`，单位 m，必须为有限值。 |
| `containment_escape_tolerance_m` | `float` | `0.0` | `containment_escape_tolerance_m`，单位 m，必须为有限值。 |
| `sampling_scope` | `Literal['initial', 'motion_result']` | `'initial'` | `sampling_scope` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |
| `operation` | `str` | `'check_assembly_integrity'` | `operation` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

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
