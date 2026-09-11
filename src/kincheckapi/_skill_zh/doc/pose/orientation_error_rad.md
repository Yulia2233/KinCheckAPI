# `orientation_error_rad`

## API 定义

```python
orientation_error_rad(*, actual: Pose, expected: Pose) -> float
```

源码：`src/kincheckapi/pose.py`。

## 导入

```python
from kincheckapi.pose import orientation_error_rad
```

## 用途

计算两个方向之间最短的无符号角误差，单位 rad。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `actual` | `Pose` | 必填 | `actual` 的公开输入或数据字段。 |
| `expected` | `Pose` | 必填 | `expected` 的公开输入或数据字段。 |

## 返回与失败

返回 `float`。

## 模块约束

- 位置使用 m，四元数顺序固定为 xyzw。
- 输入向量和四元数必须有限；零范数四元数无效。
- 明确 parent、child、actual 和 expected 的参考坐标系。

## 相关文档

- [`姿态运算`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
