---
description: checkout a PR, run ruff + black, push fixes automatically
---

# Lint & Format PR

Checks out a Pull Request branch, runs `ruff` and `black`, and force-pushes any
auto-fixed formatting back to the PR branch.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated.
- `ruff` and `black` available in the virtualenv.

## Steps

// turbo
1. Detect OS/shell:
```bash
python .skills/run_skill.py detect_os_and_terminal
```

2. Run linter and auto-fix on the target PR:
```bash
python .skills/run_skill.py lint_and_format_pr --pr <PR_NUMBER>
```

> The skill will: checkout the PR branch → run `ruff --fix` + `black` → commit + force-push any changes.
