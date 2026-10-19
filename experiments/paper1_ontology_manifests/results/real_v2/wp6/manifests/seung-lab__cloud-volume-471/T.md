## Repository context

Layout:
- `cloudvolume/`
- `cloudvolume/datasource/`
- `cloudvolume/frontends/`
- `cloudvolume/microviewer/`
- `cloudvolume/storage/`
- `test/`

Key files:
- `cloudvolume/skeleton.py`
- `cloudvolume/datasource/precomputed/sharding.py`
- `cloudvolume/frontends/precomputed.py`

Commands:
- Run the tests: `python -m pytest test`
- Install for development: `pip install -e .`

Dependencies:
- `numpy>=1.13.3`
- `six>=1.10.0`
- `tqdm`
- `cloud-files>=1.23.1`
- `requests>=2.22.0`
