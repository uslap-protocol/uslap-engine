#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP AUTO-POPULATION & SELF-CORRECTION ENGINE
Seven-Surah Architecture: al-Qamar scans → al-Alaq parses → al-Ikhlas verifies →
al-Falaq replicates → Yasin sequences → an-Nahl routes → al-Fatiha gates (bbi approves).

Usage:
    python3 uslap_autopop.py gaps          # Show all population gaps
    python3 uslap_autopop.py corrections   # Show all correction candidates
    python3 uslap_autopop.py siblings      # Show sibling gap details
    python3 uslap_autopop.py sem_review    # Audit SEM_REVIEW scores
    python3 uslap_autopop.py roots_check   # Find entries where better root may exist
    python3 uslap_autopop.py full          # Full scan (gaps + corrections)
    python3 uslap_autopop.py enforce_caps  # Enforce SEM_REVIEW score caps (writes to DB)

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
from collections import defaultdict

DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"


def get_db():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# al-Qamar (INDEX) — SCAN FOR GAPS
# ═══════════════════════════════════════════════════════════════════════════════

def scan_sibling_gaps(db):
    """Find ROOT_IDs present in one sibling but missing from others."""
    en_roots = {}
    for r in db.execute("SELECT root_id, en_term, entry_id FROM a1_entries WHERE root_id IS NOT NULL AND root_id != ''").fetchall():
        en_roots[r[0]] = (r[1], r[2])

    ru_roots = {}
    for r in db.execute("SELECT корень_id, рус_термин, запись_id FROM [a1_записи] WHERE корень_id IS NOT NULL AND корень_id != ''").fetchall():
        ru_roots[r[0]] = (r[1], r[2])

    fa_roots = {}
    for r in db.execute("""SELECT r_she_id_ریشِه_root_id, v_zhe_f_rs__واژِهِ_فارسی_persian_term, madkhal_id_مَدخَل_entry_id
                          FROM persian_a1_mad_khil
                          WHERE r_she_id_ریشِه_root_id IS NOT NULL AND r_she_id_ریشِه_root_id != ''""").fetchall():
        fa_roots[r[0]] = (r[1], r[2])

    en_set = set(en_roots.keys())
    ru_set = set(ru_roots.keys())
    fa_set = set(fa_roots.keys())

    gaps = {
        'en_not_ru': {rid: en_roots[rid] for rid in en_set - ru_set},
        'en_not_fa': {rid: en_roots[rid] for rid in en_set - fa_set},
        'ru_not_en': {rid: ru_roots[rid] for rid in ru_set - en_set},
        'ru_not_fa': {rid: ru_roots[rid] for rid in ru_set - fa_set},
        'fa_not_en': {rid: fa_roots[rid] for rid in fa_set - en_set},
        'fa_not_ru': {rid: fa_roots[rid] for rid in fa_set - ru_set},
    }
    return gaps


def scan_derivative_gaps(db):
    """Find entries with zero derivatives."""
    en_with = set(r[0] for r in db.execute(
        "SELECT DISTINCT entry_id FROM a4_derivatives WHERE entry_id IS NOT NULL AND entry_id != ''").fetchall())
    en_all = set(r[0] for r in db.execute("SELECT entry_id FROM a1_entries").fetchall())
    return en_all - en_with


def scan_crossref_gaps(db):
    """Find entries with zero cross-references."""
    linked = set()
    for r in db.execute("SELECT DISTINCT from_id FROM a5_cross_refs WHERE from_id IS NOT NULL").fetchall():
        linked.add(r[0])
    for r in db.execute("SELECT DISTINCT to_id FROM a5_cross_refs WHERE to_id IS NOT NULL").fetchall():
        linked.add(r[0])
    en_all = set(r[0] for r in db.execute("SELECT entry_id FROM a1_entries").fetchall())
    return en_all - linked


def scan_network_gaps(db):
    """Find entries with no network assignment."""
    with_net = set(r[0] for r in db.execute(
        "SELECT entry_id FROM a1_entries WHERE network_id IS NOT NULL AND network_id != ''").fetchall())
    en_all = set(r[0] for r in db.execute("SELECT entry_id FROM a1_entries").fetchall())
    return en_all - with_net


def scan_dimension_gaps(db):
    """Show dimension edge distribution and identify sparse dimensions."""
    dims = db.execute("SELECT dimension, COUNT(*) FROM term_dimensions GROUP BY dimension ORDER BY COUNT(*) DESC").fetchall()
    return dims


# ═══════════════════════════════════════════════════════════════════════════════
# al-Ikhlas (KERNEL) — SELF-CORRECTION SCANS
# ═══════════════════════════════════════════════════════════════════════════════

def scan_sem_review(db):
    """Find SEM_REVIEW entries scored above the cap (7)."""
    violations = []

    # EN
    for r in db.execute("""SELECT entry_id, en_term, score, foundation_ref FROM a1_entries
                          WHERE LOWER(foundation_ref) LIKE '%sem_review%' AND score > 7""").fetchall():
        violations.append(('EN', r[0], r[1], r[2], r[3][:100] if r[3] else ''))

    # RU
    for r in db.execute("""SELECT запись_id, рус_термин, балл, основание FROM [a1_записи]
                          WHERE LOWER(основание) LIKE '%sem_review%' AND балл > 7""").fetchall():
        violations.append(('RU', r[0], r[1], r[2], r[3][:100] if r[3] else ''))

    return violations


def scan_competing_roots(db):
    """Find entries where multiple roots produce the same consonant frame.

    If root_letters map to the same Russian/English consonants as another root,
    the entry may be assigned to the wrong root (like ХОЗЯИН: حزن vs خزن both → Х-З-Н).
    """
    # Build consonant-frame map for all roots in use
    # Group entries by their downstream consonant pattern
    candidates = []

    # For RU: group by рус_термин consonant skeleton
    ru_entries = db.execute("""SELECT запись_id, рус_термин, корень_id, корневые_буквы, балл
                              FROM [a1_записи]
                              WHERE корень_id IS NOT NULL AND корень_id != ''""").fetchall()

    # Build root_id → root_letters map
    root_map = {}
    for r in ru_entries:
        if r[2] and r[3]:
            root_map[r[2]] = r[3]

    # Find roots with identical consonant counts (potential confusion pairs)
    from collections import Counter
    letter_groups = defaultdict(list)
    for rid, letters in root_map.items():
        # Normalize: strip diacritics, get base letters
        base = letters.replace('-', '').replace(' ', '')
        letter_groups[len(base)].append((rid, letters))

    # For now, report entries that share root_letters length with other roots
    # More sophisticated: actual phonetic output comparison
    return candidates


def scan_shared_root_entries(db):
    """Find root_ids used by multiple entries — these should have cross-refs."""
    root_counts = db.execute("""
        SELECT root_id, COUNT(*) as cnt, GROUP_CONCAT(entry_id || ':' || en_term, ', ')
        FROM a1_entries
        WHERE root_id IS NOT NULL AND root_id != ''
        GROUP BY root_id HAVING cnt > 1
        ORDER BY cnt DESC
    """).fetchall()

    # Check which of these already have cross-refs
    missing_xrefs = []
    for root_id, count, entries in root_counts:
        entry_ids = [e.split(':')[0] for e in entries.split(', ')]
        # Check if cross-refs exist between these entries
        has_xref = False
        for eid in entry_ids:
            xref = db.execute("""SELECT COUNT(*) FROM a5_cross_refs
                                WHERE (from_id = ? OR to_id = ?) AND link_type = 'SAME_ROOT'""",
                              (eid, eid)).fetchone()[0]
            if xref > 0:
                has_xref = True
                break
        if not has_xref:
            missing_xrefs.append((root_id, count, entries))

    return missing_xrefs


# ═══════════════════════════════════════════════════════════════════════════════
# ENFORCEMENT — Apply caps
# ═══════════════════════════════════════════════════════════════════════════════

def enforce_sem_caps(db):
    """Cap SEM_REVIEW entries at 7. Returns count of entries modified."""
    # EN
    en_count = db.execute("""UPDATE a1_entries SET score = 7
                            WHERE LOWER(foundation_ref) LIKE '%sem_review%' AND score > 7""").rowcount

    # RU
    ru_count = db.execute("""UPDATE [a1_записи] SET балл = 7
                            WHERE LOWER(основание) LIKE '%sem_review%' AND балл > 7""").rowcount

    db.commit()
    return en_count, ru_count


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def report_gaps(db):
    print("=" * 70)
    print("al-Qamar (INDEX) — GAP SCAN")
    print("=" * 70)

    # Siblings
    gaps = scan_sibling_gaps(db)
    print("\n  SIBLING GAPS:")
    for key, data in gaps.items():
        src, tgt = key.split('_not_')
        print("    {} roots NOT in {}: {} (auto-pop candidates)".format(src.upper(), tgt.upper(), len(data)))

    # Derivatives
    deriv_gaps = scan_derivative_gaps(db)
    print("\n  DERIVATIVE GAPS:")
    print("    EN entries with 0 derivatives: {}".format(len(deriv_gaps)))

    # Cross-refs
    xref_gaps = scan_crossref_gaps(db)
    print("\n  CROSS-REF GAPS:")
    print("    EN entries with 0 cross-refs: {}".format(len(xref_gaps)))

    # Networks
    net_gaps = scan_network_gaps(db)
    print("\n  NETWORK GAPS:")
    print("    EN entries with no network: {}".format(len(net_gaps)))

    # Dimensions
    dims = scan_dimension_gaps(db)
    print("\n  DIMENSION EDGES:")
    for dim, count in dims:
        print("    {}: {}".format(dim, count))

    # Shared roots without cross-refs
    shared = scan_shared_root_entries(db)
    print("\n  SHARED ROOTS WITHOUT CROSS-REFS: {}".format(len(shared)))
    for rid, cnt, entries in shared[:10]:
        print("    {} ({} entries): {}".format(rid, cnt, entries[:80]))

    # Total auto-pop potential
    total_sibling = sum(len(v) for v in gaps.values())
    total = total_sibling + len(deriv_gaps) + len(xref_gaps) + len(shared)
    print("\n  TOTAL AUTO-POPULATION POTENTIAL: ~{} new rows".format(total))


def report_corrections(db):
    print("=" * 70)
    print("al-Ikhlas (KERNEL) — CORRECTION SCAN")
    print("=" * 70)

    violations = scan_sem_review(db)
    print("\n  SEM_REVIEW ENTRIES ABOVE CAP (7):")
    print("    Total violations: {}".format(len(violations)))
    for lang, eid, term, score, foundation in violations[:10]:
        print("    [{}] #{} {} (score {})".format(lang, eid, term, score))
    if len(violations) > 10:
        print("    ... and {} more".format(len(violations) - 10))


def report_siblings(db):
    print("=" * 70)
    print("SIBLING GAP DETAILS")
    print("=" * 70)

    gaps = scan_sibling_gaps(db)
    for key, data in gaps.items():
        if not data:
            continue
        src, tgt = key.split('_not_')
        print("\n  {} → {} ({} candidates):".format(src.upper(), tgt.upper(), len(data)))
        for i, (rid, (term, eid)) in enumerate(sorted(data.items())[:20]):
            print("    {} — {} (#{})".format(rid, term, eid))
        if len(data) > 20:
            print("    ... and {} more".format(len(data) - 20))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 uslap_autopop.py [gaps|corrections|siblings|sem_review|roots_check|full|enforce_caps]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    db = get_db()

    if cmd == 'gaps':
        report_gaps(db)
    elif cmd == 'corrections':
        report_corrections(db)
    elif cmd == 'siblings':
        report_siblings(db)
    elif cmd == 'sem_review':
        violations = scan_sem_review(db)
        print("SEM_REVIEW violations (score > 7): {}".format(len(violations)))
        for lang, eid, term, score, foundation in violations:
            print("  [{}] #{} {} — score {} — {}...".format(lang, eid, term, score, foundation[:80]))
    elif cmd == 'roots_check':
        shared = scan_shared_root_entries(db)
        print("Shared roots without SAME_ROOT cross-refs: {}".format(len(shared)))
        for rid, cnt, entries in shared:
            print("  {} ({} entries): {}".format(rid, cnt, entries))
    elif cmd == 'full':
        report_gaps(db)
        print()
        report_corrections(db)
    elif cmd == 'enforce_caps':
        en_count, ru_count = enforce_sem_caps(db)
        print("ENFORCED SEM_REVIEW CAPS:")
        print("  EN entries capped to 7: {}".format(en_count))
        print("  RU entries capped to 7: {}".format(ru_count))
        print("  Total: {}".format(en_count + ru_count))
    else:
        print("Unknown command: {}".format(cmd))
        sys.exit(1)

    db.close()


if __name__ == '__main__':
    main()
