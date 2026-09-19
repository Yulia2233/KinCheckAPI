# `IKSolution`

## API 定义

```python
@dataclass(frozen=True)
class IKSolution:
    joint_positions: Mapping[str, float]
    initial_joint_positions: Mapping[str, float]
    position_error_m: float
    orientation_error_rad: float
    residual_norm: float
    iterations: int
    seed_index: int
    status: Literal['converged', 'limit_hit', 'singular', 'stalled', 'iteration_limit']
    within_limits: bool
    jacobian_rank: int
    reference_rank: int
    singular_values: tuple[float, ...]
    residuals: tuple[ConstraintResidual, ...]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics_ik.py`。

## 导入

```python
from kincheckapi.kinematics import IKSolution
```

## 用途

表示 `IKSolution` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `joint_positions` | `Mapping[str, float]` | 必填 | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `initial_joint_positions` | `Mapping[str, float]` | 必填 | `initial_joint_positions` 的公开输入或数据字段。 |
| `position_error_m` | `float` | 必填 | `position_error_m`，单位 m，必须为有限值。 |
| `orientation_error_rad` | `float` | 必填 | `orientation_error_rad`，单位 rad，必须为有限值。 |
| `residual_norm` | `float` | 必填 | `residual_norm` 的公开输入或数据字段。 |
| `iterations` | `int` | 必填 | `iterations` 的公开输入或数据字段。 |
| `seed_index` | `int` | 必填 | `seed_index` 的公开输入或数据字段。 |
| `status` | `Literal['converged', 'limit_hit', 'singular', 'stalled', 'iteration_limit']` | 必填 | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `within_limits` | `bool` | 必填 | `within_limits` 的公开输入或数据字段。 |
| `jacobian_rank` | `int` | 必填 | `jacobian_rank` 的公开输入或数据字段。 |
| `reference_rank` | `int` | 必填 | `reference_rank` 的公开输入或数据字段。 |
| `singular_values` | `tuple[float, ...]` | `()` | `singular_values` 的公开输入或数据字段。 |
| `residuals` | `tuple[ConstraintResidual, ...]` | `()` | `residuals` 的公开输入或数据字段。 |
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
