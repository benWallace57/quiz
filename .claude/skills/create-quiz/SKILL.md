---
name: create-quiz
description: Scaffold a new quiz from a template. Pass quiz type and topic as arguments.
arguments: [type, topic]
argument-hint: [network|audio] [topic-name]
allowed-tools: Bash(python3 *) Write Read Edit
user-invocable: true
---

# Create Quiz

Scaffold a new **$type** quiz about **$topic**.

## Steps

1. Read the template at `${CLAUDE_SKILL_DIR}/templates/$type.html`
2. Read the checklist at `${CLAUDE_SKILL_DIR}/references/checklist.md`
3. Generate a filename from the topic (kebab-case, e.g. "Premier League" → `premier-league.html`)
4. Customize the template:
   - Replace placeholder title with the topic name
   - Replace placeholder data with real data for the topic (search for datasets/APIs if needed)
   - Set an appropriate accent color
   - Update the header and completion messages
5. Write the new file to the project root
6. Run through the checklist to verify nothing is missed
7. Add the new quiz to `index.html` landing page

## Data sourcing

For network quizzes, you need entities + relationships. Common sources:
- Wikipedia/Wikidata for factual relationships
- Public APIs (PokeAPI, TMDB, MusicBrainz, etc.)
- CSV datasets from Kaggle

For audio quizzes, you need audio clips. Common sources:
- iTunes Search API (30s previews)
- freesound.org API
- Web Audio API synthesis

## Output

The final quiz file should be fully self-contained (all CSS/JS inline) and follow project conventions in CLAUDE.md.
