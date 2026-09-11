# 公开异常

定义调用方可稳定捕获、序列化和报告的 KinCheckAPI 异常层级。

## 公开 API

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [`KinCheckError`](KinCheckError.md) | 类型 | 所有预期 KinCheckAPI 领域失败的公开基类。 |
| [`MJCFAdapterError`](MJCFAdapterError.md) | 类型 | CADIR MJCF、mapping 或资产无法转换为 AssemblyModel 时抛出的异常。 |
| [`AssemblyValidationError`](AssemblyValidationError.md) | 类型 | 装配模型或其引用无法满足结构契约时抛出的异常。 |
| [`ScenarioValidationError`](ScenarioValidationError.md) | 类型 | Scenario 的时间、状态、驱动或对象引用无效时抛出的异常。 |
| [`BackendUnavailableError`](BackendUnavailableError.md) | 类型 | 请求的计算后端无法加载时抛出的异常。 |
| [`BackendCapabilityError`](BackendCapabilityError.md) | 类型 | 后端无法表达调用方明确请求的能力时抛出的异常。 |
| [`MotionSolveError`](MotionSolveError.md) | 类型 | 运动求解开始后未能产生完整结果时抛出的异常；可包含失败时刻和最后有效结果。 |
| [`GeometryCheckError`](GeometryCheckError.md) | 类型 | 干涉、间隙或运动包络操作失败时抛出的异常。 |
| [`VerificationError`](VerificationError.md) | 类型 | 调用方明确要求某个结构化检查通过、但检查失败时抛出的异常。 |
| [`VisualizationExportError`](VisualizationExportError.md) | 类型 | 无法从公开装配和结果数据导出 viewer 时抛出的异常。 |
| [`MotionPackageError`](MotionPackageError.md) | 类型 | `.kincheck` 包无法安全写出、读取或验证时抛出的异常。 |

## 模块规则

- 捕获预期领域失败时优先捕获 `KinCheckError`，再按需要细分子类。
- 保留 `code`、`report`、`object_ids`、`source_paths` 和 `suggested_actions`。
- 不要通过匹配异常消息文本决定修复逻辑。
