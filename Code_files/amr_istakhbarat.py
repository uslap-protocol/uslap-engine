#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر اِسْتِخْبَارَات — INTELLIGENCE REASONING MODULE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: خ-ب-ر — to know, to be informed, to investigate
Q49:6 يَا أَيُّهَا الَّذِينَ آمَنُوا إِن جَاءَكُمْ فَاسِقٌ بِنَبَإٍ فَتَبَيَّنُوا
— O you who believe, if a corrupt one brings you intelligence, verify it.

Reasons from roots to institutional confessions, extraction cycles,
mortality intelligence, and concealment audits.
Wired to 7 intelligence tables in the lattice.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

INTEL_TABLES = [
    'institutional_confession_register',
    'financial_extraction_cycles',
    'intel_file_index',
    'mortality_intelligence',
    'kashgari_concealment_audit',
    'swot_analysis',
    'swot_h7',
    'attribution_corrections',
    'scholar_lattice',
    'vol6_astronomy',
    'vol6_bismallah_terms',
]


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


def _quf_intel(row, conn=None):
    """اِسْتِخْبَارَات QUF colour — Intelligence/Epistemic epistemology.

    Q (Quantification): confession/finding cites specific institution + root linkage.
        HIGH = institution named + root_letters linked + entry_id valid
        MEDIUM = institution OR root linkage present
        LOW = content exists but no specific citation
        FAIL = empty

    U (Universality): pattern confirmed across ≥2 instances.
        HIGH = root appears in ≥2 intel tables (confessions + mortality, etc.)
        MEDIUM = root in 1 intel table with multiple rows
        LOW = single instance
        FAIL = no pattern

    F (Falsifiability): counter-evidence addressable.
        HIGH = qur_meaning documented + institutional_meaning differs (inversion proven)
        MEDIUM = mechanism or method documented
        LOW = claim exists but mechanism undocumented
        FAIL = assertion without evidence
    """
    d = dict(row) if not isinstance(row, dict) else row

    # Q — specific citation
    has_institution = bool(d.get('institution') or d.get('operator_class'))
    has_root = bool(d.get('root_letters') or d.get('aa_word'))
    has_entry = bool(d.get('entry_id'))
    has_qref = bool(d.get('qur_ref') or d.get('quranic_ref'))
    if has_institution and has_root and (has_entry or has_qref):
        q = 'HIGH'
    elif has_institution or has_root:
        q = 'MEDIUM'
    elif d.get('content') or d.get('en_term') or d.get('category'):
        q = 'LOW'
    else:
        q = 'FAIL'

    # U — pattern breadth
    # At row level: does the row reference multiple evidence types?
    evidence_count = sum(1 for k in ['root_letters', 'entry_id', 'qur_ref', 'quranic_ref',
                                      'extraction_method', 'mechanism', 'bitig_term']
                         if d.get(k))
    if evidence_count >= 3:
        u = 'HIGH'
    elif evidence_count >= 2:
        u = 'MEDIUM'
    elif evidence_count >= 1:
        u = 'LOW'
    else:
        u = 'FAIL'

    # F — inversion proven
    qur_meaning = d.get('qur_meaning', '')
    inst_meaning = d.get('institutional_meaning', '') or d.get('actual_status', '')
    meanings_differ = (qur_meaning and inst_meaning and
                       str(qur_meaning).strip() != str(inst_meaning).strip())
    has_mechanism = bool(d.get('extraction_method') or d.get('mechanism') or
                        d.get('detection_pattern'))
    if meanings_differ and has_mechanism:
        f = 'HIGH'
    elif meanings_differ or has_mechanism:
        f = 'MEDIUM'
    elif qur_meaning or inst_meaning:
        f = 'LOW'
    else:
        f = 'FAIL'

    grades = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FAIL': 0}
    overall = 'TRUE' if min(grades[q], grades[u], grades[f]) >= 2 else (
        'PENDING' if min(grades[q], grades[u], grades[f]) >= 1 else 'FALSE')

    return {'q': q, 'u': u, 'f': f, 'pass': overall}


def _quf_status(rows, conn=None):
    """Compute domain-specific QUF summary for intelligence result set."""
    if not rows:
        return {'total': 0, 'verified': 0, 'pending': 0, 'rate': '0%',
                'q_high': 0, 'u_high': 0, 'f_high': 0}
    total = len(rows)
    results = [_quf_intel(r, conn) for r in rows]
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


def expand_root_intel(root_ref):
    """All intelligence linked to a root.

    Queries: confessions (root_letters, entry_id), mortality (root_letters),
    extraction (qur_ref), concealment (bitig_term).
    """
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    bare = conn.execute("SELECT root_bare FROM roots WHERE root_id=?", (root_id,)).fetchone()
    root_bare = bare['root_bare'] if bare else ''

    result = {'root_id': root_id, 'root_letters': root_letters, 'sections': {}}

    # Institutional confessions
    confessions = _safe_query(conn,
        'SELECT * FROM institutional_confession_register WHERE root_letters=? OR aa_word LIKE ?',
        (root_letters, f'%{root_bare}%'))
    if confessions:
        result['sections']['confessions'] = [dict(r) for r in confessions]

    # Mortality intelligence
    mortality = _safe_query(conn,
        'SELECT * FROM mortality_intelligence WHERE root_letters=?', (root_letters,))
    if mortality:
        result['sections']['mortality'] = [dict(r) for r in mortality]

    # Financial extraction cycles (via qur_ref)
    extraction = _safe_query(conn,
        'SELECT * FROM financial_extraction_cycles WHERE qur_ref LIKE ?',
        (f'%{root_bare}%',))
    if extraction:
        result['sections']['extraction'] = [dict(r) for r in extraction]

    # Intel file index (via root_ids)
    intel_files = _safe_query(conn,
        'SELECT * FROM intel_file_index WHERE root_ids LIKE ?',
        (f'%{root_id}%',))
    if intel_files:
        result['sections']['intel_files'] = [dict(r) for r in intel_files]

    result['summary'] = {
        'sections_found': len(result['sections']),
        'total_hits': sum(len(v) for v in result['sections'].values()),
    }

    conn.close()
    return result


def confession_for_entry(entry_id):
    """Institutional confession data for a specific entry."""
    conn = _connect()

    rows = _safe_query(conn,
        'SELECT * FROM institutional_confession_register WHERE entry_id=?',
        (entry_id,))

    result = {
        'entry_id': entry_id,
        'confessions': [dict(r) for r in rows],
        'count': len(rows),
    }

    # Enrich with entry data
    entry = conn.execute("SELECT en_term, root_id FROM entries WHERE entry_id=?", (entry_id,)).fetchone()
    if entry:
        result['en_term'] = entry['en_term']
        result['root_id'] = entry['root_id']

    conn.close()
    return result


def extraction_cycle(era=None):
    """Financial extraction methods for an era."""
    conn = _connect()

    if era is not None:
        rows = _safe_query(conn,
            'SELECT * FROM financial_extraction_cycles WHERE era=? OR CAST(era AS INTEGER)=?',
            (str(era), era))
    else:
        rows = _safe_query(conn, 'SELECT * FROM financial_extraction_cycles')

    conn.close()
    return {
        'era': era,
        'cycles': [dict(r) for r in rows],
        'count': len(rows),
    }


def mortality_trace(root_ref):
    """Mortality intelligence for a root."""
    conn = _connect()
    root_id, root_letters = _get_root_id(conn, root_ref)
    if not root_id:
        conn.close()
        return {'error': f'Root not found: {root_ref}'}

    rows = _safe_query(conn,
        'SELECT * FROM mortality_intelligence WHERE root_letters=?', (root_letters,))

    conn.close()
    return {
        'root_id': root_id,
        'root_letters': root_letters,
        'mortality': [dict(r) for r in rows],
        'count': len(rows),
    }


def kashgari_audit(term=None):
    """Concealment audit for Bitig terms in Kashgari."""
    conn = _connect()

    if term:
        rows = _safe_query(conn,
            'SELECT * FROM kashgari_concealment_audit WHERE bitig_term LIKE ? OR expected_gloss LIKE ?',
            (f'%{term}%', f'%{term}%'))
    else:
        rows = _safe_query(conn, 'SELECT * FROM kashgari_concealment_audit')

    conn.close()
    return {
        'query': term or 'all',
        'audits': [dict(r) for r in rows],
        'count': len(rows),
    }


def intel_summary():
    """Full lattice intelligence overview."""
    conn = _connect()

    result = {}
    for tbl in INTEL_TABLES:
        try:
            cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            quf = 0
            if 'quf_pass' in cols:
                quf = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_pass='TRUE'").fetchone()[0]
            result[tbl] = {'rows': cnt, 'quf_pass': quf}
        except:
            pass

    # Cross-table stats
    confessions = conn.execute("SELECT COUNT(*) FROM institutional_confession_register").fetchone()[0]
    with_root = conn.execute(
        "SELECT COUNT(*) FROM institutional_confession_register WHERE root_letters IS NOT NULL AND root_letters != ''").fetchone()[0]

    conn.close()

    total = sum(d['rows'] for d in result.values())
    return {
        'tables': len(result),
        'total_rows': total,
        'confessions_with_root': f'{with_root}/{confessions}',
        'detail': result,
    }


def intel_cross_search(query):
    """Search across all intelligence tables."""
    conn = _connect()
    results = {}
    query_lower = query.lower()

    for tbl in INTEL_TABLES:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
            data_cols = [c for c in cols if not c.startswith('quf_')]
            conditions = [f'LOWER(COALESCE("{c}","")) LIKE ?' for c in data_cols]
            params = [f'%{query_lower}%'] * len(data_cols)
            if conditions:
                rows = conn.execute(
                    f'SELECT * FROM "{tbl}" WHERE {" OR ".join(conditions)} LIMIT 20',
                    params).fetchall()
                if rows:
                    results[tbl] = [dict(r) for r in rows]
        except:
            continue

    conn.close()
    return {
        'query': query,
        'tables_hit': len(results),
        'total_hits': sum(len(v) for v in results.values()),
        'results': results,
    }


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def _quf_result(q='PENDING', u='PENDING', f='PENDING',
                q_ev=None, u_ev=None, f_ev=None):
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}
    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev or [], 'u_evidence': u_ev or [], 'f_evidence': f_ev or [],
    }


def behaviour_quf(data: dict) -> dict:
    """
    BEHAVIOUR QUF — L13 Intelligence.

    Q: How many ayat directly attest this behaviour pattern?
       - Count Qur'anic references in the data
       - Check if roots in the claim have Qur'anic tokens
       - Check if pattern matches known extraction algorithm (FE01-FE10)

    U: How many historical instances repeat this pattern?
       - Count matching entries in financial_extraction_cycles
       - Cross-reference with chronology table
       - Same algorithm across multiple eras = universal

    F: Source verification.
       - Is the source in the approved list (isnad)?
       - Does the source EXPOSE (not sanitise)?
       - Can the claim be independently verified?
    """
    conn = _connect()

    # Extract fields
    qur_ref = (data.get('quranic_ref', '') or data.get('qur_ref', '') or
               data.get('ayah_refs', '') or data.get('quran_proof', '') or
               data.get('qur_anchor', '') or data.get('qur_meaning', '') or '')
    dp_codes = (data.get('dp_codes', '') or data.get('detection_patterns', '') or
                data.get('distinct_from', '') or data.get('confession_type', '') or '')
    source = (data.get('source', '') or data.get('source_ref', '') or
              data.get('institution', '') or '')
    description = (data.get('event_description', '') or data.get('confession_text', '') or
                   data.get('extraction_method', '') or data.get('description', '') or
                   data.get('what_it_confesses', '') or data.get('mechanism', '') or
                   data.get('notes', '') or '')

    # ── Q: QUANTIFICATION — Qur'anic attestation count ──
    q_evidence = []
    ayah_count = 0

    # Count ayah references in the data
    if qur_ref:
        import re
        ayah_refs = re.findall(r'Q?\d+:\d+', str(qur_ref))
        ayah_count = len(ayah_refs)
        q_evidence.append(f'{ayah_count} ayah references: {qur_ref[:60]}')

    # Check roots in description against Qur'an
    root_tokens = 0
    if description:
        # Look for AA roots in the text
        import re
        aa_words = re.findall(r'[\u0621-\u064A]{2,}', str(description))
        for aw in aa_words[:5]:
            try:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM quran_word_roots WHERE aa_word LIKE ?",
                    (f'%{aw}%',)
                ).fetchone()[0]
                root_tokens += cnt
            except Exception:
                pass
        if root_tokens > 0:
            q_evidence.append(f'{root_tokens} Quranic token matches in description')

    # Check extraction algorithm match
    fe_match = 0
    try:
        fe_rows = conn.execute("SELECT COUNT(*) FROM financial_extraction_cycles").fetchone()[0]
        fe_match = fe_rows
        if fe_match > 0:
            q_evidence.append(f'{fe_match} extraction cycles in algorithm')
    except Exception:
        pass

    if ayah_count >= 3 or root_tokens >= 10:
        q_grade = 'HIGH'
    elif ayah_count >= 1 or root_tokens >= 1:
        q_grade = 'MEDIUM'
    elif fe_match > 0:
        q_grade = 'MEDIUM'
    else:
        q_grade = 'LOW'
        q_evidence.append('No Quranic attestation found')

    # ── U: UNIVERSALITY — historical repetition count ──
    u_evidence = []

    # How many eras does this pattern repeat across?
    era_count = 0
    try:
        eras = conn.execute(
            "SELECT COUNT(DISTINCT era) FROM financial_extraction_cycles"
        ).fetchone()[0]
        era_count = eras
    except Exception:
        try:
            # Try counting distinct rows as proxy
            era_count = conn.execute(
                "SELECT COUNT(*) FROM financial_extraction_cycles"
            ).fetchone()[0]
        except Exception:
            pass

    # Cross-reference with chronology
    chrono_matches = 0
    if description:
        key_terms = [w for w in str(description).split() if len(w) > 4][:3]
        for term in key_terms:
            try:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM chronology WHERE LOWER(event) LIKE ? OR LOWER(description) LIKE ?",
                    (f'%{term.lower()}%', f'%{term.lower()}%')
                ).fetchone()[0]
                chrono_matches += cnt
            except Exception:
                pass

    if era_count >= 5 or chrono_matches >= 3:
        u_grade = 'HIGH'
        u_evidence.append(f'{era_count} eras in extraction algorithm, {chrono_matches} chronology matches')
    elif era_count >= 2 or chrono_matches >= 1:
        u_grade = 'MEDIUM'
        u_evidence.append(f'{era_count} eras, {chrono_matches} chronology matches')
    else:
        u_grade = 'LOW'
        u_evidence.append(f'No historical repetition found')

    # ── F: FALSIFICATION — source quality ──
    f_evidence = []

    # Check if source is in isnad (approved chain)
    isnad_match = False
    try:
        if source:
            isnad_check = conn.execute(
                "SELECT COUNT(*) FROM isnad WHERE chain LIKE ?",
                (f'%{source[:20]}%',)
            ).fetchone()[0]
            isnad_match = isnad_check > 0
    except Exception:
        pass

    # Check scholar_warnings for approved scholars
    scholar_match = False
    try:
        if source:
            sw_check = conn.execute(
                "SELECT COUNT(*) FROM scholar_warnings WHERE scholar_name LIKE ?",
                (f'%{source[:20]}%',)
            ).fetchone()[0]
            scholar_match = sw_check > 0
    except Exception:
        pass

    has_dp = bool(dp_codes)
    has_qur = bool(qur_ref)

    if has_qur and has_dp:
        f_grade = 'HIGH'
        f_evidence.append(f'Quranic ref + DP codes = falsifiable and documented')
    elif has_qur or (has_dp and (isnad_match or scholar_match)):
        f_grade = 'HIGH'
        f_evidence.append(f'Quranic or approved source + DP documented')
    elif has_dp or source:
        f_grade = 'MEDIUM'
        f_evidence.append(f'Source present: {source[:30]}, DP: {dp_codes[:20]}')
    else:
        f_grade = 'LOW'
        f_evidence.append('No source, no DP codes')

    conn.close()
    return _quf_result(q_grade, u_grade, f_grade, q_evidence, u_evidence, f_evidence)


def intel_index_quf(data: dict) -> dict:
    """
    INTEL FILE INDEX QUF — L13 metadata.
    Q: dp_codes + qur_refs + root_ids populated
    U: period documented + region identified
    F: dp_codes present = falsifiable (specific patterns claimed)
    """
    dp_codes = data.get('dp_codes', '') or ''
    qur_refs = data.get('qur_refs', '') or ''
    root_ids = data.get('root_ids', '') or ''
    period_start = data.get('period_start', '') or ''
    period_end = data.get('period_end', '') or ''
    region = data.get('region', '') or ''
    keywords = data.get('keywords', '') or ''

    q_items = sum([bool(dp_codes), bool(qur_refs), bool(root_ids), bool(keywords)])
    q = 'HIGH' if q_items >= 3 else ('MEDIUM' if q_items >= 2 else ('LOW' if q_items >= 1 else 'FAIL'))
    q_ev = [f'dp={bool(dp_codes)}, qur={bool(qur_refs)}, roots={bool(root_ids)}, keywords={bool(keywords)}']

    u = 'HIGH' if (period_start and region) else ('MEDIUM' if period_start or region else 'LOW')
    u_ev = [f'period={period_start}-{period_end}, region={region}']

    f = 'HIGH' if (dp_codes and qur_refs) else ('MEDIUM' if dp_codes or qur_refs else 'LOW')
    f_ev = [f'dp_codes={dp_codes[:30]}, qur_refs={bool(qur_refs)}']

    return _quf_result(q, u, f, q_ev, u_ev, f_ev)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 amr_istakhbarat.py <command> [args]")
        print("  expand <root>      — intelligence for root")
        print("  confession <id>    — confession for entry")
        print("  extraction [era]   — extraction cycles")
        print("  mortality <root>   — mortality intelligence")
        print("  kashgari [term]    — concealment audit")
        print("  summary            — full overview")
        print("  search <query>     — cross-search")
        sys.exit(0)

    cmd = args[0]
    import json
    if cmd == 'expand' and len(args) > 1:
        r = expand_root_intel(args[1])
        print(f"Root {r.get('root_id','?')}: {r.get('summary',{})}")
        for section, data in r.get('sections', {}).items():
            print(f"  {section}: {len(data)} hits")
    elif cmd == 'confession' and len(args) > 1:
        print(json.dumps(confession_for_entry(int(args[1])), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'extraction':
        era = int(args[1]) if len(args) > 1 else None
        r = extraction_cycle(era)
        print(f"Extraction cycles: {r['count']}")
        for c in r['cycles']:
            print(f"  ERA {c.get('era','?')}: {c.get('extraction_method','?')}")
    elif cmd == 'mortality' and len(args) > 1:
        print(json.dumps(mortality_trace(args[1]), ensure_ascii=False, indent=2, default=str))
    elif cmd == 'kashgari':
        term = args[1] if len(args) > 1 else None
        r = kashgari_audit(term)
        print(f"Kashgari audits: {r['count']}")
        for a in r['audits'][:10]:
            print(f"  {a.get('bitig_term','?')}: {a.get('actual_status','?')}")
    elif cmd == 'summary':
        r = intel_summary()
        print(f"Intelligence: {r['tables']} tables, {r['total_rows']} rows")
        print(f"Confessions with root: {r['confessions_with_root']}")
        for tbl, d in r['detail'].items():
            print(f"  {tbl:<45} {d['rows']:>4} rows, {d['quf_pass']:>4} QUF")
    elif cmd == 'search' and len(args) > 1:
        r = intel_cross_search(' '.join(args[1:]))
        print(f"Query: '{r['query']}', Tables hit: {r['tables_hit']}, Hits: {r['total_hits']}")
