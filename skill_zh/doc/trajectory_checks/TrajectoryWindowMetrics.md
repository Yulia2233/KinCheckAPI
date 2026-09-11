# `TrajectoryWindowMetrics`

## API 定义

```python
@dataclass(frozen=True)
class TrajectoryWindowMetrics:
    indices: tuple[int, ...]
    path_length_m: float
    bounds_m: Mapping[str, tuple[float, float]]
```

源码：`src/kincheckapi/trajectory_checks.py`。

## 导入

```python
from kincheckapi.trajectory_checks import TrajectoryWindowMetrics
```

## 用途

表示 `TrajectoryWindowMetrics` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `indices` | `tuple[int, ...]` | 必填 | `indices` 的公开输入或数据字段。 |
| `path_length_m` | `float` | 必填 | `path_length_m`，单位 m，必须为有限值。 |
| `bounds_m` | `Mapping[str, tuple[float, float]]` | 必填 | `bounds_m`，单位 m，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 时间窗必须落在实际采样范围内，并至少包含足够样本。
- 空窗口和不合法位置边界不得解释为通过。
- 路径长度和 bounds 都来自离散样本。

## 相关文档

- [`轨迹工具`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
