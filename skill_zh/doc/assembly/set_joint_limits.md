# `set_joint_limits`

## API 定义

```python
set_joint_limits(*, assembly: AssemblyModel, joint_id: str, lower: float, upper: float) -> AssemblyModel
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import set_joint_limits
```

## 用途

设置字段并返回更新后的不可变对象：`set_joint_limits`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `lower` | `float` | 必填 | `lower` 的公开输入或数据字段。 |
| `upper` | `float` | 必填 | `upper` 的公开输入或数据字段。 |

## 返回与失败

返回 `AssemblyModel`。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
