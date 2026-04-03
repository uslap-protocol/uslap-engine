#!/usr/bin/env python3
"""
USLaP CHAIN EXTRACTION — Extract full phonetic chains, shift IDs, DP codes,
decay levels, and chronology from archived session logs.

Usage:
    python3 extract_chains.py scan     — extract all chain data
    python3 extract_chains.py diff     — compare extracted vs live DB
    python3 extract_chains.py report   — full report with recovery candidates
"""

import re, glob, os, sys, sqlite3
from collections import defaultdict

SESSION_DIR = os.path.expanduser("~/.claude/projects/-Users-mmsetubal-Documents-USLaP-workplace")
DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

# ============================================================
# PATTERNS — extract structured data from session text
# ============================================================

# Phonetic chain: ق→C(S01), ر→R(S15), ن→N(S18)
RE_CHAIN = re.compile(
    r'([^\s,;|]+→[^\s,;|]+\(S\d{2}\)(?:\s*,\s*[^\s,;|]+→[^\s,;|]+\(S\d{2}\))*)'
)

# ORIG2 chain: ORIG2: term → skeleton
RE_ORIG2 = re.compile(r'ORIG2[:\s]+(\S+)\s*→\s*(\S+)')

# Shift IDs: S01, S02, etc
RE_SHIFTS = re.compile(r'\b(S\d{2})\b')

# DP codes: DP01, DP08, etc
RE_DP = re.compile(r'\b(DP\d{2})\b')

# Operations: OP_NASAL, OP_SUFFIX, etc
RE_OPS = re.compile(r'\b(OP_[A-Z_]+)\b')

# Decay level
RE_DECAY = re.compile(r'\b(NEAR|MINIMAL|MEDIUM|HIGH|VERY.HIGH|MAXIMUM|ORGANIC|INSTITUTIONAL)\b')

# Corridor
RE_CORRIDOR = re.compile(r'\b(DS0[1-9]|DS1[0-4]|ORIG2|TYPE[123]|DIRECT)\b')

# Score
RE_SCORE = re.compile(r'score[=:\s]+(\d{1,2})/10|\bscore[=:\s]+(\d{1,2})\b', re.IGNORECASE)

# Pattern (inversion type)
RE_PATTERN = re.compile(r'\bpattern[=:\s]+(A\+?[BCD]?|B\+?[CD]?|C|D)\b', re.IGNORECASE)

# EN term near chain data
RE_EN_TERM = re.compile(r'\b([A-Z]{3,20})\b')

# RU term near chain data
RE_RU_TERM = re.compile(r'\b([А-ЯЁ]{3,20})\b')

# Root assignment
RE_ROOT = re.compile(r'((?:R\d+|T_?(?:BITIG)?\d+))')

# QV reference
RE_QV = re.compile(r'\b(QV\d{1,3})\b')

# Quranic reference
RE_QURAN = re.compile(r'\b(Q\d{1,3}:\d{1,3})\b')

# Chronology reference
RE_CHRONO = re.compile(r'\b(C\d{1,3})\b')

# Network reference
RE_NETWORK = re.compile(r'\b(N\d{2})\b')

# Allah Name reference
RE_ALLAH = re.compile(r'\b(A\d{2})\b')


def extract_entry_data(line):
    """Extract all structured data from a line."""
    data = {}

    chains = RE_CHAIN.findall(line)
    if chains:
        data['phonetic_chain'] = chains[0]  # Take first/best

    orig2 = RE_ORIG2.findall(line)
    if orig2:
        data['orig2_chain'] = f"ORIG2: {orig2[0][0]} → {orig2[0][1]}"

    shifts = list(set(RE_SHIFTS.findall(line)))
    if shifts:
        data['shifts'] = sorted(shifts)

    dps = list(set(RE_DP.findall(line)))
    if dps:
        data['dp_codes'] = sorted(dps)

    ops = list(set(RE_OPS.findall(line)))
    if ops:
        data['ops_applied'] = sorted(ops)

    decay = RE_DECAY.findall(line)
    if decay:
        data['decay_level'] = decay[0]

    corridor = RE_CORRIDOR.findall(line)
    if corridor:
        data['ds_corridor'] = corridor[0]

    score = RE_SCORE.findall(line)
    if score:
        s = score[0][0] or score[0][1]
        if s and 1 <= int(s) <= 10:
            data['score'] = int(s)

    pattern = RE_PATTERN.findall(line)
    if pattern:
        data['pattern'] = pattern[0].upper()

    roots = RE_ROOT.findall(line)
    if roots:
        data['root_ids'] = list(set(roots))

    qv = RE_QV.findall(line)
    if qv:
        data['qv_refs'] = sorted(set(qv))

    quran = RE_QURAN.findall(line)
    if quran:
        data['qur_refs'] = sorted(set(quran))

    chrono = RE_CHRONO.findall(line)
    if chrono:
        # Filter out C01 etc that aren't chrono refs (e.g. hex codes)
        valid = [c for c in chrono if int(c[1:]) <= 200]
        if valid:
            data['chrono_refs'] = sorted(set(valid))

    network = RE_NETWORK.findall(line)
    if network:
        data['network_id'] = sorted(set(network))

    allah = RE_ALLAH.findall(line)
    if allah:
        valid = [a for a in allah if int(a[1:]) <= 99]
        if valid:
            data['allah_name_id'] = sorted(set(valid))

    return data


def find_term_for_data(line, data):
    """Find which term this data belongs to."""
    terms = []

    en_terms = RE_EN_TERM.findall(line)
    # Filter noise
    noise = {'INSERT','UPDATE','SELECT','DELETE','FROM','WHERE','INTO','TABLE',
             'CREATE','ALTER','DROP','TEXT','INTEGER','NULL','PASS','FAIL','TRUE',
             'FALSE','ROOT','ORIG','TYPE','NONE','BITIG','KASHGARI','PATTERN',
             'CHAIN','SCORE','NEAR','MEDIUM','HIGH','MAXIMUM','DIRECT','ORGANIC',
             'INSTITUTIONAL','THE','AND','FOR','NOT','WITH','THIS','THAT','HAS',
             'WAS','ARE','BUT','ALL','CAN','HAD','HER','ONE','OUR','OUT','YOU',
             'QURANIC','ARABIC','SHIFT','ENTRY','QUERY','INDEX','COUNT','CHECK',
             'CORRIDOR','DECAY','LEVEL','PHONETIC','SEMANTIC','COMPOUND','PREFIX',
             'SUFFIX','DERIVATIVE','VERIFIED','WRITTEN','ANALYSED','PENDING',
             'SEARCH','FOUND','MATCH','CONSONANT','VOWEL','RADICAL','TRILITERAL'}
    en_terms = [t for t in en_terms if t not in noise and len(t) >= 3]

    ru_terms = RE_RU_TERM.findall(line)
    ru_noise = {'ЗАПИСИ','БУКВЫ','КОРЕНЬ','СЛОВО','ЗНАЧЕНИЕ','ЗАПИСЬ','ИСТОЧНИК'}
    ru_terms = [t for t in ru_terms if t not in ru_noise and len(t) >= 3]

    return en_terms + ru_terms


def scan_sessions():
    """Extract all chain data from all sessions."""
    files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl")))
    print(f"Scanning {len(files)} sessions...")

    # term -> best chain data (most complete)
    all_data = defaultdict(list)

    for filepath in files:
        session_id = os.path.basename(filepath)[:12]
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        session_count = 0

        try:
            with open(filepath, 'r', errors='ignore') as fh:
                for line in fh:
                    # Only process lines with chain data
                    if not RE_CHAIN.search(line) and not RE_ORIG2.search(line):
                        continue

                    data = extract_entry_data(line)
                    if not data.get('phonetic_chain') and not data.get('orig2_chain'):
                        continue

                    terms = find_term_for_data(line, data)
                    for term in terms:
                        data['session'] = session_id
                        all_data[term].append(dict(data))
                        session_count += 1

            if session_count > 0:
                print(f"  {session_id} ({size_mb:.1f}MB): {session_count} chain extractions")
        except Exception as e:
            continue

    # Deduplicate: keep the most complete data per term
    best = {}
    for term, entries in all_data.items():
        # Score each entry by completeness
        def completeness(d):
            score = 0
            if d.get('phonetic_chain'): score += 10
            if d.get('dp_codes'): score += len(d['dp_codes']) * 3
            if d.get('ops_applied'): score += len(d['ops_applied']) * 2
            if d.get('decay_level'): score += 5
            if d.get('ds_corridor'): score += 5
            if d.get('score'): score += 3
            if d.get('pattern'): score += 3
            if d.get('qur_refs'): score += len(d['qur_refs'])
            if d.get('shifts'): score += len(d['shifts'])
            return score

        entries.sort(key=completeness, reverse=True)
        best[term] = entries[0]

    print(f"\nTotal unique terms with chain data: {len(best)}")
    return best


def diff_against_db(extracted):
    """Compare extracted chain data vs live DB."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Get current DB state
    c.execute("""SELECT entry_id, en_term, ru_term, root_id, phonetic_chain,
                        dp_codes, ops_applied, decay_level, ds_corridor, pattern, score
                 FROM entries""")

    db_entries = {}
    for row in c.fetchall():
        eid, en, ru, rid, chain, dp, ops, decay, corr, pat, score = row
        record = {
            'entry_id': eid, 'root_id': rid, 'phonetic_chain': chain,
            'dp_codes': dp, 'ops_applied': ops, 'decay_level': decay,
            'ds_corridor': corr, 'pattern': pat, 'score': score
        }
        if en: db_entries[en.upper()] = record
        if ru: db_entries[ru.upper()] = record

    conn.close()

    # Categorize
    recoverable = []    # In DB but missing chain data, session has it
    conflicts = []      # Both have data but different
    not_in_db = []      # Term not in DB
    already_complete = [] # DB already has this data

    for term, session_data in extracted.items():
        if term in db_entries:
            db = db_entries[term]

            # Check what's missing in DB that session has
            missing_fields = []
            if not db['phonetic_chain'] and session_data.get('phonetic_chain'):
                missing_fields.append('phonetic_chain')
            if not db['dp_codes'] and session_data.get('dp_codes'):
                missing_fields.append('dp_codes')
            if not db['ops_applied'] and session_data.get('ops_applied'):
                missing_fields.append('ops_applied')
            if not db['decay_level'] and session_data.get('decay_level'):
                missing_fields.append('decay_level')

            if missing_fields:
                recoverable.append({
                    'term': term,
                    'entry_id': db['entry_id'],
                    'missing': missing_fields,
                    'session_data': session_data
                })
            else:
                already_complete.append(term)
        else:
            not_in_db.append({'term': term, 'session_data': session_data})

    return {
        'recoverable': recoverable,
        'conflicts': conflicts,
        'not_in_db': not_in_db,
        'already_complete': already_complete
    }


def report():
    """Full extraction + diff report."""
    print("=" * 80)
    print("USLaP CHAIN DATA RECOVERY REPORT")
    print("=" * 80)

    extracted = scan_sessions()
    results = diff_against_db(extracted)

    print(f"\n{'='*80}")
    print(f"RECOVERABLE: {len(results['recoverable'])} entries have session chain data missing from DB")
    print(f"{'='*80}")

    # Group by missing field
    by_field = defaultdict(int)
    for item in results['recoverable']:
        for f in item['missing']:
            by_field[f] += 1

    print("\nMissing fields breakdown:")
    for field, count in sorted(by_field.items(), key=lambda x: -x[1]):
        print(f"  {field:25s} {count:5d} entries")

    print(f"\nSample recoverable entries:")
    for item in sorted(results['recoverable'], key=lambda x: len(x['missing']), reverse=True)[:30]:
        sd = item['session_data']
        chain = sd.get('phonetic_chain', sd.get('orig2_chain', ''))[:60]
        dps = ','.join(sd.get('dp_codes', []))
        ops = ','.join(sd.get('ops_applied', []))
        decay = sd.get('decay_level', '')
        print(f"  {item['term']:20s} missing={item['missing']}")
        if chain: print(f"    chain: {chain}")
        if dps: print(f"    dp: {dps}")
        if ops: print(f"    ops: {ops}")
        if decay: print(f"    decay: {decay}")

    if len(results['recoverable']) > 30:
        print(f"  ... and {len(results['recoverable']) - 30} more")

    print(f"\n{'='*80}")
    print(f"ALREADY COMPLETE: {len(results['already_complete'])} entries already have chain data in DB")
    print(f"NOT IN DB: {len(results['not_in_db'])} terms found in sessions but not in DB")
    print(f"{'='*80}")

    # Generate SQL for recoverable items
    print(f"\n{'='*80}")
    print("RECOVERY SQL (dry run — not executed)")
    print(f"{'='*80}")

    sql_count = 0
    for item in results['recoverable']:
        sd = item['session_data']
        sets = []
        if 'phonetic_chain' in item['missing'] and sd.get('phonetic_chain'):
            chain = sd['phonetic_chain'].replace("'", "''")
            sets.append(f"phonetic_chain = '{chain}'")
        if 'dp_codes' in item['missing'] and sd.get('dp_codes'):
            dps = ','.join(sd['dp_codes'])
            sets.append(f"dp_codes = '{dps}'")
        if 'ops_applied' in item['missing'] and sd.get('ops_applied'):
            ops = ','.join(sd['ops_applied'])
            sets.append(f"ops_applied = '{ops}'")
        if 'decay_level' in item['missing'] and sd.get('decay_level'):
            sets.append(f"decay_level = '{sd['decay_level']}'")

        if sets:
            sql = f"UPDATE entries SET {', '.join(sets)} WHERE entry_id = {item['entry_id']};"
            print(sql)
            sql_count += 1

    print(f"\n-- Total: {sql_count} UPDATE statements")

    return results


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if cmd == 'scan':
        scan_sessions()
    elif cmd == 'diff':
        extracted = scan_sessions()
        results = diff_against_db(extracted)
        print(f"Recoverable: {len(results['recoverable'])} | Complete: {len(results['already_complete'])} | Not in DB: {len(results['not_in_db'])}")
    elif cmd == 'report':
        report()
    else:
        print(f"Unknown: {cmd}. Use: scan | diff | report")
