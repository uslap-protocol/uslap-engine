#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر أُزْبَكِي — Uzbek Multi-Script Transliteration Engine

The ASB people have had FOUR script changes in 100 years:
  1. Bitig/Orkhon (original ORIG2) — cut off ~1000 years ago
  2. Arabic script (post-Islam, Navoi wrote in this) — cut off 1928
  3. Latin (Soviet first switch, 1928-1940) — cut off 1940
  4. Cyrillic (Soviet second switch, 1940-1991) — current older generation
  5. Latin again (post-independence, 1993-present) — current younger generation

Plus "Persian" pronunciation/spelling infestation from Timurid court culture.

This module transliterates between ALL scripts and strips to root consonants.

Sources: Kashgari (1072), Navoi (1499), Suleymanov, Shipova
"""

import os
import re
import unicodedata


# ═══════════════════════════════════════════════════════════════════════
# SCRIPT DETECTION
# ═══════════════════════════════════════════════════════════════════════

def detect_script(text):
    """
    Detect which script the input uses.
    Returns: "latin", "cyrillic", "arabic", "mixed", or "unknown"
    """
    latin = 0
    cyrillic = 0
    arabic = 0

    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x007A:  # Basic Latin A-z
            latin += 1
        elif ch in "oʻgʻOʻGʻ":  # Uzbek Latin special
            latin += 1
        elif 0x0400 <= cp <= 0x04FF:  # Cyrillic block
            cyrillic += 1
        elif 0x0621 <= cp <= 0x064A:  # AA letters
            arabic += 1
        elif 0x064B <= cp <= 0x0655:  # Arabic diacritics
            arabic += 1

    total = latin + cyrillic + arabic
    if total == 0:
        return "unknown"

    if arabic > 0 and arabic >= total * 0.5:
        return "arabic"
    if cyrillic > 0 and cyrillic >= total * 0.5:
        return "cyrillic"
    if latin > 0 and latin >= total * 0.5:
        return "latin"
    return "mixed"


# ═══════════════════════════════════════════════════════════════════════
# UZBEK LATIN ↔ CYRILLIC TABLES
# ═══════════════════════════════════════════════════════════════════════

# Modern Uzbek Latin → Cyrillic (official 1995 alphabet)
# Multi-char mappings MUST come first in processing order
LATIN_TO_CYRILLIC_MULTI = {
    "sh": "ш", "Sh": "Ш", "SH": "Ш",
    "ch": "ч", "Ch": "Ч", "CH": "Ч",
    "ng": "нг", "Ng": "Нг", "NG": "НГ",
    "oʻ": "ў", "Oʻ": "Ў", "o'": "ў", "O'": "Ў",
    "gʻ": "ғ", "Gʻ": "Ғ", "g'": "ғ", "G'": "Ғ",
}

LATIN_TO_CYRILLIC_SINGLE = {
    'a': 'а', 'b': 'б', 'd': 'д', 'e': 'е', 'f': 'ф',
    'g': 'г', 'h': 'ҳ', 'i': 'и', 'j': 'ж', 'k': 'к',
    'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п',
    'q': 'қ', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у',
    'v': 'в', 'x': 'х', 'y': 'й', 'z': 'з',
    'A': 'А', 'B': 'Б', 'D': 'Д', 'E': 'Е', 'F': 'Ф',
    'G': 'Г', 'H': 'Ҳ', 'I': 'И', 'J': 'Ж', 'K': 'К',
    'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П',
    'Q': 'Қ', 'R': 'Р', 'S': 'С', 'T': 'Т', 'U': 'У',
    'V': 'В', 'X': 'Х', 'Y': 'Й', 'Z': 'З',
}

# Cyrillic → Latin (reverse)
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya',
    # Uzbek-specific Cyrillic
    'ў': "oʻ", 'қ': 'q', 'ғ': "gʻ", 'ҳ': 'h',
    # Uppercase
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
    'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z', 'И': 'I',
    'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
    'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch',
    'Ш': 'Sh', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'Ў': "Oʻ", 'Қ': 'Q', 'Ғ': "Gʻ", 'Ҳ': 'H',
}


# ═══════════════════════════════════════════════════════════════════════
# ARABIC SCRIPT ↔ LATIN (Uzbek/Chagatai Arabic orthography)
# ═══════════════════════════════════════════════════════════════════════

# Arabic → Latin phonetic (Uzbek pronunciation, not AA pronunciation)
ARABIC_TO_LATIN = {
    'ا': 'a', 'آ': 'a', 'أ': 'a', 'إ': 'i',
    'ب': 'b', 'پ': 'p',
    'ت': 't', 'ث': 's',
    'ج': 'j', 'چ': 'ch',
    'ح': 'h', 'خ': 'x',
    'د': 'd', 'ذ': 'z',
    'ر': 'r', 'ز': 'z', 'ژ': 'j',
    'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'z',
    'ط': 't', 'ظ': 'z',
    'ع': "'", 'غ': "gʻ",
    'ف': 'f', 'ق': 'q',
    'ک': 'k', 'ك': 'k',
    'گ': 'g',
    'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'ھ': 'h',
    'و': 'v',  # Uzbek pronunciation (not 'w')
    'ی': 'y', 'ي': 'y',
    'ئ': "'",
    # Vowel diacritics
    'َ': 'a', 'ِ': 'i', 'ُ': 'u',
    'ً': 'an', 'ٍ': 'in', 'ٌ': 'un',
    'ّ': '',  # shadda (gemination — handled separately)
    'ْ': '',  # sukun
}

# Latin → Arabic (approximation for Uzbek)
LATIN_TO_ARABIC = {
    'a': 'ا', 'b': 'ب', 'ch': 'چ', 'd': 'د', 'e': 'ە',
    'f': 'ف', 'g': 'گ', "gʻ": 'غ', "g'": 'غ',
    'h': 'ح', 'i': 'ی', 'j': 'ج', 'k': 'ک',
    'l': 'ل', 'm': 'م', 'n': 'ن', 'o': 'و',
    "oʻ": 'ۆ', "o'": 'ۆ',
    'p': 'پ', 'q': 'ق', 'r': 'ر', 's': 'س',
    'sh': 'ش', 't': 'ت', 'u': 'ۇ', 'v': 'و',
    'x': 'خ', 'y': 'ی', 'z': 'ز',
}


# ═══════════════════════════════════════════════════════════════════════
# TRANSLITERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def latin_to_cyrillic(text):
    """Convert modern Uzbek Latin to Cyrillic."""
    result = []
    i = 0
    while i < len(text):
        matched = False
        # Try multi-char mappings first (longest first)
        for length in (3, 2):
            if i + length <= len(text):
                chunk = text[i:i+length]
                if chunk in LATIN_TO_CYRILLIC_MULTI:
                    result.append(LATIN_TO_CYRILLIC_MULTI[chunk])
                    i += length
                    matched = True
                    break
        if not matched:
            ch = text[i]
            if ch in LATIN_TO_CYRILLIC_SINGLE:
                result.append(LATIN_TO_CYRILLIC_SINGLE[ch])
            else:
                result.append(ch)
            i += 1
    return ''.join(result)


def cyrillic_to_latin(text):
    """Convert Uzbek Cyrillic to modern Latin."""
    result = []
    for ch in text:
        if ch in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[ch])
        else:
            result.append(ch)
    return ''.join(result)


def arabic_to_latin(text):
    """Convert Arabic-script Uzbek/Chagatai to Latin phonetic form."""
    result = []
    for ch in text:
        if ch in ARABIC_TO_LATIN:
            result.append(ARABIC_TO_LATIN[ch])
        elif ch == ' ' or ch.isascii():
            result.append(ch)
        # Skip unknown Arabic diacritics/marks
    return ''.join(result)


def latin_to_arabic(text):
    """Approximate Latin → Arabic script (Uzbek orthography)."""
    result = []
    i = 0
    t = text.lower()
    while i < len(t):
        matched = False
        for length in (3, 2):
            if i + length <= len(t):
                chunk = t[i:i+length]
                if chunk in LATIN_TO_ARABIC:
                    result.append(LATIN_TO_ARABIC[chunk])
                    i += length
                    matched = True
                    break
        if not matched:
            ch = t[i]
            if ch in LATIN_TO_ARABIC:
                result.append(LATIN_TO_ARABIC[ch])
            else:
                result.append(ch)
            i += 1
    return ''.join(result)


# ═══════════════════════════════════════════════════════════════════════
# NORMALIZATION — Strip to root consonants
# ═══════════════════════════════════════════════════════════════════════

# Uzbek vowels (in Latin transliteration)
UZBEK_VOWELS = set('aeiouyаеёиоуўэюяاآأإَُِ')

# Common "Persian" prefixes/suffixes in Uzbek
PERSIAN_AFFIXES = [
    # Prefixes
    'be', 'ba', 'dar', 'bar', 'na', 'bi',
    # Suffixes
    'gar', 'kor', 'xona', 'dona', 'goh', 'iston',
    'chi', 'lik', 'siz', 'li',
]


def normalize(text):
    """
    Normalize input to a phonetic skeleton for root matching.
    Steps:
    1. Detect script and transliterate to Latin
    2. Lowercase
    3. Strip diacritics
    4. Return cleaned form
    """
    script = detect_script(text)

    if script == 'cyrillic':
        latin = cyrillic_to_latin(text)
    elif script == 'arabic':
        latin = arabic_to_latin(text)
    elif script == 'latin':
        latin = text
    else:
        latin = text

    # Lowercase
    latin = latin.lower()

    # Remove non-letter chars except apostrophe
    latin = re.sub(r"[^a-zʻ'']", '', latin)

    return latin


def extract_consonants(text):
    """Extract consonant skeleton from normalized Latin form."""
    normalized = normalize(text)
    consonants = []
    vowels = set('aeiouy')
    for ch in normalized:
        if ch not in vowels:
            consonants.append(ch)
    return ''.join(consonants)


def strip_persian(text):
    """
    Strip known "Persian" affixes to reveal the underlying root.
    Returns list of candidate stripped forms.
    """
    normalized = normalize(text)
    candidates = [normalized]

    for affix in PERSIAN_AFFIXES:
        if normalized.endswith(affix) and len(normalized) > len(affix) + 2:
            candidates.append(normalized[:-len(affix)])
        if normalized.startswith(affix) and len(normalized) > len(affix) + 2:
            candidates.append(normalized[len(affix):])

    return list(set(candidates))


# Uzbek grammatical suffixes (ordered longest first for greedy strip)
UZBEK_SUFFIXES = [
    # Longest first — greedy matching
    # Compound verb suffixes
    'lashtirilgan', 'lashtirish', 'lashmoqda',
    'lashgan', 'lashdi', 'lashi', 'lasha',
    # Case + plural combos
    'laridagi', 'laridan', 'larding', 'larning', 'lariga',
    'larda', 'lardan', 'larni', 'larga',
    # Case suffixes
    'imizdan', 'imizda', 'imizni', 'imizga',
    'ingdan', 'ingda', 'ingni',
    'ining', 'idagi',
    'dagi', 'dan', 'ning', 'ga', 'da', 'ni', 'dir',
    # Plural
    'lar', 'ler',
    # Verb tenses
    'ladi', 'laydi', 'landi',
    'moqda', 'yotir', 'yapti', 'yatir',
    'ildi', 'ilgan', 'ilish',
    'adi', 'idi', 'gan', 'kan',
    'di', 'ti', 'mi', 'shi',
    # Possessive
    'imiz', 'ingiz',
    'ing', 'im', 'si',
    # Derivational — BI native
    'lik', 'chi', 'siz', 'li',
    'ish', 'ik', 'iq',
    # Derivational — FA corridor imports (strip these to find BI root underneath)
    # These are NOT BI suffixes — they are tazik/FA wrapper morphemes
    # that replaced BI equivalents in modern Uzbek
    'iston',  # FA: -stan (land) — BI equivalent: -liq (BN01) or -yurt
    'xona',   # FA: -khana (house) — BI equivalent: -uy/-öy (house)
    'dona',   # FA: -dana (piece) — no BI equivalent, counting word
    'goh',    # FA: -gah (place) — BI equivalent: -liq (BN01) or compound
    # Additional common suffixes
    'gi', 'ki', 'qi',
    'not', 'mot', 'ot',
    'liq', 'lik',
    # Single-letter (last resort)
    'i', 'a',
]


def strip_suffixes(text):
    """
    Strip Uzbek grammatical suffixes to reveal the stem.
    Returns list of candidate stems (original + stripped forms).
    Agglutinative: suffixes stack, so strip iteratively.
    Also handles o'/g' apostrophe compounds by trying both
    with and without trailing characters after apostrophe.
    """
    normalized = normalize(text)
    candidates = [normalized]

    current = normalized
    for _ in range(4):  # max 4 rounds of stripping (Uzbek stacks deep)
        stripped = False
        for suffix in UZBEK_SUFFIXES:
            if current.endswith(suffix) and len(current) > len(suffix) + 1:
                stem = current[:-len(suffix)]
                if stem and stem not in candidates:
                    candidates.append(stem)
                # Also try ALL shorter suffixes that match, to catch intermediates
                # e.g. uzilish: -ilish→uz BUT also -ish→uzil
                for shorter in UZBEK_SUFFIXES:
                    if shorter != suffix and current.endswith(shorter) and len(current) > len(shorter) + 1:
                        alt = current[:-len(shorter)]
                        if alt and alt not in candidates:
                            candidates.append(alt)
                current = stem
                stripped = True
                break
        if not stripped:
            break

    # Apostrophe handling: for stems containing ', try cutting at apostrophe boundaries
    # e.g. bo'ladi → bo'l (not just bo')
    # Also try the form WITHOUT apostrophe for DB matching
    extra = []
    for c in candidates:
        # If candidate ends with apostrophe, it was over-stripped — try adding back
        if c.endswith("'"):
            # Try appending common post-apostrophe letters
            for ch in 'zlgn':
                trial = c + ch
                if trial not in candidates and trial not in extra:
                    extra.append(trial)
        # Try replacing o'/g' with simple o/g for broader matching
        if "'" in c:
            simple = c.replace("'", "")
            if simple not in candidates and simple not in extra:
                extra.append(simple)

    candidates.extend(extra)
    return list(set(candidates))


def load_bi_suffixes_from_db(db_path=None):
    """
    Load BI suffix inventory from bitig_*_tasrif DB tables.
    Returns dict: {suffix: (code, category, function, is_bi_native)}
    Falls back to UZBEK_SUFFIXES if DB unavailable.
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'uslap_database_v3.db'
        )
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        suffixes = {}
        # Verb tasrif
        for row in conn.execute("SELECT code, suffix_or_affix, function FROM bitig_verb_tasrif"):
            for s in row[1].replace('/', ',').split(','):
                s = s.strip().lstrip('-')
                if s and len(s) >= 2:
                    suffixes[s] = (row[0], 'VERB', row[2], True)
        # Noun tasrif
        for row in conn.execute("SELECT code, suffix_or_affix, function FROM bitig_noun_tasrif"):
            for s in row[1].replace('/', ',').split(','):
                s = s.strip().lstrip('-')
                if s and len(s) >= 2:
                    suffixes[s] = (row[0], 'NOUN', row[2], True)
        # Case tasrif
        for row in conn.execute("SELECT code, suffix_or_affix, case_name, function FROM bitig_case_tasrif"):
            for s in row[1].replace('/', ',').split(','):
                s = s.strip().lstrip('-')
                if s and len(s) >= 2:
                    suffixes[s] = (row[0], 'CASE', f'{row[2]}: {row[3]}', True)
        # Grammar tasrif
        for row in conn.execute("SELECT code, suffix_or_affix, category, function FROM bitig_grammar_tasrif"):
            if row[2] == 'VOWEL_HARMONY':
                continue  # Not a suffix
            for s in row[1].replace('/', ',').split(','):
                s = s.strip().lstrip('-')
                if s and len(s) >= 2:
                    suffixes[s] = (row[0], row[2], row[3], True)
        # FA corridor suffixes (not BI native)
        for fa_suffix, bi_equiv in [
            ('iston', '-liq/-yurt'), ('xona', '-uy/-öy'),
            ('dona', 'counting'), ('goh', '-liq/compound'),
        ]:
            suffixes[fa_suffix] = ('FA_CORRIDOR', 'FA_IMPORT', bi_equiv, False)
        conn.close()
        return suffixes
    except Exception:
        return {}


# Cached BI suffix inventory (loaded once)
_BI_SUFFIX_DB = None

def get_bi_suffix_info(suffix_text):
    """
    Check if a suffix is BI-native or FA-corridor import.
    Returns (code, category, function, is_bi_native) or None.
    """
    global _BI_SUFFIX_DB
    if _BI_SUFFIX_DB is None:
        _BI_SUFFIX_DB = load_bi_suffixes_from_db()
    return _BI_SUFFIX_DB.get(suffix_text.lower().lstrip('-'))


def to_all_scripts(latin_form):
    """
    Given a Latin Uzbek form, return it in all 3 scripts.
    Returns dict: {"latin": ..., "cyrillic": ..., "arabic": ...}
    """
    return {
        "latin": latin_form,
        "cyrillic": latin_to_cyrillic(latin_form),
        "arabic": latin_to_arabic(latin_form),
    }


# ═══════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    print('أَمْر أُزْبَكِي — Uzbek Transliteration Engine')
    print()

    # Test detect_script
    tests = [
        ("kitob", "latin"),
        ("китоб", "cyrillic"),
        ("كتاب", "arabic"),
    ]
    print("Script detection:")
    for text, expected in tests:
        result = detect_script(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}  {text} → {result}")

    print()

    # Test Latin → Cyrillic
    print("Latin → Cyrillic:")
    lat_tests = [
        ("kitob", "китоб"),
        ("oʻzbek", "ўзбек"),
        ("gʻalaba", "ғалаба"),
        ("shaxar", "шахар"),
        ("choy", "чой"),
    ]
    for lat, expected_cyr in lat_tests:
        result = latin_to_cyrillic(lat)
        status = "PASS" if result == expected_cyr else "FAIL"
        print(f"  {status}  {lat} → {result} (expected: {expected_cyr})")

    print()

    # Test Cyrillic → Latin
    print("Cyrillic → Latin:")
    cyr_tests = [
        ("китоб", "kitob"),
        ("ўзбек", "oʻzbek"),
        ("ғалаба", "gʻalaba"),
    ]
    for cyr, expected_lat in cyr_tests:
        result = cyrillic_to_latin(cyr)
        status = "PASS" if result == expected_lat else "FAIL"
        print(f"  {status}  {cyr} → {result} (expected: {expected_lat})")

    print()

    # Test Arabic → Latin
    print("Arabic → Latin:")
    ar_tests = [
        ("كتاب", "ktab"),
        ("قلم", "qlm"),
    ]
    for ar, expected in ar_tests:
        result = arabic_to_latin(ar)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}  {ar} → {result} (expected: {expected})")

    print()

    # Test normalize
    print("Normalize (all scripts → Latin):")
    norm_tests = [
        ("kitob", "kitob"),
        ("китоб", "kitob"),
        ("كتاب", "ktab"),
    ]
    for text, expected in norm_tests:
        result = normalize(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}  {text} → {result} (expected: {expected})")

    print()

    # Test consonant extraction
    print("Consonant skeleton:")
    for word in ["kitob", "dunyo", "olam", "shaxar"]:
        print(f"  {word} → {extract_consonants(word)}")

    print()

    # Test all-scripts
    print("All scripts:")
    for word in ["kitob", "dunyo", "olam"]:
        scripts = to_all_scripts(word)
        print(f"  {word}: lat={scripts['latin']} cyr={scripts['cyrillic']} ar={scripts['arabic']}")
