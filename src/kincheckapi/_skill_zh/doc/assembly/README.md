# 装配模型与拓扑

定义不可变装配对象，构造零件和组件关系，并校验运动拓扑。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`AssemblyModel`](AssemblyModel.md) | 类型 | 表示 `AssemblyModel` 的公开、可序列化数据结构。 |
| [`Closure`](Closure.md) | 类型 | 表示 `Closure` 的公开、可序列化数据结构。 |
| [`Component`](Component.md) | 类型 | 表示 `Component` 的公开、可序列化数据结构。 |
| [`Connector`](Connector.md) | 类型 | 表示 `Connector` 的公开、可序列化数据结构。 |
| [`ConnectorRef`](ConnectorRef.md) | 类型 | 表示 `ConnectorRef` 的公开、可序列化数据结构。 |
| [`Constraint`](Constraint.md) | 类型 | 表示 `Constraint` 的公开、可序列化数据结构。 |
| [`Coupling`](Coupling.md) | 类型 | 表示 `Coupling` 的公开、可序列化数据结构。 |
| [`CouplingType`](CouplingType.md) | 枚举 | 定义 `CouplingType` 接受的稳定枚举值。 |
| [`Ground`](Ground.md) | 类型 | 表示 `Ground` 的公开、可序列化数据结构。 |
| [`Joint`](Joint.md) | 类型 | 表示 `Joint` 的公开、可序列化数据结构。 |
| [`JointLimit`](JointLimit.md) | 类型 | 表示 `JointLimit` 的公开、可序列化数据结构。 |
| [`JointType`](JointType.md) | 枚举 | 定义 `JointType` 接受的稳定枚举值。 |
| [`KinematicEdge`](KinematicEdge.md) | 类型 | 表示 `KinematicEdge` 的公开、可序列化数据结构。 |
| [`KinematicTree`](KinematicTree.md) | 类型 | 表示 `KinematicTree` 的公开、可序列化数据结构。 |
| [`Limit`](Limit.md) | 类型别名 | 定义 `Limit` 使用的公开类型约定。 |
| [`Part`](Part.md) | 类型 | 表示 `Part` 的公开、可序列化数据结构。 |
| [`Pose`](Pose.md) | 类型 | 表示 `Pose` 的公开、可序列化数据结构。 |
| [`add_closure_constraint`](add_closure_constraint.md) | 函数 | 添加并返回更新后的不可变对象：`add_closure_constraint`。 |
| [`add_component`](add_component.md) | 函数 | 添加并返回更新后的不可变对象：`add_component`。 |
| [`add_constraint`](add_constraint.md) | 函数 | 添加并返回更新后的不可变对象：`add_constraint`。 |
| [`add_coupling`](add_coupling.md) | 函数 | 添加并返回更新后的不可变对象：`add_coupling`。 |
| [`add_joint`](add_joint.md) | 函数 | 添加并返回更新后的不可变对象：`add_joint`。 |
| [`add_part`](add_part.md) | 函数 | 添加并返回更新后的不可变对象：`add_part`。 |
| [`assembly_from_dict`](assembly_from_dict.md) | 函数 | 从已经解析的 mapping 重建 AssemblyModel；之后仍需执行装配与拓扑校验。 |
| [`assembly_to_dict`](assembly_to_dict.md) | 函数 | 把 AssemblyModel 转换为 JSON 兼容的确定性字典。 |
| [`create_assembly`](create_assembly.md) | 函数 | 创建公开对象：`create_assembly`。 |
| [`build_kinematic_tree`](build_kinematic_tree.md) | 函数 | 分析固定刚体组、运动树边、闭环边、ground 和断开岛；它是拓扑分析结果，不是运动求解结果。 |
| [`exclude_collision_pair`](exclude_collision_pair.md) | 函数 | 把一对不同的已存在组件加入碰撞排除表；该调用会改变后续几何验收范围。 |
| [`ground_component`](ground_component.md) | 函数 | 把一个已存在的组件标记为装配参考系中的固定组件，并返回新装配对象。 |
| [`read_assembly`](read_assembly.md) | 函数 | 读取并重建公开对象：`read_assembly`。 |
| [`set_joint_limits`](set_joint_limits.md) | 函数 | 设置字段并返回更新后的不可变对象：`set_joint_limits`。 |
| [`validate_assembly`](validate_assembly.md) | 函数 | 聚合检查装配 ID、引用、端点、ground、joint、constraint、closure 和 coupling 的一致性。 |
| [`validate_topology`](validate_topology.md) | 函数 | 验证运动图边界、连通性、ground、树边和闭环边是否满足求解前置条件。 |
| [`write_assembly`](write_assembly.md) | 函数 | 把公开对象确定性写出：`write_assembly`。 |

## 模块规则

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。
