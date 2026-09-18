# Contributing — branching & CI

## Branching model (GitFlow-lite)
- **`main`** — stable / release. No direct commits. Receives merges **only from `develop`**.
- **`develop`** — integration branch. All work lands here first.
- **`feature/*`** — branch off `develop`, PR back into `develop`.

Flow: **`feature/* → develop → main`**. A release is a `develop → main` PR.

## Rules (enforced)
- Open PRs against **`develop`**, never `main`.
- A PR into `main` is allowed **only from `develop`** — the *Branch policy* check fails otherwise.
- **CI must pass** before merge: error-lint (ruff), notebook parse, shell lint.
- `main` is branch-protected (a PR is required to change it).

## Local flow
```bash
git checkout develop && git pull
git checkout -b feature/my-change
# ...work...
git push -u origin feature/my-change
gh pr create --base develop            # ALWAYS --base develop
```

## Releasing
When `develop` is green and ready:
```bash
gh pr create --base main --head develop --title "Release: <summary>"
```
