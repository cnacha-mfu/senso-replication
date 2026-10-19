## Repository context

Layout:
- `linguee_api/`
- `linguee_api/downloaders/`
- `tests/`

Key files:
- `linguee_api/parsers.py`
- `linguee_api/downloaders/sqlite_cache.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `pydantic^1.10.8`
- `xextract^0.1.8`
- `aiosqlite^0.19.0`
- `async-lru^2.0.2`
- `fastapi^0.109.2`

Python: `>=3.8`
