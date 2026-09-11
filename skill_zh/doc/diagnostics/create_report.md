# `create_report`

## API 定义

```python
create_report(*, assembly: Any, scenario: Any = None, motion_result: Any = None, clearance_result: Any = None, check_results: Iterable[Any] = ()) -> DiagnosticReport
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import create_report
```

## 用途

合并装配、Scenario、运动、几何安全和检查结果中的 issues，形成统一 `DiagnosticReport`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `assembly` | `Any` | 必填 | 待构造、校验、求解或导出的 `AssemblyModel`。 |
| `scenario` | `Any` | `None` | 已绑定装配定义的不可变 `Scenario`。 |
| `motion_result` | `Any` | `None` | 待查询或检查的公开 `MotionResult`。 |
| `clearance_result` | `Any` | `None` | `clearance_result` 的公开输入或数据字段。 |
| `check_results` | `Iterable[Any]` | `()` | `check_results` 的公开输入或数据字段。 |

## 返回与失败

返回 `DiagnosticReport`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。
- 自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。
- 后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。

## 相关文档

- [`结构化诊断`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
