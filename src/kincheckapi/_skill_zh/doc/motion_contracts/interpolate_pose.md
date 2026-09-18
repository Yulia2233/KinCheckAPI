# `interpolate_pose`

## API 定义

```python
interpolate_pose(*, first: Pose, second: Pose, fraction: float) -> Pose
```

源码：`src/kincheckapi/motion_contracts.py`。

## 导入

```python
from kincheckapi.motion_contracts import interpolate_pose
```

## 用途

执行公开操作 `interpolate_pose`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `first` | `Pose` | 必填 | `first` 的公开输入或数据字段。 |
| `second` | `Pose` | 必填 | `second` 的公开输入或数据字段。 |
| `fraction` | `float` | 必填 | `fraction` 的公开输入或数据字段。 |

## 返回与失败

返回 `Pose`。

## 模块约束

- Targets are immutable records; time values use seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.

## 相关文档

- [`运动工况契约`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
