# `DiagnosticReport`

## API 定义

```python
@dataclass(frozen=True)
class DiagnosticReport:
    issues: tuple[SimIssue, ...]
    failure_time_s: float | None
    last_valid_result: Any
    backend_failure: BackendFailure | None
    metadata: Mapping[str, Any]
    operation: str
    status: Optional[Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']]
    traceback: str | None
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import DiagnosticReport
```

## 用途

表示 `DiagnosticReport` 的公开、可序列化数据结构。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `issues` | `tuple[SimIssue, ...]` | `()` | 结构化问题集合；保留错误码、对象和证据。 |
| `failure_time_s` | `float | None` | `None` | `failure_time_s`，单位 s，必须为有限值。 |
| `last_valid_result` | `Any` | `None` | `last_valid_result` 的公开输入或数据字段。 |
| `backend_failure` | `BackendFailure | None` | `None` | `backend_failure` 的公开输入或数据字段。 |
| `metadata` | `Mapping[str, Any]` | default_factory | 附加的只读结构化元数据。 |
| `operation` | `str` | `'diagnose'` | `operation` 的公开输入或数据字段。 |
| `status` | `Optional[Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']]` | `None` | 结构化状态；按对应结果类型允许的稳定值解释。 |
| `traceback` | `str | None` | `None` | `traceback` 的公开输入或数据字段。 |

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
