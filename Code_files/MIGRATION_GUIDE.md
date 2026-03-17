# USLaP Database Migration Guide

**بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ**

This guide provides step-by-step instructions for migrating data from the Excel master file to the full USLaP SQLite relational database. The migration creates a normalized schema designed for world-vocabulary scale (target: 25,000+ entries, 1M+ searchable objects).

## Overview

The migration process:
1. Creates a fresh SQLite database with the full relational schema (`uslap_lattice.db`)
2. Reads data from structured Excel sheets (skips the consolidated echo sheet)
3. Normalizes data into proper relational tables with foreign key relationships
4. Registers the `extract_consonants()` Python UDF for phonetic search
5. Generates the `word_fingerprints` table for O(log n) cluster expansion
6. Creates backups of any existing databases
7. Verifies data integrity and foreign key constraints

## Prerequisites

### Required Files
- `USLaP_Final_Data_Consolidated_Master_v3.xlsx` – Master Excel file (in workplace root)
- `create_uslap_db.sql` – Complete SQLite schema (in `Code_files/`)
- `migrate_to_sqlite.py` – Migration script (in `Code_files/`)
- `USLaP_Engine.py` – Contains consonant extraction logic (in `Code_files/`)

### Python Dependencies
```bash
pip install openpyxl
```
The script requires Python 3.6+ and the `openpyxl` library for reading Excel files. All other dependencies are in the Python standard library.

## Running the Migration

### Step 1: Verify File Locations
Ensure all files are in the correct locations:
```
USLaP workplace/
├── USLaP_Final_Data_Consolidated_Master_v3.xlsx
└── Code_files/
    ├── create_uslap_db.sql
    ├── migrate_to_sqlite.py
    ├── USLaP_Engine.py
    └── [existing .db files]
```

### Step 2: Run the Migration Script
From the `USLaP workplace` directory, run:
```bash
cd "/Users/mmsetubal/Documents/USLaP workplace"
python3 "Code_files/migrate_to_sqlite.py"
```

**Important Notes:**
- The script will automatically create a backup of any existing `uslap_lattice.db` file
- Migration may take 1-2 minutes depending on Excel file size
- All operations are wrapped in a transaction; on failure, the database is rolled back

### Step 3: Monitor Migration Output
The script provides real-time progress:
```
══════════════════════════════════════════════════════════════════════
  USLaP Migration: Excel → SQLite Relational Database
  بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
══════════════════════════════════════════════════════════════════════

📖 Loading Excel file: USLaP_Final_Data_Consolidated_Master_v3.xlsx
  Found 62 sheets

🗄️  Creating database: Code_files/uslap_lattice.db
  Executing schema...
  Registering extract_consonants() UDF...

📊 Migrating data...
  Migrating A1_ENTRIES...
    Migrated 59 entries
  Migrating A1_ЗАПИСИ (Russian entries)...
    Migrated 0 entries
  [Additional sheets...]

📈 Migration Statistics:
────────────────────────────────────────
  Total entries: 59
  Total roots: 0
  Child entries: 3
  Word fingerprints: 6
  Engine queue items: 0

🔍 Verifying foreign key constraints...
✓ All foreign key constraints satisfied

══════════════════════════════════════════════════════════════════════
✅ MIGRATION COMPLETED SUCCESSFULLY
✅ Database: Code_files/uslap_lattice.db
══════════════════════════════════════════════════════════════════════
```

## Verification Steps

### Verify Database Structure
After migration, verify all tables were created:
```bash
sqlite3 "Code_files/uslap_lattice.db" ".tables"
```

Expected output (30+ tables):
```
child_entries          decay_levels          operation_cycles
child_entry_links      derivatives           operators
cluster_cache          detection_patterns    operator_aliases
country_names          engine_queue          operation_codes
cross_refs             entries               phonetic_mappings
change_log             events                phonetic_shifts
dp_codes               host_civilizations    quran_refs
intel_reports          languages             roots
names_of_allah         networks              scholars
nt_codes               op_codes              script_corridors
qur_verification       session_index         sync_status
word_fingerprints
```

### Verify Row Counts
Run the verification queries in the database:
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

**Expected Results:**
- `entries`: ~390–404 entries total across all languages
- `roots`: ~200 unique roots
- `derivatives`: ~632 word forms
- `cross_refs`: ~155 relationships
- `child_entries`: ~12 operational intelligence entries
- `word_fingerprints`: ~1,400+ entries (covers all searchable terms)

### Test the UDF Function
Verify the `extract_consonants()` function works:
```bash
sqlite3 "Code_files/uslap_lattice.db" "SELECT extract_consonants('example')"
```
Expected output: `xmpl`

### Test Basic Queries
```sql
-- Get entries with high confidence scores
SELECT entry_id, en_term, score FROM entries WHERE score >= 8 ORDER BY score DESC LIMIT 10;

-- Test phonetic search via word_fingerprints
SELECT wf.raw_word, wf.consonant_skeleton, e.en_term, e.score
FROM word_fingerprints wf
LEFT JOIN entries e ON wf.entry_id = e.entry_id
WHERE wf.consonant_skeleton = extract_consonants('test')
LIMIT 5;

-- View operational intelligence (CHILD schema)
SELECT child_id, shell_name, operation_role, parent_op FROM child_entries;
```

## Database Schema Details

### Critical Tables for Engine Operations

#### 1. `word_fingerprints` – Phonetic Search Index
The most critical table for performance. Enables O(log n) cluster expansion via the composite index on `(consonant_skeleton, language)`.

**Triggers:** Automatic population when entries/derivatives/child entries are inserted or updated.

**Index:** `idx_fingerprints_lookup` enables instant phonetic matching.

#### 2. `engine_queue` – Write Conflict Prevention
Prevents direct writes from the engine to core tables. All proposed changes go through this queue for user approval via the Oversight Dashboard.

**Purpose:** Maintains Excel as the primary write interface while enabling engine proposals.

#### 3. `session_index` – Engine Session Tracking
Tracks every engine run with performance metrics and error logging.

#### 4. `child_entries` & `child_entry_links` – Operational Intelligence
CHILD schema integration links operational intelligence (SLV, SQLB, RUS entries) with main A1 entries.

### Foreign Key Enforcement
Foreign keys are strictly enforced (`PRAGMA foreign_keys = ON`). The migration script temporarily disables them during data insertion to avoid constraint violations, then re-enables and verifies all constraints.

## Python UDF: `extract_consonants()`

### Registration
The UDF is automatically registered on every database connection via:
```python
conn.create_function("extract_consonants", 1, extract_consonants)
```

**CRITICAL:** Must be registered BEFORE any INSERT operations or trigger execution.

### Implementation
The function extracts consonant skeletons from words:
- Removes vowels (a, e, i, o, u)
- Handles digraphs (sh, ch, gh, th, ph, wh, qu) as single units
- Normalizes to lowercase
- Returns empty string for null/empty input

**Source:** Logic matches `PhoneticReversal.extract_consonants()` in `USLaP_Engine.py`.

### SQL Triggers Using the UDF
The schema includes triggers that automatically populate `word_fingerprints`:
```sql
CREATE TRIGGER update_fingerprints_on_entry_insert
AFTER INSERT ON entries
BEGIN
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT NEW.entry_id, 'en', NEW.en_term, extract_consonants(NEW.en_term)
    WHERE NEW.en_term IS NOT NULL AND NEW.en_term != '';
    -- ... similar for ru_term, fa_term, ar_word
END;
```

## Excel ↔ Database Sync Strategy

### Current Architecture
- **Excel is primary write interface:** All user-facing writes go through Excel
- **Database is read/query layer:** Engine reads from database, proposes changes via queue
- **Sync direction:** Excel → Database (one-way during migration)

### Maintaining Sync
After migration, keep databases in sync:

1. **Engine proposals:** When USLaP_Engine.py detects new patterns, it writes to `engine_queue`
2. **User approval:** User reviews proposals in Oversight Dashboard (`USLaP_Oversight_Dashboard.html`)
3. **Approved changes:** User applies approved changes to Excel manually
4. **Re-sync:** Run migration script periodically to update database with Excel changes

### Migration Script Updates
The `migrate_to_sqlite.py` script can be re-run at any time. It will:
1. Create timestamped backup of existing database
2. Start fresh with current Excel data
3. Preserve any `engine_queue` items that haven't been processed

## Switching USLaP_Engine.py to SQLite Reads

### Current State
`USLaP_Engine.py` currently reads directly from Excel via openpyxl.

### Target State
Update `USLaP_Engine.py` to use the database access layer (`db_access_layer.py`) for:
1. Entry lookups (instead of reading Excel sheets)
2. Phonetic search (using `word_fingerprints` table)
3. Cluster expansion (O(log n) via indexed searches)
4. Queue operations (proposing changes via `engine_queue`)

### Implementation Steps
1. Import `db_access_layer` module
2. Replace Excel reading with database queries:
   ```python
   # Old: reading from Excel
   # New: using database
   from db_access_layer import search_word, PhoneticSearchOperations
   
   results = search_word("example")
   similar = PhoneticSearchOperations.find_similar_words("example", conn)
   ```
3. Update cluster expansion to use `word_fingerprints` index
4. Route all proposed changes through `engine_queue` instead of direct writes

### Performance Benefits
- **Phonetic search:** O(log n) vs O(n) linear scan
- **Cluster expansion:** Instant via pre-computed fingerprints
- **Memory usage:** Database queries vs loading entire Excel file
- **Concurrency:** Multiple engine sessions can query simultaneously

## Troubleshooting

### Common Issues

#### 1. "Excel file not found"
**Solution:** Ensure `USLaP_Final_Data_Consolidated_Master_v3.xlsx` is in the workplace root directory.

#### 2. "Schema file not found"
**Solution:** Ensure `create_uslap_db.sql` is in `Code_files/` directory.

#### 3. Foreign key constraint violations
**Solution:** The migration script temporarily disables foreign keys during insertion. If errors persist:
```bash
sqlite3 "Code_files/uslap_lattice.db" "PRAGMA foreign_key_check"
```
Check for circular dependencies or missing reference data.

#### 4. UDF not registered
**Solution:** Ensure `extract_consonants()` is registered before any inserts. The migration script does this automatically. For custom connections, use:
```python
from migrate_to_sqlite import extract_consonants
conn.create_function("extract_consonants", 1, extract_consonants)
```

#### 5. Low row counts after migration
**Possible causes:**
- Excel sheet names don't match expected names
- Header row detection failed
- Data is in unexpected format

**Debug:** Run the migration script with additional print statements or examine the Excel sheet structure.

### Recovery Procedures

#### Database Corruption
If the database becomes corrupted:
1. Restore from latest backup in `Code_files/backups/`
2. Or re-run migration script (creates fresh database)

#### Failed Migration
If migration fails mid-process:
1. Script automatically rolls back transaction
2. Old database remains unchanged (if backup was created)
3. Check error output for specific issue
4. Fix underlying problem (Excel format, disk space, permissions)
5. Re-run migration

#### Data Loss Prevention
- Migration always creates timestamped backups
- Excel master file remains unchanged (read-only during migration)
- Transaction rollback on any error

## Performance Optimization

### Index Usage
The schema includes optimal indexes for:
1. **Phonetic search:** `idx_fingerprints_lookup` on `(consonant_skeleton, language)`
2. **Root-based queries:** `idx_entries_root` on `entries(root_id)`
3. **Score sorting:** `idx_entries_score` on `entries(score DESC)`
4. **Full-text search:** FTS5 virtual table `entries_fts`

### Query Patterns
For best performance:
- Use `word_fingerprints` for phonetic searches
- Use `entries_fts` for full-text keyword searches
- Use `cluster_cache` for repeated expansion of same roots
- Limit results with `LIMIT` clauses for UI responsiveness

### Scaling Considerations
The schema is designed for 1M+ searchable objects. At that scale:
- Consider increasing SQLite cache size: `PRAGMA cache_size = -2000;` (2GB)
- Use WAL mode for concurrent reads: `PRAGMA journal_mode = WAL;`
- Regular VACUUM to maintain performance: `VACUUM;`

## Appendix A: Migration Script Details

### Sheets Migrated
The script reads from these structured sheets only:
- `A1_ENTRIES` – English entries
- `A1_ЗАПИСИ` – Russian entries  
- `PERSIAN_A1_MADĀKHIL` – Persian entries
- `BITIG_A1_ENTRIES` – ORIG2/Turkic entries
- `CHILD_SCHEMA` – Operational intelligence
- `A4_DERIVATIVES` – Word forms
- `A5_CROSS_REFS` – Entry relationships
- `A3_QURAN_REFS` – Verse references
- `M1_PHONETIC_SHIFTS` – Phonetic mechanism
- `M2_DETECTION_PATTERNS` – Detection patterns
- `M4_NETWORKS` – Network definitions
- `M3_SCHOLARS` – Scholar biographies
- `M5_QUR_VERIFICATION` – Qur'an verification

### Sheets Skipped
- `EXCEL_DATA_CONSOLIDATED` – Echo sheet (not a primary source)
- Various protocol, correction, and warning sheets

### Data Flow
1. Read Excel sheet → Clean column names → Map to schema → Insert
2. Extract unique roots from entries → Create `roots` table entries
3. Triggers automatically create `word_fingerprints`
4. Verify foreign key integrity
5. Commit transaction

## Appendix B: Database Access Layer

The `db_access_layer.py` module provides:
- `DatabaseConnection` – Context manager for connections
- `EntryOperations`, `RootOperations` – CRUD operations
- `PhoneticSearchOperations` – O(log n) cluster expansion
- `EngineQueueOperations`, `SessionOperations` – Engine control
- `AnalyticsOperations` – Statistics and analysis
- High-level API functions: `search_word()`, `add_new_entry()`, `run_engine_session()`

### Example Usage
```python
from db_access_layer import search_word, get_connection, EntryOperations

# High-level search
results = search_word("example")
print(f"Found {len(results['exact_matches'])} exact matches")

# Direct operations
with get_connection() as conn:
    entries = EntryOperations.get_high_score_entries(conn, min_score=8)
    print(f"High-score entries: {len(entries)}")
```

## Support

For issues with migration:
1. Check error messages in console output
2. Verify file permissions and locations
3. Ensure Excel file isn't open in another program
4. Check Python version and openpyxl installation

To report bugs or request enhancements, use the project's issue tracking system.

**وَاللَّهُ أَعْلَمُ**