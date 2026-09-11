# `limit_events_in_window`

## API 定义

```python
limit_events_in_window(*, events: Sequence[LimitEvent], joint_ids: Optional[Sequence[str]], start_time_s: float | None, end_time_s: float | None) -> tuple[LimitEvent, ...]
```

源码：`src/kincheckapi/trajectory_checks.py`。

## 导入

```python
from kincheckapi.trajectory_checks import limit_events_in_window
```

## 用途

按 joint ID 和时间窗筛选已经记录的 `LimitEvent`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `events` | `Sequence[LimitEvent]` | 必填 | `events` 的公开输入或数据字段。 |
| `joint_ids` | `Optional[Sequence[str]]` | 必填 | 显式指定的 `joint_ids` 集合。 |
| `start_time_s` | `float | None` | 必填 | 时间窗起点，单位 s。 |
| `end_time_s` | `float | None` | 必填 | 时间窗终点，单位 s。 |

## 返回与失败

返回 `tuple[LimitEvent, ...]`。

## 模块约束

- 时间窗必须落在实际采样范围内，并至少包含足够样本。
- 空窗口和不合法位置边界不得解释为通过。
- 路径长度和 bounds 都来自离散样本。

## 相关文档

- [`轨迹工具`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
