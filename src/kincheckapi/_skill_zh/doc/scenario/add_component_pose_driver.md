# `add_component_pose_driver`

## API 定义

```python
add_component_pose_driver(*, scenario: Scenario, target: kincheckapi.motion_contracts.PoseTrajectory) -> Scenario
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import add_component_pose_driver
```

## 用途

添加并返回更新后的不可变对象：`add_component_pose_driver`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | 必填 | 已绑定装配定义的不可变 `Scenario`。 |
| `target` | `kincheckapi.motion_contracts.PoseTrajectory` | 必填 | `target` 的公开输入或数据字段。 |

## 返回与失败

返回 `Scenario`。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
