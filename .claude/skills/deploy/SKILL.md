---
name: deploy
description: Deploy quiz changes to GitHub Pages — shows current git state and walks through push steps.
allowed-tools: Bash(git *) Bash(${CLAUDE_SKILL_DIR}/scripts/*)
user-invocable: true
---

# Deploy to GitHub Pages

## Current State

- Branch: !`git branch --show-current`
- Uncommitted changes: !`git status --short`
- Last deploy: !`git log origin/main -1 --format="%h %s (%cr)"`
- Files changed since last push: !`git diff --stat origin/main`

## Pre-Deploy Checks

Run `${CLAUDE_SKILL_DIR}/scripts/pre-deploy-check.sh` before deploying.

## Deploy Steps

1. Review uncommitted changes above — commit anything that should be included
2. Run pre-deploy checks (link validation, file existence)
3. Push to `main` branch (GitHub Pages auto-deploys from main)
4. Confirm deployment at https://benwallace57.github.io/quiz/

## Post-Deploy

- Verify the landing page loads
- Spot-check at least one quiz that was changed
- If anything is broken, revert with `git revert HEAD` and push again
