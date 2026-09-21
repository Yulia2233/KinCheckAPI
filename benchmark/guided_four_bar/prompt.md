# Benchmark Case：Guided Four-Bar Actuator Prompt

下面正文直接作为建模 Agent 的输入。Agent 只需要依据它生成一个可编辑的 SimpleCADAPI/CADIR 源和最终 `.scadpkg`；评测端会在独立环境中把 package 接到固定的 KinCheckAPI 仿真验证流程。不要生成验证脚本，也不要修改现有 `examples/guided_four_bar_actuator`。

## Part/Component contract

| Part/Component name | Naming | Geometry description |
| --- | --- | --- |
| Machined base plate / ground housing | `assembly_id=guided_four_bar_actuator`; `definition_id=base`; `component_id=base`; connectors `pivot_a`, `pivot_d`, `guard_mount` | CAD 单位 mm；矩形底板 76×42×8，底面中心 `(20,0,-12)`；四个安装孔半径2.25、贯穿12，孔中心 `x∈{0,40}`, `y∈{-15,15}`；两个 pivot boss 半径8、高7，中心 x=0 和40；boss bore 半径2.2，沿 Z 贯穿；底座作为 ground，不能悬空 |
| Crank link | `definition_id=crank`; `component_id=crank`; connectors `pivot_a`, `pivot_b` | pivot center distance 20；两端 bearing eye 外半径5、孔半径2.30；实体厚4；I-beam web/flanges；两处 lightening holes 半径2.2；装配在下层中心 Z=5，零位沿 +X；孔轴与公共 Z 轴平行 |
| Coupler link | `definition_id=coupler`; `component_id=coupler`; connectors `pivot_a`, `pivot_b` | pivot center distance 50；与 crank 同类的 forged link、眼孔、web/flanges 和 lightening holes；装配在上层中心 Z=10，与下层 link 保持约1 mm 轴向间隔；必须是单一实体并与其他运动件分离 |
| Rocker link | `definition_id=rocker`; `component_id=rocker`; connectors `pivot_a`, `pivot_b` | pivot center distance 35；与 crank 同类的 forged link、孔半径2.30、厚4 和 lightening holes；装配在下层中心 Z=5，ground pivot D=(40,0,0) |
| Ground pivot pins ×2 | `definition_id=ground_pin`; occurrence IDs `pin_a`, `pin_d`; connector `axis`; host `base` | 每个是独立六角头销轴：shaft 半径2、头部外半径3.4、头厚2.4、座肩真实落在 base boss；pin_a 在 A=(0,0)，pin_d 在 D=(40,0)；两个 occurrence 分别计数，不能按 definition 合并 |
| Moving pivot pins ×2 | `definition_id=link_pin`; occurrence IDs `pin_b`, `pin_c`; connector `axis`; hosts `crank`、`rocker` | 每个是独立六角头销轴、shank、shoulder 和 host seating collar；pin_b 位于 crank 的 B，pin_c 位于 rocker 的 C；两个销轴必须真实固定到宿主 link，不能浮在孔中 |
| Fixed service guard | `definition_id=guard`; `component_id=guard`; connector `mount`; host `base` | guard rail 64×3×14，bottom face center `(18,-18,-6)`；两根5×5×20 posts；service window 50×5×10；整体抬高4 mm 后固定到 base；运动件全程应避让护罩，护罩不能嵌入 base |

## Naming and assembly requirements

使用上表中的 ID，不要改成同义词：`base`、`crank`、`coupler`、`rocker`、`ground_pin`、`link_pin`、`guard`、`pin_a`、`pin_b`、`pin_c`、`pin_d`。装配根名为 `guided_four_bar_actuator`。

以下 Name Registry 是强制接口，所有字符串必须原样写入 assembly graph：

```text
assembly_id: guided_four_bar_actuator
root_component_id: node/guided_four_bar_actuator
definition_ids: base, crank, coupler, rocker, ground_pin, link_pin, guard
occurrence/component_ids: base, crank, coupler, rocker, guard, pin_a, pin_b, pin_c, pin_d
connector_ids_by_part:
  base: pivot_a, pivot_d, guard_mount
  crank: pivot_a, pivot_b
  coupler: pivot_a, pivot_b
  rocker: pivot_a, pivot_b
  ground_pin: axis
  link_pin: axis
  guard: mount
fixed_constraint_ids: guard_to_base, pin_a_fixed, pin_b_fixed, pin_c_fixed, pin_d_fixed
revolute_joint_ids: crank_to_ground, coupler_to_crank, rocker_to_ground
closure_joint_id: coupler_to_rocker
public_connector_ids: crank_input_axis
material_ids: actuator_steel, actuator_pin
density_unit: kg/mm^3
```

两个材料的演示密度均为 `7.85e-6 kg/mm^3`。不得改成 `g/cm3`，也不得把 `crank_to_ground` 改成 `base_crank` 或把 `coupler_to_crank` 改成 `crank_coupler`。

所有 connector 的原点必须落在真实 pivot 轴线或安装面上，四个 revolute 轴平行于 Z。`base` 是 ground；`guard`、`pin_a`、`pin_d` 固定到 base；`pin_b` 固定到 crank；`pin_c` 固定到 rocker。四杆连接为：crank 与 base、rocker 与 base、coupler 与 crank、coupler 与 rocker。每一个 occurrence 都必须通过真实 fixed/revolute 关系连接到 base，不能用只存在于文档里的连接。

## 要求

采用右手世界坐标：XY 是机构平面，Z 是所有转轴方向，A 为 ground pivot 和 assembly 原点；CAD 长度使用 mm。ground span A–D=40 mm，crank A–B=20 mm，coupler B–C=50 mm，rocker D–C=35 mm。闭合基准姿态为 crank 沿 +X，B=(20,0)，C=(61.875,27.322) mm。该长度组合应形成完整 crank-rocker 闭环，不能把 coupler 端点做成与 crank 无关的固定点。

初始 crank position=0 rad，crank 的零位是从 A 指向 +X。crank 和 rocker 的允许角范围为 −45° 到 85°；coupler 的安装姿态由四杆闭环求得。link 层之间保留约1 mm 轴向间隔，销轴与孔保留可建模的径向间隙，guard 与运动包络保持安全间隙。正常运动中不应发生非预期实体干涉，也不能出现任何悬空 pin、guard 或 link。

运动要求：crank 在前0.2 s 保持静止，从0.2 s 到1.8 s 以 **0.8 rad/s 匀速旋转**，最后0.2 s 平稳停止；总运动时长2.0 s。coupler 和 rocker 必须通过真实四杆约束随动，不能把它们的位置逐时刻写死。要求闭环持续成立、crank 能稳定跟踪给定速度、rocker 的角速度不超过0.7 rad/s、角加速度不超过1.0 rad/s²，并且在整个运动范围内不撞击 base、guard、pin 或其他 link。

如果需要表达传动目标，使用“输入对象—输出对象—方向—数值—单位”的形式。例如：`crank` 为输入，`rocker` 为输出，正方向均按 +Z 轴看逆时针，目标是保持闭环运动并得到连续输出摆动；不要把输出角度列表硬编码进模型。


请使用 SimpleCADAPI skill，从源文件 capture 一个 canonical package：

```text
<output>/guided_four_bar_actuator.scadpkg
```

package 内必须包含完整 assembly graph、七种 part definition、九个物理 occurrence、材料密度、connector、fixed/revolute 关系、ground 信息、feature/topology 数据和稳定 revision。只交付 `.scadpkg` 路径与构建日志。
