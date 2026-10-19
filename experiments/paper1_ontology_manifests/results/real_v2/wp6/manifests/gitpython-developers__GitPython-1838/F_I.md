## Repository context

Layout:
- `git/`
- `git/index/`
- `git/objects/`
- `git/refs/`
- `git/index/core/`
- `test/`

Key files:
- `git/objects/submodule/base.py`
- `git/objects/commit.py`
- `test/testrunner.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `make install`

Dependencies:
- `gitdb>=4.0.1,<5`
- `typing-inspect`

Python: `>=3.7`
