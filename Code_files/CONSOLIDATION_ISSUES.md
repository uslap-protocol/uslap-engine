# Schema Consolidation — Issues Found (2026-03-27)

## Status: BLOCKED — needs fixes before re-run

Backup: `backups/v3_pre_consolidation_20260327_1643.db` (85MB)
DB restored to pre-consolidation state. All other session work intact.

## Blocker 1: PK Conflicts on RU Mirror Tables

RU tables use the SAME primary keys as EN tables (they're translations, not new data):
- `a2_имена_аллаха`: allah_id 1-99 = same as `names_of_allah` allah_id 1-99
- `a4_производные`: deriv_id = same as `a4_derivatives` deriv_id
- `a5_перекрёстные_ссылки`: xref_id = same as `a5_cross_refs` xref_id

**Fix options:**
1. **UPDATE existing rows** — add RU content to the EN row (e.g., add `ru_meaning` column to `names_of_allah`). Preserves PK.
2. **Offset PKs** — insert RU rows with PK + 100000 offset. Avoids conflict but breaks ID meaning.
3. **Separate lang column** — generate NEW integer PKs for RU rows, add `lang='RU'` column. Original RU PK stored in `orig_ru_id` column.

**Recommended: Option 1** for Names of Allah (same 99 names, just add RU fields). **Option 3** for derivatives/cross-refs (genuinely different data rows).

## Blocker 2: Orphaned Views

Several views reference tables that don't exist or have been renamed:
- `m1_phonetic_shifts` → references `phonetic_shifts` (doesn't exist — data is in `shift_lookup`)
- `a3_quran_refs` → is a VIEW, not a table
- `a6_country_names` → is a VIEW, not a table
- `a1_записи` → is a VIEW (data already in `entries`)
- `a1_entries` → is a VIEW

**Fix:** Drop orphaned views BEFORE dropping triggers. Current script drops triggers first, which causes ALTER TABLE to fail when it touches a table referenced by a view.

**Correct order:**
1. Save all triggers + views (SQL)
2. Drop ALL views
3. Drop ALL triggers
4. Run migration
5. Recreate views (new definitions)
6. Recreate triggers (only for surviving tables)

## Blocker 3: UNIQUE Constraints from Hardening

`harden_v4_schema.py` added UNIQUE indexes:
- `uq_entries_en_root` on `entries(en_term, root_id)`
- `uq_bitig_orig2` on `bitig_a1_entries(orig2_term, root_letters)`
- `uq_eu_lang_term` on `european_a1_entries(lang, term)`
- `uq_lat_term` on `latin_a1_entries(lat_term)`
- `uq_roots_letters` on `roots(root_letters)`

These may block RU data insertion if values collide. Need to check each before INSERT.

## Migration Script

`consolidate_v5_clean.py` — handles Phases 1-3 but needs the above fixes.
`consolidate_schema_v5.py` — original version, same issues.

## What Was Completed This Session

1. Domain-specific QUF (12 lattice layers) — 97% pass, 102K rows, 27 tables
2. Extended QUF to 130 remaining tables — 40% pass
3. 4 new AMR AI modules (jism, hisab, tarikh, istakhbarat) — all with domain QUF colours
4. Schema hardening (indexes, views, health check)
5. amr_lawh.py QUF filtering wired
6. Automated backup script created
7. Banned term "theological" removed from all code
8. 12-layer lattice architecture defined (replaces 8 academic categories)

## Next Session: Consolidation

1. Fix Blocker 1: per-table PK strategy (UPDATE for names, new PKs for derivatives)
2. Fix Blocker 2: drop views BEFORE triggers
3. Fix Blocker 3: handle UNIQUE constraints
4. Re-run consolidation
5. Update code references (amr_jism.py, uslap_quf.py, uslap_handler.py, etc.)
6. Re-run domain QUF on consolidated structure
