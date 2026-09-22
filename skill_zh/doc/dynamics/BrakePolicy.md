# `BrakePolicy`

## API 定义

```python
@dataclass(frozen=True)
class BrakePolicy:
    policy_id: str
    trigger_time_s: float
    braking_limits: Mapping[str, float]
    delay_s: float
    hold_after_stop: bool
```

源码：`src/kincheckapi/dynamics_v07.py`。

## 导入

```python
from kincheckapi.dynamics import BrakePolicy
```

## 用途

表示 `BrakePolicy` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `policy_id` | `str` | 必填 | 稳定且可解析的 `policy_id`。 |
| `trigger_time_s` | `float` | 必填 | `trigger_time_s`，单位 s，必须为有限值。 |
| `braking_limits` | `Mapping[str, float]` | 必填 | `braking_limits` 的公开输入或数据字段。 |
| `delay_s` | `float` | `0.0` | `delay_s`，单位 s，必须为有限值。 |
| `hold_after_stop` | `bool` | `True` | `hold_after_stop` 的公开输入或数据字段。 |

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
