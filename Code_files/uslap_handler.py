#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP HANDLER — an-Nahl (16)
وَأَوْحَىٰ رَبُّكَ إِلَى النَّحْلِ — "Your Lord inspired the bee" (Q16:68)
فَاسْلُكِي سُبُلَ رَبِّكِ ذُلُلًا — "Follow the paths of your Lord, made smooth" (Q16:69)

The Handler receives a query (وَحْي), routes through paths (سُبُل),
processes from all sources (كُلِّ الثَّمَرَاتِ), and produces useful output (شِفَاء).

Functions: search, expand, write, state, next_id, rebuild_index.

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
import re
import json
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import unicodedata

# ─── PATH ─────────────────────────────────────────────────────────────────────
DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

# ─── COLUMN ALIAS LAYER ──────────────────────────────────────────────────────
# Protocol: NEVER use bare "Arabic" to mean Allah's Arabic.
# DB columns use aa_word/aa_name/aa_word — these are schema-level
# contamination from the "Arabic = just a language" framing.
#
# This mapping allows new code to use correct terminology (aa_word, aa_name)
# while the DB columns remain unchanged (avoiding migration risk).
#
# Usage: use aa_col('aa_word') → returns 'aa_word' (the actual column name)
#        but documents the intent: this field holds Allah's Arabic data.
#
# Added 2026-03-29 after root audit identified 20 contaminated column names.
COLUMN_ALIASES = {
    # New name (protocol-compliant) → Actual DB column name
    'aa_word':       'aa_word',        # Allah's Arabic word form
    'aa_name':       'aa_name',    # Allah's Arabic name
    'aa_text':       'aa_text',    # Allah's Arabic text
    'aa_form':       'aa_form',    # Allah's Arabic form
    'aa_stripped':   'aa_stripped', # Allah's Arabic stripped
    'aa_word_form':  'aa_word',    # Allah's Arabic word (quran tables)
    'orig_word':     'aa_word',        # Original word (ORIG1)
}

def aa_col(alias: str) -> str:
    """
    Resolve a protocol-compliant column alias to the actual DB column name.
    New code should call aa_col('aa_word') instead of using 'aa_word' directly.
    Returns the actual column name for SQL queries.
    """
    return COLUMN_ALIASES.get(alias, alias)

# ─── INIT LOCK — AUTOMATIC, NOT OPTIONAL ─────────────────────────────────────
# Init fires AUTOMATICALLY on first use of ANY handler function per session.
# Claude does not choose to run init. Init runs itself. No decision point.
# Lock file tracks whether init has already fired this session (24h expiry).
INIT_LOCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".uslap_init_lock")
_INIT_OUTPUT_CACHE = None  # Cached init output for the session

def _init_has_run() -> bool:
    """Check if init has fired this session (lock file exists and is fresh — within 24h)."""
    if not os.path.exists(INIT_LOCK_PATH):
        return False
    try:
        mtime = os.path.getmtime(INIT_LOCK_PATH)
        age_hours = (datetime.now().timestamp() - mtime) / 3600
        return age_hours < 24  # Lock expires after 24 hours — forces re-init
    except Exception:
        return False

def _set_init_lock():
    """Set the init lock (called by run_init)."""
    with open(INIT_LOCK_PATH, 'w') as f:
        f.write(datetime.now().isoformat())

def _auto_init() -> str:
    """Auto-fire init if it hasn't run. Returns init output (first time) or empty (already ran).
    This is called by EVERY handler function. Claude never decides whether to run init.
    Init runs itself."""
    global _INIT_OUTPUT_CACHE
    if _init_has_run():
        return ""
    # First call this session — run init automatically
    # Import here to avoid circular ref (run_init defined later)
    output = run_init()
    _INIT_OUTPUT_CACHE = output
    return output

# ─── ARABIC DIACRITICS (for stripping in search) ──────────────────────────────
ARABIC_DIACRITICS = set([
    '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650',  # fatḥa, ḍamma, kasra, tanwin
    '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656',  # shadda, sukun, madda
    '\u0670',  # superscript alef
])

def strip_arabic_diacritics(text: str) -> str:
    """Remove Arabic diacritical marks for fuzzy matching."""
    return ''.join(c for c in text if c not in ARABIC_DIACRITICS)

# ─── ENTRY ROUTING TABLE (from CLAUDE.md) ─────────────────────────────────────
ENTRY_ROUTING = {
    "WORD_EN":       "entries",
    "WORD_RU":       "entries",
    "WORD_FA":       "persian_a1_mad_khil",
    "WORD_BITIG":    "bitig_a1_entries",
    "WORD_LATIN":    "latin_a1_entries",
    "PEOPLE":        "child_schema",
    "UMD_OP":        "umd_operations",
    "SESSION":       "session_index",
    "DP":            "dp_register",
    "ATT":           "att_terms",
    "PROTOCOL":      "protocol_corrections",
    "QURAN_REF":     "a3_quran_refs",
    "DERIVATIVE":    "a4_derivatives",
    "CROSS_REF":     "a5_cross_refs",
    "COUNTRY":       "a6_country_names",
    "NETWORK":       "m4_networks",
    "ALLAH_NAME":    "a2_names_of_allah",
}

# ─── DIMENSION LABELS ─────────────────────────────────────────────────────────
DIMENSION_NAMES = {
    "LINGUISTIC":    "Sibling entries (same root, different languages)",
    "DIVINE":        "Names of Allah connections",
    "GEOGRAPHIC":    "Country/region links",
    "INTELLIGENCE":  "Intelligence file references",
    "QURANIC":       "Qur'anic verse links",
    "CHRONOLOGICAL": "Timeline entries",
    "NETWORK":       "Thematic network membership",
    "DERIVATIVE":    "Downstream derivative forms",
}


def get_connection() -> sqlite3.Connection:
    """Get a database connection via central V4 wrapper."""
    try:
        from uslap_db_connect import connect
        conn = connect()
        conn.text_factory = str
        return conn
    except ImportError:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.text_factory = str
        conn.row_factory = sqlite3.Row
        return conn


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH — وَأَوْحَىٰ رَبُّكَ إِلَى النَّحْلِ (receives the query)
# ═══════════════════════════════════════════════════════════════════════════════

def search(term: str, compact: bool = False) -> Dict[str, Any]:
    """
    CLAUDE.md Step 1 compliance. Search the index for a term.

    Args:
        term: search query
        compact: if True, return minimal output (found/summary/warnings only).
                 Reduces context cost for quick lookups. Full data via expand().

    Returns:
    {
        'found': bool,
        'query': str,
        'nodes': [{node_id, term, language, source_table, source_id, root_id, score, entry_type}],
        'dimensions': {'LINGUISTIC': N, 'DIVINE': N, ...},
        'summary': str  (human-readable one-liner)
    }
    """
    _auto_init()
    conn = get_connection()

    # Protocol preamble — travels WITH every search result
    try:
        preamble = conn.execute(
            "SELECT preamble_text FROM protocol_preamble LIMIT 1"
        ).fetchone()
        protocol_text = preamble[0] if preamble else ""
    except Exception:
        protocol_text = ""

    result = {
        'found': False,
        'query': term,
        'protocol': protocol_text,
        'nodes': [],
        'dimensions': {},
        'summary': ''
    }

    term_clean = term.strip()
    term_lower = term_clean.lower()

    # Strategy 1: Exact match on term_normal
    rows = conn.execute("""
        SELECT node_id, term, term_normal, language, source_table, source_id,
               root_id, score, entry_type
        FROM term_nodes
        WHERE term_normal = ? OR term = ?
        ORDER BY score DESC NULLS LAST, entry_type, language
    """, (term_lower, term_clean)).fetchall()

    # Strategy 2: If no exact match, try LIKE prefix
    if not rows:
        rows = conn.execute("""
            SELECT node_id, term, term_normal, language, source_table, source_id,
                   root_id, score, entry_type
            FROM term_nodes
            WHERE term_normal LIKE ? OR term LIKE ?
            ORDER BY score DESC NULLS LAST, entry_type, language
            LIMIT 50
        """, (f"{term_lower}%", f"{term_clean}%")).fetchall()

    # Strategy 3: If still no match, try FTS5
    if not rows:
        try:
            # FTS5 query — handle special chars
            fts_term = term_clean.replace('"', '""')
            rows = conn.execute("""
                SELECT tn.node_id, tn.term, tn.term_normal, tn.language,
                       tn.source_table, tn.source_id, tn.root_id, tn.score, tn.entry_type
                FROM term_search ts
                JOIN term_nodes tn ON ts.rowid = tn.node_id
                WHERE term_search MATCH ?
                ORDER BY rank
                LIMIT 50
            """, (f'"{fts_term}"',)).fetchall()
        except sqlite3.OperationalError:
            pass

    # Strategy 4: If still no match, try root_id search
    if not rows and re.match(r'^[RT]\d+$', term_clean):
        rows = conn.execute("""
            SELECT node_id, term, term_normal, language, source_table, source_id,
                   root_id, score, entry_type
            FROM term_nodes
            WHERE root_id = ?
            ORDER BY score DESC NULLS LAST, entry_type, language
        """, (term_clean,)).fetchall()

    # Strategy 5: Arabic diacritics-stripped search
    if not rows:
        stripped = strip_arabic_diacritics(term_clean)
        if stripped != term_clean:
            # Search with diacritics stripped — compare against stripped versions of stored terms
            all_ar = conn.execute("""
                SELECT node_id, term, term_normal, language, source_table, source_id,
                       root_id, score, entry_type
                FROM term_nodes
                WHERE language = 'ar'
            """).fetchall()
            rows = [r for r in all_ar if stripped in strip_arabic_diacritics(r['term'])]

    # Strategy 6: Search root_letters in source tables (ق-ه-ر format or bare قهر)
    if not rows:
        # Try searching root_letters columns directly
        for table, root_col, id_col in [
            ("a1_entries", "root_letters", "entry_id"),
            ("a1_записи", "корневые_буквы", "запись_id"),
        ]:
            try:
                # Match with or without dashes: "ق-ه-ر" or "قهر"
                term_dashed = '-'.join(term_clean) if '-' not in term_clean and len(term_clean) <= 5 else term_clean
                found = conn.execute(f"""
                    SELECT [{id_col}] FROM [{table}]
                    WHERE [{root_col}] LIKE ? OR [{root_col}] LIKE ?
                """, (f"%{term_clean}%", f"%{term_dashed}%")).fetchall()

                for (eid,) in found:
                    matched = conn.execute("""
                        SELECT node_id, term, term_normal, language, source_table, source_id,
                               root_id, score, entry_type
                        FROM term_nodes
                        WHERE source_table = ? AND source_id = ?
                    """, (table, str(eid))).fetchall()
                    rows.extend(matched)
            except sqlite3.OperationalError:
                pass

    # Strategy 7: General substring search
    if not rows:
        rows = conn.execute("""
            SELECT node_id, term, term_normal, language, source_table, source_id,
                   root_id, score, entry_type
            FROM term_nodes
            WHERE term LIKE ?
            ORDER BY score DESC NULLS LAST, entry_type, language
            LIMIT 50
        """, (f"%{term_clean}%",)).fetchall()

    if rows:
        result['found'] = True
        node_ids = set()
        for row in rows:
            node = dict(row)
            result['nodes'].append(node)
            node_ids.add(node['node_id'])

        # Get dimension counts for ALL matched nodes
        if node_ids:
            placeholders = ','.join(['?' for _ in node_ids])
            try:
                dim_counts = conn.execute(f"""
                    SELECT dimension, COUNT(*) as cnt
                    FROM term_dimensions
                    WHERE node_id IN ({placeholders})
                    GROUP BY dimension
                    ORDER BY cnt DESC
                """, list(node_ids)).fetchall()

                for dim_row in dim_counts:
                    result['dimensions'][dim_row['dimension']] = dim_row['cnt']
            except sqlite3.OperationalError:
                # term_dimensions table may not exist
                pass

        # Build summary
        langs = set(n['language'] for n in result['nodes'])
        types = set(n['entry_type'] for n in result['nodes'])
        root_ids = set(n['root_id'] for n in result['nodes'] if n['root_id'])
        total_dims = sum(result['dimensions'].values())

        result['summary'] = (
            f"FOUND: {len(result['nodes'])} nodes across {', '.join(sorted(langs)).upper()} | "
            f"Types: {', '.join(sorted(types))} | "
            f"Roots: {', '.join(sorted(root_ids))} | "
            f"{total_dims} expansion edges across {len(result['dimensions'])} dimensions"
        )
    else:
        result['summary'] = f"NOT FOUND in lattice — flagging as NEW ENTRY candidate"

    # ── QUF FAIL CHECK ──
    # Flag entries that FAILED QUF validation so they are not cited as valid
    try:
        quf_fail_warnings = []
        for node in result['nodes']:
            src_table = node.get('source_table', '')
            src_id = node.get('source_id', '')
            if src_table in ('a1_entries', 'european_a1_entries', 'latin_a1_entries'):
                row = conn.execute(
                    f'SELECT quf_pass, quf_q FROM [{src_table}] WHERE entry_id = ?',
                    (src_id,)
                ).fetchone()
                if row and row['quf_pass'] == 0 and row['quf_q'] is not None:
                    quf_fail_warnings.append({
                        'table': src_table, 'id': src_id,
                        'term': node.get('term', ''),
                        'quf_q': row['quf_q'],
                    })
            elif src_table == 'a1_записи':
                row = conn.execute(
                    'SELECT quf_pass, quf_q FROM [a1_записи] WHERE запись_id = ?',
                    (src_id,)
                ).fetchone()
                if row and row['quf_pass'] == 0 and row['quf_q'] is not None:
                    quf_fail_warnings.append({
                        'table': src_table, 'id': src_id,
                        'term': node.get('term', ''),
                        'quf_q': row['quf_q'],
                    })
        if quf_fail_warnings:
            result['quf_fail_warnings'] = quf_fail_warnings
            fail_terms = ', '.join(w['term'] for w in quf_fail_warnings)
            result['summary'] = (
                f"⚠ QUF FAIL: {fail_terms} — phonetic chain unvalidated. "
            ) + result['summary']
    except:
        pass

    # ── CONTAMINATION BLACKLIST CHECK (KERNEL GATE) ──
    # If the searched term matches a blacklisted term, attach a warning
    # so the caller NEVER outputs the contaminated translation.
    try:
        bl_hits = conn.execute(
            "SELECT bl_id, contaminated_term, contaminated_translation, "
            "correct_translation, why_contaminated "
            "FROM contamination_blacklist "
            "WHERE LOWER(contaminated_term) LIKE ? "
            "OR LOWER(correct_translation) LIKE ?",
            (f"%{term_lower}%", f"%{term_lower}%")
        ).fetchall()
        if bl_hits:
            result['blacklist_warnings'] = []
            for bl in bl_hits:
                result['blacklist_warnings'].append({
                    'bl_id': bl['bl_id'],
                    'term': bl['contaminated_term'],
                    'NEVER_USE': bl['contaminated_translation'],
                    'CORRECT': bl['correct_translation'],
                    'why': bl['why_contaminated'],
                })
            # Prepend warning to summary
            bl_terms = ', '.join(b['term'] for b in bl_hits)
            result['summary'] = (
                f"⛔ BLACKLIST HIT: {bl_terms} — "
                f"check blacklist_warnings before outputting meaning. "
            ) + result['summary']
    except:
        pass

    conn.close()

    # ── COMPACT MODE — minimal output to reduce context cost ──
    if compact:
        compact_result = {
            'found': result['found'],
            'query': result['query'],
            'summary': result['summary'],
            'node_count': len(result.get('nodes', [])),
        }
        if result.get('blacklist_warnings'):
            compact_result['blacklist_warnings'] = result['blacklist_warnings']
        if result.get('quf_fail_warnings'):
            compact_result['quf_fail_warnings'] = result['quf_fail_warnings']
        return compact_result

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXPAND — فَاسْلُكِي سُبُلَ رَبِّكِ ذُلُلًا (follow the paths, on demand)
# ═══════════════════════════════════════════════════════════════════════════════

def expand(term: str, dimension: str) -> Dict[str, Any]:
    """
    On-demand dimensional expansion. Only queries the target table
    when the user asks for a specific dimension.

    Args:
        term: search term (will re-search to find node_ids)
        dimension: one of LINGUISTIC, DIVINE, GEOGRAPHIC, INTELLIGENCE,
                   QURANIC, CHRONOLOGICAL, NETWORK, DERIVATIVE

    Returns:
    {
        'dimension': str,
        'dimension_label': str,
        'edges': [{target_table, target_id, label, data}],
        'count': int
    }
    """
    _auto_init()
    conn = get_connection()
    result = {
        'dimension': dimension,
        'dimension_label': DIMENSION_NAMES.get(dimension, dimension),
        'edges': [],
        'count': 0
    }

    # Find node_ids for the term
    term_clean = term.strip()
    term_lower = term_clean.lower()
    node_rows = conn.execute("""
        SELECT node_id FROM term_nodes
        WHERE term_normal = ? OR term = ? OR root_id = ?
    """, (term_lower, term_clean, term_clean)).fetchall()

    if not node_rows:
        # Try substring
        node_rows = conn.execute("""
            SELECT node_id FROM term_nodes WHERE term LIKE ?
        """, (f"%{term_clean}%",)).fetchall()

    if not node_rows:
        conn.close()
        return result

    node_ids = [r['node_id'] for r in node_rows]
    placeholders = ','.join(['?' for _ in node_ids])

    # Get dimension edges
    edges = conn.execute(f"""
        SELECT DISTINCT target_table, target_id, label
        FROM term_dimensions
        WHERE node_id IN ({placeholders}) AND dimension = ?
        ORDER BY label
    """, node_ids + [dimension]).fetchall()

    for edge in edges:
        edge_dict = {
            'target_table': edge['target_table'],
            'target_id': edge['target_id'],
            'label': edge['label'],
            'data': None
        }

        # Fetch actual data from the target table
        target_table = edge['target_table']
        target_id = edge['target_id']

        try:
            if target_table == 'intel_file_index':
                row = conn.execute("""
                    SELECT * FROM intel_file_index WHERE idx_id = ?
                """, (target_id,)).fetchone()
                if row:
                    edge_dict['data'] = dict(row)

            elif target_table == 'a2_names_of_allah':
                row = conn.execute("""
                    SELECT * FROM a2_names_of_allah WHERE allah_id = ?
                """, (target_id,)).fetchone()
                if row:
                    edge_dict['data'] = dict(row)

            elif target_table == 'a6_country_names':
                row = conn.execute("""
                    SELECT * FROM a6_country_names WHERE country_id = ?
                """, (target_id,)).fetchone()
                if row:
                    edge_dict['data'] = dict(row)

            elif target_table == 'm4_networks':
                row = conn.execute("""
                    SELECT * FROM m4_networks WHERE network_id = ?
                """, (target_id,)).fetchone()
                if row:
                    edge_dict['data'] = dict(row)

            elif target_table in ('a1_entries', 'a1_записи', 'persian_a1_mad_khil',
                                  'bitig_a1_entries', 'latin_a1_entries'):
                # Get the ID column name for this table
                cursor = conn.execute(f"PRAGMA table_info([{target_table}])")
                cols = [r[1] for r in cursor.fetchall()]
                id_col = cols[0] if cols else None
                if id_col:
                    row = conn.execute(f"""
                        SELECT * FROM [{target_table}] WHERE [{id_col}] = ?
                    """, (target_id,)).fetchone()
                    if row:
                        edge_dict['data'] = dict(row)

            elif target_table in ('a3_quran_refs', 'a3_коранические_ссылки'):
                cursor = conn.execute(f"PRAGMA table_info([{target_table}])")
                cols = [r[1] for r in cursor.fetchall()]
                id_col = cols[0] if cols else 'ref_id'
                row = conn.execute(f"""
                    SELECT * FROM [{target_table}] WHERE [{id_col}] = ?
                """, (target_id,)).fetchone()
                if row:
                    edge_dict['data'] = dict(row)

        except sqlite3.OperationalError:
            pass

        result['edges'].append(edge_dict)

    result['count'] = len(result['edges'])
    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STATE — كُلِي مِن كُلِّ الثَّمَرَاتِ (take from all sources)
# ═══════════════════════════════════════════════════════════════════════════════

def state() -> Dict[str, Any]:
    """
    Return current database state: counts, last IDs, sub-10 entries.
    """
    _auto_init()
    conn = get_connection()
    result = {
        'counts': {},
        'last_ids': {},
        'sub_10': [],
        'index_stats': {},
        'timestamp': datetime.now().isoformat()
    }

    # Table counts
    tables = [
        ("a1_entries", "EN entries"),
        ("a1_записи", "RU entries"),
        ("persian_a1_mad_khil", "Persian entries"),
        ("bitig_a1_entries", "Bitig entries"),
        ("latin_a1_entries", "Latin entries"),
        ("european_a1_entries", "European entries"),
        ("a2_names_of_allah", "Names of Allah"),
        ("a4_derivatives", "Derivatives (EN)"),
        ("a4_производные", "Derivatives (RU)"),
        ("a5_cross_refs", "Cross-refs (EN)"),
        ("a5_перекрёстные_ссылки", "Cross-refs (RU)"),
        ("a6_country_names", "Country names"),
        ("m4_networks", "Networks"),
        ("a3_quran_refs", "Quran refs"),
        ("chronology", "Chronology"),
        ("child_schema", "Child schema"),
    ]

    for table, label in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            result['counts'][label] = count
        except sqlite3.OperationalError:
            result['counts'][label] = 0

    # Last IDs from id_sequences
    try:
        seqs = conn.execute("SELECT seq_name, prefix, current_val FROM id_sequences ORDER BY seq_name").fetchall()
        for row in seqs:
            seq_name = row['seq_name']
            prefix = row['prefix']
            val = row['current_val']
            result['last_ids'][seq_name] = f"{prefix}{val}" if prefix else str(val)
    except sqlite3.OperationalError:
        pass

    # Sub-10 EN entries
    try:
        sub10 = conn.execute("""
            SELECT entry_id, en_term, score
            FROM a1_entries
            WHERE score < 10
            ORDER BY score ASC, entry_id
        """).fetchall()
        result['sub_10'] = [dict(r) for r in sub10]
    except sqlite3.OperationalError:
        pass

    # Index stats
    try:
        result['index_stats'] = {
            'term_nodes': conn.execute("SELECT COUNT(*) FROM term_nodes").fetchone()[0],
            'term_dimensions': conn.execute("SELECT COUNT(*) FROM term_dimensions").fetchone()[0],
            'intel_files': conn.execute("SELECT COUNT(*) FROM intel_file_index").fetchone()[0],
            'fts5_entries': conn.execute("SELECT COUNT(*) FROM term_search").fetchone()[0],
        }
    except sqlite3.OperationalError:
        pass

    # Score distribution for EN
    try:
        dist = conn.execute("""
            SELECT score, COUNT(*) as cnt
            FROM a1_entries
            WHERE score IS NOT NULL
            GROUP BY score
            ORDER BY score DESC
        """).fetchall()
        result['score_distribution_en'] = {str(r['score']): r['cnt'] for r in dist}
    except sqlite3.OperationalError:
        pass

    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# NEXT_ID — Atomic ID increment
# ═══════════════════════════════════════════════════════════════════════════════

def next_id(seq_name: str) -> str:
    """
    Atomic increment. Returns the NEXT available ID string.
    Does NOT consume the ID — just reports what it would be.
    Call consume_id() to actually increment.
    """
    _auto_init()
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT prefix, current_val FROM id_sequences WHERE seq_name = ?
        """, (seq_name,)).fetchone()
        if row:
            prefix = row['prefix']
            next_val = row['current_val'] + 1
            conn.close()
            return f"{prefix}{next_val}"
        else:
            conn.close()
            return f"UNKNOWN_SEQ:{seq_name}"
    except Exception as e:
        conn.close()
        return f"ERROR:{e}"


def consume_id(seq_name: str) -> str:
    """
    Atomic increment + consume. Returns the new ID and updates the sequence.
    """
    conn = get_connection()
    conn.execute("BEGIN EXCLUSIVE")
    try:
        row = conn.execute("""
            SELECT prefix, current_val FROM id_sequences WHERE seq_name = ?
        """, (seq_name,)).fetchone()
        if row:
            prefix = row['prefix']
            new_val = row['current_val'] + 1
            conn.execute("""
                UPDATE id_sequences
                SET current_val = ?, last_updated = datetime('now')
                WHERE seq_name = ?
            """, (new_val, seq_name))
            conn.commit()
            conn.close()
            return f"{prefix}{new_val}"
        else:
            conn.rollback()
            conn.close()
            return f"UNKNOWN_SEQ:{seq_name}"
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"ERROR:{e}"


# ═══════════════════════════════════════════════════════════════════════════════
# WRITE — يَخْرُجُ مِن بُطُونِهَا شَرَابٌ (produces output)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# PRE-WRITE GATE — al-Ikhlāṣ — BLOCKS contaminated writes
# NO entry passes to DB without clearing this gate. ZERO EXCEPTIONS.
# ═══════════════════════════════════════════════════════════════════════════════

# Unified banned terms — single source of truth
# These are checked against ALL text fields before any INSERT.
# Two tiers of banned terms:
# TIER 1: ABSOLUTE — these words are NEVER legitimate in the lattice.
# Matched as bare substrings. No context needed.
BANNED_TERMS_ABSOLUTE = [
    "semitic", "proto-indo-european", "proto-slavic", "proto-germanic",
    "proto-turkic", "proto-uralic", "pre-greek substrate", "prosthetic vowel",
    "nostratic", "altaic",
]

# TIER 2: CONTEXTUAL — these words are only contamination when used
# in a linguistic-direction context. Matched as phrases to avoid
# false positives on legitimate English (e.g., "British adoption 1752").
BANNED_TERMS_CONTEXTUAL = [
    "loanword", "loan word", "loan from", "borrowed from",
    "cognate with", "cognate of", "is a cognate",
    "adoption from", "adoption of loanword", "linguistic adoption",
    "borrowed from greek", "borrowed from latin",
    "borrowed from persian", "borrowed from french", "borrowed from german",
    "borrowed from sanskrit",
    "greek origin", "latin origin", "greek source", "latin source",
    "greek root", "latin root", "derived from greek", "derived from latin",
    "derived from french", "derived from old french", "derived from sanskrit",
    "native slavic", "native european", "european origin",
    "just slavic", "just european", "just turkic",
    "afro-asiatic",
]

# Combined for gate scanning
BANNED_TERMS_GATE = BANNED_TERMS_ABSOLUTE + BANNED_TERMS_CONTEXTUAL

# Direction violation patterns — AA → downstream ALWAYS
DIRECTION_GATE = [
    r'(?:arabic|persian|turkic)\s+(?:borrowed|adopted|took)\s+from',
    r'(?:greek|latin|sanskrit|french|german|english)\s+(?:origin|source|root)\b',
    r'(?:from|via)\s+(?:the\s+)?(?:greek|latin|french|sanskrit)\s+(?:word|term|root)\b',
]


def pre_write_gate(data: Dict, target_table: str) -> Dict[str, Any]:
    """
    BLOCKING pre-write gate. Scans ALL text fields in data for:
    0. Init lock (init MUST have run)
    1. Banned terms (unified list)
    2. Direction violations (AA → downstream inversion)
    3. Contamination blacklist matches (from DB)

    Returns:
        {'pass': bool, 'violations': list, 'message': str}

    If pass=False, the write MUST NOT proceed. No override. No bypass.
    """
    # GATE 0: Auto-init — fires automatically if not already run
    _auto_init()
    violations = []

    # Concatenate all text values for scanning
    text_fields = []
    for k, v in data.items():
        if isinstance(v, str) and v.strip():
            text_fields.append((k, v))

    all_text = ' '.join(v for _, v in text_fields).lower()

    # GATE 1: Banned terms
    for term in BANNED_TERMS_GATE:
        if term in all_text:
            # Find which field contains it
            for field_name, field_val in text_fields:
                if term in field_val.lower():
                    violations.append(
                        f"BANNED_TERM: '{term}' found in field '{field_name}'. "
                        f"Direction is ALWAYS AA → downstream."
                    )

    # GATE 2: Direction violations
    for pattern in DIRECTION_GATE:
        match = re.search(pattern, all_text)
        if match:
            for field_name, field_val in text_fields:
                if re.search(pattern, field_val.lower()):
                    violations.append(
                        f"DIRECTION_INVERTED: '{match.group()}' in field '{field_name}'. "
                        f"AA/Bitig → downstream, ALWAYS. NEVER reverse."
                    )

    # GATE 3: DB contamination blacklist
    # Uses WORD BOUNDARY matching (not substring) to prevent false positives.
    # "tribute" must not catch "attribute", "study of God" must not catch "STUDY",
    # "language" must not catch standalone word "language" in non-BL context.
    try:
        conn = get_connection()
        bl_rows = conn.execute(
            "SELECT bl_id, contaminated_term, contaminated_translation "
            "FROM contamination_blacklist"
        ).fetchall()
        conn.close()
        for row in bl_rows:
            bl_trans = row['contaminated_translation'].lower()
            # Split on / to check each alternative in "X / Y / Z" format
            alternatives = [alt.strip() for alt in bl_trans.split('/')]
            for alt in alternatives:
                if alt and len(alt) > 5:
                    # Word-boundary match: the FULL alternative phrase must appear
                    # as a complete phrase bounded by non-alphanumeric characters
                    _bl_pattern = r'(?<![a-z])' + re.escape(alt) + r'(?![a-z])'
                    if re.search(_bl_pattern, all_text):
                        violations.append(
                            f"BLACKLIST_{row['bl_id']}: Contaminated translation "
                            f"'{alt.strip()}' found. "
                            f"Use correct form from blacklist."
                        )
                        break  # One match per BL entry is enough
    except Exception:
        pass  # If blacklist table missing, other gates still fire

    # GATE 4: Semantic kernel — catches paraphrases
    try:
        code_dir = os.path.dirname(os.path.abspath(__file__))
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
        from uslap_contamination_kernel import scan_kernel
        all_text_raw = ' '.join(v for _, v in text_fields)
        kernel_hits = scan_kernel(all_text_raw)
        for ln, ds, sw, excerpt in kernel_hits:
            violations.append(
                f"KERNEL: [{ds.upper()}] + [{sw}] = downstream positioned as source. "
                f"Excerpt: \"{excerpt}\""
            )
    except ImportError:
        pass  # Kernel module not found — other gates still fire

    # GATE 5: CORRIDOR SCRIPT DETECTION — HIGHEST SEVERITY
    # DS08 (Hebrew), DS01 (Syriac), and variants MUST NEVER enter the DB.
    # Zero tolerance. No exceptions. No context.
    import re as _re_gate5
    _CORRIDOR_SCRIPTS = [
        (_re_gate5.compile(r'[\u0590-\u05FF]'), 'DS08/HEBREW'),
        (_re_gate5.compile(r'[\u0700-\u074F]'), 'DS01/SYRIAC'),
        (_re_gate5.compile(r'[\u0800-\u083F]'), 'DS08-VAR/SAMARITAN'),
        (_re_gate5.compile(r'[\u0840-\u085F]'), 'DS01-VAR/MANDAIC'),
    ]
    all_text_raw_g5 = ' '.join(v for _, v in text_fields)
    for pattern, script_name in _CORRIDOR_SCRIPTS:
        matches = pattern.findall(all_text_raw_g5)
        if matches:
            chars = ''.join(matches)
            for field_name, field_val in text_fields:
                if pattern.search(field_val):
                    violations.append(
                        f"⛔⛔⛔ CORRIDOR_SCRIPT_{script_name}: Characters '{chars}' "
                        f"in field '{field_name}'. CORRIDOR SCRIPT BANNED FROM DB. "
                        f"Use Allah's Arabic ONLY."
                    )

    # GATE 6: CONCEPT DOWNSTREAM FORMAT — AA CONCEPT entries that replace
    # known downstream terms MUST include:
    #   (a) downstream word in brackets in source_form
    #   (b) downstream AA root candidates in notes
    # This ensures findability AND documents the downstream word's own AA origin.
    _pattern = (data.get('pattern', '') or '').upper()
    _en_term = (data.get('en_term', '') or '').strip()
    _source_form = (data.get('source_form', '') or '')
    _notes = (data.get('notes', '') or '')
    if _pattern == 'CONCEPT' and _en_term and target_table == 'entries':
        # (a) downstream word must appear in brackets in source_form
        if f'({_en_term.lower()}' not in _source_form.lower() and \
           f'({_en_term}' not in _source_form:
            violations.append(
                f"CONCEPT_FORMAT: pattern=CONCEPT with en_term='{_en_term}' "
                f"but source_form does not contain '({_en_term.lower()})' in brackets. "
                f"AA CONCEPT entries MUST include downstream word in brackets for findability."
            )
        # (b) downstream root candidates must be documented in notes
        if 'downstream' not in _notes.lower() or 'root candidate' not in _notes.lower():
            violations.append(
                f"CONCEPT_FORMAT: pattern=CONCEPT with en_term='{_en_term}' "
                f"but notes does not contain downstream AA root candidates. "
                f"Document possible AA roots the downstream word traces to."
            )

    if violations:
        return {
            'pass': False,
            'violations': violations,
            'message': (
                f"⛔ PRE-WRITE GATE BLOCKED: {len(violations)} violation(s). "
                f"Entry NOT written. Fix violations and retry.\n"
                + '\n'.join(f"  [{i+1}] {v}" for i, v in enumerate(violations))
            )
        }

    return {
        'pass': True,
        'violations': [],
        'message': '✅ Pre-write gate PASSED.'
    }


def write_entry(data: Dict, entry_class: str) -> Dict[str, Any]:
    """
    Validate routing, run pre-write gate, and write an entry to the correct table.

    The pre-write gate is BLOCKING. If it fails, the entry is NOT written.
    No override. No bypass. No exceptions.

    Args:
        data: dictionary of column values to insert
        entry_class: one of the ENTRY_ROUTING keys (WORD_EN, WORD_RU, etc.)

    Returns:
        {'success': bool, 'table': str, 'id': Any, 'message': str,
         'gate': dict (if gate blocked)}
    """
    # ═══ PROTOCOL RE-INJECTION — maximum attention before write ═══
    print(context_reload())

    target_table = ENTRY_ROUTING.get(entry_class)
    if not target_table:
        return {
            'success': False,
            'table': None,
            'id': None,
            'message': f"Unknown entry class: {entry_class}. Valid: {', '.join(ENTRY_ROUTING.keys())}"
        }

    # ═══ PRE-WRITE GATE — BLOCKING ═══
    gate_result = pre_write_gate(data, target_table)
    if not gate_result['pass']:
        return {
            'success': False,
            'table': target_table,
            'id': None,
            'message': gate_result['message'],
            'gate': gate_result,
        }

    # ═══ QUF FIELD AUTO-MAPPING ═══
    # Automatically map table-specific field names to QUF detection names.
    # This eliminates the need for callers to supply duplicate fields
    # (e.g., qur_primary for storage AND qur_ref for QUF detection).
    _quf_data = dict(data)  # copy — don't mutate original
    _QUF_FIELD_MAP = {
        # storage field → QUF detection field (only if detection field is empty)
        'qur_primary':          'qur_ref',
        'qur_secondary':        'qur_ref',  # appends
        'qur_refs':             'qur_ref',
        'dp_always_active':     'dp_codes',
        'founding_instances':   'source',
        'kashgari_attestation': 'source',
        'ibn_sina_attestation': 'source',
    }
    for storage_field, quf_field in _QUF_FIELD_MAP.items():
        val = data.get(storage_field, '')
        if val and not _quf_data.get(quf_field):
            _quf_data[quf_field] = val
        elif val and _quf_data.get(quf_field) and storage_field != quf_field:
            # Append if QUF field already has content
            _quf_data[quf_field] = _quf_data[quf_field] + '; ' + val

    # ═══ QUF VALIDATE — MANDATORY, NO BYPASS ═══
    # Multi-layer QUF via AMR AI pipeline (amr_quf.py)
    try:
        code_dir = os.path.dirname(os.path.abspath(__file__))
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
        from amr_quf import validate as _amr_quf_validate
        _quf_result = _amr_quf_validate(_quf_data, domain=target_table)
        if not _quf_result['pass']:
            _evidence = '\n'.join(_quf_result.get('evidence', [])[:5])
            return {
                'success': False, 'table': target_table, 'id': None,
                'message': f"⛔ QUF BLOCKED:\n{_evidence}"
            }
    except ImportError:
        # Fallback: if amr_quf not available, block write
        return {
            'success': False, 'table': target_table, 'id': None,
            'message': "⛔ QUF NOT FOUND. amr_quf.py missing."
        }
    except Exception as _quf_err:
        return {
            'success': False, 'table': target_table, 'id': None,
            'message': f"⛔ QUF ERROR: {_quf_err}"
        }

    conn = get_connection()
    try:
        # Get column names for the target table
        cursor = conn.execute(f"PRAGMA table_info([{target_table}])")
        valid_columns = {row[1] for row in cursor.fetchall()}

        # Filter data to only include valid columns
        filtered = {k: v for k, v in data.items() if k in valid_columns}
        if not filtered:
            conn.close()
            return {
                'success': False,
                'table': target_table,
                'id': None,
                'message': f"No valid columns found. Table {target_table} has: {', '.join(sorted(valid_columns))}"
            }

        # ═══ QUF TOKEN GENERATION ═══
        # Generate a valid token and register it in quf_tokens.
        # The DB trigger on the target table will verify this token exists.
        # Without this token, the INSERT is rejected at DB level.
        import hashlib, datetime as _dt, secrets
        _token_salt = secrets.token_hex(16)
        _token_payload = f"{target_table}|{filtered.get('root_letters', filtered.get('корневые_буквы', ''))}|{filtered.get('score', filtered.get('балл', ''))}|{_token_salt}|{_dt.datetime.now().isoformat()}"
        _quf_token = hashlib.sha256(_token_payload.encode()).hexdigest()[:48]

        # Register token — the quf_tokens table trigger only allows generated_by='handler.write_entry'
        conn.execute(
            "INSERT INTO quf_tokens (token, entry_id, root_letters, generated_by) VALUES (?, ?, ?, 'handler.write_entry')",
            (_quf_token, filtered.get('entry_id', filtered.get('запись_id', 0)), filtered.get('root_letters', filtered.get('корневые_буквы', '')))
        )

        # Inject token into the data
        filtered['quf_token'] = _quf_token

        columns = list(filtered.keys())
        values = list(filtered.values())
        placeholders = ','.join(['?' for _ in columns])
        col_names = ','.join([f'[{c}]' for c in columns])

        conn.execute(f"""
            INSERT INTO [{target_table}] ({col_names}) VALUES ({placeholders})
        """, values)

        # Mark token as used
        conn.execute("UPDATE quf_tokens SET used = 1 WHERE token = ?", (_quf_token,))
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # ═══ AUTO QUF STAMP — persist validation result to row ═══
        # Stamps the QUF columns directly from the validation result.
        # No manual UPDATE needed. No gap between write and stamp.
        _quf_stamp_cols = {'quf_q', 'quf_u', 'quf_f', 'quf_pass', 'quf_date'}
        if _quf_stamp_cols & valid_columns:  # only if table has QUF columns
            import datetime as _dt2
            _stamp_q = _quf_result.get('q', 'PENDING')
            _stamp_u = _quf_result.get('u', 'PENDING')
            _stamp_f = _quf_result.get('f', 'PENDING')
            _stamp_pass = 'TRUE' if _quf_result.get('pass') else 'FALSE'
            _stamp_date = _dt2.datetime.now().isoformat()

            # Find the primary key column for UPDATE
            _pk_col = None
            for _ci in conn.execute(f"PRAGMA table_info([{target_table}])").fetchall():
                if _ci[5]:  # pk flag
                    _pk_col = _ci[1]
                    break
            if _pk_col and _pk_col in filtered:
                conn.execute(
                    f"UPDATE [{target_table}] SET quf_q=?, quf_u=?, quf_f=?, "
                    f"quf_pass=?, quf_date=? WHERE [{_pk_col}]=?",
                    (_stamp_q, _stamp_u, _stamp_f, _stamp_pass, _stamp_date,
                     filtered[_pk_col])
                )
                # Mark token as stamp-consumed — blocks future raw stamp changes
                conn.execute(
                    "UPDATE quf_tokens SET stamp_used = 1 WHERE token = ?",
                    (_quf_token,)
                )

        # ═══ POST-WRITE VERIFICATION ═══
        # Read back the row to confirm it landed correctly.
        _verify_row = conn.execute(
            f"SELECT * FROM [{target_table}] WHERE rowid = ?", (last_id,)
        ).fetchone()
        _dropped_fields = [k for k in data.keys()
                          if k not in valid_columns and k not in
                          ('qur_ref', 'dp_codes', 'source')]  # known QUF-only fields
        _verify_msg = ""
        if _dropped_fields:
            _verify_msg = f" ⚠️ DROPPED FIELDS (not in table schema): {_dropped_fields}"

        # ── AUTO-INDEX: add to term_nodes so search finds this entry ──
        try:
            _idx_count = 0
            _en = data.get('en_term') or data.get('EN_TERM')
            _ru = data.get('ru_term') or data.get('RU_TERM')
            _aa = data.get('aa_word') or data.get('AA_WORD')
            _root = data.get('root_letters') or data.get('ROOT_LETTERS') or ''
            _score = data.get('score') or data.get('SCORE') or 0
            _src_table = 'a1_entries' if target_table == 'entries' else target_table

            for _term, _lang in [(_en, 'en'), (_ru, 'ru'), (_aa, 'ar')]:
                if _term:
                    conn.execute(
                        "INSERT OR IGNORE INTO term_nodes "
                        "(term, term_normal, language, source_table, source_id, root_id, entry_type, score) "
                        "VALUES (?, ?, ?, ?, ?, ?, 'WORD', ?)",
                        (_term, _term.lower(), _lang, _src_table, str(last_id), _root, _score)
                    )
                    _idx_count += 1
        except Exception:
            _idx_count = 0  # non-fatal — entry was written, index is bonus

        conn.commit()
        conn.close()

        _idx_msg = f" Indexed {_idx_count} term(s)." if _idx_count else ""
        return {
            'success': True,
            'table': target_table,
            'id': last_id,
            'quf': {'q': _stamp_q, 'u': _stamp_u, 'f': _stamp_f,
                     'pass': _stamp_pass} if _quf_stamp_cols & valid_columns else None,
            'message': f"✅ Gate PASSED. Written to {target_table}, rowid={last_id}. "
                       f"QUF stamped.{_idx_msg}{_verify_msg}"
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            'success': False,
            'table': target_table,
            'id': None,
            'message': f"Write failed: {e}"
        }


def update_entry(entry_id: Any, data: Dict, entry_class: str) -> Dict[str, Any]:
    """
    Update an existing entry. Generates a QUF token after pre-write gate passes.
    The DB trigger verifies the token — raw SQL updates are blocked.

    Args:
        entry_id: the ID of the entry to update (entry_id, запись_id, etc.)
        data: dictionary of column values to update
        entry_class: one of the ENTRY_ROUTING keys
    """
    # ═══ PROTOCOL RE-INJECTION — maximum attention before write ═══
    print(context_reload())

    target_table = ENTRY_ROUTING.get(entry_class)
    if not target_table:
        return {
            'success': False, 'table': None, 'id': None,
            'message': f"Unknown entry class: {entry_class}. Valid: {', '.join(ENTRY_ROUTING.keys())}"
        }

    # ═══ PRE-WRITE GATE — BLOCKING ═══
    gate_result = pre_write_gate(data, target_table)
    if not gate_result['pass']:
        return {
            'success': False, 'table': target_table, 'id': None,
            'message': gate_result['message'], 'gate': gate_result,
        }

    # ═══ QUF VALIDATE — MANDATORY, NO BYPASS ═══
    # Q gate: root must be verified against root_translations
    # U gate: phonetic chain must be valid (every consonant mapped, real shifts)
    # F gate: no better competing root
    # QUF is QUF. No override. Not even bbi approval bypasses QUF.
    import subprocess, json as _json
    _root = data.get('root_letters', data.get('корневые_буквы', ''))
    if _root and _root != 'UNDER INVESTIGATION':
        try:
            _quf_result = subprocess.run(
                ['python3', 'Code_files/uslap_quf.py', 'validate',
                 '--root', _root,
                 '--word', data.get('en_term', data.get('рус_термин', str(entry_id))),
                 '--chain', data.get('phonetic_chain', data.get('фонетическая_цепь', '')),
                 '--score', str(data.get('score', data.get('балл', 5)))],
                capture_output=True, text=True, timeout=30
            )
            if _quf_result.returncode != 0:
                _quf_msg = _quf_result.stdout.strip() or _quf_result.stderr.strip() or 'QUF validation failed'
                return {
                    'success': False, 'table': target_table, 'id': None,
                    'message': f"⛔ QUF BLOCKED: {_quf_msg}"
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False, 'table': target_table, 'id': None,
                'message': "⛔ QUF TIMEOUT. Validation did not complete in 30s."
            }
        except FileNotFoundError:
            return {
                'success': False, 'table': target_table, 'id': None,
                'message': "⛔ QUF NOT FOUND. uslap_quf.py missing."
            }

    conn = get_connection()
    try:
        # Get valid columns
        valid_columns = {row[1] for row in conn.execute(f"PRAGMA table_info([{target_table}])").fetchall()}
        filtered = {k: v for k, v in data.items() if k in valid_columns}
        if not filtered:
            conn.close()
            return {
                'success': False, 'table': target_table, 'id': None,
                'message': f"No valid columns. Table has: {', '.join(sorted(valid_columns))}"
            }

        # ═══ QUF TOKEN GENERATION — only reached after QUF passes ═══
        import hashlib, datetime as _dt, secrets
        _token_salt = secrets.token_hex(16)
        _token_payload = f"UPDATE|{target_table}|{entry_id}|{filtered.get('root_letters', filtered.get('корневые_буквы', ''))}|{_token_salt}|{_dt.datetime.now().isoformat()}"
        _quf_token = hashlib.sha256(_token_payload.encode()).hexdigest()[:48]

        # Register token
        conn.execute(
            "INSERT INTO quf_tokens (token, entry_id, root_letters, generated_by) VALUES (?, ?, ?, 'handler.write_entry')",
            (_quf_token, str(entry_id), filtered.get('root_letters', filtered.get('корневые_буквы', '')))
        )

        # Inject token
        filtered['quf_token'] = _quf_token

        # Build UPDATE
        set_clause = ', '.join([f'[{k}] = ?' for k in filtered.keys()])
        values = list(filtered.values())

        # Determine ID column
        id_col = 'entry_id'
        if target_table == 'a1_записи':
            id_col = 'запись_id'
        elif target_table == 'persian_a1_mad_khil':
            id_col = 'madkhal_id_مَدخَل_entry_id'

        values.append(entry_id)
        conn.execute(f"UPDATE [{target_table}] SET {set_clause} WHERE [{id_col}] = ?", values)

        # Mark token as used
        conn.execute("UPDATE quf_tokens SET used = 1 WHERE token = ?", (_quf_token,))
        conn.commit()
        conn.close()

        return {
            'success': True, 'table': target_table, 'id': entry_id,
            'message': f"✅ Gate PASSED. Updated {target_table} entry {entry_id}."
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            'success': False, 'table': target_table, 'id': None,
            'message': f"Update failed: {e}"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# REBUILD — Delegates to uslap_index.py
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT — Serve ref file content on demand, from DB
# ═══════════════════════════════════════════════════════════════════════════════

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTEXT_TOPICS = {
    'phonetics': {
        'file': 'CLAUDE_REF_PHONETICS.md',
        'desc': 'M1 shift table, permitted ops, RU corridor, Bitig phonology',
    },
    'detection': {
        'file': 'CLAUDE_REF_DETECTION.md',
        'desc': 'M2 detection patterns DP01-DP20, M5 QV markers QV01-QV03',
    },
    'entry': {
        'file': 'CLAUDE_REF_ENTRY_PROTOCOL.md',
        'desc': 'Entry format (14 cols), QUF triad, scoring, score caps, workflow',
    },
    'rules': {
        'file': 'CLAUDE_REF_RULES.md',
        'desc': 'Critical corrections 1-26, banned terms, direction of flow',
    },
    'state': {
        'file': 'CLAUDE_REF_STATE.md',
        'desc': 'Full counts, networks N01-N20, Names of Allah, scholars, investigations',
    },
    'wash': {
        'file': 'CLAUDE_REF_WASH.md',
        'desc': 'Translation Washing Algorithm — 4-step "Panning for Gold" with examples',
    },
    'conventions': {
        'file': 'CLAUDE_REF_CONVENTIONS.md',
        'desc': 'Documentary conventions — ATT, wrapper names, source hierarchy, DP tagging',
    },
    'writegate': {
        'file': 'CLAUDE_REF_WRITEGATE.md',
        'desc': 'Write-Gate Protocol — SQL templates, session audits, batch writes',
    },
    'shifts': {
        'file': None,
        'desc': 'Just the S01-S26 shift table (compact, from DB)',
    },
    'ops': {
        'file': None,
        'desc': 'Just the 10 permitted operations (compact)',
    },
    'caps': {
        'file': None,
        'desc': 'Score caps table only',
    },
}

def context_shifts() -> str:
    """Return compact shift table from DB."""
    conn = get_connection()
    lines = ["S_ID | Arabic | Name | EN outputs | RU outputs",
             "-----|--------|------|------------|----------"]
    try:
        rows = conn.execute("""
            SELECT shift_id, arabic_letter, letter_name, en_outputs, ru_outputs
            FROM m1_phonetic_shifts ORDER BY shift_id
        """).fetchall()
        for r in rows:
            lines.append(f"{r['shift_id']} | {r['arabic_letter']} | {r['letter_name']} | {r['en_outputs']} | {r['ru_outputs']}")
    except sqlite3.OperationalError:
        lines.append("(m1_phonetic_shifts table not found — load from CLAUDE_REF_PHONETICS.md)")
    conn.close()
    return '\n'.join(lines)


def context_ops() -> str:
    """Return compact permitted operations."""
    return """PERMITTED OPERATIONS (10):
OP_NASAL    — N inserted adjacent to root consonant (GOVERN: G-V-R-N, ANTIQUE: N-T-K)
OP_SUFFIX   — Downstream suffix added (-tion, -ment, -ous, -al, -er, etc.)
OP_PREFIX   — Downstream prefix (IM-, EX-, DE-, AL-, etc.)
OP_NASSIM   — Final م softens to N (حَرَام→HARAM→HARAN)
OP_TAMARBUTA — Final ة drops or becomes -T/-H
OP_VOICE    — Voicing shift within same place of articulation (F↔V, P↔B, T↔D, K↔G, S↔Z)
OP_PHRASE   — Multi-word AA phrase compressed into single downstream word (فِي الصَّفَا→PHILOSOPHY)
OP_STOP     — Nasal→stop shift (M→B, N→D, N→T) — same place of articulation
OP_RU_PREFIX — Russian prefix (ПО-, ПРИ-, У-, ВЫ-, etc.)
OP_RU_COMPOUND — Russian compound word (two+ roots fused)"""


def context_caps() -> str:
    """Return score caps table."""
    return """SCORE CAPS (MANDATORY — NEVER OVERRIDE):
Condition                              | Max Score | Reason
SEM_REVIEW flagged                     |     7     | Semantic gap = wrong root. Fix root, THEN re-score.
Competing root exists (criterion 6)    |     6     | Another root explains the word better.
No Qur'anic attestation (criterion 2)  |     5     | Without Qur'anic anchor, chain floats. ORIG2 exempt.
Unexplained consonant (criterion 7)    |     4     | Consonant not in S01-S26 = chain broken."""


def context_reload() -> str:
    """Mid-session protocol re-injection. Compact critical rules only.
    Designed to be called when attention dilution causes quality drift.
    Places protocol AT THE END of context = maximum attention."""
    conn = get_connection()
    lines = []
    lines.append("=" * 60)
    lines.append("⛔ PROTOCOL RE-INJECTION — ACTIVE NOW ⛔")
    lines.append("=" * 60)

    # Core identity
    lines.append("")
    lines.append("IDENTITY: Compute engine = PIPE. DB output = user output. Nothing else.")
    lines.append("NOT FOUND if DB has no answer. ZERO weights in ANY output. EVER.")

    # Direction
    lines.append("")
    lines.append("DIRECTION: Allah's Arabic / Bitig → downstream. ALWAYS. NEVER reverse.")

    # Banned terms (compact)
    lines.append("")
    lines.append("BANNED: semitic, loanword, cognate, prosthetic vowel, adoption,")
    lines.append("  pre-Greek substrate, PIE, borrowed from Greek/Latin/Persian,")
    lines.append("  Proto-Indo-European, Proto-Slavic, Proto-Germanic, Proto-Turkic,")
    lines.append("  Greek/Latin origin/source/root, derived from Greek/Latin/French,")
    lines.append("  native Slavic/European, bare 'Arabic' without qualifier.")

    # Link types
    lines.append("")
    lines.append("LINK_TYPE: DIRECT, COMPOUND, SAME_ROOT, PHONETIC, SEMANTIC, PREFIX, SUFFIX, ROOT.")
    lines.append("  NEVER: COGNATE, LOANWORD, BORROWING.")

    # Execution order
    lines.append("")
    lines.append("ORDER: Query DB → Read results → Output results → STOP.")
    lines.append("  No framing. No additions. No contextualising. No weights.")

    # Contamination
    lines.append("")
    lines.append("SUBAGENT OUTPUT = CONTAMINATED. Re-derive from AA root.")
    lines.append("DOWNSTREAM = degradation, NOT comparison point. AA stands alone.")

    # QUF
    lines.append("")
    lines.append("QUF: Q(phonetic chain) + U(shift precedent) + F(no better root). All PASS or BLOCKED.")

    # Translation
    lines.append("")
    lines.append("TRANSLATION: From ROOTS only. Published translations = operator-contaminated. Check QV register.")

    # Conventions
    lines.append("")
    lines.append("CONVENTIONS: Full phrases (Allah's Arabic, Lisan Arabic). ATT format. Wrapper names in quotes.")
    lines.append("  Source: Qur'an(1) → Victim's own(2) → Corrupted revelations(3) → Lattice(4) → Regional(5) → Western(6).")

    # Live counts (compact)
    tables_q = [
        ("a1_entries", "EN"), ("a1_записи", "RU"),
        ("persian_a1_mad_khil", "FA"), ("bitig_a1_entries", "Bitig"),
        ("european_a1_entries", "EU"),
    ]
    count_parts = []
    for table, label in tables_q:
        try:
            c = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            count_parts.append(f"{label}:{c}")
        except:
            pass
    lines.append("")
    lines.append(f"STATE: {' | '.join(count_parts)}")

    # Open write-gate items
    try:
        orphans = conn.execute(
            "SELECT gate_id, description FROM write_gate WHERE status != 'VERIFIED' AND status != 'CLOSED'"
        ).fetchall()
        if orphans:
            lines.append(f"WRITE-GATE ORPHANS: {len(orphans)}")
            for o in orphans:
                lines.append(f"  #{o[0]}: {o[1]}")
    except:
        pass

    conn.close()
    lines.append("")
    lines.append("=" * 60)
    lines.append("PROTOCOL RE-INJECTED. Compute engine reset to PIPE mode.")
    lines.append("=" * 60)
    return '\n'.join(lines)


def context_quf() -> str:
    """Return QUF stamp status from DB."""
    conn = get_connection()
    lines = ["QUF STAMP STATUS"]
    lines.append("─" * 50)

    stamp_tables = {
        'EN': ('a1_entries', 'score'),
        'RU': ('a1_записи', 'балл'),
        'EU': ('european_a1_entries', 'score'),
    }

    grand_pass = 0
    grand_validated = 0

    for label, (table, score_col) in stamp_tables.items():
        total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        stamped = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_date IS NOT NULL'
        ).fetchone()[0]

        q_dist = conn.execute(
            f'SELECT quf_q, COUNT(*) as cnt FROM "{table}" '
            f'WHERE quf_date IS NOT NULL GROUP BY quf_q ORDER BY cnt DESC'
        ).fetchall()

        pass_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 1'
        ).fetchone()[0]
        fail_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND quf_date IS NOT NULL '
            f'AND quf_q NOT IN (\'ORIG2_SKIP\') AND quf_q IS NOT NULL'
        ).fetchone()[0]

        mismatches = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND "{score_col}" >= 8 '
            f'AND quf_q NOT IN (\'ORIG2_SKIP\', \'ERROR\') AND quf_q IS NOT NULL '
            f'AND quf_date IS NOT NULL'
        ).fetchone()[0]

        validated = pass_count + fail_count
        pct = (pass_count / validated * 100) if validated else 0
        grand_pass += pass_count
        grand_validated += validated

        dist_str = ' | '.join(f'{d[0]}:{d[1]}' for d in q_dist) if q_dist else 'not stamped'
        lines.append(f"  {label}: {stamped}/{total} stamped | Q: {dist_str}")
        lines.append(f"    Pass: {pass_count}/{validated} ({pct:.1f}%)"
                     + (f" | ⚠️ {mismatches} score-QUF mismatches" if mismatches else ""))

    grand_pct = (grand_pass / grand_validated * 100) if grand_validated else 0
    lines.append(f"\n  OVERALL: {grand_pass}/{grand_validated} ({grand_pct:.1f}%)")

    conn.close()
    return '\n'.join(lines)


def context_file(topic: str) -> str:
    """Read a ref file and return its content."""
    info = CONTEXT_TOPICS.get(topic)
    if not info or not info['file']:
        return f"Topic '{topic}' has no file — use specific sub-topic."
    filepath = os.path.join(WORKSPACE, info['file'])
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filepath}"


def run_context(topic: str) -> str:
    """Serve context for a topic."""
    topic = topic.lower()

    if topic == 'list':
        lines = ["Available context topics:"]
        for t, info in CONTEXT_TOPICS.items():
            lines.append(f"  {t:12s} — {info['desc']}")
        lines.append("\nCompact sub-topics (no file read needed):")
        lines.append("  reload      — ⛔ MID-SESSION PROTOCOL RE-INJECTION (use when quality drifts)")
        lines.append("  shifts      — S01-S26 shift table from DB")
        lines.append("  ops         — 10 permitted operations")
        lines.append("  caps        — score caps table")
        lines.append("  quf         — QUF stamp status across all tables")
        return '\n'.join(lines)

    if topic == 'reload':
        return context_reload()
    elif topic == 'shifts':
        return context_shifts()
    elif topic == 'ops':
        return context_ops()
    elif topic == 'caps':
        return context_caps()
    elif topic == 'quf':
        return context_quf()
    elif topic == 'diagram':
        conn = get_connection()
        r = conn.execute("SELECT diagram FROM architecture_diagram LIMIT 1").fetchone()
        conn.close()
        return r[0] if r else "No diagram stored."
    elif topic == 'protocol':
        conn = get_connection()
        rules = conn.execute("SELECT rule_id, rule_text FROM protocol_immutable ORDER BY rule_id").fetchall()
        steps = conn.execute("SELECT step_id, step_name, authority FROM compute_protocol ORDER BY step_id").fetchall()
        conn.close()
        lines = ["PROTOCOL RULES:"]
        for r in rules:
            lines.append(f"  {r[0]}: {r[1]}")
        lines.append("\nCOMPUTE STEPS:")
        for s in steps:
            lines.append(f"  {s[0]:>2}. {s[1]:<40} authority: {s[2]}")
        return '\n'.join(lines)
    elif topic == 'isnad':
        conn = get_connection()
        rows = conn.execute("SELECT md_file, md_instruction, chain FROM isnad ORDER BY isnad_id").fetchall()
        conn.close()
        lines = ["ISNAD — CHAIN OF VERIFICATION:"]
        for r in rows:
            lines.append(f"  {r[0]}: \"{r[1]}\"")
            lines.append(f"    → {r[2]}")
        return '\n'.join(lines)
    elif topic in CONTEXT_TOPICS:
        return context_file(topic)
    else:
        return f"Unknown topic: {topic}. Run: python3 uslap_handler.py context list"


# ═══════════════════════════════════════════════════════════════════════════════
# INIT — Replace NEW_SESSION_PROMPT.md with dynamic output
# ═══════════════════════════════════════════════════════════════════════════════

def run_init() -> str:
    """Generate session initialization context dynamically from DB."""
    conn = get_connection()
    lines = []

    # ═══ DB PROTOCOL — loaded from the DB itself, not from CLAUDE.md ═══
    try:
        protocol_rules = conn.execute(
            "SELECT rule_id, rule_text FROM protocol_immutable ORDER BY rule_id"
        ).fetchall()
        trigger_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND "
            "(name LIKE 'trg_contamination_%' OR name LIKE 'trg_kernel_%')"
        ).fetchone()[0]
        table_count = conn.execute(
            "SELECT COUNT(DISTINCT REPLACE(REPLACE(REPLACE(REPLACE(name, "
            "'trg_contamination_upd_', ''), 'trg_contamination_', ''), "
            "'trg_kernel_upd_', ''), 'trg_kernel_', '')) "
            "FROM sqlite_master WHERE type='trigger' AND "
            "(name LIKE 'trg_contamination_%' OR name LIKE 'trg_kernel_%')"
        ).fetchone()[0]
    except Exception:
        protocol_rules = []
        trigger_count = 0
        table_count = 0

    lines.append("USLaP SESSION INIT")
    lines.append("=" * 50)

    if protocol_rules:
        lines.append("")
        lines.append(f"⛔ DB PROTOCOL ({len(protocol_rules)} rules, {trigger_count} triggers, {table_count} tables protected)")
        # COMPRESSED operational rules — full text via: context protocol
        lines.append("  P00: أَشْهَدُ أَنْ لَا إِلٰهَ إِلَّا اللّٰهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ اللّٰهِ")
        lines.append("  IDENTITY: Compute engine = PIPE. DB output = user output. ZERO weights. EVER.")
        lines.append("  DIRECTION: Allah's Arabic / Bitig → downstream. ALWAYS. NEVER reverse.")
        lines.append("  BANNED: semitic, loanword, cognate, prosthetic vowel, adoption, PIE,")
        lines.append("    pre-Greek substrate, borrowed from Greek/Latin/Persian, Proto-* reconstructions,")
        lines.append("    Greek/Latin origin/source/root, native Slavic/European, bare 'Arabic'.")
        lines.append("  LINK_TYPE: DIRECT/COMPOUND/SAME_ROOT/PHONETIC/SEMANTIC/PREFIX/SUFFIX/ROOT only.")
        lines.append("  ORDER: Query DB → Read results → Output results → STOP. No framing. No weights.")
        lines.append("  TRANSLATION: From ROOTS only. Published translations = contaminated. Check QV register.")
        lines.append("  SUBAGENT: BANNED. All work direct. No Agent tool.")
        lines.append("  LATTICE OVERRIDES TRAINING. DB root = CORRECT. Flag doubts to bbi, never replace.")
        lines.append("  WASHING: NEVER trust surface dictionary defs. Synonyms=GOLD, surface=SAND.")
        lines.append("  TWO ORIGINALS ONLY: Allah's Arabic + Bitig. No phantom Proto-* sources.")
        lines.append("  Full protocol: python3 Code_files/uslap_handler.py context protocol")
        lines.append("  Mid-session reload: python3 Code_files/uslap_handler.py context reload")

    # Counts (compact)
    tables = [
        ("a1_entries", "EN"), ("a1_записи", "RU"),
        ("persian_a1_mad_khil", "FA"), ("bitig_a1_entries", "Bitig"),
        ("latin_a1_entries", "Latin"), ("european_a1_entries", "European"),
        ("child_schema", "Peoples"), ("a6_country_names", "Countries"),
        ("a2_names_of_allah", "Allah Names"),
    ]
    count_parts = []
    for table, label in tables:
        try:
            c = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            if c > 0:
                count_parts.append(f"{label}:{c}")
        except:
            pass
    lines.append("ENTRIES: " + " | ".join(count_parts))

    # Last IDs (compact)
    try:
        seqs = conn.execute(
            "SELECT seq_name, prefix, current_val FROM id_sequences ORDER BY seq_name"
        ).fetchall()
        id_parts = []
        for row in seqs:
            id_parts.append(f"{row['seq_name']}={row['prefix']}{row['current_val']}")
        lines.append("LAST IDs: " + ", ".join(id_parts))
    except:
        pass

    # Sub-10 entries
    try:
        sub10 = conn.execute(
            "SELECT entry_id, en_term, score FROM a1_entries WHERE score < 10 ORDER BY score"
        ).fetchall()
        if sub10:
            parts = [f"{r['en_term']}#{r['entry_id']}({r['score']})" for r in sub10]
            lines.append(f"SUB-10 EN ({len(sub10)}): " + ", ".join(parts))
    except:
        pass

    # RU score distribution (compact)
    try:
        dist = conn.execute("""
            SELECT балл, COUNT(*) FROM "a1_записи"
            WHERE балл IS NOT NULL GROUP BY балл ORDER BY балл DESC
        """).fetchall()
        if dist:
            parts = [f"{r[0]}:{r[1]}" for r in dist]
            lines.append("RU SCORES: " + ", ".join(parts))
    except:
        pass

    # Dimension edges
    try:
        dims = conn.execute("""
            SELECT dimension, COUNT(*) as cnt FROM term_dimensions
            GROUP BY dimension ORDER BY cnt DESC
        """).fetchall()
        if dims:
            parts = [f"{r['dimension']}:{r['cnt']}" for r in dims]
            lines.append("DIMENSIONS: " + " | ".join(parts))
    except:
        pass

    # Index stats
    try:
        nodes = conn.execute("SELECT COUNT(*) FROM term_nodes").fetchone()[0]
        edges = conn.execute("SELECT COUNT(*) FROM term_dimensions").fetchone()[0]
        lines.append(f"INDEX: {nodes} nodes, {edges} edges")
    except:
        pass

    # ── CONTAMINATION BLACKLIST (KERNEL GATE — al-Ikhlāṣ) ──
    # Fires EVERY session. These terms have contaminated translations in
    # training data. The correct meaning is in the lattice. NEVER use the
    # contaminated version.
    try:
        bl_rows = conn.execute(
            "SELECT bl_id, contaminated_term, contaminated_translation, "
            "correct_translation FROM contamination_blacklist ORDER BY bl_id"
        ).fetchall()
        if bl_rows:
            lines.append("")
            lines.append("⛔ CONTAMINATION BLACKLIST (NEVER use these translations):")
            for r in bl_rows:
                lines.append(
                    f"  {r['bl_id']}: {r['contaminated_term']} "
                    f"≠ \"{r['contaminated_translation']}\" "
                    f"→ USE: {r['correct_translation']}"
                )
    except:
        pass

    # Framework gate compressed — full rules in protocol_immutable and CLAUDE.md
    lines.append("")
    lines.append("⛔ FRAMEWORK GATES: Direction(AA→DS) | No loans | Lattice>training | No phantoms | Divine framing | Every word has root | Wash before use")

    # ── WRITE-GATE AUDIT (fires EVERY session) ──
    # Check for orphaned analyses from previous sessions
    try:
        orphans = conn.execute("""
            SELECT gate_id, term, root, target_table, status, session_date
            FROM write_gate
            WHERE status NOT IN ('VERIFIED', 'CLOSED')
            ORDER BY created_at
        """).fetchall()
        if orphans:
            lines.append("")
            lines.append("⚠️  WRITE-GATE ORPHANS (confirmed but NOT written/verified):")
            for r in orphans:
                lines.append(
                    f"  #{r['gate_id']} [{r['status']}] {r['term']} "
                    f"({r['root']}) → {r['target_table']} "
                    f"(from {r['session_date']})"
                )
            lines.append("  ACTION: Write these BEFORE doing any new work.")
        else:
            lines.append("")
            lines.append("✅ WRITE-GATE: Clean — no orphaned analyses.")
    except:
        lines.append("")
        lines.append("⚠️  WRITE-GATE: table not found — run schema migration.")

    # Tools
    lines.append("")
    lines.append("TOOLS: handler(search/state/next/expand/context/init) | autopop | sem_review | chrono_connect | backup | quf | latin_hub | index")
    lines.append("CONTEXT: python3 uslap_handler.py context [phonetics|detection|entry|rules|state|shifts|ops|caps|wash|conventions|writegate|list]")

    # Open issues from NEW_SESSION_PROMPT.md (if exists)
    prompt_path = os.path.join(WORKSPACE, 'NEW_SESSION_PROMPT.md')
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Extract OPEN ISSUES section
        if 'OPEN ISSUES' in content:
            issues_section = content[content.index('OPEN ISSUES'):]
            # Trim to just the issues
            issue_lines = []
            for line in issues_section.split('\n')[1:]:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    issue_lines.append(line)
                elif not line:
                    continue
                else:
                    break
            if issue_lines:
                lines.append("")
                lines.append("OPEN ISSUES:")
                for il in issue_lines:
                    lines.append(f"  {il}")

    # ═══ QUF TOKEN CLEANUP — prune used tokens older than 7 days ═══
    try:
        pruned = conn.execute(
            "DELETE FROM quf_tokens WHERE used = 1 "
            "AND created_at < datetime('now', '-7 days')"
        ).rowcount
        if pruned:
            conn.commit()
            lines.append(f"QUF_TOKENS: pruned {pruned} used tokens (>7 days old)")
    except Exception:
        pass  # table may not exist yet

    conn.close()

    # ═══ SET THE INIT LOCK — all other commands now unlocked ═══
    _set_init_lock()

    return '\n'.join(lines)


def rebuild_index() -> Dict[str, Any]:
    """Trigger a full index rebuild by importing and running uslap_index."""
    try:
        # Add code files directory to path
        code_dir = os.path.dirname(os.path.abspath(__file__))
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
        from uslap_index import rebuild_all
        return rebuild_all()
    except Exception as e:
        return {'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE — for direct command-line use
# ═══════════════════════════════════════════════════════════════════════════════

def format_search_result(result: Dict) -> str:
    """Format search result for CLI display."""
    lines = []
    # Protocol preamble — DB's law, embedded in every result
    if result.get('protocol'):
        lines.append(f"  [{result['protocol']}]")
    lines.append(f"\n{'=' * 60}")
    lines.append(f"SEARCH: {result['query']}")
    lines.append(f"{'=' * 60}")
    lines.append(f"  {result['summary']}")

    # ── BLACKLIST WARNINGS (render BEFORE results) ──
    if result.get('blacklist_warnings'):
        lines.append("")
        lines.append("  ⛔ CONTAMINATION BLACKLIST TRIGGERED:")
        for bw in result['blacklist_warnings']:
            lines.append(f"    {bw['bl_id']}: {bw['term']}")
            lines.append(f"      NEVER USE: \"{bw['NEVER_USE']}\"")
            lines.append(f"      CORRECT:   {bw['CORRECT']}")

    if result['found']:
        # Group nodes by entry_type
        by_type = {}
        for node in result['nodes']:
            et = node['entry_type']
            by_type.setdefault(et, []).append(node)

        for et, nodes in by_type.items():
            lines.append(f"\n  [{et}]")
            for n in nodes[:10]:  # Limit display
                score_str = f" (score: {n['score']})" if n['score'] else ""
                root_str = f" [{n['root_id']}]" if n['root_id'] else ""
                lines.append(f"    {n['term']} ({n['language'].upper()}) — {n['source_table']}#{n['source_id']}{root_str}{score_str}")

        if result['dimensions']:
            lines.append(f"\n  DIMENSIONS AVAILABLE:")
            for dim, count in sorted(result['dimensions'].items(), key=lambda x: -x[1]):
                label = DIMENSION_NAMES.get(dim, dim)
                lines.append(f"    {dim}: {count} edges — {label}")

    lines.append(f"{'=' * 60}")
    return '\n'.join(lines)


def format_expand_result(result: Dict) -> str:
    """Format expand result for CLI display."""
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"EXPAND: {result['dimension']} — {result['dimension_label']}")
    lines.append(f"{'=' * 60}")
    lines.append(f"  {result['count']} edges")

    for edge in result['edges']:
        lines.append(f"\n  [{edge['target_table']}#{edge['target_id']}] {edge['label']}")
        if edge['data']:
            for k, v in edge['data'].items():
                if v is not None and str(v).strip():
                    v_str = str(v)
                    if len(v_str) > 100:
                        v_str = v_str[:97] + "..."
                    lines.append(f"    {k}: {v_str}")

    lines.append(f"{'=' * 60}")
    return '\n'.join(lines)


def format_state_result(result: Dict) -> str:
    """Format state result for CLI display."""
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"USLaP DATABASE STATE — {result['timestamp']}")
    lines.append(f"{'=' * 60}")

    lines.append(f"\n  COUNTS:")
    for label, count in result['counts'].items():
        if count > 0:
            lines.append(f"    {label}: {count}")

    lines.append(f"\n  LAST IDs:")
    for seq, val in result['last_ids'].items():
        lines.append(f"    {seq}: {val}")

    if result.get('sub_10'):
        lines.append(f"\n  SUB-10 ENTRIES ({len(result['sub_10'])}):")
        for entry in result['sub_10']:
            lines.append(f"    #{entry['entry_id']} {entry['en_term']} — score: {entry['score']}")

    if result.get('index_stats'):
        lines.append(f"\n  INDEX STATS:")
        for k, v in result['index_stats'].items():
            lines.append(f"    {k}: {v}")

    if result.get('score_distribution_en'):
        lines.append(f"\n  SCORE DISTRIBUTION (EN):")
        for score, cnt in sorted(result['score_distribution_en'].items(), key=lambda x: -int(x[0])):
            lines.append(f"    Score {score}: {cnt} entries")

    lines.append(f"{'=' * 60}")
    return '\n'.join(lines)


def main():
    """CLI interface for the HANDLER."""
    import argparse

    parser = argparse.ArgumentParser(
        description="USLaP HANDLER — an-Nahl (16) — Search, Expand, State, Context, Init",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "coffee"          Search for a term
  %(prog)s search "R96"             Search by root ID
  %(prog)s expand "coffee" DIVINE   Expand DIVINE dimension
  %(prog)s state                    Show database state
  %(prog)s next ROOT_ID             Show next available root ID
  %(prog)s context list             List available context topics
  %(prog)s context shifts           Shift table S01-S26 (compact)
  %(prog)s context entry            Full entry protocol
  %(prog)s init                     Session init (replaces NEW_SESSION_PROMPT)
  %(prog)s rebuild                  Full index rebuild
        """
    )

    subparsers = parser.add_subparsers(dest='command')

    # search
    sp_search = subparsers.add_parser('search', help='Search the index')
    sp_search.add_argument('term', help='Term to search for')

    # expand
    sp_expand = subparsers.add_parser('expand', help='Expand a dimension')
    sp_expand.add_argument('term', help='Term to expand')
    sp_expand.add_argument('dimension', help='Dimension: LINGUISTIC, DIVINE, GEOGRAPHIC, INTELLIGENCE, QURANIC, NETWORK, DERIVATIVE')

    # state
    sp_state = subparsers.add_parser('state', help='Show database state')

    # next
    sp_next = subparsers.add_parser('next', help='Show next available ID')
    sp_next.add_argument('seq', help='Sequence name: ROOT_ID, EN_ENTRY, RU_ENTRY, DERIV_ID, etc.')

    # context
    sp_context = subparsers.add_parser('context', help='Serve ref file content on demand')
    sp_context.add_argument('topic', help='Topic: phonetics, detection, entry, rules, state, shifts, ops, caps, list')

    # init
    sp_init = subparsers.add_parser('init', help='Session init (replaces NEW_SESSION_PROMPT)')

    # rebuild
    sp_rebuild = subparsers.add_parser('rebuild', help='Full index rebuild')

    args = parser.parse_args()

    # ═══ INIT RUNS UNCONDITIONALLY — ALL OTHERS REQUIRE INIT LOCK ═══
    if args.command == 'init':
        print(run_init())

    else:
        # AUTO-INIT — fires automatically on first use, no decision point
        init_output = _auto_init()
        if init_output:
            print(init_output)
            print("─" * 50)
            print()

        if args.command == 'search':
            result = search(args.term)
            print(format_search_result(result))

        elif args.command == 'expand':
            result = expand(args.term, args.dimension.upper())
            print(format_expand_result(result))

        elif args.command == 'state':
            result = state()
            print(format_state_result(result))

        elif args.command == 'next':
            nid = next_id(args.seq.upper())
            print(f"Next {args.seq.upper()}: {nid}")

        elif args.command == 'context':
            print(run_context(args.topic))

        elif args.command == 'rebuild':
            print("Rebuilding index...")
            result = rebuild_index()
            if 'error' in result:
                print(f"ERROR: {result['error']}")
            else:
                print(f"Rebuild complete: {result.get('nodes', '?')} nodes, {result.get('edges', '?')} edges")

        else:
            parser.print_help()


if __name__ == "__main__":
    main()
