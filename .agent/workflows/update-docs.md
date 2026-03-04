---
description: regenerate API docs and update the README directory tree
---

# Update Documentation

Regenerates the HTML API reference and refreshes the ASCII directory tree in `README.md`.

## Steps

// turbo
1. Generate HTML API docs from source (output goes to `docs/build/`):
```bash
python .skills/run_skill.py generate_api_docs --source-dir src/bcra_connector --output-dir docs/build/html
```

2. Refresh the ASCII tree injected into `README.md`:
```bash
python .skills/run_skill.py update_readme_tree --readme README.md --root .
```

3. Commit changes if any:
```bash
git add README.md docs/build/
git commit -m "docs: refresh API docs and README tree"
```
