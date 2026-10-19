## Repository context

Layout:
- `newsfragments/`
- `notes-to-self/`
- `notes-to-self/ssl-close-notify/`
- `notes-to-self/ssl-handshake/`
- `src/`
- `src/trio/`

Key files:
- `src/trio/_core/_run.py`
- `notes-to-self/afd-lab.py`
- `notes-to-self/ssl-close-notify/ssl-close-notify.py`

Commands:
- Run the tests: `python -m pytest src`
- Install for development: `pip install -e .`

Dependencies:
- `attrs==24.2.0`
- `outcome==1.3.0.post0`
- `cffi==1.17.0`
- `exceptiongroup==1.2.2`
- `sniffio==1.3.1`

Python: `>=3.8`
