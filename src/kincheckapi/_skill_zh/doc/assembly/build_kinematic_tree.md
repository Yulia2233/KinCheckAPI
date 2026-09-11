# `build_kinematic_tree`

## API 定义

```python
build_kinematic_tree(*, assembly: AssemblyModel) -> KinematicTree
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import build_kinematic_tree
```

## 用途

分析固定刚体组、运动树边、闭环边、ground 和断开岛；它是拓扑分析结果，不是运动求解结果。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |

## 返回与失败

返回 `KinematicTree`。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
