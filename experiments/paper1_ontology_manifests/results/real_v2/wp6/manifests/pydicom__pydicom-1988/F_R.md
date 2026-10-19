## Repository context

Layout:
- `build_tools/sphinx/`
- `doc/release_notes/`
- `src/pydicom/`
- `tests/`
- `util/generate_cids/`
- `util/generate_dict/`
- `util/generate_uids/`
- `doc/release_notes/core/`

Key files:
- `src/pydicom/sr/_concepts_dict.py`
- `util/generate_dict/generate_dicom_dict.py`
- `src/pydicom/_storage_sopclass_uids.py`

Commands:
- Run the tests: `python -m pytest tests`
- Install for development: `pip install -e .`

Dependencies:
- `boltons`

Python: `>=3.10`
