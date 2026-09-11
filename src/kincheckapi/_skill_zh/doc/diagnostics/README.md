# 结构化诊断

收集、解释和持久化稳定的错误码、证据与失败上下文。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`AgentGuidance`](AgentGuidance.md) | 类型 | 表示 `AgentGuidance` 的公开、可序列化数据结构。 |
| [`AgentReadableResult`](AgentReadableResult.md) | 类型 | 表示 `AgentReadableResult` 的公开、可序列化数据结构。 |
| [`BackendFailure`](BackendFailure.md) | 类型 | 表示 `BackendFailure` 的公开、可序列化数据结构。 |
| [`DiagnosticReport`](DiagnosticReport.md) | 类型 | 表示 `DiagnosticReport` 的公开、可序列化数据结构。 |
| [`Evidence`](Evidence.md) | 类型 | 表示 `Evidence` 的公开、可序列化数据结构。 |
| [`Fix`](Fix.md) | 类型 | 表示 `Fix` 的公开、可序列化数据结构。 |
| [`IssueExplanation`](IssueExplanation.md) | 类型 | 表示 `IssueExplanation` 的公开、可序列化数据结构。 |
| [`Severity`](Severity.md) | 类型别名 | 定义 `Severity` 使用的公开类型约定。 |
| [`SimIssue`](SimIssue.md) | 类型 | 表示 `SimIssue` 的公开、可序列化数据结构。 |
| [`ValidationResult`](ValidationResult.md) | 类型 | 表示 `ValidationResult` 的公开、可序列化数据结构。 |
| [`apply_assembly_fix`](apply_assembly_fix.md) | 函数 | 保留的自动修复入口；v0.5.0 尚未实现，调用会抛出 `BackendCapabilityError`。 |
| [`apply_scenario_fix`](apply_scenario_fix.md) | 函数 | 保留的自动修复入口；v0.5.0 尚未实现，调用会抛出 `BackendCapabilityError`。 |
| [`assert_check_passed`](assert_check_passed.md) | 函数 | 要求结构化检查已经通过；失败时抛出保留原检查对象的 `VerificationError`。 |
| [`collect_issues`](collect_issues.md) | 函数 | 从多个结构化结果对象中收集并按内容去重 `SimIssue`。 |
| [`create_backend_failure_report`](create_backend_failure_report.md) | 函数 | 把未知后端异常和可选 partial 结果清洗成稳定的 `DiagnosticReport`。 |
| [`create_report`](create_report.md) | 函数 | 合并装配、Scenario、运动、几何安全和检查结果中的 issues，形成统一 `DiagnosticReport`。 |
| [`explain_issue`](explain_issue.md) | 函数 | 把一个稳定 `SimIssue` 展开为 cause、impact、evidence 和建议动作。 |
| [`format_report_for_agent`](format_report_for_agent.md) | 函数 | 兼容名称；委托给唯一的 Agent 结果渲染器，不接受样式参数。 |
| [`format_result_for_agent`](format_result_for_agent.md) | 函数 | 格式化任意公开验证结果；不接受样式参数。 |
| [`format_error_for_agent`](format_error_for_agent.md) | 函数 | 格式化结构化对象：`format_error_for_agent`。 |
| [`list_executable_fixes`](list_executable_fixes.md) | 函数 | 返回当前诊断报告中可由公开 API 安全执行的 Fix；v0.5.0 当前总是返回空元组。 |
| [`write_report`](write_report.md) | 函数 | 把完整 `DiagnosticReport` 确定性写为 JSON。 |

## 模块规则

- 优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。
- 自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。
- 后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。
