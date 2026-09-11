# 四连杆优化前后对比

[English](README.md) | 简体中文

![四连杆优化前后对比](../output/comparison.gif)

*两份实际模型网格使用同一条闭式参考轨迹同步回放。*

示例根目录只保留四个文件夹：

```text
four_bar_linkage/
├── verification/             # 验证、STEP 导出、动图生成脚本和说明
├── model_before/             # 优化前模型：MJCF、mapping、网格、scadpkg、source/
├── model_after/              # 优化后模型：MJCF、mapping、网格、scadpkg、source/
└── output/
    ├── four_bar_before.step  # 优化前完整装配体，AP242
    ├── four_bar_after.step   # 优化后完整装配体，AP242
    ├── comparison.gif        # 同视角、同比例、同步运动对比
    ├── comparison.png        # 对比首帧
    ├── step_export.json      # STEP 导出和重新读取检查
    ├── before/               # 优化前运动包、验证证据和截图
    └── after/                # 优化后运动包、验证证据和截图
```

两个模型的几何和装配关系保持不变：优化前保留同层杆件及原销轴布局；优化后保留轴向错层、
调整后的销轴和显式接口排除策略。模型目录内的 `source/` 是各自的可编辑建模源码，
`four_bar_linkage.scadpkg` 是现有模型的完整 CAD 包，MJCF 和网格是对应的运动验证输入。
STEP 来自这两份 CAD 包；重新读取后均应有效，并包含 8 个实体（4 根杆、4 个销轴）。

## 验证与运行

从 KinCheckAPI 仓库根目录运行，两个脚本也支持从其他工作目录以绝对路径启动：

```bash
.venv/bin/python examples/four_bar_linkage/verification/simulate_and_record.py
.venv/bin/python examples/four_bar_linkage/verification/simulate_before_optimization.py
```

- `simulate_and_record.py`：读取优化后模型 → 原生无驱动与整圈求解 → 参考轨迹导出和读回
  → 三组干涉检查 → 写入 `output/after/four_bar_linkage.optimization.json`。
- `simulate_before_optimization.py`：读取优化前模型，使用同一参考轨迹检查干涉，写入
  `output/before/four_bar_linkage.before_optimization.json`。
- `four_bar_reference.py`：保存两圆交点、姿态转换、数值求导和参考轨迹构造函数。
- `test/convert_mjcf_to_assemblymodel.py`：独立检查优化后模型的转换与稳定对象 ID。
- `OPTIMIZATION_LOG.md`：模型优化的历史记录。

预期结果：优化后原生整圈求解 `completed`，参考轨迹 301 帧的干涉事件数为 0；
优化前仍为预期失败，6 对组件、301 帧、1358 个干涉事件，最大穿透深度约 0.600000 mm。
验证范围、驱动、采样、结果字段和参考算法保持原有含义，文件路径随上述目录调整。

这些是案例记录脚本；原生轨迹用于记录闭合误差和曲柄转角，参考轨迹用于运动包与干涉检查。
参考轨迹中的零残差是构造值，不能当作求解器测量证据。独立、严格的 `verify(model_dir)`
教程见 [Skill 标准骨架](../../../skill_zh/SKILL.md) 和
[验证程序流程](../../../skill_zh/doc/guides/verification-procedure.md)。

## STEP 和对比动图

在安装有 SimpleCADAPI/OpenCASCADE 的 Python 环境中导出 STEP：

```bash
python examples/four_bar_linkage/verification/export_steps.py
```

先运行两个验证脚本，再在安装有 VTK、NumPy、Pillow 和中文字体的环境中生成动图：

```bash
python examples/four_bar_linkage/verification/render_comparison.py
```

`--preview` 仅生成首帧 PNG。完整 GIF 为 1200 × 660、100 帧、10 秒循环，
渲染两份运动包内的实际网格，用相同视角和比例播放同一条闭式参考轨迹。
图上的干涉事件数来自 301 帧验证报告；GIF 本身不是连续时间无碰撞证明。

## 重新构建模型（可选）

现有 CAD 包可直接导出 STEP，不需要重建。需要改变几何时，分别使用两个模型的源码入口；
在兼容这些源文件的 SimpleCADAPI 环境中执行：

```bash
python examples/four_bar_linkage/model_before/source/main.py
python examples/four_bar_linkage/model_before/source/export_mjcf.py
python examples/four_bar_linkage/model_after/source/main.py
python examples/four_bar_linkage/model_after/source/export_mjcf.py
```

每个入口把 CAD 包和 MJCF 导出到自己的 `model_before/` 或 `model_after/`，随后重新运行验证、
STEP 导出和动图生成。建模脚本只调整了目录定位，几何构建逻辑保持原样。

## 查看运动包

```bash
.venv/bin/python viewer/kincheck_viewer.py \
  examples/four_bar_linkage/output/after/four_bar_linkage_full_cycle.kincheck --serve
.venv/bin/python viewer/kincheck_viewer.py \
  examples/four_bar_linkage/output/before/four_bar_linkage_before_optimization.kincheck --serve --port 8768
```

### 原生闭环求解参数调整（v0.5.1）

含 `Closure` 的模型使用 0.02 ms 最大内部积分步长（原为 0.5 ms），
200 次求解迭代上限（原为 100 次），并将闭合点、闭合轴线和固定闭合的
软约束统一设置为 `solref="0.0001 1"`、`solimp="0.9999 0.9999 0.001"`。
0.1 ms 的响应时间常数与临界阻尼配合，每个时间常数至少分为五个积分步。
这些参数遵循 [MuJoCo 的约束参数定义](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters)。
无闭环模型仍使用原步长和迭代上限；输出采样周期由 Scenario 独立控制。

在 MuJoCo 3.11.0 上，以 `2π/10 rad/s` 驱动本案例 10 秒、每 0.01 秒采样：
原参数返回 `partial`，最大闭合位置残差约 `5.95e-4 m`；调整后返回 `completed`，
采样最大残差约 `3.94e-11 m`，实际曲柄转角约 `6.283154 rad`。
另将最初 0.005 秒按每个 0.02 ms 积分步采样，最大启动残差约 `4.77e-7 m`，
低于 `1e-6 m` 容差。整圈的稀疏采样最大值不代表内部步的最大值。
运行上面的仿真脚本可在 `native_driven_probe` 中读取本机结果；脚本的默认输出
采样周期是 0.1 秒，因此采样最大值可能与上述 0.01 秒对照不同。

内部积分步数约增至原来的 25 倍，闭环仿真耗时会增加；启用
`set_capture_integration_steps()` 时，保存的内部位姿数据也会增加。
仍使用 MuJoCo 软约束，原定闭合容差和 `partial` 判定保持不变。
高速、突变驱动或更严格的容差仍可能超标，不能以动画连续或采样通过推断全过程通过。
本案例继续保留独立闭式轨迹，作为完整一圈几何验证的可复现基准。

需要平滑启停时，可通过现有 API 显式声明速度斜坡，例如：

```python
condition = scenario.add_joint_speed_profile(
    scenario=condition,
    joint_id=CRANK_JOINT,
    profile=[(0.0, 0.0), (0.1, 0.5), (0.9, 0.5), (1.0, 0.0)],
)
```

该曲线一秒内的目标转角为 0.45 rad。后端保持调用者给定的驱动曲线，
不会自动降低速度、延长时长或加入启动斜坡。
