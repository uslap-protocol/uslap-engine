-- USLaP SQLite Database Schema - Complete Implementation
-- بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- ============================================================================
-- REFERENCE TABLES (created first due to dependencies)
-- ============================================================================

-- languages: Supported languages
CREATE TABLE languages (
    lang_code           TEXT PRIMARY KEY,           -- 'en', 'ru', 'fa', 'ar', 'tr', 'kk'
    lang_name           TEXT NOT NULL,
    script_type         TEXT,                       -- Latin, Cyrillic, Arabic
    direction           TEXT DEFAULT 'LTR',         -- RTL for Arabic/Farsi
    is_supported        BOOLEAN DEFAULT TRUE,
    notes               TEXT
);

-- Insert initial language data
INSERT INTO languages (lang_code, lang_name, script_type, direction) VALUES
    ('en', 'English', 'Latin', 'LTR'),
    ('ru', 'Russian', 'Cyrillic', 'LTR'),
    ('fa', 'Persian/Farsi', 'Arabic', 'RTL'),
    ('ar', 'Allah''s Arabic', 'Arabic', 'RTL'),
    ('tr', 'Turkish', 'Latin', 'LTR'),
    ('kk', 'Kazakh', 'Cyrillic', 'LTR');

-- decay_levels: F4 decay gradient levels
CREATE TABLE decay_levels (
    level_code          TEXT PRIMARY KEY,           -- NEAR, MINIMAL, MEDIUM, HIGH, VERY_HIGH, MAXIMUM, DESTRUCTION
    level_name          TEXT NOT NULL,
    criteria            TEXT,
    measurable_test     TEXT,
    example_ds          TEXT,
    order_index         INTEGER                      -- For sorting
);

INSERT INTO decay_levels (level_code, level_name, order_index) VALUES
    ('NEAR', 'NEAR', 1),
    ('MINIMAL', 'MINIMAL', 2),
    ('MEDIUM', 'MEDIUM', 3),
    ('HIGH', 'HIGH', 4),
    ('VERY_HIGH', 'VERY HIGH', 5),
    ('MAXIMUM', 'MAXIMUM', 6),
    ('DESTRUCTION', 'DESTRUCTION', 7);

-- script_corridors: Downstream script corridors (DS01-DS14)
CREATE TABLE script_corridors (
    ds_code             TEXT PRIMARY KEY,           -- DS01, DS02...
    script_name         TEXT NOT NULL,
    source              TEXT,                       -- ORIG1, ORIG2, or BOTH
    decay_level         TEXT REFERENCES decay_levels(level_code),
    attested_from       TEXT,                       -- Date range
    attested_to         TEXT,
    description         TEXT,
    dp_codes            TEXT,                       -- Detection patterns active
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- roots: The foundation of the entire lattice
CREATE TABLE roots (
    root_id             TEXT PRIMARY KEY,           -- R001, R002, R003...
    root_letters        TEXT NOT NULL,              -- ق-ر-ن (with hyphens for display)
    root_bare           TEXT NOT NULL,              -- قرن (without hyphens, for search)
    root_type           TEXT,                       -- TRILITERAL, QUADRILITERAL, etc.
    quran_tokens        INTEGER DEFAULT 0,          -- Total Qur'anic occurrences
    quran_lemmas        INTEGER DEFAULT 0,          -- Distinct derived forms in Qur'an
    bitig_attested      BOOLEAN DEFAULT FALSE,      -- Present in Kashgari/Orkhon?
    bitig_source        TEXT,                       -- Kashgari page/line if attested
    primary_meaning     TEXT,                       -- Core semantic field
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by         TEXT DEFAULT 'user',        -- 'user' or 'engine'
    version             INTEGER DEFAULT 1
);

CREATE INDEX idx_roots_bare ON roots(root_bare);
CREATE INDEX idx_roots_type ON roots(root_type);
CREATE INDEX idx_roots_quran ON roots(quran_tokens DESC);

-- session_index: Track every engine run (must be created before engine_queue)
CREATE TABLE session_index (
    session_id          TEXT PRIMARY KEY,           -- UUID
    start_time          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time            TIMESTAMP,
    status              TEXT DEFAULT 'RUNNING' CHECK(
        status IN ('RUNNING', 'COMPLETED', 'FAILED', 'INTERRUPTED')
    ),
    
    -- What was done
    entries_processed   INTEGER DEFAULT 0,
    queries_executed    INTEGER DEFAULT 0,
    clusters_expanded   INTEGER DEFAULT 0,
    queue_items_added   INTEGER DEFAULT 0,
    
    -- Performance metrics
    execution_time_ms   INTEGER,
    memory_peak_mb      INTEGER,
    
    -- Error tracking
    error_log           TEXT,
    
    -- Which Excel file version
    excel_version       TEXT,
    
    -- User who initiated (if any)
    initiated_by        TEXT DEFAULT 'engine'
);

CREATE INDEX idx_session_status ON session_index(status);
CREATE INDEX idx_session_time ON session_index(start_time);

-- entries: The main A1_ENTRIES table
CREATE TABLE entries (
    entry_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    score               INTEGER CHECK(score BETWEEN 1 AND 10),
    
    -- Core term fields (multi-language support)
    en_term             TEXT,                       -- English term
    ru_term             TEXT,                       -- Russian term
    fa_term             TEXT,                       -- Persian/Farsi term
    ar_word             TEXT,                       -- Arabic source word
    
    -- Root linkage
    root_id             TEXT REFERENCES roots(root_id),
    root_letters        TEXT,                       -- Denormalized for speed
    
    -- Qur'anic data
    qur_meaning         TEXT,                       -- Qur'anic meaning (Arabic/translit/translation)
    qur_refs            TEXT,                       -- Comma-separated verse references
    
    -- Pattern classification
    pattern             TEXT CHECK(pattern IN ('A', 'B', 'C', 'D', 'A+B', 'A+C', 'A+D')),
    inversion_type      TEXT,                       -- CONFESSIONAL, DIRECT, HIDDEN, WEAPONISED, etc.
    
    -- Network linkages
    network_id          TEXT,                       -- N01, N02... (can be comma-separated)
    allah_name_id       TEXT,                       -- A01, A02... (can be comma-separated)
    
    -- Phonetic chain
    phonetic_chain      TEXT,                       -- e.g., "أ→(S07), م→m(S17), ر→r(S15)"
    source_form         TEXT,                       -- Original source word
    
    -- Downstream tracking
    ds_corridor         TEXT,                       -- DS04, DS05, DS06...
    decay_level         TEXT,                       -- NEAR, MEDIUM, FAR, MAXIMUM
    
    -- Detection patterns
    dp_codes            TEXT,                       -- Comma-separated: 'DP08,DP13'
    ops_applied         TEXT,                       -- Comma-separated: 'OP_SUFFIX,OP_NASAL'
    
    -- Foundation references
    foundation_refs     TEXT,                       -- Links to F-tabs evidence
    
    -- Metadata
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by         TEXT DEFAULT 'user',
    version             INTEGER DEFAULT 1,
    
    -- Full-text search virtual columns (will be populated by triggers)
    search_text         TEXT GENERATED ALWAYS AS (
        COALESCE(en_term, '') || ' ' || 
        COALESCE(ru_term, '') || ' ' || 
        COALESCE(fa_term, '') || ' ' || 
        COALESCE(ar_word, '')
    ) VIRTUAL
);

-- Critical indexes for entries
CREATE INDEX idx_entries_root ON entries(root_id);
CREATE INDEX idx_entries_en ON entries(en_term);
CREATE INDEX idx_entries_score ON entries(score DESC);
CREATE INDEX idx_entries_ds ON entries(ds_corridor);
CREATE INDEX idx_entries_network ON entries(network_id);
CREATE INDEX idx_entries_allah ON entries(allah_name_id);

-- Full-text search virtual table
CREATE VIRTUAL TABLE entries_fts USING fts5(
    entry_id UNINDEXED,
    en_term,
    ru_term,
    fa_term,
    ar_word,
    content=entries
);

-- derivatives: The A4_DERIVATIVES table
CREATE TABLE derivatives (
    derivative_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id            INTEGER NOT NULL REFERENCES entries(entry_id) ON DELETE CASCADE,
    derivative_term     TEXT NOT NULL,              -- The derived word
    language            TEXT NOT NULL,              -- 'en', 'ru', 'fa', 'de', etc.
    link_type           TEXT,                       -- DIRECT, COMPOUND, PHONETIC, SAME_ROOT, etc.
    is_primary          BOOLEAN DEFAULT FALSE,      -- Is this the main entry term?
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_derivatives_entry ON derivatives(entry_id);
CREATE INDEX idx_derivatives_term ON derivatives(derivative_term);
CREATE INDEX idx_derivatives_lang ON derivatives(language);

-- cross_refs: The A5_CROSS_REFS table
CREATE TABLE cross_refs (
    xref_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry_id       INTEGER NOT NULL REFERENCES entries(entry_id) ON DELETE CASCADE,
    to_entry_id         INTEGER NOT NULL REFERENCES entries(entry_id) ON DELETE CASCADE,
    link_type           TEXT NOT NULL,              -- SAME_ROOT, SAME_VERSE, ANTONYM, NETWORK, etc.
    description         TEXT,
    layer_ref           TEXT,                       -- Which layer in the schema
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicates
    UNIQUE(from_entry_id, to_entry_id, link_type)
);

CREATE INDEX idx_cross_refs_from ON cross_refs(from_entry_id);
CREATE INDEX idx_cross_refs_to ON cross_refs(to_entry_id);
CREATE INDEX idx_cross_refs_type ON cross_refs(link_type);

-- quran_refs: The A3_QURAN_REFS table
CREATE TABLE quran_refs (
    ref_id              TEXT PRIMARY KEY,           -- QR01, QR02...
    surah               INTEGER NOT NULL,
    ayah                INTEGER NOT NULL,
    arabic_text         TEXT NOT NULL,              -- With diacritics
    transliteration     TEXT,
    translation         TEXT,
    relevance           TEXT,
    entry_ids           TEXT,                       -- Comma-separated entry IDs
    network_id          TEXT REFERENCES networks(network_id),
    layer_ref           TEXT,
    qv_id               TEXT REFERENCES qur_verification(qv_id),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(surah, ayah)
);

CREATE INDEX idx_quran_refs_surah ON quran_refs(surah, ayah);
CREATE INDEX idx_quran_refs_network ON quran_refs(network_id);

-- country_names: The A6_COUNTRY_NAMES table
CREATE TABLE country_names (
    country_id          TEXT PRIMARY KEY,           -- CN01, CN02...
    country_name        TEXT NOT NULL,
    al_root             TEXT REFERENCES roots(root_id),
    root_id             TEXT,
    al_word             TEXT,
    qur_meaning         TEXT,
    phonetic_chain      TEXT,
    naming_basis        TEXT,
    entry_ids           TEXT,                       -- Comma-separated
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_country_names_root ON country_names(root_id);

-- names_of_allah: The A2_NAMES_OF_ALLH table
CREATE TABLE names_of_allah (
    allah_id            TEXT PRIMARY KEY,           -- A01, A02...
    arabic_name         TEXT NOT NULL,
    transliteration     TEXT NOT NULL,
    meaning             TEXT NOT NULL,
    qur_ref             TEXT,
    entry_ids           TEXT,
    root_id             TEXT REFERENCES roots(root_id),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_allah_root ON names_of_allah(root_id);

-- ============================================================================
-- MECHANISM TABLES
-- ============================================================================

-- phonetic_shifts: The M1_PHONETIC_SHIFTS table
CREATE TABLE phonetic_shifts (
    shift_id            TEXT PRIMARY KEY,           -- S01, S02...
    ar_letter           TEXT NOT NULL,              -- ق
    ar_name             TEXT NOT NULL,              -- qāf
    en_outputs          TEXT NOT NULL,              -- c,k,q,g
    ru_outputs          TEXT,                       -- к,г
    direction           TEXT DEFAULT 'AR→EN',
    description         TEXT,
    examples            TEXT,
    entry_ids           TEXT,
    foundation_ref      TEXT,
    decay_pattern       TEXT,                       -- F4: emphatic→plain
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- detection_patterns: The M2_DETECTION_PATTERNS table
CREATE TABLE detection_patterns (
    pattern_id          TEXT PRIMARY KEY,           -- DP01, DP02...
    name                TEXT NOT NULL,
    level               TEXT CHECK(level IN ('SCHOLAR', 'CIVILISATION', 'WORD', 'INTERNAL')),
    description         TEXT NOT NULL,
    triggers            TEXT,                       -- Keywords that activate this pattern
    qur_ref             TEXT,
    example             TEXT,
    entry_ids           TEXT,
    foundation_ref      TEXT,
    severity            INTEGER CHECK(severity BETWEEN 1 AND 5),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- networks: The M4_NETWORKS table
CREATE TABLE networks (
    network_id          TEXT PRIMARY KEY,           -- N01, N02...
    name                TEXT NOT NULL,
    title               TEXT,
    link_verse          TEXT,                       -- Qur'an verse that links them
    description         TEXT NOT NULL,
    mechanism           TEXT,
    entry_ids           TEXT,
    status              TEXT DEFAULT 'CONFIRMED',
    foundation_ref      TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- scholars: The M3_SCHOLARS table
CREATE TABLE scholars (
    scholar_id          TEXT PRIMARY KEY,           -- SC01, SC02...
    verified_name       TEXT NOT NULL,              -- الخوارزمي
    birth_place         TEXT NOT NULL,
    identity            TEXT NOT NULL,              -- Khwarezmian TURKIC, etc.
    role                TEXT,
    achievement         TEXT,
    lies_applied        TEXT,                       -- DP02,DP03,DP10 (comma-separated)
    entry_ids           TEXT,
    death_fate          TEXT,
    biography_status    TEXT,                       -- MINIMAL, SUSPICIOUS, DETAILED
    status              TEXT DEFAULT 'VERIFIED',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- qur_verification: The M5_QUR_VERIFICATION table
CREATE TABLE qur_verification (
    qv_id               TEXT PRIMARY KEY,           -- QV01, QV02, QV03
    name                TEXT NOT NULL,
    mechanism           TEXT NOT NULL,
    description         TEXT NOT NULL,
    markers             TEXT,                       -- قَالُوا, زَعَمَ, etc.
    qur_refs            TEXT,
    contrast_refs       TEXT,
    foundation_ref      TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Foreign key constraints are defined inline in table definitions (SQLite doesn't support ALTER TABLE ADD CONSTRAINT)

-- ============================================================================
-- REFERENCE CODE TABLES (for CHILD schema and intelligence)
-- ============================================================================

-- nt_codes: Reference for NT codes (operational categories)
CREATE TABLE nt_codes (
    nt_code             TEXT PRIMARY KEY,           -- NT1, NT2, NT3...
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    qur_framework       TEXT,                       -- e.g., "Q28:4 framework"
    examples            TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial NT codes
INSERT INTO nt_codes (nt_code, name, description, qur_framework) VALUES
    ('NT1', 'Population Inversion', 'Population named by divine quality → inverted to bondage', 'UMD-OP1'),
    ('NT2', 'Administrative Neutralization', 'Arabicized collective noun → neutral ethnic category', 'UMD-OP1 (convergence)'),
    ('NT3', 'Command-to-Ethnic Capture', 'Functional command designation → captured as ethnic/cosmetic', 'Q28:4 framework');

-- operation_codes: Reference for parent operations (UMD-OP1, etc.)
CREATE TABLE operation_codes (
    op_code             TEXT PRIMARY KEY,           -- UMD-OP1, UMD-OP2...
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    pattern             TEXT,                       -- The inversion pattern
    first_observed      TEXT,
    last_observed       TEXT,
    status              TEXT DEFAULT 'ACTIVE',
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial operation codes
INSERT INTO operation_codes (op_code, name, description, pattern) VALUES
    ('UMD-OP1', 'Universal Mercy-to-Bondage Inversion', 'Divine mercy/quality for a people → inverted to bondage/cosmetic label', 'A (SLV), D (SQLB), C (RUS)');

-- dp_codes: Reference for detection patterns
CREATE TABLE dp_codes (
    dp_code             TEXT PRIMARY KEY,           -- DP01, DP02...
    name                TEXT NOT NULL,
    category            TEXT,                       -- SCHOLAR, CIVILISATION, WORD, INTERNAL
    description         TEXT,
    severity            INTEGER CHECK(severity BETWEEN 1 AND 5)
);

-- op_codes: Reference for phonetic operations
CREATE TABLE op_codes (
    op_code             TEXT PRIMARY KEY,           -- OP_NASAL, OP_SUFFIX, OP_NASSIM, OP_TAMARBUTA, OP_VOICE, OP_PHRASE
    description         TEXT NOT NULL,
    example             TEXT
);

INSERT INTO op_codes (op_code, description) VALUES
    ('OP_NASAL', 'Nasal insertion (N with no AL source)'),
    ('OP_SUFFIX', 'Latin/Greek suffix (strip before tracing)'),
    ('OP_NASSIM', 'Nasal assimilation (ن→م before bilabial)'),
    ('OP_TAMARBUTA', 'Taa marbuta realisation (ة→T)'),
    ('OP_VOICE', 'Downstream voicing/devoicing'),
    ('OP_PHRASE', 'Phrase-to-word compression');

-- ============================================================================
-- CHILD SCHEMA TABLES
-- ============================================================================

-- child_entries: The operational intelligence layer
CREATE TABLE child_entries (
    child_id            TEXT PRIMARY KEY,           -- SLV, SQLB, RUS...
    shell_name          TEXT NOT NULL,              -- 'Slav / slave'
    shell_language      TEXT,                       -- 'Proto-Slavic / Latin', 'Arabic', etc.
    orig_class          TEXT,                       -- 'ORIG1', 'ORIG2', 'ORIG1+ORIG2', 'ORIG1 (primary) ORIG2 (convergence)'
    orig_root           TEXT,                       -- 'س-ل-و', 'sariq / س-ل-و (convergence: ق-ل-ب)'
    orig_lemma          TEXT,                       -- 'سَلْوَى / Salwā', 'sarıg / سَارِق-اللَّوْن'
    orig_meaning        TEXT,                       -- Full meaning with context
    operation_role      TEXT,                       -- 'POPULATION', 'WEAPON-FACTION', 'POPULATION — identified and documented in Islamic administrative record', etc.
    shell_meaning       TEXT,                       -- Current/neutralized meaning
    inversion_direction TEXT,                       -- 'INVERTED (divine mercy → bondage)', 'NEUTRAL (descriptive stripped)', 'CAPTURED (operational → ethnic/cosmetic)'
    phonetic_chain      TEXT,                       -- 'سَلْوَى → *salw- → *slav- (و→V, S-class wāw shift)'
    qur_anchors         TEXT,                       -- 'Q2:57 · Q7:160 · Q20:80'
    dp_codes            TEXT,                       -- 'DP08 · DP07 · DP11 · DP15'
    nt_code             TEXT REFERENCES nt_codes(nt_code),  -- NT1, NT2, NT3...
    pattern             TEXT CHECK(pattern IN ('A', 'B', 'C', 'D')),
    parent_op           TEXT REFERENCES operation_codes(op_code),  -- 'UMD-OP1'
    gate_status         TEXT,                       -- 'Q:PASS U:PASS F:PASS CONFIRMED ✓'
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by         TEXT DEFAULT 'user',
    version             INTEGER DEFAULT 1
);

CREATE INDEX idx_child_nt ON child_entries(nt_code);
CREATE INDEX idx_child_op ON child_entries(parent_op);
CREATE INDEX idx_child_pattern ON child_entries(pattern);

-- child_entry_links: Links between CHILD entries and main A1 entries
CREATE TABLE child_entry_links (
    link_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id            TEXT NOT NULL REFERENCES child_entries(child_id) ON DELETE CASCADE,
    entry_id            INTEGER NOT NULL REFERENCES entries(entry_id) ON DELETE CASCADE,
    link_type           TEXT,                       -- 'DIRECT', 'DERIVED', 'OPERATION', 'CONVERGENCE'
    confidence          INTEGER DEFAULT 10 CHECK(confidence BETWEEN 1 AND 10),
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicates
    UNIQUE(child_id, entry_id)
);

CREATE INDEX idx_child_links_child ON child_entry_links(child_id);
CREATE INDEX idx_child_links_entry ON child_entry_links(entry_id);
CREATE INDEX idx_child_links_type ON child_entry_links(link_type);

-- ============================================================================
-- INTELLIGENCE TABLES
-- ============================================================================

-- operators: The core operator tracking
CREATE TABLE operators (
    operator_id         TEXT PRIMARY KEY,           -- OP01, OP02...
    primary_name        TEXT NOT NULL,              -- Caesar, Rothschild, etc.
    operator_class      TEXT,                       -- PRIESTLY, FINANCIAL, MILITARY, SCRIBAL
    origin_period       TEXT,                       -- "~50 BCE"
    active_period       TEXT,                       -- "58 BCE - 44 BCE"
    description         TEXT,
    modus_operandi      TEXT,
    current_status      TEXT,                       -- ACTIVE, INACTIVE, TRANSITIONED
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operators_class ON operators(operator_class);

-- host_civilizations: The host societies that were infiltrated
CREATE TABLE host_civilizations (
    host_id             TEXT PRIMARY KEY,           -- H01, H02... (مِصْر, بَابِل, etc.)
    host_name           TEXT NOT NULL,
    host_type           TEXT,                       -- TERRITORIAL, COMMERCIAL, INTELLECTUAL
    geographic_center   TEXT,
    active_period       TEXT,
    description         TEXT,
    operator_ids        TEXT,                       -- Which operators worked here
    entry_ids           TEXT,                       -- Which entries corrupted here
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- operation_cycles: The 8-step كُلَّمَا cycle tracking
CREATE TABLE operation_cycles (
    cycle_id            TEXT PRIMARY KEY,           -- C01, C02...
    host_id             TEXT REFERENCES host_civilizations(host_id),
    cycle_number        INTEGER,                    -- 1,2,3... in the كُلَّمَا chain
    start_date          TEXT,
    end_date            TEXT,
    
    -- The 8 steps
    step1_recon         TEXT,                       -- RECONNAISSANCE
    step2_entrance      TEXT,                       -- ENTRANCE
    step3_infiltrate    TEXT,                       -- INFILTRATE
    step4_position      TEXT,                       -- POSITION
    step5_fund_arm      TEXT,                       -- FUND & ARM
    step6_extract       TEXT,                       -- EXTRACT
    step7_erase_cover   TEXT,                       -- ERASE + COVER
    step8_disperse      TEXT,                       -- DISPERSE & REPEAT
    
    operator_ids        TEXT,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cycles_host ON operation_cycles(host_id);

-- events: Individual historical events with operator attribution
CREATE TABLE events (
    event_id            TEXT PRIMARY KEY,           -- E001, E002...
    event_name          TEXT NOT NULL,
    event_date          TEXT,
    event_type          TEXT,                       -- SCRIPT_CHANGE, TRANSLATION, INVASION, etc.
    description         TEXT,
    operator_ids        TEXT,                       -- Who executed it
    host_id             TEXT REFERENCES host_civilizations(host_id),
    cycle_id            TEXT REFERENCES operation_cycles(cycle_id),
    entry_ids_affected  TEXT,                       -- Which entries corrupted
    dp_codes            TEXT,                       -- Which patterns active
    evidence            TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_type ON events(event_type);

-- intel_reports: Primary source intelligence documents
CREATE TABLE intel_reports (
    report_id           TEXT PRIMARY KEY,           -- IR001, IR002...
    source_name         TEXT NOT NULL,              -- Ibn Khordadbeh, etc.
    source_type         TEXT,                       -- BARID_INTEL, SELF_INCRIMINATING, etc.
    work_title          TEXT,
    date                TEXT,
    content_summary     TEXT,
    key_evidence        TEXT,
    operator_ids        TEXT,
    event_ids           TEXT,
    entry_ids           TEXT,
    url_reference       TEXT,                       -- For digital sources
    manuscript_ref      TEXT,                       -- For physical manuscripts
    status              TEXT DEFAULT 'VERIFIED',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- operator_aliases: All the names an operator used across hosts
CREATE TABLE operator_aliases (
    alias_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id         TEXT REFERENCES operators(operator_id) ON DELETE CASCADE,
    alias_name          TEXT NOT NULL,
    host_id             TEXT REFERENCES host_civilizations(host_id),
    period_used         TEXT,
    notes               TEXT,
    
    UNIQUE(operator_id, alias_name)
);

CREATE INDEX idx_aliases_operator ON operator_aliases(operator_id);
CREATE INDEX idx_aliases_name ON operator_aliases(alias_name);

-- ============================================================================
-- SEARCH & PERFORMANCE TABLES
-- ============================================================================

-- word_fingerprints: Critical table for phonetic search (makes cluster expansion instant)
CREATE TABLE word_fingerprints (
    fingerprint_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Source record (one of these must be populated)
    entry_id            INTEGER REFERENCES entries(entry_id) ON DELETE CASCADE,
    child_id            TEXT REFERENCES child_entries(child_id) ON DELETE CASCADE,
    derivative_id       INTEGER REFERENCES derivatives(derivative_id) ON DELETE CASCADE,
    
    -- Which word this fingerprint represents
    language            TEXT NOT NULL,              -- 'en', 'ru', 'fa', 'ar'
    raw_word            TEXT NOT NULL,              -- The actual word
    
    -- The search key
    consonant_skeleton  TEXT NOT NULL,              -- 'cncr' for 'concern'
    
    -- For debugging/refinement
    normalization_applied TEXT,                     -- What we stripped
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure at least one source is specified
    CHECK (
        (entry_id IS NOT NULL) OR 
        (child_id IS NOT NULL) OR 
        (derivative_id IS NOT NULL)
    )
);

-- Critical indexes for word_fingerprints
CREATE INDEX idx_fingerprints_skeleton ON word_fingerprints(consonant_skeleton);
CREATE INDEX idx_fingerprints_entry ON word_fingerprints(entry_id);
CREATE INDEX idx_fingerprints_child ON word_fingerprints(child_id);
CREATE INDEX idx_fingerprints_lang ON word_fingerprints(language);
CREATE INDEX idx_fingerprints_lookup ON word_fingerprints(consonant_skeleton, language);

-- cluster_cache: Pre-computed cluster expansion results
CREATE TABLE cluster_cache (
    cache_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id             TEXT NOT NULL REFERENCES roots(root_id),
    expansion_type      TEXT,                       -- 'direct', 'phonetic', 'semantic'
    result_json         TEXT,                       -- JSON array of entry_ids
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hits                INTEGER DEFAULT 0,          -- Cache hit counter
    last_accessed       TIMESTAMP,
    
    -- Invalidate after root changes
    root_version        INTEGER
);

CREATE INDEX idx_cache_root ON cluster_cache(root_id);
CREATE INDEX idx_cache_type ON cluster_cache(expansion_type);

-- phonetic_mappings: Known phonetic shift patterns for rapid reversal
CREATE TABLE phonetic_mappings (
    mapping_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_phoneme      TEXT NOT NULL,              -- Original sound
    target_phoneme      TEXT NOT NULL,              -- Shifted sound
    shift_id            TEXT REFERENCES phonetic_shifts(shift_id),
    language            TEXT,                       -- 'en', 'ru', etc.
    confidence          INTEGER CHECK(confidence BETWEEN 1 AND 10),
    examples            TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mappings_source ON phonetic_mappings(source_phoneme);
CREATE INDEX idx_mappings_target ON phonetic_mappings(target_phoneme);

-- ============================================================================
-- ENGINE CONTROL TABLES
-- ============================================================================

-- engine_queue: The master queue for engine-user coordination
CREATE TABLE engine_queue (
    queue_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- What needs to be done
    operation_type      TEXT NOT NULL,              -- 'PROPOSE_ENTRY', 'UPDATE_ROOT', 'ADD_DERIVATIVE', etc.
    
    -- The data (JSON for flexibility)
    payload             TEXT NOT NULL,              -- Full data for the operation
    
    -- Status tracking
    status              TEXT DEFAULT 'PENDING' CHECK(
        status IN ('PENDING', 'APPROVED', 'REJECTED', 'CONFLICT', 'ERROR')
    ),
    
    -- Who/what created it
    source              TEXT NOT NULL,              -- 'engine' or 'user'
    session_id          TEXT REFERENCES session_index(session_id),
    
    -- Conflict resolution
    conflict_with       INTEGER REFERENCES engine_queue(queue_id),
    resolution_notes    TEXT,
    
    -- Timing
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at        TIMESTAMP,
    
    -- Version tracking
    entry_version       INTEGER,                    -- Version of entry if updating
    
    -- Index for fast pending lookups
    priority            INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10)
);

CREATE INDEX idx_queue_status ON engine_queue(status);
CREATE INDEX idx_queue_created ON engine_queue(created_at);
CREATE INDEX idx_queue_source ON engine_queue(source);
CREATE INDEX idx_queue_priority ON engine_queue(priority);

-- change_log: Complete audit trail for every change
CREATE TABLE change_log (
    log_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- What changed
    table_name          TEXT NOT NULL,
    record_id           TEXT NOT NULL,              -- entry_id, root_id, child_id, etc.
    
    -- The change
    change_type         TEXT CHECK(change_type IN ('INSERT', 'UPDATE', 'DELETE')),
    before_state        TEXT,                       -- JSON of before (for UPDATE/DELETE)
    after_state         TEXT,                       -- JSON of after (for INSERT/UPDATE)
    
    -- Who/what did it
    source              TEXT NOT NULL,              -- 'user' or 'engine'
    session_id          TEXT REFERENCES session_index(session_id),
    queue_id            INTEGER REFERENCES engine_queue(queue_id),
    
    -- When
    changed_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Why (if from engine)
    reason              TEXT
);

CREATE INDEX idx_changelog_table ON change_log(table_name, record_id);
CREATE INDEX idx_changelog_time ON change_log(changed_at);
CREATE INDEX idx_changelog_source ON change_log(source);

-- sync_status: Track Excel ↔ database synchronization
CREATE TABLE sync_status (
    sync_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- What was synced
    sync_direction      TEXT CHECK(sync_direction IN ('EXCEL_TO_DB', 'DB_TO_EXCEL')),
    
    -- Status
    status              TEXT DEFAULT 'PENDING' CHECK(
        status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')
    ),
    
    -- Counts
    records_processed   INTEGER DEFAULT 0,
    records_added       INTEGER DEFAULT 0,
    records_updated     INTEGER DEFAULT 0,
    records_conflicted  INTEGER DEFAULT 0,
    
    -- Timing
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP,
    
    -- Which session
    session_id          TEXT REFERENCES session_index(session_id),
    
    -- Error details
    error_details       TEXT
);

-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Update modified_at on changes for core tables
CREATE TRIGGER update_roots_timestamp 
AFTER UPDATE ON roots
BEGIN
    UPDATE roots SET modified_at = CURRENT_TIMESTAMP WHERE root_id = NEW.root_id;
END;

CREATE TRIGGER update_entries_timestamp 
AFTER UPDATE ON entries
BEGIN
    UPDATE entries SET modified_at = CURRENT_TIMESTAMP WHERE entry_id = NEW.entry_id;
END;

CREATE TRIGGER update_child_entries_timestamp 
AFTER UPDATE ON child_entries
BEGIN
    UPDATE child_entries SET modified_at = CURRENT_TIMESTAMP WHERE child_id = NEW.child_id;
END;

-- Maintain fingerprint table automatically when entries are inserted/updated
-- Note: extract_consonants() function must be registered as a Python UDF before these triggers fire
CREATE TRIGGER update_fingerprints_on_entry_insert
AFTER INSERT ON entries
BEGIN
    -- Insert fingerprints for English term
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'en',
        NEW.en_term,
        extract_consonants(NEW.en_term)
    WHERE NEW.en_term IS NOT NULL AND NEW.en_term != '';
    
    -- Insert fingerprints for Russian term
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'ru',
        NEW.ru_term,
        extract_consonants(NEW.ru_term)
    WHERE NEW.ru_term IS NOT NULL AND NEW.ru_term != '';
    
    -- Insert fingerprints for Persian term
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'fa',
        NEW.fa_term,
        extract_consonants(NEW.fa_term)
    WHERE NEW.fa_term IS NOT NULL AND NEW.fa_term != '';
    
    -- Insert fingerprints for Arabic word
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'ar',
        NEW.ar_word,
        extract_consonants(NEW.ar_word)
    WHERE NEW.ar_word IS NOT NULL AND NEW.ar_word != '';
END;

CREATE TRIGGER update_fingerprints_on_entry_update
AFTER UPDATE ON entries
BEGIN
    -- Delete existing fingerprints for this entry
    DELETE FROM word_fingerprints WHERE entry_id = NEW.entry_id;
    
    -- Reinsert updated fingerprints (same logic as insert trigger)
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'en',
        NEW.en_term,
        extract_consonants(NEW.en_term)
    WHERE NEW.en_term IS NOT NULL AND NEW.en_term != '';
    
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'ru',
        NEW.ru_term,
        extract_consonants(NEW.ru_term)
    WHERE NEW.ru_term IS NOT NULL AND NEW.ru_term != '';
    
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'fa',
        NEW.fa_term,
        extract_consonants(NEW.fa_term)
    WHERE NEW.fa_term IS NOT NULL AND NEW.fa_term != '';
    
    INSERT INTO word_fingerprints (entry_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.entry_id,
        'ar',
        NEW.ar_word,
        extract_consonants(NEW.ar_word)
    WHERE NEW.ar_word IS NOT NULL AND NEW.ar_word != '';
END;

CREATE TRIGGER update_fingerprints_on_child_insert
AFTER INSERT ON child_entries
BEGIN
    -- Extract searchable terms from shell_name
    INSERT INTO word_fingerprints (child_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.child_id,
        'en',
        NEW.shell_name,
        extract_consonants(NEW.shell_name)
    WHERE NEW.shell_name IS NOT NULL AND NEW.shell_name != '';
    
    -- Also extract from orig_lemma if present
    INSERT INTO word_fingerprints (child_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.child_id,
        'ar',
        NEW.orig_lemma,
        extract_consonants(NEW.orig_lemma)
    WHERE NEW.orig_lemma IS NOT NULL AND NEW.orig_lemma != '';
END;

CREATE TRIGGER update_fingerprints_on_derivative_insert
AFTER INSERT ON derivatives
BEGIN
    INSERT INTO word_fingerprints (derivative_id, language, raw_word, consonant_skeleton)
    SELECT 
        NEW.derivative_id,
        NEW.language,
        NEW.derivative_term,
        extract_consonants(NEW.derivative_term)
    WHERE NEW.derivative_term IS NOT NULL AND NEW.derivative_term != '';
END;

-- Prevent duplicate pending queue items
CREATE TRIGGER prevent_duplicate_pending_queue
BEFORE INSERT ON engine_queue
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM engine_queue 
            WHERE payload = NEW.payload 
            AND status = 'PENDING'
            AND operation_type = NEW.operation_type
        ) THEN
            RAISE(ABORT, 'Duplicate pending operation already in queue')
    END;
END;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- entries_with_roots: Join entries with their root information
CREATE VIEW entries_with_roots AS
SELECT 
    e.*,
    r.root_letters as root_display,
    r.quran_tokens as root_token_count,
    r.quran_lemmas as root_lemma_count
FROM entries e
LEFT JOIN roots r ON e.root_id = r.root_id;

-- cluster_summary: Summary of entries per root
CREATE VIEW cluster_summary AS
SELECT 
    r.root_id,
    r.root_letters,
    r.quran_tokens,
    COUNT(DISTINCT e.entry_id) as entry_count,
    COUNT(DISTINCT d.derivative_id) as derivative_count,
    GROUP_CONCAT(DISTINCT e.en_term) as sample_terms
FROM roots r
LEFT JOIN entries e ON r.root_id = e.root_id
LEFT JOIN derivatives d ON e.entry_id = d.entry_id
GROUP BY r.root_id;

-- network_entries: Join networks with their entries
CREATE VIEW network_entries AS
SELECT 
    n.network_id,
    n.name as network_name,
    e.entry_id,
    e.en_term,
    e.score,
    e.root_id
FROM networks n
JOIN entries e ON e.network_id LIKE '%' || n.network_id || '%'
ORDER BY n.network_id, e.score DESC;

-- operation_overview: Join CHILD schema with main entries
CREATE VIEW operation_overview AS
SELECT 
    c.child_id,
    c.shell_name,
    c.operation_role,
    c.inversion_direction,
    c.nt_code,
    c.parent_op,
    c.pattern,
    e.entry_id,
    e.en_term,
    e.root_id
FROM child_entries c
LEFT JOIN child_entry_links l ON c.child_id = l.child_id
LEFT JOIN entries e ON l.entry_id = e.entry_id
ORDER BY c.child_id, e.score DESC;

-- ============================================================================
-- FINAL VERIFICATION AND CLEANUP
-- ============================================================================

-- Verify foreign key support
PRAGMA foreign_keys = ON;

-- Create a view to verify the schema
CREATE VIEW schema_verification AS
SELECT 
    'roots' as table_name, COUNT(*) as row_count FROM sqlite_master WHERE type='table' AND name='roots'
UNION ALL
SELECT 'entries', COUNT(*) FROM sqlite_master WHERE type='table' AND name='entries'
UNION ALL
SELECT 'word_fingerprints', COUNT(*) FROM sqlite_master WHERE type='table' AND name='word_fingerprints'
UNION ALL
SELECT 'engine_queue', COUNT(*) FROM sqlite_master WHERE type='table' AND name='engine_queue'
UNION ALL
SELECT 'session_index', COUNT(*) FROM sqlite_master WHERE type='table' AND name='session_index'
UNION ALL
SELECT 'child_entries', COUNT(*) FROM sqlite_master WHERE type='table' AND name='child_entries'
UNION ALL
SELECT 'child_entry_links', COUNT(*) FROM sqlite_master WHERE type='table' AND name='child_entry_links';

-- Print completion message
SELECT 'USLaP SQLite Schema created successfully. Total tables: ' || COUNT(*) as completion_message 
FROM sqlite_master WHERE type='table';