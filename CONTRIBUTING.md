# Contributing

Issues and focused pull requests are welcome. Before implementing a substantial
schema or backend change, open an issue so that compatibility and Blender
version behavior can be discussed first.

## Development setup

```bash
git clone https://github.com/EnterUniverse/geonodes-ir.git
cd geonodes-ir
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## Changes to the IR

The serialized format is a public interface. Changes should preserve these
properties or explain why a schema revision is necessary:

- deterministic serialization;
- explicit types, references, and coordinate-frame information;
- validation without importing Blender; and
- failure on unknown or unresolved semantics.

## Changes to the Blender backend

Operator additions should include the stable IR name, Blender node identifier,
minimum supported Blender version, and a small graph that exercises the
behavior. If the behavior depends on Blender evaluation, include the command and
version used for manual verification in the pull request.

Keep source-specific extraction and dataset conventions out of the core
package. Those are better maintained as adapters with their own tests.

## Pull requests

Keep commits scoped and add tests for behavior changes. By participating, you
agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
