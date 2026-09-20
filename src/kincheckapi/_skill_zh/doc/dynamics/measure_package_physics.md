# `measure_package_physics`

## API 定义

```python
measure_package_physics(*, package_path: str | pathlib.Path, sdk_python: str | pathlib.Path | None = None) -> kincheckapi.physics_types.PhysicsManifest
```

源码：`src/kincheckapi/physics_cadir.py`。

## 导入

```python
from kincheckapi.dynamics import measure_package_physics
```

## 用途

执行公开操作 `measure_package_physics`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | 必填 | `package_path` 的公开输入或数据字段。 |
| `sdk_python` | `str | pathlib.Path | None` | `None` | `sdk_python` 的公开输入或数据字段。 |

## 返回与失败

返回 `PhysicsManifest`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
