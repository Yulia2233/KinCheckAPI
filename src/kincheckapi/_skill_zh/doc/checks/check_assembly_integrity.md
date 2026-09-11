# `check_assembly_integrity`

## API 定义

```python
check_assembly_integrity(*, assembly: AssemblyModel, motion_result: MotionResult | None = None, asset_root: str | pathlib.Path | None = None, component_ids: Optional[Sequence[str]] = None, geometric_connection_pairs: Optional[Sequence[Sequence[str]]] = None, containment_relations: Sequence[ContainmentRelation] = (), mechanical_relation_ids: Optional[Sequence[str]] = None, geometric_connection_tolerance_m: float = 0.0001, penetration_tolerance_m: float = 0.0, containment_escape_tolerance_m: float = 0.0001, sampling_scope: Literal['initial', 'motion_result'] = 'motion_result', require_single_network: bool = True) -> AssemblyIntegrityReport
```

源码：`src/kincheckapi/integrity.py`。

## 导入

```python
from kincheckapi.checks import check_assembly_integrity
```

## 用途

在静态或 MotionResult 的每个采样状态检查 Component 是否仍属于一个完整连接网络，并报告断开、脱离和越界。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult | None` | `None` | 待查询或检查的公开 `MotionResult`。 |
| `asset_root` | `str | pathlib.Path | None` | `None` | mesh 等资产允许解析的根目录。 |
| `component_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `component_ids` 集合。 |
| `geometric_connection_pairs` | `Optional[Sequence[Sequence[str]]]` | `None` | `geometric_connection_pairs` 的公开输入或数据字段。 |
| `containment_relations` | `Sequence[ContainmentRelation]` | `()` | `containment_relations` 的公开输入或数据字段。 |
| `mechanical_relation_ids` | `Optional[Sequence[str]]` | `None` | 显式指定的 `mechanical_relation_ids` 集合。 |
| `geometric_connection_tolerance_m` | `float` | `0.0001` | `geometric_connection_tolerance_m`，单位 m，必须为有限值。 |
| `penetration_tolerance_m` | `float` | `0.0` | `penetration_tolerance_m`，单位 m，必须为有限值。 |
| `containment_escape_tolerance_m` | `float` | `0.0001` | `containment_escape_tolerance_m`，单位 m，必须为有限值。 |
| `sampling_scope` | `Literal['initial', 'motion_result']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |
| `require_single_network` | `bool` | `True` | `require_single_network` 的公开输入或数据字段。 |

## 返回与失败

返回 `AssemblyIntegrityReport`。

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
