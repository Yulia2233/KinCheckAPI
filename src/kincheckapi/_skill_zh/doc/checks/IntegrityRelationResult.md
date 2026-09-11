# `IntegrityRelationResult`

## API 定义

```python
@dataclass(frozen=True)
class IntegrityRelationResult:
    relation_id: str
    relation_type: Literal['mechanical', 'geometric', 'containment']
    component_a_id: str
    component_b_id: str
    time_s: float
    passed: bool
    measurement_m: float | None
    tolerance_m: float | None
    reason: str | None
```

源码：`src/kincheckapi/integrity.py`。

## 导入

```python
from kincheckapi.checks import IntegrityRelationResult
```

## 用途

表示 `IntegrityRelationResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `relation_id` | `str` | 必填 | 稳定且可解析的 `relation_id`。 |
| `relation_type` | `Literal['mechanical', 'geometric', 'containment']` | 必填 | `relation_type` 的公开输入或数据字段。 |
| `component_a_id` | `str` | 必填 | 稳定且可解析的 `component_a_id`。 |
| `component_b_id` | `str` | 必填 | 稳定且可解析的 `component_b_id`。 |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `passed` | `bool` | 必填 | 结构化布尔结论；必须与 issues 和实际证据一起读取。 |
| `measurement_m` | `float | None` | `None` | `measurement_m`，单位 m，必须为有限值。 |
| `tolerance_m` | `float | None` | `None` | `tolerance_m`，单位 m，必须为有限值。 |
| `reason` | `str | None` | `None` | `reason` 的公开输入或数据字段。 |

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
