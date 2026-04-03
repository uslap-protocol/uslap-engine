#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP — Universal System of Linguistic Accountability and Proof
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

DETERMINISTIC RUNTIME — NO LLM IN THE LOOP.

This is the single entry point for all USLaP operations.
Every output traces to the database. Zero training weights.
Run the same query twice → identical output.

Usage:
    python3 uslap.py "silk"                    # trace a word
    python3 uslap.py "explain R01"             # explain a root
    python3 uslap.py "compare ر-ح-م and م-ر-ح" # compare roots
    python3 uslap.py "tasrif ر-ح-م"            # AA تَصْرِيف — all forms
    python3 uslap.py "tasrif status"           # AA تَصْرِيف coverage
    python3 uslap.py "bitig tasrif status"     # BI تَصْرِيف coverage
    python3 uslap.py --tasrif ر-ح-م            # AA تَصْرِيف (flag form)
    python3 uslap.py --bitig-tasrif status     # BI تَصْرِيف (flag form)
    python3 uslap.py --quf entries 346         # QUF validation
    python3 uslap.py --quf-status              # QUF coverage
    python3 uslap.py --state                   # lattice state
    python3 uslap.py --batch entries            # batch QUF
    python3 uslap.py -i                        # interactive REPL
"""

# ═══════════════════════════════════════════════════════════════════════
# ZERO LLM IMPORTS — this file must NEVER import anthropic/openai/etc.
# The pipeline is: User → Python → SQLite → Python → User
# ═══════════════════════════════════════════════════════════════════════

import sys
import os
import argparse

# Add Code_files to path
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

DB_PATH = os.path.join(CODE_DIR, "uslap_database_v3.db")


def tasrif_route(text):
    """Route tasrif queries to amr_tasrif.py or amr_bitig_tasrif.py.

    Routes:
        tasrif status              → AA tasrif coverage
        tasrif <root>              → all forms of AA root
        tasrif pattern <code>      → explain pattern code
        tasrif broken_plurals      → broken plural listing
        bitig tasrif status        → BI tasrif coverage
        bitig tasrif <root>        → all forms of BI root
        bitig tasrif pattern <code> → explain BI pattern
        bitig tasrif harmony <word> → check BI vowel harmony
        bitig tasrif compound <w>  → analyze BI compound
    """
    import io
    import contextlib

    parts = text.strip().split()

    # Determine track: AA or BI
    if parts[0].lower() == 'bitig' and len(parts) >= 2 and parts[1].lower() == 'tasrif':
        track = 'bi'
        subparts = parts[2:]  # after "bitig tasrif"
    elif parts[0].lower() == 'tasrif':
        track = 'aa'
        subparts = parts[1:]  # after "tasrif"
    else:
        return None  # not a tasrif query

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if track == 'aa':
            from amr_tasrif import print_status, print_root_forms, print_pattern, print_broken_plurals
            if not subparts or subparts[0] == 'status':
                print_status()
            elif subparts[0] == 'broken_plurals':
                print_broken_plurals()
            elif subparts[0] == 'pattern' and len(subparts) >= 2:
                print_pattern(subparts[1])
            else:
                # Treat as root query
                print_root_forms(' '.join(subparts))
        else:
            from amr_bitig_tasrif import (get_status as bi_get_status,
                                          get_root_forms as bi_get_root,
                                          get_pattern_info as bi_get_pattern,
                                          check_harmony as bi_check_harmony,
                                          analyze_compound as bi_analyze_compound,
                                          analyze_word as bi_analyze_word)

            if not subparts or subparts[0] == 'status':
                stats = bi_get_status()
                print("=" * 60)
                print("بِيتِيك تَصْرِيف STATUS — BI Morphological Engine")
                print("=" * 60)
                for k, v in stats.items():
                    print(f"  {k}: {v}")
            elif subparts[0] == 'pattern' and len(subparts) >= 2:
                info = bi_get_pattern(subparts[1])
                if info:
                    print(f"BI PATTERN: {subparts[1]}")
                    print("-" * 50)
                    for k, v in info.items():
                        if v is not None:
                            print(f"  {k}: {v}")
                else:
                    print(f"Pattern '{subparts[1]}' not found in BI tasrif tables.")
            elif subparts[0] == 'harmony' and len(subparts) >= 2:
                result = bi_check_harmony(' '.join(subparts[1:]))
                print(f"VOWEL HARMONY: {' '.join(subparts[1:])}")
                print("-" * 50)
                for k, v in result.items():
                    print(f"  {k}: {v}")
            elif subparts[0] == 'compound' and len(subparts) >= 2:
                result = bi_analyze_compound(' '.join(subparts[1:]))
                print(f"COMPOUND ANALYSIS: {' '.join(subparts[1:])}")
                print("-" * 50)
                if isinstance(result, dict):
                    for k, v in result.items():
                        print(f"  {k}: {v}")
                elif isinstance(result, list):
                    for item in result:
                        print(f"  {item}")
            elif subparts[0] == 'analyze' and len(subparts) >= 2:
                result = bi_analyze_word(' '.join(subparts[1:]))
                print(f"BI ANALYSIS: {' '.join(subparts[1:])}")
                print("-" * 50)
                if result:
                    for k, v in result.items():
                        if v is not None:
                            print(f"  {k}: {v}")
                else:
                    print("  Not found.")
            else:
                # Treat as root query
                forms = bi_get_root(' '.join(subparts))
                if forms:
                    print(f"BI ROOT: {' '.join(subparts)} — {len(forms)} forms")
                    print("=" * 60)
                    for f in forms:
                        if isinstance(f, dict):
                            parts_out = [f"{k}={v}" for k, v in f.items() if v]
                            print(f"  {', '.join(parts_out)}")
                        else:
                            print(f"  {f}")
                else:
                    print(f"No forms found for BI root: {' '.join(subparts)}")

    return buf.getvalue()


def query(text):
    """Run a single query through the AMR pipeline. Returns formatted string.

    PRIORITY:
    1. Search DB. If found, return DB data.
    2. Compute via amr_dhakaa (handles ALL intents including tasrif).

    Fixed 2026-03-29: was going straight to think() and skipping
    handler.search(), which meant indexed entries (scholars, peoples,
    etc.) were never returned — only root hypotheses.

    Fixed 2026-04-02: tasrif now routes through dhakaa pipeline
    (perceive → reason → articulate) instead of bypass.
    """
    from uslap_handler import search

    # Step 1: Search the index FIRST
    search_result = search(text)

    if search_result['found'] and search_result['nodes']:
        # Found in DB — format and return the DB data
        # But ALSO run through think() for root computation
        # The DB data takes priority in the output
        lines = []

        # Group by source table
        by_table = {}
        for node in search_result['nodes']:
            tbl = node['source_table']
            if tbl not in by_table:
                by_table[tbl] = []
            by_table[tbl].append(node)

        lines.append("╔" + "═" * 58 + "╗")
        lines.append(f"║ DB RESULT: '{text}' — {len(search_result['nodes'])} matches")
        lines.append("╠" + "═" * 58 + "╣")

        for tbl, nodes in by_table.items():
            lines.append(f"║ [{tbl}]:")
            for n in nodes[:10]:  # Limit per table
                term = n['term'] if isinstance(n, dict) else n[1]
                score = n['score'] if isinstance(n, dict) else n[7]
                src_id = n['source_id'] if isinstance(n, dict) else n[5]
                lines.append(f"║   {term} (id={src_id}, score={score})")

        lines.append("╚" + "═" * 58 + "╝")

        db_output = '\n'.join(lines)

        # Step 2: Also run AMR computation for root analysis
        from amr_dhakaa import think
        result = think(text)
        amr_output = result['output']

        # Don't append "No entries found" if DB already returned results
        if 'No entries found' in amr_output:
            return db_output
        else:
            return db_output + '\n\n' + amr_output

    # Not found in DB — fall through to AMR computation only
    from amr_dhakaa import think
    result = think(text)
    return result['output']


def full_report(text):
    """Type-aware full report — delegates to uslap_full_report module."""
    from uslap_full_report import generate
    return generate(text)


def _full_report_old_DISABLED(text):
    """
    Type-aware deep search across ALL tables.
    Detects WHAT the term is and structures output accordingly.

    Types:
      SCHOLAR  → WHO → WORKS → LATTICE PRESENCE → CONTAMINATION
      PEOPLE   → ROOT → QUR'AN → OPERATION → CHRONOLOGY
      ROOT     → LETTERS → QUR'AN → DOWNSTREAM → INVERSIONS
      ENTRY    → ROOT → CHAIN → SIBLINGS → DETECTION
      GENERAL  → flat search all tables

    Usage: python3 uslap.py --full "ibn sina"
    """
    import sqlite3
    import unicodedata as _ud

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    def _to_plain(val):
        if val is None:
            return None
        return ''.join(c for c in _ud.normalize('NFD', str(val))
                       if _ud.category(c) != 'Mn').lower()

    conn.create_function("plain", 1, _to_plain)

    term = text.strip()
    term_lower = term.lower()

    # Build search patterns — must catch diacritical variants
    import unicodedata
    patterns = [f"%{term}%", f"%{term_lower}%"]
    # Strip Unicode diacritics (ī→i, ā→a, etc.)
    stripped = ''.join(c for c in unicodedata.normalize('NFD', term)
                       if unicodedata.category(c) != 'Mn')
    if stripped != term:
        patterns.append(f"%{stripped}%")
        patterns.append(f"%{stripped.lower()}%")
    # For multi-word queries, search the FULL phrase only — never split into
    # individual words. Splitting "ibn sina" into "ibn" and "sina" pulls in
    # every ibn-named scholar and anything with "sina" (Sinai, assassinate, etc.)

    # DIACRITICAL BRIDGE: user types "ibn sina", DB has "Ibn Sīnā".
    # Both spellings are TRUE. Neither is stripped or degraded.
    # We search using BOTH forms so either direction finds the other.
    #
    # This works for ALL words automatically — no hardcoded lookup needed.
    # The DB column values with diacritics are searched using a custom
    # SQLite function that checks if the plain form matches the diacritical form.
    import unicodedata as _ud

    def _to_plain(s):
        """Convert diacritical text to plain equivalent. ī→i, ā→a, etc."""
        if not s:
            return ''
        return ''.join(c for c in _ud.normalize('NFD', s)
                       if _ud.category(c) != 'Mn')

    # If the query is already plain (no diacritics), generate what the
    # diacritical form MIGHT look like — but we can't guess which letters
    # have diacritics. Instead, we register a SQLite function that strips
    # diacritics from DB values at query time for comparison only.
    # The DB values themselves are NEVER modified.
    def _sql_plain(val):
        """SQLite function: returns plain form of a diacritical string for comparison."""
        if val is None:
            return None
        return ''.join(c for c in _ud.normalize('NFD', str(val))
                       if _ud.category(c) != 'Mn').lower()

    lines = []
    lines.append("═" * 60)
    lines.append(f"FULL REPORT: '{term}'")
    lines.append("═" * 60)

    # Define all searchable tables with their columns
    SEARCH_TARGETS = [
        ('scholar_warnings', ['sc_code', 'scholar', 'aa_name', 'origin', 'century',
                               'primary_work', 'warning_content', 'key_contribution_to_lattice']),
        ('entries', ['entry_id', 'en_term', 'aa_word', 'root_letters', 'notes']),
        ('child_entries', ['child_id', 'shell_name', 'orig_meaning', 'operation_role',
                           'shell_meaning', 'orig_root', 'notes']),
        ('bitig_a1_entries', ['entry_id', 'orig2_term', 'ibn_sina_attestation',
                              'kashgari_attestation', 'navoi_attestation', 'notes']),
        ('chronology', ['id', 'date', 'era', 'event', 'orig_meaning', 'notes']),
        ('roots', ['root_id', 'root_letters', 'primary_meaning']),
        ('quran_word_roots', ['surah', 'ayah', 'aa_word', 'root', 'root_meaning']),
        ('body_data', ['body_id', 'subsystem', 'category', 'english', 'description',
                       'specific_data']),
        ('dp_register', ['dp_code', 'name', 'mechanism', 'example']),
        ('qv_translation_register', ['qv_id', 'root_letters', 'quranic_meaning',
                                      'corrupted_translation']),
        ('interception_register', ['int_id', 'root_letters', 'amr_meaning', 'lisan_word',
                                    'lisan_meaning', 'inversion_note']),
        ('m4_networks', ['orig_id', 'specific_data']),
        ('formula_scholars', ['scholar_id', 'scholar_name', 'contribution']),
        ('term_nodes', ['node_id', 'term', 'source_table', 'source_id']),
        ('kashgari_diwan_extract', ['orig2_headword', 'aa_gloss', 'section_type']),
        ('diwan_roots', ['headword', 'root_letters', 'aa_gloss', 'diwan_section', 'dialect_note']),
        ('kashgari_toc', ['arabic_title', 'english_title', 'root_type', 'notes']),
        ('diwan_contamination_register', ['diwan_headword', 'kashgari_aa_gloss',
                                           'operator_translation', 'corruption_type', 'what_was_severed']),
    ]

    total_found = 0

    for table, columns in SEARCH_TARGETS:
        try:
            # Build WHERE clause searching all text columns
            existing_cols = [row[1] for row in
                             conn.execute(f"PRAGMA table_info({table})").fetchall()]
            searchable = [c for c in columns if c in existing_cols]

            if not searchable:
                continue

            where_parts = []
            params = []
            # Build plain form of search term (strip diacritics for comparison)
            term_plain = _sql_plain_init(term_lower)
            for col in searchable:
                for pat in patterns:
                    # Match 1: exact LIKE (catches exact spelling)
                    where_parts.append(f"LOWER(CAST([{col}] AS TEXT)) LIKE ?")
                    params.append(pat.lower())
                    # Match 2: plain() comparison (catches diacritical variants)
                    # plain('Ibn Sīnā') = 'ibn sina' which matches user's 'ibn sina'
                    where_parts.append(f"plain(CAST([{col}] AS TEXT)) LIKE ?")
                    params.append(_sql_plain_init(pat))

            where_clause = ' OR '.join(where_parts)

            rows = conn.execute(
                f"SELECT * FROM [{table}] WHERE {where_clause} LIMIT 20",
                params
            ).fetchall()

            if rows:
                lines.append("")
                lines.append(f"── {table} ({len(rows)} found) ──")
                total_found += len(rows)

                for row in rows:
                    row_dict = dict(row)
                    # Print key fields
                    key_fields = [c for c in searchable if c in row_dict and row_dict[c]]
                    for kf in key_fields:
                        val = str(row_dict[kf])
                        if len(val) > 200:
                            val = val[:200] + '...'
                        lines.append(f"  {kf}: {val}")
                    lines.append("  ─ ─ ─")

        except Exception as e:
            pass  # Skip tables that don't exist or have errors

    lines.append("")
    lines.append("═" * 60)
    lines.append(f"TOTAL: {total_found} records across all tables")
    lines.append("═" * 60)

    conn.close()

    # Also run standard query for AMR computation
    standard = query(text)

    return '\n'.join(lines) + '\n\n' + standard


def quf_validate(table, row_id):
    """Run QUF validation on a single row."""
    from amr_quf import validate, _connect, TABLE_ID_MAP
    conn = _connect()
    id_col = TABLE_ID_MAP.get(table, 'rowid')
    try:
        row = conn.execute(f'SELECT * FROM "{table}" WHERE "{id_col}" = ?', (row_id,)).fetchone()
    except Exception:
        row = conn.execute(f'SELECT *, rowid FROM "{table}" WHERE rowid = ?', (row_id,)).fetchone()
    conn.close()

    if not row:
        return f"Row {row_id} not found in {table}"

    result = validate(dict(row), domain=table)

    lines = ["═" * 60]
    lines.append(f"QUF VALIDATION: {table} #{row_id}")
    lines.append("═" * 60)
    lines.append(f"  Q = {result['q']}")
    lines.append(f"  U = {result['u']}")
    lines.append(f"  F = {result['f']}")
    lines.append(f"  OVERALL: {'✓ PASS' if result['pass'] else '✗ FAIL'}")
    lines.append("─" * 60)
    for layer in result.get('layers', []):
        lr = layer['result']
        status = '✓' if lr['pass'] else '✗'
        lines.append(f"  {layer['name']}: Q={lr['q']} U={lr['u']} F={lr['f']} [{status}]")
        for ev in lr.get('q_evidence', []) + lr.get('u_evidence', []) + lr.get('f_evidence', []):
            lines.append(f"    {ev}")
    lines.append("═" * 60)
    return '\n'.join(lines)


def quf_status():
    """Show QUF coverage across all tables."""
    from amr_quf import _connect, DOMAIN_GATE_MAP
    conn = _connect()
    lines = ["═" * 60, "QUF COVERAGE STATUS", "═" * 60]
    for table in sorted(DOMAIN_GATE_MAP.keys()):
        try:
            total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            passed = conn.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = "TRUE"'
            ).fetchone()[0]
            pct = f'{passed*100//max(total,1)}%'
            lines.append(f"  {table:45s} {passed:>5}/{total:<5} {pct:>5}")
        except Exception:
            lines.append(f"  {table:45s}   [error]")
    conn.close()
    lines.append("═" * 60)
    return '\n'.join(lines)


def batch_quf(table, limit=0):
    """Batch re-validate a table."""
    from amr_quf import batch_validate
    return batch_validate(table, limit=limit)


def lattice_state():
    """Show lattice state summary."""
    from amr_nutq import format_lattice_summary
    return format_lattice_summary()


def interactive():
    """Interactive REPL — deterministic, no LLM."""
    print("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    print("USLaP — Deterministic Runtime")
    print("Every answer traces to 28 letters. Zero training weights.")
    print("Type 'exit' to quit. Type 'help' for commands.\n")

    from amr_dhakaa import think, get_context, suggest_next

    while True:
        try:
            user_input = input("uslap> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nوَدَاعًا")
            break

        if not user_input:
            continue
        if user_input in ('exit', 'quit', 'خُرُوج'):
            print("وَدَاعًا")
            break

        if user_input == 'help':
            print("  trace <word>        — trace a word to its AA root")
            print("  explain <root>      — explain a root (R01 or ر-ح-م)")
            print("  compare <a> and <b> — compare two roots")
            print("  search <term>       — search the lattice")
            print("  quf <table> <id>    — QUF validation")
            print("  quf status          — QUF coverage")
            print("  state               — lattice summary")
            print("  tasrif <root>       — AA تَصْرِيف (all forms of root)")
            print("  tasrif status       — AA تَصْرِيف coverage")
            print("  tasrif pattern <c>  — explain tasrif code")
            print("  bitig tasrif <root> — BI تَصْرِيف (all forms)")
            print("  bitig tasrif status — BI تَصْرِيف coverage")
            print("  DP10                — explain detection pattern")
            print("  keyword أَمْر        — explain keyword")
            print("  context             — show current focus")
            print("  suggest             — suggest next query")
            continue

        if user_input == 'context':
            ctx = get_context()
            print(f"  Focus: {ctx['focus_root']}")
            print(f"  History: {ctx['focus_history']}")
            print(f"  Queries: {ctx['query_count']}")
            continue

        if user_input == 'suggest':
            for s in suggest_next():
                print(f"  → {s}")
            continue

        if user_input == 'state':
            print(lattice_state())
            continue

        if user_input == 'quf status':
            print(quf_status())
            continue

        if user_input.startswith('quf '):
            parts = user_input.split()
            if len(parts) >= 3:
                print(quf_validate(parts[1], parts[2]))
            else:
                print("Usage: quf <table> <id>")
            continue

        # Check tasrif routing
        if user_input.lower().startswith('tasrif') or user_input.lower().startswith('bitig tasrif'):
            result = tasrif_route(user_input)
            if result is not None:
                print(result)
                continue

        # Default: run through think()
        result = think(user_input)
        print(result['output'])
        print()


def main():
    parser = argparse.ArgumentParser(
        description='USLaP — Deterministic Runtime (NO LLM)',
        epilog='بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
    )
    parser.add_argument('query', nargs='*', help='Query text')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Interactive REPL mode')
    parser.add_argument('--quf', nargs=2, metavar=('TABLE', 'ID'),
                        help='QUF validation: --quf entries 346')
    parser.add_argument('--quf-status', action='store_true',
                        help='Show QUF coverage')
    parser.add_argument('--state', action='store_true',
                        help='Show lattice state')
    parser.add_argument('--batch', metavar='TABLE',
                        help='Batch QUF re-validation')
    parser.add_argument('--batch-limit', type=int, default=0,
                        help='Limit batch rows')
    parser.add_argument('--full', action='store_true',
                        help='Full report: search ALL tables for term')
    parser.add_argument('--tasrif', nargs='*', metavar='ARG',
                        help='تَصْرِيف engine: --tasrif status | --tasrif ر-ح-م | --tasrif pattern FA3L')
    parser.add_argument('--bitig-tasrif', nargs='*', metavar='ARG',
                        help='BI تَصْرِيف engine: --bitig-tasrif status | --bitig-tasrif kor')

    args = parser.parse_args()

    if args.interactive:
        interactive()
        return 0

    if args.quf:
        print(quf_validate(args.quf[0], args.quf[1]))
        return 0

    if args.quf_status:
        print(quf_status())
        return 0

    if args.state:
        print(lattice_state())
        return 0

    if args.batch:
        result = batch_quf(args.batch, limit=args.batch_limit)
        print(f"{'═'*60}")
        print(f"BATCH QUF: {result.get('table', '?')}")
        print(f"  Total:     {result.get('total', 0)}")
        print(f"  Pass:      {result.get('pass', 0)}")
        print(f"  Fail:      {result.get('fail', 0)}")
        print(f"  Pass rate: {result.get('pass_rate', '?')}")
        print(f"{'═'*60}")
        return 0

    if args.tasrif is not None:
        tasrif_args = args.tasrif if args.tasrif else ['status']
        result = tasrif_route('tasrif ' + ' '.join(tasrif_args))
        if result:
            print(result)
        return 0

    if args.bitig_tasrif is not None:
        bt_args = args.bitig_tasrif if args.bitig_tasrif else ['status']
        result = tasrif_route('bitig tasrif ' + ' '.join(bt_args))
        if result:
            print(result)
        return 0

    if args.query and args.full:
        text = ' '.join(args.query)
        print(full_report(text))
        return 0

    if args.query:
        text = ' '.join(args.query)
        print(query(text))
        return 0

    # No args → interactive
    interactive()
    return 0


if __name__ == '__main__':
    sys.exit(main())

