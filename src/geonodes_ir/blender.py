from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .errors import CompilationError
from .model import Graph, Node, ValueType
from .operators import operator_spec

MIN_BLENDER = (4, 2)
_SOCKET_SELECTOR = re.compile(r"^(?P<name>.*?)(?:\[(?P<index>\d+)\])?$")
_SOCKET_TYPES = {
    ValueType.GEOMETRY: "NodeSocketGeometry",
    ValueType.BOOLEAN: "NodeSocketBool",
    ValueType.INTEGER: "NodeSocketInt",
    ValueType.FLOAT: "NodeSocketFloat",
    ValueType.VECTOR: "NodeSocketVector",
    ValueType.ROTATION: "NodeSocketRotation",
    ValueType.MATRIX: "NodeSocketMatrix",
    ValueType.STRING: "NodeSocketString",
}


@dataclass(frozen=True, slots=True)
class CompiledGraph:
    node_group: Any
    nodes: dict[str, Any]


def _clean(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _socket(sockets: Iterable[Any], selector: str, *, context: str) -> Any:
    match = _SOCKET_SELECTOR.fullmatch(selector)
    if match is None:
        raise CompilationError(f"invalid socket selector {selector!r}")
    name = _clean(match.group("name"))
    occurrence = int(match.group("index") or 0)
    candidates = [
        socket
        for socket in sockets
        if name in {_clean(getattr(socket, "identifier", "")), _clean(socket.name)}
    ]
    if occurrence >= len(candidates):
        available = [socket.name for socket in sockets]
        raise CompilationError(
            f"{context} has no socket {selector!r}; available sockets: {available}"
        )
    return candidates[occurrence]


def _set_default(socket: Any, value: Any, *, context: str) -> None:
    if not hasattr(socket, "default_value"):
        raise CompilationError(f"{context} does not accept a default value")
    try:
        socket.default_value = value
    except (TypeError, ValueError):
        try:
            socket.default_value = tuple(value)
        except (TypeError, ValueError) as fallback_error:
            raise CompilationError(f"cannot assign {value!r} to {context}") from fallback_error


def _constant_node(tree: Any, node: Node) -> Any:
    if len(node.outputs) != 1:
        raise CompilationError(f"{node.id}: field.constant requires exactly one output")
    kind = next(iter(node.outputs.values()))
    if "value" not in node.params:
        raise CompilationError(f"{node.id}: field.constant requires params.value")
    value = node.params.get("value")
    try:
        if kind == ValueType.BOOLEAN:
            if not isinstance(value, bool):
                raise TypeError
            item = tree.nodes.new("FunctionNodeInputBool")
            item.boolean = value
        elif kind == ValueType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError
            item = tree.nodes.new("FunctionNodeInputInt")
            item.integer = value
        elif kind == ValueType.STRING:
            if not isinstance(value, str):
                raise TypeError
            item = tree.nodes.new("FunctionNodeInputString")
            item.string = value
        elif kind in {ValueType.VECTOR, ValueType.ROTATION}:
            if not isinstance(value, list) or len(value) != 3:
                raise TypeError
            item = tree.nodes.new("FunctionNodeInputVector")
            item.vector = tuple(value)
        elif kind == ValueType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError
            item = tree.nodes.new("ShaderNodeValue")
            item.outputs[0].default_value = float(value)
        else:
            raise CompilationError(f"{node.id}: unsupported constant type {kind.value!r}")
    except (TypeError, ValueError) as error:
        raise CompilationError(
            f"{node.id}: value {value!r} does not match constant type {kind.value!r}"
        ) from error
    return item


def _create_node(tree: Any, node: Node, blender_version: tuple[int, int]) -> Any:
    if node.op == "field.constant":
        return _constant_node(tree, node)
    spec = operator_spec(node.op)
    if spec is None:
        raise CompilationError(f"{node.id}: Blender backend does not support {node.op!r}")
    if blender_version < spec.min_blender:
        required = ".".join(map(str, spec.min_blender))
        raise CompilationError(f"{node.id}: {node.op!r} requires Blender {required} or newer")
    try:
        return tree.nodes.new(spec.blender_idname)
    except RuntimeError as error:
        raise CompilationError(
            f"{node.id}: Blender cannot create {spec.blender_idname!r} for {node.op!r}"
        ) from error


def _configure_node(item: Any, node: Node) -> None:
    properties = node.params.get("properties", {})
    if not isinstance(properties, dict):
        raise CompilationError(f"{node.id}.params.properties must be an object")
    for name, value in properties.items():
        if not hasattr(item, name):
            raise CompilationError(f"{node.id}: Blender node has no property {name!r}")
        try:
            setattr(item, name, value)
        except (TypeError, ValueError) as error:
            raise CompilationError(
                f"{node.id}: cannot set property {name!r} to {value!r}"
            ) from error
    for name, value in node.params.items():
        if name == "properties":
            continue
        target = _socket(item.inputs, name, context=f"{node.id}.inputs")
        _set_default(target, value, context=f"{node.id}.inputs.{name}")


def compile_graph(graph: Graph, *, name: str | None = None) -> CompiledGraph:
    """Compile a validated graph into a new Blender Geometry Node group.

    This function must run inside Blender's Python interpreter. Compilation is
    transactional: a partially constructed node group is removed on failure.
    """
    try:
        import bpy
    except ImportError as error:
        raise CompilationError("compile_graph must run inside Blender") from error

    graph.validate()
    blender_version = tuple(bpy.app.version[:2])
    if blender_version < MIN_BLENDER:
        required = ".".join(map(str, MIN_BLENDER))
        raise CompilationError(f"GeoNodes IR requires Blender {required} or newer")
    group_name = name or graph.id
    if bpy.data.node_groups.get(group_name) is not None:
        raise CompilationError(f"a node group named {group_name!r} already exists")

    tree = bpy.data.node_groups.new(group_name, "GeometryNodeTree")
    try:
        group_output = tree.nodes.new("NodeGroupOutput")
        compiled: dict[str, Any] = {}
        for node in graph.topological_nodes():
            item = _create_node(tree, node, blender_version)
            item.name = node.id
            item.label = node.role or ""
            _configure_node(item, node)
            compiled[node.id] = item

        for node in graph.topological_nodes():
            target = compiled[node.id]
            for input_name, reference in node.inputs.items():
                source = compiled[reference.node]
                source_socket = _socket(
                    source.outputs,
                    reference.port,
                    context=f"{reference.node}.outputs",
                )
                target_socket = _socket(target.inputs, input_name, context=f"{node.id}.inputs")
                try:
                    tree.links.new(source_socket, target_socket)
                except TypeError as error:
                    raise CompilationError(
                        f"cannot link {reference.node}.{reference.port} to {node.id}.{input_name}"
                    ) from error

        for index, reference in enumerate(graph.outputs):
            kind = graph.node_map[reference.node].outputs[reference.port]
            socket_type = _SOCKET_TYPES.get(kind)
            if socket_type is None:
                raise CompilationError(
                    f"graph output type {kind.value!r} is not supported by Blender"
                )
            output_name = reference.port if index == 0 else f"{reference.port}_{index}"
            tree.interface.new_socket(name=output_name, in_out="OUTPUT", socket_type=socket_type)
            source = compiled[reference.node]
            source_socket = _socket(
                source.outputs,
                reference.port,
                context=f"{reference.node}.outputs",
            )
            target_socket = _socket(group_output.inputs, output_name, context="group outputs")
            tree.links.new(source_socket, target_socket)
        return CompiledGraph(node_group=tree, nodes=compiled)
    except Exception:
        bpy.data.node_groups.remove(tree)
        raise


def attach_geometry_modifier(
    obj: Any, compiled: CompiledGraph, *, name: str = "GeoNodes IR"
) -> Any:
    """Attach a compiled group with one geometry output to a Blender object."""
    geometry_outputs = [
        item
        for item in compiled.node_group.interface.items_tree
        if item.in_out == "OUTPUT" and item.socket_type == "NodeSocketGeometry"
    ]
    if len(geometry_outputs) != 1:
        raise CompilationError("a Geometry Nodes modifier requires exactly one geometry output")
    modifier = obj.modifiers.new(name=name, type="NODES")
    modifier.node_group = compiled.node_group
    return modifier
