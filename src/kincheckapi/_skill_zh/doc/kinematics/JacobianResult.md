# `JacobianResult`

## API 定义

```python
@dataclass(frozen=True)
class JacobianResult:
    target_component_id: str
    target_connector_id: str | None
    joint_ids: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    rank: int
    singular_values: tuple[float, ...]
    condition_number: float | None
    units: tuple[str, ...]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics import JacobianResult
```

## 用途

表示 `JacobianResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `target_component_id` | `str` | 必填 | 作为几何或运动学目标的 component ID。 |
| `target_connector_id` | `str | None` | 必填 | 可选目标 connector ID；省略时目标为组件坐标系。 |
| `joint_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `joint_ids` 集合。 |
| `matrix` | `tuple[tuple[float, ...], ...]` | 必填 | `matrix` 的公开输入或数据字段。 |
| `rank` | `int` | 必填 | `rank` 的公开输入或数据字段。 |
| `singular_values` | `tuple[float, ...]` | 必填 | `singular_values` 的公开输入或数据字段。 |
| `condition_number` | `float | None` | 必填 | `condition_number` 的公开输入或数据字段。 |
| `units` | `tuple[str, ...]` | `('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)')` | `units` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
