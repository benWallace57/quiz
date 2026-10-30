---
name: tla-wordsearch
description: Design and generate 4x4 TLA wordsearch puzzles. Covers grid construction, clue writing under the letter constraint, difficulty balance, and verification. Use when creating or editing TLA wordsearch puzzles.
when_to_use: tla wordsearch, TLA puzzle, acronym wordsearch, 3-letter acronym, wordsearch generator
allowed-tools: Bash(python3 *) Write Read Edit
user-invocable: true
---

# TLA Wordsearch Puzzle Design

A 4×4 grid hides 5–7 three-letter acronyms. Each TLA has a clue. Cross off all the TLAs and 3 leftover cells spell a hidden final TLA. The twist: no word in any clue may start with a letter in its target TLA.

**Primary format is print** (grid + clue list on paper). An online playable version is a bonus.

## The fun

This puzzle works in **both directions**:

- **Clue → grid**: you guess the TLA from the clue, then find it in the grid and cross off cells.
- **Grid → clue**: after solving a few, the remaining letters narrow what's possible. You can read the grid to help crack a hard clue — "the only unused T is at (1,3) and there's an F diagonal from it… TFL?"

This bidirectional solving is the core of the fun. Every solve should eliminate at least one cell that no other unsolved TLA uses, giving the player new information. If all cells are shared across multiple unsolved TLAs, the grid can't help you — avoid that.

The final TLA reveal is the payoff. The player knows from the start that 3 leftover cells spell something. As they solve, the final answer crystallises — ideally becoming guessable with 1–2 clues still unsolved.

## Rules

1. **Grid**: 4 rows × 4 columns, 16 uppercase letter cells.
2. **Targets**: 5–7 TLAs, each found along a straight 3-cell path (8 directions: horizontal, vertical, diagonal — forward or backward).
3. **Overlap**: target paths share cells. Total unique cells used by targets = exactly 13.
4. **Leftover**: the 3 unused cells spell the final TLA in reading order (top-to-bottom, left-to-right).
5. **Uniqueness**: each target TLA must appear at exactly ONE path in the grid. No ambiguity about where to find it.
6. **Clue constraint**: no word in a clue may start with any letter present in its target TLA. This is surfaced to the player as a deduction aid — they know about the rule.
7. Incidental non-target TLAs appearing in the grid are fine (normal wordsearch behaviour). They just can't be a duplicate of a target.

## Picking TLAs

Theme is **UK everyday** — acronyms a British adult encounters in normal life.

### Difficulty tiers

| Tier | Examples | Role in puzzle |
|------|----------|----------------|
| **Gimme** (everyone knows) | NHS, BBC, ATM, DIY, VAT, GPS | Anchor solves — get the player started, eliminate cells early |
| **Solid** (most people know) | MOT, TLC, VIP, IPA, ETA, PIN | Core of the puzzle — gettable from a good clue |
| **Stretch** (some need grid help) | OCR, OTP, TFL, PPI, NFC, APR | Reward for bidirectional solving — the clue alone is tough |

**A good puzzle has 1–2 gimmes, 3–4 solids, and 1–2 stretches.** The gimmes unlock cells that help with the stretches. The final TLA should be well-known (gimme tier) so the payoff feels earned.

### TLAs to avoid

- **Too technical**: API, DNS, SSH, FTP, GPU, SQL, RAM — most people don't encounter these daily
- **Too obscure**: CBE, TUC, CBI, HGV — recognisable but not fun to solve
- **Ambiguous**: LED (is it the light or the past tense?), WHO (the organisation or the word?) — fine in the grid but risky as a target since clues get confusing
- **Offensive or dark**: avoid anything that makes the puzzle unpleasant unless the theme calls for it

### Useful UK TLA pool

Health: NHS, CPR, ICU, MRI, STI, BMI, ECG
Transport: MOT, TFL, MPH, SUV, MOD, RAC
Media: BBC, ITV, DVD, LCD, LED, DAB
Money: VAT, APR, ISA, PPI, CEO, ATM, PIN, GBP, LTD
Tech: USB, SIM, GPS, PDF, FAQ, SSD, VPN, URL, OCR, NFC
Everyday: DIY, TLC, VIP, OMG, LOL, FYI, ETA, TBA, IPA, BBQ, BLT, OAP, OTP, WFH, RIP, IOU, BYO, TMI, SOS
Time: GMT, BST
Honours: MBE, OBE, RAF, SAS

## Grid construction

### Strategy: work backwards from the final TLA

1. **Pick the final TLA** — something satisfying and well-known (NHS, BBC, DIY, BBQ).
2. **Place the final TLA's letters** in 3 cells such that reading order (L→R, T→B) spells it. Note: the 3 cells don't need to be adjacent — they just need to be in the right reading-order sequence.
3. **Fill the remaining 13 cells** with target TLAs. Start with the stretches (hardest to place due to fewer valid positions), then layer in solids and gimmes.
4. **Check uniqueness** as you go — after placing each TLA, verify it only appears once across all 48 possible paths.

### Layout principles

- **Use all 8 directions.** Don't put everything reading left-to-right. Diagonals and backwards paths make the grid more interesting to search. The sample puzzle uses →, ↓, ↘, and ↙ — aim for at least 3 different directions.
- **Scatter the final TLA's cells.** If they cluster (e.g. top-right column), the player spots the answer immediately. Spread them: one high, one mid, one low, in different columns.
- **Overlap thoughtfully.** A cell shared by two TLAs means solving either one gives the player information about the other. This is good — but don't overlap so heavily that solving one TLA makes three others trivially obvious. Each solve should reveal exactly 1–2 new cells, not half the grid.
- **Avoid trivial placements.** Don't put TLAs in the first row reading left-to-right. The player's eye scans L→R naturally — make them work a bit.

### Cell-elimination check

After designing the grid, simulate the solve order. For each target (roughly easiest clue first):

- How many cells does this solve **newly reveal** (cells not shared with any other unsolved TLA)?
- Can the player use the newly revealed letters to narrow down the next clue?

If a solve reveals zero new cells (everything overlaps with still-unsolved TLAs), the grid isn't helping. Reorder targets or adjust overlaps so that each step gives something.

## Writing clues

The clue constraint is the defining feature. Every word in the clue must NOT start with any letter in the target TLA. This is hard — and that's the point.

### Process

1. **List the forbidden starting letters** for the TLA.
2. **Write the clue naturally first**, ignoring the constraint.
3. **Rewrite**, swapping forbidden-starting words for synonyms. Use a thesaurus. This often produces unexpected, evocative phrasing.
4. **Read it aloud.** If it sounds tortured or ungrammatical, rewrite from scratch with a different angle.

### What makes a good clue

- **Paints a scene or scenario**, not a dictionary definition. "Yearly garage check for wheels and brakes" beats "Annual vehicle examination."
- **6–12 words.** Shorter is better. Long clues feel like they're compensating for a bad constraint dodge.
- **Specific but not obscure.** "Hoppy British craft booze served from draught taps" is vivid and accessible. "Fermented cereal-based liquid" is technically correct but lifeless.
- **The constraint should be invisible.** A well-written constrained clue reads naturally — the player shouldn't feel the strain of the constraint unless they look for it.

### Constraint difficulty by TLA

Some TLAs are much harder to clue than others because their letters are common word-starters:

| Hard to clue (common starters) | Easier to clue (rare starters) |
|------|------|
| S, T, C, A, B, P, M, D | X, Z, Q, J, K, V, Y, W |

A TLA like **SOS** (can't start with S or O) is brutal — S and O are extremely common word-starters. **VIP** (can't start with V, I, or P) is easier — V-starting words are rare.

Factor this in when selecting TLAs. If you have two stretches that are also hard-to-clue, the puzzle may be too painful.

### Clue testing

For each clue, ask: "Could this clue plausibly describe a DIFFERENT well-known TLA?" If yes, rewrite. The clue must point unambiguously to its target — especially since the player knows the constraint rule and will use forbidden-starting-letter elimination as a deduction tool.

## Verification

**Always run the verifier before finalising a puzzle.**

```bash
python3 tools/tla_wordsearch/verify.py puzzle.json
```

The verifier checks:
- Grid is 4×4 uppercase
- Declared paths spell the right letters in straight lines
- Each target TLA appears at exactly one grid path
- Exactly 13 cells used, 3 leftover spelling the final TLA
- Clue constraint holds (no forbidden starting letters)
- Flags incidental known TLAs (info, not blocking)

Fix all ERRORs. Review WARNs — an unknown TLA in the dictionary just means you should confirm it's real.

## JSON schema

```json
{
  "puzzle_id": "uk_everyday_01",
  "grid": [
    ["A", "B", "C", "D"],
    ["E", "F", "G", "H"],
    ["I", "J", "K", "L"],
    ["M", "N", "O", "P"]
  ],
  "target_answers": [
    {
      "tla": "ABC",
      "path": [[0,0], [0,1], [0,2]],
      "clue": "Description without words starting with A, B, or C"
    }
  ],
  "final_tla": "XYZ"
}
```

Grid coordinates are `[row, col]`, zero-indexed. Path is an ordered list of 3 `[row, col]` pairs forming a straight line.

## Output

Write the puzzle JSON to `tools/tla_wordsearch/puzzles/<puzzle_id>.json`, then run verification:

```bash
python3 tools/tla_wordsearch/verify.py tools/tla_wordsearch/puzzles/<puzzle_id>.json
```

## Common pitfalls

1. **All-horizontal layout.** Every TLA reads left-to-right in the top rows. Boring to search, trivial to find. Use diagonals and backwards paths.
2. **Only gimmes.** BBC, NHS, ATM, DIY, GPS, VAT, LOL — too easy. No deduction needed. Mix in stretches.
3. **Only stretches.** OCR, NFC, PPI, APR, OTP — too hard. No footholds. The player gives up.
4. **Clue constraint violations.** Easy to miss. The verifier catches these — run it.
5. **Ambiguous TLA placement.** A TLA appearing at two grid paths means the player doesn't know which to cross off. The verifier catches this too.
6. **Dead-end grid state.** After solving the easiest 3 TLAs, all remaining cells overlap — the grid can't help anymore. Simulate the solve to check.
7. **Final TLA is obscure.** The hidden answer should be the most satisfying moment. Don't make it something niche.
8. **Tortured clues.** If a clue reads like a bad thesaurus explosion, rewrite it from a different angle instead of synonym-swapping every word.
