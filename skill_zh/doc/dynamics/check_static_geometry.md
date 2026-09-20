# `check_static_geometry`

## API 定义

```python
check_static_geometry(*, package_path: str | pathlib.Path, manifest: kincheckapi.physics_types.PhysicsManifest, occurrence_components: Mapping[str, str], component_initial_poses: Mapping[str, Pose], component_poses: Mapping[str, Pose], contacts: Sequence[kincheckapi.physics_geometry.ContactRegion] = (), free_clearance_m: float = 0.0001, guard_clearance_m: float = 0.005, guard_occurrence_ids: Sequence[str] = (), query_error_m: float = 1e-09) -> kincheckapi.physics_types.PhysicsReport
```

源码：`src/kincheckapi/physics_geometry.py`。

## 导入

```python
from kincheckapi.dynamics import check_static_geometry
```

## 用途

执行结构化检查：`check_static_geometry`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | 必填 | `package_path` 的公开输入或数据字段。 |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest` | 必填 | `manifest` 的公开输入或数据字段。 |
| `occurrence_components` | `Mapping[str, str]` | 必填 | `occurrence_components` 的公开输入或数据字段。 |
| `component_initial_poses` | `Mapping[str, Pose]` | 必填 | `component_initial_poses` 的公开输入或数据字段。 |
| `component_poses` | `Mapping[str, Pose]` | 必填 | `component_poses` 的公开输入或数据字段。 |
| `contacts` | `Sequence[kincheckapi.physics_geometry.ContactRegion]` | `()` | `contacts` 的公开输入或数据字段。 |
| `free_clearance_m` | `float` | `0.0001` | `free_clearance_m`，单位 m，必须为有限值。 |
| `guard_clearance_m` | `float` | `0.005` | `guard_clearance_m`，单位 m，必须为有限值。 |
| `guard_occurrence_ids` | `Sequence[str]` | `()` | 显式指定的 `guard_occurrence_ids` 集合。 |
| `query_error_m` | `float` | `1e-09` | `query_error_m`，单位 m，必须为有限值。 |

## 返回与失败

返回 `PhysicsReport`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
