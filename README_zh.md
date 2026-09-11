# KinCheckAPI

[English](README.md) | 简体中文

![四连杆优化前后对比](examples/four_bar_linkage/output/comparison.gif)

*两份实际模型网格使用同一条闭式参考轨迹同步回放。[查看四连杆示例](examples/four_bar_linkage/verification/README_zh.md)。*

KinCheckAPI 读取 CAD 装配关系，建立机构运动模型，运行运动学仿真，并将结果导出为可独立查看的 `.kincheck` 运动包。公开 API 不暴露求解器内部对象；调用者只需操作装配体、工况、运动结果和检查报告。

## 环境要求

- Python >= 3.10
- 在独立环境安装原有仅消费 MJCF 的 API：

```bash
uv venv .venv
uv pip install --python .venv/bin/python .
```

## 插件开发版本：v0.5.3

新增可选 SimpleCADAPI addon，将经过校验的 `.scadpkg` 准备为原有 MJCF 输入。
`convert_mjcf()`、`verify(model_dir)`、装配、工况、求解和检查 API 保持不变。
CLI 修复验证器返回缺失或任意对象时被误判成功的问题。

插件运行时必须安装在与建模隔离的专用环境：

```bash
uv venv --python 3.12 "$HOME/.local/share/kincheckapi/venv"
uv pip install --python "$HOME/.local/share/kincheckapi/venv/bin/python" -e '.[addon]' -e ../CADIR
export PATH="$HOME/.local/share/kincheckapi/venv/bin:$PATH"
kincheck doctor --addon --format json
```

此开发版本配套使用相邻 CADIR 2.1.3b3 源码，修复 MJCF 导出器的 canonical 坐标帧
解码；兼容 SDK 正式发布前请使用这两个源码仓库。
探针失败必须停止并在本环境修复具体依赖。插件目前声明 macOS arm64，
SDK 兼容范围为 `>=2.1.3b3,<2.1.4`。

```bash
python scripts/package_addon.py dist/sca-kincheckapi-0.5.3
sca addon init
sca addon add ./dist/sca-kincheckapi-0.5.3
sca addon list
kincheck verify-package product.scadpkg --work-dir analysis-work --script verification/verify.py --format json
```

skill 安装名称为 `sca-kincheckapi`。产品包命令强制运行时预检，校验源包并将派生资产
保存到独立工作目录，永不修改源包。几何修改交回主 SimpleCADAPI skill 并重新 capture。
标签、单位、坐标系及发布要求见 [插件消费契约](skill_zh/doc/guides/addon-contract.md)。

## 上一版本：v0.5.1

v0.5.1 新增全状态装配体整体性检查：在静态初始姿态或完整 MotionResult 的每个采样中，通过机械关系、容纳或导向关系、几何连接和显式米制连接容差，验证各 Component 始终构成一个有效的连通整体。

近期版本：

- **v0.5.0** 统一面向 Agent 的错误和验证输出：公开错误与结果均提供 `format_for_agent()`，`str()` 输出相同的规范正文，`raise_if_failed()` 将失败转换为同源的 `VerificationError`。结构化字段仍可通过 `to_dict()` 获取。
- **v0.4.1** 移除旧 Artifact 输入路径；转换仅接受 CADIR MJCF、mapping 和网格目录。AssemblyModel → Scenario → `solve_motion()` 及下游行为保持不变。
- **v0.3.1** 统一运动结果、检查和分析的失败语义：`partial` 保留已记录的证据，但不能通过完整性验收；位置与方向残差分别使用米和弧度容差；公开阈值拒绝 NaN、无穷值和非法范围。

详见 [v0.5.1 更新记录](doc/updates/v0.5.1.md)、[运动学验证失败模式矩阵](doc/kinematic-verification-failure-modes.md) 和[可复现失败案例](fail/README.md)。完整历史见 [doc/updates](doc/updates)。

紧凑二级减速器与[四连杆示例](examples/four_bar_linkage/verification/README_zh.md) 统一使用 `verification/`、`model_before/`、`model_after/`、`output/`；建模源码位于各模型目录的 `source/` 中。

## 功能

- 将 CADIR MJCF、mapping 和网格目录读取并验证为不可变的 `AssemblyModel`；
- 表达 Component、Connector、Joint、Ground、传动关系、运动树和 Closure；
- 在调用后端前检查装配引用、拓扑与工况，并返回结构化诊断；
- 使用内置物理后端求解显式工况，返回与后端无关的 `MotionResult`；
- 检查闭环及一般约束残差、传动方程残差、关节限位和实测传动比；
- 计算雅可比、有效自由度、奇异性、可达性和工作空间；
- 检查目标姿态、轨迹和 connector 路径，支持关节锁定；
- 基于真实 STL 网格检查干涉、有符号最小间隙和运动包络；
- 通过 `run_checks()` 统一执行干涉、间隙、包络、传动、限位和轨迹验收；
- 导出、验证和读取包含轨迹与网格的 `.kincheck` 结果包；
- 提供紧凑二级行星减速器和四连杆两个示例。

## 当前边界

- 不保证任意闭环机构都能稳定完成随时间变化的位置求解；模型错误、初态不一致或不支持的机构会明确报错或返回 `partial`，不会伪装为成功；
- `partial` MotionResult 保留已记录的轨迹、残差和几何证据，其中可能包含违反约束的样本，不能据此给出通过结论；
- 几何检查基于显式离散时间点的真实三角网格，不构成连续时间绝对无碰撞证明，也不等价于精确 BREP/NURBS 曲面距离；
- 尚未实现完整动力学、接触力、摩擦和冲击；多自由度关节（`cylindrical`、`spherical`、`planar`、`free`）仍不在后端支持范围内；
- `.scadpkg` 是持久化产品源；可选 addon 校验并准备产品包，再交给原有 MJCF 转换入口，不接受原始 CADIR XML。

## 运行测试

```bash
uv run --extra test pytest -q
```

## CLI 与 Agent Skill

安装 KinCheckAPI 后，所有 Agent 环境共用 `kincheck` 运行时入口：

```bash
kincheck doctor --format json
kincheck validate-model path/to/model --format json
kincheck verify path/to/model --script verification/verify.py --format json
```

`verification/verify.py` 必须公开 `verify(model_dir)`。模型目录必须包含同一次 SimpleCADAPI 构建导出的 `scene.xml`、`scene.mapping.json` 和 `meshes/`。通过 JSON 的 `status`、`issues` 和进程退出码读取验证结果，不要解析自由文本。

生成可安装到 Codex、Gemini、Cursor、OpenCode 或 Claude Code 的 Skill：

```bash
kincheck-skill-pack --language both --archive --adapters --output-root dist
```

输出包括 `kincheckapi.tar.gz`、`kincheckapi-zh.tar.gz`，以及 `dist/adapters/claude-code/`、`codex/`、`gemini/`、`cursor-opencode/` 适配目录。Skill 只包含工作流、公开 API 参考和脚本，不包含 KinCheckAPI 源码；Python 运行时由 `kincheckapi` wheel 提供。

## 示例

紧凑二级行星减速器示例通过仿真时间序列验证传动比：

```bash
uv run python examples/compact_two_stage_planetary_reducer/verification/simulate_and_record.py
```

[四连杆示例](examples/four_bar_linkage/verification/README_zh.md) 包含优化前后模型、对应 STEP 导出和页面顶部的对比动图：

```bash
uv run python examples/four_bar_linkage/verification/simulate_and_record.py
uv run python examples/four_bar_linkage/verification/simulate_before_optimization.py
```

独立查看器可直接回放导出的 `.kincheck` 包，无需重新运行求解器：

```bash
python viewer/kincheck_viewer.py path/to/result.kincheck --serve
```

然后打开 `http://127.0.0.1:8767/`。查看器只读取已记录的网格和轨迹。

## 结果包

`.kincheck` 是 KinCheckAPI 的运动结果格式，包含结果数据和可显示网格，不包含 HTML、JavaScript 或求解器运行时对象。通过 `kincheckapi.export` 写入、验证和读取：

```python
from kincheckapi import export

package = export.motion_package(
    assembly=assembly,
    motion_result=motion_result,
    output_path="result.kincheck",
    asset_root="examples/four_bar_linkage/model_after",
)
loaded = export.read_package(path=package.path)
```
