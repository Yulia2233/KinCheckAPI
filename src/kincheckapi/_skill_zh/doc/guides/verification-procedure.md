# 验证程序优先流程

先把用户要求写成独立的 KinCheckAPI Python 验证程序，再使用 SimpleCADAPI 构建模型。验证程序是验收契约，模型目录是它的运行时输入。

## 1. 明确验收命题

记录驱动关节、初始状态、时间窗、采样周期、目标位姿或轨迹、残差阈值、限位、组件对和 SI 单位。为验证程序预先规定稳定的 joint、component 和 connector ID；信息缺失时把它列为模型接口要求，不猜测对象关系。

## 2. 先创建验证目录

默认创建 `verification/verify.py`，复杂检查再拆到 `verification/checks.py`。`verify.py` 同时提供 `verify(model_dir)` Python API 和接收一个模型目录的 CLI。它只能依赖 KinCheckAPI 公开 API 和 Python 标准库，不得导入 SimpleCADAPI 建模模块。

在模型存在前，先检查脚本语法、导入和非法路径分支。将驱动、检查对象、阈值、时间窗和采样规则固定在代码中。

## 3. 再构建并导出模型

交给主 `simplecadapi` skill 在独立建模环境建立几何、装配关系、稳定 ID 和必需
`interface.*` 标签，capture 成品 `.scadpkg`。再在插件环境通过运行时关卡并调用
`prepare_package()`；详见 [addon-contract.md](addon-contract.md)。它准备以下目录：

```text
model/
├── scene.xml
├── scene.mapping.json
└── meshes/
```

验证程序只接收这个目录，不依赖建模源码的目录布局。

## 4. 转换并预检

在 `verify(model_dir)` 中显式把三个输入路径传给 `convert_mjcf()`。依次调用 `validate_assembly()`、`validate_topology()` 和按需使用的 `build_kinematic_tree()`、`analyze_dofs()`；读取 issue 的 code、object_ids 和 evidence。

## 5. 建立 Scenario 并求解

用 `create_scenario()` 设置初始 joint 状态、驱动、运行时长、采样周期和结果请求。每个设置函数都返回新的 Scenario，必须接住返回值；求解前调用 `validate_scenario()`。

调用 `solve_motion()`；需要保留失败前轨迹时调用 `try_solve_motion()`。检查 status、sample_times_s、约束残差、limit events 和 issues。`partial` 立即退出通过路径。

## 6. 执行验收检查

使用显式 `CheckSpec` 调用 `run_checks()`，或调用与用户命题直接对应的公开检查函数。检查 passed、issues、evidence、阈值和实际样本计数，并在严格 CLI 中调用 `raise_if_failed()`。

只有用户要求运动安全时才执行干涉、最小间隙或运动包络检查。组件对、容差、资产根目录和采样范围必须显式给出。

## 7. 修改模型并重复验证

失败时把结构化证据交回主 SimpleCADAPI skill 修改所属建模源码，重新 capture 并准备
新产品包后运行同一验证程序。插件内部不得修改几何或产品包成员。除非用户改变验收
命题，不得放宽阈值、减少检查、跳过失败样本或扩大碰撞排除范围。

## 8. 交付

默认交付可重复运行的 `verification/` Python 目录，并给出运行命令。控制台输出保留通过状态、证据和错误码；失败或未完成使用非零退出码。`.kincheck`、JSON 报告和可视化仅在用户明确要求调试、归档或回放时附加生成。
