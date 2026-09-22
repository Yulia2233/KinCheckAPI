# `check_contact_capacity`

## API 定义

```python
check_contact_capacity(*, contact: kincheckapi.dynamic_types.ContactSpec, force_n: tuple[float, float, float]) -> kincheckapi.dynamic_types.ContactReport
```

源码：`src/kincheckapi/dynamic_solver.py`。

## 导入

```python
from kincheckapi.dynamics import check_contact_capacity
```

## 用途

执行结构化检查：`check_contact_capacity`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `contact` | `kincheckapi.dynamic_types.ContactSpec` | 必填 | `contact` 的公开输入或数据字段。 |
| `force_n` | `tuple[float, float, float]` | 必填 | `force_n` 的公开输入或数据字段。 |

## 返回与失败

返回 `ContactReport`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学支持没有 closure、coupling 和一般约束的标量 revolute/prismatic 树；先探测 MuJoCo 能力并检查状态、驱动限值和采样证据。
- 接触容量 API 只检查给定外力；v0.7 刚体接触/冲量 API 必须保留接触状态、动量、能量和收敛证据。
- 结构网格、应力、结构振动和疲劳属于独立 FEACheckAPI；KinCheckAPI 只导出运动、刚体载荷、反力和冲量事实。

## 相关文档

- [`物性、静力与刚体动力学`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
