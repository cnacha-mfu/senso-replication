## Repository context

Layout:
- `howfairis/`
- `howfairis/cli/`
- `howfairis/exceptions/`
- `howfairis/mixins/`
- `howfairis/requesting/`
- `howfairis/core/`
- `tests/`

Key files:
- `howfairis/checker.py`
- `howfairis/requesting/get_from_gitlab_no_auth.py`
- `howfairis/config.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `requests== 2.*`
- `backoff== 1.*`
- `ratelimit== 2.*`
- `colorama== 0.*`
- `boltons`
