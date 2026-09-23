---
description: run the test suite and optionally report results to a GitHub PR
---

# Run Tests & Report

Runs `pytest` against the full test suite and prints the results.
Optionally posts a summary comment on an open GitHub PR.

## Steps

// turbo
1. Run the test suite and display results:
```bash
pytest tests/ -v --tb=short
```

2. (Optional) If working on a PR and you want to comment the results, capture the
   summary and post it:
```bash
pytest tests/ --tb=short -q > /tmp/pytest-report.txt 2>&1; tail -20 /tmp/pytest-report.txt
gh pr comment <PR_NUMBER> --body "$(printf '```\n%s\n```' "$(tail -20 /tmp/pytest-report.txt)")"
```

> Only comment when it adds something the PR does not already show — CI already
> reports its own result on every push.
