# `KinCheckError`

## API 定义

```python
class KinCheckError(Exception): ...

KinCheckError(*, code: 'str', message: 'str | None' = None, report: 'DiagnosticReport | ValidationResult | None' = None, object_ids: 'Sequence[str]' = (), source_paths: 'Sequence[str]' = (), suggested_actions: 'Sequence[str]' = (), details: 'Mapping[str, Any] | None' = None, operation: 'str | None' = None, status: 'str | None' = None, stage: 'str | None' = None) -> 'None'
```

源码：`src/kincheckapi/errors.py`。

## 导入

```python
from kincheckapi.errors import KinCheckError
```

## 用途

所有预期 KinCheckAPI 领域失败的公开基类。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `code` | `str` | 必填 | `code` 的公开输入或数据字段。 |
| `message` | `str | None` | `None` | `message` 的公开输入或数据字段。 |
| `report` | `DiagnosticReport | ValidationResult | None` | `None` | `report` 的公开输入或数据字段。 |
| `object_ids` | `Sequence[str]` | `()` | 显式指定的 `object_ids` 集合。 |
| `source_paths` | `Sequence[str]` | `()` | `source_paths` 的公开输入或数据字段。 |
| `suggested_actions` | `Sequence[str]` | `()` | `suggested_actions` 的公开输入或数据字段。 |
| `details` | `Optional[Mapping[str, Any]]` | `None` | `details` 的公开输入或数据字段。 |
| `operation` | `str | None` | `None` | `operation` 的公开输入或数据字段。 |
| `status` | `str | None` | `None` | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `stage` | `str | None` | `None` | `stage` 的公开输入或数据字段。 |

## 返回与失败

构造公开领域异常。捕获后读取 `code`、`report` 和结构化上下文，不匹配自由文本消息。

## 模块约束

- 捕获预期领域失败时优先捕获 `KinCheckError`，再按需要细分子类。
- 保留 `code`、`report`、`object_ids`、`source_paths` 和 `suggested_actions`。
- 不要通过匹配异常消息文本决定修复逻辑。

## 相关文档

- [`公开异常`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
