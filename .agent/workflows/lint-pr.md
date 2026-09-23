---
description: checkout a PR, run ruff + black, push fixes automatically
---

# Lint & Format PR

Checks out a Pull Request branch, runs `ruff` and `black`, and pushes any
auto-fixed formatting back to the PR branch.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated.
- `ruff` and `black` available in the virtualenv.

## Steps

1. Check out the PR branch:
```bash
gh pr checkout <PR_NUMBER>
```

2. Run the linter and the formatter:
```bash
ruff check --fix src/ tests/
black src/ tests/
```

3. Push the fixes back, if there are any:
```bash
git diff --quiet || { git commit -am "style: apply ruff and black" && git push; }
```

> Never force-push someone else's PR branch: it discards work pushed in the
> meantime. A plain `git push` is enough for a fast-forward.
