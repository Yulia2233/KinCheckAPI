# `Pose`

## API 定义

```python
@dataclass(frozen=True)
class Pose:
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
```

源码：`src/kincheckapi/pose.py`。

## 导入

```python
from kincheckapi.assembly import Pose
```

## 用途

表示 `Pose` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `position_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `position_m`，单位 m，必须为有限值。 |
| `orientation_xyzw` | `tuple[float, float, float, float]` | `(0.0, 0.0, 0.0, 1.0)` | `orientation_xyzw` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。
- ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。
- 构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。

## 相关文档

- [`装配模型与拓扑`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
