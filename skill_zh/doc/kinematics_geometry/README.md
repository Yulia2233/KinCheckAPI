# 低层运动学几何

提供后端无关的姿态传播、Jacobian、mobility 和位置求解原语。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`JacobianOptions`](JacobianOptions.md) | 类型 | 表示 `JacobianOptions` 的公开、可序列化数据结构。 |
| [`JacobianResult`](JacobianResult.md) | 类型 | 表示 `JacobianResult` 的公开、可序列化数据结构。 |
| [`MobilityReport`](MobilityReport.md) | 类型 | 表示 `MobilityReport` 的公开、可序列化数据结构。 |
| [`PoseTarget`](PoseTarget.md) | 类型 | 表示 `PoseTarget` 的公开、可序列化数据结构。 |
| [`PositionSolveOptions`](PositionSolveOptions.md) | 类型 | 表示 `PositionSolveOptions` 的公开、可序列化数据结构。 |
| [`analyze_mobility`](analyze_mobility.md) | 函数 | 根据名义关节自由度和约束 Jacobian 秩分析机构的有效自由度。 |
| [`compute_jacobian`](compute_jacobian.md) | 函数 | 对指定组件或 connector 在给定 joint positions 下计算后端无关的六维有限差分 Jacobian。 |
| [`forward_component_poses`](forward_component_poses.md) | 函数 | 根据装配树和 joint positions 传播全部组件的世界姿态。 |
| [`forward_connector_poses`](forward_connector_poses.md) | 函数 | 根据装配树和 joint positions 传播全部 connector 的世界姿态。 |
| [`solve_position_core`](solve_position_core.md) | 函数 | 求解指定运动学问题：`solve_position_core`。 |

## 模块规则

- 这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。
- 输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。
- 以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。
