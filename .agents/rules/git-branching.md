---
trigger: always_on
---

# Git Branch Protection Rule (`dev` Only Push / `main` PR-Merge Only)

This rule is **ABSOLUTE AND NON-NEGOTIABLE** for all AI agents and terminal commands in this workspace:

1. **NEVER commit directly to `main`.**
2. **NEVER push directly to `main`** (`git push origin main`, `git push origin HEAD:main`, `git push --all`, or force-pushing to `main` are strictly forbidden).
3. **`main` is PULL-REQUEST MERGE ONLY:** Changes enter `main` exclusively through GitHub Pull Request merges (from `dev` → `main`). Locally, `main` may only be fast-forward pulled (`git pull --ff-only origin main`).
4. **ONLY push code to `dev` (or feature branches cut from `dev` that target `dev`):**
   - Before running any `git commit` or `git push`, always check the active branch with `git branch --show-current`.
   - If the active branch is `main`, **STOP immediately**, do not commit or push, and switch to `dev` (or cut a feature branch from `dev`: `git checkout dev && git checkout -b <type>/p<phase>-<slug>`).
5. **If asked to "push to main" by mistake:** Refuse the direct push to `main`, explain this repository invariant, push to `dev` (or the feature branch) instead, and provide the GitHub PR link to merge into `main`.
