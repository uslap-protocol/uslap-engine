#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر BITIG ALPHABET — Orkhon Script (𐰋𐰃𐱅𐰏)

Phase 0 of the BI track in the أَمْر computing system.
Mirror of amr_alphabet.py (AA Phase 0).

The Orkhon script encodes vowel harmony IN the consonants:
most consonants have TWO forms — back-vowel and front-vowel.
You cannot write a back-vowel word with front-vowel consonants.
The script ENFORCES the grammar.

Data sourced from:
  - bitig_a1_entries (1,795 entries with orig2_script)
  - bitig_phonology (26 phonemes with Kashgari frequency)
  - Orkhon inscriptions (SRC08)
  - Kashgari Dīwān (SRC01) transliterations
"""

import os
import sys
import sqlite3

# ═══════════════════════════════════════════════════════════════════════
# ORKHON ALPHABET — Back/Front vowel pairs
# ═══════════════════════════════════════════════════════════════════════
# Key insight: most consonants have TWO glyphs.
# BACK form: used when the root vowel is a, ı, o, u
# FRONT form: used when the root vowel is e, i, ö, ü
# This IS vowel harmony made visible in the script.

ALPHABET = {
    # ── VOWELS ──
    'A': {
        'orkhon': '𐰀',
        'unicode': 'U+10C00',
        'phoneme': 'a',
        'type': 'VOWEL',
        'harmony': 'BACK',
        'kashgari_freq': 3931,
        'description': 'Open back vowel. Most frequent vowel in ORIG2.',
    },
    'I': {
        'orkhon': '𐰃',
        'unicode': 'U+10C03',
        'phoneme': 'i/ı',
        'type': 'VOWEL',
        'harmony': 'FRONT/BACK',
        'kashgari_freq': 3798,
        'description': 'High vowel. Covers both front i and back ı.',
    },
    'O': {
        'orkhon': '𐰆',
        'unicode': 'U+10C06',
        'phoneme': 'o/u',
        'type': 'VOWEL',
        'harmony': 'BACK',
        'kashgari_freq': 2416 + 1416,  # o + u
        'description': 'Rounded back vowel. Covers both o and u.',
    },
    'OE': {
        'orkhon': '𐰇',
        'unicode': 'U+10C07',
        'phoneme': 'ö/ü',
        'type': 'VOWEL',
        'harmony': 'FRONT',
        'kashgari_freq': 0,  # Dankoff doesn't distinguish consistently
        'description': 'Rounded front vowel. Covers both ö and ü.',
    },

    # ── CONSONANTS WITH BACK/FRONT PAIRS ──
    'B_BACK': {
        'orkhon': '𐰉',
        'unicode': 'U+10C09',
        'phoneme': 'b',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'B_FRONT',
        'latin': 'b',
        'kashgari_freq': 640,
        'description': 'Bilabial stop, back-vowel form.',
    },
    'B_FRONT': {
        'orkhon': '𐰋',
        'unicode': 'U+10C0B',
        'phoneme': 'b',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'B_BACK',
        'latin': 'b',
        'description': 'Bilabial stop, front-vowel form.',
    },
    'G_BACK': {
        'orkhon': '𐰍',
        'unicode': 'U+10C0D',
        'phoneme': 'g/ğ',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'G_FRONT',
        'latin': 'g',
        'kashgari_freq': 556,
        'description': 'Velar stop/fricative, back-vowel form.',
    },
    'G_FRONT': {
        'orkhon': '𐰏',
        'unicode': 'U+10C0F',
        'phoneme': 'g',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'G_BACK',
        'latin': 'g',
        'description': 'Velar stop, front-vowel form.',
    },
    'D': {
        'orkhon': '𐰑',
        'unicode': 'U+10C11',
        'phoneme': 'd',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'd',
        'kashgari_freq': 791,
        'description': 'Alveolar stop. Single form for both harmonies.',
    },
    'Z': {
        'orkhon': '𐰔',
        'unicode': 'U+10C14',
        'phoneme': 'z',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'z',
        'kashgari_freq': 344,
        'description': 'Alveolar fricative.',
    },
    'Y_BACK': {
        'orkhon': '𐰖',
        'unicode': 'U+10C16',
        'phoneme': 'y',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'Y_FRONT',
        'latin': 'y',
        'kashgari_freq': 1358,
        'description': 'Palatal glide, back-vowel form.',
    },
    'Y_FRONT': {
        'orkhon': '𐰘',
        'unicode': 'U+10C18',
        'phoneme': 'y',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'Y_BACK',
        'latin': 'y',
        'description': 'Palatal glide, front-vowel form.',
    },
    'K_FRONT': {
        'orkhon': '𐰚',
        'unicode': 'U+10C1A',
        'phoneme': 'k',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'Q_BACK',
        'latin': 'k',
        'kashgari_freq': 824,
        'description': 'Front velar stop. Paired with Q (back velar).',
    },
    'Q_BACK': {
        'orkhon': '𐰴',
        'unicode': 'U+10C34',
        'phoneme': 'q',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'K_FRONT',
        'latin': 'q',
        'kashgari_freq': 1107,
        'description': 'Back velar stop. BI-distinctive. Paired with K (front velar).',
    },
    'L_BACK': {
        'orkhon': '𐰞',
        'unicode': 'U+10C1E',
        'phoneme': 'l',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'L_FRONT',
        'latin': 'l',
        'kashgari_freq': 2573,
        'description': 'Lateral, back-vowel form. Most frequent BI consonant.',
    },
    'L_FRONT': {
        'orkhon': '𐰠',
        'unicode': 'U+10C20',
        'phoneme': 'l',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'L_BACK',
        'latin': 'l',
        'description': 'Lateral, front-vowel form.',
    },
    'M': {
        'orkhon': '𐰢',
        'unicode': 'U+10C22',
        'phoneme': 'm',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'm',
        'kashgari_freq': 500,
        'description': 'Bilabial nasal. Single form.',
    },
    'N_BACK': {
        'orkhon': '𐰣',
        'unicode': 'U+10C23',
        'phoneme': 'n',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'N_FRONT',
        'latin': 'n',
        'kashgari_freq': 1111,
        'description': 'Alveolar nasal, back-vowel form.',
    },
    'N_FRONT': {
        'orkhon': '𐰤',
        'unicode': 'U+10C24',
        'phoneme': 'n',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'N_BACK',
        'latin': 'n',
        'description': 'Alveolar nasal, front-vowel form.',
    },
    'NG': {
        'orkhon': '𐰭',
        'unicode': 'U+10C2D',
        'phoneme': 'ŋ',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'ng',
        'kashgari_freq': 129,  # bigram count from Kashgari
        'description': 'Velar nasal. The ŋ sound (as in tengri). Single glyph.',
    },
    'P': {
        'orkhon': '𐰯',
        'unicode': 'U+10C2F',
        'phoneme': 'p',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'p',
        'kashgari_freq': 212,
        'description': 'Bilabial stop voiceless. Single form.',
    },
    'C': {
        'orkhon': '𐰲',
        'unicode': 'U+10C32',
        'phoneme': 'c/ç',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'c',
        'kashgari_freq': 380,
        'description': 'Palatal affricate (ch sound). Single form.',
    },
    'IQ': {
        'orkhon': '𐰶',
        'unicode': 'U+10C36',
        'phoneme': 'iq/ıq',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'latin': 'q',
        'description': 'Back velar with high vowel. Used in -ıq/-iq endings.',
    },
    'R_BACK': {
        'orkhon': '𐰺',
        'unicode': 'U+10C3A',
        'phoneme': 'r',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'R_FRONT',
        'latin': 'r',
        'kashgari_freq': 2097,
        'description': 'Alveolar trill, back-vowel form. 2nd most frequent consonant.',
    },
    'R_FRONT': {
        'orkhon': '𐰼',
        'unicode': 'U+10C3C',
        'phoneme': 'r',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'R_BACK',
        'latin': 'r',
        'description': 'Alveolar trill, front-vowel form.',
    },
    'S_BACK': {
        'orkhon': '𐰽',
        'unicode': 'U+10C3D',
        'phoneme': 's',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'S_FRONT',
        'latin': 's',
        'kashgari_freq': 867,
        'description': 'Alveolar fricative, back-vowel form.',
    },
    'S_FRONT': {
        'orkhon': '𐰾',
        'unicode': 'U+10C3E',
        'phoneme': 's',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'S_BACK',
        'latin': 's',
        'description': 'Alveolar fricative, front-vowel form.',
    },
    'SH': {
        'orkhon': '𐱁',
        'unicode': 'U+10C41',
        'phoneme': 'ş/sh',
        'type': 'CONSONANT',
        'harmony': 'BOTH',
        'latin': 'sh',
        'description': 'Palatal fricative. Single form.',
    },
    'T_BACK': {
        'orkhon': '𐱃',
        'unicode': 'U+10C43',
        'phoneme': 't',
        'type': 'CONSONANT',
        'harmony': 'BACK',
        'pair': 'T_FRONT',
        'latin': 't',
        'kashgari_freq': 1469,
        'description': 'Alveolar stop, back-vowel form.',
    },
    'T_FRONT': {
        'orkhon': '𐱅',
        'unicode': 'U+10C45',
        'phoneme': 't',
        'type': 'CONSONANT',
        'harmony': 'FRONT',
        'pair': 'T_BACK',
        'latin': 't',
        'description': 'Alveolar stop, front-vowel form.',
    },
    'BASH': {
        'orkhon': '𐱈',
        'unicode': 'U+10C48',
        'phoneme': 'baş',
        'type': 'LOGOGRAM',
        'harmony': 'BACK',
        'latin': 'bash',
        'description': 'Logogram for baş (head/chief). The ONLY logogram in Orkhon — the rest is alphabetic.',
    },
}

# ═══════════════════════════════════════════════════════════════════════
# VOWEL HARMONY PAIRS — the structural law encoded in script
# ═══════════════════════════════════════════════════════════════════════

HARMONY_PAIRS = {
    # consonant: (back_form_key, front_form_key)
    'b': ('B_BACK', 'B_FRONT'),
    'g': ('G_BACK', 'G_FRONT'),
    'k/q': ('Q_BACK', 'K_FRONT'),
    'l': ('L_BACK', 'L_FRONT'),
    'n': ('N_BACK', 'N_FRONT'),
    'r': ('R_BACK', 'R_FRONT'),
    's': ('S_BACK', 'S_FRONT'),
    't': ('T_BACK', 'T_FRONT'),
    'y': ('Y_BACK', 'Y_FRONT'),
}

# Consonants with single form (no harmony pair)
HARMONY_NEUTRAL = ['D', 'Z', 'M', 'NG', 'P', 'C', 'SH']


# ═══════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def get_status():
    """Summary stats."""
    vowels = sum(1 for v in ALPHABET.values() if v['type'] == 'VOWEL')
    consonants = sum(1 for v in ALPHABET.values() if v['type'] == 'CONSONANT')
    pairs = len(HARMONY_PAIRS)
    return {
        'total_glyphs': len(ALPHABET),
        'vowels': vowels,
        'consonants': consonants,
        'logogram': 1,  # BASH
        'harmony_pairs': pairs,
        'harmony_neutral': len(HARMONY_NEUTRAL),
    }


def get_letter(key):
    """Get letter info by key."""
    return ALPHABET.get(key)


def orkhon_to_latin(orkhon_text):
    """Convert Orkhon script to Latin transliteration."""
    # Build reverse map: orkhon char → latin
    char_map = {}
    for key, info in ALPHABET.items():
        char_map[info['orkhon']] = info.get('latin', info['phoneme'])
    result = []
    for ch in orkhon_text:
        if ch in char_map:
            result.append(char_map[ch])
        elif ch == ' ':
            result.append(' ')
        # skip unknown
    return ''.join(result)


def latin_to_orkhon(latin_text, harmony='back'):
    """Convert Latin transliteration to Orkhon script.
    harmony: 'back' or 'front' — determines which consonant form to use.
    """
    # Build forward map: latin → orkhon (with harmony)
    result = []
    i = 0
    text = latin_text.lower()
    while i < len(text):
        # Try digraphs first
        if i + 1 < len(text):
            digraph = text[i:i+2]
            if digraph == 'sh':
                result.append(ALPHABET['SH']['orkhon'])
                i += 2
                continue
            if digraph == 'ng':
                result.append(ALPHABET['NG']['orkhon'])
                i += 2
                continue
        ch = text[i]
        if ch in 'aıou' and harmony == 'back':
            if ch in 'ao':
                result.append(ALPHABET['A']['orkhon'] if ch == 'a' else ALPHABET['O']['orkhon'])
            elif ch in 'ıu':
                result.append(ALPHABET['I']['orkhon'] if ch == 'ı' else ALPHABET['O']['orkhon'])
            else:
                result.append(ALPHABET['A']['orkhon'])
        elif ch in 'eiöü' and harmony == 'front':
            if ch in 'ei':
                result.append(ALPHABET['I']['orkhon'])
            elif ch in 'öü':
                result.append(ALPHABET['OE']['orkhon'])
        elif ch in HARMONY_PAIRS.get(ch, ('', ''))[0:1]:
            # Consonant with harmony pair
            for consonant, (back_key, front_key) in HARMONY_PAIRS.items():
                if ch == consonant[0]:
                    key = back_key if harmony == 'back' else front_key
                    result.append(ALPHABET[key]['orkhon'])
                    break
        elif ch == 'q':
            result.append(ALPHABET['Q_BACK']['orkhon'])
        elif ch == 'k':
            result.append(ALPHABET['K_FRONT']['orkhon'])
        elif ch == 'd':
            result.append(ALPHABET['D']['orkhon'])
        elif ch == 'z':
            result.append(ALPHABET['Z']['orkhon'])
        elif ch == 'm':
            result.append(ALPHABET['M']['orkhon'])
        elif ch == 'p':
            result.append(ALPHABET['P']['orkhon'])
        elif ch == 'c':
            result.append(ALPHABET['C']['orkhon'])
        elif ch == ' ':
            result.append('⁚')  # Orkhon word separator
        i += 1
    return ''.join(result)


def check_harmony(orkhon_text):
    """Check if an Orkhon text obeys vowel harmony.
    Returns (is_valid, violations).
    """
    # Determine harmony from vowels
    back_vowels = {ALPHABET['A']['orkhon'], ALPHABET['O']['orkhon']}
    front_vowels = {ALPHABET['I']['orkhon'], ALPHABET['OE']['orkhon']}

    found_back = any(ch in back_vowels for ch in orkhon_text)
    found_front = any(ch in front_vowels for ch in orkhon_text)

    # Check consonant forms match
    violations = []
    for ch in orkhon_text:
        for consonant, (back_key, front_key) in HARMONY_PAIRS.items():
            back_char = ALPHABET[back_key]['orkhon']
            front_char = ALPHABET[front_key]['orkhon']
            if ch == back_char and found_front and not found_back:
                violations.append(f'{ch} is BACK form but word has FRONT vowels')
            elif ch == front_char and found_back and not found_front:
                violations.append(f'{ch} is FRONT form but word has BACK vowels')

    return (len(violations) == 0, violations)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: amr_bitig_alphabet.py [status|letter KEY|to_latin TEXT|to_orkhon TEXT|harmony TEXT]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'status':
        s = get_status()
        print(f"BI Alphabet: {s['total_glyphs']} glyphs")
        print(f"  Vowels: {s['vowels']}")
        print(f"  Consonants: {s['consonants']}")
        print(f"  Logogram: {s['logogram']} (𐱈 = baş)")
        print(f"  Harmony pairs: {s['harmony_pairs']} (9 consonants × 2 forms)")
        print(f"  Harmony neutral: {s['harmony_neutral']} (single form)")

    elif cmd == 'letter' and len(sys.argv) > 2:
        info = get_letter(sys.argv[2])
        if info:
            for k, v in info.items():
                print(f"  {k}: {v}")
        else:
            print(f"Unknown letter key: {sys.argv[2]}")

    elif cmd == 'to_latin' and len(sys.argv) > 2:
        text = ' '.join(sys.argv[2:])
        print(orkhon_to_latin(text))

    elif cmd == 'to_orkhon' and len(sys.argv) > 2:
        text = ' '.join(sys.argv[2:])
        print(f"Back harmony:  {latin_to_orkhon(text, 'back')}")
        print(f"Front harmony: {latin_to_orkhon(text, 'front')}")

    elif cmd == 'harmony' and len(sys.argv) > 2:
        text = ' '.join(sys.argv[2:])
        valid, violations = check_harmony(text)
        print(f"Valid: {valid}")
        if violations:
            for v in violations:
                print(f"  ⛔ {v}")
