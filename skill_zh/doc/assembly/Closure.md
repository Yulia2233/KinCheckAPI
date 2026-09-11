# `Closure`

## API 定义

```python
@dataclass(frozen=True)
class Closure:
    closure_id: str
    constraint: Constraint
    position_tolerance_m: float
    orientation_tolerance_rad: float
```

源码：`src/kincheckapi/assembly.py`。

## 导入

```python
from kincheckapi.assembly import Closure
```

## 用途

表示 `Closure` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `closure_id` | `str` | 必填 | 稳定且可解析的 `closure_id`。 |
| `constraint` | `Constraint` | 必填 | `constraint` 的公开输入或数据字段。 |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m`，单位 m，必须为有限值。 |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad`，单位 rad，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
