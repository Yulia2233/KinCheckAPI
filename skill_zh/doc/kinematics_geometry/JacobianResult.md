# `JacobianResult`

## API 定义

```python
@dataclass(frozen=True)
class JacobianResult:
    target_component_id: str
    target_connector_id: str | None
    joint_ids: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    rank: int
    singular_values: tuple[float, ...]
    condition_number: float | None
    units: tuple[str, ...]
    issues: tuple[SimIssue, ...]
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics_geometry import JacobianResult
```

## 用途

表示 `JacobianResult` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `target_component_id` | `str` | 必填 | 作为几何或运动学目标的 component ID。 |
| `target_connector_id` | `str | None` | 必填 | 可选目标 connector ID；省略时目标为组件坐标系。 |
| `joint_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `joint_ids` 集合。 |
| `matrix` | `tuple[tuple[float, ...], ...]` | 必填 | `matrix` 的公开输入或数据字段。 |
| `rank` | `int` | 必填 | `rank` 的公开输入或数据字段。 |
| `singular_values` | `tuple[float, ...]` | 必填 | `singular_values` 的公开输入或数据字段。 |
| `condition_number` | `float | None` | 必填 | `condition_number` 的公开输入或数据字段。 |
| `units` | `tuple[str, ...]` | `('m/(rad|m)', 'm/(rad|m)', 'm/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)', 'rad/(rad|m)')` | `units` 的公开输入或数据字段。 |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。
- 输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。
- 以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。

## 相关文档

- [`低层运动学几何`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
