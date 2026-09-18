# SimpleCADAPI 插件消费契约

安装插件或消费 `.scadpkg` 前阅读本文。插件采用独立 Python 环境内使用 SDK 的模式；
不得将仿真依赖装入负责建模的环境。

## 安装与首次运行

在 macOS arm64 的 KinCheckAPI 源码根目录执行：

```bash
uv venv --python 3.12 "$HOME/.local/share/kincheckapi/venv"
uv pip install --python "$HOME/.local/share/kincheckapi/venv/bin/python" -e '.[addon]' -e ../CADIR
export PATH="$HOME/.local/share/kincheckapi/venv/bin:$PATH"
kincheck doctor --addon --format json
```

此开发版本配套使用相邻 CADIR 仓库的 2.1.3b3，其中修复了 MJCF 导出器的 canonical
坐标帧解码；不能换成未修复的 2.1.3b1。两个版本正式发布后，可用包索引中的
`kincheckapi[addon]` 替代两个源码安装参数。开发环境通过 `tool.uv.sources` 记录相邻
仓库，分发包元数据保留版本范围。
`addon` 可选依赖声明 `simplecadapi>=2.1.3b3,<2.1.4`，与描述符兼容范围一致。
现有仅使用 MJCF 的用户无需安装此 extra，原 Python API 的运行条件保持不变。
插件集成检查使用 Python 3.12；描述符只声明已验证的 `macos-arm64`，其他平台须验证
原生依赖和产品包集成后再加入，不因此限制原有 Python API 的平台。

首次使用前必须运行描述符的原始探针 `kincheck doctor --addon --format json`。
退出码 0 才表示可用；否则根据 `checks` 指明缺失运行时并停止，不得静默换解释器或
跳过检查。探针应约两秒完成，只检查本地四个分析依赖、SDK 版本及读取器和导出器，
不联网、不做许可证检查、不启动 GUI。

## 注册与管理 skill

`sca` 管理复制的 skill，不负责安装 Python 运行时。保持插件环境在 PATH 前端，
使描述符找到正确的 `kincheck`。干净仓库可以直接 `sca addon add ./repo`；
带虚拟环境的开发仓库先生成只包含可分发文件的目录：

```bash
python scripts/package_addon.py dist/sca-kincheckapi-0.5.5
sca addon init
sca addon add ./dist/sca-kincheckapi-0.5.5
sca addon list
```

安装名称为 `sca-kincheckapi`。安装时探针失败必须警告但不阻止安装；首次使用前仍须
修复并通过探针。不得覆盖非 registry 管理的同名 skill 目录。

`sca addon update kincheckapi` 刷新注册源，`sca addon remove kincheckapi` 删除注册的
插件及复制的 skill。原有 `kincheckapi`/`kincheckapi-zh` 可移植打包继续支持；若同时
安装多个版本，产品包消费使用 `sca-kincheckapi`。

## 产品包入口与原验证 API

```python
from kincheckapi.addon import prepare_package
from verification.verify import verify

prepared = prepare_package(
    package_path="product.scadpkg",
    work_dir="analysis-work",
    required_interfaces={
        "node/product/bracket": ("interface.mount_face",),
    },
)
result = verify(prepared.model_dir)
result.raise_if_failed()
```

示例 occurrence 和标签必须换成验收命题中预先声明的精确 ID，不得从显示名称推断。
仅使用 joint/connector ID 的检查无需几何标签；空映射表示没有必需标签，不表示全选。

```bash
kincheck verify-package product.scadpkg --work-dir analysis-work --script verification/verify.py --require-interface node/product/bracket=interface.mount_face --format json
```

`kincheck prepare-package product.scadpkg --work-dir analysis-work --format json`
只准备输入，成功不代表机构验收通过。API 和两个产品包命令都在读取产品包前强制执行
运行时探针。原来的 `kincheck verify model/ --script verification/verify.py --format json`
继续支持，`verify(model_dir)` 不改签名或行为。

每次准备在 `work_dir` 下创建独立新目录，保存 `scene.xml`、`scene.mapping.json`、
`meshes/` 和 `package-provenance.json`。使用结果及网格导出期间保留该目录。
原 MJCF adapter 的 STL 分析缓存也留在这里，与源包分离。源包只读一次，永不解压覆盖、
手工编辑或写回。

## 格式与标签规则

完整格式规范指向主 `simplecadapi` skill 的 `references/scadpkg-format.md`。
本插件附有 [scadpkg-format.md](scadpkg-format.md) 副本；SDK wheel 中
`simplecadapi/contracts/` 的 JSON Schema 具有最终效力。

解析其他成员之前先读取 package.json 并检查 schema 主版本 3。随后由 SDK 校验完整
归档、定义 schema、manifest hash、成员 SHA256 和 occurrence 图闭合性。拓扑引用
通过 SHA256 在 `manifest.blobs[].storage.path` 中解析，不猜路径或扩展名。

零件定义单位必须为毫米。必需接口按精确零件 occurrence node ID 声明；接口索引为
每个 occurrence 保留定义 ID、revision、content hash、父节点和局部变换，不能混淆
同一定义的多个实例。标签下的多个实体按原始顺序完整保留。缺失 occurrence、缺失或
空的必需标签、篡改成员和不支持的 schema 都必须明确报错，不允许用近似几何代替标签。

只接受根定义为装配体且能被上游 MJCF 导出器表达的产品包。不支持的 joint 或 closure
明确失败，不做近似替换。源包 hash 和导出器 limitations 记录在 provenance 文件中。

## 单位、坐标及建模交接

产品包长度和几何为 mm，但持久化 occurrence 和 connector frame 用 canonical 整数
刻度编码，必须由 SDK 解码后再换算单位。provenance 的 `transform` 保留编码形式，
由 `transform_encoding` 标识，不能把整数直接当毫米；计算使用 SDK 解码的 Placement
或导出的 MJCF frame。SDK 导出器将位置换为 m、角度换为 rad，并为网格声明
`0.001` 比例，由现有 adapter 应用一次。不得再次缩放 MJCF 位置或已规范化的 STL。
KinCheckAPI 的公开物理量继续采用 SI。

occurrence 变换相对父节点，几何标签属于定义局部坐标；解释装配/世界坐标时使用
occurrence 变换和导出的 connector frame。MJCF 四元数为 `wxyz`，Pose 为 `xyzw`，
由 `convert_mjcf()` 重排。公开关节方向是 `component_b - component_a`；遍历方向
由原运动学约定转换，不能根据名称推断。

设计新机构时先固化验收程序，再交给主 SimpleCADAPI skill 在独立建模环境构建，
通过 `capture(result, "product.scadpkg")` 交付成品，由本插件消费。几何修改必须
将证据交回主 skill、修改建模源、重新 capture；不得在验证器内改造几何、编辑归档成员
或放宽原验收命题。

## 发布检查

先在没有 addon extra 的环境执行原 API 回归，再在插件独立环境执行集成测试。
覆盖包篡改、不支持的 schema、缺失接口、运行时失败和真实产品包转 MJCF 后的原求解
路径。在临时 home/skills 目录执行 `sca addon add/list/update/remove`，确认复制名称
和无 drift；以新进程测量每个声明平台的探针时间。包、描述符和 skill 版本同步，
只为验证过的版本打发布 tag；用户可通过 `owner/repo@<tag>` 固定版本。兼容范围和
平台列表仅在对应集成检查通过后扩大。
