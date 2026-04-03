#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP PRE-WRITE WASH GATE — al-Muṭaffifīn (83)
وَيْلٌ لِّلْمُطَفِّفِينَ الَّذِينَ إِذَا اكْتَالُوا عَلَى النَّاسِ يَسْتَوْفُونَ وَإِذَا كَالُوهُمْ أَو وَّزَنُوهُمْ يُخْسِرُونَ
"Woe to the defrauders — who, when they take a measure from people, take in full,
but when they give by measure or weight to them, give less." (Q83:1-3)

PRE-WRITE enforcement gate. Runs BEFORE any entry is written to the database.
Catches dictionary glosses, unwashed definitions, downstream etymologies,
compound folk etymologies, and missing root connections.

The self-audit gate (uslap_selfaudit.py) checks OUTPUT for banned terms.
This gate checks ANALYSIS for unwashed input — the failure that happens
BEFORE output exists.

Runs OUTSIDE context. No context cost.

Usage:
  python3 uslap_wash.py check  "term" "proposed definition/meaning"
  python3 uslap_wash.py entry  <entry_id>     # check existing entry in DB
  python3 uslap_wash.py batch                  # check all entries for unwashed glosses
  python3 uslap_wash.py patterns               # list all detection patterns

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sys
import os
import re
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')

# ═══════════════════════════════════════════════════════════════════════════════
# DICTIONARY GLOSS PATTERNS — surface definitions taken from downstream sources
# These patterns indicate the Translation Washing Algorithm was NOT run.
# ═══════════════════════════════════════════════════════════════════════════════

# 1. Compound folk etymologies — "X + Y = meaning"
#    Pattern: two words joined to produce a surface gloss
COMPOUND_FOLK = [
    (r'(?:from|means|literally)\s+\w+\s*\+\s*\w+', 'COMPOUND FOLK ETYMOLOGY — decomposing into downstream morphemes instead of tracing to AA root'),
    (r'کاه\s*\+\s*ربا', 'KNOWN WASHED: کاه+ربا is folk etymology for كَهْرَبَاء — root is ق-ه-ر'),
    (r'\w+\s*\+\s*\w+\s*=\s*["\']', 'COMPOUND DECOMPOSITION — are these AA roots or downstream morphemes?'),
]

# 2. Downstream dictionary attribution — "means X in Persian/Greek/Latin"
DOWNSTREAM_GLOSS = [
    (r'(?:means?|meaning|signifies?|denotes?)\s+["\']?\w+["\']?\s+in\s+(?:persian|greek|latin|french|german|english|russian|turkish|sanskrit|hebrew)',
     'DOWNSTREAM DICTIONARY GLOSS — meaning taken from downstream language dictionary, not from AA root'),
    (r'(?:persian|greek|latin|french|german|sanskrit|hebrew)\s+(?:word\s+)?(?:for|meaning)',
     'DOWNSTREAM DEFINITION — what a downstream language "calls" something is not what it IS'),
    (r'from\s+(?:persian|greek|latin|french|old\s+french|middle\s+english|proto-germanic|sanskrit)',
     'DOWNSTREAM ORIGIN CLAIM — direction inverted or source misattributed'),
    (r'(?:persian|greek|latin)\s+(?:compound|combination|etymology)',
     'DOWNSTREAM ETYMOLOGY — folk etymology from downstream language, not root analysis'),
]

# 3. Surface-only definitions — no root connection present
#    These catch definitions that describe appearance/function without connecting to root letters
SURFACE_ONLY = [
    (r'^[^ق-ي]*(?:attractor|attracter|attractive)',
     'SURFACE GLOSS "attractor" — what does the ROOT say? Is this from washing or from a dictionary?'),
    (r'(?:literally|lit\.|lit:)\s+["\']',
     'LITERAL TRANSLATION — "literally means X" is a translator output, not a root analysis'),
    (r'(?:derived from|comes from|originates from)\s+(?:the\s+)?(?:word|term|name)',
     'DERIVATION CLAIM without root letters — where is the AA root?'),
    (r'(?:named after|named for|named from)\s+(?:the\s+)?(?:greek|latin|french|german|english|a\s+\w+\s+person|an?\s+\w+\s+scientist)',
     'NAMED-AFTER downstream claim — is this a root connection or a downstream story?'),
]

# 4. Academic framework smuggling — phantom frameworks treated as real
FRAMEWORK_SMUGGLE = [
    (r'proto-(?:indo-european|germanic|slavic|celtic|italic|semitic|turkic)',
     'PHANTOM FRAMEWORK — no manuscripts, no inscriptions, no speakers (BL05)'),
    (r'(?:cognate|loanword|borrowed|loan\s*translation|calque)',
     'BANNED TERM — use: downstream form / SAME_ROOT / DIRECT'),
    (r'(?:semitic|afro-?asiatic|hamito-?semitic)',
     'BANNED CATEGORY — use: Allah\'s Arabic / Lisān Arabic'),
    (r'(?:indo-european|IE\s+root|\*[a-z]+[-])',
     'PHANTOM RECONSTRUCTION — asterisk roots are fabrications'),
]

# 5. Missing root indicators — signs that root analysis was skipped
MISSING_ROOT = [
    (r'(?:origin|etymology)\s+(?:unknown|uncertain|unclear|disputed|obscure)',
     'ORIGIN UNKNOWN = their framework cannot explain it. Likely AA/Bitig — they cannot say so. DO NOT treat as dead end — treat as CLUE.'),
    (r'(?:perhaps|possibly|maybe)\s+(?:from|related|connected)',
     'HEDGED ETYMOLOGY — uncertainty means the downstream framework is guessing. Go to roots.'),
]

# 6. Translator output markers — signs of copy-paste from published translations
TRANSLATOR_OUTPUT = [
    (r'(?:sahih\s+international|pickthall|yusuf\s+ali|arberry|hilali(?:\s+&?\s*khan)?|muhsin\s+khan)',
     'TRANSLATOR NAME — do not copy-paste. Translate from roots (CLAUDE.md Rule 2A).'),
    (r'(?:translated as|translation:|commonly translated)',
     'TRANSLATION MARKER — whose translation? From roots or from a translator?'),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ROOT PRESENCE CHECKS — what SHOULD be there
# ═══════════════════════════════════════════════════════════════════════════════

# AA root letter pattern (3 or 4 letters with dashes)
ROOT_PATTERN = re.compile(r'[ء-ي]\s*[-–—]\s*[ء-ي]\s*[-–—]\s*[ء-ي]')

# Qur'anic reference pattern
QURAN_REF = re.compile(r'Q\d{1,3}:\d{1,3}')

# Root ID pattern
ROOT_ID = re.compile(r'R\d+|R_[A-Z]+|T\d+')


def check_text(text, term=""):
    """
    Check text for unwashed dictionary glosses.
    Returns list of (pattern_name, category, message).
    """
    flags = []
    low = text.lower()

    all_patterns = [
        ('COMPOUND_FOLK', COMPOUND_FOLK),
        ('DOWNSTREAM_GLOSS', DOWNSTREAM_GLOSS),
        ('SURFACE_ONLY', SURFACE_ONLY),
        ('FRAMEWORK_SMUGGLE', FRAMEWORK_SMUGGLE),
        ('MISSING_ROOT', MISSING_ROOT),
        ('TRANSLATOR_OUTPUT', TRANSLATOR_OUTPUT),
    ]

    for category, patterns in all_patterns:
        for pat, msg in patterns:
            if re.search(pat, low):
                match = re.search(pat, low)
                flags.append((category, match.group(), msg))

    # Check for ROOT PRESENCE
    has_root = bool(ROOT_PATTERN.search(text))
    has_quran = bool(QURAN_REF.search(text))
    has_root_id = bool(ROOT_ID.search(text))

    if not has_root:
        flags.append(('MISSING', 'no root letters',
                       'NO AA ROOT LETTERS found (ف-ع-ل pattern). Entry MUST trace to root.'))
    if not has_quran:
        flags.append(('MISSING', 'no Qur\'anic ref',
                       'NO QUR\'ANIC REFERENCE found. Check Qur\'an first (Rule 6).'))
    if not has_root_id:
        flags.append(('MISSING', 'no root ID',
                       'NO ROOT_ID found (R###/T##). Entry must have a root ID.'))

    return flags, has_root, has_quran, has_root_id


def check_entry(entry_id):
    """Check an existing database entry for unwashed glosses."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    row = conn.execute(
        'SELECT entry_id, en_term, aa_word, root_id, root_letters, qur_meaning, '
        'phonetic_chain, source_form FROM a1_entries WHERE entry_id = ?',
        (entry_id,)
    ).fetchone()

    if not row:
        print(f"Entry {entry_id} not found.")
        conn.close()
        return

    eid, en_term, aa_word, root_id, root_letters, qur_meaning, phon, source = row

    # Combine all text fields for scanning — include root_id and root_letters
    # so presence checks find them in their dedicated columns
    all_text = ' '.join(str(f) for f in [aa_word, root_id, root_letters, qur_meaning, phon, source] if f)

    print(f"\n{'=' * 70}")
    print(f"  WASH GATE — Entry #{eid}: {en_term}")
    print(f"{'=' * 70}")
    print(f"  Root ID:     {root_id or '(NONE)'}")
    print(f"  Root Letters: {root_letters or '(NONE)'}")

    flags, has_root, has_quran, has_root_id = check_text(all_text, en_term)

    if not flags:
        print(f"\n  PASS — entry appears washed")
    else:
        print(f"\n  {len(flags)} FLAG(S):\n")
        for cat, match, msg in flags:
            print(f"  [{cat}] matched: \"{match}\"")
            print(f"    → {msg}\n")

    print(f"  Root letters present: {'YES' if has_root else 'NO'}")
    print(f"  Qur'anic ref present: {'YES' if has_quran else 'NO'}")
    print(f"  Root ID present:      {'YES' if has_root_id else 'NO'}")
    print()

    conn.close()
    return len(flags)


def check_inline(term, definition):
    """Check a proposed definition before writing."""
    print(f"\n{'=' * 70}")
    print(f"  WASH GATE — Pre-write check: {term}")
    print(f"{'=' * 70}")

    flags, has_root, has_quran, has_root_id = check_text(definition, term)

    if not flags:
        print(f"\n  PASS — definition appears washed")
    else:
        print(f"\n  {len(flags)} FLAG(S):\n")
        for cat, msg, detail in flags:
            print(f"  [{cat}] matched: \"{msg}\"")
            print(f"    → {detail}\n")

        # Wash instructions
        print(f"  {'—' * 60}")
        print(f"  WASH REQUIRED — run Translation Washing Algorithm:")
        print(f"  Step 1: Gather synonyms, antonyms, usage, collocations")
        print(f"  Step 2: Strip phantom frameworks, inverted directions, circular defs")
        print(f"  Step 3: Find the CORE — intersection of all synonyms, bounded by antonyms")
        print(f"  Step 4: Connect CORE to AA/Bitig root — not surface definition")
        print(f"  {'—' * 60}")

    print(f"\n  Root letters present: {'YES' if has_root else 'NO'}")
    print(f"  Qur'anic ref present: {'YES' if has_quran else 'NO'}")
    print(f"  Root ID present:      {'YES' if has_root_id else 'NO'}")
    print()

    return len(flags)


def batch_check(limit=0):
    """Check all entries in a1_entries for unwashed glosses."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    query = 'SELECT entry_id, en_term, aa_word, root_id, root_letters, qur_meaning, phonetic_chain, source_form FROM a1_entries ORDER BY entry_id'
    if limit > 0:
        query += f' LIMIT {limit}'
    rows = conn.execute(query).fetchall()

    flagged_entries = []
    clean_count = 0

    for row in rows:
        eid, en_term, aa_word, root_id, root_letters, qur_meaning, phon, source = row
        all_text = ' '.join(str(f) for f in [aa_word, qur_meaning, phon, source] if f)
        flags, _, _, _ = check_text(all_text, en_term or '')

        # Filter out MISSING flags for batch — focus on ACTIVE contamination
        active_flags = [f for f in flags if f[0] != 'MISSING']

        if active_flags:
            flagged_entries.append((eid, en_term, active_flags))
        else:
            clean_count += 1

    print(f"\n{'=' * 70}")
    print(f"  WASH GATE — BATCH AUDIT")
    print(f"{'=' * 70}")
    print(f"  Entries scanned: {len(rows)}")
    print(f"  Clean:           {clean_count}")
    print(f"  Flagged:         {len(flagged_entries)}")
    print(f"{'=' * 70}\n")

    if flagged_entries:
        for eid, en_term, flags in flagged_entries:
            print(f"  #{eid:<5d} {en_term or '(no term)'}")
            for cat, match, msg in flags:
                print(f"         [{cat}] \"{match}\" → {msg}")
            print()

    # Summary by category
    cat_counts = {}
    for _, _, flags in flagged_entries:
        for cat, _, _ in flags:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    if cat_counts:
        print(f"  {'—' * 60}")
        print(f"  CONTAMINATION BY CATEGORY:")
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {cnt}")
        print()

    conn.close()
    return len(flagged_entries)


def list_patterns():
    """List all detection patterns."""
    all_groups = [
        ('COMPOUND FOLK ETYMOLOGIES', COMPOUND_FOLK),
        ('DOWNSTREAM DICTIONARY GLOSSES', DOWNSTREAM_GLOSS),
        ('SURFACE-ONLY DEFINITIONS', SURFACE_ONLY),
        ('FRAMEWORK SMUGGLING', FRAMEWORK_SMUGGLE),
        ('MISSING ROOT INDICATORS', MISSING_ROOT),
        ('TRANSLATOR OUTPUT', TRANSLATOR_OUTPUT),
    ]

    print(f"\n{'=' * 70}")
    print(f"  WASH GATE — ALL DETECTION PATTERNS")
    print(f"{'=' * 70}\n")

    total = 0
    for name, patterns in all_groups:
        print(f"  --- {name} ---")
        for pat, msg in patterns:
            print(f"    /{pat}/")
            print(f"      → {msg}")
            total += 1
        print()

    print(f"  {total} patterns active")
    print(f"\n  Plus 3 PRESENCE checks: root letters, Qur'anic ref, root ID")
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'check' and len(sys.argv) >= 4:
        term = sys.argv[2]
        definition = ' '.join(sys.argv[3:])
        check_inline(term, definition)

    elif cmd == 'entry' and len(sys.argv) >= 3:
        try:
            eid = int(sys.argv[2])
            check_entry(eid)
        except ValueError:
            print(f"Entry ID must be a number: {sys.argv[2]}")

    elif cmd == 'batch':
        limit = int(sys.argv[2]) if len(sys.argv) >= 3 else 0
        batch_check(limit)

    elif cmd == 'patterns':
        list_patterns()

    else:
        print(__doc__)


if __name__ == '__main__':
    main()
