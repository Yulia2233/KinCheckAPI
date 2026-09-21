# `StressHistory`

## API 定义

```python
@dataclass(frozen=True)
class StressHistory:
    history_id: str
    times_s: tuple[float, ...]
    stress_pa: tuple[float, ...]
    unit: str
    region_id: str
    case_id: str
    coordinate_frame: str
```

源码：`src/kincheckapi/fatigue.py`。

## 导入

```python
from kincheckapi.dynamics import StressHistory
```

## 用途

表示 `StressHistory` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `history_id` | `str` | 必填 | 稳定且可解析的 `history_id`。 |
| `times_s` | `tuple[float, ...]` | 必填 | `times_s`，单位 s，必须为有限值。 |
| `stress_pa` | `tuple[float, ...]` | 必填 | `stress_pa` 的公开输入或数据字段。 |
| `unit` | `str` | `'Pa'` | `unit` 的公开输入或数据字段。 |
| `region_id` | `str` | `''` | 稳定且可解析的 `region_id`。 |
| `case_id` | `str` | `''` | 稳定且可解析的 `case_id`。 |
| `coordinate_frame` | `str` | `'material'` | `coordinate_frame` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触 API 只检查给定外力的法向、摩擦和压力容量，不提供接触响应或碰撞冲量。
- 结构、振动和疲劳 API 只对显式线性矩阵、声明材料、应力历程和 S-N 曲线给出可追溯参考结果；自动 BREP 网格、非线性接触、塑性/断裂及非线性振动返回能力边界。

## 相关文档

- [`动力学、结构、振动与疲劳`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
