# `SingularityOptions`

## API 定义

```python
@dataclass(frozen=True)
class SingularityOptions:
    tolerance: float
    near_tolerance: float
    target_component_id: str | None
    target_connector_id: str | None
```

源码：`src/kincheckapi/kinematics_analysis.py`。

## 导入

```python
from kincheckapi.kinematics import SingularityOptions
```

## 用途

表示 `SingularityOptions` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `tolerance` | `float` | `1e-08` | `tolerance` 的公开输入或数据字段。 |
| `near_tolerance` | `float` | `0.0001` | `near_tolerance` 的公开输入或数据字段。 |
| `target_component_id` | `str | None` | `None` | 作为几何或运动学目标的 component ID。 |
| `target_connector_id` | `str | None` | `None` | 可选目标 connector ID；省略时目标为组件坐标系。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 先验证装配和 Scenario，再求解或分析。
- `partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。
- 位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。

## 相关文档

- [`运动学求解与分析`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
