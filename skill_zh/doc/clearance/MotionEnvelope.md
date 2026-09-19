# `MotionEnvelope`

## API 定义

```python
@dataclass(frozen=True)
class MotionEnvelope:
    component_id: str
    world_min_position_m: tuple[float, float, float]
    world_max_position_m: tuple[float, float, float]
    sample_times_s: tuple[float, ...]
    mesh_vertex_count: int
    mesh_path: str
    mesh_sha256: str | None
    mesh_triangle_count: int | None
    sample_bounds: tuple[EnvelopeSample, ...]
    backend_id: str
    sampling_scope: Literal['motion_result', 'solver_steps']
```

源码：`src/kincheckapi/clearance_result.py`。

## 导入

```python
from kincheckapi.clearance import MotionEnvelope
```

## 用途

表示 `MotionEnvelope` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `component_id` | `str` | 必填 | 稳定且可解析的 component ID。 |
| `world_min_position_m` | `tuple[float, float, float]` | 必填 | `world_min_position_m`，单位 m，必须为有限值。 |
| `world_max_position_m` | `tuple[float, float, float]` | 必填 | `world_max_position_m`，单位 m，必须为有限值。 |
| `sample_times_s` | `tuple[float, ...]` | 必填 | 严格递增的实际采样时间，单位 s。 |
| `mesh_vertex_count` | `int` | 必填 | `mesh_vertex_count` 的公开输入或数据字段。 |
| `mesh_path` | `str` | 必填 | `mesh_path` 的公开输入或数据字段。 |
| `mesh_sha256` | `str | None` | `None` | `mesh_sha256` 的公开输入或数据字段。 |
| `mesh_triangle_count` | `int | None` | `None` | `mesh_triangle_count` 的公开输入或数据字段。 |
| `sample_bounds` | `tuple[EnvelopeSample, ...]` | `()` | `sample_bounds` 的公开输入或数据字段。 |
| `backend_id` | `str` | `'python-fcl'` | 稳定且可解析的 `backend_id`。 |
| `sampling_scope` | `Literal['motion_result', 'solver_steps']` | `'motion_result'` | `sampling_scope` 的公开输入或数据字段。 |

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
