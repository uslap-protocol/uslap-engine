-- ═══════════════════════════════════════════════════════════════════════════════
-- USLaP PENDING WRITES — accumulated during session 2026-03-24
-- Execute ALL at once when bbi approves writes
-- ═══════════════════════════════════════════════════════════════════════════════

-- #8: 72 RU entries (T163-T242, R304-R309) — KEEP FOR INVESTIGATION
-- Problem: root_letters (корневые_буквы) empty. T-prefix root_ids not registered.
-- Data IS present: Kashgari forms, phonetic chains, sources (Sevortyan ЭСТЯ + Kashgari + Baskakov).
-- STATUS: KEEP. Investigate each. Populate root_letters from source_form data.
-- Additional sources to cross-reference:
--   1. Shipova 1976 (Словарь тюркизмов в русском языке, 2000+ words, PDF in Linguistic folder)
--   2. Suleimenov "Az i Ya" 1975 (Turkic strata in Russian, banned by USSR, d→t g→k shifts)

-- #8b: ADD Suleimenov to m3_scholars
INSERT INTO m3_scholars (scholar_id, verified_name, birthplace, identity, role, achievement, lies_applied)
VALUES (
    'SC16',
    'Olzhas Suleimenov / أولجاس سلیمانوف',
    'Alma-Ata (Kazakhstan)',
    'ASB — Kazakh poet, linguist, anti-nuclear activist',
    'Turkologist, linguist, founder of Turkic-Slavic studies',
    'Az i Ya (1975): proved massive Turkic vocabulary strata in oldest Russian text (Song of Igor). '
    'Part 2 (Шумер-наме): 60 Sumerian-Turkic matches from clay tablets. '
    'd→t g→k shifts = same as S19/S01/S20 in QUF. '
    'Student Mamedov expanded to 800. Hommel found 200 in 1915. '
    'Method: "archaeology of the sign." Won Kul-Tegin Prize 2002. Still publishing at 89.',
    'BANNED by Soviet Union 1975 as "anti-scientific." '
    'Standard academia dismisses Sumerian-Turkic connection. '
    'Same pattern as Kashgari — evidence exists, operators suppress amplification.'
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- #6: A2 root_id — populate 41 missing Names of Allah
-- Mapping: Name → root letters (Arabic consonants, NOT translations)
-- root_id from a1_entries where available; root letters noted where no entry exists yet
-- ═══════════════════════════════════════════════════════════════════════════════

-- Names with existing root_id in a1_entries:
UPDATE a2_names_of_allah SET root_id = 'R341' WHERE allah_id = 'A10';  -- الحَمِيد → ح-م-د
UPDATE a2_names_of_allah SET root_id = 'R700' WHERE allah_id = 'A36';  -- الْوَهَّابُ → و-ه-ب
UPDATE a2_names_of_allah SET root_id = 'R669' WHERE allah_id = 'A40';  -- الرَّافِعُ → ر-ف-ع
UPDATE a2_names_of_allah SET root_id = 'R536' WHERE allah_id = 'A47';  -- الْخَبِيرُ → خ-ب-ر
UPDATE a2_names_of_allah SET root_id = 'R723' WHERE allah_id = 'A48';  -- الْحَلِيمُ → ح-ل-م
UPDATE a2_names_of_allah SET root_id = 'R549' WHERE allah_id = 'A49';  -- الْعَظِيمُ → ع-ظ-م
UPDATE a2_names_of_allah SET root_id = 'R571' WHERE allah_id = 'A50';  -- الْعَلِيُّ → ع-ل-و
UPDATE a2_names_of_allah SET root_id = 'R614' WHERE allah_id = 'A52';  -- الْحَفِيظُ → ح-ف-ظ
UPDATE a2_names_of_allah SET root_id = 'R582' WHERE allah_id = 'A54';  -- الْحَسِيبُ → ح-س-ب
UPDATE a2_names_of_allah SET root_id = 'R713' WHERE allah_id = 'A57';  -- الرَّقِيبُ → ر-ق-ب
UPDATE a2_names_of_allah SET root_id = 'R608' WHERE allah_id = 'A58';  -- الْمُجِيبُ → ج-و-ب
UPDATE a2_names_of_allah SET root_id = 'R499' WHERE allah_id = 'A59';  -- الْوَاسِعُ → و-س-ع
UPDATE a2_names_of_allah SET root_id = 'R618' WHERE allah_id = 'A65';  -- الْقَوِيُّ → ق-و-ي
UPDATE a2_names_of_allah SET root_id = 'R598' WHERE allah_id = 'A76';  -- الْمُقَدِّمُ → ق-د-م
UPDATE a2_names_of_allah SET root_id = 'R534' WHERE allah_id = 'A77';  -- الْمُؤَخِّرُ → أ-خ-ر
UPDATE a2_names_of_allah SET root_id = 'R632' WHERE allah_id = 'A78';  -- الْأَوَّلُ → أ-و-ل
UPDATE a2_names_of_allah SET root_id = 'R534' WHERE allah_id = 'A79';  -- الْآخِرُ → أ-خ-ر (same root as A77)
UPDATE a2_names_of_allah SET root_id = 'R540' WHERE allah_id = 'A80';  -- الظَّاهِرُ → ظ-ه-ر
UPDATE a2_names_of_allah SET root_id = 'R692' WHERE allah_id = 'A81';  -- الْبَاطِنُ → ب-ط-ن
UPDATE a2_names_of_allah SET root_id = 'R571' WHERE allah_id = 'A83';  -- الْمُتَعَالِ → ع-ل-و (same root as A50)
UPDATE a2_names_of_allah SET root_id = 'R745' WHERE allah_id = 'A85';  -- الْمُنْتَقِمُ → ن-ق-م
UPDATE a2_names_of_allah SET root_id = 'R636' WHERE allah_id = 'A86';  -- الْعَفُوُّ → ع-ف-و
UPDATE a2_names_of_allah SET root_id = 'R527' WHERE allah_id = 'A90';  -- الْجَامِعُ → ج-م-ع
UPDATE a2_names_of_allah SET root_id = 'R744' WHERE allah_id = 'A93';  -- الْمَانِعُ → م-ن-ع
UPDATE a2_names_of_allah SET root_id = 'R535' WHERE allah_id = 'A94';  -- الضَّارُّ → ض-ر-ر
UPDATE a2_names_of_allah SET root_id = 'R538' WHERE allah_id = 'A95';  -- النَّافِعُ → ن-ف-ع
UPDATE a2_names_of_allah SET root_id = 'R722' WHERE allah_id = 'A97';  -- الْبَاقِي → ب-ق-ي
UPDATE a2_names_of_allah SET root_id = 'R732' WHERE allah_id = 'A98';  -- الرَّشِيدُ → ر-ش-د

-- Names whose roots exist in QRD but have NO a1_entry yet (no root_id available):
-- A31 الْمُهَيْمِنُ → ه-م-ن (8 tokens in QRD, no a1 entry)
-- A38 الْقَابِضُ → ق-ب-ض (9 tokens, no a1 entry)
-- A39 الْخَافِضُ → خ-ف-ض (4 tokens, no a1 entry)
-- A42 الْمُذِلُّ → ذ-ل-ل (24 tokens, no a1 entry)
-- A46 اللَّطِيفُ → ل-ط-ف (8 tokens, no a1 entry)
-- A53 الْمُقِيتُ → ق-و-ت (2 tokens, no a1 entry)
-- A55 الْجَلِيلُ → ج-ل-ل (2 tokens, no a1 entry)
-- A61 الْمَجِيدُ → م-ج-د (4 tokens, no a1 entry)
-- A66 الْمَتِينُ → م-ت-ن (3 tokens, no a1 entry)
-- A69 الْمُبْدِئُ → ب-د-ء (no a1 entry — note: ب-د-ع is separate root for A96)
-- A87 الرَّءُوفُ → ر-ء-ف (no a1 entry)
-- A89 ذُو الْجَلَالِ → ج-ل-ل (same as A55, no a1 entry)
-- A96 الْبَدِيعُ → ب-د-ع (4 tokens, no a1 entry)
-- These 13 Names need EN entries created first, THEN root_id can be assigned.

-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- NAME PIPELINE: A02 الجَبَّار / al-Jabbār / root ج-ب-ر / R08
-- ═══════════════════════════════════════════════════════════════════════════════

-- A02 ROOT HUB
INSERT INTO name_root_hub (
    name_id, arabic_name, root_letters, qrd_id, token_count,
    abjad_values, abjad_total, abjad_property,
    letter_1, letter_1_abjad, letter_1_phonetic, letter_1_root_function,
    letter_2, letter_2_abjad, letter_2_phonetic, letter_2_root_function,
    letter_3, letter_3_abjad, letter_3_phonetic, letter_3_root_function,
    phonetic_arc, corrected_meaning, current_meaning, qv_ids,
    downstream_en_ids, downstream_ru_ids, downstream_eu_count
) VALUES (
    'A02', 'الجَبَّار', 'ج-ب-ر', NULL, 13,
    '3-2-200', 205, '205 = 5 × 41. Prime factor 41. The root operates in restoration cycles — 5 = hand (خَمْسَة), the instrument of mending.',
    'ج', 3, 'voiced palato-alveolar affricate — tongue presses palate then releases with friction, force applied then channelled', 'force application — the root opens with controlled pressure, the compulsion that initiates restoration',
    'ب', 2, 'voiced bilabial plosive — lips seal completely then release, containment then opening', 'containment — the force is enclosed, held within structure, the bone set before it heals',
    'ر', 200, 'voiced alveolar trill — tongue vibrates repeatedly, continuous rolling motion', 'continuation — the restoration propagates, repeats, the mending extends outward from the break point',
    'force → contain → propagate', 'The One who applies irresistible force to restore what is broken — compels fractured systems back into structural integrity. Applies force (ج), holds in place (ب), propagates restoration (ر).',
    'The Compeller / The Irresistible', 'QV232',
    '8,114', '8', 10
);

-- A02 QURANIC FORMS (7 forms, 13 tokens)
INSERT INTO name_quranic_forms (name_id, root_letters, pattern_arabic, pattern_name, form_arabic, token_count, percentage, function_description, key_ayat, key_evidence) VALUES
('A02', 'ج-ب-ر', 'فَعَّال', 'intensive agent', 'جَبَّار', 10, 76.9,
 'Pattern فَعَّال = one who does the action intensely, repeatedly, as permanent nature. 10 of 13 tokens. The Quran overwhelmingly uses ج-ب-ر in this intensive form. When applied to Allah (Q59:23): restoration so powerful it is irresistible. When applied to humans (Q11:59, Q14:15, Q26:130, Q40:35): force WITHOUT restoration = tyranny. Same pattern, opposite valence — the Quran distinguishes divine جَبَّار (restores) from human جَبَّار (destroys).',
 'Q59:23,Q11:59,Q14:15,Q26:130,Q40:35',
 'Q59:23: ٱلْجَبَّارُ — the ONLY instance applied to Allah. Placed between الْعَزِيزُ (the Unassailable) and الْمُتَكَبِّرُ (the Supreme). 9 of 10 جَبَّار tokens describe HUMAN tyrants. The Name is reclaimed from its misuse.');

INSERT INTO name_quranic_forms (name_id, root_letters, pattern_arabic, pattern_name, form_arabic, token_count, percentage, function_description, key_ayat, key_evidence) VALUES
('A02', 'ج-ب-ر', 'فَعَّارِينَ', 'intensive agent plural', 'جَبَّارِينَ', 2, 15.4,
 'Plural of جَبَّار — human tyrant-collectives. Q5:22: the جَبَّارِينَ occupying the land Banu Israil were told to enter. Q26:130: when you seize, you seize as جَبَّارِينَ — force without mercy, the inversion of the divine Name.',
 'Q5:22,Q26:130',
 'Q5:22: إِنَّ فِيهَا قَوْمًا جَبَّارِينَ — a people who are jabbareen. Q26:130: بَطَشْتُم بَطَشْتُمْ جَبَّارِينَ — when you strike you strike as jabbareen.');

INSERT INTO name_quranic_forms (name_id, root_letters, pattern_arabic, pattern_name, form_arabic, token_count, percentage, function_description, key_ayat, key_evidence) VALUES
('A02', 'ج-ب-ر', 'جِبْرِيل', 'compound proper name', 'جِبْرِيلَ', 1, 7.7,
 'ج-ب-ر + إِل (God). The God-Powered Restorer. QV232: NOT "Gabriel" (Hebrew-ized form that erases the Arabic compound roots). The angel of Revelation carries the Name of الجَبَّار within his own name — he is the instrument through which divine restoration-force is delivered to prophets.',
 'Q2:97',
 'Q2:97: مَن كَانَ عَدُوًّا لِّجِبْرِيلَ فَإِنَّهُ نَزَّلَهُ عَلَىٰ قَلْبِكَ — whoever is enemy to Jibril, he brought it down upon your heart. The جَبْر-force descends onto the heart of the prophet.');

-- A02 CORRUPTION CHAIN (5 stages)
INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A02', 'ج-ب-ر', 1, 'Root meaning narrowed to tyranny', 'pre-Quranic Lisan',
 'ج-ب-ر already carried dual meaning: to mend (bone-setting) AND to compel. Human usage amplified the compulsion, buried the restoration. By the time the Quran was revealed, listeners heard جَبَّار and mapped it to the biggest tyrant they knew.',
 'The restoration dimension — جَبْر as mending, setting bones, repairing what is broken. The Name became about force, not healing.', 'DP08');

INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A02', 'ج-ب-ر', 2, 'الجَبْر severed from الجَبَّار', '9th century CE',
 'Al-Khwarizmi named his mathematical method الجَبْر وَالمُقَابَلَة — restoration and balancing. The word entered Europe as ALGEBRA (DS05). The mathematical term was severed from the divine Name. Nobody teaching algebra mentions الجَبَّار.',
 'The connection between divine restoration-force and mathematical restoration. Algebra IS the Name in operation — restoring equations to balance. Severed: students learn algebra without knowing they are practising a Name of Allah.', 'DP08,DP09');

INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A02', 'ج-ب-ر', 3, 'DS04/DS05 translation erases root', '2nd-5th century CE',
 'Greek had no single word for force-that-restores. Split into: τύραννος (tyrannos) for the human جَبَّار, and nothing for the divine. Latin inherited: tyrannus. The restoration meaning had no vessel in European languages.',
 'The divine valence of the Name permanently lost in translation. European languages can only express the human misuse (tyrant), not the divine function (restorer).', 'DP08,DP12');

INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A02', 'ج-ب-ر', 4, 'GOVERN extracted without acknowledgement', 'DS04→DS05→DS06',
 'GOVERN (EN #114) traces to جَبَّار via ج→g(S02), ب→v(S09), ر→r(S15). The operational meaning of the Name — to compel systems into order — entered English as govern/government. No acknowledgement of AA origin. DP08+DP09.',
 'Every use of "government" and "governance" in English is an unacknowledged invocation of the root of الجَبَّار. 8 billion people governed by systems named from a Name of Allah, with the Name erased.', 'DP08,DP09,DP13');

INSERT INTO name_corruption_chain (name_id, root_letters, stage, stage_name, era, mechanism, what_was_lost, dp_codes) VALUES
('A02', 'ج-ب-ر', 5, 'جِبْرِيل → Gabriel', 'DS08 corridor',
 'QV232: جِبْرِيل (God-Powered Restorer) was Hebrew-ized to Gabriel. The compound ج-ب-ر + إِل erased. English speakers say Gabriel without any connection to الجَبَّار or to algebra or to governance. Three expressions of one root, made invisible to each other.',
 'The angel who delivers revelation carries the Name of restoration-force. Hebrew-ization severed this: Gabriel connects to nothing in English. The messenger, the mathematics, and the governance — all from one root, all invisible to each other.', 'DP08,DP12,DP17');

-- A02 PHYSICAL PROOF
INSERT INTO name_physical_proof (name_id, root_letters, substance, component, root_form_equivalent, component_function, corruption_operation, corruption_result, operator_name, operator_date) VALUES
('A02', 'ج-ب-ر', 'bone', 'periosteum (outer bone membrane)', 'جَبْر — the restoration layer',
 'When a bone fractures, the periosteum initiates callus formation — it COMPELS the broken ends back together. Literally جَبَّار at the tissue level: irresistible force applied to restore structural integrity.',
 'Modern orthopaedics replaces natural جَبْر with metal plates, screws, rods — external hardware that bypasses the periosteum restoration system',
 'The body own جَبَّار mechanism (periosteum-driven healing) atrophied under metal fixation. Bones healed but the natural restoration pathway weakened. Hardware removal often reveals bone that cannot self-repair.',
 'Surgical fixation paradigm', '20th century');

INSERT INTO name_physical_proof (name_id, root_letters, substance, component, root_form_equivalent, component_function, corruption_operation, corruption_result, operator_name, operator_date) VALUES
('A02', 'ج-ب-ر', 'bone', 'osteoblasts (bone-building cells)', 'جَبَّارِينَ — the restoring agents (divine valence)',
 'Osteoblasts are the cellular جَبَّارِينَ — they arrive at the fracture site and COMPEL new bone matrix into existence. They apply force to rebuild. They are the مَلَائِكَة of the skeletal system, executing the جَبْر program.',
 'Bisphosphonate drugs (Fosamax etc.) — supposed to strengthen bone but actually KILL osteoclasts, disrupting the natural remodelling cycle',
 'Bones become brittle-dense: hard but not resilient. The جَبْر cycle (break down old → rebuild new) is frozen. Atypical fractures result — the bone can no longer self-restore.',
 'Merck (Fosamax)', '1995');

-- A02 DAMAGE REGISTER
INSERT INTO name_damage_register (name_id, root_letters, domain, mechanism, scale, population_affected, severity, reversible, key_evidence) VALUES
('A02', 'ج-ب-ر', 'linguistics',
 'Three expressions of one root made invisible to each other: الجَبَّار (Name of Allah) / الجَبْر (algebra) / GOVERN (English). Nobody studying algebra knows it is a Name of Allah. Nobody using the word government knows it traces to جَبَّار. Nobody hearing Gabriel connects it to either. One root, three domains, total severance.',
 'global', 'all populations using algebra, governance terminology, or the name Gabriel', 'structural', 'yes — root knowledge restores all three connections instantly',
 'EN #8 ALGEBRA: ج→g, ب→b, ر→r. EN #114 GOVERN: ج→g, ب→v, ر→r. QV232 جِبْرِيل: ج-ب-ر + إِل compound. All QUF-validated at score 10.');

INSERT INTO name_damage_register (name_id, root_letters, domain, mechanism, scale, population_affected, severity, reversible, key_evidence) VALUES
('A02', 'ج-ب-ر', 'health',
 'Natural bone restoration (جَبْر) replaced by surgical hardware and pharmaceutical intervention. Periosteum-driven healing bypassed by metal fixation. Osteoblast cycle (the cellular جَبَّارِينَ) disrupted by bisphosphonates. The body own restoration-force systematically weakened.',
 'global', 'populations with access to modern orthopaedics (~4 billion)', 'structural', 'partial — natural bone healing can be supported through nutrition, movement, and allowing periosteum to function',
 'Atypical femoral fractures in long-term bisphosphonate users. Hardware-dependent healing in fixated fractures. Both = the جَبْر mechanism suppressed.');

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLE MERGE: Drop quran_root_dictionary, keep root_translations
-- Both have identical 1,738 roots. root_translations is richer (has Quranic forms, verb/noun breakdowns).
-- Code files already updated: compiler, mizan, handler, stop_scan all point to root_translations.
--
-- STEP 1: Recreate 21 triggers that reference quran_root_dictionary → root_translations
-- (Extract each trigger SQL, replace table name, drop old, create new)
-- STEP 2: DROP TABLE quran_root_dictionary;
--
-- WARNING: 21 triggers need migration. Execute trigger recreation BEFORE dropping table.
-- This is a multi-step operation — run in a single transaction.
-- STATUS: PENDING — needs trigger SQL extraction and rewrite before execution.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- #10: EU 130 QUF stamp — run batch QUF validation on unstamped EU entries
-- Execute via: python3 Code_files/uslap_quf.py stamp eu
-- This writes quf_q, quf_u, quf_f, quf_pass, quf_date columns only.
-- 130 entries currently unstamped out of 4,885 total.
-- ═══════════════════════════════════════════════════════════════════════════════

-- #8c: ADD Shipova to m3_scholars
INSERT INTO m3_scholars (scholar_id, verified_name, birthplace, identity, role, achievement, lies_applied)
VALUES (
    'SC17',
    'Elena Nikolaevna Shipova / Елена Николаевна Шипова',
    'Alma-Ata (Kazakhstan)',
    'ASB — Kazakh linguist',
    'Compiler of Turkic words in Russian language',
    'Словарь тюркизмов в русском языке (Dictionary of Turkisms in Russian), 1976. '
    '2000+ Turkic words documented in Russian. Published Alma-Ata. '
    'PDF: Linguistic/Shipova_Dictionary_Turkisms_Russian_1976.pdf (scanned Cyrillic, needs OCR).',
    'Hidden in plain sight. Kazakh scholar documenting her own peoples vocabulary inside Russian. '
    'Never amplified. Same pattern as Kashgari — evidence exists but nobody promotes it.'
);
