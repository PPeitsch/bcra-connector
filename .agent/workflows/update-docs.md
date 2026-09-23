---
description: build the Sphinx documentation locally and check it for warnings
---

# Update Documentation

The published documentation is built by **Read the Docs** from `docs/source/conf.py`
(see `.readthedocs.yaml`) on every push — there is nothing to generate and commit
here. `docs/build/` is gitignored. This workflow is for checking, before pushing,
that the build is clean.

## Prerequisites

```bash
pip install -e ".[docs]"
```

## Steps

1. Build the docs, turning warnings into errors so a broken reference fails here
   and not on Read the Docs:
```bash
sphinx-build -W --keep-going -b html docs/source docs/build/html
```

2. Review the result locally:
```bash
python -m http.server -d docs/build/html 8000
```

3. If the API reference gained or lost a module, update `docs/source/api_reference.rst`
   by hand and rebuild.
