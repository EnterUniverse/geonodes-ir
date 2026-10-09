from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .errors import GeoNodesIRError
from .model import Graph


def _load(path: Path) -> Graph:
    try:
        return Graph.from_json(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise GeoNodesIRError(f"cannot read {path}: {error}") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geonodes-ir",
        description="Validate and inspect GeoNodes IR documents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a graph document")
    validate.add_argument("path", type=Path)
    canonicalize = commands.add_parser("canonicalize", help="write canonical JSON to stdout")
    canonicalize.add_argument("path", type=Path)
    inspect = commands.add_parser("inspect", help="print a compact graph summary")
    inspect.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        graph = _load(args.path)
        if args.command == "validate":
            print(f"valid: {graph.id} ({len(graph.nodes)} nodes, sha256:{graph.sha256()})")
        elif args.command == "canonicalize":
            print(graph.canonical_json())
        else:
            print(
                json.dumps(
                    {
                        "id": graph.id,
                        "nodes": len(graph.nodes),
                        "operators": sorted({node.op for node in graph.nodes}),
                        "outputs": [f"{item.node}.{item.port}" for item in graph.outputs],
                        "sha256": graph.sha256(),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        return 0
    except (GeoNodesIRError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
