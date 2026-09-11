# `AgentGuidance`

## API 定义

```python
@dataclass(frozen=True)
class AgentGuidance:
    operation: str
    what_happened: str | None
    possible_causes: tuple[str, ...]
    how_to_fix: tuple[str, ...]
    documentation_hint: str | None
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import AgentGuidance
```

## 用途

表示 `AgentGuidance` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `operation` | `str` | 必填 | `operation` 的公开输入或数据字段。 |
| `what_happened` | `str | None` | `None` | `what_happened` 的公开输入或数据字段。 |
| `possible_causes` | `tuple[str, ...]` | `()` | `possible_causes` 的公开输入或数据字段。 |
| `how_to_fix` | `tuple[str, ...]` | `()` | `how_to_fix` 的公开输入或数据字段。 |
| `documentation_hint` | `str | None` | `None` | `documentation_hint` 的公开输入或数据字段。 |

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
