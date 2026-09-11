# `Scenario`

## API 定义

```python
@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    assembly: AssemblyModel
    assembly_id: str
    initial_joint_positions: tuple[JointValue, ...]
    initial_joint_velocities: tuple[JointValue, ...]
    joint_home_positions: tuple[JointValue, ...]
    locked_joints: tuple[JointLock, ...]
    disabled_constraint_ids: tuple[str, ...]
    position_drivers: tuple[PositionDriver, ...]
    speed_drivers: tuple[SpeedDriver, ...]
    duration_s: float | None
    sample_period_s: float | None
    joint_result_requests: tuple[JointResultRequest, ...]
    component_result_requests: tuple[ComponentResultRequest, ...]
    component_result_scope: ComponentResultScope | str
    capture_integration_steps: bool
    integration_component_ids: tuple[str, ...] | None
```

源码：`src/kincheckapi/scenario.py`。

## 导入

```python
from kincheckapi.scenario import Scenario
```

## 用途

表示 `Scenario` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario_id` | `str` | 必填 | 稳定且可解析的 `scenario_id`。 |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `assembly_id` | `str` | `''` | 稳定且可解析的 `assembly_id`。 |
| `initial_joint_positions` | `tuple[JointValue, ...]` | `()` | `initial_joint_positions` 的公开输入或数据字段。 |
| `initial_joint_velocities` | `tuple[JointValue, ...]` | `()` | `initial_joint_velocities` 的公开输入或数据字段。 |
| `joint_home_positions` | `tuple[JointValue, ...]` | `()` | `joint_home_positions` 的公开输入或数据字段。 |
| `locked_joints` | `tuple[JointLock, ...]` | `()` | `locked_joints` 的公开输入或数据字段。 |
| `disabled_constraint_ids` | `tuple[str, ...]` | `()` | 显式指定的 `disabled_constraint_ids` 集合。 |
| `position_drivers` | `tuple[PositionDriver, ...]` | `()` | `position_drivers` 的公开输入或数据字段。 |
| `speed_drivers` | `tuple[SpeedDriver, ...]` | `()` | `speed_drivers` 的公开输入或数据字段。 |
| `duration_s` | `float | None` | `None` | 运行总时长，单位 s，必须为有限正数。 |
| `sample_period_s` | `float | None` | `None` | `sample_period_s`，单位 s，必须为有限值。 |
| `joint_result_requests` | `tuple[JointResultRequest, ...]` | `()` | `joint_result_requests` 的公开输入或数据字段。 |
| `component_result_requests` | `tuple[ComponentResultRequest, ...]` | `()` | `component_result_requests` 的公开输入或数据字段。 |
| `component_result_scope` | `ComponentResultScope | str` | `<ComponentResultScope.REQUESTED: 'requested'>` | `component_result_scope` 的公开输入或数据字段。 |
| `capture_integration_steps` | `bool` | `False` | `capture_integration_steps` 的公开输入或数据字段。 |
| `integration_component_ids` | `tuple[str, ...] | None` | `None` | 显式指定的 `integration_component_ids` 集合。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- Scenario 不可变；所有设置函数都返回新对象。
- 转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。
- 求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。

## 相关文档

- [`Scenario 与驱动`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
