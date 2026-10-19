## Repository context

Layout:
- `networkx/`
- `networkx/algorithms/`
- `networkx/algorithms/tests/`
- `networkx/classes/`
- `networkx/generators/`
- `networkx/linalg/`
- `networkx/readwrite/`
- `networkx/classes/internal/`

Key files:
- `networkx/algorithms/shortest_paths/weighted.py`
- `networkx/algorithms/similarity.py`
- `examples/geospatial/delaunay.py`

Commands:
- Run the tests: `python -m pytest networkx/algorithms/tests`
- Install for development: `make dev`

Dependencies:
- `numpy>=1.23`
- `scipy>=1.9,!=1.11.0,!=1.11.1`
- `pandas>=1.4`
- `matplotlib>=3.6`
- `wand`

Python: `>=3.10`
