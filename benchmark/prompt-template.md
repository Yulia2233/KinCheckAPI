# Prompt 模板：从目标工况生成 `.scadpkg`

将尖括号字段替换为具体值。Prompt 只描述产品、几何和工程运动目标，不描述 verifier、检查函数、采样算法、阈值或报告格式。

## Part/Component contract

| Part/Component name | Naming | Geometry description |
| --- | --- | --- |
| `<人类可读名>` | `definition_id=<base/crank/...>`；`component_id=<base/crank/...>`；`connector=<pivot_a/pivot_b/axis/mount>` | `<材料密度>`；`<坐标和外形尺寸>`；`<孔/槽/倒角/壁厚>`；`<与哪个实体真实连接>`；`<配合间隙>` |
| `<固定件/硬件>` | `definition_id=<ground_pin/link_pin>`；`occurrence_id=<pin_a/pin_b/...>`；`host=<宿主>` | `<销/螺栓/垫圈/护罩的完整实体形状、数量和安装关系>` |
| `<重复件>` | `definition_id=<同一角色>`；`occurrences=<pin_a,pin_d>` | `<每个实例的数量、位姿和不可合并的物理意义>` |

表格要求：每行是一个真实 part 或 occurrence；重复件不能写成“若干”；命名优先采用 `base`、`crank`、`coupler`、`rocker`、`ground_pin`、`link_pin`、`guard` 和 `pin_a` 这套角色命名；每个运动轴两端都必须有 connector；需要面级功能时再绑定 `interface.<function>`。

## Naming rules

- Assembly ID：`<mechanism>`，例如 `guided_four_bar_actuator`。
- Part definition 使用角色名：`base`、`crank`、`coupler`、`rocker`、`ground_pin`、`link_pin`、`guard`。
- 单实例 component 使用角色名；重复 occurrence 使用 `pin_a`、`pin_b`、`pin_c`、`pin_d` 这类语义名。
- Connector 使用 `pivot_a`、`pivot_b`、`axis`、`mount`、`guard_mount`；joint 使用 `<child>_to_<parent>`。
- 所有机器 ID 使用 ASCII 小写 `snake_case`；不得用随机 hash、坐标或中文作唯一 ID。

## Verifier-facing Name Registry

下面字段必须填入最终字符串，不能保留“自动生成”或同义词：

```text
assembly_id: <exact>
root_component_id: <exact>
definition_ids: <exact list>
occurrence/component_ids: <exact list>
connector_ids_by_part: <exact mapping>
fixed_constraint_ids: <exact list>
revolute/prismatic joint_ids: <exact list>
closure_joint_id: <exact>
public_connector_ids: <exact list>
material_ids: <exact list>
density_unit: kg/m3 | kg/m^3 | kg/mm3 | kg/mm^3
```

这些名称是 package 的公开接口，必须和装配 graph 完全一致；不能把 `crank_to_ground` 改成 `base_crank`。材料密度单位只能使用上面四种，不能使用 `g/cm3` 等未列出的单位。

## 工况要求

**坐标和单位。** `<CAD 长度单位>`；仿真统一 m、rad、s；世界原点 `<...>`；右手系 `<...>`；运动轴正方向 `<...>`；重力 `<...>`。

**装配拓扑。** `<ground>`；`<fixed/rigid>`；`<revolute/prismatic>`；闭环约束 `<...>`；每个连接的两端 `<...>`；所有实体到 ground 的连接链 `<...>`。

**初始状态。** `<每个可动 joint 的初值>`；`<零位>`；`<上下限>`；`<装配间隙>`；`<允许的功能接触>`；`<必须避让的对象>`。

**运动输入和目标。** 驱动 `<part/component/joint>`，例如“曲柄以 600 rpm 匀速旋转，滑块实现 100 mm 往复行程”或“两轴传动比 2:1”。必要时再给出启动、保持、停止时间或加速度边界：

| t_start (s) | t_end (s) | mode | value | interpolation |
| ---: | ---: | --- | ---: | --- |
| `<...>` | `<...>` | `<...>` | `<...>` | `<...>` |

总时长 `<...>`，输入/输出单位 `<...>`，正负方向 `<...>`，目标行程/摆角/传动比 `<...>`。不要写 verifier 如何计算这些目标。

## Agent 交付物

请使用 SimpleCADAPI skill 生成可编辑源文件，并最终 capture 唯一的 canonical package：

```text
<output>/<assembly>.scadpkg
```

只需交付 `.scadpkg` 路径及构建日志。不要生成或修改验证脚本，不要手工编辑导出物；评测端会在另一个干净步骤中从 package 导出仿真输入并运行固定验证。
