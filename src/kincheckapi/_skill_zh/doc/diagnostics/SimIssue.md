# `SimIssue`

## API 定义

```python
@dataclass(frozen=True)
class SimIssue:
    code: str
    severity: Literal['info', 'warning', 'error']
    stage: str
    message: str
    object_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    suggested_actions: tuple[str, ...]
    failure_time_s: float | None
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import SimIssue
```

## 用途

表示 `SimIssue` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `code` | `str` | 必填 | `code` 的公开输入或数据字段。 |
| `severity` | `Literal['info', 'warning', 'error']` | 必填 | `severity` 的公开输入或数据字段。 |
| `stage` | `str` | 必填 | `stage` 的公开输入或数据字段。 |
| `message` | `str` | 必填 | `message` 的公开输入或数据字段。 |
| `object_ids` | `tuple[str, ...]` | `()` | 显式指定的 `object_ids` 集合。 |
| `source_paths` | `tuple[str, ...]` | `()` | `source_paths` 的公开输入或数据字段。 |
| `evidence` | `tuple[Evidence, ...]` | `()` | 支持结论的机器可读证据。 |
| `suggested_actions` | `tuple[str, ...]` | `()` | `suggested_actions` 的公开输入或数据字段。 |
| `failure_time_s` | `float | None` | `None` | `failure_time_s`，单位 s，必须为有限值。 |

## 返回与失败

构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。
- 自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。
- 后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。

## 相关文档

- [`结构化诊断`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
