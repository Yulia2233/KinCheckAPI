# Benchmark 验证脚本规范

建模 Agent 只接收案例的 `prompt.md`，只交付 `.scadpkg`。`verification/` 属于评测端私有评分程序；它从产物测量事实，不能读取建模源中的预期值、接受 Agent 写的报告或让 Agent 修改阈值。本规范配合 [Prompt 规范](spec.md) 使用。

## 一份案例如何组织与冻结

```text
benchmark/
  spec.md                       # Prompt 规范
  verifier-spec.md              # 本文
  adapter.py                    # scadpkg → model_dir → verify
  common.py                     # JSON、诊断、来源绑定和汇总
  guided_four_bar/
    prompt.md                   # 唯一给建模 Agent 的文件
    verify.py                   # 与 prompt 配对的固定入口
    README.md                   # 评测端说明与已知覆盖边界
    verification/…              # 同版本辅助文件
  xyz_pick_place_gantry/
    prompt.md
    verify.py
    README.md
    verification/contract.py    # 冻结 ID、SI 工况和验收预算
    verification/verify.py
```

先审定 Prompt 和可执行工况，再冻结 verifier，最后才生成模型。Prompt 中自相矛盾的命名、不可达的运动时间/距离、缺少的接触定义是 **benchmark 合同错误**，不能算成模型能力差，也不能默默改要求。新增版本必须记录修订理由并重新计算 Prompt 和 verifier（含所有辅助文件）的 SHA256。未经整包正例、故障反例验证的案例标记 `draft`，不能用于排行榜。

## 入口、输入与输出契约

Python 入口固定为 `verify(model_dir: str | Path)`，返回包含 `passed`、`hard_pass`、`status`、`checks`、`issues` 和 `coverage` 的字典。CLI 固定为 `python verification/verify.py MODEL_DIR [--report REPORT.json]`，stdout 只打印一个完整、严格 JSON 对象，进度写 stderr。验收通过退出 0；工程失败、缺数据、不支持、未完成或异常均非零。`--report` 只改变保存位置，不能改变工况、阈值或检查范围。

所有案例使用同一 adapter。准备目录包含同次导出的 `scene.xml`、`scene.mapping.json`、`meshes/`、`collision_meshes/`、`package-provenance.json` 和 adapter 写出的 `benchmark-input.json`。动力学从 provenance 指向的原 `.scadpkg` 读取 BREP/材料，不要求 Agent 额外交物性文件。输入指纹绑定原包、派生文件和单位归一化记录，运行前后均核对；禁止混用另一模型的 mesh、物性或结果。adapter 的成功导出不等于通过：必须解析 verifier JSON、检查进程退出码与布尔结论一致。无 JSON、空输出、伪造通过或报告缺项不得通过。

每个 check 必须有稳定 `check_id`、`status`、`passed`、`operation`、实际/目标/单位 evidence，以及失败时的 code、对象、原因和修复建议；时间相关失败附带时间。异常保留已完成检查，返回 `validation_failed`、`capability_failed` 或 `failed`，不能把异常吞掉当作空列表。输入本身为 NaN/Inf 时用字符串描述非法值，JSON 不允许 NaN/Infinity。

## 验收顺序与独立证据

| 门槛 | 必须获取的证据 | 不允许的替代 |
| --- | --- | --- |
| 合同与来源 | 精确 definition/occurrence/joint/connector ID、数量、类型、端点、ground、同包 hash；名称冲突先报错 | 同义词匹配、扫描文件猜模型、从 Agent 报告读取结果 |
| 几何与安装 | BREP/网格实测外形、孔、实体有效性、实际安装区域、完整硬件清单；每个叶实体到 ground 的真实连接链 | 仅检查名字或 bbox 就宣称孔与安装正确；层级父子当作机械固定 |
| 运动 | 固定初态与目标；完整时间窗的实际位置/速度/加速度、限位、约束残差、跟踪误差 | 只看最后一帧、用实际终点作为 target、少采样避开违规 |
| 无碰撞/不悬空 | N(N−1)/2 叶实体配对有明确归宿；固定对初态精查加相对位置不变性；相对运动对连续检查；局部功能接触必须有独立面级定义 | fixed/revolute 自动免检、整个相邻 pair 排除、把节点连通当成实体落座 |
| 物性与动力学 | 从原包密度、封闭 BREP 求每个 occurrence 的质量/质心/完整惯量；位姿转换、固定组聚合、显式惯量编译反查；完整状态和外力 | 用默认质量；重复计 payload/转子；把运动学驱动器输出当作真实力矩 |
| 驱动与制动 | 独立预期与实际正动力学轨迹；有限额定/短时力、超限持续时间、停机距离/时间、功率与能量平衡 | 输出非空就通过；饱和后不检查实际路径；用同一个求解器互相证明 |
| 接触承载 | 真实接触面积/方向和来源可靠的载荷；明确反力唯一性及摩擦模型 | 任意平分双导轨反力；凭空填法向力给容量 API；密度推导摩擦/强度 |

采样步长、积分步长、网格精度、连续查询预算由评测端冻结，不出现在建模 Prompt。阈值分清工程要求与数值误差预算。所有有限数和单位在输入阶段校验；空 targets、空 pairs、空结果、缺失工况、partial 均不能通过。碰撞安全限定于记录轨迹及声明的插值，不能外推为真实连续接触响应。

动力学独立基准至少包含静止极限（逆动力学与重力平衡一致）、平移 `F = m a`、旋转 `τ = I α`、力臂与外载功。质量取自导出实体，期望公式取自冻结工况。检查实际积分步上的峰值和持续时间；API 只给输出采样时必须注明覆盖不足。额定功率/效率来自冻结工程输入，不能猜材料参数。

## 完整性、负例和评分

`coverage` 列出 Prompt 的全部工程命题以及对应 check IDs。已实现子集可以给出真实子结论；没有可用 API、缺少冻结参数或没有实际证据的命题标为 `capability_failed` / `indeterminate`。`hard_pass` 只在必需命题全部有非空证据并通过时为 true；不能用静载通过代替全动态通过。报告另写 `benchmark_ready` 区分“评分合同已就绪”与“这次模型是否通过”。合同有冲突时 `benchmark_ready=false`，不能拿它评价生成模型。

每个 verifier 至少包含一个独立故障反例并保存预期错误码和实际错误对象：例如保持原模型不变，在复制的轨迹中使两个真实 mesh 相交，碰撞报告必须失败。负例检测成功只说明检测器有效，故障模型的工程结论仍是失败。测试还须覆盖错误模型、缺包、改名、缺硬件、缺物性、非法数值、空轨迹及未支持能力。禁止“任何异常都算负例通过”。

四连杆采用现有 example verifier 的冻结副本，保留闭环、跟踪、限位、36 个物理 pair 和真实网格反例。其历史脚本尚未测量 Prompt 的每一项孔/槽尺寸，因此单列 `reference_passed`；未补齐这些几何命题前不能升级成全 Prompt 的 `hard_pass`。XYZ 已冻结为三轴直驱刚体模型；直线电机的有限标量驱动可以验证，电磁定子/forcer 的物理绑定、导轨单点反力和结构强度仍须明确标为未覆盖。案例 README 必须如实记录这些边界和实测验证状态。
