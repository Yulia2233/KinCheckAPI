# Benchmark Case：Dynamics XYZ Direct-Drive Pick-and-Place Gantry Prompt

下面正文直接作为建模 Agent 的输入。Agent 只需要依据它生成可编辑的 SimpleCADAPI/CADIR 源和最终 `.scadpkg`；评测端会从 package 独立重建三轴机构、物性和有限驱动工况。不要生成验证脚本，不要修改评测端文件。

## Part/Component contract

| Part/Component name | Naming | Geometry description |
| --- | --- | --- |
| Gantry ground frame | `assembly_id=xyz_pick_place_gantry`; `definition_id=base_frame`; `component_id=base_frame`; connectors `mount_1`…`mount_8`, `x_rail_left_mount`, `x_rail_right_mount`, `x_motion_origin`, `x_stator_mount`, `guard_mount` | CAD 使用 mm；800×500×20 的机加工底座，X 范围 0…800、Y 范围 −250…250、Z=0…20；八个 Ø11 安装孔与环境安装面连接；所有导轨和护罩真实落座，base_frame 是唯一 ground |
| X-axis rails and carriage | `definition_id=x_rail`; occurrence IDs `x_rail_left`, `x_rail_right`; connectors `mount_1`…`mount_6`, `contact_left`, `contact_right`; `definition_id=x_carriage`; `component_id=x_carriage`; connectors `guide_left`, `guide_right`, `contact_left_front`, `contact_left_rear`, `contact_right_front`, `contact_right_rear`, `y_bridge_mount`, `x_axis` | 两条平行 X 导轨中心 Y=−180 和 +180，长度620、截面30×30、顶面 Z=50；每条有六个真实固定孔和两个连续导向接触面；x_carriage 是150×420×35跨轨滑台，四个滑块座与导轨实体接触，home 中心 X=400 mm；X 行程300…680 mm，不能脱轨或悬空 |
| X direct-drive linear motor | `definition_id=x_motor_stator`; `component_id=x_motor_stator`; connectors `mount_1`…`mount_4`, `axis`; `definition_id=x_motor_forcer`; `component_id=x_motor_forcer`; connectors `axis`, `carriage_mount` | 定子外壳固定在 base_frame 右端安装架；forcer 是独立实体并固定在 x_carriage；两者同轴、平行于 X，具有真实安装孔、端盖、导向间隙和有限直线驱动接口；不使用同步带、皮带齿或隐藏传动件 |
| Y bridge and carriage | `definition_id=y_bridge`; `component_id=y_bridge`; connectors `x_mount_left`, `x_mount_right`, `y_rail_front`, `y_rail_rear`, `y_axis_origin`, `y_stator_mount`; `definition_id=y_rail`; occurrence IDs `y_rail_front`, `y_rail_rear`; connectors `contact_front`, `contact_rear`; `definition_id=y_carriage`; `component_id=y_carriage`; connectors `guide_front`, `guide_rear`, `contact_front_a`, `contact_front_b`, `contact_rear_a`, `contact_rear_b`, `z_column_mount`, `y_axis` | y_bridge 是620×100×70铝合金横梁，固定在 x_carriage 上；两条 Y 导轨长度500、中心间距120、截面25×25，固定在横梁顶面；每条导轨有六个真实安装孔；y_carriage 是140×120×35双滑块台，四个实体导向块落在导轨上，z_column 固定在其中心；Y 行程−150…150 mm |
| Y direct-drive linear motor | `definition_id=y_motor_stator`; `component_id=y_motor_stator`; connectors `mount_1`…`mount_4`, `axis`; `definition_id=y_motor_forcer`; `component_id=y_motor_forcer`; connectors `axis`, `carriage_mount` | 定子固定在 y_bridge 端部；forcer 固定在 y_carriage；轴线沿 Y，定子与 forcer 之间保持制造间隙；驱动直接作用在 y_carriage，不使用皮带或丝杠 |
| Z column and carriage | `definition_id=z_column`; `component_id=z_column`; connectors `y_mount`, `z_rail_left`, `z_rail_right`, `z_axis`; `definition_id=z_rail`; occurrence IDs `z_rail_left`, `z_rail_right`; connectors `contact_left`, `contact_right`; `definition_id=z_carriage`; `component_id=z_carriage`; connectors `guide_left`, `guide_right`, `contact_left_upper`, `contact_left_lower`, `contact_right_upper`, `contact_right_lower`, `tool_mount`, `z_axis` | z_column 是100×100×360立柱，固定在 y_carriage 中央；两条 Z 导轨长度300、间距50、截面25×25，从 Z=230 延伸到530；z_carriage 是120×120×65升降块，四个实体滑块座分别包住两条导轨；Z 行程80…300 mm；上下端有实体 end stop，不能超出导轨 |
| Z direct-drive linear motor | `definition_id=z_motor_stator`; `component_id=z_motor_stator`; connectors `mount_1`…`mount_4`, `axis`; `definition_id=z_motor_forcer`; `component_id=z_motor_forcer`; connectors `axis`, `carriage_mount` | 定子固定在 z_column 顶部；forcer 固定在 z_carriage；轴线沿 Z；两者包含真实端盖、安装孔和导向间隙；驱动直接作用在 z_carriage，不使用滚珠丝杠、螺纹或隐藏传动 |
| Tool plate and payload | `definition_id=tool_plate`; `component_id=tool_plate`; connectors `z_mount`, `payload_mount`, `tool_center`, `contact_payload`, `load`; `definition_id=payload`; `component_id=payload`; connectors `mount_1`…`mount_4`, `payload_center`, `contact_tool`, `load` | tool_plate 为160×120×12铝板，固定在 z_carriage；四个 Ø9 安装孔与 payload 底座同轴；tool_plate 与 payload 的真实落座面是 `interface.contact.payload_support`；payload 是带圆角和四个安装孔的钢制箱体，实体质量5.000 kg ±0.1%，质心位于实体中心；`tool_center` 在 home 时世界位置为 `(655,0,477) mm` |
| Cable carrier bracket and protective enclosure | `definition_id=cable_carrier_bracket`; `component_id=cable_carrier_bracket`; connectors `base_mount`, `x_mount`, `y_mount`, `z_mount`; `definition_id=guard`; `component_id=guard`; connectors `mount_1`…`mount_8`, `base_mount`, `service_door`, `clearance` | cable_carrier_bracket 是固定在 base_frame 中央安装面的刚性支架集合，负责静态电缆导向并与运动包络保持间隙，不建模柔性链节；guard 包含底部围栏、顶部护罩、四个检修门和透明窗口，距三轴运动包络至少50 mm；所有支架和护罩必须有真实安装孔 |
| Rail, motor, guard and payload fasteners | `definition_id=m8_bolt`; occurrence IDs `base_bolt_1`…`base_bolt_8`, `x_rail_left_bolt_1`…`x_rail_left_bolt_6`, `x_rail_right_bolt_1`…`x_rail_right_bolt_6`, `guard_bolt_1`…`guard_bolt_8`; `definition_id=m6_bolt`; occurrence IDs `y_rail_front_bolt_1`…`y_rail_front_bolt_6`, `y_rail_rear_bolt_1`…`y_rail_rear_bolt_6`, `payload_bolt_1`…`payload_bolt_4` | 每个螺栓是独立实体，含头部、杆部、垫圈/座面和明确啮合深度；所有 occurrence 逐个穿过真实孔并固定 host；不能写成“若干螺栓”，也不能让螺钉穿过运动导轨或 payload |

## Naming and assembly requirements

以下 ID 是固定接口，不能改写同义词、添加随机 hash 或使用位置坐标命名。相同 definition 的重复导轨、滑块、直线电机和螺栓仍必须按 occurrence 保留。

```text
assembly_id: xyz_pick_place_gantry
root_component_id: node/xyz_pick_place_gantry
definition_ids: base_frame, x_rail, x_carriage, x_motor_stator, x_motor_forcer, y_bridge, y_rail, y_carriage, y_motor_stator, y_motor_forcer, z_column, z_rail, z_carriage, z_motor_stator, z_motor_forcer, tool_plate, payload, cable_carrier_bracket, guard, m8_bolt, m6_bolt
occurrence/component_ids: base_frame, x_rail_left, x_rail_right, x_carriage, x_motor_stator, x_motor_forcer, y_bridge, y_rail_front, y_rail_rear, y_carriage, y_motor_stator, y_motor_forcer, z_column, z_rail_left, z_rail_right, z_carriage, z_motor_stator, z_motor_forcer, tool_plate, payload, cable_carrier_bracket, guard, base_bolt_1, base_bolt_2, base_bolt_3, base_bolt_4, base_bolt_5, base_bolt_6, base_bolt_7, base_bolt_8, x_rail_left_bolt_1, x_rail_left_bolt_2, x_rail_left_bolt_3, x_rail_left_bolt_4, x_rail_left_bolt_5, x_rail_left_bolt_6, x_rail_right_bolt_1, x_rail_right_bolt_2, x_rail_right_bolt_3, x_rail_right_bolt_4, x_rail_right_bolt_5, x_rail_right_bolt_6, y_rail_front_bolt_1, y_rail_front_bolt_2, y_rail_front_bolt_3, y_rail_front_bolt_4, y_rail_front_bolt_5, y_rail_front_bolt_6, y_rail_rear_bolt_1, y_rail_rear_bolt_2, y_rail_rear_bolt_3, y_rail_rear_bolt_4, y_rail_rear_bolt_5, y_rail_rear_bolt_6, guard_bolt_1, guard_bolt_2, guard_bolt_3, guard_bolt_4, guard_bolt_5, guard_bolt_6, guard_bolt_7, guard_bolt_8, payload_bolt_1, payload_bolt_2, payload_bolt_3, payload_bolt_4
connector_ids_by_part:
  base_frame: mount_1, mount_2, mount_3, mount_4, mount_5, mount_6, mount_7, mount_8, x_rail_left_mount, x_rail_right_mount, x_motion_origin, x_stator_mount, guard_mount
  x_rail: mount_1, mount_2, mount_3, mount_4, mount_5, mount_6, contact_left, contact_right
  x_carriage: guide_left, guide_right, contact_left_front, contact_left_rear, contact_right_front, contact_right_rear, y_bridge_mount, x_axis
  x_motor_stator: mount_1, mount_2, mount_3, mount_4, axis
  x_motor_forcer: axis, carriage_mount
  y_bridge: x_mount_left, x_mount_right, y_rail_front, y_rail_rear, y_axis_origin, y_stator_mount
  y_rail: mount_1, mount_2, mount_3, mount_4, mount_5, mount_6, contact_front, contact_rear
  y_carriage: guide_front, guide_rear, contact_front_a, contact_front_b, contact_rear_a, contact_rear_b, z_column_mount, y_axis
  y_motor_stator: mount_1, mount_2, mount_3, mount_4, axis
  y_motor_forcer: axis, carriage_mount
  z_column: y_mount, z_rail_left, z_rail_right, z_axis
  z_rail: mount_top, mount_bottom, contact_left, contact_right
  z_carriage: guide_left, guide_right, contact_left_upper, contact_left_lower, contact_right_upper, contact_right_lower, tool_mount, z_axis
  z_motor_stator: mount_1, mount_2, mount_3, mount_4, axis
  z_motor_forcer: axis, carriage_mount
  tool_plate: z_mount, payload_mount, tool_center, contact_payload, load
  payload: mount_1, mount_2, mount_3, mount_4, payload_center, contact_tool, load
  cable_carrier_bracket: base_mount, x_mount, y_mount, z_mount
  guard: mount_1, mount_2, mount_3, mount_4, mount_5, mount_6, mount_7, mount_8, base_mount, service_door, clearance
fixed_constraint_ids: y_bridge_to_x_carriage, x_rail_left_to_base, x_rail_right_to_base, x_motor_stator_to_base, x_motor_forcer_to_x_carriage, y_rail_front_to_bridge, y_rail_rear_to_bridge, y_motor_stator_to_bridge, y_motor_forcer_to_y_carriage, z_column_to_y_carriage, z_rail_left_to_column, z_rail_right_to_column, z_motor_stator_to_column, z_motor_forcer_to_z_carriage, tool_plate_to_z_carriage, payload_to_tool_plate, cable_carrier_bracket_to_hosts, guard_to_base, base_bolt_1_fixed, base_bolt_2_fixed, base_bolt_3_fixed, base_bolt_4_fixed, base_bolt_5_fixed, base_bolt_6_fixed, base_bolt_7_fixed, base_bolt_8_fixed, x_rail_left_bolt_1_fixed, x_rail_left_bolt_2_fixed, x_rail_left_bolt_3_fixed, x_rail_left_bolt_4_fixed, x_rail_left_bolt_5_fixed, x_rail_left_bolt_6_fixed, x_rail_right_bolt_1_fixed, x_rail_right_bolt_2_fixed, x_rail_right_bolt_3_fixed, x_rail_right_bolt_4_fixed, x_rail_right_bolt_5_fixed, x_rail_right_bolt_6_fixed, y_rail_front_bolt_1_fixed, y_rail_front_bolt_2_fixed, y_rail_front_bolt_3_fixed, y_rail_front_bolt_4_fixed, y_rail_front_bolt_5_fixed, y_rail_front_bolt_6_fixed, y_rail_rear_bolt_1_fixed, y_rail_rear_bolt_2_fixed, y_rail_rear_bolt_3_fixed, y_rail_rear_bolt_4_fixed, y_rail_rear_bolt_5_fixed, y_rail_rear_bolt_6_fixed, guard_bolt_1_fixed, guard_bolt_2_fixed, guard_bolt_3_fixed, guard_bolt_4_fixed, guard_bolt_5_fixed, guard_bolt_6_fixed, guard_bolt_7_fixed, guard_bolt_8_fixed, payload_bolt_1_fixed, payload_bolt_2_fixed, payload_bolt_3_fixed, payload_bolt_4_fixed
prismatic_joint_ids: x_carriage_to_base, y_carriage_to_y_bridge, z_carriage_to_y_bridge
closure_joint_id: none
public_connector_ids: x_axis, y_axis, z_axis, tool_center, payload_center
interface_tags: interface.mount, interface.guide.x_left_front, interface.guide.x_left_rear, interface.guide.x_right_front, interface.guide.x_right_rear, interface.guide.y_front_a, interface.guide.y_front_b, interface.guide.y_rear_a, interface.guide.y_rear_b, interface.guide.z_left_upper, interface.guide.z_left_lower, interface.guide.z_right_upper, interface.guide.z_right_lower, interface.contact.payload_support, interface.contact.x_guide_envelope, interface.contact.y_guide_envelope, interface.contact.z_guide_envelope, interface.axis, interface.fastener, interface.drive, interface.load, interface.guard
material_ids: gantry_steel, gantry_aluminum, payload_steel, bearing_polymer
density_unit: kg/mm^3
```

`base_frame` 是唯一 ground。两条 X 导轨和 X motor stator 固定到 base；y_bridge 固定在 x_carriage 上；y_carriage 沿 Y 导轨运动；两条 Y 导轨和 Y motor stator 固定到 y_bridge；z_column 固定在 y_carriage 上；两条 Z 导轨和 Z motor stator 固定到 z_column；三个 motor forcer 分别固定在对应 carriage；tool_plate、payload、cable_carrier_bracket 和 guard 通过固定关系连接到相应宿主。三个可动关节分别是 X、Y、Z 直线轴，不得用闭环约束、悬空 marker 或隐藏自由度代替导向结构。

所有材料必须显式给出 `density_unit`：`gantry_steel=7.85e-6 kg/mm^3`、`gantry_aluminum=2.70e-6 kg/mm^3`、`payload_steel=7.85e-6 kg/mm^3`、`bearing_polymer=1.10e-6 kg/mm^3`。每个实体的密度、实体体积、质心和惯量都必须可从 package 追溯；不得使用 `g/cm3`、空壳、贴图或隐藏点质量。

## 工况

采用右手世界坐标，CAD 长度使用 mm，运动和动力学使用 SI。X 是横向长轴，Y 是桥架横向，Z 竖直向上；重力为 `(0,0,-9.81) m/s²`。三轴 home 位置为 `(x,y,z)=(655,0,477) mm`，工作范围为 X=300…680 mm、Y=−150…150 mm、Z=80…550 mm。每个 prismatic joint 的正方向分别为 +X、+Y、+Z；初始速度和加速度为0。

payload 的额定质量为5.000 kg，必须在所有工况中计入；tool_plate、z_carriage、三个 motor forcer 和 cable_carrier_bracket 随各自 carriage 运动，不能只计算 payload。所有导轨、滑块、直线电机、护罩和紧固件都是实体，且每个非 ground occurrence 必须有到 base_frame 的真实固定或运动连接链。

正常搬运工况如下：

1. **静载**：三轴保持 home，payload 承受重力；再分别取 X=400 mm、Y=0 mm、Z=180 mm 和 X=650 mm、Y=120 mm、Z=80 mm 两个偏置姿态，确认所有 guide、mount 和固定件仍连接且没有悬空。
2. **有限驱动运动**：X、Y、Z 三轴由独立有限直线电机驱动，驱动力 profile 由验证工况冻结；所有 profile 必须在开始和结束处有限，并且实际位置不越过各自行程。机构必须记录完整的三轴位置、速度和加速度样本。
3. **单轴加速**：X 轴最大速度0.8 m/s、最大加速度2.0 m/s²；Y 轴最大速度0.6 m/s、最大加速度2.0 m/s²；Z 轴最大速度0.3 m/s、最大加速度1.0 m/s²。有限驱动导致的实际响应必须保留，不能把目标位置直接写入结果。
4. **协调工作区**：payload 的工具中心应留在 X=300…680 mm、Y=−150…150 mm、Z=80…550 mm 内，三轴同时运动时不得出现悬空、导轨脱离、越限或姿态漂移。当前 benchmark 只声称标量轴状态和工作区范围，不声称笛卡尔轨迹跟踪器。
5. **驱动系统**：X、Y、Z 执行器额定力分别为180 N、150 N、300 N，效率为0.90；允许短时达到额定值的1.5倍。执行器不能使用无限力、瞬时无穷加速度或未建模的外部能量。
6. **几何安全**：正常记录轨迹全程不得发生非预期实体干涉；自由运动面最小间隙至少0.20 mm，guard 与运动包络至少50 mm；滑块、直线电机、螺栓和护罩不能穿入其他运动件。功能接触只允许发生在明确的 guide/end-stop 面，其他零件之间不能依靠碰撞维持运动。

四个设计接触容量输入必须明确：`payload_support` 法向 +Z、允许压力0.20 MPa；`x_guide_envelope`、`y_guide_envelope`、`z_guide_envelope` 分别代表三轴导向的整体设计载荷包络，不能解释成单个滑块的实际反力。当前 verifier 会对这些给定外力运行接触/摩擦容量检查，但不声称反力分配、柔顺接触、急停距离、结构应力、变形、振动或疲劳。

请使用 SimpleCADAPI skill，从源文件 capture 一个 canonical package：

```text
<output>/xyz_pick_place_gantry.scadpkg
```

package 内必须包含完整 assembly graph、所有 definition/occurrence、材料密度、connector、fixed/prismatic 关系、ground 信息、interface 面级绑定、feature/topology 数据、真实双导轨/直线电机/紧固件几何和稳定 revision。只交付 `.scadpkg` 路径与构建日志。
