# `EnvelopeSample`

## API 定义

```python
@dataclass(frozen=True)
class EnvelopeSample:
    time_s: float
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]
```

源码：`src/kincheckapi/clearance_result.py`。

## 导入

```python
from kincheckapi.clearance import EnvelopeSample
```

## 用途

表示 `EnvelopeSample` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `world_min_position_m` | `tuple[float, float, float]` | 必填 | `world_min_position_m`，单位 m，必须为有限值。 |
| `world_max_position_m` | `tuple[float, float, float]` | 必填 | `world_max_position_m`，单位 m，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
