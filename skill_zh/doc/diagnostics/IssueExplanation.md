# `IssueExplanation`

## API 定义

```python
@dataclass(frozen=True)
class IssueExplanation:
    cause: str
    impact: str
    evidence: tuple[Evidence, ...]
    object_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    suggested_actions: tuple[str, ...]
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import IssueExplanation
```

## 用途

表示 `IssueExplanation` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `cause` | `str` | 必填 | `cause` 的公开输入或数据字段。 |
| `impact` | `str` | 必填 | `impact` 的公开输入或数据字段。 |
| `evidence` | `tuple[Evidence, ...]` | 必填 | 支持结论的机器可读证据。 |
| `object_ids` | `tuple[str, ...]` | 必填 | 显式指定的 `object_ids` 集合。 |
| `source_paths` | `tuple[str, ...]` | 必填 | `source_paths` 的公开输入或数据字段。 |
| `suggested_actions` | `tuple[str, ...]` | 必填 | `suggested_actions` 的公开输入或数据字段。 |

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
