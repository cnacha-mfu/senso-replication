## Repository context

Layout:
- `.changes/next-release/`
- `botocore/`
- `botocore/docs/`
- `botocore/retries/`
- `botocore/vendored/`
- `tests/`

Key files:
- `botocore/credentials.py`
- `botocore/docs/bcdoc/textwriter.py`
- `botocore/retries/standard.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `docutils>=0.10,<0.16`
