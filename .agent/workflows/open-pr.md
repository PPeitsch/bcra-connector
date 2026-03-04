---
description: open a GitHub Pull Request from the current branch
---

# Open Pull Request

Creates a PR on GitHub from the current feature or fix branch.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated.
- Branch already pushed to origin.

## Steps

1. Push the current branch if not already done:
```bash
git push origin HEAD
```

2. Create the PR:
```bash
python .skills/run_skill.py create_github_pr \
  --title "<PR title>" \
  --body "<PR description>" \
  --base main
```

> Pass `--draft` to open as a draft PR.

3. (Optional) After the PR is open, run tests and post results:
```bash
python .skills/run_skill.py run_tests_and_report \
  --command "pytest tests/ -v --tb=short" \
  --pr <PR_NUMBER> \
  --fail-only
```
