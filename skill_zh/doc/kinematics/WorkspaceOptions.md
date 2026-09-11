# `WorkspaceOptions`

## API 定义

```python
@dataclass(frozen=True)
class WorkspaceOptions:
    joint_ranges: Mapping[str, Sequence[float]]
    samples_per_joint: int
    max_samples: int
    seed: int | None
    position_tolerance_m: float
    orientation_tolerance_rad: float
    singularity_tolerance: float
    near_singularity_tolerance: float
```

源码：`src/kincheckapi/kinematics_analysis.py`。

## 导入

```python
from kincheckapi.kinematics import WorkspaceOptions
```

## 用途

表示 `WorkspaceOptions` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `joint_ranges` | `Mapping[str, Sequence[float]]` | default_factory | `joint_ranges` 的公开输入或数据字段。 |
| `samples_per_joint` | `int` | `9` | `samples_per_joint` 的公开输入或数据字段。 |
| `max_samples` | `int` | `4096` | `max_samples` 的公开输入或数据字段。 |
| `seed` | `int | None` | `None` | `seed` 的公开输入或数据字段。 |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m`，单位 m，必须为有限值。 |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad`，单位 rad，必须为有限值。 |
| `singularity_tolerance` | `float` | `1e-08` | `singularity_tolerance` 的公开输入或数据字段。 |
| `near_singularity_tolerance` | `float` | `0.0001` | `near_singularity_tolerance` 的公开输入或数据字段。 |

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
