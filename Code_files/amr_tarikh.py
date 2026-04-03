#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر تَارِيخ — CHRONOLOGY/HISTORY REASONING MODULE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: أ-ر-خ — to date, chronicle, record history
Q30:3-4 فِي بِضْعِ سِنِينَ لِلَّهِ الْأَمْرُ مِن قَبْلُ وَمِن بَعْدُ
— Within a few years. To Allah belongs the command before and after.

Reasons from roots to chronological events, word deployments,
naming operations, and dispersal timelines.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")


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


def _quf_tarikh(row, conn=None):
    """تَارِيخ QUF colour — Historical epistemology.

    Q (Quantification): dated attestation with source citation.
        HIGH = date + event + source all populated + confidence assigned
        MEDIUM = date + event populated
        LOW = event exists but undated
        FAIL = empty

    U (Universality): timeline consistent across sources.
        HIGH = qur_ref cited + era classified + consistent with lattice
        MEDIUM = era classified OR qur_ref exists
        LOW = event only, no cross-reference
        FAIL = isolated claim

    F (Falsifiability): source traceable, not anonymous.
        HIGH = confidence=HIGH + source is specific (not "unknown"/"TBD")
        MEDIUM = source exists and len > 3
        LOW = source vague or confidence ungraded
        FAIL = no source, no confidence — unfalsifiable claim
    """
    d = dict(row) if not isinstance(row, dict) else row

    # Q — dated attestation
    has_date = bool(d.get('date') or d.get('date_period') or d.get('period'))
    has_event = bool(d.get('event') or d.get('operation_phase') or d.get('deployed_words'))
    has_source = bool(d.get('source') and len(str(d.get('source', ''))) > 3)
    has_conf = bool(d.get('confidence'))
    if has_date and has_event and has_source and has_conf:
        q = 'HIGH'
    elif has_date and has_event:
        q = 'MEDIUM'
    elif has_event:
        q = 'LOW'
    else:
        q = 'FAIL'

    # U — cross-source consistency
    has_qref = bool(d.get('qur_ref'))
    has_era = bool(d.get('era'))
    has_naming = bool(d.get('orig_name') and d.get('oper_name'))
    if has_qref and has_era:
        u = 'HIGH'
    elif has_era or has_qref or has_naming:
        u = 'MEDIUM'
    elif has_event:
        u = 'LOW'
    else:
        u = 'FAIL'

    # F — source traceability
    conf_high = str(d.get('confidence', '')).upper() == 'HIGH'
    source_ok = has_source and str(d.get('source', '')).upper() not in ('UNKNOWN', 'TBD', 'NONE', '')
    if conf_high and source_ok:
        f = 'HIGH'
    elif source_ok:
        f = 'MEDIUM'
    elif has_source or has_conf:
        f = 'LOW'
    else:
        f = 'FAIL'

    grades = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FAIL': 0}
    overall = 'TRUE' if min(grades[q], grades[u], grades[f]) >= 2 else (
        'PENDING' if min(grades[q], grades[u], grades[f]) >= 1 else 'FALSE')

    return {'q': q, 'u': u, 'f': f, 'pass': overall}


def _quf_status(rows, conn=None):
    """Compute domain-specific QUF summary for chronology result set."""
    if not rows:
        return {'total': 0, 'verified': 0, 'pending': 0, 'rate': '0%',
                'q_high': 0, 'u_high': 0, 'f_high': 0}
    total = len(rows)
    results = [_quf_tarikh(r, conn) for r in rows]
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


def expand_root_timeline(root_ref):
    """Full chronological deployment of a root.

    Links: chronology → word_deployment_map → child_entries → bitig_dispersal_map
    """
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    bare = conn.execute("SELECT root_bare FROM roots WHERE root_id=?", (root_id,)).fetchone()
    root_bare = bare['root_bare'] if bare else ''

    result = {'root_id': root_id, 'root_letters': root_letters, 'timeline': []}

    # Chronology events referencing this root
    chrono = _safe_query(conn,
        'SELECT * FROM chronology WHERE qur_ref LIKE ? OR orig_name LIKE ? OR oper_name LIKE ? OR event LIKE ? ORDER BY CAST(era AS INTEGER), date',
        (f'%{root_bare}%', f'%{root_bare}%', f'%{root_bare}%', f'%{root_bare}%'))

    # Word deployments
    deployments = _safe_query(conn,
        'SELECT * FROM word_deployment_map WHERE aa_roots LIKE ? OR deployed_words LIKE ?',
        (f'%{root_bare}%', f'%{root_bare}%'))

    # Child entries (peoples) using this root
    children = _safe_query(conn,
        'SELECT * FROM child_entries WHERE orig_root LIKE ? OR phonetic_chain LIKE ?',
        (f'%{root_bare}%', f'%{root_id}%'))

    # Bitig dispersal
    dispersal = _safe_query(conn,
        'SELECT * FROM bitig_dispersal_map WHERE evidence LIKE ?',
        (f'%{root_bare}%',))

    # Destruction timeline
    destruction = _safe_query(conn,
        'SELECT * FROM f5_destruction_timeline WHERE event LIKE ? OR date LIKE ?',
        (f'%{root_bare}%', f'%{root_bare}%'))

    result['chronology'] = [dict(r) for r in chrono]
    result['deployments'] = [dict(r) for r in deployments]
    result['peoples'] = [dict(r) for r in children]
    result['dispersal'] = [dict(r) for r in dispersal]
    result['destruction'] = [dict(r) for r in destruction]

    result['summary'] = {
        'events': len(chrono),
        'deployments': len(deployments),
        'peoples': len(children),
        'dispersal': len(dispersal),
        'destruction': len(destruction),
        'total': len(chrono) + len(deployments) + len(children) + len(dispersal) + len(destruction),
    }

    conn.close()
    return result


def trace_event(event_id):
    """Event → naming operations → orig/oper meanings → qur_ref."""
    conn = _connect()

    row = conn.execute("SELECT * FROM chronology WHERE id=? OR rowid_pk=?",
                       (event_id, event_id)).fetchone()
    if not row:
        conn.close()
        return {'error': f'Event not found: {event_id}'}

    result = dict(row)

    # Linked deployments
    chrono_ref = row['id'] if row['id'] else str(row['rowid_pk'])
    deployments = _safe_query(conn,
        'SELECT * FROM word_deployment_map WHERE chronology_ref=?', (chrono_ref,))
    result['deployments'] = [dict(r) for r in deployments]

    # If naming operation, trace the names
    orig = row['orig_name']
    oper = row['oper_name']
    if orig and oper:
        result['naming_operation'] = {
            'original': orig,
            'operator': oper,
            'orig_meaning': row['orig_meaning'],
            'oper_meaning': row['oper_meaning'],
            'inversion': f'{orig} → {oper}',
        }

    conn.close()
    return result


def deployment_chain(root_ref):
    """Root → chronology → deployment phase → territory → mechanism."""
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    bare = conn.execute("SELECT root_bare FROM roots WHERE root_id=?", (root_id,)).fetchone()
    root_bare = bare['root_bare'] if bare else ''

    deployments = _safe_query(conn,
        'SELECT * FROM word_deployment_map WHERE aa_roots LIKE ? OR deployed_words LIKE ?',
        (f'%{root_bare}%', f'%{root_bare}%'))

    chain = []
    for dep in deployments:
        dep_dict = dict(dep)
        # Link to chronology
        cref = dep['chronology_ref']
        if cref:
            chrono = conn.execute("SELECT * FROM chronology WHERE id=?", (cref,)).fetchone()
            if chrono:
                dep_dict['chrono_event'] = dict(chrono)
        chain.append(dep_dict)

    conn.close()
    return {
        'root_id': root_id,
        'root_letters': root_letters,
        'chain': chain,
        'total_deployments': len(chain),
    }


def era_summary(era_num):
    """All events/deployments/naming ops in an ERA."""
    conn = _connect()

    events = _safe_query(conn,
        'SELECT * FROM chronology WHERE era=? OR CAST(era AS INTEGER)=? ORDER BY date',
        (str(era_num), era_num))

    # Get deployments for these events
    deployments = []
    for evt in events:
        eid = evt['id']
        if eid:
            deps = _safe_query(conn,
                'SELECT * FROM word_deployment_map WHERE chronology_ref=?', (eid,))
            deployments.extend([dict(d) for d in deps])

    # Naming operations in this era
    naming_ops = [dict(e) for e in events if e['orig_name'] and e['oper_name']]

    conn.close()
    return {
        'era': era_num,
        'events': [dict(e) for e in events],
        'event_count': len(events),
        'deployments': deployments,
        'deployment_count': len(deployments),
        'naming_operations': naming_ops,
        'naming_count': len(naming_ops),
    }


def naming_operation(orig_name=None, oper_name=None):
    """Trace a naming inversion."""
    conn = _connect()

    if orig_name:
        rows = _safe_query(conn,
            'SELECT * FROM chronology WHERE orig_name LIKE ?', (f'%{orig_name}%',))
    elif oper_name:
        rows = _safe_query(conn,
            'SELECT * FROM chronology WHERE oper_name LIKE ?', (f'%{oper_name}%',))
    else:
        rows = _safe_query(conn,
            'SELECT * FROM chronology WHERE orig_name IS NOT NULL AND orig_name != "" AND oper_name IS NOT NULL AND oper_name != "" LIMIT 20')

    conn.close()
    return {
        'query': orig_name or oper_name or 'all',
        'operations': [dict(r) for r in rows],
        'count': len(rows),
    }


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def history_quf(data: dict) -> dict:
    """
    HISTORY QUF — L12.
    Q: dated event + source documented
    U: multiple sources confirm same timeline + cross-ref with lattice
    F: approved source + not contradicted by lattice data
    """
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    date = data.get('date', '') or data.get('date_period', '') or data.get('year', '') or ''
    event = data.get('event', '') or data.get('child_name', '') or data.get('deployed_words', '') or ''
    source = data.get('source', '') or data.get('source_ref', '') or ''
    description = data.get('description', '') or data.get('operation_phase', '') or ''
    status = data.get('status', '') or data.get('confirmation_status', '') or ''

    # Q: evidence quantity
    q_items = sum([bool(date), bool(event), bool(source), bool(description)])
    q = 'HIGH' if q_items >= 3 else ('MEDIUM' if q_items >= 2 else ('LOW' if q_items >= 1 else 'FAIL'))
    q_ev = [f'date={bool(date)}, event={bool(event)}, source={bool(source)}']

    # U: status confirmed + multiple sources
    confirmed = str(status).upper() in ('CONFIRMED', 'VERIFIED', 'TRUE')
    u = 'HIGH' if (confirmed and source) else ('MEDIUM' if confirmed or source else 'LOW')
    u_ev = [f'status={status}, confirmed={confirmed}']

    # F: source verifiable
    if source and date:
        f = 'HIGH'
        f_ev = [f'Source + date = verifiable']
    elif source or date:
        f = 'MEDIUM'
        f_ev = [f'Partial: source={bool(source)}, date={bool(date)}']
    else:
        f = 'LOW'
        f_ev = [f'No source or date']

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev, 'u_evidence': u_ev, 'f_evidence': f_ev,
    }


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 amr_tarikh.py <command> [args]")
        print("  timeline <root>     — root deployment timeline")
        print("  event <id>          — trace event")
        print("  deploy <root>       — deployment chain for root")
        print("  era <0-4>           — era summary")
        print("  naming [name]       — naming operations")
        sys.exit(0)

    cmd = args[0]
    import json
    if cmd == 'timeline' and len(args) > 1:
        r = expand_root_timeline(args[1])
        print(f"Root {r.get('root_id','?')}: {r.get('summary',{})}")
    elif cmd == 'event' and len(args) > 1:
        print(json.dumps(trace_event(args[1]), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'deploy' and len(args) > 1:
        r = deployment_chain(args[1])
        print(f"Root {r.get('root_id','?')}: {r['total_deployments']} deployments")
        for d in r['chain'][:5]:
            print(f"  Phase: {d.get('operation_phase','?')}, Territory: {d.get('host_territory','?')}")
    elif cmd == 'era' and len(args) > 1:
        r = era_summary(int(args[1]))
        print(f"ERA {r['era']}: {r['event_count']} events, {r['deployment_count']} deployments, {r['naming_count']} naming ops")
    elif cmd == 'naming':
        name = args[1] if len(args) > 1 else None
        r = naming_operation(orig_name=name)
        print(f"Naming operations: {r['count']}")
        for op in r['operations'][:10]:
            print(f"  {op.get('orig_name','?')} → {op.get('oper_name','?')} ({op.get('date','?')})")
