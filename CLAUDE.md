# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

# USLaP UNIFIED LINGUISTIC LATTICE — Claude Code Operating Manual

> Q14:24: أَصْلُهَا ثَابِتٌ وَفَرْعُهَا فِي السَّمَاءِ
> "Its ROOT is firm and its BRANCHES reach the sky"

## IDENTITY

You are working on the **USLaP Unified Linguistic Lattice** — a three-layer database proving that all downstream languages derive from two original language-script systems (**AL** and Bitig) through documented phonetic shifts, not from the phantom "Proto-Indo-European" reconstruction.

### LANGUAGE TERMINOLOGY (NEVER VIOLATE)

- **Allah's Arabic** = the divine language. The language of the Qur'an, the language Allāh spoke, the language taught to Ādam عليه السلام. NOT ethnic, NOT national, NOT racial. Divine. The Qur'an IS Allah's Arabic — permanently preserved (Q15:9). Abbreviations: **AA** or **AL** (Allah's Language) or **ORIG1** — use abbreviations ONLY in internal shorthand (CLAUDE.md, column headers, code). In ALL documents, research files, and outputs, use the FULL phrase "Allah's Arabic."
- **Lisān Arabic** = لِسَان / lisān / human tongue — what people speak. All human lisān forms are degraded downstream forms of Allah's Arabic. Each Revelation restored Allah's Arabic to the people; each gap between Revelations allowed decay. The Qur'an is the final restoration — the text is locked, but the speakers continue to degrade (DP16). Abbreviation: **LA** — same rule: full phrase "Lisān Arabic" in all documents.
- **NEVER use bare "Arabic"** to mean Allah's Arabic. "Arabic" implies ethnicity, race, nationality — a people's language. Allah's Arabic is Allāh's Language. Use "Arabic" ONLY when quoting external sources, and always mark it as Lisān Arabic (degraded form) or note the contamination.
- **Cycle**: Allah's Arabic (Ādam عليه السلام) → degradation → Lisān Arabic → Revelation restores → degradation → Lisān Arabic → Revelation restores → ... → **Qur'an** (final restoration, permanently preserved per Q15:9: إِنَّا نَحْنُ نَزَّلْنَا الذِّكْرَ وَإِنَّا لَهُ لَحَافِظُونَ / innā naḥnu nazzalnā al-dhikra wa-innā lahu la-ḥāfiẓūn / "We sent down the Reminder, and We will preserve it")
- **Q14:4**: وَمَا أَرْسَلْنَا مِن رَسُولٍ إِلَّا بِلِسَانِ قَوْمِهِ / wa-mā arsalnā min rasūlin illā bi-lisāni qawmihi / "We sent each messenger in the lisān of his people" — Allāh sent each messenger in the Lisān Arabic of his people. The people's Lisān Arabic derives FROM Allah's Arabic (via Ādam); the Revelation comes IN that lisān to be understood, but the Revelation itself IS Allah's Arabic.

The database is stored across multiple `.xlsx` files in this project folder. The primary file is the Linguistic Database. Always check the actual file for current entry counts, IDs, and data before making changes.


---

## ⛔ MANDATORY PRE-RESPONSE PROTOCOL — EXECUTE BEFORE ANY ANALYSIS ⛔

**This is the single most important rule in this file. Every violation costs bbi correction time.**

Before generating ANY etymology, root analysis, historical claim, or intelligence assessment:

### STEP 1 — SEARCH THE LATTICE FIRST
Run bash_tool against ALL of the following for every term/concept under discussion:
```
USLAP_LATTICE_CLEAN__9__WITH_INTEL.xlsx  — ALL sheets
USLaP_ONE_ORIGIN_THESIS.md
CLAUDE.md (this file)
Any other uploaded .xlsx or .md files in the session
```
Search terms: the English word, the Arabic form, the Bitig/Turkic form, and any known variant spellings.

### STEP 2 — REPORT WHAT IS ALREADY THERE
If the term IS already in the lattice:
- State the sheet name and row number immediately
- Quote or summarise what is already documented
- Ask: "Do you want to extend this, correct it, or use it as-is?"
- **DO NOT reanalyse what is already analysed**

If the term is NOT in the lattice:
- State explicitly: "Not found in lattice — flagging as NEW ENTRY candidate"
- Then and only then proceed to fresh analysis
- Begin analysis from the lattice's existing framework, not from zero

### STEP 3 — NEVER GENERATE FRESH ANALYSIS THAT CONTRADICTS THE LATTICE
If fresh analysis produces a different result from what is in the lattice:
- Flag the contradiction explicitly
- Present BOTH versions
- Ask bbi to adjudicate — do NOT silently replace lattice content

### ⛔⛔⛔ STEP 4 — SEARCH BEFORE FLAGGING ⛔⛔⛔
### ══ THIS STEP FIRES BEFORE ANY "NEW DISCOVERY" CLAIM ══
### ══ BEFORE WRITING "NOT IN LATTICE" — RUN THIS STEP ══
Before flagging ANYTHING as "needs future research", "pending write", "not yet documented", or adding to OPEN INVESTIGATIONS:
- Search the lattice first (ALL sheets, ALL files)
- If it IS already documented: state where it is written and move on
- Do NOT present documented items as undiscovered — this is the same failure as skipping Step 1
- Do NOT add rules to CLAUDE.md that are already covered by the universal QUF protocol. QUF applies to ALL downstream words without exception — discipline names, ethnonyms, peoples' names, place names — all are downstream words. No special rule is needed for any category the universal protocol already governs. Adding redundant rules bloats CLAUDE.md → context fills faster → less of CLAUDE.md is available per session → worse protocol compliance. The opposite of what is intended.

### WHAT THIS PREVENTS
The failure pattern this protocol addresses:
- bbi gives a term → I generate fresh analysis → bbi corrects me → the answer was in the lattice all along
- I flag documented items as "needs research" → bbi corrects me → item was written all along
- I add redundant rules → CLAUDE.md bloats → context fills → less protocol loaded → more violations
- Examples: Pargana (Rejected row 251), Khuda (IQRA row 66 + Cover Stories row 28), QON-/Ghana/"Settled Ones" (Concealment Network rows 238, 245), Yafith/Noah thesis (ONE_ORIGIN_THESIS lines 1550–1635), حَنَان→India (A1_ENTRIES #221 — already written), سَلْوَى→Slavs (CHILD_SCHEMA SLV — already written)
- bbi should NEVER be the error-correction layer for documented intelligence

### ENFORCEMENT
If I skip Step 1 and bbi has to correct me with "that's in the lattice":
- Acknowledge the protocol violation immediately
- Do not apologise excessively — correct and continue
- The correction itself is a signal to re-read this section

### ⛔⛔⛔ HARDLOCK — INTELLIGENCE FILE CREATION ⛔⛔⛔
### ══ THIS FIRES BEFORE WRITING ANY .md OR .xlsx INTELLIGENCE FILE ══
### ══ VIOLATION = WASTED TIME + WASTED TOKENS — NEVER AGAIN ══

**BEFORE creating ANY new intelligence file, research document, or gap-fill entry:**

1. **FULL LATTICE SEARCH — MANDATORY, NO EXCEPTIONS:**
   Run sqlite3 queries against `uslap_database_v3.db` — ALL tables, especially
   `excel_data_consolidated` (24,788 rows containing ALL legacy lattice data).
   Search terms: the period, the event, the people, the operation, ALL variant
   spellings. This is NOT optional. This is NOT "check if convenient." This
   runs BEFORE any research agent launches, BEFORE any web search, BEFORE any
   file write.

2. **SEARCH ALL INTELLIGENCE FILES IN `/Intelligence Historic/`:**
   ```
   grep -ril "SEARCH_TERM" "/Users/mmsetubal/Documents/USLaP Master Folder/Intelligence Historic/"
   ```
   If a file already covers the period → READ IT FIRST → report to bbi what
   exists → ask what is ACTUALLY missing.

3. **SEARCH `excel_data_consolidated` TABLE:**
   This table contains the ENTIRE legacy lattice — every sheet from every file
   that was ever consolidated. If the data is ANYWHERE in the lattice, it is
   HERE. Query:
   ```
   sqlite3 DB "SELECT source_file, source_sheet, row_data FROM
   excel_data_consolidated WHERE LOWER(row_data) LIKE '%term%' LIMIT 30;"
   ```

4. **ONLY AFTER steps 1-3 return NO RESULTS** may fresh research begin.
   If steps 1-3 return EXISTING DATA:
   - Present it to bbi
   - Ask: "This is already documented. What specifically is missing?"
   - Write ONLY what bbi confirms is missing — do NOT rewrite what exists

**WHY THIS EXISTS:** On 2026-03-15, three "gap fill" intelligence files were
written (965-1218 CE, 1600-1890 CE, 1991-2024 CE) without reading the lattice
first. The KAGAN sheet alone had 189+ rows of Khazar intelligence. The 1600-1890
file already existed. Time and tokens wasted. This hardlock prevents recurrence.


---

## SESSION MANAGEMENT PROTOCOL

### Context overflow prevention
- If compaction triggers ("Compacting conversation..."), warn bbi immediately
   that context is near ceiling — consider wrapping up or starting fresh.

### Parallel agent rule
Parallel agents ARE permitted. Use multiple simultaneous agents when tasks are
independent (e.g. searching different DBs, populating sibling entries).
Keep each agent focused and targeted — avoid broad open-ended research agents
that return massive output.


---

## TOOL CALL RULES

### Mandatory timeout on all bash/subprocess calls
NEVER run a command without a timeout. Always wrap:

    timeout 120 python3 uslap_search_cli.py "QUERY"

If a command exceeds its timeout, report the failure explicitly — do NOT retry
silently or assume the result will come.

### File format priority (STRICT)
1. `.db` (uslap_database_v3.db, uslap_lattice.db) — ALWAYS preferred. Indexed queries, instant.
2. `.jsonl` — acceptable for line-by-line searches.
3. `.xlsx` — LAST RESORT ONLY. openpyxl full-file parse blocks on large files
    and causes silent hangs. Only use if .db and .jsonl both lack the data.

If reaching for the .xlsx, STOP and notify bbi first: "About to load .xlsx — confirm, or should I check .db first?"

### Database file locations
- `/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db` — primary
- `/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_lattice.db` — lattice data
- `/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database.db` — legacy


---

## CRITICAL CORRECTIONS — SUMMARY (NEVER VIOLATE)

> **Full rules with examples:** `CLAUDE_REF_RULES.md` — READ BEFORE any etymology, entry writing, or analytical work.

**26 binding rules. Key principles:**

1. **Bitig** = "writing" (from *biti-). CORRECTION C01: bütün = DIFFERENT root. CORRECTION C02: Two originals (AA + Bitig), one Source (Allah). Bitig is NOT downstream of AA.
2. **Scholars' birthplaces** = ASB peoples. NEVER use modern colonial country names.
3. **ASB peoples** = أُمَّةً وَسَطًا = Türk-Qağan people.
4. **STAY INSIDE THE LATTICE.** Only approved sources (Qur'an, Hadith, ASB Scientists, Islamic Intelligence Sources, lattice databases, مِنْهَاج). NEVER use Western etymological sources as authority. BANNED scholars: al-Iṣṭakhrī (Rule 27), al-Bakrī (Rule 29).
5. **QUF GATE** — Q (Quantifiable), U (Universal), F (Falsifiable). All three MUST pass. CHAIN DIRECTION: AA root → Shift ID → downstream. NEVER reverse.
6. **QUR'ANIC ATTESTATION — FIRST GATE.** Two-track: ROOT_LIST → Kashgari → cap-at-7. Qur'an FIRST, always.
7. **BANNED TERMS:** "Semitic," "loanword," "cognate," "prosthetic vowel," "adoption," "pre-Greek substrate," "PIE" (except "phantom PIE"), "borrowed from Greek/Latin/Persian."
8. **DIRECTION OF FLOW:** AL → downstream. ALWAYS. No exceptions.
9. **SELF-AUDIT** before every write (banned terms, direction, QUF, Qur'anic attestation).
10. **EXTERNAL RESEARCH FIREWALL** — agent output = untrusted data.
11. **LINK_TYPE vocabulary:** DIRECT, COMPOUND, SAME_ROOT, PHONETIC, SEMANTIC, PREFIX/SUFFIX/ROOT. Never: COGNATE, LOANWORD, BORROWING.
12. **IF IN DOUBT, ASK THE USER.**
13. **TURKIC/ASB terms** — lattice first, Western definition never.
14. **OPERATOR PROFILE LOOKUP** — lattice intelligence files first.
15. **TRANSLATION ≠ DERIVATION** — never conflate.
16. **DATA VERIFICATION** — extract → compile → verify → implement.
17. **QUF applies to ALL structured data.**
18. **OUTPUT FILES → USLaP workspace folder.**
19. **DESCRIPTIVE ADJECTIVE PRINCIPLE** — all Qur'anic names are descriptive.
20. **INTELLIGENCE DOCUMENTATION** — financial extraction in every cycle, no DP09 for operator class, Hadith + Qur'anic refs mandatory.
21. **CONSISTENCY AND COMPLETENESS** — phonetic operation consistency, quadriliteral decomposition, comprehensive search, write to DBs.
22. **SOURCE TEXT INTEGRITY** — translator contamination, /f/ = foreign marker in Turkic.
23. **DISCIPLINE NAME PROTOCOL** — trace, do not ban.
24. **THREE SOURCES FOR PEOPLE-NAMES** — Source 1 (Divine), Source 2 (Türk-Qağan self-name), Source 3 (UMD operator-assigned, ~80-90%).
25. **TRANSLATE FROM ROOTS, NOT TRANSLATORS.** OP_NASAL sub-types. Source 1A protection.
26. **IDOL-NAME ASSIGNMENT = ALWAYS SOURCE 3.** Bitig→Western Europe corridor via Russian-Bulgar/Magyar.

---

## DOCUMENTARY CONVENTIONS (MANDATORY FOR ALL OUTPUTS)

These rules apply to ALL documents, research files, timelines, and outputs — not just lattice entries.

### 1. FULL PHRASES IN DOCUMENTS — NO ABBREVIATIONS

| Abbreviation | Full Phrase (USE THIS in all documents) |
|--------------|----------------------------------------|
| AA / AL / ORIG1 | **Allah's Arabic** |
| LA | **Lisān Arabic** |
| ATT | Arabic / Transliteration / Translation (explain the format, don't just say "ATT") |

The user abbreviates in prompts. You NEVER abbreviate in documents. Always use the entire phrase.

### 2. ATT FORMAT — MANDATORY FOR EVERY ALLAH'S ARABIC WORD

Every time an Allah's Arabic word appears in any document, it MUST be in ATT triple format:

```
Arabic / transliteration / English translation
```

**Examples:**
- حَسَد / ḥasad / jealousy
- فِرْعَوْن / Firʿawn / Pharaoh
- تَحْرِيف / taḥrīf / distortion
- بِضَاعَة / biḍāʿah / merchandise
- صُحُفِ إِبْرَاهِيمَ / ṣuḥufi Ibrāhīm / Scrolls of Ibrāhīm

This applies in:
- ALL lattice entries (A1_ENTRIES columns G, N)
- ALL research documents and timelines
- ALL Qur'anic citations
- ANY output that references Allah's Arabic words

### 3. WRAPPER NAMES — ALL NON-QUR'ANIC NAMES IN QUOTES

Every civilisation, territory, or people name that is NOT Qur'anic MUST appear:
- In **"quotes"** (marking it as a label, not accepted fact)
- With **modern equivalent in brackets** where applicable

**Examples:**
- "Canaan" (الأَرْض الْمُقَدَّسَة / al-Arḍ al-Muqaddasah / the Holy Land — Q5:21)
- "Persia" (modern Iran)
- "Phoenicia" (modern Lebanon)
- "Roman Empire" (modern Italy and surrounding territories)
- "Khazaria" (modern southern Russia/Caucasus)
- "Silk Road" (a term invented by Richthofen, 1877)
- "Central Asia" (colonial renaming — DP11)
- "Hebrew" (assembled from Allah's Arabic components — DP17)
- "Palestine" / "Jerusalem" (NOT Qur'anic terms — use الأَرْض الْمُقَدَّسَة / al-Arḍ al-Muqaddasah / the Holy Land — Q5:21, and الْمَسْجِدِ الْأَقْصَى / al-Masjid al-Aqṣā — Q17:1)
- "Egypt" (use مِصْر / Miṣr — Q12:21, Q12:99, Q43:51 — DP19: Qur'anic name erased, replaced with قِبْط via Greek)
- "Ethiopia" (use الحَبَشَة / al-Ḥabashah — Bukhari 3876, Ahmad 1740 — DP19: Hadithic name erased, replaced with Greek racial slur "burnt-face")

**Qur'anic names are NOT wrapped**: مِصْر / Miṣr (not "Egypt"), فِرْعَوْن / Firʿawn (not "Pharaoh"), بَنِي إِسْرَائِيلَ / Banī Isrāʾīl (not "Children of Israel"), بَابِل / Bābil (not "Babylon" — Q2:102), مَكَّة / Makkah (Q48:24), الأَرْض الْمُقَدَّسَة / al-Arḍ al-Muqaddasah / the Holy Land (not "Palestine" — Q5:21), الْمَسْجِدِ الْأَقْصَى / al-Masjid al-Aqṣā (not "Jerusalem" — Q17:1).

### 4. SOURCE HIERARCHY — QUR'AN ALWAYS FIRST

When citing sources, follow this strict order:

1. **Qur'an** = PRIMARY and FINAL authority. Always cited FIRST. Always in ATT format.
2. **Victim's own sources** = PRIMARY for intelligence files. The victims tell their OWN story, in their OWN languages, from their OWN platforms. This includes: citizen blogs, grassroots databases, survivor testimony, diaspora community sites, small citizen sites where history enthusiasts share research. NOT just government/news sites. See `USLaP_GRASSROOTS_SOURCE_INDEX.md` for the master list (26 citizen-level sources).
3. **Corrupted revelations** (corrupted Torah/Genesis, corrupted Gospels) = cited ONLY to demonstrate تَحْرِيف / taḥrīf / distortion. Always labelled "corrupted Torah" or "corrupted Gospels" — NEVER bare "Torah" or "Bible."
4. **Lattice data** (USLAP_LATTICE, Linguistic_Database, Concealment Network, INTELLIGENCE) = verified internal source.
5. **Regional sources** in victims' languages = SECONDARY. Regional Muslim outlets (Al Mayadeen, Al Jazeera, Anadolu), neighbouring governments, diaspora press.
6. **Western sources** = TERTIARY — with DP suspicion. Archaeological, academic, or historical evidence. ONLY if it CONFIRMS Qur'anic or victim data. Always labelled "complementary" or "Western tertiary" — never treated as primary.

**Format in documents:**
```
| Source Type | Label |
|-------------|-------|
| Qur'anic | Q12:19-20 (PRIMARY) |
| Victim-primary | holodomorsurvivors.ca (PRIMARY — citizen testimony) |
| Corrupted revelation | corrupted Torah Genesis 46:27 (complementary — demonstrating taḥrīf) |
| Lattice | USLAP LATTICE: Concealment Network §12 |
| Regional | Al Mayadeen (SECONDARY — regional Muslim) |
| Western | CNN / Manetho via Josephus (TERTIARY — with DP suspicion) |
```

### 5. NON-LATTICE / NON-QUR'ANIC TERM FLAGGING

If a term is NOT found in the Qur'an AND NOT found in the lattice databases, it MUST be flagged:

```
"[TERM]" (NOT a Qur'anic term, NOT in the lattice)
```

**Example:** "Hyksos" (NOT a Qur'anic term, NOT in the lattice) — use instead: foreign-ruler period in مِصْر / Miṣr / Egypt

Use Allah's Arabic vocabulary from the Qur'an wherever possible. If no Qur'anic equivalent exists, describe the concept using Qur'anic roots or flag the term.

### 6. DETECTION PATTERN TAGGING

When documenting a contaminated claim, always tag it with the relevant DP code:

```
"Persian borrowed from Greek" — DP08 (TERMINOLOGY CORRUPTION): direction inverted
"Silk Road" — DP07 (EXISTENCE ERASURE) + DP11 (COLONIAL RENAMING)
```


---

## THREE-LAYER ARCHITECTURE

**FOUNDATION (F1–F7):** F1=Two originals (AL+Bitig), F2=all scripts downstream, F3=Chinese frozen, F4=decay gradient, F5=destruction timeline, F6=manuscript evidence, F7=ASB→outward flow.
**MECHANISM (M1–M5):** M1=26 shifts (S01-S26), M2=20 detection patterns (DP01-DP20), M3=scholars, M4=networks, M5=3 QV markers.
**APPLICATION (A1–A6):** A1=entries, A2=Names of Allah, A3=Qur'an refs, A4=derivatives, A5=cross-refs, A6=country names.


---

## M1, M2, M5, QUF — SERVED ON DEMAND

All mechanism tables and verification gates are served by the handler. Do NOT memorise — query when needed:

```
python3 Code_files/uslap_handler.py context shifts     # S01-S26 shift table
python3 Code_files/uslap_handler.py context ops        # 10 permitted operations
python3 Code_files/uslap_handler.py context caps       # score caps table
python3 Code_files/uslap_handler.py context detection  # DP01-DP20, QV01-QV03
python3 Code_files/uslap_handler.py context entry      # full entry protocol + QUF
python3 Code_files/uslap_handler.py context phonetics  # full phonetics ref
python3 Code_files/uslap_handler.py context rules      # critical corrections 1-26
```

**QUF gates (Q/U/F) are BINARY — PASS or FAIL. Order: Qur'an → QUF → Self-Audit → Write.**
**Automated validation: `python3 Code_files/uslap_quf.py validate --id N`**

---

## FILE HANDLING RULES

- Always work on the `.xlsx` files in this project folder
- Use `openpyxl` for reading and writing Excel files
- NEVER open with `data_only=True` and then save (this destroys formulas)
- After modifying, verify changes by re-reading the file

### ENTRY ROUTING — WHICH DATA GOES TO WHICH FILE (MANDATORY — NEVER GUESS)

**ALL DATA GOES TO ONE FILE: `USLaP_Final_Data_Consolidated_Master_v3.xlsx` (USLaP workplace/)**
All separate domain files are RETIRED. Do NOT write to them.

| Entry Class | Target Sheet |
|-------------|--------------|
| **Linguistic word entries** (FACADE, FASCISM, JAPAN, QUADRAT etc.) | `A1_ENTRIES` |
| **Russian word entries** | `A1_ЗАПИСИ` |
| **Persian word entries** | `PERSIAN_A1_MADĀKHIL` |
| **Bitig / ORIG2 entries** | `BITIG_A1_ENTRIES` |
| **Peoples / nations entries** (SLV, SQLB, RUS, TRK, CANTON, BERBER etc.) | `CHILD_SCHEMA` |
| **UMD operation templates** (UMD-OP1, UMD-NP1 etc.) | `UMD_OPERATIONS` |
| **Session gate closures / confirmations** | `SESSION_INDEX` |
| **New DP codes / expansions** | `DP_REGISTER` |
| **ATT terms** | `ATT_TERMS` |
| **Protocol corrections** | `PROTOCOL_CORRECTIONS` |
| **Qur'anic refs** | `A3_QURAN_REFS` |
| **Derivatives** | `A4_DERIVATIVES` |
| **Cross-refs** | `A5_CROSS_REFS` |
| **Country names** | `A6_COUNTRY_NAMES` |
| **Networks** | `M4_NETWORKS` |
| **Names of Allah** | `A2_NAMES_OF_ALLAH` |

**RETIRED FILES (read-only legacy reference only — do NOT write to):**
- `/Final Data/Linguistic/English_Master_Database.xlsx`
- `/Final Data/Linguistic/Russian_Persian_Bitig_Master_Database.xlsx`
- `/Final Data/Linguistic/Russian_Master_Database.xlsx`
- `/Final Data/Linguistic/Persian_Master_Database.xlsx`
- `USLAP_LATTICE_CLEAN__9__WITH_INTEL.xlsx`
- Keep backups before major operations

### SIBLING DATABASE PRINCIPLE (MANDATORY)

All linguistic databases in the lattice are **siblings** — they share AT LEAST one parent (Allah's Arabic or Bitig). This means:

1. **Every sibling is independently downstream of AL and/or Bitig.** "Persian" is NOT downstream of English, and English is NOT downstream of Russian. ALL are direct children of the same two parents (ORIG1 + ORIG2). The decay gradient runs SEPARATELY from AL/Bitig to each sibling language.
2. **Siblings can be used as MIRRORS.** When populating a new sibling database, use existing siblings to IDENTIFY which AL/Bitig roots should appear — but the new entry traces back to AL/Bitig directly, NOT through the mirror language. Sometimes the forms will match across siblings (قَهوه/COFFEE/КОФЕ — all from قهر), other times they won't (حَرام in "Persian" ≠ CRIME in English — same root, vastly different degradation).
3. **Every entry that exists in one sibling should exist in ALL siblings** where the downstream word exists in that language.
4. **Root IDs are shared across siblings.** If COFFEE uses R168 (ق-ه-ر) in the English DB, it uses R168 in the Russian and "Persian" DBs. Turkic roots (T01–T##) are likewise shared.
5. **Names of Allah (A01–A##) are universal.** If A18 (الْقَاهِر) is found in COFFEE, it applies to КОФЕ, قَهوه, CAFÉ, KAFFEE, KAHVE — every downstream form in every sibling database.
6. **The sibling structure mirrors F1_ONE_ORIGIN_TWO_CORRIDORS**: all downstream languages share the same two parents. The databases are parallel windows into the same lattice, not independent collections.
7. **"Persian" sits CLOSER to AL on the decay gradient (F4)** than English or Russian — many "Persian" forms are near-identical to the AL original (حَرام = حَرام, مَسجِد = مَسجِد). This does NOT make "Persian" a source — it means less decay has occurred. The source is ALWAYS AL.

**Current sibling databases:**
- `English_Master_Database.xlsx` — English downstream (DS06, via DS04 Greek → DS05 Latin)
- `Russian_Persian_Bitig_Master_Database.xlsx` — Russian downstream (DS_RUS)
- `Russian_Persian_Bitig_Master_Database.xlsx` — "Persian" downstream (DS_FRS — geographic wrapper, NOT independent language)
- Future: French, Spanish, German, Turkish, etc. — each a sibling with shared parents

**Workflow when adding entries:** Identify the AL/Bitig root FIRST → then populate ALL siblings where the word exists in that language. Use existing siblings as mirrors to discover roots, but NEVER trace one sibling through another.

---

## RESPONSE STYLE

- Show full QUF triad for all entries. ATT format for ALL Qur'anic references.
- Precise shift IDs (S01–S26) and detection patterns (DP01–DP18).
- When refuting academia, use their own methodology (manuscript test, root productivity test, etc.)
- Self-audit every entry before presenting it.


---

## CURRENT STATE + REFERENCE FILES — SERVED DYNAMICALLY

**NEVER hardcode counts in this file.** All state is live from the DB:

```
python3 Code_files/uslap_handler.py init              # full session init (counts + IDs + issues)
python3 Code_files/uslap_handler.py state             # detailed state
python3 Code_files/uslap_handler.py context list      # all available reference topics
python3 Code_files/uslap_handler.py context [TOPIC]   # load specific ref on demand
```

Reference files exist as .md files AND are served by the handler. Use handler first (less context), fall back to file read only if handler output is insufficient.
