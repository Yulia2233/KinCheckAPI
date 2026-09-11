# `normalize_position_bounds`

## API 定义

```python
normalize_position_bounds(value: Optional[Mapping[str, Sequence[float]]]) -> Mapping[str, tuple[float, float]]
```

源码：`src/kincheckapi/trajectory_checks.py`。

## 导入

```python
from kincheckapi.trajectory_checks import normalize_position_bounds
```

## 用途

把可选位置边界规范化为每轴 `(lower, upper)` 的只读 mapping，并拒绝无效边界。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `value` | `Optional[Mapping[str, Sequence[float]]]` | 必填 | `value` 的公开输入或数据字段。 |

## 返回与失败

返回 `Mapping[str, tuple[float, float]]`。

## 模块约束

- 时间窗必须落在实际采样范围内，并至少包含足够样本。
- 空窗口和不合法位置边界不得解释为通过。
- 路径长度和 bounds 都来自离散样本。

## 相关文档

- [`轨迹工具`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
