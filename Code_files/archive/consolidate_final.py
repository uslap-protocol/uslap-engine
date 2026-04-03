#!/usr/bin/env python3
"""
USLaP Schema Consolidation — Final Clean Script
Reduces 186 tables → ~130 by merging RU duplicates into EN tables
and dropping retired tables.

Strategy:
  Phase 1: Backup triggers + views SQL, then drop all views
  Phase 2: Names of Allah — add RU columns to EN table, UPDATE from RU
  Phase 3: A3/A4/A5/A6 — add lang column to EN, INSERT RU rows with new PKs
  Phase 4: Foundation F1-F7 — add lang column, INSERT RU rows
  Phase 5: Mechanism M1-M5 — add lang column, INSERT RU rows
  Phase 6: Drop retired tables
  Phase 7: Recreate views with correct definitions
  Phase 8: Restore contamination triggers
"""

import sqlite3, os, sys, json
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")

# Column mappings: RU column → EN column (for Foundation/Mechanism merges)
F1_MAP = [
    ("ориг_id", "orig_id"), ("название", "name"), ("арабское_имя", "arabic_name"),
    ("авторитет", "authority"), ("буквы", "letters"), ("тип_письма", "script_type"),
    ("самоназвание", "self_naming"), ("коран_ссылка", "qur_ref"), ("тип_доказательства", "proof_type"),
]
F2_DS_MAP = [
    ("письмо_id", "script_id"), ("название", "name"), ("источник", "source"),
    ("дата", "date"), ("статус", "status"), ("механизм", "mechanism"),
    ("доказательства", "evidence"), ("уровень_деградации", "decay_level"), ("ссылка", "lattice_ref"),
]
F2_DC_MAP = [
    ("уровень", "level"), ("критерии", "criteria"), ("пример_ds", "example_ds"),
    ("измеримый_тест", "measurable_test"),
]
F3_MAP = [
    ("стадия", "stage"), ("эволюция_амб", "asb_evolution"), ("восточная_граница", "eastern_terminus"),
    ("значение", "meaning"), ("статус", "status"),
]
F4_MAP = [
    ("ранг", "rank"), ("язык", "language"), ("пример", "example"),
    ("морфемы", "morphemes"), ("русский_эквивалент", "english_equiv"),
    ("расстояние_от_источника", "distance_from_source"), ("тип", "type"),
]
F5_MAP = [
    ("дата", "date"), ("уничтожитель", "destroyer"), ("что_произошло", "what_happened"),
    ("что_утрачено", "what_lost"), ("чем_заменено", "replaced_with"), ("примечание_uslap", "uslap_note"),
]
F6_MAP = [
    ("свид_id", "evidence_id"), ("тип", "type"), ("местоположение", "location"),
    ("расст_мин_км", "distance_min_km"), ("расст_макс_км", "distance_max_km"),
    ("дата", "date"), ("описание", "description"), ("контаминация", "contamination"),
    ("ссылка", "lattice_ref"),
]
F7_MAP = [
    ("домен", "domain"), ("реальный_поток", "actual_flow"),
    ("перевёрнутое_утверждение", "reversed_claim"), ("опровержение", "refutation"),
    ("ссылка", "lattice_ref"),
]
M5_MAP = [
    ("кв_id", "qv_id"), ("название", "name"), ("механизм", "mechanism"),
    ("описание", "description"), ("маркеры", "markers"), ("коран_ссылки", "qur_refs"),
    ("контрастные_ссылки", "contrast_refs"), ("основание", "foundation_ref"),
]

# M1 RU has different schema than shift_lookup — it's a full descriptions table
# M2, M3, M4 have no EN base tables (phonetic_shifts, detection_patterns, scholars, networks don't exist)
# These RU tables ARE the only copy of the data — keep them as-is but rename to EN names

FOUNDATION_MERGES = [
    ("f1_один_источник_два_коридора", "f1_two_originals", F1_MAP),
    ("f2_нисходящий_поток", "f2_script_downstream", F2_DS_MAP),
    ("f2_критерии_деградации", "f2_decay_criteria", F2_DC_MAP),
    ("f3_модель_застывших_стадий", "f3_frozen_stage_model", F3_MAP),
    ("f4_градиент_деградации", "f4_decay_gradient", F4_MAP),
    ("f5_хронология_уничтожения", "f5_destruction_timeline", F5_MAP),
    ("f6_рукописные_свидетельства", "f6_manuscript_evidence", F6_MAP),
    ("f7_направление_потока", "f7_direction_of_flow", F7_MAP),
]

M5_MERGE = ("m5_коранич_верификация", "m5_qur_verification", M5_MAP)

# RU tables to rename (no EN counterpart exists)
RU_RENAME = {
    "m1_фонетические_сдвиги": "m1_shift_descriptions",
    "m2_паттерны_обнаружения": "m2_detection_patterns",
    "m3_учёные": "m3_scholars",
    "m4_сети": "m4_networks",
}

# Retired tables to drop
RETIRED = [
    "_retired_xlsx_att_terms", "_retired_xlsx_child_schema", "_retired_xlsx_dp_register",
    "_retired_xlsx_phonetic_reversal", "_retired_xlsx_protocol_corrections",
    "_retired_xlsx_scholar_warnings", "_retired_xlsx_session_index", "_retired_xlsx_umd_operations",
]


def run(dry=False):
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF;")
    cur = conn.cursor()

    dropped_tables = []

    # ─── Phase 1: Save and drop ALL views + ALL triggers ───
    print("\n=== Phase 1: Drop all views and triggers ===")
    views = cur.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name").fetchall()
    triggers = cur.execute("SELECT name, sql, tbl_name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()
    print(f"  Saving {len(views)} views, {len(triggers)} triggers...")

    if not dry:
        for vname, vsql in views:
            cur.execute(f'DROP VIEW IF EXISTS [{vname}]')
        print(f"  Dropped {len(views)} views")

        for tname, tsql, ttbl in triggers:
            cur.execute(f'DROP TRIGGER IF EXISTS [{tname}]')
        print(f"  Dropped {len(triggers)} triggers")
    else:
        print(f"  [DRY] Would drop {len(views)} views and {len(triggers)} triggers")

    # ─── Phase 2: Names of Allah — add RU columns ───
    print("\n=== Phase 2: Names of Allah — merge RU into EN ===")
    # RU a2 has: имя_id, арабское_имя, транслитерация, значение, коран_ссылка, записи_id, корень_id + QUF
    # EN has: allah_id, arabic_name, transliteration, meaning, qur_ref, entry_ids, root_id + QUF
    # Add ru_meaning, ru_transliteration to EN table

    ru_names = cur.execute("SELECT имя_id, транслитерация, значение FROM a2_имена_аллаха").fetchall()
    print(f"  RU Names: {len(ru_names)} rows")

    if not dry:
        try:
            cur.execute("ALTER TABLE names_of_allah ADD COLUMN ru_transliteration TEXT")
            print("  Added ru_transliteration column")
        except sqlite3.OperationalError:
            print("  ru_transliteration column already exists")
        try:
            cur.execute("ALTER TABLE names_of_allah ADD COLUMN ru_meaning TEXT")
            print("  Added ru_meaning column")
        except sqlite3.OperationalError:
            print("  ru_meaning column already exists")

        updated = 0
        for имя_id, translit, meaning in ru_names:
            cur.execute("""UPDATE names_of_allah
                          SET ru_transliteration = ?, ru_meaning = ?
                          WHERE allah_id = ?""", (translit, meaning, имя_id))
            if cur.rowcount > 0:
                updated += 1
        print(f"  Updated {updated}/{len(ru_names)} names")
        cur.execute("DROP TABLE IF EXISTS a2_имена_аллаха")
        dropped_tables.append("a2_имена_аллаха")
        print("  Dropped a2_имена_аллаха")
    else:
        print(f"  [DRY] Would add ru_transliteration, ru_meaning columns and update {len(ru_names)} rows")

    # ─── Phase 3: A3/A4/A5/A6 — add lang column, INSERT RU rows ───
    print("\n=== Phase 3: A3-A6 — merge RU into EN ===")

    # A3: quran_refs (EN=226 rows) ← a3_коранические_ссылки (RU=32 rows)
    # RU cols: ссылка_id, сура, аят, арабский_текст, релевантность, записи_id, сеть_id, слой, кв_id, quf*
    # EN cols: ref_id, surah, ayah, arabic_text, transliteration, translation, relevance, entry_ids, network_id, layer_ref, qv_id, created_at, quf*
    a3_ru = cur.execute("""SELECT ссылка_id, сура, аят, арабский_текст, релевантность,
                                  записи_id, сеть_id, слой, кв_id,
                                  quf_q, quf_u, quf_f, quf_pass, quf_date
                           FROM a3_коранические_ссылки""").fetchall()
    print(f"  A3 quran_refs: EN={cur.execute('SELECT COUNT(*) FROM quran_refs').fetchone()[0]}, RU={len(a3_ru)}")

    if not dry:
        try:
            cur.execute("ALTER TABLE quran_refs ADD COLUMN lang TEXT DEFAULT 'EN'")
            print("  Added lang column to quran_refs")
        except sqlite3.OperationalError:
            print("  lang column already exists on quran_refs")

        max_pk = cur.execute("SELECT MAX(CAST(REPLACE(ref_id,'QR','') AS INTEGER)) FROM quran_refs").fetchone()[0] or 0
        inserted = 0
        for row in a3_ru:
            max_pk += 1
            new_pk = f"QR{max_pk:04d}"
            # Map: сура→surah, аят→ayah, арабский_текст→arabic_text, релевантность→relevance,
            #       записи_id→entry_ids, сеть_id→network_id, слой→layer_ref, кв_id→qv_id
            vals = (new_pk, row[1], row[2], row[3], None, None, row[4],
                    row[5], row[6], row[7], row[8],
                    row[9], row[10], row[11], row[12], row[13], "RU")
            try:
                cur.execute("""INSERT INTO quran_refs
                    (ref_id, surah, ayah, arabic_text, transliteration, translation, relevance,
                     entry_ids, network_id, layer_ref, qv_id,
                     quf_q, quf_u, quf_f, quf_pass, quf_date, lang)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip A3 row {row[0]}: {e}")
        print(f"  Inserted {inserted} RU rows into quran_refs")
        cur.execute("DROP TABLE IF EXISTS a3_коранические_ссылки")
        dropped_tables.append("a3_коранические_ссылки")
    else:
        print(f"  [DRY] Would merge {len(a3_ru)} RU rows into quran_refs")

    # A4: a4_derivatives (EN=6293) ← a4_производные (RU=171)
    a4_ru = cur.execute("SELECT * FROM a4_производные").fetchall()
    print(f"  A4 derivatives: EN={cur.execute('SELECT COUNT(*) FROM a4_derivatives').fetchone()[0]}, RU={len(a4_ru)}")

    if not dry:
        try:
            cur.execute("ALTER TABLE a4_derivatives ADD COLUMN lang TEXT DEFAULT 'EN'")
            print("  Added lang column to a4_derivatives")
        except sqlite3.OperationalError:
            print("  lang column already exists on a4_derivatives")

        max_d = cur.execute("SELECT MAX(CAST(REPLACE(deriv_id,'D','') AS INTEGER)) FROM a4_derivatives").fetchone()[0] or 0
        inserted = 0
        for row in a4_ru:
            max_d += 1
            new_pk = f"D{max_d:05d}"
            # RU schema: произв_id, запись_id, рус_термин, производное, тип_связи, quf_q..quf_date
            # EN schema: deriv_id, entry_id, en_term, derivative, link_type, col_5, col_6, quf_token, quf_q..quf_date
            ru_data = list(row[1:])  # skip RU PK
            # Map: запись_id→entry_id, рус_термин→en_term, производное→derivative, тип_связи→link_type
            en_vals = [
                new_pk,           # deriv_id
                ru_data[0],       # entry_id (запись_id)
                ru_data[1],       # en_term (рус_термин)
                ru_data[2],       # derivative (производное)
                ru_data[3],       # link_type (тип_связи)
                None,             # col_5
                None,             # col_6
                None,             # quf_token
                ru_data[4] if len(ru_data) > 4 else None,  # quf_q
                ru_data[5] if len(ru_data) > 5 else None,  # quf_u
                ru_data[6] if len(ru_data) > 6 else None,  # quf_f
                ru_data[7] if len(ru_data) > 7 else None,  # quf_pass
                ru_data[8] if len(ru_data) > 8 else None,  # quf_date
                "RU",             # lang
            ]
            try:
                cur.execute("""INSERT INTO a4_derivatives
                    (deriv_id, entry_id, en_term, derivative, link_type, col_5, col_6,
                     quf_token, quf_q, quf_u, quf_f, quf_pass, quf_date, lang)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", en_vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip A4 row {row[0]}: {e}")
        print(f"  Inserted {inserted} RU rows into a4_derivatives")
        cur.execute("DROP TABLE IF EXISTS a4_производные")
        dropped_tables.append("a4_производные")
    else:
        print(f"  [DRY] Would merge {len(a4_ru)} RU rows into a4_derivatives")

    # A5: a5_cross_refs (EN=892) ← a5_перекрёстные_ссылки (RU=184)
    a5_ru = cur.execute("SELECT * FROM a5_перекрёстные_ссылки").fetchall()
    print(f"  A5 cross_refs: EN={cur.execute('SELECT COUNT(*) FROM a5_cross_refs').fetchone()[0]}, RU={len(a5_ru)}")

    if not dry:
        try:
            cur.execute("ALTER TABLE a5_cross_refs ADD COLUMN lang TEXT DEFAULT 'EN'")
            print("  Added lang column to a5_cross_refs")
        except sqlite3.OperationalError:
            print("  lang column already exists on a5_cross_refs")

        max_x = cur.execute("SELECT MAX(CAST(REPLACE(xref_id,'X','') AS INTEGER)) FROM a5_cross_refs").fetchone()[0] or 0
        inserted = 0
        for row in a5_ru:
            max_x += 1
            new_pk = f"X{max_x:05d}"
            ru_data = list(row[1:])  # skip RU PK
            # RU: перекр_id, от_id, к_id, тип_связи, описание, слой, quf_q..quf_date
            # EN: xref_id, from_id, to_id, link_type, description, layer_ref, col_6,
            #     from_entry_id, from_bitig_id, from_child_id, from_term,
            #     to_entry_id, to_bitig_id, to_child_id, to_term, quf_q..quf_date
            en_vals = [
                new_pk,           # xref_id
                ru_data[0],       # from_id
                ru_data[1],       # to_id
                ru_data[2],       # link_type
                ru_data[3],       # description
                ru_data[4],       # layer_ref
                None,             # col_6
                None, None, None, None,  # from_entry_id..from_term
                None, None, None, None,  # to_entry_id..to_term
                ru_data[5] if len(ru_data) > 5 else None,  # quf_q
                ru_data[6] if len(ru_data) > 6 else None,  # quf_u
                ru_data[7] if len(ru_data) > 7 else None,  # quf_f
                ru_data[8] if len(ru_data) > 8 else None,  # quf_pass
                ru_data[9] if len(ru_data) > 9 else None,  # quf_date
                "RU",             # lang
            ]
            try:
                cur.execute("""INSERT INTO a5_cross_refs
                    (xref_id, from_id, to_id, link_type, description, layer_ref, col_6,
                     from_entry_id, from_bitig_id, from_child_id, from_term,
                     to_entry_id, to_bitig_id, to_child_id, to_term,
                     quf_q, quf_u, quf_f, quf_pass, quf_date, lang)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", en_vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip A5 row {row[0]}: {e}")
        print(f"  Inserted {inserted} RU rows into a5_cross_refs")
        cur.execute("DROP TABLE IF EXISTS a5_перекрёстные_ссылки")
        dropped_tables.append("a5_перекрёстные_ссылки")
    else:
        print(f"  [DRY] Would merge {len(a5_ru)} RU rows into a5_cross_refs")

    # A6: country_names (EN=46) ← a6_названия_стран (RU=3)
    # RU: страна_id, название_страны, корень_al, корень_id, слово_al, коранич_значение,
    #     фонетическая_цепь, основание_названия, запись_ids, примечания, quf*
    # EN: country_id, country_name, al_root, root_id, al_word, qur_meaning,
    #     phonetic_chain, naming_basis, entry_ids, notes, created_at, quf*
    a6_ru = cur.execute("""SELECT страна_id, название_страны, корень_al, корень_id, слово_al,
                                  коранич_значение, фонетическая_цепь, основание_названия,
                                  запись_ids, примечания,
                                  quf_q, quf_u, quf_f, quf_pass, quf_date
                           FROM a6_названия_стран""").fetchall()
    print(f"  A6 country_names: EN={cur.execute('SELECT COUNT(*) FROM country_names').fetchone()[0]}, RU={len(a6_ru)}")

    if not dry:
        try:
            cur.execute("ALTER TABLE country_names ADD COLUMN lang TEXT DEFAULT 'EN'")
            print("  Added lang column to country_names")
        except sqlite3.OperationalError:
            print("  lang column already exists on country_names")

        max_c = cur.execute("SELECT MAX(CAST(REPLACE(country_id,'CN','') AS INTEGER)) FROM country_names").fetchone()[0] or 0
        inserted = 0
        for row in a6_ru:
            max_c += 1
            new_pk = f"CN{max_c:03d}"
            vals = (new_pk, row[1], row[2], row[3], row[4], row[5],
                    row[6], row[7], row[8], row[9],
                    row[10], row[11], row[12], row[13], row[14], "RU")
            try:
                cur.execute("""INSERT INTO country_names
                    (country_id, country_name, al_root, root_id, al_word, qur_meaning,
                     phonetic_chain, naming_basis, entry_ids, notes,
                     quf_q, quf_u, quf_f, quf_pass, quf_date, lang)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip A6 row {row[0]}: {e}")
        print(f"  Inserted {inserted} RU rows into country_names")
        cur.execute("DROP TABLE IF EXISTS a6_названия_стран")
        dropped_tables.append("a6_названия_стран")
    else:
        print(f"  [DRY] Would merge {len(a6_ru)} RU rows into country_names")

    # ─── Phase 4: Foundation F1-F7 — add lang column, INSERT RU rows ───
    print("\n=== Phase 4: Foundation F1-F7 — merge RU into EN ===")

    for ru_table, en_table, col_map in FOUNDATION_MERGES:
        ru_count = cur.execute(f"SELECT COUNT(*) FROM [{ru_table}]").fetchone()[0]
        en_count = cur.execute(f"SELECT COUNT(*) FROM [{en_table}]").fetchone()[0]
        print(f"  {en_table}: EN={en_count}, RU={ru_count}")

        if not dry:
            try:
                cur.execute(f"ALTER TABLE [{en_table}] ADD COLUMN lang TEXT DEFAULT 'EN'")
            except sqlite3.OperationalError:
                pass

            # Get RU data
            ru_cols = [m[0] for m in col_map]
            en_cols = [m[1] for m in col_map]
            ru_col_str = ", ".join([f"[{c}]" for c in ru_cols])

            rows = cur.execute(f"SELECT {ru_col_str}, quf_q, quf_u, quf_f, quf_pass, quf_date FROM [{ru_table}]").fetchall()

            en_col_str = ", ".join(en_cols) + ", quf_q, quf_u, quf_f, quf_pass, quf_date, lang"
            placeholders = ", ".join(["?"] * (len(en_cols) + 6))

            inserted = 0
            for row in rows:
                vals = list(row) + ["RU"]
                try:
                    cur.execute(f"INSERT INTO [{en_table}] ({en_col_str}) VALUES ({placeholders})", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {ru_table} row: {e}")
            print(f"    Merged {inserted} RU rows → {en_table}")
            cur.execute(f"DROP TABLE IF EXISTS [{ru_table}]")
            dropped_tables.append(ru_table)
        else:
            print(f"  [DRY] Would merge {ru_count} RU rows into {en_table}")

    # ─── Phase 5: Mechanism M1-M5 ───
    print("\n=== Phase 5: Mechanism tables ===")

    # M5: merge like Foundation
    ru_table, en_table, col_map = M5_MERGE
    ru_count = cur.execute(f"SELECT COUNT(*) FROM [{ru_table}]").fetchone()[0]
    en_count = cur.execute(f"SELECT COUNT(*) FROM [{en_table}]").fetchone()[0]
    print(f"  {en_table}: EN={en_count}, RU={ru_count}")

    if not dry:
        try:
            cur.execute(f"ALTER TABLE [{en_table}] ADD COLUMN lang TEXT DEFAULT 'EN'")
        except sqlite3.OperationalError:
            pass

        ru_cols = [m[0] for m in col_map]
        en_cols = [m[1] for m in col_map]
        ru_col_str = ", ".join([f"[{c}]" for c in ru_cols])

        rows = cur.execute(f"SELECT {ru_col_str}, quf_q, quf_u, quf_f, quf_pass, quf_date FROM [{ru_table}]").fetchall()

        en_col_str = ", ".join(en_cols) + ", quf_q, quf_u, quf_f, quf_pass, quf_date, lang"
        placeholders = ", ".join(["?"] * (len(en_cols) + 6))

        inserted = 0
        for row in rows:
            vals = list(row) + ["RU"]
            try:
                cur.execute(f"INSERT INTO [{en_table}] ({en_col_str}) VALUES ({placeholders})", vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip {ru_table} row: {e}")
        print(f"    Merged {inserted} RU rows → {en_table}")
        cur.execute(f"DROP TABLE IF EXISTS [{ru_table}]")
        dropped_tables.append(ru_table)
    else:
        print(f"  [DRY] Would merge {ru_count} RU rows into {en_table}")

    # M1-M4: rename RU tables to EN names (no EN counterpart exists)
    for ru_name, en_name in RU_RENAME.items():
        count = cur.execute(f"SELECT COUNT(*) FROM [{ru_name}]").fetchone()[0]
        print(f"  Rename [{ru_name}] → [{en_name}] ({count} rows)")
        if not dry:
            # Check if target already exists
            exists = cur.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (en_name,)).fetchone()[0]
            if exists:
                print(f"    Target {en_name} already exists — adding lang column and merging")
                try:
                    cur.execute(f"ALTER TABLE [{en_name}] ADD COLUMN lang TEXT DEFAULT 'EN'")
                except sqlite3.OperationalError:
                    pass
                # Can't easily merge different schemas — just keep both for now
                print(f"    Skipping merge (different schemas) — keeping [{ru_name}] as-is")
            else:
                cur.execute(f"ALTER TABLE [{ru_name}] RENAME TO [{en_name}]")
                print(f"    Renamed successfully")

    # ─── Phase 6: Drop retired tables ───
    print("\n=== Phase 6: Drop retired tables ===")
    for tbl in RETIRED:
        if not dry:
            cur.execute(f"DROP TABLE IF EXISTS [{tbl}]")
            dropped_tables.append(tbl)
            print(f"  Dropped {tbl}")
        else:
            print(f"  [DRY] Would drop {tbl}")

    # Also drop _qwr_new if empty
    qwr_count = cur.execute("SELECT COUNT(*) FROM _qwr_new").fetchone()[0]
    if qwr_count == 0:
        if not dry:
            cur.execute("DROP TABLE IF EXISTS _qwr_new")
            dropped_tables.append("_qwr_new")
            print(f"  Dropped _qwr_new (empty)")
        else:
            print(f"  [DRY] Would drop _qwr_new (empty)")

    # ─── Phase 7: Recreate views ───
    print("\n=== Phase 7: Recreate views ===")

    view_defs = {
        "a1_entries": """CREATE VIEW a1_entries AS
            SELECT entry_id, score, en_term, ru_term, fa_term, ar_word,
                   root_id, root_letters, qur_refs, pattern, inversion_type,
                   network_id, allah_name_id, phonetic_chain, source_form,
                   ds_corridor, decay_level, dp_codes, ops_applied,
                   foundation_refs, notes, qur_meaning,
                   quf_q, quf_u, quf_f, quf_pass
            FROM entries""",

        "a1_записи": """CREATE VIEW [a1_записи] AS
            SELECT entry_id AS запись_id, score AS балл, ru_term AS рус_термин,
                   ar_word AS ар_слово, root_id AS корень_id, root_letters AS корневые_буквы,
                   qur_meaning AS коранич_значение, pattern AS паттерн,
                   allah_name_id AS имя_аллаха_id, network_id AS сеть_id,
                   phonetic_chain AS фонетическая_цепь, inversion_type AS тип_инверсии,
                   source_form AS исходная_форма, foundation_refs AS основание,
                   quf_q, quf_u, quf_f, quf_pass, quf_date, quf_token
            FROM entries WHERE ru_term IS NOT NULL""",

        "a2_names_of_allah": "CREATE VIEW a2_names_of_allah AS SELECT * FROM names_of_allah",
        "a3_quran_refs": "CREATE VIEW a3_quran_refs AS SELECT * FROM quran_refs",
        "a6_country_names": "CREATE VIEW a6_country_names AS SELECT * FROM country_names",

        "child_schema": """CREATE VIEW child_schema AS
            SELECT child_id AS entry_id, shell_name, shell_language, orig_class, orig_root,
                   orig_lemma, orig_meaning, operation_role, shell_meaning, inversion_direction,
                   phonetic_chain, qur_anchors, dp_codes, nt_code, pattern, parent_op,
                   gate_status, notes
            FROM child_entries""",

        # Fix m1_phonetic_shifts — point to shift_lookup (the actual table)
        "m1_phonetic_shifts": "CREATE VIEW m1_phonetic_shifts AS SELECT * FROM shift_lookup",

        # m2-m4: point to the newly renamed tables
        "m2_detection_patterns": None,  # Will check if table exists
        "m3_scholars": None,
        "m4_networks": None,

        "persian_a1_mad_khil": """CREATE VIEW persian_a1_mad_khil AS
            SELECT entry_id, fa_term, ar_word, root_letters, qur_meaning,
                   pattern, allah_name_id, network_id, phonetic_chain,
                   inversion_type, source_form, foundation_refs, score,
                   root_id, quf_q, quf_u, quf_f, quf_pass, quf_date, quf_token
            FROM entries WHERE fa_term IS NOT NULL""",
    }

    if not dry:
        for vname, vsql in view_defs.items():
            if vsql is None:
                # Check if the table exists to create a pass-through view
                # m2_detection_patterns → check if renamed table exists
                if vname == "m2_detection_patterns":
                    exists = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='m2_detection_patterns'").fetchone()[0]
                    if exists:
                        print(f"  {vname} is now a TABLE — no view needed")
                        continue
                elif vname == "m3_scholars":
                    exists = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='m3_scholars'").fetchone()[0]
                    if exists:
                        print(f"  {vname} is now a TABLE — no view needed")
                        continue
                elif vname == "m4_networks":
                    exists = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='m4_networks'").fetchone()[0]
                    if exists:
                        print(f"  {vname} is now a TABLE — no view needed")
                        continue
                print(f"  Skipping {vname} — no valid target")
                continue

            try:
                cur.execute(vsql)
                print(f"  Created view: {vname}")
            except Exception as e:
                print(f"  ERROR creating view {vname}: {e}")
    else:
        for vname in view_defs:
            print(f"  [DRY] Would create view: {vname}")

    # ─── Phase 8: Restore triggers ───
    print("\n=== Phase 8: Restore triggers ===")
    if not dry:
        # Get current table names to filter triggers
        current_tables = set(r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall())

        restored = 0
        skipped = 0
        errors = 0
        for tname, tsql, ttbl in triggers:
            if tsql is None:
                skipped += 1
                continue
            # Skip triggers for dropped tables
            if ttbl not in current_tables:
                skipped += 1
                continue
            # Fix triggers that reference a1_entries (now a view that doesn't exist yet)
            # These will be recreated after views are recreated
            if 'a1_entries' in tsql and 'a1_entries' not in current_tables:
                # Replace a1_entries reference with entries table
                tsql = tsql.replace('a1_entries', 'entries')
            # Fix triggers with NEW.relationship (column doesn't exist)
            if 'NEW.relationship' in tsql:
                skipped += 1
                continue
            try:
                cur.execute(tsql)
                restored += 1
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"    Trigger error {tname}: {e}")
        print(f"  Restored {restored} triggers, skipped {skipped}, errors {errors}")
    else:
        print(f"  [DRY] Would restore valid triggers from {len(triggers)} saved")

    # ─── Phase 9: Commit and verify ───
    print("\n=== Phase 9: Verify ===")
    if not dry:
        conn.commit()

        final_tables = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        final_views = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
        final_triggers = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]

        print(f"  Tables: 186 → {final_tables} (dropped {len(dropped_tables)})")
        print(f"  Views: {final_views}")
        print(f"  Triggers: {final_triggers}")
        print(f"\n  Dropped tables: {', '.join(dropped_tables)}")

        # Verify key table counts
        checks = [
            ("entries", None), ("names_of_allah", None), ("a4_derivatives", None),
            ("a5_cross_refs", None), ("quran_refs", None), ("country_names", None),
        ]
        print("\n  Row counts:")
        for tbl, _ in checks:
            try:
                count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                print(f"    {tbl}: {count}")
            except:
                print(f"    {tbl}: ERROR")
    else:
        print("  [DRY RUN COMPLETE — no changes made]")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    if dry:
        print("=== DRY RUN ===")
    else:
        print("=== LIVE RUN ===")
    run(dry=dry)
