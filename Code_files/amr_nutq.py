#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر نُطْق — ARTICULATION ENGINE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: ن-ط-ق — to speak, articulate, utter
Q21:63 إِن كَانُوا يَنطِقُونَ — if they can speak

The عَقْل thinks. The نُطْق speaks.

Takes raw computation from amr_aql.py and articulates it into:
  1. ATT format (Arabic / transliteration / English)
  2. QUF triads
  3. Shift chains
  4. Root expansion reports
  5. Entry cards
  6. DP-tagged output
  7. Comparison tables
  8. Batch reports

Every output follows documentary conventions from CLAUDE.md:
  - Full phrases (Allah's Arabic, never bare "Arabic")
  - ATT for every AA word
  - Wrapper names in quotes
  - DP tags on contaminated claims
  - Direction ALWAYS Allah → downstream
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_alphabet import ABJAD, ALPHABET

try:
    from uslap_db_connect import connect as _connect
    _HAS_DB = True
except ImportError:
    _HAS_DB = False

try:
    from amr_aql import deduce_meaning, reverse_trace, expand_root, relate_roots, hypothesise
    _HAS_AQL = True
except ImportError:
    _HAS_AQL = False


# ═══════════════════════════════════════════════════════════════════════
# TRANSLITERATION TABLE — for ATT format
# ═══════════════════════════════════════════════════════════════════════

TRANSLIT = {
    'ء': 'ʾ', 'ا': 'ā', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
    'ح': 'ḥ', 'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z',
    'س': 's', 'ش': 'sh', 'ص': 'ṣ', 'ض': 'ḍ', 'ط': 'ṭ', 'ظ': 'ẓ',
    'ع': 'ʿ', 'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l',
    'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
    # Hamza carriers
    'أ': 'ʾa', 'إ': 'ʾi', 'آ': 'ʾā', 'ٱ': 'a',
    # Tashkeel
    'َ': 'a', 'ُ': 'u', 'ِ': 'i', 'ّ': '(shadda)', 'ْ': '',
    'ً': 'an', 'ٌ': 'un', 'ٍ': 'in',
    # Ta marbuta, alif maqsura
    'ة': 'a', 'ى': 'ā',
}


def transliterate(aa_text):
    """Transliterate Arabic text to Latin scholarly notation."""
    result = []
    i = 0
    text = aa_text
    while i < len(text):
        ch = text[i]
        if ch in TRANSLIT:
            result.append(TRANSLIT[ch])
        elif ch == ' ':
            result.append(' ')
        elif ch == '-':
            result.append('-')
        elif ch.isascii():
            result.append(ch)
        # Skip unknown diacritics
        i += 1
    return ''.join(result)


# ═══════════════════════════════════════════════════════════════════════
# 1. ATT FORMAT — Arabic / transliteration / English
# ═══════════════════════════════════════════════════════════════════════

def att(arabic, english, translit_override=None):
    """Format a term in ATT notation.

    ATT = Arabic / transliteration / English translation
    Mandatory for every Allah's Arabic word in documents.

    Args:
        arabic: Arabic text
        english: English meaning
        translit_override: optional manual transliteration

    Returns:
        formatted ATT string
    """
    tr = translit_override or transliterate(arabic)
    return f"{arabic} / {tr} / {english}"


def att_root(root_letters, meaning=None):
    """Format a root in ATT notation with abjad value.

    Args:
        root_letters: hyphenated root (e.g. 'ك-ف-ر')
        meaning: optional English meaning

    Returns:
        formatted root string
    """
    letters = [l for l in root_letters.split('-') if l.strip()]
    tr_parts = [TRANSLIT.get(l, l) for l in letters]
    tr = '-'.join(tr_parts)

    abjad_sum = sum(ABJAD.get(l, 0) for l in letters)

    if meaning:
        return f"{root_letters} / {tr} / {meaning} [{abjad_sum}]"
    return f"{root_letters} / {tr} [{abjad_sum}]"


# ═══════════════════════════════════════════════════════════════════════
# 2. QUF TRIAD DISPLAY
# ═══════════════════════════════════════════════════════════════════════

def format_quf(quf_q, quf_u, quf_f, quf_pass=None):
    """Format QUF triad result.

    Q = Qur'anic attestation
    U = Uniqueness (no duplicate)
    F = Phonetic shift validity

    Args:
        quf_q, quf_u, quf_f: PASS/FAIL/ORIG2_SKIP
        quf_pass: overall PASS/FAIL (computed if None)

    Returns:
        formatted QUF line
    """
    if quf_pass is None:
        quf_pass = 'PASS' if all(
            v in ('PASS', 'ORIG2_SKIP') for v in (quf_q, quf_u, quf_f)
        ) else 'FAIL'

    q_mark = '✓' if quf_q in ('PASS', 'ORIG2_SKIP') else '✗'
    u_mark = '✓' if quf_u in ('PASS', 'ORIG2_SKIP') else '✗'
    f_mark = '✓' if quf_f in ('PASS', 'ORIG2_SKIP') else '✗'
    p_mark = '✓' if quf_pass == 'PASS' else '✗'

    return (
        f"QUF: Q={quf_q}[{q_mark}] U={quf_u}[{u_mark}] F={quf_f}[{f_mark}] "
        f"→ {quf_pass}[{p_mark}]"
    )


# ═══════════════════════════════════════════════════════════════════════
# 3. SHIFT CHAIN DISPLAY
# ═══════════════════════════════════════════════════════════════════════

def format_shift_chain(chain):
    """Format a shift chain for display.

    Args:
        chain: list of shift steps, e.g. ['c←ك(S20)', 'v←ف(S08)', 'r←ر(S15)']

    Returns:
        formatted shift chain string
    """
    if not chain:
        return "No shifts"
    return " → ".join(chain)


def format_shift_id(shift_id):
    """Format a shift ID with its description.

    Requires DB for shift names.
    """
    if not _HAS_DB:
        return shift_id

    conn = _connect()
    row = conn.execute(
        "SELECT shift_name, description FROM shift_lookup WHERE shift_id = ?",
        (shift_id,)
    ).fetchone()
    conn.close()

    if row:
        return f"{shift_id} ({row['shift_name']}): {row['description']}"
    return shift_id


# ═══════════════════════════════════════════════════════════════════════
# 4. ENTRY CARD — full formatted entry
# ═══════════════════════════════════════════════════════════════════════

def format_entry_card(entry_data):
    """Format a complete entry card from DB data.

    Args:
        entry_data: dict with entry fields (from entries table)

    Returns:
        multi-line formatted entry card
    """
    lines = []
    lines.append("═" * 60)

    # Header
    entry_id = entry_data.get('entry_id', '?')
    en_term = entry_data.get('en_term', '')
    root_id = entry_data.get('root_id', '')
    lines.append(f"ENTRY: {entry_id} | {en_term} | ROOT: {root_id}")
    lines.append("─" * 60)

    # AA root + meaning
    aa_root = entry_data.get('root_letters', '')
    aa_form = entry_data.get('aa_word', '')
    correct_meaning = entry_data.get('notes', '')
    if aa_root:
        lines.append(f"AA ROOT: {att_root(aa_root, correct_meaning)}")
    if aa_form:
        lines.append(f"AA FORM: {aa_form}")

    # Terms
    if en_term:
        lines.append(f"EN: {en_term}")
    ru_term = entry_data.get('ru_term', '')
    if ru_term:
        lines.append(f"RU: {ru_term}")
    fa_term = entry_data.get('fa_term', '')
    if fa_term:
        lines.append(f"FA: {fa_term}")

    # Shift + corridor
    phonetic_chain = entry_data.get('phonetic_chain', '')
    if phonetic_chain:
        lines.append(f"SHIFTS: {phonetic_chain}")
    ds_corridor = entry_data.get('ds_corridor', '')
    if ds_corridor:
        lines.append(f"CORRIDOR: {ds_corridor}")
    decay_level = entry_data.get('decay_level', '')
    if decay_level:
        lines.append(f"DECAY: {decay_level}")

    # QUF
    quf_q = entry_data.get('quf_q', '')
    quf_u = entry_data.get('quf_u', '')
    quf_f = entry_data.get('quf_f', '')
    quf_pass = entry_data.get('quf_pass', '')
    if quf_q:
        lines.append(format_quf(quf_q, quf_u, quf_f, quf_pass))

    # DP codes
    dp_codes = entry_data.get('dp_codes', '')
    if dp_codes:
        lines.append(f"DP: {dp_codes}")

    # Qur'anic refs
    qur_refs = entry_data.get('qur_refs', '')
    if qur_refs:
        lines.append(f"QUR: {qur_refs}")

    # Tasrif summary for root (if available)
    if aa_root:
        try:
            from amr_tasrif import get_root_forms
            forms = get_root_forms(aa_root)
            if forms:
                unique = len(set(f['word'] for f in forms))
                verbs = sum(1 for f in forms if f.get('word_type') == 'VERB')
                nouns = sum(1 for f in forms if f.get('word_type') == 'NOUN')
                lines.append(f"TASRIF: {len(forms)} tokens, {unique} unique forms ({verbs}V + {nouns}N)")
        except Exception:
            pass

    lines.append("═" * 60)
    return '\n'.join(lines)


def format_entry_card_from_db(entry_id):
    """Load entry from DB and format as card."""
    if not _HAS_DB:
        return f"No DB connection for entry {entry_id}"

    conn = _connect()
    row = conn.execute("SELECT * FROM entries WHERE entry_id = ?", (entry_id,)).fetchone()
    conn.close()

    if not row:
        return f"Entry not found: {entry_id}"

    return format_entry_card(dict(row))


# ═══════════════════════════════════════════════════════════════════════
# 5. ROOT EXPANSION REPORT
# ═══════════════════════════════════════════════════════════════════════

def format_root_report(tree):
    """Format a full root expansion tree (from amr_aql.expand_root) as a report.

    Args:
        tree: dict from expand_root()

    Returns:
        multi-line formatted report
    """
    if 'error' in tree:
        return f"ERROR: {tree['error']}"

    r = tree['root']
    s = tree['summary']
    lines = []

    # Header
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║ ROOT: {r['root_id']} | {att_root(r['root_letters'], r['primary_meaning'])}")
    _qt = r.get('quran_tokens', 0) or 0
    if _qt > 0:
        lines.append(f"║ QURANIC TOKENS: {_qt}")
    else:
        lines.append(f"║ ⛔ UNATTESTED — root NOT in 77,881 Qur'anic words. LISAN ARABIC ONLY.")
    lines.append(f"║ COMPUTED: {r['computed_meaning']['composition']}")
    lines.append(f"║ DEDUCTION: {r['computed_meaning']['deduction']}")
    lines.append("╠" + "═" * 58 + "╣")

    # Downstream counts
    lines.append(f"║ DOWNSTREAM ({s['total_downstream']} total):")
    lines.append(f"║   EN: {s['en_entries']} | RU: {s['ru_entries']} | FA: {s['fa_entries']}")
    lines.append(f"║   EU: {s['european']} | Latin: {s['latin']} | Bitig: {s['bitig']} | Uzbek: {s['uzbek']}")
    lines.append(f"║   Derivatives: {s['derivatives']} | Cross-refs: {s['cross_refs']}")
    lines.append(f"║   Qur'anic words: {s['quranic_words']} | Names of Allah: {s['names_of_allah']}")

    # EN entries
    if tree['entries']['en']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ EN ENTRIES:")
        for e in tree['entries']['en']:
            dp = f" [DP:{e.get('dp_codes', '')}]" if e.get('dp_codes') else ""
            lines.append(f"║   {e.get('entry_id', '?')}: {e.get('en_term', '?')}{dp}")

    # RU entries
    if tree['entries']['ru']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ RU ENTRIES:")
        for e in tree['entries']['ru']:
            lines.append(f"║   {e.get('entry_id', '?')}: {e.get('ru_term', '?')}")

    # European
    if tree['european']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ EUROPEAN DOWNSTREAM:")
        for e in tree['european'][:10]:
            lines.append(f"║   {e.get('lang', '?')}: {e.get('term', '?')}")
        if len(tree['european']) > 10:
            lines.append(f"║   ... +{len(tree['european']) - 10} more")

    # Bitig
    if tree['bitig']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ BITIG ENTRIES:")
        for e in tree['bitig']:
            lines.append(f"║   {e.get('entry_id', '?')}: {e.get('term', '?')}")

    # Names of Allah
    if tree['names_of_allah']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ NAMES OF ALLAH:")
        for n in tree['names_of_allah']:
            lines.append(
                f"║   {n.get('name_id', '?')}: "
                f"{n.get('aa_name', '?')} / {n.get('english_name', '?')}"
            )

    # Qur'anic words sample
    if tree['quranic_words']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append(f"║ QURANIC WORDS (first {min(5, len(tree['quranic_words']))}):")
        for w in tree['quranic_words'][:5]:
            tr = w.get('correct_translation', '')
            tr_str = f" — {tr}" if tr else ""
            lines.append(
                f"║   Q{w['surah']}:{w['ayah']}:{w['word_position']} "
                f"{w.get('aa_word', '?')}{tr_str}"
            )
        if len(tree['quranic_words']) > 5:
            lines.append(f"║   ... +{len(tree['quranic_words']) - 5} more")

    # QV entries
    if tree['qv_entries']:
        lines.append("╠" + "─" * 58 + "╣")
        lines.append("║ QV REGISTER:")
        for qv in tree['qv_entries']:
            lines.append(
                f"║   {qv.get('QV_ID', '?')}: {qv.get('CORRUPTION_TYPE', '?')} — "
                f"{qv.get('CORRECT_ROOT_TRANSLATION', '?')[:40]}"
            )

    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 6. HYPOTHESIS REPORT
# ═══════════════════════════════════════════════════════════════════════

def format_hypothesis(word, candidates=None, language='en'):
    """Format a full hypothesis report for a downstream word.

    If candidates not provided, runs hypothesise() from عَقْل.

    Args:
        word: downstream word
        candidates: optional pre-computed candidates list
        language: source language

    Returns:
        multi-line formatted report
    """
    if candidates is None:
        if not _HAS_AQL:
            return f"عَقْل not available — cannot hypothesise for '{word}'"
        candidates = hypothesise(word, language)

    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║ HYPOTHESIS: '{word}' ({language})")
    lines.append(f"║ CANDIDATES: {len(candidates)}")
    lines.append("╠" + "═" * 58 + "╣")

    for i, c in enumerate(candidates[:10]):
        tokens = c.get('quranic_tokens', 0) or 0
        entries = c.get('existing_entries', 0)
        in_db = c.get('verified', False)

        # Attestation status: Qur'anic > DB-only > unverified
        if tokens > 0:
            status = f"QUR'ANIC ({tokens} tokens)"
        elif in_db:
            status = "LISAN ONLY (in DB, 0 Qur'anic tokens)"
        else:
            status = "unverified"

        lines.append(f"║ [{i+1}] {c['root_letters']} — score={c['score']} [{status}]")
        lines.append(f"║     {c['composition']}")
        lines.append(f"║     {c['deduction']}")
        lines.append(f"║     Chain: {format_shift_chain(c['shift_chain'])}")
        if in_db:
            lines.append(f"║     Qur'anic: {tokens} tokens | Entries: {entries}")
            if c.get('primary_meaning'):
                lines.append(f"║     DB meaning: {c['primary_meaning']}")
        if i < len(candidates) - 1 and i < 9:
            lines.append("║" + "─" * 58)

    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 7. COMPARISON TABLE — two roots side by side
# ═══════════════════════════════════════════════════════════════════════

def format_comparison(root_a, root_b, relation=None):
    """Format a side-by-side root comparison.

    If relation not provided, runs relate_roots() from عَقْل.

    Args:
        root_a, root_b: root_letters strings
        relation: optional pre-computed relation dict

    Returns:
        multi-line formatted comparison
    """
    if relation is None:
        if not _HAS_AQL:
            return "عَقْل not available"
        relation = relate_roots(root_a, root_b)

    ma = relation['root_a']['meaning']
    mb = relation['root_b']['meaning']

    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║ COMPARISON: {root_a} vs {root_b}")
    lines.append("╠" + "═" * 28 + "╦" + "═" * 29 + "╣")
    lines.append(f"║ {'ROOT A':^27} ║ {'ROOT B':^28} ║")
    lines.append("╠" + "═" * 28 + "╬" + "═" * 29 + "╣")
    lines.append(f"║ {root_a:^27} ║ {root_b:^28} ║")
    lines.append(f"║ Abjad: {ma['abjad_sum']:^20} ║ Abjad: {mb['abjad_sum']:^20} ║")

    sem_a = '+'.join(ma['semantic_fields'])
    sem_b = '+'.join(mb['semantic_fields'])
    lines.append(f"║ {sem_a:^27} ║ {sem_b:^28} ║")

    lines.append("╠" + "═" * 28 + "╩" + "═" * 29 + "╣")

    # Relationships
    if relation['relationships']:
        lines.append(f"║ RELATIONSHIPS ({relation['relationship_count']}):")
        for rel in relation['relationships']:
            rtype = rel['type']
            desc = rel['description']
            severity = rel.get('severity', '')
            sev_str = f" [{severity}]" if severity else ""
            lines.append(f"║   {rtype}{sev_str}")
            # Wrap description
            while desc:
                chunk = desc[:54]
                desc = desc[54:]
                lines.append(f"║     {chunk}")
    else:
        lines.append("║ No structural relationships found.")

    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 8. DP-TAGGED OUTPUT
# ═══════════════════════════════════════════════════════════════════════

DP_DESCRIPTIONS = {
    'DP01': 'Phonetic shift not documented',
    'DP02': 'Root direction reversed',
    'DP03': 'Phantom etymology injected',
    'DP04': 'Time depth falsified',
    'DP05': 'Script attribution falsified',
    'DP06': 'Root vowel pattern changed',
    'DP07': 'Meaning narrowed/shifted',
    'DP08': 'Ethnic label injected',
    'DP09': 'Genealogy severed',
    'DP10': 'Source text corrupted',
    'DP11': 'Translation washed',
    'DP12': 'Root replaced entirely',
    'DP13': 'Action frozen to noun',
    'DP14': 'Scope collapsed',
    'DP15': 'Root inverted (antonym)',
    'DP16': 'Attribute genericised',
    'DP17': 'Function replacement',
    'DP18': 'Phantom language family',
    'DP19': 'Academic authority claim',
    'DP20': 'Physical destruction cover',
}


def format_dp(dp_codes_str):
    """Format DP codes with descriptions.

    Args:
        dp_codes_str: comma-separated DP codes, e.g. 'DP02, DP07'

    Returns:
        formatted DP output
    """
    if not dp_codes_str:
        return "No DP codes"

    codes = [c.strip() for c in dp_codes_str.split(',')]
    lines = []
    for code in codes:
        desc = DP_DESCRIPTIONS.get(code, 'Unknown detection pattern')
        lines.append(f"  {code}: {desc}")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 9. BATCH REPORT — multiple entries/roots
# ═══════════════════════════════════════════════════════════════════════

def format_batch_report(items, title="BATCH REPORT"):
    """Format a batch of items as a summary table.

    Args:
        items: list of dicts, each with at minimum 'id' and 'status' keys
        title: report title

    Returns:
        formatted table
    """
    if not items:
        return f"{title}: No items."

    lines = []
    lines.append(f"\n{'═' * 60}")
    lines.append(f" {title} ({len(items)} items)")
    lines.append(f"{'═' * 60}")

    # Determine columns from first item
    keys = list(items[0].keys())
    # Compute column widths
    widths = {}
    for k in keys:
        widths[k] = max(len(str(k)), max(len(str(item.get(k, ''))) for item in items))
        widths[k] = min(widths[k], 30)  # cap width

    # Header
    header = " | ".join(f"{k:{widths[k]}}" for k in keys)
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for item in items:
        row = " | ".join(
            f"{str(item.get(k, ''))[:widths[k]]:{widths[k]}}" for k in keys
        )
        lines.append(row)

    lines.append(f"{'═' * 60}")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 10. LATTICE SUMMARY — quick overview of DB state
# ═══════════════════════════════════════════════════════════════════════

def format_lattice_summary():
    """Generate a formatted summary of the current lattice state."""
    if not _HAS_DB:
        return "No DB connection"

    conn = _connect()
    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    lines.append("║          USLaP LATTICE STATE SUMMARY")
    lines.append("╠" + "═" * 58 + "╣")

    # Core counts
    counts = {}
    tables = [
        ('roots', 'Roots'),
        ('entries', 'Entries (EN/RU/FA)'),
        ('european_a1_entries', 'European'),
        ('latin_a1_entries', 'Latin Hub'),
        ('bitig_a1_entries', 'Bitig'),
        ('uzbek_vocabulary', 'Uzbek'),
        ('a4_derivatives', 'Derivatives'),
        ('a5_cross_refs', 'Cross-refs'),
        ('names_of_allah', 'Names of Allah'),
        ('quran_word_roots', 'Qur\'anic words'),
        ('qv_translation_register', 'QV Register'),
        ('child_schema', 'Peoples'),
    ]

    for table, label in tables:
        try:
            row = conn.execute(f"SELECT count(*) as c FROM {table}").fetchone()
            count = row['c'] if row else 0
            counts[label] = count
            lines.append(f"║   {label:.<40} {count:>6}")
        except Exception:
            lines.append(f"║   {label:.<40} {'N/A':>6}")

    # Index
    try:
        idx_row = conn.execute("SELECT count(*) as c FROM lattice_index").fetchone()
        edge_row = conn.execute(
            "SELECT count(*) as c FROM lattice_index WHERE relationship_type IS NOT NULL"
        ).fetchone()
        lines.append("╠" + "─" * 58 + "╣")
        lines.append(f"║   {'Index nodes':.<40} {idx_row['c']:>6}")
    except Exception:
        pass

    # Triggers
    try:
        trig = conn.execute(
            "SELECT count(*) as c FROM sqlite_master WHERE type='trigger'"
        ).fetchone()
        lines.append(f"║   {'DB triggers':.<40} {trig['c']:>6}")
    except Exception:
        pass

    conn.close()
    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 11. WRAPPER NAME FORMAT
# ═══════════════════════════════════════════════════════════════════════

# Qur'anic names that are NOT wrapped
QURANIC_NAMES = {
    'مِصْر', 'فِرْعَوْن', 'بَابِل', 'مَكَّة', 'يَثْرِب', 'سَبَأ',
    'عَاد', 'ثَمُود', 'مَدْيَن', 'لُوط', 'نُوح', 'إِبْرَاهِيم',
    'مُوسَى', 'عِيسَى', 'مَرْيَم', 'دَاوُود', 'سُلَيْمَان',
    'يُوسُف', 'يَعْقُوب', 'إِسْمَاعِيل', 'إِسْحَاق', 'هَارُون',
    'ذُو القَرْنَيْن', 'لُقْمَان',
}


def wrapper_name(name, modern_equivalent=None):
    """Format a non-Qur'anic name with wrapper quotes.

    Qur'anic names pass through unchanged.
    Non-Qur'anic names get quotes + modern equivalent.
    """
    if name in QURANIC_NAMES:
        return name
    if modern_equivalent:
        return f'"{name}" ({modern_equivalent})'
    return f'"{name}"'


# ═══════════════════════════════════════════════════════════════════════
# 12. EXPLAIN ROOT — full traced explanation back to 28 letters
# ═══════════════════════════════════════════════════════════════════════

def explain_root(root_id_or_letters):
    """Generate a full traced explanation of a root.

    Every claim traces to:
      1. Letter values (from amr_alphabet.py — fixed, not computed)
      2. Qur'anic attestation (from quran_word_roots — observed, not interpreted)
      3. DB entries (from entries/european/latin/bitig — documented, not generated)

    Args:
        root_id_or_letters: 'R24' or 'ك-ف-ر'

    Returns:
        multi-line traced explanation
    """
    if not _HAS_AQL:
        return "عَقْل not available"

    tree = expand_root(root_id_or_letters)
    if 'error' in tree:
        return f"ERROR: {tree['error']}"

    r = tree['root']
    root_letters = r['root_letters']
    letters_list = [l for l in root_letters.split('-') if l.strip()]
    meaning = r['computed_meaning']

    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║ EXPLANATION: {att_root(root_letters, r['primary_meaning'])}")
    lines.append("╠" + "═" * 58 + "╣")

    # LAYER 1: Letters → meaning (atomic, no DB needed)
    lines.append("║")
    lines.append("║ LAYER 1 — LETTERS (fixed values, 28 letter system)")
    lines.append("║ " + "─" * 56)
    for i, l_data in enumerate(meaning['letters']):
        position = ['DOMAIN (فاء)', 'ACTION (عين)', 'RESULT (لام)'][i] if i < 3 else f'POS-{i+1}'
        letter_meta = ALPHABET.get(l_data['letter'], {})
        name = letter_meta.get('name', '?')
        lines.append(
            f"║   {l_data['letter']} ({name}) = abjad {l_data['abjad']} "
            f"= {l_data['semantic']} → {position}"
        )
    lines.append(f"║   COMPOSITION: {meaning['composition']}")
    lines.append(f"║   DEDUCTION: {meaning['deduction']}")

    # LAYER 2: Qur'anic attestation
    lines.append("║")
    lines.append("║ LAYER 2 — QURANIC ATTESTATION (observed in 6,236 ayat)")
    lines.append("║ " + "─" * 56)
    lines.append(f"║   Total tokens: {r['quran_tokens']}")

    if tree['quranic_words']:
        # Group by form
        forms = defaultdict(int)
        for w in tree['quranic_words']:
            form = w.get('aa_word', '?')
            forms[form] += 1
        top_forms = sorted(forms.items(), key=lambda x: -x[1])[:5]
        for form, count in top_forms:
            lines.append(f"║   {form}: {count} occurrences")

        # Show first 3 with translation
        lines.append("║   Sample attestations:")
        for w in tree['quranic_words'][:3]:
            tr = w.get('correct_translation', '')
            tr_str = f" — {tr}" if tr else ""
            lines.append(
                f"║     Q{w['surah']}:{w['ayah']}:{w['word_position']} "
                f"{w.get('aa_word', '?')}{tr_str}"
            )

    # QV corruptions
    if tree['qv_entries']:
        lines.append("║   QV CORRUPTIONS DETECTED:")
        for qv in tree['qv_entries'][:3]:
            lines.append(
                f"║     {qv.get('QV_ID', '?')}: {qv.get('CORRUPTION_TYPE', '?')}"
            )

    # LAYER 3: Downstream trace
    s = tree['summary']
    lines.append("║")
    lines.append("║ LAYER 3 — DOWNSTREAM TRACE (DB-documented)")
    lines.append("║ " + "─" * 56)
    lines.append(f"║   Total downstream: {s['total_downstream']}")

    # Names of Allah (highest authority)
    if tree['names_of_allah']:
        lines.append("║   NAMES OF ALLAH:")
        for n in tree['names_of_allah']:
            lines.append(
                f"║     {n.get('name_id', '?')}: "
                f"{att(n.get('aa_name', '?'), n.get('english_name', '?'))}"
            )

    # EN entries
    if tree['entries']['en']:
        lines.append(f"║   EN ({s['en_entries']}):")
        for e in tree['entries']['en'][:5]:
            dp = f" [DP:{e.get('dp_codes', '')}]" if e.get('dp_codes') else ""
            shift = f" ({e.get('shift_ids', '')})" if e.get('shift_ids') else ""
            lines.append(f"║     {e.get('en_term', '?')}{shift}{dp}")

    # European sample
    if tree['european']:
        langs = defaultdict(list)
        for e in tree['european']:
            langs[e.get('lang', '?')].append(e.get('term', '?'))
        lines.append(f"║   EU ({s['european']}):")
        for lang, terms in sorted(langs.items()):
            sample = ', '.join(terms[:3])
            more = f" +{len(terms)-3}" if len(terms) > 3 else ""
            lines.append(f"║     {lang}: {sample}{more}")

    # Bitig
    if tree['bitig']:
        lines.append(f"║   BITIG ({s['bitig']}):")
        for e in tree['bitig'][:3]:
            lines.append(f"║     {e.get('term', '?')}")

    # LAYER 4: Provenance chain
    lines.append("║")
    lines.append("║ LAYER 4 — PROVENANCE")
    lines.append("║ " + "─" * 56)
    lines.append(f"║   28 letters → {root_letters} → {r['quran_tokens']} Qur'anic tokens")
    lines.append(f"║   → {s['total_downstream']} downstream forms across {_count_languages(tree)} languages")
    lines.append(f"║   Direction: Allah's Arabic → downstream. ALWAYS.")

    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


def _count_languages(tree):
    """Count distinct languages in a root tree."""
    count = 0
    if tree['entries']['en']:
        count += 1
    if tree['entries']['ru']:
        count += 1
    if tree['entries']['fa']:
        count += 1
    if tree['bitig']:
        count += 1
    if tree['uzbek']:
        count += 1
    # European languages
    eu_langs = set(e.get('lang', '') for e in tree['european'])
    count += len(eu_langs)
    if tree['latin']:
        count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════
# 13. GENERATE REPORT — intelligence document from one root
# ═══════════════════════════════════════════════════════════════════════

def generate_report(root_id_or_letters, scope='full'):
    """Generate an intelligence-grade report from a single root.

    Scopes:
        'full'      — everything: letters, Qur'an, entries, DP analysis, corridors
        'linguistic' — letters + Qur'an + entries only
        'erasure'   — DP codes + corridors + QV corruptions focus
        'network'   — cross-refs + derivatives + sibling languages

    Args:
        root_id_or_letters: 'R24' or 'ك-ف-ر'
        scope: report scope

    Returns:
        multi-line intelligence report
    """
    if not _HAS_AQL:
        return "عَقْل not available"

    tree = expand_root(root_id_or_letters)
    if 'error' in tree:
        return f"ERROR: {tree['error']}"

    r = tree['root']
    s = tree['summary']
    root_letters = r['root_letters']
    meaning = r['computed_meaning']

    lines = []
    lines.append("═" * 60)
    lines.append(f"INTELLIGENCE REPORT: {r['root_id']} | {att_root(root_letters, r['primary_meaning'])}")
    lines.append(f"SCOPE: {scope.upper()}")
    lines.append(f"GENERATED BY: أَمْر نُطْق (Articulation Engine)")
    lines.append("═" * 60)

    if scope in ('full', 'linguistic'):
        # Section 1: Root analysis
        lines.append("")
        lines.append("1. ROOT ANALYSIS")
        lines.append("─" * 40)
        lines.append(f"   Root: {root_letters} / {meaning['composition']}")
        lines.append(f"   Meaning: {meaning['deduction']}")
        lines.append(f"   Qur'anic tokens: {r['quran_tokens']}")

        # Letter breakdown
        for l_data in meaning['letters']:
            lines.append(f"   {l_data['letter']} = {l_data['abjad']} = {l_data['semantic']}")

        # Section 2: Qur'anic evidence
        lines.append("")
        lines.append("2. QURANIC EVIDENCE")
        lines.append("─" * 40)
        if tree['quranic_words']:
            for w in tree['quranic_words'][:10]:
                tr = w.get('correct_translation', '')
                conf = w.get('confidence', '')
                lines.append(
                    f"   Q{w['surah']}:{w['ayah']}:{w['word_position']} "
                    f"{w.get('aa_word', '?')} — {tr} [{conf}]"
                )
            if len(tree['quranic_words']) > 10:
                lines.append(f"   ... +{len(tree['quranic_words']) - 10} more attestations")
        else:
            lines.append("   No Qur'anic attestations found.")

        # Section 3: Downstream entries
        lines.append("")
        lines.append("3. DOWNSTREAM ENTRIES")
        lines.append("─" * 40)
        for lang, entries in tree['entries'].items():
            if entries:
                lines.append(f"   {lang.upper()} ({len(entries)}):")
                for e in entries:
                    term_key = f'{lang}_term'
                    lines.append(f"     {e.get('entry_id', '?')}: {e.get(term_key, e.get('en_term', '?'))}")

    if scope in ('full', 'erasure'):
        # Section 4: Erasure analysis
        lines.append("")
        lines.append("4. ERASURE ANALYSIS (DP CODES)")
        lines.append("─" * 40)

        dp_found = False
        for lang, entries in tree['entries'].items():
            for e in entries:
                if e.get('dp_codes'):
                    dp_found = True
                    lines.append(f"   {e.get('en_term', '?')}:")
                    lines.append(format_dp(e['dp_codes']))

        if tree['qv_entries']:
            dp_found = True
            lines.append("   QV TRANSLATION CORRUPTIONS:")
            for qv in tree['qv_entries']:
                lines.append(
                    f"     {qv.get('QV_ID', '?')}: {qv.get('CORRUPTION_TYPE', '?')}"
                )
                lines.append(
                    f"       Operator: {qv.get('OPERATOR_TRANSLATION', '?')[:50]}"
                )
                lines.append(
                    f"       Correct:  {qv.get('CORRECT_ROOT_TRANSLATION', '?')[:50]}"
                )

        if not dp_found:
            lines.append("   No DP codes or QV corruptions documented for this root.")

        # Corridors
        corridor_entries = [e for lang in tree['entries'].values()
                           for e in lang if e.get('ds_corridor')]
        if corridor_entries:
            lines.append("")
            lines.append("   CORRIDORS:")
            for e in corridor_entries:
                lines.append(
                    f"     {e.get('en_term', '?')} → {e.get('ds_corridor', '?')} "
                    f"(decay: {e.get('decay_level', '?')})"
                )

    if scope in ('full', 'network'):
        # Section 5: Network analysis
        lines.append("")
        lines.append("5. NETWORK")
        lines.append("─" * 40)
        lines.append(f"   European: {s['european']} entries across {_count_languages(tree)} languages")
        lines.append(f"   Latin Hub: {s['latin']}")
        lines.append(f"   Bitig: {s['bitig']}")
        lines.append(f"   Uzbek: {s['uzbek']}")
        lines.append(f"   Derivatives: {s['derivatives']}")
        lines.append(f"   Cross-refs: {s['cross_refs']}")
        lines.append(f"   Names of Allah: {s['names_of_allah']}")

        if tree['names_of_allah']:
            lines.append("   NAMES OF ALLAH:")
            for n in tree['names_of_allah']:
                lines.append(
                    f"     {att(n.get('aa_name', '?'), n.get('english_name', '?'))}"
                )

        if tree['cross_refs']:
            lines.append("   CROSS-REFERENCES:")
            for cr in tree['cross_refs'][:10]:
                lines.append(
                    f"     {cr.get('from_entry_id', '?')} → {cr.get('to_entry_id', '?')} "
                    f"({cr.get('link_type', '?')})"
                )

    lines.append("")
    lines.append("═" * 60)
    lines.append(f"PROVENANCE: 28 letters → {root_letters} → {r['quran_tokens']} tokens → {s['total_downstream']} downstream")
    lines.append(f"DIRECTION: Allah's Arabic → downstream. ALWAYS.")
    lines.append("═" * 60)
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# 14. PROVENANCE — derivation chain back to 28 letters
# ═══════════════════════════════════════════════════════════════════════

def provenance(word_or_entry, language='en'):
    """Trace any word or entry back to its 28-letter source.

    This is the core function that proves every output derives from
    fixed letter values, not from statistical weights.

    Args:
        word_or_entry: downstream word, entry_id, or root_letters
        language: source language for downstream words

    Returns:
        dict with full provenance chain:
            input → root → letters → abjad → Qur'anic attestation → downstream
    """
    result = {
        'input': word_or_entry,
        'input_type': None,
        'chain': [],
        'root': None,
        'letters': None,
        'quranic_tokens': 0,
        'downstream_count': 0,
        'provenance_text': '',
    }

    # Coerce to string for pattern matching
    word_str = str(word_or_entry)

    # Determine input type
    if isinstance(word_or_entry, int) or word_str.isdigit():
        result['input_type'] = 'entry_id'
        _provenance_from_entry_id(word_str, result)
    elif word_str.startswith('R') or word_str.startswith('T'):
        result['input_type'] = 'root_id'
        _provenance_from_root_id(word_str, result)
    elif '-' in word_str and any(c in word_str for c in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'):
        result['input_type'] = 'root_letters'
        _provenance_from_root_letters(word_str, result)
    elif word_str.startswith('EN') or word_str.startswith('RU') or word_str.startswith('FA'):
        result['input_type'] = 'entry_id'
        _provenance_from_entry_id(word_str, result)
    else:
        result['input_type'] = 'downstream_word'
        _provenance_from_word(word_str, language, result)

    # Generate text
    result['provenance_text'] = _provenance_text(result)
    return result


def _provenance_from_root_id(root_id, result):
    """Fill provenance from root_id."""
    if not _HAS_DB:
        return

    conn = _connect()
    row = conn.execute(
        "SELECT root_id, root_letters, quran_tokens, primary_meaning FROM roots WHERE root_id = ?",
        (root_id,)
    ).fetchone()

    if row:
        root_letters = row['root_letters']
        result['root'] = {'root_id': row['root_id'], 'root_letters': root_letters,
                          'primary_meaning': row['primary_meaning']}
        result['quranic_tokens'] = row['quran_tokens'] or 0

        meaning = deduce_meaning(root_letters) if _HAS_AQL else {}
        result['letters'] = meaning

        # Count downstream
        counts = conn.execute(
            "SELECT count(*) as c FROM entries WHERE root_id = ?", (root_id,)
        ).fetchone()
        eu_counts = conn.execute(
            "SELECT count(*) as c FROM european_a1_entries WHERE root_id = ?", (root_id,)
        ).fetchone()
        result['downstream_count'] = (counts['c'] if counts else 0) + (eu_counts['c'] if eu_counts else 0)

        result['chain'] = [
            f"28 letters (fixed abjad values)",
            f"→ {root_letters} [{meaning.get('abjad_sum', '?')}]",
            f"→ Q attestation: {result['quranic_tokens']} tokens",
            f"→ {result['downstream_count']} downstream entries",
        ]

    conn.close()


def _provenance_from_root_letters(root_letters, result):
    """Fill provenance from root_letters."""
    if not _HAS_DB:
        return

    conn = _connect()
    row = conn.execute(
        "SELECT root_id, quran_tokens, primary_meaning FROM roots WHERE root_letters = ?",
        (root_letters,)
    ).fetchone()

    if row:
        result['root'] = {'root_id': row['root_id'], 'root_letters': root_letters,
                          'primary_meaning': row['primary_meaning']}
        result['quranic_tokens'] = row['quran_tokens'] or 0
        _provenance_from_root_id(row['root_id'], result)
    else:
        meaning = deduce_meaning(root_letters) if _HAS_AQL else {}
        result['letters'] = meaning
        result['chain'] = [
            f"28 letters (fixed abjad values)",
            f"→ {root_letters} [{meaning.get('abjad_sum', '?')}]",
            f"→ NOT IN DB (no Qur'anic attestation found)",
        ]

    conn.close()


def _provenance_from_entry_id(entry_id, result):
    """Fill provenance from entry_id."""
    if not _HAS_DB:
        return

    conn = _connect()
    row = conn.execute(
        "SELECT entry_id, en_term, root_id, phonetic_chain, ds_corridor FROM entries WHERE entry_id = ?",
        (entry_id,)
    ).fetchone()

    if row:
        result['chain'].insert(0, f"Entry: {row['en_term']} ({entry_id})")
        if row['phonetic_chain']:
            result['chain'].insert(1, f"← Shifts: {row['phonetic_chain']}")
        if row['ds_corridor']:
            result['chain'].insert(2, f"← Corridor: {row['ds_corridor']}")
        if row['root_id']:
            _provenance_from_root_id(row['root_id'], result)

    conn.close()


def _provenance_from_word(word, language, result):
    """Fill provenance from a downstream word via hypothesise."""
    if not _HAS_AQL:
        return

    candidates = hypothesise(word, language)
    if candidates:
        top = candidates[0]
        result['chain'].insert(0, f"Word: '{word}' ({language})")
        result['chain'].insert(1, f"← Shift chain: {' | '.join(top['shift_chain'])}")
        if top.get('verified') and top.get('root_id'):
            _provenance_from_root_id(top['root_id'], result)
        else:
            result['root'] = {'root_letters': top['root_letters']}
            result['letters'] = deduce_meaning(top['root_letters'])
            result['chain'].append(f"→ {top['root_letters']} (candidate, score={top['score']})")
    else:
        result['chain'] = [f"Word: '{word}' — no candidates found"]


def _provenance_text(result):
    """Generate human-readable provenance text."""
    lines = []
    lines.append("PROVENANCE CHAIN:")
    for step in result['chain']:
        lines.append(f"  {step}")
    if result.get('root'):
        root = result['root']
        lines.append(f"SOURCE: {root.get('root_letters', '?')} — {root.get('primary_meaning', '?')}")
    lines.append("DIRECTION: Allah's Arabic → downstream. ALWAYS.")
    return '\n'.join(lines)


def format_provenance(prov):
    """Format a provenance dict for display."""
    lines = []
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║ PROVENANCE: {prov['input']} ({prov['input_type']})")
    lines.append("╠" + "═" * 58 + "╣")
    for step in prov['chain']:
        lines.append(f"║   {step}")
    if prov.get('root'):
        r = prov['root']
        lines.append("╠" + "─" * 58 + "╣")
        lines.append(f"║ ROOT: {r.get('root_letters', '?')} — {r.get('primary_meaning', '?')}")
        lines.append(f"║ QURANIC: {prov['quranic_tokens']} tokens")
        lines.append(f"║ DOWNSTREAM: {prov['downstream_count']} entries")
    if prov.get('letters') and isinstance(prov['letters'], dict):
        lines.append(f"║ COMPUTATION: {prov['letters'].get('composition', '?')}")
    lines.append("╠" + "─" * 58 + "╣")
    lines.append("║ DIRECTION: Allah's Arabic → downstream. ALWAYS.")
    lines.append("╚" + "═" * 58 + "╝")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("أَمْر نُطْق — Articulation Engine")
        print()
        print("Usage:")
        print("  python3 amr_nutq.py att كَلِمَة 'word'       # ATT format")
        print("  python3 amr_nutq.py root ك-ف-ر 'to cover'    # root ATT")
        print("  python3 amr_nutq.py entry EN001               # entry card")
        print("  python3 amr_nutq.py report R24                # root report (formatted)")
        print("  python3 amr_nutq.py explain R24               # full traced explanation")
        print("  python3 amr_nutq.py intel R24 [scope]         # intelligence report")
        print("  python3 amr_nutq.py hypo cover                # hypothesis report")
        print("  python3 amr_nutq.py compare ر-ح-م م-ر-ح       # comparison")
        print("  python3 amr_nutq.py prov cover                # provenance chain")
        print("  python3 amr_nutq.py dp 'DP02, DP07'           # DP codes")
        print("  python3 amr_nutq.py summary                   # lattice summary")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'att':
        if len(sys.argv) < 4:
            print("Usage: amr_nutq.py att ARABIC ENGLISH")
            sys.exit(1)
        print(att(sys.argv[2], sys.argv[3]))

    elif cmd == 'root':
        meaning = sys.argv[3] if len(sys.argv) > 3 else None
        print(att_root(sys.argv[2], meaning))

    elif cmd == 'entry':
        print(format_entry_card_from_db(sys.argv[2]))

    elif cmd == 'report':
        if not _HAS_AQL:
            print("ERROR: عَقْل not available")
            sys.exit(1)
        tree = expand_root(sys.argv[2])
        print(format_root_report(tree))

    elif cmd == 'hypo':
        lang = sys.argv[3] if len(sys.argv) > 3 else 'en'
        print(format_hypothesis(sys.argv[2], language=lang))

    elif cmd == 'compare':
        if len(sys.argv) < 4:
            print("Usage: amr_nutq.py compare ROOT_A ROOT_B")
            sys.exit(1)
        print(format_comparison(sys.argv[2], sys.argv[3]))

    elif cmd == 'explain':
        print(explain_root(sys.argv[2]))

    elif cmd == 'intel':
        scope = sys.argv[3] if len(sys.argv) > 3 else 'full'
        print(generate_report(sys.argv[2], scope))

    elif cmd == 'prov':
        lang = sys.argv[3] if len(sys.argv) > 3 else 'en'
        prov = provenance(sys.argv[2], lang)
        print(format_provenance(prov))

    elif cmd == 'dp':
        print(format_dp(sys.argv[2]))

    elif cmd == 'summary':
        print(format_lattice_summary())

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
