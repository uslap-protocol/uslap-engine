# DOCUMENTARY CONVENTIONS — FULL REFERENCE

> Served on demand via: `python3 Code_files/uslap_handler.py context conventions`
> Referenced from: CLAUDE.md § Documentary Conventions

These rules apply to ALL documents, research files, timelines, and outputs — not just lattice entries.

---

## 1. FULL PHRASES IN DOCUMENTS — NO ABBREVIATIONS

| Abbreviation | Full Phrase (USE THIS in all documents) |
|--------------|----------------------------------------|
| AA / AL / ORIG1 | **Allah's Arabic** |
| LA | **Lisān Arabic** |
| ATT | Arabic / Transliteration / Translation (explain the format, don't just say "ATT") |

The user abbreviates in prompts. You NEVER abbreviate in documents. Always use the entire phrase.

---

## 2. ATT FORMAT — MANDATORY FOR EVERY ALLAH'S ARABIC WORD

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

---

## 2A. QUR'ANIC TRANSLATION — ROOT-ONLY (NEVER USE ENGLISH TRANSLATIONS)

**ALL English translations of the Qur'an are operator-contaminated.** Do NOT copy-paste from Sahih International, Pickthall, Yusuf Ali, or ANY published English translation. They all drink from the same contaminated well.

**MANDATORY PROTOCOL:**
1. **Read the Arabic text** — the ONLY preserved text (Q15:9)
2. **Identify each root** — use the root dictionary, NOT translator glosses
3. **Translate from roots** — build meaning from root letters, not from published translations
4. **Flag suspicious renderings** — if a root translation doesn't fit Allah's context (e.g. Allah calling His own creation "despised"), FLAG IT as QV-contaminated
5. **Check QV register** — `qv_translation_register` may already have the correction
6. **NEVER reproduce a contaminated translation without flagging it**

**Example of contamination:** Q32:8 مَّاءٍ مَّهِينٍ — operators translate مَهِين as "despised." But Q43:52 uses the SAME word — spoken by Firʿawn to insult Mūsā عليه السلام. Allah describing His creation ≠ Firʿawn insulting a Prophet. The operator gave Firʿawn's meaning to Allah's word.

---

## 3. WRAPPER NAMES — ALL NON-QUR'ANIC NAMES IN QUOTES

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

---

## 4. SOURCE HIERARCHY — QUR'AN ALWAYS FIRST

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

---

## 5. NON-LATTICE / NON-QUR'ANIC TERM FLAGGING

If a term is NOT found in the Qur'an AND NOT found in the lattice databases, it MUST be flagged:

```
"[TERM]" (NOT a Qur'anic term, NOT in the lattice)
```

**Example:** "Hyksos" (NOT a Qur'anic term, NOT in the lattice) — use instead: foreign-ruler period in مِصْر / Miṣr / Egypt

Use Allah's Arabic vocabulary from the Qur'an wherever possible. If no Qur'anic equivalent exists, describe the concept using Qur'anic roots or flag the term.

---

## 6. DETECTION PATTERN TAGGING

When documenting a contaminated claim, always tag it with the relevant DP code:

```
"Persian borrowed from Greek" — DP08 (TERMINOLOGY CORRUPTION): direction inverted
"Silk Road" — DP07 (EXISTENCE ERASURE) + DP11 (COLONIAL RENAMING)
```
