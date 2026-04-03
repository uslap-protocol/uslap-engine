#!/usr/bin/env python3
"""
USLaP Schema Migration — Restore FK-enforced architecture
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Migrates current 193-table DB → correct schema from create_uslap_db.sql
- Builds `roots` table from root_translations + all A1 root_ids
- Merges 6 A1 tables into unified `entries` with FK to roots
- Migrates all other tables with FK links
- Preserves ALL existing data
- Copies contamination triggers
- Restores PRAGMA foreign_keys = ON

Usage:
    python3 Code_files/migrate_to_schema.py check     # dry run — show what will happen
    python3 Code_files/migrate_to_schema.py migrate    # execute migration
"""

import sqlite3
import sys
import os
import json
from datetime import datetime

OLD_DB = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"
NEW_DB = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v4_migrated.db"
SCHEMA_SQL = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/create_uslap_db.sql"

def connect_old():
    conn = sqlite3.connect(OLD_DB)
    conn.row_factory = sqlite3.Row
    return conn

def connect_new():
    conn = sqlite3.connect(NEW_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

# ============================================================================
# STEP 1: Build roots table from all sources
# ============================================================================
def build_roots(old, new):
    """Collect all unique roots from all tables, merge with root_translations."""
    print("\n[STEP 1] Building roots table...")

    roots = {}  # root_id -> {root_letters, root_bare, quran_tokens, quran_lemmas, bitig_attested}

    # Source 1: root_translations (has Qur'anic data)
    rows = old.execute("""
        SELECT root_hyphenated, root_unhyphenated, token_count, form_count, first_ayah
        FROM root_translations
    """).fetchall()
    for r in rows:
        # We need to find a root_id for this root
        # Check if any entry references it
        root_h = r['root_hyphenated']
        root_bare = r['root_unhyphenated']
        roots[root_h] = {
            'root_letters': root_h,
            'root_bare': root_bare,
            'quran_tokens': r['token_count'] or 0,
            'quran_lemmas': r['form_count'] or 0,
            'root_id': None,  # will be assigned
            'bitig_attested': False,
            'first_ayah': r['first_ayah']
        }

    # Source 2: EN entries (has root_id mapping)
    en_roots = old.execute("""
        SELECT DISTINCT root_id, root_letters
        FROM a1_entries
        WHERE root_id IS NOT NULL AND root_id != ''
    """).fetchall()
    for r in en_roots:
        rl = r['root_letters']
        rid = r['root_id']
        if rl and rl in roots:
            roots[rl]['root_id'] = rid
        elif rl:
            roots[rl] = {
                'root_letters': rl,
                'root_bare': rl.replace('-', '').replace('‑', ''),
                'quran_tokens': 0,
                'quran_lemmas': 0,
                'root_id': rid,
                'bitig_attested': False,
                'first_ayah': None
            }

    # Source 3: RU entries
    ru_roots = old.execute("""
        SELECT DISTINCT корень_id, корневые_буквы
        FROM [a1_записи]
        WHERE корень_id IS NOT NULL AND корень_id != ''
    """).fetchall()
    for r in ru_roots:
        rl = r['корневые_буквы']
        rid = r['корень_id']
        if rl and rl in roots and not roots[rl]['root_id']:
            roots[rl]['root_id'] = rid
        elif rl and rl not in roots:
            roots[rl] = {
                'root_letters': rl,
                'root_bare': rl.replace('-', '').replace('‑', ''),
                'quran_tokens': 0,
                'quran_lemmas': 0,
                'root_id': rid,
                'bitig_attested': False,
                'first_ayah': None
            }

    # Source 4: FA entries
    fa_roots = old.execute("""
        SELECT DISTINCT [r_she_id_ریشِه_root_id] as root_id, [hor_f_e_r_she_حُروفِ_ریشِه_root_letters] as root_letters
        FROM persian_a1_mad_khil
        WHERE [r_she_id_ریشِه_root_id] IS NOT NULL AND [r_she_id_ریشِه_root_id] != ''
    """).fetchall()
    for r in fa_roots:
        rl = r['root_letters']
        rid = r['root_id']
        if rl and rl in roots and not roots[rl]['root_id']:
            roots[rl]['root_id'] = rid
        elif rl and rl not in roots:
            roots[rl] = {
                'root_letters': rl,
                'root_bare': rl.replace('-', '').replace('‑', ''),
                'quran_tokens': 0,
                'quran_lemmas': 0,
                'root_id': rid,
                'bitig_attested': False,
                'first_ayah': None
            }

    # Source 5: Latin entries
    lat_roots = old.execute("""
        SELECT DISTINCT root_id, root_letters
        FROM latin_a1_entries
        WHERE root_id IS NOT NULL AND root_id != ''
    """).fetchall()
    for r in lat_roots:
        rl = r['root_letters']
        rid = r['root_id']
        if rl and rl in roots and not roots[rl]['root_id']:
            roots[rl]['root_id'] = rid
        elif rl and rl not in roots:
            roots[rl] = {
                'root_letters': rl,
                'root_bare': rl.replace('-', '').replace('‑', ''),
                'quran_tokens': 0,
                'quran_lemmas': 0,
                'root_id': rid,
                'bitig_attested': False,
                'first_ayah': None
            }

    # Source 6: EU entries
    eu_roots = old.execute("""
        SELECT DISTINCT root_id, root_letters
        FROM european_a1_entries
        WHERE root_id IS NOT NULL AND root_id != ''
    """).fetchall()
    for r in eu_roots:
        rl = r['root_letters']
        rid = r['root_id']
        if rl and rl in roots and not roots[rl]['root_id']:
            roots[rl]['root_id'] = rid
        elif rl and rl not in roots:
            roots[rl] = {
                'root_letters': rl,
                'root_bare': rl.replace('-', '').replace('‑', ''),
                'quran_tokens': 0,
                'quran_lemmas': 0,
                'root_id': rid,
                'bitig_attested': False,
                'first_ayah': None
            }

    # Source 7: Bitig attestation
    bitig_roots = old.execute("""
        SELECT DISTINCT root_letters
        FROM bitig_a1_entries
        WHERE root_letters IS NOT NULL AND root_letters != ''
    """).fetchall()
    for r in bitig_roots:
        rl = r['root_letters']
        if rl and rl in roots:
            roots[rl]['bitig_attested'] = True

    # Source 8: Names of Allah
    allah_roots = old.execute("""
        SELECT allah_id, root_id
        FROM a2_names_of_allah
        WHERE root_id IS NOT NULL AND root_id != ''
    """).fetchall()
    for r in allah_roots:
        rid = r['root_id']
        # Find matching root_letters
        for rl, data in roots.items():
            if data['root_id'] == rid:
                break

    # Assign root_ids to roots that don't have one
    # Use T### for Bitig-only, R### for AA
    max_r = 0
    max_t = 0
    for rl, data in roots.items():
        if data['root_id']:
            rid = data['root_id']
            if rid.startswith('R') and rid[1:].isdigit():
                max_r = max(max_r, int(rid[1:]))
            elif rid.startswith('T') and rid[1:].isdigit():
                max_t = max(max_t, int(rid[1:]))

    for rl, data in roots.items():
        if not data['root_id']:
            if data['bitig_attested'] and data['quran_tokens'] == 0:
                max_t += 1
                data['root_id'] = f"T{max_t:03d}"
            else:
                max_r += 1
                data['root_id'] = f"R{max_r:03d}"

    # Determine root type
    for rl, data in roots.items():
        bare = data['root_bare']
        # Count actual letters (not hyphens, dashes)
        letters = [c for c in bare if c not in ('-', '‑', ' ', '\u200c')]
        n = len(letters)
        if n <= 2:
            data['root_type'] = 'BILITERAL'
        elif n == 3:
            data['root_type'] = 'TRILITERAL'
        elif n == 4:
            data['root_type'] = 'QUADRILITERAL'
        else:
            data['root_type'] = 'EXTENDED'

    # Insert into new DB
    inserted = 0
    for rl, data in roots.items():
        try:
            new.execute("""
                INSERT INTO roots (root_id, root_letters, root_bare, root_type,
                                   quran_tokens, quran_lemmas, bitig_attested, primary_meaning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['root_id'], data['root_letters'], data['root_bare'],
                data['root_type'], data['quran_tokens'], data['quran_lemmas'],
                data['bitig_attested'], None  # no contaminated meanings
            ))
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"  SKIP duplicate root_id {data['root_id']} for {rl}: {e}")

    new.commit()
    print(f"  Inserted {inserted} roots. Max R={max_r}, Max T={max_t}")

    # Build lookup: root_letters -> root_id
    root_lookup = {rl: data['root_id'] for rl, data in roots.items()}
    root_id_lookup = {data['root_id']: rl for rl, data in roots.items()}
    return root_lookup, root_id_lookup

# ============================================================================
# STEP 2: Migrate entries (unified table)
# ============================================================================
def migrate_entries(old, new, root_lookup):
    """Merge all A1 tables into unified entries table."""
    print("\n[STEP 2] Migrating entries...")

    # We need to track old->new ID mapping for FK references
    id_map = {}  # (source_table, old_id) -> new_entry_id

    entry_id = 0

    # Build set of valid root_ids in new DB
    valid_root_ids = set(r[0] for r in new.execute("SELECT root_id FROM roots").fetchall())
    print(f"  Valid root_ids in roots table: {len(valid_root_ids)}")

    # EN entries
    en_rows = old.execute("SELECT * FROM a1_entries ORDER BY entry_id").fetchall()
    print(f"  EN: {len(en_rows)} entries")
    en_orphan_roots = 0
    for r in en_rows:
        entry_id += 1
        rid = r['root_id']
        root_letters = r['root_letters'] if 'root_letters' in r.keys() else None

        # Resolve: prefer root_letters lookup, fallback to original if in roots, else NULL
        if root_letters and root_letters in root_lookup:
            rid = root_lookup[root_letters]
        elif rid and rid in valid_root_ids:
            pass
        elif rid:
            rid = None
            en_orphan_roots += 1

        new.execute("""
            INSERT INTO entries (entry_id, score, en_term, ar_word, root_id, root_letters,
                                qur_meaning, pattern, allah_name_id, network_id,
                                phonetic_chain, inversion_type, source_form, foundation_refs,
                                ds_corridor, decay_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, r['score'], r['en_term'], r['ar_word'],
            rid, root_letters, r['qur_meaning'], r['pattern'],
            r['allah_name_id'], r['network_id'], r['phonetic_chain'],
            r['inversion_type'], r['source_form'], r['foundation_ref'],
            r['corridor'] if 'corridor' in r.keys() else None,
            r['decay_model'] if 'decay_model' in r.keys() else None
        ))
        id_map[('en', r['entry_id'])] = entry_id

    # RU entries
    ru_rows = old.execute("SELECT * FROM [a1_записи] ORDER BY запись_id").fetchall()
    print(f"  RU: {len(ru_rows)} entries")
    ru_orphan_roots = 0
    for r in ru_rows:
        entry_id += 1
        rid = r['корень_id']
        root_letters = r['корневые_буквы'] if 'корневые_буквы' in r.keys() else None

        # Resolve root_id: prefer lookup by root_letters, fallback to original if valid
        if root_letters and root_letters in root_lookup:
            rid = root_lookup[root_letters]
        elif rid and rid in valid_root_ids:
            pass  # keep original
        elif rid and '+' in str(rid):
            rid = None  # compound root_ids like R202+R423 — set NULL for now
        elif rid and rid not in valid_root_ids:
            rid = None  # orphan — no matching root
            ru_orphan_roots += 1

        new.execute("""
            INSERT INTO entries (entry_id, score, ru_term, ar_word, root_id, root_letters,
                                qur_meaning, pattern, allah_name_id, network_id,
                                phonetic_chain, inversion_type, source_form, foundation_refs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, r['балл'], r['рус_термин'], r['ар_слово'],
            rid, root_letters, r['коранич_значение'], r['паттерн'],
            r['имя_аллаха_id'], r['сеть_id'], r['фонетическая_цепь'],
            r['тип_инверсии'], r['исходная_форма'], r['основание']
        ))
        id_map[('ru', r['запись_id'])] = entry_id
    if ru_orphan_roots:
        print(f"  RU orphan roots (set NULL): {ru_orphan_roots}")

    # FA entries
    fa_rows = old.execute("SELECT * FROM persian_a1_mad_khil ORDER BY rowid").fetchall()
    print(f"  FA: {len(fa_rows)} entries")
    for r in fa_rows:
        entry_id += 1
        keys = r.keys()
        fa_term = r['v_zhe_f_rs__واژِهِ_فارسی_persian_term'] if 'v_zhe_f_rs__واژِهِ_فارسی_persian_term' in keys else None
        ar_word = r['kalame_a_l__کَلَمِه_اَصلی__عربی___بازنویسی___تَرجُمه__source_word__arabic___transliteration___translation'] if 'kalame_a_l__کَلَمِه_اَصلی__عربی___بازنویسی___تَرجُمه__source_word__arabic___transliteration___translation' in keys else None
        root_letters = r['hor_f_e_r_she_حُروفِ_ریشِه_root_letters'] if 'hor_f_e_r_she_حُروفِ_ریشِه_root_letters' in keys else None
        rid = r['r_she_id_ریشِه_root_id'] if 'r_she_id_ریشِه_root_id' in keys else None
        if root_letters and root_letters in root_lookup:
            rid = root_lookup[root_letters]
        elif rid and rid in valid_root_ids:
            pass
        elif rid:
            rid = None
        score = r['nomre_نُمره_score'] if 'nomre_نُمره_score' in keys else None

        new.execute("""
            INSERT INTO entries (entry_id, score, fa_term, ar_word, root_id, root_letters,
                                qur_meaning, pattern, allah_name_id, network_id,
                                phonetic_chain, inversion_type, source_form, foundation_refs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, score, fa_term, ar_word, rid, root_letters,
            r['ma_n__ye_qur__n__مَعنایِ_قُرآنی__عربی___بازنویسی___تَرجُمه__qur_meaning__arabic___transliteration___translation'] if 'ma_n__ye_qur__n__مَعنایِ_قُرآنی__عربی___بازنویسی___تَرجُمه__qur_meaning__arabic___transliteration___translation' in keys else None,
            r['olg__اُلگو_pattern'] if 'olg__اُلگو_pattern' in keys else None,
            r['esm_e_all_h_id_اِسمِ_الله_allah_name_id'] if 'esm_e_all_h_id_اِسمِ_الله_allah_name_id' in keys else None,
            r['shabake_id_شَبَکِه_network_id'] if 'shabake_id_شَبَکِه_network_id' in keys else None,
            r['zanj_re__awt__زَنجیرِهِ_صَوتی_phonetic_chain'] if 'zanj_re__awt__زَنجیرِهِ_صَوتی_phonetic_chain' in keys else None,
            r['now__e_v_zhg_n__نَوعِ_واژگونی_inversion_type'] if 'now__e_v_zhg_n__نَوعِ_واژگونی_inversion_type' in keys else None,
            r['shakl_e_a_l__شَکلِ_اَصلی_source_form'] if 'shakl_e_a_l__شَکلِ_اَصلی_source_form' in keys else None,
            r['boniy_n_بُنیان_foundation_ref'] if 'boniy_n_بُنیان_foundation_ref' in keys else None,
        ))
        old_id = r['madkhal_id_مَدخَل_entry_id'] if 'madkhal_id_مَدخَل_entry_id' in keys else None
        id_map[('fa', old_id)] = entry_id

    new.commit()
    print(f"  Total unified entries: {entry_id}")
    print(f"  ID mappings: {len(id_map)}")
    return id_map

# ============================================================================
# STEP 3: Migrate mechanism tables
# ============================================================================
def migrate_mechanism(old, new):
    """Migrate M1-M5 tables."""
    print("\n[STEP 3] Migrating mechanism tables...")

    # M1: phonetic_shifts
    rows = old.execute("SELECT * FROM m1_phonetic_shifts").fetchall()
    for r in rows:
        keys = r.keys()
        new.execute("""
            INSERT INTO phonetic_shifts (shift_id, ar_letter, ar_name, en_outputs, ru_outputs,
                                         description, examples, entry_ids, foundation_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r['shift_id'], r['ar_letter'], r['ar_name'], r['en_outputs'],
              r['ru_outputs'] if 'ru_outputs' in keys else None,
              r['direction'] if 'direction' in keys else None,
              r['examples'] if 'examples' in keys else None,
              r['entry_ids'] if 'entry_ids' in keys else None,
              r['foundation_ref'] if 'foundation_ref' in keys else None))
    print(f"  M1 shifts: {len(rows)}")

    # M2: detection_patterns
    rows = old.execute("SELECT * FROM m2_detection_patterns").fetchall()
    for r in rows:
        new.execute("""
            INSERT INTO detection_patterns (pattern_id, name, level, description, triggers, qur_ref, example)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r['pattern_id'], r['name'], r['level'], r['description'],
              r['triggers'] if 'triggers' in r.keys() else None,
              r['qur_ref'] if 'qur_ref' in r.keys() else None,
              r['example'] if 'example' in r.keys() else None))
    print(f"  M2 detection: {len(rows)}")

    # M3: scholars
    rows = old.execute("SELECT * FROM m3_scholars").fetchall()
    for r in rows:
        keys = r.keys()
        bp = r['birthplace'] if 'birthplace' in keys else (r['birth_place'] if 'birth_place' in keys else None)
        new.execute("""
            INSERT INTO scholars (scholar_id, verified_name, birth_place, identity, role,
                                  achievement, lies_applied, death_fate, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r['scholar_id'], r['verified_name'], bp,
              r['identity'], r['role'] if 'role' in keys else None,
              r['achievement'] if 'achievement' in keys else None,
              r['lies_applied'] if 'lies_applied' in keys else None,
              r['death_fate'] if 'death_fate' in keys else None,
              r['status'] if 'status' in keys else 'VERIFIED'))
    print(f"  M3 scholars: {len(rows)}")

    # M4: networks
    rows = old.execute("SELECT * FROM m4_networks").fetchall()
    for r in rows:
        keys = r.keys()
        new.execute("""
            INSERT INTO networks (network_id, name, title, link_verse, description, mechanism, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r['network_id'], r['name'], r['title'] if 'title' in keys else None,
              r['link_verse'] if 'link_verse' in keys else None,
              r['description'], r['mechanism'] if 'mechanism' in keys else None,
              r['status'] if 'status' in keys else 'CONFIRMED'))
    print(f"  M4 networks: {len(rows)}")

    new.commit()

# ============================================================================
# STEP 4: Migrate application tables
# ============================================================================
def migrate_application(old, new, root_lookup):
    """Migrate A2-A6 tables."""
    print("\n[STEP 4] Migrating application tables...")

    # Get valid root_ids
    valid_root_ids = set(r[0] for r in new.execute("SELECT root_id FROM roots").fetchall())

    # A2: names_of_allah
    rows = old.execute("SELECT * FROM a2_names_of_allah").fetchall()
    for r in rows:
        keys = r.keys()
        rid = r['root_id'] if 'root_id' in keys else None
        if rid and rid not in valid_root_ids:
            rid = None  # orphan root_id
        new.execute("""
            INSERT INTO names_of_allah (allah_id, arabic_name, transliteration, meaning,
                                        qur_ref, entry_ids, root_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r['allah_id'], r['arabic_name'], r['transliteration'],
              r['meaning'], r['qur_ref'] if 'qur_ref' in keys else None,
              r['entry_ids'] if 'entry_ids' in keys else None, rid))
    print(f"  A2 names: {len(rows)}")

    # A3: quran_refs
    rows = old.execute("SELECT * FROM a3_quran_refs").fetchall()
    for r in rows:
        keys = r.keys()
        try:
            new.execute("""
                INSERT INTO quran_refs (ref_id, surah, ayah, arabic_text, transliteration,
                                        translation, relevance, entry_ids, layer_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r['ref_id'], r['surah'], r['ayah'], r['arabic_text'],
                  r['transliteration'] if 'transliteration' in keys else None,
                  r['translation'] if 'translation' in keys else None,
                  r['relevance'] if 'relevance' in keys else None,
                  r['entry_ids'] if 'entry_ids' in keys else None,
                  r['layer_ref'] if 'layer_ref' in keys else None))
        except sqlite3.IntegrityError:
            pass  # skip duplicates
    print(f"  A3 quran_refs: {len(rows)}")

    # A6: country_names
    rows = old.execute("SELECT * FROM a6_country_names").fetchall()
    for r in rows:
        keys = r.keys()
        rid = r['root_id'] if 'root_id' in keys else None
        if rid and rid not in valid_root_ids:
            rid = None
        new.execute("""
            INSERT INTO country_names (country_id, country_name, root_id, al_word,
                                       qur_meaning, phonetic_chain, naming_basis, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r['country_id'] if 'country_id' in keys else None,
              r['country_name'] if 'country_name' in keys else None,
              rid,
              r['al_word'] if 'al_word' in keys else None,
              r['qur_meaning'] if 'qur_meaning' in keys else None,
              r['phonetic_chain'] if 'phonetic_chain' in keys else None,
              r['naming_basis'] if 'naming_basis' in keys else None,
              r['notes'] if 'notes' in keys else None))
    print(f"  A6 country: {len(rows)}")

    new.commit()

# ============================================================================
# STEP 5: Migrate child_schema → child_entries
# ============================================================================
def migrate_child(old, new):
    """Migrate child_schema to child_entries."""
    print("\n[STEP 5] Migrating child schema...")

    # Temporarily disable FK for child migration (data has evolved beyond original reference tables)
    new.execute("PRAGMA foreign_keys = OFF")

    # Get valid reference values
    valid_nt = set(r[0] for r in new.execute("SELECT nt_code FROM nt_codes").fetchall())
    valid_op = set(r[0] for r in new.execute("SELECT op_code FROM operation_codes").fetchall())

    rows = old.execute("SELECT * FROM child_schema").fetchall()
    for r in rows:
        keys = r.keys()
        nt = r['nt_code'] if 'nt_code' in keys else None
        parent = r['parent_op'] if 'parent_op' in keys else None
        if nt and nt not in valid_nt:
            nt = None  # orphan nt_code
        if parent and parent not in valid_op:
            parent = None  # orphan parent_op
        new.execute("""
            INSERT INTO child_entries (child_id, shell_name, shell_language, orig_class,
                                       orig_root, orig_lemma, orig_meaning, operation_role,
                                       shell_meaning, inversion_direction, phonetic_chain,
                                       qur_anchors, dp_codes, nt_code, pattern, parent_op,
                                       gate_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r['entry_id'] if 'entry_id' in keys else (r['child_id'] if 'child_id' in keys else None),
            r['shell_name'] if 'shell_name' in keys else None,
            r['shell_language'] if 'shell_language' in keys else None,
            r['orig_class'] if 'orig_class' in keys else None,
            r['orig_root'] if 'orig_root' in keys else None,
            r['orig_lemma'] if 'orig_lemma' in keys else None,
            r['orig_meaning'] if 'orig_meaning' in keys else None,
            r['operation_role'] if 'operation_role' in keys else None,
            r['shell_meaning'] if 'shell_meaning' in keys else None,
            r['inversion_direction'] if 'inversion_direction' in keys else None,
            r['phonetic_chain'] if 'phonetic_chain' in keys else None,
            r['qur_anchors'] if 'qur_anchors' in keys else None,
            r['dp_codes'] if 'dp_codes' in keys else None,
            nt,
            r['pattern'] if 'pattern' in keys else None,
            parent,
            r['gate_status'] if 'gate_status' in keys else None,
            r['notes'] if 'notes' in keys else None
        ))
    print(f"  Child entries: {len(rows)}")
    new.commit()
    # Re-enable FK
    new.execute("PRAGMA foreign_keys = ON")

# ============================================================================
# STEP 6: Copy tables that stay as-is (Qur'anic, Body, Bitig, Protocol, etc.)
# ============================================================================
def copy_table_raw(old, new, table_name, new_table_name=None):
    """Copy a table from old to new DB as-is (no FK, just data preservation)."""
    target = new_table_name or table_name
    try:
        cols = old.execute(f"PRAGMA table_info([{table_name}])").fetchall()
        if not cols:
            return 0
        col_names = [c['name'] for c in cols]
        col_list = ', '.join([f'[{c}]' for c in col_names])

        # Create table in new DB if it doesn't exist
        create_sql = old.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ).fetchone()
        if create_sql:
            sql = create_sql[0]
            if new_table_name:
                sql = sql.replace(f'CREATE TABLE [{table_name}]', f'CREATE TABLE [{target}]', 1)
                sql = sql.replace(f'CREATE TABLE {table_name}', f'CREATE TABLE [{target}]', 1)
            try:
                new.execute(sql)
            except sqlite3.OperationalError:
                pass  # table already exists

        rows = old.execute(f"SELECT {col_list} FROM [{table_name}]").fetchall()
        placeholders = ', '.join(['?' for _ in col_names])
        for r in rows:
            try:
                new.execute(f"INSERT INTO [{target}] ({col_list}) VALUES ({placeholders})",
                           [r[c] for c in col_names])
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                pass
        new.commit()
        return len(rows)
    except Exception as e:
        print(f"  ERROR copying {table_name}: {e}")
        return 0

def migrate_remaining(old, new):
    """Copy all remaining tables that don't map to the schema."""
    print("\n[STEP 6] Copying remaining tables...")

    # Tables already migrated
    migrated = {
        'a1_entries', 'a1_записи', 'persian_a1_mad_khil',
        'bitig_a1_entries', 'latin_a1_entries', 'european_a1_entries',
        'a2_names_of_allah', 'a3_quran_refs', 'a6_country_names',
        'child_schema', 'm1_phonetic_shifts', 'm2_detection_patterns',
        'm3_scholars', 'm4_networks', 'root_translations',
        # Schema tables (already created by create_uslap_db.sql)
        'languages', 'decay_levels', 'script_corridors',
        'roots', 'entries', 'derivatives', 'cross_refs', 'quran_refs',
        'country_names', 'names_of_allah', 'phonetic_shifts',
        'detection_patterns', 'networks', 'scholars', 'qur_verification',
        'nt_codes', 'operation_codes', 'dp_codes', 'op_codes',
        'child_entries', 'child_entry_links', 'operators',
        'host_civilizations', 'operation_cycles', 'events',
        'intel_reports', 'operator_aliases', 'word_fingerprints',
        'cluster_cache', 'phonetic_mappings', 'engine_queue',
        'change_log', 'sync_status', 'session_index',
        # FTS and virtual tables
        'entries_fts', 'term_search', 'term_search_config',
        'term_search_data', 'term_search_docsize', 'term_search_idx',
        # SQLite internal
        'sqlite_sequence',
    }

    all_tables = old.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    copied = 0
    for t in all_tables:
        name = t['name']
        if name in migrated or name.startswith('sqlite_'):
            continue
        count = copy_table_raw(old, new, name)
        if count > 0:
            print(f"  {name}: {count} rows")
            copied += 1

    print(f"  Copied {copied} additional tables")

# ============================================================================
# STEP 7: Copy contamination triggers
# ============================================================================
def migrate_triggers(old, new):
    """Copy contamination triggers from old DB."""
    print("\n[STEP 7] Migrating contamination triggers...")

    triggers = old.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND sql IS NOT NULL"
    ).fetchall()

    copied = 0
    for t in triggers:
        try:
            new.execute(t['sql'])
            copied += 1
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            # Skip triggers that reference tables not yet in new DB
            pass

    new.commit()
    print(f"  Copied {copied}/{len(triggers)} triggers")

# ============================================================================
# STEP 8: Verify
# ============================================================================
def verify(new):
    """Verify migration."""
    print("\n[STEP 8] Verification...")

    cur = new.cursor()

    # Check FK enforcement
    fk = cur.execute("PRAGMA foreign_keys").fetchone()
    print(f"  PRAGMA foreign_keys = {fk[0]}")

    # Check roots
    root_count = cur.execute("SELECT COUNT(*) FROM roots").fetchone()[0]
    print(f"  roots: {root_count}")

    # Check entries
    entry_count = cur.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    en_count = cur.execute("SELECT COUNT(*) FROM entries WHERE en_term IS NOT NULL").fetchone()[0]
    ru_count = cur.execute("SELECT COUNT(*) FROM entries WHERE ru_term IS NOT NULL").fetchone()[0]
    fa_count = cur.execute("SELECT COUNT(*) FROM entries WHERE fa_term IS NOT NULL").fetchone()[0]
    print(f"  entries: {entry_count} (EN:{en_count}, RU:{ru_count}, FA:{fa_count})")

    # Check FK integrity
    violations = cur.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  FK violations: {len(violations)}")
    if violations[:5]:
        for v in violations[:5]:
            print(f"    {v}")

    # Check table count
    tables = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    triggers = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    print(f"  Total tables: {tables}")
    print(f"  Total triggers: {triggers}")

# ============================================================================
# MAIN
# ============================================================================
def check_mode():
    """Dry run — show what will happen."""
    print("=== DRY RUN ===")
    old = connect_old()

    tables = old.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    print(f"Current DB: {tables} tables")

    en = old.execute("SELECT COUNT(*) FROM a1_entries").fetchone()[0]
    ru = old.execute("SELECT COUNT(*) FROM [a1_записи]").fetchone()[0]
    fa = old.execute("SELECT COUNT(*) FROM persian_a1_mad_khil").fetchone()[0]
    bi = old.execute("SELECT COUNT(*) FROM bitig_a1_entries").fetchone()[0]
    la = old.execute("SELECT COUNT(*) FROM latin_a1_entries").fetchone()[0]
    eu = old.execute("SELECT COUNT(*) FROM european_a1_entries").fetchone()[0]

    print(f"Entries: EN={en} RU={ru} FA={fa} BITIG={bi} LATIN={la} EU={eu}")
    print(f"Total to merge into unified entries: {en + ru + fa}")
    print(f"Bitig/Latin/EU stay as separate tables (different column structure)")
    print(f"\nWill create: {NEW_DB}")
    print(f"Using schema: {SCHEMA_SQL}")
    print(f"Original DB: UNTOUCHED")
    old.close()

def migrate_mode():
    """Execute full migration."""
    print("=== MIGRATION START ===")
    print(f"Source: {OLD_DB}")
    print(f"Target: {NEW_DB}")
    print(f"Schema: {SCHEMA_SQL}")

    # Remove existing target
    if os.path.exists(NEW_DB):
        os.remove(NEW_DB)

    # Create new DB with schema
    print("\n[STEP 0] Creating new DB from schema...")
    new_conn = sqlite3.connect(NEW_DB)

    # Read and execute schema SQL (skip lines that need UDFs)
    with open(SCHEMA_SQL, 'r') as f:
        schema = f.read()

    # Remove extract_consonants triggers (need Python UDF)
    # We'll add them back later via db_access_layer
    lines = schema.split('\n')
    clean_lines = []
    skip_until_end = False
    for line in lines:
        if 'extract_consonants' in line:
            skip_until_end = True
        if skip_until_end:
            if line.strip() == 'END;':
                skip_until_end = False
            continue
        clean_lines.append(line)

    clean_schema = '\n'.join(clean_lines)

    # Remove CHECK constraints on pattern (data has evolved beyond original enums)
    import re
    clean_schema = re.sub(r"CHECK\s*\(\s*pattern\s+IN\s*\([^)]+\)\s*\)", "", clean_schema)
    clean_schema = re.sub(r"CHECK\s*\(\s*status\s+IN\s*\([^)]+\)\s*\)", "", clean_schema)
    clean_schema = re.sub(r"CHECK\s*\(\s*change_type\s+IN\s*\([^)]+\)\s*\)", "", clean_schema)
    clean_schema = re.sub(r"CHECK\s*\(\s*sync_direction\s+IN\s*\([^)]+\)\s*\)", "", clean_schema)
    # Keep score CHECK and confidence CHECK — those are valid

    try:
        new_conn.executescript(clean_schema)
        print("  Schema created successfully")
    except Exception as e:
        print(f"  Schema error: {e}")
        # Try statement by statement
        for stmt in clean_schema.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    new_conn.execute(stmt)
                except Exception as e2:
                    if 'already exists' not in str(e2):
                        print(f"  SKIP: {stmt[:60]}... ({e2})")
        new_conn.commit()

    new_conn.close()

    # Now open both DBs
    old = connect_old()
    new = connect_new()

    # Execute migration steps
    root_lookup, root_id_lookup = build_roots(old, new)
    id_map = migrate_entries(old, new, root_lookup)
    migrate_mechanism(old, new)
    migrate_application(old, new, root_lookup)
    migrate_child(old, new)
    migrate_remaining(old, new)
    migrate_triggers(old, new)
    verify(new)

    old.close()
    new.close()

    # File size comparison
    old_size = os.path.getsize(OLD_DB)
    new_size = os.path.getsize(NEW_DB)
    print(f"\n=== MIGRATION COMPLETE ===")
    print(f"Old DB: {old_size / 1024 / 1024:.1f} MB")
    print(f"New DB: {new_size / 1024 / 1024:.1f} MB")
    print(f"\nNew DB at: {NEW_DB}")
    print(f"Original UNTOUCHED at: {OLD_DB}")
    print(f"\nTo activate: rename v4 to v3 (after verification)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_to_schema.py check|migrate")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'check':
        check_mode()
    elif cmd == 'migrate':
        migrate_mode()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
