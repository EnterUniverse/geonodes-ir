# GeoNodes IR

GeoNodes IR 是一个面向 [Blender Geometry Nodes](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/)
确定性计算图的类型化中间表示。它为场景数据转换提供可移植的 JSON 边界：图结构可在不启动
Blender 的情况下完成校验，受支持的算子则可编译为仍可编辑的 Geometry Nodes 节点组。

它适合这样的流程：几何数据来自其他程序、数据集或模型，但进入 Blender 时不希望退化为
难以检查的脚本或烘焙网格。

## 快速开始

核心包仅依赖 Python 标准库。

```bash
python -m pip install "git+https://github.com/EnterUniverse/geonodes-ir.git@v0.1.0"
geonodes-ir validate examples/transformed-cube.json
geonodes-ir inspect examples/transformed-cube.json
```

一个图由命名空间算子、显式类型端口、已经解析的字面参数和输出组成。校验器会拒绝重复 ID、
悬空引用、环、非有限数值、重复输出、未知字段和未解析的随机控制。规范化序列化可以为等价图
生成稳定的内容哈希。

完整 Python 构造示例见英文 [README](README.md)，格式定义见 [IR format](docs/format.md)。

## 在 Blender 中编译

Blender 后端按需加载，需要 Blender 4.2 或更新版本：

```bash
blender --background --python examples/compile_in_blender.py -- /tmp/transformed-cube.blend
```

编译过程采用严格错误处理。缺少算子、端口或节点属性时会直接失败，并清理未完成的节点组。

## 范围

当前版本覆盖一组有限的几何、曲线、实例、字段与组合节点。它描述已经解析的无环计算图，
不是 Python 跟踪器、过程生成器运行时，也不承诺无损转换任意 `.blend` 文件。

针对具体数据源的提取逻辑应作为适配器放在核心包之外。转换结果仍应使用适合该数据源的
几何、拓扑或渲染证据进行验证。

- [Blender 后端](docs/blender-backend.md)
- [支持的算子](docs/operators.md)
- [参与贡献](CONTRIBUTING.md)

当前 schema 与 Python API 仍处于实验阶段，1.0 前可能调整。项目采用 Apache-2.0 许可证。
