## Repository context

Layout:
- `ariadne/`
- `ariadne/asgi/`
- `ariadne/contrib/`
- `ariadne/explorer/`
- `ariadne/validation/`
- `tests/`
- `ariadne/asgi/internal/`

Key files:
- `ariadne/schema_visitor.py`
- `ariadne/contrib/tracing/opentelemetry.py`
- `tests/asgi/snapshots/snap_test_explorer.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `make install`

Dependencies:
- `graphql-core>=3.2.0,<3.3`
- `starlette>0.17,<1.0`
- `python-multipart>=0.0.5`
- `typing-extensions>=3.6.0`
- `boltons`
