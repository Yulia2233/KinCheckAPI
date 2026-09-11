# `JacobianOptions`

## API 定义

```python
@dataclass(frozen=True)
class JacobianOptions:
    finite_difference_step: float
    rank_tolerance: float
```

源码：`src/kincheckapi/kinematics_geometry.py`。

## 导入

```python
from kincheckapi.kinematics_geometry import JacobianOptions
```

## 用途

表示 `JacobianOptions` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `finite_difference_step` | `float` | `1e-07` | `finite_difference_step` 的公开输入或数据字段。 |
| `rank_tolerance` | `float` | `1e-09` | `rank_tolerance` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。
- 输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。
- 以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。

## 相关文档

- [`低层运动学几何`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
