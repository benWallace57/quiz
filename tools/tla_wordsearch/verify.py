#!/usr/bin/env python3
"""
TLA Wordsearch puzzle verifier.

Usage:
    python verify.py                    # verify built-in sample
    python verify.py puzzle.json        # verify a puzzle file
    python verify.py --all puzzles/     # verify all .json in a directory
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# UK everyday TLAs — used to validate targets are real and flag known accidentals.
# Not exhaustive; puzzles can extend this per-puzzle if needed.
UK_EVERYDAY_TLAS: Set[str] = {
    # Health & emergency
    "NHS", "CPR", "AED", "ICU", "MRI", "STI", "OCD", "CBD", "PPE", "PCR",
    "LFT", "BMI", "DNR", "ECG",
    # Transport & driving
    "MOT", "TFL", "MPH", "MPG", "SUV", "HGV", "MOD",
    # Media & broadcasting
    "BBC", "ITV", "DVD", "LCD", "LED", "VHS", "DAB",
    # Money & business
    "VAT", "APR", "ISA", "PPI", "CEO", "CFO", "CTO", "GBP", "ATM", "PIN",
    "LTD", "PLC",
    # Tech & internet
    "USB", "SIM", "NFC", "VPN", "URL", "GPS", "API", "PDF", "FAQ", "SSD",
    "RAM", "ROM", "CPU", "GPU", "DNS", "FTP", "SSH", "OCR",
    # Honours & military
    "MBE", "OBE", "CBE", "RAF", "SAS",
    # Everyday expressions
    "DIY", "TLC", "VIP", "OMG", "LOL", "WTF", "FYI", "BTW", "BRB", "ETA",
    "TBA", "TBC", "SOS", "IPA", "BBQ", "BLT", "OAP", "OTP", "TMI", "BYO",
    "ABS", "PTO", "WFH", "RIP", "IOU",
    # Time
    "GMT", "BST", "UTC",
    # Gaming & culture
    "NPC", "RPG", "DLC", "AFK", "FPS", "DND", "MCU",
    # Organisations
    "WHO", "BMW", "CBI", "TUC", "PSA", "DNA", "RNA", "BPM", "RPM", "EMT",
    # Well-known international (common in UK media)
    "CIA", "FBI", "NBA", "NFL",
    # Health (common conditions)
    "IBS", "UTI", "HRT", "IVF", "CBT", "ENT",
    # Everyday/slang
    "MIA", "DOB", "AKA", "POV", "IRL", "IMO", "TBH", "IDK",
    # UK services & transport
    "DWP", "DBS", "MET", "PCN", "DLR", "HMV", "TSB", "RAC",
}

DIRECTIONS = [
    (0, 1),    # right
    (1, 0),    # down
    (1, 1),    # down-right
    (1, -1),   # down-left
    (0, -1),   # left
    (-1, 0),   # up
    (-1, -1),  # up-left
    (-1, 1),   # up-right
]


def extract_all_paths(grid, rows=4, cols=4):
    """All straight-line 3-cell paths in the grid. Returns (word, coords) pairs."""
    paths = []
    for r in range(rows):
        for c in range(cols):
            for dr, dc in DIRECTIONS:
                r2, c2 = r + 2 * dr, c + 2 * dc
                if 0 <= r2 < rows and 0 <= c2 < cols:
                    coords = [(r, c), (r + dr, c + dc), (r2, c2)]
                    word = "".join(grid[cr][cc] for cr, cc in coords)
                    paths.append((word, coords))
    return paths


def check_clue_constraint(tla: str, clue: str) -> List[str]:
    """No word in the clue may start with a letter present in the TLA."""
    forbidden = set(tla.upper())
    words = re.findall(r"\b[A-Za-z]+\b", clue)
    return [
        f"Clue for '{tla}': word '{w}' starts with forbidden letter '{w[0].upper()}'."
        for w in words if w[0].upper() in forbidden
    ]


def verify_puzzle(puzzle: dict) -> dict:
    """
    Full verification. Returns {valid, errors, warnings, info}.

    Checks (errors = must fix):
      1. Grid is 4x4 uppercase letters
      2. Each declared path spells its TLA and is a straight line
      3. Each target TLA exists at exactly one grid path (no ambiguity)
      4. Declared paths cover exactly 13 cells, leaving 3
      5. Leftover cells spell the final TLA in reading order
      6. Clue constraint holds for every clue

    Checks (warnings = worth knowing):
      - TLA not in the UK everyday dictionary
      - Other known TLAs incidentally present in grid
      - Target count outside 5-7 range
    """
    grid = puzzle["grid"]
    targets = puzzle["target_answers"]
    final_tla = puzzle["final_tla"]

    errors: List[str] = []
    warnings: List[str] = []

    # -- Grid structure --
    if len(grid) != 4 or any(len(row) != 4 for row in grid):
        errors.append(f"Grid must be 4x4.")
        return {"valid": False, "errors": errors, "warnings": warnings}

    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if not (len(ch) == 1 and ch.isalpha() and ch.isupper()):
                errors.append(f"Cell ({r},{c}) = '{ch}' — must be a single uppercase letter.")

    # -- Target count --
    if not (5 <= len(targets) <= 7):
        warnings.append(f"Expected 5–7 targets, got {len(targets)}.")

    # -- Path correctness --
    for item in targets:
        path = [tuple(c) for c in item["path"]]
        if len(path) != 3:
            errors.append(f"'{item['tla']}' path has {len(path)} cells, expected 3.")
            continue

        spelled = "".join(grid[r][c] for r, c in path)
        if spelled != item["tla"]:
            errors.append(f"'{item['tla']}' path spells '{spelled}'.")

        dr1 = path[1][0] - path[0][0]
        dc1 = path[1][1] - path[0][1]
        dr2 = path[2][0] - path[1][0]
        dc2 = path[2][1] - path[1][1]
        if (dr1, dc1) != (dr2, dc2):
            errors.append(f"'{item['tla']}' path is not a straight line.")
        if abs(dr1) > 1 or abs(dc1) > 1:
            errors.append(f"'{item['tla']}' path has non-adjacent cells.")

    # -- Uniqueness: each target appears at exactly one grid path --
    all_paths = extract_all_paths(grid)
    for item in targets:
        matches = [coords for w, coords in all_paths if w == item["tla"]]
        if len(matches) == 0:
            errors.append(f"'{item['tla']}' not found at any grid path.")
        elif len(matches) > 1:
            errors.append(
                f"'{item['tla']}' is ambiguous — found at {len(matches)} paths: "
                + "; ".join(str(m) for m in matches)
            )

    # -- Cell coverage (from declared paths, NOT grid scanning) --
    used: Set[Tuple[int, int]] = set()
    for item in targets:
        for c in item["path"]:
            used.add(tuple(c))

    all_coords = {(r, c) for r in range(4) for c in range(4)}
    unused = sorted(all_coords - used)

    if len(unused) != 3:
        errors.append(f"Expected 3 unused cells, got {len(unused)}: {unused}.")
    else:
        leftover = "".join(grid[r][c] for r, c in unused)
        if leftover != final_tla:
            errors.append(f"Leftover cells spell '{leftover}', expected '{final_tla}'.")

    # -- Clue constraint --
    for item in targets:
        errors.extend(check_clue_constraint(item["tla"], item["clue"]))

    # -- TLA dictionary warnings --
    for item in targets:
        if item["tla"] not in UK_EVERYDAY_TLAS:
            warnings.append(f"'{item['tla']}' not in UK everyday TLA dictionary — is it well-known?")
    if final_tla not in UK_EVERYDAY_TLAS:
        warnings.append(f"Final TLA '{final_tla}' not in UK everyday dictionary.")

    # -- Incidental TLAs in grid (info only) --
    target_set = {item["tla"] for item in targets}
    extras = sorted({w for w, _ in all_paths if w in UK_EVERYDAY_TLAS and w not in target_set and w != final_tla})
    if extras:
        warnings.append(f"Other known TLAs in grid (not blocking): {', '.join(extras)}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def print_grid(puzzle: dict):
    """Pretty-print grid with unused cells starred."""
    grid = puzzle["grid"]
    used = set()
    for item in puzzle["target_answers"]:
        for c in item["path"]:
            used.add(tuple(c))

    print("\n    0   1   2   3")
    for r, row in enumerate(grid):
        cells = []
        for c, letter in enumerate(row):
            if (r, c) in used:
                cells.append(f" {letter} ")
            else:
                cells.append(f"[{letter}]")
        print(f"  {r} {'|'.join(cells)}")
    print("  [X] = unused → final TLA\n")


def print_answers(puzzle: dict):
    """Print each target with its path direction."""
    dir_names = {
        (0, 1): "→", (0, -1): "←", (1, 0): "↓", (-1, 0): "↑",
        (1, 1): "↘", (1, -1): "↙", (-1, 1): "↗", (-1, -1): "↖",
    }
    for item in puzzle["target_answers"]:
        path = [tuple(c) for c in item["path"]]
        dr = path[1][0] - path[0][0]
        dc = path[1][1] - path[0][1]
        arrow = dir_names.get((dr, dc), "?")
        print(f"  {item['tla']} {arrow}  {path[0]}→{path[2]}  \"{item['clue']}\"")
    print(f"  Final: {puzzle['final_tla']}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        directory = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        files = sorted(directory.glob("*.json"))
        if not files:
            print(f"No .json files in {directory}")
            sys.exit(1)
        all_pass = True
        for f in files:
            puzzle = json.loads(f.read_text())
            result = verify_puzzle(puzzle)
            status = "PASS" if result["valid"] else "FAIL"
            print(f"{status}  {f.name}")
            for e in result["errors"]:
                print(f"       ERROR: {e}")
            for w in result["warnings"]:
                print(f"       WARN:  {w}")
            if not result["valid"]:
                all_pass = False
        sys.exit(0 if all_pass else 1)

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            puzzle = json.load(f)
    else:
        puzzle = {
            "grid": [
                ["M", "O", "T", "N"],
                ["O", "L", "V", "H"],
                ["C", "T", "I", "S"],
                ["R", "I", "P", "A"]
            ],
            "target_answers": [
                {"tla": "MOT", "path": [[0,0],[0,1],[0,2]], "clue": "Yearly garage check for wheels and brakes"},
                {"tla": "TLC", "path": [[0,2],[1,1],[2,0]], "clue": "Kind extra warmth given when feeling unwell or down"},
                {"tla": "VIP", "path": [[1,2],[2,2],[3,2]], "clue": "Famous guest getting backstage entry and fancy treatment"},
                {"tla": "RIP", "path": [[3,0],[3,1],[3,2]], "clue": "Words carved on headstones at churchyards"},
                {"tla": "OCR", "path": [[1,0],[2,0],[3,0]], "clue": "Software tool turning scanned paper pages into digital text"},
                {"tla": "OTP", "path": [[1,0],[2,1],[3,2]], "clue": "Single use security digits messaged when logging in"},
                {"tla": "IPA", "path": [[3,1],[3,2],[3,3]], "clue": "Hoppy British craft booze served from draught taps"}
            ],
            "final_tla": "NHS"
        }

    print_grid(puzzle)
    print_answers(puzzle)
    print()

    result = verify_puzzle(puzzle)
    if result["valid"]:
        print("✓ PASS")
    else:
        print("✗ FAIL")
    for e in result["errors"]:
        print(f"  ERROR: {e}")
    for w in result["warnings"]:
        print(f"  WARN:  {w}")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
