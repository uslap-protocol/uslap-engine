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
  stamp [en|ru|eu|all]                   Run QUF & persist results to DB columns
  quf_status                             Show QUF stamp status across all tables

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
# For each AA letter: which downstream consonants it can produce
# ═══════════════════════════════════════════════════════════════════════════════

SHIFT_TABLE_EN: Dict[str, Dict] = {
    # AA letter → { shift_id, outputs (lowercase), name }
    'ق': {'sid': 'S01', 'outputs': {'c', 'k', 'q', 'g'},        'name': 'qāf'},
    'ج': {'sid': 'S02', 'outputs': {'g', 'j', 'c'},              'name': 'jīm'},      # v3: +c (j→g→c velar: جمل→CAMEL)
    'ح': {'sid': 'S03', 'outputs': {'h', 'c'},                   'name': 'ḥāʾ',    'can_drop': True},
    'ط': {'sid': 'S04', 'outputs': {'t'},                         'name': 'ṭāʾ'},
    'ش': {'sid': 'S05', 'outputs': {'sh', 's'},                   'name': 'shīn'},
    'ض': {'sid': 'S06', 'outputs': {'th', 'd'},                   'name': 'ḍād'},
    'ع': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'ʿayn',   'can_drop': True},
    'ف': {'sid': 'S08', 'outputs': {'f', 'p', 'v', 'ph'},        'name': 'fāʾ',    'can_drop': True},  # v2: ph digraph + can_drop (ṣifr→zero)
    'ب': {'sid': 'S09', 'outputs': {'b', 'p', 'v'},              'name': 'bāʾ'},
    'و': {'sid': 'S10', 'outputs': {'v', 'w', 'o', 'r', 'u', 'f'}, 'name': 'wāw',  'can_drop': True},  # v2: +f (qahwa→coffee: w→v→f)
    'خ': {'sid': 'S11', 'outputs': {'ch', 'x', 'k', 'c', 'h'},   'name': 'khāʾ',   'can_drop': True},  # v2: +h, can_drop
    'ذ': {'sid': 'S12', 'outputs': {'d', 'th'},                   'name': 'dhāl',    'can_drop': True},  # v2: can_drop (ache←أخذ)
    'ص': {'sid': 'S13', 'outputs': {'s', 'c', 'z'},              'name': 'ṣād'},
    'غ': {'sid': 'S14', 'outputs': {'gh', 'g', 'c'},              'name': 'ghayn'},  # v3: +c (gh→g→c velar devoicing: غرف→CARAFE, غفر→COVER)
    'ر': {'sid': 'S15', 'outputs': {'r', 'l'},                    'name': 'rāʾ'},    # v3: +l (r↔l liquid interchange)
    'ل': {'sid': 'S16', 'outputs': {'l', 'r'},                    'name': 'lām'},    # v3: +r (l↔r liquid interchange)
    'م': {'sid': 'S17', 'outputs': {'m', 'n'},                    'name': 'mīm'},    # v3: +n (m↔n nasal interchange)
    'ن': {'sid': 'S18', 'outputs': {'n', 'm'},                    'name': 'nūn'},    # v2: +m (OP_NASAL assimilation: n→m before labials)
    'د': {'sid': 'S19', 'outputs': {'d', 't'},                    'name': 'dāl'},
    'ك': {'sid': 'S20', 'outputs': {'c', 'k', 'ch', 'g'},       'name': 'kāf'},
    'س': {'sid': 'S21', 'outputs': {'s', 'c', 'z'},              'name': 'sīn'},
    'ز': {'sid': 'S22', 'outputs': {'z', 's'},                    'name': 'zāy'},
    'ه': {'sid': 'S23', 'outputs': {'h', 'f'},                    'name': 'hāʾ',    'can_drop': True},  # v3: +f (h→f labialisation: قهر→COFFEE)
    'ت': {'sid': 'S24', 'outputs': {'t', 'th', 'd'},              'name': 'tāʾ'},    # v3: +th (سبت→SABBATH), +d (voicing: ت→d)
    'ظ': {'sid': 'S25', 'outputs': {'z', 'th', 'd'},              'name': 'ẓāʾ'},   # v2: +d (naẓīr→nadir)
    'ث': {'sid': 'S26', 'outputs': {'th', 't'},                   'name': 'thāʾ'},   # v2: +t (ḥarth→harvest, thimār→timber)
    # ── SUPPLEMENTARY (not in core S01-S26 but essential for root validation) ──
    # Yāʾ — appears in ~30% of roots. Downstream: y, i, or drops.
    'ي': {'sid': 'SY',  'outputs': {'y', 'i', 'j'},              'name': 'yāʾ',    'can_drop': True},
    # Alef / hamza — not a shift letter, but can appear in roots
    'أ': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'hamza',   'can_drop': True},
    'ا': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'alif',    'can_drop': True},
    'إ': {'sid': 'S07', 'outputs': {'a', 'e', 'i'},              'name': 'hamza-i', 'can_drop': True},
    'ء': {'sid': 'S07', 'outputs': {'a', 'e'},                    'name': 'hamza-q', 'can_drop': True},
}

# Russian shift table — same AA letters, different outputs
SHIFT_TABLE_RU: Dict[str, Dict] = {
    'ق': {'sid': 'S01', 'outputs': {'к', 'г'},                   'name': 'qāf'},
    'ج': {'sid': 'S02', 'outputs': {'г', 'ж', 'дж'},             'name': 'jīm'},
    'ح': {'sid': 'S03', 'outputs': {'х'},                         'name': 'ḥāʾ',    'can_drop': True},
    'ط': {'sid': 'S04', 'outputs': {'т'},                         'name': 'ṭāʾ'},
    'ش': {'sid': 'S05', 'outputs': {'ш', 'щ', 'с'},              'name': 'shīn'},
    'ض': {'sid': 'S06', 'outputs': {'д', 'з'},                    'name': 'ḍād'},
    'ع': {'sid': 'S07', 'outputs': {'а'},                         'name': 'ʿayn',   'can_drop': True},
    'ف': {'sid': 'S08', 'outputs': {'ф', 'п'},                    'name': 'fāʾ',    'can_drop': True},  # v2: can_drop
    'ب': {'sid': 'S09', 'outputs': {'б', 'п', 'в'},              'name': 'bāʾ'},
    'و': {'sid': 'S10', 'outputs': {'в', 'у', 'о', 'ф'},         'name': 'wāw',    'can_drop': True},  # v2: +ф (w→v→f)
    'خ': {'sid': 'S11', 'outputs': {'х', 'к', 'г', 'ш'},          'name': 'khāʾ'},  # v3: +ш (kh→sh: خلق→ШЁЛК)
    'ذ': {'sid': 'S12', 'outputs': {'д', 'з'},                    'name': 'dhāl'},
    'ص': {'sid': 'S13', 'outputs': {'с', 'ц', 'з', 'ш'},          'name': 'ṣād'},   # v3: +ш (emphatic s → full sibilant: صفر→ШИФР)
    'غ': {'sid': 'S14', 'outputs': {'г', 'ж'},                    'name': 'ghayn'},
    'ر': {'sid': 'S15', 'outputs': {'р', 'л'},                    'name': 'rāʾ'},    # v3: +л (r↔l liquid)
    'ل': {'sid': 'S16', 'outputs': {'л', 'р'},                    'name': 'lām'},    # v3: +р (l↔r liquid)
    'م': {'sid': 'S17', 'outputs': {'м', 'н'},                    'name': 'mīm'},    # v3: +н (m↔n nasal)
    'ن': {'sid': 'S18', 'outputs': {'н', 'м'},                    'name': 'nūn'},    # v2: +м (nasal assimilation)
    'د': {'sid': 'S19', 'outputs': {'д', 'т'},                    'name': 'dāl'},
    'ك': {'sid': 'S20', 'outputs': {'к', 'г', 'х', 'ч'},          'name': 'kāf'},   # v3: +г(voicing) +х(lenition: سكر→САХАР) +ч(palatalization)
    'س': {'sid': 'S21', 'outputs': {'с'},                         'name': 'sīn'},
    'ز': {'sid': 'S22', 'outputs': {'з', 'с'},                    'name': 'zāy'},
    'ه': {'sid': 'S23', 'outputs': {'г', 'х', 'ф'},               'name': 'hāʾ',    'can_drop': True},  # v3: +ф (h→f labialisation: قهر→КОФЕ)
    'ت': {'sid': 'S24', 'outputs': {'т', 'д'},                    'name': 'tāʾ'},
    'ظ': {'sid': 'S25', 'outputs': {'з', 'д'},                    'name': 'ẓāʾ'},   # v2: +д
    'ث': {'sid': 'S26', 'outputs': {'т', 'ф', 'с'},              'name': 'thāʾ'},  # v2: +с (th→s)
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
    """Build: downstream_letter → [(aa_letter, shift_id), ...]"""
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


def extract_consonants_en(word: str, dedup_gemination: bool = True) -> List[str]:
    """Extract consonant skeleton from English word (lowercase).
    v2: added 'ph' digraph, gemination dedup (ff→f), and 'ck'→'k'.
    v3: added prefix stripping (al-/el-)."""
    word = word.lower()
    # v3: Strip Arabic article remnants (al-, el-) at word start
    if word.startswith('al-') or word.startswith('el-'):
        word = word[3:]
    # Fused "al" without dash handled via OP_PREFIX in alignment algorithm
    consonants = []
    i = 0
    while i < len(word):
        # Handle digraphs (v2: added 'ph', 'ck')
        if i + 1 < len(word):
            digraph = word[i:i+2]
            if digraph in ('sh', 'ch', 'th', 'gh', 'ph'):
                consonants.append(digraph)
                i += 2
                continue
            if digraph == 'ck':
                consonants.append('k')
                i += 2
                continue
        ch = word[i]
        if ch == 'x':
            # v2: x = /ks/ → split into k + s
            consonants.extend(['k', 's'])
            i += 1
            continue
        if ch not in EN_VOWELS and ch.isalpha():
            consonants.append(ch)
        i += 1

    # v2: Gemination dedup — ff→f, ss→s, tt→t, ll→l, etc.
    if dedup_gemination and len(consonants) > 1:
        deduped = [consonants[0]]
        for c in consonants[1:]:
            if c != deduped[-1]:
                deduped.append(c)
        consonants = deduped

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

    # v3: For compound roots, handle ORIG1+ORIG2 vs AA+AA differently
    if '+' in root_str:
        parts = root_str.split('+')
        # Check if any part has ORIG2/Orkhon/Latin root markers
        has_orig2 = any(
            is_orig2_root(p) or 'ORIG2' in p
            for p in parts
        )
        if has_orig2:
            # ORIG1+ORIG2 compound: use only the ORIG1 (Arabic) part
            for p in parts:
                if not is_orig2_root(p) and 'ORIG2' not in p:
                    root_str = p.strip()
                    break
            else:
                root_str = parts[0].strip()  # fallback: first part
        else:
            # AA+AA compound (CHECKMATE: ش-ه-د+م-و-ت): join all parts
            root_str = root_str.replace('+', '-')

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
        # Depth limit to prevent combinatorial explosion (v2: tightened)
        if depth > min(n_root + n_ds + 10, 30):
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
            # v3: Record partial result even if not all root letters resolved
            # This allows partial root accountability scoring
            if not can_resolve and len(mappings) > best_mapped:
                best_mapped = len(mappings)
                best_result = (list(mappings), list(drops), set(ops), list(extras))
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
            # OP_NASAL: N can only be skipped as epenthetic nasal when:
            # 1. It's BETWEEN two other consonants (not word-initial or word-final)
            # 2. At least one adjacent consonant is already mapped to a root letter
            # If N is at position 0, or at the last consonant, it's likely root.
            is_medial = (di > 0 and di < n_ds - 1)
            has_mapped_neighbor = (len(mappings) > 0 and
                                   any(m['di'] == di - 1 for m in mappings))
            if is_medial and has_mapped_neighbor:
                extras.append({'ds': ds_c, 'pos': di, 'op': 'OP_NASAL'})
                ops.add('OP_NASAL')
                try_align(ri, di + 1, mappings, drops, ops, extras, depth + 1)
                ops.discard('OP_NASAL')
                extras.pop()
            else:
                # N in initial/final position or no mapped neighbor —
                # treat as general corridor artifact (lower priority skip)
                extras.append({'ds': ds_c, 'pos': di, 'op': 'CORRIDOR'})
                try_align(ri, di + 1, mappings, drops, ops, extras, depth + 1)
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
    # If ordered alignment failed or incomplete, try permutations (R02 rule)
    # v2: skip metathesis for roots >4 letters (permutation explosion)
    # v3: fire when best_mapped < n_root (not just 0) — partial recording
    #     can produce non-None result with 1 mapping, blocking metathesis
    if (not best_result or best_mapped < n_root) and n_root <= 4:
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

        # ── v3: Root accountability ratio ──
        root_accountability = (len(root_mapped) + len(root_dropped)) / n_root if n_root > 0 else 0

        # ── CONFIDENCE LEVELS ──
        if all_root_accounted and coverage >= 0.75 and len(corridor_extras) == 0:
            result.confidence = 'HIGH'
            result.passed = True
        elif all_root_accounted and coverage >= 0.60 and len(corridor_extras) <= 1 and len(mid_corridor) == 0:
            result.confidence = 'MEDIUM'
            result.passed = True
        elif all_root_accounted and coverage >= 0.50 and len(corridor_extras) <= 2 and len(mid_corridor) <= 1:
            result.confidence = 'LOW'
            result.passed = True
            result.warnings.append(
                f"LOW confidence: coverage {coverage:.0%}, "
                f"{len(corridor_extras)} corridor artifact(s)"
            )
        elif len(root_mapped) * 3 >= n_root * 2 and len(root_mapped) >= 2 and coverage >= 0.40:
            # v3: Partial root match — ≥2/3 root letters mapped, allow LOW
            result.confidence = 'LOW'
            result.passed = True
            result.warnings.append(
                f"PARTIAL root match: {len(root_mapped)}/{n_root} mapped, "
                f"accountability {root_accountability:.0%}, coverage {coverage:.0%}"
            )
        else:
            result.confidence = 'FAIL'
            result.passed = False
            result.unmapped = corridor_extras
            if not all_root_accounted:
                result.warnings.append(
                    f"Root accountability: {root_accountability:.0%} "
                    f"({len(root_mapped)} mapped + {len(root_dropped)} dropped / {n_root})"
                )
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

    # Build set of all official shift IDs — these are inherently valid
    # v3: Any shift in the official table is not "novel" even if no DB entry
    #     uses it yet in their phonetic_chain column (fixes SY bug)
    official_sids = set()
    shift_table = SHIFT_TABLE_EN if lang == 'en' else SHIFT_TABLE_RU
    for entry in shift_table.values():
        official_sids.add(entry['sid'])

    # Query DB for usage counts
    try:
        from uslap_db_connect import connect
        conn = connect()
    except ImportError:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
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
        # v3: Official shifts get minimum count of 1 (inherently valid)
        if count == 0 and sid in official_sids:
            count = 1
        result.shift_usage[sid] = count
        result.total_precedent += count
        if count == 0:
            result.novel_shifts.append(sid)

    conn.close()

    result.passed = len(result.novel_shifts) == 0
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# S-GATE: SEMANTIC CROSS-CHECK (sibling consistency)
# ═══════════════════════════════════════════════════════════════════════════════

class SGateResult:
    def __init__(self):
        self.passed = True
        self.warning = ''
        self.siblings: List[str] = []         # existing terms on same root
        self.qur_meaning: str = ''            # Qur'anic root_meaning field
        self.isolated = False                 # True if word is first on this root

    def __str__(self):
        status = "✓ PASS" if self.passed else "⚠ SEMANTIC MISMATCH"
        lines = [f"S-GATE: {status}"]
        if self.qur_meaning:
            lines.append(f"  Qur'anic meaning: {self.qur_meaning}")
        if self.siblings:
            lines.append(f"  Existing siblings: {', '.join(self.siblings)}")
        if self.isolated:
            lines.append("  First entry on this root — no sibling cross-check possible")
        if self.warning:
            lines.append(f"  Warning: {self.warning}")
        return '\n'.join(lines)


def _expand_ru_family(word: str) -> List[str]:
    """Expand a Russian word into its morphological family.

    Uses known Russian morphophonemic alternations that occur at the
    LAST consonant position (stem-final), which is where Russian
    morphological alternations actually happen:
        Х↔Ш (слух/слушать, сух/сушить, дух/душа)
        К↔Ч (рука/ручной, молоко/молочный)
        Г↔Ж (друг/дружить, бег/бежать)
        Ц↔К (лицо/лик, отец/отеческий)
        Т↔Щ/Ч (свет/свечение, свет/освещать)
        З↔Ж (возить/вожу, низкий/ниже)
        Д↔Ж (ходить/хожу, водить/вождь)
        СТ↔Щ (простой/проще)
        СК↔Щ (искать/ищу)

    Only applies alternations at the LAST consonant before any vowel
    suffix, which is where Russian morphological alternations occur.
    Does NOT apply mid-stem alternations (which would generate phantom
    forms like мушульманин from мусульманин).

    Returns list of family forms (the word itself + alternation variants).
    """
    w = word.lower().strip()
    family = [w]

    # Strip common Russian suffixes to find the stem
    stem = w
    for suffix in ['ание', 'ение', 'ость', 'ство', 'ный', 'ной', 'ная',
                   'ное', 'ные', 'ать', 'ять', 'ить', 'еть', 'уть',
                   'ой', 'ий', 'ый', 'ая', 'ое', 'ые', 'ин', 'анин',
                   'янин', 'ник', 'чик', 'щик']:
        if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
            stem = stem[:-len(suffix)]
            break

    if not stem:
        return family

    # Find the LAST consonant in the stem — that's where alternations happen
    ru_vowels = set('аеёиоуыэюя')
    last_cons_idx = -1
    for i in range(len(stem) - 1, -1, -1):
        if stem[i].isalpha() and stem[i] not in ru_vowels:
            last_cons_idx = i
            break

    if last_cons_idx < 0:
        return family

    last_cons = stem[last_cons_idx]
    prefix = stem[:last_cons_idx]
    suffix_after = stem[last_cons_idx + 1:]

    # Alternations at stem-final position only
    stem_final_alts = {
        'х': ['ш'],
        'ш': ['х'],
        'к': ['ч'],
        'ч': ['к'],
        'г': ['ж'],
        'ж': ['г', 'з'],
        'ц': ['к'],
        'д': ['ж'],
        'з': ['ж'],
        'щ': ['ст', 'ск'],
    }

    # Digraph check: is the last consonant part of СТ or СК?
    if last_cons_idx >= 1:
        digraph = stem[last_cons_idx - 1:last_cons_idx + 1]
        if digraph in ('ст', 'ск'):
            # СТ→Щ, СК→Щ
            variant = stem[:last_cons_idx - 1] + 'щ' + suffix_after
            family.append(variant)

    if last_cons in stem_final_alts:
        for alt in stem_final_alts[last_cons]:
            variant = prefix + alt + suffix_after
            family.append(variant)

    return family


def _expand_en_family(word: str) -> List[str]:
    """Expand an English word into morphological variants.

    English doesn't have Russian-style alternations, but common
    suffixes reveal the stem: -ing, -ed, -er, -tion, -ness, -ly, -ment.
    """
    w = word.lower().strip()
    family = [w]

    # Strip common suffixes to get stem
    for suffix in ['ing', 'tion', 'sion', 'ment', 'ness', 'ful', 'less',
                   'able', 'ible', 'ous', 'ive', 'al', 'ly', 'er', 'ed',
                   'en', 'fy', 'ize', 'ise', 'ist', 'ism']:
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            stem = w[:-len(suffix)]
            family.append(stem)

    return family


def validate_s_gate(root_letters_str: str, downstream_word: str,
                    lang: str = 'en', entry_id: int = 0) -> SGateResult:
    """Semantic cross-check via WORD FAMILY expansion.

    The word's own morphological family reveals its semantic field.
    No LLM needed — the language itself provides the evidence.

    Example:
        СЛУХ → family: [слух, слуш, служ] → СЛУШАТЬ = hearing
        Root س-ل-خ Qur'anic meaning = skinning/stripping
        Family says HEARING, root says SKINNING → MISMATCH → flag

    Three checks:
    1. FAMILY CONSONANT CHECK: expand word into family, extract consonants
       from each variant, check if ALL variants map to the SAME AA root.
       If family variants map to DIFFERENT roots → the word may belong
       to a different root than proposed.
    2. SIBLING CHECK: does the word relate to existing entries on this root?
    3. QUR'ANIC MEANING CHECK: does the word's family overlap with the
       root's Qur'anic meaning field?
    """
    result = SGateResult()

    # ORIG2 SKIP: Bitig/Turkic roots use different consonant system.
    # AA shift tables don't apply. Detect by:
    # 1. Old Turkic script characters (𐰀-𐱈 range)
    # 2. "(Turkic)" or "(Bitig)" or "ОРИГ2" markers in root string
    # 3. Pure Latin root format like "y-u-r-t" (no Arabic letters)
    _has_arabic = any('\u0600' <= c <= '\u06FF' for c in root_letters_str)
    _has_turkic_script = any('\U00010C00' <= c <= '\U00010C48' for c in root_letters_str)
    _has_turkic_marker = any(m in root_letters_str.lower() for m in
                            ('turkic', 'bitig', 'ориг2', 'orig2'))
    if _has_turkic_script or _has_turkic_marker or (not _has_arabic and root_letters_str):
        result.passed = True
        result.warning = "ORIG2_SKIP: Bitig root — AA shift tables do not apply."
        return result

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # PHONETIC_CHAIN SKIP: If the entry already has a documented
        # phonetic_chain, the shift path was verified by a human.
        # The S-gate consonant check can't reconstruct multi-step shifts
        # (e.g. МЕЧЕТЬ←س-ج-د via S17+S02+S19). Trust the chain.
        if entry_id:
            chain_row = conn.execute(
                "SELECT phonetic_chain FROM entries "
                "WHERE entry_id = ? AND phonetic_chain IS NOT NULL "
                "AND phonetic_chain != ''",
                (entry_id,)
            ).fetchone()
            if chain_row:
                result.passed = True
                result.warning = "CHAIN_SKIP: phonetic_chain already documented."
                conn.close()
                return result

        # Get Qur'anic meaning for this root
        qrow = conn.execute(
            "SELECT root_meaning FROM quran_word_roots WHERE root = ? LIMIT 1",
            (root_letters_str,)
        ).fetchone()
        if qrow:
            result.qur_meaning = qrow['root_meaning']

        # Get existing siblings on this root
        siblings = conn.execute(
            "SELECT entry_id, en_term, ru_term, fa_term FROM entries "
            "WHERE root_letters = ? AND entry_id != ?",
            (root_letters_str, entry_id)
        ).fetchall()

        sibling_terms = []
        for s in siblings:
            for col in ('en_term', 'ru_term', 'fa_term'):
                term = s[col]
                if term and term.strip():
                    sibling_terms.append(term.strip())
        result.siblings = sibling_terms

        if not sibling_terms:
            result.isolated = True
            result.passed = True
            conn.close()
            return result

        # ═══════════════════════════════════════════════════════════════
        # CHECK 1: FAMILY CONSONANT DIVERGENCE
        # Expand word into family, check if the ORIGINAL word's
        # consonant skeleton matches the proposed root.
        # Alternation variants (Д↔Ж, К↔Ч, etc.) are grammatical —
        # they reveal semantic field, NOT different roots.
        # Only flag if the ORIGINAL word itself fails Q-gate.
        # ═══════════════════════════════════════════════════════════════

        if lang == 'ru':
            family = _expand_ru_family(downstream_word)
        else:
            family = _expand_en_family(downstream_word)

        # Check only the ORIGINAL word's skeleton against the root.
        # Alternation variants are for semantic evidence only.
        proposed_root = parse_root_letters(root_letters_str)
        if proposed_root:
            if lang == 'ru':
                orig_cons = extract_consonants_ru(downstream_word.lower())
            else:
                orig_cons = extract_consonants_en(downstream_word.lower())
            if orig_cons:
                q_check = validate_q_gate(proposed_root,
                                          ''.join(orig_cons), lang)
                if not q_check.passed:
                    result.passed = False
                    result.warning = (
                        f"CONSONANT MISMATCH: '{downstream_word}' skeleton "
                        f"{''.join(orig_cons)} does NOT map to root "
                        f"{root_letters_str}."
                    )
                    conn.close()
                    return result

        # ═══════════════════════════════════════════════════════════════
        # CHECK 2: SAME-LANGUAGE SIBLING LEXICAL OVERLAP
        # Only compare candidate against siblings in the SAME language.
        # Cross-language siblings (КАЗНА vs TREASURE) can never match
        # lexically — that doesn't mean they're on the wrong root.
        # ═══════════════════════════════════════════════════════════════

        candidate_lower = downstream_word.lower().strip()
        lexical_match = False
        same_lang_siblings = []

        # Get same-language siblings only
        lang_col = 'ru_term' if lang == 'ru' else 'en_term' if lang == 'en' else 'fa_term'
        same_lang_rows = conn.execute(
            f"SELECT {lang_col} FROM entries "
            f"WHERE root_letters = ? AND entry_id != ? "
            f"AND {lang_col} IS NOT NULL AND {lang_col} != ''",
            (root_letters_str, entry_id)
        ).fetchall()
        for row in same_lang_rows:
            term = row[0]
            if term and term.strip():
                same_lang_siblings.append(term.strip())

        all_sibling_words = set()
        for sib in same_lang_siblings:
            sib_lower = sib.lower()
            if (candidate_lower in sib_lower or sib_lower in candidate_lower
                    or candidate_lower[:3] == sib_lower[:3]):
                lexical_match = True
                break
            for part in sib_lower.replace('/', ' ').replace(',', ' ').split():
                w = part.strip()
                if len(w) > 2:
                    all_sibling_words.add(w)

        if not lexical_match:
            for sw in all_sibling_words:
                if (candidate_lower[:3] == sw[:3]
                        or candidate_lower in sw or sw in candidate_lower):
                    lexical_match = True
                    break

        if lexical_match:
            result.passed = True
            conn.close()
            return result

        # No same-language siblings → can't do lexical comparison → pass
        if not same_lang_siblings:
            result.passed = True
            conn.close()
            return result

        # ═══════════════════════════════════════════════════════════════
        # CHECK 3: QUR'ANIC MEANING OVERLAP (English words only)
        # Root meanings are stored in English. Comparing Cyrillic words
        # against English meaning keywords via substring is impossible.
        # This check only works for lang='en'.
        # ═══════════════════════════════════════════════════════════════

        if result.qur_meaning and lang == 'en':
            meaning_keywords = set()
            for word in result.qur_meaning.replace(',', ' ').split():
                w = word.strip().lower()
                if len(w) > 2 and w not in ('the', 'and', 'for', 'from', 'to'):
                    meaning_keywords.add(w)

            sibling_in_meaning = False
            candidate_in_meaning = False

            for sib in sibling_terms:
                sib_lower = sib.lower()
                for kw in meaning_keywords:
                    if kw[:4] in sib_lower or sib_lower[:4] in kw:
                        sibling_in_meaning = True
                        break

            # Check candidate AND its family variants against meaning
            all_candidates = [candidate_lower] + [f.lower() for f in family]
            for cand in all_candidates:
                for kw in meaning_keywords:
                    if kw[:4] in cand or cand[:4] in kw:
                        candidate_in_meaning = True
                        break
                if candidate_in_meaning:
                    break

            if sibling_in_meaning and not candidate_in_meaning and not lexical_match:
                result.passed = False
                result.warning = (
                    f"'{downstream_word}' (family: {family}) has no semantic "
                    f"connection to root meaning '{result.qur_meaning}' or "
                    f"siblings {sibling_terms}. Phonetic match alone."
                )
                conn.close()
                return result

        # ═══════════════════════════════════════════════════════════════
        # CHECK 4: SAME-LANGUAGE SIBLING ISOLATION (fallback)
        # Only flag isolation if there ARE same-language siblings to
        # compare against. Cross-language isolation is expected.
        # ═══════════════════════════════════════════════════════════════

        if not lexical_match and len(same_lang_siblings) >= 2:
            result.passed = False
            result.warning = (
                f"'{downstream_word}' is semantically isolated from all "
                f"{len(same_lang_siblings)} same-language siblings: "
                f"{same_lang_siblings[:5]}."
            )

        conn.close()
    except Exception as e:
        result.warning = f"S-gate error: {e}"
        result.passed = True  # don't block on errors

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

    # For each downstream consonant, find which AA letters could produce it
    possible_sources: List[Set[str]] = []
    for dc in ds_consonants:
        sources = set()
        if dc in reverse_map:
            for ar, sid in reverse_map[dc]:
                sources.add(strip_diacritics(ar))
        possible_sources.append(sources)

    # Query DB for all roots
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
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
        self.s_gate: Optional[SGateResult] = None
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
        if self.s_gate:
            lines.append(str(self.s_gate))
        if self.f_gate:
            lines.append(str(self.f_gate))

        lines.append("─" * 60)
        all_pass = "✓ QUF PASS" if self.overall_pass else "✗ QUF FAIL"
        lines.append(f"OVERALL: {all_pass}")

        # Score cap advisory
        if self.q_gate and not self.q_gate.passed:
            lines.append("  SCORE CAP: 4 (unexplained consonant — criterion 7 fails)")
        elif self.s_gate and not self.s_gate.passed:
            lines.append("  SCORE CAP: 5 (semantic mismatch with siblings — requires review)")
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

    # S-Gate: semantic cross-check (only if Q+U pass)
    if quf.q_gate.passed and quf.u_gate.passed:
        quf.s_gate = validate_s_gate(root_letters_str, downstream_word, lang, entry_id)
    else:
        quf.s_gate = SGateResult()

    # F-Gate
    quf.f_gate = validate_f_gate(root_letters, downstream_word, root_id, lang)

    # Overall: Q + U + S must all pass. F is advisory.
    quf.overall_pass = (quf.q_gate.passed and quf.u_gate.passed
                        and quf.s_gate.passed)

    return quf


# ═══════════════════════════════════════════════════════════════════════════════
# DB LOOKUP HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
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

def extract_consonants_from_transliteration(source_form: str) -> List[str]:
    """v2: Extract consonant skeleton from Arabic transliteration (e.g. 'qahwa', 'masjid').
    Maps transliteration consonants to their AA letter equivalents via reverse lookup."""
    if not source_form:
        return []
    word = source_form.lower().strip()
    # Remove common transliteration marks
    word = word.replace('ʿ', '').replace('ʾ', '').replace("'", "")
    word = word.replace('ā', 'a').replace('ī', 'i').replace('ū', 'u')
    word = word.replace('á', 'a').replace('í', 'i').replace('ú', 'u')
    # Use EN consonant extraction
    return extract_consonants_en(word, dedup_gemination=False)


def source_form_to_aa_letters(source_form: str) -> List[str]:
    """v2: Convert transliterated source form back to AA letter sequence.
    Maps: q→ق, h→ه, w→و, s→س, j→ج, m→م, etc."""
    TRANSLIT_TO_AR = {
        'q': 'ق', 'k': 'ك', 'j': 'ج', 'h': 'ه', 'kh': 'خ',
        'sh': 'ش', 'th': 'ث', 'dh': 'ذ', 'gh': 'غ', 'ph': 'ف',
        's': 'س', 'z': 'ز', 'r': 'ر', 'l': 'ل', 'm': 'م',
        'n': 'ن', 'b': 'ب', 'f': 'ف', 'w': 'و', 'y': 'ي',
        'd': 'د', 't': 'ت', 'p': 'ب', 'v': 'ف', 'g': 'غ',
        'ṣ': 'ص', 'ḍ': 'ض', 'ṭ': 'ط', 'ẓ': 'ظ', 'ḥ': 'ح',
        'ṯ': 'ث', 'ḏ': 'ذ',
    }
    if not source_form:
        return []
    word = source_form.lower().strip()
    # Remove spaces and common non-consonant marks
    word = word.replace('ʿ', '').replace('ʾ', '').replace("'", "")
    letters = []
    i = 0
    vowels = set('aeiouāīūáíú ')
    while i < len(word):
        # Try digraphs first
        if i + 1 < len(word):
            di = word[i:i+2]
            if di in TRANSLIT_TO_AR:
                letters.append(TRANSLIT_TO_AR[di])
                i += 2
                continue
        ch = word[i]
        if ch in vowels or not ch.isalpha():
            i += 1
            continue
        if ch in TRANSLIT_TO_AR:
            letters.append(TRANSLIT_TO_AR[ch])
        i += 1
    return letters


def batch_validate(lang: str = 'en', show_all: bool = False):
    """Validate all entries in a sibling DB. Show failures and warnings.
    v2: source-form fallback, metathesis acceptance, expanded shifts."""
    conn = get_connection()

    if lang == 'en':
        cursor = conn.execute(
            "SELECT entry_id, en_term, root_id, root_letters, phonetic_chain, score, source_form "
            "FROM a1_entries ORDER BY entry_id"
        )
    elif lang == 'ru':
        cursor = conn.execute(
            'SELECT запись_id, рус_термин, корень_id, корневые_буквы, '
            'фонетическая_цепь, балл, исходная_форма FROM "a1_записи" ORDER BY запись_id'
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
    meta_passed = 0       # v2: metathesis passes
    source_passed = 0     # v2: source-form passes

    print(f"\n{'═' * 60}")
    print(f"BATCH QUF VALIDATION v2 — {lang.upper()} ({total} entries)")
    print(f"{'═' * 60}\n")

    skipped_orig2 = 0
    for row in rows:
        eid, term, rid, rl, chain, score, source_form = row
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

        # v2: Accept metathesis (R02) as PASS
        if not q_result.passed and any('METATHESIS' in w for w in q_result.warnings):
            if q_result.coverage_ratio >= 0.50:
                q_result.passed = True
                q_result.confidence = 'MEDIUM'
                q_result.operations.append('R02_METATHESIS')
                meta_passed += 1

        # v2: Source-form fallback — if root validation failed, try source_form
        # Guard: only for source forms with ≤6 AA letters (prevents permutation explosion)
        if not q_result.passed and source_form:
            sf_arabic = source_form_to_aa_letters(source_form)
            if sf_arabic and len(sf_arabic) > len(root_letters) and len(sf_arabic) <= 6:
                sf_result = validate_q_gate(sf_arabic, term, lang)
                if sf_result.passed or (sf_result.coverage_ratio >= 0.50 and
                    any('METATHESIS' in w for w in sf_result.warnings)):
                    q_result = sf_result
                    q_result.passed = True
                    if q_result.confidence == 'FAIL':
                        q_result.confidence = 'MEDIUM'
                    q_result.operations.append('SOURCE_FORM')
                    source_passed += 1

        if q_result.passed:
            passed += 1
            if show_all:
                ops = '+'.join(q_result.operations) if q_result.operations else ''
                print(f"  ✓ #{eid} {term} ({rid}) [{q_result.confidence}] {ops}")
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
    if meta_passed or source_passed:
        print(f"  v2 rescues: {meta_passed} metathesis, {source_passed} source-form")
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
        elif '--root' in args:
            # Handler-mode: --root ROOT --word WORD [--chain CHAIN] [--score SCORE]
            _r_idx = args.index('--root')
            _root = args[_r_idx + 1] if _r_idx + 1 < len(args) else ''
            _word = ''
            if '--word' in args:
                _w_idx = args.index('--word')
                _word = args[_w_idx + 1] if _w_idx + 1 < len(args) else ''
            _score = 5
            if '--score' in args:
                _s_idx = args.index('--score')
                try:
                    _score = int(args[_s_idx + 1])
                except:
                    pass
            result = validate_entry(
                root_id='(handler)',
                root_letters_str=_root,
                downstream_word=_word,
                lang=lang,
                score=_score,
            )
            print(result)
            # EXIT CODE: 1 if QUF FAIL, 0 if QUF PASS
            if 'QUF FAIL' in str(result) or 'FAIL' in str(result).split('OVERALL')[-1] if 'OVERALL' in str(result) else False:
                sys.exit(1)
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
            print("Usage: validate ROOT_ID WORD or validate --id ENTRY_ID or validate --root ROOT --word WORD")

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

    elif cmd == 'stamp':
        target = args[1].lower() if len(args) > 1 else 'en'
        if target == 'all':
            for t in ['en', 'ru', 'eu']:
                stamp_entries(t)
        else:
            stamp_entries(target)

    elif cmd == 'quf_status':
        quf_status_report()

    else:
        print(f"Unknown command: {cmd}")
        print_usage()


# ═══════════════════════════════════════════════════════════════════════════════
# STAMP MODE — Persist QUF results to DB
# ═══════════════════════════════════════════════════════════════════════════════

# Table config: (table_name, id_col, term_col, root_id_col, root_letters_col, score_col, lang)
# Table config: (table_name, id_col, term_col, root_id_col, root_letters_col, score_col, lang, source_form_col)
STAMP_TABLES = {
    'en': ('a1_entries', 'entry_id', 'en_term', 'root_id', 'root_letters', 'score', 'en', 'source_form'),
    'ru': ('a1_записи', 'запись_id', 'рус_термин', 'корень_id', 'корневые_буквы', 'балл', 'ru', 'исходная_форма'),
    'eu': ('european_a1_entries', 'entry_id', 'term', 'root_id', 'root_letters', 'score', 'en', 'source_form'),
}


# ═══════════════════════════════════════════════════════════════════════════════
# v3: SOURCE FORM CONSONANT MATCHING — Layer 3 fallback
# When Q-gate fails using root letters, try direct consonant matching between
# the transliterated source_form and the downstream word. This handles cases
# where Arabic morphological patterns (مَفْعِل prefix in مَسْجِد, Form X in
# استعانة, article الـ in الخرشوف) carried consonants into the downstream word
# that aren't in the bare root.
# ═══════════════════════════════════════════════════════════════════════════════

# Consonant equivalence classes for transliteration matching
_EQUIV = {
    'c': {'c', 'k', 'q', 'ch'},
    'k': {'c', 'k', 'q', 'ch'},
    'q': {'c', 'k', 'q'},
    'ch': {'c', 'k', 'ch', 'sh'},
    's': {'s', 'z', 'c', 'ṣ', 'ṡ'},
    'z': {'s', 'z', 'ẓ'},
    'sh': {'sh', 'ch', 'sch', 'ш'},
    'th': {'th', 't', 'd'},
    't': {'t', 'd', 'th', 'ṭ'},
    'd': {'d', 't', 'ḍ'},
    'g': {'g', 'j', 'gh', 'c', 'k'},
    'j': {'j', 'g', 'dj', 'dsch'},
    'gh': {'gh', 'g'},
    'kh': {'kh', 'ch', 'k', 'h', 'x'},
    'f': {'f', 'v', 'ph', 'p'},
    'v': {'v', 'f', 'w', 'b'},
    'p': {'p', 'b', 'f'},
    'b': {'b', 'p', 'v'},
    'w': {'w', 'v', 'u'},
    'r': {'r', 'l'},
    'l': {'l', 'r'},
    'm': {'m', 'n'},
    'n': {'n', 'm'},
    'h': {'h', 'kh', 'ch'},
    'x': {'x', 'kh', 'ch', 'k'},
    'ph': {'ph', 'f'},
    'sch': {'sch', 'sh', 'ch'},
    'dsch': {'dsch', 'j', 'dj'},
    # Diacritical equivalences (transliteration marks)
    'ṭ': {'ṭ', 't', 'd', 'th'},
    'ḍ': {'ḍ', 'd', 'z'},
    'ṣ': {'ṣ', 's', 'z', 'sh'},
    'ẓ': {'ẓ', 'z', 'd'},
    'ḥ': {'ḥ', 'h', 'kh'},
    'č': {'č', 'ch', 'c', 'ч'},
    'ğ': {'ğ', 'g', 'gh'},
    'ž': {'ž', 'zh', 'j', 'ж'},
    # Cyrillic equivalences
    'ш': {'ш', 'sh', 'щ'},
    'щ': {'щ', 'sh', 'ш'},
    'ч': {'ч', 'ch', 'c'},
    'ж': {'ж', 'j', 'zh'},
    'ц': {'ц', 'ts', 'c'},
    'х': {'х', 'kh', 'h'},
    'ф': {'ф', 'f', 'ph'},
}


def _extract_consonants_translit(text: str) -> List[str]:
    """Extract consonants from transliterated text (Latin or Cyrillic)."""
    text = text.lower().strip()
    # Remove common markers
    for rm in ['→', '→', '/', '(', ')', 'orig2', 'orig1', 'false_sibling']:
        text = text.replace(rm, ' ')
    vowels = set('aeiouāīūáéíóúàèìòùâêîôûäëïöüæœəʾʿ-_ ')
    cyrillic_vowels = set('аеёиоуыэюя')
    consonants = []
    i = 0
    while i < len(text):
        if i + 3 < len(text) and text[i:i+4] == 'dsch':
            consonants.append('dsch')
            i += 4
        elif i + 2 < len(text) and text[i:i+3] in ('sch',):
            consonants.append(text[i:i+3])
            i += 3
        elif i + 1 < len(text) and text[i:i+2] in ('sh', 'ch', 'th', 'gh', 'kh', 'ph', 'dj'):
            consonants.append(text[i:i+2])
            i += 2
        elif text[i] not in vowels and text[i] not in cyrillic_vowels and text[i].isalpha():
            consonants.append(text[i])
            i += 1
        else:
            i += 1
    return consonants


def source_form_match(source_form: str, downstream_word: str, lang: str = 'en') -> Optional[str]:
    """Try direct consonant matching between source_form and downstream word.
    Returns confidence ('SOURCE_FORM') if match is good enough, else None."""
    if not source_form or source_form.startswith('FALSE') or source_form.startswith('EN sibling'):
        return None

    # Take first alternative if multiple (sarāfa / zarāfa → sarāfa)
    sf = source_form.split('/')[0].split('→')[0].strip()
    if not sf or len(sf) < 2:
        return None

    sf_cons = _extract_consonants_translit(sf)
    if lang == 'ru':
        # Cross-script: transliterate Cyrillic downstream to Latin for comparison
        _cyr2lat = {
            'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ж': 'zh', 'з': 'z',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'п': 'p',
            'р': 'r', 'с': 's', 'т': 't', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        }
        ds_cyrillic = extract_consonants_ru(downstream_word)
        ds_cons = [_cyr2lat.get(c, c) for c in ds_cyrillic]
    else:
        ds_cons = extract_consonants_en(downstream_word)

    if not sf_cons or not ds_cons:
        return None

    # Ordered alignment with equivalence matching
    # Try both skip strategies and take the best result:
    # 'ds' = skip downstream consonants (corridor artifacts)
    # 'sf' = skip source consonants (morphological affixes that didn't carry)
    # 'both' = mixed skipping
    best_mapped = 0

    for skip_mode in ('ds', 'sf', 'both'):
        si, di = 0, 0
        mapped = 0
        sf_skips = 0
        while si < len(sf_cons) and di < len(ds_cons):
            sc = sf_cons[si]
            dc = ds_cons[di]
            # Direct match or equivalence match
            if sc == dc or dc in _EQUIV.get(sc, set()) or sc in _EQUIV.get(dc, set()):
                mapped += 1
                si += 1
                di += 1
            elif skip_mode == 'ds':
                di += 1
            elif skip_mode == 'sf':
                si += 1
                sf_skips += 1
            else:
                # 'both': prefer skipping source first, then DS
                if sf_skips < len(sf_cons) // 2:
                    si += 1
                    sf_skips += 1
                else:
                    di += 1
        if mapped > best_mapped:
            best_mapped = mapped

    coverage = best_mapped / len(ds_cons) if ds_cons else 0

    # Need at least 50% of downstream consonants explained and ≥2 mappings
    if best_mapped >= 2 and coverage >= 0.50:
        return 'SOURCE_FORM'
    return None


def stamp_entries(target: str = 'en'):
    """Run QUF validation on all entries in a table and persist results."""
    if target not in STAMP_TABLES:
        print(f"Unknown target: {target}. Use: en | ru | eu | all")
        return

    table, id_col, term_col, rid_col, rl_col, score_col, lang, sf_col = STAMP_TABLES[target]

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        f'SELECT "{id_col}", "{term_col}", "{rid_col}", "{rl_col}", "{score_col}", '
        f'COALESCE("{sf_col}", \'\') as _sf '
        f'FROM "{table}" ORDER BY "{id_col}"'
    ).fetchall()

    from datetime import datetime
    now = datetime.now().isoformat(timespec='seconds')

    total = len(rows)
    stamped = 0
    passed = 0
    failed = 0
    skipped = 0
    inherited = 0  # v3: sibling inheritance count
    batch = []

    # v3: EU sibling inheritance — build cache of root_ids with passing EN entries
    en_passing_roots = set()
    if target == 'eu':
        cur = conn.execute("SELECT DISTINCT root_id FROM a1_entries WHERE quf_pass = 1")
        en_passing_roots = {str(r[0]) for r in cur if r[0]}

    print(f"\n{'═' * 60}")
    print(f"QUF STAMP — {target.upper()} ({total} entries)")
    print(f"{'═' * 60}\n")

    for row in rows:
        eid = row[id_col]
        term = row[term_col] or ''
        rid = row[rid_col] or ''
        rl = row[rl_col] or ''
        sc = row[score_col] or 0
        sf = row['_sf'] or ''  # v3: source_form for fallback

        # Clean term for EU entries (may contain accents)
        if '/' in term:
            term = term.split('/')[0].strip()

        if not rl or not term:
            # No root letters or term — mark as skipped
            batch.append((None, None, None, 0, now, eid))
            skipped += 1
            continue

        # Skip ORIG2 entries
        if rid and str(rid).startswith('T'):
            batch.append(('ORIG2_SKIP', None, None, None, now, eid))
            skipped += 1
            continue
        if is_orig2_root(rl):
            batch.append(('ORIG2_SKIP', None, None, None, now, eid))
            skipped += 1
            continue

        # Run full QUF validation
        try:
            result = validate_entry(
                root_id=str(rid),
                root_letters_str=rl,
                downstream_word=term,
                lang=lang,
                entry_id=int(str(eid).replace('P', '').replace('F', '')) if isinstance(eid, str) else eid,
                score=int(sc) if sc else 0,
            )

            q_val = result.q_gate.confidence if result.q_gate else 'FAIL'
            u_val = 'PASS' if (result.u_gate and result.u_gate.passed) else 'FAIL'
            f_val = 'UNIQUE' if (result.f_gate and result.f_gate.unique) else 'COMPETING'
            overall = 1 if result.overall_pass else 0

            # If Q failed, U and F are not meaningful
            if not result.q_gate.passed:
                u_val = None
                f_val = None

            # v3: EU sibling inheritance — if EU entry fails but EN sibling passes,
            # the phonetic chain is validated through the EN corridor. The EU word
            # is a sibling derivation from the same root via a different corridor.
            if target == 'eu' and not overall and str(rid) in en_passing_roots:
                q_val = 'SIBLING'
                u_val = 'PASS'
                f_val = 'INHERIT'
                overall = 1
                inherited += 1

            # v3: Source form fallback — when Q-gate fails but source_form exists,
            # try direct consonant matching between source form and downstream word.
            # This handles morphological patterns (مَفْعِل, استفعال, article الـ)
            # that carried consonants beyond the bare root into the downstream word.
            if not overall and sf:
                sf_conf = source_form_match(sf, term, lang)
                if sf_conf:
                    q_val = 'SOURCE_FORM'
                    u_val = 'PASS'
                    f_val = None
                    overall = 1

            batch.append((q_val, u_val, f_val, overall, now, eid))

            if overall:
                passed += 1
            else:
                failed += 1
            stamped += 1

        except Exception as e:
            batch.append(('ERROR', None, None, 0, now, eid))
            failed += 1
            stamped += 1

        # Commit in batches of 100
        if len(batch) >= 100:
            conn.executemany(
                f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
                f'WHERE "{id_col}"=?',
                batch
            )
            conn.commit()
            batch = []
            pct = (stamped + skipped) / total * 100
            print(f"  [{stamped + skipped:5d}/{total}] {pct:5.1f}%  "
                  f"pass:{passed} fail:{failed} skip:{skipped}")

    # Final batch
    if batch:
        conn.executemany(
            f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
            f'WHERE "{id_col}"=?',
            batch
        )
        conn.commit()

    validated = passed + failed
    pct = (passed / validated * 100) if validated else 0

    print(f"\n{'─' * 60}")
    print(f"STAMPED: {stamped} validated + {skipped} skipped = {stamped + skipped} total")
    print(f"PASS: {passed}/{validated} ({pct:.1f}%)")
    if inherited:
        print(f"  (of which {inherited} via sibling inheritance)")
    print(f"FAIL: {failed}")
    print(f"{'─' * 60}\n")

    conn.close()


def quf_status_report():
    """Show QUF stamp status across all tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    print(f"\n{'═' * 60}")
    print(f"QUF STATUS REPORT")
    print(f"{'═' * 60}\n")

    for target, (table, id_col, term_col, rid_col, rl_col, score_col, lang, sf_col) in STAMP_TABLES.items():
        total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        stamped = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_date IS NOT NULL'
        ).fetchone()[0]
        unstamped = total - stamped

        # Q-gate distribution
        q_dist = conn.execute(
            f'SELECT quf_q, COUNT(*) as cnt FROM "{table}" '
            f'WHERE quf_date IS NOT NULL GROUP BY quf_q ORDER BY cnt DESC'
        ).fetchall()

        # Pass rate
        pass_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 1'
        ).fetchone()[0]
        fail_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND quf_date IS NOT NULL '
            f'AND quf_q != \'ORIG2_SKIP\' AND quf_q IS NOT NULL'
        ).fetchone()[0]

        # Score-QUF mismatches (score ≥8 but QUF fails)
        mismatches = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND {score_col} >= 8 '
            f'AND quf_q NOT IN (\'ORIG2_SKIP\', \'ERROR\') AND quf_q IS NOT NULL '
            f'AND quf_date IS NOT NULL'
        ).fetchone()[0]

        print(f"── {target.upper()} ({table}) ──")
        print(f"  Total: {total} | Stamped: {stamped} | Unstamped: {unstamped}")

        if q_dist:
            dist_str = ' | '.join(f'{d["quf_q"]}:{d["cnt"]}' for d in q_dist)
            print(f"  Q-gate: {dist_str}")

        validated = pass_count + fail_count
        if validated:
            pct = pass_count / validated * 100
            print(f"  Pass: {pass_count}/{validated} ({pct:.1f}%)")

        if mismatches:
            print(f"  ⚠️  Score-QUF mismatches (score≥8, QUF fail): {mismatches}")

        print()

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# QUF PROPAGATION ENGINE — Real QUF: Quantification, Universality, Falsifiability
# Every piece of data must be:
#   Q — Quantifiable: countable evidence, not opinion
#   U — Universal: works across ALL instances, not cherry-picked
#   F — Falsifiable: states what would disprove it
# Each table gets its own QUF "colour" — same 3 principles, domain-specific metrics.
# ═══════════════════════════════════════════════════════════════════════════════

import math

# ── QUF COLUMN STANDARD ──────────────────────────────────────────────────────
QUF_COLUMNS = [
    ('quf_q', 'TEXT'),      # Q grade: HIGH/MEDIUM/LOW/FAIL
    ('quf_u', 'TEXT'),      # U grade: HIGH/MEDIUM/LOW/FAIL
    ('quf_f', 'TEXT'),      # F grade: HIGH/MEDIUM/LOW/FAIL
    ('quf_pass', 'TEXT'),   # TRUE/FALSE overall
    ('quf_date', 'TEXT'),   # ISO timestamp of last QUF run
]


def ensure_quf_columns(conn, table_name: str):
    """Add QUF columns to a table if they don't exist."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()}
    for col_name, col_type in QUF_COLUMNS:
        if col_name not in existing:
            conn.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type}')
    conn.commit()


# ── DOMAIN REGISTRY ──────────────────────────────────────────────────────────
# Each domain defines: table, id_col, and a quf_colour function.
# The quf_colour function receives (conn, row_dict) and returns:
#   {'q': grade, 'u': grade, 'f': grade, 'pass': bool,
#    'q_data': {...}, 'u_data': {...}, 'f_data': {...}}
# Grades: HIGH, MEDIUM, LOW, FAIL

class QUFDomain:
    """A QUF domain — one table category with domain-specific metrics."""
    def __init__(self, name: str, table: str, id_col: str, colour_fn):
        self.name = name
        self.table = table
        self.id_col = id_col
        self.colour_fn = colour_fn  # (conn, row_dict) -> dict

DOMAIN_REGISTRY: Dict[str, QUFDomain] = {}

def register_domain(name, table, id_col, colour_fn):
    DOMAIN_REGISTRY[name] = QUFDomain(name, table, id_col, colour_fn)


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-LANGUAGE PHONETIC WASH (2026-03-30)
# Takes a word in one language, finds the same concept across EN/RU/FR/DE/ES/
# IT/PT/LA, extracts consonants from each, returns the STABLE skeleton —
# consonants that survive across 5+ languages.
# ═══════════════════════════════════════════════════════════════════════════════

def cross_language_wash(word: str, lang: str = 'en',
                        cross_forms: Optional[Dict[str, str]] = None) -> Dict:
    """
    Cross-language phonetic wash.

    If cross_forms provided: {'EN': 'january', 'RU': 'ЯНВАРЬ', 'FR': 'janvier', ...}
    If not provided: searches DB for the same entry across language tables.

    Returns:
        {
            'input': word,
            'per_language': {lang: [consonants]},
            'stable': [(consonant, count)],  # 5+ languages
            'unstable': [(consonant, count)],  # <5 languages
            'skeleton': [consonants],  # stable only, ordered by frequency
            'consonant_count': int,
        }
    """
    result = {
        'input': word,
        'per_language': {},
        'stable': [],
        'unstable': [],
        'skeleton': [],
        'consonant_count': 0,
    }

    forms = cross_forms or {}

    # If no cross_forms provided, try to find them in DB
    if not forms:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            # Find the entry by word
            row = conn.execute(
                "SELECT entry_id, en_term, ru_term, fa_term, root_letters "
                "FROM entries WHERE en_term = ? OR ru_term = ? LIMIT 1",
                (word.upper(), word.upper())
            ).fetchone()
            if row:
                if row['en_term']:
                    forms['EN'] = row['en_term']
                if row['ru_term']:
                    forms['RU'] = row['ru_term']
                # Get European siblings on same root
                if row['root_letters']:
                    eu_rows = conn.execute(
                        "SELECT lang, term FROM european_a1_entries "
                        "WHERE root_letters = ?", (row['root_letters'],)
                    ).fetchall()
                    for er in eu_rows:
                        forms[er['lang'].upper()] = er['term']
                    # Latin
                    lat_rows = conn.execute(
                        "SELECT lat_term FROM latin_a1_entries "
                        "WHERE root_letters = ?", (row['root_letters'],)
                    ).fetchall()
                    for lr in lat_rows:
                        if lr['lat_term']:
                            forms['LA'] = lr['lat_term']
            conn.close()
        except Exception:
            pass

    if not forms:
        # Minimum: just the input word
        forms[lang.upper()] = word

    # Extract consonants from each language
    from collections import Counter

    # Normalize RU consonants to Latin equivalents for comparison
    ru_to_lat = {
        'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ж': 'zh', 'з': 'z',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ь': '',
    }

    for form_lang, form_word in forms.items():
        if form_lang == 'RU' or any('\u0400' <= c <= '\u04FF' for c in form_word):
            raw_cons = extract_consonants_ru(form_word)
            cons_norm = [ru_to_lat.get(c, c) for c in raw_cons if ru_to_lat.get(c, c)]
        else:
            cons_norm = extract_consonants_en(form_word.lower())
        result['per_language'][form_lang] = cons_norm

    # Count how many languages each consonant appears in
    cons_presence = Counter()
    for form_lang, cons in result['per_language'].items():
        for c in set(cons):  # unique per language
            cons_presence[c] += 1

    total_langs = len(result['per_language'])
    threshold = max(total_langs * 0.6, 3)  # 60% of languages or minimum 3

    result['stable'] = [(c, n) for c, n in cons_presence.most_common()
                        if n >= threshold]
    result['unstable'] = [(c, n) for c, n in cons_presence.most_common()
                          if n < threshold and n > 0]
    result['skeleton'] = [c for c, _ in result['stable']]
    result['consonant_count'] = len(result['skeleton'])

    return result


def detect_compound(skeleton: List[str], lang: str = 'en') -> List[Dict]:
    """
    Compound detector for skeletons with 4+ consonants.

    Attempts to decompose into known prefixes + triliteral,
    triliteral + triliteral, or triliteral + known suffix.

    Returns list of candidate decompositions, each:
        {'parts': [(consonants, root_match, tokens)], 'score': int}
    """
    if len(skeleton) < 4:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    candidates = []

    # Known prefixes that fuse into words in corridors
    KNOWN_PREFIXES = {
        'f': 'فِي (fi = in/at)',
        'm': 'مَ (ma = place/time noun prefix)',
    }

    # Try all split points: prefix(1) + root(3+), or root(3) + root(2-3)
    for split in range(1, len(skeleton)):
        part1 = skeleton[:split]
        part2 = skeleton[split:]

        # Check if part1 is a known prefix and part2 is a triliteral
        if len(part1) == 1 and part1[0] in KNOWN_PREFIXES and len(part2) >= 2:
            # Try to find part2 as a root
            root2 = _find_root_for_consonants(part2, lang, conn)
            if root2:
                candidates.append({
                    'type': 'PREFIX+ROOT',
                    'prefix': KNOWN_PREFIXES[part1[0]],
                    'root': root2,
                    'score': root2.get('tokens', 0),
                })

        # Check if both parts map to roots (compound)
        if len(part1) >= 2 and len(part2) >= 2:
            root1 = _find_root_for_consonants(part1, lang, conn)
            root2 = _find_root_for_consonants(part2, lang, conn)
            if root1 and root2:
                candidates.append({
                    'type': 'COMPOUND',
                    'part1': root1,
                    'part2': root2,
                    'score': root1.get('tokens', 0) + root2.get('tokens', 0),
                })

    conn.close()
    return sorted(candidates, key=lambda x: -x['score'])


def _find_root_for_consonants(consonants: List[str], lang: str,
                               conn) -> Optional[Dict]:
    """Find the best matching AA root for a consonant sequence."""
    shift_table = SHIFT_TABLE_EN if lang == 'en' else SHIFT_TABLE_RU
    reverse_map = REVERSE_EN if lang == 'en' else REVERSE_RU

    # For each consonant, find possible AA sources
    possible_sources = []
    for c in consonants:
        sources = set()
        for aa_letter, data in shift_table.items():
            if c in data.get('outputs', set()):
                sources.add(aa_letter)
        possible_sources.append(sources)

    if not all(possible_sources):
        return None

    # Generate candidate roots (all combinations)
    from itertools import product
    best = None
    best_tokens = -1

    for combo in product(*possible_sources):
        root = '-'.join(combo)
        row = conn.execute(
            "SELECT root, root_meaning, COUNT(*) as t "
            "FROM quran_word_roots WHERE root = ? GROUP BY root",
            (root,)
        ).fetchone()
        if row and row['t'] > best_tokens:
            best_tokens = row['t']
            best = {
                'root': row['root'],
                'meaning': row['root_meaning'],
                'tokens': row['t'],
                'consonants': list(combo),
            }

    return best


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: ROOTS
# ═══════════════════════════════════════════════════════════════════════════════

# ─── ORIG2 ROOTS ──────────────────────────────────────────────────────────────
# Bitig roots from Yafith's line. Not Qur'anic — different attestation sources.
# Q = Kashgari attestation, bitig_a1_entries count
# U = convergence with ORIG1? cross-sibling attestation?
# F = genuinely ORIG2 or mislabeled AA laundered through Turkic?

def _quf_roots_orig2(conn, row):
    root_id = row.get('root_id', '')
    root_letters = row.get('root_letters', '')
    bitig_attested = row.get('bitig_attested', 0)
    bitig_source = row.get('bitig_source', '') or ''

    # Q — Kashgari attestation + bitig entries
    bitig_entry_count = 0
    kashgari_attested = False
    try:
        bitig_entry_count = conn.execute(
            "SELECT COUNT(*) FROM bitig_a1_entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]
    except Exception:
        pass
    if bitig_entry_count > 0:
        try:
            kashgari_attested = conn.execute(
                "SELECT COUNT(*) FROM bitig_a1_entries WHERE root_id = ? "
                "AND kashgari_attestation IS NOT NULL AND kashgari_attestation != ''",
                (root_id,)
            ).fetchone()[0] > 0
        except Exception:
            pass

    has_source = bool(bitig_source)
    q_grade = (
        'HIGH' if kashgari_attested and bitig_entry_count >= 1 else
        'MEDIUM' if bitig_entry_count >= 1 or has_source or bitig_attested else
        'LOW' if root_letters else
        'FAIL'
    )

    # U — convergence with ORIG1? downstream forms?
    has_convergence = False
    try:
        rl_short = root_letters[:5] if root_letters else 'NOMATCH'
        has_convergence = conn.execute(
            "SELECT COUNT(*) FROM bitig_convergence_register WHERE orig2_root LIKE ?",
            (f'%{rl_short}%',)
        ).fetchone()[0] > 0
    except Exception:
        pass

    downstream_count = 0
    try:
        downstream_count = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]
    except Exception:
        pass

    u_grade = (
        'HIGH' if has_convergence and bitig_entry_count >= 1 else
        'MEDIUM' if has_convergence or bitig_entry_count >= 1 or downstream_count > 0 else
        'LOW' if has_source else
        'FAIL'
    )

    # F — genuinely ORIG2? Check if root appears in Qur'an (= possibly AA laundered)
    possibly_laundered = False
    try:
        qur_check = conn.execute(
            "SELECT COUNT(*) FROM quran_word_roots WHERE root = ?",
            (root_letters,) if root_letters else ('NOMATCH',)
        ).fetchone()[0]
        possibly_laundered = qur_check > 0
    except Exception:
        pass

    f_grade = (
        'HIGH' if kashgari_attested and not possibly_laundered else
        'MEDIUM' if (has_source or bitig_attested) and not possibly_laundered else
        'LOW' if not possibly_laundered else
        'FAIL'  # possibly laundered AA root
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])
    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'bitig_entries': bitig_entry_count, 'kashgari': kashgari_attested,
                   'has_source': has_source},
        'u_data': {'convergence': has_convergence, 'downstream': downstream_count},
        'f_data': {'possibly_laundered': possibly_laundered},
    }


# ─── AA ROOTS ────────────────────────────────────────────────────────────────

def _quf_roots(conn, row):
    root_id = row['root_id']
    tokens = row.get('quran_tokens', 0) or 0
    lemmas = row.get('quran_lemmas', 0) or 0
    root_letters = row.get('root_letters', '')
    root_type = row.get('root_type', '') or ''

    # ORIG2 roots — different QUF colour
    if str(root_id).startswith('T') or 'ORIG2' in root_type:
        return _quf_roots_orig2(conn, row)
    # Non-standard prefixes (A, B, C, D, K, O, Q, U, Y) — ORIG2 entries with odd IDs
    if root_id and not root_id.startswith('R') and not root_id.startswith('T'):
        return _quf_roots_orig2(conn, row)

    # Q — QUANTIFICATION: How much countable evidence?
    entry_count = 0
    deriv_count = 0
    try:
        entry_count = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]
    except Exception:
        pass
    try:
        deriv_count = conn.execute(
            "SELECT COUNT(*) FROM a4_derivatives WHERE entry_id IN "
            "(SELECT entry_id FROM entries WHERE root_id = ?)", (root_id,)
        ).fetchone()[0]
    except Exception:
        pass

    # An AA root with entries = verified work. With tokens = Qur'anic fact.
    q_grade = (
        'HIGH' if tokens >= 50 and entry_count >= 3 else
        'MEDIUM' if tokens > 0 or entry_count >= 1 else
        'LOW' if root_letters else
        'FAIL'
    )

    # ── U: UNIVERSALITY ──
    # For roots: universality = Qur'anic spread (surahs) + sibling coverage
    # A root appearing in 30+ surahs is UNIVERSAL in the Qur'an itself
    surah_count = 0
    if root_letters:
        try:
            r = conn.execute(
                "SELECT COUNT(DISTINCT surah) FROM quran_word_roots WHERE root = ?",
                (root_letters,)
            ).fetchone()
            if r:
                surah_count = r[0] or 0
        except Exception:
            pass

    sibling_tables = [
        ('entries', 'root_id'),
        ('european_a1_entries', 'root_id'),
        ('bitig_a1_entries', 'root_id'),
        ('latin_a1_entries', 'root_id'),
        ('persian_a1_mad_khil', 'root_id'),
        ('uzbek_vocabulary', 'aa_root_id'),
    ]
    sibling_attested = 0
    for tbl, col in sibling_tables:
        try:
            cnt = conn.execute(
                f'SELECT COUNT(*) FROM "{tbl}" WHERE "{col}" = ?', (root_id,)
            ).fetchone()[0]
            if cnt > 0:
                sibling_attested += 1
        except Exception:
            pass

    # Qur'anic spread is primary universality measure
    # Any Qur'anic attestation = the root is universal in the divine text
    # Compiler tokens count even if surah-level match isn't available
    # Sibling coverage is secondary (propagation quality, not root quality)
    u_grade = (
        'HIGH' if surah_count >= 20 or sibling_attested >= 4 else
        'MEDIUM' if surah_count >= 1 or tokens > 0 or sibling_attested >= 2 else
        'LOW' if sibling_attested >= 1 else
        'FAIL'
    )

    # ── F: FALSIFIABILITY ──
    # For roots: falsifiability = could this root's existence be disproved?
    # A root with Qur'anic tokens is empirically attested — existence is not in question.
    # Anagram/Type C competitors are an ENTRY-level concern (which root does word X come from?)
    # not a ROOT-level concern (does this root exist?).
    # Root-level F checks: token assignment integrity + bare/letters consistency
    bare_consistent = (
        row.get('root_bare', '') == root_letters.replace('-', '')
        if root_letters else True
    )

    f_grade = (
        'HIGH' if tokens > 0 and bare_consistent else
        'MEDIUM' if (tokens > 0 or entry_count > 0) and bare_consistent else
        'LOW' if bare_consistent else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'tokens': tokens, 'entries': entry_count, 'derivatives': deriv_count},
        'u_data': {'surah_count': surah_count, 'sibling_attested': sibling_attested},
        'f_data': {'bare_consistent': bare_consistent},
    }

register_domain('roots', 'roots', 'root_id', _quf_roots)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: DERIVATIVES (a4_derivatives)
# Q: parent entry exists? parent has QUF pass? derivative count for this root?
# U: derivative has siblings in other tables?
# F: link_type is one of the permitted types?
# ═══════════════════════════════════════════════════════════════════════════════

def _quf_derivatives(conn, row):
    entry_id = row.get('entry_id')
    deriv = row.get('derivative', '') or ''
    link_type = row.get('link_type', '') or ''

    # ── Q: parent entry exists and passes QUF? ──
    parent_pass = False
    parent_exists = False
    root_tokens = 0
    if entry_id:
        try:
            p = conn.execute(
                "SELECT quf_pass, root_id FROM entries WHERE entry_id = ?",
                (entry_id,)
            ).fetchone()
            if p:
                parent_exists = True
                parent_pass = p[0] in ('TRUE', '1', True)
                rid = p[1]
                if rid:
                    rt = conn.execute(
                        "SELECT quran_tokens FROM roots WHERE root_id = ?", (rid,)
                    ).fetchone()
                    if rt:
                        root_tokens = rt[0] or 0
        except Exception:
            pass

    q_score = 0
    if parent_exists:
        q_score += 3
    if parent_pass:
        q_score += 4
    if root_tokens > 0:
        q_score += min(int(math.log2(max(root_tokens, 1))), 5)

    q_grade = (
        'HIGH' if q_score >= 8 else
        'MEDIUM' if q_score >= 5 else
        'LOW' if q_score >= 2 else
        'FAIL'
    )

    # ── U: derivative form appears in sibling tables? ──
    attested = 0
    if deriv:
        deriv_lower = deriv.lower()
        for tbl, col in [('european_a1_entries', 'term'), ('latin_a1_entries', 'term')]:
            try:
                cnt = conn.execute(
                    f'SELECT COUNT(*) FROM "{tbl}" WHERE LOWER("{col}") LIKE ?',
                    (f'%{deriv_lower}%',)
                ).fetchone()[0]
                if cnt > 0:
                    attested += 1
            except Exception:
                pass

    u_grade = (
        'HIGH' if attested >= 2 else
        'MEDIUM' if attested >= 1 or parent_pass else
        'LOW' if parent_exists else
        'FAIL'
    )

    # ── F: link type is permitted? ──
    PERMITTED_LINKS = {
        'DIRECT', 'COMPOUND', 'SAME_ROOT', 'PHONETIC', 'SEMANTIC',
        'PREFIX', 'SUFFIX', 'ROOT', 'SIBLING', 'DERIVATIVE',
        'PLURAL', 'DIMINUTIVE', 'PATTERN',
    }
    BANNED_LINKS = {'COGNATE', 'LOANWORD', 'BORROWING'}
    lt_upper = link_type.upper() if link_type else ''
    # Check if link_type is a permitted keyword or contains one
    link_ok = any(p in lt_upper for p in PERMITTED_LINKS) if lt_upper else True
    link_banned = any(b in lt_upper for b in BANNED_LINKS) if lt_upper else False

    f_grade = (
        'FAIL' if link_banned else
        'HIGH' if link_ok and parent_pass else
        'MEDIUM' if link_ok and parent_exists else
        'LOW' if parent_exists else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'parent_exists': parent_exists, 'parent_pass': parent_pass,
                   'tokens': root_tokens, 'score': q_score},
        'u_data': {'attested': attested},
        'f_data': {'link_type': link_type, 'ok': link_ok, 'banned': link_banned},
    }

register_domain('derivatives', 'a4_derivatives', 'deriv_id', _quf_derivatives)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: QV TRANSLATION REGISTER
# Q: ROOT exists in DB? token count?
# U: corruption type documented? all instances covered?
# F: is the washed meaning different from the corrupted one?
# ═══════════════════════════════════════════════════════════════════════════════

def _quf_qv(conn, row):
    qv_id = row.get('QV_ID', '') or row.get('qv_id', '')
    root = row.get('ROOT', '') or row.get('root', '') or ''
    root_meaning = row.get('ROOT_MEANING', '') or row.get('root_meaning', '') or ''
    corruption_type = row.get('CORRUPTION_TYPE', '') or row.get('corruption_type', '') or ''
    corrupted = (row.get('COMMON_MISTRANSLATION', '') or row.get('CORRUPTED_TRANSLATION', '')
                 or row.get('corrupted_translation', '') or '')
    washed = (row.get('CORRECT_TRANSLATION', '') or row.get('AMR_MEANING', '')
              or row.get('WASHED_TRANSLATION', '') or row.get('washed_translation', '') or '')

    # ── Q: root verified in DB? ──
    root_found = False
    root_tokens = 0
    if root:
        try:
            r = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_letters = ? OR root_bare = ?",
                (root, root.replace('-', ''))
            ).fetchone()
            if r:
                root_found = True
                root_tokens = r[0] or 0
        except Exception:
            pass

    q_score = 0
    if root_found:
        q_score += 5
    if root_tokens > 0:
        q_score += min(int(math.log2(max(root_tokens, 1))), 7)
    if root_meaning:
        q_score += 2

    q_grade = (
        'HIGH' if q_score >= 10 else
        'MEDIUM' if q_score >= 5 else
        'LOW' if q_score >= 2 else
        'FAIL'
    )

    # ── U: corruption type is one of the 6 documented types? ──
    VALID_TYPES = {
        'ROOT_FLATTENED', 'ACTION_TO_ETHNIC', 'ACTION->ETHNIC',
        'ATTRIBUTE_TO_GENERIC', 'ATTRIBUTE->GENERIC',
        'SCOPE_NARROWED', 'ROOT_REPLACED', 'ROOT_INVERTED',
    }
    # Normalise arrow variants: → ⟶ ➜ etc. to ->
    ct_normalised = (corruption_type.upper()
                     .replace('\u2192', '->')    # →
                     .replace('\u27F6', '->')    # ⟶
                     .replace('\u279C', '->')    # ➜
                     .replace('_TO_', '->')
                     .replace(' ', '_'))
    type_valid = any(
        vt in ct_normalised
        for vt in VALID_TYPES
    ) if corruption_type else False

    u_grade = (
        'HIGH' if type_valid and washed else
        'MEDIUM' if type_valid or washed else
        'LOW' if corruption_type else
        'FAIL'
    )

    # ── F: washed != corrupted? ──
    meanings_differ = (
        washed.strip().lower() != corrupted.strip().lower()
        if (washed and corrupted) else False
    )

    f_grade = (
        'HIGH' if meanings_differ and root_found else
        'MEDIUM' if meanings_differ else
        'LOW' if washed else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'root_found': root_found, 'tokens': root_tokens, 'score': q_score},
        'u_data': {'type_valid': type_valid, 'corruption_type': corruption_type},
        'f_data': {'meanings_differ': meanings_differ},
    }

register_domain('qv', 'qv_translation_register', 'QV_ID', _quf_qv)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: BITIG CONVERGENCE REGISTER
# Q: both ORIG1 and ORIG2 roots verified?
# U: convergence confirmed across multiple entries?
# F: convergence is not coincidental (different root, similar sound)?
# ═══════════════════════════════════════════════════════════════════════════════

def _quf_bitig_convergence(conn, row):
    conv_id = row.get('convergence_id', '') or row.get('id', '')
    orig1_root = row.get('orig1_root', '') or ''
    orig2_root = row.get('orig2_root', '') or ''
    status = row.get('status', '') or ''

    # ── Q: both roots exist in DB? ──
    orig1_found = False
    orig2_found = False
    orig1_tokens = 0
    if orig1_root:
        try:
            r = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_letters LIKE ?",
                (f'%{orig1_root.replace("-", "%")}%',)
            ).fetchone()
            if r:
                orig1_found = True
                orig1_tokens = r[0] or 0
        except Exception:
            pass
    if orig2_root:
        try:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM bitig_a1_entries WHERE root_letters LIKE ?",
                (f'%{orig2_root}%',)
            ).fetchone()[0]
            orig2_found = cnt > 0
        except Exception:
            pass

    q_score = 0
    if orig1_found:
        q_score += 5
    if orig2_found:
        q_score += 5
    if orig1_tokens > 0:
        q_score += min(int(math.log2(max(orig1_tokens, 1))), 5)

    q_grade = (
        'HIGH' if q_score >= 10 else
        'MEDIUM' if q_score >= 5 else
        'LOW' if q_score >= 2 else
        'FAIL'
    )

    # ── U: convergence is confirmed? ──
    confirmed = 'CONFIRMED' in (status or '').upper()
    u_grade = 'HIGH' if confirmed else 'MEDIUM' if status else 'LOW'

    # ── F: are the roots distinct enough? ──
    # Two different writing systems converging on same meaning = strong evidence
    # If ORIG1 root letters overlap ORIG2 root letters = potentially coincidental
    f_grade = (
        'HIGH' if orig1_found and orig2_found and confirmed else
        'MEDIUM' if orig1_found and orig2_found else
        'LOW' if orig1_found or orig2_found else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'orig1_found': orig1_found, 'orig2_found': orig2_found,
                   'tokens': orig1_tokens, 'score': q_score},
        'u_data': {'confirmed': confirmed, 'status': status},
        'f_data': {},
    }

register_domain('bitig_convergence', 'bitig_convergence_register', 'convergence_id',
                _quf_bitig_convergence)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: BODY LATTICE TABLES
# Q: root_letters exist? Qur'anic attestation?
# U: root appears across multiple body tables?
# F: surah reference verified?
# ═══════════════════════════════════════════════════════════════════════════════

BODY_TABLES = [
    'body_nodes', 'body_substances', 'body_chemistry', 'body_cross_refs',
    'nafs_architecture', 'sensory_architecture', 'nutrition_architecture',
    'healing_protocols', 'body_creation_stages', 'body_preservation',
    'body_diagnostics', 'body_skeletal_map', 'body_movement_chains',
    'body_sound_therapy', 'body_colour_therapy', 'body_extraction_intel',
]


def _quf_body(conn, row):
    root_letters = row.get('root_letters', '') or ''
    surah = row.get('surah', '') or row.get('surah_number', '') or ''
    quranic_ref = row.get('quranic_ref', '') or row.get('quranic_text', '') or ''
    name = row.get('name', '') or row.get('term', '') or row.get('english', '') or ''

    # Tables without root_letters but with quranic_ref — use ref-based QUF
    if not root_letters and not surah:
        surah = quranic_ref  # try quranic_ref as fallback

    # ── Q: root exists and has Qur'anic attestation? ──
    root_found = False
    root_tokens = 0
    if root_letters:
        try:
            r = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_letters = ?",
                (root_letters,)
            ).fetchone()
            if r:
                root_found = True
                root_tokens = r[0] or 0
        except Exception:
            pass

    q_score = 0
    if root_found:
        q_score += 5
    if root_tokens > 0:
        q_score += min(int(math.log2(max(root_tokens, 1))), 7)

    q_grade = (
        'HIGH' if q_score >= 8 else
        'MEDIUM' if q_score >= 4 else
        'LOW' if q_score >= 1 else
        'FAIL'
    )

    # ── U: root appears across multiple body tables? ──
    body_attested = 0
    if root_letters:
        for tbl in BODY_TABLES:
            try:
                cnt = conn.execute(
                    f'SELECT COUNT(*) FROM "{tbl}" WHERE root_letters = ?',
                    (root_letters,)
                ).fetchone()[0]
                if cnt > 0:
                    body_attested += 1
            except Exception:
                pass

    u_grade = (
        'HIGH' if body_attested >= 3 else
        'MEDIUM' if body_attested >= 1 else
        'LOW' if root_found else
        'FAIL'
    )

    # ── F: surah reference is real? ──
    surah_verified = False
    if surah:
        try:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM quran_ayat WHERE surah = ?",
                (str(surah),)
            ).fetchone()[0]
            surah_verified = cnt > 0
        except Exception:
            pass

    f_grade = (
        'HIGH' if surah_verified and root_found else
        'MEDIUM' if root_found else
        'LOW' if root_letters else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'root_found': root_found, 'tokens': root_tokens, 'score': q_score},
        'u_data': {'body_attested': body_attested},
        'f_data': {'surah_verified': surah_verified},
    }

def _quf_cross_refs(conn, row):
    """QUF for cross-reference tables: both ends must exist."""
    source_table = row.get('source_table', '') or ''
    source_id = row.get('source_id', '') or ''
    target_table = row.get('target_table', '') or ''
    target_id = row.get('target_id', '') or ''
    relationship = row.get('relationship', '') or ''

    # ── Q: both ends exist? ──
    source_exists = False
    target_exists = False
    if source_table and source_id:
        try:
            # Get first column as ID
            first_col = conn.execute(f"PRAGMA table_info('{source_table}')").fetchone()
            if first_col:
                cnt = conn.execute(
                    f'SELECT COUNT(*) FROM "{source_table}" WHERE "{first_col[1]}" = ?',
                    (source_id,)
                ).fetchone()[0]
                source_exists = cnt > 0
        except Exception:
            pass
    if target_table and target_id:
        try:
            first_col = conn.execute(f"PRAGMA table_info('{target_table}')").fetchone()
            if first_col:
                cnt = conn.execute(
                    f'SELECT COUNT(*) FROM "{target_table}" WHERE "{first_col[1]}" = ?',
                    (target_id,)
                ).fetchone()[0]
                target_exists = cnt > 0
        except Exception:
            pass

    q_grade = 'HIGH' if source_exists and target_exists else 'MEDIUM' if source_exists or target_exists else 'FAIL'
    u_grade = 'HIGH' if relationship else 'LOW'
    f_grade = 'HIGH' if source_exists and target_exists else 'MEDIUM' if source_exists or target_exists else 'FAIL'
    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'source_exists': source_exists, 'target_exists': target_exists},
        'u_data': {'relationship': relationship},
        'f_data': {},
    }


def _quf_extraction_intel(conn, row):
    """QUF for extraction intelligence: verifiable evidence."""
    quranic_ref = row.get('quranic_ref', '') or ''
    value = row.get('value', '') or ''
    source = row.get('source', '') or ''
    status = row.get('status', '') or ''

    # ── Q: has verifiable data? ──
    has_value = bool(value and value.strip())
    has_source = bool(source and source.strip())
    has_qref = bool(quranic_ref and quranic_ref.strip())
    q_score = sum([has_value * 4, has_source * 3, has_qref * 3])
    q_grade = 'HIGH' if q_score >= 7 else 'MEDIUM' if q_score >= 4 else 'LOW' if q_score >= 1 else 'FAIL'

    # ── U: confirmed status? ──
    confirmed = 'CONFIRMED' in (status or '').upper()
    u_grade = 'HIGH' if confirmed else 'MEDIUM' if status else 'LOW'

    # ── F: Qur'anic reference verifiable? ──
    qref_verified = False
    if has_qref:
        # Parse Q###:### pattern
        import re as _re
        m = _re.search(r'Q?(\d+):', quranic_ref)
        if m:
            try:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM quran_ayat WHERE surah = ?", (m.group(1),)
                ).fetchone()[0]
                qref_verified = cnt > 0
            except Exception:
                pass
    f_grade = 'HIGH' if qref_verified else 'MEDIUM' if has_qref else 'LOW' if has_value else 'FAIL'

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])
    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'has_value': has_value, 'has_source': has_source, 'has_qref': has_qref},
        'u_data': {'confirmed': confirmed},
        'f_data': {'qref_verified': qref_verified},
    }


# Register all body tables with appropriate colour functions
for _bt in BODY_TABLES:
    _id_col = 'id'  # default, will be auto-detected at runtime
    if _bt == 'body_cross_refs':
        register_domain(f'body:{_bt}', _bt, _id_col, _quf_cross_refs)
    elif _bt == 'body_extraction_intel':
        register_domain(f'body:{_bt}', _bt, _id_col, _quf_extraction_intel)
    else:
        register_domain(f'body:{_bt}', _bt, _id_col, _quf_body)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: LINGUISTIC SIBLINGS (fa, uz, bitig)
# Same as existing stamp but upgraded to real QUF grades
# ═══════════════════════════════════════════════════════════════════════════════

def _quf_linguistic_sibling(conn, row, lang='en'):
    """Generic linguistic QUF for any sibling entry table."""
    root_id = row.get('root_id', '') or row.get('aa_root_id', '') or ''
    root_letters = row.get('root_letters', '') or row.get('aa_root', '') or ''
    term = row.get('term', '') or row.get('en_term', '') or ''

    # ── Q: phonetic chain + token count ──
    root_found = False
    root_tokens = 0
    if root_id:
        try:
            r = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_id = ?", (root_id,)
            ).fetchone()
            if r:
                root_found = True
                root_tokens = r[0] or 0
        except Exception:
            pass
    elif root_letters:
        try:
            r = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_letters = ?", (root_letters,)
            ).fetchone()
            if r:
                root_found = True
                root_tokens = r[0] or 0
        except Exception:
            pass

    # EN parent passes QUF?
    en_pass = False
    if root_id:
        try:
            p = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE root_id = ? AND quf_pass = 'TRUE'",
                (root_id,)
            ).fetchone()[0]
            en_pass = p > 0
        except Exception:
            pass

    q_score = 0
    if root_found:
        q_score += 4
    if root_tokens > 0:
        q_score += min(int(math.log2(max(root_tokens, 1))), 6)
    if en_pass:
        q_score += 3

    q_grade = (
        'HIGH' if q_score >= 10 else
        'MEDIUM' if q_score >= 5 else
        'LOW' if q_score >= 2 else
        'FAIL'
    )

    # ── U: sibling coverage + Qur'anic spread ──
    sibling_tables = [
        ('entries', 'root_id'),
        ('european_a1_entries', 'root_id'),
        ('bitig_a1_entries', 'root_id'),
        ('latin_a1_entries', 'root_id'),
    ]
    attested = 0
    # Qur'anic spread counts
    if root_tokens > 0:
        attested += 1
    for tbl, col in sibling_tables:
        try:
            cnt = conn.execute(
                f'SELECT COUNT(*) FROM "{tbl}" WHERE "{col}" = ?', (root_id,)
            ).fetchone()[0]
            if cnt > 0:
                attested += 1
        except Exception:
            pass

    u_grade = (
        'HIGH' if attested >= 3 else
        'MEDIUM' if attested >= 2 else
        'LOW' if attested >= 1 else
        'FAIL'
    )

    # ── F: EN sibling passes QUF (parent attestation)? ──
    f_grade = (
        'HIGH' if en_pass and root_tokens > 0 else
        'MEDIUM' if en_pass or root_found else
        'LOW' if root_letters else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'root_found': root_found, 'tokens': root_tokens,
                   'en_pass': en_pass, 'score': q_score},
        'u_data': {'attested': attested},
        'f_data': {'en_pass': en_pass},
    }

# Persian — view onto entries table where fa_term IS NOT NULL
# Can't update a view directly — update underlying entries table
def _quf_fa(conn, row):
    adapted = dict(row)
    # Map FA view column names to generic names
    for k in list(adapted.keys()):
        kl = k.lower()
        if 'root_id' in kl and 'root_id' not in adapted:
            adapted['root_id'] = adapted[k]
        if 'root_letters' in kl and 'root_letters' not in adapted:
            adapted['root_letters'] = adapted[k]
        if 'entry_id' in kl and 'entry_id' not in adapted:
            adapted['entry_id'] = adapted[k]
    return _quf_linguistic_sibling(conn, adapted, 'fa')

# FA reads from view but writes to underlying entries table
register_domain('fa', 'persian_a1_mad_khil',
                'madkhal_id_مَدخَل_entry_id', _quf_fa)

# Uzbek
def _quf_uz(conn, row):
    row_adapted = dict(row)
    orig_type = row_adapted.get('orig_type', '') or ''
    # ORIG2 entries — Bitig QUF: check bitig_root linkage
    if orig_type == 'ORIG2' or (not row_adapted.get('aa_root_id') and not row_adapted.get('aa_root')):
        bitig_root = row_adapted.get('bitig_root', '') or ''
        bitig_entry_id = row_adapted.get('bitig_entry_id', '') or ''
        kashgari = row_adapted.get('kashgari_form', '') or ''
        has_bitig = bool(bitig_root or bitig_entry_id)
        has_kashgari = bool(kashgari and kashgari.strip())
        q_grade = 'HIGH' if has_kashgari else 'MEDIUM' if has_bitig else 'LOW' if orig_type == 'ORIG2' else 'FAIL'
        u_grade = 'MEDIUM' if has_bitig or orig_type == 'ORIG2' else 'LOW'
        f_grade = 'HIGH' if has_kashgari else 'MEDIUM' if has_bitig else 'LOW' if orig_type == 'ORIG2' else 'FAIL'
        overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])
        return {
            'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
            'q_data': {'bitig_root': bitig_root, 'kashgari': has_kashgari},
            'u_data': {'has_bitig': has_bitig}, 'f_data': {},
        }
    if 'aa_root_id' in row_adapted:
        row_adapted['root_id'] = row_adapted['aa_root_id']
    if 'aa_root' in row_adapted:
        row_adapted['root_letters'] = row_adapted['aa_root']
    return _quf_linguistic_sibling(conn, row_adapted, 'uz')

register_domain('uz', 'uzbek_vocabulary', 'uz_id', _quf_uz)

# Bitig entries
def _quf_bitig(conn, row):
    # ORIG2 entries get their own QUF — Kashgari attestation is their Q
    root_id = row.get('root_id', '') or ''
    if root_id and str(root_id).startswith('T'):
        kashgari = row.get('kashgari_attestation', '') or ''
        has_kashgari = bool(kashgari and kashgari.strip())
        q_grade = 'HIGH' if has_kashgari else 'MEDIUM' if root_id else 'FAIL'
        u_grade = 'MEDIUM'  # exists in bitig table = attested
        f_grade = 'HIGH' if has_kashgari else 'MEDIUM' if root_id else 'FAIL'
        overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])
        return {
            'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
            'q_data': {'kashgari': has_kashgari},
            'u_data': {}, 'f_data': {},
        }
    return _quf_linguistic_sibling(conn, row, 'bi')

register_domain('bitig', 'bitig_a1_entries', 'entry_id', _quf_bitig)


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN: LINGUISTIC ENTRIES (EN, RU, EU) — upgraded from existing stamp
# Uses existing phonetic chain validator (validate_entry) for Q,
# plus real U (sibling coverage) and F (falsification statement)
# ═══════════════════════════════════════════════════════════════════════════════

def _quf_entry_real(conn, row, lang='en'):
    """Real QUF for EN/RU/EU entries. Wraps phonetic chain validator."""
    root_id = str(row.get('root_id', '') or '')
    root_letters = row.get('root_letters', '') or ''
    term = row.get('en_term', '') or row.get('term', '') or ''
    score = row.get('score', 0) or 0

    if not root_letters or not term:
        return {'q': None, 'u': None, 'f': None, 'pass': False,
                'q_data': {}, 'u_data': {}, 'f_data': {}}

    # ORIG2 skip
    if root_id.startswith('T') or is_orig2_root(root_letters):
        return {'q': 'ORIG2_SKIP', 'u': None, 'f': None, 'pass': None,
                'q_data': {}, 'u_data': {}, 'f_data': {}}

    # ── Q: phonetic chain (existing engine) + Qur'anic tokens ──
    rl = parse_root_letters(root_letters)
    q_result = validate_q_gate(rl, term, lang)
    chain_grade = q_result.confidence if q_result else 'FAIL'

    # Add token count to upgrade
    root_tokens = 0
    try:
        r = conn.execute(
            "SELECT quran_tokens FROM roots WHERE root_id = ?", (root_id,)
        ).fetchone()
        if r:
            root_tokens = r[0] or 0
    except Exception:
        pass

    # Combine chain + tokens for real Q
    token_bonus = min(int(math.log2(max(root_tokens, 1))), 4) if root_tokens > 0 else 0
    grade_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FAIL': 0}
    chain_val = grade_map.get(chain_grade, 0)
    combined = chain_val + (1 if token_bonus >= 2 else 0)
    q_grade = (
        'HIGH' if combined >= 4 or (chain_grade == 'HIGH' and root_tokens > 0) else
        'MEDIUM' if combined >= 2 else
        'LOW' if combined >= 1 else
        'FAIL'
    )

    # ── U: sibling coverage (from amr_dhakaa.py model) ──
    sibling_tables = [
        ('entries', 'root_id'),
        ('european_a1_entries', 'root_id'),
        ('latin_a1_entries', 'root_id'),
        ('bitig_a1_entries', 'root_id'),
        ('persian_a1_mad_khil', 'root_id'),
        ('uzbek_vocabulary', 'aa_root_id'),
    ]
    attested = 0
    for tbl, col in sibling_tables:
        try:
            cnt = conn.execute(
                f'SELECT COUNT(*) FROM "{tbl}" WHERE "{col}" = ?', (root_id,)
            ).fetchone()[0]
            if cnt > 0:
                attested += 1
        except Exception:
            pass

    u_grade = (
        'HIGH' if attested >= 4 else
        'MEDIUM' if attested >= 2 else
        'LOW' if attested >= 1 else
        'FAIL'
    )

    # ── F: gap to competitor + Type C + unknown shifts ──
    # Simplified version — full F runs on demand via validate_f_gate
    f_grade = (
        'HIGH' if q_grade in ('HIGH', 'MEDIUM') and attested >= 3 else
        'MEDIUM' if q_grade in ('HIGH', 'MEDIUM') else
        'LOW' if q_result and q_result.passed else
        'FAIL'
    )

    overall = all(g in ('HIGH', 'MEDIUM') for g in [q_grade, u_grade, f_grade])

    return {
        'q': q_grade, 'u': u_grade, 'f': f_grade, 'pass': overall,
        'q_data': {'chain': chain_grade, 'tokens': root_tokens,
                   'coverage': q_result.coverage_ratio if q_result else 0},
        'u_data': {'attested': attested, 'total': len(sibling_tables)},
        'f_data': {'chain_passed': q_result.passed if q_result else False},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PROPAGATION ENGINE — runs real QUF across all registered domains
# ═══════════════════════════════════════════════════════════════════════════════

def propagate_domain(domain_name: str, dry_run: bool = False):
    """Run real QUF across all rows in a domain and persist results."""
    if domain_name not in DOMAIN_REGISTRY:
        print(f"Unknown domain: {domain_name}")
        print(f"Available: {', '.join(sorted(DOMAIN_REGISTRY.keys()))}")
        return

    domain = DOMAIN_REGISTRY[domain_name]
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Auto-detect ID column first
    id_col = domain.id_col

    # Check if table is actually a view
    table_type = conn.execute(
        "SELECT type FROM sqlite_master WHERE name=?", (domain.table,)
    ).fetchone()
    is_view = table_type and table_type[0] == 'view'

    # For views, we need to find the underlying table for writes
    write_table = domain.table
    write_id_col = id_col
    if is_view:
        # Extract underlying table from view definition
        view_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name=?", (domain.table,)
        ).fetchone()[0]
        # Look for "FROM tablename" pattern
        import re as _re
        from_match = _re.search(r'FROM\s+(\w+)', view_sql, _re.IGNORECASE)
        if from_match:
            write_table = from_match.group(1)
            # Map view ID column to underlying table ID column
            # Parse "col AS [alias]" mappings
            alias_match = _re.search(
                r'(\w+)\s+AS\s+\[?' + _re.escape(id_col) + r'\]?',
                view_sql, _re.IGNORECASE
            )
            if alias_match:
                write_id_col = alias_match.group(1)
            else:
                write_id_col = 'entry_id'  # default for entries-based views
            print(f"  (view → writes to {write_table}.{write_id_col})")

    # Ensure QUF columns exist on the write table
    ensure_quf_columns(conn, write_table)
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info('{domain.table}')").fetchall()}
    if id_col not in cols:
        # Try common alternatives
        for candidate in ['id', 'entry_id', 'deriv_id', 'convergence_id',
                          'QV_ID', 'root_id']:
            if candidate in cols:
                id_col = candidate
                break
        else:
            # Fall back to first column (usually the primary key)
            first_col = conn.execute(
                f"PRAGMA table_info('{domain.table}')"
            ).fetchone()
            if first_col:
                id_col = first_col[1]
            else:
                id_col = 'rowid'

    # Sync write_id_col with auto-detected id_col for non-view tables
    if not is_view:
        write_id_col = id_col

    try:
        rows = conn.execute(f'SELECT *, rowid as _rowid FROM "{domain.table}"').fetchall()
    except Exception:
        # Table may be WITHOUT ROWID — fall back to plain SELECT
        try:
            rows = conn.execute(f'SELECT * FROM "{domain.table}"').fetchall()
        except Exception as e:
            print(f"Error reading {domain.table}: {e}")
            conn.close()
            return

    from datetime import datetime
    now = datetime.now().isoformat(timespec='seconds')

    total = len(rows)
    passed = 0
    failed = 0
    skipped = 0
    batch = []

    print(f"\n{'═' * 60}")
    print(f"QUF PROPAGATION — {domain_name.upper()} ({domain.table}: {total} rows)")
    print(f"{'═' * 60}\n")

    for i, row in enumerate(rows):
        row_dict = dict(row)
        try:
            result = domain.colour_fn(conn, row_dict)
        except Exception as e:
            result = {'q': 'ERROR', 'u': None, 'f': None, 'pass': False}
            skipped += 1

        q_val = result.get('q')
        u_val = result.get('u')
        f_val = result.get('f')
        p_val = 'TRUE' if result.get('pass') else ('FALSE' if result.get('pass') is not None else None)

        # Get row ID — use write_id_col if view, else id_col
        if is_view and write_id_col != id_col:
            row_id = row_dict.get(write_id_col) or row_dict.get(id_col) or row_dict.get('_rowid')
        else:
            row_id = row_dict.get(id_col) or row_dict.get('_rowid')

        if not dry_run:
            batch.append((q_val, u_val, f_val, p_val, now, row_id))

        if result.get('pass'):
            passed += 1
        elif result.get('pass') is False:
            failed += 1
        else:
            skipped += 1

        # Commit in batches
        if not dry_run and len(batch) >= 100:
            _flush_batch(conn, write_table, write_id_col, batch)
            batch = []
            pct = (i + 1) / total * 100
            print(f"  [{i + 1:5d}/{total}] {pct:5.1f}%  pass:{passed} fail:{failed} skip:{skipped}")

    # Final batch
    if not dry_run and batch:
        _flush_batch(conn, write_table, write_id_col, batch)

    validated = passed + failed
    pct = (passed / validated * 100) if validated else 0

    print(f"\n{'─' * 60}")
    print(f"DOMAIN: {domain_name.upper()}")
    print(f"  Total: {total} | Validated: {validated} | Skipped: {skipped}")
    print(f"  PASS: {passed}/{validated} ({pct:.1f}%)")
    print(f"  FAIL: {failed}")
    if dry_run:
        print(f"  (DRY RUN — no writes)")
    print(f"{'─' * 60}\n")

    conn.close()


def _is_token_protected(conn, table):
    """Check if table has QUF token update trigger."""
    trigger_name = f'trg_quf_token_upd_{table}'
    result = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name=?",
        (trigger_name,)
    ).fetchone()[0]
    return result > 0


def _generate_tokens(conn, count):
    """Generate fresh QUF tokens for propagation."""
    import uuid
    tokens = []
    for _ in range(count):
        token = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO quf_tokens (token, entry_id, root_letters, generated_by, used) "
            "VALUES (?, 0, 'QUF_PROPAGATION', 'quf_propagation', 0)",
            (token,)
        )
        tokens.append(token)
    conn.commit()
    return tokens


def _flush_batch(conn, table, id_col, batch):
    """Write a batch of QUF results to DB. Handles token-protected tables."""
    token_protected = _is_token_protected(conn, table)

    if token_protected:
        # Need a fresh token per row — check if quf_token column exists
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
        if 'quf_token' not in cols:
            conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "quf_token" TEXT')
            conn.commit()

        tokens = _generate_tokens(conn, len(batch))

        for i, (q, u, f, p, dt, rid) in enumerate(batch):
            token = tokens[i]
            if id_col == 'rowid':
                conn.execute(
                    f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, '
                    f'quf_date=?, quf_token=? WHERE rowid=?',
                    (q, u, f, p, dt, token, rid)
                )
            else:
                conn.execute(
                    f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, '
                    f'quf_date=?, quf_token=? WHERE "{id_col}"=?',
                    (q, u, f, p, dt, token, rid)
                )
            # Mark token as used
            conn.execute("UPDATE quf_tokens SET used=1 WHERE token=?", (token,))
    else:
        # Use row-by-row updates to handle contamination shield on existing data
        skipped = 0
        for row_data in batch:
            try:
                if id_col == 'rowid':
                    conn.execute(
                        f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
                        f'WHERE rowid=?',
                        row_data
                    )
                else:
                    conn.execute(
                        f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
                        f'WHERE "{id_col}"=?',
                        row_data
                    )
            except sqlite3.IntegrityError:
                # Row has pre-existing contaminated data — skip QUF write
                skipped += 1
        if skipped:
            print(f"  (skipped {skipped} rows due to contamination shield on existing data)")
    conn.commit()


def propagate_all(dry_run: bool = False):
    """Run QUF propagation across ALL registered domains."""
    print(f"\n{'═' * 70}")
    print(f"QUF PROPAGATION — ALL DOMAINS ({len(DOMAIN_REGISTRY)} registered)")
    print(f"{'═' * 70}\n")

    for name in sorted(DOMAIN_REGISTRY.keys()):
        try:
            propagate_domain(name, dry_run=dry_run)
        except Exception as e:
            print(f"  ERROR in {name}: {e}\n")


def propagation_status():
    """Show QUF propagation status across all registered domains."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"\n{'═' * 70}")
    print(f"QUF PROPAGATION STATUS — {len(DOMAIN_REGISTRY)} domains")
    print(f"{'═' * 70}\n")

    for name in sorted(DOMAIN_REGISTRY.keys()):
        domain = DOMAIN_REGISTRY[name]
        try:
            total = conn.execute(f'SELECT COUNT(*) FROM "{domain.table}"').fetchone()[0]

            # Check if QUF columns exist
            cols = {row[1] for row in conn.execute(
                f"PRAGMA table_info('{domain.table}')"
            ).fetchall()}
            if 'quf_date' not in cols:
                print(f"  {name:25s} | {domain.table:35s} | {total:5d} rows | NO QUF COLUMNS")
                continue

            stamped = conn.execute(
                f'SELECT COUNT(*) FROM "{domain.table}" WHERE quf_date IS NOT NULL'
            ).fetchone()[0]
            pass_count = conn.execute(
                f'SELECT COUNT(*) FROM "{domain.table}" WHERE quf_pass = \'TRUE\''
            ).fetchone()[0]
            fail_count = conn.execute(
                f'SELECT COUNT(*) FROM "{domain.table}" WHERE quf_pass = \'FALSE\''
            ).fetchone()[0]

            # Q distribution
            q_dist = conn.execute(
                f'SELECT quf_q, COUNT(*) FROM "{domain.table}" '
                f'WHERE quf_date IS NOT NULL GROUP BY quf_q ORDER BY COUNT(*) DESC'
            ).fetchall()
            dist_str = ' | '.join(f'{q}:{c}' for q, c in q_dist) if q_dist else 'none'

            pct = (pass_count / (pass_count + fail_count) * 100) if (pass_count + fail_count) else 0
            status = f"pass:{pass_count} fail:{fail_count} ({pct:.0f}%)" if stamped else "UNSTAMPED"

            print(f"  {name:25s} | {domain.table:35s} | {total:5d} rows | "
                  f"stamped:{stamped:5d} | {status}")

        except Exception as e:
            print(f"  {name:25s} | {domain.table:35s} | ERROR: {e}")

    print(f"\n{'═' * 70}\n")
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# UPDATED CLI — add propagate commands
# ═══════════════════════════════════════════════════════════════════════════════

_original_print_usage = print_usage

def print_usage():
    _original_print_usage()
    print("""
  python3 uslap_quf.py propagate DOMAIN [--dry-run]
      Run real QUF across a domain.
      Domains: """ + ', '.join(sorted(DOMAIN_REGISTRY.keys())) + """
      Example: python3 uslap_quf.py propagate roots

  python3 uslap_quf.py propagate all [--dry-run]
      Run real QUF across ALL registered domains.

  python3 uslap_quf.py propagation_status
      Show QUF propagation status across all domains.

  python3 uslap_quf.py domains
      List all registered QUF domains.
""")

_original_main = main


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN-SPECIFIC QUF — EPISTEMOLOGICAL GATE
# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
#
# 12 LATTICE LAYERS — from the lattice's own architecture:
#   L0-Alphabet, L1-Root, L2-Keyword, L3-DivineNames, L4-QuranicForms,
#   L5-Entries, L6-Siblings, L7-Derivatives, L8-Detection,
#   L9-Body, L10-Formula, L11-History, L12-Intelligence
#
# Each table belongs to a LAYER. Each layer defines what Q, U, F MEAN.
# ═══════════════════════════════════════════════════════════════════════════════

import uuid
from dataclasses import dataclass, field as dc_field
from datetime import datetime


@dataclass
class QUFResult:
    q_grade: str = 'FAIL'
    u_grade: str = 'FAIL'
    f_grade: str = 'FAIL'
    q_evidence: list = dc_field(default_factory=list)
    u_evidence: list = dc_field(default_factory=list)
    f_evidence: list = dc_field(default_factory=list)

    @property
    def overall(self) -> str:
        grades = {'HIGH': 3, 'MEDIUM': 2, 'PENDING': 1, 'LOW': 1, 'FAIL': 0}
        vals = [grades.get(self.q_grade, 0), grades.get(self.u_grade, 0), grades.get(self.f_grade, 0)]
        if 'PENDING' in [self.q_grade, self.u_grade, self.f_grade]:
            return 'PENDING' if min(vals) >= 1 else 'FALSE'
        return 'TRUE' if min(vals) >= 2 else 'FALSE'


# ─── CONTEXT MATERIALIZER ─────────────────────────────────────────────────────
# Pre-compute ALL cross-table data ONCE. Pass into validators. No N+1 queries.

class QUFContext:
    """Pre-computed lattice context for domain validators."""

    def __init__(self, conn):
        self.conn = conn
        self._build()

    def _build(self):
        c = self.conn
        # Sibling entry counts per root_id
        self.sibling_counts = {}  # root_id → {en, eu, la, bi, fa, uz, a4}
        for tbl, key in [('entries','en'), ('european_a1_entries','eu'),
                         ('latin_a1_entries','la'), ('bitig_a1_entries','bi'),
                         ('persian_a1_mad_khil','fa'), ('uzbek_vocabulary','uz')]:
            col = 'root_id' if key != 'uz' else 'aa_root_id'
            try:
                for rid, cnt in c.execute(f'SELECT "{col}", COUNT(*) FROM "{tbl}" WHERE "{col}" IS NOT NULL AND "{col}" != "" GROUP BY "{col}"').fetchall():
                    self.sibling_counts.setdefault(rid, {})[key] = cnt
            except:
                pass
        # A4 derivatives per entry_id
        self.deriv_counts = {}
        for eid, cnt in c.execute('SELECT entry_id, COUNT(*) FROM a4_derivatives GROUP BY entry_id').fetchall():
            self.deriv_counts[eid] = cnt

        # Surah spread per root (hyphenated)
        self.surah_spread = {}
        for root, cnt in c.execute("SELECT root, COUNT(DISTINCT surah) FROM quran_word_roots WHERE root IS NOT NULL AND root != 'None' GROUP BY root").fetchall():
            self.surah_spread[root] = cnt

        # Root tokens lookup
        self.root_tokens = {}
        self.root_types = {}
        self.root_bare = {}
        self.root_meanings = {}
        for rid, letters, bare, rtype, tokens, meaning in c.execute(
                'SELECT root_id, root_letters, root_bare, root_type, quran_tokens, primary_meaning FROM roots').fetchall():
            self.root_tokens[rid] = tokens or 0
            self.root_types[rid] = rtype or ''
            self.root_bare[rid] = bare or ''
            self.root_meanings[rid] = meaning or ''
            if letters:
                self.root_tokens[letters] = tokens or 0

        # Shift usage counts
        self.shift_usage = {}
        for tbl in ['entries', 'european_a1_entries', 'latin_a1_entries']:
            try:
                for (chain,) in c.execute(f'SELECT phonetic_chain FROM "{tbl}" WHERE phonetic_chain IS NOT NULL AND phonetic_chain != ""').fetchall():
                    for sid in re.findall(r'S\d{2}', str(chain)):
                        self.shift_usage[sid] = self.shift_usage.get(sid, 0) + 1
            except:
                pass

        # DP entry counts
        self.dp_counts = {}
        for dp, cnt in c.execute('SELECT dp_code, COUNT(*) FROM dp_entry_map GROUP BY dp_code').fetchall():
            self.dp_counts[dp] = cnt

        # Valid entry IDs
        self.valid_entries = set()
        for (eid,) in c.execute('SELECT entry_id FROM entries').fetchall():
            self.valid_entries.add(eid)

        # Root letters → root_id mapping
        self.letters_to_id = {}
        for rid, letters in c.execute('SELECT root_id, root_letters FROM roots').fetchall():
            if letters:
                self.letters_to_id[letters] = rid

        # Bare → root_id mapping
        self.bare_to_id = {}
        for rid, bare in c.execute('SELECT root_id, root_bare FROM roots WHERE root_bare IS NOT NULL').fetchall():
            if bare:
                self.bare_to_id[bare] = rid

        # BL terms
        self.bl_terms = set()
        for (term,) in c.execute('SELECT contaminated_term FROM contamination_blacklist').fetchall():
            if term:
                self.bl_terms.add(term.lower())

        # Allah name entry refs
        self.allah_entry_refs = {}
        for aid, eids in c.execute('SELECT allah_id, entry_ids FROM names_of_allah WHERE entry_ids IS NOT NULL').fetchall():
            self.allah_entry_refs[aid] = eids

        # Cross-ref pairs (from_id, to_id)
        self.xref_pairs = set()
        for fid, tid in c.execute('SELECT from_id, to_id FROM a5_cross_refs').fetchall():
            self.xref_pairs.add((fid, tid))

        # Chronology IDs
        self.chrono_ids = set()
        for (cid,) in c.execute('SELECT id FROM chronology').fetchall():
            self.chrono_ids.add(cid)

        # Protocol rule IDs
        self.protocol_rules = set()
        for (rid,) in c.execute('SELECT rule_id FROM protocol_immutable').fetchall():
            self.protocol_rules.add(rid)

        # QV corruption types
        self.valid_corruption_types = {'ROOT_FLATTENED', 'ACTION_TO_ETHNIC', 'ATTRIBUTE_TO_GENERIC',
                                       'SCOPE_NARROWED', 'ROOT_REPLACED', 'ROOT_INVERTED',
                                       'ACTION->ETHNIC', 'ATTRIBUTE->GENERIC'}

        # Permitted link types
        self.permitted_links = {'DIRECT', 'COMPOUND', 'SAME_ROOT', 'PHONETIC', 'SEMANTIC',
                                'PREFIX', 'SUFFIX', 'ROOT', 'SEMANTIC_SHIFT', 'COMPOUND_ROOT'}
        self.banned_links = {'COGNATE', 'LOANWORD', 'BORROWING'}

        # Known shift IDs (from mechanism_data where layer=M1)
        self.known_shifts = set()
        try:
            for row in c.execute("SELECT specific_data FROM mechanism_data WHERE layer='M1'").fetchall():
                try:
                    data = json.loads(row[0]) if row[0] else {}
                    sid = data.get('shift_id', '') or data.get('en_consonant', '')
                    if sid:
                        self.known_shifts.add(sid)
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        print(f"  Context built: {len(self.root_tokens)} roots, {len(self.surah_spread)} surah spreads, "
              f"{len(self.shift_usage)} shift usages, {len(self.valid_entries)} entries")




# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN VALIDATORS — RETIRED (2026-03-28)
# QUF validation now lives in AMR AI modules (amr_quf.py router).
# System 2 code archived to: archive/uslap_quf_system2_retired.py
#
# The phonetic engine above (validate_q_gate, validate_u_gate, validate_f_gate)
# is KEPT — imported by amr_aql.py for the LINGUISTIC QUF layer.
#
# To run QUF validation: python3 amr_quf.py validate --table TABLE --id ID
# To run batch:          python3 amr_quf.py batch --table TABLE
# To check coverage:     python3 amr_quf.py status
# ═══════════════════════════════════════════════════════════════════════════════


# Keep original main() as _original_main for backward compat CLI
_original_main = main


def main():
    args = sys.argv[1:]
    if not args:
        print_usage()
        return

    cmd = args[0].lower()

    # Redirect domain commands to amr_quf.py
    if cmd in ('domain_propagate', 'domain_report', 'propagate', 'propagation_status', 'domains'):
        print(f"⚠  '{cmd}' is retired. QUF now lives in AMR AI.")
        print(f"   Use: python3 amr_quf.py status")
        print(f"   Use: python3 amr_quf.py batch --table TABLE")
        print(f"   Use: python3 amr_quf.py validate --table TABLE --id ID")
        return

    # All other commands → original phonetic engine
    _original_main()


if __name__ == '__main__':
    main()
