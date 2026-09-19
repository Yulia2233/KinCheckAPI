#!/usr/bin/env python3
"""Generate the Chinese skill API reference from the public runtime surface."""

from __future__ import annotations

import argparse
import dataclasses
import enum
import importlib
import inspect
import sys
import types
import typing
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


MODULES: dict[str, dict[str, Any]] = {
    "cadir": {
        "title": "CADIR 输入转换",
        "summary": "读取 CADIR 导出的 MJCF、mapping 和 mesh，构造可验证的装配模型。",
        "exports": ("AdapterResult", "convert_mjcf"),
    },
    "assembly": {
        "title": "装配模型与拓扑",
        "summary": "定义不可变装配对象，构造零件和组件关系，并校验运动拓扑。",
    },
    "scenario": {
        "title": "Scenario 与驱动",
        "summary": "定义初态、驱动、运行时间、采样和结果记录范围。",
    },
    "motion_contracts": {
        "title": "运动工况契约",
        "summary": "定义路径、位姿、周期和多轴协调目标；不伪造未实现的 6D 求解能力。",
    },
    "kinematics": {
        "title": "运动学求解与分析",
        "summary": "执行位置和连续运动求解，并分析自由度、Jacobian、奇异性和工作空间。",
    },
    "checks": {
        "title": "验收检查",
        "summary": "把用户命题转换成结构化、可复核的运动学检查。",
        "exports": ("CheckReport", "CheckSpec", "CheckSuiteReport", "DriverTrackingReport", "CheckType", "Direction", "RatioMeasurement", "AssemblyIntegrityReport", "ContainmentRelation", "IntegrityRelationResult", "check_assembly_integrity", "check_constraint_equation_residuals", "check_constraint_residuals", "check_driver_tracking", "check_joint_limits", "check_interference", "check_minimum_clearance", "check_motion_envelope", "check_pose_target", "check_pose_trajectory", "check_path_tracking", "check_planar_tracking", "check_start_stop_reversal", "check_periodic_motion", "check_synchronization", "check_continuous_interference", "check_trajectory", "check_transmission_ratio", "run_checks"),
    },
    "clearance": {
        "title": "几何安全",
        "summary": "在离散运动样本上检查网格干涉、最小间隙和运动包络。",
    },
    "continuous_result": {
        "title": "连续碰撞证据",
        "summary": "定义跨轨迹样本区间的保守连续干涉选项、接触事件和可审计报告。",
        "exports": ("ContinuousInterferenceOptions", "ContinuousContactEvent", "ContinuousInterferenceReport"),
    },
    "result": {
        "title": "结果模型与查询",
        "summary": "读取 MotionResult 中的状态、轨迹、残差和事件证据。",
    },
    "diagnostics": {
        "title": "结构化诊断",
        "summary": "收集、解释和持久化稳定的错误码、证据与失败上下文。",
    },
    "errors": {
        "title": "公开异常",
        "summary": "定义调用方可稳定捕获、序列化和报告的 KinCheckAPI 异常层级。",
    },
    "export": {
        "title": "结果包",
        "summary": "写出、校验和读取后端无关的 .kincheck 运动结果包。",
    },
    "pose": {
        "title": "姿态运算",
        "summary": "执行 SI 单位、xyzw 四元数约定下的刚体姿态运算。",
    },
    "trajectory_checks": {
        "title": "轨迹工具",
        "summary": "计算轨迹时间窗指标并筛选限位事件。",
    },
    "visualization": {
        "title": "离线可视化",
        "summary": "把公开运动结果和 mesh 导出为离线 Three.js viewer。",
    },
    "kinematics_conventions": {
        "title": "运动学坐标约定",
        "summary": "定义 authored connector 顺序与运动树传播方向之间的稳定符号约定。",
    },
    "kinematics_geometry": {
        "title": "低层运动学几何",
        "summary": "提供后端无关的姿态传播、Jacobian、mobility 和位置求解原语。",
        "exports": (
            "JacobianOptions",
            "JacobianResult",
            "MobilityReport",
            "PoseTarget",
            "PositionSolveOptions",
            "analyze_mobility",
            "compute_jacobian",
            "forward_component_poses",
            "forward_connector_poses",
            "solve_position_core",
        ),
    },
    "kinematics_limits": {
        "title": "关节限位事件",
        "summary": "从装配限位和关节轨迹中确定首次到达或超限事件。",
    },
    "dynamics": {
        "title": "动力学命名空间",
        "summary": "保留的动力学命名空间；v0.5.0 没有公开动力学操作。",
        "exports": (),
    },
}


MODULE_RULES = {
    "motion_contracts": (
        "Targets are immutable records; time values use seconds and positions use metres.",
        "PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.",
        "Path and periodic contracts require explicit finite ranges and never imply continuous-time guarantees.",
    ),
    "cadir": (
        "XML 根 `model` 必须非空并等于 mapping 的 `root_definition_id`。",
        "XML、mapping 和 mesh 必须来自同一导出批次；资产解析不得越过 `asset_root`。",
        "转换返回装配模型和 source map；转换成功不替代装配、拓扑与 Scenario 校验。",
    ),
    "assembly": (
        "数据模型不可变；所有 `add_*`、`set_*` 和 `ground_*` 调用都必须接住返回值。",
        "ID 必须稳定且唯一，所有 part、component、joint、connector 和 constraint 引用必须可解析。",
        "构造完成后先运行 `validate_assembly()` 和 `validate_topology()`，再进入求解。",
    ),
    "scenario": (
        "Scenario 不可变；所有设置函数都返回新对象。",
        "转动量使用 rad/rad/s，平移量使用 m/m/s，时间使用 s；输入必须有限。",
        "求解前运行 `validate_scenario()`；冲突驱动、无效时间窗或未知 ID 不得继续。",
    ),
    "kinematics": (
        "先验证装配和 Scenario，再求解或分析。",
        "`partial`、`capability_failed`、空样本和未收敛结果只可用于诊断，不能判为通过。",
        "位置、方向、秩和采样阈值必须显式记录，分析结果不代表动力学或强度结论。",
    ),
    "checks": (
        "检查必须对应明确的对象、时间窗、期望值、阈值和单位。",
        "检查对象为空、证据为空或 MotionResult 不完整时不得通过。",
        "`CheckReport.passed` 是最终布尔结论；同时保留 evidence、issues 和 metadata。",
        "装配体整体性检查支持任意数量的 Component；`component_ids=None` 检查整个装配体。",
        "机械、容纳/导向和几何连接共同形成连接图；几何连接必须记录米制容差。",
    ),
    "clearance": (
        "显式给出组件对或组件范围、`asset_root`、时间窗和容差。",
        "普通干涉、最小间隙和包络结果来自离散采样；跨样本连续证明必须显式调用 `check_continuous_interference()`。",
        "空 pair、空样本、缺失 mesh 或 partial 运动结果不得解释为安全通过。",
    ),
    "continuous_result": (
        "连续通过只表示声明的位姿插值和速度上界下已取得完整保守证据；不能外推到未记录的非刚体或动力学运动。",
        "`failed` 记录接触或间隙违规；`indeterminate` 表示预算、时间轴或几何证据不足，不能当作通过。",
        "事件中的最早接触时间是上界，`certainty`、查询次数、细分次数和 options 必须随报告保存。",
    ),
    "result": (
        "只读取 MotionResult 中实际记录的对象和样本，不从空结果推断通过。",
        "查询时间必须在结果时间范围内；插值后的证据应保留原始采样范围。",
        "先检查 `status`、样本数和 issues，再使用轨迹、残差或事件。",
    ),
    "diagnostics": (
        "优先使用稳定错误码、对象 ID、source path 和 Evidence，不依赖自由文本匹配。",
        "自动修复只允许执行公开 API 明确定义且前置条件可验证的 Fix。",
        "后端异常应包装为 BackendFailure，不暴露或依赖私有后端对象。",
    ),
    "errors": (
        "捕获预期领域失败时优先捕获 `KinCheckError`，再按需要细分子类。",
        "保留 `code`、`report`、`object_ids`、`source_paths` 和 `suggested_actions`。",
        "不要通过匹配异常消息文本决定修复逻辑。",
    ),
    "export": (
        "只导出已经完成并审阅的 MotionResult；结果包不是 CADIR 编辑源。",
        "读取前验证 member path、schema、hash 和跨文件引用。",
        "`require_meshes=True` 时缺少任何必需 mesh 都应失败。",
    ),
    "pose": (
        "位置使用 m，四元数顺序固定为 xyzw。",
        "输入向量和四元数必须有限；零范数四元数无效。",
        "明确 parent、child、actual 和 expected 的参考坐标系。",
    ),
    "trajectory_checks": (
        "时间窗必须落在实际采样范围内，并至少包含足够样本。",
        "空窗口和不合法位置边界不得解释为通过。",
        "路径长度和 bounds 都来自离散样本。",
    ),
    "visualization": (
        "可视化只消费公开 AssemblyModel 和 MotionResult，不读取私有后端状态。",
        "导出前检查运动状态、实际轨迹和 mesh 资产。",
        "viewer 用于复核证据，不替代数值验收检查。",
    ),
    "kinematics_conventions": (
        "公开 joint 标量方向始终按 `component_b - component_a` 解释。",
        "树传播方向可能与 authored connector 顺序相反，必须通过该模块换算符号。",
        "不能根据组件名称或树遍历顺序猜测正负方向。",
    ),
    "kinematics_geometry": (
        "这是低层、后端无关的几何原语；一般任务优先使用 `kincheckapi.kinematics` 的高层入口。",
        "输入姿态、joint positions、步长和容差必须有限并使用 SI 单位。",
        "以下划线开头的历史 `__all__` 条目仍视为内部实现，不纳入 skill 公共契约。",
    ),
    "kinematics_limits": (
        "事件检测消费实际关节轨迹和装配中已经 author 的限位。",
        "缺少限位或缺少轨迹不会产生事件，也不能据此声称限位检查通过。",
        "tolerance 必须是有限非负值。",
    ),
    "dynamics": (
        "当前版本不得调用或虚构动力学 API。",
        "运动学结果不能支持力、力矩、接触力、冲击、疲劳或振动结论。",
        "遇到动力学需求时明确报告超出当前能力范围。",
    ),
}


PURPOSE_OVERRIDES = {
    "convert_mjcf": "把 CADIR MJCF XML、mapping JSON 和 mesh 资产转换为 `AdapterResult`。规范的 `mesh_constraints` 将 gear/belt 的端点坐标和 SI 半径保留为已有原生 Constraint，支持行星架参考系下的多坐标方程；显式同轴关节别名保留在 source map 中。原有两关节 Coupling 转换继续支持，可选产品包准备入口位于 `kincheckapi.addon`。",
    "build_kinematic_tree": "分析固定刚体组、运动树边、闭环边、ground 和断开岛；它是拓扑分析结果，不是运动求解结果。",
    "validate_assembly": "聚合检查装配 ID、引用、端点、ground、joint、constraint、closure 和 coupling 的一致性。",
    "validate_topology": "验证运动图边界、连通性、ground、树边和闭环边是否满足求解前置条件。",
    "solve_motion": "沿 Scenario 时间窗执行连续运动学求解，返回后端无关的 `MotionResult`。",
    "try_solve_motion": "在失败时保留结构化报告和 `last_valid_result`；不会把失败转换成通过。",
    "run_checks": "按 `CheckSpec` 顺序执行显式验收命题，返回 `CheckSuiteReport`。",
    "check_interference": "检查离散运动样本中的指定组件对是否发生网格穿透。",
    "check_continuous_interference": "在声明的分段刚体位姿插值下，跨相邻轨迹样本保守地检查显式组件对，并返回 TOI 区间证据。",
    "measure_minimum_clearance": "测量离散运动样本中指定组件对的最小带符号间隙。",
    "create_motion_envelope": "为明确组件生成离散运动包络，供后续空间干涉分析。",
    "write_motion_result": "将完整公开运动结果写为确定性的 JSON。",
    "export_motion_package": "把装配、运动结果、校验信息和可选 mesh 写入一个 `.kincheck` 文件。",
    "motion_package": "`export_motion_package()` 的公开兼容别名。",
    "export_motion_viewer": "导出可离线打开的 Three.js 运动回放资产。",
    "verify_transmission_ratio": "弃用的兼容入口；新代码使用 `kincheckapi.checks.check_transmission_ratio()`。",
    "check_envelope_interference": "比较两个运动包络报告的世界轴对齐包围盒是否重叠。它不会执行三角网格干涉，也不会确认穿透。",
    "set_component_result_scope": "选择组件轨迹记录范围。`all` 始终记录全部组件；`requested` 在请求列表非空时仅记录所请求对象，在空列表时保留历史兼容行为并记录全部组件。",
    "list_executable_fixes": "返回当前诊断报告中可由公开 API 安全执行的 Fix；v0.5.0 当前总是返回空元组。",
    "apply_assembly_fix": "保留的自动修复入口；v0.5.0 尚未实现，调用会抛出 `BackendCapabilityError`。",
    "apply_scenario_fix": "保留的自动修复入口；v0.5.0 尚未实现，调用会抛出 `BackendCapabilityError`。",
    "compute_jacobian": "对指定组件或 connector 在给定 joint positions 下计算后端无关的六维有限差分 Jacobian。",
    "analyze_mobility": "根据名义关节自由度和约束 Jacobian 秩分析机构的有效自由度。",
    "detect_limit_events": "从实际关节轨迹中确定每个已建模限位侧首次 reached/exceeded 事件。",
    "child_motion_sign": "把公开 joint 坐标转换成当前运动树 child group 的运动符号。",
    "assert_check_passed": "要求结构化检查已经通过；失败时抛出保留原检查对象的 `VerificationError`。",
    "collect_issues": "从多个结构化结果对象中收集并按内容去重 `SimIssue`。",
    "create_report": "合并装配、Scenario、运动、几何安全和检查结果中的 issues，形成统一 `DiagnosticReport`。",
    "create_backend_failure_report": "把未知后端异常和可选 partial 结果清洗成稳定的 `DiagnosticReport`。",
    "explain_issue": "把一个稳定 `SimIssue` 展开为 cause、impact、evidence 和建议动作。",
    "format_report_for_agent": "兼容名称；委托给唯一的 Agent 结果渲染器，不接受样式参数。",
    "format_result_for_agent": "格式化任意公开验证结果；不接受样式参数。",
    "write_report": "把完整 `DiagnosticReport` 确定性写为 JSON。",
    "compose_pose": "把 parent 姿态与 parent 坐标系中的 child 姿态复合为世界姿态。",
    "inverse_pose": "返回逆刚体变换。",
    "relative_pose": "返回 child 在 parent 坐标系中的相对姿态。",
    "rotate_vector": "仅使用姿态方向旋转向量，不应用平移。",
    "transform_point": "把局部点通过姿态变换到父坐标系。",
    "orientation_error_rad": "计算两个方向之间最短的无符号角误差，单位 rad。",
    "trajectory_window_metrics": "在明确时间窗内计算单条组件或 connector 轨迹的样本索引、路径长度和世界坐标 bounds。",
    "normalize_position_bounds": "把可选位置边界规范化为每轴 `(lower, upper)` 的只读 mapping，并拒绝无效边界。",
    "limit_events_in_window": "按 joint ID 和时间窗筛选已经记录的 `LimitEvent`。",
    "read_joint_state": "在指定时间读取或插值一个 joint 的位置、速度和加速度状态。",
    "read_component_pose": "在指定时间读取或插值一个组件的世界姿态。",
    "read_component_state": "读取组件世界姿态以及结果中可用的线/角速度和加速度。",
    "read_connector_state": "读取指定 connector 的世界姿态和可用空间运动状态。",
    "read_trajectory": "返回结果中已经记录的组件或 connector 完整轨迹。",
    "summarize_motion": "汇总状态、时长、样本数、joint extrema、最大残差和事件计数。",
    "validate_package": "校验 `.kincheck` 的成员路径、schema、hash 和跨文件引用，返回聚合验证结果。",
    "read_package": "严格校验后读取并重建 `.kincheck` 包；失败时抛出 `MotionPackageError`。",
    "ground_component": "把一个已存在的组件标记为装配参考系中的固定组件，并返回新装配对象。",
    "exclude_collision_pair": "把一对不同的已存在组件加入碰撞排除表；该调用会改变后续几何验收范围。",
    "assembly_to_dict": "把 AssemblyModel 转换为 JSON 兼容的确定性字典。",
    "assembly_from_dict": "从已经解析的 mapping 重建 AssemblyModel；之后仍需执行装配与拓扑校验。",
    "scenario_to_dict": "把 Scenario 转换为 JSON 兼容的确定性字典。",
    "scenario_from_dict": "从已经解析的 mapping 重建与指定 AssemblyModel 绑定的 Scenario；严格校验需另行执行。",
    "lock_joint": "在 Scenario 中锁定指定 joint，可选给出锁定位置；这会改变待验证工况。",
    "disable_constraint": "在 Scenario 中按稳定 ID 禁用约束；只用于明确的诊断或对照工况。",
    "check_assembly_integrity": "在静态或 MotionResult 的每个采样状态检查 Component 是否仍属于一个完整连接网络，并报告断开、脱离和越界。",
    "forward_component_poses": "根据装配树和 joint positions 传播全部组件的世界姿态。",
    "forward_connector_poses": "根据装配树和 joint positions 传播全部 connector 的世界姿态。",
    "find_singularities": "在 MotionResult 的实际采样上计算 Jacobian 秩、最小奇异值和条件数，报告 singular/near-singular 样本。",
    "trace_connector_path": "从已记录 connector 轨迹计算时间序列、路径长度、起终点和世界坐标 bounds。",
    "KinCheckError": "所有预期 KinCheckAPI 领域失败的公开基类。",
    "MJCFAdapterError": "CADIR MJCF、mapping 或资产无法转换为 AssemblyModel 时抛出的异常。",
    "AssemblyValidationError": "装配模型或其引用无法满足结构契约时抛出的异常。",
    "ScenarioValidationError": "Scenario 的时间、状态、驱动或对象引用无效时抛出的异常。",
    "BackendUnavailableError": "请求的计算后端无法加载时抛出的异常。",
    "BackendCapabilityError": "后端无法表达调用方明确请求的能力时抛出的异常。",
    "MotionSolveError": "运动求解开始后未能产生完整结果时抛出的异常；可包含失败时刻和最后有效结果。",
    "GeometryCheckError": "干涉、间隙或运动包络操作失败时抛出的异常。",
    "VerificationError": "调用方明确要求某个结构化检查通过、但检查失败时抛出的异常。",
    "VisualizationExportError": "无法从公开装配和结果数据导出 viewer 时抛出的异常。",
    "MotionPackageError": "`.kincheck` 包无法安全写出、读取或验证时抛出的异常。",
}


SYMBOL_RULES = {
    "AdapterResult": (
        "读取 `assembly` 作为后续验证输入，并保留 `source_map` 用于回溯 CADIR source ID。",
    ),
    "MotionResult": (
        "只有 `completed` 或经审阅的 `completed_with_warnings` 才可进入最终验收；`partial` 只可诊断。",
        "空 `sample_times_s` 不能证明任何运动命题。",
    ),
    "ValidationResult": (
        "`passed` 由 issues 中是否存在 error 派生；验证会聚合问题而不是 fail-fast。",
    ),
    "CheckReport": (
        "读取 `passed` 的同时保留 `evidence`、`issues`、`metadata`、检查对象和阈值。",
    ),
    "verify_transmission_ratio": (
        "该函数会发出 `DeprecationWarning`；不要在新示例或新实现中使用。",
    ),
    "check_envelope_interference": (
        "输入必须是两个 `operation == 'motion_envelope'` 的 `ClearanceReport`。",
        "`metadata['confirmed_mesh_interference']` 固定为 `False`；发生 overlap 后使用精确 mesh 检查确认。",
    ),
    "set_component_result_scope": (
        "`requested` + 空请求列表会扩大为全部组件，这是明确的历史兼容特例。",
    ),
    "list_executable_fixes": (
        "当前没有可执行 fix 时返回 `()`，调用方不得据此自行猜测修改。",
    ),
    "apply_assembly_fix": (
        "当前总是以 `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED` 拒绝执行。",
    ),
    "apply_scenario_fix": (
        "当前总是以 `KINCHECK-DIAGNOSTIC-FIX-UNIMPLEMENTED` 拒绝执行。",
    ),
}


PARAMETER_NOTES = {
    "assembly": "待构造、校验、求解或导出的 `AssemblyModel`。",
    "scenario": "已绑定装配定义的不可变 `Scenario`。",
    "motion_result": "待查询或检查的公开 `MotionResult`。",
    "xml_path": "CADIR 导出的 MJCF XML 路径。",
    "mapping_path": "与 XML 同批次的 mapping JSON 路径。",
    "asset_root": "mesh 等资产允许解析的根目录。",
    "path": "输入或输出文件路径；具体方向见用途说明。",
    "output_path": "输出文件路径。",
    "output_dir": "输出目录。",
    "time_s": "查询时间，单位 s，必须位于结果时间范围内。",
    "start_time_s": "时间窗起点，单位 s。",
    "end_time_s": "时间窗终点，单位 s。",
    "duration_s": "运行总时长，单位 s，必须为有限正数。",
    "period_s": "采样周期，单位 s，必须为有限正数。",
    "joint_id": "稳定且可解析的 joint ID。",
    "component_id": "稳定且可解析的 component ID。",
    "connector_id": "稳定且可解析的 connector ID。",
    "constraint_id": "稳定且可解析的 constraint ID。",
    "check_id": "调用方提供的稳定检查 ID，用于结果追溯。",
    "parameters": "该检查类型的显式参数；不得依赖未记录的隐式默认验收标准。",
    "options": "对应求解或分析的公开配置对象；记录实际阈值。",
    "status": "结构化状态；按对应结果类型允许的稳定值解释。",
    "passed": "结构化布尔结论；必须与 issues 和实际证据一起读取。",
    "issues": "结构化问题集合；保留错误码、对象和证据。",
    "evidence": "支持结论的机器可读证据。",
    "metadata": "附加的只读结构化元数据。",
    "sample_times_s": "严格递增的实际采样时间，单位 s。",
    "joint_positions": "按稳定 joint ID 给出的关节位置；转动用 rad，平移用 m。",
    "target_component_id": "作为几何或运动学目标的 component ID。",
    "target_connector_id": "可选目标 connector ID；省略时目标为组件坐标系。",
    "expected_ratio": "期望传动比的正幅值；方向由 `expected_direction` 单独表达。",
    "expected_direction": "期望输出与输入同向 `same` 或反向 `opposite`。",
}


def clean_annotation(value: Any) -> str:
    if value is inspect.Signature.empty:
        return "未标注"
    if isinstance(value, str):
        return value
    text = inspect.formatannotation(value).replace("typing.", "")
    return requalify(text)


def requalify(text: str) -> str:
    for module_name in (
        "assembly", "checks", "clearance", "clearance_result", "continuous_result", "diagnostics",
        "errors", "export", "integrity", "kinematics", "kinematics_analysis",
        "kinematics_geometry", "pose", "result", "scenario", "trajectory_checks",
        "visualization",
    ):
        text = text.replace(f"kincheckapi.{module_name}.", "")
    return text


def clean_default(value: Any) -> str:
    if value is inspect.Signature.empty:
        return "必填"
    if value is dataclasses.MISSING:
        return "必填"
    if isinstance(value, types.MappingProxyType):
        return "{}"
    text = repr(value)
    if text == "<factory>":
        return "default_factory"
    return f"`{text}`"


def public_names(module_name: str, module: Any) -> tuple[str, ...]:
    if "exports" in MODULES[module_name]:
        return tuple(MODULES[module_name]["exports"])
    return tuple(module.__all__)


def symbol_kind(value: Any) -> str:
    if inspect.isfunction(value):
        return "function"
    if inspect.isclass(value) and issubclass(value, enum.Enum):
        return "enum"
    if inspect.isclass(value):
        return "class"
    if typing.get_origin(value) is not None or isinstance(value, types.GenericAlias):
        return "alias"
    return "constant"


def effective_kind(name: str, value: Any) -> str:
    kind = symbol_kind(value)
    if kind in {"class", "enum"} and name != getattr(value, "__name__", name):
        return "alias"
    return kind


def source_name(value: Any, module_name: str) -> str:
    try:
        source = inspect.getsourcefile(value)
    except (TypeError, OSError):
        source = None
    return Path(source).name if source else f"{module_name}.py"


def purpose(name: str, value: Any, kind: str) -> str:
    if name in PURPOSE_OVERRIDES:
        return PURPOSE_OVERRIDES[name]
    if kind == "function":
        verbs = {
            "add_": "添加并返回更新后的不可变对象",
            "set_": "设置字段并返回更新后的不可变对象",
            "read_": "读取并重建公开对象",
            "write_": "把公开对象确定性写出",
            "validate_": "聚合验证输入契约",
            "check_": "执行结构化检查",
            "create_": "创建公开对象",
            "list_": "筛选并返回已记录的结构化证据",
            "analyze_": "分析机构或结果的运动学性质",
            "compute_": "计算后端无关的运动学量",
            "solve_": "求解指定运动学问题",
            "request_": "请求在结果中记录指定对象",
            "export_": "导出公开结果资产",
            "format_": "格式化结构化对象",
        }
        for prefix, description in verbs.items():
            if name.startswith(prefix):
                return f"{description}：`{name}`。"
        return f"执行公开操作 `{name}`。"
    if kind == "enum":
        return f"定义 `{name}` 接受的稳定枚举值。"
    if kind == "alias":
        return f"定义 `{name}` 使用的公开类型约定。"
    if kind == "constant":
        return f"公开常量 `{name}`。"
    return f"表示 `{name}` 的公开、可序列化数据结构。"


def parameter_rows(value: Any, kind: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    if kind not in {"function", "class"}:
        return rows
    try:
        signature = inspect.signature(value, eval_str=True)
    except (NameError, TypeError, ValueError):
        try:
            signature = inspect.signature(value)
        except (TypeError, ValueError):
            return rows
    for name, parameter in signature.parameters.items():
        if name in {"self", "cls"}:
            continue
        note = PARAMETER_NOTES.get(name)
        if note is None:
            if name.endswith("_id"):
                note = f"稳定且可解析的 `{name}`。"
            elif name.endswith("_ids"):
                note = f"显式指定的 `{name}` 集合。"
            elif name.endswith("_m_s2"):
                note = f"`{name}`，单位 m/s^2，必须为有限值。"
            elif name.endswith("_m_s"):
                note = f"`{name}`，单位 m/s，必须为有限值。"
            elif name.endswith("_rad_s"):
                note = f"`{name}`，单位 rad/s，必须为有限值。"
            elif name.endswith("_rad"):
                note = f"`{name}`，单位 rad，必须为有限值。"
            elif name.endswith("_m"):
                note = f"`{name}`，单位 m，必须为有限值。"
            elif name.endswith("_s"):
                note = f"`{name}`，单位 s，必须为有限值。"
            else:
                note = f"`{name}` 的公开输入或数据字段。"
        rows.append((name, clean_annotation(parameter.annotation), clean_default(parameter.default), note))
    return rows


def signature_text(name: str, value: Any, kind: str) -> str:
    if kind == "function":
        try:
            signature = inspect.signature(value, eval_str=True)
            text = str(signature)
            for module_name in (
                "assembly", "checks", "clearance", "clearance_result", "continuous_result", "diagnostics",
                "errors", "export", "integrity", "kinematics", "kinematics_analysis",
                "kinematics_geometry", "pose", "result", "scenario", "trajectory_checks",
                "visualization",
            ):
                text = text.replace(f"kincheckapi.{module_name}.", "")
            return f"{name}{text}"
        except (NameError, TypeError, ValueError):
            try:
                return f"{name}{inspect.signature(value)}"
            except (TypeError, ValueError):
                pass
    if kind == "class":
        fields = parameter_rows(value, kind)
        if dataclasses.is_dataclass(value):
            body = "\n".join(f"    {field_name}: {annotation}" for field_name, annotation, _, _ in fields)
            return f"@dataclass(frozen=True)\nclass {name}:\n{body or '    ...'}"
        try:
            base = value.__bases__[0].__name__ if value.__bases__ else "object"
            return f"class {name}({base}): ...\n\n{name}{inspect.signature(value)}"
        except (TypeError, ValueError):
            return f"class {name}: ..."
    if kind == "enum":
        return f"class {name}(str, Enum): ..."
    if kind == "alias":
        target = getattr(value, "__name__", None)
        return f"{name} = {target or clean_annotation(value)}"
    return f"{name} = {value!r}"


def returns_text(value: Any, kind: str) -> str:
    if kind == "function":
        try:
            annotation = inspect.signature(value).return_annotation
        except (TypeError, ValueError):
            annotation = inspect.Signature.empty
        return f"返回 `{clean_annotation(annotation)}`。"
    if kind == "class":
        if issubclass(value, Exception):
            return "构造公开领域异常。捕获后读取 `code`、`report` 和结构化上下文，不匹配自由文本消息。"
        return "构造并返回不可变的公开数据对象；字段值会在构造阶段执行类型或范围约束。"
    if kind == "enum":
        return "使用枚举成员或其稳定字符串值，避免自行发明未定义状态。"
    if kind == "alias":
        return "这是类型约定，不是可调用函数。"
    return "这是只读公共常量，不是可调用函数。"


def enum_section(value: type[enum.Enum]) -> list[str]:
    lines = ["## 枚举值", "", "| 成员 | 值 |", "| --- | --- |"]
    for item in value:
        lines.append(f"| `{item.name}` | `{item.value}` |")
    return lines


def page(module_name: str, import_module: str, name: str, value: Any) -> str:
    kind = effective_kind(name, value)
    lines = [
        f"# `{name}`",
        "",
        "## API 定义",
        "",
        "```python",
        signature_text(name, value, kind),
        "```",
        "",
        f"源码：`src/kincheckapi/{source_name(value, module_name)}`。",
        "",
        "## 导入",
        "",
        "```python",
        f"from kincheckapi.{import_module} import {name}",
        "```",
        "",
        "## 用途",
        "",
        purpose(name, value, kind),
        "",
    ]
    rows = parameter_rows(value, kind)
    if rows:
        lines.extend(["## 参数与字段", "", "| 名称 | 类型 | 默认值 | 说明 |", "| --- | --- | --- | --- |"])
        for field_name, annotation, default, note in rows:
            lines.append(f"| `{field_name}` | `{annotation}` | {default} | {note} |")
        lines.append("")
    if kind == "enum":
        lines.extend(enum_section(value))
        lines.append("")
    lines.extend(["## 返回与失败", "", returns_text(value, kind), ""])
    if module_name in {"checks", "clearance", "continuous_result", "kinematics", "diagnostics"}:
        lines.append("结构化结果中的 `issues`、状态、样本数和实际测量是契约的一部分；不要只判断函数是否抛异常。")
        lines.append("")
    lines.extend(["## 模块约束", ""])
    for rule in MODULE_RULES[module_name]:
        lines.append(f"- {rule}")
    for rule in SYMBOL_RULES.get(name, ()):
        lines.append(f"- {rule}")
    lines.extend(["", "## 相关文档", "", f"- [`{MODULES[module_name]['title']}`](README.md)", "- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)", ""])
    return "\n".join(lines)


def readme(module_name: str, exports: list[tuple[str, Any]]) -> str:
    info = MODULES[module_name]
    lines = [f"# {info['title']}", "", info["summary"], "", "## 公开 API", ""]
    if not exports:
        lines.append("当前版本没有公开操作；不要为此命名空间虚构调用。")
        lines.append("")
    else:
        lines.extend(["| 符号 | 类型 | 用途 |", "| --- | --- | --- |"])
    for name, value in exports:
        kind = effective_kind(name, value)
        kind_zh = {"function": "函数", "class": "类型", "enum": "枚举", "alias": "类型别名", "constant": "常量"}[kind]
        summary = purpose(name, value, kind).replace("\n", " ")
        lines.append(f"| [`{name}`]({name}.md) | {kind_zh} | {summary} |")
    lines.extend(["", "## 模块规则", ""])
    for rule in MODULE_RULES[module_name]:
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def generate(repo: Path, *, check: bool) -> int:
    doc_root = repo / "skill_zh" / "doc"
    expected: dict[Path, str] = {}
    for module_name, info in MODULES.items():
        module = importlib.import_module(f"kincheckapi.{module_name}")
        directory = doc_root / info.get("directory", module_name)
        exports = [(name, getattr(module, name)) for name in public_names(module_name, module)]
        expected[directory / "README.md"] = readme(module_name, exports)
        import_module = info.get("directory", module_name)
        if module_name == "trajectory_checks":
            import_module = "trajectory_checks"
        for name, value in exports:
            expected[directory / f"{name}.md"] = page(module_name, import_module, name, value)

    if check:
        failures = []
        for path, content in expected.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                failures.append(path.relative_to(repo))
        for directory in {path.parent for path in expected}:
            expected_in_directory = {path for path in expected if path.parent == directory}
            failures.extend(
                path.relative_to(repo)
                for path in directory.glob("*.md")
                if path not in expected_in_directory
            )
        if failures:
            print("API docs are stale or missing:")
            for path in failures:
                print(f"- {path}")
            return 1
        print(f"API docs are current: {len(expected)} files")
        return 0

    generated_dirs = {path.parent for path in expected}
    for directory in generated_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        for old in directory.glob("*.md"):
            old.unlink()
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(f"Generated {len(expected)} API documentation files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated docs differ")
    args = parser.parse_args()
    return generate(REPO_ROOT, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
