#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر تَصْرِيف — MORPHOLOGICAL ENGINE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root ص-ر-ف = HEAVY(ص) + MOVEMENT(ر) + SEPARATION(ف)
= to turn something heavy from one direction to another.
Q2:164 وَتَصْرِيفِ — the turning/directing of winds.

Three layers of تَصْرِيف:
  Layer 1 — CONSONANT STRUCTURE: what letters are added to the root
            Tables: verb_tasrif_patterns (8 codes), noun_tasrif_patterns (12 codes)
  Layer 2 — VOWEL PATTERN: what vowels sit on the root letters
            Table: noun_tasrif_vowels (17 codes, 5 broken plural patterns)
  Layer 3 — GRAMMAR: external markers (tense, person, number, gender, case, definiteness)
            Tables: verb_tasrif_grammar (11 defs), noun_tasrif_grammar (11 defs)

Every output traces to 28 letters and 77,877 Qur'anic tokens.
No statistical weights. No training data. No hallucination.

Usage:
    python3 amr_tasrif.py analyze "كِتَابٌ"              # full analysis
    python3 amr_tasrif.py root "ك-ت-ب"                   # all forms of root
    python3 amr_tasrif.py status                          # coverage stats
    python3 amr_tasrif.py broken_plurals                  # list broken plurals
    python3 amr_tasrif.py pattern FA3IIL                  # explain pattern
"""

import sys
import os
import sqlite3
from collections import defaultdict, Counter

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

# ═══════════════════════════════════════════════════════════════════════
# TASHKEEL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

FATHA = '\u064E'
KASRA = '\u0650'
DAMMA = '\u064F'
SUKUN = '\u0652'
SHADDA = '\u0651'
TANWIN_F = '\u064B'
TANWIN_K = '\u064D'
TANWIN_D = '\u064C'
TASHKEEL = set([FATHA, KASRA, DAMMA, SUKUN, SHADDA, TANWIN_F, TANWIN_K, TANWIN_D, '\u0670'])

ALEF_MAP = {
    'ا': 'أإآٱء', 'أ': 'اإآٱء', 'إ': 'اأآٱء',
    'ه': 'ة', 'ة': 'ه', 'ي': 'ىئ', 'ى': 'يئ',
    'و': 'ؤ', 'ؤ': 'وء', 'ئ': 'يى'
}


def is_consonant(ch):
    return ord(ch) >= 0x0620 and ch not in TASHKEEL and ord(ch) != 0x0670


def strip_tashkeel(text):
    if not text:
        return ''
    return ''.join(ch for ch in text if ch not in TASHKEEL)


def get_vowel_after(word, pos):
    """Get the vowel mark following consonant at position pos."""
    for j in range(pos + 1, min(pos + 4, len(word))):
        ch = word[j]
        if ch == SHADDA:
            continue
        if ch == FATHA or ch == TANWIN_F:
            return 'a'
        if ch == KASRA or ch == TANWIN_K:
            return 'i'
        if ch == DAMMA or ch == TANWIN_D:
            return 'u'
        if ch == SUKUN:
            return '0'
        if is_consonant(ch):
            return '0'
    return '0'


def root_letters(root):
    return [l for l in root.split('-') if l]


# ═══════════════════════════════════════════════════════════════════════
# DATABASE QUERIES
# ═══════════════════════════════════════════════════════════════════════

def _connect():
    return sqlite3.connect(DB_PATH)


def get_status():
    """Return coverage statistics for the tasrif system."""
    conn = _connect()
    c = conn.cursor()

    stats = {}

    # Verb structural
    c.execute('SELECT COUNT(*) FROM verb_tasrif_patterns')
    stats['verb_consonant_codes'] = c.fetchone()[0]
    c.execute('SELECT SUM(quran_tokens) FROM verb_tasrif_patterns')
    stats['verb_consonant_tokens'] = c.fetchone()[0] or 0

    # Noun structural
    c.execute('SELECT COUNT(*) FROM noun_tasrif_patterns')
    stats['noun_consonant_codes'] = c.fetchone()[0]
    c.execute('SELECT SUM(quran_tokens) FROM noun_tasrif_patterns')
    stats['noun_consonant_tokens'] = c.fetchone()[0] or 0

    # Vowel patterns
    c.execute('SELECT COUNT(*) FROM noun_tasrif_vowels')
    stats['vowel_codes'] = c.fetchone()[0]
    c.execute('SELECT SUM(quran_tokens) FROM noun_tasrif_vowels')
    stats['vowel_tokens'] = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM noun_tasrif_vowels WHERE number_function = 'BROKEN_PLURAL'")
    stats['broken_plural_codes'] = c.fetchone()[0]

    # Grammar
    c.execute('SELECT COUNT(*) FROM verb_tasrif_grammar')
    stats['verb_grammar_defs'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM noun_tasrif_grammar')
    stats['noun_grammar_defs'] = c.fetchone()[0]

    # Token coverage
    c.execute('SELECT COUNT(*) FROM quran_word_roots')
    stats['total_tokens'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM quran_word_roots WHERE verb_form IS NOT NULL')
    stats['verb_struct_coded'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM quran_word_roots WHERE noun_tasrif_code IS NOT NULL')
    stats['noun_struct_coded'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM quran_word_roots WHERE noun_vowel_code IS NOT NULL')
    stats['vowel_coded'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM quran_word_roots WHERE gram_tense IS NOT NULL')
    stats['verb_gram_coded'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM quran_word_roots WHERE gram_definiteness IS NOT NULL')
    stats['noun_gram_coded'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM quran_word_roots WHERE gram_number = 'PLURAL_BROKEN'")
    stats['broken_plural_tokens'] = c.fetchone()[0]

    conn.close()
    return stats


def get_root_forms(root_hyph):
    """Get all Qur'anic forms of a root with their tasrif analysis."""
    conn = _connect()
    c = conn.cursor()

    c.execute('''SELECT aa_word, word_type, verb_form, noun_tasrif_code, noun_vowel_code,
                        gram_tense, gram_person, gram_number, gram_gender,
                        gram_case, gram_definiteness, surah, ayah
                 FROM quran_word_roots
                 WHERE root = ?
                 ORDER BY surah, ayah''', (root_hyph,))

    forms = []
    for row in c.fetchall():
        forms.append({
            'word': row[0],
            'word_type': row[1],
            'verb_structure': row[2],
            'noun_structure': row[3],
            'vowel_pattern': row[4],
            'tense': row[5],
            'person': row[6],
            'number': row[7],
            'gender': row[8],
            'case': row[9],
            'definiteness': row[10],
            'ref': f'Q{row[11]}:{row[12]}'
        })

    conn.close()
    return forms


def get_pattern_info(code):
    """Get detailed info about a tasrif pattern code."""
    conn = _connect()
    c = conn.cursor()

    # Check all tables
    for table in ['verb_tasrif_patterns', 'noun_tasrif_patterns', 'noun_tasrif_vowels']:
        try:
            if table == 'noun_tasrif_vowels':
                c.execute(f'SELECT * FROM {table} WHERE vowel_code = ?', (code,))
            else:
                c.execute(f'SELECT * FROM {table} WHERE code = ?', (code,))
            row = c.fetchone()
            if row:
                cols = [d[0] for d in c.description]
                conn.close()
                return dict(zip(cols, row)), table
        except Exception:
            pass

    conn.close()
    return None, None


def get_broken_plurals():
    """List all broken plural tokens with their singular counterparts."""
    conn = _connect()
    c = conn.cursor()

    c.execute('''SELECT aa_word, root, noun_vowel_code, surah, ayah
                 FROM quran_word_roots
                 WHERE gram_number = 'PLURAL_BROKEN'
                 ORDER BY root, surah, ayah''')

    results = defaultdict(list)
    for word, root, vcode, surah, ayah in c.fetchall():
        results[root].append({
            'word': word,
            'vowel_code': vcode,
            'ref': f'Q{surah}:{ayah}'
        })

    conn.close()
    return results


def analyze_word(aa_word, root_hyph):
    """Full tasrif analysis of a single word given its root."""
    conn = _connect()
    c = conn.cursor()

    c.execute('''SELECT word_type, verb_form, noun_tasrif_code, noun_vowel_code,
                        gram_tense, gram_person, gram_number, gram_gender,
                        gram_case, gram_definiteness, surah, ayah
                 FROM quran_word_roots
                 WHERE aa_word = ? AND root = ?
                 LIMIT 1''', (aa_word, root_hyph))

    row = c.fetchone()
    if not row:
        # Try stripped match
        c.execute('''SELECT word_type, verb_form, noun_tasrif_code, noun_vowel_code,
                            gram_tense, gram_person, gram_number, gram_gender,
                            gram_case, gram_definiteness, surah, ayah
                     FROM quran_word_roots
                     WHERE root = ? AND aa_word LIKE ?
                     LIMIT 1''', (root_hyph, f'%{strip_tashkeel(aa_word)}%'))
        row = c.fetchone()

    if not row:
        conn.close()
        return None

    analysis = {
        'word': aa_word,
        'root': root_hyph,
        'word_type': row[0],
        'layer1_consonant': row[1] if row[0] == 'VERB' else row[2],
        'layer2_vowel': row[3],
        'layer3_grammar': {
            'tense': row[4],
            'person': row[5],
            'number': row[6],
            'gender': row[7],
            'case': row[8],
            'definiteness': row[9],
        },
        'ref': f'Q{row[10]}:{row[11]}'
    }

    # Get pattern descriptions
    if analysis['layer1_consonant']:
        info, table = get_pattern_info(analysis['layer1_consonant'])
        if info:
            analysis['layer1_description'] = info.get('structural_description', '')

    if analysis['layer2_vowel']:
        info, table = get_pattern_info(analysis['layer2_vowel'])
        if info:
            analysis['layer2_description'] = info.get('structural_description', '')
            analysis['number_function'] = info.get('number_function', '')

    conn.close()
    return analysis


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════

def print_status():
    stats = get_status()
    print("=" * 60)
    print("تَصْرِيف STATUS — Three-Layer Morphological Engine")
    print("=" * 60)
    print()
    print("LAYER 1 — CONSONANT STRUCTURE (what letters added to root)")
    print(f"  verb_tasrif_patterns:  {stats['verb_consonant_codes']:3d} codes, {stats['verb_consonant_tokens']:,d} defined tokens")
    print(f"  noun_tasrif_patterns:  {stats['noun_consonant_codes']:3d} codes, {stats['noun_consonant_tokens']:,d} defined tokens")
    print(f"  Tokens coded:          VERB {stats['verb_struct_coded']:,d} | NOUN {stats['noun_struct_coded']:,d}")
    print()
    print("LAYER 2 — VOWEL PATTERN (what vowels on root letters)")
    print(f"  noun_tasrif_vowels:    {stats['vowel_codes']:3d} codes ({stats['broken_plural_codes']} broken plural)")
    print(f"  Tokens coded:          {stats['vowel_coded']:,d}")
    print(f"  Broken plural tokens:  {stats['broken_plural_tokens']:,d}")
    print()
    print("LAYER 3 — GRAMMAR (external markers)")
    print(f"  verb_tasrif_grammar:   {stats['verb_grammar_defs']:3d} definitions")
    print(f"  noun_tasrif_grammar:   {stats['noun_grammar_defs']:3d} definitions")
    print(f"  Tokens coded:          VERB {stats['verb_gram_coded']:,d} | NOUN {stats['noun_gram_coded']:,d}")
    print()
    print(f"TOTAL TOKENS: {stats['total_tokens']:,d}")
    total_coded = stats['verb_struct_coded'] + stats['noun_struct_coded']
    print(f"STRUCTURAL COVERAGE: {total_coded:,d} ({total_coded / stats['total_tokens'] * 100:.1f}%)")


def print_root_forms(root_hyph):
    forms = get_root_forms(root_hyph)
    if not forms:
        print(f"No tokens found for root {root_hyph}")
        return

    print(f"ROOT {root_hyph} — {len(forms)} tokens")
    print("=" * 80)

    # Group by unique form
    seen = {}
    for f in forms:
        key = f['word']
        if key not in seen:
            seen[key] = f
            seen[key]['count'] = 1
            seen[key]['refs'] = [f['ref']]
        else:
            seen[key]['count'] += 1
            if len(seen[key]['refs']) < 3:
                seen[key]['refs'].append(f['ref'])

    for word, f in seen.items():
        struct = f['verb_structure'] or f['noun_structure'] or '-'
        vowel = f['vowel_pattern'] or '-'
        gram_parts = []
        if f['tense']:
            gram_parts.append(f['tense'])
        if f['number']:
            gram_parts.append(f['number'])
        if f['definiteness']:
            gram_parts.append(f['definiteness'])
        gram = '/'.join(gram_parts) if gram_parts else '-'

        refs = ', '.join(f['refs'][:3])
        if f['count'] > 3:
            refs += f" (+{f['count'] - 3})"

        print(f"  {word:25s}  L1={struct:20s}  L2={vowel:10s}  L3={gram:30s}  {refs}")


def print_broken_plurals():
    bp = get_broken_plurals()
    if not bp:
        print("No broken plurals found.")
        return

    total = sum(len(v) for v in bp.values())
    print(f"BROKEN PLURALS — {len(bp)} roots, {total} tokens")
    print("=" * 60)

    for root, forms in sorted(bp.items()):
        codes = set(f['vowel_code'] for f in forms if f['vowel_code'])
        refs = [f['ref'] for f in forms[:3]]
        words = set(strip_tashkeel(f['word']) for f in forms)
        print(f"  {root:10s}  {', '.join(codes):12s}  {len(forms):3d}x  {', '.join(list(words)[:3])}")


def print_pattern(code):
    info, table = get_pattern_info(code)
    if not info:
        print(f"Pattern '{code}' not found in any tasrif table.")
        return

    print(f"PATTERN: {code}")
    print(f"TABLE: {table}")
    print("-" * 50)
    for k, v in info.items():
        if v is not None:
            print(f"  {k}: {v}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 amr_tasrif.py status")
        print("  python3 amr_tasrif.py root <root>")
        print("  python3 amr_tasrif.py broken_plurals")
        print("  python3 amr_tasrif.py pattern <code>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'status':
        print_status()
    elif cmd == 'root' and len(sys.argv) >= 3:
        print_root_forms(sys.argv[2])
    elif cmd == 'broken_plurals':
        print_broken_plurals()
    elif cmd == 'pattern' and len(sys.argv) >= 3:
        print_pattern(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
