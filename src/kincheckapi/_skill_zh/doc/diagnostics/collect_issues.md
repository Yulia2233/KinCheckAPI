# `collect_issues`

## API 定义

```python
collect_issues(*, results: Iterable[Any]) -> tuple[SimIssue, ...]
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import collect_issues
```

## 用途

从多个结构化结果对象中收集并按内容去重 `SimIssue`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `results` | `Iterable[Any]` | 必填 | `results` 的公开输入或数据字段。 |

## 返回与失败

返回 `tuple[SimIssue, ...]`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。
- 自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。
- 后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。

## 相关文档

- [`结构化诊断`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
