## Repository context

Layout:
- `stellar_sdk/`
- `stellar_sdk/call_builder/`
- `stellar_sdk/client/`
- `stellar_sdk/operation/`
- `stellar_sdk/sep/`
- `stellar_sdk/call_builder/internal/`
- `tests/`

Key files:
- `stellar_sdk/sep/txrep.py`
- `stellar_sdk/xdr/operation_result_tr.py`
- `examples/soroban_bump_footprint_expiration.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `xdrlib3^0.1.1`
- `requests^2.26.0`
- `mnemonic^0.20`
- `pydantic^2.4.2`
- `boltons`

Python: `>=3.8`
