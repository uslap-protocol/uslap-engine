#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر QUF — QUANTIFICATION · UNIVERSALITY · FALSIFICATION

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

The QUF gate. Every piece of data passes three tests:
  Q — Quantification: how much countable evidence?
  U — Universality: does it hold across ALL instances?
  F — Falsification: what would disprove it?

QUF lives in AMR AI, NOT in the schema.
The schema stores grades. AMR modules compute them.
This file is the thin router that calls the right module.

Works in BOTH directions:
  - Reading/gathering: validate existing data
  - Writing/adding: validate before write

Each domain module owns its QUF logic:
  amr_aql        → linguistic_quf (L0, L1, L5, L6, L7, L8)
  amr_istakhbarat → behaviour_quf (L13)
  amr_hisab      → formula_quf (L11)
  amr_jism       → body_quf (L10)
  amr_tarikh     → history_quf (L12)
  amr_basar      → detection_quf (L9)
  amr_keywords   → keyword_quf (L2)
  amr_nutq       → quran_quf (L3, L4)
"""

import sys
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")

# Grade hierarchy
GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}
PASS_THRESHOLD = 3  # MEDIUM or above


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.utcnow().isoformat()


def _min_grade(grades: List[str]) -> str:
    """Return the minimum grade from a list."""
    if not grades:
        return 'PENDING'
    return min(grades, key=lambda g: GRADE_ORDER.get(g, 0))


def _grade_passes(grade: str) -> bool:
    return GRADE_ORDER.get(grade, 0) >= PASS_THRESHOLD


# ═══════════════════════════════════════════════════════════════════════
# LAYER RESULT
# ═══════════════════════════════════════════════════════════════════════

def make_result(q='PENDING', u='PENDING', f='PENDING',
                q_evidence=None, u_evidence=None, f_evidence=None) -> Dict:
    """Create a QUF layer result."""
    passes = all(_grade_passes(g) for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f,
        'pass': passes,
        'q_evidence': q_evidence or [],
        'u_evidence': u_evidence or [],
        'f_evidence': f_evidence or [],
    }


# ═══════════════════════════════════════════════════════════════════════
# LAYER 0: LETTER ALIGNMENT GATE (fires BEFORE all other layers)
# ═══════════════════════════════════════════════════════════════════════
# Every meaning stored in the DB must align with what the 28 letters compute.
# If aa_word/orig_meaning contains a dictionary definition that contradicts
# compute_root_meaning(), the entry is BLOCKED.
#
# Added 2026-03-29 after ق-ر-ش contamination discovery:
#   child_schema said "to gather, to amass" (dictionary)
#   Letters compute SPEECH+MOVEMENT+SPREADING
#   2,107 entries flagged by uslap_root_audit.py
# ═══════════════════════════════════════════════════════════════════════

# Dictionary verb patterns that indicate meaning came from a lexicon, not letters
_DICT_VERB_PATTERNS = [
    'to gather', 'to collect', 'to press', 'to cut', 'to strike',
    'to pull', 'to push', 'to take', 'to give', 'to make',
    'to put', 'to throw', 'to draw', 'to hold', 'to carry',
    'to bring', 'to send', 'to come', 'to go', 'to turn',
    'to stand', 'to sit', 'to lie', 'to fall', 'to rise',
    'to open', 'to close', 'to break', 'to bend', 'to twist',
    'to tie', 'to bind', 'to join', 'to split', 'to mix',
    'to cover', 'to fill', 'to pour', 'to flow', 'to blow',
    'to burn', 'to shine', 'to grow', 'to eat', 'to drink',
]


def letter_alignment_quf(data: Dict) -> Dict:
    """
    Layer 0: Letter Alignment Gate.

    Checks that the stored meaning aligns with compute_root_meaning().
    If the meaning contains dictionary patterns that don't match the
    letter computation, it FAILS.

    Q — Does stored meaning contain letter computation concepts?
    U — Is the meaning consistent with ALL letter positions?
    F — Does the meaning contain dictionary contamination markers?
    """
    root_letters = (data.get('root_letters', '') or
                    data.get('orig_root', '') or
                    data.get('root', '') or '')

    if not root_letters or '-' not in root_letters:
        return make_result('PENDING', 'PENDING', 'PENDING',
                           ['No root_letters — letter alignment skipped'])

    # Get the meaning field to check
    meaning = (data.get('aa_word', '') or
               data.get('orig_meaning', '') or
               data.get('primary_meaning', '') or '')

    if not meaning:
        return make_result('PENDING', 'PENDING', 'PENDING',
                           ['No meaning field — letter alignment skipped'])

    # If meaning already contains letter computation format, it's aligned
    if '=SPEECH' in meaning or '=MOVEMENT' in meaning or '=ORIGIN' in meaning or \
       '=BUILDING' in meaning or '=TRUTH' in meaning or '=CREATION' in meaning or \
       '=ENCLOSURE' in meaning or '=CONNECTION' in meaning or '=BREATH' in meaning:
        return make_result('HIGH', 'HIGH', 'HIGH',
                           ['Meaning already contains letter computation'])

    # Compute what the letters say
    try:
        from amr_alphabet import compute_root_meaning
        computation = compute_root_meaning(root_letters)
        if not computation:
            return make_result('PENDING', 'PENDING', 'PENDING',
                               [f'compute_root_meaning returned None for {root_letters}'])
    except Exception as e:
        return make_result('PENDING', 'PENDING', 'PENDING',
                           [f'compute_root_meaning error: {e}'])

    semantic_core = computation.get('semantic_core', '')
    core_parts = [p.strip().lower() for p in semantic_core.split('+') if p.strip()]

    q_evidence = []
    u_evidence = []
    f_evidence = []

    meaning_lower = meaning.lower()

    # Q: Does meaning contain ANY of the semantic core concepts?
    found_concepts = [p for p in core_parts if p in meaning_lower]
    if found_concepts:
        q_grade = 'HIGH'
        q_evidence.append(f'Meaning contains: {found_concepts}')
    else:
        q_grade = 'LOW'
        q_evidence.append(f'Meaning does NOT contain any of [{semantic_core}]')
        q_evidence.append(f'Stored: {meaning[:100]}')
        q_evidence.append(f'Letters compute: {semantic_core}')

    # U: Check all letter positions are consistent
    letter_data = computation.get('letters', [])
    position_matches = 0
    for letter_info in letter_data:
        core = letter_info.get('core_concept', '').lower()
        if core and core in meaning_lower:
            position_matches += 1

    if position_matches >= 2:
        u_grade = 'HIGH'
        u_evidence.append(f'{position_matches}/{len(letter_data)} letter concepts found in meaning')
    elif position_matches == 1:
        u_grade = 'MEDIUM'
        u_evidence.append(f'Only {position_matches}/{len(letter_data)} letter concepts found')
    else:
        u_grade = 'LOW'
        u_evidence.append(f'0/{len(letter_data)} letter concepts found — meaning misaligned')

    # F: Dictionary contamination check
    dict_markers_found = [m for m in _DICT_VERB_PATTERNS if m in meaning_lower]
    if dict_markers_found:
        f_grade = 'FAIL'
        f_evidence.append(f'DICTIONARY CONTAMINATION: {dict_markers_found}')
        f_evidence.append('Meaning uses dictionary verb patterns, not letter computation')
    else:
        f_grade = 'HIGH'
        f_evidence.append('No dictionary verb patterns detected')

    return make_result(q_grade, u_grade, f_grade,
                       q_evidence, u_evidence, f_evidence)


# ═══════════════════════════════════════════════════════════════════════
# SOURCE QUF (Layer 3 — runs for all domains)
# ═══════════════════════════════════════════════════════════════════════

# Approved sources (from isnad + scholar_warnings)
APPROVED_SOURCES = {
    'QURAN', 'SC03', 'SC04', 'SC06',  # Qur'an, Ibn Khordadbeh, al-Biruni, al-Qashqari
    'SC-WARN-03',  # Navoi
    'LATTICE',  # Internal lattice data
    'COMPILER',  # Qur'an compiler output
    'KASHGARI',  # Diwan Lughat al-Turk
}


def source_quf(data: Dict) -> Dict:
    """
    Layer 3: Source verification.
    Q — source documented?
    U — multiple independent sources?
    F — source exposes (not sanitises)?
    """
    sources = []
    qur_ref = (data.get('qur_ref', '') or data.get('quranic_ref', '') or
               data.get('qur_anchor', '') or data.get('qur_meaning', '') or
               data.get('ayah_refs', '') or data.get('quran_proof', '') or
               data.get('qur_primary', '') or data.get('qur_secondary', '') or
               data.get('qur_refs', '') or '')
    source = (data.get('source', '') or data.get('source_ref', '') or
              data.get('institution', '') or
              data.get('founding_instances', '') or
              data.get('kashgari_attestation', '') or
              data.get('ibn_sina_attestation', '') or '')
    dp_codes = (data.get('dp_codes', '') or data.get('confession_type', '') or
                data.get('distinct_from', '') or
                data.get('dp_always_active', '') or '')

    if qur_ref:
        sources.append('QURAN')
    if source:
        sources.append(source.upper().split()[0] if source else '')

    # Q — is the source documented?
    if 'QURAN' in sources or qur_ref:
        q = 'HIGH'
        q_ev = [f'Quranic reference: {qur_ref}']
    elif source:
        q = 'MEDIUM'
        q_ev = [f'Source: {source[:50]}']
    else:
        q = 'LOW'
        q_ev = ['No source documented']

    # U — multiple independent sources?
    source_count = len(set(sources))
    if source_count >= 3:
        u = 'HIGH'
    elif source_count >= 2 or 'QURAN' in sources:
        u = 'HIGH'  # Qur'an alone = universal
    elif source_count >= 1:
        u = 'MEDIUM'
    else:
        u = 'LOW'
    u_ev = [f'{source_count} source(s): {", ".join(sources[:5])}']

    # F — source exposes (not sanitises)?
    if 'QURAN' in sources:
        f = 'HIGH'
        f_ev = ['Quranic source — axiomatic']
    elif dp_codes:
        f = 'HIGH'
        f_ev = [f'DP codes document erasure: {dp_codes}']
    elif source:
        f = 'MEDIUM'
        f_ev = [f'Source present, DP codes not documented']
    else:
        f = 'LOW'
        f_ev = ['No source, no DP codes']

    return make_result(q, u, f, q_ev, u_ev, f_ev)


# ═══════════════════════════════════════════════════════════════════════
# DOMAIN GATE REGISTRY
# ═══════════════════════════════════════════════════════════════════════

# Maps table name → (module_name, function_name)
# Lazy-loaded to avoid circular imports
DOMAIN_GATE_MAP = {
    # L1: ROOT
    'roots': ('amr_aql', 'linguistic_quf'),
    # L2: KEYWORD
    'att_terms': ('amr_keywords', 'keyword_quf'),
    # L3: DIVINE NAMES
    'names_of_allah': ('amr_aql', 'divine_quf'),
    'name_root_hub': ('amr_aql', 'divine_quf'),
    # L4: QUR'ANIC FORMS
    'quran_word_roots': ('amr_aql', 'quran_form_quf'),
    'quran_known_forms': ('amr_aql', 'quran_form_quf'),
    'quran_ayat': ('amr_aql', 'quran_form_quf'),
    'quran_refs': ('amr_aql', 'quran_form_quf'),
    # L5: ENTRIES
    'entries': ('amr_aql', 'linguistic_quf'),
    # L6: ORIG2
    'bitig_a1_entries': ('amr_aql', 'bitig_quf'),
    # L7: SIBLINGS
    'european_a1_entries': ('amr_aql', 'sibling_quf'),
    'latin_a1_entries': ('amr_aql', 'sibling_quf'),
    'uzbek_vocabulary': ('amr_aql', 'sibling_quf'),
    # L8: DERIVATIVES
    'a4_derivatives': ('amr_aql', 'derivative_quf'),
    'a5_cross_refs': ('amr_aql', 'xref_quf'),
    # L9: DETECTION
    'qv_translation_register': ('amr_basar', 'detection_quf'),
    'disputed_words': ('amr_basar', 'detection_quf'),
    'contamination_blacklist': ('amr_basar', 'detection_quf'),
    'dp_register': ('amr_basar', 'detection_quf'),
    'phonetic_reversal': ('amr_basar', 'detection_quf'),
    # L10: BODY
    'body_data': ('amr_jism', 'body_quf'),
    'body_cross_refs_unified': ('amr_jism', 'body_xref_quf'),
    'body_prayer_map_unified': ('amr_jism', 'body_prayer_quf'),
    'body_heptad_meta': ('amr_jism', 'body_quf'),
    'body_extraction_intel': ('amr_jism', 'body_quf'),
    # L11: FORMULA
    'formula_concealment': ('amr_hisab', 'formula_quf'),
    'formula_ratios': ('amr_hisab', 'formula_quf'),
    'formula_restoration': ('amr_hisab', 'formula_quf'),
    'formula_scholars': ('amr_hisab', 'formula_quf'),
    'formula_undiscovered': ('amr_hisab', 'formula_quf'),
    'formula_cross_refs': ('amr_hisab', 'formula_xref_quf'),
    # L12: HISTORY
    'chronology': ('amr_tarikh', 'history_quf'),
    'child_entries': ('amr_tarikh', 'history_quf'),
    'word_deployment_map': ('amr_tarikh', 'history_quf'),
    # L13: INTELLIGENCE
    'isnad': ('amr_istakhbarat', 'behaviour_quf'),
    'institutional_confession_register': ('amr_istakhbarat', 'behaviour_quf'),
    'financial_extraction_cycles': ('amr_istakhbarat', 'behaviour_quf'),
    'kashgari_concealment_audit': ('amr_istakhbarat', 'behaviour_quf'),
    'intel_file_index': ('amr_istakhbarat', 'intel_index_quf'),
    # FOUNDATION/MECHANISM
    'foundation_data': ('amr_aql', 'foundation_quf'),
    'mechanism_data': ('amr_aql', 'mechanism_quf'),
}


def _get_domain_fn(table: str):
    """Lazy-load domain QUF function for a table."""
    entry = DOMAIN_GATE_MAP.get(table)
    if not entry:
        return None
    module_name, fn_name = entry
    try:
        mod = __import__(module_name)
        return getattr(mod, fn_name, None)
    except (ImportError, AttributeError):
        return None


# ═══════════════════════════════════════════════════════════════════════
# MAIN VALIDATE — the single entry point
# ═══════════════════════════════════════════════════════════════════════

def validate(data: Dict, domain: str) -> Dict:
    """
    Run multi-layer QUF validation.

    Args:
        data: row data as dict
        domain: table name (determines which domain gates fire)

    Returns:
        {
            'q': grade, 'u': grade, 'f': grade,
            'pass': bool,
            'layers': [{'name': str, 'result': {...}}, ...],
            'evidence': [str, ...],
        }
    """
    layers = []

    # ── LAYER 0: LETTER ALIGNMENT (fires if root_letters AND meaning present) ──
    # Must fire BEFORE all other layers. If meaning contradicts letters, BLOCK.
    root_for_alignment = (data.get('root_letters', '') or
                          data.get('orig_root', '') or
                          data.get('root', '') or '')
    meaning_for_alignment = (data.get('aa_word', '') or
                             data.get('orig_meaning', '') or
                             data.get('primary_meaning', '') or '')
    if root_for_alignment and '-' in root_for_alignment and meaning_for_alignment:
        alignment_result = letter_alignment_quf(data)
        layers.append(('LETTER_ALIGNMENT', alignment_result))

    # ── LAYER 1: PHONETIC_CHAIN (fires if root_letters present AND table has phonetic data) ──
    # Intelligence/detection/confession tables have root_letters as EVIDENCE,
    # not as a linguistic entry to be phonetically validated.
    # Tables where PHONETIC_CHAIN QUF should NOT fire.
    # These are intelligence, metadata, protocol, cross-ref, or derivative
    # tables — they reference roots as EVIDENCE, not as linguistic entries.
    # Only word-entry tables (a1_entries, bitig_a1, latin_a1, etc.) get
    # linguistic validation (phonetic chain, shift precedent, etc.).
    SKIP_PHONETIC_CHAIN = {
        # Intelligence / detection / confession
        'institutional_confession_register', 'financial_extraction_cycles',
        'isnad', 'kashgari_concealment_audit', 'intel_file_index',
        'interception_register',
        # Protocol / metadata
        'dp_register', 'disputed_words', 'contamination_blacklist',
        'phonetic_reversal', 'qv_translation_register',
        'protocol_corrections', 'att_terms', 'session_index',
        # Chronology / deployment
        'chronology', 'child_entries', 'word_deployment_map',
        # Body lattice
        'body_data', 'body_cross_refs_unified', 'body_prayer_map_unified',
        'body_extraction_intel',
        # Formula lattice
        'formula_concealment', 'formula_ratios', 'formula_restoration',
        'formula_scholars', 'formula_undiscovered', 'formula_cross_refs',
        # Operations / UMD
        'umd_operations', 'operation_codes',
        # Cross-refs, derivatives, networks (reference tables, not word entries)
        'a3_quran_refs', 'a4_derivatives', 'a5_cross_refs',
        'a6_country_names', 'm4_networks',
        # Names of Allah, child schema (structured entries, not phonetic)
        'a2_names_of_allah', 'names_of_allah', 'child_schema',
        # ORIG2 (Bitig) — Yafith line, NOT AA. No phonetic chain to AA expected.
        # Validated by bitig_quf (domain layer) instead.
        'bitig_a1_entries',
    }
    root_letters = (data.get('root_letters', '') or
                    data.get('root', '') or
                    data.get('aa_root_id', '') or '')
    if root_letters and domain not in SKIP_PHONETIC_CHAIN:
        try:
            from amr_aql import linguistic_quf
            ling_result = linguistic_quf(data)
            layers.append(('PHONETIC_CHAIN', ling_result))
        except (ImportError, AttributeError):
            pass

    # ── LAYER 2: DOMAIN-SPECIFIC ──
    domain_fn = _get_domain_fn(domain)
    if domain_fn:
        try:
            domain_result = domain_fn(data)
            layers.append(('DOMAIN', domain_result))
        except Exception as e:
            layers.append(('DOMAIN', make_result('FAIL', 'FAIL', 'FAIL',
                                                  [f'Domain QUF error: {e}'])))

    # ── LAYER 3: SOURCE (fires if actual source/qur_ref present) ──
    # dp_codes alone is detection tagging, not source documentation
    has_source_fields = any(data.get(k) for k in
                           ['source', 'source_ref', 'qur_ref', 'quranic_ref',
                            'qur_anchor', 'qur_meaning', 'ayah_refs',
                            'quran_proof', 'confession_text', 'what_it_confesses',
                            'qur_primary', 'qur_secondary', 'qur_refs',
                            'founding_instances', 'dp_codes', 'dp_always_active',
                            'kashgari_attestation', 'ibn_sina_attestation'])
    if has_source_fields:
        src_result = source_quf(data)
        layers.append(('SOURCE', src_result))

    # ── LAYER 4: CONCEPT DOWNSTREAM FORMAT ──
    # AA CONCEPT entries that replace known downstream terms MUST include:
    #   (a) downstream word in brackets in source_form
    #   (b) downstream AA root candidates in notes
    # Q = brackets present? U = root candidates documented? F = multiple candidates?
    _concept_pattern = (data.get('pattern', '') or '').upper()
    _concept_en = (data.get('en_term', '') or '').strip()
    if _concept_pattern == 'CONCEPT' and _concept_en and domain == 'entries':
        _sf = (data.get('source_form', '') or '').lower()
        _nt = (data.get('notes', '') or '').lower()
        _has_brackets = f'({_concept_en.lower()}' in _sf
        _has_candidates = 'root candidate' in _nt or 'downstream' in _nt
        _has_multiple = _nt.count('(1)') >= 1 and _nt.count('(2)') >= 1

        _cq = 'HIGH' if _has_brackets else 'FAIL'
        _cu = 'HIGH' if _has_candidates else 'FAIL'
        _cf = 'HIGH' if _has_multiple else ('MEDIUM' if _has_candidates else 'LOW')
        _cev_q = [f'Downstream word in brackets: {_has_brackets}']
        _cev_u = [f'Root candidates documented: {_has_candidates}']
        _cev_f = [f'Multiple candidates: {_has_multiple}']
        layers.append(('CONCEPT_DOWNSTREAM', make_result(_cq, _cu, _cf, _cev_q, _cev_u, _cev_f)))

    # ── COMPOSITE ──
    if not layers:
        return {
            'q': 'PENDING', 'u': 'PENDING', 'f': 'PENDING',
            'pass': False,
            'layers': [],
            'evidence': ['No QUF layers applicable — no root, no domain, no source'],
        }

    all_q = [lr[1]['q'] for lr in layers]
    all_u = [lr[1]['u'] for lr in layers]
    all_f = [lr[1]['f'] for lr in layers]

    comp_q = _min_grade(all_q)
    comp_u = _min_grade(all_u)
    comp_f = _min_grade(all_f)
    comp_pass = all(_grade_passes(g) for g in [comp_q, comp_u, comp_f])

    evidence = []
    for name, result in layers:
        status = 'PASS' if result['pass'] else 'FAIL'
        evidence.append(f'{name}: Q={result["q"]} U={result["u"]} F={result["f"]} [{status}]')
        for ev in result.get('q_evidence', []) + result.get('u_evidence', []) + result.get('f_evidence', []):
            evidence.append(f'  {name}: {ev}')

    return {
        'q': comp_q, 'u': comp_u, 'f': comp_f,
        'pass': comp_pass,
        'layers': [{'name': n, 'result': r} for n, r in layers],
        'evidence': evidence,
    }


# ═══════════════════════════════════════════════════════════════════════
# WRITE GRADES TO DB
# ═══════════════════════════════════════════════════════════════════════

def write_grades(conn, table: str, row_id, id_col: str, composite: Dict):
    """Write QUF grades to a row in the database."""
    conn.execute(
        f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
        f'WHERE "{id_col}"=?',
        (composite['q'], composite['u'], composite['f'],
         str(composite['pass']).upper(), _now(), row_id)
    )


# ═══════════════════════════════════════════════════════════════════════
# BATCH VALIDATE
# ═══════════════════════════════════════════════════════════════════════

# Table → primary key column
TABLE_ID_MAP = {
    'entries': 'entry_id',
    'roots': 'root_id',
    'names_of_allah': 'allah_id',
    'quran_word_roots': 'rowid',
    'quran_known_forms': 'rowid',
    'european_a1_entries': 'eu_id',
    'latin_a1_entries': 'lat_id',
    'bitig_a1_entries': 'entry_id',
    'uzbek_vocabulary': 'uz_id',
    'a4_derivatives': 'deriv_id',
    'a5_cross_refs': 'xref_id',
    'body_data': 'body_id',
    'body_cross_refs_unified': 'rowid',
    'body_prayer_map_unified': 'rowid',
    'formula_concealment': 'rowid',
    'formula_ratios': 'rowid',
    'formula_restoration': 'rowid',
    'formula_scholars': 'rowid',
    'formula_undiscovered': 'rowid',
    'chronology': 'rowid',
    'child_entries': 'rowid',
    'isnad': 'rowid',
    'institutional_confession_register': 'rowid',
    'financial_extraction_cycles': 'rowid',
    'qv_translation_register': 'rowid',
    'disputed_words': 'rowid',
    'att_terms': 'rowid',
}


def _preload_caches(conn) -> Dict:
    """Pre-load all lookup data ONCE for batch operations."""
    caches = {}

    # Sibling counts per root_id
    sibling_tables = [
        ('entries', 'root_id'),
        ('european_a1_entries', 'root_id'),
        ('latin_a1_entries', 'root_id'),
        ('bitig_a1_entries', 'root_id'),
        ('uzbek_vocabulary', 'aa_root_id'),
    ]
    sibling_counts = {}  # root_id → count of tables with entries
    for tbl, col in sibling_tables:
        try:
            rows = conn.execute(f'SELECT DISTINCT "{col}" FROM "{tbl}" WHERE "{col}" IS NOT NULL AND "{col}" != ""').fetchall()
            for r in rows:
                rid = r[0]
                sibling_counts[rid] = sibling_counts.get(rid, 0) + 1
        except Exception:
            pass
    caches['sibling_counts'] = sibling_counts

    # Surah spread per root
    surah_spread = {}
    try:
        rows = conn.execute("SELECT root, COUNT(DISTINCT surah) FROM quran_word_roots WHERE root IS NOT NULL GROUP BY root").fetchall()
        for r in rows:
            surah_spread[r[0]] = r[1]
    except Exception:
        pass
    caches['surah_spread'] = surah_spread

    # Quranic token counts per root
    token_counts = {}
    try:
        rows = conn.execute("SELECT root, COUNT(*) FROM quran_word_roots WHERE root IS NOT NULL GROUP BY root").fetchall()
        for r in rows:
            token_counts[r[0]] = r[1]
    except Exception:
        pass
    caches['token_counts'] = token_counts

    # Roots table (bare → exists)
    root_exists = set()
    try:
        rows = conn.execute("SELECT root_bare FROM roots WHERE root_bare IS NOT NULL").fetchall()
        root_exists = {r[0] for r in rows}
        rows2 = conn.execute("SELECT root_letters FROM roots WHERE root_letters IS NOT NULL").fetchall()
        root_exists.update(r[0] for r in rows2)
    except Exception:
        pass
    caches['root_exists'] = root_exists

    # Entry existence (for derivative/xref checks)
    entry_ids = set()
    try:
        rows = conn.execute("SELECT entry_id FROM entries").fetchall()
        entry_ids = {r[0] for r in rows}
    except Exception:
        pass
    caches['entry_ids'] = entry_ids

    # EN parent root_ids (for sibling checks)
    en_root_ids = set()
    try:
        rows = conn.execute("SELECT DISTINCT root_id FROM entries WHERE root_id IS NOT NULL").fetchall()
        en_root_ids = {r[0] for r in rows}
    except Exception:
        pass
    caches['en_root_ids'] = en_root_ids

    return caches


# Module-level cache for batch operations
_BATCH_CACHES = None


def _fast_linguistic_quf(data: dict, caches: Dict) -> Dict:
    """Fast version of linguistic_quf using pre-loaded caches."""
    import re
    root_letters = data.get('root_letters', '') or data.get('root', '') or ''
    root_id = data.get('root_id', '') or data.get('aa_root_id', '') or ''
    phonetic_chain = data.get('phonetic_chain', '') or ''
    score = data.get('score', 0) or 0
    en_term = data.get('en_term', '') or data.get('term', '') or ''

    if not root_letters and not root_id:
        return make_result('PENDING', 'PENDING', 'PENDING', ['No root'])

    # Q: shift chain + token count (entries) OR quran_tokens (roots)
    q_ev = []
    direct_tokens = data.get('quran_tokens', 0) or 0  # roots table has this
    cached_tokens = caches.get('token_counts', {}).get(root_letters, 0)
    tokens = max(direct_tokens, cached_tokens)

    if phonetic_chain and len(phonetic_chain) > 5:
        shifts = re.findall(r'S\d{2}', phonetic_chain)
        if shifts:
            q = 'HIGH'
            q_ev.append(f'{len(shifts)} shifts')
        else:
            q = 'MEDIUM'
            q_ev.append('Chain present, no shift IDs')
    elif tokens >= 10:
        q = 'HIGH'
        q_ev.append(f'{tokens} Quranic tokens')
    elif tokens > 0:
        q = 'HIGH'
        q_ev.append(f'{tokens} Quranic tokens')
    elif score and score >= 8:
        q = 'HIGH'
        q_ev.append(f'Score {score}/10')
    elif score and score >= 5:
        q = 'MEDIUM'
        q_ev.append(f'Score {score}/10')
    elif root_letters:
        q = 'MEDIUM'
        q_ev.append(f'Root present, no tokens/chain')
    else:
        q = 'LOW'
        q_ev.append(f'No evidence')

    if tokens > 0 and f'{tokens} Quranic tokens' not in q_ev[0]:
        q_ev.append(f'{tokens} tokens')

    # U: sibling + surah spread (from cache)
    sib_count = caches.get('sibling_counts', {}).get(root_id, 0)
    surahs = caches.get('surah_spread', {}).get(root_letters, 0)
    if surahs >= 20 or sib_count >= 4:
        u = 'HIGH'
    elif surahs >= 5 or sib_count >= 2:
        u = 'HIGH'
    elif surahs >= 1 or sib_count >= 1:
        u = 'MEDIUM'
    else:
        u = 'LOW'
    u_ev = [f'{surahs} surahs, {sib_count} siblings']

    # F: chain + score (entries) OR tokens + consistency (roots)
    if phonetic_chain and score and score >= 8:
        f = 'HIGH'
    elif phonetic_chain:
        f = 'MEDIUM'
    elif tokens > 0:
        # Root with Quranic tokens = empirically attested
        f = 'HIGH'
        f_ev_note = f'{tokens} Quranic tokens = empirically attested'
    elif root_letters:
        f = 'MEDIUM'
    else:
        f = 'LOW'
    f_ev = [f'chain={bool(phonetic_chain)}, score={score}, tokens={tokens}']

    return make_result(q, u, f, q_ev, u_ev, f_ev)


def _fast_validate(data: Dict, domain: str, caches: Dict) -> Dict:
    """Fast validate using pre-loaded caches."""
    layers = []

    # Layer 1: linguistic (fast path)
    root_letters = (data.get('root_letters', '') or data.get('root', '') or
                    data.get('aa_root_id', '') or '')
    if root_letters:
        layers.append(('PHONETIC_CHAIN', _fast_linguistic_quf(data, caches)))

    # Layer 2: domain — skip if Layer 1 already covers it (same function)
    # For entries/roots/siblings, linguistic IS the domain gate — don't run twice
    PHONETIC_CHAIN_DOMAINS = {'entries', 'roots', 'european_a1_entries', 'latin_a1_entries',
                          'bitig_a1_entries', 'uzbek_vocabulary', 'names_of_allah',
                          'name_root_hub', 'quran_word_roots', 'quran_known_forms',
                          'quran_ayat', 'quran_refs', 'a4_derivatives', 'a5_cross_refs',
                          'foundation_data', 'mechanism_data'}
    if domain not in PHONETIC_CHAIN_DOMAINS:
        domain_fn = _get_domain_fn(domain)
        if domain_fn:
            try:
                layers.append(('DOMAIN', domain_fn(data)))
            except Exception as e:
                layers.append(('DOMAIN', make_result('FAIL', 'FAIL', 'FAIL', [str(e)])))

    # Layer 3: source — only fires if actual source/qur_ref present
    # dp_codes alone is detection tagging, not source documentation
    has_source = any(data.get(k) for k in
                     ['source', 'source_ref', 'qur_ref', 'quranic_ref', 'qur_anchor'])
    if has_source:
        layers.append(('SOURCE', source_quf(data)))

    if not layers:
        return {'q': 'PENDING', 'u': 'PENDING', 'f': 'PENDING', 'pass': False,
                'layers': [], 'evidence': ['No layers applicable']}

    comp_q = _min_grade([lr[1]['q'] for lr in layers])
    comp_u = _min_grade([lr[1]['u'] for lr in layers])
    comp_f = _min_grade([lr[1]['f'] for lr in layers])
    comp_pass = all(_grade_passes(g) for g in [comp_q, comp_u, comp_f])

    return {'q': comp_q, 'u': comp_u, 'f': comp_f, 'pass': comp_pass,
            'layers': [{'name': n, 'result': r} for n, r in layers], 'evidence': []}


def batch_validate(table: str, limit: int = 0, verbose: bool = False) -> Dict:
    """
    Re-run QUF on all rows in a table via the AMR pipeline.
    Uses pre-loaded caches for performance (single DB connection).

    Returns: {'table': str, 'total': int, 'pass': int, 'fail': int, 'grades': {...}}
    """
    id_col = TABLE_ID_MAP.get(table, 'rowid')
    conn = _connect()

    # Pre-load all caches ONCE
    print(f"  Pre-loading caches...", end=' ', flush=True)
    caches = _preload_caches(conn)
    print(f"done ({len(caches.get('sibling_counts', {}))} roots, "
          f"{len(caches.get('surah_spread', {}))} spreads)")

    try:
        rows = conn.execute(f'SELECT *, rowid as _rowid FROM "{table}"'
                            + (f' LIMIT {limit}' if limit else '')).fetchall()
    except Exception as e:
        conn.close()
        return {'table': table, 'error': str(e)}

    total = len(rows)
    pass_count = 0
    fail_count = 0
    grade_dist = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'FAIL': 0, 'PENDING': 0}
    now = _now()

    for i, row in enumerate(rows):
        row_dict = dict(row)
        rid = row_dict.get(id_col) or row_dict.get('_rowid')
        result = _fast_validate(row_dict, domain=table, caches=caches)

        try:
            conn.execute(
                f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
                f'WHERE rowid=?',
                (result['q'], result['u'], result['f'],
                 str(result['pass']).upper(), now, row_dict.get('_rowid', rid))
            )
        except Exception:
            try:
                conn.execute(
                    f'UPDATE "{table}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? '
                    f'WHERE "{id_col}"=?',
                    (result['q'], result['u'], result['f'],
                     str(result['pass']).upper(), now, rid)
                )
            except Exception:
                pass

        if result['pass']:
            pass_count += 1
        else:
            fail_count += 1
        grade_dist[result['q']] = grade_dist.get(result['q'], 0) + 1

        if verbose and not result['pass']:
            print(f"  FAIL {rid}: {' | '.join(result['evidence'][:3])}")

    conn.commit()
    conn.close()

    return {
        'table': table,
        'total': total,
        'pass': pass_count,
        'fail': fail_count,
        'pass_rate': f'{pass_count/max(total,1)*100:.1f}%',
        'q_distribution': grade_dist,
    }


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description='أَمْر QUF — Multi-layer validation')
    sub = parser.add_subparsers(dest='cmd')

    # validate --table TABLE --id ID
    p_val = sub.add_parser('validate', help='Validate a single row')
    p_val.add_argument('--table', required=True)
    p_val.add_argument('--id', required=True)

    # batch --table TABLE [--limit N] [--verbose]
    p_batch = sub.add_parser('batch', help='Batch validate all rows in a table')
    p_batch.add_argument('--table', required=True)
    p_batch.add_argument('--limit', type=int, default=0)
    p_batch.add_argument('--verbose', action='store_true')

    # status
    sub.add_parser('status', help='Show QUF coverage across all tables')

    args = parser.parse_args()

    if args.cmd == 'validate':
        conn = _connect()
        id_col = TABLE_ID_MAP.get(args.table, 'rowid')
        try:
            row = conn.execute(
                f'SELECT * FROM "{args.table}" WHERE "{id_col}" = ?', (args.id,)
            ).fetchone()
        except Exception:
            row = conn.execute(
                f'SELECT *, rowid FROM "{args.table}" WHERE rowid = ?', (args.id,)
            ).fetchone()
        conn.close()

        if not row:
            print(f"Row {args.id} not found in {args.table}")
            return

        result = validate(dict(row), domain=args.table)
        print(f"{'═'*60}")
        print(f"QUF VALIDATION: {args.table} #{args.id}")
        print(f"{'═'*60}")
        print(f"  Q = {result['q']}")
        print(f"  U = {result['u']}")
        print(f"  F = {result['f']}")
        print(f"  OVERALL: {'✓ PASS' if result['pass'] else '✗ FAIL'}")
        print(f"{'─'*60}")
        print(f"  Layers: {len(result['layers'])}")
        for ev in result['evidence']:
            print(f"  {ev}")
        print(f"{'═'*60}")

    elif args.cmd == 'batch':
        result = batch_validate(args.table, limit=args.limit, verbose=args.verbose)
        print(f"{'═'*60}")
        print(f"BATCH QUF: {result['table']}")
        print(f"  Total:     {result.get('total', 0)}")
        print(f"  Pass:      {result.get('pass', 0)}")
        print(f"  Fail:      {result.get('fail', 0)}")
        print(f"  Pass rate: {result.get('pass_rate', '?')}")
        print(f"{'═'*60}")

    elif args.cmd == 'status':
        conn = _connect()
        print(f"{'═'*60}")
        print(f"QUF COVERAGE STATUS")
        print(f"{'═'*60}")
        for table in sorted(DOMAIN_GATE_MAP.keys()):
            try:
                total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                passed = conn.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = "TRUE"'
                ).fetchone()[0]
                pct = f'{passed/max(total,1)*100:.0f}%'
                print(f"  {table:45s} {passed:>5}/{total:<5} {pct:>5}")
            except Exception:
                print(f"  {table:45s}   [no QUF columns]")
        conn.close()
        print(f"{'═'*60}")

    else:
        parser.print_help()


if __name__ == '__main__':
    _cli()
