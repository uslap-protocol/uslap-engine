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
    ("a1_entries",           "en_term",       "ar_word",     "root_id",     "score",  "entry_id",     "en"),
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
    ("latin_a1_entries",    "lat_term",       "ar_word",     "root_id",     "score",  "entry_id",     "latin"),
]

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
    conn = sqlite3.connect(DB_PATH)
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
            entry_id, term, ar_word, root_id, score = row

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
            if ar_word and str(ar_word).strip():
                ar_str = str(ar_word).strip()
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
        name_col = "arabic_name" if "arabic_name" in columns else None
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
        for allah_id, arabic_name, root_id, translit in rows:
            if not arabic_name:
                continue
            term_str = str(arabic_name).strip()
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
    total_nodes = n1 + n2 + n3 + n4 + n5
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
    total_edges = e1 + e2 + e3 + e4 + e5 + e6

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

    print("\n" + "=" * 60)
    print("INDEX REBUILD COMPLETE — بِقَدَرٍ")
    print("=" * 60)
    print(f"  term_nodes:      {final_nodes}")
    print(f"  term_dimensions: {final_edges}")
    print(f"  intel_files:     {final_intel}")
    print(f"  id_sequences:    {final_seqs}")
    print(f"  FTS5 entries:    {final_nodes}")
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
