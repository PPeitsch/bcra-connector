---
description: run the test suite and optionally report results to a GitHub PR
---

# Run Tests & Report

Runs `pytest` against the full test suite and prints the results.
Optionally posts a summary comment on an open GitHub PR.

## Steps

// turbo
1. Detect OS and shell to ensure correct command formatting:
```bash
python .skills/run_skill.py detect_os_and_terminal
```

// turbo
2. Run the test suite and display results:
```bash
python .skills/run_skill.py run_tests_and_report --command "pytest tests/ -v --tb=short"
```

3. (Optional) If working on a PR and you want to comment results:
```bash
python .skills/run_skill.py run_tests_and_report --command "pytest tests/ -v --tb=short" --pr <PR_NUMBER>
```

> Use `--fail-only` to comment only if tests fail.
