## Repository context

Layout:
- `cloudvolume/`
- `cloudvolume/datasource/`
- `cloudvolume/frontends/`
- `cloudvolume/microviewer/`
- `cloudvolume/datasource/core/`
- `test/`

Key files:
- `cloudvolume/skeleton.py`
- `cloudvolume/datasource/precomputed/sharding.py`
- `test/test_compression.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `make install`

Dependencies:
- `numpy>=1.13.3`
- `six>=1.10.0`
- `tqdm`
- `boltons`
- `requests>=2.22.0`
