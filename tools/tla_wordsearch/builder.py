#!/usr/bin/env python3
"""
Word-first TLA wordsearch builder.

Grows a grid one TLA at a time using backtracking. Each new TLA must
overlap at least one existing cell (letter must match), and every placed
TLA must have at least one unique cell. Targets exactly 13 used cells
so 3 remain for the final TLA.

Usage:
    python builder.py                               # default N=7
    python builder.py --target 9
    python builder.py --seed DIY VAT                # start with these
    python builder.py --exclude OMG HRT STI IVF
    python builder.py --top 20
"""

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

from tla_candidates import POOL as DEFAULT_POOL, tier, category

# ── Grid geometry ─────────────────────────────────────────────────────

DIRS = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
DIR_NAMES = {
    (0, 1): "→", (0, -1): "←", (1, 0): "↓", (-1, 0): "↑",
    (1, 1): "↘", (1, -1): "↙", (-1, 1): "↗", (-1, -1): "↖",
}

ALL_COORDS = [(r, c) for r in range(4) for c in range(4)]

ALL_DIRECTED = []
for r in range(4):
    for c in range(4):
        for dr, dc in DIRS:
            r2, c2 = r + 2 * dr, c + 2 * dc
            if 0 <= r2 < 4 and 0 <= c2 < 4:
                ALL_DIRECTED.append(((r, c), (r + dr, c + dc), (r2, c2)))


def path_cells(path):
    return frozenset(path)


# ── Feasibility checks ───────────────────────────────────────────────

def can_still_reach_target(grid, placed, target_n, target_used=13):
    """Check if it's still possible to reach exactly target_used cells."""
    used = set()
    for _, path in placed:
        used.update(path)
    current = len(used)
    remaining = target_n - len(placed)

    if remaining == 0:
        return current == target_used

    # Best case: each remaining TLA adds 3 new cells
    # Worst case: each remaining TLA adds 1 new cell (2 overlap)
    max_possible = current + remaining * 3
    min_possible = current + remaining * 1

    return min_possible <= target_used <= max_possible


def all_have_unique_cell(grid, placed):
    """Every placed TLA has at least 1 cell not shared with any other."""
    if not placed:
        return True
    cell_count = Counter()
    for _, path in placed:
        for c in path:
            cell_count[c] += 1
    for _, path in placed:
        if not any(cell_count[c] == 1 for c in path):
            return False
    return True


def check_uniqueness_incremental(grid, tla, path):
    """Check that this TLA appears at exactly one directed path in the grid."""
    count = 0
    for p in ALL_DIRECTED:
        match = True
        for cell in p:
            if cell not in grid:
                match = False
                break
            if grid[cell] != tla[p.index(cell)] if cell in [p[0], p[1], p[2]] else True:
                match = False
                break
        if match:
            word = "".join(grid.get(c, "?") for c in p)
            if word == tla:
                count += 1
                if count > 1:
                    return False
    return True


def check_all_uniqueness(grid, placed):
    """Each placed TLA appears at exactly one of the 48 directed paths."""
    for tla, declared in placed:
        count = 0
        for p in ALL_DIRECTED:
            word = "".join(grid.get(c, "?") for c in p)
            if word == tla:
                count += 1
                if count > 1:
                    return False
    return True


# ── Candidate generation ─────────────────────────────────────────────

def find_placements(tla, grid, placed, target_n, target_used=13):
    """
    Find all valid directed paths where this TLA could be placed.
    Must overlap at least 1 existing cell (unless first placement),
    and letters must be consistent with existing grid.
    """
    used_cells = set()
    for _, path in placed:
        used_cells.update(path)

    results = []
    for p in ALL_DIRECTED:
        cells = [p[0], p[1], p[2]]

        # Check letter consistency
        ok = True
        new_cells = []
        for i, cell in enumerate(cells):
            if cell in grid:
                if grid[cell] != tla[i]:
                    ok = False
                    break
            else:
                new_cells.append(cell)
        if not ok:
            continue

        # First placement can go anywhere; subsequent must overlap
        if placed:
            overlap = sum(1 for c in cells if c in used_cells)
            if overlap == 0:
                continue

        # Check total cells wouldn't exceed target
        total_after = len(used_cells | set(cells))
        remaining_after = target_n - len(placed) - 1
        if remaining_after == 0:
            if total_after != target_used:
                continue
        else:
            max_possible = total_after + remaining_after * 3
            min_possible = total_after + remaining_after * 1
            if not (min_possible <= target_used <= max_possible):
                continue

        results.append(p)

    return results


# ── Scoring ──────────────────────────────────────────────────────────

def score_solution(placed, grid):
    tlas = [t for t, _ in placed]
    used_cells = set()
    for _, path in placed:
        used_cells.update(path)
    unused = sorted(set(ALL_COORDS) - used_cells)

    tla_score = sum(tier(t) for t in tlas)

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

    # Letter diversity bonus: unique letters across all TLAs
    all_letters = set(c for t in tlas for c in t)
    letter_diversity = len(all_letters)

    total = scatter + tla_score + len(dirs_used) + cat_bonus + letter_diversity - stack_penalty

    return {
        "score": total,
        "scatter": scatter,
        "tla_score": tla_score,
        "dirs": len(dirs_used),
        "stack_penalty": stack_penalty,
        "cat_diversity": cat_bonus,
        "letter_diversity": letter_diversity,
        "unused": unused,
    }


# ── Output ───────────────────────────────────────────────────────────

def print_solution(placed, grid, scores, rank=None):
    prefix = f"--- Solution {rank}: " if rank else "--- "
    print(
        f"\n{prefix}score={scores['score']} "
        f"(scatter={scores['scatter']}, tla={scores['tla_score']}, "
        f"dirs={scores['dirs']}, cats={scores['cat_diversity']}, "
        f"letters={scores['letter_diversity']}, "
        f"stack={scores['stack_penalty']})"
    )
    print(f"  Unused: {scores['unused']}")

    tlas = [t for t, _ in placed]
    gimmes = [t for t in tlas if tier(t) == 3]
    solids = [t for t in tlas if tier(t) == 2]
    stretches = [t for t in tlas if tier(t) == 1]
    print(f"  Gimmes:    {gimmes}")
    print(f"  Solids:    {solids}")
    print(f"  Stretches: {stretches}")

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
        unique_cells = [c for c in path if cc[c] == 1]
        cat = category(tla)
        print(f"  {tla} {arrow} {path[0]}→{path[2]}  unique={unique_cells}  [{cat}]")


# ── Builder core ─────────────────────────────────────────────────────

def build(pool, target_n=7, target_used=13, max_solutions=1000, seed=None, shuffle=False, timelimit=0):
    """
    Build grids by placing TLAs one at a time with backtracking.
    timelimit: seconds (0 = unlimited).
    """
    pool_set = set(pool)
    all_solutions = []
    nodes_explored = 0
    timed_out = False

    grid = {}           # cell -> letter
    placed = []         # [(tla, path), ...]
    used_tlas = set()

    # Pre-seed if requested
    if seed:
        for tla in seed:
            if tla not in pool_set:
                print(f"WARNING: seed TLA {tla} not in pool", file=sys.stderr)
                continue
            placements = find_placements(tla, grid, placed, target_n, target_used)
            if not placements:
                print(f"WARNING: no valid placement for seed {tla}", file=sys.stderr)
                continue
            # Take first valid placement for seed
            path = placements[0]
            for i, cell in enumerate(path):
                grid[cell] = tla[i]
            placed.append((tla, path))
            used_tlas.add(tla)

    def backtrack():
        nonlocal nodes_explored, timed_out
        nodes_explored += 1

        if len(all_solutions) >= max_solutions or timed_out:
            return

        if timelimit and nodes_explored % 10000 == 0:
            if time.time() - t0 > timelimit:
                timed_out = True
                return

        if nodes_explored % 100000 == 0:
            elapsed = time.time() - t0
            print(
                f"  {nodes_explored:,} nodes, {len(all_solutions)} solutions, "
                f"{elapsed:.0f}s",
                file=sys.stderr,
            )

        if len(placed) == target_n:
            # Check final validity
            used_cells = set()
            for _, path in placed:
                used_cells.update(path)
            if len(used_cells) != target_used:
                return
            if not all_have_unique_cell(grid, placed):
                return
            if not check_all_uniqueness(grid, placed):
                return

            scores = score_solution(placed, grid)
            all_solutions.append((list(placed), dict(grid), scores))
            return

        remaining_pool = sorted(pool_set - used_tlas)
        if shuffle:
            random.shuffle(remaining_pool)

        for tla in remaining_pool:
            if len(all_solutions) >= max_solutions:
                return

            placements = find_placements(tla, grid, placed, target_n, target_used)
            if not placements:
                continue

            for path in placements:
                if len(all_solutions) >= max_solutions:
                    return

                # Apply
                saved = {}
                for i, cell in enumerate(path):
                    if cell not in grid:
                        saved[cell] = None
                        grid[cell] = tla[i]

                used_tlas.add(tla)
                placed.append((tla, path))

                # Quick feasibility check
                if can_still_reach_target(grid, placed, target_n, target_used):
                    backtrack()

                # Undo
                placed.pop()
                used_tlas.discard(tla)
                for c in saved:
                    del grid[c]

    t0 = time.time()
    backtrack()
    elapsed = time.time() - t0

    print(
        f"\nDone: {len(all_solutions)} solutions, "
        f"{nodes_explored:,} nodes in {elapsed:.1f}s",
        file=sys.stderr,
    )

    return all_solutions


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Word-first TLA wordsearch builder")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--target", type=int, default=7)
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--seed", nargs="*", default=[])
    parser.add_argument("--max", type=int, default=1000,
                        help="Max solutions to find (default 1000)")
    parser.add_argument("--json", type=str)
    parser.add_argument("--shuffle", action="store_true",
                        help="Randomise TLA order to explore diverse solutions")
    parser.add_argument("--timelimit", type=int, default=0,
                        help="Time limit in seconds (0=unlimited)")
    args = parser.parse_args()

    pool = [t for t in DEFAULT_POOL if t not in set(args.exclude)]

    print(f"Pool: {len(pool)} TLAs, target: {args.target}", file=sys.stderr)
    if args.exclude:
        print(f"Excluding: {args.exclude}", file=sys.stderr)
    if args.seed:
        print(f"Seeding with: {args.seed}", file=sys.stderr)

    solutions = build(
        pool, target_n=args.target, max_solutions=args.max,
        seed=args.seed if args.seed else None,
        shuffle=args.shuffle,
        timelimit=args.timelimit,
    )

    solutions.sort(key=lambda x: x[2]["score"], reverse=True)

    for i, (placed, grid, scores) in enumerate(solutions[: args.top], 1):
        print_solution(placed, grid, scores, rank=i)

    if args.json and solutions:
        serialisable = []
        for placed, grid, scores in solutions:
            s = dict(scores)
            s["tlas"] = [(tla, [list(c) for c in path]) for tla, path in placed]
            s["grid"] = {f"{r},{c}": v for (r, c), v in grid.items()}
            s["unused"] = [list(u) for u in s["unused"]]
            serialisable.append(s)
        Path(args.json).write_text(json.dumps(serialisable, indent=2))
        print(f"\nSaved {len(serialisable)} solutions to {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
