---
description: run bandit + safety to detect security vulnerabilities and outdated deps
---

# Security Vulnerability Scan

Runs static analysis (`bandit`) and dependency scanning (`safety`) against the codebase.

## Prerequisites

Install optional security extras if not already present:
```bash
pip install -e ".skills[all]"
```

## Steps

// turbo
1. Run the full security scan:
```bash
python .skills/run_skill.py check_security_vulnerabilities --target-dir src/
```

2. Review the report output. Common findings for this project:
   - `bandit`: flags `requests` calls without cert verification (expected — controlled via `verify_ssl` param).
   - `safety`: checks `requirements.txt` against known CVE database.

3. (Optional) Scan dependencies specifically:
```bash
python .skills/run_skill.py update_dependencies --check-only
```
