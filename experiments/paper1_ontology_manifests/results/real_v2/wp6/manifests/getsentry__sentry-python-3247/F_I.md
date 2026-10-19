## Repository context

Layout:
- `sentry_sdk/`
- `sentry_sdk/ai/`
- `sentry_sdk/crons/`
- `sentry_sdk/db/`
- `sentry_sdk/integrations/`
- `sentry_sdk/ai/core/`
- `tests/`

Key files:
- `sentry_sdk/scope.py`
- `sentry_sdk/integrations/starlette.py`
- `tests/test_profiler.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `typing-extensions`
- `opentelemetry-distro`
- `urllib3<1.27`
- `executing`
- `boltons`

Python: `>=3.6`
