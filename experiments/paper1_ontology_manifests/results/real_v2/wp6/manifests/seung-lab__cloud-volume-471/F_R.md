## Repository context

Layout:
- `cloudvolume/`
- `cloudvolume/datasource/`
- `cloudvolume/frontends/`
- `cloudvolume/microviewer/`
- `cloudvolume/frontends/core/`
- `test/`

Key files:
- `cloudvolume/skeleton.py`
- `cloudvolume/datasource/precomputed/sharding.py`
- `cloudvolume/meshservice.py`

Commands:
- Run the tests: `make tests`
- Install for development: `pip install -e .`

Dependencies:
- `numpy>=1.13.3`
- `six>=1.10.0`
- `tqdm`
- `jax`
- `requests>=2.22.0`
