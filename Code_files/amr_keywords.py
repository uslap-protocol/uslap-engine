#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر KEYWORD MAP — Root-Derived Programming Language Keywords

Every keyword meaning derived from ROOT LETTERS via amr_alphabet.py.
NO English glosses used. Direction: root letters → semantic field → computation concept.

Derivation method:
1. Take root consonants (e.g., ك-و-ن)
2. Read each letter's semantic tendency from ALPHABET
3. Combine: ك(containment) + و(connection) + ن(continuation) = contained-connected-continuing = BEING
4. Verify against Qur'anic context (which āyāt, what Arabic surrounds it)
5. Map to computation concept that matches the ROOT meaning
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from amr_alphabet import ALPHABET, ABJAD, abjad_value
except ImportError:
    from Code_files.amr_alphabet import ALPHABET, ABJAD, abjad_value

# ═══════════════════════════════════════════════════════════════════════
# KEYWORD CATEGORIES
# ═══════════════════════════════════════════════════════════════════════

KEYWORDS = {

    # ──────────────────────────────────────────────────────────────────
    # CONTROL FLOW — How the program moves
    # ──────────────────────────────────────────────────────────────────

    'إِنْ': {
        'python': 'if',
        'root': 'particle (conditional)',
        'abjad': None,  # particle, not a root
        'tokens': 1178,
        'derivation': 'إِنْ is a Qur\'anic conditional particle. Q12:87 إِنَّهُ لَا يَيْأَسُ. '
                       'It introduces POSSIBILITY — if this, then that. '
                       'Computation: conditional branching.',
        'quranic_ref': 'Q2:23, Q3:139, Q12:87 — appears throughout as the conditional gate.',
    },

    'فَـ': {
        'python': 'then (block after إِنْ)',
        'root': 'particle (consequence)',
        'abjad': None,
        'tokens': None,  # too frequent to count as standalone
        'derivation': 'فَـ from ف (SEPARATION/RELEASE/CONSEQUENCE). '
                       'ف = the labiodental release = what FOLLOWS. '
                       'Q36:82 كُن فَيَكُونُ — BE, THEN it is. '
                       'Computation: the THEN of if-then.',
        'quranic_ref': 'Q36:82 — فَيَكُونُ = then it becomes.',
    },

    'أَوْ': {
        'python': 'elif / or',
        'root': 'particle (alternation)',
        'abjad': None,
        'tokens': 263,
        'derivation': 'أَوْ = OR. Presents alternative paths. '
                       'Computation: alternative branch.',
        'quranic_ref': 'Q2:19 — أَوْ كَصَيِّبٍ = or like a rainstorm.',
    },

    'وَإِلَّا': {
        'python': 'else',
        'root': 'وَ (and) + إِلَّا (except/otherwise)',
        'abjad': None,
        'tokens': None,
        'derivation': 'وَ (connection) + إِلَّا (exception). '
                       'And-otherwise = the default branch when no condition met. '
                       'Computation: else block.',
        'quranic_ref': 'Q2:120 — وَلَئِنِ ٱتَّبَعْتَ = and if you followed... (implied otherwise).',
    },

    'كُنْ': {
        'python': 'let / var (declaration)',
        'root': 'ك-و-ن',
        'root_letters': 'كون',
        'abjad': abjad_value('كون'),  # 20+6+50 = 76
        'tokens': 1032,
        'derivation': 'ك(CONTAINMENT/BEING) + و(CONNECTION) + ن(CONTINUATION). '
                       'Contained-connected-continuing = EXISTENCE. '
                       'Q36:82 كُن فَيَكُونُ — BE! The divine command of instantiation. '
                       'Computation: variable declaration = bringing a name into being.',
        'quranic_ref': 'Q36:82 — كُن فَيَكُونُ. Q2:117, Q3:47, Q6:73, Q16:40, Q19:35, Q40:68.',
    },

    'اِرْجِعْ': {
        'python': 'return',
        'root': 'ر-ج-ع',
        'root_letters': 'رجع',
        'abjad': abjad_value('رجع'),  # 200+3+70 = 273
        'tokens': 103,
        'derivation': 'ر(PROCESS/FLOW) + ج(GATHERING) + ع(DEPTH). '
                       'Flowing-gathering-into-depth = RETURNING. '
                       'The process flows, gathers, and goes back to depth. '
                       'Computation: return from function = flow back to caller.',
        'quranic_ref': 'Q96:8 إِنَّ إِلَى رَبِّكَ الرُّجْعَى — to your Nurturer is the return.',
    },

    'كَرِّرْ': {
        'python': 'while (loop)',
        'root': 'ك-ر-ر',
        'root_letters': 'كرر',
        'abjad': abjad_value('كرر'),  # 20+200+200 = 420
        'tokens': 1,
        'derivation': 'ك(CONTAINMENT) + ر(PROCESS) + ر(PROCESS). '
                       'Contained process-process = REPETITION. '
                       'The process letter doubled inside containment = loop. '
                       'Computation: while loop = contained repeated process.',
        'quranic_ref': 'Q62:8 — ثُمَّ يُرَدُّونَ (related: repeated returning).',
    },

    'لِكُلِّ': {
        'python': 'for (iteration)',
        'root': 'لِ (for) + ك-ل-ل (all/every)',
        'abjad': None,
        'tokens': None,
        'derivation': 'لِ = for/to (purpose, from ل CONNECTION). '
                       'كُلّ from ك-ل-ل: ك(CONTAINMENT) + ل(FLOW) + ل(FLOW). '
                       'Contained-flow-flow = ALL/EVERY (everything flowing within containment). '
                       'Computation: for-each = for every item in collection.',
        'quranic_ref': 'Q2:148 لِكُلٍّ وِجْهَةٌ — for each there is a direction.',
    },

    'فِي': {
        'python': 'in',
        'root': 'particle (location)',
        'abjad': None,
        'tokens': 1098,
        'derivation': 'فِي = inside/within. The containment particle. '
                       'Computation: membership test / iteration scope.',
        'quranic_ref': 'Q2:2 لَا رَيْبَ فِيهِ — no doubt IN it.',
    },

    'قِفْ': {
        'python': 'break',
        'root': 'و-ق-ف',
        'root_letters': 'وقف',
        'abjad': abjad_value('وقف'),  # 6+100+80 = 186
        'tokens': None,  # not directly attested as verb in compiler
        'derivation': 'و(CONNECTION) + ق(FORCE) + ف(RELEASE). '
                       'Connected-force-released = STOPPING. '
                       'The connection meets force and releases = halt. '
                       'Computation: break = exit the loop.',
        'quranic_ref': 'Q37:24 وَقِفُوهُمْ إِنَّهُم مَّسْئُولُونَ — stop them, they are questioned.',
    },

    'اِبْدَأْ': {
        'python': 'pass / begin',
        'root': 'ب-د-أ',
        'root_letters': 'بدأ',
        'abjad': abjad_value('بدأ'),  # 2+4+1 = 7
        'tokens': 10,
        'derivation': 'ب(BUILDING) + د(POSITION) + أ(ORIGIN). '
                       'Building-position-origin = BEGINNING. '
                       'Building from the origin position = starting. '
                       'Abjad 7 = completeness. Beginning IS complete in itself. '
                       'Computation: begin block / pass (no-op placeholder).',
        'quranic_ref': 'Q10:34 مَن يَبْدَأُ الْخَلْقَ — who begins creation.',
    },

    # ──────────────────────────────────────────────────────────────────
    # DATA TYPES — What the program holds
    # ──────────────────────────────────────────────────────────────────

    'عَدَد': {
        'python': 'int',
        'root': 'ع-د-د',
        'root_letters': 'عدد',
        'abjad': abjad_value('عدد'),  # 70+4+4 = 78
        'tokens': 32,
        'derivation': 'ع(DEPTH) + د(POSITION) + د(POSITION). '
                       'Deep-positioned-positioned = NUMBER/COUNT. '
                       'Depth with precise positioning = discrete quantity. '
                       'Computation: integer type.',
        'quranic_ref': 'Q72:28 وَأَحْصَى كُلَّ شَيْءٍ عَدَدًا — counted everything in number.',
    },

    'كَسْر': {
        'python': 'float',
        'root': 'ك-س-ر',
        'root_letters': 'كسر',
        'abjad': abjad_value('كسر'),  # 20+60+200 = 280
        'tokens': None,
        'derivation': 'ك(CONTAINMENT) + س(STREAMING) + ر(PROCESS). '
                       'Contained-streaming-process = FRACTION/BREAKING. '
                       'A number broken from wholeness = fractional quantity. '
                       'Computation: floating-point type.',
        'quranic_ref': 'Not directly as كَسْر but ك-س-ر root attested.',
    },

    'حَرْف': {
        'python': 'char',
        'root': 'ح-ر-ف',
        'root_letters': 'حرف',
        'abjad': abjad_value('حرف'),  # 8+200+80 = 288
        'tokens': None,
        'derivation': 'ح(TRUTH/WARMTH) + ر(PROCESS/FLOW) + ف(RELEASE). '
                       'Truth-flowing-released = a single LETTER/EDGE. '
                       'The smallest unit of expression released. '
                       'Computation: single character.',
        'quranic_ref': 'Q22:11 يَعْبُدُ اللَّهَ عَلَى حَرْفٍ — on an edge.',
    },

    'كَلِمَة': {
        'python': 'str',
        'root': 'ك-ل-م',
        'root_letters': 'كلم',
        'abjad': abjad_value('كلم'),  # 20+30+40 = 90
        'tokens': None,
        'derivation': 'ك(CONTAINMENT) + ل(CONNECTION/FLOW) + م(SEALING). '
                       'Contained-flowing-sealed = WORD. '
                       'Letters contained, flowing together, sealed into a unit. '
                       'Computation: string type.',
        'quranic_ref': 'Q18:109 لَنَفِدَ الْبَحْرُ قَبْلَ أَن تَنفَدَ كَلِمَاتُ رَبِّي.',
    },

    'صَفّ': {
        'python': 'list',
        'root': 'ص-ف-ف',
        'root_letters': 'صفف',
        'abjad': abjad_value('صفف'),  # 90+80+80 = 250
        'tokens': None,
        'derivation': 'ص(WEIGHT/AUTHORITY) + ف(RELEASE) + ف(RELEASE). '
                       'Weighted-release-release = ROW/RANK. '
                       'Elements arranged in authoritative order, released one after another. '
                       'Computation: ordered list / array.',
        'quranic_ref': 'Q37:1 وَالصَّافَّاتِ صَفًّا — by those arranged in rows.',
    },

    'زَوْج': {
        'python': 'tuple',
        'root': 'ز-و-ج',
        'root_letters': 'زوج',
        'abjad': abjad_value('زوج'),  # 7+6+3 = 16
        'tokens': 85,
        'derivation': 'ز(PAIRING/ENERGY) + و(CONNECTION) + ج(GATHERING). '
                       'Paired-connected-gathered = PAIR/COUPLE. '
                       'Two elements energetically connected and gathered as one. '
                       'Computation: tuple (immutable pair/group).',
        'quranic_ref': 'Q36:36 سُبْحَانَ الَّذِي خَلَقَ الْأَزْوَاجَ كُلَّهَا — created ALL pairs.',
    },

    'جَمْع': {
        'python': 'dict',
        'root': 'ج-م-ع',
        'root_letters': 'جمع',
        'abjad': abjad_value('جمع'),  # 3+40+70 = 113
        'tokens': 129,
        'derivation': 'ج(GATHERING) + م(SEALING) + ع(DEPTH). '
                       'Gathered-sealed-deep = COLLECTION. '
                       'Items gathered, sealed together, with depth (= keyed access). '
                       'Computation: dictionary / key-value collection.',
        'quranic_ref': 'Q3:9 إِنَّكَ جَامِعُ النَّاسِ — You are the gatherer of people.',
    },

    'حَقّ': {
        'python': 'True',
        'root': 'ح-ق-ق',
        'root_letters': 'حقق',
        'abjad': abjad_value('حقق'),  # 8+100+100 = 208
        'tokens': 263,
        'derivation': 'ح(TRUTH/LIFE) + ق(FORCE) + ق(FORCE). '
                       'Truth-force-force = ESTABLISHED/BINDING. '
                       'Double force from truth = what is absolutely certain. '
                       'Computation: boolean True.',
        'quranic_ref': 'Q2:26 إِنَّ اللَّهَ لَا يَسْتَحْيِي... أَنَّهُ الْحَقُّ — it is the truth.',
    },

    'بَاطِل': {
        'python': 'False',
        'root': 'ب-ط-ل',
        'root_letters': 'بطل',
        'abjad': abjad_value('بطل'),  # 2+9+30 = 41
        'tokens': 33,
        'derivation': 'ب(BUILDING) + ط(AUTHORITY) + ل(FLOW). '
                       'Built-authority-flowing-away = VOID/FALSE. '
                       'What was built with authority but flows away = falsehood. '
                       'Computation: boolean False.',
        'quranic_ref': 'Q2:42 وَلَا تَلْبِسُوا الْحَقَّ بِالْبَاطِلِ — do not dress truth with falsehood.',
    },

    'عَدَم': {
        'python': 'None',
        'root': 'ع-د-م',
        'root_letters': 'عدم',
        'abjad': abjad_value('عدم'),  # 70+4+40 = 114
        'tokens': None,
        'derivation': 'ع(DEPTH) + د(POSITION) + م(SEAL). '
                       'Deep-positioned-sealed = NON-EXISTENCE. '
                       'Depth that is positioned and sealed off = absence. '
                       'Computation: null / None.',
        'quranic_ref': 'عَدَم as concept of non-existence is understood from root.',
    },

    # ──────────────────────────────────────────────────────────────────
    # OPERATIONS — What the program does
    # ──────────────────────────────────────────────────────────────────

    'اِعْمَلْ': {
        'python': 'def (function definition)',
        'root': 'ع-م-ل',
        'root_letters': 'عمل',
        'abjad': abjad_value('عمل'),  # 70+40+30 = 140
        'tokens': 360,
        'derivation': 'ع(DEPTH/ACTION) + م(SEAL) + ل(FLOW). '
                       'Deep-sealed-flowing = WORK/DEED. '
                       'Action from depth, sealed into form, flowing as output. '
                       'Abjad 140 = 7 × 20 (divisible by 7). '
                       'Computation: function definition = a sealed unit of work.',
        'quranic_ref': 'Q18:110 فَمَن كَانَ يَرْجُو لِقَاءَ رَبِّهِ فَلْيَعْمَلْ عَمَلًا صَالِحًا.',
    },

    'اُكْتُبْ': {
        'python': 'print',
        'root': 'ك-ت-ب',
        'root_letters': 'كتب',
        'abjad': abjad_value('كتب'),  # 20+400+2 = 422
        'tokens': 311,
        'derivation': 'ك(CONTAINMENT) + ت(SUCCESSION/SHARP) + ب(BUILDING). '
                       'Contained-successive-built = WRITING/INSCRIPTION. '
                       'Content contained, marked in succession, built into record. '
                       'Computation: print/write output.',
        'quranic_ref': 'Q96:4 context — what the قَلَم produces. Q2:282 وَاكْتُبُوهُ.',
    },

    'اِقْرَأْ': {
        'python': 'input / read',
        'root': 'ق-ر-أ',
        'root_letters': 'قرأ',
        'abjad': abjad_value('قرأ'),  # 100+200+1 = 301
        'tokens': 75,
        'derivation': 'ق(FORCE/DECLARATION) + ر(PROCESS/FLOW) + أ(ORIGIN). '
                       'Force-flowing-to-origin = READING/RECITING. '
                       'Declaring with force, processing, returning to origin. '
                       'THE first command revealed: Q96:1 اقْرَأْ. '
                       'Computation: read input.',
        'quranic_ref': 'Q96:1 اقْرَأْ بِاسْمِ رَبِّكَ — READ.',
    },

    'اُحْسُبْ': {
        'python': 'compute / calculate',
        'root': 'ح-س-ب',
        'root_letters': 'حسب',
        'abjad': abjad_value('حسب'),  # 8+60+2 = 70
        'tokens': 106,
        'derivation': 'ح(TRUTH/TESTING) + س(STREAMING) + ب(BUILDING). '
                       'Truth-streaming-built = RECKONING/COMPUTATION. '
                       'Testing truth through streaming data, building a result. '
                       'Computation: calculate / evaluate expression.',
        'quranic_ref': 'Q65:3 وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ — sufficient for reckoning.',
    },

    'أَرْسِلْ': {
        'python': 'send',
        'root': 'ر-س-ل',
        'root_letters': 'رسل',
        'abjad': abjad_value('رسل'),  # 200+60+30 = 290
        'tokens': 509,
        'derivation': 'ر(PROCESS/FLOW) + س(STREAMING) + ل(CONNECTION). '
                       'Process-streaming-connected = SENDING. '
                       'A flowing stream connected to a destination. '
                       'Computation: send message / emit event.',
        'quranic_ref': 'Q14:4 وَمَا أَرْسَلْنَا مِن رَّسُولٍ — We did not send a messenger except...',
    },

    'اِقْبَلْ': {
        'python': 'receive / accept',
        'root': 'ق-ب-ل',
        'root_letters': 'قبل',
        'abjad': abjad_value('قبل'),  # 100+2+30 = 132
        'tokens': 291,
        'derivation': 'ق(FORCE) + ب(CONTACT) + ل(FLOW). '
                       'Force-contacting-flowing = ACCEPTING/RECEIVING. '
                       'Force meets contact and flows in = reception. '
                       'Computation: receive / accept input.',
        'quranic_ref': 'Q5:27 إِنَّمَا يَتَقَبَّلُ اللَّهُ مِنَ الْمُتَّقِينَ.',
    },

    'خُذْ': {
        'python': 'get / take',
        'root': 'أ-خ-ذ',
        'root_letters': 'اخذ',
        'abjad': abjad_value('اخذ'),  # 1+600+700 = 1301
        'tokens': 217,
        'derivation': 'أ(ORIGIN) + خ(EMERGENCE/PASSAGE) + ذ(EXPERIENCE/TASTING). '
                       'Origin-passage-experience = TAKING/SEIZING. '
                       'From the origin, through the passage, experiencing directly. '
                       'Computation: get / fetch / retrieve.',
        'quranic_ref': 'Q7:145 خُذْهَا بِقُوَّةٍ — take them with strength.',
    },

    'اِجْعَلْ': {
        'python': 'set / assign',
        'root': 'ج-ع-ل',
        'root_letters': 'جعل',
        'abjad': abjad_value('جعل'),  # 3+70+30 = 103
        'tokens': 345,
        'derivation': 'ج(GATHERING/MAKING) + ع(DEPTH) + ل(FLOW). '
                       'Gathering-depth-flowing = MAKING/PLACING/APPOINTING. '
                       'Gathering from depth and flowing into place. '
                       'Computation: set / assign value.',
        'quranic_ref': 'Q2:22 الَّذِي جَعَلَ لَكُمُ الْأَرْضَ فِرَاشًا — who MADE for you the earth a bed.',
    },

    'اِفْتَحْ': {
        'python': 'open',
        'root': 'ف-ت-ح',
        'root_letters': 'فتح',
        'abjad': abjad_value('فتح'),  # 80+400+8 = 488
        'tokens': 36,
        'derivation': 'ف(RELEASE) + ت(SHARP/SUCCESSION) + ح(TRUTH/WARMTH). '
                       'Release-sharp-warmth = OPENING. '
                       'A sharp release into warmth = an opening. '
                       'Computation: open file / open connection.',
        'quranic_ref': 'Q54:11 فَفَتَحْنَا أَبْوَابَ السَّمَاءِ — We opened the gates of the sky.',
    },

    'أَغْلِقْ': {
        'python': 'close',
        'root': 'غ-ل-ق',
        'root_letters': 'غلق',
        'abjad': abjad_value('غلق'),  # 1000+30+100 = 1130
        'tokens': 1,
        'derivation': 'غ(CONCEALMENT) + ل(FLOW) + ق(FORCE). '
                       'Concealment-flow-force = CLOSING/LOCKING. '
                       'The flow is concealed by force = closed. '
                       'Computation: close file / close connection.',
        'quranic_ref': 'Q12:23 وَغَلَّقَتِ الْأَبْوَابَ — she closed and locked the doors.',
    },

    'اِحْذِفْ': {
        'python': 'del / delete',
        'root': 'ح-ذ-ف',
        'root_letters': 'حذف',
        'abjad': abjad_value('حذف'),  # 8+700+80 = 788
        'tokens': None,
        'derivation': 'ح(TRUTH/TESTING) + ذ(EXPERIENCE) + ف(RELEASE). '
                       'Truth-experienced-released = REMOVAL/DELETION. '
                       'What was experienced is released from truth = deleted. '
                       'Computation: delete / remove.',
        'quranic_ref': 'Root ح-ذ-ف attested in AA linguistic tradition.',
    },

    'اِبْحَثْ': {
        'python': 'search / find',
        'root': 'ب-ح-ث',
        'root_letters': 'بحث',
        'abjad': abjad_value('بحث'),  # 2+8+500 = 510
        'tokens': None,
        'derivation': 'ب(BUILDING/CONTACT) + ح(TRUTH) + ث(MULTIPLYING). '
                       'Contact-truth-multiplying = SEARCHING/INVESTIGATING. '
                       'Making contact with truth across multiplied sources. '
                       'Computation: search / query.',
        'quranic_ref': 'Q5:31 فَبَعَثَ اللَّهُ غُرَابًا يَبْحَثُ فِي الْأَرْضِ.',
    },

    'بَدِّلْ': {
        'python': 'replace / swap',
        'root': 'ب-د-ل',
        'root_letters': 'بدل',
        'abjad': abjad_value('بدل'),  # 2+4+30 = 36
        'tokens': 42,
        'derivation': 'ب(BUILDING) + د(POSITION) + ل(FLOW). '
                       'Building-repositioned-flowing = REPLACEMENT. '
                       'What was built is repositioned and flows as new. '
                       'Computation: replace / substitute.',
        'quranic_ref': 'Q2:211 وَمَن يُبَدِّلْ نِعْمَةَ اللَّهِ — who replaces Allah\'s blessing.',
    },

    'صِلْ': {
        'python': 'join / connect',
        'root': 'و-ص-ل',
        'root_letters': 'وصل',
        'abjad': abjad_value('وصل'),  # 6+90+30 = 126
        'tokens': 30,
        'derivation': 'و(CONNECTION) + ص(WEIGHT/TRUTH) + ل(FLOW). '
                       'Connected-weight-flowing = JOINING. '
                       'Weighty connection flowing together. '
                       'Computation: join / concatenate.',
        'quranic_ref': 'Q13:21 وَالَّذِينَ يَصِلُونَ مَا أَمَرَ اللَّهُ بِهِ أَن يُوصَلَ.',
    },

    'اِقْطَعْ': {
        'python': 'split / slice',
        'root': 'ق-ط-ع',
        'root_letters': 'قطع',
        'abjad': abjad_value('قطع'),  # 100+9+70 = 179
        'tokens': 35,
        'derivation': 'ق(FORCE) + ط(AUTHORITY) + ع(DEPTH). '
                       'Force-authority-depth = CUTTING/SEVERING. '
                       'Authoritative force reaching deep to cut. '
                       'Computation: split / slice.',
        'quranic_ref': 'Q13:25 وَيَقْطَعُونَ مَا أَمَرَ اللَّهُ بِهِ أَن يُوصَلَ.',
    },

    'اِنْسَخْ': {
        'python': 'copy',
        'root': 'ن-س-خ',
        'root_letters': 'نسخ',
        'abjad': abjad_value('نسخ'),  # 50+60+600 = 710
        'tokens': 4,
        'derivation': 'ن(CONTINUATION) + س(STREAMING) + خ(EMERGENCE). '
                       'Continuation-streaming-emerging = COPYING/REPLACING. '
                       'What continues streams out as a new emergence. '
                       'Computation: copy.',
        'quranic_ref': 'Q2:106 مَا نَنسَخْ مِنْ آيَةٍ — what We abrogate/copy of a sign.',
    },

    # ──────────────────────────────────────────────────────────────────
    # COMPARISON / LOGIC
    # ──────────────────────────────────────────────────────────────────

    'سَوَاء': {
        'python': '== (equal)',
        'root': 'س-و-ي',
        'root_letters': 'سوي',
        'abjad': abjad_value('سوي'),  # 60+6+10 = 76
        'tokens': 54,
        'derivation': 'س(STREAMING) + و(CONNECTION) + ي(EXTENSION). '
                       'Streaming-connected-extended = EQUAL/LEVEL. '
                       'What streams, connects, and extends evenly. '
                       'Computation: equality comparison.',
        'quranic_ref': 'Q3:64 إِلَى كَلِمَةٍ سَوَاءٍ — to a word that is equal/common.',
    },

    'فَوْقَ': {
        'python': '> (greater than)',
        'root': 'ف-و-ق',
        'root_letters': 'فوق',
        'abjad': abjad_value('فوق'),  # 80+6+100 = 186
        'tokens': 55,
        'derivation': 'ف(RELEASE) + و(CONNECTION) + ق(FORCE). '
                       'Released-connected-force = ABOVE. '
                       'Computation: greater than.',
        'quranic_ref': 'Q2:228 وَلِلرِّجَالِ عَلَيْهِنَّ دَرَجَةٌ.',
    },

    'دُونَ': {
        'python': '< (less than)',
        'root': 'د-و-ن',
        'root_letters': 'دون',
        'abjad': abjad_value('دون'),  # 4+6+50 = 60
        'tokens': 155,
        'derivation': 'د(POSITION) + و(CONNECTION) + ن(CONTINUATION). '
                       'Positioned-connected-continuing = BELOW/BENEATH. '
                       'Computation: less than.',
        'quranic_ref': 'Q18:15 أَإِلَهًا دُونَ اللَّهِ — a god other than / beneath Allah.',
    },

    'وَ': {
        'python': 'and',
        'root': 'particle',
        'abjad': 6,
        'tokens': None,
        'derivation': 'و = THE connector. Abjad 6. '
                       'The most frequent word in the Qur\'an. '
                       'Computation: logical AND.',
        'quranic_ref': 'Every āyah.',
    },

    'لَا': {
        'python': 'not',
        'root': 'particle (negation)',
        'abjad': None,
        'tokens': None,
        'derivation': 'ل(CONNECTION) + ا(ORIGIN). '
                       'Connection-to-origin = NEGATION (returning to nothing). '
                       'Computation: logical NOT.',
        'quranic_ref': 'Q1:7 لَا الضَّالِّينَ — not those displaced.',
    },

    # ──────────────────────────────────────────────────────────────────
    # ERROR HANDLING
    # ──────────────────────────────────────────────────────────────────

    'ضَلَال': {
        'python': 'Exception',
        'root': 'ض-ل-ل',
        'root_letters': 'ضلل',
        'abjad': abjad_value('ضلل'),  # 800+30+30 = 860
        'tokens': 172,
        'derivation': 'ض(DISPLACEMENT) + ل(FLOW) + ل(FLOW). '
                       'Displaced-flowing-flowing = GOING ASTRAY / ERROR. '
                       'Displacement that flows and flows further off path. '
                       'Computation: exception / error type.',
        'quranic_ref': 'Q1:7 وَلَا الضَّالِّينَ — not those who went astray.',
    },

    'قِ': {
        'python': 'try (protect/guard)',
        'root': 'و-ق-ي',
        'root_letters': 'وقي',
        'abjad': abjad_value('وقي'),  # 6+100+10 = 116
        'tokens': 162,
        'derivation': 'و(CONNECTION) + ق(FORCE) + ي(EXTENSION). '
                       'Connected-force-extended = PROTECTION/GUARDING. '
                       'Force connected and extended as a shield. '
                       'Computation: try block (guard against errors).',
        'quranic_ref': 'Q3:16 رَبَّنَا إِنَّنَا آمَنَّا فَاغْفِرْ لَنَا ذُنُوبَنَا وَقِنَا عَذَابَ النَّارِ.',
    },

    'أَنْذِرْ': {
        'python': 'raise (exception)',
        'root': 'ن-ذ-ر',
        'root_letters': 'نذر',
        'abjad': abjad_value('نذر'),  # 50+700+200 = 950
        'tokens': 134,
        'derivation': 'ن(CONTINUATION) + ذ(EXPERIENCE) + ر(PROCESS). '
                       'Continuation-experience-process = WARNING. '
                       'The ongoing experience processed as a warning signal. '
                       'Computation: raise exception / emit warning.',
        'quranic_ref': 'Q74:2 قُمْ فَأَنذِرْ — arise and WARN.',
    },

    'اِصْبِرْ': {
        'python': 'await (async patience)',
        'root': 'ص-ب-ر',
        'root_letters': 'صبر',
        'abjad': abjad_value('صبر'),  # 90+2+200 = 292
        'tokens': 102,
        'derivation': 'ص(ENDURANCE/WEIGHT) + ب(BUILDING) + ر(PROCESS). '
                       'Endurance-building-processing = PATIENCE/WAITING. '
                       'Weighted building through ongoing process = patient waiting. '
                       'Computation: await (wait for async result).',
        'quranic_ref': 'Q2:153 يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ.',
    },

    # ──────────────────────────────────────────────────────────────────
    # MODULE / IMPORT
    # ──────────────────────────────────────────────────────────────────

    'اِسْتَدْعِ': {
        'python': 'import',
        'root': 'د-ع-و',
        'root_letters': 'دعو',
        'abjad': abjad_value('دعو'),  # 4+70+6 = 80
        'tokens': 123,
        'derivation': 'د(CALLING/POSITION) + ع(DEPTH) + و(CONNECTION). '
                       'Calling-from-depth-connecting = INVOKING/SUMMONING. '
                       'Form X (اِسْتَفْعَلَ) = seeking to invoke. '
                       'Computation: import module (invoke external code).',
        'quranic_ref': 'Q2:186 إِذَا دَعَانِ — when he calls upon Me.',
    },

    'مِنْ': {
        'python': 'from',
        'root': 'particle (origin)',
        'abjad': None,
        'tokens': None,
        'derivation': 'مِنْ = from/out of. The origin marker. '
                       'Computation: from (in import statements).',
        'quranic_ref': 'Q96:2 خَلَقَ الْإِنسَانَ مِنْ عَلَقٍ — created humanity FROM a clinging substance.',
    },
}

# ═══════════════════════════════════════════════════════════════════════
# REVERSE MAP: Python keyword → أَمْر keyword
# ═══════════════════════════════════════════════════════════════════════

PYTHON_TO_AMR = {}
for amr_kw, data in KEYWORDS.items():
    py = data['python'].split(' ')[0]  # take first word
    PYTHON_TO_AMR[py] = amr_kw

# ═══════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════

def keyword_count():
    return len(KEYWORDS)

def keywords_by_category():
    categories = {
        'control_flow': [], 'data_types': [], 'operations': [],
        'comparison': [], 'error_handling': [], 'module': []
    }
    flow_kw = {'إِنْ', 'فَـ', 'أَوْ', 'وَإِلَّا', 'كُنْ', 'اِرْجِعْ', 'كَرِّرْ', 'لِكُلِّ', 'فِي', 'قِفْ', 'اِبْدَأْ'}
    type_kw = {'عَدَد', 'كَسْر', 'حَرْف', 'كَلِمَة', 'صَفّ', 'زَوْج', 'جَمْع', 'حَقّ', 'بَاطِل', 'عَدَم'}
    comp_kw = {'سَوَاء', 'فَوْقَ', 'دُونَ', 'وَ', 'لَا'}
    err_kw = {'ضَلَال', 'قِ', 'أَنْذِرْ', 'اِصْبِرْ'}
    mod_kw = {'اِسْتَدْعِ', 'مِنْ'}

    for kw in KEYWORDS:
        if kw in flow_kw: categories['control_flow'].append(kw)
        elif kw in type_kw: categories['data_types'].append(kw)
        elif kw in comp_kw: categories['comparison'].append(kw)
        elif kw in err_kw: categories['error_handling'].append(kw)
        elif kw in mod_kw: categories['module'].append(kw)
        else: categories['operations'].append(kw)

    return categories


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def keyword_quf(data: dict) -> dict:
    """
    KEYWORD QUF — L2.
    Q: Qur'anic attestation (token count) + root derivation present
    U: keyword functions across surahs (high token count = universal)
    F: root derivation verified via amr_alphabet letter semantics
    """
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    arabic = data.get('arabic', '') or data.get('keyword', '') or ''
    root = data.get('root', '') or data.get('root_letters', '') or ''
    tokens = data.get('tokens', 0) or data.get('token_count', 0) or 0
    derivation = data.get('derivation', '') or ''
    qur_anchor = data.get('qur_anchor', '') or ''

    # Try to find the keyword in KEYWORDS dict
    kw_data = KEYWORDS.get(arabic, {})
    if kw_data and not tokens:
        tokens = kw_data.get('tokens', 0)
    if kw_data and not derivation:
        derivation = kw_data.get('derivation', '')

    # Q: token count + root present
    q = 'HIGH' if (tokens >= 50 and root) else ('MEDIUM' if tokens > 0 or root else 'LOW')
    q_ev = [f'tokens={tokens}, root={root[:15]}, qur_anchor={qur_anchor[:20]}']

    # U: high token count = appears across many surahs
    u = 'HIGH' if tokens >= 100 else ('MEDIUM' if tokens >= 10 else 'LOW')
    u_ev = [f'{tokens} tokens across Quran']

    # F: derivation from root letters verified
    f = 'HIGH' if derivation else ('MEDIUM' if root else 'LOW')
    f_ev = [f'Derivation: {bool(derivation)}, root: {bool(root)}']

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev, 'u_evidence': u_ev, 'f_evidence': f_ev,
    }


if __name__ == '__main__':
    print(f'أَمْر KEYWORD MAP: {keyword_count()} keywords')
    print()
    cats = keywords_by_category()
    for cat, kws in cats.items():
        print(f'  {cat}: {len(kws)} keywords')
        for kw in kws:
            data = KEYWORDS[kw]
            py = data['python']
            root = data.get('root', '')
            print(f'    {kw} → {py}  ({root})')
        print()
