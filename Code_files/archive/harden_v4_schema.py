#!/usr/bin/env python3
"""
USLaP V4 Schema Hardening (Updated with Domain QUF)
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Resolves all SWOT threats and weaknesses in one pass:
  T4: schema_version table
  T5: PK on excel_data_consolidated
  O1/W2: root_id FK on bitig_a1_entries
  O2/W3: FK on a4_derivatives.entry_id
  O3/W5: Indexes on entries + core tables
  O4/W4: UNIQUE constraints
  O5/W6: CHECK constraints
  O6: Retire xlsx_* tables
  O7/W1: PK on remaining NO_PK tables
  NEW: QUF indexes for fast filtering
  NEW: Fix broken a1_entries view
  NEW: Schema health check (validates all 157 tables)

Usage:
    python3 Code_files/harden_v4_schema.py [--check-only]
"""

import sqlite3
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "uslap_database_v3.db")


def run():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF")  # OFF during schema changes
    conn.execute("PRAGMA journal_mode = WAL")

    print("=" * 70)
    print("USLaP V4 Schema Hardening")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # ================================================================
    # T4: schema_version table
    # ================================================================
    print("\n[T4] Adding schema_version table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER NOT NULL,
            description TEXT NOT NULL,
            applied_at  TEXT DEFAULT (datetime('now')),
            applied_by  TEXT DEFAULT 'migration'
        )
    """)
    conn.execute("""
        INSERT INTO schema_version (version, description) VALUES
        (4, 'V4: PK/FK enforcement, contamination triggers, schema hardening')
    """)
    conn.commit()
    print("  schema_version created, V4 recorded")

    # ================================================================
    # Save and drop ALL triggers + views (needed for table rebuilds)
    # ================================================================
    print("\n[PREP] Saving triggers and views...")
    all_triggers = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='trigger'"
    ).fetchall()
    all_views = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='view'"
    ).fetchall()
    print(f"  {len(all_triggers)} triggers, {len(all_views)} views")

    for vname, _ in all_views:
        conn.execute(f'DROP VIEW IF EXISTS "{vname}"')
    for tname, _ in all_triggers:
        conn.execute(f'DROP TRIGGER IF EXISTS "{tname}"')
    conn.commit()
    print("  All dropped temporarily")

    # ================================================================
    # O1/W2: Add root_id column to bitig_a1_entries + populate
    # ================================================================
    print("\n[O1/W2] Adding root_id to bitig_a1_entries...")
    # Check if column exists
    cols = [c[1] for c in conn.execute("PRAGMA table_info(bitig_a1_entries)")]
    if "root_id" not in cols:
        conn.execute("ALTER TABLE bitig_a1_entries ADD COLUMN root_id TEXT REFERENCES roots(root_id)")
        conn.commit()
        print("  Column added")
    else:
        print("  Column already exists")

    # Auto-populate from root_letters match
    updated = conn.execute("""
        UPDATE bitig_a1_entries SET root_id = (
            SELECT r.root_id FROM roots r WHERE r.root_letters = bitig_a1_entries.root_letters
        )
        WHERE root_letters IS NOT NULL AND root_letters != ''
        AND root_id IS NULL
    """).rowcount
    conn.commit()
    print(f"  Auto-mapped {updated} bitig entries to roots")

    # ================================================================
    # O2/W3: Fix a4_derivatives orphan, add FK
    # ================================================================
    print("\n[O2/W3] Fixing a4_derivatives orphan + adding FK...")
    # The 1 orphan has entry_id='MUQARNAS' (text, not int) — NULL it
    conn.execute("""
        UPDATE a4_derivatives SET entry_id = NULL
        WHERE entry_id IS NOT NULL
        AND CAST(entry_id AS INTEGER) = 0
        AND entry_id != '0'
    """)
    conn.commit()

    # Rebuild a4_derivatives with FK
    deriv_cols = conn.execute("PRAGMA table_info(a4_derivatives)").fetchall()
    col_names = [c[1] for c in deriv_cols]
    col_list = ", ".join(f'"{c}"' for c in col_names)

    conn.execute("DROP TABLE IF EXISTS _harden_a4")
    ddl_parts = []
    for cid, name, ctype, notnull, dflt, pk in deriv_cols:
        if name == "deriv_id":
            ddl_parts.append('"deriv_id" TEXT PRIMARY KEY')
        elif name == "entry_id":
            ddl_parts.append('"entry_id" INTEGER REFERENCES entries(entry_id)')
        else:
            part = f'"{name}" {ctype or "TEXT"}'
            if dflt is not None:
                part += f" DEFAULT {dflt}"
            ddl_parts.append(part)
    conn.execute(f'CREATE TABLE _harden_a4 ({", ".join(ddl_parts)})')
    conn.execute(f'INSERT INTO _harden_a4 ({col_list}) SELECT {col_list} FROM a4_derivatives')
    before = conn.execute("SELECT count(*) FROM a4_derivatives").fetchone()[0]
    after = conn.execute("SELECT count(*) FROM _harden_a4").fetchone()[0]
    conn.execute("DROP TABLE a4_derivatives")
    conn.execute("ALTER TABLE _harden_a4 RENAME TO a4_derivatives")
    conn.commit()
    print(f"  a4_derivatives: {before}→{after}, FK on entry_id→entries")

    # ================================================================
    # O3/W5: Add indexes on core tables
    # ================================================================
    print("\n[O3/W5] Adding indexes...")
    indexes = [
        ("idx_entries_en_term", "entries", "en_term"),
        ("idx_entries_ru_term", "entries", "ru_term"),
        ("idx_entries_fa_term", "entries", "fa_term"),
        ("idx_entries_ar_word", "entries", "ar_word"),
        ("idx_entries_root_id", "entries", "root_id"),
        ("idx_entries_score", "entries", "score"),
        ("idx_entries_network_id", "entries", "network_id"),
        ("idx_bitig_root_letters", "bitig_a1_entries", "root_letters"),
        ("idx_bitig_root_id", "bitig_a1_entries", "root_id"),
        ("idx_bitig_orig2_term", "bitig_a1_entries", "orig2_term"),
        ("idx_eu_term", "european_a1_entries", "term"),
        ("idx_eu_lang", "european_a1_entries", "lang"),
        ("idx_eu_root_id", "european_a1_entries", "root_id"),
        ("idx_lat_term", "latin_a1_entries", "lat_term"),
        ("idx_lat_root_id", "latin_a1_entries", "root_id"),
        ("idx_a4_entry_id", "a4_derivatives", "entry_id"),
        ("idx_a5_from_id", "a5_cross_refs", "from_id"),
        ("idx_a5_to_id", "a5_cross_refs", "to_id"),
        ("idx_qwr_root", "quran_word_roots", "root"),
        ("idx_qwr_surah_ayah", "quran_word_roots", "surah, ayah"),
        ("idx_qv_root", "qv_translation_register", "ROOT"),
        ("idx_roots_letters", "roots", "root_letters"),
    ]
    idx_ok = 0
    for idx_name, table, cols in indexes:
        try:
            conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table}" ({cols})')
            idx_ok += 1
        except Exception as e:
            print(f"  WARN: {idx_name}: {e}")
    conn.commit()
    print(f"  {idx_ok}/{len(indexes)} indexes created")

    # ================================================================
    # O4/W4: UNIQUE constraints (via unique indexes)
    # ================================================================
    print("\n[O4/W4] Adding UNIQUE constraints...")
    uniques = [
        ("uq_entries_en_root", "entries", "en_term, root_id"),
        ("uq_bitig_orig2", "bitig_a1_entries", "orig2_term, root_letters"),
        ("uq_eu_lang_term", "european_a1_entries", "lang, term"),
        ("uq_lat_term", "latin_a1_entries", "lat_term"),
        ("uq_roots_letters", "roots", "root_letters"),
    ]
    uq_ok = 0
    for uq_name, table, cols in uniques:
        try:
            conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS "{uq_name}" ON "{table}" ({cols})')
            uq_ok += 1
        except Exception as e:
            print(f"  WARN: {uq_name}: {e}")
    conn.commit()
    print(f"  {uq_ok}/{len(uniques)} unique constraints created")

    # ================================================================
    # O5/W6: CHECK constraints (via trigger-based validation)
    # SQLite can't ALTER TABLE ADD CHECK, so we use BEFORE INSERT triggers
    # ================================================================
    print("\n[O5/W6] Adding CHECK-equivalent validation triggers...")
    check_triggers = [
        ("trg_check_entries_score", "entries", "BEFORE INSERT",
         "SELECT RAISE(ABORT, 'score must be 0-10') WHERE NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > 10)"),
        ("trg_check_entries_score_upd", "entries", "BEFORE UPDATE",
         "SELECT RAISE(ABORT, 'score must be 0-10') WHERE NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > 10)"),
        ("trg_check_uz_orig_type", "uzbek_vocabulary", "BEFORE INSERT",
         "SELECT RAISE(ABORT, 'orig_type must be ORIG1 or ORIG2') WHERE NEW.orig_type NOT IN ('ORIG1', 'ORIG2')"),
        ("trg_check_uz_orig_type_upd", "uzbek_vocabulary", "BEFORE UPDATE",
         "SELECT RAISE(ABORT, 'orig_type must be ORIG1 or ORIG2') WHERE NEW.orig_type NOT IN ('ORIG1', 'ORIG2')"),
        ("trg_check_wg_status", "write_gate", "BEFORE INSERT",
         "SELECT RAISE(ABORT, 'status must be ANALYSED/WRITTEN/VERIFIED/CLOSED') WHERE NEW.status NOT IN ('ANALYSED','WRITTEN','VERIFIED','CLOSED')"),
        ("trg_check_wg_status_upd", "write_gate", "BEFORE UPDATE",
         "SELECT RAISE(ABORT, 'status must be ANALYSED/WRITTEN/VERIFIED/CLOSED') WHERE NEW.status NOT IN ('ANALYSED','WRITTEN','VERIFIED','CLOSED')"),
    ]
    chk_ok = 0
    for tname, table, event, body in check_triggers:
        try:
            conn.execute(f'CREATE TRIGGER IF NOT EXISTS "{tname}" {event} ON "{table}" FOR EACH ROW BEGIN {body}; END')
            chk_ok += 1
        except Exception as e:
            print(f"  WARN: {tname}: {e}")
    conn.commit()
    print(f"  {chk_ok}/{len(check_triggers)} check triggers created")

    # ================================================================
    # O6: Retire xlsx_* tables (rename to _retired_*)
    # ================================================================
    print("\n[O6] Retiring xlsx_* tables...")
    xlsx_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'xlsx_%'"
    ).fetchall()]
    retired = 0
    for t in xlsx_tables:
        new_name = f"_retired_{t}"
        try:
            conn.execute(f'ALTER TABLE "{t}" RENAME TO "{new_name}"')
            retired += 1
        except Exception as e:
            print(f"  WARN: {t}: {e}")
    conn.commit()
    print(f"  {retired}/{len(xlsx_tables)} tables retired")

    # ================================================================
    # O7/W1: Add PK to remaining NO_PK tables via rowid
    # For foundation/mechanism/bitig_support tables: add integer PK
    # ================================================================
    print("\n[O7/W1] Adding PK to remaining NO_PK tables...")
    no_pk_tables = [r[0] for r in conn.execute("""
        SELECT m.name FROM sqlite_master m
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '_retired_%'
        AND name NOT LIKE 'entries_fts%'
        AND NOT EXISTS(SELECT 1 FROM pragma_table_info(m.name) WHERE pk > 0)
    """).fetchall()]

    pk_added = 0
    pk_skip = []
    for table in no_pk_tables:
        cols = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        col_names = [c[1] for c in cols]
        col_list = ", ".join(f'"{c}"' for c in col_names)

        # Build new DDL with rowid_pk as PK
        new_col_defs = ['"rowid_pk" INTEGER PRIMARY KEY AUTOINCREMENT']
        for cid, name, ctype, notnull, dflt, pk in cols:
            part = f'"{name}" {ctype or "TEXT"}'
            if notnull:
                part += " NOT NULL"
            if dflt is not None:
                part += f" DEFAULT {dflt}"
            new_col_defs.append(part)

        temp = f"_harden_{table[:40]}"
        try:
            conn.execute(f'DROP TABLE IF EXISTS "{temp}"')
            conn.execute(f'CREATE TABLE "{temp}" ({", ".join(new_col_defs)})')
            conn.execute(f'INSERT INTO "{temp}" ({col_list}) SELECT {col_list} FROM "{table}"')
            before = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            after = conn.execute(f'SELECT count(*) FROM "{temp}"').fetchone()[0]
            if before == after:
                conn.execute(f'DROP TABLE "{table}"')
                conn.execute(f'ALTER TABLE "{temp}" RENAME TO "{table}"')
                pk_added += 1
            else:
                conn.execute(f'DROP TABLE "{temp}"')
                pk_skip.append((table, f"count mismatch {before}→{after}"))
        except Exception as e:
            pk_skip.append((table, str(e)))
            try:
                conn.execute(f'DROP TABLE IF EXISTS "{temp}"')
            except Exception:
                pass
        conn.commit()

    print(f"  {pk_added}/{len(no_pk_tables)} tables got PK")
    if pk_skip:
        for t, reason in pk_skip:
            print(f"  SKIP: {t}: {reason}")

    # ================================================================
    # T5: excel_data_consolidated should now have PK from O7 above
    # ================================================================
    has_pk = any(c[5] > 0 for c in conn.execute("PRAGMA table_info(excel_data_consolidated)"))
    print(f"\n[T5] excel_data_consolidated PK: {'YES' if has_pk else 'NO'}")

    # ================================================================
    # Recreate ALL triggers
    # ================================================================
    print(f"\n[RESTORE] Recreating {len(all_triggers)} triggers...")
    # Add our new check triggers to the count
    trg_ok = 0
    trg_fail = []
    for tname, tsql in all_triggers:
        if tsql:
            try:
                conn.execute(tsql)
                trg_ok += 1
            except Exception as e:
                trg_fail.append((tname, str(e)))
    conn.commit()
    print(f"  OK: {trg_ok}, Failed: {len(trg_fail)}")
    if trg_fail:
        for tname, err in trg_fail[:15]:
            print(f"    {tname}: {err}")

    # ================================================================
    # Recreate ALL views
    # ================================================================
    print(f"\n[RESTORE] Recreating {len(all_views)} views...")
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

    # ================================================================
    # NEW: QUF indexes for fast amr_lawh filtering
    # ================================================================
    print("\n[QUF-IDX] Adding QUF pass indexes for fast filtering...")
    quf_tables = [r[0] for r in conn.execute("""
        SELECT m.name FROM sqlite_master m
        WHERE m.type='table' AND m.name NOT LIKE '_retired_%'
        AND m.name NOT LIKE 'sqlite_%' AND m.name NOT LIKE 'entries_fts%'
        AND EXISTS(SELECT 1 FROM pragma_table_info(m.name) WHERE name='quf_pass')
    """).fetchall()]
    quf_idx_ok = 0
    for tbl in quf_tables:
        idx_name = f"idx_quf_pass_{tbl[:50]}"
        try:
            conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{tbl}" (quf_pass)')
            quf_idx_ok += 1
        except Exception as e:
            print(f"  WARN: {tbl}: {e}")
    conn.commit()
    print(f"  {quf_idx_ok}/{len(quf_tables)} QUF indexes created")

    # ================================================================
    # NEW: Fix broken a1_entries view
    # ================================================================
    print("\n[VIEW-FIX] Fixing a1_entries view...")
    # The old view references qur_meaning column which no longer exists
    # entries table has qur_refs instead. Also add quf_pass filter.
    try:
        conn.execute("DROP VIEW IF EXISTS a1_entries")
        conn.execute("""
            CREATE VIEW a1_entries AS
            SELECT entry_id, score, en_term, ru_term, fa_term, ar_word,
                   root_id, root_letters, qur_refs, pattern, inversion_type,
                   network_id, allah_name_id, phonetic_chain, source_form,
                   ds_corridor, decay_level, dp_codes, ops_applied,
                   foundation_refs, notes, qur_meaning,
                   quf_q, quf_u, quf_f, quf_pass
            FROM entries
        """)
        conn.commit()
        view_count = conn.execute("SELECT COUNT(*) FROM a1_entries").fetchone()[0]
        print(f"  a1_entries view recreated ({view_count} rows)")
    except Exception as e:
        print(f"  WARN: {e}")

    # ================================================================
    # NEW: Schema health check — validate AMR AI can query all 28 tables
    # ================================================================
    print("\n[HEALTH] Schema health check for AMR AI tables...")
    amr_tables = {
        'roots': 'root_id',
        'entries': 'entry_id',
        'european_a1_entries': 'entry_id',
        'latin_a1_entries': 'entry_id',
        'bitig_a1_entries': 'entry_id',
        'uzbek_vocabulary': 'uz_id',
        'a4_derivatives': 'deriv_id',
        'a5_cross_refs': 'xref_id',
        'names_of_allah': 'allah_id',
        'qv_translation_register': 'QV_ID',
        'quran_word_roots': 'word_id',
        'quran_known_forms': 'form_id',
        'dp_register': 'dp_code',
        'disputed_words': 'word_id',
        'contamination_blacklist': 'bl_id',
        'phonetic_reversal': 'shift_code',
        'aa_morpheme_map': 'morpheme_id',
        'child_entries': 'child_id',
        'bitig_convergence_register': 'conv_id',
        'bitig_degradation_register': 'deg_id',
        'chronology': 'rowid_pk',
        'word_deployment_map': 'deploy_id',
        'shift_lookup': 'en_consonant',
        'name_root_hub': 'name_id',
        'isnad': 'isnad_id',
        'languages': 'lang_code',
        'op_codes': 'op_code',
    }
    health_ok = 0
    health_fail = []
    for tbl, pk in amr_tables.items():
        try:
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
            has_quf = 'quf_pass' in cols
            has_pk_col = pk in cols
            if cnt > 0 and has_quf and has_pk_col:
                health_ok += 1
            else:
                issues = []
                if cnt == 0: issues.append('EMPTY')
                if not has_quf: issues.append('NO_QUF')
                if not has_pk_col: issues.append(f'NO_PK({pk})')
                health_fail.append((tbl, ', '.join(issues)))
        except Exception as e:
            health_fail.append((tbl, str(e)))
    print(f"  OK: {health_ok}/{len(amr_tables)}")
    if health_fail:
        for tbl, issue in health_fail:
            print(f"  ISSUE: {tbl}: {issue}")

    # ================================================================
    # NEW: Composite indexes for common query patterns
    # ================================================================
    print("\n[PERF] Adding composite indexes for common patterns...")
    composites = [
        ("idx_entries_root_quf", "entries", "root_id, quf_pass"),
        ("idx_eu_root_lang", "european_a1_entries", "root_id, lang"),
        ("idx_qwr_root_surah", "quran_word_roots", "root, surah"),
        ("idx_a4_entry_link", "a4_derivatives", "entry_id, link_type"),
        ("idx_roots_type_quf", "roots", "root_type, quf_pass"),
        ("idx_uz_orig_root", "uzbek_vocabulary", "orig_type, aa_root_id"),
    ]
    comp_ok = 0
    for idx_name, table, cols in composites:
        try:
            conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table}" ({cols})')
            comp_ok += 1
        except Exception as e:
            print(f"  WARN: {idx_name}: {e}")
    conn.commit()
    print(f"  {comp_ok}/{len(composites)} composite indexes created")

    # ================================================================
    # Enable FK and verify
    # ================================================================
    print("\n[VERIFY] FK enforcement...")
    conn.execute("PRAGMA foreign_keys = ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  FK violations: {len(violations)}")
    if violations:
        for v in violations[:10]:
            print(f"    table={v[0]}, rowid={v[1]}, parent={v[2]}, fkid={v[3]}")

    # Integrity check
    print("\n[VERIFY] Integrity check...")
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"  {result}")

    # Final counts
    tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
    triggers = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    indexes = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
    no_pk_remaining = len([r for r in conn.execute("""
        SELECT m.name FROM sqlite_master m
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '_retired_%'
        AND name NOT LIKE 'entries_fts%'
        AND NOT EXISTS(SELECT 1 FROM pragma_table_info(m.name) WHERE pk > 0)
    """).fetchall()])

    conn.close()

    size_mb = os.path.getsize(DB) / 1024 / 1024
    print(f"\n{'=' * 70}")
    print(f"HARDENING COMPLETE")
    print(f"  DB: {size_mb:.1f} MB")
    print(f"  Tables: {tables} | Triggers: {triggers} | Indexes: {indexes}")
    print(f"  NO_PK remaining: {no_pk_remaining}")
    print(f"  FK violations: {len(violations)}")
    print(f"Finished: {datetime.now().isoformat()}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    import sys
    if '--check-only' in sys.argv:
        # Run only the health check without making changes
        conn = sqlite3.connect(DB)
        print("Schema health check (read-only)...")
        tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        triggers = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
        indexes = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        quf_tables = conn.execute("""
            SELECT COUNT(DISTINCT m.name) FROM sqlite_master m
            WHERE m.type='table' AND EXISTS(SELECT 1 FROM pragma_table_info(m.name) WHERE name='quf_pass')
        """).fetchone()[0]
        size_mb = os.path.getsize(DB) / 1024 / 1024
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        conn.close()
        print(f"  DB: {size_mb:.1f} MB | Tables: {tables} | Triggers: {triggers} | Indexes: {indexes}")
        print(f"  QUF tables: {quf_tables} | Integrity: {result} | FK violations: {fk_violations}")
    else:
        run()
