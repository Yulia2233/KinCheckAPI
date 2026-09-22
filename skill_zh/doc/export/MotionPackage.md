# `MotionPackage`

## API 定义

```python
@dataclass(frozen=True)
class MotionPackage:
    path: pathlib.Path
    manifest: Mapping[str, Any]
    assembly: AssemblyModel
    motion_result: MotionResult
    validation: Mapping[str, Any]
    mesh_members: Mapping[str, str]
    dynamics_model: kincheckapi.physics_types.DynamicsModel | None
    static_results: tuple[kincheckapi.physics_types.StaticResult, ...]
    static_checks: tuple[kincheckapi.physics_types.PhysicsReport, ...]
    dynamics_history: Any | None
```

源码：`src/kincheckapi/export.py`。

## 导入

```python
from kincheckapi.export import MotionPackage
```

## 用途

表示 `MotionPackage` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `path` | `pathlib.Path` | 必填 | 输入或输出文件路径；具体方向见用途说明。 |
| `manifest` | `Mapping[str, Any]` | 必填 | `manifest` 的公开输入或数据字段。 |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `motion_result` | `MotionResult` | 必填 | 待查询或检查的公开 `MotionResult`。 |
| `validation` | `Mapping[str, Any]` | 必填 | `validation` 的公开输入或数据字段。 |
| `mesh_members` | `Mapping[str, str]` | 必填 | `mesh_members` 的公开输入或数据字段。 |
| `dynamics_model` | `kincheckapi.physics_types.DynamicsModel | None` | `None` | `dynamics_model` 的公开输入或数据字段。 |
| `static_results` | `tuple[kincheckapi.physics_types.StaticResult, ...]` | `()` | `static_results` 的公开输入或数据字段。 |
| `static_checks` | `tuple[kincheckapi.physics_types.PhysicsReport, ...]` | `()` | `static_checks` 的公开输入或数据字段。 |
| `dynamics_history` | `Any | None` | `None` | `dynamics_history` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。
- 读取前验证 member path、schema、hash 和跨文件引用。
- `require_meshes=True` 时缺少任何必需 mesh 都应失败。

## 相关文档

- [`结果包`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
