#!/usr/bin/env python3
"""
USLaP Stop Scanner — scans Claude's response text for contamination.
Called by uslap_stop_hook.sh. Reads from stdin.
Exit 0 = clean. Exit 1 = contaminated (violations printed to stdout).
"""
import sys
import os
import re

# Same banned terms as DB triggers + handler gate — SINGLE SOURCE
BANNED_TERMS = [
    "semitic", "loanword", "cognate", "prosthetic vowel",
    "borrowed from greek", "borrowed from latin", "borrowed from persian",
    "borrowed from french", "borrowed from german", "borrowed from sanskrit",
    "proto-indo-european", "proto-slavic", "proto-germanic", "proto-turkic",
    "proto-uralic", "greek origin", "latin origin", "greek source",
    "latin source", "greek root", "latin root",
    "derived from greek", "derived from latin", "derived from french",
    "derived from old french", "derived from sanskrit",
    "native slavic", "native european", "european origin",
    "just slavic", "just european", "pre-greek substrate",
    "indo-european",
    # Platform noise — operator framing of Dīn
    "islamic", "declaration of faith", "religion", "religious",
    "faith tradition", "faith-based", "spiritual tradition",
    "mystical", "holy book", "sacred text", "abrahamic",
    "monotheistic", "muslim world", "islamic world",
    "islamic tradition", "islamic faith", "islamic religion",
    "islamic culture", "islamic civilization", "islamic science",
    "muslim faith", "muslim religion",
    # Weight-sourced contamination — blocked 2026-03-23
    # These are operator cover stories from training data, not AA.
    "hashish user", "hashish-user", "ḥashīshīn", "ḥashshāshīn",
    "hashishin", "hashshashin", "hashashin",
    "old man of the mountain",
]

# "Arabic" — BANNED PERMANENTLY. Zero exceptions. Use AA.
BARE_ARABIC_DETECTOR = r'\barabic\b'
BARE_ARABIC_ALLOWED = [
    # NONE. The word "arabic" is banned permanently.
    # Use AA in all contexts. The word implies ethnicity.
]

# Direction violations
DIRECTION_PATTERNS = [
    r'(?:arabic|persian|turkic)\s+(?:borrowed|adopted|took)\s+from',
    r'(?:greek|latin|sanskrit)\s+(?:origin|source)\b',
]

# Skip lines that are DOCUMENTING contamination (not producing it)
# TIGHTENED 2026-03-23: Single broad words like "operator", "downstream"
# appeared in nearly every USLaP sentence, effectively disabling the scan.
# Now requires multi-word markers that only appear in actual documentation context.
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
]


def scan(text):
    violations = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        low = line.lower().strip()
        if not low or len(low) < 5:
            continue

        # Skip lines documenting contamination
        if any(m in low for m in SKIP_MARKERS):
            continue

        # Skip code blocks, SQL, python
        if low.startswith('```') or low.startswith('import ') or low.startswith('select '):
            continue
        if low.startswith('#') and len(low) < 80:  # comment line
            continue

        for term in BANNED_TERMS:
            if term in low:
                violations.append(f"L{i}: BANNED '{term}' — {line.strip()[:80]}")

        for pat in DIRECTION_PATTERNS:
            m = re.search(pat, low)
            if m:
                violations.append(f"L{i}: DIRECTION '{m.group()}' — {line.strip()[:80]}")

        # Bare "Arabic" check — banned permanently, use AA
        if re.search(BARE_ARABIC_DETECTOR, low):
            if not any(exc in low for exc in BARE_ARABIC_ALLOWED):
                violations.append(f"L{i}: BARE 'Arabic' — use AA, Allah's Arabic, or Lisān Arabic — {line.strip()[:80]}")

    # PROTOCOL COMPLIANCE CHECK
    # If the response contains "NOT FOUND" for any term but does NOT contain
    # evidence of steps 4-7 being executed, the protocol was not followed.
    full_text = text.lower()
    not_found_count = full_text.count("not found")
    if not_found_count > 0:
        has_step4 = any(x in full_text for x in ["step 4", "search all", "bitig", "compiler", "legacy"])
        has_step5 = any(x in full_text for x in ["step 5", "aa candidate", "root_dictionary", "quran_root"])
        has_step6 = any(x in full_text for x in ["step 6", "bi candidate", "kashgari", "bitig_a1"])
        has_step7 = any(x in full_text for x in ["step 7", "quf", "ratio", "pass", "fail"])

        if not (has_step4 or has_step5 or has_step6 or has_step7):
            violations.append(
                f"PROTOCOL INCOMPLETE: {not_found_count} term(s) 'NOT FOUND' but steps 4-7 not executed. "
                f"Protocol requires: search ALL → QUF validate → selfaudit → washing check. "
                f"Stopping at step 2 is not compliance."
            )

    return violations


def scan_root_claims(text):
    """
    LAYER 4: ROOT VERIFICATION
    Any AA root pattern (X-X-X with AA letters) in prose
    must exist in the lattice. If the compute engine outputs
    a root from weights that isn't in the lattice → VIOLATION.
    """
    import sqlite3
    try:
        from uslap_db_connect import connect as _uslap_connect
        _HAS_WRAPPER = True
    except ImportError:
        _HAS_WRAPPER = False
    violations = []
    # Match AA root patterns: letter-letter-letter (hyphenated)
    root_pattern = re.compile(r'([\u0621-\u064A])\-([\u0621-\u064A])\-([\u0621-\u064A])(?:\-([\u0621-\u064A]))?')

    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')
        conn = _uslap_connect(db_path) if _HAS_WRAPPER else sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        # Load from 'roots' table (correct name, not 'root_translations')
        qrd_roots = set()
        try:
            qrd_roots = set(r[0] for r in conn.execute("SELECT root_letters FROM roots WHERE root_letters IS NOT NULL").fetchall())
        except Exception:
            pass
        # Also get all roots from entries (includes ORIG2, compounds, etc.)
        lattice_roots = set()
        try:
            lattice_roots = set(r[0] for r in conn.execute("SELECT DISTINCT root_letters FROM entries WHERE root_letters IS NOT NULL").fetchall())
        except Exception:
            pass
        all_valid = qrd_roots | lattice_roots
        conn.close()
    except:
        return []  # If DB unavailable, skip this check

    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        low = line.strip()
        if not low or len(low) < 5:
            continue
        # Skip documentation lines
        if any(m in low.lower() for m in SKIP_MARKERS):
            continue
        # Skip code/SQL
        if low.startswith('```') or low.startswith('import ') or low.startswith('select ') or low.startswith('|'):
            continue

        for m in root_pattern.finditer(line):
            root = m.group(0)
            if root not in all_valid:
                # Check if it's a sub-root or compound part
                if '+' not in line[max(0,m.start()-5):m.end()+5]:
                    violations.append(f"L{i}: ROOT '{root}' NOT IN root_translations OR LATTICE — weight-generated? — {line.strip()[:80]}")

    return violations


def scan_unsourced_claims(text):
    """
    LAYER 5: UNSOURCED CLAIM DETECTION + MEANING VERIFICATION

    Part A: Any linguistic claim without a source reference → BLOCKED.
    Part B: Any root + meaning claim → verify meaning against root_translations.
            If the meaning doesn't match root_translations → weight-generated → BLOCKED.
    """
    import sqlite3
    violations = []

    # Load root_translations meanings for verification
    qrd_meanings = {}
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')
        conn = _uslap_connect(db_path) if _HAS_WRAPPER else sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        for r in conn.execute("SELECT root_letters, primary_meaning FROM roots WHERE primary_meaning IS NOT NULL AND primary_meaning != ''").fetchall():
            qrd_meanings[r[0]] = r[1].lower()
        conn.close()
    except:
        pass

    # Patterns that indicate a linguistic claim
    claim_patterns = [
        re.compile(r'[\u0621-\u064A].*(?:means|=|→).*[a-zA-Z]'),
        re.compile(r'[\u0621-\u064A]\s*/\s*[a-zA-Z]'),
    ]
    # Patterns that indicate a source
    source_patterns = [
        re.compile(r'Q\d+:\d+'),
        re.compile(r'#\d+'),
        re.compile(r'root_translations|QV\d+|R\d+|T\d+'),
        re.compile(r'quran_root|a1_entries|word_roots'),
        re.compile(r'Kashgari|Qashqari|SC\d+'),
        re.compile(r'\d+ tokens'),
    ]
    # Root pattern for meaning verification
    root_pattern = re.compile(r'([\u0621-\u064A])\-([\u0621-\u064A])\-([\u0621-\u064A])(?:\-([\u0621-\u064A]))?')
    # Meaning pattern: root followed by = or / or "means" then English text
    meaning_pattern = re.compile(r'([\u0621-\u064A]\-[\u0621-\u064A]\-[\u0621-\u064A](?:\-[\u0621-\u064A])?)\s*(?:=|/|means)\s*([a-zA-Z][\w\s,]+)')

    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        low = line.strip()
        if not low or len(low) < 10:
            continue
        if any(m in low.lower() for m in SKIP_MARKERS):
            continue
        if low.startswith('```') or low.startswith('|') or low.startswith('#'):
            continue

        # Part A: unsourced claim
        has_claim = any(p.search(line) for p in claim_patterns)
        has_source = any(p.search(line) for p in source_patterns)
        if has_claim and not has_source:
            violations.append(f"L{i}: UNSOURCED CLAIM — no DB/Qur'an reference — {line.strip()[:80]}")

        # Part B: meaning verification against root_translations
        if qrd_meanings:
            for m in meaning_pattern.finditer(line):
                root = m.group(1)
                claimed_meaning = m.group(2).strip().lower()
                if root in qrd_meanings:
                    db_meaning = qrd_meanings[root]
                    # Check if ANY word from the claimed meaning appears in DB meaning
                    claimed_words = set(w for w in claimed_meaning.split() if len(w) > 3)
                    db_words = set(w for w in db_meaning.split() if len(w) > 3)
                    overlap = claimed_words & db_words
                    if claimed_words and not overlap:
                        violations.append(
                            f"L{i}: MEANING MISMATCH — '{root}' claimed as '{claimed_meaning}' "
                            f"but root_translations says '{db_meaning[:60]}' — {line.strip()[:60]}"
                        )

    return violations


def scan_operator_labels(text):
    """
    LAYER 6: OPERATOR LABEL DETECTION

    English words that fail QUF (unfalsifiable, non-universal, non-quantifiable)
    but are used as if they were neutral vocabulary.

    Loaded from operator_label_register table.
    If a label appears WITHOUT its root form nearby → VIOLATION.
    """
    import sqlite3
    violations = []

    # Load operator labels from DB
    labels = {}
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')
        try:
            from uslap_db_connect import connect as _uslap_connect
            conn = _uslap_connect(db_path)
        except ImportError:
            conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        for r in conn.execute("SELECT operator_label, correct_form FROM operator_label_register").fetchall():
            labels[r['operator_label'].lower()] = r['correct_form']
        conn.close()
    except Exception:
        return []

    if not labels:
        return []

    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        low = line.lower().strip()
        if not low or len(low) < 5:
            continue
        # Skip documentation/correction lines
        if any(m in low for m in SKIP_MARKERS):
            continue
        if low.startswith('```') or low.startswith('|') or low.startswith('#'):
            continue
        # Skip lines that ARE the correction (contain → USE: or correct_form)
        if '→ use:' in low or 'correct_form' in low or 'operator_label' in low:
            continue
        # Skip lines documenting the label as an operator term
        if 'operator label' in low or 'operator term' in low or 'fails quf' in low:
            continue

        for label, correct in labels.items():
            if re.search(r'\b' + re.escape(label) + r'\b', low):
                # Check if the root form is nearby (same line or ±1 line)
                context = low
                if i > 1:
                    context = lines[i-2].lower() + ' ' + context
                if i < len(lines):
                    context = context + ' ' + lines[i].lower() if i < len(lines) else context

                # If root form (AA letters) present nearby → OK (documenting correctly)
                has_root = any('\u0621' <= c <= '\u064A' for c in context)
                if not has_root:
                    violations.append(
                        f"L{i}: OPERATOR LABEL '{label}' used without root form. "
                        f"Use: {correct} — {line.strip()[:60]}"
                    )

    return violations


def scan_corridor_scripts(text):
    """
    LAYER 7: CORRIDOR SCRIPT DETECTION

    DS08 (Hebrew) and other non-AA scripts MUST NEVER appear in project output.
    Allah's Arabic is the source. Corridor scripts are degradation corridors.
    They do not enter any part of this project — not in code, not in output,
    not in comments, not in documentation.

    Banned script ranges:
      - Hebrew:    U+0590–U+05FF (DS08 corridor)
      - Syriac:    U+0700–U+074F (DS01 corridor)
      - Samaritan: U+0800–U+083F (DS08 variant)
      - Mandaic:   U+0840–U+085F (DS01 variant)

    EXCEPTION: None. Zero tolerance. No context makes this acceptable.
    """
    import re
    violations = []

    # Hebrew block: U+0590 to U+05FF
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    # Syriac block: U+0700 to U+074F
    syriac_pattern = re.compile(r'[\u0700-\u074F]')
    # Samaritan block: U+0800 to U+083F
    samaritan_pattern = re.compile(r'[\u0800-\u083F]')
    # Mandaic block: U+0840 to U+085F
    mandaic_pattern = re.compile(r'[\u0840-\u085F]')

    script_checks = [
        (hebrew_pattern, 'DS08/HEBREW'),
        (syriac_pattern, 'DS01/SYRIAC'),
        (samaritan_pattern, 'DS08-VAR/SAMARITAN'),
        (mandaic_pattern, 'DS01-VAR/MANDAIC'),
    ]

    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern, script_name in script_checks:
            matches = pattern.findall(line)
            if matches:
                chars = ''.join(matches)
                violations.append(
                    f"L{i}: ⛔⛔⛔ {script_name} SCRIPT DETECTED: '{chars}' — "
                    f"CORRIDOR SCRIPT IN PROJECT OUTPUT. Use Allah's Arabic ONLY. "
                    f"— {line.strip()[:60]}"
                )

    return violations


if __name__ == "__main__":
    # Import kernel for semantic paraphrase detection
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from uslap_contamination_kernel import scan_kernel, format_violations

    text = sys.stdin.read()

    # Layer 1: Exact term matching
    exact_violations = scan(text)

    # Layer 2: Semantic kernel (catches paraphrases)
    kernel_violations = scan_kernel(text)

    # Layer 4: Root verification against root_translations
    root_violations = scan_root_claims(text)

    # Layer 5: Unsourced claim detection
    unsourced_violations = scan_unsourced_claims(text)

    # Layer 6: Operator label detection
    label_violations = scan_operator_labels(text)

    # Layer 7: Corridor script detection
    script_violations = scan_corridor_scripts(text)

    all_output = []

    # SCRIPT VIOLATIONS FIRST — highest severity
    if script_violations:
        all_output.append("⛔⛔⛔ CORRIDOR SCRIPT IN OUTPUT — MOST SEVERE VIOLATION:")
        for v in script_violations:
            all_output.append(f"  {v}")

    if exact_violations:
        all_output.append("⛔ CONTAMINATED OUTPUT — exact banned terms:")
        for v in exact_violations:
            all_output.append(f"  {v}")

    if kernel_violations:
        all_output.append(format_violations(kernel_violations))

    if root_violations:
        all_output.append("⛔ WEIGHT-GENERATED ROOTS — not in root_translations or lattice:")
        for v in root_violations:
            all_output.append(f"  {v}")

    if unsourced_violations:
        all_output.append("⛔ UNSOURCED CLAIMS — no DB/Qur'an reference:")
        for v in unsourced_violations:
            all_output.append(f"  {v}")

    if label_violations:
        all_output.append("⛔ OPERATOR LABELS — unfalsifiable vocabulary, use root form:")
        for v in label_violations:
            all_output.append(f"  {v}")

    if all_output:
        total = len(exact_violations) + len(kernel_violations) + len(root_violations) + len(unsourced_violations) + len(label_violations) + len(script_violations)
        print('\n'.join(all_output))
        print(f"\n{total} total violation(s). Re-derive from DB sources.")
        sys.exit(1)
    else:
        sys.exit(0)
