#!/usr/bin/env python3
"""
Max-overlap TLA wordsearch solver.

Phase 1: enumerate C(24, N) undirected line combinations, filter by
         13-cell coverage + unique-cell property.
Phase 2: assign TLAs via backtracking with most-constrained-first ordering,
         trying both directions per line. Pattern index for fast lookup.

Usage:
    python max_overlap_solver.py                          # N=7
    python max_overlap_solver.py --target 8               # N=8
    python max_overlap_solver.py --target 9               # N=9
    python max_overlap_solver.py --exclude CIA FBI
    python max_overlap_solver.py --require BBC DIY
    python max_overlap_solver.py --top 50 --json out.json
"""

import argparse
import json
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

from tla_candidates import POOL as DEFAULT_POOL, tier, category

# ── Grid geometry ─────────────────────────────────────────────────────

DIRS = [(0,1),(1,0),(1,1),(1,-1),(0,-1),(-1,0),(-1,-1),(-1,1)]
DIR_NAMES = {
    (0,1): "→", (0,-1): "←", (1,0): "↓", (-1,0): "↑",
    (1,1): "↘", (1,-1): "↙", (-1,1): "↗", (-1,-1): "↖",
}

ALL_COORDS = [(r, c) for r in range(4) for c in range(4)]

# Build 48 directed paths
ALL_DIRECTED = []
for r in range(4):
    for c in range(4):
        for dr, dc in DIRS:
            r2, c2 = r + 2 * dr, c + 2 * dc
            if 0 <= r2 < 4 and 0 <= c2 < 4:
                ALL_DIRECTED.append(((r, c), (r + dr, c + dc), (r2, c2)))

# Build 24 undirected lines (frozenset of 3 cells)
# Each line maps to its two directed paths (forward and reverse)
_seen = set()
LINES = []          # list of frozenset of 3 cells
LINE_DIRS = []      # list of (forward_path, reverse_path)
for p in ALL_DIRECTED:
    key = frozenset(p)
    if key not in _seen:
        _seen.add(key)
        rev = (p[2], p[1], p[0])
        LINES.append(key)
        LINE_DIRS.append((p, rev))

assert len(LINES) == 24


# ── Phase 1: enumerate valid line sets ────────────────────────────────

def find_valid_layouts(target_n=7, target_used=13, exact_unique=True):
    """
    Enumerate all C(24, target_n) line combinations.
    Keep those that cover exactly target_used cells and where
    each line has at least 1 singly-covered cell.
    If exact_unique=True (legacy), require exactly 1 unique cell per line.
    """
    layouts = []
    checked = 0

    for combo in combinations(range(24), target_n):
        checked += 1

        cell_count = Counter()
        for li in combo:
            for c in LINES[li]:
                cell_count[c] += 1

        if len(cell_count) != target_used:
            continue

        ok = True
        for li in combo:
            unique_count = sum(1 for c in LINES[li] if cell_count[c] == 1)
            if exact_unique:
                if unique_count != 1:
                    ok = False
                    break
            else:
                if unique_count < 1:
                    ok = False
                    break
        if not ok:
            continue

        layouts.append(combo)

    return layouts, checked


# ── Phase 2: assign TLAs to lines ────────────────────────────────────

def build_pattern_index(pool):
    """
    Index TLAs by partial patterns for fast lookup.
    pattern_index[pos][letter] = set of TLAs with that letter at that position.
    """
    idx = [{} for _ in range(3)]
    for tla in pool:
        for i, ch in enumerate(tla):
            idx[i].setdefault(ch, set()).add(tla)
    return idx


def get_candidates(line_idx, direction, assignment, pool_set, pattern_index):
    """
    Return TLAs from pool that fit the given directed path,
    consistent with existing letter assignments.
    """
    path = direction  # a directed 3-cell path
    candidates = None

    for i, cell in enumerate(path):
        if cell in assignment:
            letter = assignment[cell]
            matching = pattern_index[i].get(letter, set())
            if candidates is None:
                candidates = set(matching)
            else:
                candidates &= matching
            if not candidates:
                return []
        # If cell not assigned, no constraint from this position

    if candidates is None:
        # No cells assigned yet — all pool TLAs are candidates
        return list(pool_set)

    return list(candidates & pool_set)


def assign_tlas(layout, pool, max_solutions=0):
    """
    Backtracking TLA assignment with most-constrained-first ordering.
    For each line, tries both directions.
    max_solutions: stop after finding this many (0 = unlimited).
    """
    pattern_index = build_pattern_index(pool)
    pool_set = set(pool)
    n = len(layout)

    assignment = {}     # cell -> letter
    used_tlas = set()
    result = []
    remaining = list(range(n))  # indices into layout

    all_solutions = []
    hit_cap = False

    def count_options(layout_idx):
        li = layout[layout_idx]
        fwd, rev = LINE_DIRS[li]
        c1 = get_candidates(li, fwd, assignment, pool_set - used_tlas, pattern_index)
        c2 = get_candidates(li, rev, assignment, pool_set - used_tlas, pattern_index)
        all_opts = set(c1) | set(c2)
        return len(all_opts)

    def backtrack():
        nonlocal hit_cap
        if hit_cap:
            return
        if not remaining:
            if check_uniqueness(assignment, result):
                all_solutions.append(list(result))
                if max_solutions and len(all_solutions) >= max_solutions:
                    hit_cap = True
            return

        best = min(remaining, key=count_options)
        li = layout[best]
        fwd, rev = LINE_DIRS[li]

        remaining.remove(best)

        for directed_path in (fwd, rev):
            if hit_cap:
                break
            candidates = get_candidates(li, directed_path, assignment,
                                        pool_set - used_tlas, pattern_index)
            for tla in candidates:
                if hit_cap:
                    break
                saved = {}
                for i, cell in enumerate(directed_path):
                    if cell not in assignment:
                        saved[cell] = None
                        assignment[cell] = tla[i]

                used_tlas.add(tla)
                result.append((tla, directed_path))

                backtrack()

                result.pop()
                used_tlas.discard(tla)
                for c in saved:
                    del assignment[c]

        remaining.append(best)

    backtrack()
    return all_solutions


def check_uniqueness(assignment, tla_paths):
    """Each placed TLA appears at exactly one of the 48 directed paths."""
    for tla, declared in tla_paths:
        count = 0
        for p in ALL_DIRECTED:
            word = "".join(assignment.get(c, "?") for c in p)
            if word == tla:
                count += 1
                if count > 1:
                    return False
    return True


# ── Scoring ───────────────────────────────────────────────────────────

def score_solution(placed, assignment):
    tlas = [t for t, _ in placed]
    used_cells = set()
    for _, path in placed:
        used_cells.update(path)
    unused = sorted(set(ALL_COORDS) - used_cells)

    tla_score = sum(tier(t) for t in tlas)
    gimmes = [t for t in tlas if tier(t) == 3]
    solids = [t for t in tlas if tier(t) == 2]
    stretches = [t for t in tlas if tier(t) == 1]

    dirs_used = set()
    for _, path in placed:
        dr = path[1][0] - path[0][0]
        dc = path[1][1] - path[0][1]
        dirs_used.add((dr, dc))

    rows = set(c[0] for c in unused)
    cols = set(c[1] for c in unused)
    scatter = len(rows) + len(cols)

    # Stacking penalty
    stack_penalty = 0
    horiz = []
    for _, p in placed:
        rs = set(c[0] for c in p)
        cs = set(c[1] for c in p)
        if len(rs) == 1:
            horiz.append((list(rs)[0], cs))
    for i in range(len(horiz)):
        for j in range(i + 1, len(horiz)):
            if abs(horiz[i][0] - horiz[j][0]) == 1:
                overlap = len(horiz[i][1] & horiz[j][1])
                if overlap >= 2:
                    stack_penalty += overlap - 1

    cats = set(category(t) for t in tlas)
    cat_bonus = len(cats)

    total = scatter + tla_score + len(dirs_used) + cat_bonus - stack_penalty

    return {
        "score": total,
        "scatter": scatter,
        "tla_score": tla_score,
        "dirs": len(dirs_used),
        "stack_penalty": stack_penalty,
        "cat_diversity": cat_bonus,
        "gimmes": gimmes,
        "solids": solids,
        "stretches": stretches,
        "unused": unused,
    }


# ── Output ────────────────────────────────────────────────────────────

def print_solution(placed, grid, scores, rank=None):
    prefix = f"--- Solution {rank}: " if rank else "--- "
    print(
        f"\n{prefix}score={scores['score']} "
        f"(scatter={scores['scatter']}, tla={scores['tla_score']}, "
        f"dirs={scores['dirs']}, cats={scores['cat_diversity']}, "
        f"stack={scores['stack_penalty']})"
    )
    print(f"  Unused: {scores['unused']}")
    print(f"  Gimmes:    {scores['gimmes']}")
    print(f"  Solids:    {scores['solids']}")
    print(f"  Stretches: {scores['stretches']}")

    display = [["?"] * 4 for _ in range(4)]
    for (r, c), letter in grid.items():
        display[r][c] = letter
    for row in display:
        print(f"  {' '.join(row)}")

    cc = Counter()
    for _, path in placed:
        for c in path:
            cc[c] += 1

    for tla, path in placed:
        dr = path[1][0] - path[0][0]
        dc = path[1][1] - path[0][1]
        arrow = DIR_NAMES[(dr, dc)]
        uniq = [c for c in path if cc[c] == 1][0]
        cat = category(tla)
        print(f"  {tla} {arrow} {path[0]}→{path[2]}  unique={uniq}  [{cat}]")


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Max-overlap TLA wordsearch solver")
    parser.add_argument("--top", type=int, default=20, help="Show top N results")
    parser.add_argument("--target", type=int, default=7,
                        help="Number of TLAs (default 7)")
    parser.add_argument("--exclude", nargs="*", default=[], help="TLAs to exclude")
    parser.add_argument("--require", nargs="*", default=[], help="TLAs that must appear")
    parser.add_argument("--json", type=str, help="Save all solutions to JSON file")
    parser.add_argument("--cap", type=int, default=500,
                        help="Max solutions per layout (0=unlimited, default 500)")
    parser.add_argument("--relaxed", action="store_true",
                        help="Allow at-least-1 unique cell per TLA (not exactly 1)")
    args = parser.parse_args()

    pool = [t for t in DEFAULT_POOL if t not in set(args.exclude)]
    if args.require:
        missing = set(args.require) - set(pool)
        if missing:
            print(f"ERROR: required TLAs not in pool: {missing}", file=sys.stderr)
            sys.exit(1)
        required = sorted(args.require)
        rest = [t for t in pool if t not in set(args.require)]
        pool = required + rest

    print(f"Pool: {len(pool)} TLAs, target: {args.target}", file=sys.stderr)
    if args.exclude:
        print(f"Excluding: {args.exclude}", file=sys.stderr)
    if args.require:
        print(f"Requiring: {args.require}", file=sys.stderr)

    # Phase 1
    t0 = time.time()
    layouts, checked = find_valid_layouts(args.target, exact_unique=not args.relaxed)
    t1 = time.time()
    print(
        f"Phase 1: {len(layouts)} valid layouts from "
        f"{checked:,} combinations in {t1-t0:.1f}s",
        file=sys.stderr,
    )

    # Phase 2
    all_solutions = []
    for i, layout in enumerate(layouts):
        elapsed = time.time() - t0
        if (i + 1) % 10 == 0 or i == 0 or elapsed > 10:
            print(
                f"  Phase 2: layout {i+1}/{len(layouts)}, "
                f"{len(all_solutions)} solutions so far, {elapsed:.0f}s",
                file=sys.stderr,
            )

        solutions = assign_tlas(layout, pool, max_solutions=args.cap)
        for placed in solutions:
            # Build assignment dict
            assignment = {}
            for tla, path in placed:
                for j, cell in enumerate(path):
                    assignment[cell] = tla[j]

            # Filter for required TLAs
            if args.require:
                tla_set = {t for t, _ in placed}
                if not set(args.require).issubset(tla_set):
                    continue

            scores = score_solution(placed, assignment)
            all_solutions.append((placed, assignment, scores))

    elapsed = time.time() - t0
    print(
        f"\nDone: {len(all_solutions)} solutions from "
        f"{len(layouts)} layouts in {elapsed:.1f}s",
        file=sys.stderr,
    )

    all_solutions.sort(key=lambda x: x[2]["score"], reverse=True)

    for i, (placed, grid, scores) in enumerate(all_solutions[: args.top], 1):
        print_solution(placed, grid, scores, rank=i)

    if args.json and all_solutions:
        serialisable = []
        for placed, grid, scores in all_solutions:
            s = dict(scores)
            s["tlas"] = [(tla, [list(c) for c in path]) for tla, path in placed]
            s["grid"] = {f"{r},{c}": v for (r, c), v in grid.items()}
            s["unused"] = [list(u) for u in s["unused"]]
            serialisable.append(s)
        Path(args.json).write_text(json.dumps(serialisable, indent=2))
        print(f"\nSaved {len(serialisable)} solutions to {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
