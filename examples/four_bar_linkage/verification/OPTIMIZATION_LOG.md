# 四连杆优化轨迹

本文档记录 CADIR 四连杆样例从初始模型到当前模型的几何和干涉检查迭代。
机构的运动学拓扑仍然是平面曲柄摇杆；增加 Z 方向层间距只是为了正确表达实体
装配关系，不改变四个铰点的 XY 坐标和闭环拓扑。

## 模型级别和范围

这是一个用于 CAD 和运动学验证的机构模型，包含四个刚性连杆、四个转动接口、
一个闭环约束和可视化转轴硬件。它还不是制造发布级模型，因为当前没有进行轴承
配合、公差叠加、载荷、疲劳和接触压力分析。

优化前失败版的可视化包保存在：
`output/before_optimization/four_bar_linkage_before_optimization.kincheck`

失败版重放脚本为：
`simulate_before_optimization.py`

## 基线：优化前

- 四个连杆实体全部位于同一个 XY/Z 厚度层中。
- 地杆和运动连杆复用了同一个转轴螺栓模型。
- 导出的 mapping 没有声明碰撞检查策略。
- 运动学拓扑有效：4 个组件、4 个转动关节、1 个闭环。
- 装配求解残差在容差内，真实 CADIR 求解的最大残差约为 `1.64e-14 m`。
- 一整圈干涉检查使用 301 个样本、检查 6 对组件，得到 1,358 个事件，最大
  穿透深度约为 `0.600000 mm`。

结论：闭环方程本身是正确的，但不同连杆和转轴硬件被建在同一实体层中，导致
真实的实体重叠。这不是把数值容差调大就能合理解决的问题。

## 第 1 轮：抬高地杆桥架

### 修改内容

`link_bar.py` 增加了几何 Z 偏移参数。地杆实体被抬高，但连接器原点仍然保持在
公共转动轴上。目标是在不改变 A/D 两个铰点坐标的前提下，让地杆桥架避开耦合杆
的运动区域。

### 验证内容

- 重新构建并捕获 `four_bar_linkage.scadpkg`。
- 重新导出 `four_bar_linkage.xml` 和 mapping。
- 装配求解仍报告 `components=8`、`constraints=8`、`residuals_ok=True`。
- 地杆桥架造成的部分事件减少，但 A 点转轴螺栓仍会在耦合杆经过 A 点时发生
  重叠。

这说明剩余问题来自转轴硬件和层间堆叠，而不是地杆长梁本身。

## 第 2 轮：分离层间结构和螺栓类型

### 修改内容

- 地杆实体使用 `+5.0 mm` 的局部 Z 偏移，网格范围约为 `3..7 mm`。
- 耦合杆实体使用 `-5.0 mm` 的局部 Z 偏移，网格范围约为 `-7..-3 mm`。
- 曲柄和摇杆保持在中间层，网格范围约为 `-2..2 mm`。
- 地杆两个固定转轴使用独立的短螺栓，螺栓长度为 `7 mm`。
- 运动转轴继续使用 `11 mm` 长螺栓，只跨过运动连杆所在的层。
- 四个真实的销轴/轴眼接口写入 `collision_policy.py`，并导出到 MJCF mapping
  的 `collision_exclusions`。
- 非相邻的 `ground-coupler` 组件对没有被排除，仍保留为真实碰撞回归检查。
- 原来的 `(-30°, 30°)` 闭合角范围只保留为初始姿态搜索提示，不再作为运行时
  revolute 限位。该机构是 Grashof 曲柄摇杆，曲柄应允许完整旋转。

### 验证代码

完整重放代码位于：
`examples/four_bar_linkage/verification/simulate_and_record.py`

脚本按以下顺序执行：

1. 通过 `convert_mjcf()` 转换 MJCF 和 mapping。
2. 调用原生、无驱动的 `solve_motion()`，作为集成冒烟测试。
3. 额外执行一次原生速度驱动整圈探测，并单独记录其结果，避免把 `partial`
   结果误认为通过。
4. 使用精确的圆相交闭式公式生成一整圈、301 个采样点的轨迹。
5. 导出 `.kincheck` 并重新读回验证。
6. 分别执行不应用接口排除策略和应用接口排除策略的干涉检查，并单独检查
   非相邻组件对。

### 最终运行命令

```text
python examples/four_bar_linkage/verification/simulate_and_record.py
```

结构化证据文件：
`examples/four_bar_linkage/output/after/four_bar_linkage.optimization.json`

### 最终验证结果

| 检查项 | 结果 |
| --- | --- |
| 原生无驱动求解 | `completed`，3 个样本，无错误 |
| 原生速度驱动整圈探测 | `partial`，错误为 `KINCHECK-CLOSURE-RESIDUAL-EXCEEDED` |
| 闭式闭环轨迹 | `completed`，301 个样本 |
| 闭式轨迹最大闭环位置残差 | `0.0 m` |
| 优化后、不应用接口排除的全量检查 | 6 对组件、301 个样本、0 个事件，通过 |
| 优化后、应用接口排除后的检查 | 剩余 2 对组件、301 个样本、0 个事件，通过 |
| 非相邻碰撞回归：`ground-coupler`、`crank-rocker` | 0 个事件，通过 |
| `.kincheck` 运动包 | 约 133K，SHA-256 已写入证据 JSON |

原生速度驱动探测仍然明确暴露当前后端边界：通用闭环求解器在 MJCF 模型上执行
整圈速度驱动时无法稳定闭合，因此返回 `partial`。干涉检查使用的是代码中明确
记录、采样数明确的精确闭式轨迹，不把原生 `partial` 结果包装成通过。

## 重现顺序

```text
python examples/four_bar_linkage/model_after/source/main.py
python examples/four_bar_linkage/model_after/source/export_mjcf.py
python examples/four_bar_linkage/verification/simulate_and_record.py
```

前两个命令重新生成规范 `.scadpkg`、MJCF、mapping 和网格；第三个命令重新生成
`.kincheck` 运动包和结构化优化证据。
