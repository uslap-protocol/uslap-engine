#!/usr/bin/env python3
"""
USLaP V3 → V4 Migration — PK/FK enforcement
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Starts from a COPY of V3. Rebuilds tables that need PRIMARY KEY.
Adds FOREIGN KEY constraints on core tables.
Preserves ALL triggers, indexes, views.
Verifies row counts.

Usage:
    python3 Code_files/migrate_v3_to_v4.py check     # dry-run analysis
    python3 Code_files/migrate_v3_to_v4.py migrate    # execute migration
"""

import sqlite3
import shutil
import sys
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
V3_DB = os.path.join(BASE, "uslap_database_v3.db")
V4_DB = os.path.join(BASE, "uslap_database_v4.db")

# ============================================================================
# Tables that need PRIMARY KEY added/fixed
# Format: (table_name, pk_column, pk_type, needs_dedup)
# ============================================================================
PK_FIXES = [
    # Core tables (imported from Excel without PK)
    ("entries", "entry_id", "INTEGER", False),
    ("bitig_a1_entries", "entry_id", "TEXT", False),  # B001, B295, etc.
    ("a4_derivatives", "deriv_id", "TEXT", True),      # 2 dups: D977, D978
    ("a5_cross_refs", "xref_id", "TEXT", True),        # 9 dups: X100-X108

    # RU mirror tables
    ("a2_\u0438\u043c\u0435\u043d\u0430_\u0430\u043b\u043b\u0430\u0445\u0430", "\u0438\u043c\u044f_id", "TEXT", False),
    ("a3_\u043a\u043e\u0440\u0430\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435_\u0441\u0441\u044b\u043b\u043a\u0438", "\u0441\u0441\u044b\u043b\u043a\u0430_id", "TEXT", False),
    ("a4_\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u043d\u044b\u0435", "\u043f\u0440\u043e\u0438\u0437\u0432_id", "TEXT", False),
    ("a5_\u043f\u0435\u0440\u0435\u043a\u0440\u0451\u0441\u0442\u043d\u044b\u0435_\u0441\u0441\u044b\u043b\u043a\u0438", "\u043f\u0435\u0440\u0435\u043a\u0440_id", "TEXT", False),
    ("a6_\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f_\u0441\u0442\u0440\u0430\u043d", "\u0441\u0442\u0440\u0430\u043d\u0430_id", "TEXT", False),
]

# ============================================================================
# Tables that need FOREIGN KEY added (already have PK)
# These get rebuilt with FK constraints in CREATE TABLE
# Format: (table_name, {col: "REFERENCES target(col)"})
# ============================================================================
FK_ADDITIONS = {
    "entries": {
        "root_id": "REFERENCES roots(root_id)",
    },
    "european_a1_entries": {
        "root_id": "REFERENCES roots(root_id)",
    },
    "latin_a1_entries": {
        "root_id": "REFERENCES roots(root_id)",
    },
    # uzbek_vocabulary already has FKs defined
}


def get_table_info(conn, table_name):
    """Return list of (cid, name, type, notnull, dflt_value, pk)."""
    return conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()


def get_triggers_for_table(conn, table_name):
    """Return list of (name, sql) for triggers on this table."""
    return conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
        (table_name,)
    ).fetchall()


def get_indexes_for_table(conn, table_name):
    """Return list of (name, sql) for non-auto indexes on this table."""
    return conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (table_name,)
    ).fetchall()


def get_row_count(conn, table_name):
    """Safe row count."""
    try:
        return conn.execute(f'SELECT count(*) FROM "{table_name}"').fetchone()[0]
    except Exception:
        return -1


def build_create_ddl(table_name, cols_info, pk_column, pk_type, fk_map=None):
    """Build CREATE TABLE DDL with PK on specified column and optional FKs."""
    col_defs = []
    for cid, name, ctype, notnull, dflt, pk in cols_info:
        if name == pk_column:
            col_defs.append(f'"{name}" {pk_type} PRIMARY KEY')
        else:
            parts = [f'"{name}" {ctype or "TEXT"}']
            if notnull:
                parts.append("NOT NULL")
            if dflt is not None:
                parts.append(f"DEFAULT {dflt}")
            # Add FK if specified
            if fk_map and name in fk_map:
                parts.append(fk_map[name])
            col_defs.append(" ".join(parts))

    return f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'


def rebuild_table_with_pk(conn, table_name, pk_column, pk_type, dedup=False, fk_map=None):
    """Rebuild a table adding PRIMARY KEY (and optional FKs).
    NOTE: All triggers must be dropped BEFORE calling this function."""

    # 1. Get current schema
    cols_info = get_table_info(conn, table_name)
    col_names = [c[1] for c in cols_info]
    col_list = ", ".join(f'"{c}"' for c in col_names)

    # 2. Count before
    count_before = get_row_count(conn, table_name)

    # 3. Save indexes for this table
    indexes = get_indexes_for_table(conn, table_name)

    # 4. Create temp table with PK
    temp_name = f"_v4_migrate_{table_name[:40]}"
    new_ddl = build_create_ddl(temp_name, cols_info, pk_column, pk_type, fk_map)
    conn.execute(f'DROP TABLE IF EXISTS "{temp_name}"')
    conn.execute(new_ddl)

    # 5. Copy data (with dedup if needed)
    if dedup:
        conn.execute(f'''
            INSERT OR IGNORE INTO "{temp_name}" ({col_list})
            SELECT {col_list} FROM "{table_name}" ORDER BY rowid
        ''')
    else:
        conn.execute(f'''
            INSERT INTO "{temp_name}" ({col_list})
            SELECT {col_list} FROM "{table_name}"
        ''')

    count_after = get_row_count(conn, temp_name)

    # 6. Drop indexes
    for iname, _ in indexes:
        conn.execute(f'DROP INDEX IF EXISTS "{iname}"')

    # 7. Drop original, rename temp
    conn.execute(f'DROP TABLE "{table_name}"')
    conn.execute(f'ALTER TABLE "{temp_name}" RENAME TO "{table_name}"')

    # 8. Recreate indexes
    for iname, isql in indexes:
        if isql:
            try:
                conn.execute(isql)
            except Exception as e:
                print(f"    WARN: index {iname} failed: {e}")

    conn.commit()

    dedup_lost = count_before - count_after
    return count_before, count_after, dedup_lost


def rebuild_table_with_fk_only(conn, table_name, fk_map):
    """Rebuild a table that already has PK but needs FK constraints added.
    NOTE: All triggers must be dropped BEFORE calling this function."""

    cols_info = get_table_info(conn, table_name)
    col_names = [c[1] for c in cols_info]
    col_list = ", ".join(f'"{c}"' for c in col_names)

    # Find PK column
    pk_col = None
    pk_type = None
    for cid, name, ctype, notnull, dflt, pk in cols_info:
        if pk > 0:
            pk_col = name
            pk_type = ctype or "TEXT"
            break

    if not pk_col:
        print(f"  SKIP {table_name}: no PK found")
        return 0, 0

    count_before = get_row_count(conn, table_name)
    indexes = get_indexes_for_table(conn, table_name)

    temp_name = f"_v4_fk_{table_name[:40]}"
    new_ddl = build_create_ddl(temp_name, cols_info, pk_col, pk_type, fk_map)

    conn.execute(f'DROP TABLE IF EXISTS "{temp_name}"')
    conn.execute(new_ddl)

    conn.execute(f'''
        INSERT INTO "{temp_name}" ({col_list})
        SELECT {col_list} FROM "{table_name}"
    ''')

    count_after = get_row_count(conn, temp_name)

    for iname, _ in indexes:
        conn.execute(f'DROP INDEX IF EXISTS "{iname}"')

    conn.execute(f'DROP TABLE "{table_name}"')
    conn.execute(f'ALTER TABLE "{temp_name}" RENAME TO "{table_name}"')

    for iname, isql in indexes:
        if isql:
            try:
                conn.execute(isql)
            except Exception as e:
                print(f"    WARN: index {iname} failed: {e}")

    conn.commit()
    return count_before, count_after


def add_fts_table(conn):
    """Recreate FTS5 virtual table for entries if it was lost during rebuild."""
    try:
        conn.execute("DROP TABLE IF EXISTS entries_fts")
        conn.execute("""
            CREATE VIRTUAL TABLE entries_fts USING fts5(
                entry_id UNINDEXED,
                en_term,
                ru_term,
                fa_term,
                ar_word,
                content=entries
            )
        """)
        # Populate FTS
        conn.execute("""
            INSERT INTO entries_fts(entry_id, en_term, ru_term, fa_term, ar_word)
            SELECT entry_id, en_term, ru_term, fa_term, ar_word FROM entries
        """)
        conn.commit()
        count = conn.execute("SELECT count(*) FROM entries_fts").fetchone()[0]
        print(f"  FTS5 rebuilt: {count} entries indexed")
    except Exception as e:
        print(f"  WARN: FTS5 rebuild failed: {e}")


def recreate_views(conn):
    """Recreate all views (they may reference rebuilt tables)."""
    views = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='view'"
    ).fetchall()

    for vname, vsql in views:
        if vsql:
            try:
                conn.execute(f'DROP VIEW IF EXISTS "{vname}"')
                conn.execute(vsql)
            except Exception as e:
                print(f"  WARN: view {vname} failed: {e}")

    conn.commit()
    print(f"  {len(views)} views verified")


def verify_counts(v3_conn, v4_conn):
    """Compare row counts between V3 and V4 for all tables."""
    v3_tables = {r[0] for r in v3_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_v4_%'"
    ).fetchall()}

    v4_tables = {r[0] for r in v4_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_v4_%'"
    ).fetchall()}

    missing = v3_tables - v4_tables
    if missing:
        print(f"\n  MISSING tables in V4: {missing}")

    mismatches = []
    for t in sorted(v3_tables & v4_tables):
        c3 = get_row_count(v3_conn, t)
        c4 = get_row_count(v4_conn, t)
        if c3 != c4:
            mismatches.append((t, c3, c4))

    return missing, mismatches


def verify_pk_constraints(conn):
    """Verify all target tables now have PRIMARY KEY."""
    results = []
    for table_name, pk_col, _, _ in PK_FIXES:
        info = get_table_info(conn, table_name)
        has_pk = any(c[5] > 0 for c in info)  # c[5] = pk flag
        results.append((table_name, pk_col, has_pk))
    return results


def verify_fk_enforcement(conn):
    """Run PRAGMA foreign_key_check and report violations."""
    conn.execute("PRAGMA foreign_keys = ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    return violations


# ============================================================================
# CHECK MODE
# ============================================================================
def run_check():
    """Dry run: analyze what migration will do."""
    print("=" * 70)
    print("USLaP V3 → V4 Migration — DRY RUN CHECK")
    print("=" * 70)

    conn = sqlite3.connect(V3_DB)

    # Table counts
    table_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    trigger_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='trigger'"
    ).fetchone()[0]
    index_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    view_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='view'"
    ).fetchone()[0]

    print(f"\nV3 DB: {table_count} tables, {trigger_count} triggers, {index_count} indexes, {view_count} views")
    print(f"File size: {os.path.getsize(V3_DB) / 1024 / 1024:.1f} MB")

    print(f"\n--- Tables needing PRIMARY KEY ({len(PK_FIXES)}) ---")
    for table_name, pk_col, pk_type, dedup in PK_FIXES:
        count = get_row_count(conn, table_name)
        trg_count = len(get_triggers_for_table(conn, table_name))
        idx_count = len(get_indexes_for_table(conn, table_name))

        # Check for duplicates
        dup_count = 0
        if dedup:
            dups = conn.execute(
                f'SELECT count(*) FROM (SELECT "{pk_col}", count(*) as c FROM "{table_name}" GROUP BY "{pk_col}" HAVING c > 1)'
            ).fetchone()[0]
            dup_count = dups

        status = f"rows={count}, triggers={trg_count}, indexes={idx_count}"
        if dup_count:
            status += f", DUPS={dup_count} (will dedup)"
        print(f"  {table_name}: PK on {pk_col} ({pk_type}) — {status}")

    print(f"\n--- Tables needing FOREIGN KEY ({len(FK_ADDITIONS)}) ---")
    for table_name, fk_map in FK_ADDITIONS.items():
        count = get_row_count(conn, table_name)
        trg_count = len(get_triggers_for_table(conn, table_name))
        for col, ref in fk_map.items():
            # Check orphans
            orphans = conn.execute(
                f'SELECT count(*) FROM "{table_name}" WHERE "{col}" IS NOT NULL AND "{col}" != \'\' AND "{col}" NOT IN (SELECT root_id FROM roots)'
            ).fetchone()[0]
            print(f"  {table_name}.{col} → {ref} — rows={count}, triggers={trg_count}, orphans={orphans}")

    # Check current FK state
    print("\n--- Current FK enforcement ---")
    fk_state = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    print(f"  PRAGMA foreign_keys = {fk_state} ({'ON' if fk_state else 'OFF'})")

    conn.close()
    print("\n--- Ready to migrate. Run: python3 migrate_v3_to_v4.py migrate ---")


# ============================================================================
# MIGRATE MODE
# ============================================================================
def run_migrate():
    """Execute the full V3 → V4 migration."""
    print("=" * 70)
    print("USLaP V3 → V4 Migration — EXECUTING")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Step 0: Copy V3 → V4
    if os.path.exists(V4_DB):
        os.remove(V4_DB)
    print(f"\n[STEP 0] Copying V3 → V4...")
    shutil.copy2(V3_DB, V4_DB)
    print(f"  Copied {os.path.getsize(V4_DB) / 1024 / 1024:.1f} MB")

    conn = sqlite3.connect(V4_DB)
    conn.execute("PRAGMA journal_mode = WAL")
    # FK off during migration (we rebuild tables)
    conn.execute("PRAGMA foreign_keys = OFF")

    # Step 1a: Save and drop ALL views (cross-table dependencies during RENAME)
    print(f"\n[STEP 1a] Saving and dropping ALL views...")
    all_views = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='view'"
    ).fetchall()
    print(f"  Found {len(all_views)} views")
    for vname, _ in all_views:
        conn.execute(f'DROP VIEW IF EXISTS "{vname}"')
    conn.commit()

    # Step 1b: Save and drop ALL triggers (cross-table dependencies)
    print(f"\n[STEP 1b] Saving and dropping ALL triggers...")
    all_triggers = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='trigger'"
    ).fetchall()
    print(f"  Found {len(all_triggers)} triggers")
    for tname, _ in all_triggers:
        conn.execute(f'DROP TRIGGER IF EXISTS "{tname}"')
    conn.commit()
    remaining = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    print(f"  Dropped all. Remaining: {remaining}")

    # Step 2: Fix PRIMARY KEYs
    print(f"\n[STEP 2] Rebuilding {len(PK_FIXES)} tables with PRIMARY KEY...")
    for table_name, pk_col, pk_type, dedup in PK_FIXES:
        fk_map = FK_ADDITIONS.get(table_name)
        before, after, lost = rebuild_table_with_pk(
            conn, table_name, pk_col, pk_type, dedup, fk_map
        )
        status = f"  {table_name}: {before}→{after} rows"
        if lost:
            status += f" ({lost} dups removed)"
        print(status)

    # Step 3: Add FOREIGN KEYs to tables that already have PK
    fk_only_tables = {k: v for k, v in FK_ADDITIONS.items()
                      if k not in [t[0] for t in PK_FIXES]}
    if fk_only_tables:
        print(f"\n[STEP 3] Adding FK constraints to {len(fk_only_tables)} tables...")
        for table_name, fk_map in fk_only_tables.items():
            before, after = rebuild_table_with_fk_only(conn, table_name, fk_map)
            print(f"  {table_name}: {before}→{after} rows")

    # Step 4: Recreate ALL triggers
    print(f"\n[STEP 4] Recreating {len(all_triggers)} triggers...")
    trigger_ok = 0
    trigger_fail = []
    for tname, tsql in all_triggers:
        if tsql:
            try:
                conn.execute(tsql)
                trigger_ok += 1
            except Exception as e:
                trigger_fail.append((tname, str(e)))
    conn.commit()
    print(f"  OK: {trigger_ok}, Failed: {len(trigger_fail)}")
    if trigger_fail:
        for tname, err in trigger_fail[:10]:
            print(f"    {tname}: {err}")

    # Step 5: Rebuild FTS
    print(f"\n[STEP 5] Rebuilding FTS5 index...")
    add_fts_table(conn)

    # Step 6: Recreate views from saved list
    print(f"\n[STEP 6] Recreating {len(all_views)} views...")
    view_ok = 0
    view_fail = []
    for vname, vsql in all_views:
        if vsql:
            try:
                conn.execute(f'DROP VIEW IF EXISTS "{vname}"')
                conn.execute(vsql)
                view_ok += 1
            except Exception as e:
                view_fail.append((vname, str(e)))
    conn.commit()
    print(f"  OK: {view_ok}, Failed: {len(view_fail)}")
    if view_fail:
        for vname, err in view_fail:
            print(f"    {vname}: {err}")

    # Step 7: Enable FK enforcement
    print(f"\n[STEP 7] Enabling FK enforcement...")
    conn.execute("PRAGMA foreign_keys = ON")
    fk_state = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    print(f"  PRAGMA foreign_keys = {fk_state}")

    # Step 8: FK violation check
    print(f"\n[STEP 8] Checking FK violations...")
    violations = verify_fk_enforcement(conn)
    if violations:
        print(f"  {len(violations)} FK violations found:")
        for v in violations[:20]:
            print(f"    table={v[0]}, rowid={v[1]}, parent={v[2]}, fkid={v[3]}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
    else:
        print(f"  0 FK violations — CLEAN")

    # Step 9: Verify PK constraints
    print(f"\n[STEP 9] Verifying PRIMARY KEY constraints...")
    pk_results = verify_pk_constraints(conn)
    for tname, pk_col, has_pk in pk_results:
        status = "PK" if has_pk else "NO PK — FAILED"
        print(f"  {tname}: {status}")

    # Step 10: Verify row counts against V3
    print(f"\n[STEP 10] Verifying row counts against V3...")
    v3_conn = sqlite3.connect(V3_DB)
    missing, mismatches = verify_counts(v3_conn, conn)
    if not missing and not mismatches:
        print("  ALL tables match — CLEAN")
    else:
        for t, c3, c4 in mismatches:
            diff = c4 - c3
            print(f"  {t}: V3={c3}, V4={c4} (diff={diff:+d})")
    v3_conn.close()

    # Step 11: Final stats
    table_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    trigger_count = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='trigger'"
    ).fetchone()[0]

    conn.close()

    print(f"\n{'=' * 70}")
    print(f"MIGRATION COMPLETE")
    print(f"  V4 DB: {V4_DB}")
    print(f"  Size: {os.path.getsize(V4_DB) / 1024 / 1024:.1f} MB")
    print(f"  Tables: {table_count}, Triggers: {trigger_count}")
    if trigger_fail:
        print(f"\n  TRIGGER FAILURES ({len(trigger_fail)}):")
        for tname, err in trigger_fail:
            print(f"    {tname}: {err}")
    print(f"\nFinished: {datetime.now().isoformat()}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_v3_to_v4.py [check|migrate]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "check":
        run_check()
    elif cmd == "migrate":
        run_migrate()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python3 migrate_v3_to_v4.py [check|migrate]")
        sys.exit(1)
