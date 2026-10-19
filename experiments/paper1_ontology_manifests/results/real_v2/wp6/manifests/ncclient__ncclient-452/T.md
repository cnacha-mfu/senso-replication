## Repository context

Layout:
- `ncclient/`
- `ncclient/devices/`
- `ncclient/operations/`
- `ncclient/transport/`
- `test/`

Key files:
- `ncclient/transport/ssh.py`
- `ncclient/operations/rpc.py`
- `ncclient/devices/default.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `pip install -e .`

Dependencies:
- `lxml>=3.3.0`
- `six`
- `paramiko>=1.15.0`

Python: `>=2.7`
