# `apply_scenario_fix`

## API 定义

```python
apply_scenario_fix(*, scenario: Any, fix: Fix) -> Any
```

源码：`src/kincheckapi/diagnostics.py`。

## 导入

```python
from kincheckapi.diagnostics import apply_scenario_fix
```

## 用途

保留的自动修复入口；v0.5.0 尚未实现，调用会抛出 `BackendCapabilityError`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `scenario` | `Any` | 必填 | 已绑定装配定义的不可变 `Scenario`。 |
| `fix` | `Fix` | 必填 | `fix` 的公开输入或数据字段。 |

## 返回与失败

返回 `Any`。

结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。

## 模块约束

- 优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。
- 自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。
- 后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。
- 当前总是以 `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED` 拒绝执行。

## 相关文档

- [`结构化诊断`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
