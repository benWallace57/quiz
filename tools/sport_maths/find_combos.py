#!/usr/bin/env python3
"""Find sport-maths questions: fact A (op) fact B = fact C.

Usage:
  python3 tools/sport_maths/find_combos.py                    # top 60 overall
  python3 tools/sport_maths/find_combos.py --target snooker_max
  python3 tools/sport_maths/find_combos.py --uses hamilton_titles --top 30
  python3 tools/sport_maths/find_combos.py --ops x --min-fame 2 --stable
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

FACTS = Path(__file__).with_name("facts.json")

OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "x": lambda a, b: a * b,
    "/": lambda a, b: a // b if b and a % b == 0 else None,
}
OP_BONUS = {"x": 1.0, "+": 0.5, "-": 0.0, "/": -0.5}
COMMUTATIVE = {"+", "x"}


def score(a, op, b, c, value_counts):
    s = a["fame"] + b["fame"] + c["fame"]
    s += OP_BONUS[op]
    # A big, rare target number is the payoff (147, 180, 501...).
    s += math.log10(c["value"]) * 1.5
    s -= 0.25 * (value_counts[c["value"]] - 1)
    sports = {a["sport"], b["sport"], c["sport"]}
    s += {1: -2, 2: 0.5, 3: 1.5}[len(sports)]
    s -= sum(f.get("volatile", False) for f in (a, b, c))
    # Multiplying by 2 or adding 2 feels like filler.
    if min(a["value"], b["value"]) <= 2:
        s -= 1
    return s


def find(facts, ops, min_value):
    by_value = defaultdict(list)
    for f in facts:
        by_value[f["value"]].append(f)
    value_counts = {v: len(fs) for v, fs in by_value.items()}

    pool = [f for f in facts if f["value"] >= min_value]
    results = []
    for i, a in enumerate(pool):
        for j, b in enumerate(pool):
            if i == j:
                continue
            for op in ops:
                if op in COMMUTATIVE and j < i:
                    continue
                v = OPS[op](a["value"], b["value"])
                if v is None or v in (a["value"], b["value"]):
                    continue
                for c in by_value.get(v, []):
                    if c["id"] in (a["id"], b["id"]):
                        continue
                    results.append((score(a, op, b, c, value_counts), a, op, b, c))
    results.sort(key=lambda r: -r[0])
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--top", type=int, default=60)
    p.add_argument("--ops", default="+-x/", help="subset of + - x /")
    p.add_argument("--target", help="only results whose C is this fact id")
    p.add_argument("--uses", help="only results that use this fact id anywhere")
    p.add_argument("--min-fame", type=int, default=1, help="every fact must have at least this fame")
    p.add_argument("--min-value", type=int, default=2, help="ignore A/B values below this")
    p.add_argument("--stable", action="store_true", help="exclude volatile facts")
    p.add_argument("--per-target", type=int, default=3, help="max results per C value, for variety")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = p.parse_args()

    facts = json.loads(FACTS.read_text())["facts"]
    facts = [f for f in facts if f["fame"] >= args.min_fame]
    if args.stable:
        facts = [f for f in facts if not f.get("volatile")]

    results = find(facts, args.ops, args.min_value)
    if args.target:
        results = [r for r in results if r[4]["id"] == args.target]
    if args.uses:
        results = [r for r in results if args.uses in (r[1]["id"], r[3]["id"], r[4]["id"])]

    shown, per_target = [], defaultdict(int)
    for r in results:
        cv = r[4]["value"]
        if per_target[cv] >= args.per_target:
            continue
        per_target[cv] += 1
        shown.append(r)
        if len(shown) >= args.top:
            break

    if args.json:
        print(json.dumps([
            {"score": round(s, 2), "a": a["id"], "op": op, "b": b["id"], "c": c["id"]}
            for s, a, op, b, c in shown
        ], indent=2))
        return

    print(f"{len(results)} combos found, showing {len(shown)}\n")
    for s, a, op, b, c in shown:
        flag = " *" if any(f.get("volatile") for f in (a, b, c)) else ""
        print(f"[{s:5.2f}] {a['value']} {op} {b['value']} = {c['value']}{flag}")
        print(f"        {a['label']}\n      {op} {b['label']}\n      = {c['label']}\n")
    print("* = uses a volatile fact (check before publishing)")


if __name__ == "__main__":
    main()
