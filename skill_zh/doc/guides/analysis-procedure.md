# 运动学分析步骤

当用户问“自由度是多少”“哪里会奇异”“目标位置能否到达”时，不要直接跑一段任意动态轨迹。

1. 先完成 `validate_assembly()` 和 `validate_topology()`。
2. 用 `analyze_dofs()` 得到结构化自由度证据。
3. 对指定关节姿态用 `solve_position()`，对闭环用 `validate_closures()`。
4. 对已有完整 `MotionResult` 使用 `find_singularities()`、`check_reachability()`、`compute_workspace()` 或 `trace_connector_path()`。
5. 报告分析采样、参考坐标系、步长和阈值；分析结果不是动力学或强度结论。
