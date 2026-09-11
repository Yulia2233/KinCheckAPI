# `create_assembly`

## API 定义

```python
create_assembly(*, assembly_id: str) -> AssemblyModel
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import create_assembly
```

## 用途

创建公开对象：`create_assembly`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly_id` | `str` | 必填 | 稳定且可解析的 `assembly_id`。 |

## 返回与失败

返回 `AssemblyModel`。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
