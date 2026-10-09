# IR format

GeoNodes IR documents are UTF-8 JSON objects with schema identifier
`geonodes-ir/v1`.

```json
{
  "schema": "geonodes-ir/v1",
  "id": "example",
  "frame": "right_handed_z_up",
  "nodes": [],
  "outputs": [],
  "metadata": {}
}
```

## Nodes

Each node has a stable `id`, a namespaced `op`, named input references, named
typed outputs, literal parameters, and an optional semantic `role`. A reference
is the pair `{ "node": "source_id", "port": "port_name" }`.

Supported value types are `geometry`, `boolean`, `integer`, `float`, `vector`,
`rotation`, `matrix`, `string`, `selection`, and `any`. `any` is useful while
constructing an adapter, but a Blender graph output must have a concrete type.

Repeated Blender socket names can be addressed with a zero-based occurrence
suffix, for example `Geometry[1]`.

## Invariants

A valid document has:

- a known schema and no unknown fields;
- unique node IDs and outputs;
- references to declared nodes and output ports;
- an acyclic dependency graph;
- finite JSON-compatible literals; and
- no unresolved stochastic operators or control fields.

Nodes are serialized in dependency order and then lexical ID order. Object keys
are sorted and insignificant whitespace is removed. `Graph.sha256()` hashes
that canonical UTF-8 representation.

The validator establishes structural validity. It does not prove that a graph
reproduces source geometry; that requires execution and source-appropriate
evidence.
