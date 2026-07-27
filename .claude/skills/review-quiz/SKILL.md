---
name: review-quiz
description: Run a quality review on a quiz file — checks UX, accessibility, mobile, scoring logic.
context: fork
background: false
arguments: [file]
argument-hint: [quiz-file.html]
user-invocable: true
---

# Quiz Quality Review

Review **$file** against the criteria in `${CLAUDE_SKILL_DIR}/references/review-criteria.md`.

## Instructions

1. Read the quiz file at `$file`
2. Read the review criteria at `${CLAUDE_SKILL_DIR}/references/review-criteria.md`
3. Evaluate the quiz against each criterion, scoring 1-5
4. Note any bugs, missing features, or UX issues
5. Return a structured report with:
   - Overall score (out of 50)
   - Per-category scores and notes
   - Top 3 issues to fix (prioritized)
   - Any praise for things done well
