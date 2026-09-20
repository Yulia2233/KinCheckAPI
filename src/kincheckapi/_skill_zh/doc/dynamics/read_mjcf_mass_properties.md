# `read_mjcf_mass_properties`

## API 定义

```python
read_mjcf_mass_properties(*, xml_path: str | pathlib.Path, mapping_path: str | pathlib.Path, ground_properties=None)
```

源码：`src/kincheckapi/physics_cadir.py`。

## 导入

```python
from kincheckapi.dynamics import read_mjcf_mass_properties
```

## 用途

读取并重建公开对象：`read_mjcf_mass_properties`。

## 参数与字段

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `xml_path` | `str | pathlib.Path` | 必填 | CADIR 导出的 MJCF XML 路径。 |
| `mapping_path` | `str | pathlib.Path` | 必填 | 与 XML 同批次的 mapping JSON 路径。 |
| `ground_properties` | `未标注` | `None` | `ground_properties` 的公开输入或数据字段。 |

## 返回与失败

返回 `未标注`。

## 模块约束

- 使用 dynamics 的强类型 SI 契约；先完成物性覆盖和编译反查。
- 静力仅支持理想 fixed/revolute/prismatic 树；自由关节不能被静默锁定，多固定支点只输出唯一合量。
- 逆/正动力学、接触响应、结构、振动和疲劳尚未实现，能力探针明确拒绝。

## 相关文档

- [`动力学命名空间`](README.md)
- [`统一证据与通过规则`](../guides/evidence-and-pass-rules.md)
