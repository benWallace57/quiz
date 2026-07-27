---
name: check-publish
description: Validate all quizzes are ready to publish — checks links, file integrity, JS syntax, and consistency.
allowed-tools: Bash(node *) Bash(python3 *) Bash(grep *) Bash(wc *) Bash(find *) Read
user-invocable: true
---

# Check Publish

Validate that all quiz files in the project are ready for deployment.

## Checks to run

### 1. File integrity
- All HTML files referenced in `index.html` exist
- All HTML files are non-empty and have valid `<html>`, `<head>`, `<body>` tags
- No placeholder text remains ({{TITLE}}, {{ACCENT_COLOR}}, PLACEHOLDER, TODO)

### 2. JavaScript syntax
- Extract `<script>` content from each HTML file and validate with `node --check`
- No `console.log` debugging statements (console.error in catch blocks is OK)

### 3. Asset references
- All `src="..."` and `href="..."` paths resolve to existing local files (skip CDN URLs)
- All sprite/image paths referenced in JS data exist on disk

### 4. Data consistency
- Quiz data arrays are non-empty
- No duplicate IDs in node/entity data
- Scores and completion logic reference correct totals

### 5. Cross-quiz consistency
- All network quizzes load vis-network from the same CDN version
- All quizzes use the project dark theme (background: #0d1117 or #1a1a2e)
- All quizzes have a completion modal

### 6. Landing page
- Every quiz HTML file has a corresponding card in `index.html`
- No dead links in the landing page

## Output

Report as a checklist with PASS/FAIL/WARN for each check. Summarize any failures at the end with file and line number.
