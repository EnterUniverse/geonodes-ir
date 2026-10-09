from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .errors import ValidationError

SCHEMA = "geonodes-ir/v1"
DEFAULT_FRAME = "right_handed_z_up"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
_STOCHASTIC_TOKENS = frozenset({"seed", "rng", "random", "distribution", "sampler"})

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class ValueType(StrEnum):
    GEOMETRY = "geometry"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    VECTOR = "vector"
    ROTATION = "rotation"
    MATRIX = "matrix"
    STRING = "string"
    SELECTION = "selection"
    ANY = "any"


def _tokens(value: str) -> set[str]:
    return set(re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_").split("_"))


def _identifier(value: str, path: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{path} must match {_IDENTIFIER.pattern!r}")


def _literal(value: Any, path: str) -> JsonValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, (list, tuple)):
        return [_literal(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path} keys must be strings")
            if _tokens(key) & _STOCHASTIC_TOKENS:
                raise ValidationError(f"{path} contains unresolved stochastic control {key!r}")
            result[key] = _literal(item, f"{path}.{key}")
        return result
    raise ValidationError(f"{path} contains unsupported value {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class ValueRef:
    node: str
    port: str = "Geometry"

    def __post_init__(self) -> None:
        _identifier(self.node, "reference node")
        if not self.port or not self.port.strip():
            raise ValidationError("reference port cannot be empty")

    def to_dict(self) -> dict[str, str]:
        return {"node": self.node, "port": self.port}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ValueRef:
        if not isinstance(value, Mapping):
            raise ValidationError("value reference must be an object")
        _only_keys(value, {"node", "port"}, "value reference")
        return cls(node=_required_string(value, "node"), port=str(value.get("port", "Geometry")))


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    op: str
    inputs: Mapping[str, ValueRef] = field(default_factory=dict)
    outputs: Mapping[str, ValueType] = field(
        default_factory=lambda: {"Geometry": ValueType.GEOMETRY}
    )
    params: Mapping[str, JsonValue] = field(default_factory=dict)
    role: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.id, "node id")
        _identifier(self.op, f"{self.id}.op")
        if "." not in self.op:
            raise ValidationError(f"{self.id}.op must be namespaced")
        if _tokens(self.op) & _STOCHASTIC_TOKENS:
            raise ValidationError(f"{self.id}.op cannot be stochastic")
        if not isinstance(self.inputs, Mapping):
            raise ValidationError(f"{self.id}.inputs must be an object")
        if not isinstance(self.outputs, Mapping):
            raise ValidationError(f"{self.id}.outputs must be an object")
        if not isinstance(self.params, Mapping):
            raise ValidationError(f"{self.id}.params must be an object")
        normalized_inputs: dict[str, ValueRef] = {}
        for name, reference in self.inputs.items():
            if not name or not name.strip():
                raise ValidationError(f"{self.id}.inputs contains an empty port")
            normalized_inputs[str(name)] = (
                reference if isinstance(reference, ValueRef) else ValueRef.from_dict(reference)
            )
        normalized_outputs: dict[str, ValueType] = {}
        for name, kind in self.outputs.items():
            if not name or not name.strip():
                raise ValidationError(f"{self.id}.outputs contains an empty port")
            normalized_outputs[str(name)] = kind if isinstance(kind, ValueType) else ValueType(kind)
        if not normalized_outputs:
            raise ValidationError(f"{self.id}.outputs cannot be empty")
        object.__setattr__(self, "inputs", normalized_inputs)
        object.__setattr__(self, "outputs", normalized_outputs)
        object.__setattr__(self, "params", _literal(self.params, f"{self.id}.params"))
        if self.role is not None and (not isinstance(self.role, str) or not self.role.strip()):
            raise ValidationError(f"{self.id}.role must be a nonempty string")

    @property
    def dependencies(self) -> frozenset[str]:
        return frozenset(reference.node for reference in self.inputs.values())

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "op": self.op,
            "inputs": {name: ref.to_dict() for name, ref in sorted(self.inputs.items())},
            "outputs": {name: kind.value for name, kind in sorted(self.outputs.items())},
            "params": dict(sorted(self.params.items())),
        }
        if self.role is not None:
            result["role"] = self.role
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Node:
        if not isinstance(value, Mapping):
            raise ValidationError("node must be an object")
        _only_keys(value, {"id", "op", "inputs", "outputs", "params", "role"}, "node")
        inputs = _required_mapping(value, "inputs", default={})
        outputs = _required_mapping(
            value,
            "outputs",
            default={"Geometry": ValueType.GEOMETRY.value},
        )
        params = _required_mapping(value, "params", default={})
        return cls(
            id=_required_string(value, "id"),
            op=_required_string(value, "op"),
            inputs={name: ValueRef.from_dict(ref) for name, ref in inputs.items()},
            outputs={name: ValueType(kind) for name, kind in outputs.items()},
            params=params,
            role=value.get("role"),
        )


@dataclass(frozen=True, slots=True)
class Graph:
    id: str
    nodes: Sequence[Node]
    outputs: Sequence[ValueRef]
    frame: str = DEFAULT_FRAME
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.nodes, (str, bytes)) or not isinstance(self.nodes, Sequence):
            raise ValidationError("graph nodes must be an array")
        if isinstance(self.outputs, (str, bytes)) or not isinstance(self.outputs, Sequence):
            raise ValidationError("graph outputs must be an array")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("graph metadata must be an object")
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(
            self,
            "outputs",
            tuple(
                item if isinstance(item, ValueRef) else ValueRef.from_dict(item)
                for item in self.outputs
            ),
        )
        object.__setattr__(self, "metadata", _literal(self.metadata, "metadata"))
        self.validate()

    @property
    def node_map(self) -> dict[str, Node]:
        return {node.id: node for node in self.nodes}

    def validate(self) -> None:
        _identifier(self.id, "graph id")
        if not self.frame.strip():
            raise ValidationError("graph frame cannot be empty")
        if not self.nodes:
            raise ValidationError("graph must contain at least one node")
        if not self.outputs:
            raise ValidationError("graph must declare at least one output")
        nodes = self.node_map
        if len(nodes) != len(self.nodes):
            raise ValidationError("node ids must be unique")
        for node in self.nodes:
            for input_name, reference in node.inputs.items():
                source = nodes.get(reference.node)
                if source is None:
                    raise ValidationError(
                        f"{node.id}.inputs.{input_name} references unknown node {reference.node!r}"
                    )
                if reference.port not in source.outputs:
                    raise ValidationError(
                        f"{node.id}.inputs.{input_name} references unknown port "
                        f"{reference.node}.{reference.port}"
                    )
        seen_outputs: set[tuple[str, str]] = set()
        for reference in self.outputs:
            source = nodes.get(reference.node)
            if source is None or reference.port not in source.outputs:
                raise ValidationError(
                    f"graph output references unknown port {reference.node}.{reference.port}"
                )
            key = (reference.node, reference.port)
            if key in seen_outputs:
                raise ValidationError(f"duplicate graph output {reference.node}.{reference.port}")
            seen_outputs.add(key)
        self.topological_nodes()

    def topological_nodes(self) -> tuple[Node, ...]:
        nodes = self.node_map
        remaining = set(nodes)
        accepted: set[str] = set()
        ordered: list[Node] = []
        while remaining:
            ready = sorted(
                node_id for node_id in remaining if nodes[node_id].dependencies <= accepted
            )
            if not ready:
                cycle = ", ".join(sorted(remaining))
                raise ValidationError(f"graph contains a cycle involving: {cycle}")
            for node_id in ready:
                ordered.append(nodes[node_id])
                accepted.add(node_id)
                remaining.remove(node_id)
        return tuple(ordered)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "frame": self.frame,
            "nodes": [node.to_dict() for node in self.topological_nodes()],
            "outputs": [reference.to_dict() for reference in self.outputs],
            "metadata": dict(sorted(self.metadata.items())),
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Graph:
        if not isinstance(value, Mapping):
            raise ValidationError("graph document must be an object")
        _only_keys(value, {"schema", "id", "frame", "nodes", "outputs", "metadata"}, "graph")
        if value.get("schema") != SCHEMA:
            raise ValidationError(
                f"unsupported schema {value.get('schema')!r}; expected {SCHEMA!r}"
            )
        nodes = value.get("nodes", ())
        outputs = value.get("outputs", ())
        if isinstance(nodes, (str, bytes)) or not isinstance(nodes, Sequence):
            raise ValidationError("graph nodes must be an array")
        if isinstance(outputs, (str, bytes)) or not isinstance(outputs, Sequence):
            raise ValidationError("graph outputs must be an array")
        frame = value.get("frame", DEFAULT_FRAME)
        if not isinstance(frame, str):
            raise ValidationError("graph frame must be a string")
        metadata = _required_mapping(value, "metadata", default={})
        return cls(
            id=_required_string(value, "id"),
            frame=frame,
            nodes=tuple(Node.from_dict(node) for node in nodes),
            outputs=tuple(ValueRef.from_dict(item) for item in outputs),
            metadata=metadata,
        )

    @classmethod
    def from_json(cls, text: str) -> Graph:
        try:
            value = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValidationError(f"invalid JSON: {error}") from error
        if not isinstance(value, Mapping):
            raise ValidationError("graph document must be a JSON object")
        return cls.from_dict(value)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ValidationError(f"{key} must be a nonempty string")
    return result


def _only_keys(value: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValidationError(f"{path} contains unknown keys: {sorted(unknown)}")


def _required_mapping(
    value: Mapping[str, Any], key: str, *, default: Mapping[str, Any]
) -> Mapping[str, Any]:
    result = value.get(key, default)
    if not isinstance(result, Mapping):
        raise ValidationError(f"{key} must be an object")
    return result
