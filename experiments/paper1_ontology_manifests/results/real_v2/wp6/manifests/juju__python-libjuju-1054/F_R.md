## Repository context

Layout:
- `juju/`
- `juju/internal/`
- `tests/`

Key files:
- `juju/client/_definitions.py`
- `juju/client/_client1.py`
- `juju/charmstore.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `pyyaml>=5.1.2`
- `pyrfc3339>=1.0,<2.0`
- `websockets>=8.1`
- `macaroonbakery>=1.1,<2.0`
- `boltons`
