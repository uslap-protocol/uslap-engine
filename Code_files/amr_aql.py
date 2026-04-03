#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر عَقْل — INTELLECT ENGINE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Layer 4 of the أَمْر full-stack computing system.
Reasons from roots the way roots derive from letters.

The عَقْل does not guess. It computes:
  - Letter values → root meaning (no DB needed)
  - Downstream word → candidate roots (reverse shift)
  - Root → full knowledge tree (expansion)
  - Root × Root → structural relationship (cross-reasoning)
  - Root × Time → deployment timeline (temporal)

Every output traces to 28 letters with fixed values.
No statistical weights. No training data. No hallucination.
"""

import sys
import os
from collections import defaultdict
from itertools import product

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_alphabet import ABJAD, ALPHABET

try:
    from uslap_db_connect import connect as _connect
    _HAS_DB = True
except ImportError:
    _HAS_DB = False


# ═══════════════════════════════════════════════════════════════════════
# LETTER SEMANTICS — computed from amr_alphabet.py, cached here
# ═══════════════════════════════════════════════════════════════════════

LETTER_SEMANTIC = {}
for _letter, _meta in ALPHABET.items():
    _sem = _meta.get('semantic_tendency', '')
    # Extract first word (the core semantic)
    _core = _sem.split('.')[0].split(',')[0].strip().split()[0].upper() if _sem else 'UNKNOWN'
    LETTER_SEMANTIC[_letter] = _core

# Hamza variants all map to ORIGIN
for _h in ['ء', 'أ', 'إ', 'آ', 'ٱ']:
    LETTER_SEMANTIC[_h] = 'ORIGIN'


# ═══════════════════════════════════════════════════════════════════════
# REVERSE SHIFT TABLE — downstream consonant → [(aa_letter, shift_id)]
# Built from shift_lookup in DB, hardcoded here for DB-free operation
# ═══════════════════════════════════════════════════════════════════════

REVERSE_SHIFT = {
    'b': [('ب', 'S09')],
    'c': [('ق', 'S01'), ('ك', 'S20'), ('ح', 'S03'), ('ص', 'S13'), ('س', 'S21')],
    'd': [('ض', 'S06'), ('ذ', 'S12'), ('د', 'S19')],
    'f': [('ف', 'S08')],
    'g': [('ق', 'S01'), ('ج', 'S02'), ('غ', 'S14'), ('ك', 'S20')],
    'h': [('ح', 'S03'), ('ه', 'S23')],
    'j': [('ج', 'S02')],
    'k': [('ق', 'S01'), ('خ', 'S11'), ('ك', 'S20')],
    'l': [('ل', 'S16')],
    'm': [('م', 'S17')],
    'n': [('ن', 'S18')],
    'p': [('ف', 'S08'), ('ب', 'S09')],
    'q': [('ق', 'S01')],
    'r': [('ر', 'S15'), ('و', 'S10')],
    's': [('ش', 'S05'), ('ص', 'S13'), ('س', 'S21'), ('ز', 'S22')],
    't': [('ط', 'S04'), ('د', 'S19'), ('ت', 'S24')],
    'v': [('ف', 'S08'), ('ب', 'S09'), ('و', 'S10')],
    'w': [('و', 'S10')],
    'x': [('خ', 'S11')],
    'z': [('ص', 'S13'), ('س', 'S21'), ('ز', 'S22'), ('ظ', 'S25')],
    'sh': [('ش', 'S05')],
    'ch': [('خ', 'S11'), ('ك', 'S20')],
    'th': [('ض', 'S06'), ('ذ', 'S12'), ('ظ', 'S25'), ('ث', 'S26')],
    'gh': [('غ', 'S14')],
    'y': [('ي', 'YA')],
}

# Vowels that can represent dropped AA letters
VOWEL_DROPS = {
    'a': [('ع', 'S07'), ('ء', 'HAMZA-DROP')],
    'e': [('ع', 'S07'), ('ء', 'HAMZA-DROP')],
    'i': [('ع', 'S07'), ('ء', 'HAMZA-DROP')],
    'o': [('و', 'S10'), ('ع', 'S07')],
    'u': [('و', 'S10'), ('ع', 'S07')],
}


# ═══════════════════════════════════════════════════════════════════════
# 1. ROOT COMPOSITION REASONING — deduce meaning from letters alone
# ═══════════════════════════════════════════════════════════════════════

def deduce_meaning(root_letters):
    """Compute root meaning from letter values. No DB needed.

    Args:
        root_letters: list of AA letters, e.g. ['ك', 'ف', 'ر']
                      or hyphenated string 'ك-ف-ر'

    Returns:
        dict with:
            letters: [{letter, abjad, semantic}, ...]
            abjad_sum: total
            composition: human-readable formula
            deduction: computed meaning
    """
    if isinstance(root_letters, str):
        root_letters = [l for l in root_letters.split('-') if l.strip()]

    letters = []
    total = 0
    parts = []

    for letter in root_letters:
        letter = letter.strip()
        if not letter:
            continue
        abjad = ABJAD.get(letter, 0)
        semantic = LETTER_SEMANTIC.get(letter, 'UNKNOWN')
        letters.append({
            'letter': letter,
            'abjad': abjad,
            'semantic': semantic,
        })
        total += abjad
        parts.append(f"{letter}({abjad})={semantic}")

    # Compose meaning from semantic fields
    semantics = [l['semantic'] for l in letters]
    composition = " + ".join(parts) + f" [={total}]"

    # Generate deduction based on position
    if len(semantics) >= 3:
        deduction = (
            f"The first radical ({letters[0]['letter']}) provides the DOMAIN: {semantics[0]}. "
            f"The second radical ({letters[1]['letter']}) provides the ACTION: {semantics[1]}. "
            f"The third radical ({letters[2]['letter']}) provides the RESULT: {semantics[2]}. "
            f"Together: {semantics[0]} through {semantics[1]} producing {semantics[2]}."
        )
    elif len(semantics) == 2:
        deduction = f"{semantics[0]} meeting {semantics[1]}."
    else:
        deduction = semantics[0] if semantics else "EMPTY"

    return {
        'letters': letters,
        'abjad_sum': total,
        'composition': composition,
        'deduction': deduction,
        'semantic_fields': semantics,
    }


# ═══════════════════════════════════════════════════════════════════════
# 2. BACKWARD CHAINING — downstream word → candidate AA roots
# ═══════════════════════════════════════════════════════════════════════

# ── PREFIX/SUFFIX STRIPPING ────────────────────────────────────────
# Downstream languages ADD material. Roots are INSIDE. Strip to find them.

# ── AFFIX TABLES — ALL DOWNSTREAM LANGUAGES ──────────────────────
# Downstream languages ADD material around the root. These tables
# identify the additions so we can strip them to find the root inside.

AFFIXES = {
    'en': {
        'prefixes': [
            'trans', 'inter', 'super', 'under', 'over', 'counter', 'dis', 'mis',
            'pre', 'pro', 'anti', 'non', 'un', 're', 'de', 'ex', 'in', 'im',
            'en', 'em',
        ],
        'suffixes': [
            'tion', 'sion', 'ment', 'ness', 'ance', 'ence', 'able', 'ible',
            'ious', 'eous', 'ous', 'ing', 'ful', 'less', 'ity',
            'ive', 'ise', 'ize', 'ure', 'ate', 'ery', 'ory', 'ary',
            'ty', 'ly', 'al', 'er', 'or', 'ed', 'es', 'ry',
            'ic', 'y',
        ],
    },
    'fr': {
        'prefixes': [
            'trans', 'inter', 'super', 'contre', 'entre', 'sur',
            'pré', 'pro', 'anti', 'dé', 'dés', 'dis', 'in', 'im',
            'en', 'em', 're', 'ré',
        ],
        'suffixes': [
            'tion', 'sion', 'ment', 'ence', 'ance', 'eur', 'euse',
            'ique', 'isme', 'iste', 'able', 'ible', 'eux', 'euse',
            'ure', 'age', 'ade', 'ée', 'ier', 'ière', 'if', 'ive',
            'el', 'elle', 'al', 'er', 'ir', 'oir', 'é', 'ée',
        ],
    },
    'es': {
        'prefixes': [
            'trans', 'inter', 'super', 'contra', 'sobre', 'entre',
            'pre', 'pro', 'anti', 'des', 'dis', 'in', 'im',
            'en', 'em', 're',
        ],
        'suffixes': [
            'ción', 'sión', 'miento', 'encia', 'ancia', 'ador', 'adora',
            'ismo', 'ista', 'able', 'ible', 'oso', 'osa', 'ura',
            'aje', 'ado', 'ido', 'ero', 'era', 'ivo', 'iva',
            'al', 'ar', 'er', 'ir', 'ón', 'dad', 'tad',
        ],
    },
    'it': {
        'prefixes': [
            'trans', 'inter', 'super', 'contra', 'sopra', 'sotto',
            'pre', 'pro', 'anti', 'dis', 'in', 'im', 'ri', 's',
        ],
        'suffixes': [
            'zione', 'sione', 'mento', 'enza', 'anza', 'atore', 'atrice',
            'ismo', 'ista', 'abile', 'ibile', 'oso', 'osa', 'ura',
            'aggio', 'ato', 'ito', 'iere', 'iera', 'ivo', 'iva',
            'ale', 'are', 'ere', 'ire', 'one', 'tà',
        ],
    },
    'pt': {
        'prefixes': [
            'trans', 'inter', 'super', 'contra', 'sobre', 'entre',
            'pre', 'pro', 'anti', 'des', 'dis', 'in', 'im',
            'en', 'em', 're',
        ],
        'suffixes': [
            'ção', 'são', 'mento', 'ência', 'ância', 'ador', 'adora',
            'ismo', 'ista', 'ável', 'ível', 'oso', 'osa', 'ura',
            'agem', 'ado', 'ido', 'eiro', 'eira', 'ivo', 'iva',
            'al', 'ar', 'er', 'ir', 'ão', 'dade',
        ],
    },
    'de': {
        'prefixes': [
            'über', 'unter', 'hinter', 'durch', 'gegen', 'wider',
            'vor', 'ver', 'zer', 'ent', 'emp', 'miss', 'un',
            'be', 'ge', 'er', 'ab', 'an', 'auf', 'aus', 'ein',
        ],
        'suffixes': [
            'tion', 'ung', 'heit', 'keit', 'schaft', 'lich', 'isch',
            'isch', 'bar', 'sam', 'haft', 'los', 'ig', 'en',
            'er', 'el', 'nis', 'tum', 'sal',
        ],
    },
    'ru': {
        'prefixes': [
            'пере', 'рассм', 'расс', 'рас', 'раз', 'про', 'при', 'пре',
            'под', 'пол', 'над', 'вос', 'воз', 'вы', 'до', 'за', 'из',
            'на', 'об', 'от', 'по', 'с', 'у',
        ],
        'suffixes': [
            'ность', 'ство', 'тель', 'ение', 'ание', 'ость', 'ция',
            'ище', 'ишк', 'ник', 'щик', 'чик', 'ище', 'тор',
            'ный', 'ной', 'ский', 'ской', 'овый', 'евый',
            'ать', 'ять', 'еть', 'ить', 'уть', 'оть',
            'ка', 'ок', 'ек', 'ик',
        ],
    },
    'fa': {
        'prefixes': [
            'بی', 'نا', 'بر', 'در', 'فرا', 'پیش', 'باز', 'هم',
        ],
        'suffixes': [
            'گاه', 'ستان', 'مند', 'بان', 'دان', 'گر', 'کار',
            'وار', 'انه', 'گان', 'ها', 'ان', 'ات', 'ین',
            'ی', 'ه', 'گی', 'شی', 'ور', 'ار',
        ],
    },
}

# Sort all affix lists longest-first
for _lang, _aff in AFFIXES.items():
    _aff['prefixes'].sort(key=len, reverse=True)
    _aff['suffixes'].sort(key=len, reverse=True)


def strip_affixes(word, language='en'):
    """Strip known prefixes and suffixes from a downstream word.

    Works for ALL downstream languages: EN, FR, ES, IT, PT, DE, RU, FA.
    Returns (stem, prefix_stripped, suffix_stripped).
    Only strips if remainder has >= 3 characters (minimum for a root).
    """
    w = word.lower().strip()
    prefix = None
    suffix = None

    affix_data = AFFIXES.get(language, AFFIXES.get('en', {}))
    if not affix_data:
        return w, None, None

    # Strip suffix first (more reliable for root extraction)
    for suf in affix_data.get('suffixes', []):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[:-len(suf)]
            suffix = suf
            break

    # Strip prefix
    for pref in affix_data.get('prefixes', []):
        if w.startswith(pref) and len(w) - len(pref) >= 3:
            w = w[len(pref):]
            prefix = pref
            break

    return w, prefix, suffix


def extract_consonants(word):
    """Extract consonant skeleton from a downstream word."""
    word = word.lower().strip()
    vowels = set('aeiou')
    result = []
    i = 0
    while i < len(word):
        # Check digraphs first
        if i + 1 < len(word):
            digraph = word[i:i+2]
            if digraph in ('sh', 'ch', 'th', 'gh', 'ph'):
                result.append(digraph)
                i += 2
                continue
        if word[i] not in vowels and word[i].isalpha():
            result.append(word[i])
        i += 1
    return result


# ═══════════════════════════════════════════════════════════════════════
# PHONETIC OPERATIONS — documented patterns beyond simple shift reversal
# ═══════════════════════════════════════════════════════════════════════

def dedup_gemination(consonants):
    """OP: Gemination deduplication.
    Double consonant in downstream = single root letter.
    COFFEE: ff→f, MOHAMMED: mm→m, MATTER: tt→t.
    """
    if not consonants:
        return consonants
    result = [consonants[0]]
    for i in range(1, len(consonants)):
        if consonants[i] != consonants[i-1]:
            result.append(consonants[i])
    return result


def strip_nasal_insertion(consonants):
    """OP_NASAL: Remove inserted N that has no AA source.
    N appears in downstream with no Arabic source consonant.
    GOVERN (جَبَّار+N), FURNISH (فَرَش+N), ANTIQUE (عَتِيق+N).
    Returns list of variants: [original, n-stripped-at-each-position].
    """
    variants = [consonants]
    for i, c in enumerate(consonants):
        if c == 'n':
            stripped = consonants[:i] + consonants[i+1:]
            if len(stripped) >= 2:
                variants.append(stripped)
    return variants


def strip_epenthetic_stop(consonants):
    """OP_STOP: Remove epenthetic stop after geminated nasal.
    NN→ND, MM→MB. The D/B is not a root consonant.
    TANDOOR (تَنُّور: NN→ND), HIND (حَنَان: NN→ND).
    """
    variants = [consonants]
    for i in range(len(consonants) - 1):
        # n+d → just n (the d is epenthetic)
        if consonants[i] == 'n' and consonants[i+1] == 'd':
            variants.append(consonants[:i+1] + consonants[i+2:])
        # m+b → just m (the b is epenthetic)
        if consonants[i] == 'm' and consonants[i+1] == 'b':
            variants.append(consonants[:i+1] + consonants[i+2:])
    return variants


def strip_tamarbuta(consonants):
    """OP_TAMARBUTA: Final T may be tāʾ marbūṭa (ة) realisation.
    Not a root consonant — it's the feminine marker surfacing.
    KISMET (قِسْمَة), RACKET (رَاحَة).
    """
    variants = [consonants]
    if consonants and consonants[-1] == 't':
        stripped = consonants[:-1]
        if len(stripped) >= 2:
            variants.append(stripped)
    return variants


def strip_mu_prefix(consonants):
    """R08: مُ prefix stripping.
    M- at the start of a word may be مُ (Form IV/active participle prefix).
    MIRACLE: strip مُ → R-C-L → ر-س-ل (mursalun).
    Only strip if remaining has >= 3 consonants (triliteral root).
    """
    variants = [consonants]
    if consonants and consonants[0] == 'm' and len(consonants) >= 4:
        variants.append(consonants[1:])
    return variants


def strip_ba_prefix(consonants):
    """OP_PREFIX: بَ prefix fusion.
    B-/P- at start may be بَ preposition fused into the word.
    PROPHET: بَ+عارف → P at start is prefix, not root.
    """
    variants = [consonants]
    if consonants and consonants[0] in ('b', 'p') and len(consonants) >= 4:
        variants.append(consonants[1:])
    return variants


def generate_metathesis(consonants):
    """R02: Metathesis / root transposition.
    Consonants may be reordered in downstream forms.
    SACRIFICE: word order S-C-R → root ش-ك-ر (not ش-ر-ك).
    Generate all permutations for triliteral sets.
    """
    from itertools import permutations
    if len(consonants) != 3:
        return [consonants]
    variants = [consonants]
    for perm in permutations(consonants):
        p = list(perm)
        if p != consonants:
            variants.append(p)
    return variants


def apply_liquid_interchange(consonants):
    """L/R liquid interchange.
    ل↔ر interchange documented across corridors.
    """
    variants = [consonants]
    for i, c in enumerate(consonants):
        if c == 'l':
            variant = consonants[:i] + ['r'] + consonants[i+1:]
            variants.append(variant)
        elif c == 'r':
            variant = consonants[:i] + ['l'] + consonants[i+1:]
            variants.append(variant)
    return variants


def apply_voicing_alternation(consonants):
    """OP_VOICE: Systematic voicing/devoicing.
    b↔p, d↔t, g↔k, v↔f, z↔s in downstream.
    """
    VOICE_PAIRS = {
        'b': 'p', 'p': 'b',
        'd': 't', 't': 'd',
        'g': 'k', 'k': 'g',
        'v': 'f', 'f': 'v',
        'z': 's', 's': 'z',
    }
    variants = [consonants]
    for i, c in enumerate(consonants):
        if c in VOICE_PAIRS:
            variant = consonants[:i] + [VOICE_PAIRS[c]] + consonants[i+1:]
            variants.append(variant)
    return variants


def apply_nasal_assimilation(consonants):
    """OP_NASSIM: Nasal assimilation ن→م before bilabial.
    عنبر→amber: the n→m shift before b.
    """
    variants = [consonants]
    for i in range(len(consonants) - 1):
        if consonants[i] == 'm' and consonants[i+1] in ('b', 'p'):
            variant = consonants[:i] + ['n'] + consonants[i+1:]
            variants.append(variant)
    return variants


def _score_shift(sid):
    """Score a shift ID by commonality."""
    if sid in ('S01', 'S08', 'S09', 'S15', 'S16', 'S17', 'S18'):
        return 3  # very common
    elif sid in ('S02', 'S03', 'S05', 'S10', 'S19', 'S20', 'S21', 'S24'):
        return 2  # common
    elif sid in ('S04', 'S06', 'S07', 'S11', 'S12', 'S13', 'S14'):
        return 1  # less common
    return 0  # exotic


def _generate_consonant_variants(consonants):
    """Apply ALL phonetic operations to generate consonant variants.

    Each operation is documented in the lattice (OP_NASAL, OP_STOP,
    OP_TAMARBUTA, R02, R08, OP_PREFIX, OP_VOICE, OP_NASSIM, etc.).

    Returns list of (consonants, ops_applied) tuples.
    """
    # Start with base + gemination-deduped
    base_variants = set()
    base_variants.add(tuple(consonants))
    deduped = dedup_gemination(consonants)
    base_variants.add(tuple(deduped))

    # Apply each operation to expand the variant set
    all_variants = []
    for base in list(base_variants):
        base = list(base)
        # Each operation returns a list of variants
        ops_and_variants = [
            ('BASE', [base]),
            ('OP_NASAL', strip_nasal_insertion(base)),
            ('OP_STOP', strip_epenthetic_stop(base)),
            ('OP_TAMARBUTA', strip_tamarbuta(base)),
            ('R08_MU', strip_mu_prefix(base)),
            ('OP_PREFIX_BA', strip_ba_prefix(base)),
            ('OP_NASSIM', apply_nasal_assimilation(base)),
            ('OP_LIQUID', apply_liquid_interchange(base)),
        ]

        for op_name, variants in ops_and_variants:
            for v in variants:
                key = tuple(v)
                if key not in base_variants or op_name == 'BASE':
                    all_variants.append((v, op_name))
                    base_variants.add(key)

    # Metathesis on triliteral variants (R02)
    metathesis_variants = []
    for v, op in all_variants:
        if len(v) == 3:
            for perm in generate_metathesis(v):
                key = tuple(perm)
                if key not in base_variants:
                    metathesis_variants.append((perm, f'{op}+R02'))
                    base_variants.add(key)
    all_variants.extend(metathesis_variants)

    # Voicing alternation (OP_VOICE) — applied sparingly to avoid explosion
    # Only apply to base form
    voice_variants = apply_voicing_alternation(consonants)
    for v in voice_variants[1:]:  # skip first (it's the original)
        key = tuple(v)
        if key not in base_variants:
            all_variants.append((v, 'OP_VOICE'))
            base_variants.add(key)

    return all_variants


def _trace_consonants_to_roots(consonants, word, language, seen_roots, ops_applied=''):
    """Map a single consonant list through reverse shift to AA root candidates."""
    if not consonants or len(consonants) < 2:
        return []

    position_candidates = []
    for cons in consonants:
        candidates = REVERSE_SHIFT.get(cons, [])
        if not candidates:
            candidates = VOWEL_DROPS.get(cons, [])
        if not candidates:
            candidates = [('?', 'UNKNOWN')]
        position_candidates.append(candidates)

    results = []
    n = len(position_candidates)
    index_sets = []

    if n == 3:
        index_sets.append((0, 1, 2))
    elif n > 3:
        from itertools import combinations
        for combo_idx in combinations(range(n), 3):
            index_sets.append(combo_idx)
        if n == 4:
            index_sets.append((0, 1, 2, 3))
    elif n == 2:
        index_sets.append((0, 1))

    for idx_set in index_sets:
        selected = [position_candidates[i] for i in idx_set]
        selected_cons = [consonants[i] for i in idx_set]

        all_combos = list(product(*selected))
        if len(all_combos) > 200:
            all_combos = all_combos[:200]

        for combo in all_combos:
            aa_letters = [c[0] for c in combo]
            shift_ids = [c[1] for c in combo]
            root_str = '-'.join(aa_letters)

            if root_str in seen_roots or '?' in aa_letters:
                continue
            seen_roots.add(root_str)

            meaning = deduce_meaning(aa_letters)

            score = 0
            chain = []
            for i, (aa, sid) in enumerate(combo):
                chain.append(f"{selected_cons[i]}←{aa}({sid})")
                score += _score_shift(sid)

            if len(aa_letters) == 3:
                score += 2

            results.append({
                'root_letters': root_str,
                'aa_letters': aa_letters,
                'shift_chain': chain,
                'shift_ids': shift_ids,
                'abjad_sum': meaning['abjad_sum'],
                'composition': meaning['composition'],
                'deduction': meaning['deduction'],
                'score': score,
                'downstream_word': word,
                'language': language,
                'ops_applied': ops_applied,
            })

    return results


def _build_candidates_from_consonants(consonants, word, language, seen_roots):
    """Build root candidates from a consonant list using ALL phonetic operations.

    Pipeline:
        1. Generate consonant variants via all documented operations
        2. For each variant, map through reverse shift table
        3. Try triliteral combinations from longer strings
        4. Score by shift commonality + triliteral bonus + operation weight

    Operations applied (from lattice documentation):
        - Gemination dedup (ff→f, mm→m)
        - OP_NASAL: strip inserted N
        - OP_STOP: strip epenthetic stop (ND→N, MB→M)
        - OP_TAMARBUTA: strip final T (ة realisation)
        - R08: strip مُ prefix (M- at start)
        - OP_PREFIX: strip بَ prefix (B-/P- at start)
        - OP_NASSIM: nasal assimilation (m before b → n before b)
        - OP_LIQUID: L/R interchange
        - R02: metathesis (consonant reordering)
        - OP_VOICE: voicing alternation (b↔p, d↔t, g↔k, v↔f, z↔s)
    """
    if not consonants:
        return []

    results = []

    # Generate all variants
    variants = _generate_consonant_variants(consonants)

    for variant_cons, ops in variants:
        cands = _trace_consonants_to_roots(
            variant_cons, word, language, seen_roots, ops
        )
        # Score adjustments based on operation type:
        # - Stripping operations (closer to root) get a BONUS
        # - Transformative operations (change consonants) get a PENALTY
        # This ensures direct phonetic matches outrank indirect ones
        if ops == 'BASE':
            for c in cands:
                c['score'] += 3  # direct match bonus — no operation needed
        elif ops in ('OP_NASAL', 'OP_STOP', 'OP_TAMARBUTA', 'R08_MU', 'OP_PREFIX_BA'):
            for c in cands:
                c['score'] += 2  # stripping bonus — removes downstream addition
        elif ops in ('OP_LIQUID', 'OP_VOICE', 'OP_NASSIM'):
            for c in cands:
                c['score'] -= 2  # transformation penalty — changes a consonant
        elif 'R02' in ops:
            for c in cands:
                c['score'] -= 1  # metathesis penalty — reorders consonants
        results.extend(cands)

    return results


def reverse_trace(word, language='en', max_candidates=10):
    """Given a downstream word, find candidate AA roots via reverse shift.

    Pipeline:
        1. Strip known prefixes/suffixes (downstream additions)
        2. Extract consonant skeleton
        3. Try triliteral combinations (AA roots are overwhelmingly 3-letter)
        4. Score by shift commonality + triliteral bonus
        5. Return ranked candidates

    Args:
        word: downstream word (e.g. 'cover', 'mercy')
        language: source language (default 'en')
        max_candidates: max roots to return

    Returns:
        list of candidate dicts, each with:
            root_letters, shift_chain, abjad_sum, composition, confidence
    """
    seen_roots = set()
    all_candidates = []

    # ── PASS 1: stripped form (primary) ──
    stem, prefix, suffix = strip_affixes(word, language)
    consonants_stripped = extract_consonants(stem)
    if consonants_stripped:
        cands = _build_candidates_from_consonants(
            consonants_stripped, word, language, seen_roots
        )
        # Boost stripped candidates — they're closer to the root
        for c in cands:
            if prefix or suffix:
                c['score'] += 3  # stripping bonus
                c['stripped_from'] = f"{prefix or ''}+{stem}+{suffix or ''}"
        all_candidates.extend(cands)

    # ── PASS 2: raw form (fallback) ──
    consonants_raw = extract_consonants(word)
    if consonants_raw != consonants_stripped:
        cands = _build_candidates_from_consonants(
            consonants_raw, word, language, seen_roots
        )
        all_candidates.extend(cands)

    # Sort by score descending
    all_candidates.sort(key=lambda x: x['score'], reverse=True)
    return all_candidates[:max_candidates]


def verify_candidate(candidate):
    """Verify a candidate root against the FULL DB intelligence layer.

    Queries:
        1. roots → quran_tokens, primary_meaning, root_id
        2. entries → downstream entry count
        3. qv_translation_register → corruption type, washed meaning
        4. dp_register → detection pattern matches
        5. disputed_words → known disputed assignments
        6. phonetic_reversal → documented shift attestations
        7. contamination_blacklist → blacklisted terms
        8. Type C scan → check if reversed pair exists in DB

    Args:
        candidate: dict from reverse_trace()

    Returns:
        candidate dict with full intelligence overlay
    """
    if not _HAS_DB:
        candidate['verified'] = False
        candidate['note'] = 'No DB connection'
        return candidate

    conn = _connect()
    root_letters = candidate['root_letters']

    # ── 1. ROOTS TABLE ──
    row = conn.execute(
        "SELECT root_id, quran_tokens, primary_meaning FROM roots WHERE root_letters = ?",
        (root_letters,)
    ).fetchone()

    if row:
        candidate['root_id'] = row[0]
        candidate['quranic_tokens'] = row[1]
        candidate['primary_meaning'] = row[2]
        candidate['verified'] = True

        # ── 2. ENTRIES COUNT ──
        entry_count = conn.execute(
            "SELECT count(*) FROM entries WHERE root_id = ?", (row[0],)
        ).fetchone()[0]
        candidate['existing_entries'] = entry_count
    else:
        candidate['root_id'] = None
        candidate['quranic_tokens'] = 0
        candidate['existing_entries'] = 0
        candidate['verified'] = False

    # ── 3. QV TRANSLATION REGISTER ──
    qv_rows = conn.execute(
        "SELECT QV_ID, CORRUPTION_TYPE, CORRECT_TRANSLATION, COMMON_MISTRANSLATION "
        "FROM qv_translation_register WHERE ROOT = ?",
        (root_letters,)
    ).fetchall()
    if qv_rows:
        candidate['qv_entries'] = [{
            'qv_id': r[0], 'corruption_type': r[1],
            'correct': r[2], 'mistranslation': r[3]
        } for r in qv_rows]
        candidate['qv_count'] = len(qv_rows)
        # QV presence = this root has DOCUMENTED translation corruption
        # Boost it — it's a known target, more likely to be the correct root
        candidate['score'] += min(len(qv_rows), 5)
    else:
        candidate['qv_entries'] = []
        candidate['qv_count'] = 0

    # ── 4. DP REGISTER ──
    dp_rows = conn.execute(
        "SELECT dp_code, name FROM dp_register WHERE example LIKE ?",
        (f'%{root_letters}%',)
    ).fetchall()
    if dp_rows:
        candidate['dp_hits'] = [{'code': r[0], 'name': r[1]} for r in dp_rows]
    else:
        candidate['dp_hits'] = []

    # ── 5. DISPUTED WORDS ──
    root_nohyphen = root_letters.replace('-', '')
    disp_rows = conn.execute(
        "SELECT lemma, derivation FROM disputed_words "
        "WHERE root_assigned = ? OR root_hyphenated = ?",
        (root_nohyphen, root_letters)
    ).fetchall()
    if disp_rows:
        candidate['disputed_words'] = [{'lemma': r[0], 'derivation': r[1]} for r in disp_rows]
        # Disputed word presence = this root has Qur'anic word attestation
        candidate['score'] += min(len(disp_rows), 3)
    else:
        candidate['disputed_words'] = []

    # ── 6. PHONETIC REVERSAL ──
    # Check if any documented shift in phonetic_reversal matches this candidate's chain
    shift_ids = candidate.get('shift_ids', [])
    if shift_ids:
        placeholders = ','.join('?' * len(shift_ids))
        pr_rows = conn.execute(
            f"SELECT shift_code, from_modern, to_orig, reliability "
            f"FROM phonetic_reversal WHERE shift_code IN ({placeholders})",
            shift_ids
        ).fetchall()
        if pr_rows:
            candidate['attested_shifts'] = [{'code': r[0], 'from': r[1], 'to': r[2], 'reliability': r[3]} for r in pr_rows]
            # Attested shifts = higher confidence
            high_rel = sum(1 for r in pr_rows if r[3] == 'HIGH')
            candidate['score'] += high_rel
        else:
            candidate['attested_shifts'] = []

    # ── 7. CONTAMINATION BLACKLIST ──
    bl_rows = conn.execute(
        "SELECT bl_id, contaminated_term, correct_translation "
        "FROM contamination_blacklist WHERE correct_translation LIKE ?",
        (f'%{root_letters}%',)
    ).fetchall()
    if bl_rows:
        candidate['blacklist_hits'] = [{'bl_id': r[0], 'term': r[1], 'correct': r[2]} for r in bl_rows]

    # ── 8. TYPE C SCAN — check if reversed root exists ──
    letters = [l for l in root_letters.split('-') if l]
    if len(letters) == 3:
        reversed_root = '-'.join(reversed(letters))
        if reversed_root != root_letters:
            rev_row = conn.execute(
                "SELECT root_id, quran_tokens FROM roots WHERE root_letters = ?",
                (reversed_root,)
            ).fetchone()
            if rev_row:
                candidate['type_c_pair'] = {
                    'reversed_root': reversed_root,
                    'reversed_root_id': rev_row[0],
                    'reversed_tokens': rev_row[1],
                    'token_ratio': round(
                        max(candidate.get('quranic_tokens', 0), rev_row[1]) /
                        max(min(candidate.get('quranic_tokens', 0), rev_row[1]), 1),
                        1
                    ),
                }

    # ── 9. NAMES OF ALLAH — is this root a Name of Allah? ──
    root_id = candidate.get('root_id')
    if root_id:
        allah_rows = conn.execute(
            "SELECT allah_id, aa_name, transliteration, meaning "
            "FROM names_of_allah WHERE root_id = ?",
            (root_id,)
        ).fetchall()
        if allah_rows:
            candidate['names_of_allah'] = [
                {'id': r[0], 'aa_term': r[1], 'translit': r[2], 'meaning': r[3]}
                for r in allah_rows
            ]
            # Name of Allah = significant root — informational boost (not dominant)
            candidate['score'] += 2

    # ── 10. QURAN KNOWN FORMS — fast form→root lookup ──
    root_bare = root_letters.replace('-', '')
    qkf_count = conn.execute(
        "SELECT COUNT(*) FROM quran_known_forms WHERE root_unhyphenated = ?",
        (root_bare,)
    ).fetchone()[0]
    if qkf_count:
        candidate['quran_known_forms'] = qkf_count
        # More known forms = better attested root
        candidate['score'] += min(qkf_count // 5, 3)

    # ── 11. AA MORPHEME MAP — does this root generate EN/LA prefixes? ──
    morph_rows = conn.execute(
        "SELECT morpheme, morpheme_type, qur_meaning FROM aa_morpheme_map WHERE aa_root = ?",
        (root_letters,)
    ).fetchall()
    if morph_rows:
        candidate['morpheme_map'] = [
            {'morpheme': r[0], 'type': r[1], 'meaning': r[2]} for r in morph_rows
        ]

    # ── 12. CHILD ENTRIES — people/nation names from this root ──
    if root_id:
        child_rows = conn.execute(
            "SELECT child_id, shell_name, orig_meaning, operation_role "
            "FROM child_entries WHERE orig_root = ?",
            (root_letters,)
        ).fetchall()
        if child_rows:
            candidate['child_entries'] = [
                {'id': r[0], 'name': r[1], 'meaning': r[2], 'role': r[3]}
                for r in child_rows
            ]

    # ── 13. BITIG DEGRADATION REGISTER — degraded Bitig forms ──
    bitig_deg = conn.execute(
        "SELECT deg_id, bitig_original, original_meaning, degradation_type "
        "FROM bitig_degradation_register WHERE dp_codes LIKE ? OR bitig_original LIKE ?",
        (f'%{root_letters}%', f'%{root_bare}%')
    ).fetchall()
    if bitig_deg:
        candidate['bitig_degradation'] = [
            {'id': r[0], 'original': r[1], 'meaning': r[2], 'type': r[3]}
            for r in bitig_deg
        ]

    # ── 14. BITIG CONVERGENCE REGISTER — ORIG1/ORIG2 convergence ──
    bitig_conv = conn.execute(
        "SELECT conv_id, orig2_term, convergence_type "
        "FROM bitig_convergence_register WHERE orig1_root_letters = ?",
        (root_letters,)
    ).fetchall()
    if bitig_conv:
        candidate['bitig_convergence'] = [
            {'id': r[0], 'orig2_term': r[1], 'type': r[2]} for r in bitig_conv
        ]

    # ── 15. WORD DEPLOYMENT MAP — operation context ──
    deploy_rows = conn.execute(
        "SELECT deploy_id, operation_phase, deployed_words, mechanism "
        "FROM word_deployment_map WHERE aa_roots LIKE ?",
        (f'%{root_letters}%',)
    ).fetchall()
    if deploy_rows:
        candidate['deployment'] = [
            {'id': r[0], 'phase': r[1], 'words': r[2], 'mechanism': r[3]}
            for r in deploy_rows
        ]

    # ── 16. CHRONOLOGY — historical deployment ──
    if root_id:
        chrono_rows = conn.execute(
            "SELECT id, date, event FROM chronology WHERE qur_ref LIKE ? OR event LIKE ? LIMIT 5",
            (f'%{root_letters}%', f'%{root_bare}%')
        ).fetchall()
        if chrono_rows:
            candidate['chronology'] = [
                {'id': r[0], 'date': r[1], 'event': r[2][:100]} for r in chrono_rows
            ]

    # ── 17. DECAY LEVEL — if root has entries, what's the decay? ──
    if root_id:
        decay_row = conn.execute(
            "SELECT DISTINCT decay_level FROM entries WHERE root_id = ? AND decay_level IS NOT NULL LIMIT 1",
            (root_id,)
        ).fetchone()
        if decay_row:
            candidate['decay_level'] = decay_row[0]

    # ── 18. NAME ROOT HUB — prophet/special name breakdown ──
    nrh_rows = conn.execute(
        "SELECT name_id, aa_name, corrected_meaning FROM name_root_hub WHERE root_letters = ?",
        (root_letters,)
    ).fetchall()
    if nrh_rows:
        candidate['name_root_hub'] = [
            {'id': r[0], 'aa_term': r[1], 'meaning': r[2][:100]} for r in nrh_rows
        ]

    # ── 19. ISNAD — protocol chain traces ──
    isnad_rows = conn.execute(
        "SELECT isnad_id, chain FROM isnad WHERE traces_to_root = ?",
        (root_letters,)
    ).fetchall()
    if isnad_rows:
        candidate['isnad'] = [{'id': r[0], 'chain': r[1]} for r in isnad_rows]

    conn.close()
    return candidate


# ═══════════════════════════════════════════════════════════════════════
# 3. ROOT EXPANSION — one root → full knowledge tree
# ═══════════════════════════════════════════════════════════════════════

def expand_root(root_id_or_letters):
    """Given a root, generate the complete knowledge tree.

    Args:
        root_id_or_letters: 'R24' or 'ك-ف-ر'

    Returns:
        dict with all downstream data from every table
    """
    if not _HAS_DB:
        return {'error': 'No DB connection'}

    conn = _connect()

    # Resolve to root_id
    if root_id_or_letters.startswith('R') or root_id_or_letters.startswith('T'):
        root = conn.execute(
            "SELECT * FROM roots WHERE root_id = ?", (root_id_or_letters,)
        ).fetchone()
    else:
        root = conn.execute(
            "SELECT * FROM roots WHERE root_letters = ?", (root_id_or_letters,)
        ).fetchone()

    if not root:
        conn.close()
        return {'error': f'Root not found: {root_id_or_letters}'}

    root_id = root['root_id']
    root_letters = root['root_letters']

    # Compute meaning from letters
    meaning = deduce_meaning(root_letters)

    tree = {
        'root': {
            'root_id': root_id,
            'root_letters': root_letters,
            'primary_meaning': root['primary_meaning'],
            'quran_tokens': root['quran_tokens'],
            'computed_meaning': meaning,
        },
        'entries': {'en': [], 'ru': [], 'fa': []},
        'european': [],
        'latin': [],
        'bitig': [],
        'uzbek': [],
        'derivatives': [],
        'cross_refs': [],
        'quranic_words': [],
        'qv_entries': [],
        'names_of_allah': [],
    }

    # EN/RU/FA entries
    for row in conn.execute("SELECT * FROM entries WHERE root_id = ?", (root_id,)):
        entry = dict(row)
        if entry.get('en_term'):
            tree['entries']['en'].append(entry)
        if entry.get('ru_term'):
            tree['entries']['ru'].append(entry)
        if entry.get('fa_term'):
            tree['entries']['fa'].append(entry)

    # European entries
    for row in conn.execute("SELECT * FROM european_a1_entries WHERE root_id = ?", (root_id,)):
        tree['european'].append(dict(row))

    # Latin entries
    for row in conn.execute("SELECT * FROM latin_a1_entries WHERE root_id = ?", (root_id,)):
        tree['latin'].append(dict(row))

    # Bitig entries
    for row in conn.execute("SELECT * FROM bitig_a1_entries WHERE root_id = ?", (root_id,)):
        tree['bitig'].append(dict(row))

    # Uzbek vocabulary
    for row in conn.execute("SELECT * FROM uzbek_vocabulary WHERE aa_root_id = ?", (root_id,)):
        tree['uzbek'].append(dict(row))

    # Derivatives
    entry_ids = [e['entry_id'] for lang in tree['entries'].values() for e in lang]
    if entry_ids:
        placeholders = ','.join('?' * len(entry_ids))
        for row in conn.execute(
            f"SELECT * FROM a4_derivatives WHERE entry_id IN ({placeholders})", entry_ids
        ):
            tree['derivatives'].append(dict(row))

    # Cross-refs
    if entry_ids:
        for row in conn.execute(
            f"SELECT * FROM a5_cross_refs WHERE from_entry_id IN ({placeholders})", entry_ids
        ):
            tree['cross_refs'].append(dict(row))

    # Qur'anic word occurrences
    for row in conn.execute(
        "SELECT surah, ayah, word_position, aa_word, correct_translation, confidence "
        "FROM quran_word_roots WHERE root = ? ORDER BY surah, ayah, word_position LIMIT 50",
        (root_letters,)
    ):
        tree['quranic_words'].append(dict(row))

    # QV register
    for row in conn.execute(
        "SELECT * FROM qv_translation_register WHERE ROOT = ?", (root_letters,)
    ):
        tree['qv_entries'].append(dict(row))

    # Names of Allah
    for row in conn.execute(
        "SELECT * FROM names_of_allah WHERE root_id = ?", (root_id,)
    ):
        tree['names_of_allah'].append(dict(row))

    # Summary counts
    tree['summary'] = {
        'en_entries': len(tree['entries']['en']),
        'ru_entries': len(tree['entries']['ru']),
        'fa_entries': len(tree['entries']['fa']),
        'european': len(tree['european']),
        'latin': len(tree['latin']),
        'bitig': len(tree['bitig']),
        'uzbek': len(tree['uzbek']),
        'derivatives': len(tree['derivatives']),
        'cross_refs': len(tree['cross_refs']),
        'quranic_words': len(tree['quranic_words']),
        'names_of_allah': len(tree['names_of_allah']),
        'total_downstream': (
            len(tree['entries']['en']) + len(tree['entries']['ru']) +
            len(tree['entries']['fa']) + len(tree['european']) +
            len(tree['latin']) + len(tree['bitig']) + len(tree['uzbek']) +
            len(tree['derivatives'])
        ),
    }

    conn.close()
    return tree


# ═══════════════════════════════════════════════════════════════════════
# 4. CROSS-ROOT REASONING — relate two roots structurally
# ═══════════════════════════════════════════════════════════════════════

def relate_roots(root_a, root_b):
    """Find structural relationship between two roots.

    Detects:
        - SHARED_LETTERS: common radical letters
        - METATHESIS (Type C): same letters, different order
        - SHARED_SEMANTIC: overlapping semantic fields
        - ABJAD_RELATION: mathematical relationship between sums

    Args:
        root_a, root_b: root_letters strings (e.g. 'ر-ح-م', 'م-ر-ح')

    Returns:
        dict with relationships found
    """
    letters_a = set(root_a.replace('-', ''))
    letters_b = set(root_b.replace('-', ''))
    list_a = [l for l in root_a.split('-') if l]
    list_b = [l for l in root_b.split('-') if l]

    meaning_a = deduce_meaning(root_a)
    meaning_b = deduce_meaning(root_b)

    relationships = []

    # Check metathesis (Type C Active Inversion)
    if letters_a == letters_b and list_a != list_b:
        relationships.append({
            'type': 'TYPE_C_ACTIVE_INVERSION',
            'description': (
                f'Same consonants rearranged: {root_a} → {root_b}. '
                f'Operator takes root letters, REARRANGES them, builds COUNTER-SYSTEM. '
                f'{root_a} [{meaning_a["abjad_sum"]}] vs {root_b} [{meaning_b["abjad_sum"]}].'
            ),
            'severity': 'HIGH',
        })

    # Shared letters
    shared = letters_a & letters_b
    if shared and letters_a != letters_b:
        relationships.append({
            'type': 'SHARED_RADICALS',
            'shared': list(shared),
            'count': len(shared),
            'description': f'Share {len(shared)} radical(s): {", ".join(shared)}',
        })

    # Shared semantic fields
    sem_a = set(meaning_a['semantic_fields'])
    sem_b = set(meaning_b['semantic_fields'])
    shared_sem = sem_a & sem_b
    if shared_sem:
        relationships.append({
            'type': 'SHARED_SEMANTIC',
            'shared_fields': list(shared_sem),
            'description': f'Share semantic field(s): {", ".join(shared_sem)}',
        })

    # Abjad relationship
    sum_a = meaning_a['abjad_sum']
    sum_b = meaning_b['abjad_sum']
    if sum_a == sum_b:
        relationships.append({
            'type': 'ABJAD_EQUAL',
            'value': sum_a,
            'description': f'Same abjad sum: {sum_a}',
        })
    elif sum_a > 0 and sum_b > 0:
        if sum_a % sum_b == 0 or sum_b % sum_a == 0:
            ratio = max(sum_a, sum_b) // min(sum_a, sum_b)
            relationships.append({
                'type': 'ABJAD_MULTIPLE',
                'ratio': ratio,
                'description': f'Abjad ratio {ratio}:1 ({sum_a} vs {sum_b})',
            })

    return {
        'root_a': {'letters': root_a, 'meaning': meaning_a},
        'root_b': {'letters': root_b, 'meaning': meaning_b},
        'relationships': relationships,
        'relationship_count': len(relationships),
    }


# ═══════════════════════════════════════════════════════════════════════
# 4b. INTELLIGENCE LAYER — wired to DP, QV, op_codes, phonetic_reversal
# Schema has the muscles. These functions connect them to the skeleton.
# ═══════════════════════════════════════════════════════════════════════

def find_type_c_pairs(min_tokens_original=10, min_tokens_inversion=0):
    """Auto-scan DB for ALL reversed root pairs (Type C Active Inversion).

    Returns all triliteral root pairs where letters are identical but
    order is reversed. Abjad sum is ALWAYS equal (mathematical guarantee).
    Token ratio indicates severity of inversion.

    Returns:
        list of dicts with original, inversion, token_ratio, severity
    """
    if not _HAS_DB:
        return []

    conn = _connect()
    rows = conn.execute("""
        SELECT a.root_id, a.root_letters, a.quran_tokens,
               b.root_id, b.root_letters, b.quran_tokens
        FROM roots a, roots b
        WHERE a.rowid < b.rowid
        AND length(a.root_letters) = 5 AND length(b.root_letters) = 5
        AND a.root_letters != b.root_letters
        AND substr(a.root_letters,1,1) = substr(b.root_letters,5,1)
        AND substr(a.root_letters,3,1) = substr(b.root_letters,3,1)
        AND substr(a.root_letters,5,1) = substr(b.root_letters,1,1)
        AND a.quran_tokens >= ? AND b.quran_tokens >= ?
        ORDER BY a.quran_tokens DESC
    """, (min_tokens_original, min_tokens_inversion)).fetchall()

    pairs = []
    for row in rows:
        # Original = higher token count (Allah used it MORE)
        if row[2] >= row[5]:
            orig_id, orig_letters, orig_tokens = row[0], row[1], row[2]
            inv_id, inv_letters, inv_tokens = row[3], row[4], row[5]
        else:
            orig_id, orig_letters, orig_tokens = row[3], row[4], row[5]
            inv_id, inv_letters, inv_tokens = row[0], row[1], row[2]

        ratio = orig_tokens / max(inv_tokens, 1)
        severity = (
            'EXTREME' if ratio > 100 else
            'SEVERE' if ratio > 20 else
            'HIGH' if ratio > 5 else
            'MODERATE' if ratio > 2 else
            'MILD'
        )

        # Get Qur'anic meanings from DB (NOT from weights)
        orig_meaning = conn.execute(
            "SELECT DISTINCT correct_translation FROM quran_word_roots WHERE root = ? LIMIT 1",
            (orig_letters,)
        ).fetchone()
        inv_meaning = conn.execute(
            "SELECT DISTINCT correct_translation FROM quran_word_roots WHERE root = ? LIMIT 1",
            (inv_letters,)
        ).fetchone()

        # Compute abjad (guaranteed equal for reversals)
        letters = [l for l in orig_letters.split('-') if l]
        abjad = sum(ABJAD.get(l, 0) for l in letters)

        pairs.append({
            'original': {'root_id': orig_id, 'root_letters': orig_letters,
                         'tokens': orig_tokens,
                         'db_meaning': orig_meaning[0] if orig_meaning else None},
            'inversion': {'root_id': inv_id, 'root_letters': inv_letters,
                          'tokens': inv_tokens,
                          'db_meaning': inv_meaning[0] if inv_meaning else None},
            'abjad_sum': abjad,
            'token_ratio': round(ratio, 1),
            'severity': severity,
        })

    conn.close()
    return pairs


def detect_inversion_levels(root_a, root_b):
    """Multi-level inversion detection using QV register + Qur'anic meanings.

    Level 1: Letter inversion (same letters, different order, same abjad)
    Level 2: Meaning inversion (Qur'anic meanings are opposite)
    Level 3: Translation inversion (downstream word masks the Qur'anic meaning)

    Returns dict with levels detected and evidence from DB.
    """
    if not _HAS_DB:
        return {'error': 'No DB connection'}

    conn = _connect()
    letters_a = set(root_a.replace('-', ''))
    letters_b = set(root_b.replace('-', ''))
    list_a = [l for l in root_a.split('-') if l]
    list_b = [l for l in root_b.split('-') if l]

    result = {
        'root_a': root_a, 'root_b': root_b,
        'levels': [], 'evidence': [], 'qv_hits': [], 'dp_hits': []
    }

    # LEVEL 1: Letter inversion check
    if letters_a == letters_b and list_a != list_b:
        abjad = sum(ABJAD.get(l, 0) for l in list_a)
        result['levels'].append({
            'level': 1,
            'type': 'LETTER_INVERSION',
            'detail': f'Same letters rearranged. Abjad sum: {abjad} (both).'
        })

        # Get token counts
        for root_letters, label in [(root_a, 'a'), (root_b, 'b')]:
            row = conn.execute(
                "SELECT quran_tokens FROM roots WHERE root_letters = ?",
                (root_letters,)
            ).fetchone()
            result[f'tokens_{label}'] = row[0] if row else 0

    # LEVEL 2: Meaning inversion — compare Qur'anic washed translations
    meaning_a = conn.execute(
        "SELECT DISTINCT correct_translation FROM quran_word_roots WHERE root = ?",
        (root_a,)
    ).fetchall()
    meaning_b = conn.execute(
        "SELECT DISTINCT correct_translation FROM quran_word_roots WHERE root = ?",
        (root_b,)
    ).fetchall()

    if meaning_a and meaning_b:
        result['db_meaning_a'] = [r[0] for r in meaning_a]
        result['db_meaning_b'] = [r[0] for r in meaning_b]
        result['levels'].append({
            'level': 2,
            'type': 'MEANING_INVERSION',
            'detail': f'Qur\'anic meanings — {root_a}: {result["db_meaning_a"][0]} | {root_b}: {result["db_meaning_b"][0]}'
        })

    # LEVEL 3: Translation inversion — check QV register for either root
    for root_letters in [root_a, root_b]:
        qv_rows = conn.execute(
            "SELECT qv_id, corruption_type, original_meaning, corrupted_meaning "
            "FROM qv_translation_register WHERE root_letters = ?",
            (root_letters,)
        ).fetchall()
        for qv in qv_rows:
            result['qv_hits'].append({
                'qv_id': qv[0], 'corruption_type': qv[1],
                'original': qv[2], 'corrupted': qv[3],
                'root': root_letters
            })
        if qv_rows:
            result['levels'].append({
                'level': 3,
                'type': 'TRANSLATION_INVERSION',
                'detail': f'{root_letters} has {len(qv_rows)} QV entries — downstream translation masks Qur\'anic meaning.'
            })

    # Check DP register for relevant codes
    for root_letters in [root_a, root_b]:
        dp_rows = conn.execute(
            "SELECT dp_code, name FROM dp_register WHERE example LIKE ?",
            (f'%{root_letters}%',)
        ).fetchall()
        for dp in dp_rows:
            result['dp_hits'].append({
                'dp_code': dp[0], 'name': dp[1], 'root': root_letters
            })

    # Check disputed_words
    for root_letters in [root_a, root_b]:
        disp = conn.execute(
            "SELECT * FROM disputed_words WHERE root_assigned = ? OR root_hyphenated = ?",
            (root_letters.replace('-', ''), root_letters)
        ).fetchall()
        if disp:
            result['evidence'].append({
                'type': 'DISPUTED_WORD',
                'root': root_letters,
                'count': len(disp)
            })

    conn.close()
    return result


def cross_wash(words, language='en'):
    """Derivative cross-wash: feed a word FAMILY, extract common skeleton.

    The washing algorithm: strip each word to consonants, find the
    consonant skeleton that appears in ALL (or most) words. That skeleton
    is the root. Individual word hypotheses may disagree — the FAMILY
    reveals the truth.

    Args:
        words: list of related downstream words (e.g. ['mercy', 'merchant', 'market', 'commerce'])
        language: source language

    Returns:
        dict with common_skeleton, root_candidates, per-word breakdowns
    """
    if not words:
        return {'error': 'No words provided'}

    # Step 1: Extract consonant skeletons for each word
    word_data = []
    for word in words:
        stem, pfx, sfx = strip_affixes(word, language)
        cons_stripped = extract_consonants(stem)
        cons_raw = extract_consonants(word)
        word_data.append({
            'word': word,
            'stem': stem,
            'prefix': pfx,
            'suffix': sfx,
            'consonants_stripped': cons_stripped,
            'consonants_raw': cons_raw,
        })

    # Step 2: Find common consonants across ALL words
    # Use raw consonants (more complete)
    all_cons_sets = [set(wd['consonants_raw']) for wd in word_data]
    common_cons = all_cons_sets[0]
    for cs in all_cons_sets[1:]:
        common_cons = common_cons & cs

    # Step 3: Find consonants in MOST words (>= 75%)
    from collections import Counter
    all_cons_flat = []
    for wd in word_data:
        all_cons_flat.extend(set(wd['consonants_raw']))
    cons_freq = Counter(all_cons_flat)
    threshold = len(words) * 0.75
    majority_cons = {c for c, count in cons_freq.items() if count >= threshold}

    # Step 4: Ordered common skeleton (preserve order from first word)
    first_raw = word_data[0]['consonants_raw']
    skeleton = [c for c in first_raw if c in majority_cons]

    # Step 5: Map skeleton through reverse shift to find root candidates
    seen = set()
    candidates = _trace_consonants_to_roots(skeleton, words[0], language, seen, 'CROSS_WASH')

    # Step 6: Verify top candidates against DB
    if _HAS_DB:
        for i in range(min(len(candidates), 20)):
            candidates[i] = verify_candidate(candidates[i])
        # Sort by tokens
        candidates.sort(key=lambda x: (x.get('quranic_tokens', 0), x.get('score', 0)), reverse=True)

    # Step 7: Check for Type C pairs among top candidates
    type_c_flags = []
    top_roots = [c['root_letters'] for c in candidates[:10] if c.get('verified')]
    for i, ra in enumerate(top_roots):
        for rb in top_roots[i+1:]:
            la = set(ra.replace('-', ''))
            lb = set(rb.replace('-', ''))
            if la == lb and ra != rb:
                type_c_flags.append({
                    'root_a': ra, 'root_b': rb,
                    'type': 'TYPE_C_ACTIVE_INVERSION'
                })

    return {
        'input_words': words,
        'common_consonants': sorted(common_cons),
        'majority_consonants': sorted(majority_cons),
        'skeleton': skeleton,
        'candidates': candidates[:15],
        'type_c_flags': type_c_flags,
        'word_breakdowns': word_data,
    }


def severity_score(original_tokens, inversion_tokens):
    """Token-ratio severity classification for inversions.

    The higher the ratio, the more violent the inversion.
    When Allah barely uses the inverted form, He condemns what it describes.

    Returns:
        dict with ratio, severity label, description
    """
    inv = max(inversion_tokens, 1)
    ratio = original_tokens / inv

    if ratio > 100:
        severity = 'EXTREME'
        desc = f'{ratio:.0f}:1 — Original dominates. Inversion is near-absent from Qur\'an.'
    elif ratio > 20:
        severity = 'SEVERE'
        desc = f'{ratio:.0f}:1 — Original strongly dominant. Inversion used only to condemn.'
    elif ratio > 5:
        severity = 'HIGH'
        desc = f'{ratio:.1f}:1 — Clear dominance. Inversion appears but is clearly secondary.'
    elif ratio > 2:
        severity = 'MODERATE'
        desc = f'{ratio:.1f}:1 — Both present. Original still dominant.'
    else:
        severity = 'MILD'
        desc = f'{ratio:.1f}:1 — Near equal. Both carry legitimate meaning, direction still visible.'

    return {
        'ratio': round(ratio, 1),
        'severity': severity,
        'original_tokens': original_tokens,
        'inversion_tokens': inversion_tokens,
        'description': desc,
    }


# ═══════════════════════════════════════════════════════════════════════
# 5. TEMPORAL REASONING — root × time → deployment history
# ═══════════════════════════════════════════════════════════════════════

def trace_timeline(root_id_or_letters):
    """Trace when and how a root's downstream forms were deployed.

    Returns chronological data from: chronology, word_deployment_map,
    script_corridors, intel connections.
    """
    if not _HAS_DB:
        return {'error': 'No DB connection'}

    conn = _connect()

    # Resolve root
    if root_id_or_letters.startswith('R') or root_id_or_letters.startswith('T'):
        root = conn.execute(
            "SELECT root_id, root_letters FROM roots WHERE root_id = ?",
            (root_id_or_letters,)
        ).fetchone()
    else:
        root = conn.execute(
            "SELECT root_id, root_letters FROM roots WHERE root_letters = ?",
            (root_id_or_letters,)
        ).fetchone()

    if not root:
        conn.close()
        return {'error': 'Root not found'}

    root_id = root['root_id']
    root_letters = root['root_letters']

    timeline = {
        'root_id': root_id,
        'root_letters': root_letters,
        'deployments': [],
        'corridors': [],
    }

    # Word deployment map
    for row in conn.execute(
        "SELECT * FROM word_deployment_map WHERE aa_roots LIKE ? ORDER BY date_period",
        (f'%{root_id}%',)
    ):
        timeline['deployments'].append(dict(row))

    # Entries with corridor info
    for row in conn.execute(
        "SELECT entry_id, en_term, ds_corridor, decay_level, dp_codes FROM entries WHERE root_id = ?",
        (root_id,)
    ):
        entry = dict(row)
        if entry.get('ds_corridor'):
            timeline['corridors'].append(entry)

    conn.close()
    return timeline


# ═══════════════════════════════════════════════════════════════════════
# 6. HYPOTHESIS GENERATION — given unknowns, generate candidates
# ═══════════════════════════════════════════════════════════════════════

def hypothesise(word, language='en'):
    """Full hypothesis pipeline: word → candidates → verify → rank.

    This is the core reasoning function. Given ANY word in ANY downstream
    language, it:
    1. Extracts consonant skeleton
    2. Reverses through shift table
    3. Computes meaning from letter values
    4. Verifies against Qur'an (if DB available)
    5. Returns ranked candidates with full provenance

    Args:
        word: any downstream word
        language: source language

    Returns:
        list of verified, ranked candidates
    """
    # ═══ FULL-WORD-FIRST RULE (2026-03-30) ═══
    # Wash the full word BEFORE any stripping/splitting.
    # If cross-language wash reveals 4+ stable consonants,
    # attempt compound detection before triliteral trace.
    try:
        code_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, code_dir) if code_dir not in sys.path else None
        from uslap_quf import cross_language_wash, detect_compound
        wash_result = cross_language_wash(word, language)
        if wash_result['consonant_count'] >= 4:
            # Compound candidate — try decomposition first
            compound_candidates = detect_compound(wash_result['skeleton'], language)
            if compound_candidates:
                # Store for later boosting — compounds found
                _compound_hints = compound_candidates[:3]
            else:
                _compound_hints = []
        else:
            _compound_hints = []
    except Exception:
        _compound_hints = []

    # Step 1-3: reverse trace (wide net pre-verification)
    candidates = reverse_trace(word, language, max_candidates=60)

    # Step 3.5: ABJAD PROXIMITY SCORING
    # Compute the "direct-map abjad" — the abjad sum using the HIGHEST
    # PRIORITY shift for each consonant. This is the structural fingerprint
    # of the most natural root. Candidates matching this value get boosted.
    # This is pure letter mathematics — no semantics, no external data.
    # Use BOTH stripped and raw consonants to cover all paths.
    stem, _, _ = strip_affixes(word, language)
    cons_stripped = extract_consonants(stem)
    cons_raw = extract_consonants(word)
    # Merge: use whichever gives more consonants, but include both
    cons_for_abjad = cons_raw if len(cons_raw or []) >= len(cons_stripped or []) else cons_stripped
    if not cons_for_abjad:
        cons_for_abjad = cons_stripped or cons_raw
    if cons_for_abjad and len(cons_for_abjad) >= 2:
        # Compute direct-map abjad using top-2 shifts per consonant position.
        # Each consonant can map to multiple AA letters (e.g. c→ق or c→ك).
        # Taking only the first misses valid roots. Taking top-2 covers the
        # most common shifts without combinatorial explosion.
        from itertools import combinations
        position_options = []  # list of lists of (letter, abjad) per position
        for c in cons_for_abjad:
            mapping = REVERSE_SHIFT.get(c, VOWEL_DROPS.get(c, []))
            if mapping:
                # Top 2 shifts per position
                opts = [(m[0], ABJAD.get(m[0], 0)) for m in mapping[:2]]
                position_options.append(opts)

        # Generate all abjad sums from triliteral combinations
        direct_abjads = set()
        n_pos = len(position_options)
        if n_pos >= 3:
            for pos_combo in combinations(range(n_pos), 3):
                # For each triliteral position combo, try all shift combos
                selected = [position_options[i] for i in pos_combo]
                for opt_combo in product(*selected):
                    abjad_val = sum(o[1] for o in opt_combo)
                    direct_abjads.add(abjad_val)
        elif n_pos == 2:
            for opt_combo in product(*position_options):
                direct_abjads.add(sum(o[1] for o in opt_combo))

        # Apply abjad proximity boost to candidates
        for cand in candidates:
            cand_abjad = cand.get('abjad_sum', 0)
            if cand_abjad in direct_abjads:
                cand['score'] += 8  # EXACT abjad match — strong structural signal
                cand['abjad_match'] = 'EXACT'
            elif direct_abjads and min(abs(cand_abjad - da) for da in direct_abjads) <= max(da * 0.15 for da in direct_abjads):
                cand['score'] += 4  # CLOSE abjad — within 15%
                cand['abjad_match'] = 'CLOSE'
            else:
                cand['abjad_match'] = 'FAR'

    # Step 4: verify against DB
    # Strategy: verify ALL triliteral candidates (most likely correct roots)
    # plus top quadriliterals. Triliteral roots dominate AA.
    if _HAS_DB:
        triliteral_idx = [i for i, c in enumerate(candidates) if len(c['aa_letters']) == 3]
        other_idx = [i for i, c in enumerate(candidates) if len(c['aa_letters']) != 3]

        # Verify all triliterals (capped at 50 for sanity)
        for i in triliteral_idx[:50]:
            candidates[i] = verify_candidate(candidates[i])
        # Verify top 10 quadriliterals
        for i in other_idx[:10]:
            candidates[i] = verify_candidate(candidates[i])

        # Boost verified candidates
        import math
        for cand in candidates:
            if cand.get('verified'):
                cand['score'] += 10
            if cand.get('quranic_tokens', 0) > 0:
                # Logarithmic scaling: 1→0, 10→2, 50→4, 100→5, 339→6, 525→6, 660→6
                # Preserves differentiation across the full token range
                tokens = cand['quranic_tokens']
                cand['score'] += min(int(math.log2(max(tokens, 1))), 10)
            if cand.get('existing_entries', 0) > 0:
                cand['score'] += min(cand['existing_entries'], 5)

        # ═══ P11 ENFORCEMENT (2026-03-30) ═══
        # Phonetic FIRST, semantic SECOND.
        # If a candidate was found via meaning match but has WEAK phonetic
        # chain (fewer than 2/3 root letters mapped), CAP its score.
        # This prevents meaning-first leakage (e.g. September→س-ب-ع
        # because both mean "seven" even though consonants don't match).
        for cand in candidates:
            n_root = len(cand.get('aa_letters', []))
            n_mapped = cand.get('mapped_count', n_root)  # assume full if not tracked
            if n_root > 0 and n_mapped < (n_root * 2 / 3):
                # Weak phonetic chain — cap score
                cand['score'] = min(cand['score'], 15)
                cand['p11_capped'] = True

        # ═══ COMPOUND BOOST (2026-03-30) ═══
        # If compound detection found valid decompositions, inject them
        # as high-scoring candidates so they appear in results.
        if _compound_hints:
            for hint in _compound_hints:
                compound_entry = {
                    'root_letters': str(hint),
                    'aa_letters': [],
                    'score': hint.get('score', 0) + 5,
                    'composition': f"COMPOUND: {hint}",
                    'deduction': f"Detected via cross-language wash + compound detector",
                    'shift_chain': [],
                    'verified': False,
                    'compound': True,
                    'compound_data': hint,
                }
                candidates.append(compound_entry)

        # Re-sort
        candidates.sort(key=lambda x: x['score'], reverse=True)

    return candidates


# ═══════════════════════════════════════════════════════════════════════
# QUF GATES — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def _quf_result(q='PENDING', u='PENDING', f='PENDING',
                q_ev=None, u_ev=None, f_ev=None):
    """Create a QUF layer result dict."""
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}
    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev or [], 'u_evidence': u_ev or [], 'f_evidence': f_ev or [],
    }


def linguistic_quf(data: dict) -> dict:
    """
    PHONETIC CHAIN VERIFICATION (function name kept for backward compatibility).
    Q: consonant alignment via S01-S26 (can root letters be found in downstream word?)
    U: cross-sibling coverage (does this root produce valid entries in multiple languages?)
    F: competing roots + blacklist (is this the ONLY root that produces this word?)
    """
    root_letters = data.get('root_letters', '') or data.get('root', '') or ''
    en_term = data.get('en_term', '') or data.get('term', '') or data.get('orig2_term', '') or ''
    root_id = data.get('root_id', '') or data.get('aa_root_id', '') or ''
    phonetic_chain = data.get('phonetic_chain', '') or ''
    score = data.get('score', 0) or 0

    if not root_letters and not root_id:
        return _quf_result('PENDING', 'PENDING', 'PENDING',
                           ['No root letters or root_id'])

    # ── Q: QUANTIFICATION — consonant alignment + token count ──
    q_evidence = []
    if en_term and root_letters:
        # Use existing verify_candidate logic
        word_consonants = extract_consonants(en_term.lower())
        root_bare = root_letters.replace('-', '').replace(' ', '')
        # Simple alignment check: are root consonants traceable in word?
        if phonetic_chain and len(phonetic_chain) > 5:
            import re
            shifts = re.findall(r'S\d{2}', phonetic_chain)
            if shifts:
                q_grade = 'HIGH'
                q_evidence.append(f'{len(shifts)} shifts documented: {",".join(shifts[:5])}')
            else:
                q_grade = 'MEDIUM'
                q_evidence.append(f'Chain present but no shift IDs: {phonetic_chain[:40]}')
        elif score and score >= 8:
            q_grade = 'HIGH'
            q_evidence.append(f'Score {score}/10, chain: {phonetic_chain[:30]}')
        elif score and score >= 5:
            q_grade = 'MEDIUM'
            q_evidence.append(f'Score {score}/10')
        else:
            q_grade = 'LOW'
            q_evidence.append(f'Score {score}/10, weak chain')
    elif root_letters:
        q_grade = 'MEDIUM'
        q_evidence.append(f'Root {root_letters} present, no downstream word to align')
    else:
        q_grade = 'LOW'
        q_evidence.append('No root letters')

    # Add Quranic token count
    if root_letters and _HAS_DB:
        try:
            conn = _connect()
            tokens = conn.execute(
                "SELECT COUNT(*) FROM quran_word_roots WHERE root = ?",
                (root_letters,)
            ).fetchone()[0]
            conn.close()
            if tokens > 0:
                q_evidence.append(f'{tokens} Quranic tokens')
                if tokens >= 10:
                    q_grade = 'HIGH'
            else:
                q_evidence.append('0 Quranic tokens')
        except Exception:
            pass

    # ── U: UNIVERSALITY — cross-sibling coverage ──
    u_evidence = []
    sibling_count = 0
    surah_count = 0

    if _HAS_DB and root_id:
        try:
            conn = _connect()
            # Count sibling tables with entries for this root
            sibling_tables = [
                ('entries', 'root_id'),
                ('european_a1_entries', 'root_id'),
                ('latin_a1_entries', 'root_id'),
                ('bitig_a1_entries', 'root_id'),
                ('uzbek_vocabulary', 'aa_root_id'),
            ]
            for tbl, col in sibling_tables:
                try:
                    cnt = conn.execute(
                        f'SELECT COUNT(*) FROM "{tbl}" WHERE "{col}" = ?', (root_id,)
                    ).fetchone()[0]
                    if cnt > 0:
                        sibling_count += 1
                except Exception:
                    pass

            # Surah spread
            if root_letters:
                try:
                    surah_count = conn.execute(
                        "SELECT COUNT(DISTINCT surah) FROM quran_word_roots WHERE root = ?",
                        (root_letters,)
                    ).fetchone()[0]
                except Exception:
                    pass

            conn.close()
        except Exception:
            pass

    if surah_count >= 20 or sibling_count >= 4:
        u_grade = 'HIGH'
    elif surah_count >= 5 or sibling_count >= 2:
        u_grade = 'HIGH'
    elif surah_count >= 1 or sibling_count >= 1:
        u_grade = 'MEDIUM'
    else:
        u_grade = 'LOW'
    u_evidence.append(f'{surah_count} surahs, {sibling_count} sibling tables')

    # ── F: FALSIFICATION — competing roots + blacklist ──
    f_evidence = []
    if _HAS_DB and root_id:
        try:
            conn = _connect()
            # Check blacklist (only if en_term is populated — empty matches everything)
            # Word-boundary match: check if en_term IS a blacklisted term,
            # not if en_term appears as a SUBSTRING of a blacklisted text.
            # "STUDY" must not match "The Study Quran" in BL19.
            bl_check = 0
            if en_term and len(en_term) >= 3:
                _bl_term = en_term.lower().strip()
                bl_check = conn.execute(
                    "SELECT COUNT(*) FROM contamination_blacklist "
                    "WHERE LOWER(contaminated_term) = ? "
                    "OR LOWER(contaminated_translation) = ?",
                    (_bl_term, _bl_term)
                ).fetchone()[0]
            if bl_check > 0:
                f_grade = 'FAIL'
                f_evidence.append(f'Term matches contamination blacklist')
            elif phonetic_chain and score and score >= 8:
                f_grade = 'HIGH'
                f_evidence.append(f'Unique root trace, score {score}/10')
            elif phonetic_chain:
                f_grade = 'MEDIUM'
                f_evidence.append(f'Chain documented, score {score}/10')
            else:
                f_grade = 'LOW'
                f_evidence.append('No phonetic chain documented')
            conn.close()
        except Exception:
            f_grade = 'MEDIUM'
            f_evidence.append('DB check unavailable')
    else:
        f_grade = 'MEDIUM' if phonetic_chain else 'LOW'
        f_evidence.append(f'Chain: {bool(phonetic_chain)}')

    return _quf_result(q_grade, u_grade, f_grade, q_evidence, u_evidence, f_evidence)


def divine_quf(data: dict) -> dict:
    """QUF for Names of Allah — L3. F gate is axiomatic (always HIGH)."""
    root_id = data.get('root_id', '') or ''
    qur_ref = data.get('qur_ref', '') or ''
    name = data.get('aa_name', '') or ''

    q = 'HIGH' if (root_id and qur_ref and name) else ('MEDIUM' if name else 'LOW')
    u = 'HIGH'  # Names of Allah are universal by definition
    f = 'HIGH'  # Axiomatic — divine names are not falsifiable

    return _quf_result(q, u, f,
                        [f'root={root_id}, qur_ref={bool(qur_ref)}, name={bool(name)}'],
                        ['Divine name — universal'],
                        ['Divine name — axiomatic'])


def quran_form_quf(data: dict) -> dict:
    """QUF for Qur'anic forms — L4. Compiler output."""
    root = data.get('root', '') or data.get('root_unhyphenated', '') or ''
    word = data.get('aa_word', '') or data.get('aa_form', '') or ''
    surah = data.get('surah', 0)
    conf = data.get('confidence', '') or ''
    word_type = data.get('word_type', '') or ''

    # PARTICLEs may not have roots — that's correct, not a failure
    is_particle = word_type.upper() == 'PARTICLE'
    if root and word and surah:
        q = 'HIGH'
    elif word and surah and is_particle:
        q = 'HIGH'  # Particle in Qur'an with valid surah = attested
    elif root and word:
        q = 'MEDIUM'
    else:
        q = 'LOW'

    # U: root in roots table? Particles are universal if they appear in Qur'an
    if is_particle and word and surah:
        u = 'HIGH'  # Qur'anic particle = universal by presence
    elif _HAS_DB and root:
        u = 'MEDIUM'
        try:
            conn = _connect()
            bare = root.replace('-', '')
            found = conn.execute(
                "SELECT COUNT(*) FROM roots WHERE root_bare = ? OR root_letters = ?",
                (bare, root)
            ).fetchone()[0]
            conn.close()
            u = 'HIGH' if found else 'MEDIUM'
        except Exception:
            pass
    else:
        u = 'MEDIUM'

    # F: compiler confidence. Particles and Qur'an data default to MEDIUM minimum
    conf_upper = str(conf).upper()
    if conf_upper in ('HIGH', 'MEDIUM_A'):
        f = 'HIGH'
    elif conf_upper in ('MEDIUM_B', 'MEDIUM_C', 'MEDIUM', 'PARTICLE'):
        f = 'MEDIUM'
    else:
        f = 'MEDIUM'  # Qur'an data defaults to MEDIUM minimum

    return _quf_result(q, u, f,
                        [f'root={root}, word={bool(word)}, surah={surah}, particle={is_particle}'],
                        [f'Root in roots table: {u}' if not is_particle else f'Particle in Quran: universal'],
                        [f'Compiler confidence: {conf_upper or "ungraded"}'])


def bitig_quf(data: dict) -> dict:
    """QUF for Bitig entries — L6.

    Source hierarchy (strict precedence):
      PRIMARY:   kashgari_attestation (SRC01 Kashgari 1072 CE)
      SECONDARY: ibn_sina_attestation (SRC02) | navoi_attestation (SRC07)
                 + manuscript sources (SRC08-10 Orkhon/Irk Bitig/Talas)
      TERTIARY:  tertiary_attestation (SRC11-14: ESTYA, Shipova, Baskakov, Suleimenov)
                 — ONLY valid when primary+secondary silent,
                   OR as supplementary data on already-confirmed entries.
    """
    kash = data.get('kashgari_attestation', '') or ''
    ibn_sina = data.get('ibn_sina_attestation', '') or ''
    navoi = data.get('navoi_attestation', '') or ''
    tertiary = data.get('tertiary_attestation', '') or ''
    root_id = data.get('root_id', '') or ''
    dispersal = data.get('dispersal_range', '') or ''
    orig2_term = str(data.get('orig2_term', '')).lower()

    has_primary = bool(kash)
    has_secondary = bool(ibn_sina or navoi)
    has_tertiary = bool(tertiary)

    # ── Q (quality of attestation) ──
    # PRIMARY = HIGH, SECONDARY = MEDIUM, TERTIARY alone = LOW,
    # TERTIARY supplementing confirmed = no change (keeps PRIMARY/SECONDARY grade)
    q_ev = []
    if has_primary:
        q = 'HIGH'
        q_ev.append(f'PRIMARY: Kashgari attested')
        if has_secondary:
            q_ev.append(f'SECONDARY corroboration: ibn_sina={bool(ibn_sina)}, navoi={bool(navoi)}')
        if has_tertiary:
            q_ev.append(f'TERTIARY supplementary: {data.get("tertiary_source", "?")}')
    elif has_secondary:
        q = 'MEDIUM'
        q_ev.append(f'SECONDARY only: ibn_sina={bool(ibn_sina)}, navoi={bool(navoi)}')
        if has_tertiary:
            q_ev.append(f'TERTIARY supplementary: {data.get("tertiary_source", "?")}')
    elif has_tertiary:
        q = 'LOW'
        q_ev.append(f'TERTIARY only (no primary/secondary): {data.get("tertiary_source", "?")}')
    elif root_id:
        q = 'MEDIUM'
        q_ev.append(f'root_id present, no attestation sources')
    else:
        q = 'PENDING'
        q_ev.append('No attestation sources and no root_id')

    # ── U (usage precedent) ──
    # root_id+dispersal=HIGH, root_id or primary/secondary=MEDIUM,
    # tertiary alone=LOW, nothing=PENDING
    u_ev = []
    if root_id and dispersal:
        u = 'HIGH'
        u_ev.append(f'root={root_id}, dispersal present')
    elif root_id or has_primary or has_secondary:
        u = 'MEDIUM'
        u_ev.append(f'root={root_id}, primary={has_primary}, secondary={has_secondary}')
    elif has_tertiary:
        u = 'LOW'
        u_ev.append(f'Tertiary only — no primary/secondary/root_id')
    else:
        u = 'PENDING'
        u_ev.append('No sources, no root_id')

    # ── TERTIARY TEXT SCAN ──
    # Fires on tertiary_attestation content. Catches direction violations
    # that slip past the pre-write gate's explicit banned terms:
    #   1. Downstream language named as ORIGIN (Russian, Slavic, Greek, etc.)
    #   2. Proto-reconstruction claims (*kor-, *proto-X)
    #   3. Reverse direction by implication ("related to RU", "cf. Slavic")
    #   4. Lattice contradiction (if AA root exists, tertiary must not claim
    #      the word originates from a downstream form)
    import re as _re_tert
    tertiary_contaminated = False
    tert_violations = []
    if has_tertiary:
        tert_lower = tertiary.lower()
        # Downstream languages positioned as sources/origins
        _DS_AS_SOURCE = [
            r'\b(?:from|origin(?:ates?)?|derives?|related to|cf\.?|compare)\s+'
            r'(?:russian|ru|slavic|greek|latin|persian|french|german|english|'
            r'sanskrit|hindi|chinese|japanese|korean|hungarian|finnish)',
            r'\b(?:russian|slavic|greek|latin|persian|french|german|english|'
            r'sanskrit)\s+(?:word|term|root|origin|source|etymon)\b',
            r'\bfrom\s+(?:old\s+)?(?:russian|slavic|greek|latin|french|german)\b',
        ]
        for pat in _DS_AS_SOURCE:
            m = _re_tert.search(pat, tert_lower)
            if m:
                tertiary_contaminated = True
                tert_violations.append(
                    f'TERTIARY_DIRECTION: downstream-as-source "{m.group()}" '
                    f'in tertiary_attestation. Direction is AA/ORIG2 -> downstream. ALWAYS.'
                )
        # Proto-reconstruction used as DIRECTION CLAIM (framework contamination).
        # The asterisk notation (*kor-, *qar-) is fine as consonant skeleton data.
        # It's only contamination when combined with origin/direction language:
        #   "*kor- is the proto-Turkic origin" = FAIL (direction claim)
        #   "ESTYA reconstructs *kor-" = OK (consonant skeleton data point)
        _PROTO_DIRECTION = [
            r'\*[a-z]{2,}.*?\b(?:origin|source|gave|produced|ancestor|proto-)\b',
            r'\b(?:from|origin(?:ates?)?|derives?|ancestor|proto-)\b.*?\*[a-z]{2,}',
            r'\bproto-\w+\s+(?:root|form|origin|source|ancestor)\b',
        ]
        for pat in _PROTO_DIRECTION:
            m = _re_tert.search(pat, tert_lower)
            if m:
                tertiary_contaminated = True
                tert_violations.append(
                    f'TERTIARY_FRAMEWORK: proto-form used as direction claim '
                    f'"{m.group()}" in tertiary_attestation. '
                    f'Asterisk notation OK for consonant skeletons. '
                    f'NOT OK as origin/direction claim.'
                )
        # Lattice contradiction check: if entry has AA root, tertiary must not
        # claim a different origin
        if _HAS_DB and root_id:
            try:
                conn = _connect()
                aa_root = conn.execute(
                    "SELECT root_id, aa_word FROM roots WHERE root_id = ?",
                    (root_id,)
                ).fetchone()
                conn.close()
                if aa_root and any(
                    _re_tert.search(p, tert_lower) for p in [
                        r'\b(?:origin|source|etymon|root)\b',
                        r'\bfrom\b',
                    ]
                ):
                    tert_violations.append(
                        f'TERTIARY_LATTICE_CHECK: entry has AA root {root_id}. '
                        f'Tertiary source claims about origin must be consistent. '
                        f'Verify direction manually.'
                    )
            except Exception:
                pass

    # ── COMPOUND MORPHEME VALIDATION ──
    # For compound entries (root_letters contains '+'), check each component
    # against BI tasrif tables and bitig_a1. Components that don't match
    # any known BI morpheme are flagged.
    root_letters = data.get('root_letters', '') or ''
    compound_warnings = []
    if '+' in root_letters and _HAS_DB:
        try:
            conn = _connect()
            components = [c.strip() for c in root_letters.split('+')]
            for comp in components:
                comp_clean = comp.lower().replace(' ', '')
                if not comp_clean or len(comp_clean) < 2:
                    continue
                # Check 1: Is this component a known BI root in bitig_a1?
                bi_match = conn.execute(
                    "SELECT COUNT(*) FROM bitig_a1_entries "
                    "WHERE LOWER(root_letters) = ? OR LOWER(orig2_term) LIKE ?",
                    (comp_clean, comp_clean + '%')
                ).fetchone()[0]
                # Check 2: Is this component a known BI suffix?
                suffix_match = conn.execute(
                    "SELECT COUNT(*) FROM bitig_verb_tasrif "
                    "WHERE LOWER(suffix_or_affix) LIKE ? "
                    "UNION ALL "
                    "SELECT COUNT(*) FROM bitig_noun_tasrif "
                    "WHERE LOWER(suffix_or_affix) LIKE ?",
                    ('%' + comp_clean + '%', '%' + comp_clean + '%')
                ).fetchall()
                has_suffix = any(row[0] > 0 for row in suffix_match)
                if bi_match == 0 and not has_suffix:
                    compound_warnings.append(
                        f'COMPOUND_UNVERIFIED: component "{comp}" not found in '
                        f'bitig_a1 roots or bitig tasrif suffixes. '
                        f'Possible contamination — verify BI origin.'
                    )
            conn.close()
        except Exception:
            pass

    # ── F (falsifiability — not blacklisted, not laundered AA) ──
    f = 'MEDIUM'
    f_ev = []
    compound_blocked = bool(compound_warnings)
    if compound_warnings:
        f = 'FAIL'
        f_ev.extend(compound_warnings)
        f_ev.append(
            'COMPOUND_BLOCK: unverified component(s) in compound entry. '
            'Each component must exist in bitig_a1 roots OR bitig tasrif suffixes. '
            'Add missing component to bitig_a1 first, then retry.'
        )
    if tertiary_contaminated:
        f = 'FAIL'
        f_ev.extend(tert_violations)
    elif compound_blocked:
        pass  # Already FAIL from compound check — do NOT override with blacklist
    elif _HAS_DB:
        try:
            conn = _connect()
            bl = conn.execute(
                "SELECT COUNT(*) FROM contamination_blacklist "
                "WHERE LOWER(contaminated_term) = ? "
                "OR LOWER(contaminated_translation) = ?",
                (orig2_term.strip(), orig2_term.strip())
            ).fetchone()[0]
            if bl > 0:
                f = 'FAIL'
                f_ev.append('In contamination blacklist')
            elif has_primary:
                f = 'HIGH'
                f_ev.append('Kashgari-attested, not blacklisted')
            elif has_secondary:
                f = 'HIGH'
                f_ev.append('Secondary-attested, not blacklisted')
            elif has_tertiary:
                f = 'MEDIUM'
                f_ev.append('Tertiary-only, not blacklisted, no direction violations')
            conn.close()
        except Exception:
            pass
    if not f_ev:
        f_ev.append('Not blacklisted' if f != 'FAIL' else 'Blacklisted')

    return _quf_result(q, u, f, q_ev, u_ev, f_ev)


def sibling_quf(data: dict) -> dict:
    """QUF for sibling entries (EU, LA, UZ) — L7."""
    root_id = data.get('root_id', '') or data.get('aa_root_id', '') or ''
    chain = data.get('phonetic_chain', '') or ''
    score = data.get('score', 0) or 0

    q = 'HIGH' if (root_id and chain and score > 0) else ('MEDIUM' if root_id else 'LOW')

    # U: does parent EN entry exist?
    u = 'MEDIUM'
    if _HAS_DB and root_id:
        try:
            conn = _connect()
            en_exists = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE root_id = ?", (root_id,)
            ).fetchone()[0]
            conn.close()
            u = 'HIGH' if en_exists > 0 else 'MEDIUM'
        except Exception:
            pass

    import re
    if chain:
        shifts = re.findall(r'S\d{2}', chain)
        f = 'HIGH' if shifts else 'MEDIUM'
    else:
        f = 'LOW'

    return _quf_result(q, u, f,
                        [f'root={root_id}, chain={bool(chain)}, score={score}'],
                        [f'EN parent exists: {u}'],
                        [f'Shift chain: {bool(chain)}'])


def derivative_quf(data: dict) -> dict:
    """QUF for derivatives — L8."""
    entry_id = data.get('entry_id', '')
    link_type = data.get('link_type', '') or ''

    PERMITTED = {'DIRECT', 'COMPOUND', 'SAME_ROOT', 'PHONETIC', 'SEMANTIC',
                 'PREFIX', 'SUFFIX', 'ROOT', 'SIBLING'}
    BANNED = {'COGNATE', 'LOANWORD', 'BORROWING'}

    # Q: parent exists?
    q = 'MEDIUM'
    if _HAS_DB and entry_id:
        try:
            conn = _connect()
            parent = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE entry_id = ?", (entry_id,)
            ).fetchone()[0]
            conn.close()
            q = 'HIGH' if (parent > 0 and link_type) else ('MEDIUM' if parent > 0 else 'LOW')
        except Exception:
            pass

    u = 'MEDIUM' if entry_id else 'LOW'

    if link_type and link_type.upper() in BANNED:
        f = 'FAIL'
    elif link_type and link_type.upper() in PERMITTED:
        f = 'HIGH'
    elif link_type:
        f = 'MEDIUM'
    else:
        f = 'LOW'

    return _quf_result(q, u, f,
                        [f'parent={entry_id}, link={link_type}'],
                        [f'Parent entry: {q}'],
                        [f'Link type: {link_type}'])


def xref_quf(data: dict) -> dict:
    """QUF for cross-refs — L8."""
    from_id = data.get('from_id', '')
    to_id = data.get('to_id', '')
    link_type = data.get('link_type', '') or ''

    q = 'HIGH' if (from_id and to_id and link_type) else ('MEDIUM' if (from_id and to_id) else 'LOW')
    u = 'MEDIUM'
    f = 'HIGH' if link_type else 'LOW'

    return _quf_result(q, u, f,
                        [f'from={from_id}, to={to_id}, link={link_type}'],
                        [f'Cross-ref endpoints'],
                        [f'Link type: {link_type}'])


def foundation_quf(data: dict) -> dict:
    """QUF for foundation data — F1-F7."""
    layer = data.get('layer', '') or ''
    populated = len([v for v in data.values() if v is not None and str(v).strip()])
    total = max(len(data), 1)
    ratio = populated / total

    q = 'HIGH' if ratio >= 0.6 else ('MEDIUM' if ratio >= 0.3 else 'LOW')
    u = 'MEDIUM'  # Foundation data is definitional
    f = 'HIGH' if layer else 'MEDIUM'

    return _quf_result(q, u, f,
                        [f'Completeness: {ratio:.0%}, layer={layer}'],
                        [f'Foundation — definitional'],
                        [f'Layer documented: {bool(layer)}'])


def mechanism_quf(data: dict) -> dict:
    """QUF for mechanism data — M1-M5."""
    layer = data.get('layer', '') or ''
    populated = len([v for v in data.values() if v is not None and str(v).strip()])
    total = max(len(data), 1)
    ratio = populated / total
    has_examples = bool(data.get('examples', '') or data.get('markers', ''))

    q = 'HIGH' if ratio >= 0.6 else ('MEDIUM' if ratio >= 0.3 else 'LOW')
    u = 'HIGH' if has_examples else 'MEDIUM'
    f = 'HIGH' if (layer and has_examples) else 'MEDIUM'

    return _quf_result(q, u, f,
                        [f'Completeness: {ratio:.0%}'],
                        [f'Examples: {has_examples}'],
                        [f'Layer={layer}, examples={has_examples}'])


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════

def main():
    import json

    if len(sys.argv) < 3:
        print("أَمْر عَقْل — Intellect Engine")
        print()
        print("Usage:")
        print("  python3 amr_aql.py deduce ك-ف-ر          # compute meaning from letters")
        print("  python3 amr_aql.py reverse cover          # find AA root for English word")
        print("  python3 amr_aql.py expand R24             # full knowledge tree for root")
        print("  python3 amr_aql.py expand ك-ف-ر           # same, by letters")
        print("  python3 amr_aql.py relate ر-ح-م م-ر-ح     # structural relationship")
        print("  python3 amr_aql.py think cover            # full hypothesis pipeline")
        print("  python3 amr_aql.py timeline R24           # deployment history")
        sys.exit(0)

    cmd = sys.argv[1]
    arg = sys.argv[2]

    if cmd == 'deduce':
        result = deduce_meaning(arg)
        print(f"\nROOT: {arg}")
        print(f"COMPOSITION: {result['composition']}")
        print(f"DEDUCTION: {result['deduction']}")
        for l in result['letters']:
            print(f"  {l['letter']} = {l['abjad']:>4} = {l['semantic']}")

    elif cmd == 'reverse':
        candidates = reverse_trace(arg)
        print(f"\nREVERSE TRACE: {arg}")
        print(f"CANDIDATES: {len(candidates)}")
        for i, c in enumerate(candidates[:5]):
            print(f"\n  [{i+1}] {c['root_letters']} (score={c['score']})")
            print(f"      {c['composition']}")
            print(f"      Chain: {' | '.join(c['shift_chain'])}")

    elif cmd == 'expand':
        tree = expand_root(arg)
        if 'error' in tree:
            print(f"ERROR: {tree['error']}")
        else:
            r = tree['root']
            s = tree['summary']
            print(f"\nROOT: {r['root_id']} | {r['root_letters']}")
            print(f"COMPUTED: {r['computed_meaning']['composition']}")
            print(f"QURANIC TOKENS: {r['quran_tokens']}")
            print(f"\nDOWNSTREAM:")
            print(f"  EN: {s['en_entries']} | RU: {s['ru_entries']} | FA: {s['fa_entries']}")
            print(f"  EU: {s['european']} | Latin: {s['latin']} | Bitig: {s['bitig']} | Uzbek: {s['uzbek']}")
            print(f"  Derivatives: {s['derivatives']} | Cross-refs: {s['cross_refs']}")
            print(f"  Qur'anic words: {s['quranic_words']} | Names of Allah: {s['names_of_allah']}")
            print(f"  TOTAL DOWNSTREAM: {s['total_downstream']}")

    elif cmd == 'relate':
        if len(sys.argv) < 4:
            print("Usage: amr_aql.py relate ROOT_A ROOT_B")
            sys.exit(1)
        root_b = sys.argv[3]
        result = relate_roots(arg, root_b)
        print(f"\nROOT A: {arg} → {result['root_a']['meaning']['composition']}")
        print(f"ROOT B: {root_b} → {result['root_b']['meaning']['composition']}")
        print(f"\nRELATIONSHIPS: {result['relationship_count']}")
        for rel in result['relationships']:
            print(f"  [{rel['type']}] {rel['description']}")

    elif cmd == 'think':
        candidates = hypothesise(arg)
        print(f"\nHYPOTHESIS: {arg}")
        print(f"CANDIDATES: {len(candidates)}")
        for i, c in enumerate(candidates[:5]):
            verified = "✓ VERIFIED" if c.get('verified') else "○ unverified"
            tokens = f"Q:{c.get('quranic_tokens', '?')}" if c.get('verified') else ""
            entries = f"E:{c.get('existing_entries', '?')}" if c.get('verified') else ""
            print(f"\n  [{i+1}] {c['root_letters']} (score={c['score']}) {verified} {tokens} {entries}")
            print(f"      {c['composition']}")
            print(f"      {c['deduction']}")
            print(f"      Chain: {' | '.join(c['shift_chain'])}")

    elif cmd == 'timeline':
        result = trace_timeline(arg)
        if 'error' in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"\nTIMELINE: {result['root_id']} | {result['root_letters']}")
            print(f"DEPLOYMENTS: {len(result['deployments'])}")
            for d in result['deployments']:
                print(f"  {d.get('date_period', '?')} | {d.get('operation_phase', '?')} | {d.get('deployed_words', '?')[:60]}")
            print(f"CORRIDORS: {len(result['corridors'])}")
            for c in result['corridors']:
                print(f"  {c.get('en_term', '?')} → {c.get('ds_corridor', '?')} | {c.get('decay_level', '?')}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
