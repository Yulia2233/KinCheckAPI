# 求解失败诊断规则

1. 先区分输入、装配、场景、后端和检查阶段；不要把所有异常归为“模型不能动”。
2. 捕获结构化的 `KinCheckError` 子类，读取 code、message、object_ids、report 和 suggested_actions。
3. 求解失败时优先使用 `try_solve_motion()`，保存 `last_valid_result`、失败时间、残差和最后一帧。
4. `partial` 结果可以用于定位哪个 joint/closure 首先失效，但必须标记为未完成。
5. 直接打印公开错误或结果，或用 `diagnostics.explain_issue()`、`format_report_for_agent()` 解释失败；只有用户要求持久化时才调用 `write_report()`。
6. 如果根因在几何、装配关系或导出定义，修改 SimpleCADAPI 模型并重新导出；不要在 KinCheckAPI 验证程序中静默改写模型语义。
7. 保持原验收条件不变。只有用户改变机构要求时，才能同步修改验证程序中的阈值、范围或排除项。
