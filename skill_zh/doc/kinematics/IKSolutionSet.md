# `IKSolutionSet`

## API 定义

```python
@dataclass(frozen=True)
class IKSolutionSet:
    status: Literal['solved', 'unreachable', 'nonconverged', 'singular', 'invalid', 'capability_failed']
    target: PoseTarget | None
    options: kincheckapi.kinematics_ik.IKOptions | None
    solutions: tuple[kincheckapi.kinematics_ik.IKSolution, ...]
    selected_solution: kincheckapi.kinematics_ik.IKSolution | None
    attempts: tuple[kincheckapi.kinematics_ik.IKSolution, ...]
    issues: tuple[SimIssue, ...]
    metadata: Mapping[str, Any]
```

源码：`src/kincheckapi/kinematics_ik.py`。

## 导入

```python
from kincheckapi.kinematics import IKSolutionSet
```

## 用途

表示 `IKSolutionSet` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `status` | `Literal['solved', 'unreachable', 'nonconverged', 'singular', 'invalid', 'capability_failed']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `target` | `PoseTarget | None` | `None` | `target` 的公开输入或数据字段。 |
| `options` | `kincheckapi.kinematics_ik.IKOptions | None` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |
| `solutions` | `tuple[kincheckapi.kinematics_ik.IKSolution, ...]` | `()` | `solutions` 的公开输入或数据字段。 |
| `selected_solution` | `kincheckapi.kinematics_ik.IKSolution | None` | `None` | `selected_solution` 的公开输入或数据字段。 |
| `attempts` | `tuple[kincheckapi.kinematics_ik.IKSolution, ...]` | `()` | `attempts` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |

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
