#!/usr/bin/env python3
"""
USLaP Qur'an COMPILER (al-ʿAlaq layer)
Auto-seeds āyāt with root mappings from the root dictionary.

Usage:
    python3 uslap_compiler.py seed 112             # auto-seed sūrah 112
    python3 uslap_compiler.py seed 112:1            # auto-seed single āyah
    python3 uslap_compiler.py load quran.txt        # load Qur'an text (tanzil format)
    python3 uslap_compiler.py status                # show compilation status
    python3 uslap_compiler.py unmapped 112          # show unmapped words in sūrah
    python3 uslap_compiler.py translate 1           # generate Layer 2 for sūrah 1
    python3 uslap_compiler.py translate all         # generate Layer 2 for ALL sūrahs

Text format (for 'load' or built-in):
    surah|ayah|arabic text
"""

import sqlite3
import sys
import os
import re
import unicodedata

DB_PATH = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")

# ── Arabic prefix/suffix stripping tables ──
# Common prefixes in Qur'anic Arabic (ordered longest-first)
PREFIXES = [
    'وَلَ', 'فَلَ', 'وَبِ', 'فَبِ', 'وَلِ', 'فَلِ',
    'أَفَ', 'أَوَ',
    'بِال', 'كَال', 'فَال', 'وَال', 'لِل',
    'وَال', 'فَال',
    'فَسَ', 'وَسَ', 'لَسَ',
    'سَيَ', 'سَنَ', 'سَتَ', 'سَأ',
    'وَأ', 'فَأ',
    'بِ', 'كَ', 'فَ', 'وَ', 'لَ', 'لِ',
    'ال',
]

# Common suffix pronouns
SUFFIXES = [
    'كُمُوهَا', 'كُمُوهُ',
    'هُمَا', 'هُمْ', 'هُنَّ', 'كُمْ', 'كُنَّ', 'نَا',
    'تُمْ', 'تُنَّ',
    'هَا', 'هُ', 'هِ', 'كَ', 'كِ', 'نِي', 'يَ',
    'ونَ', 'ينَ', 'انِ', 'اتٍ', 'ُوا',
]

# Particles (never have roots — just pass through)
PARTICLES = {
    'فِي', 'مِنْ', 'مِن', 'عَلَى', 'إِلَى', 'إِلَّا', 'عَنْ', 'عَن',
    'بَيْنَ', 'بَلْ', 'بَل', 'حَتَّى', 'مُنْذُ', 'مُذْ', 'قَدْ', 'قَد',
    'لَمْ', 'لَم', 'لَنْ', 'لَن', 'لَا', 'مَا', 'إِنْ', 'إِنَّ', 'أَنَّ',
    'أَنْ', 'أَن', 'كَيْ', 'لَوْ', 'لَو', 'أَمْ', 'أَم', 'أَوْ', 'أَو',
    'ثُمَّ', 'ثُمّ', 'وَ', 'فَ',
    'هُوَ', 'هِيَ', 'هُمْ', 'هُمَا', 'هُنَّ', 'أَنَا', 'نَحْنُ',
    'أَنْتَ', 'أَنْتِ', 'أَنْتُمْ', 'أَنْتُنَّ',
    'هَذَا', 'هَذِهِ', 'ذَلِكَ', 'تِلْكَ', 'أُولَئِكَ', 'هَؤُلَاءِ',
    'الَّذِي', 'الَّتِي', 'الَّذِينَ', 'اللَّاتِي', 'اللَّائِي',
    'مَنْ', 'مَن', 'مَاذَا',
    'كُلَّ', 'كُلُّ', 'كُلِّ', 'بَعْضَ', 'بَعْضُ', 'بَعْضِ',
    'عِنْدَ', 'عِندَ', 'لَدَى', 'لَدُنْ',
    'إِذَا', 'إِذْ', 'إِذ',
    'كَيْفَ', 'أَيْنَ', 'مَتَى',
    'يَا', 'أَيُّهَا', 'أَيَّتُهَا',
    'لَيْسَ', 'كَانَ',
    'إِيَّاكَ', 'إِيَّاهُ', 'إِيَّاهُمْ',
    'غَيْرِ', 'غَيْرَ', 'غَيْرُ',
    'وَلَا', 'فَلَا',
    # Compound particles (conjunction + particle)
    'وَمَا', 'فَمَا', 'بِمَا', 'لِمَا', 'كَمَا', 'مِمَّا',
    'وَمَن', 'فَمَن', 'لِمَن',
    'وَإِن', 'فَإِن', 'وَإِنَّ', 'فَإِنَّ',
    'وَأَنَّ', 'فَأَنَّ', 'لِأَنَّ',
    'وَإِذَا', 'فَإِذَا', 'وَإِذْ',
    'فَلَمَّا', 'وَلَمَّا', 'لَمَّا',
    'وَلَكِنَّ', 'وَلَٰكِنَّ', 'لَكِنَّ', 'لَٰكِنَّ',
    'وَلَوْ', 'فَلَوْ',
    'وَلَنْ', 'فَلَنْ',
    'وَلَقَدْ', 'فَلَقَدْ', 'لَقَدْ',
    'وَلَمْ', 'فَلَمْ', 'أَلَمْ',
    'وَهُوَ', 'وَهُمْ', 'وَهِيَ',
    'إِنَّمَا', 'فَإِنَّمَا', 'وَإِنَّمَا',
    'كَذَٰلِكَ', 'فَكَذَٰلِكَ',
    'هَلْ', 'فَهَلْ',
    'بَلَىٰ', 'نَعَمْ', 'كَلَّا',
    # Vocative forms
    'يَٰٓأَيُّهَا', 'يَا',
    # Additional pronouns
    'أَنتُمْ',
    # Preposition+pronoun combos (functional, no extractable root)
    'بِهِ', 'بِهَا', 'بِهِمْ', 'بِنَا', 'بِكُمْ', 'بِكَ', 'بِيَ',
    'لَهُ', 'لَهَا', 'لَهُمْ', 'لَنَا', 'لَكُمْ', 'لَكَ', 'لِي',
    'فِيهِ', 'فِيهَا', 'فِيهِمْ', 'فِينَا', 'فِيكُمْ', 'فِيكَ',
    'عَلَيْهِ', 'عَلَيْهَا', 'عَلَيْهِمْ', 'عَلَيْنَا', 'عَلَيْكُمْ', 'عَلَيْكَ',
    'إِلَيْهِ', 'إِلَيْهَا', 'إِلَيْهِمْ', 'إِلَيْنَا', 'إِلَيْكُمْ', 'إِلَيْكَ',
    'مِنْهُ', 'مِنْهَا', 'مِنْهُمْ', 'مِنْكُمْ', 'مِنْكَ',
    'عَنْهُ', 'عَنْهَا', 'عَنْهُمْ', 'عَنْكُمْ',
    'مَعَهُ', 'مَعَهُمْ', 'مَعَكُمْ', 'مَعَنَا',
    'إِنَّهُ', 'إِنَّهَا', 'إِنَّهُمْ', 'أَنَّهُ', 'أَنَّهَا', 'أَنَّهُمْ',
    'كَأَنَّهُمْ', 'كَأَنَّهُ',
    'لَعَلَّهُمْ', 'لَعَلَّكُمْ', 'لَعَلَّكَ',
    # Compound demonstratives
    'وَذَلِكَ', 'فَذَلِكَ',
    # Tanzil-specific compound particles (conjunction + relative/demonstrative)
    'وَٱلَّذِينَ', 'لِلَّذِينَ', 'فَٱلَّذِينَ',
    # إنّ + pronoun suffixes
    'إِنِّي', 'إِنِّى', 'إِنَّكَ', 'إِنَّكُمْ', 'إِنَّنَا',
    # Additional functional words
    'مَعَ', 'مَعَهُ', 'مَعَهُمْ', 'مَعَكُمْ',
    'أَفَلَا', 'أَوَلَمْ', 'أَفَلَمْ',
    'عَمَّا', 'فِيمَا', 'بِمَ', 'لِمَ', 'عَلَامَ',
    'بَيْنَهُمْ', 'بَيْنَهُمَا', 'بَيْنَكُمْ', 'بَيْنَنَا',
    'وَأَنتُمْ', 'فَأَنتُمْ',
    'فَأُولَئِكَ', 'وَأُولَئِكَ',
    'وَلَهُمْ', 'وَلَهُ', 'وَلَهَا',
    'وَكَذَلِكَ', 'فَكَذَلِكَ',
    'بِكُلِّ', 'وَكُلِّ', 'فَكُلِّ',
    'فَبِأَيِّ', 'بِأَيِّ',
    'وَعَلَى', 'فَعَلَى',
    'وَبَيْنَ', 'فَبَيْنَ',
    'فَأَمَّا', 'وَأَمَّا', 'أَمَّا',
    'إِذْ', 'مُنذُ',
    'لَعَلَّ', 'لَعَلَّهُ', 'لَعَلَّهُمْ', 'لَعَلَّكُمْ',
    # Additional compound particles (from frequency analysis)
    'وَإِنَّا', 'فَهُوَ', 'وَلِلَّهِ', 'لَفِي', 'فَسَوْفَ', 'سَوْفَ',
    'ذَٰلِكُمْ', 'ذَٰلِكُمُ',
    'وَإِنَّهُ', 'بِأَنَّهُمْ', 'بِأَنَّ', 'وَبِأَنَّ',
    'وَمِنْهُم', 'وَمِنْهَا', 'وَمِنْهُ',
    'وَلَئِن', 'فَلَئِن', 'لَئِن',
    'وَإِلَيْهِ', 'وَإِلَيْنَا', 'وَإِلَيْكُمْ',
    'بِإِذْنِ', 'بِإِذْنِهِ', 'بِإِذْنِهِۦ',
    'وَعَلَيْهِمْ', 'وَعَلَيْكُمْ',
    'لَوْلَا', 'وَلَوْلَا', 'فَلَوْلَا',
    'حَيْثُ',
    'بَيْنَهُمَا',
    'وَفِي', 'وَفِيهَا', 'وَفِيهِ',
    'وَبَيْنَهُمْ',
    'فَأَنَّى', 'أَنَّى',
    'كَأَنَّ', 'كَأَنَّمَا',
    'إِنَّمَا', 'كَمَا', 'مِثْلَ', 'مِثْلُ',
    # Phase 1D: Additional particles from frequency analysis of unrooted words
    'ذُو', 'ذِي', 'ذَا', 'ذُوا۟', 'ذُو۟',
    'وَنَحْنُ', 'وَلَكُمْ', 'وَلَكَ',
    'وَهَٰذَا', 'بِهَٰذَا', 'هَٰذَا', 'فَهَٰذَا',
    'وَأَنتَ', 'وَأَنتُمْ',
    'كَمْ', 'وَكَمْ',
    'عَنَّا',
    'عَلَيْهِنَّ', 'لَهُنَّ', 'مِنْهُنَّ', 'بِهِنَّ', 'فِيهِنَّ',
    'أَفَمَن', 'أَفَمَنْ',
    'وَتِلْكَ', 'فَتِلْكَ',
    'أَءِذَا', 'أَئِذَا',
    'وَيْلٌ', 'وَيْلَ',
    'بِذَاتِ', 'ذَاتَ', 'ذَاتِ',
    'فَأَيْنَ', 'وَأَيْنَ',
    'وَلَدَيْنَا', 'لَدَيْهِ', 'لَدَيْنَا', 'لَدَيْهِمْ',
    'وَلَدَيْهِمْ', 'وَلَدَيْهِ',
    'إِيَّاكُمْ', 'إِيَّاهُمْ', 'إِيَّايَ', 'إِيَّانَا',
    # Phase 1D batch 2: more compound particles from unrooted analysis
    'هُنَالِكَ', 'لَذُو', 'بِمَن', 'كَمَن',
    'فَمِنْهُم', 'فَمِنْهُمْ', 'فَهِىَ',
    'وَمِمَّا', 'مِمَّنِ', 'مِمَّن', 'مِّمَّنْ',
    'وَلَعَلَّكُمْ', 'وَمِنكُم', 'وَمِنكُمْ',
    'فَلِلَّهِ', 'أَفَأَنتَ',
    'مِّنْهُمَا', 'مَّعَكَ', 'مَعَكَ',
    'ءَأَنتُمْ', 'ءَأَنتَ', 'هَٰٓأَنتُمْ',
    'حمٓ', 'الٓر', 'المٓر', 'كٓهٰيٰعٓصٓ', 'طسٓمٓ', 'طسٓ', 'يسٓ', 'صٓ', 'قٓ', 'نٓ',
    'فَلَهُۥ', 'ٱلْـَٰٔنَ',
    'عَنكَ', 'عَنِّى', 'فَبِمَا',
    'وَإِنَّهُمْ', 'وَإِنَّكَ', 'أَءِنَّا', 'إِنَّنِى',
    'لَّعَلِّىٓ', 'لَعَلِّى',
    'لَنَحْنُ', 'لَكُمَا',
    'وَمِمَّنْ', 'وَبِمَا',
    'وَأَنَّهُمْ', 'وَأَنَّهُ',
    'فَإِنَّهُ', 'فَإِنَّهُمْ', 'فَإِنَّهَا',
    'يَٰٓأَيُّهَا', 'يَٰقَوْمِ', 'يَٰبَنِىٓ', 'يَٰبَنِى',
    'يَٰٓإِبْرَٰهِيمُ', 'يَٰٓأَبَانَا', 'يَٰٓأَبَتِ',
    'يَٰٓمُوسَىٰ', 'يَٰنُوحُ', 'يَٰمَرْيَمُ',
    'وَلِأَنتُمْ', 'لَأَنتُمْ',
    'عِندَهُ', 'عِندَهُمْ', 'عِندَنَا', 'عِندَكُمْ',
    'وَعِنْدَهُ', 'وَعِندَنَا',
    # Phase 1D batch 3: more particles
    'هَٰهُنَا', 'فَمَاذَا', 'فَلَهَا', 'فَفِى',
    'عَنْهُمَا', 'وَذَا', 'وَهَلْ', 'وَعَنِ', 'وَعَلَيْهَا',
    'بِذَٰلِكَ', 'أَيْنَمَا', 'أَهُمْ',
    'وَإِنَّكُمْ', 'لَنَرَىٰكَ',
    'فَفِيهِ', 'فَفِيهَا', 'وَفِيهِمْ',
    'وَبِهِ', 'وَبِهَا', 'وَبِهِمْ',
    'فَعَلَيْهِ', 'فَعَلَيْهِمْ', 'فَعَلَيْكُمْ',
    'فَلَكُمْ', 'فَلَهُمْ', 'فَلَنَا',
    'وَلَنَا', 'وَلِلْكَٰفِرِينَ',
    'فَعَنْهُمْ', 'وَعَنْهُ',
    'وَمِنْ', 'فَمِنْ',
    'لِّمَنْ', 'لِّمَن',
    'وَإِلَى', 'فَإِلَى',
    'فَعَلَى',
}

# Diacritics to strip for root matching
# Includes standard tashkeel + Qur'anic recitation marks (U+06E5 small waw, U+06E6 small yaa)
# These are NOT ornamental — they carry recitation purpose. Stripped here ONLY for root-matching.
DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
ALEF_VARIANTS = re.compile(r'[إأآٱ]')  # NOT ء (standalone hamza) — it's a distinct letter
TATWEEL = '\u0640'

# Tanzil uses U+0649 (alef maksura/yaa without dots) interchangeably with U+064A (yaa)
# In word-final position this matters for matching particles (فِى vs فِي)
ALEF_MAKSURA = '\u0649'  # ى
YAA = '\u064A'  # ي

# Hamza carriers — all normalize to bare hamza (ء) for root extraction
HAMZA_CARRIERS = re.compile(r'[ؤئ]')
# Tanzil-specific Unicode characters
TANZIL_WASLA = '\u0671'  # ٱ → alef
TANZIL_SMALL_WAW = '\u06E5'  # ۥ
TANZIL_SMALL_YAA = '\u06E6'  # ۦ
TANZIL_SUPERSCRIPT_ALEF = '\u0670'  # ٰ (dagger alef)
TANZIL_HAMZA_ON_TATWEEL = '\u0654'  # ـٔ (hamza above, on tatweel)

# Arabic consonants (for skeleton extraction) — excludes long vowels ا و ي
ARABIC_CONSONANTS = set('بتثجحخدذرزسشصضطظعغفقكلمنهءئؤ')

# Pronoun suffixes (longest first for greedy match)
PRONOUN_SUFFIXES = [
    'كموها', 'كموه',
    'هما', 'هم', 'هن', 'كم', 'كن', 'نا',
    'ها', 'ه', 'ك', 'ني', 'ي',
]

# Case/mood/plural suffixes
GRAM_SUFFIXES = [
    'ون', 'ين', 'ان', 'ات', 'وا', 'تم', 'تن',
]


def strip_diacritics(text):
    """Remove all Arabic diacritical marks including tanzil ornamental signs."""
    text = DIACRITICS.sub('', text)
    text = text.replace(TATWEEL, '')
    # Strip zero-width joiners, soft hyphens, and other invisible chars
    text = text.replace('\u200D', '').replace('\u200C', '').replace('\u00AD', '')
    return text


def normalize_alef(text):
    """Normalize all alef variants to bare alef, and alef maksura to yaa."""
    text = ALEF_VARIANTS.sub('ا', text)
    # Normalize alef maksura → yaa (tanzil uses ى where standard has ي)
    text = text.replace(ALEF_MAKSURA, YAA)
    return text


def prepare_for_root(word, expand_shadda=False):
    """
    Full normalization pipeline for root extraction (Phase 1A).
    MUST run Tanzil normalization BEFORE diacritics strip because
    the diacritics regex catches hamza-above (U+0654), small waw/yaa
    (U+06E5/06E6), and superscript alef (U+0670).

    Order: Tanzil normalize → (optional shadda expand) → diacritics strip → alef normalize
    """
    text = word

    # Step 1: Tanzil-specific Unicode (on diacritics-bearing text)
    text = text.replace(TANZIL_WASLA, 'ا')        # ٱ → ا
    text = text.replace(TANZIL_SMALL_WAW, '')       # ۥ → strip
    text = text.replace(TANZIL_SMALL_YAA, '')       # ۦ → strip
    text = text.replace('\u0654', 'ء')              # hamza above (combining) → standalone ء
    text = HAMZA_CARRIERS.sub('ء', text)            # ؤ ئ → ء
    text = text.replace('\u0627\u0653', 'اء')         # decomposed alef-madda (ا + maddah) → alef + hamza
    text = text.replace('آ', 'اء')                  # precomposed alef-madda → alef + hamza

    # Step 2: Optionally expand shadda (double the previous consonant)
    # Used specifically for ال sun-letter deduplication
    if expand_shadda:
        expanded = []
        i = 0
        while i < len(text):
            if text[i] == '\u0651':  # shadda
                for j in range(len(expanded) - 1, -1, -1):
                    if not DIACRITICS.match(expanded[j]) and expanded[j] != TATWEEL:
                        expanded.insert(j + 1, expanded[j])
                        break
            else:
                expanded.append(text[i])
            i += 1
        text = ''.join(expanded)

    # Step 3: Strip remaining diacritics
    text = strip_diacritics(text)

    # Step 4: Normalize alef
    text = normalize_alef(text)

    return text


def strip_consonant_skeleton(text):
    """Strip medial long vowels (ا و ي) from text to get consonant skeleton."""
    if len(text) < 4:
        return text
    skeleton = []
    for i, ch in enumerate(text):
        if ch in ('ا', 'و', 'ي'):
            # Keep if first or last character (likely root letter)
            if i == 0 or i == len(text) - 1:
                skeleton.append(ch)
            # Strip medial long vowels (between consonants)
            elif ch == 'ا':
                continue  # medial alef is almost always a long vowel
            elif ch in ('و', 'ي') and i > 0 and i < len(text) - 1:
                prev = text[i-1] in ARABIC_CONSONANTS
                nxt = text[i+1] in ARABIC_CONSONANTS
                if prev and nxt:
                    continue  # between consonants = long vowel
                skeleton.append(ch)
            else:
                skeleton.append(ch)
        else:
            skeleton.append(ch)
    result = ''.join(skeleton)
    return result if len(result) >= 2 else text


def generate_root_candidates(word):
    """
    Generate candidate root forms from MOST CONSERVATIVE to MOST AGGRESSIVE.
    Each candidate will be tried against the dictionary — first match wins.
    This prevents over-stripping (e.g., stripping ف from فضل).
    """
    bare = prepare_for_root(word)
    bare_shad = prepare_for_root(word, expand_shadda=True)
    candidates = []
    seen = set()

    def add(c):
        if c and len(c) >= 2 and c not in seen:
            seen.add(c)
            candidates.append(c)

    # Level 0: Direct normalized forms (both with and without shadda expansion)
    add(bare)
    if bare_shad != bare:
        add(bare_shad)

    # Level 1: Strip definite article ال
    if bare_shad.startswith('ال') and len(bare_shad) > 3:
        after_al = bare_shad[2:]
        # Sun-letter deduplication (shadda was expanded → doubled first letter)
        if len(after_al) >= 2 and after_al[0] == after_al[1]:
            add(after_al[1:])  # deduplicated
        add(after_al)
    if bare.startswith('ال') and len(bare) > 3:
        add(bare[2:])

    # Level 2: Strip suffix patterns (on ALL current candidates)
    bases_for_suffix = list(candidates)  # copy current candidates
    for base in bases_for_suffix:
        # Pronoun suffixes
        for suf in PRONOUN_SUFFIXES:
            if base.endswith(suf) and len(base) > len(suf) + 1:
                add(base[:-len(suf)])
                break
        # Grammatical suffixes
        for suf in GRAM_SUFFIXES:
            if base.endswith(suf) and len(base) > len(suf) + 1:
                add(base[:-len(suf)])
                break
        # Taa marbuta
        if base.endswith('ة') and len(base) > 2:
            add(base[:-1])
        # Final alef (tanwin)
        if base.endswith('ا') and len(base) > 3:
            add(base[:-1])

    # Level 3: Strip conjunction prefix (و ف) — ONLY as prefix, tested against dict
    if len(bare) > 3 and bare[0] in ('و', 'ف'):
        rest = bare[1:]
        add(rest)
        # Conjunction + ال
        if rest.startswith('ال') and len(rest) > 3:
            after_al = rest[2:]
            add(after_al)
            # With shadda expansion for sun-letter
            rest_shad = bare_shad[1:] if len(bare_shad) > 3 and bare_shad[0] in ('و', 'ف') else rest
            if rest_shad.startswith('ال') and len(rest_shad) > 3:
                after_al_shad = rest_shad[2:]
                if len(after_al_shad) >= 2 and after_al_shad[0] == after_al_shad[1]:
                    add(after_al_shad[1:])
        # Conjunction + suffix stripping
        for suf in PRONOUN_SUFFIXES:
            if rest.endswith(suf) and len(rest) > len(suf) + 1:
                add(rest[:-len(suf)])
                break
        for suf in GRAM_SUFFIXES:
            if rest.endswith(suf) and len(rest) > len(suf) + 1:
                add(rest[:-len(suf)])
                break
        if rest.endswith('ة') and len(rest) > 2:
            add(rest[:-1])
        if rest.endswith('ا') and len(rest) > 3:
            add(rest[:-1])

    # Level 4: Strip preposition prefix (ب ك ل) — can stack with conjunction
    for prep_base in [bare, bare[1:] if len(bare) > 3 and bare[0] in ('و', 'ف') else None]:
        if prep_base and len(prep_base) > 3 and prep_base[0] in ('ب', 'ك', 'ل'):
            rest = prep_base[1:]
            add(rest)
            if rest.startswith('ال') and len(rest) > 3:
                add(rest[2:])
            # Prep + suffix
            for suf in PRONOUN_SUFFIXES:
                if rest.endswith(suf) and len(rest) > len(suf) + 1:
                    add(rest[:-len(suf)])
                    break
            if rest.endswith('ة') and len(rest) > 2:
                add(rest[:-1])
            if rest.endswith('ا') and len(rest) > 3:
                add(rest[:-1])
        # لل = لِ + ال
        if prep_base and prep_base.startswith('لل') and len(prep_base) > 3:
            add(prep_base[2:])

    # Level 5: Verbal/morphological prefix stripping
    for c in list(candidates):
        stems = []
        # Strip imperfect verb prefixes (يَفْعَل, تَفْعَل, نَفْعَل, أَفْعَل)
        if len(c) >= 4 and c[0] in ('ي', 'ت', 'ن', 'ا'):
            stems.append(c[1:])
            add(c[1:])
        # Strip م prefix (active/passive participle: مُفْعِل, مَفْعُول)
        if len(c) >= 4 and c[0] == 'م':
            stems.append(c[1:])
            add(c[1:])
        # Form VII/VIII/X prefix stripping: است, انف, افت
        if len(c) >= 6 and c[:3] == 'است':
            stems.append(c[3:])
            add(c[3:])  # Form X
        if len(c) >= 5 and c[:3] == 'افت':
            stems.append(c[3:])
            add(c[3:])  # Form VIII (افتعل)
            # Also try: remove ا and ت (keeping middle radical): افتعل → فعل
            if len(c) >= 5:
                stems.append(c[1] + c[3:])
                add(c[1] + c[3:])
        if len(c) >= 5 and c[:2] == 'ان':
            stems.append(c[2:])
            add(c[2:])  # Form VII

        # Level 5b: Strip suffixes from verbal stems (critical for conjugated verbs)
        for stem in stems:
            for suf in PRONOUN_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 1:
                    add(stem[:-len(suf)])
                    break
            for suf in GRAM_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 1:
                    add(stem[:-len(suf)])
                    break
            if stem.endswith('ة') and len(stem) > 2:
                add(stem[:-1])
            if stem.endswith('ا') and len(stem) > 3:
                add(stem[:-1])
            # Combined Form X + suffix: استفعلوا → فعل
            if len(stem) >= 5 and stem[:3] == 'ست':
                x_stem = stem[3:]
                add(x_stem)
                for suf in PRONOUN_SUFFIXES:
                    if x_stem.endswith(suf) and len(x_stem) > len(suf) + 1:
                        add(x_stem[:-len(suf)])
                        break
            # Combined Form VIII inside: stem = فتعل → try فعل
            if len(stem) >= 4 and stem[1] == 'ت':
                viii_stem = stem[0] + stem[2:]
                add(viii_stem)
                for suf in PRONOUN_SUFFIXES + GRAM_SUFFIXES:
                    if viii_stem.endswith(suf) and len(viii_stem) > len(suf) + 1:
                        add(viii_stem[:-len(suf)])
                        break

    # Level 5c: Double-hamza collapse (آ expansion artifact: ءء → ء)
    for c in list(candidates):
        if 'ءء' in c:
            collapsed = c.replace('ءء', 'ء')
            add(collapsed)
            # Also try with stripped medial ا after collapse
            if len(collapsed) >= 4:
                skel = strip_consonant_skeleton(collapsed)
                if skel != collapsed:
                    add(skel)

    # Level 6: Consonant skeleton on all candidates so far
    for c in list(candidates):
        skel = strip_consonant_skeleton(c)
        if skel != c:
            add(skel)

    # Level 7: 3-letter subsets (last resort)
    for c in list(candidates):
        if len(c) >= 4:
            add(c[:3])
            add(c[1:4])
        if len(c) >= 5:
            add(c[2:5])
            add(c[:2] + c[3])  # skip middle letter
            add(c[0] + c[2:4])  # skip 2nd letter

    return candidates


def extract_root_letters(word):
    """
    Extract potential root consonants from an Arabic word.
    Returns the FIRST candidate from generate_root_candidates().
    For actual root matching, find_root() tries ALL candidates against the dictionary.
    """
    candidates = generate_root_candidates(word)
    return candidates[0] if candidates else prepare_for_root(word)


def check_qv_applies(word, qv_ref, conn):
    """
    Check if a QV correction actually applies to this specific word form.
    Some roots have dual usage: ن-ص-ر means 'help' (root meaning) but
    النَّصَارَى is the mistranslated people-label form. The QV correction
    only applies to the people-label forms, not the root's general usage.

    Returns qv_ref if the correction applies, None if it doesn't.
    """
    if not qv_ref:
        return None

    row = conn.execute(
        "SELECT QV_FORMS FROM qv_translation_register WHERE QV_ID = ?",
        (qv_ref,)
    ).fetchone()

    if not row or not row[0]:
        return qv_ref  # no forms defined = always apply (safety default)

    qv_forms = row[0].strip()

    # '*' means all forms of this root trigger the correction
    if qv_forms == '*':
        return qv_ref

    # Check if this specific word form is in the trigger list
    bare = strip_diacritics(word)
    bare_norm = normalize_alef(bare)
    trigger_forms = [f.strip() for f in qv_forms.split(',')]

    for form in trigger_forms:
        form_bare = normalize_alef(strip_diacritics(form))
        if bare_norm == form_bare or word == form:
            return qv_ref

    # Word uses the same root but is NOT a trigger form — no QV correction
    return None


def find_root(word, conn):
    """
    Try to match an Arabic word to a root in the dictionary.
    Returns (root_hyphenated, root_meaning, qv_ref, word_type, verb_form) or (None, None, None, None, None).

    Phase 1B: Multi-candidate cascade — generates progressively more aggressive
    extraction variants and checks each against the dictionary. First match wins.
    This prevents over-stripping (e.g., stripping ف from فضل).
    """
    bare_norm = prepare_for_root(word)

    # Strategy 0 (FASTEST): Known forms lookup — pre-mapped Qur'anic word forms
    kf = conn.execute(
        "SELECT k.root_unhyphenated, k.word_type, k.verb_form, "
        "d.root_hyphenated, d.root_meaning, d.qv_ref "
        "FROM quran_known_forms k "
        "LEFT JOIN quran_root_dictionary d ON k.root_unhyphenated = d.root_unhyphenated "
        "WHERE k.bare_form = ?", (bare_norm,)
    ).fetchone()
    if kf:
        root_hyph = kf[3] if kf[3] else '-'.join(kf[0]) if kf[0] else None
        qv = check_qv_applies(word, kf[5], conn)
        return (root_hyph, kf[4], qv, kf[1], kf[2])

    # Also try with the diacritised form directly in known_forms
    kf2 = conn.execute(
        "SELECT k.root_unhyphenated, k.word_type, k.verb_form, "
        "d.root_hyphenated, d.root_meaning, d.qv_ref "
        "FROM quran_known_forms k "
        "LEFT JOIN quran_root_dictionary d ON k.root_unhyphenated = d.root_unhyphenated "
        "WHERE k.arabic_form = ?", (word,)
    ).fetchone()
    if kf2:
        root_hyph = kf2[3] if kf2[3] else '-'.join(kf2[0]) if kf2[0] else None
        qv = check_qv_applies(word, kf2[5], conn)
        return (root_hyph, kf2[4], qv, kf2[1], kf2[2])

    # Strategy 1: Try ALL root candidates against dictionary (most conservative first)
    # For each candidate, also try hamza variants (dictionary stores أ not ا or ء)
    candidates = generate_root_candidates(word)

    def try_lookup(candidate):
        """Try candidate and its hamza variants. Returns (root_hyph, meaning, qv) or None."""
        # Direct lookup
        row = conn.execute(
            "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
            "WHERE root_unhyphenated = ?", (candidate,)
        ).fetchone()
        if row and row[1]:  # prefer matches WITH meaning
            return row
        direct_hit = row  # save partial match

        # Try ا → أ at start (dictionary uses أ for hamza-initial roots)
        if candidate.startswith('ا'):
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                "WHERE root_unhyphenated = ?", ('أ' + candidate[1:],)
            ).fetchone()
            if row and row[1]:
                return row
            if not direct_hit:
                direct_hit = row

        # Try ء → أ anywhere (hamza carriers normalized to ء, dict uses أ)
        if 'ء' in candidate:
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                "WHERE root_unhyphenated = ?", (candidate.replace('ء', 'أ'),)
            ).fetchone()
            if row and row[1]:
                return row
            if not direct_hit:
                direct_hit = row

        # Try weak-letter root reconstruction for 2-letter candidates
        # Many roots are hollow (و/ي as middle radical) or assimilated (و as first radical)
        if len(candidate) == 2:
            for weak in ('و', 'ي'):
                # Insert weak letter as middle radical: فل → فول / فيل
                trial = candidate[0] + weak + candidate[1]
                row = conn.execute(
                    "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                    "WHERE root_unhyphenated = ?", (trial,)
                ).fetchone()
                if row and row[1]:
                    return row
                if not direct_hit and row:
                    direct_hit = row
                # Insert weak letter as first radical: فل → وفل / يفل
                trial2 = weak + candidate
                row = conn.execute(
                    "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                    "WHERE root_unhyphenated = ?", (trial2,)
                ).fetchone()
                if row and row[1]:
                    return row
                if not direct_hit and row:
                    direct_hit = row
            # Try أ as first radical: فل → أفل
            trial_hamza = 'أ' + candidate
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                "WHERE root_unhyphenated = ?", (trial_hamza,)
            ).fetchone()
            if row and row[1]:
                return row
            if not direct_hit and row:
                direct_hit = row

        # Try hollow verb reconstruction for 3-letter candidates with medial ا
        # جاء → جيأ (hollow verb: middle radical ي/و manifests as ا in past tense)
        if len(candidate) == 3 and candidate[1] == 'ا':
            for weak in ('و', 'ي'):
                trial = candidate[0] + weak + candidate[2]
                row = conn.execute(
                    "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                    "WHERE root_unhyphenated = ?", (trial,)
                ).fetchone()
                if row and row[1]:
                    return row
                if not direct_hit and row:
                    direct_hit = row
                # Also try with ء→أ on last letter
                if candidate[2] == 'ء':
                    trial2 = candidate[0] + weak + 'أ'
                    row = conn.execute(
                        "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                        "WHERE root_unhyphenated = ?", (trial2,)
                    ).fetchone()
                    if row and row[1]:
                        return row
                    if not direct_hit and row:
                        direct_hit = row

        # Try defective verb reconstruction: 3-letter with final ا/ء → try و/ي as last radical
        if len(candidate) == 3 and candidate[2] in ('ا', 'ء'):
            for weak in ('و', 'ي', 'ه'):
                trial = candidate[0] + candidate[1] + weak
                # Try direct and with ء→أ variant (covers ءلا→ألو for ءَالَآءِ)
                for t in set([trial, trial.replace('ء', 'أ')]):
                    row = conn.execute(
                        "SELECT root_hyphenated, root_meaning, qv_ref FROM quran_root_dictionary "
                        "WHERE root_unhyphenated = ?", (t,)
                    ).fetchone()
                    if row and row[1]:
                        return row
                    if not direct_hit and row:
                        direct_hit = row

        return direct_hit  # may be None

    # Try each candidate; prefer matches with meaning
    best_no_meaning = None
    for candidate in candidates:
        hit = try_lookup(candidate)
        if hit:
            if hit[1]:  # has meaning → use immediately
                qv = check_qv_applies(word, hit[2], conn)
                return (hit[0], hit[1], qv, None, None)
            elif not best_no_meaning:
                best_no_meaning = hit  # save first match without meaning

    # Fall back to match without meaning if nothing better found
    if best_no_meaning:
        qv = check_qv_applies(word, best_no_meaning[2], conn)
        return (best_no_meaning[0], best_no_meaning[1], qv, None, None)

    return (None, None, None, None, None)


def classify_word(word):
    """Classify word type based on Arabic morphological patterns."""
    bare_norm = prepare_for_root(word)

    # Build normalized particle set (cache on first call)
    if not hasattr(classify_word, '_particle_cache'):
        classify_word._particle_cache = set()
        for p in PARTICLES:
            p_stripped = prepare_for_root(p)
            classify_word._particle_cache.add(p_stripped)
        # Also add Tanzil variants (with wasla etc.)
        for p in PARTICLES:
            p_bare = normalize_alef(strip_diacritics(p))
            classify_word._particle_cache.add(p_bare)

    # Check if particle (after normalization to handle tanzil ى vs ي etc.)
    if bare_norm in classify_word._particle_cache:
        return 'PARTICLE'

    # Very rough heuristics for type classification
    if bare_norm.startswith('ال') or bare_norm.endswith('ة'):
        return 'NOUN'

    # Imperfect verb prefixes
    if len(bare_norm) >= 3 and bare_norm[0] in 'يتنا':
        return 'VERB'

    return 'NOUN'  # default


def detect_verb_form(word):
    """
    Detect Arabic verb form (I-X) from morphological pattern.
    Uses both diacritics (from original Tanzil text) and consonant patterns.
    Returns form number as string ('I'-'X') or None if not a detectable verb.
    """
    # Work with the original diacritised text for shadda/vowel detection
    original = word
    bare = prepare_for_root(word)

    # Strip conjunction prefixes (و ف) for detection
    if len(bare) > 3 and bare[0] in ('و', 'ف'):
        bare = bare[1:]

    # Strip imperfect prefix (ي ت ن أ) — these are conjugation markers, not form markers
    stem = bare
    has_imperfect_prefix = False
    if len(bare) >= 4 and bare[0] in ('ي', 'ت', 'ن', 'ا'):
        stem = bare[1:]
        has_imperfect_prefix = True

    # ── Form X: استفعل (stem starts with ست, or bare starts with است) ──
    if stem.startswith('ست') and len(stem) >= 5:
        return 'X'
    if bare.startswith('است') and len(bare) >= 6:
        return 'X'

    # ── Form VIII: افتعل — infixed ت after first radical ──
    # Imperfect: يفتعل → stem = فتعل → stem[1] == ت
    if len(stem) >= 4 and stem[1] == 'ت' and stem[0] not in ('س', 'ا', 'ت'):
        return 'VIII'
    # Perfect: افتعل, اكتسب, اشترى → bare[2] == ت
    if bare.startswith('ا') and len(bare) >= 5 and bare[2] == 'ت':
        return 'VIII'

    # ── Form VII: انفعل ──
    if bare.startswith('ان') and len(bare) >= 5:
        return 'VII'

    # ── Form V/VI: تفعّل / تفاعل ──
    # KEY: Form V/VI has ت as PART OF THE FORM, not as imperfect prefix.
    # So we look at the ORIGINAL bare form (before imperfect prefix stripping).
    # Perfect: تَفَعَّلَ / تَفَاعَلَ → bare starts with ت
    # Imperfect: يَتَفَعَّلُ → bare starts with يت, stem starts with ت
    is_form_v_vi = False
    if has_imperfect_prefix and stem.startswith('ت') and len(stem) >= 4:
        # Imperfect Form V/VI: يتفعّل / يتفاعل — stem after ي starts with ت
        is_form_v_vi = True
    elif bare.startswith('ت') and len(bare) >= 5 and not has_imperfect_prefix:
        # Perfect Form V/VI: تفعّل / تفاعل — bare starts with ت AND is 5+ letters
        is_form_v_vi = True

    if is_form_v_vi:
        # Distinguish V from VI: check if medial letter after ت is ا (Form VI: تفاعل)
        v_stem = stem[1:] if stem.startswith('ت') else bare[1:]
        if len(v_stem) >= 3 and v_stem[1] in ('ا', 'و'):
            return 'VI'
        return 'V'

    # ── Form IV: أفعل — causative ──
    # Perfect: أفعل → bare starts with ا, 4 letters total
    if not has_imperfect_prefix and bare.startswith('ا') and len(bare) == 4:
        return 'IV'
    # Imperfect Form IV: يُفْعِلُ — detected by damma (ُ) on the imperfect prefix
    # This distinguishes يُنزِلُ (Form IV) from يَفْعَلُ (Form I)
    # Also covers perfect passive أُنزِلَ and similar
    if has_imperfect_prefix:
        # Find the first consonant in original that matches (accounting for alef variants)
        target = bare[0]
        alef_set = set('اأإآٱ')
        for j, ch in enumerate(original):
            match = (ch == target) or (ch in alef_set and target in alef_set)
            if match:
                if j + 1 < len(original) and original[j + 1] == '\u064F':
                    return 'IV'
                break

    # ── Form II: فعّل — shadda on middle radical ──
    if '\u0651' in original:
        # Shadda present. Check it's NOT on the first letter (which would be sun-letter assimilation)
        # and NOT part of a geminate root. Best heuristic: if stem is 3+ letters and form not yet detected
        # Look for shadda specifically on the position corresponding to the 2nd radical
        return 'II'

    # ── Form III: فاعل — alef after first radical ──
    # Only detect if stem is 4+ letters and second letter is ا
    # Be careful: many words have ا as a long vowel, not Form III marker
    # Only apply to perfect tense (no imperfect prefix) where pattern is clear
    if not has_imperfect_prefix and len(bare) >= 4 and bare[1] == 'ا':
        return 'III'

    return None  # Form I or undetectable


# ── VERB FORM SEMANTIC MODIFIERS ──
# Maps verb form to semantic shift applied to the base root meaning
FORM_MODIFIERS = {
    'I': '',  # base form
    'II': 'intensify/cause',   # فَعَّلَ — intensive, causative, denominative
    'III': 'with/toward',      # فَاعَلَ — associative, attempt, directed action
    'IV': 'cause',             # أَفْعَلَ — causative, factitive
    'V': 'self-intensify',     # تَفَعَّلَ — reflexive of II, gradual
    'VI': 'mutual',            # تَفَاعَلَ — reciprocal, pretend
    'VII': 'passive',          # اِنْفَعَلَ — medio-passive, submission
    'VIII': 'self/reflexive',  # اِفْتَعَلَ — reflexive, middle voice
    'IX': 'become-colored',    # اِفْعَلَّ — colors, defects (rare)
    'X': 'seek/consider',      # اِسْتَفْعَلَ — estimative, requestive
}


def apply_form_modifier(root_meaning, verb_form):
    """Apply verb form semantic modifier to root meaning for Layer 2 translation."""
    if not verb_form or verb_form == 'I' or not root_meaning:
        return root_meaning

    # Extract base verb — take first meaning, strip "to " prefix
    base = root_meaning.split(',')[0].split('/')[0].strip()
    if base.startswith('to '):
        base = base[3:]

    modifiers = {
        'II': f'{base}-intensely',
        'III': f'{base}-together',
        'IV': f'make-{base}',
        'V': f'{base}-oneself',
        'VI': f'{base}-each-other',
        'VII': f'be-{base}d',
        'VIII': f'{base}-oneself',
        'IX': f'become-{base}',
        'X': f'seek-{base}',
    }

    return modifiers.get(verb_form, base)


def seed_ayah(conn, surah, ayah, arabic_text, force=False):
    """
    Auto-seed a single āyah with root mappings.
    Returns (total_words, mapped_words, qv_corrections).
    """
    # Check if already seeded
    existing = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE surah=? AND ayah=?",
        (surah, ayah)
    ).fetchone()[0]

    if existing > 0 and not force:
        return (0, 0, 0)  # skip already-seeded

    # Delete existing words if force re-seeding
    if force:
        conn.execute(
            "DELETE FROM quran_word_roots WHERE surah=? AND ayah=?",
            (surah, ayah)
        )

    # Insert/update the āyah record
    conn.execute(
        "INSERT OR REPLACE INTO quran_ayat (surah, ayah, arabic_text, status) VALUES (?, ?, ?, 'AUTO_MAPPED')",
        (surah, ayah, arabic_text)
    )

    # Tokenize
    words = arabic_text.split()
    total = len(words)
    mapped = 0
    qv_count = 0

    for pos, word in enumerate(words, 1):
        word_type = classify_word(word)
        verb_form = None
        root_hyph = None
        root_meaning = None
        qv_ref = None

        if word_type == 'PARTICLE':
            # Particles have no root
            conn.execute(
                "INSERT INTO quran_word_roots (surah, ayah, word_position, arabic_word, word_type, correct_translation, common_translation) "
                "VALUES (?, ?, ?, ?, 'PARTICLE', ?, ?)",
                (surah, ayah, pos, word, word, word)
            )
            mapped += 1
            continue

        # Try to find root (returns 5-tuple now)
        result = find_root(word, conn)
        root_hyph, root_meaning, qv_ref, kf_type, kf_form = result

        if root_hyph:
            mapped += 1
            if qv_ref:
                qv_count += 1
            # Use known-form type/form if available, else detect
            if kf_type:
                word_type = kf_type
            if kf_form:
                verb_form = kf_form
            elif word_type == 'VERB':
                verb_form = detect_verb_form(word)

        conn.execute(
            "INSERT INTO quran_word_roots (surah, ayah, word_position, arabic_word, root, root_meaning, "
            "verb_form, word_type, qv_ref) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (surah, ayah, pos, word, root_hyph, root_meaning, verb_form, word_type, qv_ref)
        )

    return (total, mapped, qv_count)


def seed_surah_text(conn, surah_data):
    """
    Seed multiple āyāt from a list of (surah, ayah, text) tuples.
    Returns summary stats.
    """
    total_words = 0
    total_mapped = 0
    total_qv = 0
    ayat_count = 0

    for surah, ayah, text in surah_data:
        t, m, q = seed_ayah(conn, surah, ayah, text)
        total_words += t
        total_mapped += m
        total_qv += q
        if t > 0:
            ayat_count += 1

    conn.commit()
    return ayat_count, total_words, total_mapped, total_qv


def load_text_file(conn, filepath):
    """Load Qur'an text from tanzil-format file (surah|ayah|text)."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|', 2)
            if len(parts) == 3:
                surah, ayah, text = int(parts[0]), int(parts[1]), parts[2].strip()
                data.append((surah, ayah, text))

    if not data:
        print("  No valid lines found in file.")
        return

    ayat, words, mapped, qv = seed_surah_text(conn, data)
    pct = mapped / words * 100 if words > 0 else 0
    print(f"\n  Loaded from: {filepath}")
    print(f"  Āyāt seeded: {ayat}")
    print(f"  Words: {words} total, {mapped} mapped ({pct:.1f}%), {words - mapped} unmapped")
    print(f"  QV corrections: {qv}")


# ── Built-in short sūrahs for testing without external file ──
BUILTIN_SURAHS = {
    112: [
        (112, 1, "قُلْ هُوَ اللَّهُ أَحَدٌ"),
        (112, 2, "اللَّهُ الصَّمَدُ"),
        (112, 3, "لَمْ يَلِدْ وَلَمْ يُولَدْ"),
        (112, 4, "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ"),
    ],
    113: [
        (113, 1, "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ"),
        (113, 2, "مِن شَرِّ مَا خَلَقَ"),
        (113, 3, "وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ"),
        (113, 4, "وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ"),
        (113, 5, "وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ"),
    ],
    114: [
        (114, 1, "قُلْ أَعُوذُ بِرَبِّ النَّاسِ"),
        (114, 2, "مَلِكِ النَّاسِ"),
        (114, 3, "إِلَٰهِ النَّاسِ"),
        (114, 4, "مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ"),
        (114, 5, "الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ"),
        (114, 6, "مِنَ الْجِنَّةِ وَالنَّاسِ"),
    ],
    105: [
        (105, 1, "أَلَمْ تَرَ كَيْفَ فَعَلَ رَبُّكَ بِأَصْحَابِ الْفِيلِ"),
        (105, 2, "أَلَمْ يَجْعَلْ كَيْدَهُمْ فِي تَضْلِيلٍ"),
        (105, 3, "وَأَرْسَلَ عَلَيْهِمْ طَيْرًا أَبَابِيلَ"),
        (105, 4, "تَرْمِيهِم بِحِجَارَةٍ مِّن سِجِّيلٍ"),
        (105, 5, "فَجَعَلَهُمْ كَعَصْفٍ مَّأْكُولٍ"),
    ],
    108: [
        (108, 1, "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ"),
        (108, 2, "فَصَلِّ لِرَبِّكَ وَانْحَرْ"),
        (108, 3, "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ"),
    ],
    110: [
        (110, 1, "إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ"),
        (110, 2, "وَرَأَيْتَ النَّاسَ يَدْخُلُونَ فِي دِينِ اللَّهِ أَفْوَاجًا"),
        (110, 3, "فَسَبِّحْ بِحَمْدِ رَبِّكَ وَاسْتَغْفِرْهُ إِنَّهُ كَانَ تَوَّابًا"),
    ],
}


def seed_builtin(conn, surah_num, force=False):
    """Seed from built-in sūrah data."""
    if surah_num not in BUILTIN_SURAHS:
        print(f"  Sūrah {surah_num} not in built-in library.")
        print(f"  Available: {sorted(BUILTIN_SURAHS.keys())}")
        print(f"  Use 'load' command with a text file for other sūrahs.")
        return

    data = BUILTIN_SURAHS[surah_num]

    # If force, delete existing
    if force:
        for s, a, t in data:
            conn.execute("DELETE FROM quran_word_roots WHERE surah=? AND ayah=?", (s, a))
            conn.execute("DELETE FROM quran_ayat WHERE surah=? AND ayah=?", (s, a))
        conn.commit()

    ayat, words, mapped, qv = seed_surah_text(conn, data)
    pct = mapped / words * 100 if words > 0 else 0

    print(f"\n  COMPILER — Sūrah {surah_num}")
    print(f"  {'─' * 50}")
    print(f"  Āyāt compiled: {ayat}")
    print(f"  Words: {words} total")
    print(f"  Mapped to roots: {mapped} ({pct:.1f}%)")
    print(f"  Unmapped: {words - mapped}")
    print(f"  QV corrections applied: {qv}")
    print(f"  {'─' * 50}")

    # Show unmapped words
    unmapped = conn.execute(
        "SELECT DISTINCT arabic_word FROM quran_word_roots "
        "WHERE surah=? AND root IS NULL AND word_type != 'PARTICLE'",
        (surah_num,)
    ).fetchall()
    if unmapped:
        print(f"\n  Unmapped words (need manual root assignment):")
        for u in unmapped:
            print(f"    {u[0]}")


def show_status(conn):
    """Show overall compilation status."""
    # Total āyāt
    total_ayat = conn.execute("SELECT COUNT(*) FROM quran_ayat").fetchone()[0]
    auto_mapped = conn.execute(
        "SELECT COUNT(*) FROM quran_ayat WHERE status='AUTO_MAPPED'"
    ).fetchone()[0]
    manual = conn.execute(
        "SELECT COUNT(*) FROM quran_ayat WHERE status='MAPPED'"
    ).fetchone()[0]

    # Words
    total_words = conn.execute("SELECT COUNT(*) FROM quran_word_roots").fetchone()[0]
    with_root = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE root IS NOT NULL"
    ).fetchone()[0]
    with_qv = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE qv_ref IS NOT NULL"
    ).fetchone()[0]
    particles = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE word_type='PARTICLE'"
    ).fetchone()[0]

    # Dictionary
    dict_size = conn.execute("SELECT COUNT(*) FROM quran_root_dictionary").fetchone()[0]
    dict_qv = conn.execute(
        "SELECT COUNT(*) FROM quran_root_dictionary WHERE qv_ref IS NOT NULL"
    ).fetchone()[0]

    # QV register
    qv_size = conn.execute("SELECT COUNT(*) FROM qv_translation_register").fetchone()[0]

    # By sūrah
    surahs = conn.execute(
        "SELECT surah, COUNT(DISTINCT ayah) as ayat, COUNT(*) as words, "
        "SUM(CASE WHEN root IS NOT NULL THEN 1 ELSE 0 END) as rooted, "
        "SUM(CASE WHEN qv_ref IS NOT NULL THEN 1 ELSE 0 END) as qv, "
        "status "
        "FROM quran_word_roots w JOIN quran_ayat a USING (surah, ayah) "
        "GROUP BY surah ORDER BY surah"
    ).fetchall()

    mapped_pct = (with_root + particles) / total_words * 100 if total_words > 0 else 0

    print(f"\n  USLaP COMPILER STATUS")
    print(f"  {'═' * 55}")
    print(f"  Āyāt compiled:    {total_ayat} / 6,236 ({total_ayat/6236*100:.1f}%)")
    print(f"    Manual (MAPPED):   {manual}")
    print(f"    Auto (AUTO_MAPPED): {auto_mapped}")
    print(f"  Words compiled:    {total_words}")
    print(f"    With root:         {with_root} ({with_root/total_words*100:.1f}%)" if total_words else "")
    print(f"    Particles:         {particles}")
    print(f"    Unmapped:          {total_words - with_root - particles}")
    print(f"    QV corrections:    {with_qv}")
    print(f"  Effective coverage: {mapped_pct:.1f}%")
    print(f"  {'─' * 55}")
    print(f"  Root dictionary:   {dict_size} roots ({dict_qv} with QV meanings)")
    print(f"  QV Register:       {qv_size} mistranslated terms")
    print(f"  {'═' * 55}")

    if surahs:
        print(f"\n  Per-sūrah breakdown:")
        print(f"  {'Sūrah':<8} {'Āyāt':<7} {'Words':<8} {'Rooted':<8} {'QV':<5} {'Status'}")
        print(f"  {'─' * 50}")
        for s in surahs:
            pct = s[3] / s[2] * 100 if s[2] > 0 else 0
            print(f"  {s[0]:<8} {s[1]:<7} {s[2]:<8} {s[3]:<8} {s[4]:<5} {s[5]}")


def show_unmapped(conn, surah):
    """Show unmapped words in a sūrah."""
    rows = conn.execute(
        "SELECT ayah, word_position, arabic_word FROM quran_word_roots "
        "WHERE surah=? AND root IS NULL AND word_type != 'PARTICLE' "
        "ORDER BY ayah, word_position",
        (surah,)
    ).fetchall()

    if not rows:
        print(f"  All words in sūrah {surah} are mapped or classified as particles.")
        return

    print(f"\n  UNMAPPED WORDS — Sūrah {surah}")
    print(f"  {'─' * 40}")
    print(f"  {'Āyah':<7} {'Pos':<5} {'Arabic'}")
    print(f"  {'─' * 40}")
    for r in rows:
        print(f"  {r[0]:<7} {r[1]:<5} {r[2]}")
    print(f"\n  Total: {len(rows)} words need manual root assignment.")


# ── Layer 2: Auto-translate from root data ──

# Particle translation map — functional English for Qur'anic particles
PARTICLE_TRANSLATIONS = {
    # Prepositions
    'في': 'in', 'من': 'from', 'على': 'upon', 'الى': 'toward', 'عن': 'from/about',
    'بين': 'between', 'عند': 'at/with', 'لدى': 'at/with', 'لدن': 'from-the-presence-of',
    'حتى': 'until', 'منذ': 'since', 'مع': 'with',
    # Conjunctions
    'و': 'and', 'ف': 'then', 'ثم': 'then', 'او': 'or', 'ام': 'or',
    'بل': 'rather', 'لكن': 'but', 'لاكن': 'but',
    # Negation/condition
    'لا': 'not', 'لم': 'not', 'لن': 'not/never', 'ما': 'not/what', 'ان': 'that/if',
    'لو': 'if', 'اذا': 'when', 'اذ': 'when', 'كيف': 'how',
    'هل': 'is/does?', 'اين': 'where', 'متى': 'when',
    # Emphasis
    'ان': 'indeed', 'قد': 'already/certainly', 'لقد': 'certainly',
    'انما': 'only/indeed', 'كلا': 'no indeed',
    # Pronouns
    'هو': 'He', 'هي': 'she/it', 'هم': 'they', 'انا': 'I', 'نحن': 'We',
    'انت': 'you', 'انتم': 'you(pl)', 'هما': 'they-two', 'هن': 'they(f)',
    # Demonstratives
    'هذا': 'this', 'هذه': 'this(f)', 'ذلك': 'that', 'تلك': 'that(f)',
    'اولائك': 'those', 'هاولاء': 'these',
    # Relative
    'الذي': 'the-one-who', 'التي': 'the-one-who(f)', 'الذين': 'those-who',
    'من': 'whoever', 'ماذا': 'what',
    # Quantifiers
    'كل': 'every/all', 'بعض': 'some',
    # Others
    'غير': 'other-than', 'مثل': 'like',
    'ليس': 'is-not', 'كان': 'was',
    'كما': 'as/like', 'سوف': 'will',
    'بلى': 'yes-indeed', 'نعم': 'yes',
    'يا': 'O', 'ايها': 'O(you)',
    'حيث': 'where', 'انى': 'wherever',
    'لعل': 'perhaps',
    'كان': 'was/be', 'لما': 'when',
    'اما': 'as-for', 'كذلك': 'likewise',
    'لولا': 'if-not-for',
    # Phase 1D additions
    'ذو': 'possessor-of', 'ذي': 'possessor-of', 'ذا': 'this/possessor-of',
    'ويل': 'woe', 'ذات': 'possessor-of(f)',
    'اءذا': 'then-when?', 'ايايا': 'me-alone',
}

# Preposition+pronoun translations
PREP_PRONOUN_TRANS = {
    # به، بها، بهم...
    'به': 'by-him/it', 'بها': 'by-her/it', 'بهم': 'by-them',
    'بنا': 'by-us', 'بكم': 'by-you(pl)', 'بك': 'by-you', 'بي': 'by-me',
    # له، لها...
    'له': 'for-him', 'لها': 'for-her', 'لهم': 'for-them',
    'لنا': 'for-us', 'لكم': 'for-you(pl)', 'لك': 'for-you', 'لي': 'for-me',
    # فيه، فيها...
    'فيه': 'in-it', 'فيها': 'in-it(f)', 'فيهم': 'in-them',
    'فينا': 'in-us', 'فيكم': 'in-you(pl)', 'فيك': 'in-you',
    # عليه...
    'عليه': 'upon-him', 'عليها': 'upon-her', 'عليهم': 'upon-them',
    'علينا': 'upon-us', 'عليكم': 'upon-you(pl)', 'عليك': 'upon-you',
    # إليه...
    'اليه': 'toward-him', 'اليها': 'toward-her', 'اليهم': 'toward-them',
    'الينا': 'toward-us', 'اليكم': 'toward-you(pl)', 'اليك': 'toward-you',
    # منه...
    'منه': 'from-him', 'منها': 'from-her/it', 'منهم': 'from-them',
    'منكم': 'from-you(pl)', 'منك': 'from-you',
    # عنه...
    'عنه': 'from-him', 'عنها': 'from-her', 'عنهم': 'from-them',
    # إنه...
    'انه': 'indeed-he', 'انها': 'indeed-she', 'انهم': 'indeed-they',
    'اني': 'indeed-I', 'انك': 'indeed-you', 'انكم': 'indeed-you(pl)',
    'اننا': 'indeed-we', 'انا': 'indeed-we',
    # Compounds
    'وما': 'and-not/and-what', 'فما': 'then-what', 'بما': 'with-what',
    'ومن': 'and-whoever', 'وان': 'and-if', 'فان': 'then-if',
    'واذا': 'and-when', 'فاذا': 'then-when',
    'ولقد': 'and-certainly', 'الم': 'have-not?',
    'افلا': 'then-will-not?', 'اولم': 'have-not?',
    'ولا': 'and-not', 'فلا': 'then-not',
    'وهو': 'and-He', 'وهم': 'and-they', 'وهي': 'and-she',
    'ولكن': 'but',
    'فهو': 'then-He', 'ذلكم': 'that(emph)',
    'لله': 'for-Allah', 'ولله': 'and-for-Allah',
    'بالله': 'by-Allah', 'والله': 'and-Allah',
    'وفي': 'and-in', 'وفيها': 'and-in-it',
    'فلما': 'then-when', 'ولما': 'and-when',
    'بانهم': 'because-they', 'بان': 'because/that',
    'باذن': 'by-permission-of', 'باذنه': 'by-His-permission',
    'ولاين': 'and-if', 'لاين': 'if',
    'بايا': 'by-which', 'فبايا': 'then-by-which',
    'عما': 'about-what', 'فيما': 'in-what',
    'بكل': 'with-every', 'وكل': 'and-every',
    'بينهم': 'between-them', 'بينكم': 'between-you',
    'بيننا': 'between-us', 'بينهما': 'between-them-two',
    'معه': 'with-him', 'معهم': 'with-them', 'معكم': 'with-you',
    'معنا': 'with-us',
    'ولهم': 'and-for-them', 'وله': 'and-for-him', 'ولها': 'and-for-her',
    'وعلى': 'and-upon', 'وعليهم': 'and-upon-them', 'وعليكم': 'and-upon-you',
    'واليه': 'and-toward-him', 'والينا': 'and-toward-us',
    'واليكم': 'and-toward-you',
    'وبين': 'and-between', 'وبينهم': 'and-between-them',
    'ومنهم': 'and-from-them', 'ومنها': 'and-from-her',
    'ومنه': 'and-from-him',
    'عليهن': 'upon-them(f)', 'لهن': 'for-them(f)', 'منهن': 'from-them(f)',
    'بهن': 'by-them(f)', 'فيهن': 'in-them(f)',
    'لديه': 'with-him', 'لدينا': 'with-us', 'لديهم': 'with-them',
    'ولدينا': 'and-with-us', 'ولديهم': 'and-with-them',
    'كانهم': 'as-if-they', 'كانه': 'as-if-he',
    'لعلهم': 'perhaps-they', 'لعلكم': 'perhaps-you',
    'لعلك': 'perhaps-you', 'لعله': 'perhaps-he',
    'وذلك': 'and-that', 'فذلك': 'then-that',
    'فاولايك': 'then-those', 'واولايك': 'and-those',
    'وكذلك': 'and-likewise', 'فكذلك': 'then-likewise',
    'والذين': 'and-those-who', 'للذين': 'for-those-who',
    'للناس': 'for-the-people',
    'وانتم': 'and-you(pl)',
    'وانا': 'and-indeed-we', 'وانه': 'and-indeed-he',
    'فسوف': 'then-will', 'ولو': 'and-if', 'ولن': 'and-never',
    'ولم': 'and-not', 'فلم': 'then-not',
    'اياك': 'You-alone',
}


def translate_particle(word):
    """Get English translation for a particle word."""
    bare = normalize_alef(strip_diacritics(word))
    # Try direct match
    if bare in PARTICLE_TRANSLATIONS:
        return PARTICLE_TRANSLATIONS[bare]
    if bare in PREP_PRONOUN_TRANS:
        return PREP_PRONOUN_TRANS[bare]
    # Try stripping leading waw/fa
    if bare.startswith('و') and bare[1:] in PARTICLE_TRANSLATIONS:
        return 'and-' + PARTICLE_TRANSLATIONS[bare[1:]]
    if bare.startswith('ف') and bare[1:] in PARTICLE_TRANSLATIONS:
        return 'then-' + PARTICLE_TRANSLATIONS[bare[1:]]
    return '...'


def get_word_gloss(arabic, root, meaning, wtype, qv_ref, verb_form, conn):
    """Get the English gloss for a single word, applying QV corrections and form modifiers."""
    if wtype == 'PARTICLE':
        return translate_particle(arabic)

    if wtype == 'NAME':
        bare = normalize_alef(strip_diacritics(arabic))
        if bare in ('الله', 'لله', 'بالله', 'والله', 'فالله', 'تالله'):
            return 'Allah'
        if qv_ref:
            qv_row = conn.execute(
                "SELECT CORRECT_TRANSLATION FROM qv_translation_register WHERE QV_ID=?",
                (qv_ref,)).fetchone()
            if qv_row:
                return qv_row[0].split('/')[0].strip()
        if meaning:
            return meaning.split('/')[0].strip()
        return arabic

    # QV correction takes priority
    if qv_ref:
        qv_row = conn.execute(
            "SELECT CORRECT_TRANSLATION FROM qv_translation_register WHERE QV_ID=?",
            (qv_ref,)).fetchone()
        if qv_row:
            return qv_row[0].split('/')[0].strip()

    if meaning:
        base = meaning.split(',')[0].split('/')[0].strip()
        # Apply verb form modifier
        if wtype == 'VERB' and verb_form and verb_form not in ('I', None, ''):
            base = apply_form_modifier(meaning, verb_form)
        return base

    if root:
        return f'[{root}]'
    return '___'


def detect_definite(arabic):
    """Check if word has definite article ال."""
    bare = prepare_for_root(arabic)
    return bare.startswith('ال')


def detect_prefix_particle(arabic):
    """Detect conjunction/preposition prefix on a content word. Returns (prefix_gloss, has_prefix)."""
    bare = prepare_for_root(arabic)
    if len(bare) > 3:
        if bare[0] == 'و':
            rest = bare[1:]
            if rest.startswith('ال') or len(rest) > 2:
                return ('and', True)
        if bare[0] == 'ف':
            rest = bare[1:]
            if rest.startswith('ال') or len(rest) > 2:
                return ('then', True)
        if bare.startswith('بال') or (bare[0] == 'ب' and len(bare) > 3):
            return ('with/in', True)
        if bare.startswith('كال') or (bare[0] == 'ك' and len(bare) > 3):
            return ('like', True)
        if bare.startswith('لل') or (bare[0] == 'ل' and len(bare) > 3):
            return ('for/to', True)
    return (None, False)


def detect_pronoun_suffix(arabic):
    """Detect possessive/object pronoun suffix. Returns pronoun gloss or None."""
    bare = prepare_for_root(arabic)
    # Check longest suffixes first
    suffixes = [
        ('كم', 'your(pl)'), ('هم', 'their'), ('هن', 'their(f)'),
        ('نا', 'our'), ('ها', 'her/its'), ('ه', 'his/its'),
        ('ك', 'your'), ('ي', 'my'),
    ]
    for suf, gloss in suffixes:
        if bare.endswith(suf) and len(bare) > len(suf) + 2:
            return gloss
    return None


def translate_ayah(conn, surah, ayah):
    """
    Generate Layer 2 root-translation for a single āyah.

    Phase 3: Grammar-aware assembly engine.
    Pass 1: Get word glosses
    Pass 2: Detect grammatical patterns (iḍāfah, prep phrases, etc.)
    Pass 3: Assemble English with pattern templates
    """
    words = conn.execute(
        "SELECT arabic_word, root, root_meaning, word_type, qv_ref, verb_form "
        "FROM quran_word_roots WHERE surah=? AND ayah=? ORDER BY word_position",
        (surah, ayah)
    ).fetchall()

    if not words:
        return None

    # ── Pass 1: Get base glosses for each word ──
    glosses = []
    for w in words:
        arabic, root, meaning, wtype, qv_ref, vform = w
        gloss = get_word_gloss(arabic, root, meaning, wtype, qv_ref, vform, conn)
        is_def = detect_definite(arabic) if wtype not in ('PARTICLE',) else False
        pron_suf = detect_pronoun_suffix(arabic) if wtype not in ('PARTICLE', 'NAME') else None
        prefix_gloss, has_prefix = detect_prefix_particle(arabic) if wtype not in ('PARTICLE',) else (None, False)

        glosses.append({
            'arabic': arabic,
            'gloss': gloss,
            'type': wtype,
            'root': root,
            'verb_form': vform,
            'definite': is_def,
            'pronoun': pron_suf,
            'prefix': prefix_gloss,
            'has_prefix': has_prefix,
        })

    # ── Pass 2: Pattern detection and assembly ──
    parts = []
    i = 0
    while i < len(glosses):
        g = glosses[i]

        # Particles pass through directly
        if g['type'] == 'PARTICLE':
            parts.append(g['gloss'])
            i += 1
            continue

        # Build the word translation
        word_parts = []

        # Add prefix particle if detected
        if g['has_prefix'] and g['prefix']:
            word_parts.append(g['prefix'])

        # Add "the" for definite nouns
        if g['definite'] and g['type'] in ('NOUN', 'NAME'):
            word_parts.append('the')

        # Main gloss
        word_parts.append(g['gloss'])

        # Iḍāfah detection: NOUN + NOUN (without particle between)
        # "X Y" → "X of Y" (construct chain)
        if (g['type'] == 'NOUN' and i + 1 < len(glosses)
                and glosses[i+1]['type'] == 'NOUN'
                and not glosses[i+1]['has_prefix']
                and not g['definite']  # first noun in iḍāfah is typically indefinite form
                ):
            # Check if next word is definite (strong iḍāfah signal)
            if glosses[i+1]['definite']:
                word_parts.append('of')

        # Add pronoun suffix
        if g['pronoun'] and g['type'] in ('NOUN', 'VERB'):
            word_parts.append(g['pronoun'])

        parts.append(' '.join(word_parts))
        i += 1

    return ' '.join(parts)


def translate_surah(conn, surah):
    """Generate Layer 2 translations for all āyāt in a sūrah."""
    rows = conn.execute(
        "SELECT ayah FROM quran_ayat WHERE surah=? ORDER BY ayah", (surah,)
    ).fetchall()

    if not rows:
        print(f"  No āyāt found for sūrah {surah}.")
        return

    translated = 0
    for r in rows:
        ayah = r[0]
        translation = translate_ayah(conn, surah, ayah)
        if translation:
            conn.execute(
                "UPDATE quran_ayat SET root_translation=? WHERE surah=? AND ayah=?",
                (translation, surah, ayah)
            )
            translated += 1

    conn.commit()
    print(f"  Translated sūrah {surah}: {translated}/{len(rows)} āyāt")
    return translated


def translate_all(conn):
    """Generate Layer 2 translations for ALL āyāt."""
    surahs = conn.execute(
        "SELECT DISTINCT surah FROM quran_ayat ORDER BY surah"
    ).fetchall()

    total = 0
    for s in surahs:
        rows = conn.execute(
            "SELECT ayah FROM quran_ayat WHERE surah=? ORDER BY ayah", (s[0],)
        ).fetchall()
        for r in rows:
            translation = translate_ayah(conn, s[0], r[0])
            if translation:
                conn.execute(
                    "UPDATE quran_ayat SET root_translation=? WHERE surah=? AND ayah=?",
                    (translation, s[0], r[0])
                )
                total += 1

    conn.commit()
    return total


def parse_ref(ref_str):
    """Parse reference like '112', '112:1'."""
    if ':' in ref_str:
        s, a = ref_str.split(':', 1)
        return int(s), int(a)
    return int(ref_str), None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if cmd == "seed":
        if len(sys.argv) < 3:
            print("  Usage: uslap_compiler.py seed <surah>[:<ayah>]")
            print(f"  Built-in sūrahs: {sorted(BUILTIN_SURAHS.keys())}")
            return
        surah, ayah = parse_ref(sys.argv[2])
        force = '--force' in sys.argv
        if ayah:
            # Single āyah from built-in
            if surah in BUILTIN_SURAHS:
                data = [(s, a, t) for s, a, t in BUILTIN_SURAHS[surah] if a == ayah]
                if data:
                    if force:
                        conn.execute("DELETE FROM quran_word_roots WHERE surah=? AND ayah=?", (surah, ayah))
                        conn.commit()
                    ayat, words, mapped, qv = seed_surah_text(conn, data)
                    print(f"  Āyah {surah}:{ayah} — {words} words, {mapped} mapped, {qv} QV")
                else:
                    print(f"  Āyah {surah}:{ayah} not in built-in data.")
            else:
                print(f"  Sūrah {surah} not in built-in library.")
        else:
            seed_builtin(conn, surah, force=force)

    elif cmd == "load":
        if len(sys.argv) < 3:
            print("  Usage: uslap_compiler.py load <path-to-quran-text>")
            return
        load_text_file(conn, sys.argv[2])

    elif cmd == "status":
        show_status(conn)

    elif cmd == "unmapped":
        if len(sys.argv) < 3:
            print("  Usage: uslap_compiler.py unmapped <surah>")
            return
        show_unmapped(conn, int(sys.argv[2]))

    elif cmd == "translate":
        if len(sys.argv) < 3:
            print("  Usage: uslap_compiler.py translate <surah|all>")
            print("  Generates Layer 2 root-translations from word-level data.")
            return
        target = sys.argv[2]
        if target == "all":
            total = translate_all(conn)
            print(f"\n  LAYER 2 TRANSLATION — ALL SŪRAHS")
            print(f"  {'─' * 40}")
            print(f"  Āyāt translated: {total}")
        else:
            surah = int(target)
            translate_surah(conn, surah)

    else:
        print(f"  Unknown command: {cmd}")
        print(__doc__)

    conn.close()


if __name__ == "__main__":
    main()
