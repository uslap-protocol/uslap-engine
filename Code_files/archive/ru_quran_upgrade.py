#!/usr/bin/env python3
"""
Batch-upgrade score-7 and score-8 Russian entries (a1_записи)
by adding Qur'anic attestation from quran_word_roots compiler table.

Algorithm:
- Score 7 entries: if root found in Qur'an -> add Q refs, upgrade to 9
- Score 8 entries: if root found AND entry lacks Q refs -> add Q refs, upgrade to 9
- Score 8 entries that ALREADY have Q refs: upgrade to 9 (they have the data)
- Compounds: try FIRST root only
- If root NOT in Qur'an: leave unchanged, log it
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")


def get_quran_data(cursor, root):
    """
    Query quran_word_roots for a given root.
    Returns (token_count, refs_string) or (0, None) if not found.
    refs_string = "Q1:2, Q3:45, Q7:89" (first 3 unique surah:ayah)
    """
    cursor.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE root = ?",
        (root,)
    )
    token_count = cursor.fetchone()[0]

    if token_count == 0:
        return 0, None

    cursor.execute(
        """SELECT DISTINCT surah, ayah FROM quran_word_roots
           WHERE root = ?
           ORDER BY surah, ayah
           LIMIT 3""",
        (root,)
    )
    refs = cursor.fetchall()
    refs_string = ", ".join(f"Q{s}:{a}" for s, a in refs)

    return token_count, refs_string


def extract_first_root(root_letters):
    """
    Handle compound roots like ج-ب-ل+ط-ر-ق by extracting the FIRST root.
    Also handle None/empty values.
    """
    if not root_letters or not root_letters.strip():
        return None
    first = root_letters.strip().split('+')[0].strip()
    if not first or '-' not in first:
        return None
    return first


def main():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all score-7 and score-8 entries
    cursor.execute(
        """SELECT запись_id, корневые_буквы, балл, коранич_значение, рус_термин
           FROM "a1_записи"
           WHERE балл IN (7, 8)
           ORDER BY балл, запись_id"""
    )
    entries = cursor.fetchall()

    print("=" * 80)
    print("RU BATCH UPGRADE: Qur'anic Attestation from Compiler")
    print("=" * 80)
    print(f"Total entries to process: {len(entries)}")
    print(f"  Score 7: {sum(1 for e in entries if e['балл'] == 7)}")
    print(f"  Score 8: {sum(1 for e in entries if e['балл'] == 8)}")
    print()

    # Counters
    upgraded_7_to_9 = []
    upgraded_8_to_9 = []
    no_quran_root_7 = []
    no_quran_root_8 = []
    already_has_refs_8 = []
    bad_root = []
    compounds_processed = []

    for entry in entries:
        eid = entry['запись_id']
        root_raw = entry['корневые_буквы']
        score = entry['балл']
        current_meaning = entry['коранич_значение'] or ""
        term = entry['рус_термин'] or f"ID:{eid}"

        # Extract root (handle compounds)
        is_compound = root_raw and '+' in root_raw
        root = extract_first_root(root_raw)

        if not root:
            bad_root.append((eid, term, root_raw, score))
            continue

        if is_compound:
            compounds_processed.append((eid, term, root_raw, root))

        # Check if score-8 already has Q refs with actual surah:ayah references
        has_refs_already = (
            score == 8
            and "Qur'anic root" in current_meaning
            and "Refs:" in current_meaning
        )

        # Get Qur'anic data
        token_count, refs_string = get_quran_data(cursor, root)

        if token_count > 0:
            # Build the new meaning
            new_meaning = f"Qur'anic root {root.replace('-', '')}. Token count: {token_count}. Refs: {refs_string}"

            if score == 7:
                cursor.execute(
                    """UPDATE "a1_записи"
                       SET коранич_значение = ?, балл = 9
                       WHERE запись_id = ?""",
                    (new_meaning, eid)
                )
                upgraded_7_to_9.append((eid, term, root, token_count, refs_string))

            elif score == 8:
                if has_refs_already:
                    # Already has refs -- just upgrade score to 9
                    cursor.execute(
                        """UPDATE "a1_записи"
                           SET балл = 9
                           WHERE запись_id = ?""",
                        (eid,)
                    )
                    already_has_refs_8.append((eid, term, root, current_meaning[:60]))
                else:
                    # Needs refs added + upgrade
                    cursor.execute(
                        """UPDATE "a1_записи"
                           SET коранич_значение = ?, балл = 9
                           WHERE запись_id = ?""",
                        (new_meaning, eid)
                    )
                upgraded_8_to_9.append((eid, term, root, token_count, refs_string))
        else:
            # Root NOT in Qur'an -- leave unchanged
            if score == 7:
                no_quran_root_7.append((eid, term, root_raw))
            else:
                no_quran_root_8.append((eid, term, root_raw))

    # Commit all changes
    conn.commit()

    # -- DETAILED RESULTS --

    print("-" * 80)
    print(f"UPGRADED 7 -> 9 ({len(upgraded_7_to_9)} entries)")
    print("-" * 80)
    for eid, term, root, tc, refs in upgraded_7_to_9:
        print(f"  #{eid:<5} {term:<25} {root:<12} tokens={tc:<5} {refs}")

    print()
    print("-" * 80)
    print(f"UPGRADED 8 -> 9 ({len(upgraded_8_to_9)} entries, new refs added)")
    print("-" * 80)
    for eid, term, root, tc, refs in upgraded_8_to_9:
        print(f"  #{eid:<5} {term:<25} {root:<12} tokens={tc:<5} {refs}")

    if already_has_refs_8:
        print()
        print("-" * 80)
        print(f"SCORE 8 -> 9 (already had refs, score upgraded) ({len(already_has_refs_8)} entries)")
        print("-" * 80)
        for eid, term, root, meaning in already_has_refs_8:
            print(f"  #{eid:<5} {term:<25} {root:<12} {meaning}...")

    if compounds_processed:
        print()
        print("-" * 80)
        print(f"COMPOUND ROOTS (first root used) ({len(compounds_processed)} entries)")
        print("-" * 80)
        for eid, term, full_root, first_root in compounds_processed:
            print(f"  #{eid:<5} {term:<25} full={full_root:<20} -> used={first_root}")

    print()
    print("-" * 80)
    print(f"NO QUR'ANIC ROOT -- LEFT AT SCORE 7 ({len(no_quran_root_7)} entries)")
    print("-" * 80)
    for eid, term, root in no_quran_root_7:
        print(f"  #{eid:<5} {term:<25} {root}")

    if no_quran_root_8:
        print()
        print("-" * 80)
        print(f"NO QUR'ANIC ROOT -- LEFT AT SCORE 8 ({len(no_quran_root_8)} entries)")
        print("-" * 80)
        for eid, term, root in no_quran_root_8:
            print(f"  #{eid:<5} {term:<25} {root}")

    if bad_root:
        print()
        print("-" * 80)
        print(f"BAD/MISSING ROOT -- SKIPPED ({len(bad_root)} entries)")
        print("-" * 80)
        for eid, term, root, score in bad_root:
            print(f"  #{eid:<5} {term:<25} root={root!r:<20} score={score}")

    # -- SUMMARY --
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_upgraded = len(upgraded_7_to_9) + len(upgraded_8_to_9) + len(already_has_refs_8)
    print(f"  Upgraded 7 -> 9:          {len(upgraded_7_to_9)}")
    print(f"  Upgraded 8 -> 9 (new ref): {len(upgraded_8_to_9)}")
    print(f"  Upgraded 8 -> 9 (had ref): {len(already_has_refs_8)}")
    print(f"  Total upgraded:           {total_upgraded}")
    print(f"  Left at score 7 (no Q):   {len(no_quran_root_7)}")
    print(f"  Left at score 8 (no Q):   {len(no_quran_root_8)}")
    print(f"  Bad/missing root:         {len(bad_root)}")
    print(f"  Compounds (1st used):     {len(compounds_processed)}")

    # Verify new distribution
    cursor.execute(
        """SELECT балл, COUNT(*) FROM "a1_записи" GROUP BY балл ORDER BY балл"""
    )
    print()
    print("  NEW SCORE DISTRIBUTION:")
    for row in cursor.fetchall():
        print(f"    Score {row[0]}: {row[1]} entries")

    conn.close()
    print()
    print("Done. All changes committed.")


if __name__ == "__main__":
    main()
