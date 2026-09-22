# `ContactEvent`

## API 定义

```python
@dataclass(frozen=True)
class ContactEvent:
    time_s: float
    contact_id: str
    state: str
    normal_force_n: float
    tangential_force_n: tuple[float, float, float]
    penetration_m: float
    normal_impulse_ns: float
    normal: tuple[float, float, float]
    contact_point_m: tuple[float, float, float]
```

源码：`src/kincheckapi/dynamics_v07.py`。

## 导入

```python
from kincheckapi.dynamics import ContactEvent
```

## 用途

表示 `ContactEvent` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `contact_id` | `str` | 必填 | 稳定且可解析的 `contact_id`。 |
| `state` | `str` | 必填 | `state` 的公开输入或数据字段。 |
| `normal_force_n` | `float` | 必填 | `normal_force_n` 的公开输入或数据字段。 |
| `tangential_force_n` | `tuple[float, float, float]` | 必填 | `tangential_force_n` 的公开输入或数据字段。 |
| `penetration_m` | `float` | 必填 | `penetration_m`，单位 m，必须为有限值。 |
| `normal_impulse_ns` | `float` | `0.0` | `normal_impulse_ns` 的公开输入或数据字段。 |
| `normal` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | `normal` 的公开输入或数据字段。 |
| `contact_point_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `contact_point_m`，单位 m，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触容量 API 只检查给定外力；v0.7 刚体接触/冲量 API 必须保留接触状态、动量、能量和收敛证据。
- 结构网格、应力、结构振动和疲劳属于独立 FEACheckAPI；KinCheckAPI 只导出运动、刚体载荷、反力和冲量事实。

## 相关文档

- [`物性、静力与刚体动力学`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
