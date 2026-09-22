# `RandomExcitation`

## API 定义

```python
@dataclass(frozen=True)
class RandomExcitation:
    excitation_id: str
    seed: int
    sample_rate_hz: float
    bandwidth_hz: float
    samples: tuple[float, ...]
    algorithm: str
    source: str
```

源码：`src/kincheckapi/dynamics_v07.py`。

## 导入

```python
from kincheckapi.dynamics import RandomExcitation
```

## 用途

表示 `RandomExcitation` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `excitation_id` | `str` | 必填 | 稳定且可解析的 `excitation_id`。 |
| `seed` | `int` | 必填 | `seed` 的公开输入或数据字段。 |
| `sample_rate_hz` | `float` | 必填 | `sample_rate_hz` 的公开输入或数据字段。 |
| `bandwidth_hz` | `float` | 必填 | `bandwidth_hz` 的公开输入或数据字段。 |
| `samples` | `tuple[float, ...]` | 必填 | `samples` 的公开输入或数据字段。 |
| `algorithm` | `str` | `'declared-samples'` | `algorithm` 的公开输入或数据字段。 |
| `source` | `str` | `'declared'` | `source` 的公开输入或数据字段。 |

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
