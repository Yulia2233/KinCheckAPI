# 姿态运算

执行 SI 单位、xyzw 四元数约定下的刚体姿态运算。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`Pose`](Pose.md) | 类型 | 表示 `Pose` 的公开、可序列化数据结构。 |
| [`Quaternion`](Quaternion.md) | 类型别名 | 定义 `Quaternion` 使用的公开类型约定。 |
| [`Vector3`](Vector3.md) | 类型别名 | 定义 `Vector3` 使用的公开类型约定。 |
| [`compose_pose`](compose_pose.md) | 函数 | 把 parent 姿态与 parent 坐标系中的 child 姿态复合为世界姿态。 |
| [`inverse_pose`](inverse_pose.md) | 函数 | 返回逆刚体变换。 |
| [`orientation_error_rad`](orientation_error_rad.md) | 函数 | 计算两个方向之间最短的无符号角误差，单位 rad。 |
| [`relative_pose`](relative_pose.md) | 函数 | 返回 child 在 parent 坐标系中的相对姿态。 |
| [`rotate_vector`](rotate_vector.md) | 函数 | 仅使用姿态方向旋转向量，不应用平移。 |
| [`transform_point`](transform_point.md) | 函数 | 把局部点通过姿态变换到父坐标系。 |

## 模块规则

- 位置使用 m，四元数顺序固定为 xyzw。
- 输入向量和四元数必须有限；零范数四元数无效。
- 明确 parent、child、actual 和 expected 的参考坐标系。
