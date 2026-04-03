#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر ALPHABET REFERENCE — 28 Letters of Allah's Arabic

Phase 0 of the أَمْر full-stack computing system.
Every keyword in the أَمْر language traces through these 28 letters.
Data sourced from uslap_database_v3.db (quran_word_roots, shift_lookup, roots).

PHONETIC DESCRIPTIONS: Derived from the letters' behaviour IN Qur'anic roots,
NOT from external phonetics textbooks. The articulation points (مَخَارِج)
are observable from how each letter functions across 77,881 Qur'anic word tokens.

SEMANTIC TENDENCIES: Computed from the top roots where each letter appears
as first (فاء), second (عين), or third (لام) radical. These are DATA patterns,
not interpretations.
"""

ABJAD = {
    'ا': 1, 'ب': 2, 'ج': 3, 'د': 4, 'ه': 5, 'و': 6, 'ز': 7, 'ح': 8, 'ط': 9,
    'ي': 10, 'ك': 20, 'ل': 30, 'م': 40, 'ن': 50, 'س': 60, 'ع': 70, 'ف': 80,
    'ص': 90, 'ق': 100, 'ر': 200, 'ش': 300, 'ت': 400, 'ث': 500, 'خ': 600,
    'ذ': 700, 'ض': 800, 'ظ': 900, 'غ': 1000,
}

# ═══════════════════════════════════════════════════════════════════════
# Each letter entry contains ALL 10 required fields from Phase 0 spec
# ═══════════════════════════════════════════════════════════════════════

ALPHABET = {

    # ──────────────────────────────────────────────────────────────────
    # 0. ء — HAMZA (glottal stop, carried by alif/wāw/yāʾ)
    # ──────────────────────────────────────────────────────────────────
    'ء': {
        'name': 'هَمْزَة',
        'transliteration': 'hamza',
        'abjad': 1,  # shares abjad value with alif (its carrier)
        'phonetic': {
            'makhraj': 'أَقْصَى الحَلْق — deepest point of the throat (glottal)',
            'manner': 'Glottal stop. Complete closure of the vocal cords, then abrupt release. '
                      'The MOST INTERNAL articulation — deeper than any other consonant.',
            'voiced': False,
            'emphatic': False,
            'description': 'Hamza is the glottal stop — the catch in the throat before a vowel. '
                           'It is NOT alif. Alif is the CARRIER; hamza is the SOUND. '
                           'Hamza initiates the highest-frequency roots: أ-ل-ه (2930), أ-م-ن (832), '
                           'أ-ت-ي (385), أ-م-ر (223), أ-خ-ذ (217). '
                           'The glottal stop = the FIRST act of speech — before any vowel can sound, '
                           'the glottis must open. Hamza IS that opening.',
        },
        'classification': {
            'sun_moon': 'Neither — hamza is not a solar or lunar letter; it precedes the article.',
            'type': 'Glottal stop',
            'group': 'حُرُوف الحَلْق — throat letters (deepest)',
        },
        'behaviour': {
            'as_first_radical': 'THE most important position. Roots with hamza as first radical '
                                'carry the foundational concepts: أ-ل-ه (divinity, 2930), '
                                'أ-م-ن (security, 832), أ-ي-ي (signs, 388), أ-ت-ي (coming, 385), '
                                'أ-م-ر (command, 223), أ-خ-ذ (taking, 217), أ-ر-ض (earth, 465). '
                                'Hamza as opener = PRIMORDIAL — the first sound initiates the deepest concepts.',
            'as_second_radical': 'Rare. س-أ-ل (asking, 68), ر-أ-ي (seeing, 135). '
                                 'As core, hamza provides INTERRUPTION — a glottal pause at the root\'s heart.',
            'as_third_radical': 'ج-ي-أ (coming, 149), ش-ي-أ (thing, 355), ب-د-أ (beginning, 10). '
                                'As closer, hamza CUTS — the word ends in an abrupt glottal closure.',
            'as_prefix': 'أَ = interrogative prefix (أَلَمْ = did not?). '
                         'أُ = first person singular imperfect in Form IV (أُرْسِلُ = I send).',
            'as_suffix': 'ـأ = rare final hamza (بَدَأَ = he began).',
        },
        'shifts': [
            {'downstream': '(drop)', 'shift_id': 'HAMZA', 'note': 'Hamza drops entirely in most DS corridors'},
            {'downstream': '(vowel)', 'shift_id': 'HAMZA-DROP', 'note': 'Hamza resolves to a bare vowel'},
        ],
        'quranic_stats': {
            'tokens_any_position': None,  # hamza stats are embedded in roots catalogued under أ
            'distinct_roots_any': None,
            'roots_as_first': None,
            'top5_first': [('أ-ل-ه', 2930), ('أ-م-ن', 832), ('أ-ر-ض', 465), ('أ-ي-ي', 388), ('أ-ت-ي', 385)],
            'top5_second': [('ر-أ-ي', 135), ('س-أ-ل', 68)],
            'top5_third': [('ش-ي-أ', 355), ('ج-ي-أ', 149), ('ب-د-أ', 10)],
            'muqattaat': [],
            'note': 'Hamza statistics overlap with alif (ا) — roots like أ-ل-ه are catalogued '
                    'under alif in the compiler but the first radical is hamza phonetically. '
                    'The top5_first list here represents the TRUE hamza-initial roots.',
        },
        'semantic_tendency': 'STOP. INITIATION. THE FIRST ACT. '
                             'Hamza begins the most fundamental concepts: divinity (أ-ل-ه), '
                             'security (أ-م-ن), command (أ-م-ر), creation (أ-ر-ض = earth). '
                             'The glottal stop = the first physical act of speech = the beginning of everything.',
        'paired_letters': {
            'ل (lām)': 'أ-ل = origin + flow (أ-ل-ه divinity). The divine = origin flowing.',
            'م (mīm)': 'أ-م = origin + seal (أ-م-ن security, أ-م-ر command). Sealed origin = certainty.',
            'خ (khāʾ)': 'أ-خ = origin + passage (أ-خ-ذ taking). Taking = passing from origin.',
        },
        'unique': 'Abjad 1 (shared with its carrier alif). Hamza initiates أ-ل-ه (2930) — '
                  'the HIGHEST-frequency root in the Qur\'an. It is the FIRST sound. '
                  'In the أَمْر system, ء = the initializer — the system boot, the first instruction.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 1. ا — ALIF (carrier of hamza, long vowel marker)
    # ──────────────────────────────────────────────────────────────────
    'ا': {
        'name': 'أَلِف',
        'transliteration': 'alif',
        'abjad': 1,

        'phonetic': {
            'makhraj': 'أَقْصَى الحَلْق — deepest point of the throat (furthest cavity)',
            'manner': 'Glottal opener. Not a consonant in the articulated sense — it is '
                      'the CARRIER of the hamza (ء) and the vessel for long vowels (ā). '
                      'It opens the airway. It is the BEGINNING.',
            'voiced': True,
            'emphatic': False,
            'description': 'Alif is the vertical stroke — the ONE. Abjad value 1 = unity. '
                           'It does not articulate against any surface; it is the pure opening '
                           'of the throat. In Qur\'anic morphology it serves as: (1) carrier '
                           'of hamza at word-initial position, (2) long vowel marker (ā), '
                           '(3) the alif of waṣl (connecting alif in definite article ال). '
                           'It has NO downstream shift — no DS language has alif. They inherit '
                           'only what alif carries (the hamza or the vowel), never alif itself.',
        },

        'classification': {
            'sun_moon': 'Neither — alif is not a solar or lunar letter; it is the carrier '
                        'of the definite article but does not assimilate with it.',
            'type': 'Glottal / Vowel carrier',
            'group': 'حُرُوف الحَلْق — throat letters',
        },

        'behaviour': {
            'as_first_radical': 'Rare as true first radical (5 roots, 87 tokens). '
                                'When ا opens a root, it marks PRIMORDIAL concepts: '
                                'ا-ل-ه (divinity, 2930 tokens via أ-ل-ه), ا-ن-س (humanity/familiarity). '
                                'The alif-initial root points to ORIGINS.',
            'as_second_radical': 'Extremely rare (3 roots). ا in the middle = the root\'s '
                                 'core is a VOWEL — openness, space, air.',
            'as_third_radical': 'Rare (2 roots). ا at the end = the root terminates in '
                                'openness, trailing away.',
            'as_prefix': 'Hamzat al-waṣl (ٱ): definite article carrier. '
                         'Hamzat al-qaṭʿ (أَ): interrogative marker (أَلَمْ = did not?). '
                         'First-person singular imperfect prefix (أَعْلَمُ = I know).',
            'as_suffix': 'Dual marker (ا as part of ان). Alif maqṣūra (ى pronounced ā) '
                         'marks certain verb endings and proper nouns.',
        },

        'shifts': [
            # Alif itself has NO shift in shift_lookup — it carries hamza
            # Hamza shifts: drops or becomes a vowel
            {'downstream': '(drop)', 'shift_id': 'HAMZA', 'note': 'Hamza carried by alif drops entirely in DS languages'},
            {'downstream': '(vowel)', 'shift_id': 'HAMZA-DROP', 'note': 'Hamza resolves to a bare vowel sound'},
        ],

        'quranic_stats': {
            'tokens_any_position': 173,
            'distinct_roots_any': 10,
            'roots_as_first': 5,
            'top5_first': [('ا-ل-س', 36), ('ا-ن-س', 28), ('ا-و-ب', 12), ('ا-ز-ر', 6), ('ا-ج-ج', 5)],
            'top5_second': [('م-ا-ء', 8), ('ه-ا-ت', 6), ('ه-ا-ء', 3)],
            'top5_third': [('س-ر-ا', 42), ('ر-ي-ا', 27)],
            'muqattaat': [],  # Alif appears in الم, المر, المص but as PART of combinations
            'note': 'Alif\'s true Qur\'anic weight is HIDDEN in these numbers — '
                    'ا carries the hamza in roots like أ-ل-ه (2930), أ-م-ن (832), '
                    'أ-ت-ي (385), أ-م-ر (223), أ-خ-ذ (217). These are catalogued under hamza (ء) '
                    'in the ALPHABET dict, but alif is the VESSEL. '
                    'See ء entry for hamza-initial root statistics.',
        },

        'semantic_tendency': 'OPENING. UNITY. BEGINNING. Alif opens. Abjad 1 = the ONE. '
                             'Roots with alif/hamza as first radical point to fundamental '
                             'concepts: divinity (أ-ل-ه), security (أ-م-ن), command (أ-م-ر), '
                             'coming (أ-ت-ي), taking (أ-خ-ذ), humanity (أ-ن-س).',

        'paired_letters': {
            'ل (lām)': 'أ-ل = the definite article ال. The most frequent pairing in all of AA. '
                       'Alif (origin/unity) + lām (connection) = THE definite marker.',
            'م (mīm)': 'أ-م = the mother principle. أُمّ (mother), أَمْن (security), أَمْر (command). '
                       'Alif (unity) + mīm (enclosure) = what encloses from the beginning.',
            'ن (nūn)': 'أ-ن = the self-declaration. أَنَا (I), أَنَّ (that/indeed). '
                       'Alif (unity) + nūn (continuation) = the self continuing.',
        },

        'unique': 'Abjad value 1. The ONLY letter that is a pure vertical stroke. '
                  'The only letter with no articulation point in the mouth — it is '
                  'the opening of the throat itself. Every word begins with a breath, '
                  'and alif IS that breath. In the أَمْر system, ا = the boot sequence — '
                  'the system opens.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 2. ب — BĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ب': {
        'name': 'بَاء',
        'transliteration': 'bāʾ',
        'abjad': 2,

        'phonetic': {
            'makhraj': 'الشَّفَتَان — the two lips (bilabial)',
            'manner': 'Plosive. Both lips close completely, then release. '
                      'The FIRST articulated consonant — lips are the outermost gate.',
            'voiced': True,
            'emphatic': False,
            'description': 'Bāʾ is the first letter that requires physical contact — '
                           'lips touching. If alif is the opening of the throat (internal), '
                           'bāʾ is the first EXTERNAL articulation. Abjad 2 = duality, '
                           'pair (the two lips). It is the letter of BUILDING — things '
                           'constructed from parts touching.',
        },

        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate with ال',
            'type': 'Voiced bilabial plosive',
            'group': 'حُرُوف الشَّفَتَيْن — lip letters',
        },

        'behaviour': {
            'as_first_radical': '88 roots, 2194 tokens. Opens roots of CONSTRUCTION and CLARITY: '
                                'ب-ي-ن (to make clear, 282), ب-ع-د (distance, 236), ب-ن-ي (to build, 128), '
                                'ب-ش-ر (human skin/glad tidings, 124), ب-ص-ر (to see, 100). '
                                'When ب opens, it BUILDS or SHOWS.',
            'as_second_radical': 'ر-ب-ب (to nurture, 907 — the HIGHEST), ق-ب-ل (to accept, 291), '
                                 'ع-ب-د (to devote, 265), س-ب-ل (a path, 177), ت-ب-ع (to follow, 166). '
                                 'As the core of a root, ب provides CONTINUITY — nurturing, following, accepting.',
            'as_third_radical': 'ر-ب-ب (907), ع-ذ-ب (denial of sweetness, 373), ك-ت-ب (to write, 311), '
                                'ك-ذ-ب (to deny, 282), ق-ل-ب (to turn/heart, 166). '
                                'As closer, ب SEALS — it closes with an emphatic bilabial stop.',
            'as_prefix': 'بِ = the preposition "by/with/in." Q96:1 بِٱسْمِ = "in/by the name of." '
                         'The ب of instrumentality — HOW something is done.',
            'as_suffix': 'Not typically a suffix letter.',
        },

        'shifts': [
            {'downstream': 'b', 'shift_id': 'S09', 'note': 'Preserved in most DS corridors'},
            {'downstream': 'p', 'shift_id': 'S09', 'note': 'Devoicing: ب→p. Common in DS05 (Latin), Bitig'},
            {'downstream': 'v', 'shift_id': 'S09', 'note': 'Fricativisation: ب→v. Common in DS05'},
        ],

        'quranic_stats': {
            'tokens_any_position': 8322,
            'distinct_roots_any': 296,
            'roots_as_first': 88,
            'top5_first': [('ب-ي-ن', 282), ('ب-ع-د', 236), ('ب-ن-ي', 128), ('ب-ش-ر', 124), ('ب-ص-ر', 100)],
            'top5_second': [('ر-ب-ب', 907), ('ق-ب-ل', 291), ('ع-ب-د', 265), ('س-ب-ل', 177), ('ت-ب-ع', 166)],
            'top5_third': [('ر-ب-ب', 907), ('ع-ذ-ب', 373), ('ك-ت-ب', 311), ('ك-ذ-ب', 282), ('ق-ل-ب', 166)],
            'muqattaat': [],
        },

        'semantic_tendency': 'CLOSURE. CONSTRUCTION. CONTACT. CLARITY. '
                             'ب is the letter of things that TOUCH and BUILD: '
                             'ب-ن-ي (building), ب-ي-ن (clarifying by separating), '
                             'ب-ص-ر (seeing = light touching the eye). '
                             'The two lips touch = two things brought together = construction.',

        'paired_letters': {
            'ن (nūn)': 'ب-ن = to build (ب-ن-ي). Lips (ب) + continuation (ن) = construction that continues.',
            'ي (yāʾ)': 'ب-ي = house/between (ب-ي-ت/ب-ي-ن). The built enclosure or the space between.',
            'ر (rāʾ)': 'ب-ر = land/righteousness (ب-ر-ر). Building outward = open land, goodness.',
        },

        'unique': 'Abjad 2 = duality. The two lips = the first PAIR. ب is the letter of بِسْمِ — '
                  'the very first letter uttered in the Qur\'an after the opening. '
                  'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ begins with ب. '
                  'In the أَمْر system, ب = the construction operator — what builds structures.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 3. ت — TĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ت': {
        'name': 'تَاء',
        'transliteration': 'tāʾ',
        'abjad': 400,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا العُلْيَا — tip of tongue against upper front teeth roots',
            'manner': 'Voiceless dental plosive. Tongue tip strikes upper teeth base, releases sharply. '
                      'The NON-emphatic partner of ط (ṭāʾ). Where ط is heavy/deep, ت is light/sharp.',
            'voiced': False,
            'emphatic': False,
            'description': 'Tāʾ is the light dental stop. Abjad 400 — high value for a light letter. '
                           'It marks FOLLOWING and SUCCESSION — things that come AFTER. '
                           'ت-ب-ع (to follow), ت-و-ب (to return/repent = to follow back). '
                           'As a prefix it marks second person (أَنْتَ تَعْلَمُ = you know) '
                           'and feminine (كَتَبَتْ = she wrote).',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates with ال: التَّوْبَة',
            'type': 'Voiceless dental plosive',
            'group': 'حُرُوف أَسَلِيَّة — tongue-tip letters',
        },
        'behaviour': {
            'as_first_radical': '20 roots. Opens FOLLOWING/SUCCESSION: ت-ب-ع (to follow, 166), '
                                'ت-و-ب (to return, 106), ت-ل-و (to recite/follow, 71), ت-ج-ر (commerce, 61). '
                                'When ت opens, it marks what COMES AFTER.',
            'as_second_radical': 'أ-ت-ي (to come/arrive, 385), ك-ت-ب (to write/prescribe, 311), '
                                 'ق-ت-ل (to fight, 164). As core, ت provides the STRIKING action — '
                                 'the sharp dental contact = impact, arrival, inscription.',
            'as_third_radical': 'م-و-ت (to die, 148), ب-ي-ت (house, 77), ت-ح-ت (beneath, 56). '
                                'As closer, ت CUTS OFF — the sharp stop ends the word decisively.',
            'as_prefix': 'Second person imperfect: تَفْعَلُ (you do). '
                         'Feminine marker: كَتَبَتْ (she wrote). '
                         'Verbal noun pattern: تَفْعِيل (intensification).',
            'as_suffix': 'تْ = feminine past tense marker. تُ = first person past (كَتَبْتُ = I wrote).',
        },
        'shifts': [
            {'downstream': 't', 'shift_id': 'S24', 'note': 'Preserved as t in most DS corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 2710, 'distinct_roots_any': 97, 'roots_as_first': 20,
            'top5_first': [('ت-ب-ع', 166), ('ت-و-ب', 106), ('ت-ل-و', 71), ('ت-ج-ر', 61), ('ت-ح-ت', 56)],
            'top5_second': [('أ-ت-ي', 385), ('ك-ت-ب', 311), ('ق-ت-ل', 164), ('ء-ت-ي', 116), ('م-ت-ع', 67)],
            'top5_third': [('م-و-ت', 148), ('ب-ي-ت', 77), ('ت-ح-ت', 56), ('ف-و-ت', 40), ('م-ر-ت', 26)],
            'muqattaat': [],
        },
        'semantic_tendency': 'SNAP. FOLLOWING. SHARP ACTION. '
                             'ت marks what comes AFTER — following (ت-ب-ع), returning (ت-و-ب), '
                             'reciting (ت-ل-و = following the text). The sharp dental strike = decisive action.',
        'paired_letters': {
            'ب (bāʾ)': 'ت-ب = following + building (ت-ب-ع). To follow is to build upon what came before.',
            'و (wāw)': 'ت-و = succession + connection (ت-و-ب). Returning = reconnecting after succession.',
            'ل (lām)': 'ت-ل = succession + flow (ت-ل-و). Recitation = following the flow.',
        },
        'unique': 'Abjad 400. The feminine marker of AA — grammatical gender lives in ت. '
                  'As prefix (تَ) it addresses YOU directly (second person). '
                  'In the أَمْر system, ت = the iterator — what follows, what comes next.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 4. ث — THĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ث': {
        'name': 'ثَاء',
        'transliteration': 'thāʾ',
        'abjad': 500,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أَطْرَاف الثَّنَايَا العُلْيَا — tongue tip between upper/lower front teeth',
            'manner': 'Voiceless interdental fricative. Tongue tip protrudes slightly between teeth, '
                      'air passes as friction. The NON-emphatic partner of ظ (ẓāʾ).',
            'voiced': False,
            'emphatic': False,
            'description': 'Thāʾ is the lightest interdental. Abjad 500. '
                           'The tongue protrudes between the teeth — exposed, vulnerable. '
                           'ث roots deal with WEIGHT, MULTIPLICATION, REMAINS: '
                           'ث-ل-ث (three/third), ث-ق-ل (heaviness), ث-م-ر (fruit = product of growth).',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates with ال: الثَّمَر',
            'type': 'Voiceless interdental fricative',
            'group': 'حُرُوف لَثَوِيَّة — interdental letters',
        },
        'behaviour': {
            'as_first_radical': '20 roots. Opens MULTIPLICATION/WEIGHT: ث-ل-ث (three, 32), '
                                'ث-ق-ل (heavy, 28), ث-م-د (Thamūd, 26), ث-م-ر (fruit, 24), ث-و-ب (garment/reward, 21). '
                                'When ث opens, it marks what MULTIPLIES or WEIGHS.',
            'as_second_radical': 'ك-ث-ر (many/abundance, 166), م-ث-ل (likeness/example, 119), '
                                 'أ-ث-م (sin, 60), و-ث-ق (trust/bind, 33). As core, ث provides DENSITY — '
                                 'thickness, multiplicity, heaviness.',
            'as_third_radical': 'ب-ع-ث (to raise/resurrect, 67), ح-د-ث (event/new, 36). '
                                'As closer, ث trails off — the interdental lets the word DISSIPATE.',
            'as_prefix': 'Not a prefix letter.',
            'as_suffix': 'Not a typical suffix.',
        },
        'shifts': [
            {'downstream': 'th', 'shift_id': 'S26', 'note': 'Preserved as th in DS05 corridor'},
        ],
        'quranic_stats': {
            'tokens_any_position': 943, 'distinct_roots_any': 63, 'roots_as_first': 20,
            'top5_first': [('ث-ل-ث', 32), ('ث-ق-ل', 28), ('ث-م-د', 26), ('ث-م-ر', 24), ('ث-و-ب', 21)],
            'top5_second': [('ك-ث-ر', 166), ('م-ث-ل', 119), ('أ-ث-م', 60), ('و-ث-ق', 33), ('أ-ث-ر', 22)],
            'top5_third': [('ب-ع-ث', 67), ('ح-د-ث', 36), ('ث-ل-ث', 32), ('و-ر-ث', 31), ('ل-ب-ث', 31)],
            'muqattaat': [],
        },
        'semantic_tendency': 'THINNING. DENSITY. WEIGHT. REMAINS. '
                             'ث marks what accumulates: ك-ث-ر (many), ث-ق-ل (heavy), '
                             'ث-م-ر (fruit = accumulated growth), و-ر-ث (inheritance = what remains).',
        'paired_letters': {
            'ل (lām)': 'ث-ل = multiplication + flow (ث-ل-ث = three). The first number beyond duality.',
            'ق (qāf)': 'ث-ق = weight + force (ث-ق-ل = heavy). Density meeting deep articulation.',
            'م (mīm)': 'ث-م = density + enclosure (ث-م-ر = fruit). Growth enclosed and multiplied.',
        },
        'unique': 'Abjad 500. The interdental that DS languages LOSE first — '
                  'English preserves it (th) but most DS corridors collapse ث→t or ث→s. '
                  'In the أَمْر system, ث = the multiplier — what produces abundance.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 5. ج — JĪM
    # ──────────────────────────────────────────────────────────────────
    'ج': {
        'name': 'جِيم',
        'transliteration': 'jīm',
        'abjad': 3,
        'phonetic': {
            'makhraj': 'وَسَط اللِّسَان مَعَ الحَنَك الأَعْلَى — middle of tongue against upper palate',
            'manner': 'Voiced palatal affricate. Tongue body rises to palate, releases with friction. '
                      'The voiced partner of ش (shīn) in articulation zone.',
            'voiced': True,
            'emphatic': False,
            'description': 'Jīm is the palatal voiced affricate. Abjad 3 = the first odd number after 1. '
                           'Three = the triangle, the first stable structure. '
                           'ج roots deal with GATHERING, MAKING, COMING: '
                           'ج-ع-ل (to make/set, 345), ج-ن-ن (to conceal, 172), ج-م-ع (to gather, 129).',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الجَنَّة',
            'type': 'Voiced palatal affricate',
            'group': 'حُرُوف شَجَرِيَّة — palatal letters',
        },
        'behaviour': {
            'as_first_radical': '68 roots. Opens MAKING/GATHERING/CONCEALING: '
                                'ج-ع-ل (to make, 345), ج-ن-ن (to conceal, 172), ج-ي-أ (to come, 149), '
                                'ج-م-ع (to gather, 129). When ج opens, it BRINGS TOGETHER or MAKES.',
            'as_second_radical': 'ر-ج-ع (to return, 103), أ-ج-ر (reward, 98), و-ج-د (to find, 97), '
                                 'س-ج-د (to prostrate, 93). As core, ج is the PIVOT — the turning point.',
            'as_third_radical': 'خ-ر-ج (to exit/extract, 170), ز-و-ج (pair, 85), و-ل-ج (to enter, 21). '
                                'As closer, ج COMPLETES by gathering/joining.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'g', 'shift_id': 'S02', 'note': 'ج→g in most DS corridors (hard g)'},
            {'downstream': 'j', 'shift_id': 'S02', 'note': 'ج→j in DS05 and some Bitig corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 3258, 'distinct_roots_any': 145, 'roots_as_first': 68,
            'top5_first': [('ج-ع-ل', 345), ('ج-ن-ن', 172), ('ج-ي-أ', 149), ('ج-م-ع', 129), ('ج-ي-ء', 111)],
            'top5_second': [('ر-ج-ع', 103), ('أ-ج-ر', 98), ('و-ج-د', 97), ('س-ج-د', 93), ('و-ج-ه', 87)],
            'top5_third': [('خ-ر-ج', 170), ('ز-و-ج', 85), ('و-ل-ج', 21), ('د-ر-ج', 20), ('ح-و-ج', 16)],
            'muqattaat': [],
        },
        'semantic_tendency': 'PRESS. MAKING. CONCEALING. ARRIVAL. '
                             'ج brings things together: ج-م-ع (gather), ج-ع-ل (make/place), '
                             'ج-ن-ن (conceal = gather into hiddenness). Abjad 3 = first stable structure (triangle).',
        'paired_letters': {
            'ع (ʿayn)': 'ج-ع = making + depth (ج-ع-ل). To make something requires reaching deep.',
            'ن (nūn)': 'ج-ن = gathering + continuation (ج-ن-ن). What is concealed continues hidden.',
            'م (mīm)': 'ج-م = gathering + enclosure (ج-م-ع). To collect into a contained whole.',
        },
        'unique': 'Abjad 3. The MAKER letter. ج-ع-ل is the second most frequent verb root used for '
                  'Allah\'s creative action after خ-ل-ق. ج-ع-ل = to MAKE/SET (appoint), '
                  'خ-ل-ق = to CREATE (from nothing). '
                  'In the أَمْر system, ج = the assembler — what gathers parts into wholes.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 6. ح — ḤĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ح': {
        'name': 'حَاء',
        'transliteration': 'ḥāʾ',
        'abjad': 8,
        'phonetic': {
            'makhraj': 'وَسَط الحَلْق — middle of the throat (pharyngeal)',
            'manner': 'Voiceless pharyngeal fricative. Air passes through the constricted pharynx '
                      'without voicing. The voiceless partner of ع (ʿayn). '
                      'NO DS language has this sound — it is UNIQUE to AA.',
            'voiced': False,
            'emphatic': False,
            'description': 'Ḥāʾ is the voiceless pharyngeal. Abjad 8. '
                           'From the middle of the throat — deeper than the mouth, not as deep as hamza. '
                           'ح roots deal with TRUTH, JUDGEMENT, LIFE, BEAUTY: '
                           'ح-ق-ق (truth/binding, 263), ح-ك-م (rule/wisdom, 195), '
                           'ح-س-ن (beauty/goodness, 189), ح-ي-ي (life, 153). '
                           'The pharyngeal squeeze = PRESSURE that tests and refines.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الحَقّ',
            'type': 'Voiceless pharyngeal fricative',
            'group': 'حُرُوف الحَلْق — throat letters',
        },
        'behaviour': {
            'as_first_radical': '95 roots. Opens TRUTH/LIFE/BEAUTY/JUDGEMENT: '
                                'ح-ق-ق (truth, 263), ح-ك-م (rule, 195), ح-س-ن (good, 189), '
                                'ح-ي-ي (life, 153), ح-س-ب (reckon, 106). '
                                'When ح opens, it tests and establishes what is TRUE.',
            'as_second_radical': 'ر-ح-م (womb/mercy, 553 — MASSIVE), ص-ح-ب (companion, 97), '
                                 'و-ح-ي (revelation, 78), أ-ح-د (one/unique, 78). '
                                 'As core, ح provides the WARMTH — the pharyngeal heat that nurtures.',
            'as_third_radical': 'ص-ل-ح (righteousness, 177), س-ب-ح (glorification, 91), '
                                'ن-و-ح (Nūḥ, 48), ر-و-ح (spirit, 48). '
                                'As closer, ح seals with BREATH — the spirit exhalation.',
            'as_prefix': 'Not a standard prefix in verbal morphology.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'h', 'shift_id': 'S03', 'note': 'ح→h (weakened to plain h, pharyngeal quality lost)'},
            {'downstream': 'c', 'shift_id': 'S03', 'note': 'ح→c in some DS05 Latin corridor words'},
        ],
        'quranic_stats': {
            'tokens_any_position': 4036, 'distinct_roots_any': 193, 'roots_as_first': 95,
            'top5_first': [('ح-ق-ق', 263), ('ح-ك-م', 195), ('ح-س-ن', 189), ('ح-ي-ي', 153), ('ح-س-ب', 106)],
            'top5_second': [('ر-ح-م', 553), ('ص-ح-ب', 97), ('و-ح-ي', 78), ('أ-ح-د', 78), ('و-ح-د', 75)],
            'top5_third': [('ص-ل-ح', 177), ('س-ب-ح', 91), ('ن-و-ح', 48), ('ر-و-ح', 48), ('ص-ب-ح', 45)],
            'muqattaat': ['حم — Surahs 40,41,42,43,44,45,46 (the حم series)'],
        },
        'semantic_tendency': 'CONSTRICTION. LIFE. JUDGEMENT. BEAUTY. WARMTH. '
                             'ح is the letter of what is REAL and ALIVE. حَقّ (truth), حَيَاة (life), '
                             'حُسْن (beauty), حِكْمَة (wisdom). The pharyngeal warmth = the heat of life itself. '
                             'ر-ح-م (553 tokens) — the WOMB — is ح at its core: warmth that nurtures.',
        'paired_letters': {
            'ق (qāf)': 'ح-ق = truth + force (ح-ق-ق). What is binding and established.',
            'ك (kāf)': 'ح-ك = life + containment (ح-ك-م). Judgement = life-force contained in rules.',
            'س (sīn)': 'ح-س = warmth + flow (ح-س-ن). Beauty = warmth flowing.',
        },
        'unique': 'Abjad 8. NO DS language has ح. It collapses to h (losing pharyngeal quality) or c. '
                  'The حم muqaṭṭaʿāt series (7 surahs) = ح paired with م = warmth + enclosure. '
                  'In the أَمْر system, ح = the validator — what tests truth and establishes binding state.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 7. خ — KHĀʾ
    # ──────────────────────────────────────────────────────────────────
    'خ': {
        'name': 'خَاء',
        'transliteration': 'khāʾ',
        'abjad': 600,
        'phonetic': {
            'makhraj': 'أَدْنَى الحَلْق — nearest part of the throat to the mouth (uvular)',
            'manner': 'Voiceless uvular/velar fricative. Air passes over the raised back of tongue '
                      'near the uvula. The voiceless partner of غ (ghayn).',
            'voiced': False,
            'emphatic': False,
            'description': 'Khāʾ is the voiceless uvular fricative. Abjad 600. '
                           'From the back of the throat but nearer the mouth than ح — '
                           'it is the EXIT from the throat. خ roots deal with CREATION, EMERGENCE, EXTRACTION: '
                           'خ-ل-ق (to create, 261), خ-ر-ج (to exit/extract, 170), خ-ل-ف (to succeed, 123). '
                           'The uvular friction = passage from inner to outer.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الخَلْق',
            'type': 'Voiceless uvular fricative',
            'group': 'حُرُوف الحَلْق — throat letters (nearest the mouth)',
        },
        'behaviour': {
            'as_first_radical': '68 roots. Opens CREATION/EXTRACTION/GOODNESS: '
                                'خ-ل-ق (to create, 261), خ-ي-ر (good, 191), خ-ر-ج (to exit, 170), '
                                'خ-ل-ف (to succeed, 123), خ-و-ف (fear, 120). '
                                'When خ opens, things EMERGE into existence.',
            'as_second_radical': 'أ-خ-ر (other/latter, 250), أ-خ-ذ (to take/seize, 217), '
                                 'د-خ-ل (to enter, 120). As core, خ is the PASSAGE — through which things move.',
            'as_third_radical': 'ن-ف-خ (to blow, 20), ن-س-خ (to copy, 4). '
                                'As closer, خ opens outward — the word does not stop but breathes out.',
            'as_prefix': 'Not a standard verbal prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'k', 'shift_id': 'S11', 'note': 'خ→k (uvular friction lost, becomes velar stop)'},
            {'downstream': 'ch', 'shift_id': 'S11', 'note': 'خ→ch in Germanic DS corridors'},
            {'downstream': 'x', 'shift_id': 'S11', 'note': 'خ→x in Bitig and some DS corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 2450, 'distinct_roots_any': 100, 'roots_as_first': 68,
            'top5_first': [('خ-ل-ق', 261), ('خ-ي-ر', 191), ('خ-ر-ج', 170), ('خ-ل-ف', 123), ('خ-و-ف', 120)],
            'top5_second': [('أ-خ-ر', 250), ('أ-خ-ذ', 217), ('د-خ-ل', 120), ('أ-خ-و', 48), ('ء-خ-ذ', 45)],
            'top5_third': [('ن-ف-خ', 20), ('م-س-خ', 5), ('ن-س-خ', 4), ('ص-ر-خ', 4), ('ش-ي-خ', 4)],
            'muqattaat': [],
        },
        'semantic_tendency': 'PASSAGE. EMERGENCE. EXTRACTION. CREATION. '
                             'خ marks what COMES FORTH: خ-ل-ق (creation from nothing), '
                             'خ-ر-ج (exiting), خ-ي-ر (goodness = what emerges as best). '
                             'The uvular passage = the throat-gate between inside and outside.',
        'paired_letters': {
            'ل (lām)': 'خ-ل = emergence + flow (خ-ل-ق creation, خ-ل-ف succession). The creative flow.',
            'ر (rāʾ)': 'خ-ر = emergence + movement (خ-ر-ج exit). Moving outward.',
            'ي (yāʾ)': 'خ-ي = emergence + reach (خ-ي-ر good). What emerges and extends as best.',
        },
        'unique': 'Abjad 600. خ-ل-ق is THE Qur\'anic word for creation from nothing — '
                  'Allah as الخَالِق. Q96:1-2 uses خ-ل-ق TWICE in the first revelation. '
                  'In the أَمْر system, خ = the constructor — what brings new entities into existence.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 8. د — DĀL
    # ──────────────────────────────────────────────────────────────────
    'د': {
        'name': 'دَال',
        'transliteration': 'dāl',
        'abjad': 4,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا العُلْيَا — tongue tip against upper front teeth roots',
            'manner': 'Voiced dental plosive. Tongue tip strikes upper teeth base with voicing. '
                      'The voiced partner of ت (tāʾ). Where ت is light/voiceless, د is heavy/voiced.',
            'voiced': True,
            'emphatic': False,
            'description': 'Dāl is the voiced dental stop. Abjad 4 = stability (four corners, four directions). '
                           'د roots deal with CALLING, ENTERING, INDEBTEDNESS, NEARNESS: '
                           'د-ع-و (to call, 123), د-خ-ل (to enter, 120), د-ي-ن (accountability, 113). '
                           'The voiced dental = DEFINITE impact (stronger than ت).',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الدِّين',
            'type': 'Voiced dental plosive',
            'group': 'حُرُوف أَسَلِيَّة — tongue-tip letters',
        },
        'behaviour': {
            'as_first_radical': '48 roots. Opens CALLING/ENTERING/ACCOUNTABILITY: '
                                'د-و-ن (below/beneath, 155), د-ع-و (to call, 123), '
                                'د-خ-ل (to enter, 120), د-ي-ن (system of accountability, 113). '
                                'When د opens, it CALLS or ESTABLISHES position.',
            'as_second_radical': 'ه-د-ي (guidance, 259), ص-د-ق (truth/sincerity, 149), '
                                 'ق-د-ر (measure/decree, 132). As core, د provides WEIGHT — '
                                 'the definite impact that makes guidance, truth, and decree REAL.',
            'as_third_radical': 'ع-ب-د (to devote, 265), ب-ع-د (distance, 236), '
                                'ر-و-د (to seek/intend, 159), ش-ه-د (to witness, 158). '
                                'As closer, د ANCHORS — the voiced dental pins the word down.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'd', 'shift_id': 'S19', 'note': 'Preserved as d in most corridors'},
            {'downstream': 't', 'shift_id': 'S19', 'note': 'د→t devoicing in some DS corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 5204, 'distinct_roots_any': 223, 'roots_as_first': 48,
            'top5_first': [('د-و-ن', 155), ('د-ع-و', 123), ('د-خ-ل', 120), ('د-ي-ن', 113), ('د-ن-ي', 110)],
            'top5_second': [('ه-د-ي', 259), ('ص-د-ق', 149), ('ق-د-ر', 132), ('ي-د-ي', 106), ('ش-د-د', 93)],
            'top5_third': [('ع-ب-د', 265), ('ب-ع-د', 236), ('ر-و-د', 159), ('ش-ه-د', 158), ('و-ع-د', 139)],
            'muqattaat': [],
        },
        'semantic_tendency': 'KNOCK. POSITION. ACCOUNTABILITY. ANCHORING. '
                             'د establishes WHERE something is: د-و-ن (below), د-خ-ل (inside), '
                             'د-ن-ي (near/low). And it establishes OBLIGATION: د-ي-ن (the system of accounts). '
                             'Abjad 4 = four directions = establishing position in space.',
        'paired_letters': {
            'ع (ʿayn)': 'د-ع = calling + depth (د-ع-و). To call from deep within.',
            'ي (yāʾ)': 'د-ي = position + reach (د-ي-ن). The system that extends accountability.',
            'خ (khāʾ)': 'د-خ = position + passage (د-خ-ل). Entering = establishing position through a passage.',
        },
        'unique': 'Abjad 4. د-ي-ن is THE USLaP concept — the system of accountability. '
                  'Q1:4 مَالِكِ يَوْمِ الدِّينِ — Master of the Day of الدِّين. '
                  'In the أَمْر system, د = the pointer — what establishes position and reference.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 9. ذ — DHĀL
    # ──────────────────────────────────────────────────────────────────
    'ذ': {
        'name': 'ذَال',
        'transliteration': 'dhāl',
        'abjad': 700,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أَطْرَاف الثَّنَايَا العُلْيَا — tongue tip between teeth',
            'manner': 'Voiced interdental fricative. Tongue protrudes between teeth with voicing. '
                      'The voiced partner of ث (thāʾ).',
            'voiced': True,
            'emphatic': False,
            'description': 'Dhāl is the voiced interdental. Abjad 700. '
                           'ذ roots deal with CONTACT, TASTING, GOING: '
                           'ذ-ك-ر (to mention/remember, 286), ذ-و-ق (to taste, 58), ذ-ه-ب (to go, 56). '
                           'The voiced interdental = an ACTIVE protrusion — reaching out to experience.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الذِّكْر',
            'type': 'Voiced interdental fricative',
            'group': 'حُرُوف لَثَوِيَّة — interdental letters',
        },
        'behaviour': {
            'as_first_radical': '21 roots. Opens CONTACT/EXPERIENCE: '
                                'ذ-ك-ر (to remember/mention, 286), ذ-و-ق (to taste, 58), '
                                'ذ-ه-ب (to go, 56), ذ-ن-ب (sin/fault, 38). '
                                'When ذ opens, it REACHES OUT to experience or recall.',
            'as_second_radical': 'ع-ذ-ب (denial of sweetness, 373), ك-ذ-ب (to deny, 282), '
                                 'ن-ذ-ر (to warn, 134), أ-ذ-ن (permission, 74). '
                                 'As core, ذ provides SENSATION — the experience-contact.',
            'as_third_radical': 'أ-خ-ذ (to take/seize, 217), ل-و-ذ (to take refuge, 27). '
                                'As closer, ذ trails with voiced interdental friction — the word lingers.',
            'as_prefix': 'ذُو / ذَا / ذِي = possessor/owner (ذُو العَرْشِ = Owner of the Throne).',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'th', 'shift_id': 'S12', 'note': 'ذ→th voiced (as in English "this")'},
            {'downstream': 'd', 'shift_id': 'S12', 'note': 'ذ→d in most DS corridors (interdental lost)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1896, 'distinct_roots_any': 49, 'roots_as_first': 21,
            'top5_first': [('ذ-ك-ر', 286), ('ذ-و-ق', 58), ('ذ-ه-ب', 56), ('ذ-ن-ب', 38), ('ذ-ر-ر', 25)],
            'top5_second': [('ع-ذ-ب', 373), ('ك-ذ-ب', 282), ('ن-ذ-ر', 134), ('أ-ذ-ن', 74), ('أ-ذ-ي', 47)],
            'top5_third': [('أ-خ-ذ', 217), ('ء-خ-ذ', 45), ('ل-و-ذ', 27), ('ع-و-ذ', 17), ('ن-ب-ذ', 10)],
            'muqattaat': [],
        },
        'semantic_tendency': 'EXTENSION. TASTING. EXPERIENCE. SENSATION. '
                             'ذ is the letter of DIRECT CONTACT with reality: ذ-ك-ر (active contact/mention), '
                             'ذ-و-ق (tasting = direct sensory contact). The tongue protrudes between teeth '
                             'to TOUCH — ذ is the letter of touching reality.',
        'paired_letters': {
            'ك (kāf)': 'ذ-ك = experience + containment (ذ-ك-ر). Remembrance = containing experience.',
            'و (wāw)': 'ذ-و = experience + connection (ذ-و-ق). Tasting = connecting through experience.',
            'ه (hāʾ)': 'ذ-ه = experience + breath (ذ-ه-ب). Going = experiencing departure.',
        },
        'unique': 'Abjad 700. ذ-ك-ر (286 tokens) is the Qur\'anic concept of ACTIVE CONTACT — '
                  'not passive recall but PRESENT BIDIRECTIONAL MENTION. Q2:152 فَاذْكُرُونِي أَذْكُرْكُمْ. '
                  'In the أَمْر system, ذ = the contact initiator — tongue reaches out between teeth to TOUCH reality.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 10. ر — RĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ر': {
        'name': 'رَاء',
        'transliteration': 'rāʾ',
        'abjad': 200,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان قَرِيبًا مِنَ اللِّثَة — tongue tip near the gums (alveolar)',
            'manner': 'Voiced alveolar trill/tap. Tongue tip vibrates against the alveolar ridge. '
                      'The MOST resistant consonant — survives in almost ALL DS corridors.',
            'voiced': True,
            'emphatic': False,
            'description': 'Rāʾ is the alveolar trill. Abjad 200. '
                           'The VIBRATING letter — the tongue REPEATS its contact. '
                           'ر roots are the HIGHEST-frequency family: ر-ب-ب (nurturing, 907), '
                           'ر-ح-م (womb, 553), ر-س-ل (sending, 509). '
                           'ر = MOVEMENT, FLOW, REPETITION. It is the letter of PROCESS.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الرَّحْمَٰن',
            'type': 'Voiced alveolar trill/tap (liquid)',
            'group': 'حُرُوف ذَلْقِيَّة — tongue-tip letters (liquids)',
        },
        'behaviour': {
            'as_first_radical': '90 roots. Opens NURTURING/SENDING/MERCY: '
                                'ر-ب-ب (nurturing, 907), ر-ح-م (womb, 553), ر-س-ل (sending, 509). '
                                'When ر opens, it initiates SUSTAINED PROCESS — vibration that continues.',
            'as_second_radical': 'أ-ر-ض (earth, 465), خ-ر-ج (exit, 170), ش-ر-ك (sharing, 149). '
                                 'As core, ر provides the MOVEMENT — the oscillating energy at the root\'s heart.',
            'as_third_radical': 'ك-ف-ر (covering, 487), ذ-ك-ر (remembering, 286), '
                                'أ-خ-ر (other, 250), غ-ف-ر (shielding, 231), أ-م-ر (commanding, 223). '
                                'As closer, ر CONTINUES — the trill does not stop abruptly.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'r', 'shift_id': 'S15', 'note': 'ر→r (nearly always preserved — highest resistance)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 12268, 'distinct_roots_any': 439, 'roots_as_first': 90,
            'top5_first': [('ر-ب-ب', 907), ('ر-ح-م', 553), ('ر-س-ل', 509), ('ر-و-د', 159), ('ر-أ-ي', 135)],
            'top5_second': [('أ-ر-ض', 465), ('خ-ر-ج', 170), ('ش-ر-ك', 149), ('و-ر-ي', 94), ('ق-ر-ب', 93)],
            'top5_third': [('ك-ف-ر', 487), ('ذ-ك-ر', 286), ('أ-خ-ر', 250), ('غ-ف-ر', 231), ('أ-م-ر', 223)],
            'muqattaat': ['الر — Surahs 10,11,12,14,15. المر — Surah 13'],
        },
        'semantic_tendency': 'MOVEMENT. PROCESS. FLOW. NURTURING. REPETITION. '
                             'ر = the vibrating letter. 12,268 tokens, 439 roots — the MOST connected letter. '
                             'Every process-word has ر: nurturing (ر-ب-ب), mercy (ر-ح-م), sending (ر-س-ل), '
                             'returning (ر-ج-ع). The trill = repeated contact = ongoing process.',
        'paired_letters': {
            'ب (bāʾ)': 'ر-ب = flow + building (ر-ب-ب). Nurturing = sustained building. THE highest root.',
            'ح (ḥāʾ)': 'ر-ح = flow + warmth (ر-ح-م). The womb = flowing warmth. 553 tokens.',
            'س (sīn)': 'ر-س = flow + streaming (ر-س-ل). Sending = flowing outward.',
        },
        'unique': 'Abjad 200. THE most connected letter in the entire Qur\'an — 439 distinct roots, '
                  '12,268 tokens. ر-ب-ب (907) is the root of رَبّ (the Nurturer). '
                  'The trill = the only consonant that inherently REPEATS itself. '
                  'In the أَمْر system, ر = the process runner — what executes continuously.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 11. ز — ZĀY
    # ──────────────────────────────────────────────────────────────────
    'ز': {
        'name': 'زَاي',
        'transliteration': 'zāy',
        'abjad': 7,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا السُّفْلَى — tongue tip near lower front teeth',
            'manner': 'Voiced alveolar fricative. Air passes through narrow channel between tongue '
                      'tip and alveolar ridge with voicing. The voiced partner of س (sīn).',
            'voiced': True,
            'emphatic': False,
            'description': 'Zāy is the voiced sibilant. Abjad 7 = THE number (seven heavens, seven earths, '
                           'seven circuits, heptad structure). ز roots deal with PAIRING, GROWTH, ADORNMENT: '
                           'ز-و-ج (pair, 85), ز-ك-و (purification/growth, 59), ز-ي-ن (adornment, 47). '
                           'The buzzing voiced sibilant = ENERGY that pairs and purifies.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الزَّوْج',
            'type': 'Voiced alveolar fricative (sibilant)',
            'group': 'حُرُوف صَفِيرِيَّة — whistling/sibilant letters',
        },
        'behaviour': {
            'as_first_radical': '38 roots. Opens PAIRING/GROWTH/PURIFICATION: '
                                'ز-و-ج (pair, 85), ز-ك-و (purification, 59), ز-ي-ن (adornment, 47), '
                                'ز-ي-د (increase, 31). When ز opens, it PAIRS or GROWS.',
            'as_second_radical': 'ن-ز-ل (to descend/reveal, 293), ر-ز-ق (provision, 121), '
                                 'ع-ز-ز (might, 118). As core, ز provides ENERGY — the buzzing force.',
            'as_third_radical': 'ع-ز-ز (might, 118), ف-و-ز (triumph, 26), ع-ج-ز (inability, 26). '
                                'As closer, ز BUZZES — the word ends with resonant energy.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'z', 'shift_id': 'S22', 'note': 'ز→z (preserved)'},
            {'downstream': 's', 'shift_id': 'S22', 'note': 'ز→s (devoicing — loses the buzzing quality)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1462, 'distinct_roots_any': 101, 'roots_as_first': 38,
            'top5_first': [('ز-و-ج', 85), ('ز-ك-و', 59), ('ز-ي-ن', 47), ('ز-ي-د', 31), ('ز-و-د', 23)],
            'top5_second': [('ن-ز-ل', 293), ('ر-ز-ق', 121), ('ع-ز-ز', 118), ('ج-ز-ي', 69), ('ج-ز-أ', 45)],
            'top5_third': [('ع-ز-ز', 118), ('ف-و-ز', 26), ('ع-ج-ز', 26), ('ر-ج-ز', 10), ('ك-ن-ز', 9)],
            'muqattaat': [],
        },
        'semantic_tendency': 'BUZZ. PURIFICATION. GROWTH. ENERGY. '
                             'ز is the letter of DUALITY MADE PRODUCTIVE: ز-و-ج (pair), ز-ك-و (purify = grow clean), '
                             'ز-ي-ن (adorn = add beauty). Abjad 7 = the heptad number = completeness through pairing.',
        'paired_letters': {
            'و (wāw)': 'ز-و = energy + connection (ز-و-ج pair). Two connected with energy = a productive pair.',
            'ك (kāf)': 'ز-ك = energy + containment (ز-ك-و). Purification = contained growth energy.',
            'ي (yāʾ)': 'ز-ي = energy + extension (ز-ي-ن adorn, ز-ي-د increase). Energy extending outward.',
        },
        'unique': 'Abjad 7. THE heptad letter. Every heptad in the lattice sums to 462 = 7 × 66 = 7 × Allah. '
                  'ز-و-ج (pair) is the Qur\'anic structure of creation: everything in pairs (Q36:36, Q51:49). '
                  'In the أَمْر system, ز = the pair operator — what creates matched/coupled structures.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 12. س — SĪN
    # ──────────────────────────────────────────────────────────────────
    'س': {
        'name': 'سِين',
        'transliteration': 'sīn',
        'abjad': 60,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا السُّفْلَى — tongue tip near lower teeth',
            'manner': 'Voiceless alveolar fricative. Air streams through narrow channel. '
                      'The voiceless partner of ز (zāy). The NON-emphatic partner of ص (ṣād).',
            'voiced': False, 'emphatic': False,
            'description': 'Sīn is the voiceless sibilant. Abjad 60. '
                           'STREAMING air — the hissing sound of things FLOWING. '
                           'س roots: س-م-و (elevation, 457), س-م-ع (hearing, 197), '
                           'س-ب-ل (a path, 177), س-ل-م (peace/wholeness, 148). '
                           'The streaming sibilant = CONTINUOUS FLOW.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: السَّمَاء',
            'type': 'Voiceless alveolar fricative (sibilant)',
            'group': 'حُرُوف صَفِيرِيَّة — whistling/sibilant letters',
        },
        'behaviour': {
            'as_first_radical': '108 roots — second most prolific opener. '
                                'س-م-و (elevation/sky, 457), س-م-ع (hearing, 197), '
                                'س-ب-ل (path, 177), س-و-أ (wrongdoing, 150), س-ل-م (peace, 148). '
                                'When س opens, things STREAM or FLOW.',
            'as_second_radical': 'ر-س-ل (sending, 509), ح-س-ن (beauty, 189), '
                                 'ح-س-ب (reckoning, 106). As core, س is the CHANNEL — the flowing middle.',
            'as_third_radical': 'ن-ف-س (self/soul, 296), أ-ن-س (humanity, 263). '
                                'As closer, س hisses away — the word trails into breath.',
            'as_prefix': 'سَـ = near future marker (سَيَعْلَمُونَ = they will soon know). '
                         'The سين of futurity — what is COMING.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 's', 'shift_id': 'S21', 'note': 'Preserved as s'},
            {'downstream': 'c', 'shift_id': 'S21', 'note': 'س→c before front vowels in DS05 Latin'},
            {'downstream': 'z', 'shift_id': 'S21', 'note': 'س→z (voicing) in some corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 5429, 'distinct_roots_any': 232, 'roots_as_first': 108,
            'top5_first': [('س-م-و', 457), ('س-م-ع', 197), ('س-ب-ل', 177), ('س-و-أ', 150), ('س-ل-م', 148)],
            'top5_second': [('ر-س-ل', 509), ('ح-س-ن', 189), ('ح-س-ب', 106), ('خ-س-ر', 65), ('ن-س-أ', 60)],
            'top5_third': [('ن-ف-س', 296), ('أ-ن-س', 263), ('م-و-س', 105), ('ل-ي-س', 59), ('ن-و-س', 56)],
            'muqattaat': ['يس — Surah 36. طس — Surah 27. طسم — Surahs 26,28'],
        },
        'semantic_tendency': 'FLOW. STREAMING. ELEVATION. PATH. '
                             'س is the letter of things that MOVE CONTINUOUSLY: sky (س-م-و), '
                             'path (س-ب-ل), peace (س-ل-م = wholeness flowing). '
                             'As future prefix (سَـ), it marks what FLOWS toward you.',
        'paired_letters': {
            'م (mīm)': 'س-م = stream + enclosure (س-م-و sky, س-م-ع hearing). The sky = streaming enclosure above.',
            'ل (lām)': 'س-ل = stream + flow (س-ل-م peace). Peace = streaming flow.',
            'ب (bāʾ)': 'س-ب = stream + building (س-ب-ل path). A path = a built stream for travel.',
        },
        'unique': 'Abjad 60. Second most prolific opener (108 roots). '
                  'The future prefix سَـ makes س the letter of ANTICIPATION. '
                  'In the أَمْر system, س = the stream — data flow, I/O channel, pipeline.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 13. ش — SHĪN
    # ──────────────────────────────────────────────────────────────────
    'ش': {
        'name': 'شِين',
        'transliteration': 'shīn',
        'abjad': 300,
        'phonetic': {
            'makhraj': 'وَسَط اللِّسَان مَعَ الحَنَك — middle tongue against palate',
            'manner': 'Voiceless palatal fricative. Broad air flow over flattened tongue. '
                      'The voiceless partner of ج (jīm) in articulation zone.',
            'voiced': False, 'emphatic': False,
            'description': 'Shīn is the voiceless palatal fricative. Abjad 300. '
                           'WIDE dispersal — air spreads across the palate (unlike the narrow channel of س). '
                           'ش roots: ش-ي-أ (a thing, 355), ش-ه-د (to witness, 158), '
                           'ش-ر-ك (to share, 149). ش = SPREADING, DISPERSAL, SHARING.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الشَّمْس',
            'type': 'Voiceless palatal fricative',
            'group': 'حُرُوف شَجَرِيَّة — palatal letters',
        },
        'behaviour': {
            'as_first_radical': '62 roots. Opens THINGS/WITNESSING/SHARING: '
                                'ش-ي-أ (a thing, 355), ش-ه-د (to witness, 158), ش-ر-ك (to share, 149). '
                                'When ش opens, it SPREADS or EXPOSES.',
            'as_second_radical': 'ب-ش-ر (humanity/glad tidings, 124), خ-ش-ي (to fear, 45). '
                                 'As core, ش provides DISPERSAL — the wide spreading.',
            'as_third_radical': 'ع-ر-ش (throne, 31), ف-ح-ش (obscenity, 17). '
                                'As closer, ش DISSIPATES — the word spreads and fades.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'sh', 'shift_id': 'S05', 'note': 'Preserved as sh'},
            {'downstream': 's', 'shift_id': 'S05', 'note': 'ش→s (narrowing — loses palatal width)'},
            {'downstream': 's / sh', 'shift_id': 'S-SIB-SH', 'note': 'Sibilant-palatalization interchange'},
        ],
        'quranic_stats': {
            'tokens_any_position': 2088, 'distinct_roots_any': 99, 'roots_as_first': 62,
            'top5_first': [('ش-ي-أ', 355), ('ش-ه-د', 158), ('ش-ي-ء', 151), ('ش-ر-ك', 149), ('ش-د-د', 93)],
            'top5_second': [('ب-ش-ر', 124), ('خ-ش-ي', 45), ('ح-ش-ر', 41), ('ع-ش-ر', 25), ('م-ش-ي', 23)],
            'top5_third': [('ع-ر-ش', 31), ('ف-ح-ش', 17), ('ب-ط-ش', 10), ('ن-و-ش', 6), ('ف-ر-ش', 6)],
            'muqattaat': [],
        },
        'semantic_tendency': 'SPREADING. THINGNESS. WITNESSING. SHARING. '
                             'ش is the letter of DISPERSAL: ش-ي-أ (thing = entity spread in existence), '
                             'ش-ه-د (witness = perception spread across reality), ش-ر-ك (sharing = spreading ownership).',
        'paired_letters': {
            'ي (yāʾ)': 'ش-ي = spreading + extension (ش-ي-أ thing). A thing = what extends spread in existence.',
            'ه (hāʾ)': 'ش-ه = spreading + breath (ش-ه-د witness). To witness = to breathe in the spread reality.',
            'ر (rāʾ)': 'ش-ر = spreading + flow (ش-ر-ك sharing). To share = spreading flow among many.',
        },
        'unique': 'Abjad 300. ش-ي-أ (355 tokens) is how the Qur\'an says THING — any entity. '
                  'Q36:82 إِنَّمَا أَمْرُهُ إِذَا أَرَادَ شَيْئًا أَن يَقُولَ لَهُ كُن فَيَكُونُ — '
                  'His أَمْر when He intends a شَيْء is to say كُن. '
                  'In the أَمْر system, ش = the object type — entities spread in the system.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 14. ص — ṢĀD
    # ──────────────────────────────────────────────────────────────────
    'ص': {
        'name': 'صَاد',
        'transliteration': 'ṣād',
        'abjad': 90,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا السُّفْلَى — tongue tip near lower teeth',
            'manner': 'Voiceless emphatic alveolar fricative. Same position as س but with '
                      'tongue body raised toward the palate (تَفْخِيم). '
                      'The EMPHATIC partner of س. Heavier, deeper, more forceful.',
            'voiced': False, 'emphatic': True,
            'description': 'Ṣād is the emphatic sibilant. Abjad 90. '
                           'Same air-stream as س but with WEIGHT — the tongue body presses upward. '
                           'ص roots: ص-ل-ح (righteousness, 177), ص-د-ق (truth, 149), '
                           'ص-ب-ر (endurance, 102). ص = TRUTH UNDER PRESSURE — what holds when tested.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الصَّبْر',
            'type': 'Voiceless emphatic alveolar fricative',
            'group': 'حُرُوف صَفِيرِيَّة — whistling/sibilant letters (emphatic)',
        },
        'behaviour': {
            'as_first_radical': '64 roots. Opens RIGHTEOUSNESS/TRUTH/ENDURANCE: '
                                'ص-ل-ح (righteousness, 177), ص-د-ق (truth, 149), ص-ب-ر (patience, 102). '
                                'When ص opens, it declares what is TRUE AND WEIGHTY.',
            'as_second_radical': 'ن-ص-ر (help/victory, 111), ب-ص-ر (vision, 100), ف-ص-ل (separation, 40). '
                                 'As core, ص provides FORCE — the emphatic weight of certainty.',
            'as_third_radical': 'خ-ل-ص (purity, 31), ق-ص-ص (narration, 23). '
                                'As closer, ص seals with AUTHORITY — heavy, definitive.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 's', 'shift_id': 'S13', 'note': 'ص→s (emphasis lost — flattened to plain s)'},
            {'downstream': 'c', 'shift_id': 'S13', 'note': 'ص→c in DS05 Latin corridor'},
            {'downstream': 'z', 'shift_id': 'S13', 'note': 'ص→z (voiced + de-emphasized)'},
            {'downstream': 'ص→s retention', 'shift_id': 'S-SIB-E', 'note': 'Emphatic sibilant preserved as s'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1957, 'distinct_roots_any': 122, 'roots_as_first': 64,
            'top5_first': [('ص-ل-ح', 177), ('ص-د-ق', 149), ('ص-ب-ر', 102), ('ص-ي-ر', 97), ('ص-ح-ب', 97)],
            'top5_second': [('ن-ص-ر', 111), ('ب-ص-ر', 100), ('ف-ص-ل', 40), ('و-ص-د', 38), ('و-ص-ي', 33)],
            'top5_third': [('خ-ل-ص', 31), ('ق-ص-ص', 23), ('ن-ق-ص', 16), ('ح-ي-ص', 9), ('ر-ب-ص', 8)],
            'muqattaat': ['ص — Surah 38. المص — Surah 7. كهيعص — Surah 19'],
        },
        'semantic_tendency': 'HEAVY STREAM. ENDURANCE. RIGHTEOUSNESS. WEIGHT. '
                             'ص is the emphatic س — what stands under PRESSURE. '
                             'ص-د-ق (truth = what holds firm), ص-ب-ر (patience = enduring weight), '
                             'ص-ل-ح (righteousness = corrected under pressure).',
        'paired_letters': {
            'ل (lām)': 'ص-ل = weight + flow (ص-ل-ح righteousness). Heavy flow = righteous conduct.',
            'د (dāl)': 'ص-د = weight + anchor (ص-د-ق truth). Weighted and anchored = truth.',
            'ب (bāʾ)': 'ص-ب = weight + building (ص-ب-ر patience). Built under weight = endurance.',
        },
        'unique': 'Abjad 90. ص appears as a standalone muqaṭṭaʿa (Surah 38). '
                  'ص-ر-ط (الصِّرَاط = THE path) — the emphatic path, the one with weight and authority. '
                  'In the أَمْر system, ص = the assertion — what declares truth with authority.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 15. ض — ḌĀD
    # ──────────────────────────────────────────────────────────────────
    'ض': {
        'name': 'ضَاد',
        'transliteration': 'ḍād',
        'abjad': 800,
        'phonetic': {
            'makhraj': 'حَافَّة اللِّسَان مَعَ الأَضْرَاس — side of tongue against molars',
            'manner': 'Voiced emphatic lateral fricative. Air passes along the SIDE of the tongue. '
                      'The ONLY letter in AA articulated from the side. Unique to AA — '
                      'لُغَة الضَّاد (the language of ḍād).',
            'voiced': True, 'emphatic': True,
            'description': 'Ḍād is the DEFINING letter of AA. Abjad 800. '
                           'NO other language in history has this sound. '
                           'ض roots: ض-ل-ل (going astray/displacement, 172), ض-ر-ب (striking, 56), '
                           'ض-ع-ف (weakness, 49). ض = DISPLACEMENT, WRONG POSITION. '
                           'The lateral articulation = SIDEWAYS motion = off the straight path.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الضَّلَال',
            'type': 'Voiced emphatic lateral fricative',
            'group': 'UNIQUE — no group. ض is the only lateral fricative.',
        },
        'behaviour': {
            'as_first_radical': '25 roots. Opens DISPLACEMENT/STRIKING/WEAKNESS: '
                                'ض-ل-ل (displacement, 172), ض-ر-ب (striking, 56), ض-ع-ف (weakness, 49). '
                                'When ض opens, something is DISPLACED or STRUCK.',
            'as_second_radical': 'ف-ض-ل (excellence, 106), ق-ض-ي (decree, 57), و-ض-ع (placing, 26). '
                                 'As core, ض is the FORCE — lateral pressure that distinguishes or displaces.',
            'as_third_radical': 'أ-ر-ض (earth, 465 — MASSIVE), ب-ع-ض (some/part, 97), '
                                'ع-ر-ض (width, 79). As closer, ض GROUNDS — the heavy lateral stops the word firmly.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'd', 'shift_id': 'S06', 'note': 'ض→d (lateral quality lost entirely)'},
            {'downstream': 'th', 'shift_id': 'S06', 'note': 'ض→th in some DS corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1601, 'distinct_roots_any': 79, 'roots_as_first': 25,
            'top5_first': [('ض-ل-ل', 172), ('ض-ر-ب', 56), ('ض-ع-ف', 49), ('ض-و-أ', 34), ('ض-ر-ر', 34)],
            'top5_second': [('ف-ض-ل', 106), ('ق-ض-ي', 57), ('و-ض-ع', 26), ('ح-ض-ر', 25), ('غ-ض-ب', 24)],
            'top5_third': [('أ-ر-ض', 465), ('ب-ع-ض', 97), ('ع-ر-ض', 79), ('ر-و-ض', 47), ('م-ر-ض', 28)],
            'muqattaat': [],
        },
        'semantic_tendency': 'EDGE. STRIKING. GROUNDING. THE DEFINITIVE LETTER. '
                             'ض = what is OFF PATH or what FORCES distinction. ض-ل-ل (astray = displaced), '
                             'but also أ-ر-ض (earth = the GROUND itself, 465 tokens). '
                             'The lateral letter DEFINES AA — no imitation possible.',
        'paired_letters': {
            'ل (lām)': 'ض-ل = displacement + flow (ض-ل-ل). Going astray = flowing off path.',
            'ر (rāʾ)': 'ض-ر = force + process (ض-ر-ب). Striking = forced process.',
            'ع (ʿayn)': 'ض-ع = force + depth (ض-ع-ف). Weakness = deep force deficit.',
        },
        'unique': 'Abjad 800. THE letter that DEFINES AA (لُغَة الضَّاد). '
                  'UNIQUE in human phonetics — no other language has a voiced emphatic lateral fricative. '
                  'أَرْض (Layer 3 of the أَمْر system) ends with ض — the OS kernel is grounded in THE defining letter. '
                  'In the أَمْر system, ض = the exception handler — what catches displacement/error.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 16. ط — ṬĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ط': {
        'name': 'طَاء',
        'transliteration': 'ṭāʾ',
        'abjad': 9,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا العُلْيَا — tongue tip against upper teeth roots',
            'manner': 'Voiceless emphatic dental plosive. Same position as ت but with '
                      'tongue body raised (تَفْخِيم). The EMPHATIC partner of ت. '
                      'Heavy, authoritative, commanding.',
            'voiced': False, 'emphatic': True,
            'description': 'Ṭāʾ is the emphatic dental stop. Abjad 9. '
                           'The HEAVY ت — where ت is light succession, ط is COMMANDING authority. '
                           'ط roots: ط-و-ع (obedience, 111), ط-ع-م (food, 50), ط-ي-ب (pure/good, 49). '
                           'The emphatic dental = AUTHORITATIVE impact.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الطَّاعَة',
            'type': 'Voiceless emphatic dental plosive',
            'group': 'حُرُوف أَسَلِيَّة — tongue-tip letters (emphatic)',
        },
        'behaviour': {
            'as_first_radical': '37 roots. Opens OBEDIENCE/PURITY/AUTHORITY: '
                                'ط-و-ع (obedience, 111), ط-ع-م (food/provision, 50), '
                                'ط-ي-ب (pure/good, 49), ط-و-ف (circling, 36), ط-غ-ي (transgression, 35). '
                                'When ط opens, it marks AUTHORITY — either obeyed (ط-و-ع) or transgressed (ط-غ-ي).',
            'as_second_radical': 'ش-ط-ن (adversary, 88), ق-ط-ع (cutting, 35), ب-ط-ل (falsehood, 33). '
                                 'As core, ط provides FORCE OF AUTHORITY.',
            'as_third_radical': 'ص-ر-ط (the path, 45), س-ل-ط (authority, 36), ل-و-ط (Lūṭ, 28). '
                                'As closer, ط STAMPS — definitive, authoritative closure.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 't', 'shift_id': 'S04', 'note': 'ط→t (emphasis lost — flattened to plain t)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1205, 'distinct_roots_any': 109, 'roots_as_first': 37,
            'top5_first': [('ط-و-ع', 111), ('ط-ع-م', 50), ('ط-ي-ب', 49), ('ط-و-ف', 36), ('ط-غ-ي', 35)],
            'top5_second': [('ش-ط-ن', 88), ('ق-ط-ع', 35), ('ب-ط-ل', 33), ('ب-ط-ن', 19), ('ف-ط-ر', 18)],
            'top5_third': [('ص-ر-ط', 45), ('س-ل-ط', 36), ('ل-و-ط', 28), ('ق-س-ط', 25), ('ح-و-ط', 25)],
            'muqattaat': ['طه — Surah 20. طس — Surah 27. طسم — Surahs 26,28'],
        },
        'semantic_tendency': 'SEAL. OBEDIENCE. PURITY. COMMAND. '
                             'ط is the letter of SOVEREIGN FORCE: ط-و-ع (submit to authority), '
                             'ط-ي-ب (pure = meeting the authority\'s standard), ط-غ-ي (transgress authority). '
                             'Abjad 9 = completion of single digits.',
        'paired_letters': {
            'و (wāw)': 'ط-و = authority + connection (ط-و-ع obedience). Submitting = connecting to authority.',
            'ع (ʿayn)': 'ط-ع = authority + depth (ط-ع-م food). Nourishment = authority reaching deep.',
            'ي (yāʾ)': 'ط-ي = authority + extension (ط-ي-ب pure). Purity = authority extended.',
        },
        'unique': 'Abjad 9. The emphatic ت. طه is one of the Qur\'anic muqaṭṭaʿāt (Surah 20). '
                  'الصِّرَاطَ الْمُسْتَقِيمَ (Q1:6) ends with ط — the STRAIGHT path is stamped with authority. '
                  'In the أَمْر system, ط = the permission gate — the authority check.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 17. ظ — ẒĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ظ': {
        'name': 'ظَاء',
        'transliteration': 'ẓāʾ',
        'abjad': 900,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ أَطْرَاف الثَّنَايَا العُلْيَا — tongue tip between teeth',
            'manner': 'Voiced emphatic interdental fricative. Tongue protrudes between teeth '
                      'with emphasis (tongue body raised). The EMPHATIC partner of ذ (dhāl).',
            'voiced': True, 'emphatic': True,
            'description': 'Ẓāʾ is the emphatic interdental. Abjad 900 — highest single-letter abjad '
                           'except غ (1000). ظ roots: ظ-ل-م (displacement/darkness, 315), '
                           'ظ-ن-ن (assumption, 62), ظ-ه-ر (appearing/manifest, 58). '
                           'The heavy interdental = WHAT APPEARS or WHAT IS DISPLACED.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: الظُّلْم',
            'type': 'Voiced emphatic interdental fricative',
            'group': 'حُرُوف لَثَوِيَّة — interdental letters (emphatic)',
        },
        'behaviour': {
            'as_first_radical': '7 roots — the RAREST opener. ظ-ل-م (displacement, 315), '
                                'ظ-ن-ن (assumption, 62), ظ-ه-ر (manifesting, 58). '
                                'When ظ opens, it marks the HEAVIEST concepts: oppression, assumption, manifestation.',
            'as_second_radical': 'ن-ظ-ر (looking, 128), ع-ظ-م (greatness, 128). '
                                 'As core, ظ provides MAGNITUDE — what is great and visible.',
            'as_third_radical': 'ح-ف-ظ (preservation, 37), و-ع-ظ (admonition, 24), غ-ل-ظ (harshness, 13). '
                                'As closer, ظ seals with WEIGHT AND EXPOSURE.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'z', 'shift_id': 'S25', 'note': 'ظ→z (emphatic interdental → plain fricative)'},
            {'downstream': 'th', 'shift_id': 'S25', 'note': 'ظ→th (emphatic quality lost)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 833, 'distinct_roots_any': 21, 'roots_as_first': 7,
            'top5_first': [('ظ-ل-م', 315), ('ظ-ن-ن', 62), ('ظ-ه-ر', 58), ('ظ-ل-ل', 30), ('ظ-م-أ', 3)],
            'top5_second': [('ن-ظ-ر', 128), ('ع-ظ-م', 128), ('ح-ظ-ظ', 7), ('ك-ظ-م', 6), ('ل-ظ-ي', 3)],
            'top5_third': [('ح-ف-ظ', 37), ('و-ع-ظ', 24), ('غ-ل-ظ', 13), ('غ-ي-ظ', 10), ('ح-ظ-ظ', 7)],
            'muqattaat': [],
        },
        'semantic_tendency': 'HEAVY CONTACT. APPEARANCE. MAGNITUDE. HEAVINESS. '
                             'ظ marks what is OUT OF PLACE or what is MASSIVE: '
                             'ظ-ل-م (315 — placing in wrong position), ع-ظ-م (greatness), '
                             'ظ-ه-ر (manifestation = becoming visible/apparent).',
        'paired_letters': {
            'ل (lām)': 'ظ-ل = magnitude + flow (ظ-ل-م displacement). Wrong-flowing = oppression.',
            'ن (nūn)': 'ظ-ن = magnitude + continuation (ظ-ن-ن assumption). Assumed magnitude.',
            'ه (hāʾ)': 'ظ-ه = magnitude + breath (ظ-ه-ر manifesting). Breathing into visibility.',
        },
        'unique': 'Abjad 900. Only 7 roots as opener — the RAREST first radical. '
                  'But ظ-ل-م alone has 315 tokens — the concept of DISPLACEMENT is massive. '
                  'In the أَمْر system, ظ = the error state — displacement from correct position.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 18. ع — ʿAYN
    # ──────────────────────────────────────────────────────────────────
    'ع': {
        'name': 'عَيْن',
        'transliteration': 'ʿayn',
        'abjad': 70,
        'phonetic': {
            'makhraj': 'وَسَط الحَلْق — middle of the throat (pharyngeal)',
            'manner': 'Voiced pharyngeal fricative. The throat constricts with voicing. '
                      'The voiced partner of ح (ḥāʾ). NO DS language has this sound.',
            'voiced': True, 'emphatic': False,
            'description': 'ʿAyn is the voiced pharyngeal. Abjad 70. '
                           'The DEEPEST voiced consonant — from the middle of the throat, '
                           'it represents DEEP KNOWLEDGE and INNER REALITY. '
                           'ع roots: ع-ل-م (knowledge, 846 — 2nd highest verb), '
                           'ع-ذ-ب (denial of sweetness, 373), ع-م-ل (action, 360), '
                           'ع-ب-د (devotion, 265). ع = DEPTH. KNOWLEDGE. ACTION.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: العِلْم',
            'type': 'Voiced pharyngeal fricative',
            'group': 'حُرُوف الحَلْق — throat letters',
        },
        'behaviour': {
            'as_first_radical': '102 roots. Opens KNOWLEDGE/ACTION/DEVOTION: '
                                'ع-ل-م (knowledge, 846), ع-ذ-ب (denial of sweetness, 373), '
                                'ع-م-ل (action, 360), ع-ب-د (devotion, 265), ع-ظ-م (greatness, 128). '
                                'When ع opens, it reaches DEEP — knowledge, action, devotion all come from depth.',
            'as_second_radical': 'ج-ع-ل (making, 345), ب-ع-د (distance, 236), '
                                 'و-ع-د (promise, 139), ن-ع-م (blessing, 133). '
                                 'As core, ع provides DEPTH — the deep well from which meaning rises.',
            'as_third_radical': 'س-م-ع (hearing, 197), ت-ب-ع (following, 166), '
                                'ج-م-ع (gathering, 129), ط-و-ع (obedience, 111). '
                                'As closer, ع pulls INWARD — the word concludes by going deep.',
            'as_prefix': 'Not a standard verbal prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'a', 'shift_id': 'S07', 'note': 'ع→a (pharyngeal collapses to vowel)'},
            {'downstream': 'e', 'shift_id': 'S07', 'note': 'ع→e (pharyngeal collapses to vowel)'},
            {'downstream': '(drops)', 'shift_id': 'S07', 'note': 'ع drops entirely in many DS corridors'},
            {'downstream': '(vowel / silent)', 'shift_id': 'AYN-DROP', 'note': 'Pharyngeal quality disappears completely'},
        ],
        'quranic_stats': {
            'tokens_any_position': 6878, 'distinct_roots_any': 220, 'roots_as_first': 102,
            'top5_first': [('ع-ل-م', 846), ('ع-ذ-ب', 373), ('ع-م-ل', 360), ('ع-ب-د', 265), ('ع-ظ-م', 128)],
            'top5_second': [('ج-ع-ل', 345), ('ب-ع-د', 236), ('و-ع-د', 139), ('ن-ع-م', 133), ('د-ع-و', 123)],
            'top5_third': [('س-م-ع', 197), ('ت-ب-ع', 166), ('ج-م-ع', 129), ('ط-و-ع', 111), ('ر-ج-ع', 103)],
            'muqattaat': ['كهيعص — Surah 19 (ع is one of the five letters)'],
        },
        'semantic_tendency': 'DEPTH. KNOWLEDGE. ACTION. DEVOTION. THE INNER. '
                             'ع is the letter of the DEEP INTERIOR — ع-ل-م (846) is knowledge gained from depth, '
                             'ع-م-ل (action = depth manifested), ع-ب-د (devotion = depth committed). '
                             'NO DS language can produce this sound — they lose the depth entirely.',
        'paired_letters': {
            'ل (lām)': 'ع-ل = depth + flow (ع-ل-م knowledge). Knowledge = deep flow.',
            'م (mīm)': 'ع-م = depth + enclosure (ع-م-ل action). Action = depth enclosed and expressed.',
            'ب (bāʾ)': 'ع-ب = depth + building (ع-ب-د devotion). Devotion = building from deep within.',
        },
        'unique': 'Abjad 70. NO equivalent in ANY DS language — ع DROPS or becomes a bare vowel. '
                  'This is the MOST lost letter in degradation — and it carries the DEEPEST concepts. '
                  'ع-ل-م (846 tokens) = knowledge. Q96:5 عَلَّمَ الإِنسَانَ مَا لَمْ يَعْلَمْ. '
                  'In the أَمْر system, ع = the kernel depth — the deep internal state that no surface can access.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 19. غ — GHAYN
    # ──────────────────────────────────────────────────────────────────
    'غ': {
        'name': 'غَيْن',
        'transliteration': 'ghayn',
        'abjad': 1000,
        'phonetic': {
            'makhraj': 'أَدْنَى الحَلْق — nearest part of the throat to the mouth (uvular)',
            'manner': 'Voiced uvular fricative. Air passes over raised back of tongue '
                      'near uvula with voicing. The voiced partner of خ (khāʾ).',
            'voiced': True, 'emphatic': False,
            'description': 'Ghayn is the voiced uvular fricative. Abjad 1000 — the HIGHEST single-letter value. '
                           'غ roots: غ-ف-ر (covering/shielding, 231), غ-ي-ر (other/change, 84), '
                           'غ-ن-ي (richness, 73). غ = COVERING, CONCEALMENT, ABUNDANCE. '
                           'The uvular rumble = what lies HIDDEN or what is OVERFLOWING.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الغَفُور',
            'type': 'Voiced uvular fricative',
            'group': 'حُرُوف الحَلْق — throat letters (nearest the mouth)',
        },
        'behaviour': {
            'as_first_radical': '49 roots. Opens COVERING/CHANGE/RICHNESS: '
                                'غ-ف-ر (shielding, 231), غ-ي-ر (change, 84), غ-ن-ي (richness, 73), '
                                'غ-ي-ب (unseen, 57). When غ opens, something is HIDDEN or CHANGED.',
            'as_second_radical': 'ب-غ-ي (seeking/transgression, 94), ط-غ-ي (overflowing, 35). '
                                 'As core, غ provides CONCEALMENT — the hidden force.',
            'as_third_radical': 'ب-ل-غ (reaching, 71), ز-ي-غ (deviation, 10). '
                                'As closer, غ veils — the word ends in concealment.',
            'as_prefix': 'Not a standard prefix.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'g', 'shift_id': 'S14', 'note': 'غ→g (uvular fricative → velar stop)'},
            {'downstream': 'gh', 'shift_id': 'S14', 'note': 'غ→gh (preserved in some corridors)'},
            {'downstream': 'silent / g', 'shift_id': 'GH-DROP', 'note': 'غ drops or weakens to g'},
        ],
        'quranic_stats': {
            'tokens_any_position': 1134, 'distinct_roots_any': 78, 'roots_as_first': 49,
            'top5_first': [('غ-ف-ر', 231), ('غ-ي-ر', 84), ('غ-ن-ي', 73), ('غ-ي-ب', 57), ('غ-ف-ل', 35)],
            'top5_second': [('ب-غ-ي', 94), ('ط-غ-ي', 35), ('ل-غ-و', 21), ('ب-غ-ت', 15), ('ص-غ-ر', 13)],
            'top5_third': [('ب-ل-غ', 71), ('ز-ي-غ', 10), ('ن-ز-غ', 6), ('ف-ر-غ', 5), ('م-ض-غ', 3)],
            'muqattaat': [],
        },
        'semantic_tendency': 'SCRAPE. CONCEALMENT. CHANGE. RICHNESS. THE HIDDEN. '
                             'غ = what is VEILED: غ-ف-ر (shielding from consequences), غ-ي-ب (the unseen), '
                             'غ-ن-ي (rich = concealed resources). Abjad 1000 = the largest single-letter value = abundance.',
        'paired_letters': {
            'ف (fāʾ)': 'غ-ف = concealment + release (غ-ف-ر shielding). Forgiving = releasing from under cover.',
            'ي (yāʾ)': 'غ-ي = concealment + extension (غ-ي-ب unseen). The unseen = hidden extension.',
            'ن (nūn)': 'غ-ن = concealment + continuation (غ-ن-ي richness). Wealth = hidden continuity.',
        },
        'unique': 'Abjad 1000 — the HIGHEST value. غ-ف-ر (231 tokens) is how the Qur\'an describes '
                  'Allah\'s covering/shielding (الغَفُور). غ-ي-ب (the unseen) is a core Qur\'anic concept. '
                  'In the أَمْر system, غ = the encryption/hidden layer — what is concealed from surface access.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 20. ف — FĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ف': {
        'name': 'فَاء',
        'transliteration': 'fāʾ',
        'abjad': 80,
        'phonetic': {
            'makhraj': 'بَاطِن الشَّفَة السُّفْلَى مَعَ أَطْرَاف الثَّنَايَا العُلْيَا — inner lower lip + upper teeth',
            'manner': 'Voiceless labiodental fricative. Lower lip touches upper teeth, air passes as friction.',
            'voiced': False, 'emphatic': False,
            'description': 'Fāʾ is the labiodental fricative. Abjad 80. '
                           'Lip meets teeth — an INTERFACE between two surfaces. '
                           'ف roots: ف-ض-ل (excellence, 106), ف-ع-ل (doing, 103), ف-ر-ق (separating, 67). '
                           'ف = SEPARATION, ACTION, RELEASE. The air escapes between lip and teeth = release.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الفَضْل',
            'type': 'Voiceless labiodental fricative',
            'group': 'حُرُوف الشَّفَتَيْن — lip letters (labiodental)',
        },
        'behaviour': {
            'as_first_radical': '71 roots. Opens SEPARATION/ACTION/SPLITTING: '
                                'ف-ض-ل (excellence, 106), ف-ع-ل (doing, 103), ف-ر-ع (branching, 75), '
                                'ف-ر-ق (separating, 67). When ف opens, it SEPARATES or RELEASES.',
            'as_second_radical': 'ك-ف-ر (covering, 487), ن-ف-س (self, 296), غ-ف-ر (shielding, 231). '
                                 'As core, ف provides the ESCAPE — the air-release at the root\'s heart.',
            'as_third_radical': 'خ-ل-ف (succession, 123), خ-و-ف (fear, 120), '
                                'ع-ر-ف (knowing, 70). As closer, ف releases — the word opens at the end.',
            'as_prefix': 'فَـ = THEN/SO (sequential conjunction). Q2:37 فَتَابَ عَلَيْهِ = then He turned to him. '
                         'The ف of consequence — what FOLLOWS from what came before.',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'f', 'shift_id': 'S08', 'note': 'Preserved as f'},
            {'downstream': 'p', 'shift_id': 'S08', 'note': 'ف→p in Bitig and some DS corridors'},
            {'downstream': 'v', 'shift_id': 'S08', 'note': 'ف→v (voicing in some corridors)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 4126, 'distinct_roots_any': 215, 'roots_as_first': 71,
            'top5_first': [('ف-ض-ل', 106), ('ف-ع-ل', 103), ('ف-ر-ع', 75), ('ف-ر-ق', 67), ('ف-ق-د', 60)],
            'top5_second': [('ك-ف-ر', 487), ('ن-ف-س', 296), ('غ-ف-ر', 231), ('ن-ف-ق', 100), ('و-ف-ي', 74)],
            'top5_third': [('خ-ل-ف', 123), ('خ-و-ف', 120), ('ع-ر-ف', 70), ('ض-ع-ف', 49), ('أ-ل-ف', 41)],
            'muqattaat': [],
        },
        'semantic_tendency': 'SEPARATION. RELEASE. ACTION. CONSEQUENCE. '
                             'ف marks what SPLITS or what FOLLOWS: ف-ر-ق (separate), ف-ع-ل (do/act). '
                             'As prefix فَـ it marks THEN — the consequence connector. '
                             'The labiodental release = air escaping = action released.',
        'paired_letters': {
            'ع (ʿayn)': 'ف-ع = release + depth (ف-ع-ل action). To act = to release from depth.',
            'ر (rāʾ)': 'ف-ر = release + process (ف-ر-ق separation). Separating = releasing through process.',
            'ض (ḍād)': 'ف-ض = release + force (ف-ض-ل excellence). Excellence = forceful release.',
        },
        'unique': 'Abjad 80. The CONSEQUENCE letter — فَـ (then/so) is the most frequent Qur\'anic connector. '
                  'Every conditional leads to فَـ: إِنْ...فَـ (if...then). '
                  'In the أَمْر system, ف = the conditional branch — the THEN of if-then logic.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 21. ق — QĀF
    # ──────────────────────────────────────────────────────────────────
    'ق': {
        'name': 'قَاف',
        'transliteration': 'qāf',
        'abjad': 100,
        'phonetic': {
            'makhraj': 'أَقْصَى اللِّسَان مَعَ الحَنَك الأَعْلَى — back of tongue against soft palate (uvular)',
            'manner': 'Voiceless uvular plosive. Back of tongue strikes uvula/soft palate, '
                      'releases with a deep pop. DEEPER than ك (kāf). '
                      'No DS language has a true ق — it collapses to k/g/c.',
            'voiced': False, 'emphatic': False,
            'description': 'Qāf is the deep uvular stop. Abjad 100. '
                           'The DEEPEST plosive — from the back of the throat. '
                           'ق roots: ق-و-ل (speech, 1690 — THE highest), ق-و-م (standing, 583), '
                           'ق-ب-ل (accepting, 291), ق-ل-ب (heart, 166). '
                           'ق = FORCE. SPEECH. STANDING. The deep pop = DECISIVE utterance.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: القَوْل',
            'type': 'Voiceless uvular plosive',
            'group': 'حُرُوف لَهَوِيَّة — uvular letters',
        },
        'behaviour': {
            'as_first_radical': '77 roots. Opens SPEECH/STANDING/FORCE: '
                                'ق-و-ل (speech, 1690 — HIGHEST root), ق-و-م (standing, 583), '
                                'ق-ب-ل (accepting, 291), ق-ل-ب (heart, 166), ق-ت-ل (fighting, 164). '
                                'When ق opens, it DECLARES with force.',
            'as_second_radical': 'ح-ق-ق (truth, 263), و-ق-ي (protection, 162). '
                                 'As core, ق provides FORCE — the deep uvular impact.',
            'as_third_radical': 'ح-ق-ق (truth, 263), خ-ل-ق (creation, 261), '
                                'ص-د-ق (truth, 149), ر-ز-ق (provision, 121). '
                                'As closer, ق STAMPS with deep authority.',
            'as_prefix': 'قَدْ = particle of emphasis/certainty (قَدْ أَفْلَحَ = certainly succeeded).',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'k', 'shift_id': 'S01', 'note': 'ق→k (uvular → velar, most common shift)'},
            {'downstream': 'c', 'shift_id': 'S01', 'note': 'ق→c in DS05 Latin corridor'},
            {'downstream': 'q', 'shift_id': 'S01', 'note': 'ق→q (preserved in some corridors)'},
            {'downstream': 'g', 'shift_id': 'S01', 'note': 'ق→g (voiced in some corridors)'},
            {'downstream': 'k / c / g (hard)', 'shift_id': 'Q-VEL', 'note': 'General velar range'},
        ],
        'quranic_stats': {
            'tokens_any_position': 6570, 'distinct_roots_any': 205, 'roots_as_first': 77,
            'top5_first': [('ق-و-ل', 1690), ('ق-و-م', 583), ('ق-ب-ل', 291), ('ق-ل-ب', 166), ('ق-ت-ل', 164)],
            'top5_second': [('ح-ق-ق', 263), ('و-ق-ي', 162), ('ل-ق-ي', 113), ('ع-ق-ب', 96), ('ف-ق-د', 60)],
            'top5_third': [('ح-ق-ق', 263), ('خ-ل-ق', 261), ('ص-د-ق', 149), ('ر-ز-ق', 121), ('ن-ف-ق', 100)],
            'muqattaat': ['ق — Surah 50 (standalone)'],
        },
        'semantic_tendency': 'STRIKE. FORCE. STANDING. HEART. DECLARATION. '
                             'ق is the letter of DECISIVE UTTERANCE. ق-و-ل (1690) = speech/saying. '
                             'ق-و-م (583) = standing/establishing. ق-ل-ب (heart = the core that turns). '
                             'The deep uvular pop = what cannot be taken back.',
        'paired_letters': {
            'و (wāw)': 'ق-و = force + connection (ق-و-ل speech, ق-و-م standing). Force that connects.',
            'ل (lām)': 'ق-ل = force + flow (ق-ل-ب heart). The heart = force flowing.',
            'ب (bāʾ)': 'ق-ب = force + contact (ق-ب-ل accepting). Accepting = force meeting contact.',
        },
        'unique': 'Abjad 100. ق-و-ل (1690) is the HIGHEST-frequency root in the entire Qur\'an. '
                  'ق appears as standalone muqaṭṭaʿa (Surah 50). Q36:82 أَمْرُهُ... كُن فَيَكُونُ — '
                  'His أَمْر is to SAY (from ق-و-ل) كُن (from ك-و-ن). Speech IS creation. '
                  'In the أَمْر system, ق = the execution engine — what DECLARES and EXECUTES.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 22. ك — KĀF
    # ──────────────────────────────────────────────────────────────────
    'ك': {
        'name': 'كَاف',
        'transliteration': 'kāf',
        'abjad': 20,
        'phonetic': {
            'makhraj': 'أَدْنَى اللِّسَان مَعَ الحَنَك الأَعْلَى — back of tongue near soft palate (velar)',
            'manner': 'Voiceless velar plosive. Shallower than ق — tongue strikes soft palate '
                      'rather than uvula. ك is the LIGHT version of ق.',
            'voiced': False, 'emphatic': False,
            'description': 'Kāf is the velar stop. Abjad 20. '
                           'ك roots: ك-و-ن (being/existence, 1032), ك-ف-ر (covering, 487), '
                           'ك-ت-ب (writing, 311). ك = EXISTENCE, CONTAINMENT, COVERING. '
                           'Q36:82: كُن فَيَكُونُ — BE and it IS. ك-و-ن is the root of BEING.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الكِتَاب',
            'type': 'Voiceless velar plosive',
            'group': 'حُرُوف لَهَوِيَّة — velar letters',
        },
        'behaviour': {
            'as_first_radical': '57 roots. Opens BEING/COVERING/WRITING: '
                                'ك-و-ن (being, 1032), ك-ف-ر (covering, 487), ك-ت-ب (writing, 311), '
                                'ك-ذ-ب (denial, 282). When ك opens, it ESTABLISHES existence or CONTAINS.',
            'as_second_radical': 'ذ-ك-ر (remembrance, 286), ح-ك-م (judgement, 195), '
                                 'و-ك-ل (reliance, 108). As core, ك is the VESSEL — what holds.',
            'as_third_radical': 'م-ل-ك (sovereignty, 185), ش-ر-ك (sharing, 149), '
                                'ه-ل-ك (destruction, 44). As closer, ك GRASPS — the velar stop seizes.',
            'as_prefix': 'كَـ = like/as (comparison). كَمَثَلِ = like the example of. '
                         'Also second person pronoun suffix: كِتَابُكَ = your book.',
            'as_suffix': 'ـكَ/ـكِ = your (second person possessive).',
        },
        'shifts': [
            {'downstream': 'k', 'shift_id': 'S20', 'note': 'Preserved as k'},
            {'downstream': 'c', 'shift_id': 'S20', 'note': 'ك→c in DS05 Latin'},
            {'downstream': 'g', 'shift_id': 'S20', 'note': 'ك→g (voicing)'},
            {'downstream': 'ch', 'shift_id': 'S20', 'note': 'ك→ch in some corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 4804, 'distinct_roots_any': 127, 'roots_as_first': 57,
            'top5_first': [('ك-و-ن', 1032), ('ك-ف-ر', 487), ('ك-ت-ب', 311), ('ك-ذ-ب', 282), ('ك-ث-ر', 166)],
            'top5_second': [('ذ-ك-ر', 286), ('ح-ك-م', 195), ('و-ك-ل', 108), ('أ-ك-ل', 76), ('ش-ك-ر', 74)],
            'top5_third': [('م-ل-ك', 185), ('ش-ر-ك', 149), ('ه-ل-ك', 44), ('ت-ر-ك', 40), ('م-س-ك', 35)],
            'muqattaat': ['كهيعص — Surah 19'],
        },
        'semantic_tendency': 'TAP. EXISTENCE. CONTAINMENT. COVERING. '
                             'ك is the letter of WHAT IS: ك-و-ن (1032) = to be/exist. كُن = BE. '
                             'ك-ف-ر (covering), ك-ت-ب (writing = prescribed containment). '
                             'Abjad 20 = contained completeness.',
        'paired_letters': {
            'و (wāw)': 'ك-و = containment + connection (ك-و-ن being). Being = contained connection.',
            'ف (fāʾ)': 'ك-ف = containment + release (ك-ف-ر covering). Covering = sealed containment.',
            'ت (tāʾ)': 'ك-ت = containment + succession (ك-ت-ب writing). Writing = successive containment.',
        },
        'unique': 'Abjad 20. كُن (BE!) is the divine command of creation (Q36:82). '
                  'ك-و-ن (1032) is the 2nd highest-frequency root. '
                  'In the أَمْر system, ك = the instantiator — كُن = bring into being.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 23. ل — LĀM
    # ──────────────────────────────────────────────────────────────────
    'ل': {
        'name': 'لَام',
        'transliteration': 'lām',
        'abjad': 30,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ اللِّثَة العُلْيَا — tongue tip against upper gum ridge',
            'manner': 'Voiced alveolar lateral approximant. Air flows along the SIDES of the tongue '
                      'while the tip touches the ridge. The FLOWING letter.',
            'voiced': True, 'emphatic': False,
            'description': 'Lām is the lateral approximant. Abjad 30. '
                           'The MOST CONNECTED letter by token count (14,445). '
                           'Air flows AROUND the tongue = CONNECTION, BINDING, FLOWING. '
                           'ل is the letter of ال (the definite article) — what DEFINES.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: اللَّيْل. '
                        'BUT ل IS the second letter of ال — it defines ALL other letters.',
            'type': 'Voiced alveolar lateral approximant (liquid)',
            'group': 'حُرُوف ذَلْقِيَّة — tongue-tip letters (liquids)',
        },
        'behaviour': {
            'as_first_radical': '53 roots. Opens MEETING/NIGHT/NEGATION: '
                                'ل-ق-ي (meeting, 113), ل-ي-ل (night, 99), ل-ي-س (is not, 59). '
                                'When ل opens, it CONNECTS or BINDS.',
            'as_second_radical': 'أ-ل-ه (divinity, 2930 — THE HIGHEST), ع-ل-م (knowledge, 846), '
                                 'ظ-ل-م (displacement, 315), خ-ل-ق (creation, 261). '
                                 'As core, ل is THE FLOW — the connective tissue of the most important roots.',
            'as_third_radical': 'ق-و-ل (speech, 1690), ر-س-ل (sending, 509), '
                                'ع-م-ل (action, 360), ج-ع-ل (making, 345). '
                                'As closer, ل FLOWS ONWARD — the word does not stop but continues.',
            'as_prefix': 'لِـ = for/to (purpose). لَـ = surely/indeed (emphasis). '
                         'ال = THE (definite article — the DEFINING function). '
                         'لَا = not (negation).',
            'as_suffix': 'Not a standard suffix.',
        },
        'shifts': [
            {'downstream': 'l', 'shift_id': 'S16', 'note': 'Preserved as l (highest resistance after ر)'},
            {'downstream': 'r / l swap', 'shift_id': 'L-META', 'note': 'ل↔ر metathesis in some corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 14445, 'distinct_roots_any': 282, 'roots_as_first': 53,
            'top5_first': [('ل-ق-ي', 113), ('ل-ي-ل', 99), ('ل-ي-س', 59), ('ل-ع-ن', 39), ('ل-ب-ث', 31)],
            'top5_second': [('أ-ل-ه', 2930), ('ع-ل-م', 846), ('ظ-ل-م', 315), ('خ-ل-ق', 261), ('و-ل-ي', 204)],
            'top5_third': [('ق-و-ل', 1690), ('ر-س-ل', 509), ('ع-م-ل', 360), ('ج-ع-ل', 345), ('ن-ز-ل', 293)],
            'muqattaat': ['الم — Surahs 2,3,29,30,31,32. الر — Surahs 10,11,12,14,15. '
                          'المص — Surah 7. المر — Surah 13'],
        },
        'semantic_tendency': 'CONNECTION. DEFINITION. FLOW. BINDING. '
                             'ل is in MORE roots than any other letter (14,445 tokens). '
                             'أ-ل-ه (2930) = divinity. ع-ل-م (846) = knowledge. ق-و-ل (1690) = speech. '
                             'ل connects everything — it IS the lattice itself.',
        'paired_letters': {
            'ا (alif)': 'ل-ا / ا-ل = THE definite article. Alif (unity) + lām (connection) = definition.',
            'م (mīm)': 'ل-م = flow + enclosure (الم muqaṭṭaʿāt, عِلْم knowledge). The core triad.',
            'ه (hāʾ)': 'ل-ه = flow + breath (أ-ل-ه divinity). The divine = flowing breath.',
        },
        'unique': 'Abjad 30. THE most connected letter — 14,445 tokens, appears in the TOP roots '
                  'of EVERY category. ل IS ال — the definite article that defines all nouns. '
                  'In the أَمْر system, ل = the connector — the pipe, the link, the binding operator.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 24. م — MĪM
    # ──────────────────────────────────────────────────────────────────
    'م': {
        'name': 'مِيم',
        'transliteration': 'mīm',
        'abjad': 40,
        'phonetic': {
            'makhraj': 'الشَّفَتَان — the two lips (bilabial)',
            'manner': 'Voiced bilabial nasal. Lips close, air passes through the nose. '
                      'The NASAL partner of ب (bāʾ). Where ب explodes outward, م resonates inward.',
            'voiced': True, 'emphatic': False,
            'description': 'Mīm is the bilabial nasal. Abjad 40. '
                           'Lips close and SEAL — air redirected through nose = ENCLOSURE. '
                           'م roots: م-ل-ك (sovereignty, 185), م-و-ت (death, 148), م-ث-ل (likeness, 119). '
                           'م = ENCLOSURE. SEALING. WHAT IS CONTAINED.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: المَوْت',
            'type': 'Voiced bilabial nasal',
            'group': 'حُرُوف الشَّفَتَيْن — lip letters (nasal)',
        },
        'behaviour': {
            'as_first_radical': '70 roots. Opens SOVEREIGNTY/DEATH/LIKENESS: '
                                'م-ل-ك (sovereignty, 185), م-و-ت (death, 148), م-ث-ل (likeness, 119). '
                                'When م opens, it ENCLOSES or CONTAINS.',
            'as_second_radical': 'أ-م-ن (security, 832), س-م-و (elevation, 457), '
                                 'ع-م-ل (action, 360), أ-م-ر (command, 223). '
                                 'As core, م is the SEAL — what holds the root\'s content.',
            'as_third_radical': 'ع-ل-م (knowledge, 846), ق-و-م (standing, 583), '
                                'ر-ح-م (womb, 553), ي-و-م (day, 551), ظ-ل-م (displacement, 315). '
                                'As closer, م SEALS — the lips close the word with finality.',
            'as_prefix': 'مَـ = what/that which (مَا = what. مَنْ = who). '
                         'مُـ = active participle prefix (مُسْلِم = one who submits). '
                         'مَفْعُول pattern = passive participle (مَكْتُوب = written).',
            'as_suffix': 'ـم = plural masculine pronoun suffix (هُمْ = them, كُمْ = you all).',
        },
        'shifts': [
            {'downstream': 'm', 'shift_id': 'S17', 'note': 'Preserved as m (nasal = highest resistance)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 9522, 'distinct_roots_any': 268, 'roots_as_first': 70,
            'top5_first': [('م-ل-ك', 185), ('م-و-ت', 148), ('م-ث-ل', 119), ('م-و-ل', 108), ('م-و-س', 105)],
            'top5_second': [('أ-م-ن', 832), ('س-م-و', 457), ('ع-م-ل', 360), ('أ-م-ر', 223), ('س-م-ع', 197)],
            'top5_third': [('ع-ل-م', 846), ('ق-و-م', 583), ('ر-ح-م', 553), ('ي-و-م', 551), ('ظ-ل-م', 315)],
            'muqattaat': ['الم — Surahs 2,3,29,30,31,32. حم — Surahs 40-46. المص — Surah 7. المر — Surah 13'],
        },
        'semantic_tendency': 'ENCLOSURE. SEALING. CONTAINMENT. FINALITY. '
                             'م is the SEALER — lips close, word is contained. '
                             'م-و-ت (death = final seal), م-ل-ك (sovereignty = sealed authority). '
                             'As third radical in ع-ل-م, ق-و-م, ر-ح-م — م seals the deepest concepts.',
        'paired_letters': {
            'ل (lām)': 'م-ل = seal + flow (م-ل-ك sovereignty). Sealed flow = dominion.',
            'و (wāw)': 'م-و = seal + connection (م-و-ت death). Death = sealed connection.',
            'ن (nūn)': 'م-ن = seal + continuation (مِن from, مَن who). The sealed question.',
        },
        'unique': 'Abjad 40. The SEALER. م appears in more muqaṭṭaʿāt than any letter. '
                  'م + ن = the two nasals = the MOST RESISTANT consonant pair in all languages. '
                  'In the أَمْر system, م = the encapsulator — what wraps and seals data.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 25. ن — NŪN
    # ──────────────────────────────────────────────────────────────────
    'ن': {
        'name': 'نُون',
        'transliteration': 'nūn',
        'abjad': 50,
        'phonetic': {
            'makhraj': 'طَرَف اللِّسَان مَعَ اللِّثَة العُلْيَا — tongue tip against upper gum ridge',
            'manner': 'Voiced alveolar nasal. Tongue tip touches ridge, air flows through nose. '
                      'The CONTINUATION nasal — where م (mīm) seals with lips, ن continues with tongue.',
            'voiced': True, 'emphatic': False,
            'description': 'Nūn is the alveolar nasal. Abjad 50. '
                           'ن roots: ن-ف-س (self/soul, 296), ن-ز-ل (descending, 293), '
                           'ن-و-ر (light, 191), ن-ذ-ر (warning, 134). '
                           'ن = CONTINUATION. SOUL. DESCENT. The nasal hum that continues.',
        },
        'classification': {
            'sun_moon': 'Sun letter (شَمْسِيَّة) — assimilates: النُّور',
            'type': 'Voiced alveolar nasal',
            'group': 'حُرُوف ذَلْقِيَّة — tongue-tip letters (nasal)',
        },
        'behaviour': {
            'as_first_radical': '105 roots. Opens SOUL/DESCENT/LIGHT/WARNING: '
                                'ن-ف-س (self, 296), ن-ز-ل (descending, 293), ن-و-ر (light, 191), '
                                'ن-ذ-ر (warning, 134). When ن opens, it marks what CONTINUES or DESCENDS.',
            'as_second_radical': 'أ-ن-س (humanity, 263), ج-ن-ن (concealment, 172), '
                                 'ب-ن-ي (building, 128). As core, ن is the THREAD — what runs through.',
            'as_third_radical': 'ك-و-ن (being, 1032), أ-م-ن (security, 832), '
                                'ب-ي-ن (clarity, 282), ح-س-ن (beauty, 189). '
                                'As closer, ن HUMS — the word trails with nasal resonance, continuing.',
            'as_prefix': 'نَـ = first person plural imperfect (نَعْبُدُ = we devote). '
                         'Also tanwīn (nunation): ـًا ـٍ ـٌ = indefinite marker.',
            'as_suffix': 'ـنَ = feminine plural. ـنَا = our/us.',
        },
        'shifts': [
            {'downstream': 'n', 'shift_id': 'S18', 'note': 'Preserved as n (nasal = highest resistance)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 7924, 'distinct_roots_any': 261, 'roots_as_first': 105,
            'top5_first': [('ن-ف-س', 296), ('ن-ز-ل', 293), ('ن-و-ر', 191), ('ن-ذ-ر', 134), ('ن-ع-م', 133)],
            'top5_second': [('أ-ن-س', 263), ('ج-ن-ن', 172), ('ب-ن-ي', 128), ('د-ن-ي', 110), ('غ-ن-ي', 73)],
            'top5_third': [('ك-و-ن', 1032), ('أ-م-ن', 832), ('ب-ي-ن', 282), ('ح-س-ن', 189), ('ج-ن-ن', 172)],
            'muqattaat': ['ن — Surah 68 (standalone, opening of Sūrat al-Qalam)'],
        },
        'semantic_tendency': 'CONTINUATION. SOUL. LIGHT. DESCENT. THE THREAD. '
                             'ن continues what م seals: م closes, ن carries forward. '
                             'ن-ف-س (soul = the continuing self), ن-و-ر (light = continuous illumination). '
                             'As third radical in ك-و-ن (1032) and أ-م-ن (832) — ن carries BEING and SECURITY forward.',
        'paired_letters': {
            'ف (fāʾ)': 'ن-ف = continuation + release (ن-ف-س self). The self = what continues released.',
            'و (wāw)': 'ن-و = continuation + connection (ن-و-ر light). Light = connected continuation.',
            'ز (zāy)': 'ن-ز = continuation + energy (ن-ز-ل descent). Descending = energized continuation.',
        },
        'unique': 'Abjad 50. ن opens Surah 68 as standalone muqaṭṭaʿa — followed immediately by '
                  'وَٱلْقَلَمِ (and the pen). ن + قَلَم = the nūn + the pen. '
                  'Tanwīn (ـًا ـٍ ـٌ) = the hidden ن that makes nouns INDEFINITE. '
                  'In the أَمْر system, ن = the continuation/loop — what keeps running.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 26. ه — HĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ه': {
        'name': 'هَاء',
        'transliteration': 'hāʾ',
        'abjad': 5,
        'phonetic': {
            'makhraj': 'أَقْصَى الحَلْق — deepest part of the throat (glottal)',
            'manner': 'Voiceless glottal fricative. Pure breath from the deepest point. '
                      'The lightest consonant — almost just breath.',
            'voiced': False, 'emphatic': False,
            'description': 'Hāʾ is the glottal breath. Abjad 5. '
                           'PURE BREATH from the deepest point of the throat. '
                           'ه roots: ه-د-ي (guidance, 259), ه-و-د (descending, 88). '
                           'ه = BREATH. GUIDANCE. THE LIGHTEST TOUCH.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الهُدَى',
            'type': 'Voiceless glottal fricative',
            'group': 'حُرُوف الحَلْق — throat letters (deepest)',
        },
        'behaviour': {
            'as_first_radical': '42 roots. Opens GUIDANCE/DESCENT: '
                                'ه-د-ي (guidance, 259), ه-و-د (descending, 88), ه-و-ر (collapsing, 61). '
                                'When ه opens, it BREATHES — the lightest possible opening.',
            'as_second_radical': 'ش-ه-د (witnessing, 158), أ-ه-ل (people, 135), ظ-ه-ر (appearing, 58). '
                                 'As core, ه is the BREATH — what animates from within.',
            'as_third_radical': 'أ-ل-ه (divinity, 2930 — THE HIGHEST), و-ج-ه (face, 87). '
                                'As closer, ه BREATHES OUT — the word ends in exhalation. '
                                'أ-ل-ه (2930) ends with ه — DIVINITY concludes in pure breath.',
            'as_prefix': 'هَلْ = interrogative particle (هَلْ أَتَاكَ = has there come to you?). '
                         'هُـ = third person masculine prefix in some forms.',
            'as_suffix': 'ـهُ/ـهِ = his/him/it. The third person pronoun = the ABSENT one referred to by breath.',
        },
        'shifts': [
            {'downstream': 'h', 'shift_id': 'S23', 'note': 'ه→h (preserved but weakened)'},
            {'downstream': '(drops)', 'shift_id': 'S23', 'note': 'ه drops entirely in many positions'},
        ],
        'quranic_stats': {
            'tokens_any_position': 5101, 'distinct_roots_any': 117, 'roots_as_first': 42,
            'top5_first': [('ه-د-ي', 259), ('ه-و-د', 88), ('ه-و-ر', 61), ('ه-و-ي', 49), ('ه-ل-ك', 44)],
            'top5_second': [('ش-ه-د', 158), ('أ-ه-ل', 135), ('ج-ه-ن-م', 77), ('ظ-ه-ر', 58), ('ن-ه-ر', 56)],
            'top5_third': [('أ-ل-ه', 2930), ('و-ج-ه', 87), ('م-و-ه', 71), ('ك-ر-ه', 33), ('ف-ق-ه', 20)],
            'muqattaat': ['كهيعص — Surah 19. طه — Surah 20'],
        },
        'semantic_tendency': 'BREATH. GUIDANCE. THE LIGHTEST. THE DEEPEST. '
                             'ه is almost nothing — pure breath. Yet it closes the HIGHEST root: '
                             'أ-ل-ه (2930) = divinity ends in breath. ه-د-ي (259) = guidance starts in breath. '
                             'The lightest letter carries the heaviest concept.',
        'paired_letters': {
            'د (dāl)': 'ه-د = breath + anchor (ه-د-ي guidance). Guidance = breath that anchors.',
            'ل (lām)': 'ه-ل = breath + flow (ه-ل-ك destruction). Destruction = breath flowing away.',
            'و (wāw)': 'ه-و = breath + connection (ه-و-ي desire). Desire = breath seeking connection.',
        },
        'unique': 'Abjad 5. The BREATH letter. أ-ل-ه ends with ه — the name of Allah concludes in breath. '
                  'The تَاء مَرْبُوطَة (ة) is a ه with two dots — the feminine ending IS a hāʾ. '
                  'In the أَمْر system, ه = the null/void — the lightest possible state, pure space.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 27. و — WĀW
    # ──────────────────────────────────────────────────────────────────
    'و': {
        'name': 'وَاو',
        'transliteration': 'wāw',
        'abjad': 6,
        'phonetic': {
            'makhraj': 'الشَّفَتَان — the two lips (bilabial approximant)',
            'manner': 'Voiced bilabial-velar approximant / semivowel. Lips round, '
                      'back of tongue rises. Serves as BOTH consonant (w) AND long vowel (ū/ō).',
            'voiced': True, 'emphatic': False,
            'description': 'Wāw is the rounded semivowel. Abjad 6. '
                           'DUAL NATURE — consonant AND vowel. The CONNECTOR. '
                           'و as particle = AND (the most frequent word in the Qur\'an). '
                           'و roots: و-ل-ي (closeness/governance, 204), و-ق-ي (protection, 162), '
                           'و-ع-د (promise, 139). و = CONNECTION. JOINING. AND.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: الوَعْد',
            'type': 'Voiced bilabial-velar approximant / semivowel',
            'group': 'حُرُوف العِلَّة — weak/vowel letters',
        },
        'behaviour': {
            'as_first_radical': '81 roots. Opens CLOSENESS/PROTECTION/PROMISE: '
                                'و-ل-ي (closeness, 204), و-ق-ي (protection, 162), '
                                'و-ع-د (promise, 139), و-ك-ل (reliance, 108). '
                                'When و opens, it CONNECTS or PROTECTS.',
            'as_second_radical': 'ق-و-ل (speech, 1690), ك-و-ن (being, 1032), '
                                 'ق-و-م (standing, 583), ي-و-م (day, 551). '
                                 'As core, و is the BRIDGE — connecting first and last radical.',
            'as_third_radical': 'س-م-و (elevation, 457), د-ع-و (calling, 123), '
                                'ص-ل-و (connection, 86). As closer, و OPENS OUT — the lips round and release.',
            'as_prefix': 'وَ = AND (conjunction). The most frequent word in the Qur\'an. '
                         'Every sentence connects to the next through و.',
            'as_suffix': 'ـوا = third person masculine plural past (كَتَبُوا = they wrote). '
                         'ـون = masculine plural present (يَكْتُبُونَ = they write).',
        },
        'shifts': [
            {'downstream': 'w', 'shift_id': 'S10', 'note': 'Preserved as w'},
            {'downstream': 'v', 'shift_id': 'S10', 'note': 'و→v in many DS corridors'},
            {'downstream': 'o', 'shift_id': 'S10', 'note': 'و→o (vowelized)'},
            {'downstream': 'r', 'shift_id': 'S10', 'note': 'و→r in some rare corridors'},
        ],
        'quranic_stats': {
            'tokens_any_position': 12299, 'distinct_roots_any': 325, 'roots_as_first': 81,
            'top5_first': [('و-ل-ي', 204), ('و-ق-ي', 162), ('و-ع-د', 139), ('و-ك-ل', 108), ('و-ج-د', 97)],
            'top5_second': [('ق-و-ل', 1690), ('ك-و-ن', 1032), ('ق-و-م', 583), ('ي-و-م', 551), ('أ-و-ل', 199)],
            'top5_third': [('س-م-و', 457), ('د-ع-و', 123), ('ص-ل-و', 86), ('ت-ل-و', 71), ('أ-ل-و', 67)],
            'muqattaat': [],
        },
        'semantic_tendency': 'ROUNDING. AND. JOINING. BRIDGING. THE LINK. '
                             'و IS connection itself: the word AND. As middle radical in '
                             'ق-و-ل (1690), ك-و-ن (1032), ق-و-م (583) — و bridges the BIGGEST roots. '
                             'The rounded lips = embrace = what brings together.',
        'paired_letters': {
            'ل (lām)': 'و-ل = connection + flow (و-ل-ي closeness). Closeness = connected flow.',
            'ق (qāf)': 'و-ق = connection + force (و-ق-ي protection). Protection = connected force.',
            'ع (ʿayn)': 'و-ع = connection + depth (و-ع-د promise). Promise = deep connection.',
        },
        'unique': 'Abjad 6. وَ (AND) is the most frequent word in the entire Qur\'an. '
                  'و is in the CORE of the three highest roots: ق-و-ل, ك-و-ن, ق-و-م. '
                  'DUAL nature: consonant + vowel. '
                  'In the أَمْر system, و = the AND operator — the fundamental connector.',
    },

    # ──────────────────────────────────────────────────────────────────
    # 28. ي — YĀʾ
    # ──────────────────────────────────────────────────────────────────
    'ي': {
        'name': 'يَاء',
        'transliteration': 'yāʾ',
        'abjad': 10,
        'phonetic': {
            'makhraj': 'وَسَط اللِّسَان مَعَ الحَنَك — middle tongue toward palate',
            'manner': 'Voiced palatal approximant / semivowel. Tongue body rises toward palate. '
                      'Serves as BOTH consonant (y) AND long vowel (ī/ē). '
                      'The REACHING letter — tongue extends upward.',
            'voiced': True, 'emphatic': False,
            'description': 'Yāʾ is the palatal semivowel. Abjad 10. '
                           'DUAL NATURE — consonant AND vowel (like و). '
                           'ي roots: ي-و-م (day, 551), ي-م-ن (right/oath, 125), '
                           'ي-د-ي (hand, 106). ي = REACHING. EXTENSION. TIME. '
                           'The tongue reaches up = aspiration, extension toward.',
        },
        'classification': {
            'sun_moon': 'Moon letter (قَمَرِيَّة) — does not assimilate: اليَوْم',
            'type': 'Voiced palatal approximant / semivowel',
            'group': 'حُرُوف العِلَّة — weak/vowel letters',
        },
        'behaviour': {
            'as_first_radical': '13 roots — rare as opener. ي-و-م (day, 551), '
                                'ي-م-ن (right/oath, 125), ي-د-ي (hand, 106). '
                                'When ي opens, it marks TIME or EXTENSION.',
            'as_second_radical': 'أ-ي-ي (sign, 388), ش-ي-أ (thing, 355), '
                                 'ب-ي-ن (clarity, 282), خ-ي-ر (good, 191). '
                                 'As core, ي is the REACH — extension at the heart of the root.',
            'as_third_radical': 'أ-ي-ي (sign, 388), أ-ت-ي (coming, 385), '
                                'ه-د-ي (guidance, 259), و-ل-ي (closeness, 204). '
                                'As closer, ي EXTENDS — the word reaches forward, does not stop.',
            'as_prefix': 'يَـ = third person masculine imperfect (يَعْلَمُ = he knows). '
                         'Also vocative in يَا (يَا أَيُّهَا النَّاسُ = O people).',
            'as_suffix': 'ـي = my (first person possessive). ـين = masculine plural oblique.',
        },
        'shifts': [
            {'downstream': 'y', 'shift_id': 'S27', 'note': 'ي→y (preserved as palatal approximant)'},
            {'downstream': 'i', 'shift_id': 'S27', 'note': 'ي→i/ī (vowelized, loses consonantal quality)'},
        ],
        'quranic_stats': {
            'tokens_any_position': 8429, 'distinct_roots_any': 224, 'roots_as_first': 13,
            'top5_first': [('ي-و-م', 551), ('ي-م-ن', 125), ('ي-د-ي', 106), ('ي-ت-م', 49), ('ي-س-ر', 31)],
            'top5_second': [('أ-ي-ي', 388), ('ش-ي-أ', 355), ('ب-ي-ن', 282), ('خ-ي-ر', 191), ('ح-ي-ي', 153)],
            'top5_third': [('أ-ي-ي', 388), ('أ-ت-ي', 385), ('ه-د-ي', 259), ('و-ل-ي', 204), ('و-ق-ي', 162)],
            'muqattaat': ['يس — Surah 36. كهيعص — Surah 19'],
        },
        'semantic_tendency': 'CONTRACTION. REACHING. TIME. ASPIRATION. '
                             'ي is the letter of REACHING FORWARD: ي-و-م (day = a unit of time extending), '
                             'ي-د-ي (hand = what reaches), ي-م-ن (right side = the reaching hand). '
                             'As يَا it CALLS OUT — reaching toward the addressed.',
        'paired_letters': {
            'و (wāw)': 'ي-و = extension + connection (ي-و-م day). A day = connected extension of time.',
            'م (mīm)': 'ي-م = extension + seal (ي-م-ن oath). An oath = sealed extension.',
            'د (dāl)': 'ي-د = extension + position (ي-د-ي hand). Hand = positioned extension.',
        },
        'unique': 'Abjad 10. DUAL nature like و — consonant + vowel. '
                  'يَا = the VOCATIVE — how you CALL someone. The reaching call. '
                  'ي-و-م (551) = day — the fundamental unit of TIME in the Qur\'an. '
                  'Q1:4 مَالِكِ يَوْمِ الدِّينِ — Master of the يَوْم of the دِين. '
                  'In the أَمْر system, ي = the iterator/pointer — what reaches toward the next element.',
    },
}

# ALL 28 letters COMPLETE. Phase 0 delivered.

# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def abjad_value(word):
    """Compute abjad value of any AA word."""
    return sum(ABJAD.get(c, 0) for c in word)

def abjad_div7(word):
    """Check if abjad value is divisible by 7."""
    val = abjad_value(word)
    return val, val % 7 == 0, val // 7 if val % 7 == 0 else None

def letter_info(letter):
    """Return full info for a letter, or None if not yet populated."""
    return ALPHABET.get(letter)

def all_letters():
    """Return all 29 entries (hamza + 28 letters) in order."""
    return list('ءابتثجحخدذرزسشصضطظعغفقكلمنهوي')

def all_letters_28():
    """Return the 28 standard letters (without separate hamza)."""
    return list('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')

def populated_count():
    """How many entries have full data."""
    return sum(1 for l in all_letters() if l in ALPHABET and 'phonetic' in ALPHABET[l])

def validate_alphabet():
    """Ensure all entries have all required fields. Returns list of issues."""
    required = ['name', 'transliteration', 'abjad', 'phonetic',
                'classification', 'behaviour', 'shifts',
                'quranic_stats', 'semantic_tendency', 'paired_letters', 'unique']
    issues = []
    for letter in all_letters():
        data = ALPHABET.get(letter)
        if not data:
            issues.append(f'{letter}: MISSING ENTIRELY')
            continue
        for field in required:
            if field not in data:
                issues.append(f'{letter} ({data.get("name", "?")}): missing \'{field}\'')
    return issues

def export_json(filepath='amr_alphabet.json'):
    """Export alphabet as JSON for downstream tools."""
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ALPHABET, f, ensure_ascii=False, indent=2)
    return filepath


def compute_root_meaning(root_letters_str):
    """
    حِسَاب مَعْنَى الجَذْر — Compute root meaning from letter values.

    Takes root letters (e.g. 'ر-ح-م' or 'رحم') and derives meaning
    from each letter's abjad value, semantic tendency, and positional
    behaviour (as_first_radical, as_second_radical, as_third_radical).

    Returns dict with:
      letters: list of letter analyses
      abjad_sum: total abjad value
      abjad_product: positional product (1st * 2nd * 3rd)
      semantic_core: derived meaning from letter combination
      positional: meaning derived from each letter's role at its position
    """
    # Normalize hamza variants to base forms
    HAMZA_MAP = {
        'أ': 'ء', 'إ': 'ء', 'آ': 'ء', 'ؤ': 'ء', 'ئ': 'ء',  # all hamza → ء
        'ى': 'ي', 'ة': 'ه',  # alif maqsura → ya, ta marbuta → ha
    }
    raw = root_letters_str.replace('-', '')
    letters = [HAMZA_MAP.get(c, c) for c in raw if HAMZA_MAP.get(c, c) in ALPHABET]
    if not letters:
        return None

    analyses = []
    abjad_sum = 0
    positional_meanings = []
    semantic_parts = []

    positions = ['as_first_radical', 'as_second_radical', 'as_third_radical']

    for i, letter in enumerate(letters):
        data = ALPHABET.get(letter)
        if not data:
            continue

        abjad_val = data.get('abjad', ABJAD.get(letter, 0))
        abjad_sum += abjad_val

        tendency = data.get('semantic_tendency', '')
        # First word of tendency = core concept
        core = tendency.split('.')[0].strip() if tendency else ''
        semantic_parts.append(core)

        # Positional behaviour
        pos_key = positions[i] if i < len(positions) else positions[-1]
        behaviour = data.get('behaviour', {})
        pos_meaning = behaviour.get(pos_key, '')

        analyses.append({
            'letter': letter,
            'name': data.get('name', ''),
            'abjad': abjad_val,
            'position': i + 1,
            'semantic_tendency': tendency,
            'core_concept': core,
            'positional_behaviour': pos_meaning,
        })

        positional_meanings.append(pos_meaning)

    # Build semantic core from letter combination
    if len(semantic_parts) >= 3:
        semantic_core = f'{semantic_parts[0]} + {semantic_parts[1]} + {semantic_parts[2]}'
    elif len(semantic_parts) == 2:
        semantic_core = f'{semantic_parts[0]} + {semantic_parts[1]}'
    else:
        semantic_core = semantic_parts[0] if semantic_parts else ''

    return {
        'root': root_letters_str,
        'letters': analyses,
        'abjad_sum': abjad_sum,
        'semantic_parts': semantic_parts,
        'semantic_core': semantic_core,
        'positional': positional_meanings,
    }


def compute_root_meaning_text(root_letters_str):
    """
    Return a single-line human-readable meaning derived from letter values.
    This is what goes into roots.primary_meaning and entries.qur_meaning.
    """
    result = compute_root_meaning(root_letters_str)
    if not result:
        return None

    parts = []
    for a in result['letters']:
        parts.append(f"{a['letter']}({a['abjad']})={a['core_concept']}")

    return ' | '.join(parts) + f" [={result['abjad_sum']}]"


if __name__ == '__main__':
    total = len(all_letters())
    done = populated_count()
    print(f'أَمْر ALPHABET: {done}/{total} entries populated')
    print()
    for letter in all_letters():
        info = ALPHABET.get(letter)
        if info and 'phonetic' in info:
            print(f'  {letter} ({info["name"]}) — abjad {info["abjad"]} — COMPLETE')
        else:
            print(f'  {letter} — abjad {ABJAD.get(letter, "?")} — PENDING')

    print()
    issues = validate_alphabet()
    if issues:
        print(f'VALIDATION: {len(issues)} issues found:')
        for issue in issues:
            print(f'  ✗ {issue}')
    else:
        print('VALIDATION: ALL PASS — every entry has all 11 required fields.')
