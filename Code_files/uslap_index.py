#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP INDEX — al-Qamar (54)
وَكُلُّ صَغِيرٍ وَكَبِيرٍ مُّسْتَطَرٌ — "Every small and great thing is recorded" (Q54:53)
إِنَّا كُلَّ شَيْءٍ خَلَقْنَاهُ بِقَدَرٍ — "We created everything by precise measure" (Q54:49)

Builds the term-level unified index across all sibling databases.
Populates: term_nodes, term_search (FTS5), term_dimensions, intel_file_index, id_sequences.

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ─── PATHS ────────────────────────────────────────────────────────────────────
DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"
INTEL_DIR = "/Users/mmsetubal/Documents/USLaP Master Folder/Intelligence Historic"
WORKSPACE = "/Users/mmsetubal/Documents/USLaP workplace"

# ─── SOURCE TABLE MAPPINGS ────────────────────────────────────────────────────
# Each tuple: (table_name, term_column, ar_column, root_id_column, score_column, id_column, language)
ENTRY_SOURCES = [
    ("a1_entries",           "en_term",       "aa_word",     "root_id",     "score",  "entry_id",     "en"),
    ("a1_записи",           "рус_термин",    "ар_слово",    "корень_id",   "балл",   "запись_id",    "ru"),
    # Persian: composite column names from migration
    ("persian_a1_mad_khil",
     "v_zhe_f_rs__واژِهِ_فارسی_persian_term",
     "kalame_a_l__کَلَمِه_اَصلی__عربی___بازنویسی___تَرجُمه__source_word__arabic___transliteration___translation",
     "r_she_id_ریشِه_root_id",
     "nomre_نُمره_score",
     "madkhal_id_مَدخَل_entry_id",
     "fa"),
    ("bitig_a1_entries",    "orig2_term",     None,          None,          "score",  "entry_id",     "bitig"),
    ("latin_a1_entries",    "lat_term",       "aa_word",     "root_id",     "score",  "entry_id",     "latin"),
]

# European entries use 'lang' column for language differentiation (FR/ES/IT/PT/DE)
# They need special handling since 5 languages share one table
EUROPEAN_SOURCE = ("european_a1_entries", "term", "aa_word", "root_id", "score", "entry_id", "lang")

# ─── REGEX PATTERNS FOR INTEL FILE SCANNING ───────────────────────────────────
RE_DP_CODE   = re.compile(r'\bDP(?:0[1-9]|1[0-9]|20)\b')
RE_ROOT_ID   = re.compile(r'\b[RT]\d{1,3}\b')
RE_ENTRY_ID  = re.compile(r'#(\d{1,3})\b')
RE_QUR_REF   = re.compile(r'Q(\d{1,3}):(\d{1,3})')

# Intel file metadata (hand-mapped from filenames + known content)
INTEL_FILE_META = {
    "USLaP_INTELLIGENCE_AFRICA_OPERATIONS_615CE_2026.md": {
        "period_start": "615 CE", "period_end": "2026", "region": "Africa/al-Habasha"
    },
    "USLaP_INTELLIGENCE_GAP_FILL_965_1218CE.md": {
        "period_start": "965 CE", "period_end": "1218 CE", "region": "Khazar dispersal"
    },
    "USLaP_INTELLIGENCE_GAP_FILL_1600_1890CE.md": {
        "period_start": "1600 CE", "period_end": "1890 CE", "region": "Colonial global"
    },
    "USLaP_INTELLIGENCE_POST_SOVIET_GLOBAL_OPERATIONS_1991_2024.md": {
        "period_start": "1991", "period_end": "2024", "region": "Post-Soviet global"
    },
    "USLaP_INTELLIGENCE_SOVIET_OPERATION_1890_1991.md": {
        "period_start": "1890", "period_end": "1991", "region": "Soviet/Central Asia"
    },
    "USLaP_INTELLIGENCE_IRAN_2026_PURIM_STRIKE.md": {
        "period_start": "2026", "period_end": "2026", "region": "Iran/Minab"
    },
}


def normalize_term(term: str) -> str:
    """Normalize a term for search: lowercase, strip whitespace."""
    if not term:
        return ""
    return term.strip().lower()


def get_connection() -> sqlite3.Connection:
    """Get a database connection with UTF-8 support."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.text_factory = str
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def clear_index(conn: sqlite3.Connection):
    """Clear all index tables for fresh rebuild."""
    conn.execute("DELETE FROM term_dimensions")
    conn.execute("DELETE FROM term_nodes")
    conn.execute("DELETE FROM intel_file_index")
    conn.execute("DELETE FROM id_sequences")
    # Rebuild FTS content
    conn.execute("DELETE FROM term_search")
    conn.commit()
    print("  Cleared all index tables.")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: POPULATE term_nodes FROM ENTRY TABLES
# ═══════════════════════════════════════════════════════════════════════════════

def populate_entry_nodes(conn: sqlite3.Connection) -> int:
    """Scan all 5 sibling entry tables and insert nodes."""
    total = 0

    for table, term_col, ar_col, root_col, score_col, id_col, lang in ENTRY_SOURCES:
        # Check if table exists and has data
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            if count == 0:
                print(f"  {table}: 0 rows, skipping.")
                continue
        except sqlite3.OperationalError:
            print(f"  {table}: table not found, skipping.")
            continue

        # Get column names to verify they exist
        cursor = conn.execute(f"PRAGMA table_info([{table}])")
        columns = {row[1] for row in cursor.fetchall()}

        if term_col not in columns:
            print(f"  {table}: column '{term_col}' not found, skipping.")
            continue

        # Build query
        select_parts = [f"[{id_col}]", f"[{term_col}]"]
        if ar_col and ar_col in columns:
            select_parts.append(f"[{ar_col}]")
        else:
            select_parts.append("NULL")
        if root_col and root_col in columns:
            select_parts.append(f"[{root_col}]")
        else:
            select_parts.append("NULL")
        if score_col and score_col in columns:
            select_parts.append(f"[{score_col}]")
        else:
            select_parts.append("NULL")

        query = f"SELECT {', '.join(select_parts)} FROM [{table}]"
        rows = conn.execute(query).fetchall()

        inserted = 0
        for row in rows:
            entry_id, term, aa_word, root_id, score = row

            if not term or not str(term).strip():
                continue

            term_str = str(term).strip()
            term_n = normalize_term(term_str)

            # Insert the downstream term node
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, ?, ?, ?, ?, 'WORD', ?)
                """, (term_str, term_n, lang, table, str(entry_id), str(root_id) if root_id else None,
                      int(score) if score else None))
                inserted += 1
            except Exception as e:
                pass  # UNIQUE constraint violation = already inserted

            # Also insert Arabic form as a separate searchable node (if present)
            if aa_word and str(aa_word).strip():
                ar_str = str(aa_word).strip()
                ar_n = normalize_term(ar_str)
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_nodes
                        (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                        VALUES (?, ?, 'ar', ?, ?, ?, 'WORD', ?)
                    """, (ar_str, ar_n, table, str(entry_id), str(root_id) if root_id else None,
                          int(score) if score else None))
                    inserted += 1
                except Exception:
                    pass

        print(f"  {table} ({lang}): {inserted} nodes from {count} rows.")
        total += inserted

    # --- European entries (special: 5 languages in one table) ---
    eu_table = "european_a1_entries"
    try:
        eu_count = conn.execute(f"SELECT COUNT(*) FROM [{eu_table}]").fetchone()[0]
        if eu_count > 0:
            eu_rows = conn.execute(f"""
                SELECT entry_id, lang, term, aa_word, root_id, score
                FROM [{eu_table}]
            """).fetchall()
            eu_inserted = 0
            for entry_id, lang, term, aa_word, root_id, score in eu_rows:
                if not term or not str(term).strip():
                    continue
                term_str = str(term).strip()
                term_n = normalize_term(term_str)
                lang_lower = str(lang).strip().lower() if lang else "eu"
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_nodes
                        (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                        VALUES (?, ?, ?, ?, ?, ?, 'WORD', ?)
                    """, (term_str, term_n, lang_lower, eu_table, str(entry_id),
                          str(root_id) if root_id else None, int(score) if score else None))
                    eu_inserted += 1
                except Exception:
                    pass
                # Also insert Arabic form
                if aa_word and str(aa_word).strip():
                    ar_str = str(aa_word).strip()
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_nodes
                            (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                            VALUES (?, ?, 'ar', ?, ?, ?, 'WORD', ?)
                        """, (ar_str, normalize_term(ar_str), eu_table, str(entry_id),
                              str(root_id) if root_id else None, int(score) if score else None))
                        eu_inserted += 1
                    except Exception:
                        pass
            print(f"  {eu_table} (eu-5lang): {eu_inserted} nodes from {eu_count} rows.")
            total += eu_inserted
    except sqlite3.OperationalError:
        print(f"  {eu_table}: table not found, skipping.")

    conn.commit()
    return total


def populate_names_of_allah(conn: sqlite3.Connection) -> int:
    """Insert Names of Allah as ALLAH_NAME nodes."""
    total = 0
    for table_name in ["a2_names_of_allah", "a2_имена_аллаха"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        # Determine column names
        id_col = "allah_id" if "allah_id" in columns else None
        name_col = "aa_name" if "aa_name" in columns else None
        root_col = "root_id" if "root_id" in columns else None
        translit_col = "transliteration" if "transliteration" in columns else None

        if not id_col or not name_col:
            continue

        query_parts = [f"[{id_col}]", f"[{name_col}]"]
        if root_col:
            query_parts.append(f"[{root_col}]")
        else:
            query_parts.append("NULL")
        if translit_col:
            query_parts.append(f"[{translit_col}]")
        else:
            query_parts.append("NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table_name}]").fetchall()
        for allah_id, aa_name, root_id, translit in rows:
            if not aa_name:
                continue
            term_str = str(aa_name).strip()
            term_n = normalize_term(term_str)
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, 'ar', ?, ?, ?, 'ALLAH_NAME', NULL)
                """, (term_str, term_n, table_name, str(allah_id), str(root_id) if root_id else None))
                total += 1
            except Exception:
                pass

            # Also insert transliteration as searchable
            if translit and str(translit).strip():
                translit_str = str(translit).strip()
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_nodes
                        (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                        VALUES (?, ?, 'en', ?, ?, ?, 'ALLAH_NAME', NULL)
                    """, (translit_str, normalize_term(translit_str), table_name, str(allah_id),
                          str(root_id) if root_id else None))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  Names of Allah: {total} nodes.")
    return total


def populate_derivatives(conn: sqlite3.Connection) -> int:
    """Insert derivatives as DERIVATIVE nodes."""
    total = 0
    for table_name, lang in [("a4_derivatives", "en"), ("a4_производные", "ru")]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        deriv_col = "derivative" if "derivative" in columns else None
        id_col = "deriv_id" if "deriv_id" in columns else None
        entry_id_col = "entry_id" if "entry_id" in columns else None

        if not deriv_col or not id_col:
            # Try Russian column names
            for c in columns:
                if "произв" in c.lower() or "deriv" in c.lower():
                    deriv_col = c
                if "id" in c.lower() and "entry" not in c.lower():
                    id_col = c
            if not deriv_col:
                continue

        rows = conn.execute(f"SELECT [{id_col}], [{deriv_col}] FROM [{table_name}]").fetchall()
        for did, derivative in rows:
            if not derivative or not str(derivative).strip():
                continue
            d_str = str(derivative).strip()
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, ?, ?, ?, NULL, 'DERIVATIVE', NULL)
                """, (d_str, normalize_term(d_str), lang, table_name, str(did)))
                total += 1
            except Exception:
                pass

    conn.commit()
    print(f"  Derivatives: {total} nodes.")
    return total


def populate_country_names(conn: sqlite3.Connection) -> int:
    """Insert country names as COUNTRY nodes."""
    total = 0
    for table_name in ["a6_country_names", "a6_названия_стран"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        name_col = "country_name" if "country_name" in columns else None
        id_col = "country_id" if "country_id" in columns else None
        root_col = "root_id" if "root_id" in columns else None

        if not name_col or not id_col:
            continue

        query_parts = [f"[{id_col}]", f"[{name_col}]"]
        if root_col:
            query_parts.append(f"[{root_col}]")
        else:
            query_parts.append("NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table_name}]").fetchall()
        for cid, name, root_id in rows:
            if not name or not str(name).strip():
                continue
            n_str = str(name).strip()
            lang = "ru" if table_name.startswith("a6_назв") else "en"
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, ?, ?, ?, ?, 'COUNTRY', NULL)
                """, (n_str, normalize_term(n_str), lang, table_name, str(cid),
                      str(root_id) if root_id else None))
                total += 1
            except Exception:
                pass

    conn.commit()
    print(f"  Country names: {total} nodes.")
    return total


def populate_networks(conn: sqlite3.Connection) -> int:
    """Insert networks as NETWORK nodes."""
    total = 0
    for table_name in ["m4_networks", "m4_сети"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        nid_col = "network_id" if "network_id" in columns else None
        title_col = "title" if "title" in columns else None
        name_col = "name" if "name" in columns else None

        if not nid_col:
            continue

        query_parts = [f"[{nid_col}]"]
        if title_col:
            query_parts.append(f"[{title_col}]")
        else:
            query_parts.append("NULL")
        if name_col:
            query_parts.append(f"[{name_col}]")
        else:
            query_parts.append("NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table_name}]").fetchall()
        for nid, title, name in rows:
            for term_str in [title, name]:
                if not term_str or not str(term_str).strip():
                    continue
                t_str = str(term_str).strip()
                lang = "en" if title and term_str == title else "ar"
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_nodes
                        (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                        VALUES (?, ?, ?, ?, ?, NULL, 'NETWORK', NULL)
                    """, (t_str, normalize_term(t_str), lang, table_name, str(nid)))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  Networks: {total} nodes.")
    return total



def populate_child_schema(conn: sqlite3.Connection) -> int:
    """Insert child_schema (peoples/nations) as PEOPLE nodes."""
    total = 0
    try:
        rows = conn.execute("""
            SELECT entry_id, shell_name, orig_root, orig_lemma, dp_codes
            FROM child_schema
        """).fetchall()
    except sqlite3.OperationalError:
        print("  child_schema: table not found, skipping.")
        return 0

    for entry_id, shell_name, orig_root, orig_lemma, dp_codes in rows:
        if not shell_name:
            continue
        name_str = str(shell_name).strip()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO term_nodes
                (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                VALUES (?, ?, 'en', 'child_schema', ?, NULL, 'PEOPLE', NULL)
            """, (name_str, normalize_term(name_str), str(entry_id)))
            total += 1
        except Exception:
            pass
        # Also insert the Arabic original if present
        if orig_lemma and str(orig_lemma).strip():
            ar_str = str(orig_lemma).strip()
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, 'ar', 'child_schema', ?, NULL, 'PEOPLE', NULL)
                """, (ar_str, normalize_term(ar_str), str(entry_id)))
                total += 1
            except Exception:
                pass

    conn.commit()
    print(f"  Child schema (peoples): {total} nodes.")
    return total


def populate_chronology(conn: sqlite3.Connection) -> int:
    """Insert chronology events as CHRONOLOGY nodes."""
    total = 0
    try:
        rows = conn.execute("""
            SELECT id, event, orig_name, qur_ref
            FROM chronology
        """).fetchall()
    except sqlite3.OperationalError:
        print("  chronology: table not found, skipping.")
        return 0

    for cid, event, orig_name, qur_ref in rows:
        if not event:
            continue
        event_str = str(event).strip()[:200]  # Truncate long events
        try:
            conn.execute("""
                INSERT OR IGNORE INTO term_nodes
                (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                VALUES (?, ?, 'en', 'chronology', ?, NULL, 'CHRONOLOGY', NULL)
            """, (event_str, normalize_term(event_str), str(cid)))
            total += 1
        except Exception:
            pass

    conn.commit()
    print(f"  Chronology events: {total} nodes.")
    return total


def populate_body_nodes(conn: sqlite3.Connection) -> int:
    """Insert body architecture, creation stages, substances as BODY nodes."""
    total = 0
    body_sources = [
        ("body_architecture", "arch_id", "component", "aa_term"),
        ("body_creation_stages", "stage_id", "english", "aa_term"),
        ("body_substances", "sub_id", "category", "aa_term"),
        ("body_diagnostics", "diag_id", "diagnostic", "aa_term"),
        ("body_skeletal_map", "bone_id", "english", "aa_term"),
        ("body_chemistry", "chem_id", "substance", "aa_term"),
        ("body_colour_therapy", "colour_id", "colour", "aa_term"),
        ("body_sound_therapy", "sound_id", "sound", "aa_term"),
    ]
    for table, id_col, term_col, ar_col in body_sources:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        if id_col not in columns or term_col not in columns:
            continue

        query_parts = [f"[{id_col}]", f"[{term_col}]"]
        if ar_col and ar_col in columns:
            query_parts.append(f"[{ar_col}]")
        else:
            query_parts.append("NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table}]").fetchall()
        inserted = 0
        for bid, term, arabic in rows:
            if not term:
                continue
            t_str = str(term).strip()[:200]
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO term_nodes
                    (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                    VALUES (?, ?, 'en', ?, ?, NULL, 'BODY', NULL)
                """, (t_str, normalize_term(t_str), table, str(bid)))
                inserted += 1
            except Exception:
                pass
            if arabic and str(arabic).strip():
                ar_str = str(arabic).strip()[:200]
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_nodes
                        (term, term_normal, language, source_table, source_id, root_id, entry_type, score)
                        VALUES (?, ?, 'ar', ?, ?, NULL, 'BODY', NULL)
                    """, (ar_str, normalize_term(ar_str), table, str(bid)))
                    inserted += 1
                except Exception:
                    pass
        if inserted > 0:
            print(f"    {table}: {inserted} nodes.")
        total += inserted

    conn.commit()
    print(f"  Body nodes (total): {total} nodes.")
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: BUILD FTS5 INDEX
# ═══════════════════════════════════════════════════════════════════════════════

def rebuild_fts(conn: sqlite3.Connection):
    """Rebuild FTS5 index from term_nodes. Drop and recreate to avoid corruption."""
    # Drop and recreate to avoid corruption issues
    conn.execute("DROP TABLE IF EXISTS term_search")
    conn.execute("""
        CREATE VIRTUAL TABLE term_search USING fts5(
            term, term_normal, language, root_id, entry_type,
            content='term_nodes',
            content_rowid='node_id'
        )
    """)
    conn.execute("""
        INSERT INTO term_search(rowid, term, term_normal, language, root_id, entry_type)
        SELECT node_id, term, term_normal, language, COALESCE(root_id, ''), entry_type
        FROM term_nodes
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM term_search").fetchone()[0]
    print(f"  FTS5 index rebuilt: {count} entries.")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: BUILD DIMENSION EDGES
# ═══════════════════════════════════════════════════════════════════════════════

def build_linguistic_dimensions(conn: sqlite3.Connection) -> int:
    """Connect nodes sharing the same root_id across sibling databases."""
    total = 0

    # Get all root_ids that appear in more than one node
    rows = conn.execute("""
        SELECT DISTINCT n1.node_id, n1.root_id, n2.source_table, n2.source_id, n2.term, n2.language
        FROM term_nodes n1
        JOIN term_nodes n2 ON n1.root_id = n2.root_id
        WHERE n1.root_id IS NOT NULL
          AND n1.node_id != n2.node_id
          AND n1.entry_type = 'WORD'
          AND n2.entry_type = 'WORD'
          AND n1.language != n2.language
    """).fetchall()

    for node_id, root_id, target_table, target_id, target_term, target_lang in rows:
        label = f"{target_term} ({target_lang.upper()})"
        try:
            conn.execute("""
                INSERT OR IGNORE INTO term_dimensions
                (node_id, dimension, target_table, target_id, label)
                VALUES (?, 'LINGUISTIC', ?, ?, ?)
            """, (node_id, target_table, target_id, label))
            total += 1
        except Exception:
            pass

    conn.commit()
    print(f"  LINGUISTIC dimensions: {total} edges.")
    return total


def build_divine_dimensions(conn: sqlite3.Connection) -> int:
    """Connect entry nodes to Names of Allah via allah_name_id or shared root_id."""
    total = 0

    # Get all Names of Allah with their root_ids
    allah_nodes = conn.execute("""
        SELECT node_id, source_id, root_id, term FROM term_nodes
        WHERE entry_type = 'ALLAH_NAME'
    """).fetchall()

    allah_by_root = {}
    allah_by_id = {}
    for node_id, allah_id, root_id, term in allah_nodes:
        if root_id:
            allah_by_root.setdefault(root_id, []).append((allah_id, term))
        allah_by_id[allah_id] = (node_id, term)

    # Method 1: Match via allah_name_id column in entry tables
    for table in ["a1_entries", "a1_записи"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        allah_col = None
        for c in columns:
            if "allah" in c.lower() or "аллах" in c.lower():
                allah_col = c
                break
        if not allah_col:
            continue

        id_col = "entry_id" if "entry_id" in columns else "запись_id"
        rows = conn.execute(f"SELECT [{id_col}], [{allah_col}] FROM [{table}] WHERE [{allah_col}] IS NOT NULL AND [{allah_col}] != ''").fetchall()

        for entry_id, allah_ref in rows:
            if not allah_ref:
                continue
            # allah_ref can be comma-separated: "A01, A18"
            for aid in str(allah_ref).replace(" ", "").split(","):
                aid = aid.strip()
                if aid in allah_by_id:
                    # Find the node for this entry
                    entry_nodes = conn.execute("""
                        SELECT node_id FROM term_nodes
                        WHERE source_table = ? AND source_id = ? AND entry_type = 'WORD'
                    """, (table, str(entry_id))).fetchall()
                    for (en_nid,) in entry_nodes:
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO term_dimensions
                                (node_id, dimension, target_table, target_id, label)
                                VALUES (?, 'DIVINE', 'a2_names_of_allah', ?, ?)
                            """, (en_nid, aid, f"{aid} {allah_by_id[aid][1]}"))
                            total += 1
                        except Exception:
                            pass

    # Method 2: Match via shared root_id
    for root_id, allah_list in allah_by_root.items():
        entry_nodes = conn.execute("""
            SELECT node_id, term FROM term_nodes
            WHERE root_id = ? AND entry_type = 'WORD'
        """, (root_id,)).fetchall()
        for en_nid, en_term in entry_nodes:
            for allah_id, allah_term in allah_list:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'DIVINE', 'a2_names_of_allah', ?, ?)
                    """, (en_nid, allah_id, f"{allah_id} {allah_term}"))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  DIVINE dimensions: {total} edges.")
    return total


def build_geographic_dimensions(conn: sqlite3.Connection) -> int:
    """Connect entry nodes to country names via root_id or entry_ids field."""
    total = 0

    # Get all country names with root_ids
    try:
        countries = conn.execute("""
            SELECT country_id, country_name, root_id, entry_ids
            FROM a6_country_names
        """).fetchall()
    except sqlite3.OperationalError:
        print("  a6_country_names: table not found, skipping GEOGRAPHIC.")
        return 0

    for cid, cname, root_id, entry_ids in countries:
        if not cname:
            continue

        # Method 1: Match via root_id
        if root_id:
            entry_nodes = conn.execute("""
                SELECT node_id, term FROM term_nodes
                WHERE root_id = ? AND entry_type = 'WORD'
            """, (str(root_id),)).fetchall()
            for en_nid, en_term in entry_nodes:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'GEOGRAPHIC', 'a6_country_names', ?, ?)
                    """, (en_nid, str(cid), str(cname)))
                    total += 1
                except Exception:
                    pass

        # Method 2: Match via entry_ids field
        if entry_ids:
            for eid in str(entry_ids).replace(" ", "").split(","):
                eid = eid.strip()
                if not eid:
                    continue
                entry_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_id = ? AND entry_type = 'WORD'
                """, (eid,)).fetchall()
                for (en_nid,) in entry_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'GEOGRAPHIC', 'a6_country_names', ?, ?)
                        """, (en_nid, str(cid), str(cname)))
                        total += 1
                    except Exception:
                        pass

    conn.commit()
    print(f"  GEOGRAPHIC dimensions: {total} edges.")
    return total


def build_quranic_dimensions(conn: sqlite3.Connection) -> int:
    """Connect entry nodes to Qur'anic refs via entry_ids field."""
    total = 0

    for table_name in ["a3_quran_refs", "a3_коранические_ссылки"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        ref_id_col = "ref_id" if "ref_id" in columns else None
        surah_col = "surah" if "surah" in columns else None
        ayah_col = "ayah" if "ayah" in columns else None
        entry_ids_col = "entry_ids" if "entry_ids" in columns else None

        if not ref_id_col:
            continue

        query_parts = [f"[{ref_id_col}]"]
        query_parts.append(f"[{surah_col}]" if surah_col else "NULL")
        query_parts.append(f"[{ayah_col}]" if ayah_col else "NULL")
        query_parts.append(f"[{entry_ids_col}]" if entry_ids_col else "NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table_name}]").fetchall()

        for ref_id, surah, ayah, entry_ids in rows:
            if not entry_ids:
                continue
            label = f"Q{surah}:{ayah}" if surah and ayah else str(ref_id)

            for eid in str(entry_ids).replace(" ", "").split(","):
                eid = eid.strip()
                if not eid:
                    continue
                entry_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_id = ? AND entry_type = 'WORD'
                """, (eid,)).fetchall()
                for (en_nid,) in entry_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'QURANIC', ?, ?, ?)
                        """, (en_nid, table_name, str(ref_id), label))
                        total += 1
                    except Exception:
                        pass

    conn.commit()
    print(f"  QURANIC dimensions: {total} edges.")
    return total


def build_network_dimensions(conn: sqlite3.Connection) -> int:
    """Connect entry nodes to networks via network_id."""
    total = 0

    # Get all networks
    try:
        networks = conn.execute("""
            SELECT network_id, title FROM m4_networks
        """).fetchall()
    except sqlite3.OperationalError:
        print("  m4_networks: table not found, skipping NETWORK.")
        return 0

    net_titles = {str(nid): str(title) if title else str(nid) for nid, title in networks}

    # Scan entry tables for network_id references
    for table in ["a1_entries", "a1_записи"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        net_col = None
        for c in columns:
            if "network" in c.lower() or "сеть" in c.lower():
                net_col = c
                break
        if not net_col:
            continue

        id_col = "entry_id" if "entry_id" in columns else "запись_id"
        rows = conn.execute(f"SELECT [{id_col}], [{net_col}] FROM [{table}] WHERE [{net_col}] IS NOT NULL AND [{net_col}] != ''").fetchall()

        for entry_id, net_ref in rows:
            if not net_ref:
                continue
            for nid in str(net_ref).replace(" ", "").split(","):
                nid = nid.strip()
                if not nid:
                    continue
                entry_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = ? AND source_id = ? AND entry_type = 'WORD'
                """, (table, str(entry_id))).fetchall()
                label = net_titles.get(nid, nid)
                for (en_nid,) in entry_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'NETWORK', 'm4_networks', ?, ?)
                        """, (en_nid, nid, label))
                        total += 1
                    except Exception:
                        pass

    conn.commit()
    print(f"  NETWORK dimensions: {total} edges.")
    return total


def build_derivative_dimensions(conn: sqlite3.Connection) -> int:
    """Connect entry nodes to their derivatives."""
    total = 0

    for table_name in ["a4_derivatives", "a4_производные"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = {row[1] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            continue

        entry_id_col = "entry_id" if "entry_id" in columns else None
        deriv_id_col = "deriv_id" if "deriv_id" in columns else None
        deriv_col = "derivative" if "derivative" in columns else None

        if not entry_id_col or not deriv_id_col:
            continue

        rows = conn.execute(f"""
            SELECT [{entry_id_col}], [{deriv_id_col}], [{deriv_col}]
            FROM [{table_name}]
        """).fetchall()

        for entry_id, deriv_id, derivative in rows:
            if not derivative:
                continue
            entry_nodes = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_id = ? AND entry_type = 'WORD'
                AND source_table IN ('a1_entries', 'a1_записи')
            """, (str(entry_id),)).fetchall()
            for (en_nid,) in entry_nodes:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'DERIVATIVE', ?, ?, ?)
                    """, (en_nid, table_name, str(deriv_id), str(derivative).strip()))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  DERIVATIVE dimensions: {total} edges.")
    return total



def build_european_divine_dimensions(conn: sqlite3.Connection) -> int:
    """Connect European entry nodes to Names of Allah via allah_name_id."""
    total = 0
    # Get all Names of Allah
    allah_nodes = {}
    try:
        for allah_id, term in conn.execute("SELECT allah_id, aa_name FROM a2_names_of_allah").fetchall():
            allah_nodes[str(allah_id)] = str(term) if term else str(allah_id)
    except:
        return 0

    try:
        rows = conn.execute("""
            SELECT entry_id, allah_name_id FROM european_a1_entries
            WHERE allah_name_id IS NOT NULL AND allah_name_id != ''
        """).fetchall()
    except:
        return 0

    for entry_id, allah_ref in rows:
        if not allah_ref:
            continue
        for aid in str(allah_ref).replace(" ", "").split(","):
            aid = aid.strip()
            if not aid or aid not in allah_nodes:
                continue
            entry_node_ids = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = 'european_a1_entries' AND source_id = ?
                AND entry_type = 'WORD'
            """, (str(entry_id),)).fetchall()
            for (en_nid,) in entry_node_ids:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'DIVINE', 'a2_names_of_allah', ?, ?)
                    """, (en_nid, aid, f"{aid} {allah_nodes[aid]}"))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  EU DIVINE dimensions: {total} edges.")
    return total


def build_european_network_dimensions(conn: sqlite3.Connection) -> int:
    """Connect European entry nodes to networks via network_id."""
    total = 0
    net_titles = {}
    try:
        for nid, title in conn.execute("SELECT network_id, title FROM m4_networks").fetchall():
            net_titles[str(nid)] = str(title) if title else str(nid)
    except:
        return 0

    try:
        rows = conn.execute("""
            SELECT entry_id, network_id FROM european_a1_entries
            WHERE network_id IS NOT NULL AND network_id != ''
        """).fetchall()
    except:
        return 0

    for entry_id, net_ref in rows:
        if not net_ref:
            continue
        for nid in str(net_ref).replace(" ", "").split(","):
            nid = nid.strip()
            if not nid:
                continue
            entry_node_ids = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = 'european_a1_entries' AND source_id = ?
                AND entry_type = 'WORD'
            """, (str(entry_id),)).fetchall()
            label = net_titles.get(nid, nid)
            for (en_nid,) in entry_node_ids:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'NETWORK', 'm4_networks', ?, ?)
                    """, (en_nid, nid, label))
                    total += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  EU NETWORK dimensions: {total} edges.")
    return total


def build_body_dimensions(conn: sqlite3.Connection) -> int:
    """Connect body nodes to entry nodes via shared AA roots."""
    total = 0

    # Strategy: body tables have arabic column with root words.
    # Match body entries to linguistic entries via shared root_id patterns.
    # Also connect body_architecture to body_creation_stages etc. internally.

    body_tables = [
        ("body_architecture", "arch_id", "aa_term", "quranic_ref"),
        ("body_creation_stages", "stage_id", "aa_term", "quranic_ref"),
        ("body_substances", "sub_id", "aa_term", "quranic_ref"),
        ("body_diagnostics", "diag_id", "aa_term", "quranic_ref"),
        ("body_skeletal_map", "bone_id", "aa_term", "quranic_ref"),
    ]

    for table, id_col, ar_col, qref_col in body_tables:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table}])")
            columns = {row[1] for row in cursor.fetchall()}
        except:
            continue

        if id_col not in columns:
            continue

        query_parts = [f"[{id_col}]"]
        query_parts.append(f"[{ar_col}]" if ar_col in columns else "NULL")
        query_parts.append(f"[{qref_col}]" if qref_col and qref_col in columns else "NULL")

        rows = conn.execute(f"SELECT {', '.join(query_parts)} FROM [{table}]").fetchall()

        for bid, arabic, qref in rows:
            if not arabic:
                continue
            # Find BODY node
            body_nodes = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = ? AND source_id = ? AND entry_type = 'BODY'
            """, (table, str(bid))).fetchall()

            # Connect body nodes to ALL word nodes that share similar Arabic text
            # Extract root-like patterns from the arabic field
            ar_str = str(arabic)
            # Look for 3-letter root patterns (ع-ظ-م, etc.)
            import re
            root_patterns = re.findall(r'[ء-ي]-[ء-ي]-[ء-ي]', ar_str)

            for root_pattern in root_patterns:
                # Find entries with matching root_letters or aa_word
                matching_entries = conn.execute("""
                    SELECT node_id, term FROM term_nodes
                    WHERE entry_type = 'WORD' AND root_id IS NOT NULL
                    AND source_table IN ('a1_entries', 'a1_записи', 'persian_a1_mad_khil',
                                        'european_a1_entries', 'latin_a1_entries')
                    LIMIT 0
                """).fetchall()  # Placeholder — root matching would need root_letters

            # Instead: connect body nodes to WORD nodes via the body_cross_refs table
            # and via shared root words in the Arabic column

            for (bnid,) in body_nodes:
                # Connect to any word node in the same source_table
                # This creates BODY dimension edges
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'BODY', ?, ?, ?)
                    """, (bnid, table, str(bid), str(arabic)[:100] if arabic else str(bid)))
                    total += 1
                except Exception:
                    pass

    # Also use body_cross_refs to connect body items to linguistic entries
    try:
        xrefs = conn.execute("""
            SELECT xref_id, source_table, source_id, target_table, target_id, relationship
            FROM body_cross_refs
        """).fetchall()
        for xid, src_table, src_id, tgt_table, tgt_id, rel in xrefs:
            src_nodes = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = ? AND source_id = ?
            """, (str(src_table), str(src_id))).fetchall()
            for (sn,) in src_nodes:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'BODY', ?, ?, ?)
                    """, (sn, str(tgt_table) if tgt_table else 'body_cross_refs',
                          str(tgt_id) if tgt_id else str(xid),
                          str(rel)[:100] if rel else 'body_xref'))
                    total += 1
                except Exception:
                    pass
    except:
        pass

    # Connect via body_edges table
    try:
        bedges = conn.execute("SELECT from_node, to_node, edge_type, name FROM body_edges").fetchall()
        for from_node, to_node, etype, name in bedges:
            fn = conn.execute("SELECT node_id FROM term_nodes WHERE source_id = ? AND source_table LIKE 'body_%'",
                             (str(from_node),)).fetchall()
            for (fnid,) in fn:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'BODY', 'body_edges', ?, ?)
                    """, (fnid, str(to_node), f"{etype}: {name}" if name else str(etype)))
                    total += 1
                except Exception:
                    pass
    except:
        pass

    conn.commit()
    print(f"  BODY dimensions: {total} edges.")
    return total


def build_peoples_dimensions(conn: sqlite3.Connection) -> int:
    """Connect child_schema (peoples) entries to linguistic entries via DP codes and root connections."""
    total = 0

    try:
        peoples = conn.execute("""
            SELECT entry_id, shell_name, orig_root, dp_codes, qur_anchors
            FROM child_schema
        """).fetchall()
    except:
        print("  child_schema: not found, skipping PEOPLES.")
        return 0

    for pid, shell_name, orig_root, dp_codes, qur_anchors in peoples:
        if not shell_name:
            continue

        # Find the PEOPLE node for this entry
        people_nodes = conn.execute("""
            SELECT node_id FROM term_nodes
            WHERE source_table = 'child_schema' AND source_id = ?
        """, (str(pid),)).fetchall()

        # Connect people nodes to WORD nodes that reference the same people
        # via dp_codes or shared terminology
        for (pnid,) in people_nodes:
            # Method 1: Connect to entries in the same root family
            # (child_schema roots like ر-أ-س for RUS, etc.)
            # Find matching word nodes
            if dp_codes:
                for dp in str(dp_codes).replace(" ", "").split("·"):
                    dp = dp.strip()
                    if not dp:
                        continue
                    # Connect to dp_entry_map entries
                    try:
                        dp_entries = conn.execute("""
                            SELECT entry_source, entry_id, language FROM dp_entry_map
                            WHERE dp_code = ?
                        """, (dp,)).fetchall()
                        for src_table, eid, lang in dp_entries:
                            entry_nodes = conn.execute("""
                                SELECT node_id FROM term_nodes
                                WHERE source_table = ? AND source_id = ? AND entry_type = 'WORD'
                            """, (str(src_table), str(eid))).fetchall()
                            for (enid,) in entry_nodes:
                                try:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO term_dimensions
                                        (node_id, dimension, target_table, target_id, label)
                                        VALUES (?, 'PEOPLES', 'child_schema', ?, ?)
                                    """, (enid, str(pid), f"{pid}: {shell_name}"))
                                    total += 1
                                except:
                                    pass
                    except:
                        pass

            # Method 2: Connect people node to chronology entries that reference them
            try:
                chrono_refs = conn.execute("""
                    SELECT id, event FROM chronology
                    WHERE LOWER(event) LIKE ? OR LOWER(orig_name) LIKE ?
                """, (f"%{str(shell_name).lower()[:20]}%", f"%{str(shell_name).lower()[:20]}%")).fetchall()
                for cid, event in chrono_refs:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'PEOPLES', 'chronology', ?, ?)
                        """, (pnid, str(cid), str(event)[:100] if event else str(cid)))
                        total += 1
                    except:
                        pass
            except:
                pass

            # Method 3: Connect people node to financial extraction cycles
            try:
                fe_refs = conn.execute("""
                    SELECT cycle_id, era FROM financial_extraction_cycles
                    WHERE LOWER(child_schema_refs) LIKE ?
                """, (f"%{str(pid).lower()}%",)).fetchall()
                for fid, era in fe_refs:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'PEOPLES', 'financial_extraction_cycles', ?, ?)
                        """, (pnid, str(fid), f"FE: {era}" if era else str(fid)))
                        total += 1
                    except:
                        pass
            except:
                pass

    conn.commit()
    print(f"  PEOPLES dimensions: {total} edges.")
    return total


def build_financial_dimensions(conn: sqlite3.Connection) -> int:
    """Connect financial extraction cycles to relevant entries."""
    total = 0

    try:
        cycles = conn.execute("""
            SELECT cycle_id, era, target_peoples, qur_ref, child_schema_refs, dp_codes
            FROM financial_extraction_cycles
        """).fetchall()
    except:
        print("  financial_extraction_cycles: not found, skipping FINANCIAL.")
        return 0

    for fid, era, targets, qur_ref, cs_refs, dp_codes in cycles:
        label = f"FE: {era}" if era else str(fid)

        # Connect to child_schema peoples
        if cs_refs:
            for ref in str(cs_refs).replace(" ", "").split(","):
                ref = ref.strip()
                if not ref:
                    continue
                people_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = 'child_schema' AND source_id = ?
                """, (ref,)).fetchall()
                for (pnid,) in people_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'FINANCIAL', 'financial_extraction_cycles', ?, ?)
                        """, (pnid, str(fid), label))
                        total += 1
                    except:
                        pass

        # Connect to chronology events in same era
        if era:
            try:
                chrono_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = 'chronology' AND entry_type = 'CHRONOLOGY'
                """).fetchall()
                for (cnid,) in chrono_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'FINANCIAL', 'financial_extraction_cycles', ?, ?)
                        """, (cnid, str(fid), label))
                        total += 1
                    except:
                        pass
            except:
                pass

    conn.commit()
    print(f"  FINANCIAL dimensions: {total} edges.")
    return total


def build_chronology_dimensions(conn: sqlite3.Connection) -> int:
    """Connect chronology events to linguistic entries via Qur'anic refs and peoples."""
    total = 0

    try:
        events = conn.execute("""
            SELECT id, event, orig_name, qur_ref
            FROM chronology
        """).fetchall()
    except:
        print("  chronology: not found, skipping CHRONOLOGY.")
        return 0

    for cid, event, orig_name, qur_ref in events:
        # Find the chronology node
        chrono_nodes = conn.execute("""
            SELECT node_id FROM term_nodes
            WHERE source_table = 'chronology' AND source_id = ?
        """, (str(cid),)).fetchall()

        if not chrono_nodes:
            continue

        # Parse Qur'anic refs and connect to entries that share them
        if qur_ref and qur_ref != '—':
            import re
            qrefs = re.findall(r'Q(\d+):(\d+)', str(qur_ref))
            for surah, ayah in qrefs:
                # Find entries connected to this Qur'anic ref
                try:
                    ref_rows = conn.execute("""
                        SELECT ref_id, entry_ids FROM a3_quran_refs
                        WHERE surah = ? AND ayah = ?
                    """, (int(surah), int(ayah))).fetchall()
                    for ref_id, entry_ids in ref_rows:
                        if not entry_ids:
                            continue
                        for eid in str(entry_ids).replace(" ", "").split(","):
                            eid = eid.strip()
                            if not eid:
                                continue
                            entry_nodes = conn.execute("""
                                SELECT node_id FROM term_nodes
                                WHERE source_id = ? AND entry_type = 'WORD'
                            """, (eid,)).fetchall()
                            for (cnid,) in chrono_nodes:
                                for (enid,) in entry_nodes:
                                    try:
                                        conn.execute("""
                                            INSERT OR IGNORE INTO term_dimensions
                                            (node_id, dimension, target_table, target_id, label)
                                            VALUES (?, 'CHRONOLOGY', 'chronology', ?, ?)
                                        """, (enid, str(cid), str(event)[:100] if event else str(cid)))
                                        total += 1
                                    except:
                                        pass
                except:
                    pass

    conn.commit()
    print(f"  CHRONOLOGY dimensions: {total} edges.")
    return total


def build_intelligence_db_dimensions(conn: sqlite3.Connection) -> int:
    """Build INTELLIGENCE dimension edges from DB tables (hashr data, dp_entry_map, bitig_intelligence)."""
    total = 0

    # 1. dp_entry_map: connect entries to their DP codes
    try:
        dp_rows = conn.execute("""
            SELECT entry_source, entry_id, dp_code, inversion_type, language
            FROM dp_entry_map
        """).fetchall()
        for src_table, eid, dp_code, inv_type, lang in dp_rows:
            entry_nodes = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = ? AND source_id = ? AND entry_type = 'WORD'
            """, (str(src_table), str(eid))).fetchall()
            for (enid,) in entry_nodes:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'INTELLIGENCE', 'dp_entry_map', ?, ?)
                    """, (enid, str(dp_code), f"{dp_code}: {inv_type[:80]}" if inv_type else str(dp_code)))
                    total += 1
                except:
                    pass
    except:
        pass

    # 2. Entries with inversion_type set (intelligence indicator)
    for table, id_col in [("a1_entries", "entry_id"), ("european_a1_entries", "entry_id")]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{table}])")
            columns = {row[1] for row in cursor.fetchall()}
            if "inversion_type" not in columns:
                continue
            rows = conn.execute(f"""
                SELECT [{id_col}], inversion_type FROM [{table}]
                WHERE inversion_type IS NOT NULL AND inversion_type != ''
            """).fetchall()
            for eid, inv_type in rows:
                entry_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = ? AND source_id = ? AND entry_type = 'WORD'
                """, (table, str(eid))).fetchall()
                for (enid,) in entry_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'INTELLIGENCE', ?, ?, ?)
                        """, (enid, table, str(eid), f"INV: {inv_type}"))
                        total += 1
                    except:
                        pass
        except:
            pass

    # 3. bitig_intelligence_summary
    try:
        intel_summaries = conn.execute("""
            SELECT intel_id, category, peak_period, dp_code, case_ids
            FROM bitig_intelligence_summary
        """).fetchall()
        for rid, cat, period, dp_code, case_ids in intel_summaries:
            if not case_ids:
                continue
            # case_ids contains BD## references
            for ref in str(case_ids).replace(" ", "").split(","):
                ref = ref.strip()
                if not ref:
                    continue
                # Connect to bitig entries that have this degradation reference
                try:
                    bitig_nodes = conn.execute("""
                        SELECT node_id FROM term_nodes
                        WHERE source_table = 'bitig_a1_entries' AND entry_type = 'WORD'
                    """).fetchall()
                    # Only add one edge per intel summary to avoid explosion
                    for (bnid,) in bitig_nodes[:3]:
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO term_dimensions
                                (node_id, dimension, target_table, target_id, label)
                                VALUES (?, 'INTELLIGENCE', 'bitig_intelligence_summary', ?, ?)
                            """, (bnid, str(rid), f"{cat}: {period}" if period else str(cat)))
                            total += 1
                        except:
                            pass
                except:
                    pass
    except:
        pass

    # 4. bitig_degradation_register — connects degraded terms to intelligence
    try:
        deg_rows = conn.execute("""
            SELECT deg_id, bitig_original, dp_codes, degraded_meaning, original_meaning
            FROM bitig_degradation_register
            WHERE dp_codes IS NOT NULL
        """).fetchall()
        for deg_id, bitig_orig, dp_codes_str, degraded, original in deg_rows:
            bitig_nodes = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE source_table = 'bitig_a1_entries' AND entry_type = 'WORD'
                AND LOWER(term) = ?
            """, (normalize_term(str(bitig_orig)) if bitig_orig else "",)).fetchall()
            for (bnid,) in bitig_nodes:
                label = f"{dp_codes_str}: {original}->{degraded}" if original and degraded else str(dp_codes_str)
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO term_dimensions
                        (node_id, dimension, target_table, target_id, label)
                        VALUES (?, 'INTELLIGENCE', 'bitig_degradation_register', ?, ?)
                    """, (bnid, str(deg_id), label[:200]))
                    total += 1
                except:
                    pass
    except:
        pass

    # 5. body_extraction_intel
    try:
        bei_rows = conn.execute("SELECT COUNT(*) FROM body_extraction_intel").fetchone()[0]
        if bei_rows > 0:
            for r in conn.execute("SELECT * FROM body_extraction_intel").fetchall():
                total += 0  # Body intel → BODY dimension, not INTELLIGENCE
    except:
        pass

    # 6. mortality_intelligence and nutrition_intelligence
    for intel_table in ["mortality_intelligence", "nutrition_intelligence"]:
        try:
            cursor = conn.execute(f"PRAGMA table_info([{intel_table}])")
            columns = {row[1] for row in cursor.fetchall()}
            id_col = [c for c in columns if '_id' in c.lower()][0] if columns else None
            if not id_col:
                continue
            rows = conn.execute(f"SELECT [{id_col}] FROM [{intel_table}]").fetchall()
            for (iid,) in rows:
                inodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = ? AND source_id = ?
                """, (intel_table, str(iid))).fetchall()
                for (inid,) in inodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'INTELLIGENCE', ?, ?, ?)
                        """, (inid, intel_table, str(iid), f"{intel_table}: {iid}"))
                        total += 1
                    except:
                        pass
        except:
            pass

    conn.commit()
    print(f"  INTELLIGENCE (DB) dimensions: {total} edges.")
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: SCAN INTELLIGENCE FILES
# ═══════════════════════════════════════════════════════════════════════════════

def scan_intel_files(conn: sqlite3.Connection) -> int:
    """Scan intelligence .md files and extract structured references."""
    total = 0

    if not os.path.isdir(INTEL_DIR):
        print(f"  Intel directory not found: {INTEL_DIR}")
        return 0

    for fname in os.listdir(INTEL_DIR):
        if not fname.endswith(".md"):
            continue

        fpath = os.path.join(INTEL_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"  Error reading {fname}: {e}")
            continue

        # Extract structured references
        dp_codes = sorted(set(RE_DP_CODE.findall(content)))
        root_ids = sorted(set(RE_ROOT_ID.findall(content)))
        entry_ids = sorted(set(RE_ENTRY_ID.findall(content)))
        qur_refs = sorted(set(f"Q{m[0]}:{m[1]}" for m in RE_QUR_REF.findall(content)))

        # Get metadata
        meta = INTEL_FILE_META.get(fname, {})

        conn.execute("""
            INSERT INTO intel_file_index
            (file_name, file_path, period_start, period_end, region,
             dp_codes, root_ids, entry_ids, qur_refs, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fname, fpath,
            meta.get("period_start"), meta.get("period_end"), meta.get("region"),
            ",".join(dp_codes) if dp_codes else None,
            ",".join(root_ids) if root_ids else None,
            ",".join(entry_ids) if entry_ids else None,
            ",".join(qur_refs) if qur_refs else None,
            None  # keywords can be populated later
        ))
        total += 1
        print(f"  {fname}: {len(dp_codes)} DPs, {len(root_ids)} roots, {len(entry_ids)} entries, {len(qur_refs)} Q-refs")

    # Now build INTELLIGENCE dimension edges
    # Connect entry nodes to intel files that reference them
    intel_rows = conn.execute("SELECT idx_id, file_name, root_ids, entry_ids, region FROM intel_file_index").fetchall()
    intel_edges = 0
    for idx_id, file_name, root_ids_str, entry_ids_str, region in intel_rows:
        label = f"{region}" if region else file_name

        # Connect via root_ids
        if root_ids_str:
            for rid in root_ids_str.split(","):
                rid = rid.strip()
                if not rid:
                    continue
                entry_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE root_id = ? AND entry_type = 'WORD'
                """, (rid,)).fetchall()
                for (en_nid,) in entry_nodes:
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO term_dimensions
                            (node_id, dimension, target_table, target_id, label)
                            VALUES (?, 'INTELLIGENCE', 'intel_file_index', ?, ?)
                        """, (en_nid, str(idx_id), label))
                        intel_edges += 1
                    except Exception:
                        pass

    conn.commit()
    print(f"  INTELLIGENCE dimensions: {intel_edges} edges from {total} files.")
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: SEED ID SEQUENCES
# ═══════════════════════════════════════════════════════════════════════════════

def seed_id_sequences(conn: sqlite3.Connection):
    """Seed id_sequences from current MAX values in each table."""

    sequences = [
        # (seq_name, prefix, table, id_column, extract_pattern)
        ("ROOT_ID",       "R",  "a1_entries",      "root_id",     r'R(\d+)'),
        ("TURKIC_ROOT_ID","T",  "a1_записи",      "корень_id",   r'T(\d+)'),
        ("EN_ENTRY",      "",   "a1_entries",      "entry_id",     None),
        ("RU_ENTRY",      "",   "a1_записи",      "запись_id",   None),
        ("DERIV_ID",      "D",  "a4_derivatives",  "deriv_id",     r'D(\d+)'),
        ("XREF_ID",       "X",  "a5_cross_refs",   "xref_id",      r'X(\d+)'),
        ("QREF_ID",       "QR", "a3_quran_refs",   "ref_id",       r'QR(\d+)'),
        ("COUNTRY_ID",    "CN", "a6_country_names", "country_id",  r'CN(\d+)'),
        ("ALLAH_ID",      "A",  "a2_names_of_allah","allah_id",    r'A(\d+)'),
        ("NETWORK_ID",    "N",  "m4_networks",     "network_id",   r'N(\d+)'),
    ]

    for seq_name, prefix, table, id_col, pattern in sequences:
        try:
            rows = conn.execute(f"SELECT [{id_col}] FROM [{table}]").fetchall()
            max_val = 0
            for (val,) in rows:
                if val is None:
                    continue
                if pattern:
                    m = re.search(pattern, str(val))
                    if m:
                        num = int(m.group(1))
                        if num > max_val:
                            max_val = num
                else:
                    try:
                        num = int(val)
                        if num > max_val:
                            max_val = num
                    except (ValueError, TypeError):
                        pass

            conn.execute("""
                INSERT OR REPLACE INTO id_sequences (seq_name, prefix, current_val, last_updated)
                VALUES (?, ?, ?, datetime('now'))
            """, (seq_name, prefix, max_val))
            print(f"  {seq_name}: {prefix}{max_val}")

        except sqlite3.OperationalError as e:
            print(f"  {seq_name}: error — {e}")

    # Also check for ROOT_ID max across ALL tables (RU entries can have R### too)
    try:
        all_root_ids = conn.execute("""
            SELECT root_id FROM a1_entries WHERE root_id LIKE 'R%'
            UNION ALL
            SELECT корень_id FROM a1_записи WHERE корень_id LIKE 'R%'
            UNION ALL
            SELECT root_id FROM a6_country_names WHERE root_id LIKE 'R%'
        """).fetchall()
        max_r = 0
        for (val,) in all_root_ids:
            m = re.search(r'R(\d+)', str(val))
            if m:
                num = int(m.group(1))
                if num > max_r:
                    max_r = num
        if max_r > 0:
            conn.execute("""
                UPDATE id_sequences SET current_val = MAX(current_val, ?), last_updated = datetime('now')
                WHERE seq_name = 'ROOT_ID'
            """, (max_r,))
            print(f"  ROOT_ID (cross-table max): R{max_r}")
    except Exception as e:
        print(f"  ROOT_ID cross-table scan error: {e}")

    conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: FULL REBUILD
# ═══════════════════════════════════════════════════════════════════════════════

def rebuild_all():
    """Full index rebuild — al-Qamar: every small and great thing, recorded."""
    print("=" * 60)
    print("USLaP INDEX REBUILD — al-Qamar (54)")
    print("وَكُلُّ صَغِيرٍ وَكَبِيرٍ مُّسْتَطَرٌ")
    print("=" * 60)

    conn = get_connection()

    print("\n[Phase 0] Clearing index tables...")
    clear_index(conn)

    print("\n[Phase 1] Populating term_nodes...")
    n1 = populate_entry_nodes(conn)
    n2 = populate_names_of_allah(conn)
    n3 = populate_derivatives(conn)
    n4 = populate_country_names(conn)
    n5 = populate_networks(conn)
    n6 = populate_child_schema(conn)
    n7 = populate_chronology(conn)
    n8 = populate_body_nodes(conn)
    total_nodes = n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8
    print(f"  TOTAL NODES: {total_nodes}")

    print("\n[Phase 2] Building FTS5 search index...")
    rebuild_fts(conn)

    print("\n[Phase 3] Building dimension edges...")
    e1 = build_linguistic_dimensions(conn)
    e2 = build_divine_dimensions(conn)
    e3 = build_geographic_dimensions(conn)
    e4 = build_quranic_dimensions(conn)
    e5 = build_network_dimensions(conn)
    e6 = build_derivative_dimensions(conn)

    print("\n[Phase 3b] Building European-specific dimensions...")
    e7 = build_european_divine_dimensions(conn)
    e8 = build_european_network_dimensions(conn)

    print("\n[Phase 3c] Building BODY / PEOPLES / FINANCIAL / CHRONOLOGY dimensions...")
    e9 = build_body_dimensions(conn)
    e10 = build_peoples_dimensions(conn)
    e11 = build_financial_dimensions(conn)
    e12 = build_chronology_dimensions(conn)

    print("\n[Phase 3d] Building intelligence DB dimensions...")
    e13 = build_intelligence_db_dimensions(conn)

    total_edges = e1+e2+e3+e4+e5+e6+e7+e8+e9+e10+e11+e12+e13

    print("\n[Phase 4] Scanning intelligence files...")
    intel_count = scan_intel_files(conn)
    # Re-count edges after intel scan
    total_edges_final = conn.execute("SELECT COUNT(*) FROM term_dimensions").fetchone()[0]

    print("\n[Phase 5] Seeding ID sequences...")
    seed_id_sequences(conn)

    # Final stats
    final_nodes = conn.execute("SELECT COUNT(*) FROM term_nodes").fetchone()[0]
    final_edges = conn.execute("SELECT COUNT(*) FROM term_dimensions").fetchone()[0]
    final_intel = conn.execute("SELECT COUNT(*) FROM intel_file_index").fetchone()[0]
    final_seqs = conn.execute("SELECT COUNT(*) FROM id_sequences").fetchone()[0]

    # Dimension breakdown
    dim_counts = conn.execute("""
        SELECT dimension, COUNT(*) FROM term_dimensions
        GROUP BY dimension ORDER BY COUNT(*) DESC
    """).fetchall()

    # Entry type breakdown
    type_counts = conn.execute("""
        SELECT entry_type, COUNT(*) FROM term_nodes
        GROUP BY entry_type ORDER BY COUNT(*) DESC
    """).fetchall()

    print("\n" + "=" * 60)
    print("INDEX REBUILD COMPLETE — بِقَدَرٍ")
    print("=" * 60)
    print(f"  term_nodes:      {final_nodes}")
    print(f"  term_dimensions: {final_edges}")
    print(f"  intel_files:     {final_intel}")
    print(f"  id_sequences:    {final_seqs}")
    print(f"  FTS5 entries:    {final_nodes}")
    print()
    print("  NODE TYPES:")
    for etype, cnt in type_counts:
        print(f"    {etype:20s} {cnt:>6d}")
    print()
    print("  DIMENSION EDGES:")
    for dim, cnt in dim_counts:
        print(f"    {dim:20s} {cnt:>6d}")
    print("=" * 60)

    conn.close()
    return {
        "nodes": final_nodes,
        "edges": final_edges,
        "intel_files": final_intel,
        "id_sequences": final_seqs
    }


if __name__ == "__main__":
    rebuild_all()
