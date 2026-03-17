#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP QUF VALIDATOR — al-Alaq (96) Extension
اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ — "Read in the name of your Lord who created" (Q96:1)

Automated QUF (Quantifiable, Universal, Falsifiable) gate checker.
Takes a root and downstream word, validates the phonetic chain against S01–S26.

Modes:
  validate ROOT_ID WORD [--lang en|ru]   Validate one entry
  batch [en|ru|fa|bitig|latin|all]       Validate all entries in a sibling DB
  compete WORD [--lang en|ru]            Find all competing roots for a word
  stats                                   Shift usage statistics across the lattice
  audit                                   Flag entries with chain problems

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
import re
import sys
import os
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict

# ─── PATH ─────────────────────────────────────────────────────────────────────
DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

# ─── ARABIC DIACRITICS (strip for comparison) ────────────────────────────────
ARABIC_DIACRITICS = set([
    '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650',
    '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656',
    '\u0670',
])

def strip_diacritics(text: str) -> str:
    return ''.join(c for c in text if c not in ARABIC_DIACRITICS)


# ═══════════════════════════════════════════════════════════════════════════════
# M1 SHIFT TABLE — S01–S26
# For each Arabic letter: which downstream consonants it can produce
# ═══════════════════════════════════════════════════════════════════════════════

SHIFT_TABLE_EN: Dict[str, Dict] = {
    # Arabic letter → { shift_id, outputs (lowercase), name }
    'ق': {'sid': 'S01', 'outputs': {'c', 'k', 'q', 'g'},        'name': 'qāf'},
    'ج': {'sid': 'S02', 'outputs': {'g', 'j'},                   'name': 'jīm'},
    'ح': {'sid': 'S03', 'outputs': {'h', 'c'},                   'name': 'ḥāʾ',    'can_drop': True},
    'ط': {'sid': 'S04', 'outputs': {'t'},                         'name': 'ṭāʾ'},
    'ش': {'sid': 'S05', 'outputs': {'sh', 's'},                   'name': 'shīn'},
    'ض': {'sid': 'S06', 'outputs': {'th', 'd'},                   'name': 'ḍād'},
    'ع': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'ʿayn',   'can_drop': True},
    'ف': {'sid': 'S08', 'outputs': {'f', 'p', 'v'},              'name': 'fāʾ'},
    'ب': {'sid': 'S09', 'outputs': {'b', 'p', 'v'},              'name': 'bāʾ'},
    'و': {'sid': 'S10', 'outputs': {'v', 'w', 'o', 'r', 'u'},   'name': 'wāw',    'can_drop': True},  # also vowelizes
    'خ': {'sid': 'S11', 'outputs': {'ch', 'x', 'k', 'c'},        'name': 'khāʾ'},
    'ذ': {'sid': 'S12', 'outputs': {'d', 'th'},                   'name': 'dhāl'},
    'ص': {'sid': 'S13', 'outputs': {'s', 'c', 'z'},              'name': 'ṣād'},
    'غ': {'sid': 'S14', 'outputs': {'gh', 'g'},                   'name': 'ghayn'},
    'ر': {'sid': 'S15', 'outputs': {'r'},                         'name': 'rāʾ'},
    'ل': {'sid': 'S16', 'outputs': {'l'},                         'name': 'lām'},
    'م': {'sid': 'S17', 'outputs': {'m'},                         'name': 'mīm'},
    'ن': {'sid': 'S18', 'outputs': {'n'},                         'name': 'nūn'},
    'د': {'sid': 'S19', 'outputs': {'d', 't'},                    'name': 'dāl'},
    'ك': {'sid': 'S20', 'outputs': {'c', 'k', 'ch', 'g'},       'name': 'kāf'},
    'س': {'sid': 'S21', 'outputs': {'s', 'c', 'z'},              'name': 'sīn'},
    'ز': {'sid': 'S22', 'outputs': {'z', 's'},                    'name': 'zāy'},
    'ه': {'sid': 'S23', 'outputs': {'h'},                         'name': 'hāʾ',    'can_drop': True},
    'ت': {'sid': 'S24', 'outputs': {'t'},                         'name': 'tāʾ'},
    'ظ': {'sid': 'S25', 'outputs': {'z', 'th'},                   'name': 'ẓāʾ'},
    'ث': {'sid': 'S26', 'outputs': {'th'},                        'name': 'thāʾ'},
    # ── SUPPLEMENTARY (not in core S01-S26 but essential for root validation) ──
    # Yāʾ — appears in ~30% of roots. Downstream: y, i, or drops.
    'ي': {'sid': 'SY',  'outputs': {'y', 'i', 'j'},              'name': 'yāʾ',    'can_drop': True},
    # Alef / hamza — not a shift letter, but can appear in roots
    'أ': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'hamza',   'can_drop': True},
    'ا': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'alif',    'can_drop': True},
    'إ': {'sid': 'S07', 'outputs': {'a', 'e', 'i'},              'name': 'hamza-i', 'can_drop': True},
    'ء': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'hamza-q', 'can_drop': True},
}

# Russian shift table — same Arabic letters, different outputs
SHIFT_TABLE_RU: Dict[str, Dict] = {
    'ق': {'sid': 'S01', 'outputs': {'к', 'г'},                   'name': 'qāf'},
    'ج': {'sid': 'S02', 'outputs': {'г', 'ж', 'дж'},             'name': 'jīm'},
    'ح': {'sid': 'S03', 'outputs': {'х'},                         'name': 'ḥāʾ',    'can_drop': True},
    'ط': {'sid': 'S04', 'outputs': {'т'},                         'name': 'ṭāʾ'},
    'ش': {'sid': 'S05', 'outputs': {'ш', 'щ', 'с'},              'name': 'shīn'},
    'ض': {'sid': 'S06', 'outputs': {'д', 'з'},                    'name': 'ḍād'},
    'ع': {'sid': 'S07', 'outputs': {'а'},                         'name': 'ʿayn',   'can_drop': True},
    'ف': {'sid': 'S08', 'outputs': {'ф', 'п'},                    'name': 'fāʾ'},
    'ب': {'sid': 'S09', 'outputs': {'б', 'п', 'в'},              'name': 'bāʾ'},
    'و': {'sid': 'S10', 'outputs': {'в', 'у', 'о'},              'name': 'wāw',    'can_drop': True},
    'خ': {'sid': 'S11', 'outputs': {'х', 'к', 'г'},              'name': 'khāʾ'},
    'ذ': {'sid': 'S12', 'outputs': {'д', 'з'},                    'name': 'dhāl'},
    'ص': {'sid': 'S13', 'outputs': {'с', 'ц', 'з'},              'name': 'ṣād'},
    'غ': {'sid': 'S14', 'outputs': {'г', 'ж'},                    'name': 'ghayn'},
    'ر': {'sid': 'S15', 'outputs': {'р'},                         'name': 'rāʾ'},
    'ل': {'sid': 'S16', 'outputs': {'л'},                         'name': 'lām'},
    'م': {'sid': 'S17', 'outputs': {'м'},                         'name': 'mīm'},
    'ن': {'sid': 'S18', 'outputs': {'н'},                         'name': 'nūn'},
    'د': {'sid': 'S19', 'outputs': {'д', 'т'},                    'name': 'dāl'},
    'ك': {'sid': 'S20', 'outputs': {'к'},                         'name': 'kāf'},
    'س': {'sid': 'S21', 'outputs': {'с'},                         'name': 'sīn'},
    'ز': {'sid': 'S22', 'outputs': {'з', 'с'},                    'name': 'zāy'},
    'ه': {'sid': 'S23', 'outputs': {'г', 'х'},                    'name': 'hāʾ',    'can_drop': True},
    'ت': {'sid': 'S24', 'outputs': {'т', 'д'},                    'name': 'tāʾ'},
    'ظ': {'sid': 'S25', 'outputs': {'з'},                         'name': 'ẓāʾ'},
    'ث': {'sid': 'S26', 'outputs': {'т', 'ф'},                    'name': 'thāʾ'},
    'ي': {'sid': 'SY',  'outputs': {'й', 'и'},                    'name': 'yāʾ',    'can_drop': True},
    'أ': {'sid': 'S07', 'outputs': {'а'},                         'name': 'hamza',   'can_drop': True},
    'ا': {'sid': 'S07', 'outputs': {'а'},                         'name': 'alif',    'can_drop': True},
    'إ': {'sid': 'S07', 'outputs': {'а'},                         'name': 'hamza-i', 'can_drop': True},
    'ء': {'sid': 'S07', 'outputs': {'а'},                         'name': 'hamza-q', 'can_drop': True},
}

# ═══════════════════════════════════════════════════════════════════════════════
# REVERSE LOOKUPS — downstream consonant → possible Arabic sources
# ═══════════════════════════════════════════════════════════════════════════════

def build_reverse_map(shift_table: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """Build: downstream_letter → [(arabic_letter, shift_id), ...]"""
    rev = defaultdict(list)
    for ar_letter, info in shift_table.items():
        for output in info['outputs']:
            rev[output].append((ar_letter, info['sid']))
    return dict(rev)

REVERSE_EN = build_reverse_map(SHIFT_TABLE_EN)
REVERSE_RU = build_reverse_map(SHIFT_TABLE_RU)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSONANT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

EN_VOWELS = set('aeiou')
RU_VOWELS = set('аеёиоуыэюя')

# Common Latin/Greek suffixes to strip (OP_SUFFIX)
EN_SUFFIXES = [
    'tion', 'sion', 'ment', 'ness', 'ment', 'ence', 'ance', 'ious',
    'eous', 'ible', 'able', 'ture', 'ular', 'ular', 'ling', 'ity',
    'ous', 'ive', 'ary', 'ery', 'ory', 'ism', 'ist', 'ate', 'ise',
    'ize', 'ful', 'ish', 'ent', 'ant', 'ure', 'ile', 'ine', 'ual',
    'ial', 'tic', 'ric', 'nic', 'age', 'ade', 'ude', 'ite', 'ute',
    'ing', 'est', 'ess', 'dom', 'fy', 'ly', 'al', 'le', 'er', 'or',
    'ed', 'en', 'ic', 'ty',
]

# Arabic grammatical prefixes (OP_PREFIX)
AR_PREFIXES = ['مُ', 'بَ', 'يَ', 'تَ', 'أَ', 'مَ']
# Mapped to downstream: mu→M, ba→B/P, ya→Y, ta→T, a→A
EN_PREFIXES_FROM_AR = {
    'm': 'مُ',   # MIRACLE: مُرسَل → M-R-S-L
    'b': 'بَ',   # PROPHET: بَعارِف → P/B
    'p': 'بَ',
    'pro': 'بَ',  # PROTECT: prefix PRO from بَ-route
}

# Russian prefixes (OP_RU_PREFIX)
RU_PREFIXES = [
    'ПЕРЕ', 'ВОС', 'ВОЗ', 'РАС', 'РАЗ', 'ПРО', 'ПРИ', 'ПРЕ',
    'ПОД', 'НАД', 'ОТ', 'ДО', 'ПО', 'НА', 'ЗА', 'ИЗ', 'ВЫ',
    'ОБ', 'С', 'У',
]


def extract_consonants_en(word: str) -> List[str]:
    """Extract consonant skeleton from English word (lowercase)."""
    word = word.lower()
    consonants = []
    i = 0
    while i < len(word):
        # Handle digraphs
        if i + 1 < len(word):
            digraph = word[i:i+2]
            if digraph in ('sh', 'ch', 'th', 'gh'):
                consonants.append(digraph)
                i += 2
                continue
        if word[i] not in EN_VOWELS and word[i].isalpha():
            consonants.append(word[i])
        i += 1
    return consonants


def extract_consonants_ru(word: str) -> List[str]:
    """Extract consonant skeleton from Russian word (uppercase)."""
    word = word.upper()
    consonants = []
    i = 0
    while i < len(word):
        # Handle digraph ДЖ
        if i + 1 < len(word) and word[i:i+2] == 'ДЖ':
            consonants.append('дж')
            i += 2
            continue
        ch = word[i].lower()
        if ch not in RU_VOWELS and ch.isalpha():
            consonants.append(ch)
        i += 1
    return consonants


def parse_root_letters(root_str: str) -> List[str]:
    """Parse root letters from format like 'ق-ص-ر' or 'ح-ن-ن'.
    Handles compound roots ('+') by taking the FIRST root only.
    Strips annotations like '(ORIG1)', '(ORIG2)' etc."""
    if not root_str:
        return []

    # For compound roots (CHECKMATE: ش-ه-د+م-و-ت), take first root
    if '+' in root_str:
        root_str = root_str.split('+')[0].strip()

    # Strip annotations in parentheses
    root_str = re.sub(r'\([^)]*\)', '', root_str).strip()

    # Strip everything after ' / ' (alternate notation)
    if ' / ' in root_str:
        root_str = root_str.split(' / ')[0].strip()

    # Strip diacritics
    root_str = strip_diacritics(root_str)

    # Split on hyphen
    letters = [l.strip() for l in root_str.split('-') if l.strip()]
    return letters


def is_orig2_root(root_str: str) -> bool:
    """Check if root contains ORIG2 (Bitig/Turkic) characters.
    These use Orkhon runic script (Unicode range U+10C00-U+10C4F)
    or Latin/Cyrillic transliteration with ' / ' separator."""
    if not root_str:
        return False
    # Orkhon runic Unicode range
    for ch in root_str:
        if '\U00010C00' <= ch <= '\U00010C4F':
            return True
    # Latin letters in root (q-r-t format) — ORIG2 indicator
    if re.search(r'[a-z]-[a-z]', root_str.lower()):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Q-GATE: CONSONANT MAPPING VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

class QGateResult:
    def __init__(self):
        self.passed = False
        self.confidence = 'NONE'             # HIGH / MEDIUM / LOW / FAIL
        self.coverage_ratio = 0.0            # mapped root letters / total DS consonants
        self.mappings: List[Dict] = []       # successful mappings
        self.unmapped: List[Dict] = []       # downstream consonants with no source
        self.operations: List[str] = []      # operations invoked
        self.dropped: List[Dict] = []        # root letters that dropped
        self.extras: List[Dict] = []         # explained extras (ops)
        self.warnings: List[str] = []
        self.ds_consonants: List[str] = []
        self.root_letters_used: List[str] = []

    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        conf = f" [{self.confidence}]" if self.confidence != 'NONE' else ""
        cov = f" (coverage: {self.coverage_ratio:.0%})"
        lines = [f"Q-GATE: {status}{conf}{cov}"]
        if self.ds_consonants:
            lines.append(f"  DS skeleton: {'-'.join(self.ds_consonants)}")
        if self.mappings:
            chain_parts = []
            for m in self.mappings:
                chain_parts.append(f"{m['ar']}→{m['ds']}({m['sid']})")
            lines.append(f"  Chain: {', '.join(chain_parts)}")
        if self.dropped:
            for d in self.dropped:
                lines.append(f"  Drop: {d['ar']} ({d['reason']})")
        if self.operations:
            lines.append(f"  Operations: {', '.join(self.operations)}")
        if self.extras:
            for e in self.extras:
                lines.append(f"  Extra: '{e['ds']}' @{e['pos']} → {e['op']}")
        if self.unmapped:
            for u in self.unmapped:
                lines.append(f"  ✗ UNMAPPED: '{u['ds']}' at position {u['pos']} — no root source")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        return '\n'.join(lines)


def validate_q_gate(root_letters: List[str], downstream_word: str,
                     lang: str = 'en', strip_suffix: bool = True) -> QGateResult:
    """
    Core Q-gate: check if root consonants can be found IN ORDER within the
    downstream consonant skeleton, with extras explained by operations.

    Algorithm:
    1. Extract downstream consonants
    2. Use DP to find optimal alignment: root letters mapped left→right onto
       downstream consonants, allowing skips (corridor artifacts)
    3. Classify skipped consonants: OP_NASAL, OP_SUFFIX, OP_PREFIX, epenthetic
    4. Pass if ALL root letters are mapped; extras explained by ops
    """
    result = QGateResult()

    shift_table = SHIFT_TABLE_EN if lang == 'en' else SHIFT_TABLE_RU
    reverse_map = REVERSE_EN if lang == 'en' else REVERSE_RU

    # Extract downstream consonants
    if lang == 'en':
        ds_consonants = extract_consonants_en(downstream_word)
    else:
        ds_consonants = extract_consonants_ru(downstream_word)

    if not ds_consonants:
        result.warnings.append(f"No consonants extracted from '{downstream_word}'")
        return result

    if not root_letters:
        result.warnings.append("No root letters provided")
        return result

    # Build: for each root letter, what downstream consonants can it produce?
    root_can_produce: Dict[int, Set[str]] = {}
    root_can_drop: Dict[int, bool] = {}
    root_sid: Dict[int, str] = {}

    for i, rl in enumerate(root_letters):
        rl_clean = strip_diacritics(rl)
        if rl_clean in shift_table:
            root_can_produce[i] = shift_table[rl_clean]['outputs']
            root_can_drop[i] = shift_table[rl_clean].get('can_drop', False)
            root_sid[i] = shift_table[rl_clean]['sid']
        else:
            root_can_produce[i] = set()
            root_can_drop[i] = False
            root_sid[i] = '???'
            result.warnings.append(f"Root letter '{rl_clean}' not in shift table")

    # ── OP_VOICE pairs: extend root_can_produce with voiced/devoiced variants ──
    voice_pairs_en = {'t': 'd', 'd': 't', 's': 'z', 'z': 's', 'f': 'v', 'v': 'f',
                      'p': 'b', 'b': 'p', 'k': 'g', 'g': 'k'}
    voice_pairs_ru = {'т': 'д', 'д': 'т', 'с': 'з', 'з': 'с', 'ф': 'в', 'в': 'ф',
                      'п': 'б', 'б': 'п', 'к': 'г', 'г': 'к'}
    voice_pairs = voice_pairs_en if lang == 'en' else voice_pairs_ru

    root_can_produce_extended: Dict[int, Dict[str, str]] = {}
    # Maps: root_index → {downstream_char: shift_label}
    for i in range(len(root_letters)):
        extended = {}
        for out in root_can_produce.get(i, set()):
            extended[out] = root_sid[i]
            # Add voiced/devoiced variant
            if out in voice_pairs:
                extended[voice_pairs[out]] = root_sid[i] + '+OP_VOICE'
        root_can_produce_extended[i] = extended

    # ── ALIGNMENT: find best mapping of root letters onto ds consonants ──
    # State: (ri, di) → best result
    # ri = next root letter to map, di = next ds consonant to consider
    # Root letters are consumed in order. DS consonants can be skipped (as corridor artifacts).

    n_root = len(root_letters)
    n_ds = len(ds_consonants)

    # memo[ri][di] = (max_mapped, mappings, drops, ops, extras)
    # We use backtracking with memoization-like pruning

    best_result = None
    best_mapped = -1

    def try_align(ri: int, di: int, mappings: List, drops: List,
                  ops: Set, extras: List, depth: int = 0):
        nonlocal best_result, best_mapped

        # Pruning: can't beat best even if all remaining root letters map
        remaining_possible = n_root - ri
        if len(mappings) + remaining_possible <= best_mapped:
            return
        # Depth limit to prevent combinatorial explosion
        if depth > n_root + n_ds + 10:
            return

        # Base case: all root letters consumed (mapped or dropped)
        if ri >= n_root:
            # Remaining DS consonants are extras (suffix/corridor material)
            final_extras = list(extras)
            final_ops = set(ops)
            for j in range(di, n_ds):
                dc = ds_consonants[j]
                # Classify the extra
                if dc in ('n', 'н') and 'OP_NASAL' not in final_ops:
                    final_ops.add('OP_NASAL')
                    final_extras.append({'ds': dc, 'pos': j, 'op': 'OP_NASAL'})
                elif dc in ('t', 'd', 'т', 'д') and j >= n_ds - 2:
                    final_ops.add('OP_TAMARBUTA')
                    final_extras.append({'ds': dc, 'pos': j, 'op': 'OP_TAMARBUTA'})
                else:
                    final_ops.add('OP_SUFFIX')
                    final_extras.append({'ds': dc, 'pos': j, 'op': 'OP_SUFFIX'})

            mapped_count = len(mappings)
            if mapped_count > best_mapped:
                best_mapped = mapped_count
                best_result = (list(mappings), list(drops), set(final_ops),
                               list(final_extras))
            return

        # If no more DS consonants but root letters remain → can only drop
        if di >= n_ds:
            can_resolve = False
            if root_can_drop.get(ri, False):
                drops.append({'ar': root_letters[ri], 'reason': f'{root_sid[ri]}: can_drop'})
                try_align(ri + 1, di, mappings, drops, ops, extras, depth + 1)
                drops.pop()
                can_resolve = True
            # Gemination: second of two identical root letters can simplify
            if (ri > 0 and
                strip_diacritics(root_letters[ri]) == strip_diacritics(root_letters[ri - 1])):
                drops.append({
                    'ar': root_letters[ri],
                    'reason': f'{root_sid[ri]}: gemination simplified'
                })
                try_align(ri + 1, di, mappings, drops, ops, extras, depth + 1)
                drops.pop()
                can_resolve = True
            return

        ds_c = ds_consonants[di]

        # Option A: Map root[ri] → ds[di] (direct shift or with OP_VOICE)
        extended = root_can_produce_extended.get(ri, {})
        if ds_c in extended:
            sid_label = extended[ds_c]
            use_voice = '+OP_VOICE' in sid_label
            mappings.append({
                'ar': root_letters[ri], 'ds': ds_c,
                'sid': sid_label, 'ri': ri, 'di': di
            })
            if use_voice:
                ops.add('OP_VOICE')
            try_align(ri + 1, di + 1, mappings, drops, ops, extras, depth + 1)
            if use_voice:
                ops.discard('OP_VOICE')
            mappings.pop()

        # Option B: OP_STOP — geminated root (ri, ri+1 same letter) → NN→ND
        if (ri + 1 < n_root and di + 1 < n_ds and
            strip_diacritics(root_letters[ri]) == strip_diacritics(root_letters[ri + 1])):
            if ds_c in root_can_produce_extended.get(ri, {}):
                next_ds = ds_consonants[di + 1]
                stop_pairs = {'n': 'd', 'm': 'b', 'н': 'д', 'м': 'б'}
                if ds_c in stop_pairs and next_ds == stop_pairs[ds_c]:
                    mappings.append({
                        'ar': root_letters[ri], 'ds': ds_c,
                        'sid': root_sid[ri], 'ri': ri, 'di': di
                    })
                    mappings.append({
                        'ar': root_letters[ri+1], 'ds': next_ds,
                        'sid': 'OP_STOP', 'ri': ri+1, 'di': di+1
                    })
                    ops.add('OP_STOP')
                    try_align(ri + 2, di + 2, mappings, drops, ops, extras, depth + 1)
                    ops.discard('OP_STOP')
                    mappings.pop()
                    mappings.pop()

        # Option C: Root letter DROPS (can_drop=True) — skip root, keep DS position
        if root_can_drop.get(ri, False):
            drops.append({'ar': root_letters[ri], 'reason': f'{root_sid[ri]}: can_drop'})
            try_align(ri + 1, di, mappings, drops, ops, extras, depth + 1)
            drops.pop()

        # Option C2: Geminated root letter simplifies — second of two identical
        # root letters absorbs into the first (standard gemination reduction)
        if (ri > 0 and
            strip_diacritics(root_letters[ri]) == strip_diacritics(root_letters[ri - 1])):
            drops.append({
                'ar': root_letters[ri],
                'reason': f'{root_sid[ri]}: gemination simplified'
            })
            try_align(ri + 1, di, mappings, drops, ops, extras, depth + 1)
            drops.pop()

        # Option D: Skip DS consonant as corridor artifact (epenthetic/prefix/suffix)
        # Classify the skip
        if di == 0 or (di < 3 and ri == 0):
            # Leading consonant — could be OP_PREFIX
            extras.append({'ds': ds_c, 'pos': di, 'op': 'OP_PREFIX'})
            ops.add('OP_PREFIX')
            try_align(ri, di + 1, mappings, drops, ops, extras, depth + 1)
            ops.discard('OP_PREFIX')
            extras.pop()
        elif ds_c in ('n', 'н'):
            # Nasal insertion
            extras.append({'ds': ds_c, 'pos': di, 'op': 'OP_NASAL'})
            ops.add('OP_NASAL')
            try_align(ri, di + 1, mappings, drops, ops, extras, depth + 1)
            ops.discard('OP_NASAL')
            extras.pop()
        else:
            # General corridor artifact (epenthetic consonant)
            extras.append({'ds': ds_c, 'pos': di, 'op': 'CORRIDOR'})
            try_align(ri, di + 1, mappings, drops, ops, extras, depth + 1)
            extras.pop()

    # Run alignment
    try_align(0, 0, [], [], set(), [])

    result.ds_consonants = ds_consonants
    result.root_letters_used = root_letters

    # ── METATHESIS FALLBACK ──
    # If ordered alignment failed, try permutations of root letters (R02 rule)
    if not best_result or best_mapped <= 0:
        from itertools import permutations
        best_perm_result = None
        best_perm_score = -1
        best_perm_order = None

        for perm in permutations(range(n_root)):
            perm_letters = [root_letters[i] for i in perm]
            if perm_letters == root_letters:
                continue  # already tried

            # Rebuild root data for permuted order
            perm_can_produce = {i: root_can_produce[perm[i]] for i in range(n_root)}
            perm_can_drop = {i: root_can_drop[perm[i]] for i in range(n_root)}
            perm_sid = {i: root_sid[perm[i]] for i in range(n_root)}

            # Rebuild extended map
            perm_extended = {}
            for i in range(n_root):
                ext = {}
                for out in perm_can_produce.get(i, set()):
                    ext[out] = perm_sid[i]
                    if out in voice_pairs:
                        ext[voice_pairs[out]] = perm_sid[i] + '+OP_VOICE'
                perm_extended[i] = ext

            # Override for this permutation
            saved = (root_can_produce_extended, root_can_drop)
            root_can_produce_extended_local = perm_extended
            root_can_drop_local = perm_can_drop

            # Quick alignment check (simplified — just try ordered match)
            ri, di = 0, 0
            perm_mappings = []
            while ri < n_root and di < n_ds:
                ds_c = ds_consonants[di]
                ext = perm_extended.get(ri, {})
                if ds_c in ext:
                    perm_mappings.append({
                        'ar': perm_letters[ri], 'ds': ds_c,
                        'sid': ext[ds_c], 'ri': ri, 'di': di
                    })
                    ri += 1
                    di += 1
                elif perm_can_drop.get(ri, False):
                    ri += 1
                else:
                    di += 1  # skip DS consonant

            # Also try dropping remaining root letters
            while ri < n_root:
                if perm_can_drop.get(ri, False):
                    ri += 1
                elif (ri > 0 and strip_diacritics(perm_letters[ri]) ==
                      strip_diacritics(perm_letters[ri-1])):
                    ri += 1  # gemination
                else:
                    break

            if len(perm_mappings) > best_perm_score and ri >= n_root:
                best_perm_score = len(perm_mappings)
                best_perm_result = perm_mappings
                best_perm_order = perm_letters

        if best_perm_result and best_perm_score > best_mapped:
            # Metathesis alignment is better
            best_result = (best_perm_result, [], {'METATHESIS'}, [])
            best_mapped = best_perm_score
            result.warnings.append(
                f"METATHESIS detected: root reordered as "
                f"{'-'.join(best_perm_order)} (R02 rule)"
            )

    if best_result:
        mappings, drops, ops, extras = best_result
        result.mappings = mappings
        result.dropped = drops
        result.operations = sorted(ops)

        # ── Determine pass/fail with confidence levels ──

        # Root accountability
        root_mapped = set(m['ri'] for m in mappings)
        root_dropped = set()
        for d in drops:
            for i, rl in enumerate(root_letters):
                if rl == d['ar'] and i not in root_mapped and i not in root_dropped:
                    root_dropped.add(i)
                    break
        all_root_accounted = len(root_mapped) + len(root_dropped) >= n_root

        # Coverage ratio: how many DS consonants are directly explained by root?
        n_mapped = len(mappings)
        coverage = n_mapped / n_ds if n_ds > 0 else 0
        result.coverage_ratio = coverage

        # Classify extras
        explained_extras = [e for e in extras if e.get('op') != 'CORRIDOR']
        corridor_extras = [e for e in extras if e.get('op') == 'CORRIDOR']
        n_extras = len(explained_extras) + len(corridor_extras)

        result.extras = explained_extras + corridor_extras

        # ── Mid-word corridor check ──
        # Corridor artifacts in the middle of the word (not first/last 2 positions)
        # are much more suspicious than edge artifacts
        mid_corridor = [e for e in corridor_extras
                        if 2 <= e['pos'] < n_ds - 2]

        # ── CONFIDENCE LEVELS ──
        if not all_root_accounted:
            result.confidence = 'FAIL'
            result.passed = False
        elif coverage >= 0.75 and len(corridor_extras) == 0:
            result.confidence = 'HIGH'
            result.passed = True
        elif coverage >= 0.60 and len(corridor_extras) <= 1 and len(mid_corridor) == 0:
            result.confidence = 'MEDIUM'
            result.passed = True
        elif coverage >= 0.50 and len(corridor_extras) <= 2 and len(mid_corridor) <= 1:
            result.confidence = 'LOW'
            result.passed = True
            result.warnings.append(
                f"LOW confidence: coverage {coverage:.0%}, "
                f"{len(corridor_extras)} corridor artifact(s)"
            )
        else:
            result.confidence = 'FAIL'
            result.passed = False
            result.unmapped = corridor_extras
            if not all_root_accounted:
                result.warnings.append("Not all root letters accounted for")
            if coverage < 0.50:
                result.warnings.append(f"Coverage too low: {coverage:.0%} (<50%)")
            if len(mid_corridor) > 1:
                result.warnings.append(
                    f"Multiple mid-word corridor artifacts: suspicious"
                )
    else:
        result.unmapped = [{'ds': c, 'pos': i} for i, c in enumerate(ds_consonants)]
        result.passed = False
        result.confidence = 'FAIL'
        result.warnings.append("No valid alignment found between root and downstream consonants")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# U-GATE: UNIVERSALITY CHECK
# ═══════════════════════════════════════════════════════════════════════════════

class UGateResult:
    def __init__(self):
        self.passed = False
        self.shift_usage: Dict[str, int] = {}   # sid → count of entries using it
        self.novel_shifts: List[str] = []        # shifts with 0 precedent
        self.total_precedent: int = 0

    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        lines = [f"U-GATE: {status}"]
        for sid, count in sorted(self.shift_usage.items()):
            marker = "✓" if count > 0 else "✗ NOVEL"
            lines.append(f"  {sid}: {count} prior entries {marker}")
        if self.novel_shifts:
            lines.append(f"  ⚠ Novel shifts with no precedent: {', '.join(self.novel_shifts)}")
        return '\n'.join(lines)


def validate_u_gate(q_result: QGateResult, lang: str = 'en') -> UGateResult:
    """Check if every shift used has precedent in the DB."""
    result = UGateResult()

    if not q_result.passed:
        result.passed = False
        return result

    # Collect all shift IDs used
    sids_used = set()
    for m in q_result.mappings:
        sid = m['sid'].split('+')[0]  # strip OP_VOICE suffix
        if sid.startswith('S'):
            sids_used.add(sid)

    # Query DB for usage counts
    conn = sqlite3.connect(DB_PATH)
    table = 'a1_entries' if lang == 'en' else 'a1_записи'
    chain_col = 'phonetic_chain' if lang == 'en' else 'фонетическая_цепь'

    for sid in sorted(sids_used):
        try:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM \"{table}\" WHERE \"{chain_col}\" LIKE ?",
                (f'%{sid}%',)
            )
            count = cursor.fetchone()[0]
        except Exception:
            count = 0
        result.shift_usage[sid] = count
        result.total_precedent += count
        if count == 0:
            result.novel_shifts.append(sid)

    conn.close()

    result.passed = len(result.novel_shifts) == 0
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# F-GATE: COMPETING ROOT FINDER
# ═══════════════════════════════════════════════════════════════════════════════

class FGateResult:
    def __init__(self):
        self.passed = False
        self.competing_roots: List[Dict] = []  # other roots that could produce same pattern
        self.unique = True

    def __str__(self):
        status = "✓ PASS" if self.passed else "⚠ COMPETING ROOTS"
        lines = [f"F-GATE: {status}"]
        if self.competing_roots:
            for cr in self.competing_roots[:5]:  # show top 5
                conf = cr.get('confidence', '?')
                cov = cr.get('coverage', 0)
                lines.append(f"  Competing: {cr['root_id']} ({cr['root_letters']}) — "
                             f"{cr['term']} [score={cr['score']}, conf={conf}, cov={cov:.0%}]")
            if len(self.competing_roots) > 5:
                lines.append(f"  ... and {len(self.competing_roots) - 5} more")
        else:
            lines.append("  No competing roots found — chain is unique")
        return '\n'.join(lines)


def validate_f_gate(root_letters: List[str], downstream_word: str,
                     current_root_id: str = '', lang: str = 'en') -> FGateResult:
    """
    Find competing roots: other AA roots that could also produce the same
    downstream consonant pattern via S01–S26.
    """
    result = FGateResult()

    shift_table = SHIFT_TABLE_EN if lang == 'en' else SHIFT_TABLE_RU
    reverse_map = REVERSE_EN if lang == 'en' else REVERSE_RU

    # Get downstream consonants
    if lang == 'en':
        ds_consonants = extract_consonants_en(downstream_word)
    else:
        ds_consonants = extract_consonants_ru(downstream_word)

    if not ds_consonants:
        result.passed = True
        return result

    # For each downstream consonant, find which Arabic letters could produce it
    possible_sources: List[Set[str]] = []
    for dc in ds_consonants:
        sources = set()
        if dc in reverse_map:
            for ar, sid in reverse_map[dc]:
                sources.add(strip_diacritics(ar))
        possible_sources.append(sources)

    # Query DB for all roots
    conn = sqlite3.connect(DB_PATH)
    table = 'a1_entries' if lang == 'en' else 'a1_записи'

    if lang == 'en':
        cursor = conn.execute(
            f"SELECT entry_id, en_term, root_id, root_letters, score FROM \"{table}\""
        )
    else:
        cursor = conn.execute(
            f"SELECT запись_id, рус_термин, корень_id, корневые_буквы, балл FROM \"{table}\""
        )

    competing = []
    for row in cursor.fetchall():
        rid = row[2] if row[2] else ''
        if rid == current_root_id:
            continue  # skip self
        rl_str = row[3] if row[3] else ''
        rl = parse_root_letters(rl_str)
        if not rl:
            continue

        # Quick check: could this root's letters appear in the possible sources?
        # This is a heuristic — not a full alignment
        rl_set = set(strip_diacritics(l) for l in rl)
        all_possible = set()
        for ps in possible_sources:
            all_possible.update(ps)

        overlap = rl_set.intersection(all_possible)
        if len(overlap) >= min(len(rl), 2):  # at least 2 letters could match
            # Run a quick Q-gate to see if it's actually viable
            q_test = validate_q_gate(rl, downstream_word, lang)
            # Only count as competing if MEDIUM+ confidence
            if q_test.passed and q_test.confidence in ('HIGH', 'MEDIUM'):
                competing.append({
                    'root_id': rid,
                    'root_letters': rl_str,
                    'term': row[1],
                    'score': row[4],
                    'entry_id': row[0],
                    'confidence': q_test.confidence,
                    'coverage': q_test.coverage_ratio,
                })

    conn.close()

    result.competing_roots = competing
    result.unique = len(competing) == 0
    # F-gate passes if unique OR if competing roots are lower-scored
    result.passed = result.unique
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED QUF VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class QUFResult:
    def __init__(self):
        self.q_gate: Optional[QGateResult] = None
        self.u_gate: Optional[UGateResult] = None
        self.f_gate: Optional[FGateResult] = None
        self.overall_pass = False
        self.entry_info: Dict = {}

    def __str__(self):
        lines = ["═" * 60]
        if self.entry_info:
            ei = self.entry_info
            lines.append(f"QUF VALIDATION: {ei.get('term', '?')} "
                         f"({ei.get('root_id', '?')}: {ei.get('root_letters', '?')})")
            if ei.get('score'):
                lines.append(f"Current score: {ei['score']}/10")
        lines.append("═" * 60)

        if self.q_gate:
            lines.append(str(self.q_gate))
        if self.u_gate:
            lines.append(str(self.u_gate))
        if self.f_gate:
            lines.append(str(self.f_gate))

        lines.append("─" * 60)
        all_pass = "✓ QUF PASS" if self.overall_pass else "✗ QUF FAIL"
        lines.append(f"OVERALL: {all_pass}")

        # Score cap advisory
        if self.q_gate and not self.q_gate.passed:
            lines.append("  SCORE CAP: 4 (unexplained consonant — criterion 7 fails)")
        elif self.f_gate and not self.f_gate.passed:
            lines.append("  SCORE CAP: 6 (competing root exists — criterion 6 fails)")

        lines.append("═" * 60)
        return '\n'.join(lines)


def validate_entry(root_id: str = '', root_letters_str: str = '',
                    downstream_word: str = '', lang: str = 'en',
                    entry_id: int = 0, score: int = 0) -> QUFResult:
    """Run full QUF validation on a single entry."""
    quf = QUFResult()
    quf.entry_info = {
        'term': downstream_word,
        'root_id': root_id,
        'root_letters': root_letters_str,
        'score': score,
        'entry_id': entry_id,
    }

    root_letters = parse_root_letters(root_letters_str)

    # Q-Gate
    quf.q_gate = validate_q_gate(root_letters, downstream_word, lang)

    # U-Gate (only if Q passes)
    if quf.q_gate.passed:
        quf.u_gate = validate_u_gate(quf.q_gate, lang)
    else:
        quf.u_gate = UGateResult()
        quf.u_gate.passed = False

    # F-Gate
    quf.f_gate = validate_f_gate(root_letters, downstream_word, root_id, lang)

    # Overall
    quf.overall_pass = (quf.q_gate.passed and quf.u_gate.passed)
    # F-gate is advisory — competing roots don't block, but flag

    return quf


# ═══════════════════════════════════════════════════════════════════════════════
# DB LOOKUP HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = str
    return conn


def lookup_root(root_id: str) -> Optional[Dict]:
    """Look up a root across all sibling tables."""
    conn = get_connection()
    tables = [
        ('a1_entries', 'entry_id', 'en_term', 'root_id', 'root_letters',
         'phonetic_chain', 'score', 'en'),
        ('a1_записи', 'запись_id', 'рус_термин', 'корень_id', 'корневые_буквы',
         'фонетическая_цепь', 'балл', 'ru'),
    ]
    results = []
    for table, id_col, term_col, rid_col, rl_col, chain_col, score_col, lang in tables:
        try:
            cursor = conn.execute(
                f'SELECT "{id_col}", "{term_col}", "{rid_col}", "{rl_col}", '
                f'"{chain_col}", "{score_col}" FROM "{table}" WHERE "{rid_col}" = ?',
                (root_id,)
            )
            for row in cursor.fetchall():
                results.append({
                    'entry_id': row[0], 'term': row[1], 'root_id': row[2],
                    'root_letters': row[3], 'phonetic_chain': row[4],
                    'score': row[5], 'lang': lang, 'table': table,
                })
        except Exception:
            pass
    conn.close()
    return results if results else None


def lookup_entry_by_id(entry_id: int, lang: str = 'en') -> Optional[Dict]:
    """Look up entry by ID."""
    conn = get_connection()
    if lang == 'en':
        cursor = conn.execute(
            "SELECT entry_id, en_term, root_id, root_letters, phonetic_chain, score "
            "FROM a1_entries WHERE entry_id = ?", (entry_id,)
        )
    else:
        cursor = conn.execute(
            'SELECT запись_id, рус_термин, корень_id, корневые_буквы, '
            'фонетическая_цепь, балл FROM "a1_записи" WHERE запись_id = ?',
            (entry_id,)
        )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'entry_id': row[0], 'term': row[1], 'root_id': row[2],
            'root_letters': row[3], 'phonetic_chain': row[4], 'score': row[5],
            'lang': lang,
        }
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH MODE
# ═══════════════════════════════════════════════════════════════════════════════

def batch_validate(lang: str = 'en', show_all: bool = False):
    """Validate all entries in a sibling DB. Show failures and warnings."""
    conn = get_connection()

    if lang == 'en':
        cursor = conn.execute(
            "SELECT entry_id, en_term, root_id, root_letters, phonetic_chain, score "
            "FROM a1_entries ORDER BY entry_id"
        )
    elif lang == 'ru':
        cursor = conn.execute(
            'SELECT запись_id, рус_термин, корень_id, корневые_буквы, '
            'фонетическая_цепь, балл FROM "a1_записи" ORDER BY запись_id'
        )
    else:
        print(f"Language '{lang}' not yet supported for batch mode")
        return

    rows = cursor.fetchall()
    conn.close()

    total = len(rows)
    passed = 0
    failed = 0
    warnings = 0
    failures = []

    print(f"\n{'═' * 60}")
    print(f"BATCH QUF VALIDATION — {lang.upper()} ({total} entries)")
    print(f"{'═' * 60}\n")

    skipped_orig2 = 0
    for row in rows:
        eid, term, rid, rl, chain, score = row
        if not rl or not term:
            continue

        # Skip Turkic/ORIG2 entries (they use Bitig phonology, not S01-S26)
        if rid and rid.startswith('T'):
            skipped_orig2 += 1
            continue
        if is_orig2_root(rl):
            skipped_orig2 += 1
            continue

        root_letters = parse_root_letters(rl)
        q_result = validate_q_gate(root_letters, term, lang)

        if q_result.passed:
            passed += 1
            if show_all:
                print(f"  ✓ #{eid} {term} ({rid}) [{q_result.confidence}]")
        else:
            failed += 1
            failures.append({
                'entry_id': eid, 'term': term, 'root_id': rid,
                'root_letters': rl, 'score': score,
                'unmapped': q_result.unmapped,
                'warnings': q_result.warnings,
                'confidence': q_result.confidence,
                'coverage': q_result.coverage_ratio,
            })

    # Report
    validated = passed + failed
    print(f"\n{'─' * 60}")
    print(f"RESULTS: {passed}/{validated} PASS ({passed/validated*100:.1f}%), "
          f"{failed} FAIL")
    if skipped_orig2:
        print(f"SKIPPED: {skipped_orig2} ORIG2/Bitig entries (not validated by S01–S26)")
    print(f"{'─' * 60}\n")

    if failures:
        print("FAILURES (Q-gate):\n")
        for f in failures[:30]:  # limit output
            unmapped_str = ', '.join(
                f"'{u['ds']}' @{u['pos']}" for u in f['unmapped']
            ) if f['unmapped'] else 'alignment failure'
            warn_str = '; '.join(f['warnings']) if f['warnings'] else ''
            cov = f.get('coverage', 0)
            print(f"  ✗ #{f['entry_id']} {f['term']} ({f['root_id']}: {f['root_letters']}) "
                  f"score={f['score']} cov={cov:.0%}")
            print(f"    {unmapped_str}")
            if warn_str:
                print(f"    {warn_str}")
            print()
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more failures")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETE MODE — find all roots that could produce a given word
# ═══════════════════════════════════════════════════════════════════════════════

def compete_search(downstream_word: str, lang: str = 'en'):
    """Find all roots in the DB that could produce the given downstream word."""
    shift_table = SHIFT_TABLE_EN if lang == 'en' else SHIFT_TABLE_RU
    reverse_map = REVERSE_EN if lang == 'en' else REVERSE_RU

    if lang == 'en':
        ds_consonants = extract_consonants_en(downstream_word)
    else:
        ds_consonants = extract_consonants_ru(downstream_word)

    print(f"\n{'═' * 60}")
    print(f"COMPETING ROOT SEARCH: {downstream_word}")
    print(f"Consonant skeleton: {'-'.join(ds_consonants)}")
    print(f"{'═' * 60}\n")

    # For each consonant, show possible Arabic sources
    print("Possible Arabic sources per consonant:")
    for i, dc in enumerate(ds_consonants):
        sources = reverse_map.get(dc, [])
        src_str = ', '.join(f"{ar}({sid})" for ar, sid in sources)
        print(f"  [{i}] {dc} ← {src_str}")
    print()

    # Query all unique roots
    conn = get_connection()
    if lang == 'en':
        cursor = conn.execute(
            "SELECT DISTINCT root_id, root_letters FROM a1_entries WHERE root_id IS NOT NULL"
        )
    else:
        cursor = conn.execute(
            'SELECT DISTINCT корень_id, корневые_буквы FROM "a1_записи" WHERE корень_id IS NOT NULL'
        )

    viable = []
    for row in cursor.fetchall():
        rid, rl_str = row
        if not rl_str or not rid:
            continue
        if rid.startswith('T'):
            continue
        rl = parse_root_letters(rl_str)
        if not rl:
            continue

        q_test = validate_q_gate(rl, downstream_word, lang)
        if q_test.passed:
            viable.append({
                'root_id': rid,
                'root_letters': rl_str,
                'chain': ', '.join(f"{m['ar']}→{m['ds']}({m['sid']})" for m in q_test.mappings),
                'ops': q_test.operations,
            })

    conn.close()

    if viable:
        print(f"VIABLE ROOTS ({len(viable)}):\n")
        for v in viable:
            ops_str = f" [{', '.join(v['ops'])}]" if v['ops'] else ""
            print(f"  {v['root_id']} ({v['root_letters']}): {v['chain']}{ops_str}")
    else:
        print("  No viable roots found in the database.")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# STATS MODE — shift usage across the lattice
# ═══════════════════════════════════════════════════════════════════════════════

def shift_stats():
    """Show shift usage statistics across EN and RU databases."""
    conn = get_connection()

    print(f"\n{'═' * 60}")
    print("SHIFT TABLE USAGE STATISTICS")
    print(f"{'═' * 60}\n")

    for lang, table, chain_col in [
        ('EN', 'a1_entries', 'phonetic_chain'),
        ('RU', 'a1_записи', 'фонетическая_цепь'),
    ]:
        print(f"\n{lang} Database:\n")
        print(f"  {'S_ID':<6} {'Letter':<4} {'Name':<10} {'Count':<8} {'Bar'}")
        print(f"  {'─'*6} {'─'*4} {'─'*10} {'─'*8} {'─'*30}")

        for sid_num in range(1, 27):
            sid = f"S{sid_num:02d}"
            try:
                cursor = conn.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE "{chain_col}" LIKE ?',
                    (f'%{sid}%',)
                )
                count = cursor.fetchone()[0]
            except Exception:
                count = 0

            # Find the letter for this SID
            letter = '?'
            name = '?'
            st = SHIFT_TABLE_EN
            for ar, info in st.items():
                if info['sid'] == sid and len(ar) == 1:
                    letter = ar
                    name = info['name']
                    break

            bar = '█' * min(count // 3, 30)
            print(f"  {sid:<6} {letter:<4} {name:<10} {count:<8} {bar}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT MODE — find entries with potential chain problems
# ═══════════════════════════════════════════════════════════════════════════════

def audit_entries(lang: str = 'en'):
    """Audit entries for chain problems: missing chains, score mismatches, etc."""
    conn = get_connection()

    if lang == 'en':
        cursor = conn.execute(
            "SELECT entry_id, en_term, root_id, root_letters, phonetic_chain, score "
            "FROM a1_entries ORDER BY entry_id"
        )
    else:
        cursor = conn.execute(
            'SELECT запись_id, рус_термин, корень_id, корневые_буквы, '
            'фонетическая_цепь, балл FROM "a1_записи" ORDER BY запись_id'
        )

    rows = cursor.fetchall()
    conn.close()

    print(f"\n{'═' * 60}")
    print(f"AUDIT — {lang.upper()} ({len(rows)} entries)")
    print(f"{'═' * 60}\n")

    issues = {
        'no_chain': [],
        'no_root': [],
        'score_10_but_q_fail': [],
        'score_low_but_q_pass': [],
        'missing_sid_refs': [],
    }

    for row in rows:
        eid, term, rid, rl, chain, score = row

        # No phonetic chain
        if not chain or chain.strip() == '':
            issues['no_chain'].append((eid, term, score))
            continue

        # No root letters
        if not rl or rl.strip() == '':
            issues['no_root'].append((eid, term, score))
            continue

        # Skip Turkic
        if rid and rid.startswith('T'):
            continue

        # Check if chain references S-IDs
        has_sid = bool(re.search(r'S\d{2}', chain))
        if not has_sid:
            issues['missing_sid_refs'].append((eid, term, score, chain[:60]))

        # Run Q-gate
        root_letters = parse_root_letters(rl)
        q_result = validate_q_gate(root_letters, term, lang)

        if score == 10 and not q_result.passed:
            issues['score_10_but_q_fail'].append((eid, term, rid, rl))
        elif score and score < 8 and q_result.passed:
            issues['score_low_but_q_pass'].append((eid, term, rid, rl, score))

    # Report
    for category, label in [
        ('no_chain', 'MISSING PHONETIC CHAIN'),
        ('no_root', 'MISSING ROOT LETTERS'),
        ('missing_sid_refs', 'CHAIN WITHOUT S-ID REFERENCES'),
        ('score_10_but_q_fail', 'SCORE 10 BUT Q-GATE FAILS (investigate)'),
        ('score_low_but_q_pass', 'LOW SCORE BUT Q-GATE PASSES (may deserve upgrade)'),
    ]:
        items = issues[category]
        if items:
            print(f"\n{label} ({len(items)}):")
            for item in items[:20]:
                print(f"  #{item[0]} {item[1]} " + ' '.join(str(x) for x in item[2:]))
            if len(items) > 20:
                print(f"  ... and {len(items) - 20} more")

    total_issues = sum(len(v) for v in issues.values())
    print(f"\n{'─' * 60}")
    print(f"Total issues found: {total_issues}")
    print(f"{'═' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def print_usage():
    print("""
USLaP QUF Validator — al-Alaq Extension
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Usage:
  python3 uslap_quf.py validate ROOT_ID WORD [--lang en|ru]
      Validate a single entry against QUF gates.
      Example: python3 uslap_quf.py validate R168 COFFEE

  python3 uslap_quf.py validate --id ENTRY_ID [--lang en|ru]
      Validate an existing entry by its ID.
      Example: python3 uslap_quf.py validate --id 221

  python3 uslap_quf.py batch [en|ru|all]
      Validate all entries in a sibling database.
      Example: python3 uslap_quf.py batch en

  python3 uslap_quf.py compete WORD [--lang en|ru]
      Find all competing roots that could produce WORD.
      Example: python3 uslap_quf.py compete MARTYR

  python3 uslap_quf.py stats
      Show shift usage statistics across the lattice.

  python3 uslap_quf.py audit [en|ru]
      Audit entries for chain problems, score mismatches, etc.
""")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help', 'help'):
        print_usage()
        return

    cmd = args[0].lower()

    # Parse --lang flag
    lang = 'en'
    if '--lang' in args:
        idx = args.index('--lang')
        if idx + 1 < len(args):
            lang = args[idx + 1].lower()

    if cmd == 'validate':
        if '--id' in args:
            idx = args.index('--id')
            if idx + 1 < len(args):
                eid = int(args[idx + 1])
                entry = lookup_entry_by_id(eid, lang)
                if entry:
                    result = validate_entry(
                        root_id=entry['root_id'],
                        root_letters_str=entry['root_letters'],
                        downstream_word=entry['term'],
                        lang=lang,
                        entry_id=entry['entry_id'],
                        score=entry['score'],
                    )
                    print(result)
                else:
                    print(f"Entry #{eid} not found in {lang} database")
            else:
                print("Missing entry ID after --id")
        elif len(args) >= 3:
            root_id = args[1]
            word = args[2]

            # Look up root in DB to get root_letters
            entries = lookup_root(root_id)
            if entries:
                rl_str = entries[0]['root_letters']
                result = validate_entry(
                    root_id=root_id,
                    root_letters_str=rl_str,
                    downstream_word=word,
                    lang=lang,
                )
                print(result)
            else:
                # Try treating arg1 as root_letters directly (e.g., "ق-ه-ر")
                result = validate_entry(
                    root_id='(manual)',
                    root_letters_str=root_id,
                    downstream_word=word,
                    lang=lang,
                )
                print(result)
        else:
            print("Usage: validate ROOT_ID WORD or validate --id ENTRY_ID")

    elif cmd == 'batch':
        target = args[1].lower() if len(args) > 1 else 'en'
        show_all = '--all' in args
        if target == 'all':
            batch_validate('en', show_all)
            batch_validate('ru', show_all)
        else:
            batch_validate(target, show_all)

    elif cmd == 'compete':
        if len(args) >= 2:
            word = args[1]
            compete_search(word, lang)
        else:
            print("Usage: compete WORD [--lang en|ru]")

    elif cmd == 'stats':
        shift_stats()

    elif cmd == 'audit':
        target = args[1].lower() if len(args) > 1 else 'en'
        if target == 'all':
            audit_entries('en')
            audit_entries('ru')
        else:
            audit_entries(target)

    else:
        print(f"Unknown command: {cmd}")
        print_usage()


if __name__ == '__main__':
    main()
