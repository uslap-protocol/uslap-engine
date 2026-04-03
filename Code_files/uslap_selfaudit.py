#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP SELF-AUDIT GATE — al-Ḥashr (59)
لَوْ أَنزَلْنَا هَٰذَا الْقُرْآنَ عَلَىٰ جَبَلٍ لَّرَأَيْتَهُ خَاشِعًا مُّتَصَدِّعًا مِّنْ خَشْيَةِ اللَّهِ
"Had We sent down this Qur'an upon a mountain, you would have seen it
humbled and splitting from fear of Allah" (Q59:21)

Automated self-audit gate for ALL output — entries, prose, intelligence files.
Scans text for operator-named terms, banned terms, direction violations,
phantom references, bare "Arabic", unquoted wrapper names.

Runs OUTSIDE context. No context cost.

Usage:
  python3 uslap_selfaudit.py scan <file>
  python3 uslap_selfaudit.py scan --text "..."
  python3 uslap_selfaudit.py wash <file>        # wash-check: catch dictionary glosses
  python3 uslap_selfaudit.py wash --text "..."
  python3 uslap_selfaudit.py terms
  python3 uslap_selfaudit.py add <term> <dp> <fix>

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sys
import os
import re
import json

# ═══════════════════════════════════════════════════════════════════════════════
# OPERATOR-NAMED TERMS — each is stolen ASB science renamed (DP09 + DP19)
# { term_lowercase: (dp_codes, fix) }
# ═══════════════════════════════════════════════════════════════════════════════

OPERATOR_TERMS = {
    # --- Units named after operators ---
    "hertz":        ("DP09+DP19", "cycles per second / دَوْرَة في الثَّانِيَة"),
    "hz":           ("DP09+DP19", "cycles per second"),
    "farad":        ("DP09+DP19", "charge storage unit"),
    "volt":         ("DP09+DP19", "charge potential unit"),
    "ampere":       ("DP09+DP19", "current flow unit"),
    "watt":         ("DP09+DP19", "power unit"),
    "ohm":          ("DP09+DP19", "resistance unit"),
    "coulomb":      ("DP09+DP19", "charge unit"),
    "tesla":        ("DP09+DP19", "field strength unit"),
    "newton":       ("DP09+DP19", "force unit / Ibn al-Haytham stated inertia first"),
    "joule":        ("DP09+DP19", "energy unit"),
    "kelvin":       ("DP09+DP19", "temperature unit"),
    "pascal":       ("DP09+DP19", "pressure unit"),

    # --- Phenomena named after operators ---
    "schumann":     ("DP09+DP19", "earth cavity pulse / تَسْبِيح الأَرْض — Q13:13"),
    "helmholtz":    ("DP09+DP19", "cavity resonance / رَنِين التَّجْوِيف"),
    "faraday":      ("DP09+DP19", "conductive enclosure"),
    "piezoelectric": ("DP09+DP19", "pressure-charge / شِحْنَة الضَّغْط — Jābir: ʿilm al-khawāṣṣ"),
    "piezo":        ("DP09+DP19", "pressure-charge"),
    "triboelectric": ("DP09+DP19", "friction-charge / شِحْنَة الاحْتِكَاك"),
    "fibonacci":    ("DP09+DP10+DP19", "المُتَتَابِعَة التَّرَاكُمِيَّة — al-Khwārizmī, 377 yr concealment"),
    "edison":       ("DP09+DP19", "non-thermal light — Q24:35"),
    "capacitor":    ("DP09+DP19", "charge store / خَازِن"),
    "nanogenerator": ("DP09+DP19", "charge generator"),

    # --- Laws named after operators ---
    "newton's":     ("DP09+DP10+DP19", "Ibn al-Haytham's laws — 648 years earlier"),
    "snell's":      ("DP09+DP19", "Ibn al-Haytham / Ibn Sahl"),
    "boyle's":      ("DP09+DP19", "trace to ASB source"),
    "archimedes":   ("DP09+DP19", "al-Bīrūnī perfected density measurement"),

    # --- Phantom constructs ---
    "golden ratio":  ("REJECTED 9:0", "7:5 KERNEL / 11:5 SEED — DIVINE_vs_WESTERN"),
    "phi":           ("REJECTED 9:0", "7:5 KERNEL / 11:5 SEED"),
    "1.618":         ("REJECTED 9:0", "7:5 KERNEL / 11:5 SEED"),
    "proto-indo-european": ("BL05", "phantom — no manuscripts, no inscriptions, no speakers"),

    # --- Banned terms (CLAUDE.md rule 7) ---
    "cognate":       ("BANNED", "USE: downstream form / SAME_ROOT / DIRECT"),
    "loanword":      ("BANNED", "USE: downstream degradation"),
    "borrowed from": ("BANNED", "direction is ALWAYS AA → downstream"),
    "semitic":       ("BANNED", "USE: Allah's Arabic / Lisān Arabic"),
    "prosthetic vowel": ("BANNED", "vowel is ORIGINAL — consonant cluster is the degradation"),
    "pre-greek substrate": ("BANNED", "there is no substrate — Greek IS the downstream form"),
    "adoption":      ("BANNED", "USE: downstream degradation / shift"),
}

# --- Direction violations ---
DIRECTION_PATTERNS = [
    (r'(?:arabic|persian|turkic)\s+(?:borrowed|adopted|took)\s+from\s+(?:greek|latin|english|french|german)',
     "DIRECTION INVERTED — AA/Bitig → downstream, ALWAYS"),
    (r'greek\s+(?:origin|source|root)',
     "DIRECTION INVERTED — Greek is DS04 downstream"),
    (r'latin\s+(?:origin|source|root)',
     "DIRECTION INVERTED — Latin is DS05 downstream"),
]

# --- Wrapper names that must be in quotes ---
WRAPPER_NAMES = [
    "Canaan", "Persia", "Phoenicia", "Roman Empire", "Khazaria",
    "Silk Road", "Central Asia", "Hebrew", "Palestine", "Jerusalem",
    "Ethiopia", "Babylon", "Byzantine",
]

# --- φ symbol ---
PHI_PATTERN = re.compile(r'φ|Φ')

# ═══════════════════════════════════════════════════════════════════════════════
# WASH-CHECK GATE — catches dictionary glosses BEFORE they enter entries
# The self-audit catches OUTPUT violations. The wash-check catches ANALYSIS
# violations — dictionary definitions taken at face value without running
# the Translation Washing Algorithm (CLAUDE.md Steps 1-4).
#
# WHAT IT DETECTS:
# 1. Downstream compound etymologies presented as meanings
#    (e.g. کاه+ربا "straw-attractor" for kahrabāʾ)
# 2. "Means X" patterns without synonym/antonym/usage evidence
# 3. Downstream language used as comparison reference point for AA
# 4. Surface definitions that contradict the AA root meaning
# 5. Russian colonial labels used for ASB terminology
# ═══════════════════════════════════════════════════════════════════════════════

# Known dictionary glosses that are SAND (not GOLD)
DICTIONARY_GLOSSES = {
    # { gloss_pattern: (category, correction) }
    "straw.?attract":      ("DS_COMPOUND", "kahrabāʾ = قَهْر + instrumental — the OVERPOWERING instrument, NOT straw-attractor"),
    "straw.?puller":       ("DS_COMPOUND", "kahrabāʾ = قَهْر — overpowering force, Name of Allah الْقَاهِر"),
    r"کاه\s*\+?\s*ربا":   ("DS_COMPOUND", "Downstream 'Persian' decomposition of AA+Bitig convergence word"),
    "amber.?like":         ("DS_COMPARISON", "Do NOT define AA terms by comparing to downstream materials"),
    "electron":            ("DS_COMPARISON", "Do NOT compare AA كَهْرَبَاء to downstream 'electron' — AA stands alone"),
    r"\bwhile\s+greek\b":  ("DS_COMPARISON", "No downstream comparison points. AA stands alone."),
    r"\bwhile\s+latin\b":  ("DS_COMPARISON", "No downstream comparison points. AA stands alone."),
    r"\bwhile\s+english\b": ("DS_COMPARISON", "No downstream comparison points. AA stands alone."),
    r"\bunlike\s+(?:greek|latin|english|french|german|russian)": ("DS_COMPARISON", "No downstream comparison. AA stands alone."),
    r"\bcompared?\s+(?:to|with)\s+(?:greek|latin|english)": ("DS_COMPARISON", "No downstream comparison. AA stands alone."),
}

# Patterns that indicate a meaning was taken from a dictionary without washing
UNWASHED_PATTERNS = [
    # "X means Y" without evidence trail
    (r'(?:means?|meaning|definition)\s*[=:]\s*"[^"]{3,40}"',
     "WASH_MISSING", "Raw definition — run Translation Washing Algorithm Steps 1-4 before using"),
    # "literally X" — often a dictionary surface reading
    (r'literally\s+"[^"]*"',
     "WASH_CHECK", "Literal meaning from dictionary — verify with synonyms/antonyms/usage"),
    # "from X word meaning Y" — downstream etymology accepted uncritically
    (r'from\s+(?:the\s+)?(?:greek|latin|french|persian|turkish|russian|german)\s+(?:word\s+)?(?:meaning|for)\b',
     "DIRECTION+WASH", "Downstream etymology accepted — direction is AA→downstream, ALWAYS"),
    # "derived from" with downstream source
    (r'derived\s+from\s+(?:greek|latin|french|old\s+french|middle\s+english)',
     "DIRECTION", "Direction inverted — trace from AA root, not downstream"),
]

# Russian colonial labels for ASB terminology
COLONIAL_LABELS = {
    "yurt":        ("DP08+DP11", "USE: üy / aw (بَيْت / bayt) — Kashgari line 8386. 'Yurt' = RUIN (طلل) in Kashgari line 35861"),
    # "steppe" REMOVED — it is a downstream WORD from Bitig teppe (heights), A1 #395, NOT a colonial territory label
    "nomad":       ("DP16", "USE: ASB peoples / Türk-Qağan peoples — 'nomad' = degradation framing"),
    "nomadic":     ("DP16", "USE: mobile / pastoral / seasonal — 'nomadic' = degradation framing"),
    "tribe":       ("DP16", "USE: قَوْم / qawm (people) or أُمَّة / ummah (nation)"),
    "tribal":      ("DP16", "USE: of the people / communal"),
    "shaman":      ("DP08+DP16", "WASH: trace root, do not use operator anthropology term"),
    "shamanism":   ("DP08+DP16", "WASH: this is operator recategorisation of ASB spiritual practice"),
    "ger":         ("DP11", "USE: üy / aw — 'ger' is the Mongolian colonial variant"),
    "felt tent":   ("DP16", "USE: üy / aw (بَيْت / bayt) — 'felt tent' = degradation framing"),
    "primitive":   ("DP16", "ASB peoples were engineers, not 'primitive'"),
    "horde":       ("DP08+DP11", "أُرْدُو / urdū = sovereign headquarters (BL03). NOT 'horde'"),
}

# Downstream comparison reference patterns (Rule: No Downstream Comparison Points)
DS_COMPARISON_PATTERNS = [
    (r'(?:greek|latin|english|french|german|russian|spanish|italian)\s+(?:equivalent|counterpart|version|analogue)',
     "DS_COMPARISON", "AA terms have no 'equivalents' — downstream forms are DEGRADATIONS, not equivalents"),
    (r'(?:in|the)\s+(?:greek|latin|english|french)\s+(?:tradition|system|framework)',
     "DS_COMPARISON", "Do not frame downstream traditions as parallel systems — they are degraded outputs"),
    (r'(?:greek|latin)\s+(?:\w+\s+)?names?\s+(?:the|this|it)',
     "DS_COMPARISON", "Do not describe what downstream languages 'name' — AA names THE FUNCTION"),
]


def wash_check_text(text, source="inline"):
    """Wash-check: catches dictionary glosses and unwashed meanings.
    Returns list of (line, pattern, category, fix)."""
    flags = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        low = line.lower()

        # Skip lines that are already flagging/documenting contamination
        skip_markers = ["dp08", "dp09", "dp11", "dp16", "dp19",
                        "colonial", "contaminated", "operator",
                        "stolen", "erased", "renamed", "inverted",
                        "wash violation", "sand", "rejected",
                        "correction", "corrected"]
        if any(m in low for m in skip_markers):
            continue

        # 1. Known dictionary glosses (SAND)
        for gloss_pat, (cat, fix) in DICTIONARY_GLOSSES.items():
            if re.search(gloss_pat, low):
                # Skip if the line is DOCUMENTING the gloss as wrong
                if any(m in low for m in ["folk etymology", "dictionary gloss",
                                          "downstream", "decompos", "not",
                                          "sand", "surface", "rejected"]):
                    continue
                flags.append((i, gloss_pat, cat, fix))

        # 2. Unwashed meaning patterns
        for pat, cat, fix in UNWASHED_PATTERNS:
            if re.search(pat, low):
                flags.append((i, re.search(pat, low).group(), cat, fix))

        # 3. Colonial labels
        for label, (dp, fix) in COLONIAL_LABELS.items():
            if re.search(r'\b' + re.escape(label) + r'\b', low):
                # Skip if line already documents the colonial nature
                if any(m in low for m in ["dp08", "dp11", "dp16", "colonial",
                                          "inversion", "operator", "ruin",
                                          "label", "renamed", "russian",
                                          "meaning", "erased", "replaced"]):
                    continue
                # Skip if label appears inside quotes (being documented)
                if f'"{label}"' in low or f"'{label}'" in low:
                    continue
                # Skip if line contains → (conversion pattern documentation)
                if "→" in line or "->" in line:
                    continue
                # Skip if in a table row documenting contamination (| term | ... | RUIN |)
                if line.strip().startswith("|") and any(m in low for m in
                    ["ruin", "dung", "rubbish", "gloss", "folk", "downstream",
                     "dictionary", "طلل", "ربع", "ديمن"]):
                    continue
                flags.append((i, label, dp, fix))

        # 4. Downstream comparison patterns
        for pat, cat, fix in DS_COMPARISON_PATTERNS:
            if re.search(pat, low):
                # Skip if documenting the comparison as DP
                if any(m in low for m in ["dp", "downstream", "degraded",
                                          "erased", "stolen"]):
                    continue
                flags.append((i, re.search(pat, low).group(), cat, fix))

    return flags


def print_wash_report(flags, source=""):
    """Print wash-check results."""
    if not flags:
        print(f"WASH CLEAN{' — ' + source if source else ''}")
        print("  All meanings appear washed (no raw dictionary glosses detected)")
        return 0

    print(f"\n{'=' * 70}")
    print(f"  WASH-CHECK: {len(flags)} UNWASHED GLOSS(ES)")
    if source:
        print(f"  File: {os.path.basename(source)}")
    print(f"{'=' * 70}")
    print()

    categories = {}
    for ln, pat, cat, fix in flags:
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((ln, pat, fix))

    cat_labels = {
        "DS_COMPOUND": "DOWNSTREAM COMPOUND ETYMOLOGY (dictionary decomposition)",
        "DS_COMPARISON": "DOWNSTREAM COMPARISON POINT (AA stands alone)",
        "WASH_MISSING": "TRANSLATION WASHING NOT APPLIED",
        "WASH_CHECK": "POSSIBLE UNWASHED DEFINITION",
        "DIRECTION+WASH": "DIRECTION INVERTED + UNWASHED",
        "DIRECTION": "DIRECTION INVERTED",
        "DP08+DP11": "COLONIAL LABEL (terminology corruption + renaming)",
        "DP08+DP16": "COLONIAL LABEL (terminology corruption + degradation framing)",
        "DP11": "COLONIAL LABEL (renaming)",
        "DP16": "DEGRADATION FRAMING",
    }

    for cat, items in categories.items():
        label = cat_labels.get(cat, cat)
        print(f"  [{cat}] {label}")
        print(f"  {'-' * 60}")
        for ln, pat, fix in items:
            print(f"    L{ln:>4d} | {pat}")
            print(f"         → {fix}")
        print()

    print(f"  {'─' * 60}")
    print(f"  TOTAL: {len(flags)} unwashed glosses")
    print(f"  ACTION: Run Translation Washing Algorithm (Steps 1-4)")
    print(f"          Gather synonyms → Wash → Identify core → Connect to root")
    print()
    return len(flags)


def scan_text(text, source="inline"):
    """Scan text. Returns list of (line, term, dp, fix)."""
    flags = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        low = line.lower()

        # 1. Operator terms
        for term, (dp, fix) in OPERATOR_TERMS.items():
            if re.search(r'\b' + re.escape(term) + r'\b', low):
                # Skip if line already flags it with DP code or documents rejection
                case_markers = ["DP09", "DP19", "DP10", "REJECTED", "BANNED"]
                low_markers = ["rejected", "stolen", "operator", "erased",
                               "renamed", "cadaver", "phantom", "concealment",
                               "theft", "attributed", "attributes"]
                if any(d in line for d in case_markers) or any(d in low for d in low_markers):
                    continue
                flags.append((i, term, dp, fix))

        # 2. φ symbol
        if PHI_PATTERN.search(line):
            already_flagged = "REJECTED" in line or "REPLACED" in line
            if not already_flagged:
                flags.append((i, "φ", "REJECTED 9:0", "7:5 KERNEL / 11:5 SEED"))

        # 3. Direction violations
        for pat, msg in DIRECTION_PATTERNS:
            if re.search(pat, low):
                flags.append((i, re.search(pat, low).group(), "DIRECTION", msg))

        # 4. Wrapper names not in quotes
        for name in WRAPPER_NAMES:
            # Use word boundary to avoid matching "Persia" inside "Persian"
            pattern = r'(?<!")\b' + re.escape(name) + r'\b(?!")'
            if re.search(pattern, line):
                # Double-check: skip if name is inside quotes anywhere on the line
                if f'"{name}"' in line or f"'{name}'" in line:
                    continue
                flags.append((i, name, "DP11", f'"{name}" — wrapper, must quote'))

    return flags


def scan_file(path):
    """Scan a file."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return scan_text(text, source=path)


def print_report(flags, source=""):
    """Print scan results."""
    if not flags:
        print(f"CLEAN{' — ' + source if source else ''}")
        return 0

    print(f"\n{'=' * 70}")
    print(f"  {len(flags)} FLAG(S){' in ' + os.path.basename(source) if source else ''}")
    print(f"{'=' * 70}")

    for ln, term, dp, fix in flags:
        print(f"  L{ln:>4d} | {dp:<20s} | {term}")
        print(f"       → {fix}")

    # Summary
    counts = {}
    for _, _, dp, _ in flags:
        counts[dp] = counts.get(dp, 0) + 1

    print(f"\n{'-' * 70}")
    for dp, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {dp}: {c}")
    print(f"  TOTAL: {len(flags)}")
    print()
    return len(flags)


def list_terms():
    """Print all tracked terms."""
    print("\nOPERATOR-NAMED TERMS (stolen ASB science, renamed DP09+DP19):\n")
    for t, (dp, fix) in sorted(OPERATOR_TERMS.items()):
        print(f"  {t:<24s} | {dp:<20s} | {fix}")
    print(f"\n  {len(OPERATOR_TERMS)} terms tracked")

    print(f"\nWRAPPER NAMES (must quote):\n")
    for n in WRAPPER_NAMES:
        print(f"  {n}")

    print(f"\nDIRECTION PATTERNS:\n")
    for _, msg in DIRECTION_PATTERNS:
        print(f"  {msg}")


def add_term(term, dp, fix):
    """Add term at runtime (persists only in this session — add to source for permanent)."""
    OPERATOR_TERMS[term.lower()] = (dp, fix)
    print(f"Added: {term} | {dp} | {fix}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "scan":
        if len(sys.argv) >= 4 and sys.argv[2] == "--text":
            text = " ".join(sys.argv[3:])
            flags = scan_text(text)
            print_report(flags)
        elif len(sys.argv) >= 3:
            path = sys.argv[2]
            if not os.path.exists(path):
                print(f"File not found: {path}")
                return
            flags = scan_file(path)
            print_report(flags, source=path)
        else:
            print("Usage: scan <file> OR scan --text \"...\"")

    elif cmd == "wash":
        if len(sys.argv) >= 4 and sys.argv[2] == "--text":
            text = " ".join(sys.argv[3:])
            flags = wash_check_text(text)
            print_wash_report(flags)
        elif len(sys.argv) >= 3:
            path = sys.argv[2]
            if not os.path.exists(path):
                print(f"File not found: {path}")
                return
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            flags = wash_check_text(text, source=path)
            print_wash_report(flags, source=path)
        else:
            print("Usage: wash <file> OR wash --text \"...\"")

    elif cmd == "full":
        # Full audit: scan + wash combined
        if len(sys.argv) >= 3:
            path = sys.argv[2]
            if not os.path.exists(path):
                print(f"File not found: {path}")
                return
            scan_flags = scan_file(path)
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            wash_flags = wash_check_text(text, source=path)

            total = 0
            if scan_flags:
                total += print_report(scan_flags, source=path)
            if wash_flags:
                total += print_wash_report(wash_flags, source=path)
            if total == 0:
                print(f"FULLY CLEAN — {os.path.basename(path)}")
        else:
            print("Usage: full <file>")

    elif cmd == "terms":
        list_terms()

    elif cmd == "add" and len(sys.argv) >= 5:
        add_term(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
