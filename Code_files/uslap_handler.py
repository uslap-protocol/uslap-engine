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
    "WORD_EN":       "a1_entries",
    "WORD_RU":       "a1_записи",
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
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = str
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH — وَأَوْحَىٰ رَبُّكَ إِلَى النَّحْلِ (receives the query)
# ═══════════════════════════════════════════════════════════════════════════════

def search(term: str) -> Dict[str, Any]:
    """
    CLAUDE.md Step 1 compliance. Search the index for a term.

    Returns:
    {
        'found': bool,
        'query': str,
        'nodes': [{node_id, term, language, source_table, source_id, root_id, score, entry_type}],
        'dimensions': {'LINGUISTIC': N, 'DIVINE': N, ...},
        'summary': str  (human-readable one-liner)
    }
    """
    conn = get_connection()
    result = {
        'found': False,
        'query': term,
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
            dim_counts = conn.execute(f"""
                SELECT dimension, COUNT(*) as cnt
                FROM term_dimensions
                WHERE node_id IN ({placeholders})
                GROUP BY dimension
                ORDER BY cnt DESC
            """, list(node_ids)).fetchall()

            for dim_row in dim_counts:
                result['dimensions'][dim_row['dimension']] = dim_row['cnt']

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

def write_entry(data: Dict, entry_class: str) -> Dict[str, Any]:
    """
    Validate routing and write an entry to the correct table.

    Args:
        data: dictionary of column values to insert
        entry_class: one of the ENTRY_ROUTING keys (WORD_EN, WORD_RU, etc.)

    Returns:
        {'success': bool, 'table': str, 'id': Any, 'message': str}
    """
    target_table = ENTRY_ROUTING.get(entry_class)
    if not target_table:
        return {
            'success': False,
            'table': None,
            'id': None,
            'message': f"Unknown entry class: {entry_class}. Valid: {', '.join(ENTRY_ROUTING.keys())}"
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

        columns = list(filtered.keys())
        values = list(filtered.values())
        placeholders = ','.join(['?' for _ in columns])
        col_names = ','.join([f'[{c}]' for c in columns])

        conn.execute(f"""
            INSERT INTO [{target_table}] ({col_names}) VALUES ({placeholders})
        """, values)
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        return {
            'success': True,
            'table': target_table,
            'id': last_id,
            'message': f"Written to {target_table}, rowid={last_id}. Index NOT updated — run rebuild when ready."
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
        lines.append("  shifts      — S01-S26 shift table from DB")
        lines.append("  ops         — 10 permitted operations")
        lines.append("  caps        — score caps table")
        return '\n'.join(lines)

    if topic == 'shifts':
        return context_shifts()
    elif topic == 'ops':
        return context_ops()
    elif topic == 'caps':
        return context_caps()
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

    lines.append("USLaP SESSION INIT")
    lines.append("=" * 50)

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

    # Tools
    lines.append("")
    lines.append("TOOLS: handler(search/state/next/expand/context/init) | autopop | sem_review | chrono_connect | backup | quf | latin_hub | index")
    lines.append("CONTEXT: python3 uslap_handler.py context [phonetics|detection|entry|rules|state|shifts|ops|caps|list]")

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

    conn.close()
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

    elif args.command == 'init':
        print(run_init())

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
