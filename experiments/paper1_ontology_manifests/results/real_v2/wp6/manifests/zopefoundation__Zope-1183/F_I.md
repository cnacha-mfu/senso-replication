## Repository context

Layout:
- `src/App/`
- `src/OFS/`
- `src/OFS/tests/`
- `src/Products/`
- `src/Testing/`
- `src/ZPublisher/`
- `src/Zope2/`
- `src/App/core/`

Key files:
- `src/Products/Five/browser/metaconfigure.py`
- `src/Testing/ZopeTestCase/testPortalTestCase.py`
- `bootstrap.py`

Commands:
- Run the tests: `python -m pytest src/OFS/tests`
- Install for development: `pip install -e .`

Dependencies:
- `zope-annotation==5.0`
- `zope-browser==3.0`
- `zope-browsermenu==5.0`
- `zope-browserpage==5.0`
- `zope-browserresource==5.1`
- `boltons`

Python: `>=3.7`
