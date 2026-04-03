#!/usr/bin/env python3
"""
USLaP Schema Consolidation — Phases 2, 3, 4
Phase 3: Bitig cleanup (drop 3 empty, merge 2 pairs) — 5 tables eliminated
Phase 2: Body consolidation (46 tables → 5) — 41 tables eliminated
Phase 4: Foundation/Mechanism (16 → 2) — 14 tables eliminated
Total: ~60 tables eliminated

Must run AFTER Phase 1 (RU mirrors already done).
"""

import sqlite3, os, sys, json
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: Bitig cleanup
# ═══════════════════════════════════════════════════════════════════

BITIG_DROP = ["bitig_bridge_xref", "bitig_dispersal_edges", "bitig_sibling_propagation"]

BITIG_MERGE_CORRECTIONS = {
    "source": "bitig_investigation",
    "target": "bitig_corrections",
    # investigation cols: inv_id, word, meaning, status, issue, next_step, quf*
    # corrections cols: corr_id, what_was_wrong, corrected_to, evidence, affects, status, quf*
    # Strategy: add source='investigation' column, map inv cols into corrections structure
}

BITIG_MERGE_INTEL = {
    "source": "bitig_operator_profiles",
    "target": "bitig_intelligence_summary",
    # intel cols: intel_id, category, dp_code, frequency, operation_signature, peak_period,
    #             case_ids, target_language, intelligence_assessment, notes, quf*
    # profiles cols: profile_id, name, role, period, location, access_type, dp_codes,
    #               method, cover_story, evidence, naming_pattern, intel_refs, notes, quf_token, quf*
    # Strategy: profiles have very different schema → store as JSON in notes column
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: Body consolidation — 46 tables → 5
# ═══════════════════════════════════════════════════════════════════

# Tables that go into body_data (the main unified table)
BODY_DATA_TABLES = [
    "body_architecture", "body_chemistry", "body_colour_therapy", "body_creation_stages",
    "body_diagnostics", "body_movement_chains", "body_nodes", "body_preservation",
    "body_skeletal_map", "body_sound_therapy", "body_substances", "body_technical",
    "death_mechanism", "emotional_disorders", "food_contrasts", "food_production_cycle",
    "healing_protocols", "heart_compilation", "lifecycle_architecture",
    "mortality_intelligence", "nafs_architecture", "nutrition_architecture",
    "nutrition_intelligence", "pelvis_tissue", "perception_contamination",
    "perception_hierarchy", "qalb_states", "sensory_architecture", "sensory_diagnostics",
    "sensory_disorders", "social_health", "spirit_infusion", "transition_states",
]

# Tables that go into body_cross_refs_unified
BODY_XREF_TABLES = [
    "body_cross_refs", "nafs_cross_refs", "sensory_cross_refs",
    "nutrition_cross_refs", "lifecycle_cross_refs", "body_edges",
]

# Tables that go into body_prayer_map_unified
BODY_PRAYER_TABLES = [
    "prayer_states", "prayer_transitions", "sensory_prayer_map",
    "therapy_prayer_map", "nafs_prayer_map", "heptad_prayer_map",
]

# Tables that stay as-is
BODY_KEEP = ["body_heptad_meta", "body_extraction_intel"]

# Common columns to extract (if present) — rest goes to specific_data JSON
COMMON_COLS = [
    "category", "arabic", "transliteration", "english", "description",
    "root_letters", "aa_root_id", "quranic_ref", "score", "status",
    "q_gate", "u_gate", "f_gate",
]

QUF_COLS = ["quf_q", "quf_u", "quf_f", "quf_pass", "quf_date", "quf_token"]

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: Foundation/Mechanism consolidation
# ═══════════════════════════════════════════════════════════════════

FOUNDATION_TABLES = [
    "f1_two_originals", "f2_script_downstream", "f2_decay_criteria",
    "f3_frozen_stage_model", "f4_decay_gradient", "f5_destruction_timeline",
    "f6_manuscript_evidence", "f7_direction_of_flow",
]

MECHANISM_TABLES = [
    "m1_shift_descriptions", "m2_detection_patterns", "m3_scholars",
    "m4_networks", "m5_qur_verification", "shift_lookup", "bi_shift_lookup",
]


def get_subsystem(table_name):
    """Map table name to subsystem category."""
    if table_name.startswith("body_"):
        return table_name.replace("body_", "")
    if table_name.startswith("nafs_"):
        return "nafs"
    if table_name.startswith("sensory_"):
        return "sensory"
    if table_name.startswith("nutrition_"):
        return "nutrition"
    if table_name.startswith("lifecycle_"):
        return "lifecycle"
    if table_name.startswith("perception_"):
        return "perception"
    if table_name.startswith("food_"):
        return "food"
    mapping = {
        "death_mechanism": "mortality",
        "emotional_disorders": "nafs",
        "healing_protocols": "healing",
        "heart_compilation": "qalb",
        "mortality_intelligence": "mortality",
        "pelvis_tissue": "skeletal",
        "qalb_states": "qalb",
        "social_health": "social",
        "spirit_infusion": "spirit",
        "transition_states": "lifecycle",
    }
    return mapping.get(table_name, table_name)


def get_layer(table_name):
    """Map foundation/mechanism table to layer ID."""
    if table_name.startswith("f"):
        # f1_two_originals → F1, f2_script_downstream → F2, etc.
        return table_name.split("_")[0].upper()
    if table_name.startswith("m"):
        return table_name.split("_")[0].upper()
    if table_name == "shift_lookup":
        return "M1"
    if table_name == "bi_shift_lookup":
        return "M1_BITIG"
    return table_name


def run(dry=False):
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF;")
    cur = conn.cursor()

    # Save and drop ALL triggers first (they block ALTER/INSERT)
    print("\n=== Saving and dropping triggers ===")
    triggers = cur.execute("SELECT name, sql, tbl_name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()
    print(f"  {len(triggers)} triggers saved")

    if not dry:
        for tname, _, _ in triggers:
            cur.execute(f'DROP TRIGGER IF EXISTS [{tname}]')
        print(f"  All triggers dropped")

    dropped = []

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3: BITIG CLEANUP
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  PHASE 3: Bitig Cleanup")
    print("="*60)

    # 3a: Drop 3 empty tables
    for tbl in BITIG_DROP:
        count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        print(f"  {tbl}: {count} rows", end="")
        if count == 0:
            if not dry:
                cur.execute(f"DROP TABLE [{tbl}]")
                dropped.append(tbl)
            print(" → DROPPED" if not dry else " → [DRY] would drop")
        else:
            print(" → SKIPPED (not empty!)")

    # 3b: Merge bitig_investigation → bitig_corrections
    inv_rows = cur.execute("SELECT * FROM bitig_investigation").fetchall()
    inv_cols = [d[1] for d in cur.execute("PRAGMA table_info(bitig_investigation)").fetchall()]
    print(f"\n  Merging bitig_investigation ({len(inv_rows)}) → bitig_corrections")

    if not dry:
        try:
            cur.execute("ALTER TABLE bitig_corrections ADD COLUMN source TEXT DEFAULT 'correction'")
        except sqlite3.OperationalError:
            pass

        inserted = 0
        for row in inv_rows:
            row_dict = dict(zip(inv_cols, row))
            # Map: inv_id→corr_id, word→what_was_wrong, issue→corrected_to,
            #       next_step→evidence, meaning→affects
            vals = (
                row_dict.get("inv_id", ""),
                row_dict.get("word", "") + ": " + row_dict.get("issue", ""),
                row_dict.get("next_step", ""),
                row_dict.get("meaning", ""),
                row_dict.get("status", ""),
                row_dict.get("status", ""),
                row_dict.get("quf_q"), row_dict.get("quf_u"), row_dict.get("quf_f"),
                row_dict.get("quf_pass"), row_dict.get("quf_date"),
                "investigation",
            )
            try:
                cur.execute("""INSERT INTO bitig_corrections
                    (corr_id, what_was_wrong, corrected_to, evidence, affects, status,
                     quf_q, quf_u, quf_f, quf_pass, quf_date, source)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip {row_dict.get('inv_id')}: {e}")
        print(f"    Inserted {inserted} rows")
        cur.execute("DROP TABLE bitig_investigation")
        dropped.append("bitig_investigation")

    # 3c: Merge bitig_operator_profiles → bitig_intelligence_summary
    prof_rows = cur.execute("SELECT * FROM bitig_operator_profiles").fetchall()
    prof_cols = [d[1] for d in cur.execute("PRAGMA table_info(bitig_operator_profiles)").fetchall()]
    print(f"\n  Merging bitig_operator_profiles ({len(prof_rows)}) → bitig_intelligence_summary")

    if not dry:
        try:
            cur.execute("ALTER TABLE bitig_intelligence_summary ADD COLUMN source TEXT DEFAULT 'intel'")
        except sqlite3.OperationalError:
            pass

        inserted = 0
        for row in prof_rows:
            row_dict = dict(zip(prof_cols, row))
            # Map profile data into intel structure, store extras in notes as JSON
            extras = json.dumps({k: v for k, v in row_dict.items()
                                if k not in ("profile_id", "name", "role", "dp_codes",
                                            "quf_q", "quf_u", "quf_f", "quf_pass", "quf_date")
                                and v is not None}, ensure_ascii=False)
            vals = (
                row_dict.get("profile_id", ""),
                row_dict.get("role", "operator_profile"),
                row_dict.get("dp_codes", ""),
                0,  # frequency
                row_dict.get("name", ""),  # operation_signature
                row_dict.get("period", ""),  # peak_period
                "",  # case_ids
                "",  # target_language
                row_dict.get("method", ""),  # intelligence_assessment
                extras,  # notes
                row_dict.get("quf_q"), row_dict.get("quf_u"), row_dict.get("quf_f"),
                row_dict.get("quf_pass"), row_dict.get("quf_date"),
                "operator_profile",
            )
            try:
                cur.execute("""INSERT INTO bitig_intelligence_summary
                    (intel_id, category, dp_code, frequency, operation_signature, peak_period,
                     case_ids, target_language, intelligence_assessment, notes,
                     quf_q, quf_u, quf_f, quf_pass, quf_date, source)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                inserted += 1
            except Exception as e:
                print(f"    Skip {row_dict.get('profile_id')}: {e}")
        print(f"    Inserted {inserted} rows")
        cur.execute("DROP TABLE bitig_operator_profiles")
        dropped.append("bitig_operator_profiles")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: BODY CONSOLIDATION
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  PHASE 2: Body Consolidation (46 → 5)")
    print("="*60)

    # 2a: Create body_data unified table
    if not dry:
        cur.execute("""CREATE TABLE IF NOT EXISTS body_data (
            body_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            subtable TEXT NOT NULL,
            orig_id TEXT,
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
            q_gate TEXT,
            u_gate TEXT,
            f_gate TEXT,
            specific_data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT, quf_token TEXT
        )""")
        print("  Created body_data table")

    # Migrate each body data table
    total_migrated = 0
    for tbl in BODY_DATA_TABLES:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        except:
            print(f"  {tbl}: NOT FOUND — skipping")
            continue

        if count == 0:
            print(f"  {tbl}: 0 rows → DROP")
            if not dry:
                cur.execute(f"DROP TABLE [{tbl}]")
                dropped.append(tbl)
            continue

        cols = [d[1] for d in cur.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        rows = cur.execute(f"SELECT * FROM [{tbl}]").fetchall()
        subsystem = get_subsystem(tbl)

        if not dry:
            inserted = 0
            for row in rows:
                row_dict = dict(zip(cols, row))

                # Extract common columns
                orig_id = row_dict.get(cols[0], "")  # First col is always the PK
                category_val = row_dict.get("category", row_dict.get("section",
                               row_dict.get("level", row_dict.get("stage_order", ""))))
                arabic_val = row_dict.get("arabic", "")
                translit = row_dict.get("transliteration", "")
                english = row_dict.get("english", row_dict.get("component",
                          row_dict.get("domain", "")))
                desc = row_dict.get("description", row_dict.get("function",
                       row_dict.get("health_impact", row_dict.get("biological_process", ""))))
                root_letters = row_dict.get("root_letters", "")
                aa_root = row_dict.get("aa_root_id", "")
                qur_ref = row_dict.get("quranic_ref", row_dict.get("quranic_text", ""))
                score_val = row_dict.get("score", None)
                status_val = row_dict.get("status", "")
                q_gate = row_dict.get("q_gate", "")
                u_gate = row_dict.get("u_gate", "")
                f_gate = row_dict.get("f_gate", "")

                # Everything else goes to specific_data JSON
                skip_keys = {"rowid_pk", cols[0], "category", "section", "level", "stage_order",
                            "arabic", "transliteration", "english", "component", "domain",
                            "description", "function", "health_impact", "biological_process",
                            "root_letters", "aa_root_id", "quranic_ref", "quranic_text",
                            "score", "status", "q_gate", "u_gate", "f_gate",
                            "quf_q", "quf_u", "quf_f", "quf_pass", "quf_date", "quf_token"}
                specific = {k: v for k, v in row_dict.items()
                           if k not in skip_keys and v is not None and str(v).strip()}
                specific_json = json.dumps(specific, ensure_ascii=False) if specific else None

                vals = (
                    subsystem, tbl, orig_id, str(category_val) if category_val else None,
                    arabic_val, translit, english, desc, root_letters, aa_root,
                    qur_ref, score_val, status_val, q_gate, u_gate, f_gate,
                    specific_json,
                    row_dict.get("quf_q"), row_dict.get("quf_u"), row_dict.get("quf_f"),
                    row_dict.get("quf_pass"), row_dict.get("quf_date"), row_dict.get("quf_token"),
                )
                try:
                    cur.execute("""INSERT INTO body_data
                        (subsystem, subtable, orig_id, category, arabic, transliteration,
                         english, description, root_letters, aa_root_id, quranic_ref,
                         score, status, q_gate, u_gate, f_gate, specific_data,
                         quf_q, quf_u, quf_f, quf_pass, quf_date, quf_token)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {tbl}/{orig_id}: {e}")
            total_migrated += inserted
            cur.execute(f"DROP TABLE [{tbl}]")
            dropped.append(tbl)
            print(f"  {tbl}: {count} rows → body_data ({inserted} inserted)")
        else:
            print(f"  [DRY] {tbl}: {count} rows → body_data")
            total_migrated += count

    print(f"\n  Total body_data rows: {total_migrated}")

    # 2b: Create body_cross_refs_unified
    if not dry:
        cur.execute("""CREATE TABLE IF NOT EXISTS body_cross_refs_unified (
            xref_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            orig_id TEXT,
            source_table TEXT,
            source_id TEXT,
            target_table TEXT,
            target_id TEXT,
            relationship TEXT,
            quranic_ref TEXT,
            description TEXT,
            notes TEXT,
            aa_root_id TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT
        )""")
        print("\n  Created body_cross_refs_unified table")

    xref_total = 0
    for tbl in BODY_XREF_TABLES:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        except:
            print(f"  {tbl}: NOT FOUND — skipping")
            continue

        cols = [d[1] for d in cur.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        rows = cur.execute(f"SELECT * FROM [{tbl}]").fetchall()
        subsystem = get_subsystem(tbl)

        if not dry:
            inserted = 0
            for row in rows:
                rd = dict(zip(cols, row))
                # body_edges has different schema: from_node, to_node, edge_type, label
                if tbl == "body_edges":
                    vals = (
                        subsystem, rd.get(cols[0], ""),
                        "body_nodes", str(rd.get("from_node", "")),
                        "body_nodes", str(rd.get("to_node", "")),
                        rd.get("edge_type", ""), rd.get("quranic_ref", ""),
                        rd.get("label", ""), rd.get("notes", ""),
                        rd.get("aa_root_id", ""),
                        None, None, None, None, None,
                    )
                else:
                    vals = (
                        subsystem, rd.get(cols[0], ""),
                        rd.get("source_table", ""), rd.get("source_id", ""),
                        rd.get("target_table", ""), rd.get("target_id", ""),
                        rd.get("relationship", ""), rd.get("quranic_ref", ""),
                        rd.get("description", ""), rd.get("notes", ""),
                        rd.get("aa_root_id", ""),
                        rd.get("quf_q"), rd.get("quf_u"), rd.get("quf_f"),
                        rd.get("quf_pass"), rd.get("quf_date"),
                    )
                try:
                    cur.execute("""INSERT INTO body_cross_refs_unified
                        (subsystem, orig_id, source_table, source_id, target_table, target_id,
                         relationship, quranic_ref, description, notes, aa_root_id,
                         quf_q, quf_u, quf_f, quf_pass, quf_date)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {tbl}/{rd.get(cols[0])}: {e}")
            xref_total += inserted
            cur.execute(f"DROP TABLE [{tbl}]")
            dropped.append(tbl)
            print(f"  {tbl}: {count} rows → body_cross_refs_unified ({inserted})")
        else:
            print(f"  [DRY] {tbl}: {count} rows → body_cross_refs_unified")
            xref_total += count

    print(f"  Total cross_refs: {xref_total}")

    # 2c: Create body_prayer_map_unified
    if not dry:
        cur.execute("""CREATE TABLE IF NOT EXISTS body_prayer_map_unified (
            map_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subsystem TEXT NOT NULL,
            subtable TEXT NOT NULL,
            orig_id TEXT,
            prayer_state TEXT,
            specific_data TEXT,
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT
        )""")
        print("\n  Created body_prayer_map_unified table")

    prayer_total = 0
    for tbl in BODY_PRAYER_TABLES:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        except:
            print(f"  {tbl}: NOT FOUND — skipping")
            continue

        cols = [d[1] for d in cur.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        rows = cur.execute(f"SELECT * FROM [{tbl}]").fetchall()
        subsystem = get_subsystem(tbl)

        if not dry:
            inserted = 0
            for row in rows:
                rd = dict(zip(cols, row))
                orig_id = rd.get(cols[0], "")
                prayer_state = rd.get("prayer_state", rd.get("from_state",
                               rd.get("arabic", rd.get("heptad", ""))))

                skip = {"rowid_pk", cols[0], "prayer_state", "from_state",
                        "quf_q", "quf_u", "quf_f", "quf_pass", "quf_date"}
                specific = {k: v for k, v in rd.items()
                           if k not in skip and v is not None and str(v).strip()}
                specific_json = json.dumps(specific, ensure_ascii=False) if specific else None

                vals = (
                    subsystem, tbl, orig_id, str(prayer_state) if prayer_state else None,
                    specific_json,
                    rd.get("quf_q"), rd.get("quf_u"), rd.get("quf_f"),
                    rd.get("quf_pass"), rd.get("quf_date"),
                )
                try:
                    cur.execute("""INSERT INTO body_prayer_map_unified
                        (subsystem, subtable, orig_id, prayer_state, specific_data,
                         quf_q, quf_u, quf_f, quf_pass, quf_date)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {tbl}/{orig_id}: {e}")
            prayer_total += inserted
            cur.execute(f"DROP TABLE [{tbl}]")
            dropped.append(tbl)
            print(f"  {tbl}: {count} rows → body_prayer_map_unified ({inserted})")
        else:
            print(f"  [DRY] {tbl}: {count} rows → body_prayer_map_unified")
            prayer_total += count

    print(f"  Total prayer_map: {prayer_total}")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 4: FOUNDATION/MECHANISM CONSOLIDATION
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  PHASE 4: Foundation/Mechanism Consolidation")
    print("="*60)

    # 4a: foundation_data
    if not dry:
        cur.execute("""CREATE TABLE IF NOT EXISTS foundation_data (
            fnd_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT NOT NULL,
            subtable TEXT NOT NULL,
            orig_id TEXT,
            specific_data TEXT,
            lang TEXT DEFAULT 'EN',
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT
        )""")
        print("  Created foundation_data table")

    fnd_total = 0
    for tbl in FOUNDATION_TABLES:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        except:
            print(f"  {tbl}: NOT FOUND — skipping")
            continue

        cols = [d[1] for d in cur.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        rows = cur.execute(f"SELECT * FROM [{tbl}]").fetchall()
        layer = get_layer(tbl)

        if not dry:
            inserted = 0
            for row in rows:
                rd = dict(zip(cols, row))
                orig_id = rd.get(cols[1], "") if len(cols) > 1 else ""  # skip rowid_pk
                lang = rd.get("lang", "EN")
                skip = {"rowid_pk", "quf_q", "quf_u", "quf_f", "quf_pass", "quf_date", "lang"}
                specific = {k: v for k, v in rd.items()
                           if k not in skip and v is not None and str(v).strip()}
                specific_json = json.dumps(specific, ensure_ascii=False) if specific else None

                vals = (
                    layer, tbl, orig_id, specific_json, lang,
                    rd.get("quf_q"), rd.get("quf_u"), rd.get("quf_f"),
                    rd.get("quf_pass"), rd.get("quf_date"),
                )
                try:
                    cur.execute("""INSERT INTO foundation_data
                        (layer, subtable, orig_id, specific_data, lang,
                         quf_q, quf_u, quf_f, quf_pass, quf_date)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {tbl}: {e}")
            fnd_total += inserted
            cur.execute(f"DROP TABLE [{tbl}]")
            dropped.append(tbl)
            print(f"  {tbl}: {count} rows → foundation_data ({inserted})")
        else:
            print(f"  [DRY] {tbl}: {count} rows → foundation_data")
            fnd_total += count

    print(f"  Total foundation_data: {fnd_total}")

    # 4b: mechanism_data
    if not dry:
        cur.execute("""CREATE TABLE IF NOT EXISTS mechanism_data (
            mech_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT NOT NULL,
            subtable TEXT NOT NULL,
            orig_id TEXT,
            specific_data TEXT,
            lang TEXT DEFAULT 'EN',
            quf_q TEXT, quf_u TEXT, quf_f TEXT, quf_pass TEXT, quf_date TEXT
        )""")
        print("\n  Created mechanism_data table")

    mech_total = 0
    for tbl in MECHANISM_TABLES:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        except:
            print(f"  {tbl}: NOT FOUND — skipping")
            continue

        cols = [d[1] for d in cur.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        rows = cur.execute(f"SELECT * FROM [{tbl}]").fetchall()
        layer = get_layer(tbl)

        if not dry:
            inserted = 0
            for row in rows:
                rd = dict(zip(cols, row))
                # First non-rowid column is the semantic ID
                id_col = cols[0] if cols[0] != "rowid_pk" else (cols[1] if len(cols) > 1 else "")
                orig_id = rd.get(id_col, "")

                skip = {"rowid_pk", "quf_q", "quf_u", "quf_f", "quf_pass", "quf_date",
                        "quf_token", "lang"}
                specific = {k: v for k, v in rd.items()
                           if k not in skip and v is not None and str(v).strip()}
                specific_json = json.dumps(specific, ensure_ascii=False) if specific else None

                vals = (
                    layer, tbl, orig_id, specific_json, rd.get("lang", "EN"),
                    rd.get("quf_q"), rd.get("quf_u"), rd.get("quf_f"),
                    rd.get("quf_pass"), rd.get("quf_date"),
                )
                try:
                    cur.execute("""INSERT INTO mechanism_data
                        (layer, subtable, orig_id, specific_data, lang,
                         quf_q, quf_u, quf_f, quf_pass, quf_date)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""", vals)
                    inserted += 1
                except Exception as e:
                    print(f"    Skip {tbl}: {e}")
            mech_total += inserted
            cur.execute(f"DROP TABLE [{tbl}]")
            dropped.append(tbl)
            print(f"  {tbl}: {count} rows → mechanism_data ({inserted})")
        else:
            print(f"  [DRY] {tbl}: {count} rows → mechanism_data")
            mech_total += count

    print(f"  Total mechanism_data: {mech_total}")

    # ═══════════════════════════════════════════════════════════════
    # RECREATE VIEWS + TRIGGERS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  Recreating views and triggers")
    print("="*60)

    if not dry:
        # Compatibility views for body tables
        body_views = {}
        for tbl in BODY_DATA_TABLES:
            body_views[tbl] = f"""CREATE VIEW [{tbl}] AS
                SELECT body_id, orig_id, category, arabic, transliteration, english,
                       description, root_letters, aa_root_id, quranic_ref, score, status,
                       q_gate, u_gate, f_gate, specific_data,
                       quf_q, quf_u, quf_f, quf_pass, quf_date
                FROM body_data WHERE subtable = '{tbl}'"""

        for tbl in BODY_XREF_TABLES:
            body_views[tbl] = f"""CREATE VIEW [{tbl}] AS
                SELECT xref_id, orig_id, source_table, source_id, target_table, target_id,
                       relationship, quranic_ref, description, notes, aa_root_id,
                       quf_q, quf_u, quf_f, quf_pass, quf_date
                FROM body_cross_refs_unified WHERE subsystem = '{get_subsystem(tbl)}'"""

        for tbl in BODY_PRAYER_TABLES:
            body_views[tbl] = f"""CREATE VIEW [{tbl}] AS
                SELECT map_id, orig_id, prayer_state, specific_data,
                       quf_q, quf_u, quf_f, quf_pass, quf_date
                FROM body_prayer_map_unified WHERE subtable = '{tbl}'"""

        # Foundation/Mechanism views
        for tbl in FOUNDATION_TABLES:
            layer = get_layer(tbl)
            body_views[tbl] = f"""CREATE VIEW [{tbl}] AS
                SELECT fnd_id, orig_id, specific_data, lang,
                       quf_q, quf_u, quf_f, quf_pass, quf_date
                FROM foundation_data WHERE subtable = '{tbl}'"""

        for tbl in MECHANISM_TABLES:
            body_views[tbl] = f"""CREATE VIEW [{tbl}] AS
                SELECT mech_id, orig_id, specific_data, lang,
                       quf_q, quf_u, quf_f, quf_pass, quf_date
                FROM mechanism_data WHERE subtable = '{tbl}'"""

        created_views = 0
        for vname, vsql in body_views.items():
            try:
                cur.execute(vsql)
                created_views += 1
            except Exception as e:
                print(f"    View error {vname}: {e}")
        print(f"  Created {created_views} compatibility views")

        # Also ensure the main lattice views exist
        main_views = {
            "a1_entries": """CREATE VIEW IF NOT EXISTS a1_entries AS
                SELECT entry_id, score, en_term, ru_term, fa_term, ar_word,
                       root_id, root_letters, qur_refs, pattern, inversion_type,
                       network_id, allah_name_id, phonetic_chain, source_form,
                       ds_corridor, decay_level, dp_codes, ops_applied,
                       foundation_refs, notes, qur_meaning,
                       quf_q, quf_u, quf_f, quf_pass
                FROM entries""",
            "a1_записи": """CREATE VIEW IF NOT EXISTS [a1_записи] AS
                SELECT entry_id AS запись_id, score AS балл, ru_term AS рус_термин,
                       ar_word AS ар_слово, root_id AS корень_id, root_letters AS корневые_буквы,
                       qur_meaning AS коранич_значение, pattern AS паттерн,
                       allah_name_id AS имя_аллаха_id, network_id AS сеть_id,
                       phonetic_chain AS фонетическая_цепь, inversion_type AS тип_инверсии,
                       source_form AS исходная_форма, foundation_refs AS основание,
                       quf_q, quf_u, quf_f, quf_pass, quf_date, quf_token
                FROM entries WHERE ru_term IS NOT NULL""",
            "a2_names_of_allah": "CREATE VIEW IF NOT EXISTS a2_names_of_allah AS SELECT * FROM names_of_allah",
            "a3_quran_refs": "CREATE VIEW IF NOT EXISTS a3_quran_refs AS SELECT * FROM quran_refs",
            "a6_country_names": "CREATE VIEW IF NOT EXISTS a6_country_names AS SELECT * FROM country_names",
            "child_schema": """CREATE VIEW IF NOT EXISTS child_schema AS
                SELECT child_id AS entry_id, shell_name, shell_language, orig_class, orig_root,
                       orig_lemma, orig_meaning, operation_role, shell_meaning, inversion_direction,
                       phonetic_chain, qur_anchors, dp_codes, nt_code, pattern, parent_op,
                       gate_status, notes
                FROM child_entries""",
            "m1_phonetic_shifts": None,  # Now handled by mechanism_data view
            "persian_a1_mad_khil": """CREATE VIEW IF NOT EXISTS persian_a1_mad_khil AS
                SELECT entry_id, fa_term, ar_word, root_letters, qur_meaning,
                       pattern, allah_name_id, network_id, phonetic_chain,
                       inversion_type, source_form, foundation_refs, score,
                       root_id, quf_q, quf_u, quf_f, quf_pass, quf_date, quf_token
                FROM entries WHERE fa_term IS NOT NULL""",
        }
        for vname, vsql in main_views.items():
            if vsql is None:
                continue
            try:
                cur.execute(vsql)
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"    Main view error {vname}: {e}")

        # Restore triggers — only for tables that still exist
        current_tables = set(r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall())

        restored = 0
        skipped = 0
        for tname, tsql, ttbl in triggers:
            if tsql is None:
                skipped += 1
                continue
            if ttbl not in current_tables:
                skipped += 1
                continue
            if 'NEW.relationship' in tsql:
                skipped += 1
                continue
            # Fix references to a1_entries (now a view)
            if 'a1_entries' in tsql and 'a1_entries' not in current_tables:
                tsql = tsql.replace('a1_entries', 'entries')
            try:
                cur.execute(tsql)
                restored += 1
            except:
                skipped += 1
        print(f"  Restored {restored} triggers (skipped {skipped})")

    # ═══════════════════════════════════════════════════════════════
    # FINAL VERIFY
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  FINAL VERIFICATION")
    print("="*60)

    if not dry:
        conn.commit()

        tables = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        views = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
        trigs = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]

        print(f"  Tables: 163 → {tables}")
        print(f"  Views: {views}")
        print(f"  Triggers: {trigs}")
        print(f"  Dropped: {len(dropped)} tables")

        # Key counts
        for tbl in ["body_data", "body_cross_refs_unified", "body_prayer_map_unified",
                     "foundation_data", "mechanism_data", "entries", "names_of_allah"]:
            try:
                c = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                print(f"    {tbl}: {c}")
            except:
                print(f"    {tbl}: ERROR")

        # Integrity
        ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"  Integrity: {ic}")
    else:
        print(f"  [DRY RUN] Would drop {len(BITIG_DROP) + len(BODY_DATA_TABLES) + len(BODY_XREF_TABLES) + len(BODY_PRAYER_TABLES) + len(FOUNDATION_TABLES) + len(MECHANISM_TABLES) + 2} tables")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    if dry:
        print("=== DRY RUN ===")
    else:
        print("=== LIVE RUN ===")
    run(dry=dry)
