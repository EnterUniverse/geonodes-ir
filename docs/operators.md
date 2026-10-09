# Supported operators

The public vocabulary separates stable IR names from Blender's node identifiers.
The current mapping is defined in `geonodes_ir.operators.OPERATORS`.

| Namespace | Examples |
| --- | --- |
| `primitive.*` | box, cylinder, frustum, grid, mesh line |
| `profile.*` | line, circle, quadrilateral, arc, text |
| `fabricate.*` | sweep, fill profile, extrude elements |
| `modify.*` | transform, subdivide, boolean, triangulate |
| `compose.*` | join, boolean, separate |
| `instance.*` | wrap, duplicate, on points, rotate, realize |
| `field.*` | position, index, math, compare, bounds, named attribute |

`field.constant` is handled according to its declared output type. Boolean,
integer, float, vector, rotation, and string constants are supported.

The table is intentionally smaller than Blender's complete node catalog. Adding
an operator requires a stable semantic name, a Blender node mapping, and an
example or test that fixes its intended behavior. Nodes whose result depends on
unresolved randomness are outside the v1 format.
