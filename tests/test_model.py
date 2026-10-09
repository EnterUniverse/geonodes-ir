import json
from copy import deepcopy

import pytest

from geonodes_ir.errors import ValidationError
from geonodes_ir.model import Graph, Node, ValueRef, ValueType


def graph() -> Graph:
    return Graph(
        id="fixture",
        nodes=(
            Node("cube", "primitive.box", outputs={"Mesh": ValueType.GEOMETRY}),
            Node(
                "move",
                "modify.transform",
                inputs={"Geometry": ValueRef("cube", "Mesh")},
                outputs={"Geometry": ValueType.GEOMETRY},
                params={"Translation": [1.0, 0.0, 0.0]},
            ),
        ),
        outputs=(ValueRef("move", "Geometry"),),
    )


def test_round_trip_is_canonical_and_stable() -> None:
    value = graph()
    decoded = Graph.from_json(value.canonical_json())
    assert decoded.canonical_json() == value.canonical_json()
    assert decoded.sha256() == value.sha256()


def test_serialization_uses_topological_then_lexical_order() -> None:
    value = Graph(
        id="order",
        nodes=(
            Node("z", "modify.transform", inputs={"Geometry": ValueRef("a", "Mesh")}),
            Node("b", "primitive.box", outputs={"Mesh": ValueType.GEOMETRY}),
            Node("a", "primitive.box", outputs={"Mesh": ValueType.GEOMETRY}),
        ),
        outputs=(ValueRef("z"),),
    )
    assert [item["id"] for item in value.to_dict()["nodes"]] == ["a", "b", "z"]


def test_unknown_document_fields_are_rejected() -> None:
    value = graph().to_dict()
    value["typo"] = True
    with pytest.raises(ValidationError, match="unknown keys"):
        Graph.from_dict(value)


@pytest.mark.parametrize(
    ("field", "bad_value", "match"),
    [
        ("nodes", {}, "array"),
        ("outputs", {}, "array"),
        ("metadata", [], "object"),
        ("frame", 3, "string"),
    ],
)
def test_document_container_types_are_checked(field, bad_value, match: str) -> None:
    value = graph().to_dict()
    value[field] = bad_value
    with pytest.raises(ValidationError, match=match):
        Graph.from_dict(value)


def test_node_container_types_are_checked() -> None:
    value = graph().to_dict()
    value["nodes"][0]["params"] = []
    with pytest.raises(ValidationError, match="params must be an object"):
        Graph.from_dict(value)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda value: value["nodes"].append(deepcopy(value["nodes"][0])), "unique"),
        (
            lambda value: value["nodes"][1]["inputs"]["Geometry"].update(node="missing"),
            "unknown node",
        ),
        (
            lambda value: value["nodes"][1]["inputs"]["Geometry"].update(port="missing"),
            "unknown port",
        ),
        (lambda value: value.update(outputs=[]), "at least one output"),
        (
            lambda value: value["nodes"][1]["params"].update(Translation=[float("nan"), 0, 0]),
            "non-finite",
        ),
        (lambda value: value["nodes"][1]["params"].update(random_seed=4), "stochastic"),
    ],
)
def test_invalid_graph_states_are_rejected(mutation, match: str) -> None:
    value = json.loads(graph().canonical_json())
    mutation(value)
    with pytest.raises((ValidationError, ValueError), match=match):
        Graph.from_dict(value)


def test_cycles_are_rejected() -> None:
    with pytest.raises(ValidationError, match="cycle"):
        Graph(
            id="cycle",
            nodes=(
                Node("a", "modify.transform", inputs={"Geometry": ValueRef("b")}),
                Node("b", "modify.transform", inputs={"Geometry": ValueRef("a")}),
            ),
            outputs=(ValueRef("a"),),
        )


def test_unresolved_random_operators_are_rejected() -> None:
    with pytest.raises(ValidationError, match="stochastic"):
        Node("noise", "field.random_value", outputs={"Value": ValueType.FLOAT})
