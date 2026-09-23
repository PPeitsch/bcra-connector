---
description: run bandit + safety to detect security vulnerabilities and outdated deps
---

# Security Vulnerability Scan

Runs static analysis (`bandit`) and dependency scanning (`safety`) against the codebase.

## Prerequisites

```bash
pip install bandit safety
```

## Steps

// turbo
1. Run the full security scan (SAST plus the dependency CVE check):
```bash
python "${CLAUDE_PLUGIN_ROOT}/run_skill.py" check_security_vulnerabilities --target-dir src/ --check-deps
```

2. Review the report output. Common findings for this project:
   - `bandit`: flags `requests` calls without cert verification (expected — controlled via `verify_ssl` param).
   - `safety`: checks `requirements.txt` against known CVE database.

3. (Optional) List outdated dependencies without touching anything:
```bash
pip list --outdated
```
