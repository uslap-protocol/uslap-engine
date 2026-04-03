#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP ḤASHR — al-Ḥashr (59)
هُوَ ٱلَّذِىٓ أَخْرَجَ ٱلَّذِينَ كَفَرُوا۟ مِنْ أَهْلِ ٱلْكِتَٰبِ مِن دِيَٰرِهِمْ
"He it is Who expelled those who disbelieved from among the People of the Book
 from their homes" (Q59:2)

ḤASHR = The Gathering. Gathers ALL intelligence threads across the lattice
into a unified INTELLIGENCE dimension in the index.

Sources:
  1. EN a1_entries — inversion_type (HIDDEN/WEAPONISED/CONFESSIONAL) — 369 entries
  2. RU a1_записи — тип_инверсии — 538 entries
  3. Bitig degradation register — 38 BD entries with DP codes
  4. Bitig intelligence summary — 16 INT entries
  5. Chronology — 96 events with DP implications
  6. M4 networks (concealment) — 39 entries
  7. DP register — 5 formal rulings
  8. Contamination blacklist — 12 BL entries
  9. Intel file index — 7 intelligence files

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
import re
from collections import Counter

DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"


def get_conn():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: find node_id for an entry in term_nodes
# ═══════════════════════════════════════════════════════════════════════════════

def find_node(conn, source_table, source_id, entry_type='WORD'):
    """Find node_id(s) for a given source entry."""
    rows = conn.execute("""
        SELECT node_id FROM term_nodes
        WHERE source_table = ? AND source_id = ? AND entry_type = ?
    """, (source_table, str(source_id), entry_type)).fetchall()
    return [r['node_id'] for r in rows]


def insert_edge(conn, node_id, target_table, target_id, label):
    """Insert an INTELLIGENCE dimension edge (ignores duplicates)."""
    try:
        conn.execute("""
            INSERT OR IGNORE INTO term_dimensions
            (node_id, dimension, target_table, target_id, label)
            VALUES (?, 'INTELLIGENCE', ?, ?, ?)
        """, (node_id, target_table, str(target_id), label))
        return 1
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 1: INVERSION TYPE — EN + RU entries
# ═══════════════════════════════════════════════════════════════════════════════

def wire_inversion_types(conn):
    """Wire all entries that have inversion_type into INTELLIGENCE dimension.

    Edge: entry_node → inversion_type classification
    Label format: "INVERSION:{type}" (e.g., "INVERSION:HIDDEN", "INVERSION:WEAPONISED")
    """
    total = 0

    # EN entries
    rows = conn.execute("""
        SELECT entry_id, en_term, inversion_type
        FROM a1_entries
        WHERE inversion_type IS NOT NULL AND inversion_type != ''
    """).fetchall()

    for r in rows:
        inv_type = r['inversion_type'].strip()
        nodes = find_node(conn, 'a1_entries', r['entry_id'])
        for nid in nodes:
            total += insert_edge(conn, nid, 'inversion_class', inv_type,
                                 f"INVERSION:{inv_type}")

    en_count = total
    print(f"  EN inversion types: {en_count} edges from {len(rows)} entries")

    # RU entries
    rows = conn.execute("""
        SELECT запись_id, рус_термин, тип_инверсии
        FROM a1_записи
        WHERE тип_инверсии IS NOT NULL AND тип_инверсии != ''
    """).fetchall()

    ru_start = total
    for r in rows:
        inv_type = r['тип_инверсии'].strip()
        nodes = find_node(conn, 'a1_записи', r['запись_id'])
        for nid in nodes:
            total += insert_edge(conn, nid, 'inversion_class', inv_type,
                                 f"INVERSION:{inv_type}")

    ru_count = total - ru_start
    print(f"  RU inversion types: {ru_count} edges from {len(rows)} entries")

    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 2: BITIG DEGRADATION REGISTER
# ═══════════════════════════════════════════════════════════════════════════════

def wire_bitig_degradation(conn):
    """Wire Bitig degradation register into INTELLIGENCE dimension.

    For each BD entry:
      - Find Bitig source node → edge to degradation record
      - Find RU downstream node → edge to degradation record
      - Both get DP code labels
    """
    total = 0

    rows = conn.execute("""
        SELECT deg_id, bitig_original, downstream_form, dp_codes,
               degradation_type, lattice_source
        FROM bitig_degradation_register
    """).fetchall()

    for r in rows:
        deg_id = r['deg_id']
        dp_codes = r['dp_codes'] or ''
        deg_type = r['degradation_type'] or ''
        label = f"DEGRADATION:{deg_id} {deg_type} [{dp_codes}]"

        # Try to find Bitig source node via lattice_source
        lattice_src = r['lattice_source'] or ''
        bitig_refs = re.findall(r'bitig_a1\s*#(\d+)', lattice_src)
        for ref_id in bitig_refs:
            nodes = find_node(conn, 'bitig_a1_entries', ref_id)
            for nid in nodes:
                total += insert_edge(conn, nid, 'bitig_degradation_register',
                                     deg_id, label)

        # Try to find EN/RU downstream nodes via lattice_source
        en_refs = re.findall(r'a1_entries\s*#(\d+)', lattice_src)
        for ref_id in en_refs:
            nodes = find_node(conn, 'a1_entries', ref_id)
            for nid in nodes:
                total += insert_edge(conn, nid, 'bitig_degradation_register',
                                     deg_id, label)

        ru_refs = re.findall(r'a1_записи\s*#(\d+)', lattice_src)
        for ref_id in ru_refs:
            nodes = find_node(conn, 'a1_записи', ref_id)
            for nid in nodes:
                total += insert_edge(conn, nid, 'bitig_degradation_register',
                                     deg_id, label)

    print(f"  Bitig degradation: {total} edges from {len(rows)} BD entries")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 3: CHRONOLOGY → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_chronology_intelligence(conn):
    """Wire chronology events that have intelligence implications.

    Chronology events with naming_op, oper_name, or oper_meaning
    contain intelligence about naming operations. Connect them.
    """
    total = 0

    rows = conn.execute("""
        SELECT id, date, event, orig_name, oper_name, naming_op, era
        FROM chronology
    """).fetchall()

    for r in rows:
        chrono_id = r['id']
        naming_op = r['naming_op'] or ''
        oper_name = r['oper_name'] or ''
        era = r['era'] or ''
        event_short = (r['event'] or '')[:60]

        # Only wire events that have intelligence content
        has_intel = (naming_op and naming_op != '—' and naming_op != '-') or \
                    (oper_name and oper_name != r['orig_name'])

        if not has_intel:
            continue

        label = f"CHRONO:{chrono_id} {r['date']} {naming_op}" if naming_op and naming_op != '—' \
                else f"CHRONO:{chrono_id} {r['date']}"

        # Find nodes connected to this chronology event already
        # (via existing CHRONOLOGICAL edges)
        linked_nodes = conn.execute("""
            SELECT node_id FROM term_dimensions
            WHERE dimension = 'CHRONOLOGICAL'
              AND target_table = 'chronology'
              AND target_id = ?
        """, (chrono_id,)).fetchall()

        for ln in linked_nodes:
            total += insert_edge(conn, ln['node_id'], 'chronology',
                                 chrono_id, label)

        # Also try to find nodes via orig_name / oper_name
        orig_name = r['orig_name'] or ''
        if orig_name:
            # Search for nodes matching the original name
            matched = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE (term_normal LIKE ? OR term LIKE ?)
                  AND entry_type = 'WORD'
                LIMIT 5
            """, (f"%{orig_name.lower()[:20]}%",
                  f"%{orig_name[:20]}%")).fetchall()
            for m in matched:
                total += insert_edge(conn, m['node_id'], 'chronology',
                                     chrono_id, label)

    print(f"  Chronology intelligence: {total} edges from {len(rows)} events")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 4: M4 NETWORKS → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_network_intelligence(conn):
    """Wire concealment networks into INTELLIGENCE dimension.

    M4 networks describe concealment operations. Each network entry
    that has entry_ids links those entries to intelligence.
    """
    total = 0

    try:
        rows = conn.execute("""
            SELECT network_id, title, entry_ids, mechanism
            FROM m4_networks
        """).fetchall()
    except sqlite3.OperationalError:
        print("  m4_networks: table not found, skipping.")
        return 0

    for r in rows:
        nid = r['network_id']
        title = (r['title'] or str(nid))[:50]
        mechanism = (r['mechanism'] or '')[:40]
        label = f"NETWORK:{nid} {title}"

        entry_ids_str = r['entry_ids'] or ''
        if not entry_ids_str:
            continue

        # Parse entry_ids (comma-separated, may contain #)
        for eid in re.findall(r'(\d+)', entry_ids_str):
            # Try EN
            nodes = find_node(conn, 'a1_entries', eid)
            for node_id in nodes:
                total += insert_edge(conn, node_id, 'm4_networks', nid, label)
            # Try RU
            nodes = find_node(conn, 'a1_записи', eid)
            for node_id in nodes:
                total += insert_edge(conn, node_id, 'm4_networks', nid, label)

    print(f"  Network intelligence: {total} edges from {len(rows)} networks")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 5: CONTAMINATION BLACKLIST → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_blacklist(conn):
    """Wire contamination blacklist into INTELLIGENCE dimension.

    Each BL entry warns about contaminated translations.
    Split compound terms on "/" and search each part separately.
    Also connect via Bitig degradation register cross-references.
    """
    total = 0

    rows = conn.execute("""
        SELECT bl_id, contaminated_term, contaminated_translation, correct_translation
        FROM contamination_blacklist
    """).fetchall()

    for r in rows:
        bl_id = r['bl_id']
        compound_term = r['contaminated_term'] or ''
        label = f"BLACKLIST:{bl_id} {compound_term[:30]}"

        # Split compound terms: "qağan / قاغان" → ["qağan", "قاغان"]
        parts = [p.strip() for p in compound_term.split('/') if p.strip()]

        # Also try extracting just the first word for broader matching
        for part in parts:
            search_term = part.lower().strip()
            if not search_term or len(search_term) < 2:
                continue
            matched = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE term_normal LIKE ?
                   OR term LIKE ?
                LIMIT 15
            """, (f"%{search_term}%", f"%{part}%")).fetchall()

            for m in matched:
                total += insert_edge(conn, m['node_id'],
                                     'contamination_blacklist', bl_id, label)

        # Also connect via the degradation register (BL entries map to BD entries)
        # e.g., BL01 qağan = BD02, BL03 ordu = BD01, BL08 balıq = BD03
        bl_to_bd = {
            'BL01': 'BD02', 'BL02': 'BD15', 'BL03': 'BD01',
            'BL08': 'BD03', 'BL09': 'BD05', 'BL10': 'BD04',
            'BL11': 'BD07', 'BL12': 'BD22'
        }
        if bl_id in bl_to_bd:
            bd_id = bl_to_bd[bl_id]
            # Find nodes already linked to this BD entry
            bd_nodes = conn.execute("""
                SELECT node_id FROM term_dimensions
                WHERE dimension = 'INTELLIGENCE'
                  AND target_table = 'bitig_degradation_register'
                  AND target_id = ?
            """, (bd_id,)).fetchall()
            for bn in bd_nodes:
                total += insert_edge(conn, bn['node_id'],
                                     'contamination_blacklist', bl_id, label)

    print(f"  Blacklist intelligence: {total} edges from {len(rows)} BL entries")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 6: DP REGISTER → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_dp_register(conn):
    """Wire DP register formal rulings into INTELLIGENCE dimension.

    DP register entries describe detection patterns.
    Connect to entries that reference these DPs in their fields,
    plus connect to Bitig degradation entries that use these DP codes.
    """
    total = 0

    try:
        dp_rows = conn.execute(
            "SELECT dp_code, name FROM dp_register"
        ).fetchall()
    except sqlite3.OperationalError:
        print("  dp_register: table not found, skipping.")
        return 0

    for r in dp_rows:
        dp_id = r['dp_code']
        dp_name = str(r['name'] or dp_id)[:40]
        label = f"DP_RULING:{dp_id} {dp_name}"

        # Strategy 1: Search text columns in entry tables for DP code reference
        search_configs = [
            ('a1_entries', 'entry_id',
             ['phonetic_chain', 'source_form', 'foundation_ref', 'qur_meaning', 'pattern']),
            ('a1_записи', 'запись_id',
             ['фонетическая_цепь', 'исходная_форма', 'основание', 'коранич_значение', 'паттерн']),
        ]
        for table, id_col, text_cols in search_configs:
            for col in text_cols:
                try:
                    matches = conn.execute(f"""
                        SELECT [{id_col}] FROM [{table}]
                        WHERE [{col}] LIKE ?
                        LIMIT 30
                    """, (f"%{dp_id}%",)).fetchall()
                    for m in matches:
                        nodes = find_node(conn, table, m[0])
                        for nid in nodes:
                            total += insert_edge(conn, nid, 'dp_register',
                                                 dp_id, label)
                except (sqlite3.OperationalError, TypeError):
                    continue

        # Strategy 2: Connect via Bitig degradation register dp_codes
        bd_matches = conn.execute("""
            SELECT deg_id FROM bitig_degradation_register
            WHERE dp_codes LIKE ?
        """, (f"%{dp_id}%",)).fetchall()
        for bd in bd_matches:
            # Find nodes linked to this BD entry
            bd_nodes = conn.execute("""
                SELECT node_id FROM term_dimensions
                WHERE dimension = 'INTELLIGENCE'
                  AND target_table = 'bitig_degradation_register'
                  AND target_id = ?
            """, (bd['deg_id'],)).fetchall()
            for bn in bd_nodes:
                total += insert_edge(conn, bn['node_id'], 'dp_register',
                                     dp_id, label)

        # Strategy 3: Connect via child_schema dp_codes
        try:
            cs_matches = conn.execute("""
                SELECT entry_id FROM child_schema
                WHERE dp_codes LIKE ?
            """, (f"%{dp_id}%",)).fetchall()
            for cs in cs_matches:
                cs_nodes = conn.execute("""
                    SELECT node_id FROM term_nodes
                    WHERE source_table = 'child_schema' AND source_id = ?
                """, (str(cs['entry_id']),)).fetchall()
                for cn in cs_nodes:
                    total += insert_edge(conn, cn['node_id'], 'dp_register',
                                         dp_id, label)
        except sqlite3.OperationalError:
            pass

    print(f"  DP register: {total} edges from {len(dp_rows)} rulings")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 7: BITIG INTELLIGENCE SUMMARIES → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_bitig_intel_summaries(conn):
    """Wire Bitig intelligence summaries into INTELLIGENCE dimension.

    Each INT entry references BD case_ids. Connect the BD-linked nodes
    to the intelligence assessment.
    """
    total = 0

    rows = conn.execute("""
        SELECT intel_id, category, dp_code, case_ids, intelligence_assessment
        FROM bitig_intelligence_summary
        WHERE case_ids IS NOT NULL AND case_ids != ''
    """).fetchall()

    for r in rows:
        intel_id = r['intel_id']
        dp_code = r['dp_code'] or ''
        category = r['category'] or ''
        label = f"INTEL_SUMMARY:{intel_id} {dp_code} {category}"

        case_ids = r['case_ids'] or ''
        for bd_id in case_ids.split(','):
            bd_id = bd_id.strip()
            if not bd_id:
                continue
            # Find nodes already linked to this BD entry
            bd_nodes = conn.execute("""
                SELECT node_id FROM term_dimensions
                WHERE dimension = 'INTELLIGENCE'
                  AND target_table = 'bitig_degradation_register'
                  AND target_id = ?
            """, (bd_id,)).fetchall()

            for bn in bd_nodes:
                total += insert_edge(conn, bn['node_id'],
                                     'bitig_intelligence_summary',
                                     intel_id, label)

    print(f"  Bitig intel summaries: {total} edges from {len(rows)} assessments")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# PASS 8: CHILD_SCHEMA (Peoples) → INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def wire_child_schema(conn):
    """Wire CHILD_SCHEMA peoples entries into INTELLIGENCE dimension.

    child_schema columns: entry_id, shell_name, dp_codes, inversion_direction,
    operation_role, etc. Each people entry IS intelligence — operator-assigned names,
    DP codes, inversion patterns.
    """
    total = 0

    try:
        rows = conn.execute("""
            SELECT entry_id, shell_name, dp_codes, inversion_direction,
                   operation_role, orig_root, phonetic_chain
            FROM child_schema
        """).fetchall()
    except sqlite3.OperationalError:
        print("  child_schema: table not found, skipping.")
        return 0

    for r in rows:
        pid = r['entry_id']
        sname = r['shell_name'] or ''
        dp_codes = r['dp_codes'] or ''
        inv_dir = r['inversion_direction'] or ''
        label = f"PEOPLE:{pid} {sname[:30]} [{dp_codes}]"

        # Find nodes: child_schema entries or term_nodes matching the name
        # Extract searchable parts from shell_name (e.g., "Slav / slave" → "slav")
        search_parts = [p.strip().lower() for p in sname.split('/') if p.strip()]
        # Also try just the ID
        all_matched = set()

        # Direct lookup by source_table
        direct = conn.execute("""
            SELECT node_id FROM term_nodes
            WHERE source_table = 'child_schema' AND source_id = ?
        """, (str(pid),)).fetchall()
        for d in direct:
            all_matched.add(d['node_id'])

        # Search by name parts
        for part in search_parts:
            if len(part) < 3:
                continue
            matched = conn.execute("""
                SELECT node_id FROM term_nodes
                WHERE term_normal LIKE ?
                  AND entry_type = 'WORD'
                LIMIT 10
            """, (f"%{part}%",)).fetchall()
            for m in matched:
                all_matched.add(m['node_id'])

        for nid in all_matched:
            total += insert_edge(conn, nid, 'child_schema', pid, label)

    print(f"  Child schema (peoples): {total} edges from {len(rows)} entries")
    conn.commit()
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def status(conn):
    """Show INTELLIGENCE dimension status with breakdown."""
    print("=" * 60)
    print("ḤASHR — INTELLIGENCE DIMENSION STATUS")
    print("هُوَ ٱلَّذِىٓ أَخْرَجَ ٱلَّذِينَ كَفَرُوا۟")
    print("=" * 60)

    # Total INTELLIGENCE edges
    total = conn.execute("""
        SELECT COUNT(*) FROM term_dimensions WHERE dimension = 'INTELLIGENCE'
    """).fetchone()[0]
    print(f"\n  TOTAL INTELLIGENCE EDGES: {total}")

    # Breakdown by target_table
    breakdown = conn.execute("""
        SELECT target_table, COUNT(*) as cnt
        FROM term_dimensions
        WHERE dimension = 'INTELLIGENCE'
        GROUP BY target_table
        ORDER BY cnt DESC
    """).fetchall()

    print(f"\n  {'TARGET TABLE':<35s} {'EDGES':>6s}")
    print(f"  {'─'*35} {'─'*6}")
    for r in breakdown:
        bar = '█' * (r['cnt'] // 5)
        print(f"  {r['target_table']:<35s} {r['cnt']:>6d}  {bar}")

    # Breakdown by label prefix (edge type)
    labels = conn.execute("""
        SELECT label FROM term_dimensions WHERE dimension = 'INTELLIGENCE'
    """).fetchall()

    prefix_counts = Counter()
    for r in labels:
        lbl = r['label'] or ''
        prefix = lbl.split(':')[0] if ':' in lbl else lbl.split(' ')[0]
        prefix_counts[prefix] += 1

    print(f"\n  {'EDGE TYPE':<25s} {'COUNT':>6s}")
    print(f"  {'─'*25} {'─'*6}")
    for prefix, cnt in prefix_counts.most_common():
        print(f"  {prefix:<25s} {cnt:>6d}")

    # Unique nodes with INTELLIGENCE edges
    unique_nodes = conn.execute("""
        SELECT COUNT(DISTINCT node_id) FROM term_dimensions
        WHERE dimension = 'INTELLIGENCE'
    """).fetchone()[0]
    print(f"\n  UNIQUE NODES WITH INTEL: {unique_nodes}")

    # Compare with total nodes
    total_nodes = conn.execute("SELECT COUNT(*) FROM term_nodes").fetchone()[0]
    pct = (unique_nodes / total_nodes * 100) if total_nodes > 0 else 0
    print(f"  TOTAL NODES: {total_nodes}")
    print(f"  COVERAGE: {pct:.1f}%")

    # All dimensions for comparison
    print(f"\n  {'ALL DIMENSIONS':}")
    dims = conn.execute("""
        SELECT dimension, COUNT(*) FROM term_dimensions
        GROUP BY dimension ORDER BY COUNT(*) DESC
    """).fetchall()
    for d in dims:
        marker = " ◀ ḤASHR" if d['dimension'] == 'INTELLIGENCE' else ""
        print(f"    {d['dimension']:<20s} {d[1]:>6d}{marker}")


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT — trace intelligence edges for a specific entry
# ═══════════════════════════════════════════════════════════════════════════════

def audit(conn, term):
    """Show all intelligence edges for a given term."""
    print(f"\n  ḤASHR AUDIT: '{term}'")
    print(f"  {'─'*50}")

    # Find nodes
    nodes = conn.execute("""
        SELECT node_id, term, language, source_table, source_id
        FROM term_nodes
        WHERE term_normal LIKE ? OR term LIKE ?
    """, (f"%{term.lower()}%", f"%{term}%")).fetchall()

    if not nodes:
        print(f"  No nodes found for '{term}'")
        return

    for n in nodes:
        print(f"\n  NODE {n['node_id']}: {n['term']} ({n['language']}) "
              f"[{n['source_table']} #{n['source_id']}]")

        edges = conn.execute("""
            SELECT target_table, target_id, label
            FROM term_dimensions
            WHERE node_id = ? AND dimension = 'INTELLIGENCE'
        """, (n['node_id'],)).fetchall()

        if not edges:
            print(f"    (no INTELLIGENCE edges)")
        for e in edges:
            print(f"    → {e['target_table']}: {e['target_id']} | {e['label']}")


# ═══════════════════════════════════════════════════════════════════════════════
# GATHER — Full ḤASHR run (all passes)
# ═══════════════════════════════════════════════════════════════════════════════

def gather(conn):
    """Execute all ḤASHR passes — gather intelligence across the lattice."""
    print("=" * 60)
    print("ḤASHR — THE GATHERING")
    print("Q59:2 — Intelligence integration across the lattice")
    print("=" * 60)

    # First: count existing INTELLIGENCE edges
    existing = conn.execute("""
        SELECT COUNT(*) FROM term_dimensions WHERE dimension = 'INTELLIGENCE'
    """).fetchone()[0]
    print(f"\n  Existing INTELLIGENCE edges: {existing}")

    # Clear existing INTELLIGENCE edges for clean rebuild
    conn.execute("DELETE FROM term_dimensions WHERE dimension = 'INTELLIGENCE'")
    conn.commit()
    print(f"  Cleared {existing} existing edges for clean rebuild.")

    print(f"\n[Pass 1] Inversion types (EN + RU)...")
    p1 = wire_inversion_types(conn)

    print(f"\n[Pass 2] Bitig degradation register...")
    p2 = wire_bitig_degradation(conn)

    print(f"\n[Pass 3] Chronology intelligence...")
    p3 = wire_chronology_intelligence(conn)

    print(f"\n[Pass 4] Network intelligence...")
    p4 = wire_network_intelligence(conn)

    print(f"\n[Pass 5] Contamination blacklist...")
    p5 = wire_blacklist(conn)

    print(f"\n[Pass 6] DP register...")
    p6 = wire_dp_register(conn)

    print(f"\n[Pass 7] Bitig intelligence summaries...")
    p7 = wire_bitig_intel_summaries(conn)

    print(f"\n[Pass 8] Child schema (peoples)...")
    p8 = wire_child_schema(conn)

    # Final count
    final = conn.execute("""
        SELECT COUNT(*) FROM term_dimensions WHERE dimension = 'INTELLIGENCE'
    """).fetchone()[0]

    print(f"\n{'='*60}")
    print(f"  ḤASHR COMPLETE")
    print(f"  Before: {existing} → After: {final}")
    print(f"  New edges: {final - 0}")  # rebuilt from scratch
    print(f"  Pass breakdown: P1={p1} P2={p2} P3={p3} P4={p4} P5={p5} P6={p6} P7={p7} P8={p8}")
    print(f"{'='*60}")

    return final


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 uslap_hashr.py <command> [args]")
        print("Commands:")
        print("  gather   — Run all 8 ḤASHR passes (full intelligence wiring)")
        print("  status   — Show INTELLIGENCE dimension status")
        print("  audit TERM — Show intelligence edges for a term")
        return

    cmd = sys.argv[1].lower()
    conn = get_conn()

    if cmd == 'gather':
        gather(conn)
    elif cmd == 'status':
        status(conn)
    elif cmd == 'audit':
        if len(sys.argv) < 3:
            print("Usage: python3 uslap_hashr.py audit <term>")
            return
        audit(conn, ' '.join(sys.argv[2:]))
    else:
        print(f"Unknown command: {cmd}")

    conn.close()


if __name__ == '__main__':
    main()
