-- ============================================================
-- NAMES OF ALLAH — ROOT HUB ARCHITECTURE
-- 5 tables. Root-centric. Zero weights needed for queries.
-- ============================================================

-- 1. ROOT_HUB — one row per Name, connects everything
CREATE TABLE IF NOT EXISTS name_root_hub (
    name_id TEXT PRIMARY KEY,           -- A01, A02...
    arabic_name TEXT NOT NULL,
    root_letters TEXT NOT NULL,          -- م-ل-ك
    qrd_id INTEGER,                     -- links to quran_root_dictionary
    token_count INTEGER,
    abjad_values TEXT,                   -- 40-30-20
    abjad_total INTEGER,                -- 90
    abjad_property TEXT,                -- "descending arithmetic sequence, d=10, unique among 99"
    letter_1 TEXT,                       -- م
    letter_1_abjad INTEGER,             -- 40
    letter_1_phonetic TEXT,             -- "bilabial nasal"
    letter_1_root_function TEXT,        -- "containment — lips seal, sound held inside"
    letter_2 TEXT,
    letter_2_abjad INTEGER,
    letter_2_phonetic TEXT,
    letter_2_root_function TEXT,
    letter_3 TEXT,
    letter_3_abjad INTEGER,
    letter_3_phonetic TEXT,
    letter_3_root_function TEXT,
    letter_4 TEXT,                       -- for quadrilateral roots (ه-ي-م-ن)
    letter_4_abjad INTEGER,
    letter_4_phonetic TEXT,
    letter_4_root_function TEXT,
    phonetic_arc TEXT,                  -- "contain → channel → manifest"
    corrected_meaning TEXT NOT NULL,    -- washed translation from root
    current_meaning TEXT,               -- what DB currently says (for comparison)
    qv_ids TEXT,                        -- QV234
    downstream_en_ids TEXT,             -- 2,734,735
    downstream_ru_ids TEXT,             -- 156,173,801,802
    downstream_eu_count INTEGER,
    quf_token TEXT
);

-- 2. QURANIC_FORM_REGISTER — morphological patterns per Name root
CREATE TABLE IF NOT EXISTS name_quranic_forms (
    form_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_id TEXT NOT NULL,              -- A01
    root_letters TEXT NOT NULL,         -- م-ل-ك
    pattern_arabic TEXT,                -- فُعْل
    pattern_name TEXT,                  -- "base noun"
    form_arabic TEXT,                   -- مُلْك
    token_count INTEGER,               -- 46
    percentage REAL,                    -- 24.9
    function_description TEXT NOT NULL, -- "the operational authority itself — revocable, allocated..."
    key_ayat TEXT,                      -- Q67:1,Q3:26
    key_evidence TEXT,                  -- "بِيَدِهِ الْمُلْكُ — held in His hand, directly gripped"
    quf_token TEXT,
    FOREIGN KEY (name_id) REFERENCES name_root_hub(name_id)
);

-- 3. CORRUPTION_CHAIN — staged corruption per Name
CREATE TABLE IF NOT EXISTS name_corruption_chain (
    chain_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_id TEXT NOT NULL,
    root_letters TEXT NOT NULL,
    stage INTEGER NOT NULL,             -- 1,2,3,4,5
    stage_name TEXT NOT NULL,           -- "Pre-Quranic Lisan", "Lisan lexicography", "DS04/DS05", "Political"
    era TEXT,                           -- "pre-610 CE", "8th-10th c.", "12th-15th c.", "ongoing"
    mechanism TEXT NOT NULL,            -- what exactly was done
    what_was_lost TEXT NOT NULL,        -- what understanding was destroyed
    operator_id TEXT,                   -- links to m3_scholars or new operator entry
    dp_codes TEXT,                      -- DP08,DP12
    quf_token TEXT,
    FOREIGN KEY (name_id) REFERENCES name_root_hub(name_id)
);

-- 4. PHYSICAL_PROOF — downstream physical manifestations per root
CREATE TABLE IF NOT EXISTS name_physical_proof (
    proof_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_id TEXT NOT NULL,
    root_letters TEXT NOT NULL,
    substance TEXT NOT NULL,            -- "raw milk"
    component TEXT NOT NULL,            -- "living enzymes (lactase, lipase, phosphatase)"
    root_form_equivalent TEXT NOT NULL, -- "مَلَائِكَة — executing agents"
    component_function TEXT NOT NULL,   -- "break down, process, deliver nutrients"
    corruption_operation TEXT,          -- "pasteurisation — heating to 72°C for 15 seconds"
    corruption_result TEXT,             -- "enzymes dead — body must process alone, cannot → lactose intolerance"
    operator_name TEXT,                 -- "Louis Pasteur"
    operator_date TEXT,                 -- "1864"
    operator_network TEXT,              -- network_id if applicable
    quf_token TEXT,
    FOREIGN KEY (name_id) REFERENCES name_root_hub(name_id)
);

-- 5. DAMAGE_REGISTER — impact assessment per Name
CREATE TABLE IF NOT EXISTS name_damage_register (
    damage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_id TEXT NOT NULL,
    root_letters TEXT NOT NULL,
    domain TEXT NOT NULL,               -- "governance", "health", "economics", "identity", "perception"
    mechanism TEXT NOT NULL,            -- how the corruption enables the damage
    scale TEXT,                         -- "global", "Muslim-majority", "specific population"
    population_affected TEXT,           -- "all populations under monarchical rule"
    severity TEXT,                      -- "structural" / "surface" / "total"
    reversible TEXT,                    -- "yes — by restoring root knowledge" / "partial"
    key_evidence TEXT,                  -- specific example or proof
    quf_token TEXT,
    FOREIGN KEY (name_id) REFERENCES name_root_hub(name_id)
);

-- ============================================================
-- A01 — الْمَلِكُ — DATA
-- ============================================================

-- ROOT HUB
INSERT INTO name_root_hub (
    name_id, arabic_name, root_letters, qrd_id, token_count,
    abjad_values, abjad_total, abjad_property,
    letter_1, letter_1_abjad, letter_1_phonetic, letter_1_root_function,
    letter_2, letter_2_abjad, letter_2_phonetic, letter_2_root_function,
    letter_3, letter_3_abjad, letter_3_phonetic, letter_3_root_function,
    phonetic_arc, corrected_meaning, current_meaning, qv_ids,
    downstream_en_ids, downstream_ru_ids, downstream_eu_count
) VALUES (
    'A01', 'الْمَلِكُ', 'م-ل-ك', 1423, 185,
    '40-30-20', 90, 'descending arithmetic sequence d=10 — unique among the 99 Names. Authority descends from source through medium to manifestation.',
    'م', 40, 'bilabial nasal — lips seal completely, airflow through nasal cavity, simultaneous closure and continuation',
    'containment — the root opens with enclosure, holding, taking-within',
    'ل', 30, 'lateral approximant — tongue channels airflow without blocking, the only Arabic consonant that directs without stopping',
    'direction — channels what م enclosed, gives it movement and aim toward manifestation',
    'ك', 20, 'voiceless velar plosive — back of tongue seals against velum, pressure builds then releases into the world',
    'manifestation — completes the sequence, pressure accumulated then released into reality',
    'contain → channel → manifest',
    'The One whose nature is operational authority over all reality at every layer — unseen architecture (مَلَكُوت) through executing agents (مَلَائِكَة) to visible order (مُلْك) — active possessor of the Day of the System of Accountability, allocator and revoker of all authority',
    'The King / Owner',
    'QV234',
    '2,734,735', '156,173,801,802', 10
);

-- QURANIC FORMS (7 patterns)
INSERT INTO name_quranic_forms (name_id, root_letters, pattern_arabic, pattern_name, form_arabic, token_count, percentage, function_description, key_ayat, key_evidence) VALUES
('A01', 'م-ل-ك', 'فَعَالِكَة', 'executing agents plural', 'مَلَائِكَة', 74, 40.0,
 'Primary deployment — 40% of all tokens. The executing agents of governance. م-ل-ك in operational motion. Not messengers (Greek ἄγγελος replaced root with ἀγγέλλω to announce — downgraded governance to communication).',
 'Q2:30,Q2:34,Q3:39,Q3:42', 'Q2:30: announced khalifah TO the malaikah — they are the operational system into which human was introduced. Q2:34: commanded to prostrate — governance hierarchy restructured.'),

('A01', 'م-ل-ك', 'فُعْل', 'base noun', 'مُلْك', 46, 24.9,
 'The operational authority itself. Revocable — given and stripped at will (Q3:26). Held directly — in His hand (Q67:1). Not territory, not power, not wealth — the capacity to govern.',
 'Q67:1,Q3:26,Q2:247,Q2:251', 'Q67:1: بِيَدِهِ الْمُلْكُ — in His hand, actively gripped. Q3:26: تُؤْتِي الْمُلْكَ مَن تَشَاءُ وَتَنزِعُ — given and stripped, both verbs present tense = ongoing.'),

('A01', 'م-ل-ك', 'يَفْعِلُ/مَلَكَتْ', 'verb forms', 'يَمْلِكُ/مَلَكَتْ', 39, 21.1,
 'Creature-level م-ل-ك. Primarily NEGATED: لَا يَمْلِكُ appears 18 times — the Quran uses the root more to DENY creature possession than to affirm it. Positive usage limited to مَا مَلَكَتْ أَيْمَانُكُم (temporary legal custody).',
 'Q5:76,Q13:16,Q25:3,Q36:71', 'Q5:76: مَا لَا يَمْلِكُ لَكُمْ ضَرًّا وَلَا نَفْعًا — what does NOT possess authority over harm or benefit for you. The Quran systematically restricts creature م-ل-ك.'),

('A01', 'م-ل-ك', 'فَعِل', 'permanent quality adjective', 'مَلِك', 12, 6.5,
 'Pattern فَعِل = permanent essential attribute, not acquired or temporary. This is م-ل-ك as the NATURE of Allah, not an action He performs.',
 'Q59:23,Q114:2,Q23:116', 'Q59:23: الْمَلِكُ — first attribute after testimony of oneness. Q114:2: مَلِكِ النَّاسِ — of the species, not a territory. Q23:116: الْمَلِكُ الْحَقُّ — the Malik in binding reality.'),

('A01', 'م-ل-ك', 'فَاعِل', 'active participle', 'مَالِك', 4, 2.2,
 'Active present possession. Dual qiraah in Q1:4 (مَالِكِ/مَلِكِ) encodes both active exercise AND essential nature simultaneously. Most-recited م-ل-ك instance — every salah.',
 'Q1:4,Q3:26', 'Q1:4: مَالِكِ يَوْمِ الدِّينِ — active possessor of the Day of the System of Accountability. Q3:26: مَالِكَ الْمُلْكِ — the possessor of possession itself.'),

('A01', 'م-ل-ك', 'فَعَلُوت', 'maximum scope', 'مَلَكُوت', 4, 2.2,
 'The total operational architecture — visible and unseen. مُلْك = the display. مَلَكُوت = the operating system. Pattern فَعَلُوت is the most expansive morphological form available for a trilateral root.',
 'Q6:75,Q7:185,Q23:88,Q36:83', 'Q23:88: بِيَدِهِ مَلَكُوتُ كُلِّ شَيْءٍ — the malakut of EVERYTHING is in His hand. Q6:75: Ibrahim was shown the malakut — the architecture, not the interface.'),

('A01', 'م-ل-ك', 'فَعْل', 'autonomous control', 'مَلْك', 1, 0.5,
 'Single token. Q20:87: Banu Israil deny autonomous control — مَا أَخْلَفْنَا مَوْعِدَكَ بِمَلْكِنَا. The only instance, in a context of denied responsibility. Autonomous human م-ل-ك: claimed, questionable.',
 'Q20:87', 'Used by those who worshipped the calf to deny they had مَلْك over their actions. The Quran places autonomous human م-ل-ك in the category of excuse-making.');

-- CORRUPTION CHAIN (5 stages)
INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A01', 'م-ل-ك', 1, 'Pre-Quranic Lisan', 'pre-610 CE',
 'م-ل-ك already degraded to political title — مُلُوك = tribal rulers. Word in use as human title BEFORE revelation. Quran was reclaiming; listeners were mapping backward onto the biggest human مَلِك they knew.',
 'The full root architecture — مَلَكُوت, مَلَائِكَة as operational agents, the essential/active distinction (مَلِك/مَالِك). Reduced to: one man controlling one territory.', 'DP08'),

('A01', 'م-ل-ك', 2, 'Severance of مَلَك from مَلِك', '8th-10th century CE',
 'Lisan lexicography and education taught مَلَك (angel) and مَلِك (sovereign) as separate vocabulary. Dictionaries list them under separate entries. Children learn them on different pages.',
 '40% of the root Quranic usage (مَلَائِكَة) disconnected from the Name. The governance system severed from the governor. A sovereign without his executive branch.', 'DP08,DP07'),

('A01', 'م-ل-ك', 3, 'Loss of مَلَكُوت', '10th century CE onward',
 'Low frequency (4 tokens) made مَلَكُوت invisible to non-specialists. The deepest form of the root — the total operating architecture — fell out of common understanding.',
 'Governance understood as surface (political, visible order) instead of total (ontological — the operating system of everything). The Name lost its depth dimension.', 'DP08'),

('A01', 'م-ل-ك', 4, 'DS04/DS05 translation — Greek/Latin split', '2nd-5th century CE',
 'Greek replaced one root with two unrelated words: βασιλεύς (basileus) for مَلِك, ἄγγελος (angelos) for مَلَك. Latin inherited the split: rex/angelus. English: king/angel — no connection visible.',
 'Root unity permanently unrecoverable in European languages. The Qurans 40% allocation to مَلَائِكَة structurally invisible in English. Angel and king share no etymological connection.', 'DP08,DP12'),

('A01', 'م-ل-ك', 5, 'Political claim by human rulers', 'ongoing',
 'Human rulers took the title: مَلِك الأردن, السعودية, المغرب. A Name of Allah worn by creatures. Q3:26 revocability obscured. Inherited authority legitimised through linguistic corruption.',
 'The Name scaled to human size so humans could wear it. Populations accept monarchical authority as inherent right instead of revocable loan.', 'DP07,DP12');

-- PHYSICAL PROOF (raw milk — 5 components mapped)
INSERT INTO name_physical_proof (name_id, root_letters, substance, component, root_form_equivalent, component_function, corruption_operation, corruption_result, operator_name, operator_date) VALUES
('A01', 'م-ل-ك', 'raw milk', 'living enzymes (lactase, lipase, phosphatase)',
 'مَلَائِكَة — the executing agents',
 'break down, process, and deliver nutrients to the body — they DO the governance work',
 'pasteurisation — heating to 72°C for 15 seconds',
 'enzymes killed. Body must process alone. Lactose intolerance = body lacking the مَلَائِكَة that raw milk carried within itself.',
 'Louis Pasteur', '1864'),

('A01', 'م-ل-ك', 'raw milk', 'beneficial bacteria (lactobacillus, bifidobacterium)',
 'مَلَائِكَة — operational governance layer',
 'govern the gut biome, protect against pathogens, maintain internal order',
 'pasteurisation — heating to 72°C for 15 seconds',
 'bacteria killed. Gut governance system left undefended. Replaced by external probiotics (dependency on processed substitutes).',
 'Louis Pasteur', '1864'),

('A01', 'م-ل-ك', 'raw milk', 'immunoglobulins (IgA, IgG)',
 'مَلَكُوت — the unseen protective architecture',
 'shield the recipient at the immune level — invisible governance operating below the surface',
 'pasteurisation — heating to 72°C for 15 seconds',
 'immunoglobulins denatured. The unseen protective architecture stripped. Immune function must be built without the مَلَكُوت layer.',
 'Louis Pasteur', '1864'),

('A01', 'م-ل-ك', 'raw milk', 'bioavailable vitamins (B12, C, B6)',
 'مُلْك — the visible substance, the nourishment the body can see and use',
 'direct nourishment — the visible, measurable nutritional content',
 'pasteurisation — heating to 72°C for 15 seconds',
 'vitamins reduced 20-50%. The visible substance remains but weakened. The surface survives; the content is diminished.',
 'Louis Pasteur', '1864'),

('A01', 'م-ل-ك', 'raw milk', 'intact protein structures (casein, whey)',
 'the root م-ل-ك intact — the complete structure carrying all components',
 'the structural integrity that holds enzymes, bacteria, immunoglobulins, and vitamins in their functional relationships',
 'pasteurisation — heating to 72°C for 15 seconds',
 'proteins denatured. Root structure damaged. Body recognises altered structure as foreign — allergic reactions. The form of م-ل-ك remains; the architecture is broken.',
 'Louis Pasteur', '1864');

-- DAMAGE REGISTER (2 domains)
INSERT INTO name_damage_register (name_id, root_letters, domain, mechanism, scale, population_affected, severity, reversible, key_evidence) VALUES
('A01', 'م-ل-ك', 'governance',
 'Reducing الْمَلِكُ to The King allowed human rulers to model authority on a divine attribute they do not possess. If the Name includes مَلَكُوت and مَلَائِكَة, no human qualifies. All human مُلْك is a revocable loan (Q3:26). The corruption scaled the Name to human size so humans could wear it.',
 'global', 'all populations under monarchical/authoritarian rule in Muslim-majority societies',
 'structural', 'yes — restoring root knowledge reveals all human مُلْك as temporary allocation, not inherent right',
 'Q3:26: تُؤْتِي الْمُلْكَ مَن تَشَاءُ وَتَنزِعُ الْمُلْكَ مِمَّن تَشَاءُ — given AND stripped at will. No human مَلِك is permanent.'),

('A01', 'م-ل-ك', 'health',
 'Pasteurisation of milk = physical م-ل-ك corruption. Living م-ل-ك (raw milk with enzymes/bacteria/immunoglobulins) processed into dead م-ل-ك (white liquid without operating system). Generations raised on pasteurised milk lost capacity to digest raw milk — lactose intolerance. Same mechanism as linguistic corruption: strip مَلَائِكَة, keep surface, sell it back as safe.',
 'global', 'all populations consuming pasteurised dairy (~6 billion)',
 'structural', 'partial — raw milk reintroduction restores gut capacity over time, but generational damage compounds',
 'Lactose intolerance rates: 65-70% of global population. Highest in populations longest separated from raw milk. The intolerance is not genetic — it is the result of مَلَائِكَة deprivation across generations.');

-- Fix the wrong root_id in a2_names_of_allah for A01
-- (Currently R02 = أ-ب-د, should reference QRD 1423 = م-ل-ك)
-- UPDATE a2_names_of_allah SET root_id = 'R1423' WHERE allah_id = 'A01';
-- (commented out — will execute separately after verification)
