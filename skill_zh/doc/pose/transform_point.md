# `transform_point`

## API 定义

```python
transform_point(*, pose: Pose, point_m: Sequence[float]) -> tuple[float, float, float]
```

源码：`src/kincheckapi/pose.py`。

## 导入

```python
from kincheckapi.pose import transform_point
```

## 用途

把局部点通过姿态变换到父坐标系。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `pose` | `Pose` | 必填 | `pose` 的公开输入或数据字段。 |
| `point_m` | `Sequence[float]` | 必填 | `point_m`，单位 m，必须为有限值。 |

## 返回与失败

返回 `Vector3`。

## 模块约束

- 位置使用 m，四元数顺序固定为 xyzw。
- 输入向量和四元数必须有限；零范数四元数无效。
- 明确 parent、child、actual 和 expected 的参考坐标系。

## 相关文档

- [`姿态运算`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
