# `compose_pose`

## API 定义

```python
compose_pose(*, parent: Pose, child: Pose) -> Pose
```

源码：`src/kincheckapi/pose.py`。

## 导入

```python
from kincheckapi.pose import compose_pose
```

## 用途

把 parent 姿态与 parent 坐标系中的 child 姿态复合为世界姿态。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `parent` | `Pose` | 必填 | `parent` 的公开输入或数据字段。 |
| `child` | `Pose` | 必填 | `child` 的公开输入或数据字段。 |

## 返回与失败

返回 `Pose`。

## 模块约束

- 位置使用 m，四元数顺序固定为 xyzw。
- 输入向量和四元数必须有限；零范数四元数无效。
- 明确 parent、child、actual 和 expected 的参考坐标系。

## 相关文档

- [`姿态运算`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
