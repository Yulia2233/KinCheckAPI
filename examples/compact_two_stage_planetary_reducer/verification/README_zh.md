# 紧凑二级行星减速器：修复前后对比

[English](README.md) | 简体中文

目录与四连杆一致：`verification/`、`model_before/`、`model_after/`、`output/`。
两个模型目录都包含 `source/`、产品包和 MJCF 输入；MJCF 文件名保持
`scene.xml`、`scene.mapping.json`、`meshes/`，兼容原有 `verify(model_dir)`。

## 修复内容与验收

保留原来的输入速度 **8 rad/s**、时长 **1 s**、采样周期 **0.02 s**、同向
**20:1** 减速比和 **1e-3** 相对容差，传动比检查窗仍为 0.1-1.0 s。
另外显式要求全部 **12 条啮合方程**，在完整运动窗检查残差，容差为 **1e-8 m**。
缺失方程不能通过。

旧导出文件丢失了 gear/belt 传动关系。修复版从模型源重新 capture，保留啮合两端
connector 坐标和米制半径，并让两端都相对同一行星架表达运动。同轴重复关节记录为
明确别名，不再产生重复父节点或错误固定关系。减速比只用于验收，未写入求解器强制输出。
齿数、尺寸和原有几何参数保持不变。

二级模型另为轴承零件补充了显式的名义钢材密度 7850 kg/m3，与模型中既有钢材
密度一致，避免依赖导出器的默认密度；该值属于建模假设，不代表实测材料参数。

## 运行

在 CADSimAPI 仓库根目录、分析环境执行：

```bash
.venv-addon/bin/python examples/compact_two_stage_planetary_reducer/verification/simulate_and_record.py
.venv-addon/bin/python examples/compact_two_stage_planetary_reducer/verification/simulate_before_optimization.py
.venv-addon/bin/kincheck verify examples/compact_two_stage_planetary_reducer/model_after --script examples/compact_two_stage_planetary_reducer/verification/verify.py --format json
```

修复版验收失败时返回错误；旧版应复现失败并标记 `expected_failure: true`。
报告和真实求解轨迹分别写入 `output/before/`、`output/after/` 下的
`compact_two_stage_planetary_reducer.verification.json` 和 `compact_two_stage_planetary_reducer.kincheck`。
可用仓库的 `viewer/kincheck_viewer.py` 回放，轨迹不是按目标减速比构造的动画。

## 重建

在独立建模环境运行 `model_after/source/main.py`，然后在插件环境运行
`model_after/source/export_mjcf.py`。也可直接使用新增产品包入口：

```bash
.venv-addon/bin/kincheck verify-package examples/compact_two_stage_planetary_reducer/model_after/compact_two_stage_planetary_reducer.scadpkg --work-dir examples/compact_two_stage_planetary_reducer/output/package-work --script examples/compact_two_stage_planetary_reducer/verification/verify.py --format json
```

配套 SDK 最低版本为 CADIR 2.1.3b3。`model_before` 的旧格式产品包原样保留，不能
通过手改归档兼容新版 SDK；需要建模变更时修改 `model_after/source/` 并重新 capture。
原验证代码和历史说明保存在 `verify_original.py`、`README_legacy.md`。
本例验证运动学传动，不据此声称齿面接触、强度、寿命或连续时间无碰撞。
