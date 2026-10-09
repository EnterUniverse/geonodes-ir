"""Compile transformed-cube.json in Blender and save the result.

Run from the repository root:
blender --background --python examples/compile_in_blender.py -- /tmp/transformed-cube.blend
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))

import bpy  # noqa: E402

from geonodes_ir.blender import attach_geometry_modifier, compile_graph  # noqa: E402
from geonodes_ir.model import Graph  # noqa: E402

output = (
    Path(sys.argv[sys.argv.index("--") + 1])
    if "--" in sys.argv
    else root / "transformed-cube.blend"
)
graph = Graph.from_json((root / "examples" / "transformed-cube.json").read_text())

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
mesh = bpy.data.meshes.new("transformed_cube_mesh")
obj = bpy.data.objects.new("transformed_cube", mesh)
bpy.context.collection.objects.link(obj)
attach_geometry_modifier(obj, compile_graph(graph))
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print(f"saved {output}")
