#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر جِسْم — BODY/HEALTH REASONING MODULE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: ج-س-م — body, substance, corporeality
Q95:4 لَقَدْ خَلَقْنَا الْإِنسَانَ فِي أَحْسَنِ تَقْوِيمٍ
— We created the human in the best form

Reasons from roots to body systems, organs, therapies, prayers.
Wired to 46 body/health tables in the lattice.
Every answer traces to 28 letters.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

# Body domain tables — grouped by function
ARCHITECTURE_TABLES = [
    'body_architecture', 'body_nodes', 'body_skeletal_map',
    'body_chemistry', 'body_substances', 'body_technical',
]
THERAPY_TABLES = [
    'body_colour_therapy', 'body_sound_therapy', 'healing_protocols',
    'therapy_prayer_map',
]
LIFECYCLE_TABLES = [
    'body_creation_stages', 'lifecycle_architecture', 'lifecycle_cross_refs',
    'death_mechanism', 'spirit_infusion',
]
NAFS_TABLES = [
    'nafs_architecture', 'nafs_cross_refs', 'qalb_states',
    'emotional_disorders', 'transition_states', 'perception_hierarchy',
    'perception_contamination',
]
SENSORY_TABLES = [
    'sensory_architecture', 'sensory_cross_refs', 'sensory_diagnostics',
    'sensory_disorders', 'sensory_prayer_map',
]
NUTRITION_TABLES = [
    'nutrition_architecture', 'nutrition_cross_refs', 'nutrition_intelligence',
    'food_contrasts', 'food_production_cycle', 'agricultural_system',
]
PRAYER_TABLES = [
    'prayer_states', 'prayer_transitions', 'body_heptad_meta',
]
DIAGNOSTIC_TABLES = [
    'body_diagnostics', 'body_extraction_intel',
]
CROSS_REF_TABLES = [
    'body_cross_refs', 'body_edges', 'body_movement_chains',
]
OTHER_TABLES = [
    'heart_compilation', 'pelvis_tissue', 'social_health',
    'body_preservation', 'body_colour_therapy',
]

ALL_BODY_TABLES = (ARCHITECTURE_TABLES + THERAPY_TABLES + LIFECYCLE_TABLES +
                   NAFS_TABLES + SENSORY_TABLES + NUTRITION_TABLES +
                   PRAYER_TABLES + DIAGNOSTIC_TABLES + CROSS_REF_TABLES + OTHER_TABLES)

# Deduplicate
ALL_BODY_TABLES = list(dict.fromkeys(ALL_BODY_TABLES))


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_query(conn, sql, params=(), quf_filter=True):
    """Query with QUF filter. Only returns TRUE/PENDING rows."""
    try:
        if quf_filter and 'WHERE' in sql.upper():
            sql = sql + " AND (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL)"
        elif quf_filter and 'WHERE' not in sql.upper() and 'LIMIT' in sql.upper():
            sql = sql.replace('LIMIT', "WHERE (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL) LIMIT")
        return conn.execute(sql, params).fetchall()
    except:
        try:
            return conn.execute(sql.replace("AND (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL)", "")
                               .replace("WHERE (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL) ", ""), params).fetchall()
        except:
            return []


def _quf_body(row, conn=None):
    """جِسْم QUF colour — Body/Health epistemology.

    Q (Quantification): root has Qur'anic tokens + body table linkage count.
        HIGH = root_id valid + tokens > 0 + quranic_ref is specific ayah
        MEDIUM = root_id valid + tokens > 0
        LOW = root_letters present but no root_id match
        FAIL = no root linkage at all

    U (Universality): root appears across multiple body subsystems.
        HIGH = root found in ≥3 body table groups (architecture + therapy + nafs etc.)
        MEDIUM = root in ≥2 groups
        LOW = root in 1 group
        FAIL = no cross-system presence

    F (Falsifiability): quranic_ref is specific, not vague.
        HIGH = quranic_ref contains Q##:## pattern (specific ayah)
        MEDIUM = quranic_ref exists but vague
        LOW = no quranic_ref but root has tokens
        FAIL = no evidence trail
    """
    import re
    d = dict(row) if not isinstance(row, dict) else row

    # Q — root linkage + tokens
    root_id = d.get('aa_root_id', '') or d.get('root_id', '')
    root_letters = d.get('root_letters', '')
    qur_ref = d.get('quranic_ref', '') or d.get('qur_ref', '') or ''
    tokens = 0
    if conn and root_id:
        r = conn.execute("SELECT quran_tokens FROM roots WHERE root_id=?", (root_id,)).fetchone()
        tokens = r[0] if r else 0

    has_specific_ref = bool(re.search(r'Q?\d+:\d+', str(qur_ref)))
    if root_id and tokens > 0 and has_specific_ref:
        q = 'HIGH'
    elif root_id and tokens > 0:
        q = 'MEDIUM'
    elif root_id or root_letters:
        q = 'LOW'
    else:
        q = 'FAIL'

    # U — cross-subsystem presence (checked at result level, not row level)
    # At row level: does this row have cross-refs to other body tables?
    arabic = d.get('arabic', '')
    has_arabic = bool(arabic and any('\u0600' <= c <= '\u06FF' for c in str(arabic)))
    if root_id and has_arabic:
        u = 'HIGH'
    elif root_id:
        u = 'MEDIUM'
    elif has_arabic:
        u = 'LOW'
    else:
        u = 'FAIL'

    # F — specificity of evidence
    if has_specific_ref and tokens > 0:
        f = 'HIGH'
    elif qur_ref or tokens > 0:
        f = 'MEDIUM'
    elif root_letters:
        f = 'LOW'
    else:
        f = 'FAIL'

    grades = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FAIL': 0}
    overall = 'TRUE' if min(grades[q], grades[u], grades[f]) >= 2 else (
        'PENDING' if min(grades[q], grades[u], grades[f]) >= 1 else 'FALSE')

    return {'q': q, 'u': u, 'f': f, 'pass': overall}


def _quf_status(rows, conn=None):
    """Compute domain-specific QUF summary for body result set."""
    if not rows:
        return {'total': 0, 'verified': 0, 'pending': 0, 'rate': '0%',
                'q_high': 0, 'u_high': 0, 'f_high': 0}
    total = len(rows)
    results = [_quf_body(r, conn) for r in rows]
    verified = sum(1 for r in results if r['pass'] == 'TRUE')
    pending = sum(1 for r in results if r['pass'] == 'PENDING')
    q_high = sum(1 for r in results if r['q'] == 'HIGH')
    u_high = sum(1 for r in results if r['u'] == 'HIGH')
    f_high = sum(1 for r in results if r['f'] == 'HIGH')
    return {'total': total, 'verified': verified, 'pending': pending,
            'rate': f'{verified*100//max(total,1)}%',
            'q_high': q_high, 'u_high': u_high, 'f_high': f_high}


def _get_root_id(conn, root_ref):
    """Resolve root reference to root_id + root_letters."""
    if not root_ref:
        return None, None
    # Try direct root_id
    row = conn.execute("SELECT root_id, root_letters FROM roots WHERE root_id=?", (root_ref,)).fetchone()
    if row:
        return row['root_id'], row['root_letters']
    # Try root_letters
    row = conn.execute("SELECT root_id, root_letters FROM roots WHERE root_letters=?", (root_ref,)).fetchone()
    if row:
        return row['root_id'], row['root_letters']
    # Try root_bare
    row = conn.execute("SELECT root_id, root_letters FROM roots WHERE root_bare=?", (root_ref,)).fetchone()
    if row:
        return row['root_id'], row['root_letters']
    return None, None


# ═══════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def expand_root_body(root_ref):
    """Expand a root into its full body lattice.

    Returns all body systems, organs, therapies, prayers, and diagnostics
    connected to this root.

    Args:
        root_ref: root_id (R001), root_letters (ق-ل-ب), or root_bare (قلب)

    Returns:
        dict with sections: architecture, therapy, lifecycle, nafs, sensory,
        nutrition, prayer, diagnostics, cross_refs, summary
    """
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)

    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}', 'sections': {}}

    # Get root data
    root_row = conn.execute("SELECT * FROM roots WHERE root_id=?", (root_id,)).fetchone()
    result = {
        'root': {
            'root_id': root_id,
            'root_letters': root_letters,
            'primary_meaning': root_row['primary_meaning'] if root_row else '',
            'quran_tokens': root_row['quran_tokens'] if root_row else 0,
        },
        'sections': {},
        'summary': {},
    }

    # Query each domain table group
    for group_name, tables in [
        ('architecture', ARCHITECTURE_TABLES),
        ('therapy', THERAPY_TABLES),
        ('lifecycle', LIFECYCLE_TABLES),
        ('nafs', NAFS_TABLES),
        ('sensory', SENSORY_TABLES),
        ('nutrition', NUTRITION_TABLES),
        ('prayer', PRAYER_TABLES),
        ('diagnostics', DIAGNOSTIC_TABLES),
        ('cross_refs', CROSS_REF_TABLES),
    ]:
        section = {}
        for tbl in tables:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            # Try multiple linkage columns
            rows = []
            if 'aa_root_id' in cols:
                rows = _safe_query(conn,
                    f'SELECT * FROM "{tbl}" WHERE aa_root_id=? ',
                    (root_id,))
            if not rows and 'root_letters' in cols:
                rows = _safe_query(conn,
                    f'SELECT * FROM "{tbl}" WHERE root_letters=? ',
                    (root_letters,))
            if not rows and 'arabic' in cols:
                # Try matching Arabic text against root_bare
                bare = root_row['root_bare'] if root_row else ''
                if bare:
                    rows = _safe_query(conn,
                        f'SELECT * FROM "{tbl}" WHERE arabic LIKE ? ',
                        (f'%{bare}%',))

            if rows:
                section[tbl] = [dict(r) for r in rows]

        if section:
            result['sections'][group_name] = section

    # Summary
    total_hits = sum(
        sum(len(v) for v in section.values())
        for section in result['sections'].values()
    )
    # QUF status across all results
    all_rows = []
    for section in result['sections'].values():
        for tbl_rows in section.values():
            all_rows.extend(tbl_rows)

    result['summary'] = {
        'root_id': root_id,
        'sections_found': len(result['sections']),
        'total_hits': total_hits,
        'tables_hit': sum(len(s) for s in result['sections'].values()),
        'quf': _quf_status(all_rows),
    }

    conn.close()
    return result


def trace_body_system(system_name):
    """Find all roots connected to a body system.

    Args:
        system_name: e.g., "heart", "nafs", "sensory", "skeletal", "digestive"

    Returns:
        dict with all roots and their body data for this system
    """
    conn = _connect()

    # Map system names to table groups
    system_map = {
        'heart': ['heart_compilation', 'qalb_states'],
        'nafs': NAFS_TABLES,
        'sensory': SENSORY_TABLES,
        'skeletal': ['body_skeletal_map'],
        'nutrition': NUTRITION_TABLES,
        'prayer': PRAYER_TABLES,
        'lifecycle': LIFECYCLE_TABLES,
        'therapy': THERAPY_TABLES,
        'architecture': ARCHITECTURE_TABLES,
        'diagnostics': DIAGNOSTIC_TABLES,
    }

    # Fuzzy match
    tables = []
    for key, tbls in system_map.items():
        if system_name.lower() in key or key in system_name.lower():
            tables = tbls
            break

    if not tables:
        # Search across all body tables
        tables = ALL_BODY_TABLES

    roots_found = {}
    for tbl in tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        except:
            continue

        # Get all rows with root linkage
        if 'aa_root_id' in cols:
            rows = _safe_query(conn, f'SELECT * FROM "{tbl}" WHERE aa_root_id IS NOT NULL AND aa_root_id != ""')
            for row in rows:
                rid = row['aa_root_id']
                roots_found.setdefault(rid, {'tables': [], 'data': []})
                roots_found[rid]['tables'].append(tbl)
                roots_found[rid]['data'].append(dict(row))
        elif 'root_letters' in cols:
            rows = _safe_query(conn, f'SELECT * FROM "{tbl}" WHERE root_letters IS NOT NULL AND root_letters != ""')
            for row in rows:
                rl = row['root_letters']
                # Resolve to root_id
                rid_row = conn.execute("SELECT root_id FROM roots WHERE root_letters=?", (rl,)).fetchone()
                rid = rid_row['root_id'] if rid_row else rl
                roots_found.setdefault(rid, {'tables': [], 'data': []})
                roots_found[rid]['tables'].append(tbl)
                roots_found[rid]['data'].append(dict(row))

    conn.close()
    return {
        'system': system_name,
        'tables_searched': len(tables),
        'roots_found': len(roots_found),
        'roots': roots_found,
    }


def diagnose_root(root_ref):
    """Get diagnostics and healing protocols for a root.

    Args:
        root_ref: root_id, root_letters, or root_bare

    Returns:
        dict with diagnostics, healing_protocols, therapies, prayer_mappings
    """
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)

    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    result = {'root_id': root_id, 'root_letters': root_letters}

    # Diagnostics
    for tbl, key in [
        ('body_diagnostics', 'diagnostics'),
        ('healing_protocols', 'healing'),
        ('body_colour_therapy', 'colour_therapy'),
        ('body_sound_therapy', 'sound_therapy'),
        ('therapy_prayer_map', 'prayer_therapy'),
        ('sensory_diagnostics', 'sensory_diagnostics'),
    ]:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        rows = []
        if 'aa_root_id' in cols:
            rows = _safe_query(conn, f'SELECT * FROM "{tbl}" WHERE aa_root_id=?', (root_id,))
        elif 'root_letters' in cols:
            rows = _safe_query(conn, f'SELECT * FROM "{tbl}" WHERE root_letters=?', (root_letters,))
        if rows:
            result[key] = [dict(r) for r in rows]

    conn.close()
    return result


def body_heptad(heptad_num):
    """Get full heptad manifest with surah-body mappings.

    Args:
        heptad_num: 1-7

    Returns:
        dict with heptad meta, body architecture, prayer map
    """
    conn = _connect()

    result = {'heptad': heptad_num}

    # Heptad meta
    meta = _safe_query(conn,
        'SELECT * FROM body_heptad_meta WHERE heptad=? OR heptad_number=?',
        (heptad_num, heptad_num))
    if not meta:
        meta = _safe_query(conn,
            'SELECT * FROM body_heptad_meta WHERE CAST(heptad AS INTEGER)=?',
            (heptad_num,))
    result['meta'] = [dict(r) for r in meta]

    # Prayer map for this heptad
    prayers = _safe_query(conn,
        'SELECT * FROM sensory_prayer_map WHERE heptad=? OR heptad_number=?',
        (heptad_num, heptad_num))
    result['prayer_map'] = [dict(r) for r in prayers]

    conn.close()
    return result


def body_cross_search(query):
    """Search across all 46 body tables for a term.

    Args:
        query: search term (English, Arabic, or root reference)

    Returns:
        dict with hits per table
    """
    conn = _connect()
    results = {}
    query_lower = query.lower()

    for tbl in ALL_BODY_TABLES:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            data_cols = [c for c in cols if not c.startswith('quf_') and c not in ('created_at', 'modified_at')]

            # Build search across all text columns
            conditions = []
            params = []
            for col in data_cols:
                conditions.append(f'LOWER(COALESCE("{col}","")) LIKE ?')
                params.append(f'%{query_lower}%')

            if conditions:
                sql = f'SELECT * FROM "{tbl}" WHERE {" OR ".join(conditions)} LIMIT 20'
                rows = conn.execute(sql, params).fetchall()
                if rows:
                    results[tbl] = [dict(r) for r in rows]
        except Exception:
            continue

    conn.close()
    return {
        'query': query,
        'tables_searched': len(ALL_BODY_TABLES),
        'tables_hit': len(results),
        'total_hits': sum(len(v) for v in results.values()),
        'results': results,
    }


def body_stats():
    """Return statistics for all body tables."""
    conn = _connect()
    stats = {}
    total_rows = 0
    total_rooted = 0

    for tbl in ALL_BODY_TABLES:
        try:
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]

            rooted = 0
            if 'aa_root_id' in cols:
                rooted = conn.execute(f'SELECT COUNT(*) FROM "{tbl}" WHERE aa_root_id IS NOT NULL AND aa_root_id != ""').fetchone()[0]
            elif 'root_letters' in cols:
                rooted = conn.execute(f'SELECT COUNT(*) FROM "{tbl}" WHERE root_letters IS NOT NULL AND root_letters != ""').fetchone()[0]

            quf_pass = 0
            if 'quf_pass' in cols:
                quf_pass = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_pass='TRUE'").fetchone()[0]

            stats[tbl] = {'rows': cnt, 'rooted': rooted, 'quf_pass': quf_pass}
            total_rows += cnt
            total_rooted += rooted
        except:
            pass

    conn.close()
    return {
        'tables': len(stats),
        'total_rows': total_rows,
        'total_rooted': total_rooted,
        'root_coverage': f'{total_rooted*100//max(total_rows,1)}%',
        'detail': stats,
    }


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def body_quf(data: dict) -> dict:
    """
    BODY QUF — L10.
    Q: arabic + english + root_letters present + Qur'anic body reference
    U: 7×7 heptad integrity (heptad column valid, root linked)
    F: cross-subsystem consistency + not blacklisted
    """
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    arabic = data.get('arabic', '') or ''
    english = data.get('english', '') or ''
    root_letters = data.get('root_letters', '') or data.get('aa_root_id', '') or ''
    heptad = data.get('heptad', 0) or 0
    qur_ref = data.get('quranic_ref', '') or data.get('qur_ref', '') or ''
    subsystem = data.get('subsystem', '') or data.get('subtable', '') or ''
    status = data.get('status', '') or ''

    # Q: evidence quantity
    q_items = sum([bool(arabic), bool(english), bool(root_letters), bool(qur_ref)])
    q = 'HIGH' if q_items >= 3 else ('MEDIUM' if q_items >= 2 else ('LOW' if q_items >= 1 else 'FAIL'))
    q_ev = [f'arabic={bool(arabic)}, english={bool(english)}, root={bool(root_letters)}, qur_ref={bool(qur_ref)}']

    # U: heptad structure + root linkage
    heptad_valid = 1 <= heptad <= 7 if heptad else False
    has_root = bool(root_letters)
    u = 'HIGH' if (heptad_valid and has_root) else ('MEDIUM' if heptad_valid or has_root else 'LOW')
    u_ev = [f'heptad={heptad} (valid={heptad_valid}), root={has_root}']

    # F: consistency
    has_subsystem = bool(subsystem)
    f = 'HIGH' if (has_subsystem and has_root and english) else ('MEDIUM' if has_subsystem else 'LOW')
    f_ev = [f'subsystem={subsystem}, status={status}']

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev, 'u_evidence': u_ev, 'f_evidence': f_ev,
    }


def body_xref_quf(data: dict) -> dict:
    """BODY CROSS-REF QUF — L10 cross-references."""
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    source_id = data.get('source_id', '') or ''
    target_id = data.get('target_id', '') or ''
    relationship = data.get('relationship', '') or ''
    qur_ref = data.get('quranic_ref', '') or ''
    subsystem = data.get('subsystem', '') or ''

    q = 'HIGH' if (source_id and target_id and relationship) else ('MEDIUM' if source_id and target_id else 'LOW')
    u = 'HIGH' if (subsystem and relationship) else ('MEDIUM' if subsystem else 'LOW')
    f = 'HIGH' if qur_ref else ('MEDIUM' if relationship else 'LOW')

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': [f'source={bool(source_id)}, target={bool(target_id)}, rel={relationship[:20]}'],
        'u_evidence': [f'subsystem={subsystem}'],
        'f_evidence': [f'qur_ref={bool(qur_ref)}'],
    }


def body_prayer_quf(data: dict) -> dict:
    """BODY PRAYER MAP QUF — L10 prayer states."""
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    prayer_state = data.get('prayer_state', '') or ''
    specific_data = data.get('specific_data', '') or ''
    subsystem = data.get('subsystem', '') or ''

    # Parse specific_data JSON for richness
    import json
    sd = {}
    try:
        sd = json.loads(specific_data) if specific_data else {}
    except (json.JSONDecodeError, TypeError):
        pass

    has_arabic = bool(sd.get('arabic', ''))
    has_root = bool(sd.get('root_letters', ''))
    has_tokens = (sd.get('quranic_tokens', 0) or 0) > 0
    field_count = len([v for v in sd.values() if v])

    q = 'HIGH' if (prayer_state and field_count >= 5) else ('MEDIUM' if prayer_state else 'LOW')
    u = 'HIGH' if (has_root and has_tokens) else ('MEDIUM' if has_root or has_tokens else 'LOW')
    f = 'HIGH' if (has_arabic and field_count >= 8) else ('MEDIUM' if has_arabic else 'LOW')

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': [f'state={prayer_state}, fields={field_count}'],
        'u_evidence': [f'root={has_root}, tokens={has_tokens}'],
        'f_evidence': [f'arabic={has_arabic}, fields={field_count}'],
    }


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 amr_jism.py <command> [args]")
        print("  expand <root>     — expand root into body lattice")
        print("  system <name>     — trace body system")
        print("  diagnose <root>   — diagnostics + healing for root")
        print("  heptad <1-7>      — heptad manifest")
        print("  search <query>    — cross-search all body tables")
        print("  stats             — body table statistics")
        sys.exit(0)

    cmd = args[0]
    if cmd == 'expand' and len(args) > 1:
        import json
        r = expand_root_body(args[1])
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    elif cmd == 'system' and len(args) > 1:
        import json
        r = trace_body_system(args[1])
        print(f"System: {r['system']}, Roots: {r['roots_found']}")
        for rid, data in list(r['roots'].items())[:10]:
            print(f"  {rid}: {len(data['tables'])} tables — {data['tables']}")
    elif cmd == 'diagnose' and len(args) > 1:
        import json
        r = diagnose_root(args[1])
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    elif cmd == 'heptad' and len(args) > 1:
        import json
        r = body_heptad(int(args[1]))
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    elif cmd == 'search' and len(args) > 1:
        r = body_cross_search(' '.join(args[1:]))
        print(f"Query: '{r['query']}', Tables hit: {r['tables_hit']}, Total hits: {r['total_hits']}")
        for tbl, rows in r['results'].items():
            print(f"  {tbl}: {len(rows)} hits")
    elif cmd == 'stats':
        r = body_stats()
        print(f"Body lattice: {r['tables']} tables, {r['total_rows']} rows, {r['root_coverage']} rooted")
        for tbl, d in sorted(r['detail'].items()):
            if d['rows'] > 0:
                print(f"  {tbl:<40} {d['rows']:>4} rows, {d['rooted']:>4} rooted, {d['quf_pass']:>4} QUF")
    else:
        print(f"Unknown command: {cmd}")
