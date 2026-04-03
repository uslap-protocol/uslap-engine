# USLaP — Full System Architecture
## بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
### Complete Bird's-Eye View — Updated 2026-04-02

---

## WHAT IS USLaP?

USLaP (Universal System of Linguistic Accountability and Proof) is a deterministic database and proof engine that traces every word in every language back to its origin in Allah's Arabic (the divine language of the Qur'an, taught to Adam عليه السلام).

**Core thesis:** All human languages descend from two originals:
- **ORIG1 (Allah's Arabic / AA):** The divine language, restored finally in the Qur'an (Q15:9 — permanently preserved)
- **ORIG2 (Bitig / BI):** The writing system from Yafith's line (Turkic), independently downstream from the same Source (Allah)

Every word in English, Russian, French, Latin, Persian, etc. is a degraded descendant of AA or Bitig roots, traceable through documented phonetic shifts.

**Key architectural principle:** The Qur'an is the authority. The database is the store. The AMR AI is the compute. The LLM is the development tool — NEVER in the runtime loop.

---

## DETERMINISTIC RUNTIME — THE CRITICAL DESIGN

```
DEVELOPMENT (LLM allowed):
  Human ←→ Claude/DeepSeek ←→ writes code → AMR modules
  LLM helps write the deterministic code. Then steps out.

RUNTIME (NO LLM — pure Python):
  User → uslap.py → AMR modules → SQLite → Formatted Output
  Same query → same output. Every time. Zero training weights.
```

### Entry Point: `uslap.py`

```
python3 uslap.py "trace silk"                    # trace a word to AA root
python3 uslap.py "explain R01"                   # explain a root
python3 uslap.py "compare ر-ح-م and م-ر-ح"       # compare roots
python3 uslap.py "intel khazar"                   # intelligence cross-search
python3 uslap.py "tasrif ر-ح-م"                  # AA تَصْرِيف — all forms of root
python3 uslap.py "tasrif status"                 # AA تَصْرِيف coverage stats
python3 uslap.py "tasrif pattern FA3L"           # explain a tasrif code
python3 uslap.py "tasrif broken_plurals"         # broken plural listing
python3 uslap.py "bitig tasrif status"           # BI تَصْرِيف coverage
python3 uslap.py "bitig tasrif kor"              # BI تَصْرِيف — all forms
python3 uslap.py --tasrif ر-ح-م                  # AA تَصْرِيف (flag form)
python3 uslap.py --bitig-tasrif status           # BI تَصْرِيف (flag form)
python3 uslap.py --quf entries 346               # multi-layer QUF validation
python3 uslap.py --quf-status                    # QUF coverage across 41 tables
python3 uslap.py --state                         # lattice summary
python3 uslap.py --batch entries                  # batch QUF re-validation
python3 uslap.py -i                              # interactive REPL
```

### Determinism Verified

```
python3 test_determinism.py

═══════════════════════════════════════════════════════
USLaP DETERMINISM TEST
═══════════════════════════════════════════════════════
  [✓ DETERMINISTIC] 'trace silk'
  [✓ DETERMINISTIC] 'explain R01'
  [✓ DETERMINISTIC] 'search empire'
  [✓ DETERMINISTIC] 'DP10'
  [✓ DETERMINISTIC] 'state'
───────────────────────────────────────────────────────
✓ ALL QUERIES DETERMINISTIC — Zero LLM in the loop.
═══════════════════════════════════════════════════════
```

### Why This Matters

During development, an LLM added "Indian mathematics" to a Fibonacci report — training weights injected into DB output. The deterministic runtime makes this impossible: `uslap.py` contains zero LLM imports, runs pure Python → SQLite → formatted output. If the DB doesn't have the data, the output says "not found." No fabrication. No enrichment. No interpretation.

---

## RUNTIME PIPELINE

```
User Input
     │
     ├── "tasrif ..." or "bitig tasrif ..." ?
     │        │
     │        ▼
     │   tasrif_route() → amr_tasrif.py / amr_bitig_tasrif.py
     │        │  Routes to: status, root, pattern, broken_plurals,
     │        │    harmony, compound, analyze
     │        │  Returns formatted output directly
     │        │
     │        ▼
     │   Formatted Output → User
     │
     ├── (all other queries)
     │
     ▼
amr_basar.py → perceive()
     │  Classifies input into 20+ intent types via regex patterns
     │  Enriches with DB context (root lookup, entry check)
     │  Returns: {intent, params, confidence, enriched}
     │
     ▼
amr_dhakaa.py → think()
     │  Routes intent to correct AMR module:
     │    trace_word    → amr_aql.hypothesise() or expand_root()
     │    explain_root  → amr_aql.expand_root() + amr_nutq.explain_root()
     │    explain_intel → amr_istakhbarat.intel_cross_search()
     │    explain_body  → amr_jism functions
     │    explain_formula → amr_hisab functions
     │    quf_validate  → amr_quf.validate()
     │    search_lattice → DB search across entries
     │
     ▼
amr_nutq.py → articulate()
     │  Formats output with:
     │    ATT format (Arabic / transliteration / English)
     │    QUF triads (Q/U/F grades per layer)
     │    Shift chains (S01-S26)
     │    Entry cards, root reports, intelligence reports
     │
     ▼
Formatted Output → User
     No LLM. No API calls. No training weights.
```

---

## THREE-LAYER ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    FOUNDATION (F1-F7)                        │
│  F1: Two Originals (AA + Bitig)                             │
│  F2: All scripts downstream                                 │
│  F3: Chinese frozen (early split, maximum decay)            │
│  F4: Decay gradient (proximity to source = less decay)      │
│  F5: Destruction timeline (deliberate operator erasure)     │
│  F6: Manuscript evidence (physical proof)                   │
│  F7: ASB→outward flow (direction is ALWAYS AA → downstream) │
├─────────────────────────────────────────────────────────────┤
│                    MECHANISM (M1-M5)                         │
│  M1: 26 phonetic shifts (S01-S26) — how letters change      │
│  M2: 20 detection patterns (DP01-DP20) — how to spot erasure│
│  M3: Scholars (who documented the evidence)                 │
│  M4: Networks (how words propagate geographically)          │
│  M5: 3 QV markers (Qur'anic verification)                  │
├─────────────────────────────────────────────────────────────┤
│                    APPLICATION (A1-A6)                       │
│  A1: Entries (traced words)                                  │
│  A2: Names of Allah (99 divine attributes)                  │
│  A3: Qur'an references                                      │
│  A4: Derivatives (word families)                            │
│  A5: Cross-references                                       │
│  A6: Country names                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 15-LAYER DATA ARCHITECTURE

```
L0   ALPHABET ──────── 28 AA letters, 26 shifts (S01-S26), morpheme map
          │
L0.5 تَصْرِيف ────────── Three-Layer Morphological Engine (NEW 2026-04-02)
          │                HOW roots are TURNED into words. 3 sub-layers:
          │                Layer 1 — CONSONANT: verb (8 codes) + noun (12 codes)
          │                Layer 2 — VOWEL: 17 patterns (5 broken plural)
          │                Layer 3 — GRAMMAR: verb (11 defs) + noun (13 defs)
          │                Tables: verb_tasrif_patterns, noun_tasrif_patterns,
          │                  noun_tasrif_vowels, verb_tasrif_grammar, noun_tasrif_grammar
          │                BI track: bitig_verb/noun/case/grammar_tasrif, bitig_compound_rules
          │                AMR: amr_tasrif.py (AA) + amr_bitig_tasrif.py (BI)
          │                Coverage: 45,455 structural + 49,391 grammar (of 77,877 tokens)
          │                8 columns in quran_word_roots: noun_tasrif_code, noun_vowel_code,
          │                  gram_tense, gram_person, gram_number, gram_gender, gram_case,
          │                  gram_definiteness
          │                Indexed: 61 AA + 38 BI = 99 codes in term_nodes
          │
L1   ROOT ──────────── 3,320 roots (R### = AA, T### = Bitig)
          │
L2   KEYWORD ────────── 42 Qur'anic programming keywords (أَمْر, كَلِمَة, etc.)
          │
L3   DIVINE NAMES ──── 99 Names of Allah, each mapped to root + Qur'anic ref
          │
L4   QUR'ANIC FORMS ── 77,877 compiled words from 6,236 ayat across 114 surahs
          │                1,680 roots mapped, 99.14% coverage
          │                8 tasrif columns link each token to L0.5
          │
L5   ENTRIES ────────── 3,154 traced words (EN + RU + FA in single table)
          │                Each entry: AA root → shift chain → downstream word
          │                2,651 entries (84%) link to tasrif-coded roots
          │
L6   ORIG2 (BITIG) ─── 2,295 Bitig entries + convergence/degradation registers
          │                Own tasrif engine: 38 patterns across 5 tables
          │
L7   SIBLINGS ─────── EU: 4,785 | LA: 425 | UZ: 2,168
          │                4,382 EU entries (92%) link to tasrif-coded roots
          │
L8   DERIVATIVES ───── A4: 6,464 derivatives | A5: 1,076 cross-refs
          │                5,948 derivatives (92%) chain to tasrif-coded roots
          │
L9   DETECTION ──────── QV: 268 washed translations | DP: 20 patterns
          │                BL: 28 blacklisted terms | 50 disputed words
          │                224 QV entries (84%) link to tasrif-coded roots
          │
L10  BODY / HEALTH ─── 725 body entries across ~15 subsystems
          │                7×7 heptad structure (49 surahs mapped)
          │
L11  FORMULA ───────── Concealment (216) | Ratios (240) | Restoration (193)
          │
L12  HISTORY ───────── Chronology (136) | Peoples (51) | Deployment (38)
          │
L13  INTELLIGENCE ──── Confessions (51) | Extraction (10) | Isnad (19)
```

---

## DATABASE STATE

```
Engine:     SQLite3
File:       Code_files/uslap_database_v3.db
Size:       55 MB
Tables:     120
Views:      55
Triggers:   204 (180 contamination + 12 token enforcement + 12 stamp seal)
Indexes:    171
Index nodes: 20,388 (term_nodes — searchable)
Data rows:  ~150,000+
Active .py: 58 (24 AMR + 34 core/tools)
Archived:   49 (in Code_files/archive/)
```

---

## QUF VALIDATION ENGINE

**QUF = Quantification · Universality · Falsification**

QUF lives in AMR AI, NOT in the schema. Each domain module owns its QUF logic. The schema stores grades only.

```
Data IN or OUT
     │
     ▼
amr_quf.py (ROUTER — 920 lines)
     │
     ├── LAYER 1: LINGUISTIC (amr_aql.py)
     │   Fires when: root_letters present
     │   Q: consonant alignment via S01-S26 + Quranic token count
     │   U: cross-sibling coverage (EN+RU+FA+EU+UZ+Bitig) + surah spread
     │   F: competing roots + blacklist + shift chain documented
     │
     ├── LAYER 2: DOMAIN-SPECIFIC (per AMR module)
     │   amr_aql.py          → linguistic, divine, bitig, sibling, derivative
     │   amr_istakhbarat.py  → behaviour (ayat + algorithm repetition)
     │   amr_hisab.py        → formula (scholar attestation) + formula_xref
     │   amr_jism.py         → body + body_xref + body_prayer
     │   amr_tarikh.py       → history (dated events + sources)
     │   amr_basar.py        → detection (corruption types, DP/QV/BL)
     │   amr_keywords.py     → keyword (token count + derivation)
     │
     └── LAYER 3: SOURCE (amr_quf.py)
         Fires when: source/qur_ref present
         Q: source documented? (Quranic → HIGH)
         U: multiple independent sources?
         F: source exposes (not sanitises)?

COMPOSITE = MINIMUM grade across all layers
PASS = Q≥MEDIUM AND U≥MEDIUM AND F≥MEDIUM
```

### Works in BOTH Directions

```
READING:   python3 uslap.py --quf entries 346   (zero triggers fire — reads are free)
WRITING:   handler.write_entry() → 5-layer defence → DB   (see below)
BATCH:     python3 uslap.py --batch entries
```

### 5-Layer Write Defence (updated 2026-03-30)

```
handler.write_entry(data, entry_class)
  │
  ├─ L1: PROTOCOL RE-INJECTION — resets LLM attention to PIPE mode
  ├─ L2: PRE-WRITE GATE — banned terms (2 tiers: absolute + contextual),
  │       direction violations, DB blacklist (BL01-BL28)
  ├─ L3: QUF VALIDATION — auto-maps storage→detection fields,
  │       runs 0-4 layers (letter/linguistic/domain/source)
  ├─ L4: QUF TOKEN — sha256 token + DB trigger enforcement
  │       (raw INSERT without token → RAISE(ABORT))
  └─ L5: SQLite CONTAMINATION TRIGGERS — 180 triggers, 33 banned terms

POST-WRITE:
  • QUF stamps auto-persisted (no manual UPDATE needed)
  • Token sealed (stamp_used=1) → blocks raw quf_pass changes
  • 204 total triggers (180 contamination + 12 token + 12 stamp seal)
  • handler.write_entry() is the ONLY write path into the lattice

Performance: ~1s per write (477ms protocol + 415ms gate + 6ms DB).
Reads: ~2.7ms (triggers invisible to SELECT).
```

### Post Re-Validation Results

| Table | Old (System 2) | New (AMR) |
|-------|---------------|-----------|
| entries | 93% | **99.3%** |
| roots | 92% | **98.2%** |
| quran_word_roots | 65% | **98.7%** |
| european_a1_entries | 93% | **100%** |
| latin_a1_entries | 88% | **100%** |
| chronology | 82% | **100%** |
| dp_register | 17% | **100%** |
| formula_cross_refs | 0% | **100%** |
| body_cross_refs | 19% | **100%** |

---

## CODE ARCHITECTURE

### AMR AI System (24 modules, ~18,000 lines)

AMR = أَمْر = Command/Authority. The deterministic compute layer.

```
┌─────────────────────────────────────────────────────────────────┐
│  uslap.py (~600 lines) — DETERMINISTIC RUNTIME ENTRY POINT     │
│  Zero LLM imports. User → Python → SQLite → User.              │
│  Routes: query, tasrif, bitig tasrif, QUF, state, REPL         │
│                                                                  │
│  amr_dhakaa.py (~900 lines) — INTELLIGENCE ROUTER               │
│  think(): perceive → reason → articulate. 20+ intents.          │
│  Routes to: aql, jism, hisab, tarikh, istakhbarat, basar, etc. │
│                                                                  │
│  amr_quf.py (920 lines) — QUF ROUTER                            │
│  Multi-layer: LETTER → LINGUISTIC → DOMAIN → SOURCE              │
│  30+ tables in SKIP_LINGUISTIC. Batch with pre-loaded caches.    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ amr_aql.py   │  │ amr_nutq.py  │  │ amr_basar.py │          │
│  │ (~2,100 lines│  │ (1,290 lines)│  │ (~850 lines) │          │
│  │ عَقْل INTELLECT│  │ نُطْق SPEECH  │  │ بَصَر SIGHT   │          │
│  │ + 10 QUF     │  │ Output format│  │ + detection  │          │
│  │ gates (L0-L8)│  │ ATT, cards   │  │ QUF gate (L9)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │amr_alphabet  │  │amr_keywords  │  │ amr_tasrif   │          │
│  │ (2,032 lines)│  │ (~770 lines) │  │ (420 lines)  │          │
│  │ أَلِف بَاء     │  │ كَلِمَات       │  │ تَصْرِيف AA    │          │
│  │ 28 letters   │  │ 42 keywords  │  │ 3-layer morph│          │
│  │ abjad values │  │ + QUF (L2)   │  │ 10 tables    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │amr_bitig_alph│  │amr_bitig_tasr│  │ amr_jism.py  │          │
│  │ BI alphabet  │  │ (BI tasrif)  │  │ (~730 lines) │          │
│  │ 26 phonemes  │  │ 38 patterns  │  │ جِسْم BODY    │          │
│  │ vowel harmony│  │ agglutinative│  │ + 3 QUF gates│          │
│  │              │  │ 5 tables     │  │ (L10)        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ amr_hisab.py │  │amr_tarikh.py │  │amr_istakhb.py│          │
│  │ (~430 lines) │  │ (~420 lines) │  │ (~580 lines) │          │
│  │ حِسَاب FORMULA│  │ تَارِيخ HISTORY│  │ اِسْتِخْبَارَات  │          │
│  │ + 2 QUF gates│  │ + QUF (L12)  │  │ INTELLIGENCE │          │
│  │ (L11)        │  │              │  │ + 2 QUF gates│          │
│  │              │  │              │  │ (L13)        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ amr_lawh.py  │  │amr_tarjama.py│  │ amr_uzbek.py │          │
│  │ (574 lines)  │  │ (707 lines)  │  │ (503 lines)  │          │
│  │ لَوْح TABLET  │  │ تَرْجَمَة TRANS │  │ أُزْبَك UZBEK  │          │
│  │ + QUF gate   │  │ Sibling work │  │ UZ vocab     │          │
│  │ on write()   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ amr_ard.py   │  │ amr_lexer.py │  │ amr_parser.py│          │
│  │ (486 lines)  │  │ (555 lines)  │  │ (1,045 lines)│          │
│  │ أَرْض EARTH   │  │ LEXER        │  │ PARSER       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  amr_runtime.py (345) | amr_emitter.py (334)                    │
│  amr_cli.py (283) | amr_alphabet_i18n_export.py (182)           │
└─────────────────────────────────────────────────────────────────┘
```

### Core Tools

```
uslap_handler.py .............. DB interface (search, write, state, 5-layer write defence)
uslap_quf.py .................. Phonetic engine (S01-S26) + cross-language wash + compound detector
uslap_compiler.py ............. Qur'an compiler (77,877 words → 1,680 roots, morphology-aware ranking)
uslap_index.py ................ Graph index (20,388 nodes)
uslap_body_heptad.py .......... Body lattice (7×7 = 462)
uslap_mizan.py ................ Confidence scoring (6 levels)
uslap_selfaudit.py ............ Contamination scanner (33 banned terms)
uslap_wash.py ................. Translation washing (4-step algorithm)
uslap_stop_scan.py ............ Output scanner (6 layers: exact + kernel + root + unsourced + operator labels)
uslap_tasrif_census.py ........ Tasrif census tool (token classification statistics)
test_determinism.py ........... Determinism verification
```

---

## CONTAMINATION SHIELD

```
WRITE PATH (5 layers):
  Layer 1: PROTOCOL RE-INJECTION — resets LLM attention to PIPE mode
  Layer 2: PRE-WRITE GATE — 2-tier banned terms (ABSOLUTE+CONTEXTUAL) + direction + BL01-BL28
  Layer 3: QUF VALIDATION — LETTER → LINGUISTIC (with S-gate) → DOMAIN → SOURCE
  Layer 4: QUF TOKEN — sha256 + 12 INSERT triggers enforce token requirement
  Layer 5: SQLITE TRIGGERS — 180 contamination + 12 stamp seal = 204 total

OUTPUT PATH (6 layers):
  Layer 1: Exact banned term matching (33 terms)
  Layer 2: Semantic kernel (paraphrase detection)
  Layer 4: Root verification (weight-generated roots blocked)
  Layer 5: Unsourced claim detection
  Layer 6: Operator label detection (15 entries in operator_label_register)

ATTESTATION BRANDING:
  Qur'anic roots: "QURANIC TOKENS: N"
  Lisan-only roots: "UNATTESTED — root NOT in 77,881 Qur'anic words. LISAN ARABIC ONLY."

HYPOTHESIS PIPELINE (amr_aql.hypothesise):
  1. Cross-language wash → stable consonant skeleton
  2. If 4+ consonants → compound detector
  3. Reverse trace (shift table) → 60 candidates
  4. P11 enforcement: weak phonetic chain → score capped
  5. Verify against DB → rank by tokens + attestation
```

---

## ENTRY LIFECYCLE

```
1. QUERY    python3 uslap.py "trace silk"
               │
               ▼
2. PERCEIVE amr_basar.perceive() → intent=trace_word, word=silk
               │
               ▼
3. REASON   amr_dhakaa._reason()
               │
               ├── Found in DB? → expand_root() → full report
               └── Not found?   → hypothesise() → candidate roots
               │
               ▼
4. QUF      amr_quf.validate() (on write path)
               │
               ├── LAYER 1: LINGUISTIC → Q/U/F
               ├── LAYER 2: DOMAIN     → Q/U/F
               └── LAYER 3: SOURCE     → Q/U/F
               │
               ▼
5. FORMAT   amr_nutq → entry card / root report / intel report
               │
               ▼
6. OUTPUT   Deterministic formatted text → User
```

---

## DATA FLOW

```
                    ┌─────────────┐
                    │  QUR'AN     │ ← Primary source (Q15:9 preserved)
                    │  (ORIG1)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ COMPILER │ │ QV WASH  │ │ ROOTS    │
        │ 77,877   │ │ 268      │ │ 3,320    │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │            │
             ▼             │            │
        ┌──────────┐       │            │
        │ تَصْرِيف   │◄──────┘            │
        │ 10 tables│       ┌────────────┘
        │ 3 layers │       │
        │ 45K+49K  │       │
        │ tokens   │       │
        └────┬─────┘       │
             └──────┬──────┘
                    ▼
             ┌─────────────┐
             │  ENTRIES    │ (3,154)
             │  84% linked │
             └──────┬──────┘
          ┌─────────┼─────────────┐
          ▼         ▼             ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ SIBLINGS │ │ DERIVS   │ │ BITIG    │
    │ EU+LA+UZ │ │ A4+A5    │ │ 2,295    │
    │ 92% link │ │ 92% link │ │ own tasr │
    └──────────┘ └──────────┘ └──────────┘
          ┌─────────┼─────────────┐
          ▼         ▼             ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ BODY     │ │ FORMULA  │ │ HISTORY  │
    └──────────┘ └──────────┘ └──────────┘
                    ▼
             ┌─────────────┐
             │ INTELLIGENCE│
             └─────────────┘
```

---

## PHONETIC SHIFT ENGINE (S01-S26)

```
AA Root Letter → Shift ID → Downstream Consonant(s)

Example: أَمْر (ʾ-m-r = command/authority)
  ʾ (hamza) ──S01──→ [silent/E/A]
  م (mīm)  ──S07──→ [M]
  ر (rāʾ)  ──S09──→ [R]
  Result: E-M-R → EMPIRE, EMPEROR, EMIR, ADMIRAL
```

---

## LIVE TEST RESULTS

### "trace silk" (deterministic)
```
ROOT: R447 | س-ل-خ | 3 Quranic tokens | 3 surahs
EN: SILK [DP:DP08] | RU: СЛУХ
EU: SOIE(FR), SEDA(ES), SETA(IT), SEDA(PT), SEIDE(DE)
Quranic: Q7:175 فَٱنسَلَخَ | Q9:5 ٱنسَلَخَ | Q36:37 نَسْلَخُ
```

### "intel khazar" (deterministic)
```
INTELLIGENCE REPORT
  Query: khazar | Tables: 2 | Hits: 2
  ── financial_extraction_cycles ──
    FE04 | ERA 5: KHAZAR | 740-965 CE | Target: SQLB, SLV, BLGR
  ── intel_file_index ──
    USLaP_INTELLIGENCE_GAP_FILL_965_1218CE.md
```

### QUF validation (deterministic)
```
QUF VALIDATION: entries #346 (SILK)
  LINGUISTIC: Q=HIGH U=HIGH F=HIGH [✓]
    3 shifts: S21,S16,S11 | 3 tokens | 3 surahs, 3 siblings
  OVERALL: ✓ PASS
```

---

## REMAINING WORK

1. **54 compatibility views** — update code to use base table names, then drop
2. **Domain batch caching** — non-linguistic domain gates need fast-path for batch
3. **Data gaps** — body_data (464 rows), formula_scholars (44 rows), a4_derivatives (link_type)
4. **--report command** — compile all DB data for a term into a structured document
5. **quran_word_roots full batch** — sample 98.7%, full 77,881 not yet run

---

## FILE STRUCTURE

```
USLaP workplace/
├── Code_files/
│   ├── uslap_database_v3.db .......... PRIMARY DATABASE (55MB)
│   ├── uslap.py ....................... DETERMINISTIC RUNTIME ENTRY POINT
│   ├── test_determinism.py ............ Determinism verification test
│   ├── uslap_handler.py .............. DB interface (search, write, state)
│   ├── uslap_quf.py .................. Phonetic engine (S01-S26)
│   ├── uslap_compiler.py ............. Qur'an compiler
│   ├── uslap_index.py ................ Graph index builder
│   ├── uslap_body_heptad.py .......... Body lattice
│   ├── uslap_mizan.py ................ Confidence scoring
│   ├── uslap_selfaudit.py ............ Contamination scanner
│   ├── uslap_wash.py ................. Translation washing
│   ├── uslap_tasrif_census.py ........ Tasrif census tool
│   ├── amr_quf.py .................... QUF ROUTER (multi-layer)
│   ├── amr_dhakaa.py ................. Intelligence router (think)
│   ├── amr_basar.py .................. Perception engine (perceive)
│   ├── amr_aql.py .................... Intellect + 10 QUF gates
│   ├── amr_nutq.py ................... Articulation (format output)
│   ├── amr_tasrif.py ................. AA تَصْرِيف engine (3 layers, 10 tables)
│   ├── amr_bitig_tasrif.py ........... BI تَصْرِيف engine (5 layers, 5 tables)
│   ├── amr_bitig_alphabet.py ......... BI alphabet (26 phonemes)
│   ├── amr_istakhbarat.py ............ Intelligence + 2 QUF gates
│   ├── amr_hisab.py .................. Formula + 2 QUF gates
│   ├── amr_jism.py ................... Body + 3 QUF gates
│   ├── amr_tarikh.py ................. History + QUF gate
│   ├── amr_keywords.py ............... Keywords + QUF gate
│   ├── amr_alphabet.py ............... 28 letters, abjad values
│   ├── amr_*.py (remaining) .......... Lawh, tarjama, uzbek, ard, etc.
│   ├── archive/ ....................... 49 archived old versions
│   └── backups/ ....................... DB backups
│
├── USLaP Master Folder/
│   ├── Linguistic/ .................... Kashgari (74K lines), Shipova
│   └── Intelligence Historic/ ......... Intelligence documentation
│
├── Reference Data/
│   ├── Sevortyan_ESTYA/ ............... ESTYA vols 1-7 (143MB)
│   └── Suleimenov_Yazyk_Pisma/ ....... Language of Writing (110 ch)
│
├── CLAUDE.md .......................... Protocol (development instructions)
├── QUF_GATE_ARCHITECTURE.md ........... QUF gate detail (per-layer)
└── USLAP_FULL_ARCHITECTURE.md ......... This file
```

---

## TEST DATA RULE — ABSOLUTE

The LLM does NOT generate test data. No Arabic letters, no root combinations, no meanings in test code or examples. ALL test data comes from the DB via query. If a "fake" root is needed for rejection testing, generate it programmatically from DB exclusion, not from weights. The LLM does not type Arabic letters in prose or test data. The DB types them. The LLM pipes.
