#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر بِيتِيك تَصْرِيف — BI MORPHOLOGICAL ENGINE

Phase 0 of the BI track. Mirror of amr_tasrif.py (AA track).

BI تَصْرِيف works by AGGLUTINATION — suffixes stack on a root:
  kor (see) + -gan (participle) + -lar (plural) = qorganlar

Three layers of BI تَصْرِيف:
  Layer 1 — VERB PATTERNS: 8 suffix types (bitig_verb_tasrif)
  Layer 2 — NOUN PATTERNS: 6 suffix types (bitig_noun_tasrif)
  Layer 3 — CASE: 6 case suffixes (bitig_case_tasrif)
  Layer 4 — GRAMMAR: 10 patterns — possessive, voice, negation, question,
            vowel harmony (bitig_grammar_tasrif)
  Layer 5 — COMPOUND: 8 compound formation rules (bitig_compound_rules)

Every suffix checked against Kashgari (1072 CE) headword frequency.
Vowel harmony (BG10) is the structural law — violation = contamination signal.

Usage:
    python3 amr_bitig_tasrif.py status                    # coverage stats
    python3 amr_bitig_tasrif.py analyze "qorganlar"       # decompose word
    python3 amr_bitig_tasrif.py root "kor"                # all forms of root
    python3 amr_bitig_tasrif.py pattern BV01              # explain pattern
    python3 amr_bitig_tasrif.py harmony "qorganlar"       # check vowel harmony
    python3 amr_bitig_tasrif.py compound "qara tas"       # analyze compound
"""

import sys
import os
import sqlite3
import re

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

# ═══════════════════════════════════════════════════════════════════════
# BI PHONOLOGY CONSTANTS — sourced from amr_bitig_alphabet if available
# ═══════════════════════════════════════════════════════════════════════

try:
    from amr_bitig_alphabet import HARMONY_PAIRS, HARMONY_NEUTRAL
    _HAS_BITIG_ALPHABET = True
except ImportError:
    _HAS_BITIG_ALPHABET = False

BACK_VOWELS = set('aıou')
FRONT_VOWELS = set('eiöü')
ALL_VOWELS = BACK_VOWELS | FRONT_VOWELS

# Vowel harmony pairing: back ↔ front
HARMONY_MAP = {
    'a': 'e', 'e': 'a',
    'ı': 'i', 'i': 'ı',
    'o': 'ö', 'ö': 'o',
    'u': 'ü', 'ü': 'u',
}


def _connect(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════
# LAYER 0: VOWEL HARMONY
# ═══════════════════════════════════════════════════════════════════════

def get_root_harmony(word):
    """Determine vowel harmony class of a word from its vowels.
    Returns 'BACK', 'FRONT', 'MIXED' (contamination signal), or 'NONE'.
    """
    word_lower = word.lower()
    has_back = any(v in word_lower for v in BACK_VOWELS)
    has_front = any(v in word_lower for v in FRONT_VOWELS)

    if has_back and has_front:
        return 'MIXED'  # violation — contamination signal
    elif has_back:
        return 'BACK'
    elif has_front:
        return 'FRONT'
    return 'NONE'


def check_harmony(word):
    """Full vowel harmony check.
    Returns (harmony_class, is_valid, violations).
    """
    harmony = get_root_harmony(word)
    violations = []

    if harmony == 'MIXED':
        # Find which vowels conflict
        word_lower = word.lower()
        backs = [v for v in word_lower if v in BACK_VOWELS]
        fronts = [v for v in word_lower if v in FRONT_VOWELS]
        violations.append(
            f'MIXED HARMONY: back vowels {backs} and front vowels {fronts} '
            f'in same word. BI words obey vowel harmony (BG10). '
            f'Violation = contamination signal.'
        )

    return (harmony, len(violations) == 0, violations)


# ═══════════════════════════════════════════════════════════════════════
# LAYER 1-4: SUFFIX DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════

def _load_all_suffixes(conn):
    """Load all suffixes from all 4 tasrif tables.
    Returns list of (suffix, code, table, category, function) sorted by length desc.
    """
    suffixes = []
    tables = [
        ('bitig_verb_tasrif', 'code', 'suffix_or_affix', 'function', 'VERB'),
        ('bitig_noun_tasrif', 'code', 'suffix_or_affix', 'function', 'NOUN'),
        ('bitig_case_tasrif', 'code', 'suffix_or_affix', 'case_name', 'CASE'),
        ('bitig_grammar_tasrif', 'code', 'suffix_or_affix', 'category', 'GRAMMAR'),
    ]
    for table, code_col, suffix_col, func_col, category in tables:
        try:
            rows = conn.execute(
                f'SELECT {code_col}, {suffix_col}, {func_col} FROM {table}'
            ).fetchall()
            for row in rows:
                raw = row[1] or ''
                func = row[2] or ''
                if 'VOWEL_HARMONY' in raw:
                    continue  # BG10 is a rule, not a suffix
                # Split on / to get all variants
                for variant in raw.replace(',', '/').split('/'):
                    v = variant.strip().lstrip('-')
                    if v and len(v) >= 2:
                        suffixes.append((v, row[0], table, category, func))
        except sqlite3.OperationalError:
            pass

    # Sort by suffix length descending (greedy matching)
    suffixes.sort(key=lambda x: len(x[0]), reverse=True)
    return suffixes


def decompose_suffixes(word, conn=None):
    """Decompose a word by stripping BI suffixes layer by layer.
    Returns list of layers:
      [(remaining_stem, stripped_suffix, code, table, category, function), ...]
    """
    close_conn = False
    if conn is None:
        conn = _connect()
        close_conn = True

    all_suffixes = _load_all_suffixes(conn)
    word_lower = word.lower()
    layers = []
    current = word_lower

    for _ in range(5):  # max 5 suffix layers (BI can stack deep)
        found = False
        for suffix, code, table, category, func in all_suffixes:
            if current.endswith(suffix) and len(current) > len(suffix) + 1:
                stem = current[:-len(suffix)]
                layers.append((stem, suffix, code, table, category, func))
                current = stem
                found = True
                break
        if not found:
            break

    if close_conn:
        conn.close()

    return layers


def analyze_word(word):
    """Full morphological analysis of a BI word.
    Returns dict with harmony, suffix layers, root candidates, bitig matches.
    """
    conn = _connect()

    # Vowel harmony
    harmony, harmony_valid, harmony_violations = check_harmony(word)

    # Suffix decomposition
    layers = decompose_suffixes(word, conn)

    # Get all candidate stems (original + each stripped layer)
    stems = [word.lower()]
    for stem, *_ in layers:
        if stem not in stems:
            stems.append(stem)

    # Search bitig_a1 for each candidate stem
    bitig_matches = []
    for stem in stems:
        row = conn.execute(
            'SELECT entry_id, orig2_term, root_letters, kashgari_attestation, '
            'semantic_field FROM bitig_a1_entries '
            'WHERE LOWER(orig2_term) = ? LIMIT 1',
            (stem,)
        ).fetchone()
        if row:
            bitig_matches.append({
                'entry_id': row['entry_id'],
                'orig2_term': row['orig2_term'],
                'root_letters': row['root_letters'],
                'kashgari': row['kashgari_attestation'],
                'semantic_field': row['semantic_field'],
                'matched_stem': stem,
            })

    conn.close()

    return {
        'input': word,
        'harmony': harmony,
        'harmony_valid': harmony_valid,
        'harmony_violations': harmony_violations,
        'suffix_layers': [
            {
                'stem': stem,
                'suffix': f'-{suffix}',
                'code': code,
                'category': cat,
                'function': func,
            }
            for stem, suffix, code, table, cat, func in layers
        ],
        'root_stem': layers[-1][0] if layers else word.lower(),
        'bitig_matches': bitig_matches,
    }


# ═══════════════════════════════════════════════════════════════════════
# LAYER 5: COMPOUND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def analyze_compound(compound_text):
    """Analyze a compound word (space-separated or + separated).
    Checks each component against bitig_a1 and compound_rules.
    """
    conn = _connect()

    # Split on space or +
    parts = re.split(r'[\s+]+', compound_text.strip())

    components = []
    for part in parts:
        part_lower = part.lower()
        # Search bitig_a1
        row = conn.execute(
            'SELECT entry_id, orig2_term, root_letters, semantic_field '
            'FROM bitig_a1_entries WHERE LOWER(orig2_term) = ? LIMIT 1',
            (part_lower,)
        ).fetchone()

        # Also decompose
        layers = decompose_suffixes(part, conn)

        components.append({
            'form': part,
            'bitig_match': dict(row) if row else None,
            'suffix_layers': [
                {'stem': s, 'suffix': f'-{sx}', 'code': c, 'category': cat}
                for s, sx, c, _, cat, _ in layers
            ],
        })

    # Match against compound rules
    rules = conn.execute('SELECT code, pattern, function, description FROM bitig_compound_rules').fetchall()
    matched_rules = []
    for rule in rules:
        matched_rules.append({
            'code': rule['code'],
            'pattern': rule['pattern'],
            'function': rule['function'],
        })

    conn.close()

    return {
        'input': compound_text,
        'components': components,
        'available_rules': matched_rules,
    }


# ═══════════════════════════════════════════════════════════════════════
# ROOT EXPANSION
# ═══════════════════════════════════════════════════════════════════════

def get_root_forms(root_letters):
    """Get all bitig_a1 entries with matching root_letters."""
    conn = _connect()
    rows = conn.execute(
        'SELECT entry_id, orig2_term, root_letters, kashgari_attestation, '
        'semantic_field, status FROM bitig_a1_entries '
        'WHERE root_letters = ? OR root_letters LIKE ?',
        (root_letters, f'%{root_letters}%')
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════
# PATTERN INFO
# ═══════════════════════════════════════════════════════════════════════

def get_pattern_info(code):
    """Get full info for a tasrif pattern code (BV01, BN01, BC01, BG01, COMP01)."""
    conn = _connect()
    tables = {
        'BV': 'bitig_verb_tasrif',
        'BN': 'bitig_noun_tasrif',
        'BC': 'bitig_case_tasrif',
        'BG': 'bitig_grammar_tasrif',
        'CO': 'bitig_compound_rules',
    }
    prefix = code[:2]
    table = tables.get(prefix)
    if not table:
        conn.close()
        return None

    row = conn.execute(f'SELECT * FROM {table} WHERE code = ?', (code,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════

def get_status():
    """Coverage stats across all BI tasrif tables."""
    conn = _connect()
    stats = {}
    tables = [
        ('bitig_verb_tasrif', 'Verb patterns'),
        ('bitig_noun_tasrif', 'Noun patterns'),
        ('bitig_case_tasrif', 'Case suffixes'),
        ('bitig_grammar_tasrif', 'Grammar patterns'),
        ('bitig_compound_rules', 'Compound rules'),
        ('bitig_phonology', 'Phonemes'),
    ]
    for table, label in tables:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            stats[label] = count
        except sqlite3.OperationalError:
            stats[label] = 0

    # Bitig entries total
    stats['bitig_a1 entries'] = conn.execute(
        'SELECT COUNT(*) FROM bitig_a1_entries'
    ).fetchone()[0]

    conn.close()
    return stats


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  amr_bitig_tasrif.py status")
        print("  amr_bitig_tasrif.py analyze <word>")
        print("  amr_bitig_tasrif.py root <root_letters>")
        print("  amr_bitig_tasrif.py pattern <code>")
        print("  amr_bitig_tasrif.py harmony <word>")
        print("  amr_bitig_tasrif.py compound <compound>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'status':
        stats = get_status()
        print("╔══════════════════════════════════════════╗")
        print("║  BI TASRIF — بِيتِيك تَصْرِيف          ║")
        print("╠══════════════════════════════════════════╣")
        for label, count in stats.items():
            print(f"║  {label:25} {count:>6}       ║")
        total = sum(v for k, v in stats.items() if k != 'bitig_a1 entries')
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  TOTAL PATTERNS           {total:>6}       ║")
        print(f"║  BITIG ENTRIES            {stats.get('bitig_a1 entries', 0):>6}       ║")
        print(f"╚══════════════════════════════════════════╝")

    elif cmd == 'analyze' and len(sys.argv) > 2:
        word = sys.argv[2]
        result = analyze_word(word)
        print(f"Input: {result['input']}")
        print(f"Harmony: {result['harmony']} ({'VALID' if result['harmony_valid'] else 'VIOLATION'})")
        if result['harmony_violations']:
            for v in result['harmony_violations']:
                print(f"  ⛔ {v}")
        print(f"Root stem: {result['root_stem']}")
        if result['suffix_layers']:
            print(f"Suffix layers ({len(result['suffix_layers'])}):")
            for layer in result['suffix_layers']:
                print(f"  {layer['suffix']:8} {layer['code']:6} {layer['category']:8} {layer['function'][:50]}")
        if result['bitig_matches']:
            print(f"Bitig matches:")
            for m in result['bitig_matches']:
                print(f"  {m['entry_id']}|{m['orig2_term']}|{m['root_letters']}|{m['semantic_field']}")
        else:
            print("Bitig matches: NONE")

    elif cmd == 'root' and len(sys.argv) > 2:
        root = sys.argv[2]
        forms = get_root_forms(root)
        print(f"Root: {root} — {len(forms)} entries")
        for f in forms[:20]:
            print(f"  {f['entry_id']}|{f['orig2_term']}|{f['root_letters']}|{f.get('semantic_field', '')}")

    elif cmd == 'pattern' and len(sys.argv) > 2:
        code = sys.argv[2]
        info = get_pattern_info(code)
        if info:
            for k, v in info.items():
                if v is not None:
                    print(f"  {k}: {v}")
        else:
            print(f"Pattern {code} not found.")

    elif cmd == 'harmony' and len(sys.argv) > 2:
        word = sys.argv[2]
        harmony, valid, violations = check_harmony(word)
        print(f"Word: {word}")
        print(f"Harmony: {harmony} ({'VALID' if valid else 'VIOLATION'})")
        for v in violations:
            print(f"  ⛔ {v}")

    elif cmd == 'compound' and len(sys.argv) > 2:
        compound = ' '.join(sys.argv[2:])
        result = analyze_compound(compound)
        print(f"Compound: {result['input']}")
        for comp in result['components']:
            match_str = f"bitig {comp['bitig_match']['entry_id']}" if comp['bitig_match'] else 'NOT IN BITIG'
            print(f"  {comp['form']}: {match_str}")
            for layer in comp['suffix_layers']:
                print(f"    {layer['suffix']} ({layer['code']}/{layer['category']})")


if __name__ == '__main__':
    main()
