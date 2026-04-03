# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

# BITIG RESTORATION DB — Technical Reference (QALAM)

> Q68:1 — نٓ ۚ وَالْقَلَمِ وَمَا يَسْطُرُونَ / Nūn. wa-al-qalami wa-mā yasṭurūn / "Nūn. By the Pen and what they inscribe."

**Purpose:** Session-loadable reference for the Bitig Restoration DB. Load this instead of re-deriving schema, relationships, and query patterns each session.

**Date:** 2026-03-17 | **Version:** 1.0 (QALAM, Surah 13)

---

## 1. DATABASE SCHEMA — 14 TABLES

### 1.1 CORE TABLE: `bitig_a1_entries` (228 rows)

The central ORIG2 word database. Every other table links to this.

| Column | Type | Description |
|--------|------|-------------|
| `entry_id` | INTEGER PK | Unique entry ID (1-228) |
| `score` | INTEGER | MĪZĀN quality score (5-10, rubric-based) |
| `orig2_term` | TEXT | Bitig/Turkic original form (Latin transcription) |
| `orig2_script` | TEXT | Orkhon/Arabic script form (when available) |
| `root_letters` | TEXT | Consonantal skeleton (e.g., t-l-k for tuluk) |
| `kashgari_attestation` | TEXT | Dīwān Lughāt al-Turk attestation |
| `ibn_sina_attestation` | TEXT | Ibn Sīnā attestation (rarely filled) |
| `modern_reflexes` | TEXT | Modern Turkic reflexes |
| `navoi_attestation` | TEXT | Alisher Navoi attestation |
| `downstream_forms` | TEXT | Downstream forms in target languages |
| `phonetic_chain` | TEXT | B-coded phonetic chain (e.g., q→к(B01), a→а(VPRES)) |
| `semantic_field` | TEXT | One of 20 fields: MILITARY, NATURE, FOOD, etc. |
| `dispersal_range` | TEXT | Geographic range: CENTRAL EURASIA, TURKIC+SLAVIC, etc. |
| `status` | TEXT | CONFIRMED (153) or PENDING_VERIFICATION (75) |
| `notes` | TEXT | Substantive notes with Kashgari + AA parallel |

**Score distribution:** 10:20, 9:36, 8:105, 7:63, 6:3, 5:1 | Mean: 8.02 (post-KAWTHAR)
**Status:** 153 CONFIRMED (67.1%), 75 PENDING (32.9%)
**Chains:** 228/228 (100%)

### 1.2 SHIFT TABLE: `bitig_shift_register` (25 rows)

B-codes: the ORIG2→downstream phonetic shift register (parallel to M1 S01-S26 for ORIG1).

| Column | Type | Description |
|--------|------|-------------|
| `shift_id` | TEXT PK | B-code ID (B01-B25) |
| `shift_type` | TEXT NN | CONSONANT_SHIFT, VOWEL_SHIFT, MORPHOLOGICAL, PRESERVATION, CONSONANT_DEVOICE, CONSONANT_VOICE, CONSONANT_ASSIM, CONSONANT_FRIC |
| `orig2_phoneme` | TEXT NN | Source phoneme in Bitig |
| `phoneme_name` | TEXT NN | Phonetic description |
| `ru_outputs` | TEXT | Russian output(s) |
| `tr_outputs` | TEXT | Turkish output(s) |
| `en_outputs` | TEXT | English output(s) |
| `regularity_pct` | REAL | Percentage regularity |
| `frequency` | INTEGER | How many entries use this shift |
| `s_code_parallel` | TEXT | Corresponding S-code in ORIG1 corridor (or NULL = ORIG2-unique) |
| `examples` | TEXT NN | Example words |
| `entry_ids` | TEXT | Comma-separated entry_id list |
| `notes` | TEXT | Notes |
| `is_orig2_unique` | INTEGER | 1 = no S-code parallel (diagnostic ORIG2 marker) |

**11 ORIG2-unique shifts (diagnostic markers):**
B03 (ŋ velar nasal), B06 (word-final devoicing), B07 (ü), B08 (ö), B09 (ı),
B10 (prothetic в-), B11 (a-drop), B12 (suffix adaptation), B13 (vowel harmony loss),
B23 (n→м labial assimilation), B25 (p→ф labial fricative)

### 1.3 DEGRADATION: `bitig_degradation_register` (38 rows)

Tracks semantic degradation of Bitig words in downstream languages.

| Column | Type | Description |
|--------|------|-------------|
| `deg_id` | TEXT PK | BD01-BD38 |
| `bitig_original` | TEXT NN | Original Bitig form (may include Orkhon script) |
| `bitig_script` | TEXT | Orkhon script form |
| `original_meaning` | TEXT NN | Sovereign/neutral Bitig meaning |
| `downstream_form` | TEXT NN | Degraded form in target language |
| `downstream_language` | TEXT NN | Target language(s) |
| `degraded_meaning` | TEXT NN | Degraded downstream meaning |
| `degradation_type` | TEXT NN | Type label (e.g., SOVEREIGNTY→MOB, WARRIOR→SERF) |
| `dp_codes` | TEXT | Detection pattern codes (DP05, DP07, DP09, DP11, DP14, DP17) |
| `lattice_source` | TEXT | Reference to main lattice entries |
| `kashgari_ref` | TEXT | Kashgari Dīwān reference |
| `notes` | TEXT | Intelligence notes |
| `intel_refs` | TEXT | Cross-links to bitig_intelligence_summary (ḤASHR) |

**27 unique degradation types. DP code frequency: DP09(23), DP07(17), DP05(16), DP14(6), DP11(2), DP17(1).**

### 1.4 CONVERGENCE: `bitig_convergence_register` (15 rows)

Two-Original (ORIG1+ORIG2) convergence points — where Allah's Arabic and Bitig share a root.

| Column | Type | Description |
|--------|------|-------------|
| `conv_id` | TEXT PK | CV01-CV15 |
| `orig2_term` | TEXT NN | Bitig form |
| `orig2_root` | TEXT NN | ORIG2 consonantal root |
| `orig2_meaning` | TEXT NN | ORIG2 meaning |
| `orig1_root` | TEXT NN | Allah's Arabic root |
| `orig1_root_letters` | TEXT NN | ORIG1 consonantal root letters |
| `orig1_meaning` | TEXT NN | ORIG1 meaning |
| `quranic_ref` | TEXT | Qur'anic attestation |
| `shared_semantics` | TEXT NN | Shared semantic domain |
| `consonantal_match` | TEXT NN | Consonantal correspondence |
| `shift_ids` | TEXT | B-codes / S-codes used |
| `convergence_type` | TEXT NN | ROOT_MATCH(5), COMPOUND(4), AA_THROUGH_TURKIC(4), SEMANTIC_OVERLAP(2) |
| `status` | TEXT | ALL 15 = CONFIRMED (via FURQĀN adjudication) |
| `lattice_refs` | TEXT | References to main lattice |
| `notes` | TEXT | Includes FURQĀN scores (e.g., "10/10 (G1:2 G2:2 G3:2 G4:2 G5:2)") |

### 1.5 DISPERSAL: `bitig_dispersal_edges` (276 rows)

Language dispersal network — how Bitig words spread across languages.

| Column | Type | Description |
|--------|------|-------------|
| `edge_id` | INTEGER PK | Auto-increment |
| `bitig_entry_id` | INTEGER NN FK→bitig_a1_entries | Source entry |
| `orig2_term` | TEXT NN | Bitig form |
| `target_language` | TEXT NN | Target language name |
| `target_form` | TEXT | Form in target language |
| `meaning_preserved` | INTEGER | 1=preserved, 0=degraded |
| `degradation_id` | TEXT | FK→bitig_degradation_register if degraded |

**Distribution:** Russian 196 (38 degraded=19%), Turkish 23, English 18 (4 degraded), "Persian" 9, FR/ES/IT/DE/PT 5 each, Hungarian 3, Mongolian 2.

### 1.6 SIBLING PROPAGATION: `bitig_sibling_propagation` (56 rows)

Bitig words that entered sibling languages via Ottoman/Hungarian/Mongol corridors (ISRĀ').

| Column | Type | Description |
|--------|------|-------------|
| `prop_id` | INTEGER PK | Auto-increment |
| `bitig_entry_id` | INTEGER FK→bitig_a1_entries | Source entry |
| `orig2_term` | TEXT NN | Bitig form |
| `target_language` | TEXT NN | EN, FA, FR, ES, IT, DE, PT |
| `target_form` | TEXT NN | Form in target language |
| `corridor` | TEXT NN | Entry corridor (Ottoman, Hungarian, Mongol, Direct) |
| `meaning_preserved` | INTEGER | 1=preserved, 0=degraded |
| `degradation_type` | TEXT | If degraded, type |
| `phonetic_chain` | TEXT | B-coded chain |
| `notes` | TEXT | Notes |

**Key finding: European corridor (FR/ES/IT/DE/PT) = ZERO degradation. Only EN (2/15) and FA (1/11) show degradation.**

### 1.7 INTELLIGENCE: `bitig_intelligence_summary` (16 rows)

ḤASHR intelligence integration — unified operation profile from 38 degradation cases.

| Column | Type | Description |
|--------|------|-------------|
| `intel_id` | TEXT PK | INT-DP##, INT-TL##, INT-OP##, INT-UP01 |
| `category` | TEXT NN | DP_ANALYSIS(6), TIMELINE(5), OPERATOR_PATTERN(4), UNIFIED_PICTURE(1) |
| `dp_code` | TEXT | DP code (for DP_ANALYSIS category) |
| `frequency` | INTEGER | Number of cases |
| `operation_signature` | TEXT | Description of the operation |
| `peak_period` | TEXT | Historical period |
| `case_ids` | TEXT | Comma-separated BD## IDs |
| `target_language` | TEXT | Primary target |
| `intelligence_assessment` | TEXT | Full assessment |
| `notes` | TEXT | Additional intelligence notes |

### 1.8 BRIDGE CROSS-REFS: `bitig_bridge_xref` (13 rows)

Links bitig_a1_entries to convergence_register entries.

| Column | Type | Description |
|--------|------|-------------|
| `xref_id` | INTEGER PK | Auto-increment |
| `bitig_entry_id` | INTEGER FK→bitig_a1_entries | Entry |
| `convergence_id` | TEXT NN FK→bitig_convergence_register | Convergence point |
| `relationship` | TEXT NN | Relationship type |

### 1.9-1.14 SUPPORT TABLES

| Table | Rows | Purpose | Key Columns |
|-------|:----:|---------|-------------|
| `bitig_corrections` | 8 | Tracked corrections | corr_id, what_was_wrong, corrected_to, evidence |
| `bitig_investigation` | 8 | Open investigations | inv_id, word, meaning, status, issue |
| `bitig_orig2_sources` | 10 | Primary Bitig sources | source_id, name, date, work, significance |
| `bitig_protocol` | 29 | Protocol rules | Single بِسْمِ column |
| `bitig_semantic_fields` | 10 | Field definitions | field_id, domain, arabic_name, entry_count |
| `bitig_dispersal_map` | 10 | Detailed per-language attestation | orig2_word + 11 language columns |

---

## 2. FOREIGN KEY RELATIONSHIPS

```
bitig_a1_entries (228)
  ├── bitig_dispersal_edges (276) ← bitig_entry_id
  ├── bitig_sibling_propagation (56) ← bitig_entry_id
  └── bitig_bridge_xref (13) ← bitig_entry_id
        └── bitig_convergence_register (15) ← convergence_id

bitig_degradation_register (38)
  └── intel_refs → bitig_intelligence_summary (16) [text cross-link]
  └── bitig_dispersal_edges.degradation_id [text cross-link]
```

---

## 3. ESSENTIAL QUERIES

### 3.1 Entry Lookup

```sql
-- Find a Bitig entry by term
SELECT * FROM bitig_a1_entries WHERE orig2_term LIKE '%ordu%';

-- Find all entries in a semantic field
SELECT entry_id, orig2_term, score, status FROM bitig_a1_entries
WHERE semantic_field = 'MILITARY' ORDER BY score DESC;

-- Score distribution
SELECT score, COUNT(*) FROM bitig_a1_entries GROUP BY score ORDER BY score DESC;
```

### 3.2 Degradation Analysis

```sql
-- All degradation cases for a term
SELECT * FROM bitig_degradation_register WHERE bitig_original LIKE '%ordu%';

-- Cases by DP code (note: dp_codes may contain multiple codes separated by +/,)
SELECT deg_id, bitig_original, degradation_type FROM bitig_degradation_register
WHERE dp_codes LIKE '%DP09%' ORDER BY deg_id;

-- Cases with intelligence cross-links
SELECT deg_id, bitig_original, degradation_type, intel_refs
FROM bitig_degradation_register WHERE intel_refs IS NOT NULL ORDER BY deg_id;
```

### 3.3 Convergence Points

```sql
-- All confirmed convergences
SELECT conv_id, orig2_term, orig1_root, convergence_type, notes
FROM bitig_convergence_register WHERE status = 'CONFIRMED';

-- ROOT_MATCH convergences (strongest evidence)
SELECT * FROM bitig_convergence_register WHERE convergence_type = 'ROOT_MATCH';
```

### 3.4 Dispersal Network

```sql
-- All dispersal edges for a specific entry
SELECT d.target_language, d.target_form, d.meaning_preserved, d.degradation_id
FROM bitig_dispersal_edges d
WHERE d.bitig_entry_id = (SELECT entry_id FROM bitig_a1_entries WHERE orig2_term = 'ordu');

-- Degradation rate by language
SELECT target_language, COUNT(*) as total,
  SUM(CASE WHEN meaning_preserved=0 THEN 1 ELSE 0 END) as degraded,
  ROUND(100.0 * SUM(CASE WHEN meaning_preserved=0 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_degraded
FROM bitig_dispersal_edges GROUP BY target_language ORDER BY total DESC;
```

### 3.5 Sibling Propagation

```sql
-- All sibling edges for a term
SELECT target_language, target_form, corridor, meaning_preserved
FROM bitig_sibling_propagation WHERE orig2_term = 'yogurt';

-- Degradation by corridor
SELECT corridor, COUNT(*), SUM(CASE WHEN meaning_preserved=0 THEN 1 ELSE 0 END) as degraded
FROM bitig_sibling_propagation GROUP BY corridor;
```

### 3.6 Intelligence Analysis

```sql
-- All DP analysis records
SELECT intel_id, dp_code, frequency, operation_signature
FROM bitig_intelligence_summary WHERE category = 'DP_ANALYSIS' ORDER BY frequency DESC;

-- Timeline phases
SELECT intel_id, peak_period, operation_signature
FROM bitig_intelligence_summary WHERE category = 'TIMELINE' ORDER BY intel_id;

-- Operator patterns
SELECT intel_id, operation_signature, case_ids
FROM bitig_intelligence_summary WHERE category = 'OPERATOR_PATTERN';

-- Unified picture
SELECT * FROM bitig_intelligence_summary WHERE category = 'UNIFIED_PICTURE';
```

### 3.7 B-Code Shift Analysis

```sql
-- All ORIG2-unique shifts
SELECT shift_id, shift_type, orig2_phoneme, phoneme_name, ru_outputs
FROM bitig_shift_register WHERE is_orig2_unique = 1 ORDER BY shift_id;

-- Most frequent shifts
SELECT shift_id, orig2_phoneme, ru_outputs, frequency
FROM bitig_shift_register WHERE frequency > 0 ORDER BY frequency DESC;
```

### 3.8 Cross-Table Joins

```sql
-- Entry + degradation + intelligence (full picture for a term)
SELECT a.entry_id, a.orig2_term, a.semantic_field, a.score,
  d.deg_id, d.degradation_type, d.dp_codes, d.intel_refs
FROM bitig_a1_entries a
JOIN bitig_dispersal_edges e ON a.entry_id = e.bitig_entry_id AND e.meaning_preserved = 0
JOIN bitig_degradation_register d ON e.degradation_id = d.deg_id
ORDER BY a.orig2_term;

-- Entry + convergence (Two-Original link)
SELECT a.entry_id, a.orig2_term, c.conv_id, c.orig1_root, c.convergence_type, c.notes
FROM bitig_a1_entries a
JOIN bitig_bridge_xref x ON a.entry_id = x.bitig_entry_id
JOIN bitig_convergence_register c ON x.convergence_id = c.conv_id
ORDER BY c.conv_id;

-- Full dispersal for an entry across all tables
SELECT a.orig2_term,
  'dispersal' as source, e.target_language, e.target_form, e.meaning_preserved
FROM bitig_a1_entries a
JOIN bitig_dispersal_edges e ON a.entry_id = e.bitig_entry_id
WHERE a.orig2_term = 'ordu'
UNION ALL
SELECT a.orig2_term,
  'sibling' as source, s.target_language, s.target_form, s.meaning_preserved
FROM bitig_a1_entries a
JOIN bitig_sibling_propagation s ON a.entry_id = s.bitig_entry_id
WHERE a.orig2_term = 'ordu';
```

---

## 4. DATA FLOW DIAGRAM

```
                    ┌──────────────────────────────┐
                    │    BITIG SOURCE CORPUS        │
                    │  Orkhon inscriptions (8th c.) │
                    │  Kashgari Dīwān (1072 CE)     │
                    │  ЭСТЯ (Sevortyan)             │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     bitig_a1_entries (228)    │
                    │  Core ORIG2 word database     │
                    │  Score: 5-10 (mean 7.74)      │
                    │  Status: CONFIRMED/PENDING    │
                    └──┬────┬────┬────┬────┬───────┘
                       │    │    │    │    │
          ┌────────────┘    │    │    │    └─────────────┐
          ▼                 ▼    │    ▼                  ▼
  ┌───────────────┐ ┌──────────┐│┌──────────────┐ ┌──────────────┐
  │ bitig_shift   ││ bitig_   │││ bitig_       │ │ bitig_bridge │
  │ _register(25) ││ dispersal│││ sibling_     │ │ _xref (13)   │
  │ B01-B25       ││ _edges   │││ propagation  │ │              │
  │ Phonetic      ││ (276)    │││ (56)         │ │      │       │
  │ shift codes   ││ 11 langs │││ 7 langs      │ │      ▼       │
  └───────────────┘ └────┬─────┘│└──────────────┘ │┌────────────┐│
                         │      │                  ││ bitig_     ││
                         ▼      │                  ││ convergence││
              ┌──────────────┐  │                  ││ _register  ││
              │ bitig_       │  │                  ││ (15)       ││
              │ degradation_ │  │                  ││ ALL CONFMD ││
              │ register(38) │  │                  │└────────────┘│
              │ 27 types     │  │                  └──────────────┘
              │ 6 DP codes   │  │
              └──────┬───────┘  │
                     │          │
                     ▼          │
              ┌──────────────┐  │
              │ bitig_intel  │  │
              │ _summary(16) │  │
              │ 4 categories │◄─┘
              │ ḤASHR engine │
              └──────────────┘
```

---

## 5. INTELLIGENCE REFERENCE CARD

### 5.1 DP Codes Used in Bitig Degradation

| Code | Name | Count | Signature | Example |
|------|------|:-----:|-----------|---------|
| DP09 | Status inversion | 23 | Sovereign term → inverted meaning | ordu (HQ→mob) |
| DP07 | Existence erasure | 17 | Original meaning deleted from record | čardaq (palace→obsolete) |
| DP05 | Trivialization | 16 | Serious→comical/dismissive | балаган (market→circus) |
| DP14 | Master-parasite swap | 6 | Ruler vocabulary → servant vocabulary | batraq (warrior→serf) |
| DP11 | Colonial renaming | 2 | Original name → foreign label | bay→boyar |
| DP17 | Assembled identity | 1 | False etymology constructed | boyar "Slavic" origin |

### 5.2 Timeline

| Phase | Period | % Cases | Summary |
|-------|--------|:-------:|---------|
| TL01 Baseline | Pre-1200 | 0% | Intact Bitig corpus |
| TL02 Prestige | 1200-1480 | 0% | Words enter Russian as HIGH-STATUS |
| **TL03 Peak** | **1480-1700** | **61%** | **Post-conquest systematic inversion** |
| TL04 Codification | 1700-1917 | 39% | Academic works lock degradation |
| TL05 Perpetuation | 1917-present | 0% | Maintenance of inversions |

### 5.3 Compound Operations

| ID | Pattern | DP Codes | Target |
|----|---------|----------|--------|
| OP01 | INVERT-AND-ERASE | DP09+DP07 | Sovereignty vocabulary |
| OP02 | TRIVIALIZE-AND-ERASE | DP05+DP07 | Domestic/civilian vocabulary |
| OP03 | INVERT-AND-SWAP | DP09+DP14 | Power relationship vocabulary |
| OP04 | ERASE-RENAME-ASSEMBLE | DP07+DP11+DP17 | Identity titles |

### 5.4 High-Value Cases

| BD# | Term | Degradation | DP | Intel Refs |
|-----|------|-------------|-----|------------|
| BD01 | ordu | HQ→mob | DP09+DP05 | INT-DP09, INT-DP05, INT-TL03, INT-UP01 |
| BD05 | yasa | law→tax | DP09+DP14 | INT-DP09, INT-DP14, INT-TL03, INT-OP03, INT-UP01 |
| BD22 | yarlïɣ | decree→sticker | DP09+DP05 | INT-DP09, INT-DP05, INT-TL03, INT-UP01 |
| BD34 | batraq | warrior→serf | DP09+DP14+DP07 | INT-DP09, INT-DP07, INT-DP14, INT-TL04, INT-OP03, INT-UP01 |
| BD37 | bay | noble→boyar | DP07+DP11+DP17 | INT-DP07, INT-DP11, INT-DP17, INT-TL04, INT-OP04, INT-UP01 |

---

## 6. CONVERGENCE REFERENCE CARD

### 6.1 ROOT_MATCH (strongest evidence — pre-split roots)

| CV | ORIG2 | ORIG1 | Match | Score | Qur'anic |
|----|-------|-------|-------|:-----:|----------|
| CV06 | tamga (T-M-Ğ) stamp | دمغ (D-M-Gh) stamp | T↔D(S19), Ğ=Gh | 10/10 | Q21:18 |
| CV07 | balıq (B-L-Q) city | بلد (B-L-D) city | Q↔D gap | 8/10 | Q90:1 |
| CV13 | Temür (T-M-R) iron | دمر (D-M-R) destroy | T↔D(S19) | 10/10 | Q57:25 |
| CV14 | ordu (R-D) HQ | أرض (R-Ḍ) land | Ḍ→D | 9/10 | 444 tokens |
| CV15 | kün (K-N) day | كون (K-W-N) be | W absorbed | 10/10 | Q2:117 (كُنْ) |

### 6.2 FURQĀN Adjudication Gates

| Gate | Criterion | Points | Pass if |
|------|-----------|:------:|---------|
| G1 | Consonantal match | 2 | 3/3=2, 2/3=1, <2/3=0 |
| G2 | Semantic coherence | 2 | Same meaning=2, overlap=1, none=0 |
| G3 | Qur'anic attestation | 2 | Exact=2, tangential=1, absent=0 |
| G4 | Independent attestation | 2 | Both sides=2, one=1, neither=0 |
| G5 | Pattern integrity | 2 | Documented shift=2, plausible=1, none=0 |

**Threshold:** ≥7=CONFIRMED | 5-6=STRONG_CANDIDATE | <5=REJECT

---

## 7. B-CODE QUICK REFERENCE

### 7.1 Consonant Shifts (B01-B06, B21-B25)

| Code | Shift | Example | Frequency |
|------|-------|---------|:---------:|
| B01 | q→к | qalpaq→колпак | 61 |
| B02 | ğ/ɣ→г/х/∅ | toɣan→туган | 25 |
| B03★ | ŋ→н/∅ | — | rare |
| B04 | ç/č→ш/ч | čardaq→чертог | 6 |
| B05 | j→ж | — | 5 |
| B06★ | FINAL devoicing | — | systemic |
| B21 | b→п | bitig→письмо | 3 |
| B22 | t→д | tanbur→домра | 2 |
| B23★ | n→м | nišan→мишень | 1 |
| B24 | q→х | qamıt→хомут | 1 |
| B25★ | p→ф | puta→фата | 1 |

### 7.2 Vowel Shifts (B07-B09)

| Code | Shift | Example | Frequency |
|------|-------|---------|:---------:|
| B07★ | ü→у/ю/и | küterme→кутерьма | 22 |
| B08★ | ö→о/у | köpek→кобель | 6 |
| B09★ | ı→ы/и | qılıč→кляча | 11 |

### 7.3 Morphological (B10-B13)

| Code | Shift | Example | Frequency |
|------|-------|---------|:---------:|
| B10★ | prothetic в- | otaɣ→ватага | 2 |
| B11★ | initial a-drop | arslan→слон | 3 |
| B12★ | suffix adaptation | — | systemic |
| B13★ | vowel harmony loss | — | systemic |

### 7.4 Preservation (B14-B20)

| Code | Consonant | Frequency |
|------|-----------|:---------:|
| B14 | b=б | 22 |
| B15 | t=т | 58 |
| B16 | r=р | 47 |
| B17 | l=л | 34 |
| B18 | n=н | 23 |
| B19 | s=с | 15 |
| B20 | m=м | 14 |

★ = ORIG2-unique (no S-code parallel — diagnostic marker of Bitig origin)

---

## 8. CLI TOOL REFERENCE

**Tool:** `python3 Code_files/uslap_bitig.py [command]`

| Command | Function | Example Output |
|---------|----------|----------------|
| `status` | Full DB status with charts | Entry counts, score dist, status breakdown |
| `search TERM` | Search bitig_a1 + degradation + convergence + blacklist | All matching records across tables |
| `degrade` | List all 38 degradation cases with type summary | BD01-BD38 with degradation types |
| `converge` | List all 15 convergence points | CV01-CV15 with FURQĀN scores |
| `pending` | List 75 PENDING entries with source quality | Entry IDs needing verification |
| `verify ID` | Full Q/U/F gate verification for any entry | 3-gate pass/fail report |
| `fields` | Semantic field distribution | 20 fields with confirmed/pending counts |
| `add` | Print SQL template for new entries | INSERT template with all columns |
| `scan` | Scan for undocumented degradation/convergence | Candidate discovery |
| `dispersal` | Dispersal network statistics | Language distribution, degradation rates |

---

## 9. MĪZĀN SCORING RUBRIC (10-point)

| # | Criterion | Pass Condition | Current Rate |
|---|-----------|---------------|:------------:|
| 1 | CHAIN | B-coded phonetic chain present | 100% |
| 2 | SCRIPT | Orkhon/Arabic script documented | 35.5% (post-KAWTHAR, was 15.4%) |
| 3 | ROOT | Consonantal skeleton (not T-prefix) | 99.6% |
| 4 | KASHGARI | Dīwān attestation present | 100% |
| 5 | STATUS | CONFIRMED verification status | 67.1% |
| 6 | DS_MULTI | Downstream forms in 2+ languages | 93.9% (post-KAWTHAR, was 85.1%) |
| 7 | DS_DETAIL | Downstream forms detailed (>50 chars) | 97.8% |
| 8 | NOTES | Substantive notes (>80 chars) | 92.1% |
| 9 | DISPERSAL | Dispersal range classified | 100% |
| 10 | REGISTER | In degradation or convergence register | 16.2% |

**Non-auto-fillable blockers:** SCRIPT (requires Orkhon corpus), STATUS (requires source verification), REGISTER (requires degradation documentation).

---

## 10. SESSION STARTUP CHECKLIST

When starting a new session that involves the Bitig Restoration DB:

1. **Load this file:** `Read BITIG_TECHNICAL_REFERENCE.md` — gives you the complete schema, queries, and reference cards
2. **Check current state:** `sqlite3 Code_files/uslap_database_v3.db "SELECT COUNT(*) FROM bitig_a1_entries; SELECT COUNT(*) FROM bitig_degradation_register; SELECT COUNT(*) FROM bitig_convergence_register;"`
3. **Use CLI tool:** `python3 Code_files/uslap_bitig.py status` — formatted overview
4. **For specific entries:** Use queries from §3 above
5. **For intelligence:** Use queries from §3.6
6. **For cross-table analysis:** Use joins from §3.8

**DO NOT re-derive what is documented here.** This file IS the technical reference.

---

## 11. ARCHITECTURE STATUS

**14-Surah Architecture — BOTH HEPTADS COMPLETE ✅:**

| # | Surah | Name | Status | Engine Built |
|---|-------|------|:------:|---|
| 8 | BURŪJ | al-Burūj Q85 | ✅ | Phonetic shift table (25 B-codes, 228/228 chains) |
| 9 | MĪZĀN | al-Raḥmān Q55 | ✅ | Quality scoring engine (10-point rubric, 5 auto-fills) |
| 10 | FURQĀN | al-Furqān Q25 | ✅ | Convergence adjudication (5-gate rubric, 15/15 confirmed) |
| 11 | ISRĀ' | al-Isrā' Q17 | ✅ | Sibling propagation (56 edges, 7 languages, zero EU degradation) |
| 12 | ḤASHR | al-Ḥashr Q59 | ✅ | Intelligence integration (16 records, 4 compound operations) |
| 13 | QALAM | al-Qalam Q68 | ✅ | Documentation (this file + summary update) |
| 14 | KAWTHAR | al-Kawthar Q108 | ✅ | Expansion (81 Orkhon scripts, 21 dispersal_maps, mean 8.02) |

---

**وَاللَّهُ أَعْلَمُ**
