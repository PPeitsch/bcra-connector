---
description: full release workflow — changelog, version bump, tag push
---

# Release Workflow

End-to-end steps to publish a new version of `bcra-connector`.
See also [WORKFLOW.md](../../WORKFLOW.md) for the full SOP.

## Steps

1. Ensure you are on `main` and the working tree is clean:
```bash
git checkout main && git pull --ff-only
git status
```

2. Add the release entry to `CHANGELOG.md` (Keep a Changelog format, history intact):
```bash
python "${CLAUDE_PLUGIN_ROOT}/run_skill.py" update_changelog \
  --version v<NEW_VERSION> \
  --added "- ..." --fixed "- ..."
```

3. Bump the version in `src/bcra_connector/__about__.py` manually (single source of truth).
   Also verify `docs/source/conf.py` picks it up automatically (it imports from `__about__`).

4. Commit the release artifacts:
```bash
git add CHANGELOG.md src/bcra_connector/__about__.py
git commit -m "chore: release v<NEW_VERSION>"
git push origin main
```

5. Push the tag — the skill waits for the branch workflows to pass first, because
   pushing the tag alongside the commit collides with the release workflow:
```bash
python "${CLAUDE_PLUGIN_ROOT}/run_skill.py" release_tag_push v<NEW_VERSION> --branch main
```
