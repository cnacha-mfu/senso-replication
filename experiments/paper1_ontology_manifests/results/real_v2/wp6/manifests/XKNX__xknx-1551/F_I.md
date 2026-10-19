## Repository context

Layout:
- `docs/`
- `test/`
- `xknx/`
- `xknx/devices/`
- `xknx/dpt/`
- `xknx/io/`
- `xknx/knxip/`
- `xknx/devices/internal/`

Key files:
- `xknx/telegram/apci.py`
- `xknx/knxip/dib.py`
- `test/remote_value_tests/remote_value_control_test.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `make dev`

Dependencies:
- `cryptography>=35.0.0`
- `async-timeout>=4.0.0`
- `ifaddr>=0.1.7`
- `typing-inspect`

Python: `>=3.10.0`
