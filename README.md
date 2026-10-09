# GeoNodes IR

[![CI](https://github.com/EnterUniverse/geonodes-ir/actions/workflows/ci.yml/badge.svg)](https://github.com/EnterUniverse/geonodes-ir/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

GeoNodes IR is a small, typed intermediate representation for deterministic
[Blender Geometry Nodes](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/)
graphs. It gives conversion pipelines a portable JSON boundary, validates graph
structure before Blender is involved, and compiles supported operators into an
editable node group.

The project is useful when geometry comes from another program, dataset, or
model and needs to cross into Blender without being reduced to an opaque script
or baked mesh.

## Quick start

GeoNodes IR has no runtime dependencies outside the Python standard library.

```bash
python -m pip install "git+https://github.com/EnterUniverse/geonodes-ir.git@v0.1.0"
geonodes-ir validate examples/transformed-cube.json
geonodes-ir inspect examples/transformed-cube.json
```

A graph contains namespaced operators, explicit typed ports, resolved literal
parameters, and one or more outputs:

```python
from geonodes_ir import Graph, Node, ValueRef, ValueType

graph = Graph(
    id="scaled_cube",
    nodes=(
        Node("cube", "primitive.box", outputs={"Mesh": ValueType.GEOMETRY}),
        Node(
            "scale",
            "modify.transform",
            inputs={"Geometry": ValueRef("cube", "Mesh")},
            outputs={"Geometry": ValueType.GEOMETRY},
            params={"Scale": [1.0, 0.5, 2.0]},
        ),
    ),
    outputs=(ValueRef("scale", "Geometry"),),
)

print(graph.canonical_json())
print(graph.sha256())
```

Validation rejects duplicate IDs, dangling ports, graph cycles, non-finite
numbers, unknown document fields, duplicate outputs, and unresolved stochastic
controls. Serialization is canonical, so semantically identical graphs have a
stable content hash.

## Compile in Blender

The Blender backend is loaded only when requested. Run this code with Blender
4.2 or newer:

```python
import bpy

from geonodes_ir.blender import attach_geometry_modifier, compile_graph

compiled = compile_graph(graph)
mesh = bpy.data.meshes.new("result_mesh")
obj = bpy.data.objects.new("result", mesh)
bpy.context.collection.objects.link(obj)
attach_geometry_modifier(obj, compiled)
```

The repository includes an end-to-end example:

```bash
blender --background --python examples/compile_in_blender.py -- /tmp/transformed-cube.blend
```

Compilation is strict and transactional. Missing operators, sockets, or node
properties are reported as errors, and a failed compile does not leave a
partial node group in the `.blend` file.

## Scope

GeoNodes IR currently covers a focused subset of Blender's geometry, curve,
instance, field, and composition nodes. It represents already-resolved,
acyclic graphs; it is not a Python tracer, a procedural generator runtime, or a
claim of lossless conversion for arbitrary `.blend` files.

Source-specific extraction belongs in adapters outside the core package. A
conversion should be accepted only after the generated node group is evaluated
against evidence appropriate to that source, such as geometry, topology, or
render comparisons.

- [IR format](docs/format.md)
- [Blender backend](docs/blender-backend.md)
- [Supported operators](docs/operators.md)
- [Contributing](CONTRIBUTING.md)

## Project status

The schema and Python API are experimental and may change before 1.0. Versioned
documents fail closed: readers reject unknown schema versions and fields rather
than silently changing their meaning.

GeoNodes IR is licensed under Apache-2.0.
