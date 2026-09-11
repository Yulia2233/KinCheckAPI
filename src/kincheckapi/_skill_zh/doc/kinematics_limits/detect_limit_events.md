# `detect_limit_events`

## API 定义

```python
detect_limit_events(*, assembly: AssemblyModel, joint_trajectories: Sequence[JointTrajectory], tolerance: float = 1e-09) -> tuple[LimitEvent, ...]
```

源码：`src/kincheckapi/kinematics_limits.py`。

## 导入

```python
from kincheckapi.kinematics_limits import detect_limit_events
```

## 用途

从实际关节轨迹中确定每个已建模限位侧首次 reached/exceeded 事件。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `joint_trajectories` | `Sequence[JointTrajectory]` | 必填 | `joint_trajectories` 的公开输入或数据字段。 |
| `tolerance` | `float` | `1e-09` | `tolerance` 的公开输入或数据字段。 |

## 返回与失败

返回 `tuple[LimitEvent, ...]`。

## 模块约束

- 事件检测消费实际关节轨迹和装配中已经 author 的限位。
- 缺少限位或缺少轨迹不会产生事件，也不能据此声称限位检查通过。
- tolerance 必须是有限非负值。

## 相关文档

- [`关节限位事件`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
