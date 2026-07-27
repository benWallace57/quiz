---
name: fix-quiz
description: Debug and fix issues in a specific quiz file. Injects file structure and JS function list.
arguments: [file]
argument-hint: [quiz-file.html]
allowed-tools: Bash(python3 -m http.server *) Bash(node *) Read Edit
user-invocable: true
---

# Fix Quiz

Debug and fix the reported issue in **$file**.

## File Overview

Lines: !`wc -l $file | awk '{print $1}'`
Functions: !`grep -c 'function ' $file`

## Script Structure

```
!`grep -n 'function \|addEventListener\|\.on(' $file | head -40`
```

## Game State Variables

```
!`grep -n 'let \|const .*=' $file | grep -i 'state\|game\|score\|attempt\|reveal\|select' | head -20`
```

## Debugging Steps

1. Read the file and understand the game flow
2. Identify the reported bug's location using the structure above
3. Check for common issues:
   - Event listener not firing (wrong selector, missing element)
   - State not updating (set vs array, object reference)
   - vis-network API misuse (update vs set, node ID types)
   - CSS z-index conflicts (modal hidden behind network)
   - Audio context not resumed (browser autoplay policy)
4. Fix the issue with minimal changes
5. Verify no regressions in surrounding logic
