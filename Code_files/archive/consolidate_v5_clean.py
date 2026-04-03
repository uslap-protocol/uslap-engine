#!/usr/bin/env python3
"""
USLaP Schema Consolidation v5 — Clean
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Verified state:
  VIEWS (already migrated, skip): a1_записи, a3_quran_refs, a6_country_names, a1_entries
  TABLES to migrate: a2_имена_аллаха(19), a3_коранические_ссылки(32), a4_производные(171),
                     a5_перекрёстные_ссылки(184), a6_названия_стран(3)
  Foundation RU: 8 tables (~57 rows)
  Mechanism RU: 5 tables (~65 rows)
  Body: 46 tables → 5
  Bitig: drop 3 empty, merge 2 pairs
"""

import sqlite3, json, os, sys
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

def is_table(conn, name):
    r = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (name,)).fetchone()
    return r and r[0] == 'table'

def safe_exec(conn, sql, params=(), label=""):
    try:
        conn.execute(sql, params)
        return True
    except Exception as e:
        print(f"  WARN {label}: {e}")
        return False

def add_lang_col(conn, tbl):
    if not is_table(conn, tbl):
        return
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
    if 'lang' not in cols:
        conn.execute(f'ALTER TABLE "{tbl}" ADD COLUMN lang TEXT DEFAULT "EN"')
        conn.execute(f'UPDATE "{tbl}" SET lang="EN" WHERE lang IS NULL')

def migrate_ru(conn, ru_tbl, en_tbl, col_map):
    """Migrate RU table → EN parent with column mapping."""
    if not is_table(conn, ru_tbl):
        print(f"  {ru_tbl}: VIEW or missing — skip")
        return 0
    add_lang_col(conn, en_tbl)
    ru_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru_tbl}')").fetchall()]
    en_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{en_tbl}')").fetchall()]
    rows = conn.execute(f'SELECT * FROM "{ru_tbl}"').fetchall()
    migrated = 0
    for row in rows:
        rd = dict(zip(ru_cols, row))
        vals = {'lang': 'RU'}
        for ru_name, val in rd.items():
            if ru_name.startswith('quf_'):
                continue
            en_name = col_map.get(ru_name)
            if en_name and en_name in en_cols:
                vals[en_name] = val
        if len(vals) > 1:
            ks = ', '.join(f'"{k}"' for k in vals)
            ps = ', '.join('?' * len(vals))
            if safe_exec(conn, f'INSERT INTO "{en_tbl}" ({ks}) VALUES ({ps})', list(vals.values()), ru_tbl):
                migrated += 1
    conn.execute(f'ALTER TABLE "{ru_tbl}" RENAME TO "_retired_v5_{ru_tbl}"')
    conn.commit()
    print(f"  {ru_tbl} → {en_tbl}: {migrated}/{len(rows)}")
    return migrated

def migrate_foundation_ru(conn, ru_tbl, en_tbl):
    """Merge foundation RU → EN parent as JSON in notes."""
    if not is_table(conn, ru_tbl):
        return
    add_lang_col(conn, en_tbl)
    en_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{en_tbl}')").fetchall()]
    if 'ru_data' not in en_cols:
        conn.execute(f'ALTER TABLE "{en_tbl}" ADD COLUMN ru_data TEXT')
    ru_cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru_tbl}')").fetchall()]
    rows = conn.execute(f'SELECT * FROM "{ru_tbl}"').fetchall()
    for row in rows:
        rd = {ru_cols[i]: row[i] for i in range(len(ru_cols)) if not ru_cols[i].startswith('quf_') and row[i]}
        conn.execute(f'INSERT INTO "{en_tbl}" (lang, ru_data) VALUES ("RU", ?)',
                    (json.dumps(rd, ensure_ascii=False),))
    conn.execute(f'ALTER TABLE "{ru_tbl}" RENAME TO "_retired_v5_{ru_tbl}"')
    conn.commit()
    print(f"  {ru_tbl} → {en_tbl}: {len(rows)} rows")

def run():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF")
    now = datetime.now().isoformat()

    print("=" * 70)
    print(f"Schema Consolidation v5 — {now}")
    print("=" * 70)

    # Save + drop triggers
    triggers = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
    print(f"\n[PREP] {len(triggers)} triggers saved")
    for t, _ in triggers:
        conn.execute(f'DROP TRIGGER IF EXISTS "{t}"')
    conn.commit()

    # Drop existing compat views
    for v in ['a1_записи', 'a1_entries', 'a3_quran_refs', 'a6_country_names']:
        r = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (v,)).fetchone()
        if r and r[0] == 'view':
            conn.execute(f'DROP VIEW IF EXISTS "{v}"')
            print(f"  Dropped view: {v}")
    conn.commit()

    # ════════ PHASE 1: RU MIRRORS ════════
    print("\n[PHASE 1] RU Mirrors")

    # a1_записи was already a view → data in entries. Just need lang column.
    add_lang_col(conn, 'entries')
    conn.commit()
    print("  entries: lang column ensured (a1_записи was already view)")

    migrate_ru(conn, 'a2_имена_аллаха', 'names_of_allah',
               {'имя_id': 'allah_id', 'арабское_имя': 'arabic_name', 'транслитерация': 'transliteration',
                'значение': 'meaning', 'коран_ссылка': 'qur_ref', 'записи_id': 'entry_ids', 'корень_id': 'root_id'})

    # a3_коранические_ссылки → quran_refs (the actual table, not the view)
    migrate_ru(conn, 'a3_коранические_ссылки', 'quran_refs',
               {'ссылка_id': 'ref_id', 'сура': 'surah', 'аят': 'ayah', 'арабский_текст': 'arabic_text',
                'кв_id': 'qv_id', 'слой': 'layer_ref', 'записи_id': 'entry_ids',
                'сеть_id': 'network_id', 'релевантность': 'relevance'})

    migrate_ru(conn, 'a4_производные', 'a4_derivatives',
               {'произв_id': 'deriv_id', 'запись_id': 'entry_id', 'рус_термин': 'en_term',
                'производное': 'derivative', 'тип_связи': 'link_type'})

    migrate_ru(conn, 'a5_перекрёстные_ссылки', 'a5_cross_refs',
               {'перекр_id': 'xref_id', 'от_id': 'from_id', 'к_id': 'to_id',
                'тип_связи': 'link_type', 'описание': 'description', 'слой': 'layer_ref'})

    migrate_ru(conn, 'a6_названия_стран', 'country_names',
               {'страна_id': 'country_id', 'название_страны': 'country_name', 'корень_id': 'root_id',
                'слово_al': 'al_word', 'корень_al': 'al_root', 'коранич_значение': 'qur_meaning',
                'фонетическая_цепь': 'phonetic_chain', 'основание_названия': 'naming_basis',
                'запись_ids': 'entry_ids', 'примечания': 'notes'})

    # Foundation RU
    for ru, en in [('f1_один_источник_два_коридора', 'f1_two_originals'),
                   ('f2_нисходящий_поток', 'f2_script_downstream'),
                   ('f2_критерии_деградации', 'f2_decay_criteria'),
                   ('f3_модель_застывших_стадий', 'f3_frozen_stage_model'),
                   ('f4_градиент_деградации', 'f4_decay_gradient'),
                   ('f5_хронология_уничтожения', 'f5_destruction_timeline'),
                   ('f6_рукописные_свидетельства', 'f6_manuscript_evidence'),
                   ('f7_направление_потока', 'f7_direction_of_flow')]:
        migrate_foundation_ru(conn, ru, en)

    # Mechanism RU → mechanism_data
    conn.execute("""CREATE TABLE IF NOT EXISTS mechanism_data (
        mech_id INTEGER PRIMARY KEY AUTOINCREMENT, layer TEXT, lang TEXT DEFAULT 'RU',
        data TEXT, quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT)""")
    for ru, layer in [('m1_фонетические_сдвиги','m1'), ('m2_паттерны_обнаружения','m2'),
                      ('m3_учёные','m3'), ('m4_сети','m4'), ('m5_коранич_верификация','m5')]:
        if is_table(conn, ru):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{ru}')").fetchall()]
            rows = conn.execute(f'SELECT * FROM "{ru}"').fetchall()
            for row in rows:
                rd = {cols[i]: row[i] for i in range(len(cols)) if not cols[i].startswith('quf_') and row[i]}
                conn.execute("INSERT INTO mechanism_data (layer, data) VALUES (?, ?)",
                            (layer, json.dumps(rd, ensure_ascii=False)))
            conn.execute(f'ALTER TABLE "{ru}" RENAME TO "_retired_v5_{ru}"')
            print(f"  {ru} → mechanism_data: {len(rows)} rows")
    conn.commit()

    # Recreate compat views
    conn.execute('CREATE VIEW "a1_записи" AS SELECT entry_id AS запись_id, score AS балл, ru_term AS рус_термин, ar_word AS ар_слово, root_id AS корень_id, root_letters AS корневые_буквы, qur_meaning AS коранич_значение, pattern AS паттерн, inversion_type AS тип_инверсии, network_id AS сеть_id, allah_name_id AS имя_аллаха_id, phonetic_chain AS фонетическая_цепь, source_form AS исходная_форма, foundation_refs AS основание FROM entries WHERE lang IS NULL OR lang="EN"')
    conn.execute('CREATE VIEW a1_entries AS SELECT * FROM entries')
    conn.commit()
    print("  Compat views created: a1_записи, a1_entries")

    # ════════ PHASE 2: BODY → 5 TABLES ════════
    print("\n[PHASE 2] Body Consolidation")

    conn.execute("""CREATE TABLE IF NOT EXISTS body_data (
        body_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subsystem TEXT NOT NULL, subtable TEXT NOT NULL, heptad INTEGER,
        category TEXT, arabic TEXT, transliteration TEXT, english TEXT,
        description TEXT, root_letters TEXT, aa_root_id TEXT, quranic_ref TEXT,
        score REAL, status TEXT, specific_data TEXT,
        quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS body_cross_refs_unified (
        xref_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subsystem TEXT, subtable TEXT, data TEXT,
        quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS body_prayer_map_unified (
        prayer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subsystem TEXT, subtable TEXT, data TEXT,
        quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT)""")

    COMMON = ['category','arabic','transliteration','english','description',
              'root_letters','aa_root_id','quranic_ref','score','status']

    body_tables = [r[0] for r in conn.execute("""SELECT name FROM sqlite_master WHERE type='table'
        AND (name LIKE 'body_%' OR name LIKE 'sensory_%' OR name LIKE 'nutrition_%'
             OR name LIKE 'healing_%' OR name LIKE 'nafs_%' OR name LIKE 'lifecycle_%'
             OR name LIKE 'heart_%' OR name LIKE 'prayer_%' OR name LIKE 'emotional_%'
             OR name LIKE 'social_%' OR name LIKE 'death_%' OR name LIKE 'perception_%'
             OR name LIKE 'pelvis_%' OR name LIKE 'spirit_%' OR name LIKE 'qalb_%'
             OR name LIKE 'transition_%' OR name LIKE 'therapy_%' OR name LIKE 'food_%'
             OR name LIKE 'agricultural_%')
        AND name NOT LIKE '_retired%'
        AND name NOT IN ('body_data','body_cross_refs_unified','body_prayer_map_unified',
                         'body_heptad_meta','body_extraction_intel')""").fetchall()]

    data_count = xref_count = prayer_count = 0
    for tbl in body_tables:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        rows = conn.execute(f'SELECT * FROM "{tbl}"').fetchall()
        if not rows:
            conn.execute(f'DROP TABLE "{tbl}"')
            continue

        subsystem = tbl.split('_')[0]
        is_xref = 'cross_ref' in tbl or 'edges' in tbl
        is_prayer = 'prayer' in tbl and ('map' in tbl or 'state' in tbl or 'transition' in tbl)

        for row in rows:
            rd = dict(zip(cols, row))
            if is_xref:
                data = {k: v for k, v in rd.items() if not k.startswith('quf_') and k != 'rowid_pk' and v}
                conn.execute("INSERT INTO body_cross_refs_unified (subsystem, subtable, data) VALUES (?,?,?)",
                            (subsystem, tbl, json.dumps(data, ensure_ascii=False)))
                xref_count += 1
            elif is_prayer:
                data = {k: v for k, v in rd.items() if not k.startswith('quf_') and k != 'rowid_pk' and v}
                conn.execute("INSERT INTO body_prayer_map_unified (subsystem, subtable, data) VALUES (?,?,?)",
                            (subsystem, tbl, json.dumps(data, ensure_ascii=False)))
                prayer_count += 1
            else:
                common_vals = {c: rd.get(c) for c in COMMON}
                specific = {k: v for k, v in rd.items()
                           if k not in COMMON and not k.startswith('quf_') and k != 'rowid_pk' and v is not None}
                conn.execute("""INSERT INTO body_data (subsystem, subtable, category, arabic, transliteration,
                    english, description, root_letters, aa_root_id, quranic_ref, score, status, specific_data)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (subsystem, tbl, common_vals.get('category'), common_vals.get('arabic'),
                     common_vals.get('transliteration'), common_vals.get('english'),
                     common_vals.get('description'), common_vals.get('root_letters'),
                     common_vals.get('aa_root_id'), common_vals.get('quranic_ref'),
                     common_vals.get('score'), common_vals.get('status'),
                     json.dumps(specific, ensure_ascii=False) if specific else None))
                data_count += 1

        conn.execute(f'ALTER TABLE "{tbl}" RENAME TO "_retired_body_{tbl}"')

    conn.commit()
    print(f"  body_data: {data_count} rows")
    print(f"  body_cross_refs_unified: {xref_count} rows")
    print(f"  body_prayer_map_unified: {prayer_count} rows")
    print(f"  Retired: {len(body_tables)} body tables")

    # ════════ PHASE 3: BITIG ════════
    print("\n[PHASE 3] Bitig Cleanup")

    for tbl in ['bitig_bridge_xref', 'bitig_dispersal_edges', 'bitig_sibling_propagation']:
        if is_table(conn, tbl):
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            if cnt == 0:
                conn.execute(f'DROP TABLE "{tbl}"')
                print(f"  Dropped empty: {tbl}")

    # Merge corrections + investigation
    if is_table(conn, 'bitig_corrections') and is_table(conn, 'bitig_investigation'):
        conn.execute("""CREATE TABLE bitig_corrections_new (
            corr_id TEXT, source TEXT, word TEXT, issue TEXT, resolution TEXT,
            evidence TEXT, status TEXT, next_step TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT)""")
        for row in conn.execute('SELECT * FROM bitig_corrections').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_corrections')").fetchall()]
            d = dict(zip(cols, row))
            conn.execute("INSERT INTO bitig_corrections_new (corr_id,source,issue,resolution,evidence,status) VALUES (?,'corrections',?,?,?,?)",
                        (d.get('corr_id'), d.get('what_was_wrong'), d.get('corrected_to'), d.get('evidence'), d.get('status')))
        for row in conn.execute('SELECT * FROM bitig_investigation').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_investigation')").fetchall()]
            d = dict(zip(cols, row))
            conn.execute("INSERT INTO bitig_corrections_new (corr_id,source,word,issue,status,next_step) VALUES (?,'investigation',?,?,?,?)",
                        (d.get('inv_id'), d.get('word'), d.get('issue'), d.get('status'), d.get('next_step')))
        conn.execute('ALTER TABLE bitig_corrections RENAME TO "_retired_bitig_corrections"')
        conn.execute('ALTER TABLE bitig_investigation RENAME TO "_retired_bitig_investigation"')
        conn.execute('ALTER TABLE bitig_corrections_new RENAME TO bitig_corrections')
        conn.commit()
        print("  Merged: bitig_corrections + bitig_investigation")

    # Merge intel + profiles
    if is_table(conn, 'bitig_intelligence_summary') and is_table(conn, 'bitig_operator_profiles'):
        conn.execute("""CREATE TABLE bitig_intelligence (
            intel_id TEXT, source TEXT, category TEXT, content TEXT, period TEXT,
            dp_codes TEXT, method TEXT, data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT)""")
        for row in conn.execute('SELECT * FROM bitig_intelligence_summary').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_intelligence_summary')").fetchall()]
            d = dict(zip(cols, row))
            conn.execute("INSERT INTO bitig_intelligence (intel_id,source,category,dp_codes,data) VALUES (?,'summary',?,?,?)",
                        (d.get('intel_id'), d.get('category'), d.get('dp_code'),
                         json.dumps({k:v for k,v in d.items() if not k.startswith('quf_') and v}, ensure_ascii=False)))
        for row in conn.execute('SELECT * FROM bitig_operator_profiles').fetchall():
            cols = [r[1] for r in conn.execute("PRAGMA table_info('bitig_operator_profiles')").fetchall()]
            d = dict(zip(cols, row))
            conn.execute("INSERT INTO bitig_intelligence (intel_id,source,category,period,method,data) VALUES (?,'profiles',?,?,?,?)",
                        (d.get('profile_id'), d.get('role'), d.get('period'), d.get('method'),
                         json.dumps({k:v for k,v in d.items() if not k.startswith('quf_') and v}, ensure_ascii=False)))
        conn.execute('ALTER TABLE bitig_intelligence_summary RENAME TO "_retired_bitig_intel_summary"')
        conn.execute('ALTER TABLE bitig_operator_profiles RENAME TO "_retired_bitig_op_profiles"')
        conn.commit()
        print("  Merged: bitig_intelligence_summary + bitig_operator_profiles")

    # ════════ RECREATE TRIGGERS ════════
    print("\n[TRIGGERS] Recreating...")
    surviving = set(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_retired%'").fetchall())
    ok = skip = 0
    for tname, tsql in triggers:
        if not tsql: continue
        table_exists = any(f'[{t}]' in tsql or f'"{t}"' in tsql for t in surviving)
        if table_exists:
            try:
                conn.execute(tsql)
                ok += 1
            except: skip += 1
        else: skip += 1
    conn.commit()
    print(f"  OK: {ok}, Skipped: {skip}")

    # ════════ VERIFY ════════
    print("\n[VERIFY]")
    active = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE '_retired%' AND name NOT LIKE 'sqlite%' AND name NOT LIKE 'entries_fts%'").fetchone()[0]
    retired = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE '_retired%'").fetchone()[0]
    trigs = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    body = conn.execute("SELECT COUNT(*) FROM body_data").fetchone()[0]
    subs = conn.execute("SELECT COUNT(DISTINCT subsystem) FROM body_data").fetchone()[0]
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    size = os.path.getsize(DB) / 1024 / 1024

    print(f"  Active tables: {active}")
    print(f"  Retired: {retired}")
    print(f"  Triggers: {trigs}")
    print(f"  body_data: {body} rows, {subs} subsystems")
    print(f"  Integrity: {integrity}")
    print(f"  DB: {size:.1f} MB")
    print(f"\n{'='*70}\nDONE — {datetime.now().isoformat()}\n{'='*70}")
    conn.close()

if __name__ == "__main__":
    run()
