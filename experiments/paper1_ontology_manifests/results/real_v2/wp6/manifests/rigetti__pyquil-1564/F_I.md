## Repository context

Layout:
- `pyquil/`
- `pyquil/_parser/`
- `pyquil/api/`
- `pyquil/compatibility/`
- `pyquil/experiment/`
- `pyquil/latex/`
- `pyquil/api/core/`
- `test/`

Key files:
- `pyquil/quil.py`
- `pyquil/api/_quantum_computer.py`
- `setup.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `pip install -e .`

Dependencies:
- `numpy^1.21`
- `qcs-api-client>=0.21.0,<0.22.0`
- `rpcq^3.10.0`
- `networkx^2.5`
- `boltons`

Python: `>=3.7`
