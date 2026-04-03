#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP SESSION INIT — compact state dump for LLM session start.

Prints ONLY what the LLM needs to begin work. No prose. No full lists.
Replaces: reading MEMORY.md + NEW_SESSION_PROMPT.md + running 10 queries.

Usage:
  python3 uslap_session_init.py              # compact state (default)
  python3 uslap_session_init.py --full       # include last 5 changes per table
  python3 uslap_session_init.py --changelog  # what changed since last session

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sys
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')


def get_conn():
    try:
        from uslap_db_connect import connect
        return connect(DB_PATH)
    except ImportError:
        return sqlite3.connect(DB_PATH)


def compact_state():
    """Print compact state — everything the LLM needs, nothing it doesn't."""
    conn = get_conn()
    c = conn.cursor()

    print("=" * 70)
    print("  USLaP SESSION INIT — COMPACT STATE")
    print("=" * 70)

    # ── SHAHADA ──
    try:
        c.execute("SELECT rule_text FROM protocol_immutable WHERE rule_id = 'P00'")
        row = c.fetchone()
        if row:
            print(f"\n  P00: {row[0]}")
    except:
        print("\n  P00: أَشْهَدُ أَنْ لَا إِلٰهَ إِلَّا اللّٰهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ اللّٰهِ")

    # ── CORE COUNTS ──
    print("\n  ── DATA ──")
    counts = {}
    table_queries = [
        ('EN', "SELECT COUNT(*) FROM entries WHERE en_term IS NOT NULL"),
        ('RU', "SELECT COUNT(*) FROM entries WHERE ru_term IS NOT NULL"),
        ('FA', "SELECT COUNT(*) FROM entries WHERE fa_term IS NOT NULL"),
        ('EU', "SELECT COUNT(*) FROM european_a1_entries"),
        ('LA', "SELECT COUNT(*) FROM latin_a1_entries"),
        ('BI', "SELECT COUNT(*) FROM bitig_a1_entries"),
        ('Diwan', "SELECT COUNT(*) FROM diwan_roots"),
        ('Roots', "SELECT COUNT(*) FROM roots"),
        ('A4', "SELECT COUNT(*) FROM a4_derivatives"),
        ('A5', "SELECT COUNT(*) FROM a5_cross_refs"),
        ('QWR', "SELECT COUNT(*) FROM quran_word_roots"),
        ('Index', "SELECT COUNT(*) FROM term_nodes"),
        ('QV', "SELECT COUNT(*) FROM qv_translation_register"),
        ('BL', "SELECT COUNT(*) FROM contamination_blacklist"),
        ('Body', "SELECT COUNT(*) FROM body_data"),
        ('DCR', "SELECT COUNT(*) FROM diwan_contamination_register"),
        ('Allah', "SELECT COUNT(*) FROM names_of_allah"),
    ]

    parts = []
    for label, query in table_queries:
        try:
            c.execute(query)
            n = c.fetchone()[0]
            counts[label] = n
            parts.append(f"{label}:{n}")
        except:
            parts.append(f"{label}:?")

    # Print in rows of 6
    for i in range(0, len(parts), 6):
        print(f"  {' | '.join(parts[i:i+6])}")

    # ── LAST IDs ──
    print("\n  ── LAST IDs ──")
    id_queries = [
        ('EN', "SELECT MAX(entry_id) FROM entries"),
        ('BI', "SELECT MAX(entry_id) FROM bitig_a1_entries"),
        ('Diwan', "SELECT MAX(diwan_id) FROM diwan_roots"),
        ('Root', "SELECT MAX(root_id) FROM roots"),
        ('EU', "SELECT MAX(entry_id) FROM european_a1_entries"),
        ('A4', "SELECT MAX(deriv_id) FROM a4_derivatives"),
    ]
    id_parts = []
    for label, query in id_queries:
        try:
            c.execute(query)
            val = c.fetchone()[0]
            id_parts.append(f"{label}={val}")
        except:
            id_parts.append(f"{label}=?")
    print(f"  {' | '.join(id_parts)}")

    # ── TRIGGERS ──
    print("\n  ── PROTECTION ──")
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
    trigger_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'auto_index_%'")
    auto_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_contamination_%'")
    contam_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_quf_%'")
    quf_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'diwan_roots_%'")
    diwan_count = c.fetchone()[0]

    print(f"  Triggers: {trigger_count} total ({contam_count} contamination, {quf_count} QUF, {auto_count} auto-index, {diwan_count} diwan)")
    print(f"  Auto-index: term_nodes populated on INSERT to 6 tables")
    print(f"  Write path: handler.write_entry() → 5-layer defence")

    # ── QUF STATUS (summary only) ──
    print("\n  ── QUF ──")
    quf_tables = ['entries', 'roots', 'bitig_a1_entries', 'european_a1_entries',
                   'latin_a1_entries', 'quran_word_roots']
    for table in quf_tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table} WHERE quf_pass IN (1, '1', 'TRUE', 'True', 'true')")
            passed = c.fetchone()[0]
            c.execute(f"SELECT COUNT(*) FROM {table}")
            total = c.fetchone()[0]
            pct = (passed / total * 100) if total > 0 else 0
            if pct < 100:
                print(f"  {table}: {passed}/{total} ({pct:.0f}%)")
        except:
            pass

    # ── COMPILER ──
    print("\n  ── COMPILER ──")
    try:
        c.execute("SELECT COUNT(*) FROM quran_word_roots")
        qwr = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT root) FROM quran_word_roots WHERE root IS NOT NULL AND root != ''")
        roots_mapped = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM quran_word_roots WHERE root IS NOT NULL AND root != ''")
        mapped = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT surah) FROM quran_word_roots")
        surahs = c.fetchone()[0]
        pct = (mapped / qwr * 100) if qwr > 0 else 0
        print(f"  {qwr} words | {roots_mapped} roots | {surahs} surahs | {pct:.1f}% coverage")
    except Exception as e:
        print(f"  (compiler: {e})")

    # ── TOOLS AVAILABLE ──
    print("\n  ── TOOLS (no LLM needed) ──")
    tools = [
        ("python3 uslap.py 'query'", "Runtime query"),
        ("python3 uslap.py --state", "Full state"),
        ("python3 uslap.py --quf-status", "QUF coverage"),
        ("python3 uslap.py --batch TABLE", "QUF batch"),
        ("python3 uslap_wash_gloss.py scan", "Gloss contamination scan"),
        ("python3 uslap_wash_gloss.py clean", "Gloss auto-clean"),
        ("python3 uslap_selfaudit.py", "Banned term scan"),
        ("python3 uslap_handler.py context [topic]", "Load reference"),
        ("python3 uslap_session_init.py --changelog", "Recent changes"),
    ]
    for cmd, desc in tools:
        print(f"  {cmd:48s} {desc}")

    # ── SEE_MS COUNT (pending re-reads) ──
    print("\n  ── PENDING WORK ──")
    try:
        c.execute("SELECT COUNT(*) FROM diwan_roots WHERE aa_gloss = 'SEE_MS'")
        see_ms = c.fetchone()[0]
        if see_ms > 0:
            print(f"  diwan_roots SEE_MS: {see_ms} entries need Arabic re-read from MS PNGs")
    except:
        pass

    try:
        c.execute("SELECT COUNT(*) FROM bitig_a1_entries WHERE diwan_source = 'DANKOFF'")
        dankoff = c.fetchone()[0]
        if dankoff > 0:
            print(f"  bitig_a1 DANKOFF: {dankoff} entries pending verification against Arabic MS")
    except:
        pass

    print()
    conn.close()


def changelog():
    """Show what changed recently — entries with recent created_date or modified_at."""
    conn = get_conn()
    c = conn.cursor()

    print("=" * 70)
    print("  USLaP CHANGELOG — RECENT CHANGES")
    print("=" * 70)

    # Check tables with date columns
    tables_with_dates = [
        ('entries', 'modified_at', 'entry_id', 'en_term'),
        ('entries', 'created_at', 'entry_id', 'en_term'),
        ('diwan_roots', 'created_date', 'diwan_id', 'headword'),
    ]

    for table, date_col, id_col, label_col in tables_with_dates:
        try:
            c.execute(f"SELECT {id_col}, {label_col}, {date_col} FROM {table} WHERE {date_col} IS NOT NULL ORDER BY {date_col} DESC LIMIT 10")
            rows = c.fetchall()
            if rows:
                print(f"\n  ── {table} (last 10 by {date_col}) ──")
                for r in rows:
                    print(f"  {r[0]:>6} | {str(r[1] or '')[:30]:30s} | {r[2]}")
        except Exception as e:
            pass

    # Count by date for diwan_roots
    try:
        c.execute("SELECT created_date, COUNT(*) FROM diwan_roots WHERE created_date IS NOT NULL GROUP BY created_date ORDER BY created_date DESC LIMIT 5")
        rows = c.fetchall()
        if rows:
            print(f"\n  ── diwan_roots by date ──")
            for date, count in rows:
                print(f"  {date}: +{count} entries")
    except:
        pass

    # Bitig entries count by diwan_source
    try:
        c.execute("SELECT diwan_source, COUNT(*) FROM bitig_a1_entries GROUP BY diwan_source")
        rows = c.fetchall()
        if rows:
            print(f"\n  ── bitig_a1 by source ──")
            for src, count in rows:
                print(f"  {src or 'NULL':20s}: {count}")
    except:
        pass

    print()
    conn.close()


def main():
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == '--changelog':
            changelog()
        elif flag == '--full':
            compact_state()
            changelog()
        else:
            print(__doc__)
    else:
        compact_state()


if __name__ == '__main__':
    main()
