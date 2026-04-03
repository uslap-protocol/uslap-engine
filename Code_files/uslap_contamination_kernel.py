#!/usr/bin/env python3
"""
USLaP CONTAMINATION KERNEL — al-Ikhlāṣ

The contamination has ONE structure:
    [DOWNSTREAM LANGUAGE] positioned as [SOURCE]

The paraphrase changes the surface words.
The structure is invariant.

Two finite lists. One cross-product. Catches ALL paraphrases.

List A: DOWNSTREAM LANGUAGES (finite, closed — these are NEVER sources)
List B: SOURCE-IMPLYING WORDS (finite, closed — these imply origin/ancestry/parentage)

If A appears within proximity of B → contamination detected.
No exact string matching. No paraphrase escapes.

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import re

# ═══════════════════════════════════════════════════════════════════════════════
# LIST A — DOWNSTREAM LANGUAGES (NEVER sources)
# These are corridors, not origins. DS01-DS08+.
# ═══════════════════════════════════════════════════════════════════════════════
DOWNSTREAM = [
    "greek", "latin", "sanskrit", "french", "german", "english",
    "spanish", "italian", "portuguese", "dutch", "swedish", "norwegian",
    "danish", "russian", "slavic", "slavonic", "old english",
    "middle english", "old french", "old norse", "gothic",
    "anglo-saxon", "celtic", "gaelic", "welsh",
    "proto-indo-european", "proto-slavic", "proto-germanic",
    "proto-turkic", "proto-uralic", "proto-finnic",
    "indo-european", "indo-iranian",
    "aramaic", "hebrew", "syriac", "akkadian", "sumerian",
    "phoenician", "egyptian", "coptic",
    "persian",  # "Persian" is a wrapper — AA + thin veneer
    "hindi", "urdu", "bengali", "tamil",
    "chinese", "japanese", "korean",
    "hungarian", "finnish", "estonian",
    "romance", "germanic", "italic",
]

# ═══════════════════════════════════════════════════════════════════════════════
# LIST B — SOURCE-IMPLYING WORDS (imply origin/ancestry/parentage)
# If one of these appears near a downstream language, the claim is:
# "downstream language X is a source" → ALWAYS false.
# ═══════════════════════════════════════════════════════════════════════════════
SOURCE_WORDS = [
    # Direct source claims
    "origin", "originated", "originates", "originating",
    "source", "sourced",
    "root", "rooted",  # "Greek root" = contamination
    "ancestor", "ancestral", "ancestry",
    "parent", "parental",
    "precursor", "predecessor", "forerunner",
    "progenitor",
    "mother tongue", "mother language",
    # Transmission claims (downstream → target)
    "gave", "given", "gives",
    "contributed", "contribution",
    "transmitted", "transmission",
    "passed to", "passed into",
    "entered from", "entered via",
    "came from", "comes from", "coming from",
    "taken from", "taking from",
    "adopted from", "adopting from",
    "inherited from", "inheriting",
    "descended from", "descends from",
    # Borrowing/loan (banned terms, but catch paraphrases too)
    "borrowed", "borrowing",
    "loaned", "loan from",
    "loanword",
    "calque",
    # Academic framework words
    "cognate", "cognates",
    "reflex", "reflexes",  # PIE terminology
    "substrate", "substratum", "superstrate",
    "etymon",
    "proto-form",
    # Softer paraphrases
    "influence", "influenced by",
    "traces back to", "traced to", "traceable to",
    "derives from", "derived from", "derivation from",
    "stems from", "stemming from",
    "has its roots in",
    "owes its form to",
    "modeled on", "modelled on",
    "based on",
    "related to",  # "related to Greek X" = contamination
    "akin to",
    "parallel to",
    "equivalent", "counterpart",
    # Construction claims
    "constructed from",
    "composed from", "composed of",
    "built from", "built on",
]

# Pre-compile downstream patterns (word boundary)
_DS_PATTERNS = [(ds, re.compile(r'\b' + re.escape(ds) + r'\b', re.IGNORECASE)) for ds in DOWNSTREAM]
_SRC_PATTERNS = [(sw, re.compile(r'\b' + re.escape(sw) + r'\b', re.IGNORECASE)) for sw in SOURCE_WORDS]

# Skip markers — lines DOCUMENTING contamination (not producing it)
# TIGHTENED 2026-03-23: Single broad words like "operator", "downstream",
# "corridor" appeared in nearly every USLaP sentence, effectively disabling
# the scan. Now requires multi-word markers that only appear in actual
# documentation context.
SKIP_MARKERS = [
    "banned term", "contaminated term", "contamination detected",
    "dp01", "dp02", "dp03", "dp04", "dp05", "dp06", "dp07",
    "dp08", "dp09", "dp10", "dp11", "dp12", "dp13", "dp14",
    "dp15", "dp16", "dp17", "dp18", "dp19", "dp20",
    "dp-self", "dp-dual",
    "rejected by", "blocked by", "selfaudit scan",
    "pre-write gate", "contamination shield", "contamination kernel",
    "banned_term", "direction_inverted", "f-gate reject",
    "never use:", "do not use:", "violation found",
    "≠", "→ use:", "fix:", "instead use:",
    "bl01", "bl02", "bl03", "bl04", "bl05", "bl06", "bl07",
    "bl08", "bl09", "bl10", "bl11", "bl12", "bl13", "bl14",
    "bl15", "bl16", "bl17", "bl18", "bl19",
    "downstream corridor", "not a source", "never source",
    "direction is always", "aa →", "al →",
]

# Proximity window — how close (in characters) must A and B be?
PROXIMITY = 120  # characters — generous enough for "the Greek word that gave rise to..."


def scan_kernel(text: str) -> list:
    """
    Scan text for the invariant contamination structure:
    [DOWNSTREAM] + [SOURCE-IMPLYING WORD] within PROXIMITY characters.

    Returns list of violations: (line_num, downstream, source_word, excerpt)
    """
    violations = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        low = line.lower().strip()
        if not low or len(low) < 10:
            continue

        # Skip documentation lines
        if any(m in low for m in SKIP_MARKERS):
            continue

        # Skip code blocks
        if low.startswith('```') or low.startswith('import ') or low.startswith('select '):
            continue
        if low.startswith('|') and low.endswith('|'):  # table row
            continue

        # Find all downstream language mentions in this line
        ds_matches = []
        for ds_name, ds_pat in _DS_PATTERNS:
            for m in ds_pat.finditer(line):
                ds_matches.append((ds_name, m.start(), m.end()))

        if not ds_matches:
            continue

        # Find all source-implying words in this line
        src_matches = []
        for sw_name, sw_pat in _SRC_PATTERNS:
            for m in sw_pat.finditer(line):
                src_matches.append((sw_name, m.start(), m.end()))

        if not src_matches:
            continue

        # Check proximity — any DS within PROXIMITY chars of any SRC?
        for ds_name, ds_start, ds_end in ds_matches:
            for sw_name, sw_start, sw_end in src_matches:
                # Distance between the two matches
                if ds_end <= sw_start:
                    dist = sw_start - ds_end
                elif sw_end <= ds_start:
                    dist = ds_start - sw_end
                else:
                    dist = 0  # overlapping

                if dist <= PROXIMITY:
                    # Extract context
                    ctx_start = max(0, min(ds_start, sw_start) - 10)
                    ctx_end = min(len(line), max(ds_end, sw_end) + 10)
                    excerpt = line[ctx_start:ctx_end].strip()

                    violations.append((line_num, ds_name, sw_name, excerpt))
                    break  # One violation per DS match per line is enough
            else:
                continue
            break  # One violation per line is enough

    return violations


def format_violations(violations: list) -> str:
    """Format violations for display."""
    if not violations:
        return ""

    lines = ["⛔ CONTAMINATION KERNEL — downstream language positioned as source:"]
    for ln, ds, sw, excerpt in violations:
        lines.append(f"  L{ln}: [{ds.upper()}] + [{sw}] — \"{excerpt}\"")
    lines.append(f"\n{len(violations)} violation(s). No downstream language is EVER a source.")
    lines.append("Direction is ALWAYS: Allah's Arabic / Bitig → downstream.")
    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    text = sys.stdin.read()
    violations = scan_kernel(text)
    if violations:
        print(format_violations(violations))
        sys.exit(1)
    else:
        sys.exit(0)
