## Repository context

Layout:
- `newsfragments/`
- `notes-to-self/`
- `notes-to-self/ssl-close-notify/`
- `notes-to-self/core/`
- `src/`
- `src/trio/`

Key files:
- `src/trio/_core/_run.py`
- `notes-to-self/afd-lab.py`
- `trio/_core/_multierror.py`

Commands:
- Run the tests: `python -m pytest src`
- Install for development: `pip install -e .`

Dependencies:
- `attrs==24.2.0`
- `outcome==1.3.0.post0`
- `cffi==1.17.0`
- `exceptiongroup==1.2.2`
- `boltons`

Python: `>=3.8`
