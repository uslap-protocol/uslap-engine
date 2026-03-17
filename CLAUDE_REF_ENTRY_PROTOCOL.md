# USLaP REFERENCE — ENTRY PROTOCOL, QUF VERIFICATION & SCORING

> **Load this file when:** writing a new entry to the lattice, running QUF gates, or scoring entries.
> **Parent file:** CLAUDE.md (core)

---

## ENTRY FORMAT (A1_ENTRIES COLUMNS)

Every entry in A1_ENTRIES has 14 columns:

| Col | Field | Description |
|-----|-------|-------------|
| A | ENTRY_ID | Integer. Sequential. Check last ID before adding. |
| B | SCORE | Integer 1–10. Target: 10/10 for all new entries. |
| C | EN_TERM | English word (capitalised). |
| D | AR_WORD | Arabic/Turkic source word with full diacritics. |
| E | ROOT_ID | Root identifier (R001, R002...). Check for existing roots before creating new ones. |
| F | ROOT_LETTERS | Arabic root letters separated by hyphens: ق-ص-ر |
| G | QUR_MEANING | Qur'anic/original meaning in **ATT format** (see below). |
| H | PATTERN | A (Hidden), B (Direct loanword), C (Confessional), D (Jāhilīan), or combos like A+D. |
| I | ALLAH_NAME_ID | A01–A17+ if the entry contains a Name of Allah. Otherwise blank. |
| J | NETWORK_ID | N01–N11+ if entry belongs to a network. Otherwise blank. |
| K | PHONETIC_CHAIN | Full chain showing each consonant mapped via shift table. e.g. "ق→c(S01),ص→s(S13),ر→r(S15)" |
| L | INVERSION_TYPE | HIDDEN, CONFESSIONAL, DIRECT, etc. |
| M | SOURCE_FORM | The Arabic/Turkic word in transliteration. |
| N | FOUNDATION_REF | The Qur'anic verse in **ATT format**, foundation layer refs, detection patterns, and refutation notes. |


---

## QUF TRIAD VERIFICATION (EVERY ENTRY MUST PASS)

Before any entry is accepted, it must pass all three tests:

### Q — Qur'anic Attestation
- The Arabic root word MUST appear in the Qur'an (or for ORIG2 entries, in attested Turkic inscriptions)
- Provide specific verse reference (e.g. Q88:22)
- Show the word IN the verse in ATT format
- Multiple attestations strengthen the entry

### U — Phonetic Unity (Shift Table Compliance)
- EVERY consonant in the English word must trace back to an Arabic/Turkic root consonant
- Each mapping must reference a specific Shift ID (S01–S25)
- Format: "ق→c(S01), ص→s(S13), ر→r(S15)"
- Permitted operations: consonant shift (via table), vowel absorption, standard prefix (al-→al, مُ→m), metathesis (with precedent)
- FORBIDDEN: unexplained consonants, shifts not in the table, semantic-only connections

### F — Foundation Layer Alignment
- Entry must connect to at least one Foundation layer (F1–F7)
- Typically F2 (downstream script corridor) — specify DS04 (Greek), DS05 (Latin), DS06 (Germanic), etc.
- Detection patterns (DP01–DP18) should be identified where applicable
- Network membership (N01–N13) noted if relevant

**Self-Audit**: After generating each candidate, run the QUF triad explicitly. If any test fails, reject the candidate. Do not force entries.

---

## 10/10 SCORING CRITERIA

An entry scores 10/10 when ALL of the following are true:
1. **All root consonants preserved** (or shifts documented with S-IDs)
2. **Qur'anic attestation** with specific verse(s)
3. **Semantic connection** between Arabic meaning and English meaning is clear
4. **Foundation layer** identified
5. **Detection pattern(s)** identified where applicable
6. **No competing Arabic root** that better explains the English word
7. **Phonetic chain** is clean (no unexplained consonants or additions)
8. **ATT format** used throughout
9. **Derivatives** identified (the English word spawns further words from the same root)
10. **Network potential** — connects to existing entries or creates new links

### SCORE CAPS (MANDATORY — NEVER OVERRIDE)

| Condition | Maximum Score | Reason |
|-----------|--------------|--------|
| **SEM_REVIEW flagged** | **7** | Semantic gap between root meaning and downstream meaning = WRONG ROOT, not "almost right." A phonetic match with no semantic lock is a false positive. Fix the root, THEN re-score. |
| **Competing root exists** (criterion 6 fails) | **6** | If another root explains the word better, this entry is a candidate, not confirmed. |
| **No Qur'anic attestation** (criterion 2 fails) | **5** | Without Qur'anic anchor, the chain floats. ORIG2 entries exempt (use Bitig attestation instead). |
| **Unexplained consonant** (criterion 7 fails) | **4** | A consonant that doesn't map through S01–S26 = the chain is broken. |

**Enforcement:** These caps are HARD CEILINGS. An entry cannot score above the cap regardless of how many other criteria it passes. Example: ХОЗЯИН #230 was scored 9/10 with SEM_REVIEW — this should have been capped at 7. The root was WRONG (حزن/grief instead of خزن/treasure). The high score masked the error.


---

## WORKFLOW FOR ADDING NEW ENTRIES

1. **Check the file first** — read current last ENTRY_ID and last ROOT_ID
2. **Generate candidate** — identify English word, trace consonants back through shift table
3. **Find Qur'anic attestation** — locate the root in the Qur'an with specific verse
4. **Run QUF triad** — verify Q, U, F all pass
5. **Self-audit** — check for duplicate entries, duplicate roots, and competing explanations
6. **Build the entry** — all 14 columns, ATT format throughout
7. **Update related tabs** — A2 (if Name of Allah), A3 (Qur'an refs), A4 (derivatives), A5 (cross-refs), M1 (shift IDs), M4 (networks)
8. **Verify after writing** — re-read the file to confirm changes applied correctly

---

## PATTERN TYPES

| Code | Name | Description |
|------|------|-------------|
| A | HIDDEN | Arabic/Turkic origin invisible to English speaker |
| B | DIRECT LOANWORD | Recognised borrowing (coffee, algebra, zero) |
| C | CONFESSIONAL | The English word accidentally confesses its origin (e.g. Police ← إِبْلِيس) |
| D | JĀHILĪAN | Qur'anic weight stripped within Arabic itself (e.g. خَلَاص → "khalas") |

Entries can combine: A+D, B+C, etc.

---


---

## FULL ENTRY PROTOCOL

**STEP 0 — DECLARE ENTRY CLASS(ES) + UMD YES/NO**
Most entries are compound. Declare all applicable domain classes before Stage 0 begins. UMD is declared separately as a base layer that overlays any domain class combination.

Domain classes (declare one or more):
- **LINGUISTIC** — any word, name, or term being traced phonetically
- **MATHEMATICAL** — any formula, constant, or numerical claim
- **INTELLIGENCE** — any historical operation, operator profile, or source assessment
- **GEOGRAPHIC** — any place name, country name, or peoples' name

UMD — Usurpation and Manipulation of Divine: declare if any of the following has been usurped by an operator class: divine knowledge, divine naming of peoples (رُوم, النَّصَارَى), divine naming of places, divine naming of substances, divine systems (financial/medical), divine attributes, divine calendar, divine language.

Compound examples: Fleming/Penicillin = LINGUISTIC + UMD | Newton/Calculus = LINGUISTIC + MATHEMATICAL + UMD | النَّصَارَى → "Christians" = LINGUISTIC + GEOGRAPHIC + UMD | رُوم → "Roman Empire" = GEOGRAPHIC + LINGUISTIC + UMD | Soviet Operation = INTELLIGENCE + GEOGRAPHIC + UMD

---

**MANDATORY CORE — ALL entry classes — always runs:**

- Stage 0: Wrapper Identification — all contaminated terms quarantined before analysis. Wrapper terms in quotes throughout entire entry. **QUARANTINE IS TOTAL — once a wrapper term is quarantined it is gone.** Do not reference its downstream language of origin anywhere in the analysis — "English," "Greek," "Latin," "French," "Persian" are all wrapper languages themselves and are equally inadmissible as descriptive categories. The phrase "English wrapper" is itself a violation — "English" is DP17. The phrase "Greek-derived" is itself a violation — "Greek" is DS04. Stage 0 output is: Term quarantined → proceed to AA or Bitig. The quarantined term does not reappear in any stage.
- Stage 1: Qur'anic Attestation — Ayat cited FIRST, before any claim. Qur'anic meaning IS the root meaning. All downstream is decay from it.
- Stage 2: Root Verification — all roots checked against Four-Source Lattice. Token counts confirmed. ATT format on every Arabic term.
- Stage 2a: EVIDENCE SOURCE GATE — **DS02 through DS11 (all downstream scripts) are INADMISSIBLE as source evidence.** They may only appear as decay path illustrations — never as origin confirmation. Any claim that can only be sourced through a downstream script (Greek, Latin, Old Persian, Sanskrit, Aramaic, Hebrew, Cyrillic, etc.) is classified UNVERIFIED until re-routed directly to AA or Bitig. Routing through a downstream wrapper to reach another term is a chain error — the wrapper adds nothing and introduces DS contamination. Go directly to AA or Bitig. If the AA or Bitig source cannot be established without the downstream intermediary — mark UNVERIFIED, do not cite the intermediary as confirmation.
- Stage 2b: SCRIPT QUALIFICATION GATE — A script qualifies as a script under USLaP only if it meets ALL THREE: (1) continuous community of scribes — not royal or monumental use only; (2) administrative and/or literary use — not display inscription only; (3) organic transmission — not rediscovered and reconstructed by outside scholars. Failure on ANY ONE = political monument, not a script. Record as UMD evidence of Step 7 (LEGITIMISE), not as a linguistic source. Examples of disqualified "scripts": Old Persian cuneiform (royal monument only, ~200yr use, abandoned, rediscovered by Europeans 19th c.) — cite as Darius I UMD operation, not as linguistic evidence.
- Stage Q-U-F: Gates — BINARY ONLY. Q / U / F each PASS or FAIL. No conditionals. No partial verdicts. All three must pass.
- Final: Formal Entry Block — structured record, every claim independently verifiable. Compliance checklist confirms all stages ran.

---

**DOMAIN CONDITIONAL STAGES — activated by declared class(es):**

LINGUISTIC → L1: Phonetic Chain (AA root → Shift ID → downstream, every consonant mapped, chain direction non-negotiable) | L2: Compound Analysis (if تَنُّور pattern applies — multi-root compound, sequence: medium/process/function) | L3: Pattern C Check (does the name confess its Qur'anic origin in the sounds? Register if confirmed)

MATHEMATICAL → M1: Irrational Replacement (constant identified → replaced from map, denominators from {3,5,7}) | M2: Qur'anic Ratio Verification (chain formula against 6,236-verse structure, Q54:49 بِقَدَرٍ as standard) | M3: Formula Restoration (contaminated formula replaced with Four-Source equivalent via USLaP_Formula_Restoration_Master.xlsx)

INTELLIGENCE → I1: Operator Profile (OP code assigned, role in 8-Step Cycle mapped, reliability assessment, OP05 rule applied to sole sources) | I2: Manuscript Chain (gap between event and earliest manuscript flagged — no corroboration = UNRELIABLE) | I3: كُلَّمَا Chain Mapping (Q2:100 — same zone, same operator class, same financial back-end, 9 ASB hosts mapped)

GEOGRAPHIC → G1: Colonial Name Rejection (modern wrapper rejected, Qur'anic name or original ASB designation restored with attestation) | G2: Toponym Phonetic Chain (place name: AA root → Shift ID → downstream, renaming event identified and dated) | G3: Peoples Naming (Qur'anic name of the people restored — رُوم, النَّصَارَى, أُمَّةً وَسَطًا — operator renaming documented as UMD event)

---

**UMD CONDITIONAL STAGES — activated when UMD declared — runs AFTER Q-U-F gates:**

- UMD-1: UMD 8-Step Cycle — 1.RECONNAISSANCE → 2.ENTRANCE → 3.INFILTRATE & POSITION → 4.DIVIDE THE HOST (Q28:4) → 5.FUND & ARM BOTH SIDES → 6.EXTRACT (الْحَرْثَ + النَّسْلَ) → 7.ERASE + COVER → 8.DISPERSE & REPEAT. All 8 steps mapped with dated evidence.
- UMD-2: Detection Pattern Register — all active DP codes listed with evidence. Minimum: DP07 (Gatekeeping), DP08 (Terminology Corruption), DP12 (Attribution Inversion), DP15 (Timeline Compression), DP16 (Jāhilīan Lisān), Pattern C (Confessional).
- UMD-3: Compliant Statement — lattice-compliant formulation of the phenomenon. Encounter report, not discovery. Divine attribution restored. Operator-class name removed from the principle.

---

**EXECUTION ORDER — FIXED:**
Stage 0 → Stage 1 → Stage 2 → Domain Stages (L then M then G then I) → Q-U-F Gates → UMD Stages → Formal Entry Block

**Visual map: `USLaP_ENTRY_PROTOCOL_DIAGRAM.html`**

---

