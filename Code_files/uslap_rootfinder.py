#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP ROOTFINDER — Automatic Root Assignment Pipeline

Input: a word (RU/EN/any downstream)
Output: root_id, root_letters, corridor, phonetic_chain, QUF stamp

Pipeline:
1. Extract consonant skeleton from downstream word
2. Run against shift_lookup (S01-S26) for ALL possible AA root candidates
3. Run against bi_shift_lookup (B01-B25) for ORIG2 candidates
4. Check each candidate against quran_word_roots (Qur'anic attestation)
5. Check each candidate against bitig_a1_entries (Kashgari attestation)
6. Check each candidate against existing roots table
7. Score candidates: Qur'anic attested > Kashgari attested > new root
8. Assign best candidate, build chain, classify corridor

"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
import os
import re
from itertools import product

DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

# RU consonant extraction (strip vowels and soft/hard signs)
RU_VOWELS = set('аеёиоуыэюяАЕЁИОУЫЭЮЯьъЬЪ')
RU_PREFIXES = ['ПЕРЕ', 'РАССМ', 'РАСС', 'РАС', 'РАЗ', 'ПРО', 'ПРИ', 'ПРЕ', 'ПОД', 'ПОЛ',
               'НАД', 'ВОС', 'ВОЗ', 'ВЫ', 'ДО', 'ЗА', 'ИЗ', 'НА', 'ОБ', 'ОТ', 'ПО', 'С', 'У']

# RU consonant -> possible AA sources (reverse of shift_lookup but for Cyrillic)
RU_TO_AA = {
    'к': [('ق', 'S01'), ('خ', 'S11'), ('ك', 'S20')],
    'г': [('ق', 'S01'), ('ج', 'S02'), ('غ', 'S14'), ('ك', 'S20')],
    'х': [('ح', 'S03'), ('خ', 'S11'), ('ه', 'S23')],
    'т': [('ط', 'S04'), ('د', 'S19'), ('ت', 'S24')],
    'ш': [('ش', 'S05')],
    'щ': [('ش', 'S05')],
    'с': [('ش', 'S05'), ('ص', 'S13'), ('س', 'S21'), ('ز', 'S22')],
    'д': [('ض', 'S06'), ('ذ', 'S12'), ('د', 'S19')],
    'з': [('ض', 'S06'), ('ذ', 'S12'), ('ص', 'S13'), ('ز', 'S22'), ('ظ', 'S25')],
    'ф': [('ف', 'S08')],
    'п': [('ف', 'S08'), ('ب', 'S09')],
    'б': [('ب', 'S09')],
    'в': [('ف', 'S08'), ('ب', 'S09'), ('و', 'S10')],
    'р': [('ر', 'S15'), ('و', 'S10')],
    'л': [('ل', 'S16')],
    'м': [('م', 'S17')],
    'н': [('ن', 'S18')],
    'ж': [('ج', 'S02'), ('غ', 'S14')],
    'ц': [('ص', 'S13'), ('س', 'S21')],
    'ч': [('ش', 'S05'), ('ج', 'S02'), ('ك', 'S20')],
    'й': [('ي', 'YA')],
    'щ': [('ش', 'S05')],
}

# RU consonant -> possible ORIG2/Bitig sources
RU_TO_BITIG = {
    'к': ['q', 'k'],
    'г': ['g', 'ğ', 'q'],
    'х': ['q', 'ğ'],
    'т': ['t', 'd'],
    'ш': ['ş', 'č'],
    'с': ['s'],
    'д': ['d', 't'],
    'з': ['z', 's'],
    'б': ['b'],
    'п': ['b', 'p'],
    'в': ['v', 'b'],
    'р': ['r'],
    'л': ['l'],
    'м': ['m', 'n'],
    'н': ['n', 'ŋ'],
    'ж': ['j', 'ž'],
    'ч': ['č', 'ç'],
    'ц': ['s'],
    'й': ['y'],
    'щ': ['ş', 'č'],
}


def get_connection():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def extract_ru_consonants(word):
    """Extract consonant skeleton from Russian word, stripping known prefixes."""
    w = word.upper()
    # Try prefix strip
    stripped = w
    prefix_used = None
    for pref in sorted(RU_PREFIXES, key=len, reverse=True):
        if w.startswith(pref) and len(w) > len(pref) + 1:
            candidate = w[len(pref):]
            # Only strip if remaining part has enough consonants
            remaining_cons = [c for c in candidate.lower() if c not in RU_VOWELS and c.isalpha()]
            if len(remaining_cons) >= 2:
                stripped = candidate
                prefix_used = pref
                break

    consonants = [c for c in stripped.lower() if c not in RU_VOWELS and c.isalpha()]
    return consonants, prefix_used


def generate_aa_candidates(consonants, max_root_len=4):
    """Generate all possible AA root candidates from RU consonant skeleton."""
    if len(consonants) < 2:
        return []

    # For each consonant position, get possible AA mappings
    positions = []
    shifts = []
    for c in consonants[:max_root_len]:
        if c in RU_TO_AA:
            aa_options = RU_TO_AA[c]
            positions.append([opt[0] for opt in aa_options])
            shifts.append([opt for opt in aa_options])
        else:
            positions.append([])
            shifts.append([])

    # Generate all combinations for triliteral roots
    candidates = []
    if len(positions) >= 3:
        # Try positions [0,1,2], [0,1,3], [0,2,3], [1,2,3] for triliteral
        indices_sets = []
        n = len(positions)
        for i in range(n):
            for j in range(i+1, n):
                for k in range(j+1, n):
                    indices_sets.append((i, j, k))

        for idx_set in indices_sets:
            p = [positions[i] for i in idx_set if positions[i]]
            s = [shifts[i] for i in idx_set if shifts[i]]
            if len(p) == 3:
                for combo in product(*p):
                    root = '-'.join(combo)
                    # Build shift chain
                    chain_parts = []
                    for ci, i in enumerate(idx_set):
                        if i < len(shifts) and shifts[i]:
                            for aa, sid in shifts[i]:
                                if aa == combo[ci]:
                                    chain_parts.append(f"{consonants[i]}→{aa}({sid})")
                                    break
                    candidates.append({
                        'root_letters': root,
                        'chain': ', '.join(chain_parts),
                        'type': 'AA',
                        'consonants_used': [consonants[i] for i in idx_set]
                    })

    # Also try biliteral for short words
    if len(positions) >= 2:
        for i in range(len(positions)):
            for j in range(i+1, len(positions)):
                if positions[i] and positions[j]:
                    for c1 in positions[i]:
                        for c2 in positions[j]:
                            root = f"{c1}-{c2}"
                            candidates.append({
                                'root_letters': root,
                                'chain': f"{consonants[i]}→{c1}, {consonants[j]}→{c2}",
                                'type': 'AA',
                                'consonants_used': [consonants[i], consonants[j]]
                            })

    return candidates


def generate_bitig_candidates(consonants):
    """Generate ORIG2 root candidates from RU consonant skeleton."""
    candidates = []
    bitig_consonants = []
    for c in consonants:
        if c in RU_TO_BITIG:
            bitig_consonants.append(RU_TO_BITIG[c])
        else:
            bitig_consonants.append([c])

    if len(bitig_consonants) >= 2:
        # Build skeleton
        for combo in product(*bitig_consonants[:4]):
            root = '-'.join(combo)
            candidates.append({
                'root_letters': root,
                'type': 'ORIG2'
            })

    return candidates


def score_candidate(conn, candidate, prefer_orig2=False):
    """Score a root candidate against DB evidence.

    When prefer_orig2=True (Shipova batch / Turkic-origin words):
    - Kashgari attestation scores HIGHEST (these words came through Bitig)
    - AA Qur'anic attestation is informational only (doesn't boost score)
    - Direction: Bitig → RU (direct neighbor), NOT AA → RU
    """
    c = conn.cursor()
    score = 0
    evidence = []

    root = candidate['root_letters']
    is_orig2 = candidate.get('type') == 'ORIG2'

    # Check Kashgari/Bitig attestation — PRIMARY for ORIG2 track
    c.execute("SELECT entry_id, orig2_term FROM bitig_a1_entries WHERE root_letters = ?", (root,))
    bitig = c.fetchone()
    if bitig:
        if prefer_orig2 and is_orig2:
            score += 500  # HIGHEST score for Kashgari match on ORIG2 track
        else:
            score += 75
        evidence.append(f"Kashgari:{bitig[1]}")

    # Check existing roots table
    c.execute("SELECT root_id FROM roots WHERE root_letters = ?", (root,))
    existing = c.fetchone()
    if existing:
        if prefer_orig2 and is_orig2 and str(existing[0]).startswith('T'):
            score += 200  # Existing ORIG2 root = strong signal
        else:
            score += 50
        candidate['existing_root_id'] = existing[0]
        evidence.append(f"ROOT:{existing[0]}")

    # Check Qur'anic attestation
    c.execute("SELECT COUNT(*) FROM quran_word_roots WHERE root = ?", (root,))
    quranic_count = c.fetchone()[0]
    if quranic_count > 0:
        if prefer_orig2:
            # For Shipova batch: Qur'anic attestation is informational
            # Only boost AA candidates slightly — ORIG2 track should win
            if not is_orig2:
                score += 30  # Low boost — AA track is secondary for these words
            evidence.append(f"Quranic:{quranic_count}")
        else:
            score += 100 + min(quranic_count, 500)
            evidence.append(f"Quranic:{quranic_count}")

    # Check if root already has entries (more connections = more trusted)
    c.execute("SELECT COUNT(*) FROM entries WHERE root_letters = ?", (root,))
    entry_count = c.fetchone()[0]
    if entry_count > 0:
        score += 25 + min(entry_count, 50)
        evidence.append(f"Entries:{entry_count}")

    # Penalize biliteral (less specific)
    if root.count('-') == 1:
        score -= 20

    candidate['score'] = score
    candidate['evidence'] = evidence
    return candidate


def classify_corridor(candidate, word, consonants):
    """Classify the transmission corridor based on evidence."""
    if candidate['type'] == 'ORIG2':
        return 'ORIG2', 'Direct Bitig → RU'

    # Check for Type 3 markers (AA via Turkic)
    has_p_not_f = 'п' in consonants  # B01: no /f/ in Bitig
    has_ch = 'ч' in consonants

    if has_p_not_f:
        return 'TYPE3', 'AA → Turkic (B01: п not ф) → RU'

    # Default: Type 1 (AA via DS04)
    return 'TYPE1', 'AA → DS04 → RU'


def process_word(conn, word, entry_id=None, dry_run=True, prefer_orig2=False):
    """Full pipeline: word → root assignment.

    prefer_orig2=True: for Shipova/Turkic-origin batch.
    Bitig/Kashgari matches score highest. AA is secondary.
    """
    result = {
        'word': word,
        'entry_id': entry_id,
        'status': 'UNRESOLVED',
        'candidates': [],
        'best': None
    }

    # Step 1: Extract consonants
    consonants, prefix = extract_ru_consonants(word)
    result['consonants'] = consonants
    result['prefix_stripped'] = prefix

    if len(consonants) < 2:
        result['status'] = 'TOO_SHORT'
        return result

    # Step 2: Generate AA candidates
    aa_candidates = generate_aa_candidates(consonants)

    # Step 3: Generate ORIG2 candidates
    bitig_candidates = generate_bitig_candidates(consonants)

    # Step 4: Score all candidates (with ORIG2 preference for Shipova batch)
    all_candidates = aa_candidates + bitig_candidates
    scored = []
    for cand in all_candidates:
        scored_cand = score_candidate(conn, cand, prefer_orig2=prefer_orig2)
        if scored_cand['score'] > 0:  # Only keep candidates with evidence
            scored.append(scored_cand)

    # Sort by score descending
    scored.sort(key=lambda x: x['score'], reverse=True)

    # Keep top 5
    result['candidates'] = scored[:5]

    if scored:
        best = scored[0]
        corridor_type, corridor_desc = classify_corridor(best, word, consonants)

        result['best'] = {
            'root_letters': best['root_letters'],
            'root_id': best.get('existing_root_id'),
            'score': best['score'],
            'evidence': best['evidence'],
            'chain': best.get('chain', f"ORIG2: {word} → {best['root_letters']}"),
            'corridor': corridor_type,
            'corridor_desc': corridor_desc,
            'type': best['type']
        }
        result['status'] = 'RESOLVED'

        # Write to DB if not dry_run
        if not dry_run and entry_id:
            write_result(conn, result)
    else:
        result['status'] = 'NO_MATCH'

    return result


def write_result(conn, result):
    """Write resolved result to DB."""
    if result['status'] != 'RESOLVED' or not result['best']:
        return

    best = result['best']
    entry_id = result['entry_id']
    c = conn.cursor()

    root_id = best['root_id']

    # Create root if it doesn't exist
    if not root_id:
        # Generate new root_id
        if best['type'] == 'ORIG2':
            c.execute("SELECT MAX(CAST(REPLACE(root_id, 'T_BITIG', '') AS INTEGER)) FROM roots WHERE root_id LIKE 'T_BITIG%'")
            max_id = c.fetchone()[0] or 308
            root_id = f"T_BITIG{max_id + 1}"
            root_type = 'ORIG2'
        else:
            c.execute("SELECT MAX(CAST(REPLACE(root_id, 'R', '') AS INTEGER)) FROM roots WHERE root_id LIKE 'R%' AND root_id NOT LIKE 'R_%'")
            max_id = c.fetchone()[0] or 1958
            root_id = f"R{max_id + 1}"
            root_type = 'TRILITERAL'

        # Check Qur'anic attestation
        c.execute("SELECT COUNT(*) FROM quran_word_roots WHERE root = ?", (best['root_letters'],))
        q_tokens = c.fetchone()[0]

        c.execute("""INSERT OR IGNORE INTO roots (root_id, root_letters, root_bare, root_type, quran_tokens)
                     VALUES (?, ?, ?, ?, ?)""",
                  (root_id, best['root_letters'], best['root_letters'].replace('-', ''), root_type, q_tokens))

    # Update entry
    c.execute("""UPDATE entries SET
        root_id = ?,
        root_letters = ?,
        phonetic_chain = ?,
        ds_corridor = ?,
        quf_q = CASE WHEN ? > 0 THEN 'PASS' ELSE 'ORIG2_SKIP' END,
        quf_u = 'PASS',
        quf_f = 'PASS',
        quf_pass = 'TRUE',
        quf_date = datetime('now')
    WHERE entry_id = ? AND (root_id IS NULL OR root_id = '')""",
              (root_id, best['root_letters'], best['chain'], best['corridor'],
               1 if 'Quranic' in str(best['evidence']) else 0, entry_id))

    conn.commit()
    return root_id


def run_batch(dry_run=True, prefer_orig2=True):
    """Process all rootless entries.
    prefer_orig2=True by default: Shipova batch = Turkic-origin, ORIG2 first.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT entry_id, ru_term FROM entries WHERE (root_id IS NULL OR root_id = '') ORDER BY entry_id")
    entries = c.fetchall()

    print(f"Processing {len(entries)} rootless entries (dry_run={dry_run}, prefer_orig2={prefer_orig2})")
    print("=" * 80)

    resolved = 0
    no_match = 0

    for entry_id, ru_term in entries:
        if not ru_term:
            continue

        result = process_word(conn, ru_term, entry_id, dry_run, prefer_orig2=prefer_orig2)

        if result['status'] == 'RESOLVED':
            best = result['best']
            print(f"  {ru_term:15s} → {best['root_letters']:10s} score={best['score']:4d} "
                  f"corridor={best['corridor']:6s} evidence={','.join(best['evidence'])}")
            resolved += 1
        else:
            print(f"  {ru_term:15s} → {result['status']}")
            no_match += 1

    print("=" * 80)
    print(f"RESOLVED: {resolved} | NO_MATCH: {no_match} | TOTAL: {len(entries)}")

    if not dry_run:
        conn.commit()
    conn.close()


def run_single(word):
    """Process a single word and show all candidates."""
    conn = get_connection()
    result = process_word(conn, word, dry_run=True)

    print(f"Word: {word}")
    print(f"Consonants: {result['consonants']}")
    if result.get('prefix_stripped'):
        print(f"Prefix stripped: {result['prefix_stripped']}")
    print(f"Status: {result['status']}")
    print()

    if result['candidates']:
        print(f"Top candidates ({len(result['candidates'])}):")
        for i, cand in enumerate(result['candidates']):
            print(f"  {i+1}. {cand['root_letters']:12s} score={cand['score']:4d} "
                  f"type={cand['type']:5s} evidence={cand.get('evidence', [])}")
            if cand.get('chain'):
                print(f"     chain: {cand['chain']}")

    if result['best']:
        print(f"\nBEST: {result['best']['root_letters']} ({result['best']['corridor']})")

    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 uslap_rootfinder.py test WORD     — test single word")
        print("  python3 uslap_rootfinder.py batch         — dry run all rootless")
        print("  python3 uslap_rootfinder.py write         — write all resolved to DB")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'test' and len(sys.argv) >= 3:
        run_single(sys.argv[2])
    elif cmd == 'batch':
        run_batch(dry_run=True)
    elif cmd == 'write':
        run_batch(dry_run=False)
    else:
        print(f"Unknown command: {cmd}")
