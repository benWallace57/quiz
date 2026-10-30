#!/usr/bin/env python3
"""
UK everyday TLA candidates for wordsearch puzzles.

Each TLA is tagged with a difficulty tier and category.
Import POOL, GIMME, SOLID, or use get_pool() to filter.

Usage:
    from tla_candidates import POOL, tier, category

    # or run standalone to print stats
    python tla_candidates.py
"""

# ── Candidate definitions ─────────────────────────────────────────────
# Format: (TLA, tier, category)
#   tier: "gimme" (everyone knows), "solid" (most know), "stretch" (some need help)
#   category: broad domain grouping
#
# Vetting rules:
#   - Must be a genuine acronym/initialism (not a word: ENT, LAB, CON, NOW, SKY)
#   - Must be recognisable to a UK adult without specialist knowledge
#   - No offensive terms (WTF removed — not print-appropriate)
#   - Political acronyms OK if genuine initialisms (SNP yes, LAB no)
#   - Brand names OK if widely known as TLAs (HMV, DFS, CEX)

CANDIDATES = [
    # Health & emergency
    ("NHS", "gimme",   "health"),
    ("CPR", "solid",   "health"),
    ("AED", "stretch", "health"),
    ("ICU", "solid",   "health"),
    ("MRI", "solid",   "health"),
    ("STI", "solid",   "health"),
    ("OCD", "solid",   "health"),
    ("CBD", "stretch", "health"),
    ("PPE", "solid",   "health"),
    ("BMI", "solid",   "health"),
    ("ECG", "stretch", "health"),
    ("UTI", "solid",   "health"),
    ("IBS", "solid",   "health"),
    ("IVF", "solid",   "health"),
    ("HRT", "solid",   "health"),
    ("SPF", "solid",   "health"),
    ("DVT", "solid",   "health"),
    ("RSI", "solid",   "health"),

    # Transport & driving
    ("MOT", "solid",   "transport"),
    ("TFL", "stretch", "transport"),
    ("MPH", "solid",   "transport"),
    ("SUV", "solid",   "transport"),
    ("HGV", "solid",   "transport"),
    ("RAC", "solid",   "transport"),
    ("PCN", "solid",   "transport"),
    ("DLR", "stretch", "transport"),
    ("KGX", "stretch", "transport"),
    ("GWR", "solid",   "transport"),
    ("MPG", "solid",   "transport"),
    ("ABS", "stretch", "transport"),
    ("RPM", "stretch", "transport"),

    # Media & broadcasting
    ("BBC", "gimme",   "media"),
    ("ITV", "solid",   "media"),
    ("DVD", "gimme",   "media"),
    ("VHS", "solid",   "media"),
    ("DAB", "solid",   "media"),
    ("SNL", "solid",   "media"),
    ("VOD", "solid",   "media"),
    ("MSN", "solid",   "tech"),
    ("PVR", "solid",   "tech"),
    ("HMV", "solid",   "retail"),
    ("DFS", "solid",   "retail"),
    ("CEX", "solid",   "retail"),

    # Tech & gadgets
    ("LCD", "gimme",   "tech"),
    ("LED", "gimme",   "tech"),
    ("USB", "gimme",   "tech"),
    ("SIM", "gimme",   "tech"),
    ("VPN", "gimme",   "tech"),
    ("GPS", "gimme",   "tech"),
    ("PDF", "gimme",   "tech"),
    ("FAQ", "gimme",   "tech"),
    ("PIN", "gimme",   "tech"),
    ("NFC", "stretch", "tech"),
    ("URL", "solid",   "tech"),
    ("SSD", "solid",   "tech"),
    ("OCR", "stretch", "tech"),
    ("OTP", "stretch", "tech"),

    # Money & business
    ("VAT", "gimme",   "money"),
    ("ATM", "gimme",   "money"),
    ("APR", "stretch", "money"),
    ("ISA", "solid",   "money"),
    ("PPI", "solid",   "money"),
    ("CEO", "solid",   "business"),
    ("GBP", "solid",   "money"),
    ("LTD", "solid",   "business"),
    ("TSB", "solid",   "money"),
    ("IOU", "solid",   "money"),
    ("RRP", "gimme",   "money"),
    ("GDP", "solid",   "money"),
    ("CPI", "solid",   "money"),
    ("OOO", "solid",   "business"),
    ("KPI", "solid",   "business"),
    ("NDA", "solid",   "business"),

    # Government & services
    ("MOD", "solid",   "government"),
    ("DWP", "solid",   "government"),
    ("DBS", "solid",   "government"),
    ("MET", "solid",   "government"),
    ("PIP", "solid",   "government"),
    ("SNP", "solid",   "politics"),
    ("DUP", "solid",   "politics"),
    ("RMT", "solid",   "politics"),

    # Honours & military
    ("MBE", "solid",   "honours"),
    ("OBE", "solid",   "honours"),
    ("RAF", "solid",   "military"),
    ("SAS", "solid",   "military"),

    # Everyday expressions
    ("DIY", "gimme",   "everyday"),
    ("TLC", "solid",   "everyday"),
    ("VIP", "solid",   "everyday"),
    ("FYI", "solid",   "everyday"),
    ("ETA", "solid",   "everyday"),
    ("TBA", "solid",   "everyday"),
    ("TBC", "solid",   "everyday"),
    ("SOS", "solid",   "everyday"),
    ("OAP", "solid",   "everyday"),
    ("WFH", "solid",   "everyday"),
    ("RIP", "solid",   "everyday"),
    ("DOB", "solid",   "everyday"),
    ("AKA", "solid",   "everyday"),
    ("MIA", "solid",   "everyday"),
    ("WIP", "solid",   "everyday"),
    ("TBD", "solid",   "everyday"),

    # Slang & text speak
    ("OMG", "gimme",   "slang"),
    ("LOL", "gimme",   "slang"),
    ("BTW", "solid",   "slang"),
    ("BRB", "solid",   "slang"),
    ("TMI", "solid",   "slang"),
    ("POV", "solid",   "slang"),
    ("IRL", "solid",   "slang"),
    ("IMO", "solid",   "slang"),
    ("TBH", "solid",   "slang"),
    ("IDK", "solid",   "slang"),
    ("AFK", "solid",   "slang"),
    ("FTW", "solid",   "slang"),
    ("LMK", "solid",   "slang"),
    ("NVM", "solid",   "slang"),
    ("NBD", "solid",   "slang"),
    ("BFF", "solid",   "slang"),

    # Food & drink
    ("BBQ", "gimme",   "food"),
    ("IPA", "solid",   "food"),
    ("BLT", "solid",   "food"),
    ("BYO", "solid",   "food"),

    # Time
    ("GMT", "solid",   "time"),
    ("BST", "solid",   "time"),

    # Sport
    ("EFL", "solid",   "sport"),
    ("VAR", "solid",   "sport"),
    ("LBW", "stretch", "sport"),
    ("DRS", "solid",   "sport"),

    # Science & everyday
    ("DNA", "solid",   "science"),
    ("BPM", "stretch", "music"),
    ("TNT", "gimme",   "everyday"),
    ("REM", "solid",   "science"),
    ("RNA", "solid",   "science"),

    # Education
    ("UCL", "stretch", "education"),
    ("LSE", "stretch", "education"),
]

# ── Derived sets ──────────────────────────────────────────────────────

POOL = sorted(set(tla for tla, _, _ in CANDIDATES))

_TIER_MAP = {tla: t for tla, t, _ in CANDIDATES}
_CAT_MAP = {tla: cat for tla, _, cat in CANDIDATES}

GIMME = {tla for tla, t, _ in CANDIDATES if t == "gimme"}
SOLID = {tla for tla, t, _ in CANDIDATES if t == "solid"}
STRETCH = {tla for tla, t, _ in CANDIDATES if t == "stretch"}

CATEGORIES = sorted(set(cat for _, _, cat in CANDIDATES))


def tier(tla):
    """Return numeric tier: gimme=3, solid=2, stretch=1, unknown=0."""
    t = _TIER_MAP.get(tla)
    if t == "gimme":
        return 3
    if t == "solid":
        return 2
    if t == "stretch":
        return 1
    return 0


def category(tla):
    """Return the category string for a TLA."""
    return _CAT_MAP.get(tla, "unknown")


def get_pool(exclude=None, require=None, categories=None, tiers=None):
    """Filter the pool by various criteria."""
    exclude = set(exclude or [])
    require = set(require or [])
    result = []
    for tla, t, cat in CANDIDATES:
        if tla in exclude:
            continue
        if categories and cat not in categories:
            continue
        if tiers and t not in tiers:
            continue
        result.append(tla)
    result = sorted(set(result))
    if require:
        missing = require - set(result)
        if missing:
            raise ValueError(f"Required TLAs excluded by filters: {missing}")
    return result


# ── Standalone: print stats ───────────────────────────────────────────

if __name__ == "__main__":
    print(f"Total candidates: {len(POOL)}")
    print(f"  Gimme:   {len(GIMME):3d}  {sorted(GIMME)}")
    print(f"  Solid:   {len(SOLID):3d}  {sorted(SOLID)}")
    print(f"  Stretch: {len(STRETCH):3d}  {sorted(STRETCH)}")
    print()
    print("By category:")
    from collections import Counter
    cats = Counter(cat for _, _, cat in CANDIDATES)
    for cat, n in cats.most_common():
        tlas = sorted(t for t, _, c in CANDIDATES if c == cat)
        print(f"  {cat:12s} ({n:2d}): {', '.join(tlas)}")
