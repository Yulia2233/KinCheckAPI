# `solve_position_core`

## API 定义

```python
solve_position_core(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None, pose_targets: Sequence[PoseTarget] = (), options: PositionSolveOptions | None = None) -> tuple[str, typing.Mapping[str, float], typing.Mapping[str, Pose], tuple[ConstraintResidual, ...], tuple[SimIssue, ...]]
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics_geometry import solve_position_core
```

## 用途

求解指定运动学问题：`solve_position_core`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `pose_targets` | `Sequence[PoseTarget]` | `()` | `pose_targets` 的公开输入或数据字段。 |
| `options` | `PositionSolveOptions | None` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `tuple[str, Mapping[str, float], Mapping[str, Pose], tuple[ConstraintResidual, ...], tuple[SimIssue, ...]]`。

## 模块约束

- 这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。
- 输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。
- 以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。

## 相关文档

- [`低层运动学几何`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
