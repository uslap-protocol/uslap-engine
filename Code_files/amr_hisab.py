#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر حِسَاب — FORMULA/NUMERICAL REASONING MODULE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: ح-س-ب — reckoning, computation, accountability
Q84:8 فَسَوْفَ يُحَاسَبُ حِسَابًا يَسِيرًا
— He will be given an easy reckoning

Reasons from roots to formulas, ratios, concealment chains, and scholars.
Wired to 6 formula tables in the lattice.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

FORMULA_TABLES = [
    'formula_restoration', 'formula_concealment', 'formula_ratios',
    'formula_cross_refs', 'formula_scholars', 'formula_undiscovered',
]


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_query(conn, sql, params=(), quf_filter=True):
    """Query with QUF filter. Only returns TRUE/PENDING rows from QUF-enabled tables."""
    try:
        if quf_filter and 'WHERE' in sql.upper():
            # Inject QUF filter
            sql = sql + " AND (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL)"
        elif quf_filter and 'WHERE' not in sql.upper() and 'LIMIT' in sql.upper():
            sql = sql.replace('LIMIT', "WHERE (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL) LIMIT")
        return conn.execute(sql, params).fetchall()
    except:
        # If quf_pass column doesn't exist, retry without filter
        try:
            return conn.execute(sql.replace("AND (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL)", "")
                               .replace("WHERE (quf_pass IN ('TRUE','PENDING') OR quf_pass IS NULL) ", ""), params).fetchall()
        except:
            return []


def _quf_formula(row, conn=None):
    """حِسَاب QUF colour — Formula/Numerical epistemology.

    Q (Quantification): ratio has numerical value + root linkage.
        HIGH = numerical value present + root_letters + quranic_ref
        MEDIUM = numerical value OR root linkage present
        LOW = content exists but no numerical grounding
        FAIL = empty row

    U (Universality): formula verified across multiple instances.
        HIGH = ratio verified (divine_fraction computed) + source cited
        MEDIUM = content populated + category assigned
        LOW = partial data
        FAIL = insufficient data

    F (Falsifiability): concealment mechanism documented with DP code.
        HIGH = detection_pattern/dp code assigned + mechanism documented
        MEDIUM = mechanism or source exists
        LOW = content only
        FAIL = no evidence trail
    """
    d = dict(row) if not isinstance(row, dict) else row

    # Q — numerical grounding
    has_value = bool(d.get('ratio_value') or d.get('divine_fraction') or d.get('formula_ar'))
    has_root = bool(d.get('root_letters') or d.get('quranic_root') or d.get('related_roots'))
    has_qref = bool(d.get('quranic_ref'))
    if has_value and has_root and has_qref:
        q = 'HIGH'
    elif has_value or has_root:
        q = 'MEDIUM'
    elif d.get('content') or d.get('contaminated_formula') or d.get('formula_en'):
        q = 'LOW'
    else:
        q = 'FAIL'

    # U — verification breadth
    has_fraction = bool(d.get('divine_fraction'))
    has_source = bool(d.get('source_sheet') or d.get('western_attribution'))
    has_category = bool(d.get('category') or d.get('domain'))
    if has_fraction and has_source:
        u = 'HIGH'
    elif has_category and (has_source or has_fraction):
        u = 'MEDIUM'
    elif has_category:
        u = 'LOW'
    else:
        u = 'FAIL'

    # F — falsifiability via detection pattern
    has_dp = bool(d.get('detection_pattern') or d.get('dp_codes'))
    has_mechanism = bool(d.get('mechanism') and len(str(d.get('mechanism', ''))) > 5)
    has_audit = bool(d.get('status_audit'))
    if has_dp and has_mechanism:
        f = 'HIGH'
    elif has_dp or has_mechanism or has_audit:
        f = 'MEDIUM'
    elif d.get('content') or d.get('description'):
        f = 'LOW'
    else:
        f = 'FAIL'

    grades = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FAIL': 0}
    overall = 'TRUE' if min(grades[q], grades[u], grades[f]) >= 2 else (
        'PENDING' if min(grades[q], grades[u], grades[f]) >= 1 else 'FALSE')

    return {'q': q, 'u': u, 'f': f, 'pass': overall}


def _quf_status(rows, conn=None):
    """Compute domain-specific QUF summary for formula result set."""
    if not rows:
        return {'total': 0, 'verified': 0, 'pending': 0, 'rate': '0%',
                'q_high': 0, 'u_high': 0, 'f_high': 0}
    total = len(rows)
    results = [_quf_formula(r, conn) for r in rows]
    verified = sum(1 for r in results if r['pass'] == 'TRUE')
    pending = sum(1 for r in results if r['pass'] == 'PENDING')
    return {'total': total, 'verified': verified, 'pending': pending,
            'rate': f'{verified*100//max(total,1)}%',
            'q_high': sum(1 for r in results if r['q'] == 'HIGH'),
            'u_high': sum(1 for r in results if r['u'] == 'HIGH'),
            'f_high': sum(1 for r in results if r['f'] == 'HIGH')}


def _get_root_id(conn, root_ref):
    if not root_ref:
        return None, None
    for col in ['root_id', 'root_letters', 'root_bare']:
        row = conn.execute(f"SELECT root_id, root_letters FROM roots WHERE {col}=?", (root_ref,)).fetchone()
        if row:
            return row['root_id'], row['root_letters']
    return None, None


def expand_root_formula(root_ref):
    """All formulas connected to a root.

    Queries formula_restoration, formula_scholars, formula_undiscovered
    via root_letters/quranic_root columns, plus cross-refs.
    """
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    bare = conn.execute("SELECT root_bare FROM roots WHERE root_id=?", (root_id,)).fetchone()
    root_bare = bare['root_bare'] if bare else ''

    result = {'root_id': root_id, 'root_letters': root_letters, 'sections': {}}

    # formula_scholars has root_letters + quranic_ref
    scholars = _safe_query(conn,
        'SELECT * FROM formula_scholars WHERE root_letters=? OR root_letters LIKE ?',
        (root_letters, f'%{root_bare}%'))
    if scholars:
        result['sections']['scholars'] = [dict(r) for r in scholars]

    # formula_undiscovered has quranic_root + related_roots
    undiscovered = _safe_query(conn,
        'SELECT * FROM formula_undiscovered WHERE quranic_root LIKE ? OR related_roots LIKE ?',
        (f'%{root_bare}%', f'%{root_bare}%'))
    if undiscovered:
        result['sections']['undiscovered'] = [dict(r) for r in undiscovered]

    # formula_restoration — search by domain/content for root reference
    restoration = _safe_query(conn,
        'SELECT * FROM formula_restoration WHERE contaminated_formula LIKE ? OR subfield LIKE ? LIMIT 20',
        (f'%{root_bare}%', f'%{root_bare}%'))
    if restoration:
        result['sections']['restoration'] = [dict(r) for r in restoration]

    # formula_concealment
    concealment = _safe_query(conn,
        'SELECT * FROM formula_concealment WHERE content LIKE ? LIMIT 20',
        (f'%{root_bare}%',))
    if concealment:
        result['sections']['concealment'] = [dict(r) for r in concealment]

    result['summary'] = {
        'sections_found': len(result['sections']),
        'total_hits': sum(len(v) for v in result['sections'].values()),
    }

    conn.close()
    return result


def trace_formula(formula_id):
    """Full provenance: formula → concealment → restoration → root."""
    conn = _connect()

    result = {'formula_id': formula_id}

    # Try restoration table
    row = conn.execute("SELECT * FROM formula_restoration WHERE formula_id=?", (formula_id,)).fetchone()
    if row:
        result['restoration'] = dict(row)

    # Try concealment
    concealment = _safe_query(conn,
        'SELECT * FROM formula_concealment WHERE conceal_id=? OR content LIKE ?',
        (formula_id, f'%{formula_id}%'))
    if concealment:
        result['concealment'] = [dict(r) for r in concealment]

    # Cross-refs for this formula
    xrefs = _safe_query(conn,
        'SELECT * FROM formula_cross_refs WHERE source_id=? OR target_id=?',
        (formula_id, formula_id))
    if xrefs:
        result['cross_refs'] = [dict(r) for r in xrefs]

    conn.close()
    return result


def ratio_analysis(ratio_id=None, category=None):
    """Ratio analysis — divine fraction vs western constant.

    Args:
        ratio_id: specific ratio ID
        category: filter by category (e.g., 'geometry', 'astronomy')
    """
    conn = _connect()

    if ratio_id:
        rows = _safe_query(conn, 'SELECT * FROM formula_ratios WHERE ratio_id=?', (ratio_id,))
    elif category:
        rows = _safe_query(conn, 'SELECT * FROM formula_ratios WHERE LOWER(category) LIKE ?',
                          (f'%{category.lower()}%',))
    else:
        rows = _safe_query(conn, 'SELECT * FROM formula_ratios LIMIT 50')

    result = {
        'count': len(rows),
        'ratios': [dict(r) for r in rows],
    }

    conn.close()
    return result


def concealment_chain(formula_id):
    """How a formula was hidden — mechanism + DP codes."""
    conn = _connect()

    rows = _safe_query(conn,
        'SELECT * FROM formula_concealment WHERE conceal_id=? OR content LIKE ?',
        (formula_id, f'%{formula_id}%'))

    result = {
        'formula_id': formula_id,
        'chain': [dict(r) for r in rows],
        'mechanisms': list(set(r['mechanism'] for r in rows if r.get('mechanism'))),
        'dp_codes': list(set(r['detection_pattern'] for r in rows if r.get('detection_pattern'))),
    }

    conn.close()
    return result


def formula_scholars_for_root(root_ref):
    """Scholars who worked on formulas for this root."""
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    rows = _safe_query(conn,
        'SELECT * FROM formula_scholars WHERE root_letters=?', (root_letters,))

    conn.close()
    return {
        'root_id': root_id,
        'scholars': [dict(r) for r in rows],
    }


def formula_stats():
    """Statistics for all formula tables."""
    conn = _connect()
    stats = {}
    for tbl in FORMULA_TABLES:
        try:
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            quf = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_pass='TRUE'").fetchone()[0]
            stats[tbl] = {'rows': cnt, 'quf_pass': quf}
        except:
            pass
    conn.close()
    total = sum(d['rows'] for d in stats.values())
    return {'tables': len(stats), 'total_rows': total, 'detail': stats}


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def formula_quf(data: dict) -> dict:
    """
    FORMULA QUF — L11.
    Q: mathematical relationship verified + root present + fields populated
    U: al-Khorezmi / ibn Sina attestation + cross-formula consistency
    F: concealment documented + restoration proven
    """
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    root = data.get('root_letters', '') or data.get('aa_root', '') or ''
    arabic = data.get('arabic', '') or data.get('arabic_term', '') or ''
    qur_ref = data.get('quranic_ref', '') or data.get('qur_ref', '') or ''
    scholar = data.get('scholar', '') or data.get('scholar_name', '') or ''
    concealment = data.get('concealment_method', '') or data.get('concealment_type', '') or ''
    restoration = data.get('restoration_path', '') or data.get('correct_form', '') or ''

    # Count populated fields
    populated = len([v for v in data.values() if v is not None and str(v).strip()])
    total = max(len(data), 1)
    ratio = populated / total

    # Q: evidence quantity
    q_items = sum([bool(root), bool(arabic), bool(qur_ref), ratio >= 0.5])
    q = 'HIGH' if q_items >= 3 else ('MEDIUM' if q_items >= 2 else ('LOW' if q_items >= 1 else 'FAIL'))
    q_ev = [f'root={bool(root)}, arabic={bool(arabic)}, qur_ref={bool(qur_ref)}, fill={ratio:.0%}']

    # U: scholar attestation
    approved_scholars = {'khorezmi', 'khwarizmi', 'خوارزمي', 'ibn sina', 'ابن سينا',
                         'biruni', 'بيروني', 'tusi', 'طوسي', 'kashi', 'كاشي'}
    scholar_match = any(s in str(scholar).lower() for s in approved_scholars) if scholar else False
    u = 'HIGH' if (scholar_match and qur_ref) else ('MEDIUM' if scholar_match or qur_ref else 'LOW')
    u_ev = [f'Scholar: {scholar[:30] if scholar else "none"}, approved={scholar_match}']

    # F: concealment documented + restoration
    if concealment and restoration:
        f = 'HIGH'
        f_ev = [f'Concealment + restoration documented']
    elif concealment or restoration:
        f = 'MEDIUM'
        f_ev = [f'Partial: concealment={bool(concealment)}, restoration={bool(restoration)}']
    elif ratio >= 0.5:
        f = 'MEDIUM'
        f_ev = [f'Fields populated but no concealment/restoration chain']
    else:
        f = 'LOW'
        f_ev = [f'Incomplete data']

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev, 'u_evidence': u_ev, 'f_evidence': f_ev,
    }


def formula_xref_quf(data: dict) -> dict:
    """FORMULA CROSS-REF QUF — L11 cross-references between formula tables."""
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    source_id = data.get('source_id', '') or ''
    target_id = data.get('target_id', '') or ''
    relationship = data.get('relationship', '') or ''
    source_table = data.get('source_table', '') or ''
    target_table = data.get('target_table', '') or ''
    notes = data.get('notes', '') or ''

    q = 'HIGH' if (source_id and target_id and relationship) else ('MEDIUM' if source_id and target_id else 'LOW')
    u = 'HIGH' if (source_table and target_table and relationship) else ('MEDIUM' if relationship else 'LOW')
    f = 'HIGH' if notes else ('MEDIUM' if relationship else 'LOW')

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': [f'source={source_id}, target={target_id}, rel={relationship[:20]}'],
        'u_evidence': [f'{source_table} → {target_table}'],
        'f_evidence': [f'notes={bool(notes)}'],
    }


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 amr_hisab.py <command> [args]")
        print("  expand <root>       — formulas for root")
        print("  trace <formula_id>  — formula provenance")
        print("  ratios [category]   — ratio analysis")
        print("  scholars <root>     — scholars for root")
        print("  stats               — formula statistics")
        sys.exit(0)

    cmd = args[0]
    import json
    if cmd == 'expand' and len(args) > 1:
        print(json.dumps(expand_root_formula(args[1]), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'trace' and len(args) > 1:
        print(json.dumps(trace_formula(args[1]), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'ratios':
        cat = args[1] if len(args) > 1 else None
        r = ratio_analysis(category=cat)
        print(f"Ratios: {r['count']}")
        for ratio in r['ratios'][:10]:
            print(f"  {ratio.get('ratio_id','?')}: {ratio.get('content','')[:60]}")
    elif cmd == 'scholars' and len(args) > 1:
        print(json.dumps(formula_scholars_for_root(args[1]), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'stats':
        r = formula_stats()
        print(f"Formula: {r['tables']} tables, {r['total_rows']} rows")
        for tbl, d in r['detail'].items():
            print(f"  {tbl:<35} {d['rows']:>4} rows, {d['quf_pass']:>4} QUF")
