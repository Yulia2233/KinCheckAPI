# `BackendUnavailableError`

## API 定义

```python
class BackendUnavailableError(KinCheckError): ...

BackendUnavailableError(*, backend_failure: 'BackendFailure | None' = None, **kwargs: 'Any') -> 'None'
```

源码：`src/kincheckapi/errors.py`。

## 导入

```python
from kincheckapi.errors import BackendUnavailableError
```

## 用途

请求的计算后端无法加载时抛出的异常。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `backend_failure` | `BackendFailure | None` | `None` | `backend_failure` 的公开输入或数据字段。 |
| `kwargs` | `Any` | 必填 | `kwargs` 的公开输入或数据字段。 |

## 返回与失败

构造公开领域异常。捕获后读取 `code`、`report` 和结构化上下文，不匹配自由文本消息。

## 模块约束

- 捕获预期领域失败时优先捕获 `KinCheckError`，再按需要细分子类。
- 保留 `code`、`report`、`object_ids`、`source_paths` 和 `suggested_actions`。
- 不要通过匹配异常消息文本决定修复逻辑。

## 相关文档

- [`公开异常`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
