#!/usr/bin/env python3
"""
USLaP Schema Consolidation — 185 tables → ~80
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Phase 1: RU mirrors → EN parents (13 eliminated)
Phase 2: Body 46 → 5 tables (41 eliminated)
Phase 3: Bitig 15 → 10 (5 eliminated)
Phase 4: Foundation/Mechanism consolidation

Usage: python3 consolidate_schema_v5.py [--dry-run]
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "uslap_database_v3.db")
DRY_RUN = '--dry-run' in sys.argv

def run():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA journal_mode = WAL")

    print("=" * 70)
    print(f"USLaP Schema Consolidation {'(DRY RUN)' if DRY_RUN else ''}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Save triggers
    print("\n[PREP] Saving triggers...")
    all_triggers = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
    print(f"  {len(all_triggers)} triggers saved")

    # Drop ALL triggers for migration (NOT in dry run)
    if not DRY_RUN:
        for tname, _ in all_triggers:
            conn.execute(f'DROP TRIGGER IF EXISTS "{tname}"')
        conn.commit()
        print("  All triggers dropped")
    else:
        print("  (dry run — triggers preserved)")

    # Drop existing compatibility views that conflict
    existing_views = set()
    for view_name in ['a1_записи', 'a1_entries']:
        vtype = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (view_name,)).fetchone()
        if vtype and vtype[0] == 'view':
            existing_views.add(view_name)
            if not DRY_RUN:
                conn.execute(f'DROP VIEW IF EXISTS "{view_name}"')
            print(f"  {'Would drop' if DRY_RUN else 'Dropped'} view: {view_name}")

    # ================================================================
    # PHASE 1: RU MIRRORS → EN PARENTS
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 1: RU Mirrors → EN Parents")
    print("=" * 70)

    # Add lang column to parent tables (skip views)
    lang_tables = ['entries', 'names_of_allah', 'a3_quran_refs', 'a4_derivatives',
                   'a5_cross_refs', 'a6_country_names']
    for tbl in lang_tables:
        ttype = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (tbl,)).fetchone()
        if not ttype or ttype[0] == 'view':
            print(f"  Skipping {tbl} (view or missing)")
            continue
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        if 'lang' not in cols:
            if not DRY_RUN:
                conn.execute(f'ALTER TABLE "{tbl}" ADD COLUMN lang TEXT DEFAULT "EN"')
                conn.execute(f'UPDATE "{tbl}" SET lang="EN" WHERE lang IS NULL')
            print(f"  {tbl}: lang column {'would be added' if DRY_RUN else 'added'}")
        else:
            print(f"  {tbl}: lang column exists")
    if not DRY_RUN:
        conn.commit()

    # Merge a1_записи → entries (SKIP if it's already a view)
    a1_type = conn.execute("SELECT type FROM sqlite_master WHERE name='a1_записи'").fetchone()
    if a1_type and a1_type[0] == 'view':
        print("  a1_записи is already a VIEW (data in entries) — skipping merge")
        ru_rows = []
    else:
        ru_cols = {r[1]: r for r in conn.execute("PRAGMA table_info('a1_записи')").fetchall()}
    col_map = {
        'запись_id': 'entry_id', 'балл': 'score', 'рус_термин': 'ru_term',
        'ар_слово': 'ar_word', 'корень_id': 'root_id', 'корневые_буквы': 'root_letters',
        'коранич_значение': 'qur_meaning', 'паттерн': 'pattern',
        'тип_инверсии': 'inversion_type', 'сеть_id': 'network_id',
        'имя_аллаха_id': 'allah_name_id', 'фонетическая_цепь': 'phonetic_chain',
        'исходная_форма': 'source_form', 'основание': 'foundation_refs',
    }

    ru_rows = conn.execute('SELECT * FROM "a1_записи"').fetchall()
    ru_col_names = [r[1] for r in conn.execute("PRAGMA table_info('a1_записи')").fetchall()]
    migrated = 0
    for row in ru_rows:
        row_dict = dict(zip(ru_col_names, row))
        # Map to EN column names
        en_vals = {}
        for ru_name, value in row_dict.items():
            if ru_name.startswith('quf_'):
                en_vals[ru_name] = value
            elif ru_name in col_map:
                en_vals[col_map[ru_name]] = value
        en_vals['lang'] = 'RU'
        en_vals['en_term'] = row_dict.get('рус_термин', '')  # RU term goes in en_term for now

        # Insert
        cols_str = ', '.join(f'"{k}"' for k in en_vals.keys())
        placeholders = ', '.join('?' * len(en_vals))
        if not DRY_RUN:
            try:
                conn.execute(f'INSERT INTO entries ({cols_str}) VALUES ({placeholders})',
                            list(en_vals.values()))
                migrated += 1
            except Exception as e:
                if migrated == 0:
                    print(f"  WARN: {e}")
    conn.commit()
    print(f"  a1_записи → entries: {migrated}/{len(ru_rows)} rows migrated")

    # Merge a2_имена_аллаха → names_of_allah
    a2_map = {'имя_id': 'allah_id', 'арабское_имя': 'arabic_name',
              'транслитерация': 'transliteration', 'значение': 'meaning',
              'коран_ссылка': 'qur_ref', 'записи_id': 'entry_ids', 'корень_id': 'root_id'}
    _migrate_ru_table(conn, 'a2_имена_аллаха', 'names_of_allah', a2_map)

    # Merge a3
    a3_map = {'ссылка_id': 'ref_id', 'сура': 'surah', 'аят': 'ayah',
              'арабский_текст': 'arabic_text', 'кв_id': 'qv_id',
              'слой': 'layer_ref', 'записи_id': 'entry_ids',
              'сеть_id': 'network_id', 'релевантность': 'relevance'}
    _migrate_ru_table(conn, 'a3_коранические_ссылки', 'a3_quran_refs', a3_map)

    # Merge a4
    a4_map = {'произв_id': 'deriv_id', 'запись_id': 'entry_id',
              'рус_термин': 'en_term', 'производное': 'derivative',
              'тип_связи': 'link_type'}
    _migrate_ru_table(conn, 'a4_производные', 'a4_derivatives', a4_map)

    # Merge a5
    a5_map = {'перекр_id': 'xref_id', 'от_id': 'from_id', 'к_id': 'to_id',
              'тип_связи': 'link_type', 'описание': 'description', 'слой': 'layer_ref'}
    _migrate_ru_table(conn, 'a5_перекрёстные_ссылки', 'a5_cross_refs', a5_map)

    # Merge a6
    a6_map = {'страна_id': 'country_id', 'название_страны': 'country_name',
              'корень_id': 'root_id', 'слово_al': 'al_word', 'корень_al': 'al_root',
              'коранич_значение': 'qur_meaning', 'фонетическая_цепь': 'phonetic_chain',
              'основание_названия': 'naming_basis', 'запись_ids': 'entry_ids',
              'примечания': 'notes'}
    _migrate_ru_table(conn, 'a6_названия_стран', 'a6_country_names', a6_map)

    # Foundation RU mirrors → add lang column to EN tables
    for ru_tbl, en_tbl in [
        ('f1_один_источник_два_коридора', 'f1_two_originals'),
        ('f2_нисходящий_поток', 'f2_script_downstream'),
        ('f2_критерии_деградации', 'f2_decay_criteria'),
        ('f3_модель_застывших_стадий', 'f3_frozen_stage_model'),
        ('f4_градиент_деградации', 'f4_decay_gradient'),
        ('f5_хронология_уничтожения', 'f5_destruction_timeline'),
        ('f6_рукописные_свидетельства', 'f6_manuscript_evidence'),
        ('f7_направление_потока', 'f7_direction_of_flow'),
    ]:
        _merge_generic_ru(conn, ru_tbl, en_tbl)

    # Mechanism RU → new mechanism_data table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mechanism_data (
            mech_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT NOT NULL,
            lang TEXT DEFAULT 'RU',
            data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
        )
    """)
    for ru_tbl, layer in [
        ('m1_фонетические_сдвиги', 'm1'), ('m2_паттерны_обнаружения', 'm2'),
        ('m3_учёные', 'm3'), ('m4_сети', 'm4'), ('m5_коранич_верификация', 'm5'),
    ]:
        try:
            rows = conn.execute(f'SELECT * FROM "{ru_tbl}"').fetchall()
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru_tbl}')").fetchall()]
            for row in rows:
                row_dict = {cols[i]: row[i] for i in range(len(cols)) if not cols[i].startswith('quf_')}
                if not DRY_RUN:
                    conn.execute("INSERT INTO mechanism_data (layer, lang, data) VALUES (?, 'RU', ?)",
                                (layer, json.dumps(row_dict, ensure_ascii=False)))
            print(f"  {ru_tbl} → mechanism_data: {len(rows)} rows")
        except Exception as e:
            print(f"  WARN {ru_tbl}: {e}")
    conn.commit()

    # Retire all RU tables
    ru_retire = [
        'a1_записи', 'a2_имена_аллаха', 'a3_коранические_ссылки',
        'a4_производные', 'a5_перекрёстные_ссылки', 'a6_названия_стран',
        'f1_один_источник_два_коридора', 'f2_нисходящий_поток', 'f2_критерии_деградации',
        'f3_модель_застывших_стадий', 'f4_градиент_деградации', 'f5_хронология_уничтожения',
        'f6_рукописные_свидетельства', 'f7_направление_потока',
        'm1_фонетические_сдвиги', 'm2_паттерны_обнаружения', 'm3_учёные', 'm4_сети', 'm5_коранич_верификация',
    ]
    retired = 0
    for tbl in ru_retire:
        try:
            if not DRY_RUN:
                conn.execute(f'ALTER TABLE "{tbl}" RENAME TO "_retired_consol_{tbl}"')
            retired += 1
        except:
            pass
    conn.commit()
    print(f"  Retired {retired} RU tables")

    # Create compatibility views
    if not DRY_RUN:
        conn.execute('CREATE VIEW IF NOT EXISTS "a1_записи" AS SELECT * FROM entries WHERE lang="RU"')
    print("  Compatibility view created: a1_записи")

    # ================================================================
    # PHASE 2: BODY → 5 TABLES
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 2: Body 46 → 5 tables")
    print("=" * 70)

    # Create body_data
    conn.execute("""
        CREATE TABLE IF NOT EXISTS body_data (
            body_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            subtable TEXT NOT NULL,
            heptad INTEGER,
            category TEXT,
            arabic TEXT,
            transliteration TEXT,
            english TEXT,
            description TEXT,
            root_letters TEXT,
            aa_root_id TEXT,
            quranic_ref TEXT,
            score REAL,
            status TEXT,
            specific_data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
        )
    """)

    # Create body_cross_refs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS body_cross_refs_unified (
            xref_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            subtable TEXT NOT NULL,
            source_ref TEXT,
            target_ref TEXT,
            relationship TEXT,
            notes TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
        )
    """)

    # Create body_prayer_map
    conn.execute("""
        CREATE TABLE IF NOT EXISTS body_prayer_map (
            prayer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            subtable TEXT NOT NULL,
            prayer TEXT,
            state TEXT,
            arabic TEXT,
            quranic_ref TEXT,
            specific_data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
        )
    """)
    conn.commit()

    # Migrate body data tables
    COMMON_COLS = ['category', 'arabic', 'transliteration', 'english', 'description',
                   'root_letters', 'aa_root_id', 'quranic_ref', 'score', 'status']

    body_data_tables = []
    body_xref_tables = []
    body_prayer_tables = []

    for (tbl,) in conn.execute("""SELECT name FROM sqlite_master WHERE type='table'
        AND (name LIKE 'body_%' OR name LIKE 'sensory_%' OR name LIKE 'nutrition_%'
             OR name LIKE 'healing_%' OR name LIKE 'nafs_%' OR name LIKE 'lifecycle_%'
             OR name LIKE 'heart_%' OR name LIKE 'prayer_%' OR name LIKE 'emotional_%'
             OR name LIKE 'social_%' OR name LIKE 'death_%' OR name LIKE 'perception_%'
             OR name LIKE 'pelvis_%' OR name LIKE 'spirit_%' OR name LIKE 'qalb_%'
             OR name LIKE 'transition_%' OR name LIKE 'therapy_%' OR name LIKE 'food_%'
             OR name LIKE 'agricultural_%')
        AND name NOT LIKE '_retired%'
        AND name != 'body_data' AND name != 'body_cross_refs_unified' AND name != 'body_prayer_map'
        AND name != 'body_heptad_meta' AND name != 'body_extraction_intel'
    """).fetchall():
        if 'cross_ref' in tbl or 'edges' in tbl:
            body_xref_tables.append(tbl)
        elif 'prayer' in tbl and ('map' in tbl or 'state' in tbl or 'transition' in tbl):
            body_prayer_tables.append(tbl)
        else:
            body_data_tables.append(tbl)

    # Determine subsystem from table name
    def get_subsystem(tbl):
        for prefix in ['body_', 'sensory_', 'nutrition_', 'healing_', 'nafs_',
                       'lifecycle_', 'heart_', 'emotional_', 'social_', 'death_',
                       'perception_', 'pelvis_', 'spirit_', 'qalb_', 'transition_',
                       'therapy_', 'food_', 'agricultural_']:
            if tbl.startswith(prefix):
                return prefix.rstrip('_')
        return tbl.split('_')[0]

    # Migrate data tables
    total_migrated = 0
    for tbl in body_data_tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            rows = conn.execute(f'SELECT * FROM "{tbl}"').fetchall()
            subsystem = get_subsystem(tbl)

            for row in rows:
                row_dict = dict(zip(cols, row))

                # Extract common columns
                common_vals = {c: row_dict.get(c) for c in COMMON_COLS}

                # Everything else goes to specific_data
                specific = {k: v for k, v in row_dict.items()
                           if k not in COMMON_COLS and not k.startswith('quf_')
                           and k not in ('rowid_pk',) and v is not None}

                if not DRY_RUN:
                    conn.execute("""
                        INSERT INTO body_data (subsystem, subtable, category, arabic, transliteration,
                            english, description, root_letters, aa_root_id, quranic_ref, score, status,
                            specific_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (subsystem, tbl, common_vals.get('category'), common_vals.get('arabic'),
                          common_vals.get('transliteration'), common_vals.get('english'),
                          common_vals.get('description'), common_vals.get('root_letters'),
                          common_vals.get('aa_root_id'), common_vals.get('quranic_ref'),
                          common_vals.get('score'), common_vals.get('status'),
                          json.dumps(specific, ensure_ascii=False) if specific else None))
                total_migrated += 1
        except Exception as e:
            print(f"  WARN {tbl}: {e}")

    conn.commit()
    print(f"  body_data: {total_migrated} rows from {len(body_data_tables)} tables")

    # Migrate cross-ref tables
    xref_migrated = 0
    for tbl in body_xref_tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            rows = conn.execute(f'SELECT * FROM "{tbl}"').fetchall()
            for row in rows:
                row_dict = dict(zip(cols, row))
                specific = {k: v for k, v in row_dict.items()
                           if not k.startswith('quf_') and k not in ('rowid_pk',) and v is not None}
                if not DRY_RUN:
                    conn.execute("""
                        INSERT INTO body_cross_refs_unified (subsystem, subtable, source_ref, target_ref, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (get_subsystem(tbl), tbl,
                          json.dumps({k: v for k, v in specific.items() if 'source' in k or 'from' in k}, ensure_ascii=False),
                          json.dumps({k: v for k, v in specific.items() if 'target' in k or 'to' in k}, ensure_ascii=False),
                          json.dumps(specific, ensure_ascii=False)))
                xref_migrated += 1
        except Exception as e:
            print(f"  WARN xref {tbl}: {e}")
    conn.commit()
    print(f"  body_cross_refs_unified: {xref_migrated} rows from {len(body_xref_tables)} tables")

    # Migrate prayer tables
    prayer_migrated = 0
    for tbl in body_prayer_tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            rows = conn.execute(f'SELECT * FROM "{tbl}"').fetchall()
            for row in rows:
                row_dict = dict(zip(cols, row))
                specific = {k: v for k, v in row_dict.items()
                           if not k.startswith('quf_') and k not in ('rowid_pk',) and v is not None}
                if not DRY_RUN:
                    conn.execute("""
                        INSERT INTO body_prayer_map (subsystem, subtable, specific_data)
                        VALUES (?, ?, ?)
                    """, (get_subsystem(tbl), tbl, json.dumps(specific, ensure_ascii=False)))
                prayer_migrated += 1
        except Exception as e:
            print(f"  WARN prayer {tbl}: {e}")
    conn.commit()
    print(f"  body_prayer_map: {prayer_migrated} rows from {len(body_prayer_tables)} tables")

    # Retire body tables
    body_retired = 0
    for tbl in body_data_tables + body_xref_tables + body_prayer_tables:
        try:
            if not DRY_RUN:
                conn.execute(f'ALTER TABLE "{tbl}" RENAME TO "_retired_body_{tbl}"')
            body_retired += 1
        except:
            pass
    conn.commit()
    print(f"  Retired {body_retired} body tables")

    # ================================================================
    # PHASE 3: BITIG CLEANUP
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 3: Bitig Cleanup")
    print("=" * 70)

    # Drop empty tables
    for tbl in ['bitig_bridge_xref', 'bitig_dispersal_edges', 'bitig_sibling_propagation']:
        try:
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            if cnt == 0 and not DRY_RUN:
                conn.execute(f'DROP TABLE "{tbl}"')
                print(f"  Dropped {tbl} (empty)")
        except:
            pass

    # Merge corrections + investigation
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bitig_corrections_merged (
                corr_id TEXT,
                source_table TEXT,
                word TEXT,
                issue TEXT,
                resolution TEXT,
                evidence TEXT,
                status TEXT,
                next_step TEXT,
                quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
            )
        """)
        # Copy corrections
        for row in conn.execute('SELECT * FROM bitig_corrections').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_corrections')").fetchall()]
            d = dict(zip(cols, row))
            if not DRY_RUN:
                conn.execute("INSERT INTO bitig_corrections_merged (corr_id, source_table, issue, resolution, evidence, status) VALUES (?, 'corrections', ?, ?, ?, ?)",
                            (d.get('corr_id'), d.get('what_was_wrong'), d.get('corrected_to'), d.get('evidence'), d.get('status')))
        # Copy investigations
        for row in conn.execute('SELECT * FROM bitig_investigation').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_investigation')").fetchall()]
            d = dict(zip(cols, row))
            if not DRY_RUN:
                conn.execute("INSERT INTO bitig_corrections_merged (corr_id, source_table, word, issue, status, next_step) VALUES (?, 'investigation', ?, ?, ?, ?)",
                            (d.get('inv_id'), d.get('word'), d.get('issue'), d.get('status'), d.get('next_step')))
        conn.commit()
        if not DRY_RUN:
            conn.execute('ALTER TABLE bitig_corrections RENAME TO "_retired_bitig_corrections"')
            conn.execute('ALTER TABLE bitig_investigation RENAME TO "_retired_bitig_investigation"')
            conn.execute('ALTER TABLE bitig_corrections_merged RENAME TO bitig_corrections')
        print(f"  Merged bitig_corrections + bitig_investigation → bitig_corrections")
    except Exception as e:
        print(f"  WARN merge corrections: {e}")

    # Merge intelligence_summary + operator_profiles
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bitig_intelligence_merged (
                intel_id TEXT,
                source_table TEXT,
                category TEXT,
                content TEXT,
                period TEXT,
                dp_codes TEXT,
                method TEXT,
                specific_data TEXT,
                quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
            )
        """)
        for row in conn.execute('SELECT * FROM bitig_intelligence_summary').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_intelligence_summary')").fetchall()]
            d = dict(zip(cols, row))
            if not DRY_RUN:
                conn.execute("INSERT INTO bitig_intelligence_merged (intel_id, source_table, category, dp_codes, specific_data) VALUES (?, 'summary', ?, ?, ?)",
                            (d.get('intel_id'), d.get('category'), d.get('dp_code'),
                             json.dumps({k:v for k,v in d.items() if not k.startswith('quf_')}, ensure_ascii=False)))
        for row in conn.execute('SELECT * FROM bitig_operator_profiles').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_operator_profiles')").fetchall()]
            d = dict(zip(cols, row))
            if not DRY_RUN:
                conn.execute("INSERT INTO bitig_intelligence_merged (intel_id, source_table, category, period, method, specific_data) VALUES (?, 'profiles', ?, ?, ?, ?)",
                            (d.get('profile_id'), d.get('role'), d.get('period'), d.get('method'),
                             json.dumps({k:v for k,v in d.items() if not k.startswith('quf_')}, ensure_ascii=False)))
        conn.commit()
        if not DRY_RUN:
            conn.execute('ALTER TABLE bitig_intelligence_summary RENAME TO "_retired_bitig_intel_summary"')
            conn.execute('ALTER TABLE bitig_operator_profiles RENAME TO "_retired_bitig_op_profiles"')
            conn.execute('ALTER TABLE bitig_intelligence_merged RENAME TO bitig_intelligence')
        print(f"  Merged bitig_intelligence_summary + bitig_operator_profiles → bitig_intelligence")
    except Exception as e:
        print(f"  WARN merge intel: {e}")

    conn.commit()

    # ================================================================
    # PHASE 4: FOUNDATION/MECHANISM
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 4: Foundation/Mechanism")
    print("=" * 70)

    # Add lang column to foundation tables
    for tbl in ['f1_two_originals', 'f2_script_downstream', 'f2_decay_criteria',
                'f3_frozen_stage_model', 'f4_decay_gradient', 'f5_destruction_timeline',
                'f6_manuscript_evidence', 'f7_direction_of_flow']:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        if 'lang' not in cols:
            try:
                conn.execute(f'ALTER TABLE "{tbl}" ADD COLUMN lang TEXT DEFAULT "EN"')
                conn.execute(f'UPDATE "{tbl}" SET lang="EN" WHERE lang IS NULL')
            except:
                pass
    conn.commit()
    print("  Foundation tables: lang column added")

    # ================================================================
    # RECREATE TRIGGERS (on surviving tables only)
    # ================================================================
    print("\n" + "=" * 70)
    print("RESTORE: Recreating triggers")
    print("=" * 70)

    # Get surviving table names
    surviving = set(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_retired%'"
    ).fetchall())

    trg_ok = 0
    trg_skip = 0
    for tname, tsql in all_triggers:
        if not tsql:
            continue
        # Check if the trigger's table still exists
        tbl_match = None
        for tbl in surviving:
            if f'ON [{tbl}]' in tsql or f'ON "{tbl}"' in tsql:
                tbl_match = tbl
                break
        if tbl_match and not DRY_RUN:
            try:
                conn.execute(tsql)
                trg_ok += 1
            except:
                trg_skip += 1
        else:
            trg_skip += 1
    conn.commit()
    print(f"  Recreated: {trg_ok}, Skipped (retired tables): {trg_skip}")

    # ================================================================
    # VERIFY
    # ================================================================
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    tables_after = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_retired%' AND name NOT LIKE 'entries_fts%'"
    ).fetchone()[0]
    retired_count = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE '_retired%'"
    ).fetchone()[0]
    triggers_after = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]

    # Data verification
    if not DRY_RUN:
        ru_in_entries = conn.execute("SELECT COUNT(*) FROM entries WHERE lang='RU'").fetchone()[0]
        body_data_count = conn.execute("SELECT COUNT(*) FROM body_data").fetchone()[0]
        body_subsystems = conn.execute("SELECT COUNT(DISTINCT subsystem) FROM body_data").fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    else:
        ru_in_entries = body_data_count = body_subsystems = 0
        integrity = 'DRY RUN'

    db_size = os.path.getsize(DB) / 1024 / 1024

    print(f"  Active tables: {tables_after}")
    print(f"  Retired tables: {retired_count}")
    print(f"  Triggers: {triggers_after}")
    print(f"  entries WHERE lang='RU': {ru_in_entries}")
    print(f"  body_data rows: {body_data_count}")
    print(f"  body_data subsystems: {body_subsystems}")
    print(f"  Integrity: {integrity}")
    print(f"  DB size: {db_size:.1f} MB")

    print(f"\n{'=' * 70}")
    print(f"CONSOLIDATION {'COMPLETE' if not DRY_RUN else 'DRY RUN COMPLETE'}")
    print(f"Finished: {datetime.now().isoformat()}")
    print(f"{'=' * 70}")

    conn.close()


def _migrate_ru_table(conn, ru_tbl, en_tbl, col_map):
    """Generic RU → EN migration with column mapping."""
    try:
        ru_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru_tbl}')").fetchall()]
        en_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{en_tbl}')").fetchall()]
        rows = conn.execute(f'SELECT * FROM "{ru_tbl}"').fetchall()

        # Add lang column if missing
        if 'lang' not in en_cols:
            conn.execute(f'ALTER TABLE "{en_tbl}" ADD COLUMN lang TEXT DEFAULT "EN"')
            conn.execute(f'UPDATE "{en_tbl}" SET lang="EN" WHERE lang IS NULL')

        migrated = 0
        for row in rows:
            row_dict = dict(zip(ru_cols, row))
            en_vals = {'lang': 'RU'}
            for ru_name, value in row_dict.items():
                if ru_name.startswith('quf_'):
                    en_vals[ru_name] = value
                elif ru_name in col_map and col_map[ru_name] in en_cols:
                    en_vals[col_map[ru_name]] = value

            if en_vals and not DRY_RUN:
                cols_str = ', '.join(f'"{k}"' for k in en_vals.keys())
                placeholders = ', '.join('?' * len(en_vals))
                try:
                    conn.execute(f'INSERT INTO "{en_tbl}" ({cols_str}) VALUES ({placeholders})',
                                list(en_vals.values()))
                    migrated += 1
                except:
                    pass
        conn.commit()
        print(f"  {ru_tbl} → {en_tbl}: {migrated}/{len(rows)} rows")
    except Exception as e:
        print(f"  WARN {ru_tbl}: {e}")


def _merge_generic_ru(conn, ru_tbl, en_tbl):
    """Merge generic RU table into EN parent using JSON data column."""
    try:
        ru_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru_tbl}')").fetchall()]
        en_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{en_tbl}')").fetchall()]
        rows = conn.execute(f'SELECT * FROM "{ru_tbl}"').fetchall()

        if 'lang' not in en_cols:
            conn.execute(f'ALTER TABLE "{en_tbl}" ADD COLUMN lang TEXT DEFAULT "EN"')
            conn.execute(f'UPDATE "{en_tbl}" SET lang="EN" WHERE lang IS NULL')

        for row in rows:
            row_dict = {ru_cols[i]: row[i] for i in range(len(ru_cols)) if not ru_cols[i].startswith('quf_')}
            # Try to insert mapped values; store unmappable as JSON in notes
            if not DRY_RUN:
                if 'notes' not in en_cols:
                    conn.execute(f'ALTER TABLE "{en_tbl}" ADD COLUMN notes TEXT')
                    en_cols.append('notes')
                conn.execute(f'INSERT INTO "{en_tbl}" (lang, notes) VALUES ("RU", ?)',
                            (json.dumps(row_dict, ensure_ascii=False),))
        conn.commit()
        print(f"  {ru_tbl} → {en_tbl}: {len(rows)} rows (as JSON)")
    except Exception as e:
        print(f"  WARN {ru_tbl}: {e}")


if __name__ == "__main__":
    run()
