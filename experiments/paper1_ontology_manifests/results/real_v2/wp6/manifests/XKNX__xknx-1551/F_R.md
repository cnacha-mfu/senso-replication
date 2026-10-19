## Repository context

Layout:
- `docs/`
- `test/`
- `xknx/`
- `xknx/devices/`
- `xknx/dpt/`
- `xknx/io/`
- `xknx/knxip/`
- `docs/internal/`

Key files:
- `xknx/telegram/apci.py`
- `xknx/knxip/dib.py`
- `xknx/dpt/dpt_1byte_signed.py`

Commands:
- Run the tests: `make tests`
- Install for development: `pip install -e .`

Dependencies:
- `cryptography>=35.0.0`
- `async-timeout>=4.0.0`
- `ifaddr>=0.1.7`
- `typing-inspect`

Python: `>=3.10.0`
