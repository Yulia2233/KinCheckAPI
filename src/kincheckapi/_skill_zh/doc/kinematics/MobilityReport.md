# `MobilityReport`

## API 定义

```python
@dataclass(frozen=True)
class MobilityReport:
    nominal_dofs: int
    effective_dofs: int
    joint_dofs: Mapping[str, int]
    constraint_rank: int
    constraint_ids: tuple[str, ...]
    singular_values: tuple[float, ...]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics import MobilityReport
```

## 用途

表示 `MobilityReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `nominal_dofs` | `int` | 必填 | `nominal_dofs` 的公开输入或数据字段。 |
| `effective_dofs` | `int` | 必填 | `effective_dofs` 的公开输入或数据字段。 |
| `joint_dofs` | `Mapping[str, int]` | 必填 | `joint_dofs` 的公开输入或数据字段。 |
| `constraint_rank` | `int` | 必填 | `constraint_rank` 的公开输入或数据字段。 |
| `constraint_ids` | `tuple[str, ...]` | `()` | 显式指定的 `constraint_ids` 集合。 |
| `singular_values` | `tuple[float, ...]` | `()` | `singular_values` 的公开输入或数据字段。 |
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
