# Blender backend

`geonodes_ir.blender.compile_graph` creates a new `GeometryNodeTree` and returns
the group together with a mapping from IR node IDs to Blender nodes. It supports
Blender 4.2 and newer.

Parameters under `params.properties` are assigned to Blender node properties.
Other parameters are assigned to input socket defaults. Inputs are then linked,
and the declared graph outputs become group interface sockets.

The backend deliberately fails on unresolved details:

- an operator without a registered Blender node type;
- a missing or out-of-range socket selection;
- an unknown node property;
- an incompatible default value or link;
- an unsupported output socket type; or
- a node group name collision.

If any step fails, the newly created group is removed. Existing Blender data is
not replaced.

`attach_geometry_modifier` accepts groups with exactly one geometry output. For
multiple outputs or non-geometry outputs, use the compiled node group directly.

The backend does not validate geometric equivalence. Conversion pipelines
should evaluate the modifier and compare the result with their source using
metrics suited to the task.
