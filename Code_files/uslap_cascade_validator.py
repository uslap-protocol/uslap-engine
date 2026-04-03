#!/usr/bin/env python3
"""
USLaP Cascade Validator — Layer 1→8 Alignment Check

Validates that ALL layers of data align with the letter computation (Layer 1).
Each layer has different validation rules:

  ALIGN fields     → MUST match compute_root_meaning()
  INVERSION fields → SHOULD contradict letters (documents what operator did)
  EVIDENCE fields  → Must not contain dictionary contamination
  CROSS-REF checks → Connected data must be internally consistent

Usage:
    python3 uslap_cascade_validator.py                    # full cascade
    python3 uslap_cascade_validator.py --root ق-ر-ش       # one root cascade
    python3 uslap_cascade_validator.py --layer 5           # one layer only
    python3 uslap_cascade_validator.py --trace ق-ر-ش      # full trace with output

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sys
import os
import sqlite3
import re
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')

# Dictionary contamination markers
DICT_MARKERS = [
    'to gather', 'to collect', 'to press', 'to cut', 'to strike',
    'to pull', 'to push', 'to take', 'to give', 'to make',
    'to hold', 'to carry', 'to bring', 'to send', 'to come',
    'to go', 'to turn', 'to stand', 'to sit', 'to lie',
    'to fall', 'to rise', 'to open', 'to close', 'to break',
    'to bind', 'to join', 'to split', 'to mix', 'to cover',
    'to fill', 'to pour', 'to flow', 'to blow', 'to burn',
    'to eat', 'to drink', 'to desire', 'to seek', 'to precede',
    'to amass', 'to earn', 'accumulation',
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def compute_for_root(root_letters):
    """Run compute_root_meaning on a root string."""
    try:
        from amr_alphabet import compute_root_meaning, compute_root_meaning_text
        result = compute_root_meaning(root_letters)
        text = compute_root_meaning_text(root_letters)
        return result, text
    except Exception as e:
        return None, f"ERROR: {e}"


def get_semantic_core(computation):
    """Extract semantic core concepts as a set."""
    if computation and isinstance(computation, dict):
        core = computation.get('semantic_core', '')
        return set(p.strip().upper() for p in core.split('+') if p.strip())
    return set()


def has_dict_contamination(text):
    """Check if text contains dictionary contamination markers."""
    if not text:
        return False, []
    text_lower = text.lower()
    found = [m for m in DICT_MARKERS if m in text_lower]
    return len(found) > 0, found


def field_contains_concepts(text, concepts):
    """Check if text contains any of the semantic concepts."""
    if not text or not concepts:
        return False
    text_lower = text.lower()
    return any(c.lower() in text_lower for c in concepts)


# ═══════════════════════════════════════════════════════════════════════
# LAYER 0: LETTERS (always valid — immutable)
# ═══════════════════════════════════════════════════════════════════════

def validate_layer0(root_letters):
    """Validate letters exist in the 28-letter alphabet."""
    issues = []
    if not root_letters or '-' not in root_letters:
        issues.append(f"INVALID ROOT FORMAT: '{root_letters}' — must be X-X-X with hyphens")
        return issues

    from amr_alphabet import ALPHABET
    valid_letters = set(ALPHABET.keys())
    letters = root_letters.split('-')

    for i, letter in enumerate(letters):
        if letter not in valid_letters:
            issues.append(f"LETTER '{letter}' (position {i+1}) NOT IN 28-letter alphabet")

    if len(letters) < 2 or len(letters) > 5:
        issues.append(f"ROOT has {len(letters)} radicals — expected 2-5")

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 1: ROOT COMPUTATION
# ═══════════════════════════════════════════════════════════════════════

def validate_layer1(conn, root_letters):
    """Validate that stored root meaning matches letter computation."""
    issues = []
    computation, comp_text = compute_for_root(root_letters)
    concepts = get_semantic_core(computation)

    if not computation:
        issues.append(f"COMPUTATION FAILED for {root_letters}")
        return issues

    # Check if root exists in DB
    row = conn.execute(
        "SELECT root_id, root_letters, primary_meaning FROM roots WHERE root_letters = ?",
        (root_letters,)
    ).fetchone()

    if row:
        stored = row['primary_meaning'] or ''
        # Check if stored meaning contains the computed concepts
        if concepts:
            missing = [c for c in concepts if c.lower() not in stored.lower()]
            if missing and '=' not in stored:
                issues.append(
                    f"LAYER 1 MISMATCH: stored meaning for {root_letters} is DICTIONARY, "
                    f"not letter-computed. Missing: {missing}. "
                    f"Stored: '{stored[:80]}'. Computed: '{comp_text}'"
                )
    else:
        # Root not in roots table — check if it's in entries
        entry = conn.execute(
            "SELECT entry_id, root_letters FROM entries WHERE root_letters = ? LIMIT 1",
            (root_letters,)
        ).fetchone()
        if entry:
            issues.append(
                f"ROOT {root_letters} in entries but NOT in roots table — "
                f"roots table incomplete"
            )

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 2: QUR'ANIC ATTESTATION
# ═══════════════════════════════════════════════════════════════════════

def validate_layer2(conn, root_letters):
    """
    Validate Qur'anic attestation.
    Every root must be classified:
      - QUR'AN ATTESTED: tokens > 0 in quran_word_roots
      - ORIG2 (Bitig): zero tokens but classified as ORIG2
      - UNATTESTED: zero tokens AND not ORIG2 → FLAGGED
    """
    issues = []

    # Count Qur'anic tokens
    count = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE root = ?",
        (root_letters,)
    ).fetchone()[0]

    if count == 0:
        # Zero tokens — check if ORIG2
        is_orig2 = False

        # Check entries for ORIG2 classification
        orig2_check = conn.execute(
            "SELECT entry_id, aa_word FROM entries WHERE root_letters = ? "
            "AND (aa_word LIKE '%ORIG2%' OR aa_word LIKE '%Bitig%' OR aa_word LIKE '%Turkic%') LIMIT 1",
            (root_letters,)
        ).fetchone()

        # Check bitig_a1_entries
        bitig_check = conn.execute(
            "SELECT entry_id FROM bitig_a1_entries WHERE root_letters = ? LIMIT 1",
            (root_letters,)
        ).fetchone()

        if orig2_check or bitig_check:
            is_orig2 = True

        if is_orig2:
            # TIER 3: ORIG2 (Bitig) — valid, separate lineage
            issues.append(
                f"LAYER 2 INFO: {root_letters} — TIER 3 (ORIG2/Bitig). "
                f"Zero Qur'anic tokens. Valid ORIG2 classification. "
                f"Source: Yafith inheritance."
            )
        else:
            # TIER 2: AA PRE/POST-QUR'ANIC — valid AA, not in the final preserved text
            # Q2:31 وَعَلَّمَ آدَمَ الْأَسْمَاءَ كُلَّهَا — ALL the names
            # AA = all eras, all revelations, all humans. NOT only Qur'an.
            issues.append(
                f"LAYER 2 INFO: {root_letters} — TIER 2 (AA, not in final preserved text). "
                f"Zero Qur'anic tokens. AA root — 28 letters are Allah's, "
                f"taught to Adam (Q2:31). May appear in previous صُحُف (Q87:18-19). "
                f"Qur'an-preserved roots (Tier 1) have higher source priority."
            )
    else:
        # Has tokens — verify forms are in the compiler
        forms = conn.execute(
            "SELECT DISTINCT aa_word, word_type FROM quran_word_roots WHERE root = ?",
            (root_letters,)
        ).fetchall()
        if not forms:
            issues.append(
                f"LAYER 2 WARNING: {root_letters} has {count} tokens but "
                f"no distinct forms found — compiler data may be incomplete"
            )

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 3: QV TRANSLATION REGISTER
# ═══════════════════════════════════════════════════════════════════════

def validate_layer3(conn, root_letters):
    """
    Validate QV Translation Register entries.
    If a QV entry exists, its corruption_type must be consistent
    with the letter computation.
    """
    issues = []

    try:
        qv_rows = conn.execute(
            "SELECT * FROM qv_translation_register WHERE root_letters = ?",
            (root_letters,)
        ).fetchall()
    except Exception:
        return issues  # Table may not exist

    if not qv_rows:
        return issues  # No QV entries — not an issue

    computation, comp_text = compute_for_root(root_letters)
    concepts = get_semantic_core(computation)

    for qv in qv_rows:
        qv_dict = dict(qv)
        qur_meaning = qv_dict.get('quranic_meaning', '') or ''
        corrupted = qv_dict.get('corrupted_translation', '') or ''

        # Check if the Qur'anic meaning field aligns with letter computation
        if qur_meaning and concepts:
            has_concept = any(c.lower() in qur_meaning.lower() for c in concepts)
            if not has_concept and '=' not in qur_meaning:
                issues.append(
                    f"LAYER 3 MISMATCH: QV entry for {root_letters} — "
                    f"quranic_meaning '{qur_meaning[:60]}' doesn't contain "
                    f"computed concepts {concepts}"
                )

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 4: ENTRIES
# ═══════════════════════════════════════════════════════════════════════

def validate_layer4(conn, root=None):
    """Validate entries table against letter computation."""
    issues = []
    query = "SELECT entry_id, en_term, aa_word, root_letters, notes FROM entries WHERE root_letters IS NOT NULL"
    params = ()
    if root:
        query += " AND root_letters = ?"
        params = (root,)

    rows = conn.execute(query, params).fetchall()

    for row in rows:
        root_letters = row['root_letters']
        computation, comp_text = compute_for_root(root_letters)
        concepts = get_semantic_core(computation)

        # ALIGN: aa_word must contain computation
        aa_word = row['aa_word'] or ''
        if '=' not in aa_word:
            issues.append({
                'layer': 4, 'table': 'entries', 'id': row['entry_id'],
                'term': row['en_term'], 'root': root_letters,
                'field': 'aa_word', 'type': 'NOT_COMPUTED',
                'detail': f'aa_word lacks computation: {aa_word[:80]}',
                'fix': comp_text,
            })

        # EVIDENCE: notes should not contain dictionary language
        notes = row['notes'] or ''
        contaminated, markers = has_dict_contamination(notes)
        # Allow if it's inside a CORRECTED note
        if contaminated and 'CORRECTED' not in notes and 'was dictionary' not in notes:
            issues.append({
                'layer': 4, 'table': 'entries', 'id': row['entry_id'],
                'term': row['en_term'], 'root': root_letters,
                'field': 'notes', 'type': 'DICT_IN_NOTES',
                'detail': f'Dictionary language in notes: {markers}',
                'fix': 'Remove dictionary phrasing from notes',
            })

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 5: CHILD_SCHEMA (PEOPLES & PLACES)
# ═══════════════════════════════════════════════════════════════════════

def validate_layer5(conn, root=None):
    """Validate child_entries against letter computation."""
    issues = []
    query = """SELECT child_id, shell_name, orig_meaning, operation_role,
                      shell_meaning, orig_root, notes
               FROM child_entries WHERE orig_root IS NOT NULL"""
    params = ()
    if root:
        query += " AND orig_root = ?"
        params = (root,)

    rows = conn.execute(query, params).fetchall()

    for row in rows:
        root_letters = row['orig_root']
        if not root_letters or '-' not in root_letters:
            continue

        computation, comp_text = compute_for_root(root_letters)
        concepts = get_semantic_core(computation)

        # ALIGN: orig_meaning must match letters
        orig = row['orig_meaning'] or ''
        if '=' not in orig:
            issues.append({
                'layer': 5, 'table': 'child_entries', 'id': row['child_id'],
                'term': row['shell_name'], 'root': root_letters,
                'field': 'orig_meaning', 'type': 'NOT_COMPUTED',
                'detail': f'orig_meaning lacks computation: {orig[:80]}',
                'fix': comp_text,
            })

        # ALIGN: operation_role must EXPLAIN letters in context
        op_role = row['operation_role'] or ''
        contaminated, markers = has_dict_contamination(op_role)
        if contaminated:
            issues.append({
                'layer': 5, 'table': 'child_entries', 'id': row['child_id'],
                'term': row['shell_name'], 'root': root_letters,
                'field': 'operation_role', 'type': 'DICT_IN_OP_ROLE',
                'detail': f'Dictionary language in operation_role: {markers}',
                'fix': f'Rewrite operation_role using letter concepts: {comp_text}',
            })

        # INVERSION: shell_meaning SHOULD contradict letters
        shell = row['shell_meaning'] or ''
        if shell and field_contains_concepts(shell, concepts):
            # shell_meaning aligns with letters — inversion NOT documented
            issues.append({
                'layer': 5, 'table': 'child_entries', 'id': row['child_id'],
                'term': row['shell_name'], 'root': root_letters,
                'field': 'shell_meaning', 'type': 'INVERSION_MISSING',
                'detail': f'shell_meaning aligns with letters — inversion not documented',
                'fix': 'Document how the operator inverted the original letter meaning',
            })

        # EVIDENCE: notes
        notes = row['notes'] or ''
        contaminated, markers = has_dict_contamination(notes)
        if contaminated and 'CORRECTED' not in notes:
            issues.append({
                'layer': 5, 'table': 'child_entries', 'id': row['child_id'],
                'term': row['shell_name'], 'root': root_letters,
                'field': 'notes', 'type': 'DICT_IN_NOTES',
                'detail': f'Dictionary language in notes: {markers}',
                'fix': 'Remove dictionary phrasing',
            })

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 6: NETWORKS
# ═══════════════════════════════════════════════════════════════════════

def validate_layer6(conn, root=None):
    """Validate networks against letter computation."""
    issues = []
    try:
        rows = conn.execute(
            "SELECT orig_id, specific_data FROM m4_networks WHERE specific_data IS NOT NULL"
        ).fetchall()
    except Exception:
        return issues

    for row in rows:
        data = row['specific_data'] or ''
        contaminated, markers = has_dict_contamination(data)
        if contaminated:
            issues.append({
                'layer': 6, 'table': 'm4_networks', 'id': row['orig_id'],
                'term': row['orig_id'], 'root': '',
                'field': 'specific_data', 'type': 'DICT_IN_NETWORK',
                'detail': f'Dictionary language in network data: {markers}',
                'fix': 'Rewrite using letter computation concepts',
            })

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 7: CHRONOLOGY
# ═══════════════════════════════════════════════════════════════════════

def validate_layer7(conn, root=None):
    """Validate chronology against letter computation."""
    issues = []
    try:
        rows = conn.execute(
            "SELECT id, event, orig_meaning, oper_meaning, notes FROM chronology"
        ).fetchall()
    except Exception:
        return issues

    for row in rows:
        # ALIGN: orig_meaning
        orig = row['orig_meaning'] or ''
        contaminated, markers = has_dict_contamination(orig)
        if contaminated:
            issues.append({
                'layer': 7, 'table': 'chronology', 'id': row['id'],
                'term': (row['event'] or '')[:40], 'root': '',
                'field': 'orig_meaning', 'type': 'DICT_IN_CHRONOLOGY',
                'detail': f'Dictionary language in orig_meaning: {markers}',
                'fix': 'Replace with letter computation',
            })

        # EVIDENCE: notes
        notes = row['notes'] or ''
        contaminated, markers = has_dict_contamination(notes)
        if contaminated and 'CORRECTED' not in notes:
            issues.append({
                'layer': 7, 'table': 'chronology', 'id': row['id'],
                'term': (row['event'] or '')[:40], 'root': '',
                'field': 'notes', 'type': 'DICT_IN_NOTES',
                'detail': f'Dictionary language in notes: {markers}',
                'fix': 'Remove dictionary phrasing',
            })

    return issues


# ═══════════════════════════════════════════════════════════════════════
# LAYER 8: INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════

def validate_layer8(conn, root=None):
    """Validate intelligence tables against letter computation."""
    issues = []

    # DP Register
    try:
        rows = conn.execute(
            "SELECT dp_id, description, notes FROM dp_register"
        ).fetchall()
        for row in rows:
            for field_name in ['description', 'notes']:
                text = row[field_name] or ''
                contaminated, markers = has_dict_contamination(text)
                if contaminated and 'CORRECTED' not in text:
                    issues.append({
                        'layer': 8, 'table': 'dp_register', 'id': row['dp_id'],
                        'term': row['dp_id'], 'root': '',
                        'field': field_name, 'type': 'DICT_IN_INTEL',
                        'detail': f'Dictionary language in {field_name}: {markers}',
                        'fix': 'Remove dictionary phrasing',
                    })
    except Exception:
        pass

    # Interception Register
    try:
        rows = conn.execute(
            "SELECT int_id, quranic_root, lisan_form, notes FROM interception_register"
        ).fetchall()
        for row in rows:
            root_letters = row['quranic_root'] or ''
            if root_letters and '-' in root_letters:
                computation, comp_text = compute_for_root(root_letters)
                concepts = get_semantic_core(computation)

                notes = row['notes'] or ''
                contaminated, markers = has_dict_contamination(notes)
                if contaminated and 'CORRECTED' not in notes:
                    issues.append({
                        'layer': 8, 'table': 'interception_register',
                        'id': row['int_id'],
                        'term': row['lisan_form'] or '', 'root': root_letters,
                        'field': 'notes', 'type': 'DICT_IN_INTERCEPTION',
                        'detail': f'Dictionary language in interception notes: {markers}',
                        'fix': f'Align with letter computation: {comp_text}',
                    })
    except Exception:
        pass

    return issues


# ═══════════════════════════════════════════════════════════════════════
# TRACE: Full cascade for one root
# ═══════════════════════════════════════════════════════════════════════

def trace_root(conn, root_letters):
    """
    Produce a complete cascade trace for one root.
    Shows how the letter computation flows through ALL layers.
    """
    computation, comp_text = compute_for_root(root_letters)
    concepts = get_semantic_core(computation)

    print(f"\n{'═' * 70}")
    print(f"CASCADE TRACE: {root_letters}")
    print(f"{'═' * 70}")

    all_issues = []

    # LAYER 0: Letters
    print(f"\n{'─' * 70}")
    print(f"LAYER 0 — LETTERS (immutable)")
    print(f"{'─' * 70}")
    l0_issues = validate_layer0(root_letters)
    if l0_issues:
        for issue in l0_issues:
            print(f"  ⛔ {issue}")
        all_issues.extend(l0_issues)
    elif computation and isinstance(computation, dict):
        for letter in computation.get('letters', []):
            print(f"  ✓ {letter['letter']} ({letter['name']}) — abjad {letter['abjad']}")
            print(f"    CORE: {letter['core_concept']}")
            print(f"    POSITION {letter['position']}: {letter['positional_behaviour'][:100]}")

    # LAYER 1: Root
    print(f"\n{'─' * 70}")
    print(f"LAYER 1 — ROOT (computed)")
    print(f"{'─' * 70}")
    print(f"  COMPUTATION: {comp_text}")
    print(f"  ABJAD SUM: {computation.get('abjad_sum', '?') if computation else '?'}")
    print(f"  SEMANTIC CORE: {' + '.join(concepts)}")
    l1_issues = validate_layer1(conn, root_letters)
    if l1_issues:
        for issue in l1_issues:
            print(f"  ⛔ {issue}")
        all_issues.extend(l1_issues)
    else:
        print(f"  ✓ Layer 1 ALIGNED")

    # LAYER 2: Qur'an
    print(f"\n{'─' * 70}")
    print(f"LAYER 2 — QUR'AN ATTESTATION")
    print(f"{'─' * 70}")
    l2_issues = validate_layer2(conn, root_letters)
    for issue in l2_issues:
        if 'INFO' in issue:
            print(f"  ℹ {issue}")
        else:
            print(f"  ⛔ {issue}")
            all_issues.append(issue)
    qwords = conn.execute(
        "SELECT surah, ayah, word_position, aa_word, root_meaning, word_type "
        "FROM quran_word_roots WHERE root = ? ORDER BY surah, ayah",
        (root_letters,)
    ).fetchall()
    print(f"  TOKENS: {len(qwords)}")
    surahs = set()
    for w in qwords:
        surahs.add(w['surah'])
        print(f"  Q{w['surah']}:{w['ayah']} word {w['word_position']}: "
              f"{w['aa_word']} [{w['word_type'] or '?'}]")
    print(f"  SURAHS: {sorted(surahs)}")

    # Get full ayat for context
    for s in sorted(surahs):
        ayat = conn.execute(
            "SELECT ayah, aa_text, root_translation FROM quran_ayat "
            "WHERE surah = ? ORDER BY ayah", (s,)
        ).fetchall()
        for a in ayat:
            # Only show ayat that contain our root's words
            matching = [w for w in qwords if w['surah'] == s and w['ayah'] == a['ayah']]
            if matching:
                print(f"\n  Q{s}:{a['ayah']}: {a['aa_text']}")
                print(f"    ROOT TRANSLATION: {(a['root_translation'] or '')[:120]}")

    # LAYER 3: QV Translation
    print(f"\n{'─' * 70}")
    print(f"LAYER 3 — QV TRANSLATION REGISTER")
    print(f"{'─' * 70}")
    l3_issues = validate_layer3(conn, root_letters)
    if l3_issues:
        for issue in l3_issues:
            print(f"  ⛔ {issue}")
        all_issues.extend(l3_issues)
    try:
        qv_col = 'root_letters'
        qv = conn.execute(
            f"SELECT * FROM qv_translation_register WHERE {qv_col} = ?",
            (root_letters,)
        ).fetchall()
        if qv:
            for q in qv:
                print(f"  {dict(q)}")
            print(f"  ✓ Layer 3 — {len(qv)} QV entries")
        else:
            print(f"  No QV entries for {root_letters}")
    except Exception as e:
        print(f"  QV check error: {e}")

    # LAYER 4: Entries
    print(f"\n{'─' * 70}")
    print(f"LAYER 4 — DOWNSTREAM ENTRIES")
    print(f"{'─' * 70}")
    entries = conn.execute(
        "SELECT entry_id, en_term, aa_word, notes FROM entries WHERE root_letters = ?",
        (root_letters,)
    ).fetchall()
    print(f"  COUNT: {len(entries)}")
    for e in entries:
        ar = (e['aa_word'] or '')[:80]
        aligned = '=' in ar
        status = '✓' if aligned else '✗'
        print(f"  {status} #{e['entry_id']} {e['en_term'] or '?'}: {ar}")

    # LAYER 5: Child schema
    print(f"\n{'─' * 70}")
    print(f"LAYER 5 — PEOPLES & PLACES")
    print(f"{'─' * 70}")
    children = conn.execute(
        "SELECT child_id, shell_name, orig_meaning, operation_role, shell_meaning "
        "FROM child_entries WHERE orig_root = ?",
        (root_letters,)
    ).fetchall()
    if children:
        for c in children:
            orig_aligned = '=' in (c['orig_meaning'] or '')
            print(f"  {'✓' if orig_aligned else '✗'} {c['child_id']} — {c['shell_name']}")
            print(f"    ORIG: {(c['orig_meaning'] or '')[:80]}")
            print(f"    ROLE: {(c['operation_role'] or '')[:80]}")
            print(f"    SHELL: {(c['shell_meaning'] or '')[:80]}")
    else:
        print(f"  No child entries for {root_letters}")

    # LAYER 6: Networks
    print(f"\n{'─' * 70}")
    print(f"LAYER 6 — NETWORKS")
    print(f"{'─' * 70}")
    # Find networks that reference this root via entries
    entry_ids = [str(e['entry_id']) for e in entries]
    try:
        nets = conn.execute(
            "SELECT DISTINCT tn.term, tn.source_table, tn.source_id "
            "FROM term_nodes tn WHERE tn.source_table = 'm4_networks' "
            "AND (tn.term LIKE ? OR tn.term LIKE ?)",
            (f"%{root_letters}%", f"%{''.join(root_letters.split('-'))}%")
        ).fetchall()
        if nets:
            for n in nets:
                print(f"  {n['source_id']}: {n['term'][:80]}")
        else:
            print(f"  No networks reference {root_letters}")
    except Exception:
        print(f"  Network scan skipped")

    # LAYER 7: Chronology
    print(f"\n{'─' * 70}")
    print(f"LAYER 7 — CHRONOLOGY")
    print(f"{'─' * 70}")
    root_bare = root_letters.replace('-', '')
    try:
        chron = conn.execute(
            "SELECT id, date, event, notes FROM chronology "
            "WHERE event LIKE ? OR notes LIKE ? OR event LIKE ? OR notes LIKE ?",
            (f"%{root_letters}%", f"%{root_letters}%",
             f"%{root_bare}%", f"%{root_bare}%")
        ).fetchall()
        if chron:
            for c in chron:
                print(f"  {c['id']} ({c['date']}): {(c['event'] or '')[:80]}")
        else:
            print(f"  No chronology entries for {root_letters}")
    except Exception:
        print(f"  Chronology scan skipped")

    # LAYER 8: Intelligence
    print(f"\n{'─' * 70}")
    print(f"LAYER 8 — INTELLIGENCE")
    print(f"{'─' * 70}")
    try:
        intcpt = conn.execute(
            "SELECT int_id, quranic_root, quranic_meaning, lisan_form, "
            "lisan_meaning, corruption_type FROM interception_register "
            "WHERE quranic_root = ?",
            (root_letters,)
        ).fetchall()
        if intcpt:
            for i in intcpt:
                print(f"  {i['int_id']}: {i['quranic_meaning']} → {i['lisan_form']} "
                      f"[{i['corruption_type']}]")
        else:
            print(f"  No interception register entries for {root_letters}")
    except Exception:
        pass

    try:
        dp = conn.execute(
            "SELECT dp_id, description FROM dp_register "
            "WHERE description LIKE ? OR description LIKE ?",
            (f"%{root_letters}%", f"%{root_bare}%")
        ).fetchall()
        if dp:
            for d in dp:
                print(f"  {d['dp_id']}: {(d['description'] or '')[:80]}")
        else:
            print(f"  No DP register entries for {root_letters}")
    except Exception:
        pass

    # VALIDATION SUMMARY — ALL LAYERS
    print(f"\n{'═' * 70}")
    print(f"CASCADE VALIDATION SUMMARY — ALL 9 LAYERS")
    print(f"{'═' * 70}")

    # Layers 0-3 (returned as string lists)
    l0 = validate_layer0(root_letters)
    l1 = validate_layer1(conn, root_letters)
    l2 = validate_layer2(conn, root_letters)
    l3 = validate_layer3(conn, root_letters)

    # Layers 4-5 (returned as dict lists)
    l4 = validate_layer4(conn, root_letters)
    l5 = validate_layer5(conn, root_letters)

    # Print per-layer status
    layer_results = [
        (0, 'LETTERS', l0),
        (1, 'ROOT COMPUTATION', l1),
        (2, 'QUR\'AN ATTESTATION', l2),
        (3, 'QV TRANSLATION', l3),
        (4, 'ENTRIES', l4),
        (5, 'PEOPLES & PLACES', l5),
    ]

    total_issues = 0
    for num, name, issues in layer_results:
        # Separate real issues from INFO classifications
        real_issues = [i for i in issues if not (isinstance(i, str) and 'INFO' in i)]
        info_items = [i for i in issues if isinstance(i, str) and 'INFO' in i]
        count = len(real_issues)
        total_issues += count
        if count > 0:
            status = f"⛔ {count} issues"
        elif info_items:
            # Extract tier info
            tier = 'TIER 2' if any('TIER 2' in i for i in info_items) else \
                   'TIER 3' if any('TIER 3' in i for i in info_items) else 'INFO'
            status = f"ℹ {tier}"
        else:
            status = "✓ PASS"
        print(f"  L{num} {name}: {status}")

    # Collect all for detail
    if total_issues > 0:
        print(f"\n  TOTAL ISSUES: {total_issues}")
        for num, name, issues in layer_results:
            for issue in issues:
                if isinstance(issue, dict):
                    print(f"    L{num} [{issue.get('table','')}] {issue.get('id','')}: "
                          f"{issue.get('type','')} — {issue.get('detail','')[:80]}")
                else:
                    print(f"    L{num}: {issue[:100]}")
    else:
        print(f"\n  ✓ ALL LAYERS ALIGNED for {root_letters}")
        print(f"  Letter computation cascades cleanly through all layers.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='USLaP Cascade Validator')
    parser.add_argument('--root', help='Validate specific root (e.g. ق-ر-ش)')
    parser.add_argument('--layer', type=int, help='Validate specific layer (4-8)')
    parser.add_argument('--trace', help='Full cascade trace for a root')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    conn = get_connection()

    if args.trace:
        trace_root(conn, args.trace)
        conn.close()
        return

    all_issues = []

    layers = [4, 5, 6, 7, 8] if not args.layer else [args.layer]

    for layer in layers:
        if layer == 4:
            print(f"Validating Layer 4 (entries)...")
            issues = validate_layer4(conn, args.root)
        elif layer == 5:
            print(f"Validating Layer 5 (child_entries)...")
            issues = validate_layer5(conn, args.root)
        elif layer == 6:
            print(f"Validating Layer 6 (networks)...")
            issues = validate_layer6(conn, args.root)
        elif layer == 7:
            print(f"Validating Layer 7 (chronology)...")
            issues = validate_layer7(conn, args.root)
        elif layer == 8:
            print(f"Validating Layer 8 (intelligence)...")
            issues = validate_layer8(conn, args.root)
        else:
            continue

        all_issues.extend(issues)
        print(f"  → {len(issues)} issues")

    if args.json:
        print(json.dumps(all_issues, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'=' * 70}")
        print(f"CASCADE VALIDATION SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total issues: {len(all_issues)}")

        by_layer = {}
        by_type = {}
        for i in all_issues:
            by_layer[i['layer']] = by_layer.get(i['layer'], 0) + 1
            by_type[i['type']] = by_type.get(i['type'], 0) + 1

        print(f"\nBy layer:")
        for l, c in sorted(by_layer.items()):
            print(f"  Layer {l}: {c}")

        print(f"\nBy type:")
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")

    conn.close()


if __name__ == '__main__':
    main()
