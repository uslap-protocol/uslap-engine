# USLaP — QUF Gate Architecture
## Complete Map of Every QUF Gate, Definition, and Application
### Updated 2026-04-02 (AMR migration + deterministic runtime + gate fixes + re-validation + S-gate + token enforcement + تَصْرِيف engine)

---

## QUF = Quantification · Universality · Falsification

Every piece of data in the lattice must pass three tests before it is verified:

| Gate | Question | What it measures |
|------|----------|-----------------|
| **Q — Quantification** | How much countable evidence supports this claim? | Tokens, attestations, entries, dated sources — things you can COUNT |
| **U — Universality** | Does this hold across ALL instances, not just cherry-picked ones? | Surah spread, sibling language coverage, cross-table linkage, historical repetition |
| **F — Falsification** | What would disprove this? Is it empirically testable? | Shift chain validity, blacklist check, competing roots, consistency, source quality |

**Grades:** HIGH / MEDIUM / LOW / FAIL / PENDING
**Overall PASS:** Q ≥ MEDIUM AND U ≥ MEDIUM AND F ≥ MEDIUM

---

## ARCHITECTURE: QUF Lives in AMR AI (Deterministic Runtime)

QUF validation lives in the AMR AI modules — deterministic Python, zero LLM. Each domain module owns its QUF logic. The schema stores grades only. All validation runs through `uslap.py` (the deterministic runtime entry point) or `amr_quf.py` (the QUF router). No training weights touch the validation pipeline.

**Verified deterministic:** `test_determinism.py` runs same query 3 times → identical output every time.

```
Data IN or OUT
     │
     ▼
amr_quf.py (ROUTER)
     │
     ├── PRE-CHECKS (before any layer fires):
     │   • ORIG2 SKIP: Bitig/Turkic roots detected → skip linguistic validation
     │   •   (Old Turkic script chars, "(Turkic)" markers, non-Arabic roots)
     │   • PHONETIC CHAIN SKIP: if entry has documented phonetic_chain → skip
     │   •   (multi-step shift paths already verified by human)
     │
     ├── LAYER 0: LETTER ALIGNMENT
     │   Fires when: root_letters + meaning present
     │   Checks: do abjad letter values match the stated meaning?
     │
     ├── LAYER 1: LINGUISTIC (amr_aql.py)
     │   Fires when: root_letters present AND table is linguistic
     │   SKIPS: 30+ non-linguistic tables (umd_operations, chronology,
     │     formula_*, body_*, a4_derivatives, a5_cross_refs, etc.)
     │   Sub-gates (run in sequence):
     │     Q-gate: consonant skeleton match via S01-S26
     │     U-gate: shift table precedent (are these shifts documented?)
     │     S-gate: semantic family cross-check (NEW 2026-03-29)
     │       • Expands word into morphological family
     │       • RU: stem-final alternations (Д↔Ж, К↔Ч, Г↔Ж, СТ↔Щ, etc.)
     │       • EN: suffix stripping (-ing, -tion, -ment, etc.)
     │       • Checks same-language siblings only (cross-language = impossible)
     │       • Conservative: flags for REVIEW, not auto-reject
     │     F-gate: competing root check
     │   Overall: Q + U + S must all PASS. F is advisory.
     │
     ├── LAYER 2: DOMAIN-SPECIFIC (varies by table)
     │   Fires when: table is registered in DOMAIN_GATE_MAP
     │   Each AMR module defines its own Q/U/F logic
     │   (see per-layer detail below)
     │
     └── LAYER 3: SOURCE (amr_quf.py)
         Fires when: qur_ref/qur_primary/qur_secondary/source/dp_codes/
           founding_instances/kashgari_attestation/ibn_sina_attestation present
         Q: source documented? (Quranic → HIGH)
         U: multiple independent sources?
         F: source exposes (not sanitises)? DP codes present?

COMPOSITE GRADE = MINIMUM across all layers that fired.
An entry passing LINGUISTIC but failing SOURCE = overall FAIL.
Zero layers fired = BLOCK (nothing to validate = suspicious).
```

### Entry Point

```
python3 amr_quf.py validate --table TABLE --id ID    # single row
python3 amr_quf.py batch --table TABLE                # all rows
python3 amr_quf.py status                              # coverage report
```

### Write Pipeline (5-Layer Defence — updated 2026-03-30)

```
handler.write_entry(data, entry_class)
     │
     ├── LAYER 1: PROTOCOL RE-INJECTION (context_reload)
     │   Prints full protocol to stdout — resets LLM attention to PIPE mode.
     │   Non-blocking. ~477ms.
     │
     ├── LAYER 2: PRE-WRITE GATE (pre_write_gate)
     │   Scans ALL text fields for contamination:
     │   • TIER 1 ABSOLUTE: bare terms NEVER valid (semitic, PIE, proto-*, etc.)
     │   • TIER 2 CONTEXTUAL: phrase-based (loanword, borrowed from, cognate with)
     │   • Direction violations (AA → downstream inversion patterns)
     │   • DB blacklist (BL01-BL28 from contamination_blacklist table)
     │   ANY hit → BLOCK. ~415ms.
     │
     ├── LAYER 3: QUF VALIDATION (amr_quf.validate)
     │   Auto-maps storage fields → QUF detection fields:
     │     qur_primary → qur_ref, dp_always_active → dp_codes, etc.
     │   Runs 0-4 layers (letter/linguistic/domain/source).
     │   If FAIL → write blocked, evidence returned. ~0.1ms.
     │
     ├── LAYER 4: QUF TOKEN (sha256 + DB trigger enforcement)
     │   Generates cryptographic token, registers in quf_tokens table.
     │   INSERT trigger on target table verifies token exists + unused.
     │   Raw SQL INSERT without valid token → RAISE(ABORT). ~234ms.
     │
     └── LAYER 5: SQLite CONTAMINATION TRIGGERS (180 triggers)
         33 banned terms checked on INSERT and UPDATE.
         RAISE(ABORT) if found. Last line of defence.
         ~3.7ms for INSERT + all triggers.

POST-WRITE (automatic):
  • QUF stamps (q/u/f/pass/date) auto-persisted to row from validation result
  • Token marked stamp_used=1 → seals QUF columns against raw UPDATE
  • Dropped fields reported in return message
  • Total write time: ~1s (acceptable — human verification is the real bottleneck)

TRIGGER ENFORCEMENT (204 total triggers):
  • 180 contamination triggers (INSERT + UPDATE on protected tables)
  • 12 token enforcement triggers (BEFORE INSERT — require valid quf_token)
  • 12 stamp seal triggers (BEFORE UPDATE — block quf_pass changes after sealing)

BYPASS PROTECTION:
  • Raw INSERT → blocked by token trigger
  • Raw UPDATE of quf_pass → blocked by stamp seal trigger
  • handler.write_entry() is the ONLY write path into the lattice
```

---

## COMPLETE QUF GATE MAP — ALL 14 LAYERS

### L0: ALPHABET (28 letters, shifts, morphemes)
**Tables:** `aa_morpheme_map` (35 rows)
**AMR Module:** `amr_aql.py` → `mechanism_quf()`
**Coverage:** Via `mechanism_data` validator

| Gate | Definition |
|------|-----------|
| Q | Field completeness ratio ≥ 60% → HIGH |
| U | Has examples/markers documented → HIGH |
| F | Layer documented + examples present |

---

### L1: ROOT (3,320 letter combinations)
**Tables:** `roots` (3,320 rows)
**AMR Module:** `amr_aql.py` → `linguistic_quf()`

| Gate | Definition |
|------|-----------|
| Q | Shift chain documented with S## IDs + Quranic token count. ≥10 tokens → HIGH |
| U | Surah spread (≥20 surahs → HIGH) + sibling table count (≥4 tables → HIGH) |
| F | Unique root trace (no competing root) + not blacklisted. Score ≥8 → HIGH |

**ORIG2 roots (T-prefix):** `bitig_quf()` — Kashgari attestation is Q, dispersal is U, not-laundered-AA is F.

---

### L2: KEYWORD (42 Quranic programming keywords)
**Tables:** `att_terms` (8 rows)
**AMR Module:** `amr_keywords.py` → `keyword_quf()`
**Previously: NO QUF — now covered.**

| Gate | Definition |
|------|-----------|
| Q | Quranic token count (≥50 + root → HIGH) |
| U | Token count ≥100 = appears across many surahs → HIGH |
| F | Root derivation verified via amr_alphabet letter semantics |

---

### L3: DIVINE NAMES (99 Names of Allah)
**Tables:** `names_of_allah` (99 rows), `name_root_hub` (1 row)
**AMR Module:** `amr_aql.py` → `divine_quf()`

| Gate | Definition |
|------|-----------|
| Q | root_id + qur_ref + arabic_name all present → HIGH |
| U | **Universal by definition** — always HIGH |
| F | **Axiomatic** — always HIGH (Names of Allah are not falsifiable) |

**Test result:** A01 (الرَّحْمَٰن) → Q=HIGH, U=HIGH, F=HIGH ✓ PASS

---

### L0.5: تَصْرِيف (Three-Layer Morphological Engine — NEW 2026-04-02)
**AA Tables:** `verb_tasrif_patterns` (8), `noun_tasrif_patterns` (12), `noun_tasrif_vowels` (17), `verb_tasrif_grammar` (11), `noun_tasrif_grammar` (13)
**BI Tables:** `bitig_verb_tasrif` (8), `bitig_noun_tasrif` (6), `bitig_case_tasrif` (6), `bitig_grammar_tasrif` (10), `bitig_compound_rules` (8)
**AMR Modules:** `amr_tasrif.py` (AA) + `amr_bitig_tasrif.py` (BI)
**8 columns in `quran_word_roots`:** noun_tasrif_code, noun_vowel_code, gram_tense, gram_person, gram_number, gram_gender, gram_case, gram_definiteness
**Coverage:** 45,455 structural tokens (58.4%) + 49,391 grammar tokens (63.4%)
**Indexed:** 61 AA + 38 BI = 99 codes in term_nodes

Three sub-layers:
- **Layer 1 — CONSONANT**: What letters added to root. 8 verb codes + 12 noun codes.
- **Layer 2 — VOWEL**: What vowels sit on root letters. 17 patterns (5 broken plural).
- **Layer 3 — GRAMMAR**: External markers. Verb: tense/person/number/gender. Noun: definiteness/case/number/gender.

Cross-index audit (2026-04-02):
- Pattern ↔ token orphans: **0** (every code in tokens exists in tables, every table code has tokens)
- Grammar ↔ token orphans: **0** (UNMARKED case added this session — 6,957 indeclinable nouns)
- 2,651 entries (84%) link to tasrif-coded roots
- 4,382 EU entries (92%) link to tasrif-coded roots
- 5,948 derivatives (92%) chain to tasrif-coded roots
- 224 QV entries (84%) link to tasrif-coded roots

**Note:** Tasrif data is DESCRIPTIVE — it classifies existing Qur'anic tokens. It does not need its own QUF validation (the tokens themselves are validated at L4). The pattern/grammar definition tables are reference data.

---

### L4: QUR'ANIC FORMS (77,877 compiler words + 6,236 ayat)
**Tables:** `quran_word_roots` (77,877), `quran_known_forms` (927), `quran_ayat` (6,236), `quran_refs` (242)
**AMR Module:** `amr_aql.py` → `quran_form_quf()`
**Tasrif columns:** 8 columns link each token to L0.5 pattern/grammar tables (see above)

| Gate | Definition |
|------|-----------|
| Q | root + word + valid surah (1-114) all present → HIGH |
| U | Root matches roots table (bare or hyphenated) → HIGH |
| F | Compiler confidence grade: HIGH/MEDIUM_A → HIGH, MEDIUM_B/C → MEDIUM |

**All 4 tables now covered** (previously quran_ayat and quran_refs had no validator).

---

### L5: ENTRIES (EN 3,154 + RU + FA)
**Tables:** `entries` (3,154 rows)
**AMR Module:** `amr_aql.py` → `linguistic_quf()`

| Gate | Definition |
|------|-----------|
| Q | Shift chain with S## IDs (≥1 shift → HIGH) + Quranic token count + score |
| U | Surah spread + sibling table count (≥2 siblings AND tokens → HIGH) |
| F | Not blacklisted + phonetic chain documented + score ≥8 → HIGH |

**Test result:** SILK (entry 346) → LINGUISTIC: Q=HIGH U=HIGH F=HIGH ✓ PASS
(SOURCE layer fails because no source field populated — reveals data gap, not logic gap)

**Previous problem (SOLVED):** Two systems overwrote each other. Now one pipeline: `amr_quf.validate()` → `linguistic_quf()` + `source_quf()`.

---

### L6: ORIG2 (Bitig — second original)
**Tables:** `bitig_a1_entries` (2,295 rows) + 10 supporting bitig tables + 5 BI tasrif tables
**AMR Module:** `amr_aql.py` → `bitig_quf()`

| Gate | Definition |
|------|-----------|
| Q | Kashgari 1072 attestation → HIGH; root_id present → MEDIUM; none → PENDING |
| U | root linked to roots table + dispersal documented → HIGH |
| F | Not in contamination blacklist + not laundered AA (Kashgari-attested → HIGH) |

---

### L7: SIBLINGS (EU 4,785 + LA 425 + UZ 2,168)
**Tables:** `european_a1_entries` (4,785), `latin_a1_entries` (425), `uzbek_vocabulary` (2,168)
**AMR Module:** `amr_aql.py` → `sibling_quf()`

| Gate | Definition |
|------|-----------|
| Q | root valid + chain documented + score > 0 → HIGH |
| U | EN parent entry exists for this root → HIGH |
| F | Shift chain has known S## IDs → HIGH |

---

### L8: DERIVATIVES + CROSS-REFS
**Tables:** `a4_derivatives` (6,464), `a5_cross_refs` (1,076)
**AMR Module:** `amr_aql.py` → `derivative_quf()`, `xref_quf()`

| Gate | Derivatives | Cross-Refs |
|------|-------------|------------|
| Q | Parent entry exists + link_type valid | Both endpoints exist + link_type |
| U | Parent entry exists | Cross-ref endpoints both present |
| F | Link type in PERMITTED set (not COGNATE/LOANWORD/BORROWING) | Link type present |

---

### L9: DETECTION (DP + QV + BL + disputed)
**Tables:** `qv_translation_register` (268), `disputed_words` (50), `contamination_blacklist` (28), `dp_register` (6), `phonetic_reversal` (24)
**AMR Module:** `amr_basar.py` → `detection_quf()`

| Gate | Definition |
|------|-----------|
| Q | root + corruption_type + ayat_count > 0 (≥3 items → HIGH) |
| U | Valid corruption type (ROOT_FLATTENED, ACTION_TO_ETHNIC, etc.) + correction provided → HIGH |
| F | Washed translation ≠ corrupted translation → HIGH |

---

### L10: BODY / HEALTH (consolidated)
**Tables:** `body_data` (725), `body_cross_refs_unified` (206), `body_prayer_map_unified` (89), `body_heptad_meta` (42), `body_extraction_intel` (54)
**AMR Module:** `amr_jism.py` → `body_quf()`

| Gate | Definition |
|------|-----------|
| Q | arabic + english + root_letters + qur_ref (≥3 items → HIGH) |
| U | Valid heptad (1-7) + root linked → HIGH |
| F | Subsystem documented + root + english present → HIGH |

---

### L11: FORMULA (ḥisāb)
**Tables:** `formula_concealment` (216), `formula_ratios` (240), `formula_restoration` (193), `formula_scholars` (77), `formula_undiscovered` (58), `formula_cross_refs` (624)
**AMR Module:** `amr_hisab.py` → `formula_quf()`
**Previously: generic field-counting — now domain-specific.**

| Gate | Definition |
|------|-----------|
| Q | root + arabic + qur_ref + fill ratio ≥50% (≥3 items → HIGH) |
| U | Approved scholar attestation (al-Khorezmi, ibn Sina, al-Biruni, al-Tusi, al-Kashi) + Quranic ref → HIGH |
| F | Concealment method + restoration path both documented → HIGH |

---

### L12: HISTORY (chronology + deployment + peoples)
**Tables:** `chronology` (136), `child_entries` (51), `word_deployment_map` (38)
**AMR Module:** `amr_tarikh.py` → `history_quf()`

| Gate | Definition |
|------|-----------|
| Q | date + event + source + description (≥3 items → HIGH) |
| U | Status = CONFIRMED/VERIFIED + source documented → HIGH |
| F | Source + date both present = verifiable → HIGH |

---

### L13: INTELLIGENCE
**Tables:** `isnad` (19), `institutional_confession_register` (51), `financial_extraction_cycles` (10), `kashgari_concealment_audit` (15), `intel_file_index` (10)
**AMR Module:** `amr_istakhbarat.py` → `behaviour_quf()`
**Previously: only isnad covered — now ALL 5 tables covered.**

| Gate | Definition |
|------|-----------|
| Q | Quranic ayah references counted + root token matches in description + extraction algorithm match (≥3 ayat → HIGH) |
| U | Historical repetition: how many eras does this pattern repeat? (FE01-FE10 = 10 eras, ≥5 → HIGH) + chronology cross-ref |
| F | Quranic ref + DP codes = falsifiable and documented → HIGH. Approved source (isnad/scholar_warnings) → HIGH |

**Test result:** FE04 (Khazar extraction) → DOMAIN: Q=MEDIUM U=HIGH F=HIGH ✓ PASS

---

## MULTI-LAYER EXAMPLE: "Silk Road"

```
LAYER 1 — LINGUISTIC (amr_aql):
  SILK: R447 (س-ل-خ) → S21,S16,S11 → 3 Quranic tokens, 3 surahs, 3 siblings
  ROAD: R539 (ر-د-د) → S15,S19,S19 → 20 Quranic tokens, 16 lemmas
  Result: Q=HIGH U=HIGH F=HIGH ✓ PASS

LAYER 2 — BEHAVIOUR (amr_istakhbarat):
  Extraction algorithm: FE04 (Khazar) + FE01-FE10 (10 eras same pattern)
  Ayat: Q28:4, Q15:21, Q2:11-12, Q36:37, Q2:217
  Source: Ibn Khordadbeh (SC03), Richthofen 1877 (operator naming = DP07 evidence)
  Result: Q=HIGH U=HIGH F=HIGH ✓ PASS

LAYER 3 — SOURCE (amr_quf):
  Quranic references present, DP08 tagged
  Result: Q=HIGH U=HIGH F=HIGH ✓ PASS

COMPOSITE: Q=HIGH U=HIGH F=HIGH ✓ VERIFIED
```

---

## COVERAGE STATUS — POST RE-VALIDATION (2026-03-28)

Batch re-validation run with AMR pipeline after gate fixes.
Domain tables (L9-L13 non-linguistic) pending batch performance optimisation for per-row DB calls.

```
Layer   Table                                    Old→New        Rate
─────   ─────                                    ───────        ────
L1      roots                                     92%→98.2%     ▲ 3,259/3,320
L2      att_terms                                 100%→*         (pending domain batch)
L3      names_of_allah                            100%→100%      99/99
L4      quran_word_roots                           65%→98.7%    ▲ (sample 987/1,000)
L5      entries                                    93%→99.3%    ▲ 3,117/3,154
L6      bitig_a1_entries                          100%→99.9%     2,294/2,295
L7      european_a1_entries                        93%→100%     ▲ 4,785/4,785
L7      latin_a1_entries                           88%→100%     ▲ 425/425
L7      uzbek_vocabulary                           99%→96.6%     2,095/2,168
L8      a4_derivatives                             87%→*         (pending domain batch)
L9      qv_translation_register                   100%→100%      268/268
L9      dp_register                                17%→100%     ▲ 6/6
L10     body_cross_refs_unified                    19%→100%     ▲ 206/206
L10     body_data                                  82%→36%      ▼ (stricter: heptad+root required)
L11     formula_cross_refs                          0%→100%     ▲ 624/624
L11     formula_scholars                           73%→42.9%    ▼ (stricter: scholar attestation)
L12     chronology                                 82%→100%     ▲ 136/136
L13     financial_extraction_cycles               100%→100%      10/10
L13     intel_file_index                            0%→70%      ▲ 7/10

Tables marked * need domain batch optimisation (per-row DB calls too slow).
Tables with ▼ are STRICTER under new gates — failures = real data gaps, not gate bugs.
```

### Key Improvements
- **quran_word_roots: 65% → 98.7%** — PARTICLE fix (26,067 rows were false failures)
- **entries: 93% → 99.3%** — stale System 2 grades replaced
- **european/latin: 93%/88% → 100%** — sibling check now uses cached data
- **dp_register: 17% → 100%** — column mapping fixed
- **formula_cross_refs: 0% → 100%** — separate xref validator
- **body_cross_refs: 19% → 100%** — separate xref validator
- **chronology: 82% → 100%** — status/source fields now properly checked

### Real Data Gaps (not gate bugs)
- **body_data 36%** — 464 rows missing heptad assignment or root_letters
- **formula_scholars 43%** — 44 rows missing approved scholar attestation or qur_ref
- **a4_derivatives** — pending batch, likely ~87% (link_type gaps)
- **uzbek_vocabulary 96.6%** — 73 entries with missing root linkage

---

## FULL SESSION CHANGELOG (2026-03-28)

### Phase 1: Schema Strip + Cleanup
| Before | After |
|--------|-------|
| 99MB database | 48MB database (VACUUM + bloat removal) |
| 368 triggers | 204 triggers (181 contamination + 12 token enforcement + 12 stamp seal — 2026-03-30) |
| 158 indexes | 76 indexes (useless small-table indexes removed) |
| 68 views | 55 views (14 unreferenced dropped, +1 root_translations view 2026-03-30) |
| 94 .py files | 50 active files, 49 archived |
| uslap_quf.py 4,801 lines | 4,164 lines (System 2 archived + cross_language_wash + detect_compound added 2026-03-30) |

### Phase 2: QUF Migration to AMR AI
| Before | After |
|--------|-------|
| Two QUF systems fighting in uslap_quf.py | One pipeline: amr_quf.py router (920 lines) → AMR modules |
| System 2 overwrites System 1 grades | Single execution path, one result |
| L2 KEYWORD: no QUF | keyword_quf() in amr_keywords.py |
| L11 FORMULA: generic field-counting | formula_quf() + formula_xref_quf() with scholar attestation |
| L13 INTELLIGENCE: only isnad (19 rows) | behaviour_quf() + intel_index_quf() covers all 5 tables |
| QUF = phonetic only | QUF = linguistic + domain + source (multi-layer) |
| handler.write_entry() calls subprocess | calls amr_quf.validate() directly |
| amr_lawh.py bypassed QUF | QUF gate added to _write() |
| No S-gate (phonetic-only matches passed) | S-gate: semantic family cross-check between U and F (2026-03-29) |
| No ORIG2 skip (Bitig roots ran through AA shifts) | ORIG2 auto-detected and skipped (2026-03-29) |
| No phonetic_chain skip (documented entries re-validated) | phonetic_chain present → skip S-gate (human-verified) (2026-03-29) |
| Raw SQL INSERT bypassed all Python gates | 12 token enforcement triggers block raw INSERT (2026-03-30) |
| QUF stamps could be faked with raw UPDATE | 12 stamp seal triggers block raw quf_pass changes (2026-03-30) |
| QUF stamps required manual post-write UPDATE | Auto-persisted from validation result (2026-03-30) |
| Banned terms gate: bare word "adoption" false positive | Two tiers: ABSOLUTE (bare) + CONTEXTUAL (phrases) (2026-03-30) |
| Source detection missed qur_primary/qur_secondary | 15 field names now recognized for SOURCE layer (2026-03-30) |
| Single-method hypothesis (Q-gate only) | 5-method pipeline: family reduction, cross-language wash, reverse lookup, synonym trace, source form (2026-03-30) |
| No cross-language wash | `cross_language_wash()` in uslap_quf.py — extracts stable skeleton across 8+ languages (2026-03-30) |
| No compound detection | `detect_compound()` in uslap_quf.py — splits 4+ consonant skeletons into prefix+root or root+root (2026-03-30) |
| OP_NASAL fires unconditionally on any N | Constrained: N only skippable when medial + adjacent to mapped consonant (2026-03-30) |
| No P11 enforcement in scoring | Weak phonetic chain (<2/3 mapped) score-capped at 15 (2026-03-30) |
| No full-word-first rule | Wash full word before splitting; compound detector runs before triliteral trace (2026-03-30) |
| Compiler `root_translations` table missing | Created as VIEW mapping to `roots` table (3,320 roots) (2026-03-30) |
| Compiler misassigns 79+ roots (suffix=root confusion) | Morphology-aware ranking + `quran_known_forms` expansion 927→945 (2026-03-30) |
| No operator label detection in output | `operator_label_register` (15 entries) + stop hook Layer 6 (2026-03-30) |
| Unattested roots shown same as attested | Output brands: UNATTESTED — LISAN ARABIC ONLY (2026-03-30) |
| No morphological engine | تَصْرِيف 3-layer engine: 10 AA tables + 5 BI tables + 2 AMR modules + 8 columns in quran_word_roots (2026-04-02) |
| No tasrif routing in uslap.py | tasrif_route() intercepts "tasrif"/"bitig tasrif" before dhakaa pipeline + --tasrif/--bitig-tasrif CLI flags (2026-04-02) |
| Tasrif patterns not in search index | 99 codes indexed (61 AA + 38 BI) in term_nodes (2026-04-02) |
| UNMARKED case (6,957 tokens) not in grammar table | Added to noun_tasrif_grammar CASE dimension (2026-04-02) |
| Old index referenced deleted table name 'tasrif_patterns' | Cleaned + rebuilt as verb_tasrif_patterns (2026-04-02) |

### Phase 3: Gate Fixes + Re-Validation
| Fix | Impact |
|-----|--------|
| PARTICLE default (F=MEDIUM) | quran_word_roots: 65% → 98.7% |
| dp_register column mapping | 17% → 100% |
| body_cross_refs own validator | 19% → 100% |
| body_prayer_map own validator | 10% → needs re-run |
| formula_cross_refs → xref validator | 0% → 100% |
| intel_file_index own validator | 0% → 70% |
| Empty en_term blacklist false positive | roots: 0% → 98.2% |
| Batch performance (pre-loaded caches) | 3,138 entries in seconds (was timeout) |

### Phase 4: Deterministic Runtime
| Before | After |
|--------|-------|
| LLM in runtime loop (User → LLM → DB → LLM → Output) | Zero LLM (User → uslap.py → AMR → SQLite → Output) |
| LLM adds training weights to output | Output = pure DB content. NOT FOUND if DB empty. |
| Non-deterministic (different output each run) | Deterministic (test_determinism.py: ✓ ALL PASS) |
| No standalone runtime | `uslap.py` — full CLI + REPL, zero LLM imports |
| Fabrication possible ("Indian mathematics") | Fabrication impossible (no weights in pipeline) |
| 16 intent types in amr_basar | 22 intent types (added QUF, detection, keyword, intel patterns) |
| _reason() handles 7 intents | _reason() handles 13 intents (added body, formula, history, intel, QUF, detection, keyword) |
| No articulation for domain intents | Full articulation for all domain intents |

---

## QUF FAILURE AUDIT (2026-03-28)

All grades below are from the OLD System 2 run (2026-03-27). Batch re-validation with the new AMR pipeline is pending (performance optimisation needed — current batch is too slow per-row due to per-row DB connections in cross-sibling checks).

**Single-row validation with the new pipeline shows HIGHER pass rates** — e.g., entry #3 (Philosophy) has F=LOW in DB from old System 2, but gets F=HIGH from new AMR pipeline.

### Failure Pattern Analysis

| Table | Pass Rate | Failure Pattern | Root Cause | Fix |
|-------|----------|-----------------|------------|-----|
| `quran_word_roots` | 65% | 26,067 rows: Q=HIGH U=HIGH **F=LOW** | All are PARTICLEs — compiler assigned them no confidence grade. F gate reads NULL confidence → LOW | **GATE FIX:** PARTICLEs should get F=MEDIUM minimum (they're Qur'anic text, not unverified) |
| `quran_word_roots` | — | 1,429 rows: Q=LOW U=LOW F=LOW | NULL root — particles with no root assignment | **DATA:** Correct — particles don't have roots. Grade is accurate. |
| `entries` | 93% | 158 rows: Q=HIGH U=HIGH **F=LOW** | **STALE GRADES from System 2.** New AMR pipeline gives F=HIGH (e.g., entry #3 Philosophy). | **BATCH RE-RUN** needed |
| `roots` | 92% | 110 rows: Q=PENDING | ORIG2 roots not yet linked to Kashgari attestation | **DATA GAP:** Need Kashgari lookup for 110 unattested ORIG2 roots |
| `roots` | — | 59 rows: U=PENDING | AA roots with 0 surah spread and 0 sibling entries | **DATA GAP:** Roots exist but no entries trace to them yet |
| `a4_derivatives` | 87% | 638 rows: F=LOW | Missing link_type or link_type not in PERMITTED set | **DATA GAP:** 638 derivatives need link_type assignment |
| `a4_derivatives` | — | 171 rows: U=LOW | Parent entry_id not found in entries table | **DATA GAP:** Orphaned derivatives pointing to non-existent entries |
| `european_a1_entries` | 93% | 328 rows: U=PENDING | Root_id not found in entries table (no EN parent) | **DATA GAP:** EU entries without corresponding EN parent entry |
| `latin_a1_entries` | 88% | 50 rows: U=PENDING | Same — no EN parent entry | **DATA GAP** |
| `body_data` | 82% | 128 rows: U=LOW | Heptad=0 (not assigned) or no root_letters | **DATA GAP:** 128 body rows need heptad assignment + root linkage |
| `formula_concealment` | 71% | 63 rows: U=LOW | No scholar attestation | **DATA GAP:** Need al-Khorezmi/ibn Sina/al-Biruni references |
| `formula_cross_refs` | 0% | 624 rows: U=LOW | Cross-ref table has no scholar/source fields | **GATE FIX:** formula_cross_refs should use a different validator (xref, not formula) |
| `chronology` | 82% | 25 rows: F=LOW | "THIN COVERAGE" gap markers — no source/date because they document ABSENCE of data | **DATA:** Correct — these ARE gaps, not entries |
| `quran_refs` | 5% | 229 rows: F=LOW | Missing fields under new gate | **BATCH RE-RUN** needed (old grades) |
| `dp_register` | 17% | 5 rows: U=PENDING | No corruption_type field match | **GATE FIX:** dp_register uses different column names than QV register |
| `body_cross_refs_unified` | 19% | 165 rows: U=LOW | Cross-ref validator expects fields that don't exist | **GATE FIX:** body cross-refs need own validator |
| `body_prayer_map_unified` | 10% | 80 rows: U=LOW | Same — needs own validator | **GATE FIX** |
| `body_extraction_intel` | 35% | 35 rows: U=LOW | No heptad/root on intel rows | **DATA GAP** |
| `formula_scholars` | 73% | 21 rows: U=LOW | Scholar entries without Quranic attestation | **DATA GAP:** Need qur_ref for 21 scholars |
| `intel_file_index` | 0% | 10 rows: U=LOW | No root/heptad/source fields | **GATE FIX:** needs intel-specific validator, not body_quf |

### Summary

| Cause | Tables Affected | Rows | Action |
|-------|----------------|------|--------|
| **STALE GRADES** (old System 2) | entries, quran_refs, possibly others | ~400+ | Batch re-run with new AMR pipeline (needs performance fix) |
| **DATA GAPS** (missing fields) | roots, a4_derivatives, eu, latin, body_data, formula_scholars | ~1,500 | Data entry work — fill missing fields |
| **GATE FIXES** (wrong validator or missing field mapping) | quran_word_roots PARTICLEs, dp_register, body cross-refs, body prayer, formula_cross_refs, intel_file_index | ~27,000 | Fix gate definitions in AMR modules |

### Priority

1. **Gate fixes first** — 27,000 rows affected. Biggest: quran_word_roots PARTICLEs (set F=MEDIUM for PARTICLEs)
2. **Batch re-run** — update stale System 2 grades (needs performance fix: single connection, not per-row)
3. **Data gaps** — ongoing work, not urgent
