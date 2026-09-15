# `DriverTarget`

## API 定义

```python
@dataclass(frozen=True)
class DriverTarget:
    joint_id: str
    time_s: float
    mode: Literal['position', 'speed']
    target: float
    actual: float
    error: float
```

源码：`src/kincheckapi/result.py`。

## 导入

```python
from kincheckapi.result import DriverTarget
```

## 用途

表示 `DriverTarget` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `joint_id` | `str` | 必填 | 稳定且可解析的 joint ID。 |
| `time_s` | `float` | 必填 | 查询时间，单位 s，必须位于结果时间范围内。 |
| `mode` | `Literal['position', 'speed']` | 必填 | `mode` 的公开输入或数据字段。 |
| `target` | `float` | 必填 | `target` 的公开输入或数据字段。 |
| `actual` | `float` | 必填 | `actual` 的公开输入或数据字段。 |
| `error` | `float` | 必填 | `error` 的公开输入或数据字段。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

## 模块约束

- 只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。
- 查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。
- 先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。

## 相关文档

- [`结果模型与查询`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
