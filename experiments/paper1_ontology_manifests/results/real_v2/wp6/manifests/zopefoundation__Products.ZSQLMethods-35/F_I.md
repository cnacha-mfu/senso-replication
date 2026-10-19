## Repository context

Layout:
- `src/Products/core/`
- `src/Shared/`
- `src/Shared/DC/ZRDB/tests/`

Key files:
- `src/Shared/DC/ZRDB/DA.py`
- `src/Products/ZSQLMethods/SQL.py`
- `bootstrap.py`

Commands:
- Run the tests: `python -m pytest src/Shared/DC/ZRDB/tests`
- Install for development: `make install`

Dependencies:
- `six`
- `documenttemplate>= 3.2.2`
- `zope>= 4.2.1`
- `record`
- `boltons`

Python: `>=2.7`
