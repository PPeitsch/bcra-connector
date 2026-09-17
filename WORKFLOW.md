# Development Workflow (SOP) — BCRA Connector

This document is the detailed Standard Operating Procedure for working in this
repository, human or agent.

> **The canonical entry point is [AGENTS.md](./AGENTS.md).** Read it first — it
> contains the non-negotiable rules. This file expands on the procedure and holds the
> full release protocol.

---

## 1. Environment

| | |
|---|---|
| **OS** | Linux |
| **Shell** | bash |
| **Package manager** | `pip` with `venv` |
| **Build system** | `hatch` (configured in `pyproject.toml`) |
| **Version source** | `src/bcra_connector/__about__.py` |

All commands below are POSIX shell.

### One-time bootstrap

```bash
git submodule update --init --recursive   # required by .agent/workflows/*
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,pandas]"
pre-commit install
```

Install the `pandas` extra as well as `dev`: without it the DataFrame tests skip
rather than run, and you lose that coverage locally.

---

## 2. Initial exploration

At the start of every task:

```bash
git status                 # the workspace must be clean
git checkout main
git pull origin main       # never work from a stale main
```

Then read:
1. `CHANGELOG.md` — what shipped most recently.
2. `pyproject.toml` — current dependencies and tooling configuration.

---

## 3. Implementation flow (features / fixes)

### 3.1 Create a branch

Naming convention: `type/issue-id-short-description`

Types: `feature`, `fix`, `docs`, `refactor`, `chore`

```bash
git checkout -b fix/issue-52-setuptools-vuln
```

`CONTRIBUTING.md` requires an issue for any significant change. Create one first if
it does not exist; the branch name and the PR body both reference it.

### 3.2 Develop

- Make the change.
- Add or update tests — required for every fix and feature.
- If you add dependencies, update `pyproject.toml` (`dependencies` or
  `optional-dependencies`). `pyproject.toml` is authoritative.
- Update `CHANGELOG.md` under `## [Unreleased]` for any user-visible change.

### 3.3 Verify — mandatory

```bash
pre-commit run --all-files && pytest
```

- **If `pre-commit` rewrites files** (trailing whitespace, formatting), stage them and
  run it again until it exits 0.
- **Never skip this.** It is exactly what CI's Code Quality job runs; skipping it is
  the single most common cause of a red PR.
- If `pre-commit` passes locally but CI fails, the hook's `additional_dependencies`
  have drifted from the pinned dev dependencies. Fix the pin — do not work around it.

### 3.4 Commit

Format — **lowercase tag with a colon**, matching this repository's history:

```
[fix]: Concise description in 50 characters or less

Explain WHY the change is needed, wrapped at 72 characters. The diff
already shows what changed; use this space for motivation and context.

 - Bullet points are welcome

Resolves: #123
```

Valid tags: `[feature]:` `[fix]:` `[docs]:` `[refactor]:` `[chore]:` `[test]:` `[release]:`

```bash
git commit -m "[fix]: Update setuptools constraint" -m "Resolves: #52"
```

### 3.5 Open the pull request

```bash
git push -u origin HEAD
gh pr create --base main --title "[fix]: ..." --body "..."
```

- Base the body on `.github/PULL_REQUEST_TEMPLATE.md` and complete the checklists
  honestly. Mark items `n/a` with a reason rather than ticking them falsely.
- Start the body with the ⚡ token required by `CONTRIBUTING.md`.
- Reference the issue: `Fixes #N`.
- **One change per PR.** Do not bundle unrelated fixes.

### 3.6 Verify CI — mandatory

```bash
gh pr checks <PR_NUMBER>
gh run list --branch <branch-name>
```

- **Never merge without green CI.** Fix failures on the same branch.
- Never ignore a red check. If a failure is genuinely pre-existing and unrelated,
  state that in the PR body **with evidence** (for example the same failure
  reproduced on `main`).

> **Stacked PRs receive no CI.** `.github/workflows/test-and-publish.yaml` triggers on
> `pull_request: branches: [main]`. A PR targeting any other branch gets **no checks
> at all** — verify it locally and say so explicitly in the PR body.

### 3.7 Merge

Only when every check passes:

```bash
gh pr merge --admin --merge --delete-branch
```

**Always delete the branch on merge.** Use `--delete-branch`, or the "Delete branch"
button when merging through the web UI. This is not housekeeping:

- GitHub re-targets a **stacked** PR onto `main` only when its base branch is
  **deleted** on merge. If the base branch survives, the stacked PR keeps pointing at
  an already-merged branch, receives **no CI**, and goes stale unnoticed.
- This is exactly what happened to #86 after #85 was merged without deleting its
  branch.

After merging a PR that another PR was stacked on, verify the re-target:

```bash
gh pr view <N> --json baseRefName     # expect "main"
gh pr edit <N> --base main            # if it did not re-target
```

> **Repository setting:** enable **Settings -> General -> Automatically delete head
> branches**. The `--delete-branch` flag only covers CLI merges; the setting also
> covers merges done through the web UI, which is where this is most often missed.

---

## 4. Hard rules

1. **Never merge with errors.** Not if `pre-commit` fails, not if `pytest` fails, not
   if CI is red.
2. **`pre-commit run --all-files` before every commit.** If it auto-corrects files,
   stage them and commit again.
3. **`pytest` before opening a PR.**
4. **Do not invent commands.** Use the tooling defined here (`pip`, `venv`, `hatch`,
   `pre-commit`, `pytest`, `gh`).
5. **Never edit `src/bcra_connector/_version.py`** — generated by hatch.
6. **Never modify `.skills/`** — shared submodule used by other projects.
7. **Report honestly.** If something failed or was skipped, say so. Never claim a
   verification you did not run.

---

## 5. Release protocol

This project uses **release automation**. Do not create the GitHub release manually —
push a tag and let the workflow do it.

### 5.1 Decide the version

Read `src/bcra_connector/__about__.py` for the current version and choose the next one
using SemVer (patch / minor / major).

### 5.2 Update the version files

**`src/bcra_connector/__about__.py`**
```python
__version__ = "X.Y.Z"
```
> `docs/source/conf.py` reads this automatically — no manual edit needed.
> **Never edit `src/bcra_connector/_version.py`** (generated by hatch).

**`CHANGELOG.md`**
- Rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`.
- Add a fresh empty `## [Unreleased]` section above it.
- Update the comparison links at the bottom:
  `[X.Y.Z]: .../compare/vPrevious...vX.Y.Z`

### 5.3 Commit, tag and push

```bash
git add src/bcra_connector/__about__.py CHANGELOG.md
git commit -m "[release]: Version X.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

The tag must match the version exactly, with a `v` prefix.

### 5.4 Verify

```bash
gh run list
```

Confirm the "Test and Publish" workflow started for the tag.

---

## 6. Common problems

| Problem | Resolution |
|---------|-----------|
| **Linting failed in CI** | Run `pre-commit run --all-files` locally and commit the fixes. |
| **Local passes, CI fails (mypy)** | The pre-commit hook's `additional_dependencies` are unpinned and resolve differently from your venv. Pin them. |
| **DataFrame tests error instead of skipping** | Install the extra: `pip install -e ".[dev,pandas]"`. Tests must use `pytest.importorskip("pandas")`. |
| **Tag already exists** | `git tag -d vX.Y.Z` and `git push origin :refs/tags/vX.Y.Z`, then retry. |
| **Merge conflicts** | `git pull --rebase origin main` before pushing. |
| **`.agent/workflows/*` commands fail** | The submodule is not initialized: `git submodule update --init --recursive`. |
