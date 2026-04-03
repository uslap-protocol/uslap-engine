#!/usr/bin/env python3
"""
USLaP Full Report — Type-Aware Deep Search

Detects WHAT the term is and structures output accordingly:
  SCHOLAR  → WHO → WORKS → LATTICE PRESENCE → CONTAMINATION
  PEOPLE   → ROOT → QUR'AN → OPERATION → CHRONOLOGY
  ROOT     → LETTERS → QUR'AN → DOWNSTREAM → INVERSIONS
  ENTRY    → ROOT → CHAIN → SIBLINGS → DETECTION
  GENERAL  → flat search all tables

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
import os
import sys
import unicodedata as _ud

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")


def _to_plain(val):
    """Convert diacritical text to plain form for comparison. DB values stay untouched."""
    if val is None:
        return None
    return ''.join(c for c in _ud.normalize('NFD', str(val))
                   if _ud.category(c) != 'Mn').lower()


def generate(text):
    """Generate a type-aware full report for a term."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.create_function("plain", 1, _to_plain)

    term = text.strip()
    term_lower = term.lower()

    # Build search patterns — diacritical bridge (both spellings TRUE)
    patterns = [f"%{term}%", f"%{term_lower}%"]
    stripped = _to_plain(term)
    if stripped and stripped != term_lower:
        patterns.append(f"%{stripped}%")

    def _search(table, columns):
        try:
            existing = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            cols = [c for c in columns if c in existing]
            if not cols:
                return []
            parts, params = [], []
            for col in cols:
                for pat in patterns:
                    parts.append(f"LOWER(CAST([{col}] AS TEXT)) LIKE ?")
                    params.append(pat.lower())
                    parts.append(f"plain(CAST([{col}] AS TEXT)) LIKE ?")
                    params.append(_to_plain(pat))
            rows = conn.execute(
                f"SELECT * FROM [{table}] WHERE {' OR '.join(parts)} LIMIT 100", params
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    # ─── DETECT TYPE ─────────────────────────────────────────────────
    scholar_hits = _search('scholar_warnings',
        ['sc_code', 'scholar', 'aa_name', 'origin', 'century',
         'primary_work', 'warning_content', 'key_contribution_to_lattice'])
    child_hits = _search('child_entries',
        ['child_id', 'shell_name', 'orig_meaning', 'operation_role',
         'shell_meaning', 'orig_root', 'notes'])
    entry_hits = _search('entries',
        ['entry_id', 'en_term', 'aa_word', 'root_letters', 'notes'])
    root_hits = _search('roots',
        ['root_id', 'root_letters', 'primary_meaning'])

    # Type priority: check if term is a DIRECT match on primary name fields
    # This prevents "quraysh" matching scholar notes and being misclassified
    def _is_direct_match(hits, name_fields):
        """Check if any hit has the term as a direct match on a name field."""
        for h in hits:
            for f in name_fields:
                val = _to_plain(h.get(f, '') or '')
                if val and (_to_plain(term) in val or term_lower in val):
                    return True
        return False

    child_direct = _is_direct_match(child_hits, ['shell_name', 'child_id'])
    scholar_direct = _is_direct_match(scholar_hits, ['scholar', 'sc_code', 'aa_name'])
    entry_direct = _is_direct_match(entry_hits, ['en_term'])

    if child_direct:
        rtype = 'PEOPLE'
    elif scholar_direct:
        rtype = 'SCHOLAR'
    elif root_hits:
        rtype = 'ROOT'
    elif entry_direct:
        rtype = 'ENTRY'
    elif scholar_hits:
        rtype = 'SCHOLAR'
    elif child_hits:
        rtype = 'PEOPLE'
    elif entry_hits:
        rtype = 'ENTRY'
    else:
        rtype = 'GENERAL'

    L = []
    total = 0
    L.append("═" * 60)
    L.append(f"FULL REPORT: '{term}' — TYPE: {rtype}")
    L.append("═" * 60)

    # ─── SCHOLAR ─────────────────────────────────────────────────────
    if rtype == 'SCHOLAR':
        sc = scholar_hits[0]
        L.append("")
        L.append("┌─ WHO ─────────────────────────────────────────────")
        L.append(f"│ {sc.get('scholar', '?')}")
        L.append(f"│ {sc.get('aa_name', '')}")
        L.append(f"│ Origin: {sc.get('origin', '?')}")
        L.append(f"│ Era:    {sc.get('century', '?')}")
        L.append(f"│ Code:   {sc.get('sc_code', '?')}")
        L.append("└──────────────────────────────────────────────────")

        L.append("")
        L.append("┌─ WORKS ───────────────────────────────────────────")
        L.append(f"│ Primary: {sc.get('primary_work', '?')}")
        for wl in (sc.get('warning_content', '') or '').split('\n'):
            wl = wl.strip()
            if wl:
                L.append(f"│ {wl}")
        L.append("└──────────────────────────────────────────────────")
        total += len(scholar_hits)

        L.append("")
        L.append("┌─ LATTICE PRESENCE ────────────────────────────────")

        if entry_hits:
            L.append(f"│")
            L.append(f"│ ENTRIES ({len(entry_hits)}):")
            for e in entry_hits:
                L.append(f"│   #{e.get('entry_id','?')} {e.get('en_term','?')}: {(e.get('aa_word','') or '')[:100]}")
            total += len(entry_hits)

        bitig_hits = _search('bitig_a1_entries',
            ['entry_id', 'orig2_term', 'ibn_sina_attestation', 'kashgari_attestation', 'notes'])
        if bitig_hits:
            L.append(f"│")
            L.append(f"│ BITIG ATTESTATION ({len(bitig_hits)}):")
            for b in bitig_hits:
                att = b.get('ibn_sina_attestation','') or b.get('kashgari_attestation','') or b.get('notes','') or ''
                L.append(f"│   {b.get('orig2_term','?')}: {att[:120]}")
            total += len(bitig_hits)

        body_hits = _search('body_data',
            ['body_id', 'subsystem', 'category', 'english', 'description', 'specific_data'])
        if body_hits:
            by_sub = {}
            for b in body_hits:
                s = b.get('subsystem', '?')
                by_sub.setdefault(s, []).append(b)
            L.append(f"│")
            L.append(f"│ BODY/HEALING ({len(body_hits)} rows, {len(by_sub)} subsystems):")
            for sub, rows in sorted(by_sub.items(), key=lambda x: -len(x[1])):
                L.append(f"│   {sub}: {len(rows)} rows")
                for r in rows[:2]:
                    L.append(f"│     → {(r.get('english','') or r.get('category','') or '')[:80]}")
            total += len(body_hits)

        L.append("└──────────────────────────────────────────────────")

        # CONTAMINATION
        chron_hits = _search('chronology', ['id', 'date', 'era', 'event', 'orig_meaning', 'notes'])
        dp_hits = _search('dp_register', ['dp_code', 'name', 'mechanism', 'example'])
        int_hits = _search('interception_register',
            ['int_id', 'root_letters', 'amr_meaning', 'lisan_word', 'lisan_meaning', 'inversion_note'])

        if chron_hits or dp_hits or int_hits:
            L.append("")
            L.append("┌─ CONTAMINATION / INTELLIGENCE ────────────────────")
            if chron_hits:
                L.append(f"│ CHRONOLOGY ({len(chron_hits)}):")
                for c in sorted(chron_hits, key=lambda x: str(x.get('date', ''))):
                    L.append(f"│   {c.get('id','?')} ({c.get('date','?')}): {(c.get('event','') or '')[:100]}")
                total += len(chron_hits)
            if dp_hits:
                L.append(f"│ DETECTION ({len(dp_hits)}):")
                for d in dp_hits:
                    L.append(f"│   {d.get('dp_code','?')}: {d.get('name','?')}")
                    L.append(f"│     {(d.get('mechanism','') or '')[:150]}")
                total += len(dp_hits)
            if int_hits:
                L.append(f"│ INTERCEPTIONS ({len(int_hits)}):")
                for i in int_hits:
                    L.append(f"│   #{i.get('int_id','?')} {i.get('root_letters','?')} → {i.get('lisan_word','?')}")
                    L.append(f"│     {(i.get('inversion_note','') or '')[:150]}")
                total += len(int_hits)
            L.append("└──────────────────────────────────────────────────")

    # ─── PEOPLE ──────────────────────────────────────────────────────
    elif rtype == 'PEOPLE':
        # Sort: direct name/id matches first
        def _people_sort_key(h):
            name = _to_plain(h.get('shell_name', '') or '')
            cid = _to_plain(h.get('child_id', '') or '')
            t = _to_plain(term)
            if t == cid or t == name:
                return 0  # exact match
            if t in name or t in cid:
                return 1  # partial match on name
            return 2  # matched on other field
        child_hits.sort(key=_people_sort_key)
        ch = child_hits[0]
        root = ch.get('orig_root', '')
        L.append("")
        L.append("┌─ IDENTITY ────────────────────────────────────────")
        L.append(f"│ {ch.get('shell_name', '?')}")
        L.append(f"│ Root: {root}")
        L.append(f"│ Orig: {ch.get('orig_meaning', '?')}")
        L.append("└──────────────────────────────────────────────────")

        if root and '-' in root:
            try:
                from amr_alphabet import compute_root_meaning_text
                L.append("")
                L.append("┌─ LETTER COMPUTATION ──────────────────────────────")
                L.append(f"│ {compute_root_meaning_text(root)}")
                L.append("└──────────────────────────────────────────────────")
            except Exception:
                pass

        L.append("")
        L.append("┌─ OPERATION ───────────────────────────────────────")
        L.append(f"│ Role:  {ch.get('operation_role', '?')}")
        L.append(f"│ Shell: {ch.get('shell_meaning', '?')}")
        L.append("└──────────────────────────────────────────────────")
        total += len(child_hits)

        if entry_hits:
            L.append("")
            L.append(f"┌─ DOWNSTREAM ({len(entry_hits)}) ──────────────────────────────")
            for e in entry_hits:
                L.append(f"│ #{e.get('entry_id','?')} {e.get('en_term','?')}: {(e.get('aa_word','') or '')[:80]}")
            L.append("└──────────────────────────────────────────────────")
            total += len(entry_hits)

        chron_hits = _search('chronology', ['id', 'date', 'era', 'event', 'notes'])
        if chron_hits:
            L.append("")
            L.append(f"┌─ CHRONOLOGY ({len(chron_hits)}) ──────────────────────────────")
            for c in sorted(chron_hits, key=lambda x: str(x.get('date', ''))):
                L.append(f"│ {c.get('id','?')} ({c.get('date','?')}): {(c.get('event','') or '')[:100]}")
            L.append("└──────────────────────────────────────────────────")
            total += len(chron_hits)

        net_hits = _search('m4_networks', ['orig_id', 'specific_data'])
        if net_hits:
            L.append("")
            L.append(f"┌─ NETWORKS ({len(net_hits)}) ─────────────────────────────────")
            for n in net_hits:
                L.append(f"│ {n.get('orig_id','?')}: {(n.get('specific_data','') or '')[:100]}")
            L.append("└──────────────────────────────────────────────────")
            total += len(net_hits)

    # ─── ROOT ────────────────────────────────────────────────────────
    elif rtype == 'ROOT':
        rt = root_hits[0]
        rl = rt.get('root_letters', '')
        try:
            from amr_alphabet import compute_root_meaning_text, compute_root_meaning
            comp = compute_root_meaning(rl)
            comp_text = compute_root_meaning_text(rl)
        except Exception:
            comp, comp_text = None, ''

        L.append("")
        L.append("┌─ LETTERS ─────────────────────────────────────────")
        L.append(f"│ {comp_text}")
        if comp:
            for lt in comp.get('letters', []):
                L.append(f"│ {lt['letter']} ({lt['name']}) abjad {lt['abjad']} = {lt['core_concept']}")
        L.append("└──────────────────────────────────────────────────")

        try:
            qw = conn.execute(
                "SELECT surah, ayah, aa_word, word_type FROM quran_word_roots WHERE root = ? ORDER BY surah, ayah",
                (rl,)).fetchall()
            L.append("")
            L.append(f"┌─ QUR'AN ({len(qw)} tokens) ─────────────────────────────")
            for w in qw[:15]:
                L.append(f"│ Q{w['surah']}:{w['ayah']} — {w['aa_word']} [{w['word_type'] or '?'}]")
            L.append("└──────────────────────────────────────────────────")
        except Exception:
            pass

        re_entries = conn.execute(
            "SELECT entry_id, en_term, aa_word FROM entries WHERE root_letters = ?", (rl,)).fetchall()
        if re_entries:
            L.append("")
            L.append(f"┌─ DOWNSTREAM ({len(re_entries)}) ──────────────────────────────")
            for e in re_entries:
                L.append(f"│ #{e['entry_id']} {e['en_term'] or '?'}: {(e['aa_word'] or '')[:80]}")
            L.append("└──────────────────────────────────────────────────")
        total += len(root_hits) + len(re_entries)

    # ─── ENTRY ───────────────────────────────────────────────────────
    elif rtype == 'ENTRY':
        en = entry_hits[0]
        root = en.get('root_letters', '')
        L.append("")
        L.append("┌─ ENTRY ───────────────────────────────────────────")
        L.append(f"│ #{en.get('entry_id','?')} {en.get('en_term','?')}")
        L.append(f"│ AA: {en.get('aa_word', '?')}")
        L.append(f"│ Root: {root}")
        L.append("└──────────────────────────────────────────────────")

        if root and '-' in root:
            try:
                from amr_alphabet import compute_root_meaning_text
                L.append("")
                L.append("┌─ LETTER COMPUTATION ──────────────────────────────")
                L.append(f"│ {compute_root_meaning_text(root)}")
                L.append("└──────────────────────────────────────────────────")
            except Exception:
                pass
            siblings = conn.execute(
                "SELECT entry_id, en_term, aa_word FROM entries WHERE root_letters = ? AND entry_id != ?",
                (root, en.get('entry_id', -1))).fetchall()
            if siblings:
                L.append("")
                L.append(f"┌─ SIBLINGS — root {root} ({len(siblings)}) ────────────────")
                for s in siblings:
                    L.append(f"│ #{s['entry_id']} {s['en_term'] or '?'}: {(s['aa_word'] or '')[:80]}")
                L.append("└──────────────────────────────────────────────────")
        total += len(entry_hits)

    # ─── GENERAL ─────────────────────────────────────────────────────
    else:
        ALL = [
            ('scholar_warnings', ['sc_code', 'scholar', 'warning_content']),
            ('entries', ['entry_id', 'en_term', 'aa_word']),
            ('child_entries', ['child_id', 'shell_name', 'orig_meaning']),
            ('bitig_a1_entries', ['entry_id', 'orig2_term', 'notes']),
            ('chronology', ['id', 'date', 'event']),
            ('body_data', ['body_id', 'subsystem', 'english']),
            ('dp_register', ['dp_code', 'name', 'mechanism']),
            ('interception_register', ['int_id', 'root_letters', 'lisan_word']),
            ('m4_networks', ['orig_id', 'specific_data']),
        ]
        for table, columns in ALL:
            hits = _search(table, columns)
            if hits:
                L.append("")
                L.append(f"── {table} ({len(hits)}) ──")
                for h in hits[:10]:
                    kv = [f"{k}: {str(v)[:80]}" for k, v in h.items() if v and k in columns]
                    L.append(f"  {' | '.join(kv[:3])}")
                total += len(hits)

    L.append("")
    L.append("═" * 60)
    L.append(f"TOTAL: {total} records — TYPE: {rtype}")
    L.append("═" * 60)
    conn.close()
    return '\n'.join(L)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(generate(' '.join(sys.argv[1:])))
    else:
        print("Usage: python3 uslap_full_report.py <term>")
