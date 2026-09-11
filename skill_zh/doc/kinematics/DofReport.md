# `DofReport`

## API 定义

```python
@dataclass(frozen=True)
class DofReport:
    total_dofs: int
    joint_dofs: Mapping[str, int]
    component_dofs: Mapping[str, int]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics.py`。

## 导入

```python
from kincheckapi.kinematics import DofReport
```

## 用途

表示 `DofReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `total_dofs` | `int` | 必填 | `total_dofs` 的公开输入或数据字段。 |
| `joint_dofs` | `Mapping[str, int]` | 必填 | `joint_dofs` 的公开输入或数据字段。 |
| `component_dofs` | `Mapping[str, int]` | 必填 | `component_dofs` 的公开输入或数据字段。 |
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
