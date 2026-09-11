# `compute_jacobian`

## API 定义

```python
compute_jacobian(*, assembly: AssemblyModel, joint_positions: Mapping[str, float], target_component_id: str | None = None, target_connector_id: str | None = None, options: JacobianOptions | None = None) -> JacobianResult
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics_geometry import compute_jacobian
```

## 用途

对指定组件或 connector 在给定 joint positions 下计算后端无关的六维有限差分 Jacobian。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `joint_positions` | `Mapping[str, float]` | 必填 | 按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。 |
| `target_component_id` | `str | None` | `None` | 作为几何或运动学目标的 component ID。 |
| `target_connector_id` | `str | None` | `None` | 可选目标 connector ID；省略时目标为组件坐标系。 |
| `options` | `JacobianOptions | None` | `None` | 对应求解或分析的公开配置对象；记录实际阈值。 |

## 返回与失败

返回 `JacobianResult`。

## 模块约束

- 这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。
- 输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。
- 以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。

## 相关文档

- [`低层运动学几何`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
