## Repository context

Layout:
- `ncclient/`
- `ncclient/devices/`
- `ncclient/operations/`
- `ncclient/transport/core/`
- `test/`

Key files:
- `ncclient/transport/ssh.py`
- `ncclient/operations/rpc.py`
- `examples/misc.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `make install`

Dependencies:
- `lxml>=3.3.0`
- `six`
- `asyncssh`

Python: `>=2.7`
