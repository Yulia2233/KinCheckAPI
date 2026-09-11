# `MinimumClearance`

## API 定义

```python
@dataclass(frozen=True)
class MinimumClearance:
    component_a_id: str
    component_b_id: str
    minimum_clearance_m: float
    time_s: float
    closest_point_a_m: tuple[float, float, float] | None
    closest_point_b_m: tuple[float, float, float] | None
    backend_id: str
    sampling_scope: Literal['motion_result', 'solver_steps']
```

源码：`src/kincheckapi/clearance_result.py`。

## 导入

```python
from kincheckapi.clearance import MinimumClearance
```

## 用途

表示 `MinimumClearance` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `component_a_id` | `str` | 必填 | 稳定且可解析的 `component_a_id`。 |
| `component_b_id` | `str` | 必填 | 稳定且可解析的 `component_b_id`。 |
| `minimum_clearance_m` | `float` | 必填 | `minimum_clearance_m`，单位 m，必须为有限值。 |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `closest_point_a_m` | `tuple[float, float, float] | None` | `None` | `closest_point_a_m`，单位 m，必须为有限值。 |
| `closest_point_b_m` | `tuple[float, float, float] | None` | `None` | `closest_point_b_m`，单位 m，必须为有限值。 |
| `backend_id` | `str` | `'python-fcl'` | 稳定且可解析的 `backend_id`。 |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 显式给出组件对或组件范围、`asset_root`、时间窗和容差。
- 结果来自三角网格和离散时间采样，不是连续时间无碰撞证明。
- 空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。

## 相关文档

- [`几何安全`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
