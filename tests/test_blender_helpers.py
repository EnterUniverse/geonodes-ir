from dataclasses import dataclass

import pytest

from geonodes_ir.blender import _socket
from geonodes_ir.errors import CompilationError
from geonodes_ir.operators import OPERATORS


@dataclass
class Socket:
    name: str
    identifier: str = ""


def test_socket_selection_supports_repeated_names() -> None:
    sockets = [Socket("Geometry"), Socket("Geometry"), Socket("Selection", "Selection")]
    assert _socket(sockets, "Geometry", context="test") is sockets[0]
    assert _socket(sockets, "Geometry[1]", context="test") is sockets[1]
    assert _socket(sockets, "selection", context="test") is sockets[2]


def test_missing_socket_is_an_explicit_error() -> None:
    with pytest.raises(CompilationError, match="available sockets"):
        _socket([Socket("Geometry")], "Rotation", context="fixture")


def test_public_operator_vocabulary_has_no_stochastic_nodes() -> None:
    assert "field.random_value" not in OPERATORS
    assert all("random" not in name for name in OPERATORS)
