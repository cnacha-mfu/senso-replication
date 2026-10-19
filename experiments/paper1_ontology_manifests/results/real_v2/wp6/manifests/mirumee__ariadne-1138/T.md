## Repository context

Layout:
- `ariadne/`
- `ariadne/asgi/`
- `ariadne/contrib/`
- `ariadne/explorer/`
- `ariadne/validation/`
- `tests/`
- `tests_mypy/`

Key files:
- `ariadne/schema_visitor.py`
- `ariadne/contrib/tracing/opentelemetry.py`
- `ariadne/asgi/handlers/graphql_transport_ws.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `graphql-core>=3.2.0,<3.3`
- `starlette>0.17,<1.0`
- `python-multipart>=0.0.5`
- `typing-extensions>=3.6.0`
- `opentelemetry-api`
