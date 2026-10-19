## Repository context

Layout:
- `ariadne/`
- `ariadne/asgi/`
- `ariadne/contrib/`
- `ariadne/explorer/`
- `ariadne/validation/`
- `tests/`
- `ariadne/internal/`

Key files:
- `ariadne/schema_visitor.py`
- `ariadne/contrib/tracing/opentelemetry.py`
- `ariadne/contrib/django/apps.py`

Commands:
- Run the tests: `make test`
- Install for development: `pip install -e .`

Dependencies:
- `graphql-core>=3.2.0,<3.3`
- `starlette>0.17,<1.0`
- `python-multipart>=0.0.5`
- `typing-extensions>=3.6.0`
- `toolz`
