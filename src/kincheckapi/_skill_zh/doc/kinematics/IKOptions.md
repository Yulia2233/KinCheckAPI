# `IKOptions`

## API 定义

```python
@dataclass(frozen=True)
class IKOptions:
    position_tolerance_m: float
    orientation_tolerance_rad: float
    max_iterations: int
    damping: float
    step_tolerance: float
    residual_tolerance: float
    multi_start_count: int
    random_seed: int
    enforce_joint_limits: bool
    singular_value_tolerance: float
    finite_difference_step: float
    max_step_rad: float
    max_step_m: float
    solution_tolerance_rad: float
    solution_tolerance_m: float
    task_mode: Literal['pose', 'position']
```

源码：`src/kincheckapi/kinematics_ik.py`。

## 导入

```python
from kincheckapi.kinematics import IKOptions
```

## 用途

表示 `IKOptions` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m`，单位 m，必须为有限值。 |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad`，单位 rad，必须为有限值。 |
| `max_iterations` | `int` | `100` | `max_iterations` 的公开输入或数据字段。 |
| `damping` | `float` | `0.0001` | `damping` 的公开输入或数据字段。 |
| `step_tolerance` | `float` | `1e-09` | `step_tolerance` 的公开输入或数据字段。 |
| `residual_tolerance` | `float` | `1e-09` | `residual_tolerance` 的公开输入或数据字段。 |
| `multi_start_count` | `int` | `1` | `multi_start_count` 的公开输入或数据字段。 |
| `random_seed` | `int` | `0` | `random_seed` 的公开输入或数据字段。 |
| `enforce_joint_limits` | `bool` | `True` | `enforce_joint_limits` 的公开输入或数据字段。 |
| `singular_value_tolerance` | `float` | `1e-08` | `singular_value_tolerance` 的公开输入或数据字段。 |
| `finite_difference_step` | `float` | `1e-07` | `finite_difference_step` 的公开输入或数据字段。 |
| `max_step_rad` | `float` | `0.5` | `max_step_rad`，单位 rad，必须为有限值。 |
| `max_step_m` | `float` | `0.05` | `max_step_m`，单位 m，必须为有限值。 |
| `solution_tolerance_rad` | `float` | `1e-05` | `solution_tolerance_rad`，单位 rad，必须为有限值。 |
| `solution_tolerance_m` | `float` | `1e-07` | `solution_tolerance_m`，单位 m，必须为有限值。 |
| `task_mode` | `Literal['pose', 'position']` | `'pose'` | `task_mode` 的公开输入或数据字段。 |

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
