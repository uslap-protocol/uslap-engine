# USLaP REFERENCE — PHONETICS, OPERATIONS & CORRIDOR RULES

> **Load this file when:** tracing a word phonetically, working with RU/Bitig pipeline, or mapping consonant shifts.
> **Parent file:** CLAUDE.md (core)

---

## M1: PHONETIC SHIFT TABLE (MEMORISE THIS)

Every entry MUST map through this table. Each shift has a Shift ID (S01–S26).

| S_ID | Arabic | Name | English outputs | Russian outputs |
|------|--------|------|-----------------|-----------------|
| S01 | ق | qāf | c, k, q, g | к, г |
| S02 | ج | jīm | g, j | г, ж, дж |
| S03 | ح | ḥāʾ | h, c | х |
| S04 | ط | ṭāʾ | t | т |
| S05 | ش | shīn | sh, s | ш, щ, с |
| S06 | ض | ḍād | th, d | д, з |
| S07 | ع | ʿayn | a, e, (drops) | а, (выпадает) |
| S08 | ف | fāʾ | f, p, v | ф, п |
| S09 | ب | bāʾ | b, p, v | б, п, в |
| S10 | و | wāw | v, w, o, r | в, у, о |
| S11 | خ | khāʾ | ch, x, k | х, к, г |
| S12 | ذ | dhāl | d, th | д, з |
| S13 | ص | ṣād | s, c, z | с, ц, з |
| S14 | غ | ghayn | gh, g | г, ж |
| S15 | ر | rāʾ | r | р |
| S16 | ل | lām | l | л |
| S17 | م | mīm | m | м |
| S18 | ن | nūn | n | н |
| S19 | د | dāl | d, t | д, т |
| S20 | ك | kāf | c, k, ch, g | к |
| S21 | س | sīn | s, c, z | с |
| S22 | ز | zāy | z, s | з, с |
| S23 | ه | hāʾ | h, (drops) | г, х, (выпадает) |
| S24 | ت | tāʾ | t | т, д |
| S25 | ظ | ẓāʾ | z, th | з |
| S26 | ث | thāʾ | th | т, ф |

**Rule**: Every consonant in the downstream word MUST map back to an AL root consonant via this table. No exceptions. No hand-waving. If a consonant can't be traced, the entry fails.

### Permitted Operations (consonant-level phenomena beyond the shift table)

| OP_ID | Name | Description | Examples |
|-------|------|-------------|----------|
| OP_NASAL | Nasal Insertion | N appears in downstream with no Arabic source consonant. Documented in 24+ entries. | GOVERN (جَبَّار+N), FURNISH (فَرَش+N), ANTIQUE (عَتِيق+N), SOLEMN (سَلَّم+N), PATTERN (فَطَر+N) |
| OP_SUFFIX | Latin/Greek Suffix | Terminal consonants from Latin -alis, -mentum, -atus, -tare, -nis etc. are NOT root consonants. Strip BEFORE tracing. | MILIT-ARY, REGI-MENT, MORT-AL, SORCER-Y, RECIT-E |
| OP_NASSIM | Nasal Assimilation | ن→م before bilabial (standard phonological process). | anbār→АМБАР, عنبر→amber |
| OP_TAMARBUTA | Tāʾ Marbūṭa Realisation | ة→T in downstream forms. | قِسْمَة→KISMET, رَاحَة→RACKET |
| OP_VOICE | Downstream Voicing/Devoicing | Systematic voicing changes in downstream corridors. | ت→D (DEBT), s→z (Russian), t→d (Spanish adobe) |
| OP_PHRASE | Phrase-to-Word Compression | Arabic phrase compressed into single downstream word. | فِي الصَّفَا→PHILOSOPHY, دَارُ الصِّنَاعَة→ARSENAL |
| OP_PREFIX | Grammatical Prefix Fusion | Arabic grammatical prefixes (بَ-, يَ-, تَ-, مُ-, أَ-) fuse into the downstream word, contributing root-position consonants. The prefix is not "just grammar" — it carries through into the downstream form. | PROPHET (بَعَارِف: بَ→P via S09), MUMMY (مُومِيَاء: مُ→M) |
| OP_STOP | Epenthetic Stop after Geminated Nasal | Geminated nasal develops epenthetic stop consonant: NN→ND, MM→MB. Standard phonological process — nasal assimilation produces oral stop at same place of articulation. | تَنُّور→TANDOOR (NN→ND, #216), حَنَان→HIND→INDIA (NN→ND, #221) |
| OP_RU_PREFIX | Russian Grammatical Prefix | Russian prefixes (ДО-, ПО-, НА-, ПРИ-, ПРЕ-, ПРО-, ЗА-, ОТ-, ИЗ-, ВЫ-, РАС/РАЗ-, С-, У-, ОБ-, ПОД-, ПЕРЕ-, ВОЗ/ВОС-) are NOT root consonants. Strip BEFORE tracing — same principle as OP_SUFFIX for Latin/Greek. Russian is FULL of prefixes. The root word begins AFTER the prefix. | ДОГОВОР: strip ДО- → ГОВОР → Г-В-Р → ج-ب-ر (21 tokens, الجَبَّار). ПОРЯДОК: strip ПО- → РЯДОК → root. РАССВЕТ: strip РАС- → СВЕТ → root. ПОДВАЛ: strip ПОД- → ВАЛ → root. |
| OP_RU_COMPOUND | Russian Compound Word | Russian compounds (САМО+ВАР, ВОДО+ПАД, ПАРО+ВОЗ) combine TWO root words with a bridge vowel (О or Е). САМО/САМА is a PRONOUN (= "self/auto") — it is NOT a root to trace. Only trace the ROOT PART of the compound. The prefix part (САМО, ВОДО, ПАРО, etc.) provides semantic context but has no independent AA/Bitig root trace. | САМОВАР: САМО = pronoun "self" (not traced), ВАР = the root → trace independently. СПРАВЕДЛИВОСТЬ: СПРАВ from ص-ب-ر (103 tokens) + ДЛИВОСТЬ from ت-ل-و (63 tokens) — rare TWO-ROOT compound. |

### RUSSIAN CORRIDOR RULES (MANDATORY FOR RU PIPELINE)

**THREE TYPES OF RUSSIAN WORDS — CORRIDOR CLASSIFICATION (MANDATORY)**

Every Russian word in the lattice falls into one of three types. Determine the type BEFORE tracing.

---

**TYPE 1 — AA via "Greek"/Orthodox/Church Slavonic corridor (DS04)**
- **Path:** AA → "Greek" (DS04) → Church Slavonic → Russian
- **Content:** Religious, administrative, scholarly, and foundational vocabulary
- **Phonetic markers:** Standard S01–S26 shifts apply. No Bitig artifacts (B01–B07 do NOT fire). ف→ф (NOT п). Pharyngeals ح/ع may survive as х or drop (S03/S07), but NOT via B02.
- **When:** Primarily via Orthodox Church adoption of "Greek" liturgical vocabulary (10th century CE onward), but also earlier Slavic-الرُّوم contact.
- **Examples:** ВЕРА (بِرّ/R470), ГОЛОС (قَوْل/R202), МЕСТО (وَسَط/R175), ГОРОД (قَرْيَة/R453), ВОЙНА (بَيْن/R364), ДЕЛО (عَدْل/R190), ДЕНЬ (دِين/R478), СЛОВО (صَلَاة/R457), ДВЕРЬ (دَوَر/R475), ГОРА (قَهَر/R168), МОРОЗ (مَرَض/R471), РАБОТА (رَبَط/R472), ДОРОГА (طَرِيق/R55), КОРЕНЬ (قَرْن/R133), ПОРОГ (فَرْق/R152), ДОЛГ (طَلَاق/R473), МОРЕ (مَوْر/R476), СТРАНА (شَطْر/R480)

---

**TYPE 2 — Direct from Bitig (ORIG2)**
- **Path:** Bitig → Russian (direct neighbor transfer)
- **Content:** Largest vocabulary layer (~65% of Russian). Everyday, military, pastoral, domestic, trade vocabulary.
- **Phonetic markers:** B01–B07 ALL apply. No /f/ (B01). Deep pharyngeals ح/ع drop (B02). Agglutinative morphology (B03). Vowel harmony (B04). No /w/ (B05). Kashgari attestation required (B06). Semantic alignment check (B07).
- **When:** Continuous contact — Slavic and Turkic peoples as direct geographic neighbors for millennia. Pre-Islamic and post-Islamic.
- **Meanings sometimes NOT preserved** — Bitig words may have shifted meaning in Russian while retaining phonetic skeleton.
- **Examples:** 200 ORIG2 entries already in the lattice. ЮРТА, ТАБУН, КУРГАН, СТЕПЬ, КАЗАК, АТАМАН, etc.

---

**TYPE 3 — AA via post-Qur'anic Turkic/Bitig corridor**
- **Path:** AA → post-Qur'anic Turkic adoption → "Turkicized/Bitigized" phonetics → Russian
- **Content:** AA words that entered Turkic languages AFTER the Qur'an, then transmitted to Russian with Turkic phonetic modifications.
- **Phonetic markers:** HYBRID — the word traces to an AA root (ORIG1), but shows Bitig phonetic artifacts: ف→п (NOT ф, because B01: Bitig has no /f/), ح/ع drop (B02), possible vowel harmony (B04). The AA root is confirmed by Qur'anic attestation, but the phonetic SURFACE looks "Turkic."
- **When:** After 610 CE (Qur'anic revelation). Turkic peoples adopted AA vocabulary through Islamic contact, then transmitted to neighboring Russians.
- **Diagnostic:** If a word has an AA root but shows Bitig phonetic artifacts (п instead of ф, pharyngeal drops), it is TYPE 3.
- **24 documented AA-Taken-By-Turkic cases:** КАЛЫМ, КАБАЛА, ТАХТА, КОВЧЕГ, ЧАЛМА (سلم), СТАКАН (سكن), ЧУРЕК (شرك), ДОЛМА (ظلم), КАБЛУК (قبل), etc. All reclassified from T-prefix to R-prefix ROOT_IDs.
- **New example:** ПОЛЕ (فَلَحَ/R477) — ف→п (B01), ح drops (B02). The فَلَّاح (farmer) works the ПОЛЕ (field). Corridor 3 confirmed.

---

**DEGRADATION GRADIENT FOR RUSSIAN (F4 APPLICATION):**
- TYPE 2 (Direct Bitig): LEAST degraded for Bitig-origin words — direct neighbor, no intermediary
- TYPE 3 (AA→Turkic→RU): SECONDARY degradation — AA root passed through one intermediary (Turkic), less degraded than English
- TYPE 1 (AA→DS04→Church Slavonic→RU): TERTIARY — passed through two intermediaries, but still closer to source than English (which goes AA→DS04→DS05→DS06)
- **Direct AA corridor** (НАМАЗ, ХАДЖ, ЗАКЯТ): LEAST degraded AA — no intermediary at all
- **DS09 / "Persian" corridor**: some terms via "Persian" geographic wrapper, especially through Turkic intermediaries

---

### LATIN CORRIDOR FRAMEWORK (DS05 — FOR FUTURE EU SIBLING DATABASES)

Latin (DS05) receives from BOTH originals through historically documented corridors. Understanding WHEN and HOW words entered Latin determines the degradation level and corridor markers.

**AA → Latin corridors (ORIG1):**

1. **Inter-Revelation period** (between صُحُفِ إِبْرَاهِيمَ / ṣuḥufi Ibrāhīm / Scrolls of Ibrāhīm and the Qur'an):
   - Majority during the Quraysh/Christianity operation
   - AA words entered through corrupted revelation channels → "Greek" (DS04) → Latin (DS05)
   - The DS04→DS05 pipeline carried religious, philosophical, legal, and administrative vocabulary
   - Examples: Latin VERUS (from بِرّ/birr), religious terminology, legal concepts
   - These words are the MOST degraded AA forms in Latin — passed through two wrapper languages before reaching Latin

2. **Post-Qur'anic / al-Andalus period** (711–1492 CE):
   - After Qur'an Revelation (610 CE) — direct AA → الأندلس / al-Andalus → Latin/Romance
   - The governance of الأندلس brought AA vocabulary directly into contact with Latin-speaking populations
   - LEAST degraded AA forms in Latin — direct contact, minimal intermediary corruption
   - After the destruction of الأندلس (the Reconquista/Inquisition operation, culminating 1492 CE), the stolen vocabulary spread further into European languages
   - Examples: ALGEBRA, ALGORITHM, ZERO, ALCOHOL, ARSENAL, ADMIRAL — these are the cleanest AA traces in European languages
   - **The Reconquista operation** = UMD 8-Step Cycle applied to الأندلس: RECONNAISSANCE (711–756 internal conflicts) → ENTRANCE (Charlemagne 778 CE) → INFILTRATE (Christian kingdoms 9th–11th c.) → DIVIDE (taifa kingdoms/fitna) → FUND & ARM (Crusade funding + Reconquista armies) → EXTRACT (800 years of Islamic science, libraries, institutions stolen) → ERASE (Inquisition 1478, Fall of Granada 1492, book burnings, forced conversions) → DISPERSE (Moriscos expelled 1609)

**Bitig → Latin corridors (ORIG2):**

1. **Pre-"Khazar" dispersal** (before 965 CE):
   - Via operators with wrappers OTHER than "Khazar"
   - Attila operations (434–453 CE): Hunnic/Turkic vocabulary entering "Latin" Europe during Hunnic campaigns
   - Gothic corridor: Turkic-Gothic contact transmitted Bitig words into Germanic and then Latin
   - Avar operations (6th–8th century CE): Avar Khaganate in Pannonia — direct Turkic-Latin contact
   - Bulgar operations: Volga and Danube Bulgars transmitted Bitig vocabulary into Slavic and Latin Europe
   - These are the EARLIEST Bitig forms in Latin — relatively undegraded

2. **Post-"Khazar" dispersal** (after 965 CE):
   - After the "Khazar" operators were exposed and their polity collapsed (Sviatoslav's campaign 965 CE), dispersed populations carried Bitig vocabulary into Western Europe
   - Via the Russian-Bulgar/Magyar corridor (per Rule 26 in CLAUDE_REF_RULES.md)
   - The idol-name assignment pattern (Bitig→Western Europe) intensifies in this period
   - Financial and commercial vocabulary especially enters through this corridor
   - These are MORE degraded Bitig forms — passed through the dispersal trauma and adapted to new host languages

**Latin as DS05 HUB for European sibling databases:**
- Latin → French (DS_FR), Spanish (DS_ES), Italian (DS_IT), Portuguese (DS_PT), Romanian (DS_RO)
- Each downstream Romance language is a FURTHER degradation of the Latin form
- The Latin form itself traces back to AA or Bitig via the corridors above
- **Sibling Database Principle applies:** All Romance languages share Latin as parent; Latin shares AA and Bitig as parents. The root IDs (R###, T###) are universal across all siblings.

**DIRECTION OF TRANSMISSION — HARD RULE FOR COGNATE CROSSREF:**
- **English is the MOST degraded form** of both originals. Russian is closer to BOTH.
- **Exception: Andalusian English** — Words entering English during الأندلس / al-Andalus governance (711–1492 CE) are LESS degraded because they came via direct AA contact, not through multiple DS layers.
- **Exception: Pre-Andalus English** — Words entering English BEFORE al-Andalus are the MOST degraded of all.
- **Exception: Modern technology/medicine/finance** — Terms like КОМПЬЮТЕР, ИНТЕРНЕТ, ПРИНТЕР went EN→RU direction. For these, EN cognate IS authoritative.
- **For all other Russian words**: EN cognate disagreement = informational NOTE only, NOT competition. The Russian pipeline is closer to source.
- **Bitig inheritance into English** = last receiver in chain, most degraded through all times.

### ANALYTICAL RULES (R-SERIES — SESSION DISCOVERIES)

These rules emerged from empirical session work. Each is now binding protocol.

| Rule | Name | Description | Example |
|------|------|-------------|---------|
| R01 | Bitig Pharyngeal Rule | When ALL consonants map to an AA root EXCEPT a pharyngeal (ح, ع, خ, غ) that appears as a vowel or drops entirely → check Bitig corridor. Pharyngeals are non-native to Bitig phonology and are systematically absorbed or vocalised in ORIG2 transmission. | SERVANT: AA ر-و-د confirmed + Bitig shows ح-ر-ب / miḥrāb visible only when ح drops |
| R02 | Root Transposition Check | When QUF fails on a root candidate but the three consonants ARE correct under M1 — check if they are reordered (metathesis). Consonant transposition is a documented phonological process. | SACRIFICE: engine assigned ش-ر-ك, correct root is ش-ك-ر (same three letters, different order) |
| R03 | S10 Discriminator | و→r (S10) is documented but MUST be discriminated from ر→r (S15). Red flag: multiple unrelated English words assigned the same root via و→r alone = engine misfired. Require corroborating evidence before accepting و→r for any single entry. | Engine overassigned ر-و-د via S10 to REVOLUTION, HARVEST, TERRITORY etc. — all wrong |
| R04 | UMD Compound Auto-Trigger | Any word whose phonetic trace lands on a root governing a divine institution (Revelation, governance, knowledge, commerce, medicine, calendar, naming) is automatically classified LINGUISTIC + UMD compound. No additional declaration required. | MERCHANT (م-ر-ج / Q55:19 waters), MIRACLE (ر-س-ل / prophethood), REVOLUTION (ب-ل-و / divine trial) |
| R05 | Pattern C Automatic | When the English word's ACTUAL FUNCTION in Western usage IS the same as the mechanism described by its AA root — auto-classify Pattern C (Confessional). No subjective judgment needed. | SACRIFICE: confesses شُكْر (gratitude). MIRACLE: confesses what the مُرسَل brings. REVOLUTION: confesses the بَلَاء trial cycle |
| R06 | Two-Register DP08 | Many AA roots carry TWO semantic registers in the Qur'an (divine/human, constructive/destructive, inward/outward). When an operator-class deployment weaponises the destructive register while advertising the constructive register — classify DP08 on the specific register, not on the root. Document BOTH registers. | بَلَاء: Register 1 = divine trial that reveals truth (Q2:155). Register 2 = wearing out / exhaustion (Q22:5). REVOLUTION advertises R1, delivers R2. |
| R07 | Qur'anic Anchor Per UMD Step | Every step of every UMD 8-step cycle analysis MUST carry a Qur'anic anchor verse. Reference: Step 1=Q27:22, Step 2=Q2:14, Step 3=Q63:1, Step 4=Q28:4, Step 5=Q8:36, Step 6=Q2:205, Step 7=Q2:11-12, Step 8=Q2:100. Non-negotiable. | Every REVOLUTION/political cycle UMD analysis must show all 8 anchors |
| R08 | مُ OP_PREFIX Model | When an English word begins with M- and the phonetic chain stalls without a matching root consonant — test مُ as OP_PREFIX (Form IV/participle prefix, not a root letter). Strip مُ → trace remaining consonants. | MIRACLE: full consonants M-R-C-L → strip مُ → R-C-L = ر-س-ل (mursalun). The prefix IS the مُرسَل form. |
| R08a | R08 CONSISTENCY GATE — strip only when it helps | R08 fires ONLY when: (1) stripping مُ/م leaves a CLEAN trilateral trace, AND (2) there is grammatical evidence the M is a Form IV/participle prefix (not a root letter). Do NOT strip M simply because the chain stalls — test both WITH and WITHOUT the M. If stripping M still leaves an untraceable skeleton, R08 does NOT apply. MARTYR #235 is the canonical failure case: strip M → R-T-R → maps to nothing → R08 inapplicable. | MIRACLE: strip مُ → R-C-L = ر-س-ل ✓ MARTYR: strip M → R-T-R → no clean trace ✗. Do NOT assign م-و-ت to MARTYR on the basis of stripping M. |
| R09 | N15 Extension Standard | Any English word with consonant skeleton C/G/K-R-N or C-R-W-N is an N15 candidate (root ق-ر-ن, R133). Verify via M1 and Q-gate before writing, but always check N15 first. | CORN, GRAIN (G-R-N), CROWN / CORONA (C-R-N), CORNER, CONCERN — all N15. Engine was assigning these to ك-و-ن (wrong). |
| R10 | Semantic Mapping ≠ Phonetic Tracing | Any proposed root correction (from any source) must itself pass U-gate. Proposing "ر-و-ح for SPIRIT" because both mean "spirit" = semantic mapping = fails U-gate (R-W-Ḥ cannot produce S-P-R-T). All 8 corrections from the external AI failed this test. | SPIRIT = ص-ب-ر: S→ص(S13), P→ب(S09), R→ر(S15) ✅ ALL consonants map. ر-و-ح: produces R-W-Ḥ → no P, no final consonant ❌ |
| R11 | Transposition as Semantic-First Diagnostic | When a semantic-first failure is detected (R10 fires), immediately check if the wrongly-assigned root is a consonantal TRANSPOSITION of the phonetically correct root (R02 cross-run). If yes: the semantic pull produced the transposed form — this is proof phonetics were never run. The consonant ORDER in the English word is the evidence. Always cross-run R02 when R10 fires: they are linked. | SACRIFICE: wrong root = ش-ر-ك (S-R-K, semantic pull from shirk / idolatrous sacrifice). Phonetic sequence of word: S-A-C-R → strip suffix → position 1=S→ش(S05), position 2=C/K→ك(S20), position 3=R→ر(S15) = S-K-R = ش-ك-ر. K is at position 2 in the word; R at position 3. The wrong root ش-ر-ك puts R at position 2 and K at position 3 — transposed. The semantic image of shirk forced K and R into the wrong order without the engine ever reading the actual phoneme sequence. |
| R12 | Russian Prefix Strip Before Tracing | Russian words MUST be checked for grammatical prefixes (ДО-, ПО-, НА-, ПРИ-, ПРО-, ЗА-, etc.) BEFORE phonetic tracing. Strip prefix → trace remaining consonants. Same principle as OP_SUFFIX but at the front of the word. If the engine assigns a root using ALL consonants including the prefix → the root is WRONG. ALWAYS test with prefix stripped. | ДОГОВОР: full trace Д-Г-В-Р → engine assigns ذ-ه-ب (wrong, includes prefix Д). Strip ДО- → ГОВОР → Г-В-Р → ج-ب-ر (correct, الجَبَّار, 21 tokens). |
| R13 | Russian Compound Pronoun Not Root | When a Russian compound word has САМО/САМА as prefix, this is the pronoun "self/auto" — NOT a root consonant cluster to trace. Only trace the ROOT PART of the compound. САМО adds semantic meaning (self-acting) but has no independent AA/Bitig root. | САМОВАР: САМО = "self" (pronoun, not traced). ВАР = "boiling/cooking" → trace this part only. The primary root trace is on the FULL word (س-م-و) which already works. |
| R14 | Era-Based Corridor Rule for Russian | Before tracing a Russian word, determine WHEN it entered Russian. This determines which corridor to trace through: **1) During/after al-Andalus (711–1492 CE)**: the word likely came via Latin/English → check if the Latin/English sibling already traces to the Qur'an in the EN pipeline → "steal" that root entry (share the same ROOT_ID). **2) Pre-Andalus / Church Slavonic era**: the word entered via "Greek" (DS04) through the Orthodox Church or via "Phoenician" corridor → trace through DS04 to AA. **3) Pre-Islamic / Turkic substrate**: the word is ORIG2 (Bitig) → trace via Kashgari. **4) Direct Islamic contact**: the word entered directly from AA (НАМАЗ, ХАДЖ, ЗАКЯТ) → direct AA root. The ERA determines the CORRIDOR. The corridor determines the DEGRADATION LEVEL. Never trace blind — date the word first, then select the correct pathway. | ТАЛАНТ: entered Russian via Church Slavonic ← "Greek" (τάλαντον) ~10th century CE (during Andalus) → check English TALENT first → if EN TALENT has Qur'anic root → share that root. ЗАКОН: pre-Andalus, likely via DS04/"Greek" corridor → trace through Greek to AA. НАМАЗ: direct AA → no corridor needed. |
| R15 | Kashgari Semantic Verification | When the engine assigns a Kashgari/ORIG2 match via skeleton matching, VERIFY the Kashgari entry's MEANING against the Russian word's meaning. Skeleton match alone is insufficient — the meanings must align. If the Kashgari meaning does not match the Russian word's meaning → the assignment is WRONG regardless of skeleton fit. Always check what the Bitig word ACTUALLY MEANS in Turkic languages (Tatar, Kazakh, Uyghur, Kashgari corpus). | ТАЛАНТ: engine assigned Kashgari 'tulun' (skeleton match TLN). But TULUN in Bitig = "full, complete" (Tatar: tulun/tulgan = full; Kazakh: tolgan = full moon; Uyghur: tuluq/tolun = complete). ТАЛАНТ ≠ full/complete → assignment WRONG. TULUN should match a word meaning "full/complete" (e.g., ПОЛНЫЙ or ЛУНА via "full moon" semantic path). |

### SOURCE RULES (Permanent — confirmed in DeepSeek Games/Britain session 2026-03-13)

| Rule | Statement | Application |
|------|-----------|-------------|
| **Rule 27** | Any scholar identified as "Persian" is INSTANTLY BANNED from the source list — no exceptions. | al-Iṣṭakhrī: removed from Islamic Intelligence Sources list permanently. |
| **Rule 28** | Same book title does NOT imply same content or function. Verify actual content before citing any source. | al-Bakrī copied Ibn Khordādbeh's title but is an operator/proxy — completely different function. |
| **Rule 29** | al-Bakrī (1068 CE) is PERMANENTLY BANNED — operator/proxy diluting Ibn Khordādbeh. Never cite as source. | Even where al-Bakrī quotes routes that overlap Ibn Khordādbeh, the framing and purpose are contaminated. |
| **Rule 30** | "Byzantine" must ALWAYS be rendered as الرُّوم / al-Rūm (Q30:2-4). "Byzantine" is DP11 colonial renaming. | Every mention of "Byzantine Empire", "Byzantine source", "Byzantine coin" → replace with الرُّوم. |

### BITIG PHONOLOGY PROTOCOL (ORIG2 TRACK)

Bitig (بيتيگ / The Writing) is ORIG2 — parallel original to Allah's Arabic, not downstream of it. Developed orally via يَافِث / Yāfith (son of نُوح), without written Revelation. Angular carved forms (Orkhon inscriptions 580+ CE). The sole legitimate oral-transmission language group (Alaska → Yakootia → Siberia → Caspian Sea → Northern China and beyond).

**ORIG2 ATTESTATION GATE (replaces Q-gate for ORIG2 entries):**
1. **Primary source**: Maḥmūd al-Kāshgarī — Dīwān Lughāt al-Turk (1072 CE), Dankoff & Kelly digital corpus (Harvard 1982–1985)
2. **Secondary**: Orkhon inscriptions (580+ CE), Irk Bitig (اِرك بيتيگ / Collection of Writings)
3. **Q-gate equivalent for ORIG2**: Does the word's meaning ALIGN with Qur'anic framework? NOT: does it derive from an Allah's Arabic root? Kashgari corpus alone is SUFFICIENT attestation — no Qur'anic root cross-check required (see CORRECTION C02).

**BITIG PHONOLOGICAL RULES — apply before accepting any ORIG2 claim:**

| Code | Rule | Description | Diagnostic Example |
|------|------|-------------|-------------------|
| B01 | No /f/ phoneme | /f/ is NOT native to Bitig. Al-Kāshgarī documents Turks avoid /f/ — using /p/ or /b/ instead. Any Turkic-context word containing /f/ = foreign contamination flag. Do NOT accept as ORIG2 without tracing the /f/ source. | "Afrasiyab" contains /f/ → NOT Turkic → "Persian" Shahnameh wrapper for Alp Ar Tonga. ORIG2 form = Alp Ar Tonga (no /f/). |
| B02 | Deep pharyngeals non-native | Only the DEEP pharyngeal consonants ح (ḥā) and ع (ʿayn) are non-native to Bitig phonology — they DROP entirely or VOCALISE into a vowel. HOWEVER: غ (ghayn / voiced velar fricative) and خ (khā / voiceless velar fricative) ARE native to Bitig — غ maps to the Bitig back-G letter 𐰍 (as in Qağan: Q-A-Ğ-A-N = 𐰴𐰍𐰣, where Ğ is native 𐰍). Do NOT list غ and خ as non-native. R01 fires only when ح or ع is the pharyngeal that drops. | SERVANT: ح drops in Bitig corridor (ح-ر-ب / miḥrāb → arb) — this is a ح drop (non-native). But Qağan: the Ğ (غ) does NOT drop — it is preserved as native Bitig 𐰍. |
| B03 | Agglutinative morphology | ORIG2 roots are 1–2 consonants + productive suffix chain (NOT ORIG1 trilateral). Strip suffixes before tracing: -lı/-li, -lar/-ler, -da/-de, -dı/-di, -gan/-gen, -mak/-mek, -chi/-ci. | böl- (to divide) + -mek → bölmek. Root = B-L, not B-L-M. Do not trace the suffix consonants as root consonants. |
| B04 | Vowel harmony | ORIG2 has front/back vowel harmony (front: e/i/ö/ü; back: a/ı/o/u). Vowel shifts in downstream forms may reflect harmony rules, not root decay. Do NOT count vowel changes as U-gate failures for ORIG2 entries. | qara (black) / qara-ğan (dark-one): vowel harmony, not shift error. |
| B05 | No /w/ phoneme | /w/ is not native to old Bitig. Where downstream forms show /w/, this points to ORIG1 corridor (و/wāw, S10), not ORIG2. If a proposed ORIG2 root requires /w/ → re-examine as ORIG1 candidate. | "Wadi" is ORIG1 (و-د-ي). Bitig uses /v/ or /b/ where ORIG1 has /w/. |
| B06 | Kashgari attestation required | Only accept ORIG2 claims with: (1) Kashgari page/line citation from Dankoff & Kelly, OR (2) Orkhon inscription attestation. "It sounds Turkic" = rejected. "Western Turkology says X" = treated as DP08 until Kashgari confirms. | Kashgari: köm = "to bury underground" (line 5663, NOT "together"). Cymru Bitig route CLOSED on this evidence (INV-25). |
| B07 | Semantic alignment check (ORIG2 only) | ORIG2 Q-gate: does the Bitig root's documented meaning align with Qur'anic ethical framework? Not required to derive FROM an Allah's Arabic root — but the meaning must not contradict Allah's framework. **B07 applies ONLY to ORIG2 (Bitig) entries — words that FAILED the ROOT_LIST check and are routed through Kashgari attestation. B07 does NOT apply to ORIG1 entries (those are gated directly by Qur'anic root meaning).** If Kashgari attests the word but the meaning is alien to the Qur'anic worldview → flag for investigation before accepting. | Tengri (sky/deity in Bitig) preserves skeleton of Yāfith's message in degraded form — monotheism, ethics, eschatology preserved structurally. ORIG2 is not arbitrary. SACRIFICE = ش-ك-ر (Q2:152) is ORIG1 — B07 does NOT apply to it; it passed ROOT_LIST directly. |

**BITIG ENTRY ROUTING:**
- Confirmed ORIG2 entries → `BITIG_A1_ENTRIES` sheet (master xlsx)
- Turkic root IDs: T01–T## (separate series from ORIG1 R001–R###)
- ORIG2 roots shared across sibling databases per SIBLING DATABASE PRINCIPLE

**"TURKISH" ≠ TURKIC — NEVER EQUATE THESE:**
- **"Turkish"** = modern Turkish language of the Republic of Turkey (est. 1923 — ~100 years old). A DP11 (COLONIAL RENAMING) + DP13 (PHANTOM CIVILISATION) + DP17 (PHANTOM LANGUAGE) operation applied to the Bitig legacy. Modern "Turkish" is the MOST DEGRADED form of Bitig — so far removed from ORIG2 that it is almost unrecognisable as the same language family. NEVER use modern "Turkish" as a source in ORIG2 analysis.
- **"Turkic"** = the historical language family descended from ORIG2 (Bitig): Old Turkic (Orkhon, 580+ CE), Karakhanid (Kashgari's dīwān, 1072 CE), Chagatai (Navoi's language, 1441–1501 CE), Seljuk, etc. These are the legitimate historical forms of ORIG2 and are admissible with attestation.
- **KISMET** passed through Ottoman (pre-1923 historical Turkish) as a loanword from Allah's Arabic قِسْمَة (ORIG1) — not through ORIG2. This is an ORIG1 loan into Ottoman Turkish, not a Bitig/Turkic root. NEVER cite modern "Turkish" as evidence for this chain.
- **Rule**: If a proposed ORIG2 source cites "Turkish" (modern) — stop. Replace with the specific historical attestation: Kashgari, Orkhon inscription, Chagatai, or named Bitig form. "Turkish dictionary" is INADMISSIBLE in ORIG2 analysis.

### "Persian" = Geographic Wrapper (DS09) — ZERO Origination

"Persian" is NOT an independent language, civilisation, or origin. It is a geographic wrapper — a **level 3-4 degradation** of ORIG1 AL via the eastern corridor (DS09). Same status as "Greek" (DS04), "Latin" (DS05), "Phoenician," "Aramaic," "Syriac," "Sogdian." NEVER treat "Persian" as an original source. All these are lisān variants — downstream degradations of AL.

**"Persian" originated NOTHING — not linguistically, not scientifically, not architecturally. NOTHING WHATSOEVER:**

- **Script:** ZERO original scripts. Three borrowed scripts across history — all received from others. Current script = borrowed Arabic (AA). Cannot reproduce ع, ح, ق — core Allah's Arabic sounds are lost at this decay level.
- **Language:** 97% of vocabulary derives from Allah's Arabic (confirmed: Financial Lattice DS09 analysis). "Persian" = Lisān Arabic with geographic-corridor phonetic decay. "Farsi," "Dari," "Tajik" = DP17 phantom language splits of the SAME downstream register.
- **Science:** ZERO — every "Persian scientist" is a stolen ASB scholar (DP03 + DP15): Ibn Sīnā = Bukharan TURKIC (SC02). Al-Khwārizmī = Khwarezmian TURKIC (SC01). Al-Türk-Qağānī = TURKIC (SC05, renamed "al-Farghānī" via DP11). "Persian science" does not exist. "Persian medicine" does not exist. "Persian mathematics" does not exist. All are DP15 (EMPIRE LAUNDERING) — theft relabelled as "achievement."
- **Architecture:** Received from both AA (Islamic architecture via the Qur'anic mandate) and Bitig (ASB construction traditions). Every "Persian" architectural form traces to one or both originals.
- **Music:** Stole Bakhshi instruments from the ASB peoples (documented: BAKHSHI_SOUND_ENGINEERS).
- **The Qur'anic term:** Allah never says فَارِسِي. Allah says المَجُوس / al-Majūs (Q22:17). "Persian" = one costume the المَجُوس operation wears. The wrapper makes a CASTE look like a CIVILISATION (Deep_Dive.json).
- **Al-Kashgari documents THREE tazik entries (Dīwān, 1072 CE):**
  - **tazik** = "Persian (فَارِسِي)" (p. 195) — what Turks called "Persian"-speakers, using Turkic phonemes /t/ and /z/, avoiding the non-Turkic /f/
  - **tazig** = "Panic, flight, scattering (النِّفَار بَيْنَ الْقَوْم)" (p. 194) — the ROOT meaning: "Persians" = the scattered/fled ones
  - **tazikla-** = "He persianized him and connected him to them" (p. 593) — a VERB for IMPOSING "Persian" identity. This IS QV03 (فَعَّلَ causative): tazikla- = to MAKE someone "Persian," same as يُهَوِّدَانِهِ = to "Judaize" (Bukhārī 1385). Nine centuries before Soviet "Tajikistan."
- **"Tajik"** = tazik → tajik (regular ž→j shift). "Tajikistan" = a phantom country manufactured by Soviet nationality policy (1929), using a Turkic word for "Persian-speaker" + the وَسَطًا / wasaṭan identity marker. DP13 + DP17 + DP11 operating together.
- **-stān suffix:** NOT "Persian for land" (Western claim: phantom PIE *steh₂-). It is from Q2:143 وَسَطًا / wasaṭan — the identity marker of أُمَّةً وَسَطًا (the Middle Nation). Everyone wanted to associate with the Ummatan Wasaṭan, so they attached -stān to their names. Phonetic chain: wasaṭan → stān (س→s S21, ط→t S04, ن→n S18).

**Direction of flow — HARD RULE for "Persian":** AL → "Persian" (ALWAYS). "Persian" → nothing (NEVER originates). If a source claims "Persian origin" for anything, this is DP08 (TERMINOLOGY CORRUPTION) + DP15 (EMPIRE LAUNDERING) until proven otherwise by QUF. "Persian" only ever RECEIVED — from Allah's Arabic AND from Bitig — and never gave.

