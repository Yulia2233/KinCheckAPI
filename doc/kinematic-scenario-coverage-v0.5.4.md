# KinCheckAPI v0.5.4 运动学工况覆盖分析

本文只分析本工作区的 KinCheckAPI，不分析 CADSimAPI。覆盖结论以当前 src/kincheckapi
公开 API、tests 回归测试和 v0.5.4 曲柄滑块案例为依据。

## 结论和覆盖等级

“可覆盖”指公开 API 能提供稳定输入、输出和结构化 pass/fail 报告；不等于库已经替用户自动生成所有工况或自动决定工程阈值。

- A：直接覆盖，已有专门 API 和结构化 pass/fail 报告。
- B：组合覆盖，已有 profile、轨迹或 Jacobian 数据，需要验证脚本组合 API 并写少量派生指标。
- C：部分覆盖，能得到相邻证据，但用户要求的关键量或通用求解器缺失。
- D：当前不覆盖，没有公开的输入模型、求解器或验收检查。

| 运动学工况 | 等级 | 当前能证明的内容 | 推荐组合调用 | 主要缺口 |
|---|---|---|---|---|
| 静止/初始位姿 | A/B | 单个位姿、关节值、连接器位姿和残差；home/零位可写入 Scenario。Pose 使用 SI 米和 xyzw 四元数。 | create_scenario → set_initial_joint_position 或 set_joint_home_position + set_initial_state_from_home → validate_scenario → solve_position；动态初始状态再用 set_initial_joint_velocity、solve_motion。 | 没有公开 Pose 到 4×4 位姿矩阵的转换。 |
| 匀速直线运动 | A/B | prismatic Joint 的恒定速度、位移、线速度和轨迹。 | add_joint_speed_driver 或相同速度 MotionSegment → solve_motion → check_driver_tracking + check_trajectory。 | 没有笛卡尔直线目标规划器。 |
| 变速直线运动 | B | 线性 speed profile 的斜率可产生加速度，能检查最大线速度和加速度。 | add_joint_speed_profile/add_joint_motion_segments → solve_motion → check_trajectory(max_speed_m_s, max_acceleration_m_s2)。 | 没有 jerk、S 曲线、加加速度或专门启动/停止事件报告；加速时间和停止距离需脚本计算。 |
| 匀速转动 | A/B | revolute Joint 的角度、角速度和角位移。 | add_joint_speed_driver → solve_motion → check_driver_tracking + check_trajectory(max_angular_speed_rad_s)。 | 没有转数、圈数专用报告。 |
| 变速转动 | B | 角速度 profile 斜率和角加速度峰值。 | add_joint_speed_profile/segments → solve_motion → check_driver_tracking + check_trajectory(max_angular_acceleration_rad_s2)。 | 没有 jerk 和制动冲击专用指标。 |
| 曲线运动 | B/C | Connector 轨迹可用 trace_connector_path 得到路径长度、端点和 XYZ 包围范围；曲率可由位置差分计算。 | request_component_result(..., connector_id=...) → solve_motion → trace_connector_path；脚本计算曲率和转弯半径。 | 没有曲率、曲率半径、切向/法向速度或样条轨迹规划器；离散采样不是连续曲率证明。 |
| 平面运动 | B/C | 平面机构的 X/Y 位移、世界系角速度和四元数姿态。 | request_component_result/Connector → solve_motion → read_component_state/read_connector_state + check_trajectory。 | 没有 x,y,yaw 专用目标或平面轨迹检查；yaw 需从四元数解算。 |
| 空间运动 | C | Pose、世界系线/角速度、线/角加速度和六行 Jacobian。 | solve_motion → read_component_state/read_connector_state → compute_jacobian、find_singularities。 | backend 能力仅支持 fixed/revolute/prismatic；cylindrical、spherical、planar、free 均为 false，没有通用 6D 自由体积分和姿态驱动。 |
| 单自由度运动 | A | 一个标量 Joint 的位置、速度、加速度、限位和路径。 | 初始关节值 → 一个 driver/profile → solve_motion → check_joint_limits、check_driver_tracking、check_trajectory。 | 需先确认拓扑确实只有一个有效 DOF。 |
| 多自由度协调运动 | B/C | 可同时声明多个 Joint driver；每个关节可分别跟踪，传动约束可检查。 | 多次 add_joint_position_driver/add_joint_speed_profile → solve_motion → 每个关节 check_driver_tracking + check_transmission_ratio。 | 没有多轴同步误差、统一插补器、末端协同规划或同时到达专用检查。 |
| 正运动学 | A/B | 已知标量关节值可得到 Component/Connector 位姿。 | solve_position(assembly, joint_positions) → PositionResult.component_poses；动态场景读取 MotionResult。 | 对一般 6D Joint 不支持；没有 DH/齐次矩阵报告。 |
| 逆运动学 | C | PoseTarget + solve_position 或 check_reachability 可对受支持拓扑尝试一个目标。 | PoseTarget → check_reachability 或 solve_position → 读取 reachable、position_result、residuals。 | 不是通用多解 IK：无冗余解集、连续轨迹规划、碰撞约束 IK 和优化目标；仅标量树 Joint。 |
| 工作空间分析 | B | compute_workspace 对显式有限关节范围做确定性网格采样，并保留 reachability/residual/Jacobian。 | WorkspaceOptions(joint_ranges, samples_per_joint, max_samples) → compute_workspace。 | 不是连续工作空间边界证明；可能截断，姿态工作空间和障碍物约束需外部分析。 |
| 奇异位形 | A/B | compute_jacobian 提供 rank、奇异值、condition number；find_singularities 对 MotionResult 每个采样分类。 | solve_motion → find_singularities；静态点用 compute_jacobian。 | 依赖有限差分和 target；没有动力学意义上的力矩能力或连续区间证明。 |
| 启动工况 | B | 零速度初始状态加速度 ramp，可记录启动时间、速度和加速度。 | set_initial_joint_velocity(..., 0) → ramp MotionSegment/speed profile → solve_motion → check_driver_tracking + check_trajectory；启动时间脚本计算。 | 没有 startup API、稳态判据、峰值摘要或 jerk 指标。 |
| 停止工况 | B | 减速 profile 到零，可读取停止时间和停止距离。 | 减速 MotionSegment → solve_motion → check_trajectory；停止距离从实际 Trajectory 计算。 | 没有停止事件、制动距离和最终静止判定 API。 |
| 换向工况 | B | 速度 profile 可跨过零并反向；实际速度可跟踪。 | 正值→零→负值 MotionSegment → solve_motion → check_driver_tracking + check_trajectory；换向时刻由速度符号变化检测。 | 没有换向事件、速度冲击、反向间隙或 backlash 模型。 |
| 周期运动 | B/C | 可手工生成重复 position/speed profile，在有限时间窗内逐采样检查。 | 重复 MotionProfile/segments → solve_motion → check_driver_tracking、check_trajectory；周期/频率/幅值由脚本计算。 | 没有周期驱动、频谱、周期稳定性或跨周期漂移专用 API。 |
| 跟踪运动 | A/B | 单 Joint 的 position/speed 有 check_driver_tracking；Pose/Connector 目标有 check_pose_target。 | MotionProfile/segments → solve_motion → check_driver_tracking；位姿另加 check_pose_target。 | driver tracking 是关节标量跟踪；复杂笛卡尔轨迹需自定义目标和误差计算。 |
| 极限运动 | A/B | authored Joint limits、采样极值、limit events、速度/加速度上限。 | Assembly 写 JointLimit → solve_motion → check_joint_limits + check_trajectory；list_limit_events 读取事件。 | 没有自动极限探索，采样点之外不保证连续极限。 |
| 碰撞前运动状态 | B/C | 采样点的组件相对 Pose、相对速度、mesh 最小间隙和首次干涉时间。 | request_component_result(scope=all) → solve_motion → check_interference/check_minimum_clearance + read_component_state；相对速度由状态差分。 | 没有连续 TOI、接触法向角和接触前预测器；FCL 是离散采样证据。 |

## 已覆盖工况的通用组合模板

### 静态、正运动学和单关节动态

~~~python
scenario = create_scenario(scenario_id="nominal", assembly=assembly)
scenario = set_initial_joint_position(
    scenario=scenario, joint_id="joint.input", position_rad_or_m=0.0
)
scenario = set_initial_joint_velocity(
    scenario=scenario, joint_id="joint.input", velocity_rad_s_or_m_s=0.0
)
scenario = set_run_duration(scenario=scenario, duration_s=2.0)
scenario = set_sample_period(scenario=scenario, period_s=0.01)
scenario = add_joint_speed_profile(
    scenario=scenario, joint_id="joint.input",
    profile=((0.0, 1.0), (2.0, 1.0)),
)
scenario = request_joint_result(scenario=scenario, joint_id="joint.input")
scenario = request_component_result(
    scenario=scenario, component_id="component.end", connector_id="tool"
)
validate_scenario(scenario=scenario).raise_if_failed()
motion = solve_motion(scenario=scenario)
tracking = check_driver_tracking(
    motion_result=motion, scenario=scenario,
    joint_id="joint.input", tolerance=1e-3,
)
trajectory = check_trajectory(
    motion_result=motion, component_id="component.end",
    max_speed_m_s=2.0, max_acceleration_m_s2=10.0,
)
~~~

所有 check 都要读取 passed、issues 和 evidence，不能只判断函数是否抛异常。

### 变速、启动、停止、换向和周期

使用 MotionSegment 表达 piecewise 工况：

~~~python
segments = (
    MotionSegment(start_time_s=0.0, end_time_s=0.5,
                  mode="speed", value=0.0, interpolation="linear"),
    MotionSegment(start_time_s=0.5, end_time_s=1.0,
                  mode="speed", value=1.0, interpolation="linear"),
    MotionSegment(start_time_s=1.0, end_time_s=1.5,
                  mode="speed", value=-1.0, interpolation="linear"),
    MotionSegment(start_time_s=1.5, end_time_s=2.0,
                  mode="speed", value=0.0, interpolation="linear"),
)
scenario = add_joint_motion_segments(
    scenario=scenario, joint_id="joint.input", segments=segments
)
~~~

add_joint_motion_segments 会校验段连续性、模式和插值模式一致性，但不会自动给出
启动时间、停止距离、冲击或周期频率；这些指标要从 JointTrajectory/Trajectory
采样计算，再用 check_trajectory 验收峰值。

### 位姿、跟踪、IK、Jacobian 和奇异性

- 已知关节值：solve_position(assembly=..., joint_positions=...)。
- 目标位姿：PoseTarget + solve_position 或 check_reachability。
- 已记录位姿目标：check_pose_target。
- Jacobian：compute_jacobian。
- 运动过程奇异性：find_singularities。
- 路径统计：trace_connector_path。
- 工作空间：显式 WorkspaceOptions.joint_ranges + compute_workspace。

这些 API 输出结构化证据，但没有把任意 6D 末端任务转成可执行的多轴轨迹；
需要外部规划器生成关节 profile，再回到 Scenario/solve/check 链路。

### 干涉、间隙、装配连接和运动包络

~~~python
pairs = (
    ("component.ground", "component.link"),
    ("component.link", "component.slider"),
)
interference = check_interference(
    assembly=assembly, motion_result=motion,
    component_pairs=pairs, asset_root=model_dir,
    sampling_scope="motion_result", max_sample_period_s=0.01,
)
clearance = check_minimum_clearance(
    assembly=assembly, motion_result=motion,
    component_pairs=pairs, minimum_allowed_clearance_m=5e-4,
    asset_root=model_dir, sampling_scope="motion_result",
)
integrity = check_assembly_integrity(
    assembly=assembly, motion_result=motion,
    asset_root=model_dir, sampling_scope="motion_result",
    containment_relations=(ContainmentRelation(
        relation_id="guide",
        contained_component_id="component.slider",
        container_component_id="component.ground",
        axis=(1.0, 0.0, 0.0),
        min_position_m=0.10, max_position_m=0.20,
        allowed_escape_tolerance_m=1e-3,
    ),),
)
~~~

干涉和最小间隙是离散 mesh 检查，不是连续时间碰撞证明。关节、closure 和
containment 可以证明装配关系持续存在；要证明没有悬空，应同时检查机械关系、
导轨 containment、所有 Component trajectory 和明确的结果 scope。

## 当前错误追踪能力

当前已经具备可用的“语义 traceback”链路，但它不是 Python 原生调用栈 traceback。
推荐保留以下四层：

1. 输入/场景层：validate_scenario 返回 ValidationResult，包含稳定 code、stage、
   object_ids、evidence 和 suggested_actions。
2. 求解层：MotionResult 有 status、时间范围、样本、残差、limit events、warnings
   和 backend metadata；try_solve_motion 还保留 last_valid_result、failure 和 report。
3. 检查层：CheckReport、DriverTrackingReport、ClearanceReport 有 passed、status、
   evidence、issues 和 metadata。
4. CLI/持久化层：使用 error.to_dict() 或 result.to_dict()；.kincheck/JSON 保存
   原始结构化结果，不要只解析人类可读 stdout。

推荐失败入口：

~~~python
attempt = try_solve_motion(scenario=scenario, options=options)
if not attempt.succeeded:
    payload = attempt.to_dict()
~~~

对于预期的模型、场景、backend 和检查失败，这条链路可以回答：

- 是否 pass：读取最外层 passed/succeeded，并拒绝 partial、capability_failed、空
  samples 和不完整 evidence。
- 发生了什么：读取 status、stage、failure_time_s、对象 ID 和实际 evidence。
- 什么原因：读取稳定错误码、backend capability 和 diagnostics。
- 怎么修复：读取 suggested_actions，回到对应的场景、装配或 geometry source 修复。

### 尚未做到“任何报错都可完整 traceback”的地方

- solve_position 的部分未知对象和非法参数路径返回 PositionResult(passed=False)，部分
  底层输入错误仍可能直接抛 ValueError。
- check_reachability、compute_workspace、find_singularities 虽包装若干
  TypeError/ValueError，但 public signature 仍有 **kwargs，错误字段不如显式参数稳定。
- backend 异常转换后通常保留类型、对象和时间，不一定保留完整原生 Python traceback 文本。
- clearance/FCL 能提供稳定 code 和测量值，但 native mesh 错误可能只剩
  technical_error_type，不能定位具体三角面或源代码行。
- ProfileBoundary 只有 HOLD 和 ZERO，没有越界即报错的第三种行为。
- 几何检查的底层错误通常放在 metadata["error"]；调用者只读 issues 会丢失上下文。
- 原生异常是否带 stack frame 取决于调用者是否保存 traceback.format_exc()；当前协议
  主要是语义诊断，不是标准 Python traceback 文本。

因此，v0.5.4 可以对预期的运动学验证失败做到“是否 pass、发生了什么、原因、修复
建议”的结构化追踪；不能承诺对任意第三方 backend 原生异常都返回统一的 Python
traceback 文本。

## 建议的 v0.5.5 修复顺序

1. 统一 PositionResult、ReachabilityResult、WorkspaceResult、CheckReport 的错误
   字段：code、stage、message、object_ids、failure_time_s、evidence、
   suggested_actions、native_error_type。
2. 将 public **kwargs 分析入口改成显式签名或统一参数解析器。
3. 在 try_solve_motion 和检查包装器中增加可选 traceback_text，同时保留语义字段。
4. 为 backend compile、initial-state、step、non-finite、mesh/FCL、导出/导入分配
   稳定错误码，并始终保留失败时间和最后有效样本。
5. 增加公共 diagnostic_trace(result_or_error) 序列化入口，固定输出 passed、
   what_happened、cause、how_to_fix、traceback。
6. 增加 profile 越界 ERROR 行为和启动/停止/换向/周期/碰撞前专用检查。

## 证据范围

本分析检查了运动学、Scenario、result、checks、clearance、assembly、pose 和
backend 实现，以及静态/动态、空间运动、位置求解、workspace、singularity、
trajectory、clearance、integrity 和 v0.5.4 contract 测试。结论针对受支持的标量
关节和离散采样模型，不代表连续时间碰撞、动力学、强度或制造可行性证明。


## v0.5.5 实现后的状态

本轮已经把标量关节范围内可落地的 C 类能力实现为公开检查：PathTarget 曲线
跟踪、PoseTrajectory 平面/位姿跟踪、启动/停止/换向事件、周期漂移和显式目标
多轴同步。Scenario 现在能记录周期目标、协调目标和 PoseTrajectory 验收目标；
ProfileBoundary.ERROR、未支持关节 capability failure、统一 diagnostic_trace、
最后有效结果和可选原生 traceback 也已经接入。

连续时间 TOI、Cartesian Pose driver、通用多解 IK 和 6D Joint 仍然是明确的
capability failure。它们没有被包装成“检查通过”；调用方会得到稳定错误码、
missing_capabilities、stage、object_ids、evidence 和修复建议。
