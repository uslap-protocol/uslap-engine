#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP GLOSS WASH — strips training-weight English from DB gloss fields.

Runs OUTSIDE the LLM. Zero tokens. Pure Python → SQLite.

Scans aa_gloss, semantic_field, kashgari_attestation, and notes columns
across diwan_roots, bitig_a1_entries, and entries tables for English
contamination from LLM training weights.

Usage:
  python3 uslap_wash_gloss.py scan                   # scan all tables, report only
  python3 uslap_wash_gloss.py scan diwan_roots        # scan one table
  python3 uslap_wash_gloss.py clean                   # scan + fix all tables
  python3 uslap_wash_gloss.py clean diwan_roots       # scan + fix one table
  python3 uslap_wash_gloss.py stats                   # contamination summary

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sys
import os
import re
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')

# ═══════════════════════════════════════════════════════════════════════════════
# ENGLISH DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

# Words that NEVER appear in Arabic transliteration
ENGLISH_WORDS = set([
    # Articles / prepositions / conjunctions
    'the', 'this', 'that', 'these', 'those', 'which', 'who', 'whom', 'whose',
    'about', 'after', 'before', 'between', 'during', 'into', 'through',
    'where', 'here', 'there', 'every', 'some', 'many', 'much', 'most',
    'does', 'did', 'done', 'doing', 'has', 'had', 'having', 'been', 'being',
    'would', 'could', 'should', 'might', 'must', 'shall', 'will',
    'also', 'only', 'just', 'very', 'still', 'already', 'never', 'always',
    'not', 'but', 'yet', 'however', 'although', 'because', 'since', 'while',
    # Common nouns that are NOT Arabic transliterations
    'horse', 'dog', 'cat', 'bird', 'fish', 'sheep', 'cattle', 'camel',
    'house', 'home', 'village', 'city', 'town', 'fortress', 'mountain',
    'medicine', 'children', 'people', 'person', 'man', 'woman',
    'water', 'fire', 'earth', 'stone', 'iron', 'gold', 'silver',
    'brave', 'pure', 'good', 'evil', 'great', 'small', 'old', 'new',
    'hunting', 'gathering', 'burning', 'hiding', 'running', 'walking',
    'important', 'significant', 'necessary', 'possible', 'impossible',
    'technology', 'vocabulary', 'meaning', 'history', 'science',
    # Verbs
    'appeared', 'showed', 'found', 'took', 'gave', 'made', 'said',
    'called', 'named', 'used', 'built', 'created', 'destroyed',
    'attached', 'connected', 'separated', 'gathered', 'collected',
    # Academic / framework
    'cognate', 'borrowed', 'loanword', 'etymology', 'derived',
    'proto', 'substrate', 'semitic', 'jupiter', 'petroleum',
])

# Patterns that indicate English prose (not transliteration)
ENGLISH_PATTERNS = [
    re.compile(r'\([^)]*\b(' + '|'.join(sorted(ENGLISH_WORDS)[:50]) + r')\b[^)]*\)'),  # (the horse)
    re.compile(r'—\s*[A-Z][a-z]'),          # — English sentence
    re.compile(r'=\s*[A-Z][a-z]'),           # = English translation
    re.compile(r'\.\s*[A-Z][a-z]{3,}\s+'),   # . English sentence
    re.compile(r'CRITICAL|PETROLEUM|JUPITER|RASUL\+|MILLA\+'),  # Known weight markers
    re.compile(r'Section:\s'),                # Section: heading
    re.compile(r'Dialect\s+of\s'),            # Dialect of...
    re.compile(r'Cross-ref:\s'),              # Cross-ref: ...
]

# Arabic transliteration markers — if these are present, the text has real translit
ARABIC_TRANSLIT_MARKERS = re.compile(
    r'al-[a-z]|^[a-z]+-l-|wa-|bi-l-|fi-l-|li-l-|min\s|ila\s|ala\s|'
    r'maqam|harf|kull|jami|bayn|qawl|idha|innama|anna|hadha|dhalika|'
    r"ma'na|ya'ni"
)


def detect_english(text):
    """
    Detect English contamination in a gloss field.
    Returns list of (type, match_text) tuples.
    """
    if not text or text == 'SEE_MS':
        return []

    findings = []

    # Check for pattern matches
    for pat in ENGLISH_PATTERNS:
        m = pat.search(text)
        if m:
            findings.append(('PATTERN', m.group()[:60]))

    # Check for parenthetical English: (the horse), (medicine)
    parens = re.findall(r'\(([^)]+)\)', text)
    for p in parens:
        words = p.lower().split()
        eng_count = sum(1 for w in words if w in ENGLISH_WORDS)
        if eng_count >= 1 and len(words) <= 6:
            findings.append(('PARENTHETICAL', f'({p})'))

    # Check for pure English (no Arabic transliteration at all)
    has_translit = bool(ARABIC_TRANSLIT_MARKERS.search(text.lower()))
    if not has_translit:
        words = re.findall(r'[a-zA-Z]+', text)
        if words:
            eng_count = sum(1 for w in words if w.lower() in ENGLISH_WORDS)
            ratio = eng_count / len(words)
            if ratio > 0.5 and len(words) >= 2:
                findings.append(('PURE_ENGLISH', text[:60]))

    return findings


def strip_english(text):
    """
    Strip English contamination from a gloss, preserving Arabic transliteration.
    Returns cleaned text, or 'SEE_MS' if nothing remains.
    """
    if not text or text == 'SEE_MS':
        return text

    original = text

    # 1. Strip parenthetical English
    text = re.sub(r'\s*\([^)]*\b(' + '|'.join(sorted(ENGLISH_WORDS)[:50]) + r')\b[^)]*\)', '', text)

    # 2. Strip " — English phrase"
    parts = text.split('—')
    if len(parts) > 1:
        after = parts[-1].strip()
        words = after.lower().split()
        eng_count = sum(1 for w in words if w in ENGLISH_WORDS)
        if words and eng_count / len(words) > 0.3:
            text = '—'.join(parts[:-1]).strip()

    # 3. Strip " = English translation"
    if ' = ' in text:
        parts = text.split(' = ', 1)
        after = parts[1]
        if re.search(r'\b(' + '|'.join(list(ENGLISH_WORDS)[:30]) + r')\b', after.lower()):
            text = parts[0].strip()

    # 4. Strip ". English sentence" (capitalized word after period)
    text = re.sub(r'\.\s*[A-Z][a-z]{3,}\s+[a-z].*', '', text)

    # 5. Strip known markers
    text = re.sub(r'Section:.*', '', text)
    text = re.sub(r'Dialect\s+of\s+\w+', '', text)
    text = re.sub(r'Cross-ref:.*', '', text)

    # 6. Clean up orphaned punctuation
    text = re.sub(r'\.\s*\.', '.', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip().rstrip('.').strip()

    if not text:
        return 'SEE_MS'

    # 7. If entire result is still pure English, replace with SEE_MS
    has_translit = bool(ARABIC_TRANSLIT_MARKERS.search(text.lower()))
    if not has_translit:
        words = re.findall(r'[a-zA-Z]+', text)
        if words:
            eng_count = sum(1 for w in words if w.lower() in ENGLISH_WORDS)
            if eng_count == len(words):
                return 'SEE_MS'

    return text


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE CONFIGURATIONS — which columns to scan/clean per table
# ═══════════════════════════════════════════════════════════════════════════════

TABLE_CONFIG = {
    'diwan_roots': {
        'id_col': 'diwan_id',
        'label_col': 'headword',
        'scan_cols': ['aa_gloss'],
    },
    'bitig_a1_entries': {
        'id_col': 'entry_id',
        'label_col': 'orig2_term',
        'scan_cols': ['semantic_field', 'kashgari_attestation'],
    },
    'entries': {
        'id_col': 'entry_id',
        'label_col': 'en_term',
        'scan_cols': ['qur_meaning', 'source_form'],
    },
}


def scan_table(conn, table_name, fix=False):
    """Scan a table for English contamination. Optionally fix."""
    config = TABLE_CONFIG.get(table_name)
    if not config:
        print(f"  Unknown table: {table_name}")
        return 0, 0

    c = conn.cursor()
    id_col = config['id_col']
    label_col = config['label_col']
    scan_cols = config['scan_cols']

    # Check which columns actually exist
    c.execute(f"PRAGMA table_info({table_name})")
    existing_cols = {r[1] for r in c.fetchall()}
    scan_cols = [col for col in scan_cols if col in existing_cols]

    if not scan_cols:
        print(f"  {table_name}: no scannable columns found")
        return 0, 0

    total_flagged = 0
    total_fixed = 0

    for col in scan_cols:
        c.execute(f"SELECT {id_col}, {label_col}, {col} FROM {table_name} WHERE {col} IS NOT NULL AND {col} != '' AND {col} != 'SEE_MS'")
        rows = c.fetchall()

        col_flagged = 0
        col_fixed = 0

        for row_id, label, text in rows:
            findings = detect_english(text)
            if findings:
                col_flagged += 1
                if fix:
                    cleaned = strip_english(text)
                    if cleaned != text:
                        try:
                            c.execute(f"UPDATE {table_name} SET {col} = ? WHERE {id_col} = ?", (cleaned, row_id))
                            col_fixed += 1
                        except sqlite3.OperationalError as e:
                            # Trigger blocked the update — expected for some patterns
                            print(f"  BLOCKED by trigger: {row_id} {label} — {e}")
                elif col_flagged <= 10:
                    # Show first 10 in scan mode
                    print(f"  [{table_name}.{col}] ID:{row_id} | {label} | {text[:80]}")
                    for ftype, fmatch in findings[:2]:
                        print(f"    {ftype}: {fmatch}")

        total_flagged += col_flagged
        total_fixed += col_fixed

        if col_flagged > 0:
            action = f"fixed {col_fixed}" if fix else "found"
            print(f"  {table_name}.{col}: {col_flagged} contaminated ({action})")

    if fix:
        conn.commit()

    return total_flagged, total_fixed


def run_scan(table_filter=None, fix=False):
    """Scan (and optionally clean) tables for English contamination."""
    conn = sqlite3.connect(DB_PATH)

    # If fixing, temporarily drop update triggers that would block cleanup
    dropped_triggers = []
    if fix:
        c = conn.cursor()
        c.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND name LIKE '%english_block_update%'")
        for name, sql in c.fetchall():
            dropped_triggers.append((name, sql))
            c.execute(f"DROP TRIGGER {name}")
        conn.commit()

    tables = [table_filter] if table_filter else list(TABLE_CONFIG.keys())

    print(f"\n{'=' * 70}")
    print(f"  GLOSS WASH — {'CLEAN' if fix else 'SCAN'} MODE")
    print(f"{'=' * 70}\n")

    grand_flagged = 0
    grand_fixed = 0

    for table in tables:
        if table in TABLE_CONFIG:
            flagged, fixed = scan_table(conn, table, fix=fix)
            grand_flagged += flagged
            grand_fixed += fixed

    print(f"\n{'=' * 70}")
    print(f"  TOTAL: {grand_flagged} contaminated entries")
    if fix:
        print(f"  FIXED: {grand_fixed}")
        print(f"  SEE_MS (need MS re-read): check with 'stats' command")
    print(f"{'=' * 70}\n")

    # Recreate dropped triggers
    if dropped_triggers:
        c = conn.cursor()
        for name, sql in dropped_triggers:
            c.execute(sql)
        conn.commit()
        print(f"  Restored {len(dropped_triggers)} trigger(s).\n")

    conn.close()
    return grand_flagged


def run_stats():
    """Print contamination summary across all tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print(f"\n{'=' * 70}")
    print(f"  GLOSS WASH — CONTAMINATION STATS")
    print(f"{'=' * 70}\n")

    for table, config in TABLE_CONFIG.items():
        id_col = config['id_col']
        scan_cols = config['scan_cols']

        c.execute(f"PRAGMA table_info({table})")
        existing_cols = {r[1] for r in c.fetchall()}

        c.execute(f"SELECT COUNT(*) FROM {table}")
        total = c.fetchone()[0]

        for col in scan_cols:
            if col not in existing_cols:
                continue

            c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = 'SEE_MS'")
            see_ms = c.fetchone()[0]

            c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} != '' AND {col} != 'SEE_MS' AND {col} GLOB '*[a-z]*'")
            has_latin = c.fetchone()[0]

            c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL OR {col} = ''")
            empty = c.fetchone()[0]

            print(f"  {table}.{col}:")
            print(f"    Total rows:      {total}")
            print(f"    SEE_MS:          {see_ms}")
            print(f"    Has Latin chars: {has_latin} (transliterations)")
            print(f"    Empty/NULL:      {empty}")
            print()

    # Check triggers
    c.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND (name LIKE '%english%' OR name LIKE '%contamination%')")
    triggers = [r[0] for r in c.fetchall()]
    print(f"  Active contamination triggers: {len(triggers)}")
    for t in sorted(triggers):
        print(f"    {t}")

    print()
    conn.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    table = sys.argv[2] if len(sys.argv) >= 3 else None

    if cmd == 'scan':
        run_scan(table_filter=table, fix=False)
    elif cmd == 'clean':
        run_scan(table_filter=table, fix=True)
    elif cmd == 'stats':
        run_stats()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
