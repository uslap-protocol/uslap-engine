#!/usr/bin/env python3
"""
USLaP تَصْرِيف Census — Observe What the Qur'an Actually Does

Analyzes all 77,881 compiled words to discover what letter-addition
patterns the Qur'an uses. ALL data from DB. Zero training weights.

Root ص-ر-ف appears 29 times in the Qur'an (6x as صَرَّفْنَا "We varied/morphed").
This script observes the variations — it does not impose a framework.

Usage:
    python3 uslap_tasrif_census.py              # full census
    python3 uslap_tasrif_census.py --summary     # summary only
"""

import sqlite3
import os
import sys
import re
import unicodedata
from collections import Counter, defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")

# ── Diacritics stripping ──
DIACRITICS = set('\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670\u06DF\u06E0\u06E1\u06E5\u06E6\u06EA\u06EB\u06EC\u06ED')
HAMZA_MAP = str.maketrans('إأآٱءؤئ', 'اااا\u0621وي')
ALEF_NORM = str.maketrans('إأآٱ', 'اااا')


def strip_diacritics(word):
    """Remove all Arabic diacritical marks."""
    return ''.join(c for c in word if c not in DIACRITICS)


def normalize_alef(word):
    """Normalize hamza carriers and alef variants."""
    return word.translate(ALEF_NORM)


def get_consonants(word):
    """Extract consonant skeleton from a Quranic word form (strip diacritics, keep consonants)."""
    bare = strip_diacritics(word)
    bare = normalize_alef(bare)
    # Remove tatweel, special marks
    bare = bare.replace('\u0640', '')  # tatweel
    bare = bare.replace('\u06E4', '')  # small high madda
    bare = ''.join(c for c in bare if '\u0621' <= c <= '\u064A' or c in 'اوي')
    return bare


def get_root_letters(root_hyph):
    """Extract root letters from hyphenated form (e.g., 'ق-و-ل' → 'قول')."""
    if not root_hyph:
        return ''
    return root_hyph.replace('-', '')


def compute_addition(surface, root_letters):
    """
    Given surface consonants and root letters, identify what was ADDED.
    Returns a tuple: (additions_description, positions)

    This is pure observation — what letters appear in the surface form
    that are NOT in the root.
    """
    if not surface or not root_letters:
        return ('UNKNOWN', [])

    # Try to align root letters within surface
    # Find the best alignment: where do the root letters sit in the surface?
    s = surface
    r = root_letters

    # Simple greedy alignment: find each root letter in order
    positions = []
    si = 0
    for ri, rc in enumerate(r):
        found = False
        while si < len(s):
            if s[si] == rc:
                positions.append(si)
                si += 1
                found = True
                break
            # Check hamza variants
            elif rc in 'اأإآ' and s[si] in 'اأإآء':
                positions.append(si)
                si += 1
                found = True
                break
            # Check و/ي weak letters that might appear as ا
            elif rc in 'وي' and s[si] == 'ا':
                positions.append(si)
                si += 1
                found = True
                break
            si += 1
        if not found:
            return ('UNALIGNED', [])

    if len(positions) != len(r):
        return ('UNALIGNED', [])

    # Now identify what's NOT root
    root_positions = set(positions)
    additions = []
    for i, c in enumerate(s):
        if i not in root_positions:
            # Describe position relative to root
            if i < positions[0]:
                additions.append(('PRE', c, i))
            elif len(positions) > 1 and positions[0] < i < positions[1]:
                additions.append(('MID1', c, i))
            elif len(positions) > 2 and positions[1] < i < positions[2]:
                additions.append(('MID2', c, i))
            elif i > positions[-1]:
                additions.append(('POST', c, i))
            else:
                additions.append(('INNER', c, i))

    return (additions, positions)


def classify_pattern(additions, surface, root_letters):
    """
    Classify the letter-addition pattern into a descriptive code.
    Based ONLY on what letters are added and where.
    """
    if not additions:
        return 'BASE'  # No additions detected

    if additions == 'UNKNOWN' or additions == 'UNALIGNED':
        return additions

    # Build a signature from the additions
    added_letters = ''.join(a[1] for a in additions)
    positions = [a[0] for a in additions]

    # Common patterns — described by what the letters DO

    # Prefix patterns
    if len(additions) == 1:
        pos, letter, _ = additions[0]
        if pos == 'PRE':
            if letter == 'ت': return 'T_PREFIX'
            if letter == 'ن': return 'N_PREFIX'
            if letter == 'ي': return 'Y_PREFIX'
            if letter == 'ا': return 'A_PREFIX'
            if letter == 'م': return 'M_PREFIX'
            return f'{letter}_PREFIX'
        if pos == 'MID1':
            if letter == 'ت': return 'T_INFIX'
            if letter == 'ا': return 'A_EXTEND'
            if letter == 'و': return 'W_EXTEND'
            if letter == 'ي': return 'Y_EXTEND'
            return f'{letter}_INFIX'
        if pos == 'POST':
            return f'{letter}_SUFFIX'
        if pos == 'MID2':
            return f'{letter}_MID2'

    if len(additions) == 2:
        p1, l1, _ = additions[0]
        p2, l2, _ = additions[1]
        sig = f"{p1}:{l1}+{p2}:{l2}"

        # ت prefix + ا extension = تَفَاعَل pattern
        if p1 == 'PRE' and l1 == 'ت' and p2 == 'MID1' and l2 == 'ا':
            return 'T_PREFIX_A'
        # ت prefix + doubled middle (shadda)
        if p1 == 'PRE' and l1 == 'ت' and p2 == 'MID1':
            return 'T_PREFIX_DD'
        # ا + ن prefix = انفعل
        if p1 == 'PRE' and l1 == 'ا' and p2 == 'PRE' and l2 == 'ن':
            return 'AN_PREFIX'
        if p1 == 'PRE' and l1 == 'ن' and p2 == 'PRE':
            return 'N_PREFIX_PLUS'
        # ا prefix + ت infix = افتعل
        if p1 == 'PRE' and l1 == 'ا' and p2 == 'MID1' and l2 == 'ت':
            return 'A_T_INFIX'
        # م prefix + something
        if p1 == 'PRE' and l1 == 'م':
            return f'M_PREFIX_{l2}'

        return f'ADD2:{sig}'

    if len(additions) == 3:
        letters = ''.join(a[1] for a in additions)
        poss = [a[0] for a in additions]

        # است prefix = استفعل
        if letters == 'است' or (poss[0] == 'PRE' and poss[1] == 'PRE' and poss[2] == 'MID1'):
            return 'ST_PREFIX'

        return f'ADD3:{letters}'

    if len(additions) >= 4:
        letters = ''.join(a[1] for a in additions)
        return f'ADD{len(additions)}:{letters}'

    return 'OTHER'


def run_census(conn, summary_only=False):
    """Run the full census on all compiled words."""

    # Get all rooted words
    rows = conn.execute('''
        SELECT aa_word, root, word_type
        FROM quran_word_roots
        WHERE root IS NOT NULL
    ''').fetchall()

    print(f"تَصْرِيف CENSUS — {len(rows)} rooted words")
    print("=" * 60)

    pattern_counts = Counter()
    pattern_examples = defaultdict(list)
    pattern_roots = defaultdict(set)
    unaligned = 0
    total = 0

    for word, root_hyph, wtype in rows:
        surface = get_consonants(word)
        root_letters = get_root_letters(root_hyph)

        if not surface or not root_letters:
            continue

        total += 1
        additions, positions = compute_addition(surface, root_letters)

        if additions in ('UNKNOWN', 'UNALIGNED'):
            unaligned += 1
            continue

        pattern = classify_pattern(additions, surface, root_letters)
        pattern_counts[pattern] += 1
        pattern_roots[pattern].add(root_hyph)

        if len(pattern_examples[pattern]) < 5:
            pattern_examples[pattern].append((word, root_hyph, surface))

    # Report
    print(f"\nTotal analysed: {total}")
    print(f"Aligned: {total - unaligned} ({(total-unaligned)*100/total:.1f}%)")
    print(f"Unaligned: {unaligned} ({unaligned*100/total:.1f}%)")

    print(f"\n{'PATTERN':<20} {'TOKENS':>8} {'ROOTS':>8} {'DESCRIPTION'}")
    print("-" * 65)

    for pattern, count in pattern_counts.most_common():
        roots_n = len(pattern_roots[pattern])
        print(f"{pattern:<20} {count:>8} {roots_n:>8}")

        if not summary_only:
            for word, root, surface in pattern_examples[pattern][:3]:
                print(f"  {word} ({root}) [{surface}]")

    return pattern_counts, pattern_examples, pattern_roots


def main():
    summary = '--summary' in sys.argv
    conn = sqlite3.connect(DB_PATH)

    counts, examples, roots = run_census(conn, summary_only=summary)

    conn.close()


if __name__ == '__main__':
    main()
