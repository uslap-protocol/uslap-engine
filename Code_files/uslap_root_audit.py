#!/usr/bin/env python3
"""
USLaP Root Audit — Letter→Root Contamination Scanner

For every entry with root_letters in the DB:
1. Runs compute_root_meaning() on the root
2. Compares the letter computation against the stored aa_word / orig_meaning
3. Flags entries where stored meaning contradicts letter computation
4. Outputs a report of all contaminated entries

Usage:
    python3 Code_files/uslap_root_audit.py                # full audit
    python3 Code_files/uslap_root_audit.py --table entries # audit one table
    python3 Code_files/uslap_root_audit.py --root ق-ر-ش   # audit one root
    python3 Code_files/uslap_root_audit.py --fix           # show fix suggestions
"""

import sys
import os
import sqlite3
import re
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')

# Dictionary contamination markers — if aa_word contains these,
# it was likely written from a dictionary, not from letters
DICT_MARKERS = [
    'to gather', 'to collect', 'to press', 'to cut', 'to strike',
    'to pull', 'to push', 'to take', 'to give', 'to make',
    'to put', 'to throw', 'to draw', 'to hold', 'to carry',
    'to bring', 'to send', 'to come', 'to go', 'to turn',
    'to stand', 'to sit', 'to lie', 'to fall', 'to rise',
    'to open', 'to close', 'to break', 'to bend', 'to twist',
    'to tie', 'to bind', 'to join', 'to split', 'to mix',
    'to cover', 'to fill', 'to pour', 'to flow', 'to blow',
    'to burn', 'to shine', 'to grow', 'to eat', 'to drink',
    'to bite', 'to suck', 'to spit', 'to breathe', 'to smell',
    'to see', 'to hear', 'to feel', 'to touch', 'to taste',
]

# Known contaminated meaning patterns
CONTAMINATED_PATTERNS = [
    # Dictionary-style definitions that DON'T come from letter computation
    r'to \w+ and to \w+',  # "to X and to Y" = dictionary phrasing
    r'a place where',       # geographic definitions
    r'one who \w+s',        # agent-noun definitions
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def compute_for_root(root_letters):
    """Run compute_root_meaning on a root string like ق-ر-ش"""
    try:
        from amr_alphabet import compute_root_meaning, compute_root_meaning_text
        result = compute_root_meaning(root_letters)
        text = compute_root_meaning_text(root_letters)
        return result, text
    except Exception as e:
        return None, f"ERROR: {e}"


def extract_semantic_core(computation):
    """Extract the semantic core from computation result"""
    if computation and isinstance(computation, dict):
        return computation.get('semantic_core', '')
    return ''


def check_alignment(aa_word, computation_text, semantic_core):
    """
    Check if the stored aa_word aligns with the letter computation.
    Returns: (aligned: bool, issues: list[str])
    """
    if not aa_word or not computation_text:
        return True, []  # Can't check, skip

    issues = []
    ar_lower = aa_word.lower()

    # Check 1: Does aa_word already contain the computation?
    # If it has the letter=CONCEPT format, it's already computed
    if '=SPEECH' in aa_word or '=MOVEMENT' in aa_word or '=ORIGIN' in aa_word:
        return True, []  # Already letter-computed

    # Check 2: Dictionary contamination markers
    for marker in DICT_MARKERS:
        if marker in ar_lower:
            # Check if this dictionary meaning aligns with the semantic core
            issues.append(f"DICT_MARKER: '{marker}' found — may be dictionary-derived, not letter-computed")
            break

    # Check 3: Pattern-based contamination
    for pattern in CONTAMINATED_PATTERNS:
        if re.search(pattern, ar_lower):
            issues.append(f"DICT_PATTERN: matches '{pattern}'")
            break

    # Check 4: Does the aa_word contain ANY of the semantic core concepts?
    if semantic_core:
        core_parts = [p.strip() for p in semantic_core.split('+')]
        found_any = False
        for part in core_parts:
            part_clean = part.strip().lower()
            if part_clean and part_clean in ar_lower:
                found_any = True
                break
        if not found_any and len(core_parts) >= 2:
            issues.append(f"MISALIGNED: aa_word doesn't mention any of [{semantic_core}]")

    aligned = len(issues) == 0
    return aligned, issues


def audit_entries_table(conn, target_root=None):
    """Audit the main entries table"""
    results = []

    if target_root:
        rows = conn.execute(
            "SELECT entry_id, en_term, aa_word, root_letters FROM entries WHERE root_letters = ?",
            (target_root,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT entry_id, en_term, aa_word, root_letters FROM entries WHERE root_letters IS NOT NULL AND root_letters != ''"
        ).fetchall()

    for row in rows:
        root = row['root_letters']
        if not root or '-' not in root:
            continue

        computation, comp_text = compute_for_root(root)
        semantic_core = extract_semantic_core(computation)

        aligned, issues = check_alignment(row['aa_word'] or '', comp_text, semantic_core)

        if not aligned:
            results.append({
                'table': 'entries',
                'entry_id': row['entry_id'],
                'en_term': row['en_term'] or '',
                'aa_word': row['aa_word'] or '',
                'root': root,
                'computation': comp_text,
                'semantic_core': semantic_core,
                'issues': issues,
            })

    return results


def audit_child_entries(conn, target_root=None):
    """Audit child_entries table"""
    results = []

    if target_root:
        rows = conn.execute(
            "SELECT child_id, shell_name, orig_meaning, orig_root, operation_role FROM child_entries WHERE orig_root = ?",
            (target_root,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT child_id, shell_name, orig_meaning, orig_root, operation_role FROM child_entries WHERE orig_root IS NOT NULL AND orig_root != ''"
        ).fetchall()

    for row in rows:
        root = row['orig_root']
        if not root or '-' not in root:
            continue

        computation, comp_text = compute_for_root(root)
        semantic_core = extract_semantic_core(computation)

        aligned, issues = check_alignment(row['orig_meaning'] or '', comp_text, semantic_core)

        if not aligned:
            results.append({
                'table': 'child_entries',
                'entry_id': row['child_id'],
                'en_term': row['shell_name'] or '',
                'aa_word': row['orig_meaning'] or '',
                'root': root,
                'computation': comp_text,
                'semantic_core': semantic_core,
                'issues': issues,
            })

    return results


def print_report(results, show_fix=False):
    """Print the audit report"""
    if not results:
        print("✓ NO CONTAMINATION FOUND")
        return

    # Group by root
    by_root = {}
    for r in results:
        root = r['root']
        if root not in by_root:
            by_root[root] = []
        by_root[root].append(r)

    print(f"\n{'='*70}")
    print(f"ROOT AUDIT REPORT — {len(results)} flagged entries across {len(by_root)} roots")
    print(f"{'='*70}\n")

    for root, entries in sorted(by_root.items(), key=lambda x: -len(x[1])):
        comp_text = entries[0]['computation']
        semantic = entries[0]['semantic_core']

        print(f"ROOT: {root} — LETTERS COMPUTE: {comp_text}")
        print(f"  SEMANTIC CORE: {semantic}")
        print(f"  FLAGGED ENTRIES: {len(entries)}")
        print()

        for e in entries:
            print(f"  [{e['table']}] #{e['entry_id']} {e['en_term']}")
            print(f"    STORED:   {e['aa_word'][:120]}")
            for issue in e['issues']:
                print(f"    ⚠ {issue}")

            if show_fix:
                print(f"    FIX:  Replace aa_word/orig_meaning with letter computation:")
                print(f"          {comp_text}")
            print()

        print(f"  {'-'*60}\n")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total flagged:      {len(results)}")
    print(f"Unique roots:       {len(by_root)}")
    print(f"  entries table:    {sum(1 for r in results if r['table'] == 'entries')}")
    print(f"  child_entries:    {sum(1 for r in results if r['table'] == 'child_entries')}")

    # Count by issue type
    issue_counts = {}
    for r in results:
        for issue in r['issues']:
            itype = issue.split(':')[0]
            issue_counts[itype] = issue_counts.get(itype, 0) + 1

    print(f"\nIssue breakdown:")
    for itype, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
        print(f"  {itype}: {count}")


def apply_corrections(conn, results, dry_run=True):
    """
    Batch-correct flagged entries by replacing dictionary meanings
    with letter computation. Preserves the AA word FORM (e.g. قُرَيْشٍ),
    replaces only the meaning portion.

    Strategy:
    - If aa_word has format "WORD / transliteration / dictionary meaning"
      → replace "dictionary meaning" with letter computation
    - If aa_word is just a bare AA word (e.g. حَرَام)
      → append the computation after it
    - If orig_meaning (child_entries) → replace entirely with computation

    Args:
        dry_run: if True, only print what would change. If False, execute.
    """
    corrected = 0
    skipped = 0
    errors = 0

    for r in results:
        entry_id = r['entry_id']
        table = r['table']
        old_value = r['aa_word']
        comp_text = r['computation']
        root = r['root']

        if not comp_text or 'ERROR' in comp_text:
            skipped += 1
            continue

        # Build the new value
        if table == 'entries':
            # Parse existing aa_word format
            parts = old_value.split(' / ')
            if len(parts) >= 3:
                # Format: "WORD / transliteration / old_meaning"
                # Keep word + transliteration, replace meaning
                new_value = f"{parts[0]} / {parts[1]} / {comp_text}"
            elif len(parts) == 2:
                # Format: "WORD / transliteration"
                new_value = f"{parts[0]} / {parts[1]} / {comp_text}"
            else:
                # Bare word — append computation
                new_value = f"{old_value} / {comp_text}"

            if dry_run:
                print(f"  [{table}] #{entry_id}: {old_value[:80]}")
                print(f"    → {new_value[:80]}")
            else:
                try:
                    conn.execute(
                        "UPDATE entries SET aa_word = ? WHERE entry_id = ?",
                        (new_value, entry_id)
                    )
                    corrected += 1
                except Exception as e:
                    print(f"  ERROR [{table}] #{entry_id}: {e}")
                    errors += 1

        elif table == 'child_entries':
            # Replace orig_meaning with computation
            new_value = comp_text

            if dry_run:
                print(f"  [{table}] #{entry_id}: {old_value[:80]}")
                print(f"    → {new_value[:80]}")
            else:
                try:
                    conn.execute(
                        "UPDATE child_entries SET orig_meaning = ? WHERE child_id = ?",
                        (new_value, entry_id)
                    )
                    corrected += 1
                except Exception as e:
                    print(f"  ERROR [{table}] #{entry_id}: {e}")
                    errors += 1

    if not dry_run:
        conn.commit()

    return corrected, skipped, errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description='USLaP Root Audit — Letter→Root Contamination Scanner')
    parser.add_argument('--table', help='Audit specific table (entries, child_entries)')
    parser.add_argument('--root', help='Audit specific root (e.g. ق-ر-ش)')
    parser.add_argument('--fix', action='store_true', help='Show fix suggestions')
    parser.add_argument('--apply', action='store_true', help='Apply corrections (replaces dictionary meanings with letter computation)')
    parser.add_argument('--dry-run', action='store_true', help='With --apply, show what would change without writing')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--limit', type=int, default=0, help='Limit output to N entries')
    args = parser.parse_args()

    conn = get_connection()
    all_results = []

    target_root = args.root

    if not args.table or args.table == 'entries':
        print("Auditing entries table...")
        results = audit_entries_table(conn, target_root)
        all_results.extend(results)
        print(f"  → {len(results)} flagged")

    if not args.table or args.table == 'child_entries':
        print("Auditing child_entries table...")
        results = audit_child_entries(conn, target_root)
        all_results.extend(results)
        print(f"  → {len(results)} flagged")

    if args.limit:
        all_results = all_results[:args.limit]

    if args.apply:
        dry = args.dry_run
        mode = "DRY RUN" if dry else "APPLYING"
        print(f"\n{'='*70}")
        print(f"LETTER ALIGNMENT CORRECTION — {mode}")
        print(f"{'='*70}\n")
        corrected, skipped, errors = apply_corrections(conn, all_results, dry_run=dry)
        print(f"\n{'='*70}")
        if dry:
            print(f"DRY RUN: {len(all_results)} entries would be corrected")
            print(f"  Skipped (no computation): {skipped}")
            print(f"Run without --dry-run to apply.")
        else:
            print(f"APPLIED: {corrected} corrected, {skipped} skipped, {errors} errors")
        print(f"{'='*70}")
    elif args.json:
        print(json.dumps(all_results, ensure_ascii=False, indent=2))
    else:
        print_report(all_results, show_fix=args.fix)

    conn.close()


if __name__ == '__main__':
    main()
