---
description: full release workflow — changelog, version bump, tag push
---

# Release Workflow

End-to-end steps to publish a new version of `bcra-connector`.
See also [WORKFLOW.md](../../WORKFLOW.md) for the full SOP.

## Steps

1. Ensure you are on `main` and the working tree is clean:
```bash
git checkout main
git status
```

2. Update `CHANGELOG.md` from the git log since the last tag:
```bash
python .skills/run_skill.py update_changelog --version <NEW_VERSION>
```

3. Bump the version in `src/bcra_connector/__about__.py` manually (single source of truth).
   Also verify `docs/source/conf.py` picks it up automatically (it imports from `__about__`).

4. Commit the release artifacts:
```bash
git add CHANGELOG.md src/bcra_connector/__about__.py
git commit -m "chore: release v<NEW_VERSION>"
git push origin main
```

5. Wait for CI to pass, then push the tag:
```bash
python .skills/run_skill.py release_tag_push --tag v<NEW_VERSION> --branch main
```

> `release_tag_push` polls the GitHub Actions workflow status and only pushes when green.
