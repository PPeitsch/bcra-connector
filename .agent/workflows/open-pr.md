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
git push -u origin HEAD
```

2. Create the PR:
```bash
gh pr create --base main --title "<PR title>" --body "<PR description>"
```

> Pass `--draft` to open as a draft PR. If `gh` fails (not installed, not
> authenticated, HTTP 403), the branch is pushed but there is **no PR**: say so
> explicitly and hand over the link to open it by hand —
> `https://github.com/PPeitsch/bcra-connector/compare/main...<branch>?expand=1`.

3. (Optional) After the PR is open, check that CI went green:
```bash
gh pr checks --watch
```
