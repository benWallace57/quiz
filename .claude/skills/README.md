# Skills Directory

This project demonstrates advanced Claude Code skill features for managing a quiz codebase. Each skill showcases different capabilities that would scale to larger repositories.

## Skills Overview

```
.claude/skills/
├── audio-quiz/          (basic reference skill)
├── network-quiz/        (basic reference skill)
├── create-quiz/         (parameterized + templates + tool approval)
├── deploy/              (dynamic context injection + shell scripts)
├── review-quiz/         (subagent fork)
├── data-pipeline/       (path-scoped auto-activation)
└── fix-quiz/            (dynamic context + arguments)
```

---

## Feature Demonstrations

### 1. Parameters / Arguments — `create-quiz`

Skills can accept arguments when invoked, making them reusable across different inputs.

```yaml
arguments: [type, topic]
argument-hint: [network|audio] [topic-name]
```

**Usage:** `/create-quiz network "Formula 1"`

The arguments `$type` and `$topic` are substituted into the skill body, so a single skill handles scaffolding any quiz type about any topic.

---

### 2. Resource Files (Templates + References) — `create-quiz`

Skills aren't limited to a single SKILL.md. The directory can contain supporting files:

```
create-quiz/
├── SKILL.md
├── templates/
│   ├── network.html      ← starter HTML with placeholders
│   └── audio.html        ← starter HTML for audio quizzes
└── references/
    └── checklist.md      ← pre-launch quality checklist
```

The skill instructions reference these via `${CLAUDE_SKILL_DIR}/templates/$type.html`, and Claude reads them on demand — they don't bloat every session's context.

---

### 3. Dynamic Context Injection — `deploy`

Shell commands prefixed with `!` execute at skill-load time and inject their output directly into the prompt:

```markdown
- Branch: !`git branch --show-current`
- Uncommitted: !`git status --short`
- Last deploy: !`git log origin/main -1 --format="%h %s (%cr)"`
```

When you invoke `/deploy`, Claude already sees the current git state — no need to ask it to run `git status` first. The prompt arrives pre-populated with live data.

---

### 4. Shell Scripts — `deploy`

Skills can bundle executable scripts that Claude is pre-approved to run:

```
deploy/
├── SKILL.md
└── scripts/
    └── pre-deploy-check.sh   ← validates links, checks file sizes, scans for secrets
```

Combined with `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/*)`, Claude can execute these without permission prompts.

---

### 5. Tool Pre-Approval — `create-quiz`, `deploy`, `fix-quiz`

The `allowed-tools` frontmatter field pre-approves specific tools for the duration of the skill, reducing permission prompts:

```yaml
# create-quiz — can write new files without asking
allowed-tools: Bash(python3 *) Write Read Edit

# deploy — can run git commands and custom scripts
allowed-tools: Bash(git *) Bash(${CLAUDE_SKILL_DIR}/scripts/*)

# fix-quiz — can spin up a server and run node
allowed-tools: Bash(python3 -m http.server *) Bash(node *) Read Edit
```

---

### 6. Subagent Execution (context: fork) — `review-quiz`

A skill with `context: fork` runs in an isolated subagent — a separate Claude instance that doesn't see your conversation history:

```yaml
context: fork
background: false
```

This is useful for structured, repeatable tasks. The review agent reads the quiz file, evaluates it against a rubric (`references/review-criteria.md`), and returns a scored report. It can't be influenced by earlier conversation context.

`background: false` means the main session waits for the result. Set `background: true` to keep working while the review runs.

---

### 7. Path-Scoped Auto-Activation — `data-pipeline`

Skills can auto-load when Claude edits files matching a glob pattern:

```yaml
paths: ["generate_*.py", "**/*_generator.py", "**/*_data.py"]
```

When you edit `generate_music_quiz.py`, the `data-pipeline` skill activates automatically — Claude gains access to the API catalog and pipeline patterns without being explicitly invoked. No `/data-pipeline` command needed.

---

### 8. Dynamic Context with Arguments — `fix-quiz`

Combines arguments with dynamic context injection to introspect the target file at load time:

```markdown
Lines: !`wc -l $file | awk '{print $1}'`
Functions: !`grep -c 'function ' $file`

## Script Structure
!`grep -n 'function \|addEventListener\|\.on(' $file | head -40`
```

When invoked as `/fix-quiz pokemon.html`, Claude's prompt arrives pre-loaded with the file's function list and state variables — it can jump straight to debugging.

---

## How This Scales

In a larger repository, these features compose:

- **Path-scoped skills** keep irrelevant instructions out of context (a backend dev never sees frontend skills)
- **Parameterized skills** replace dozens of near-duplicate skills with one reusable template
- **Resource directories** let you version templates and references alongside their skill
- **Dynamic context** eliminates the "first, check the current state" preamble from every interaction
- **Subagent forks** isolate expensive/structured tasks (reviews, migrations, audits) from the conversation
- **Tool pre-approval** streamlines repetitive workflows where permission prompts add friction

A monorepo might have 20-50 skills organized by team or domain, with path scoping ensuring each developer only activates what's relevant to their current work.
