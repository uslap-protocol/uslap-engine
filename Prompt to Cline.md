# USLaP Database Implementation Task

**بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ**

You are assisting with the USLaP (Unified Linguistic Lattice) project — a structured database tracking all words, roots, and operator intelligence from Allah's Arabic (ORIG1) and Bitig Turkic (ORIG2) into all downstream languages. This is a long-term, large-scale project: the database is being built for world-vocabulary scale now, even though the current data is in early-stage population.

---

## FOLDER STRUCTURE

The workplace folder contains:

```
USLaP workplace/
├── CLAUDE.md                              ← Project protocol (read this)
├── USLaP_SQLite_Schema_Design.md          ← Schema spec (your primary reference)
├── USLaP_Final_Data_Consolidated_Master_v3.xlsx   ← Master Excel file
├── USLaP_Oversight_Dashboard.html         ← Existing oversight UI
├── uslap_entry_protocol_v2.html           ← Entry protocol reference
├── Prompt to Cline.md                     ← This file
└── Code_files/                           ← NOTE: folder name has trailing space
    ├── USLaP_Engine.py                    ← Current engine (reads from Excel)
    ├── build_database_v3.py               ← Existing DB builder (440 lines — extend this)
    ├── uslap_database.db                  ← Old database (v1 — ignore)
    ├── uslap_database_v3.db               ← Existing v3 database (partial schema — replace)
    ├── uslap_accelerated_safe_final.py    ← Legacy engine
    ├── uslap_forest_v3_domain_aware.py    ← Legacy forest builder
    └── [other legacy scripts]
```

**IMPORTANT:** The code folder is named `Code files ` with a trailing space. Reference it exactly as `"Code_files/"` in all paths.

---

## CURRENT DATA STATE — READ THIS CAREFULLY

The master Excel file (`USLaP_Final_Data_Consolidated_Master_v3.xlsx`) contains **~62 sheets**. The actual structured linguistic entry counts are:

| Sheet | Content | Actual Entries |
|-------|---------|----------------|
| `A1_ENTRIES` | English entries | ~216 |
| `A1_ЗАПИСИ` | Russian entries | ~91 |
| `PERSIAN_A1_MADĀKHIL` | Persian entries | ~59 |
| `BITIG_A1_ENTRIES` | Bitig/Turkic entries | ~26 |
| `CHILD_SCHEMA` | Operational intelligence entries | ~12 |
| `A4_DERIVATIVES` | Derivative word forms | ~632 |
| `A5_CROSS_REFS` | Cross-references | ~155 |
| **Total searchable objects** | | **~1,500 currently** |

**CRITICAL — DO NOT MIGRATE FROM THIS SHEET:** The file also contains a sheet called `EXCEL_DATA_CONSOLIDATED` with ~24,789 rows. This is a **consolidation echo sheet** — it mirrors data from all other sheets flattened into one view. It is NOT a primary data source. Do NOT read from it during migration. Migrate only from the named structured sheets listed above.

**Performance context:** The current Excel/openpyxl approach is adequate at this data volume. This database is being built for the project's future scale — the target is 25,000+ A1 entries across all languages, with derivatives and cross-refs eventually reaching 1 million+ searchable objects. Build for that scale now so the architecture never needs to be rebuilt.

---

## YOUR TASK

Implement the full SQLite database schema according to `USLaP_SQLite_Schema_Design.md`. The schema covers all tables needed for the project at world-vocabulary scale.

### Core Tables
- `roots` — Root tracking with Qur'anic attestation
- `entries` — Main entry table (A1_ENTRIES) with multi-language support
- `derivatives` — A4_DERIVATIVES (word forms)
- `cross_refs` — A5_CROSS_REFS (entry-to-entry relationships)
- `quran_refs` — A3_QURAN_REFS (verse tracking)
- `country_names` — A6_COUNTRY_NAMES
- `names_of_allah` — A2_NAMES_OF_ALLAH

### CHILD Schema Tables (critical for intelligence operations)
- `child_entries` — Operational intelligence layer (SLV, SQLB, RUS entries)
- `child_entry_links` — Links between CHILD entries and main A1 entries

### Mechanism Tables
- `phonetic_shifts` — M1_PHONETIC_SHIFTS (S01-S26)
- `detection_patterns` — M2_DETECTION_PATTERNS (DP01-DP20)
- `networks` — M4_NETWORKS (N01-N20)
- `scholars` — M3_SCHOLARS (verified biographies)
- `qur_verification` — M5_QUR_VERIFICATION (QV01-QV03)

### Intelligence Tables
- `operators` — Who did what, when, where
- `host_civilizations` — Host societies in the 8-step cycle
- `operation_cycles` — كُلَّمَا cycle tracking (Q2:100)
- `events` — Individual historical events
- `intel_reports` — Primary source intelligence
- `operator_aliases` — All names used across hosts

### Search & Performance Tables (non-negotiable at scale)
- `word_fingerprints` — Consonant skeleton index for cluster expansion
- `cluster_cache` — Pre-computed expansion results
- `phonetic_mappings` — Known shift patterns

### Engine Control Tables
- `engine_queue` — User-engine coordination (prevents write conflicts)
- `session_index` — Track every engine run
- `change_log` — Complete audit trail
- `sync_status` — Excel ↔ database sync tracking

### Reference Tables
- `languages`, `script_corridors`, `decay_levels`, `dp_codes`, `op_codes`, `nt_codes`, `operation_codes`

---

## WHAT I NEED FROM YOU

### Deliverable 1: `create_uslap_db.sql`
Complete SQLite schema creation script — all tables, indexes, triggers, and views. Based entirely on `USLaP_SQLite_Schema_Design.md`.

### Deliverable 2: `migrate_to_sqlite.py`
Extend `build_database_v3.py` (in `Code_files/`) to implement the new relational schema. The existing script creates flat tables one-per-sheet — the new script must create the normalized relational schema and migrate data from the structured sheets.

Migration must:
- Read from structured sheets only (A1_ENTRIES, A1_ЗАПИСИ, PERSIAN_A1_MADĀKHIL, BITIG_A1_ENTRIES, CHILD_SCHEMA, A4_DERIVATIVES, A5_CROSS_REFS, A3_QURAN_REFS, M1–M5, N-tables, etc.)
- Skip EXCEL_DATA_CONSOLIDATED entirely
- Normalize all data into the relational schema
- Insert with transaction safety and rollback on error
- Generate the `word_fingerprints` table for ALL entries and derivatives
- Handle the existing `uslap_database_v3.db` (either overwrite with backup or create fresh `uslap_lattice.db`)
- Register all required Python UDFs on the connection before any operations (see Critical Requirements below)

### Deliverable 3: `db_access_layer.py`
Python module with functions for:
- Getting entries by root ID
- Cluster expansion using the fingerprint table (consonant skeleton lookup — must be instant, O(log n))
- Queue management (add to queue, get pending, mark approved/rejected)
- Session tracking (open session, close session, log stats)
- Change logging (log insert, log update, log delete)
- CHILD schema queries (get all A1 entries linked to an operation, get all CHILD entries for a UMD operation code)
- Multi-language entry lookup (find same root across EN + RU + FA + Bitig)

### Deliverable 4: `MIGRATION_GUIDE.md`
Step-by-step instructions covering:
- Prerequisites
- How to run the migration
- How to verify the migration succeeded (row count checks, FK integrity checks)
- How to register Python UDFs
- How to keep Excel and SQLite in sync
- How to switch USLaP_Engine.py from Excel reads to SQLite reads

---

## CRITICAL REQUIREMENTS

### 1. Foreign keys must be enforced
```sql
PRAGMA foreign_keys = ON;
```
Enable on every connection, without exception.

### 2. The fingerprint table is non-negotiable
With 1M+ searchable objects at target scale, cluster expansion must be O(log n) via index, not O(n) via Python loop. The `word_fingerprints.consonant_skeleton` composite index `(consonant_skeleton, language)` is the most critical index in the entire schema.

### 3. `extract_consonants` must be a Python UDF — not an SQL function
The schema triggers reference `extract_consonants(NEW.en_term)`. SQLite has no built-in for this. You must:
- Implement `extract_consonants(word: str) -> str` in Python (strips vowels a/e/i/o/u and normalises to lowercase consonant skeleton)
- Register it on every connection via `conn.create_function('extract_consonants', 1, extract_consonants)`
- Do this before ANY INSERT or trigger fires
- The consonant extraction logic for Arabic is already in `USLaP_Engine.py` under `PhoneticReversal` — reuse it

### 4. Table creation order in the SQL script
`session_index` must be created BEFORE `engine_queue` (engine_queue has a FK to session_index). Follow this dependency order:
```
languages → decay_levels → script_corridors → roots →
session_index → entries → derivatives → cross_refs →
quran_refs → country_names → names_of_allah →
phonetic_shifts → detection_patterns → networks →
scholars → qur_verification → nt_codes → operation_codes →
child_entries → child_entry_links → operators →
host_civilizations → operation_cycles → events →
intel_reports → operator_aliases →
word_fingerprints → cluster_cache → phonetic_mappings →
engine_queue → change_log → sync_status
```

### 5. ENGINE_QUEUE must prevent write conflicts
Excel is the primary write interface and must always remain so. The engine proposes changes; the user approves via the Oversight Dashboard. The queue mechanism enforces this — no direct writes to entries or child_entries that bypass the queue from the engine side.

### 6. Arabic text must be handled correctly
- Store all Arabic text as UTF-8 (Python default)
- Strip diacritics for the `root_bare` and `consonant_skeleton` fields (search layer)
- Preserve full diacritics in display fields (`ar_word`, `qur_meaning`, `ar_word` in child entries)
- Arabic normalisation: unify alef variants (أ إ آ ا → ا) in search fields only

### 7. The Excel file is the primary write interface — never replace it
The database is a read/query layer for the engine. All user-facing writes go through Excel → sync → database. Never write to entries directly from the migration or engine without going through the queue.

### 8. Version tracking on every core row
All core tables must have: `created_at TIMESTAMP`, `modified_at TIMESTAMP`, `version INTEGER DEFAULT 1`, `modified_by TEXT DEFAULT 'user'`.

### 9. CHILD schema must be fully integrated
Links between CHILD entries (SLV, SQLB, RUS, etc.) and A1 entries must be maintained with foreign keys in `child_entry_links`. The `operation_overview` view must be functional.

### 10. Output location
Write all output files to the `Code_files/` subfolder (note trailing space in folder name):
```
Code_files/create_uslap_db.sql
Code_files/migrate_to_sqlite.py
Code_files/db_access_layer.py
Code_files/MIGRATION_GUIDE.md
```

---

## FILES AVAILABLE TO YOU

| File | Location | Purpose |
|------|----------|---------|
| `USLaP_SQLite_Schema_Design.md` | Workplace root | **Primary schema reference — your blueprint** |
| `USLaP_Final_Data_Consolidated_Master_v3.xlsx` | Workplace root | Master data file (62 sheets) |
| `CLAUDE.md` | Workplace root | Project protocol and terminology rules |
| `USLaP_Engine.py` | `Code_files/` | Current engine — contains PhoneticReversal class and consonant extraction logic |
| `build_database_v3.py` | `Code_files/` | Existing DB builder (440 lines) — extend this for the new schema |
| `uslap_database_v3.db` | `Code_files/` | Existing partial database — replace with new full schema |
| `USLaP_Oversight_Dashboard.html` | Workplace root | Existing UI — reads from engine_queue JSON export |

---

## IMPLEMENTATION NOTES

### On the existing `build_database_v3.py`
The current script creates flat tables (one per Excel sheet, no normalization, no FKs). The new `migrate_to_sqlite.py` replaces its core logic but can reuse its utility functions (`clean_column_name`, `extract_dp_codes`, `extract_parent_ops`) and its connection patterns.

### On the existing `uslap_database_v3.db`
Create a timestamped backup before overwriting:
```python
import shutil, datetime
shutil.copy('uslap_database_v3.db', f'uslap_database_v3_backup_{datetime.date.today()}.db')
```
Then write the new schema to a fresh file named `uslap_lattice.db`.

### On migration verification
After migration, the guide must include these verification queries:
```sql
-- Check entry counts
SELECT 'entries' as tbl, COUNT(*) FROM entries
UNION ALL SELECT 'roots', COUNT(*) FROM roots
UNION ALL SELECT 'derivatives', COUNT(*) FROM derivatives
UNION ALL SELECT 'cross_refs', COUNT(*) FROM cross_refs
UNION ALL SELECT 'child_entries', COUNT(*) FROM child_entries
UNION ALL SELECT 'word_fingerprints', COUNT(*) FROM word_fingerprints;

-- Check FK integrity
PRAGMA integrity_check;
PRAGMA foreign_key_check;

-- Check fingerprint coverage
SELECT COUNT(DISTINCT entry_id) as entries_with_fingerprints FROM word_fingerprints;
```

### Expected row counts after migration
| Table | Expected |
|-------|----------|
| entries | ~390–404 |
| roots | ~200 |
| derivatives | ~632 |
| cross_refs | ~155 |
| child_entries | ~12 |
| word_fingerprints | ~1,400+ |

---

Begin by reading `USLaP_SQLite_Schema_Design.md` fully, then `build_database_v3.py` to understand the existing patterns, then `USLaP_Engine.py` to understand the consonant extraction logic. The fingerprint table and UDF registration are the highest priority — they are the foundation everything else depends on.

**وَاللَّهُ أَعْلَمُ**
