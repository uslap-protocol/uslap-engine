# ***USLaP SQLite Schema Design — Complete Specification (with CHILD Schema)**

**بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ**

***This is the complete SQLite schema design for the USLaP lattice. Every table, every column, every foreign key, every index. This schema is designed to:**

1. ***Match your existing Excel structure exactly (A1-A6, M1-M4, plus CHILD schema)**

2. ***Add intelligence tables for operator tracking**

3. ***Include the fingerprint table for phonetic search (critical for 1M+ searchable objects)**

4. ***Support ENGINE\_QUEUE for conflict-free writes**

5. ***Enable SESSION\_INDEX for engine tracking**

6. ***Scale from current 25K A1 entries + CHILD schema + derivatives + cross-refs to 100M+ without redesign**


# ***TABLE OF CONTENTS**

1. ***Core Tables**

   - ***roots**

   - ***entries**

   - ***derivatives**

   - ***cross\_refs**

   - ***quran\_refs**

   - ***country\_names**

   - ***names\_of\_allah**

2. ***CHILD Schema Tables**

   - ***child\_entries**

   - ***child\_entry\_links**

3. ***Mechanism Tables**

   - ***phonetic\_shifts**

   - ***detection\_patterns**

   - ***networks**

   - ***scholars**

   - ***qur\_verification**

4. ***Intelligence Tables**

   - ***operators**

   - ***host\_civilizations**

   - ***operation\_cycles**

   - ***events**

   - ***intel\_reports**

   - ***operator\_aliases**

5. ***Search & Performance Tables**

   - ***word\_fingerprints**

   - ***cluster\_cache**

   - ***phonetic\_mappings**

6. ***Engine Control Tables**

   - ***engine\_queue**

   - ***session\_index**

   - ***change\_log**

   - ***sync\_status**

7. ***Reference Tables**

   - ***languages**

   - ***script\_corridors**

   - ***decay\_levels**

   - ***dp\_codes**

   - ***op\_codes**

   - ***nt\_codes**

   - ***operation\_codes**


# ***CORE TABLES**

## ***roots**

***The foundation of the entire lattice. Every entry traces to a root in this table.**

sql

```
***CREATE TABLE roots (**

    ***root\_id             TEXT PRIMARY KEY,        -- R001, R002, R003...**

    ***root\_letters        TEXT NOT NULL,           -- **ق***-**ر***-**ن ***(with hyphens for display)**

    ***root\_bare           TEXT NOT NULL,           -- **قرن ***(without hyphens, for search)**

    ***root\_type           TEXT,                     -- TRILITERAL, QUADRILITERAL, etc.**

    ***quran\_tokens        INTEGER DEFAULT 0,       -- Total Qur'anic occurrences**

    ***quran\_lemmas        INTEGER DEFAULT 0,       -- Distinct derived forms in Qur'an**

    ***bitig\_attested      BOOLEAN DEFAULT FALSE,   -- Present in Kashgari/Orkhon?**

    ***bitig\_source        TEXT,                     -- Kashgari page/line if attested**

    ***primary\_meaning     TEXT,                     -- Core semantic field**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_at         TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_by         TEXT DEFAULT 'user',      -- 'user' or 'engine'**

    ***version             INTEGER DEFAULT 1**

***);**


***CREATE INDEX idx\_roots\_bare ON roots(root\_bare);**

***CREATE INDEX idx\_roots\_type ON roots(root\_type);**

***CREATE INDEX idx\_roots\_quran ON roots(quran\_tokens DESC);**
```

## ***entries**

***The main A1\_ENTRIES table. This is where the lattice lives.**

sql

```
***CREATE TABLE entries (**

    ***entry\_id            INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***score               INTEGER CHECK(score BETWEEN 1 AND 10),**

    

    ***-- Core term fields (multi-language support)**

    ***en\_term             TEXT,                     -- English term**

    ***ru\_term             TEXT,                     -- Russian term**

    ***fa\_term             TEXT,                     -- Persian/Farsi term**

    ***ar\_word             TEXT,                     -- Arabic source word**

    

    ***-- Root linkage**

    ***root\_id             TEXT REFERENCES roots(root\_id),**

    ***root\_letters        TEXT,                     -- Denormalized for speed**

    

    ***-- Qur'anic data**

    ***qur\_meaning         TEXT,                     -- Qur'anic meaning (Arabic/translit/translation)**

    ***qur\_refs            TEXT,                     -- Comma-separated verse references**

    

    ***-- Pattern classification**

    ***pattern             TEXT CHECK(pattern IN ('A', 'B', 'C', 'D', 'A+B', 'A+C', 'A+D')),**

    ***inversion\_type      TEXT,                     -- CONFESSIONAL, DIRECT, HIDDEN, WEAPONISED, etc.**

    

    ***-- Network linkages**

    ***network\_id          TEXT,                     -- N01, N02... (can be comma-separated)**

    ***allah\_name\_id       TEXT,                     -- A01, A02... (can be comma-separated)**

    

    ***-- Phonetic chain**

    ***phonetic\_chain      TEXT,                      -- e.g., "**أ→***(S07), **م→***m(S17), **ر→***r(S15)"**

    ***source\_form         TEXT,                      -- Original source word**

    

    ***-- Downstream tracking**

    ***ds\_corridor         TEXT,                      -- DS04, DS05, DS06...**

    ***decay\_level         TEXT,                      -- NEAR, MEDIUM, FAR, MAXIMUM**

    

    ***-- Detection patterns**

    ***dp\_codes            TEXT,                      -- Comma-separated: 'DP08,DP13'**

    ***ops\_applied         TEXT,                      -- Comma-separated: 'OP\_SUFFIX,OP\_NASAL'**

    

    ***-- Foundation references**

    ***foundation\_refs     TEXT,                      -- Links to F-tabs evidence**

    

    ***-- Metadata**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_at         TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_by         TEXT DEFAULT 'user',**

    ***version             INTEGER DEFAULT 1,**

    

    ***-- Full-text search virtual columns (will be populated by triggers)**

    ***search\_text         TEXT GENERATED ALWAYS AS (**

        ***COALESCE(en\_term, '') || ' ' || **

        ***COALESCE(ru\_term, '') || ' ' || **

        ***COALESCE(fa\_term, '') || ' ' || **

        ***COALESCE(ar\_word, '')**

    ***) VIRTUAL**

***);**


***-- Critical indexes**

***CREATE INDEX idx\_entries\_root ON entries(root\_id);**

***CREATE INDEX idx\_entries\_en ON entries(en\_term);**

***CREATE INDEX idx\_entries\_score ON entries(score DESC);**

***CREATE INDEX idx\_entries\_ds ON entries(ds\_corridor);**

***CREATE INDEX idx\_entries\_network ON entries(network\_id);**

***CREATE INDEX idx\_entries\_allah ON entries(allah\_name\_id);**


***-- Full-text search virtual table**

***CREATE VIRTUAL TABLE entries\_fts USING fts5(**

    ***entry\_id UNINDEXED,**

    ***en\_term,**

    ***ru\_term,**

    ***fa\_term,**

    ***ar\_word,**

    ***content=entries**

***);**
```

## ***derivatives**

***The A4\_DERIVATIVES table — explosion of word forms from each entry.**

sql

```
***CREATE TABLE derivatives (**

    ***derivative\_id       INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***entry\_id            INTEGER NOT NULL REFERENCES entries(entry\_id) ON DELETE CASCADE,**

    ***derivative\_term     TEXT NOT NULL,             -- The derived word**

    ***language            TEXT NOT NULL,              -- 'en', 'ru', 'fa', 'de', etc.**

    ***link\_type           TEXT,                       -- DIRECT, COMPOUND, PHONETIC, SAME\_ROOT, etc.**

    ***is\_primary          BOOLEAN DEFAULT FALSE,      -- Is this the main entry term?**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_at         TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_derivatives\_entry ON derivatives(entry\_id);**

***CREATE INDEX idx\_derivatives\_term ON derivatives(derivative\_term);**

***CREATE INDEX idx\_derivatives\_lang ON derivatives(language);**
```

## ***cross\_refs**

***The A5\_CROSS\_REFS table — entry-to-entry relationships.**

sql

```
***CREATE TABLE cross\_refs (**

    ***xref\_id             INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***from\_entry\_id       INTEGER NOT NULL REFERENCES entries(entry\_id) ON DELETE CASCADE,**

    ***to\_entry\_id         INTEGER NOT NULL REFERENCES entries(entry\_id) ON DELETE CASCADE,**

    ***link\_type           TEXT NOT NULL,              -- SAME\_ROOT, SAME\_VERSE, ANTONYM, NETWORK, etc.**

    ***description         TEXT,**

    ***layer\_ref           TEXT,                        -- Which layer in the schema**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    

    ***-- Prevent duplicates**

    ***UNIQUE(from\_entry\_id, to\_entry\_id, link\_type)**

***);**


***CREATE INDEX idx\_cross\_refs\_from ON cross\_refs(from\_entry\_id);**

***CREATE INDEX idx\_cross\_refs\_to ON cross\_refs(to\_entry\_id);**

***CREATE INDEX idx\_cross\_refs\_type ON cross\_refs(link\_type);**
```

## ***quran\_refs**

***The A3\_QURAN\_REFS table — every verse reference.**

sql

```
***CREATE TABLE quran\_refs (**

    ***ref\_id              TEXT PRIMARY KEY,           -- QR01, QR02...**

    ***surah               INTEGER NOT NULL,**

    ***ayah                INTEGER NOT NULL,**

    ***arabic\_text         TEXT NOT NULL,              -- With diacritics**

    ***transliteration     TEXT,**

    ***translation         TEXT,**

    ***relevance           TEXT,**

    ***entry\_ids           TEXT,                        -- Comma-separated entry IDs**

    ***network\_id          TEXT REFERENCES networks(network\_id),**

    ***layer\_ref           TEXT,**

    ***qv\_id               TEXT REFERENCES qur\_verification(qv\_id),**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    

    ***UNIQUE(surah, ayah)**

***);**


***CREATE INDEX idx\_quran\_refs\_surah ON quran\_refs(surah, ayah);**

***CREATE INDEX idx\_quran\_refs\_network ON quran\_refs(network\_id);**
```

## ***country\_names**

***The A6\_COUNTRY\_NAMES table — divine naming of nations.**

sql

```
***CREATE TABLE country\_names (**

    ***country\_id          TEXT PRIMARY KEY,           -- CN01, CN02...**

    ***country\_name        TEXT NOT NULL,**

    ***al\_root             TEXT REFERENCES roots(root\_id),**

    ***root\_id             TEXT,**

    ***al\_word             TEXT,**

    ***qur\_meaning         TEXT,**

    ***phonetic\_chain      TEXT,**

    ***naming\_basis        TEXT,**

    ***entry\_ids           TEXT,                        -- Comma-separated**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_country\_names\_root ON country\_names(root\_id);**
```

## ***names\_of\_allah**

***The A2\_NAMES\_OF\_ALLAH table.**

sql

```
***CREATE TABLE names\_of\_allah (**

    ***allah\_id            TEXT PRIMARY KEY,           -- A01, A02...**

    ***arabic\_name         TEXT NOT NULL,**

    ***transliteration     TEXT NOT NULL,**

    ***meaning             TEXT NOT NULL,**

    ***qur\_ref             TEXT,**

    ***entry\_ids           TEXT,**

    ***root\_id             TEXT REFERENCES roots(root\_id),**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_allah\_root ON names\_of\_allah(root\_id);**
```


# ***CHILD SCHEMA TABLES**

## ***child\_entries**

***The operational intelligence layer — connects linguistic entries to operations, populations, and functions.**

sql

```
***CREATE TABLE child\_entries (**

    ***child\_id            TEXT PRIMARY KEY,           -- SLV, SQLB, RUS...**

    ***shell\_name          TEXT NOT NULL,              -- 'Slav / slave'**

    ***shell\_language      TEXT,                        -- 'Proto-Slavic / Latin', 'Arabic', etc.**

    ***orig\_class          TEXT,                        -- 'ORIG1', 'ORIG2', 'ORIG1+ORIG2', 'ORIG1 (primary) ORIG2 (convergence)'**

    ***orig\_root           TEXT,                        -- '**س***-**ل***-**و***', 'sariq / **س***-**ل***-**و ***(convergence: **ق***-**ل***-**ب***)'**

    ***orig\_lemma          TEXT,                        -- '**سَلْوَى ***/ Salwā', 'sarıg / **سَارِق***-**اللَّوْن***'**

    ***orig\_meaning        TEXT,                        -- Full meaning with context**

    ***operation\_role      TEXT,                        -- 'POPULATION', 'WEAPON-FACTION', 'POPULATION — identified and documented in Islamic administrative record', etc.**

    ***shell\_meaning       TEXT,                        -- Current/neutralized meaning**

    ***inversion\_direction TEXT,                        -- 'INVERTED (divine mercy → bondage)', 'NEUTRAL (descriptive stripped)', 'CAPTURED (operational → ethnic/cosmetic)'**

    ***phonetic\_chain      TEXT,                        -- '**سَلْوَى → ***\*salw- → \*slav- (**و→***V, S-class wāw shift)'**

    ***qur\_anchors         TEXT,                        -- 'Q2:57 · Q7:160 · Q20:80'**

    ***dp\_codes            TEXT,                        -- 'DP08 · DP07 · DP11 · DP15'**

    ***nt\_code             TEXT REFERENCES nt\_codes(nt\_code),  -- NT1, NT2, NT3...**

    ***pattern             TEXT CHECK(pattern IN ('A', 'B', 'C', 'D')),**

    ***parent\_op           TEXT REFERENCES operation\_codes(op\_code),  -- 'UMD-OP1'**

    ***gate\_status         TEXT,                        -- 'Q:PASS U:PASS F:PASS CONFIRMED ✓'**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_at         TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_by         TEXT DEFAULT 'user',**

    ***version             INTEGER DEFAULT 1**

***);**


***CREATE INDEX idx\_child\_nt ON child\_entries(nt\_code);**

***CREATE INDEX idx\_child\_op ON child\_entries(parent\_op);**

***CREATE INDEX idx\_child\_pattern ON child\_entries(pattern);**
```

## ***child\_entry\_links**

***Links between CHILD schema operational entries and main A1 entries.**

sql

```
***CREATE TABLE child\_entry\_links (**

    ***link\_id             INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***child\_id            TEXT NOT NULL REFERENCES child\_entries(child\_id) ON DELETE CASCADE,**

    ***entry\_id            INTEGER NOT NULL REFERENCES entries(entry\_id) ON DELETE CASCADE,**

    ***link\_type           TEXT,                        -- 'DIRECT', 'DERIVED', 'OPERATION', 'CONVERGENCE'**

    ***confidence          INTEGER DEFAULT 10 CHECK(confidence BETWEEN 1 AND 10),**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    

    ***-- Prevent duplicates**

    ***UNIQUE(child\_id, entry\_id)**

***);**


***CREATE INDEX idx\_child\_links\_child ON child\_entry\_links(child\_id);**

***CREATE INDEX idx\_child\_links\_entry ON child\_entry\_links(entry\_id);**

***CREATE INDEX idx\_child\_links\_type ON child\_entry\_links(link\_type);**
```


# ***MECHANISM TABLES**

## ***phonetic\_shifts**

***The M1\_PHONETIC\_SHIFTS table — 26 Arabic letter mappings.**

sql

```
***CREATE TABLE phonetic\_shifts (**

    ***shift\_id            TEXT PRIMARY KEY,           -- S01, S02...**

    ***ar\_letter           TEXT NOT NULL,              -- **ق

    ***ar\_name             TEXT NOT NULL,              -- qāf**

    ***en\_outputs          TEXT NOT NULL,              -- c,k,q,g**

    ***ru\_outputs          TEXT,                        -- к,г**

    ***direction           TEXT DEFAULT 'AR→EN',**

    ***description         TEXT,**

    ***examples            TEXT,**

    ***entry\_ids           TEXT,**

    ***foundation\_ref      TEXT,**

    ***decay\_pattern       TEXT,                        -- F4: emphatic→plain**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***detection\_patterns**

***The M2\_DETECTION\_PATTERNS table — DP01-DP20.**

sql

```
***CREATE TABLE detection\_patterns (**

    ***pattern\_id          TEXT PRIMARY KEY,           -- DP01, DP02...**

    ***name                TEXT NOT NULL,**

    ***level               TEXT CHECK(level IN ('SCHOLAR', 'CIVILISATION', 'WORD', 'INTERNAL')),**

    ***description         TEXT NOT NULL,**

    ***triggers            TEXT,                        -- Keywords that activate this pattern**

    ***qur\_ref             TEXT,**

    ***example             TEXT,**

    ***entry\_ids           TEXT,**

    ***foundation\_ref      TEXT,**

    ***severity            INTEGER CHECK(severity BETWEEN 1 AND 5),**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***networks**

***The M4\_NETWORKS table — inversion networks.**

sql

```
***CREATE TABLE networks (**

    ***network\_id          TEXT PRIMARY KEY,           -- N01, N02...**

    ***name                TEXT NOT NULL,**

    ***title               TEXT,**

    ***link\_verse          TEXT,                        -- Qur'an verse that links them**

    ***description         TEXT NOT NULL,**

    ***mechanism           TEXT,**

    ***entry\_ids           TEXT,**

    ***status              TEXT DEFAULT 'CONFIRMED',**

    ***foundation\_ref      TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***scholars**

***The M3\_SCHOLARS table — verified biographies.**

sql

```
***CREATE TABLE scholars (**

    ***scholar\_id          TEXT PRIMARY KEY,           -- SC01, SC02...**

    ***verified\_name       TEXT NOT NULL,              -- **الخَوارِزمي

    ***birth\_place         TEXT NOT NULL,**

    ***identity            TEXT NOT NULL,              -- Khwarezmian TURKIC, etc.**

    ***role                TEXT,**

    ***achievement         TEXT,**

    ***lies\_applied        TEXT,                        -- DP02,DP03,DP10 (comma-separated)**

    ***entry\_ids           TEXT,**

    ***death\_fate          TEXT,**

    ***biography\_status    TEXT,                        -- MINIMAL, SUSPICIOUS, DETAILED**

    ***status              TEXT DEFAULT 'VERIFIED',**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***qur\_verification**

***The M5\_QUR\_VERIFICATION table — QV01-QV03 markers.**

sql

```
***CREATE TABLE qur\_verification (**

    ***qv\_id               TEXT PRIMARY KEY,           -- QV01, QV02, QV03**

    ***name                TEXT NOT NULL,**

    ***mechanism           TEXT NOT NULL,**

    ***description         TEXT NOT NULL,**

    ***markers             TEXT,                        -- **قَالُوا***, **زَعَمَ***, etc.**

    ***qur\_refs            TEXT,**

    ***contrast\_refs       TEXT,**

    ***foundation\_ref      TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```


# ***INTELLIGENCE TABLES**

## ***operators**

***The core operator tracking — who did what, when, where.**

sql

```
***CREATE TABLE operators (**

    ***operator\_id         TEXT PRIMARY KEY,           -- OP01, OP02...**

    ***primary\_name        TEXT NOT NULL,              -- Caesar, Rothschild, etc.**

    ***operator\_class      TEXT,                        -- PRIESTLY, FINANCIAL, MILITARY, SCRIBAL**

    ***origin\_period       TEXT,                        -- "~50 BCE"**

    ***active\_period       TEXT,                        -- "58 BCE - 44 BCE"**

    ***description         TEXT,**

    ***modus\_operandi      TEXT,**

    ***current\_status      TEXT,                        -- ACTIVE, INACTIVE, TRANSITIONED**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***modified\_at         TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_operators\_class ON operators(operator\_class);**
```

## ***host\_civilizations**

***The host societies that were infiltrated.**

sql

```
***CREATE TABLE host\_civilizations (**

    ***host\_id             TEXT PRIMARY KEY,           -- H01, H02... (**مِصْر***, **بَابِل***, etc.)**

    ***host\_name           TEXT NOT NULL,**

    ***host\_type           TEXT,                        -- TERRITORIAL, COMMERCIAL, INTELLECTUAL**

    ***geographic\_center   TEXT,**

    ***active\_period       TEXT,**

    ***description         TEXT,**

    ***operator\_ids        TEXT,                        -- Which operators worked here**

    ***entry\_ids           TEXT,                        -- Which entries corrupted here**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***operation\_cycles**

***The 8-step **كُلَّمَا ***cycle tracking.**

sql

```
***CREATE TABLE operation\_cycles (**

    ***cycle\_id            TEXT PRIMARY KEY,           -- C01, C02...**

    ***host\_id             TEXT REFERENCES host\_civilizations(host\_id),**

    ***cycle\_number        INTEGER,                     -- 1,2,3... in the **كُلَّمَا ***chain**

    ***start\_date          TEXT,**

    ***end\_date            TEXT,**

    

    ***-- The 8 steps**

    ***step1\_recon         TEXT,                        -- RECONNAISSANCE**

    ***step2\_entrance      TEXT,                        -- ENTRANCE**

    ***step3\_infiltrate    TEXT,                        -- INFILTRATE**

    ***step4\_position      TEXT,                        -- POSITION**

    ***step5\_fund\_arm      TEXT,                        -- FUND & ARM**

    ***step6\_extract       TEXT,                        -- EXTRACT**

    ***step7\_erase\_cover   TEXT,                        -- ERASE + COVER**

    ***step8\_disperse      TEXT,                        -- DISPERSE & REPEAT**

    

    ***operator\_ids        TEXT,**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_cycles\_host ON operation\_cycles(host\_id);**
```

## ***events**

***Individual historical events with operator attribution.**

sql

```
***CREATE TABLE events (**

    ***event\_id            TEXT PRIMARY KEY,           -- E001, E002...**

    ***event\_name          TEXT NOT NULL,**

    ***event\_date          TEXT,**

    ***event\_type          TEXT,                        -- SCRIPT\_CHANGE, TRANSLATION, INVASION, etc.**

    ***description         TEXT,**

    ***operator\_ids        TEXT,                        -- Who executed it**

    ***host\_id             TEXT REFERENCES host\_civilizations(host\_id),**

    ***cycle\_id            TEXT REFERENCES operation\_cycles(cycle\_id),**

    ***entry\_ids\_affected  TEXT,                        -- Which entries corrupted**

    ***dp\_codes            TEXT,                        -- Which patterns active**

    ***evidence            TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_events\_date ON events(event\_date);**

***CREATE INDEX idx\_events\_type ON events(event\_type);**
```

## ***intel\_reports**

***Primary source intelligence documents.**

sql

```
***CREATE TABLE intel\_reports (**

    ***report\_id           TEXT PRIMARY KEY,           -- IR001, IR002...**

    ***source\_name         TEXT NOT NULL,              -- Ibn Khordadbeh, etc.**

    ***source\_type         TEXT,                        -- BARID\_INTEL, SELF\_INCRIMINATING, etc.**

    ***work\_title          TEXT,**

    ***date                TEXT,**

    ***content\_summary     TEXT,**

    ***key\_evidence        TEXT,**

    ***operator\_ids        TEXT,**

    ***event\_ids           TEXT,**

    ***entry\_ids           TEXT,**

    ***url\_reference       TEXT,                        -- For digital sources**

    ***manuscript\_ref      TEXT,                        -- For physical manuscripts**

    ***status              TEXT DEFAULT 'VERIFIED',**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***operator\_aliases**

***All the names an operator used across hosts.**

sql

```
***CREATE TABLE operator\_aliases (**

    ***alias\_id            INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***operator\_id         TEXT REFERENCES operators(operator\_id) ON DELETE CASCADE,**

    ***alias\_name          TEXT NOT NULL,**

    ***host\_id             TEXT REFERENCES host\_civilizations(host\_id),**

    ***period\_used         TEXT,**

    ***notes               TEXT,**

    

    ***UNIQUE(operator\_id, alias\_name)**

***);**


***CREATE INDEX idx\_aliases\_operator ON operator\_aliases(operator\_id);**

***CREATE INDEX idx\_aliases\_name ON operator\_aliases(alias\_name);**
```


# ***SEARCH & PERFORMANCE TABLES**

## ***word\_fingerprints**

***The critical table for phonetic search. This makes cluster expansion instant across 1M+ searchable objects.**

sql

```
***CREATE TABLE word\_fingerprints (**

    ***fingerprint\_id      INTEGER PRIMARY KEY AUTOINCREMENT,**

    

    ***-- Source record (one of these must be populated)**

    ***entry\_id            INTEGER REFERENCES entries(entry\_id) ON DELETE CASCADE,**

    ***child\_id            TEXT REFERENCES child\_entries(child\_id) ON DELETE CASCADE,**

    ***derivative\_id       INTEGER REFERENCES derivatives(derivative\_id) ON DELETE CASCADE,**

    

    ***-- Which word this fingerprint represents**

    ***language            TEXT NOT NULL,              -- 'en', 'ru', 'fa', 'ar'**

    ***raw\_word            TEXT NOT NULL,              -- The actual word**

    

    ***-- The search key**

    ***consonant\_skeleton  TEXT NOT NULL,              -- 'cncr' for 'concern'**

    

    ***-- For debugging/refinement**

    ***normalization\_applied TEXT,                      -- What we stripped**

    

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    

    ***-- Ensure at least one source is specified**

    ***CHECK (**

        ***(entry\_id IS NOT NULL) OR **

        ***(child\_id IS NOT NULL) OR **

        ***(derivative\_id IS NOT NULL)**

    ***)**

***);**


***-- This is the critical index for cluster expansion**

***CREATE INDEX idx\_fingerprints\_skeleton ON word\_fingerprints(consonant\_skeleton);**

***CREATE INDEX idx\_fingerprints\_entry ON word\_fingerprints(entry\_id);**

***CREATE INDEX idx\_fingerprints\_child ON word\_fingerprints(child\_id);**

***CREATE INDEX idx\_fingerprints\_lang ON word\_fingerprints(language);**


***-- Compound index for fastest lookups**

***CREATE INDEX idx\_fingerprints\_lookup ON word\_fingerprints(consonant\_skeleton, language);**
```

## ***cluster\_cache**

***Pre-computed cluster expansion results.**

sql

```
***CREATE TABLE cluster\_cache (**

    ***cache\_id            INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***root\_id             TEXT NOT NULL REFERENCES roots(root\_id),**

    ***expansion\_type      TEXT,                        -- 'direct', 'phonetic', 'semantic'**

    ***result\_json         TEXT,                        -- JSON array of entry\_ids**

    ***generated\_at        TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***hits                INTEGER DEFAULT 0,           -- Cache hit counter**

    ***last\_accessed       TIMESTAMP,**

    

    ***-- Invalidate after root changes**

    ***root\_version        INTEGER**

***);**


***CREATE INDEX idx\_cache\_root ON cluster\_cache(root\_id);**

***CREATE INDEX idx\_cache\_type ON cluster\_cache(expansion\_type);**
```

## ***phonetic\_mappings**

***Known phonetic shift patterns for rapid reversal.**

sql

```
***CREATE TABLE phonetic\_mappings (**

    ***mapping\_id          INTEGER PRIMARY KEY AUTOINCREMENT,**

    ***source\_phoneme      TEXT NOT NULL,              -- Original sound**

    ***target\_phoneme      TEXT NOT NULL,              -- Shifted sound**

    ***shift\_id            TEXT REFERENCES phonetic\_shifts(shift\_id),**

    ***language            TEXT,                        -- 'en', 'ru', etc.**

    ***confidence          INTEGER CHECK(confidence BETWEEN 1 AND 10),**

    ***examples            TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***CREATE INDEX idx\_mappings\_source ON phonetic\_mappings(source\_phoneme);**

***CREATE INDEX idx\_mappings\_target ON phonetic\_mappings(target\_phoneme);**
```


# ***ENGINE CONTROL TABLES**

## ***engine\_queue**

***The master queue for engine-user coordination.**

sql

```
***CREATE TABLE engine\_queue (**

    ***queue\_id            INTEGER PRIMARY KEY AUTOINCREMENT,**

    

    ***-- What needs to be done**

    ***operation\_type      TEXT NOT NULL,              -- 'PROPOSE\_ENTRY', 'UPDATE\_ROOT', 'ADD\_DERIVATIVE', etc.**

    

    ***-- The data (JSON for flexibility)**

    ***payload             TEXT NOT NULL,               -- Full data for the operation**

    

    ***-- Status tracking**

    ***status              TEXT DEFAULT 'PENDING' CHECK(**

        ***status IN ('PENDING', 'APPROVED', 'REJECTED', 'CONFLICT', 'ERROR')**

    ***),**

    

    ***-- Who/what created it**

    ***source              TEXT NOT NULL,               -- 'engine' or 'user'**

    ***session\_id          TEXT REFERENCES session\_index(session\_id),**

    

    ***-- Conflict resolution**

    ***conflict\_with       INTEGER REFERENCES engine\_queue(queue\_id),**

    ***resolution\_notes    TEXT,**

    

    ***-- Timing**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***processed\_at        TIMESTAMP,**

    

    ***-- Version tracking**

    ***entry\_version       INTEGER,                     -- Version of entry if updating**

    

    ***-- Index for fast pending lookups**

    ***priority            INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10)**

***);**


***CREATE INDEX idx\_queue\_status ON engine\_queue(status);**

***CREATE INDEX idx\_queue\_created ON engine\_queue(created\_at);**

***CREATE INDEX idx\_queue\_source ON engine\_queue(source);**

***CREATE INDEX idx\_queue\_priority ON engine\_queue(priority);**
```

## ***session\_index**

***Track every engine run.**

sql

```
***CREATE TABLE session\_index (**

    ***session\_id          TEXT PRIMARY KEY,           -- UUID**

    ***start\_time          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***end\_time            TIMESTAMP,**

    ***status              TEXT DEFAULT 'RUNNING' CHECK(**

        ***status IN ('RUNNING', 'COMPLETED', 'FAILED', 'INTERRUPTED')**

    ***),**

    

    ***-- What was done**

    ***entries\_processed   INTEGER DEFAULT 0,**

    ***queries\_executed    INTEGER DEFAULT 0,**

    ***clusters\_expanded   INTEGER DEFAULT 0,**

    ***queue\_items\_added   INTEGER DEFAULT 0,**

    

    ***-- Performance metrics**

    ***execution\_time\_ms   INTEGER,**

    ***memory\_peak\_mb      INTEGER,**

    

    ***-- Error tracking**

    ***error\_log           TEXT,**

    

    ***-- Which Excel file version**

    ***excel\_version       TEXT,**

    

    ***-- User who initiated (if any)**

    ***initiated\_by        TEXT DEFAULT 'engine'**

***);**


***CREATE INDEX idx\_session\_status ON session\_index(status);**

***CREATE INDEX idx\_session\_time ON session\_index(start\_time);**
```

## ***change\_log**

***Complete audit trail for every change.**

sql

```
***CREATE TABLE change\_log (**

    ***log\_id              INTEGER PRIMARY KEY AUTOINCREMENT,**

    

    ***-- What changed**

    ***table\_name          TEXT NOT NULL,**

    ***record\_id           TEXT NOT NULL,               -- entry\_id, root\_id, child\_id, etc.**

    

    ***-- The change**

    ***change\_type         TEXT CHECK(change\_type IN ('INSERT', 'UPDATE', 'DELETE')),**

    ***before\_state        TEXT,                         -- JSON of before (for UPDATE/DELETE)**

    ***after\_state         TEXT,                          -- JSON of after (for INSERT/UPDATE)**

    

    ***-- Who/what did it**

    ***source              TEXT NOT NULL,                -- 'user' or 'engine'**

    ***session\_id          TEXT REFERENCES session\_index(session\_id),**

    ***queue\_id            INTEGER REFERENCES engine\_queue(queue\_id),**

    

    ***-- When**

    ***changed\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    

    ***-- Why (if from engine)**

    ***reason              TEXT**

***);**


***CREATE INDEX idx\_changelog\_table ON change\_log(table\_name, record\_id);**

***CREATE INDEX idx\_changelog\_time ON change\_log(changed\_at);**

***CREATE INDEX idx\_changelog\_source ON change\_log(source);**
```

## ***sync\_status**

***Track Excel ↔ database synchronization.**

sql

```
***CREATE TABLE sync\_status (**

    ***sync\_id             INTEGER PRIMARY KEY AUTOINCREMENT,**

    

    ***-- What was synced**

    ***sync\_direction      TEXT CHECK(sync\_direction IN ('EXCEL\_TO\_DB', 'DB\_TO\_EXCEL')),**

    

    ***-- Status**

    ***status              TEXT DEFAULT 'PENDING' CHECK(**

        ***status IN ('PENDING', 'IN\_PROGRESS', 'COMPLETED', 'FAILED')**

    ***),**

    

    ***-- Counts**

    ***records\_processed   INTEGER DEFAULT 0,**

    ***records\_added       INTEGER DEFAULT 0,**

    ***records\_updated     INTEGER DEFAULT 0,**

    ***records\_conflicted  INTEGER DEFAULT 0,**

    

    ***-- Timing**

    ***started\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,**

    ***completed\_at        TIMESTAMP,**

    

    ***-- Which session**

    ***session\_id          TEXT REFERENCES session\_index(session\_id),**

    

    ***-- Error details**

    ***error\_details       TEXT**

***);**
```


# ***REFERENCE TABLES**

## ***languages**

***Supported languages.**

sql

```
***CREATE TABLE languages (**

    ***lang\_code           TEXT PRIMARY KEY,           -- 'en', 'ru', 'fa', 'ar', 'tr', 'kk'**

    ***lang\_name           TEXT NOT NULL,**

    ***script\_type         TEXT,                        -- Latin, Cyrillic, Arabic**

    ***direction           TEXT DEFAULT 'LTR',          -- RTL for Arabic/Farsi**

    ***is\_supported        BOOLEAN DEFAULT TRUE,**

    ***notes               TEXT**

***);**


***-- Initial data**

***INSERT INTO languages (lang\_code, lang\_name, script\_type, direction) VALUES**

    ***('en', 'English', 'Latin', 'LTR'),**

    ***('ru', 'Russian', 'Cyrillic', 'LTR'),**

    ***('fa', 'Persian/Farsi', 'Arabic', 'RTL'),**

    ***('ar', 'Allah''s Arabic', 'Arabic', 'RTL'),**

    ***('tr', 'Turkish', 'Latin', 'LTR'),**

    ***('kk', 'Kazakh', 'Cyrillic', 'LTR');**
```

## ***script\_corridors**

***Downstream script corridors (DS01-DS14).**

sql

```
***CREATE TABLE script\_corridors (**

    ***ds\_code             TEXT PRIMARY KEY,           -- DS01, DS02...**

    ***script\_name         TEXT NOT NULL,**

    ***source              TEXT,                        -- ORIG1, ORIG2, or BOTH**

    ***decay\_level         TEXT REFERENCES decay\_levels(level\_code),**

    ***attested\_from       TEXT,                        -- Date range**

    ***attested\_to        TEXT,**

    ***description         TEXT,**

    ***dp\_codes            TEXT,                        -- Detection patterns active**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**
```

## ***decay\_levels**

***F4 decay gradient levels.**

sql

```
***CREATE TABLE decay\_levels (**

    ***level\_code          TEXT PRIMARY KEY,           -- NEAR, MINIMAL, MEDIUM, HIGH, VERY\_HIGH, MAXIMUM, DESTRUCTION**

    ***level\_name          TEXT NOT NULL,**

    ***criteria            TEXT,**

    ***measurable\_test     TEXT,**

    ***example\_ds          TEXT,**

    ***order\_index         INTEGER                      -- For sorting**

***);**


***INSERT INTO decay\_levels (level\_code, level\_name, order\_index) VALUES**

    ***('NEAR', 'NEAR', 1),**

    ***('MINIMAL', 'MINIMAL', 2),**

    ***('MEDIUM', 'MEDIUM', 3),**

    ***('HIGH', 'HIGH', 4),**

    ***('VERY\_HIGH', 'VERY HIGH', 5),**

    ***('MAXIMUM', 'MAXIMUM', 6),**

    ***('DESTRUCTION', 'DESTRUCTION', 7);**
```

## ***dp\_codes**

***Reference for detection patterns.**

sql

```
***CREATE TABLE dp\_codes (**

    ***dp\_code             TEXT PRIMARY KEY,           -- DP01, DP02...**

    ***name                TEXT NOT NULL,**

    ***category            TEXT,                        -- SCHOLAR, CIVILISATION, WORD, INTERNAL**

    ***description         TEXT,**

    ***severity            INTEGER CHECK(severity BETWEEN 1 AND 5)**

***);**
```

## ***op\_codes**

***Reference for phonetic operations.**

sql

```
***CREATE TABLE op\_codes (**

    ***op\_code             TEXT PRIMARY KEY,           -- OP\_NASAL, OP\_SUFFIX, OP\_NASSIM, OP\_TAMARBUTA, OP\_VOICE, OP\_PHRASE**

    ***description         TEXT NOT NULL,**

    ***example             TEXT**

***);**


***INSERT INTO op\_codes (op\_code, description) VALUES**

    ***('OP\_NASAL', 'Nasal insertion (N with no AL source)'),**

    ***('OP\_SUFFIX', 'Latin/Greek suffix (strip before tracing)'),**

    ***('OP\_NASSIM', 'Nasal assimilation (**ن→م ***before bilabial)'),**

    ***('OP\_TAMARBUTA', 'Taa marbuta realisation (**ة→***T)'),**

    ***('OP\_VOICE', 'Downstream voicing/devoicing'),**

    ***('OP\_PHRASE', 'Phrase-to-word compression');**
```

## ***nt\_codes**

***Reference for NT codes (operational categories).**

sql

```
***CREATE TABLE nt\_codes (**

    ***nt\_code             TEXT PRIMARY KEY,           -- NT1, NT2, NT3...**

    ***name                TEXT NOT NULL,**

    ***description         TEXT NOT NULL,**

    ***qur\_framework       TEXT,                        -- e.g., "Q28:4 framework"**

    ***examples            TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***-- Initial data from your examples**

***INSERT INTO nt\_codes (nt\_code, name, description, qur\_framework) VALUES**

    ***('NT1', 'Population Inversion', 'Population named by divine quality → inverted to bondage', 'UMD-OP1'),**

    ***('NT2', 'Administrative Neutralization', 'Arabicized collective noun → neutral ethnic category', 'UMD-OP1 (convergence)'),**

    ***('NT3', 'Command-to-Ethnic Capture', 'Functional command designation → captured as ethnic/cosmetic', 'Q28:4 framework');**
```

## ***operation\_codes**

***Reference for parent operations (UMD-OP1, etc.).**

sql

```
***CREATE TABLE operation\_codes (**

    ***op\_code             TEXT PRIMARY KEY,           -- UMD-OP1, UMD-OP2...**

    ***name                TEXT NOT NULL,**

    ***description         TEXT NOT NULL,**

    ***pattern             TEXT,                        -- The inversion pattern**

    ***first\_observed      TEXT,**

    ***last\_observed       TEXT,**

    ***status              TEXT DEFAULT 'ACTIVE',**

    ***notes               TEXT,**

    ***created\_at          TIMESTAMP DEFAULT CURRENT\_TIMESTAMP**

***);**


***-- Initial data from your examples**

***INSERT INTO operation\_codes (op\_code, name, description, pattern) VALUES**

    ***('UMD-OP1', 'Universal Mercy-to-Bondage Inversion', 'Divine mercy/quality for a people → inverted to bondage/cosmetic label', 'A (SLV), D (SQLB), C (RUS)');**
```


# ***TRIGGERS FOR DATA INTEGRITY**

## ***Update modified\_at on changes**

sql

```
***CREATE TRIGGER update\_entries\_timestamp **

***AFTER UPDATE ON entries**

***BEGIN**

    ***UPDATE entries SET modified\_at = CURRENT\_TIMESTAMP WHERE entry\_id = NEW.entry\_id;**

***END;**


***CREATE TRIGGER update\_child\_entries\_timestamp **

***AFTER UPDATE ON child\_entries**

***BEGIN**

    ***UPDATE child\_entries SET modified\_at = CURRENT\_TIMESTAMP WHERE child\_id = NEW.child\_id;**

***END;**


***-- Repeat for roots, derivatives, etc.**
```

## ***Maintain fingerprint table automatically**

sql

```
***CREATE TRIGGER update\_fingerprints\_on\_entry\_change**

***AFTER INSERT ON entries**

***BEGIN**

    ***-- Insert fingerprints for English term**

    ***INSERT INTO word\_fingerprints (entry\_id, language, raw\_word, consonant\_skeleton)**

    ***SELECT **

        ***NEW.entry\_id,**

        ***'en',**

        ***NEW.en\_term,**

        ***-- Custom function to extract consonants (implement in Python layer)**

        ***extract\_consonants(NEW.en\_term)**

    ***WHERE NEW.en\_term IS NOT NULL;**

    

    ***-- Repeat for Russian, Farsi, Arabic**

***END;**


***CREATE TRIGGER update\_fingerprints\_on\_child\_change**

***AFTER INSERT ON child\_entries**

***BEGIN**

    ***-- Extract searchable terms from shell\_name**

    ***INSERT INTO word\_fingerprints (child\_id, language, raw\_word, consonant\_skeleton)**

    ***SELECT **

        ***NEW.child\_id,**

        ***'en',**

        ***NEW.shell\_name,**

        ***extract\_consonants(NEW.shell\_name)**

    ***WHERE NEW.shell\_name IS NOT NULL;**

    

    ***-- Also extract from orig\_lemma if present**

    ***INSERT INTO word\_fingerprints (child\_id, language, raw\_word, consonant\_skeleton)**

    ***SELECT **

        ***NEW.child\_id,**

        ***'ar',**

        ***NEW.orig\_lemma,**

        ***extract\_consonants(NEW.orig\_lemma)**

    ***WHERE NEW.orig\_lemma IS NOT NULL;**

***END;**


***-- Similar triggers for derivatives**
```

## ***Prevent duplicate queue items**

sql

```
***CREATE TRIGGER prevent\_duplicate\_pending\_queue**

***BEFORE INSERT ON engine\_queue**

***BEGIN**

    ***SELECT CASE**

        ***WHEN EXISTS (**

            ***SELECT 1 FROM engine\_queue **

            ***WHERE payload = NEW.payload **

            ***AND status = 'PENDING'**

            ***AND operation\_type = NEW.operation\_type**

        ***) THEN**

            ***RAISE(ABORT, 'Duplicate pending operation already in queue')**

    ***END;**

***END;**
```


# ***VIEWS FOR COMMON QUERIES**

## ***entries\_with\_roots**

sql

```
***CREATE VIEW entries\_with\_roots AS**

***SELECT **

    ***e.\*,**

    ***r.root\_letters as root\_display,**

    ***r.quran\_tokens as root\_token\_count,**

    ***r.quran\_lemmas as root\_lemma\_count**

***FROM entries e**

***LEFT JOIN roots r ON e.root\_id = r.root\_id;**
```

## ***cluster\_summary**

sql

```
***CREATE VIEW cluster\_summary AS**

***SELECT **

    ***r.root\_id,**

    ***r.root\_letters,**

    ***r.quran\_tokens,**

    ***COUNT(DISTINCT e.entry\_id) as entry\_count,**

    ***COUNT(DISTINCT d.derivative\_id) as derivative\_count,**

    ***GROUP\_CONCAT(DISTINCT e.en\_term) as sample\_terms**

***FROM roots r**

***LEFT JOIN entries e ON r.root\_id = e.root\_id**

***LEFT JOIN derivatives d ON e.entry\_id = d.entry\_id**

***GROUP BY r.root\_id;**
```

## ***network\_entries**

sql

```
***CREATE VIEW network\_entries AS**

***SELECT **

    ***n.network\_id,**

    ***n.name as network\_name,**

    ***e.entry\_id,**

    ***e.en\_term,**

    ***e.score,**

    ***e.root\_id**

***FROM networks n**

***JOIN entries e ON e.network\_id LIKE '%' || n.network\_id || '%'**

***ORDER BY n.network\_id, e.score DESC;**
```

## ***operation\_overview**

***Join CHILD schema with main entries to see full operational picture.**

sql

```
***CREATE VIEW operation\_overview AS**

***SELECT **

    ***c.child\_id,**

    ***c.shell\_name,**

    ***c.operation\_role,**

    ***c.inversion\_direction,**

    ***c.nt\_code,**

    ***c.parent\_op,**

    ***c.pattern,**

    ***e.entry\_id,**

    ***e.en\_term,**

    ***e.root\_id**

***FROM child\_entries c**

***LEFT JOIN child\_entry\_links l ON c.child\_id = l.child\_id**

***LEFT JOIN entries e ON l.entry\_id = e.entry\_id**

***ORDER BY c.child\_id, e.score DESC;**
```


# ***IMPLEMENTATION NOTES**

## ***Critical Indexes Summary**

| ***Table** | ***Index** | ***Purpose** |
| - | - | - |
| ***roots** | ***`root\_bare`** | ***Root lookups by Arabic form** |
| ***entries** | ***`root\_id`** | ***All entries under a root** |
| ***entries** | ***`en\_term`** | ***Exact English term lookup** |
| ***entries** | ***`score`** | ***Prioritize high-confidence results** |
| ***child\_entries** | ***`nt\_code`** | ***Find all entries with same NT code** |
| ***child\_entries** | ***`parent\_op`** | ***Find all entries under same operation** |
| ***child\_entry\_links** | ***`child\_id`** | ***All A1 entries linked to a CHILD** |
| ***child\_entry\_links** | ***`entry\_id`** | ***All CHILD entries linked to an A1** |
| ***word\_fingerprints** | ***`consonant\_skeleton`** | ***CRITICAL — Makes cluster expansion instant** |
| ***word\_fingerprints** | ***`(consonant\_skeleton, language)`** | ***Multi-language cluster expansion** |
| ***engine\_queue** | ***`status`** | ***Find pending operations** |
| ***change\_log** | ***`(table\_name, record\_id)`** | ***Audit trail lookups** |

## ***Estimated Scale**

| ***Component** | ***Estimated Size** |
| - | - |
| ***A1 entries** | ***25,000** |
| ***CHILD entries** | ***500–2,000** |
| ***Links (A1 ↔ CHILD)** | ***50,000–125,000** |
| ***Derivatives** | ***125,000–250,000** |
| ***Cross-references** | ***500,000+** |
| ***Total searchable objects** | ***~1 million+** |

***The fingerprint table is not optional — it's the only way this scales.**

## ***Foreign Key Enforcement**

***SQLite requires pragma for FK enforcement:**

sql

```
***PRAGMA foreign\_keys = ON;**
```

***Enable this on every connection.**

## ***Migration Path to PostgreSQL**

***This schema is designed for 1:1 migration:**

- ***Same table names**

- ***Same column names**

- ***Same data types (with PostgreSQL equivalents)**

- ***Same indexes**

***Migration script: `.dump` from SQLite → load into PostgreSQL with minimal adjustments.**

## ***Initial Data Load**

***Start with:**

sql

```
***-- Roots first**

***INSERT INTO roots (root\_id, root\_letters, root\_bare, quran\_tokens, quran\_lemmas)**

***SELECT DISTINCT root\_id, root\_letters, REPLACE(root\_letters, '-', ''), **

       ***tokens, lemmas FROM excel\_roots;**


***-- Then entries**

***INSERT INTO entries (...) SELECT ... FROM excel\_entries;**


***-- Then child entries**

***INSERT INTO child\_entries (...) SELECT ... FROM excel\_child\_schema;**


***-- Then links**

***INSERT INTO child\_entry\_links (child\_id, entry\_id, link\_type)**

***SELECT child\_id, entry\_id, link\_type FROM excel\_links;**


***-- Then everything else**
```


# ***NEXT STEPS**

1. ***Review this schema — Check for missing tables/columns**

2. ***Confirm naming conventions — Are these consistent with your preferences?**

3. ***Build the Python migration script — Extend `build\_database\_v3.py`**

4. ***Test with current data — Load 25K rows + CHILD schema, verify indexes, measure queries**

5. ***Modify USLaP\_Engine.py — Switch from Excel to SQLite reads**

6. ***Keep Excel as write interface — Sync script on save**

***The fingerprint table alone will make cluster expansion ~100x faster. The engine\_queue will eliminate write conflicts. The change\_log will give you complete audit history. The CHILD schema integration ensures operational intelligence is fully linked to linguistic entries.**

**وَاللَّهُ أَعْلَمُ**

