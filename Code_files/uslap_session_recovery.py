#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP SESSION RECOVERY — Extract all root assignments, phonetic chains,
and write operations from archived session logs. Diff against live DB.
Find lost work.

Usage:
    python3 uslap_session_recovery.py scan      — extract all assignments from sessions
    python3 uslap_session_recovery.py diff       — compare extracted vs live DB
    python3 uslap_session_recovery.py report     — full report of lost work
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import json
import re
import os
import glob
import sys
from collections import defaultdict

DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"
SESSION_DIR = os.path.expanduser("~/.claude/projects/-Users-mmsetubal-Documents-USLaP-workplace")

# Patterns to extract concrete assignments
# Match: root_id=R123, root_id=T_BITIG45, root_id='R123'
RE_ROOT_ASSIGN = re.compile(
    r"""(?:root_id|ROOT_ID|root)\s*[=:]\s*['"]?((?:R\d+|T_?(?:BITIG)?\d+|T\d+))\b""",
    re.IGNORECASE
)

# Match phonetic chains like: ب→V(S09), ر→R(S15)
RE_CHAIN = re.compile(
    r"""([^\s,]+→[^\s,]+\(S\d{2}\)(?:\s*,\s*[^\s,]+→[^\s,]+\(S\d{2}\))*)""",
)

# Match ORIG2 chains
RE_ORIG2_CHAIN = re.compile(
    r"""ORIG2:\s*(\S+)\s*→\s*(?:skeleton\s+)?(\S+)""",
)

# Match RU term assignments: КАВАРДАК → root, or term=КАВАРДАК
RE_RU_TERM = re.compile(
    r"""([А-ЯЁ]{2,20})\s*(?:→|root_id[=:]\s*|assigned\s+)['"]?((?:R\d+|T_?\w*\d+))""",
    re.IGNORECASE
)

# Match EN term assignments
RE_EN_TERM = re.compile(
    r"""([A-Z]{2,20})\s*(?:→|root_id[=:]\s*|assigned\s+|root\s+)['"]?((?:R\d+|T_?\w*\d+))""",
)

# Match INSERT/UPDATE with entry_id and root
RE_SQL_WRITE = re.compile(
    r"""(?:INSERT|UPDATE).*?(?:root_id|root_letters)\s*[=,]\s*['"]?([^'",\s]+)""",
    re.IGNORECASE
)

# Match write_gate entries
RE_WRITE_GATE = re.compile(
    r"""(?:gate_id|write.gate).*?(\d+).*?(?:VERIFIED|WRITTEN|ANALYSED)""",
    re.IGNORECASE
)


def scan_sessions():
    """Extract all root assignments from all session files."""
    files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl")))
    print(f"Scanning {len(files)} session files...")

    all_assignments = []  # (session_id, term, root_id, chain, source_line_hint)
    all_chains = {}       # term -> [chains found]
    all_writes = []       # (session_id, sql_snippet)

    for filepath in files:
        session_id = os.path.basename(filepath).replace('.jsonl', '')[:12]
        size_mb = os.path.getsize(filepath) / 1024 / 1024

        term_roots = {}  # term -> root found in this session
        term_chains = {} # term -> chain found in this session

        try:
            with open(filepath, 'r', errors='ignore') as fh:
                for line_num, line in enumerate(fh):
                    # Find RU term → root assignments
                    for m in RE_RU_TERM.finditer(line):
                        term, root = m.group(1), m.group(2)
                        if len(term) >= 3:  # Skip noise
                            term_roots[term] = root

                    # Find EN term → root assignments
                    for m in RE_EN_TERM.finditer(line):
                        term, root = m.group(1), m.group(2)
                        if len(term) >= 3 and term not in ('INSERT', 'UPDATE', 'SELECT', 'DELETE',
                            'FROM', 'WHERE', 'INTO', 'TABLE', 'CREATE', 'ALTER', 'DROP',
                            'TEXT', 'INTEGER', 'NULL', 'PASS', 'FAIL', 'TRUE', 'FALSE',
                            'ROOT', 'ORIG', 'TYPE', 'NONE', 'BITIG', 'KASHGARI'):
                            term_roots[term] = root

                    # Find phonetic chains
                    for m in RE_CHAIN.finditer(line):
                        chain = m.group(1)
                        # Try to find which term this chain belongs to
                        # Look for a term near the chain in the same line
                        for tm in RE_RU_TERM.finditer(line):
                            term_chains[tm.group(1)] = chain
                        for tm in RE_EN_TERM.finditer(line):
                            t = tm.group(1)
                            if t not in ('INSERT', 'UPDATE', 'SELECT', 'DELETE', 'FROM',
                                'WHERE', 'INTO', 'TABLE', 'ROOT', 'ORIG', 'TYPE'):
                                term_chains[t] = chain

                    # Find ORIG2 chains
                    for m in RE_ORIG2_CHAIN.finditer(line):
                        term_name, skeleton = m.group(1), m.group(2)
                        term_upper = term_name.upper()
                        if len(term_upper) >= 3:
                            term_chains[term_upper] = f"ORIG2: {term_name} → {skeleton}"

        except Exception as e:
            print(f"  ERROR reading {filepath}: {e}")
            continue

        # Collect results
        for term, root in term_roots.items():
            chain = term_chains.get(term, '')
            all_assignments.append({
                'session': session_id,
                'term': term,
                'root_id': root,
                'chain': chain,
            })

        if term_roots:
            print(f"  {session_id} ({size_mb:.1f}MB): {len(term_roots)} terms, {len(term_chains)} chains")

    print(f"\nTotal extracted: {len(all_assignments)} term→root assignments")
    return all_assignments


def diff_against_db(assignments):
    """Compare extracted assignments against live DB."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Build lookup of current DB state
    db_state = {}

    # Entries (unified)
    c.execute("SELECT entry_id, en_term, ru_term, fa_term, root_id, root_letters, phonetic_chain FROM entries")
    for row in c.fetchall():
        eid, en, ru, fa, rid, rl, pc = row
        if en: db_state[en.upper()] = {'entry_id': eid, 'root_id': rid, 'root_letters': rl, 'chain': pc, 'table': 'entries'}
        if ru: db_state[ru.upper()] = {'entry_id': eid, 'root_id': rid, 'root_letters': rl, 'chain': pc, 'table': 'entries'}

    # European
    c.execute("SELECT entry_id, term, root_id, root_letters, phonetic_chain FROM european_a1_entries")
    for row in c.fetchall():
        eid, term, rid, rl, pc = row
        if term: db_state[term.upper()] = {'entry_id': eid, 'root_id': rid, 'root_letters': rl, 'chain': pc, 'table': 'eu'}

    # Bitig
    c.execute("SELECT entry_id, orig2_term, root_letters, phonetic_chain FROM bitig_a1_entries")
    for row in c.fetchall():
        eid, term, rl, pc = row
        if term: db_state[term.upper()] = {'entry_id': eid, 'root_id': None, 'root_letters': rl, 'chain': pc, 'table': 'bitig'}

    conn.close()

    # Categorize
    lost_work = []       # Was in session, NOT in DB or DB has different/no root
    confirmed = []       # Session agrees with DB
    conflicts = []       # Session has different root than DB
    not_in_db = []       # Term not found in DB at all

    seen_terms = set()

    for assign in assignments:
        term = assign['term'].upper()
        if term in seen_terms:
            continue  # Skip duplicates, keep first (most sessions)
        seen_terms.add(term)

        if term in db_state:
            db = db_state[term]
            if db['root_id'] and db['root_id'] == assign['root_id']:
                confirmed.append(assign)
            elif db['root_id'] is None or db['root_id'] == '':
                lost_work.append({**assign, 'db_state': 'NO_ROOT', 'db_entry_id': db['entry_id']})
            elif db['root_id'] != assign['root_id']:
                conflicts.append({**assign, 'db_root': db['root_id'], 'db_entry_id': db['entry_id']})
            else:
                confirmed.append(assign)
        else:
            not_in_db.append(assign)

    return {
        'lost_work': lost_work,
        'confirmed': confirmed,
        'conflicts': conflicts,
        'not_in_db': not_in_db,
    }


def report():
    """Full report: scan + diff + output."""
    print("=" * 80)
    print("USLaP SESSION RECOVERY REPORT")
    print("=" * 80)

    # Scan
    assignments = scan_sessions()

    # Diff
    print("\n" + "=" * 80)
    print("DIFFING AGAINST LIVE DB...")
    print("=" * 80)
    results = diff_against_db(assignments)

    # Report: Lost Work
    print(f"\n{'=' * 80}")
    print(f"LOST WORK: {len(results['lost_work'])} entries have session analysis but NO root in DB")
    print(f"{'=' * 80}")
    for item in sorted(results['lost_work'], key=lambda x: x['term']):
        print(f"  {item['term']:20s} session_root={item['root_id']:12s} chain={item.get('chain', '')[:50]}")

    # Report: Conflicts
    print(f"\n{'=' * 80}")
    print(f"CONFLICTS: {len(results['conflicts'])} entries have DIFFERENT root in DB vs session")
    print(f"{'=' * 80}")
    for item in sorted(results['conflicts'], key=lambda x: x['term']):
        print(f"  {item['term']:20s} session={item['root_id']:10s} vs DB={item['db_root']:10s}")

    # Report: Confirmed
    print(f"\n{'=' * 80}")
    print(f"CONFIRMED: {len(results['confirmed'])} entries match between session and DB")
    print(f"{'=' * 80}")

    # Report: Not in DB
    print(f"\n{'=' * 80}")
    print(f"NOT IN DB: {len(results['not_in_db'])} terms found in sessions but not in any DB table")
    print(f"{'=' * 80}")
    for item in sorted(results['not_in_db'], key=lambda x: x['term'])[:30]:
        print(f"  {item['term']:20s} session_root={item['root_id']:12s}")
    if len(results['not_in_db']) > 30:
        print(f"  ... and {len(results['not_in_db']) - 30} more")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Total unique terms found in sessions: {len(results['lost_work']) + len(results['confirmed']) + len(results['conflicts']) + len(results['not_in_db'])}")
    print(f"  LOST (in session, no root in DB):     {len(results['lost_work'])}")
    print(f"  CONFLICTS (different root):            {len(results['conflicts'])}")
    print(f"  CONFIRMED (matches DB):                {len(results['confirmed'])}")
    print(f"  NOT IN DB (term missing entirely):     {len(results['not_in_db'])}")

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 uslap_session_recovery.py scan    — extract assignments")
        print("  python3 uslap_session_recovery.py diff    — compare vs DB")
        print("  python3 uslap_session_recovery.py report  — full report")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'scan':
        scan_sessions()
    elif cmd == 'diff':
        assignments = scan_sessions()
        results = diff_against_db(assignments)
        print(f"\nLost: {len(results['lost_work'])} | Conflicts: {len(results['conflicts'])} | Confirmed: {len(results['confirmed'])} | Not in DB: {len(results['not_in_db'])}")
    elif cmd == 'report':
        report()
    else:
        print(f"Unknown command: {cmd}")
