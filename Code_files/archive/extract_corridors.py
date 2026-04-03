#!/usr/bin/env python3
import re, glob, os, sqlite3
from collections import Counter

SESSION_DIR = os.path.expanduser("~/.claude/projects/-Users-mmsetubal-Documents-USLaP-workplace")
DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl")))
print(f"Scanning {len(files)} sessions...")

corridor_assigns = {}  # term -> corridor

pat_update = re.compile(r"ds_corridor\s*=\s*'(DS\d+|ORIG2|TYPE[123]|DIRECT)'")
pat_term_en = re.compile(r"en_term\s*=\s*'([A-Z][A-Za-z]+)'")
pat_term_ru = re.compile(r"ru_term\s*=\s*'([А-ЯЁ][А-ЯЁа-яё]+)'")

for filepath in files:
    session_id = os.path.basename(filepath)[:12]
    try:
        with open(filepath, 'r', errors='ignore') as fh:
            for line in fh:
                m_corr = pat_update.search(line)
                if m_corr:
                    corridor = m_corr.group(1)
                    m_en = pat_term_en.search(line)
                    m_ru = pat_term_ru.search(line)
                    if m_en:
                        corridor_assigns[m_en.group(1).upper()] = corridor
                    if m_ru:
                        corridor_assigns[m_ru.group(1).upper()] = corridor
    except:
        continue

print(f"\nTotal unique term->corridor assignments found in sessions: {len(corridor_assigns)}")

by_corridor = Counter(corridor_assigns.values())
for c, cnt in sorted(by_corridor.items(), key=lambda x: -x[1]):
    print(f"  {c:10s} {cnt:5d}")

# Now diff against DB
conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

# Get current corridors
db_corridors = {}
c.execute("SELECT en_term, ru_term, ds_corridor FROM entries WHERE ds_corridor IS NOT NULL AND ds_corridor != ''")
for row in c.fetchall():
    if row[0]: db_corridors[row[0].upper()] = row[2]
    if row[1]: db_corridors[row[1].upper()] = row[2]

# Get entries with NO corridor
c.execute("SELECT en_term, ru_term FROM entries WHERE ds_corridor IS NULL OR ds_corridor = ''")
no_corridor = set()
for row in c.fetchall():
    if row[0]: no_corridor.add(row[0].upper())
    if row[1]: no_corridor.add(row[1].upper())

conn.close()

# Find lost corridors
lost = {}
for term, corr in corridor_assigns.items():
    if term in no_corridor:
        lost[term] = corr

print(f"\n{'='*70}")
print(f"LOST CORRIDORS: {len(lost)} terms had corridor in sessions but NOT in DB")
print(f"{'='*70}")

lost_by_corr = Counter(lost.values())
for c, cnt in sorted(lost_by_corr.items(), key=lambda x: -x[1]):
    print(f"  {c:10s} {cnt:5d}")

print(f"\nSample lost assignments:")
for term, corr in sorted(list(lost.items()))[:50]:
    print(f"  {term:25s} -> {corr}")

if len(lost) > 50:
    print(f"  ... and {len(lost) - 50} more")
