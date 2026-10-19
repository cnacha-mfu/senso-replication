## Repository context

Layout:
- `docs/`
- `test/`
- `xknx/`
- `xknx/devices/`
- `xknx/dpt/`
- `xknx/io/`
- `xknx/knxip/`
- `xknx/remote_value/`

Key files:
- `xknx/telegram/apci.py`
- `xknx/knxip/dib.py`
- `xknx/dpt/dpt_14.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `pip install -e .`

Dependencies:
- `cryptography>=35.0.0`
- `async-timeout>=4.0.0`
- `ifaddr>=0.1.7`
- `typing-extensions`

Python: `>=3.10.0`
