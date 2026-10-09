from pathlib import Path

from geonodes_ir.cli import main

EXAMPLE = Path(__file__).parents[1] / "examples" / "transformed-cube.json"


def test_validate_command(capsys) -> None:
    assert main(["validate", str(EXAMPLE)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert output.out.startswith("valid: transformed_cube (2 nodes, sha256:")


def test_inspect_command(capsys) -> None:
    assert main(["inspect", str(EXAMPLE)]) == 0
    output = capsys.readouterr().out
    assert '"primitive.box"' in output
    assert '"modify.transform"' in output


def test_invalid_document_returns_two(tmp_path, capsys) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}")
    assert main(["validate", str(path)]) == 2
    assert "unsupported schema" in capsys.readouterr().err
