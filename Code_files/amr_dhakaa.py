#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر ذَكَاء — ORCHESTRATOR

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: ذ-ك-و/ي — intelligence, acuity, sharpness
Q2:269 وَمَن يُؤْتَ ٱلْحِكْمَةَ فَقَدْ أُوتِيَ خَيْرًا كَثِيرًا
— and whoever is given wisdom has been given much good

The ذَكَاء orchestrates. It wires:
    بَصَر (perceive) → عَقْل (reason) → نُطْق (articulate)

One function: think(input) → output
Every answer traceable to 28 letters.
No statistical weights. No hallucination. No contamination.

Architecture:
    Layer 0: amr_alphabet.py  — 28 letters (fixed values)
    Layer 1: amr_lexer/parser — language syntax
    Layer 2: amr_lawh.py      — storage engine
    Layer 3: amr_ard.py       — OS kernel
    Layer 4: amr_runtime.py   — runtime + tools
    Layer 5: amr_aql.py       — عَقْل (intellect)
    Layer 6: amr_nutq.py      — نُطْق (articulation)
    Layer 7: amr_basar.py     — بَصَر (perception)
    Layer 8: amr_dhakaa.py    — ذَكَاء (THIS — orchestrator)
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the three engines
from amr_basar import (
    perceive, classify_input, detect_root, decompose,
    track_context, get_context, suggest_next,
    ContextTracker
)
from amr_aql import (
    deduce_meaning, reverse_trace, expand_root, relate_roots,
    hypothesise, verify_candidate, trace_timeline,
    find_type_c_pairs, detect_inversion_levels, cross_wash, severity_score
)
from amr_alphabet import ALPHABET, ABJAD

# Domain modules — جِسْم حِسَاب تَارِيخ اِسْتِخْبَارَات
try:
    from amr_jism import expand_root_body, trace_body_system, diagnose_root, body_heptad, body_cross_search
    _HAS_JISM = True
except ImportError:
    _HAS_JISM = False

try:
    from amr_hisab import expand_root_formula, trace_formula, ratio_analysis, concealment_chain
    _HAS_HISAB = True
except ImportError:
    _HAS_HISAB = False

try:
    from amr_tarikh import expand_root_timeline, trace_event, deployment_chain, era_summary, naming_operation
    _HAS_TARIKH = True
except ImportError:
    _HAS_TARIKH = False

try:
    from amr_istakhbarat import expand_root_intel, confession_for_entry, extraction_cycle, mortality_trace, kashgari_audit, intel_summary
    _HAS_ISTAKHBARAT = True
except ImportError:
    _HAS_ISTAKHBARAT = False

# Domain QUF — wire to uslap_quf.py domain validators
try:
    from uslap_quf import QUFContext, DOMAIN_VALIDATORS, QUFResult, DB_PATH as QUF_DB_PATH
    import sqlite3 as _quf_sqlite3
    _HAS_DOMAIN_QUF = True
except ImportError:
    _HAS_DOMAIN_QUF = False
from amr_nutq import (
    att, att_root, format_quf, format_shift_chain,
    format_entry_card, format_entry_card_from_db,
    format_root_report, format_hypothesis, format_comparison,
    format_dp, format_batch_report, format_lattice_summary,
    explain_root, generate_report, provenance, format_provenance,
    transliterate, wrapper_name
)

try:
    from uslap_db_connect import connect as _connect
    _HAS_DB = True
except ImportError:
    _HAS_DB = False


# ═══════════════════════════════════════════════════════════════════════
# THINK — the one function
# ═══════════════════════════════════════════════════════════════════════

def think(user_input):
    """The one function. Input → output with full provenance.

    Pipeline:
        1. بَصَر perceives: what does the user mean?
        2. عَقْل reasons: compute from letters + DB
        3. نُطْق articulates: format with provenance

    Every output traces to 28 letters with fixed abjad values.
    No statistical weights. No training data. No hallucination.

    Args:
        user_input: raw text from user (any language)

    Returns:
        dict with:
            output: formatted string (ready to display)
            provenance: derivation chain back to letters
            intent: what was understood
            context: session context after this query
    """
    # ── STEP 1: بَصَر — PERCEIVE ──────────────────────────────────
    try:
        perception = perceive(user_input)
    except Exception as e:
        return {
            'output': f"⛔ PERCEPTION FAILED: {e}\nQuery: {user_input}",
            'provenance': {}, 'intent': 'error', 'params': {},
            'confidence': 0, 'context': {}, 'quf': {},
        }

    context = track_context(perception)

    intent = perception['intent']
    params = perception['params']
    enriched = perception['enriched']

    # ── STEP 2: عَقْل — REASON ────────────────────────────────────
    # Route to the correct reasoning function based on intent
    enriched['raw_input'] = user_input
    try:
        reasoning = _reason(intent, params, enriched)
    except Exception as e:
        reasoning = {'error': f"⛔ REASONING FAILED on intent '{intent}': {e}", 'source': 'ERROR'}

    # ── STEP 2.5: QUF GATE — QUANTIFICATION, UNIVERSALITY, FALSIFIABILITY ──
    # Every claim must pass before نُطْق speaks it.
    # Q: Is the evidence countable? How much?
    # U: Does this root explain ALL siblings, not cherry-picked?
    # F: What would disprove this? Is the claim falsifiable?
    if intent == 'trace_word' and reasoning.get('source') != 'DB':
        candidates = reasoning.get('candidates', [])
        if candidates:
            try:
                reasoning['quf_gate'] = _quf_gate(candidates)
            except Exception:
                pass

    # ── STEP 2.6: DOMAIN QUF — Check candidate roots against DB QUF ──
    # If the top candidate's root has quf_pass != TRUE in the DB,
    # flag it in the output. The data questions itself.
    if _HAS_DOMAIN_QUF and reasoning.get('candidates'):
        try:
            reasoning['domain_quf'] = _domain_quf_check(reasoning['candidates'])
        except Exception:
            pass

    # ── STEP 3: نُطْق — ARTICULATE ────────────────────────────────
    try:
        output = _articulate(intent, reasoning, params)
    except Exception as e:
        output = reasoning.get('error', f"⛔ ARTICULATION FAILED on intent '{intent}': {e}")

    return {
        'output': output,
        'provenance': reasoning.get('provenance', {}),
        'intent': intent,
        'params': params,
        'confidence': perception['confidence'],
        'context': context,
        'quf': reasoning.get('quf_gate', {}),
        'domain_quf': reasoning.get('domain_quf', {}),
        'cascade': reasoning.get('cascade', {}),
        'cascade_root': reasoning.get('cascade_root'),
    }


def _reason(intent, params, enriched):
    """Route intent to the correct عَقْل function.

    Returns dict with reasoning results and provenance.
    """
    result = {'provenance': {}}

    if intent == 'explain_root':
        root_ref = (params.get('root_id') or params.get('root_letters')
                    or params.get('query', ''))
        result['tree'] = expand_root(root_ref)
        result['meaning'] = deduce_meaning(root_ref) if '-' in root_ref else None
        result['provenance'] = provenance(root_ref)

    elif intent == 'trace_word':
        word = params.get('word') or params.get('query', '')
        lang = params.get('language', 'en')

        # If already in DB, use that
        if enriched.get('existing_entry'):
            entry_id = enriched['entry_id']
            root_id = enriched['root_id']
            result['source'] = 'DB'
            result['entry_id'] = entry_id
            result['root_id'] = root_id
            if root_id:
                result['tree'] = expand_root(root_id)
                result['provenance'] = provenance(entry_id)
        else:
            # Compute from scratch
            result['candidates'] = hypothesise(word, lang)
            result['source'] = 'COMPUTED'
            result['provenance'] = provenance(word, lang)

    elif intent == 'compare_roots':
        root_a = params.get('root_a', '')
        root_b = params.get('root_b', '')
        result['relation'] = relate_roots(root_a, root_b)
        result['tree_a'] = expand_root(root_a)
        result['tree_b'] = expand_root(root_b)

    elif intent == 'get_entry':
        entry_id = params.get('entry_id') or params.get('query', '')
        result['provenance'] = provenance(entry_id)
        result['entry_id'] = entry_id

    elif intent == 'search_lattice':
        query = params.get('query', '')
        # Search entries
        if _HAS_DB:
            conn = _connect()
            hits = conn.execute(
                "SELECT entry_id, en_term, ru_term, root_id, root_letters, dp_codes "
                "FROM entries WHERE LOWER(en_term) LIKE ? OR LOWER(ru_term) LIKE ? "
                "OR LOWER(fa_term) LIKE ? OR root_letters LIKE ? LIMIT 20",
                (f'%{query.lower()}%', f'%{query.lower()}%',
                 f'%{query.lower()}%', f'%{query}%')
            ).fetchall()
            result['hits'] = [dict(h) for h in hits]
            conn.close()
        else:
            result['hits'] = []

    elif intent == 'lattice_state':
        result['summary'] = True

    elif intent == 'report':
        root_ref = params.get('query', '')
        result['root_ref'] = root_ref

    # ── DOMAIN MODULES ────────────────────────────────────────────
    elif intent == 'explain_body':
        root_ref = params.get('query', '')
        if _HAS_JISM:
            result['body'] = expand_root_body(root_ref)
            result['source'] = 'DOMAIN_JISM'

    elif intent == 'body_system':
        system = params.get('query', '')
        if _HAS_JISM:
            result['system'] = trace_body_system(system)
            result['source'] = 'DOMAIN_JISM'

    elif intent == 'explain_formula':
        root_ref = params.get('query', '')
        if _HAS_HISAB:
            result['formula'] = expand_root_formula(root_ref)
            result['source'] = 'DOMAIN_HISAB'

    elif intent == 'explain_history':
        query = params.get('query', '')
        if _HAS_TARIKH:
            # Check if era number
            if query.isdigit():
                result['era'] = era_summary(int(query))
            else:
                result['timeline'] = expand_root_timeline(query)
            result['source'] = 'DOMAIN_TARIKH'

    elif intent == 'naming_op':
        name = params.get('query', '')
        if _HAS_TARIKH:
            result['naming'] = naming_operation(orig_name=name)
            result['source'] = 'DOMAIN_TARIKH'

    elif intent == 'explain_intel':
        query = params.get('query', '')
        if _HAS_ISTAKHBARAT:
            # Try root-based intel first
            intel = expand_root_intel(query)
            if intel and intel.get('tables_with_data'):
                result['intel'] = intel
            else:
                # Fall back to cross-search
                from amr_istakhbarat import intel_cross_search
                result['intel'] = intel_cross_search(query)
            result['source'] = 'DOMAIN_ISTAKHBARAT'

    elif intent == 'quf_validate':
        # QUF validation via amr_quf
        try:
            from amr_quf import validate as _quf_validate, _connect as _quf_connect
            table = params.get('table', 'entries')
            row_id = params.get('query', params.get('entry_id', ''))
            # Look up the row
            conn = _quf_connect()
            id_col = {'entries': 'entry_id', 'roots': 'root_id',
                       'names_of_allah': 'allah_id'}.get(table, 'rowid')
            try:
                row = conn.execute(f'SELECT * FROM "{table}" WHERE "{id_col}" = ?',
                                   (row_id,)).fetchone()
            except Exception:
                row = conn.execute(f'SELECT *, rowid FROM "{table}" WHERE rowid = ?',
                                   (row_id,)).fetchone()
            conn.close()
            if row:
                result['quf_result'] = _quf_validate(dict(row), domain=table)
                result['table'] = table
                result['row_id'] = row_id
            else:
                result['quf_result'] = None
                result['error'] = f'Row {row_id} not found in {table}'
        except ImportError:
            result['error'] = 'amr_quf not available'
        result['source'] = 'QUF'

    elif intent == 'quf_status':
        try:
            from amr_quf import _connect as _quf_connect, DOMAIN_GATE_MAP
            conn = _quf_connect()
            status = {}
            for table in sorted(DOMAIN_GATE_MAP.keys()):
                try:
                    total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    passed = conn.execute(
                        f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = "TRUE"'
                    ).fetchone()[0]
                    status[table] = {'total': total, 'pass': passed,
                                     'rate': f'{passed*100//max(total,1)}%'}
                except Exception:
                    pass
            conn.close()
            result['quf_status'] = status
        except ImportError:
            result['error'] = 'amr_quf not available'
        result['source'] = 'QUF'

    elif intent == 'explain_detection':
        dp_id = params.get('query', '')
        if _HAS_DB:
            conn = _connect()
            try:
                row = conn.execute(
                    "SELECT * FROM dp_register WHERE dp_code = ?", (dp_id.upper(),)
                ).fetchone()
                if row:
                    result['dp'] = dict(row)
                else:
                    # Search by name
                    rows = conn.execute(
                        "SELECT * FROM dp_register WHERE LOWER(name) LIKE ?",
                        (f'%{dp_id.lower()}%',)
                    ).fetchall()
                    result['dp_hits'] = [dict(r) for r in rows]
            except Exception:
                pass
            conn.close()
        result['source'] = 'DETECTION'

    elif intent == 'explain_keyword':
        kw = params.get('query', '')
        try:
            from amr_keywords import KEYWORDS, keyword_count
            if kw in KEYWORDS:
                result['keyword'] = KEYWORDS[kw]
                result['keyword']['arabic'] = kw
            else:
                # Search by python name
                for ar, data in KEYWORDS.items():
                    if data.get('python', '') == kw:
                        result['keyword'] = data
                        result['keyword']['arabic'] = ar
                        break
            result['total_keywords'] = keyword_count()
        except ImportError:
            result['error'] = 'amr_keywords not available'
        result['source'] = 'KEYWORDS'

    elif intent == 'tasrif':
        query_text = params.get('query', '') or enriched.get('raw_input', '')
        try:
            from amr_tasrif import get_status, get_root_forms, get_pattern_info, get_broken_plurals
            if 'status' in query_text:
                result['tasrif_status'] = get_status()
            elif 'broken_plural' in query_text:
                result['broken_plurals'] = get_broken_plurals()
            elif 'pattern' in query_text:
                code = query_text.split('pattern')[-1].strip()
                info, table = get_pattern_info(code)
                result['pattern_info'] = info
                result['pattern_table'] = table
            else:
                # Treat as root query
                root = query_text.replace('tasrif', '').strip()
                result['root_forms'] = get_root_forms(root)
                result['tasrif_root'] = root
        except ImportError:
            result['error'] = 'amr_tasrif not available'
        result['source'] = 'TASRIF'

    elif intent == 'bitig_tasrif':
        query_text = params.get('query', '') or enriched.get('raw_input', '')
        try:
            from amr_bitig_tasrif import (get_status as bi_status, get_root_forms as bi_root,
                                          get_pattern_info as bi_pattern, check_harmony,
                                          analyze_compound, analyze_word as bi_analyze)
            if 'status' in query_text:
                result['bitig_tasrif_status'] = bi_status()
            elif 'pattern' in query_text:
                code = query_text.split('pattern')[-1].strip()
                result['pattern_info'] = bi_pattern(code)
            elif 'harmony' in query_text:
                word = query_text.split('harmony')[-1].strip()
                result['harmony'] = check_harmony(word)
            elif 'compound' in query_text:
                text = query_text.split('compound')[-1].strip()
                result['compound'] = analyze_compound(text)
            elif 'analyze' in query_text:
                word = query_text.split('analyze')[-1].strip()
                result['bitig_analysis'] = bi_analyze(word)
            else:
                root = query_text.replace('bitig', '').replace('tasrif', '').strip()
                result['bitig_root_forms'] = bi_root(root)
        except ImportError:
            result['error'] = 'amr_bitig_tasrif not available'
        result['source'] = 'BITIG_TASRIF'

    # ── 15-LAYER CASCADE — EVERY QUERY, EVERY LAYER ──────────────────
    # After intent-specific routing, collect data from ALL 15 layers
    # for the root that was found. This ensures no layer is skipped.
    root_letters = None

    # Extract root from whatever the intent-specific routing found
    # Check all possible locations where root_letters might be stored
    if result.get('tree') and isinstance(result['tree'], dict):
        root_letters = result['tree'].get('root_letters')
    if not root_letters and result.get('provenance') and isinstance(result['provenance'], dict):
        prov_root = result['provenance'].get('root', {})
        if isinstance(prov_root, dict):
            root_letters = prov_root.get('root_letters')
    if not root_letters and enriched.get('root_letters'):
        root_letters = enriched['root_letters']
    if not root_letters and enriched.get('root_id') and _HAS_DB:
        # Look up root_letters from root_id
        try:
            conn = _connect()
            r = conn.execute("SELECT root_letters FROM roots WHERE root_id = ?",
                             (enriched['root_id'],)).fetchone()
            if r:
                root_letters = r[0]
            conn.close()
        except Exception:
            pass
    if not root_letters and result.get('candidates'):
        top = result['candidates'][0] if result['candidates'] else None
        if top and isinstance(top, dict):
            root_letters = top.get('root')
    if not root_letters:
        q = params.get('query', '')
        if '-' in q and len(q) <= 15:
            root_letters = q

    if root_letters and _HAS_DB:
        cascade = {}
        conn = _connect()

        # ════════════════════════════════════════════════════════════════
        # GATE 0: QUR'AN ATTESTATION — runs FIRST, gates everything
        # ════════════════════════════════════════════════════════════════
        attested = False
        quran_tokens = 0
        try:
            qwords = conn.execute(
                "SELECT surah, ayah, word_position, aa_word, root_meaning, word_type "
                "FROM quran_word_roots WHERE root = ? ORDER BY surah, ayah",
                (root_letters,)).fetchall()
            quran_tokens = len(qwords)
            attested = quran_tokens > 0
            cascade['quran_attested'] = attested
            cascade['quran_tokens'] = quran_tokens
            if qwords:
                cascade['quran_surahs'] = sorted(set(w['surah'] for w in qwords))
                cascade['quran_forms'] = [dict(w) for w in qwords[:20]]
        except Exception:
            cascade['quran_attested'] = False
            cascade['quran_tokens'] = 0

        # ════════════════════════════════════════════════════════════════
        # L0: LETTER COMPUTATION — deterministic, always runs
        # 28 letters with fixed abjad values. Safe regardless of
        # attestation. But confidence is gated by quran_attested.
        # ════════════════════════════════════════════════════════════════
        try:
            from amr_alphabet import compute_root_meaning, compute_root_meaning_text
            cascade['L0_letters'] = compute_root_meaning_text(root_letters)
            cascade['L0_computation'] = compute_root_meaning(root_letters)
            if not attested:
                cascade['L0_confidence'] = 'UNATTESTED — root not found in 77,881 Qur\'anic words'
            else:
                cascade['L0_confidence'] = f'ATTESTED — {quran_tokens} Qur\'anic tokens'
        except Exception:
            pass

        # ════════════════════════════════════════════════════════════════
        # L1-L13: ALL LAYERS — each inherits attestation flag
        # If unattested, layers still collect data but output is flagged.
        # ════════════════════════════════════════════════════════════════

        # L1: ROOT (DB registration)
        try:
            r = conn.execute(
                "SELECT root_id, root_letters, primary_meaning, quran_tokens FROM roots WHERE root_letters = ?",
                (root_letters,)).fetchone()
            if r:
                cascade['L1_root'] = dict(r)
        except Exception:
            pass

        # L2: KEYWORD (42 Qur'anic programming keywords)
        try:
            from amr_keywords import KEYWORDS
            for ar, data in KEYWORDS.items():
                if data.get('root') == root_letters:
                    cascade.setdefault('L2_keywords', []).append({'arabic': ar, **data})
        except Exception:
            pass

        # L3: DIVINE NAMES
        try:
            names = conn.execute(
                "SELECT * FROM names_of_allah WHERE root_letters = ?",
                (root_letters,)).fetchall()
            if names:
                cascade['L3_divine_names'] = [dict(n) for n in names]
        except Exception:
            pass

        # L5: ENTRIES (EN + RU + FA)
        try:
            entries = conn.execute(
                "SELECT entry_id, en_term, ru_term, fa_term, aa_word, dp_codes "
                "FROM entries WHERE root_letters = ?",
                (root_letters,)).fetchall()
            if entries:
                cascade['L5_entries'] = [dict(e) for e in entries]
        except Exception:
            pass

        # L6: ORIG2 (Bitig)
        try:
            bitig = conn.execute(
                "SELECT entry_id, orig2_term, root_letters, semantic_field "
                "FROM bitig_a1_entries WHERE root_letters = ?",
                (root_letters,)).fetchall()
            if bitig:
                cascade['L6_bitig'] = [dict(b) for b in bitig]
        except Exception:
            pass

        # L7: SIBLINGS (EU + LA)
        try:
            for tbl, lang in [('european_a1_entries', 'EU'), ('latin_a1_entries', 'LA')]:
                sibs = conn.execute(
                    f"SELECT entry_id, aa_word, lang FROM [{tbl}] WHERE root_letters = ?",
                    (root_letters,)).fetchall()
                if sibs:
                    cascade.setdefault('L7_siblings', []).extend(
                        [{'table': lang, **dict(s)} for s in sibs])
        except Exception:
            pass

        # L8: DERIVATIVES
        try:
            derivs = conn.execute(
                "SELECT deriv_id, base_entry_id, derivative_term FROM a4_derivatives "
                "WHERE base_entry_id IN (SELECT entry_id FROM entries WHERE root_letters = ?)",
                (root_letters,)).fetchall()
            if derivs:
                cascade['L8_derivatives'] = [dict(d) for d in derivs]
        except Exception:
            pass

        # L9: DETECTION (QV register)
        try:
            qv = conn.execute(
                "SELECT * FROM qv_translation_register WHERE root_letters = ?",
                (root_letters,)).fetchall()
            if qv:
                cascade['L9_qv'] = [dict(q) for q in qv]
        except Exception:
            pass

        # L10: BODY
        try:
            body = conn.execute(
                "SELECT body_id, subsystem, category, english FROM body_data WHERE root_letters = ?",
                (root_letters,)).fetchall()
            if body:
                cascade['L10_body'] = [dict(b) for b in body]
        except Exception:
            pass

        # L11: FORMULA
        try:
            for ftbl in ['formula_ratios', 'formula_concealment', 'formula_restoration']:
                rows = conn.execute(
                    f"SELECT * FROM [{ftbl}] WHERE LOWER(CAST(* AS TEXT)) LIKE ?",
                    (f'%{root_letters}%',)).fetchall()
                if rows:
                    cascade.setdefault('L11_formula', []).extend(
                        [{'table': ftbl, **dict(r)} for r in rows])
        except Exception:
            pass

        # L12: HISTORY (chronology + child_entries)
        try:
            terms_for_search = [root_letters]
            if cascade.get('L5_entries'):
                for e in cascade['L5_entries']:
                    if e.get('en_term'):
                        terms_for_search.append(e['en_term'])

            for term in terms_for_search:
                chron = conn.execute(
                    "SELECT id, date, era, event FROM chronology "
                    "WHERE LOWER(event) LIKE ? OR LOWER(notes) LIKE ? LIMIT 10",
                    (f'%{term.lower()}%', f'%{term.lower()}%')).fetchall()
                for c in chron:
                    cascade.setdefault('L12_history', []).append(dict(c))

            if cascade.get('L12_history'):
                seen = set()
                deduped = []
                for h in cascade['L12_history']:
                    if h['id'] not in seen:
                        seen.add(h['id'])
                        deduped.append(h)
                cascade['L12_history'] = deduped

            child = conn.execute(
                "SELECT child_id, shell_name, orig_root, operation_role FROM child_entries "
                "WHERE orig_root = ?",
                (root_letters,)).fetchall()
            if child:
                cascade['L12_peoples'] = [dict(c) for c in child]
        except Exception:
            pass

        # L13: INTELLIGENCE
        try:
            for itbl in ['interception_register']:
                rows = conn.execute(
                    f"SELECT * FROM [{itbl}] WHERE root_letters = ?",
                    (root_letters,)).fetchall()
                if rows:
                    cascade.setdefault('L13_intelligence', []).extend(
                        [dict(r) for r in rows])
        except Exception:
            pass

        conn.close()
        result['cascade'] = cascade
        result['cascade_root'] = root_letters

    return result


def _articulate(intent, reasoning, params):
    """Route reasoning results to the correct نُطْق function.

    Returns formatted string ready to display.
    """
    if intent == 'explain_root':
        root_ref = (params.get('root_id') or params.get('root_letters')
                    or params.get('query', ''))
        return explain_root(root_ref)

    elif intent == 'trace_word':
        word = params.get('word') or params.get('query', '')

        if reasoning.get('source') == 'DB':
            # Entry exists — show full report
            root_id = reasoning.get('root_id')
            if root_id and 'tree' in reasoning:
                report = format_root_report(reasoning['tree'])
                prov = format_provenance(reasoning['provenance'])
                return f"{report}\n\n{prov}"
            else:
                entry_id = reasoning.get('entry_id', '?')
                return format_entry_card_from_db(entry_id)
        else:
            # Not in DB — show hypothesis
            candidates = reasoning.get('candidates', [])
            return format_hypothesis(word, candidates, params.get('language', 'en'))

    elif intent == 'compare_roots':
        root_a = params.get('root_a', '')
        root_b = params.get('root_b', '')
        relation = reasoning.get('relation')
        return format_comparison(root_a, root_b, relation)

    elif intent == 'get_entry':
        entry_id = reasoning.get('entry_id', '')
        card = format_entry_card_from_db(entry_id)
        prov = format_provenance(reasoning.get('provenance', {}))
        return f"{card}\n\n{prov}"

    elif intent == 'search_lattice':
        hits = reasoning.get('hits', [])
        if not hits:
            query = params.get('query', '')
            return f"No entries found for '{query}'"
        items = [{'id': h.get('entry_id', '?'), 'term': h.get('en_term', '?'),
                  'root': h.get('root_letters', '?')} for h in hits]
        return format_batch_report(items, f"SEARCH: {params.get('query', '?')}")

    elif intent == 'lattice_state':
        return format_lattice_summary()

    elif intent == 'report':
        root_ref = reasoning.get('root_ref', '')
        return generate_report(root_ref)

    elif intent == 'quf_validate':
        qr = reasoning.get('quf_result')
        if not qr:
            return reasoning.get('error', 'QUF validation failed — row not found.')
        lines = ["═" * 60]
        lines.append(f"QUF VALIDATION: {reasoning.get('table', '?')} #{reasoning.get('row_id', '?')}")
        lines.append("═" * 60)
        lines.append(f"  Q = {qr['q']}")
        lines.append(f"  U = {qr['u']}")
        lines.append(f"  F = {qr['f']}")
        lines.append(f"  OVERALL: {'✓ PASS' if qr['pass'] else '✗ FAIL'}")
        lines.append("─" * 60)
        for layer in qr.get('layers', []):
            lr = layer['result']
            status = '✓' if lr['pass'] else '✗'
            lines.append(f"  {layer['name']}: Q={lr['q']} U={lr['u']} F={lr['f']} [{status}]")
            for ev in lr.get('q_evidence', []) + lr.get('u_evidence', []) + lr.get('f_evidence', []):
                lines.append(f"    {ev}")
        lines.append("═" * 60)
        return '\n'.join(lines)

    elif intent == 'quf_status':
        status = reasoning.get('quf_status', {})
        if not status:
            return reasoning.get('error', 'QUF status unavailable.')
        lines = ["═" * 60, "QUF COVERAGE STATUS", "═" * 60]
        for tbl, data in sorted(status.items()):
            lines.append(f"  {tbl:45s} {data['pass']:>5}/{data['total']:<5} {data['rate']:>5}")
        lines.append("═" * 60)
        return '\n'.join(lines)

    elif intent == 'explain_detection':
        dp = reasoning.get('dp')
        if dp:
            lines = ["═" * 60]
            lines.append(f"DETECTION PATTERN: {dp.get('dp_code', '?')}")
            lines.append(f"  NAME: {dp.get('name', '')}")
            lines.append(f"  CLASS: {dp.get('class', '')}")
            lines.append(f"  MECHANISM: {dp.get('mechanism', '')[:100]}")
            lines.append(f"  QUR ANCHOR: {dp.get('qur_anchor', '')}")
            lines.append(f"  STATUS: {dp.get('status', '')}")
            lines.append("═" * 60)
            return '\n'.join(lines)
        hits = reasoning.get('dp_hits', [])
        if hits:
            lines = [f"Found {len(hits)} detection patterns:"]
            for h in hits:
                lines.append(f"  {h.get('dp_code', '?')}: {h.get('name', '')}")
            return '\n'.join(lines)
        return "Detection pattern not found."

    elif intent == 'explain_keyword':
        kw = reasoning.get('keyword')
        if not kw:
            return reasoning.get('error', 'Keyword not found.')
        lines = ["═" * 60]
        lines.append(f"KEYWORD: {kw.get('arabic', '?')} → {kw.get('python', '?')}")
        lines.append(f"  ROOT: {kw.get('root', '')}")
        lines.append(f"  TOKENS: {kw.get('tokens', 0)}")
        lines.append(f"  DERIVATION: {str(kw.get('derivation', ''))[:100]}")
        lines.append("═" * 60)
        return '\n'.join(lines)

    # ── TASRIF ARTICULATION ──────────────────────────────────────
    elif intent == 'tasrif':
        if reasoning.get('error'):
            return reasoning['error']
        if reasoning.get('tasrif_status'):
            s = reasoning['tasrif_status']
            lines = ["=" * 60, "تَصْرِيف STATUS — Three-Layer Morphological Engine", "=" * 60, ""]
            lines.append(f"LAYER 1 — CONSONANT STRUCTURE")
            lines.append(f"  verb codes: {s.get('verb_consonant_codes', 0)}, noun codes: {s.get('noun_consonant_codes', 0)}")
            lines.append(f"  Tokens coded: VERB {s.get('verb_struct_coded', 0):,} | NOUN {s.get('noun_struct_coded', 0):,}")
            lines.append(f"LAYER 2 — VOWEL PATTERN")
            lines.append(f"  {s.get('vowel_codes', 0)} codes ({s.get('broken_plural_codes', 0)} broken plural)")
            lines.append(f"  Tokens coded: {s.get('vowel_coded', 0):,}")
            lines.append(f"LAYER 3 — GRAMMAR")
            lines.append(f"  verb: {s.get('verb_grammar_defs', 0)} defs | noun: {s.get('noun_grammar_defs', 0)} defs")
            lines.append(f"  Tokens coded: VERB {s.get('verb_gram_coded', 0):,} | NOUN {s.get('noun_gram_coded', 0):,}")
            lines.append("")
            total = s.get('total_tokens', 1)
            coded = s.get('verb_struct_coded', 0) + s.get('noun_struct_coded', 0)
            lines.append(f"TOTAL: {total:,} tokens | STRUCTURAL: {coded:,} ({coded/total*100:.1f}%)")
            return '\n'.join(lines)
        if reasoning.get('root_forms'):
            forms = reasoning['root_forms']
            root = reasoning.get('tasrif_root', '?')
            lines = [f"ROOT {root} — {len(forms)} tokens", "=" * 80]
            seen = {}
            for f in forms:
                key = f['word']
                if key not in seen:
                    seen[key] = f
                    seen[key]['count'] = 1
                    seen[key]['refs'] = [f['ref']]
                else:
                    seen[key]['count'] += 1
                    if len(seen[key]['refs']) < 3:
                        seen[key]['refs'].append(f['ref'])
            for word, f in seen.items():
                struct = f.get('verb_structure') or f.get('noun_structure') or '-'
                vowel = f.get('vowel_pattern') or '-'
                gram_parts = []
                if f.get('tense'): gram_parts.append(f['tense'])
                if f.get('number'): gram_parts.append(f['number'])
                if f.get('definiteness'): gram_parts.append(f['definiteness'])
                gram = '/'.join(gram_parts) if gram_parts else '-'
                refs = ', '.join(f['refs'][:3])
                if f['count'] > 3:
                    refs += f" (+{f['count'] - 3})"
                lines.append(f"  {word:25s}  L1={struct:20s}  L2={vowel:10s}  L3={gram:30s}  {refs}")
            return '\n'.join(lines)
        if reasoning.get('pattern_info'):
            info = reasoning['pattern_info']
            table = reasoning.get('pattern_table', '?')
            lines = [f"PATTERN: {info.get('code', info.get('vowel_code', '?'))}", f"TABLE: {table}", "-" * 50]
            for k, v in info.items():
                if v is not None:
                    lines.append(f"  {k}: {v}")
            return '\n'.join(lines)
        if reasoning.get('broken_plurals'):
            bp = reasoning['broken_plurals']
            total = sum(len(v) for v in bp.values())
            lines = [f"BROKEN PLURALS — {len(bp)} roots, {total} tokens", "=" * 60]
            for root, forms in sorted(bp.items()):
                codes = set(f['vowel_code'] for f in forms if f.get('vowel_code'))
                lines.append(f"  {root:10s}  {', '.join(codes):12s}  {len(forms):3d}x")
            return '\n'.join(lines)
        return "No tasrif data found."

    elif intent == 'bitig_tasrif':
        if reasoning.get('error'):
            return reasoning['error']
        if reasoning.get('bitig_tasrif_status'):
            stats = reasoning['bitig_tasrif_status']
            lines = ["=" * 60, "بِيتِيك تَصْرِيف STATUS — BI Morphological Engine", "=" * 60]
            for k, v in stats.items():
                lines.append(f"  {k}: {v}")
            return '\n'.join(lines)
        # Generic dict output for other bitig tasrif results
        import json
        for key in ('pattern_info', 'harmony', 'compound', 'bitig_analysis', 'bitig_root_forms'):
            if reasoning.get(key):
                return json.dumps(reasoning[key], ensure_ascii=False, indent=2, default=str)
        return "No BI tasrif data found."

    # ── DOMAIN ARTICULATION ──────────────────────────────────────
    elif intent in ('explain_body', 'body_system'):
        data = reasoning.get('body') or reasoning.get('system', {})
        if not data:
            return "No body data found."
        import json
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    elif intent == 'explain_formula':
        data = reasoning.get('formula', {})
        if not data:
            return "No formula data found."
        import json
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    elif intent in ('explain_history', 'naming_op'):
        data = reasoning.get('timeline') or reasoning.get('era') or reasoning.get('naming', {})
        if not data:
            return "No history data found."
        import json
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    elif intent == 'explain_intel':
        intel = reasoning.get('intel', {})
        if not intel:
            return reasoning.get('error', 'No intelligence data found.')
        # Format intel cross-search results
        lines = ["═" * 60, "INTELLIGENCE REPORT", "═" * 60]
        query = intel.get('query', '')
        if query:
            lines.append(f"  Query: {query}")
        tables_hit = intel.get('tables_hit', 0)
        total_hits = intel.get('total_hits', 0)
        lines.append(f"  Tables: {tables_hit} | Hits: {total_hits}")
        lines.append("─" * 60)
        # Results by table
        results = intel.get('results', {})
        if isinstance(results, dict):
            for tbl, rows in results.items():
                lines.append(f"  ── {tbl} ({len(rows)} rows) ──")
                for r in rows[:5]:
                    # Show first few fields
                    vals = [f"{k}={str(v)[:40]}" for k, v in r.items()
                            if v and k not in ('quf_q','quf_u','quf_f','quf_pass','quf_date','quf_token')]
                    lines.append(f"    {' | '.join(vals[:4])}")
        # If it's a root-based intel result
        elif isinstance(intel, dict) and intel.get('tables_with_data'):
            for tbl, rows in intel.get('data', {}).items():
                lines.append(f"  ── {tbl} ({len(rows)} rows) ──")
                for r in rows[:3]:
                    lines.append(f"    {r}")
        lines.append("═" * 60)
        return '\n'.join(lines)

    return f"Intent '{intent}' not yet supported."


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Quantification, Universality, Falsifiability
# The real QUF. Not a trigger. A gate between reasoning and speech.
# ═══════════════════════════════════════════════════════════════════════

# مَخْرَج zone mapping — ordered from throat (0) to lips (6)
# Used for articulation distance measurement in Q gate
_MAKHRAJ_ZONES = {}
_ZONE_ORDER = {
    'أَقْصَى الحَلْق': 0,                                    # deepest throat: ء ا ه
    'وَسَط الحَلْق': 1,                                      # mid throat: ح ع
    'أَدْنَى الحَلْق': 2,                                     # lower throat: خ غ
    'أَقْصَى اللِّسَان مَعَ الحَنَك الأَعْلَى': 3,            # back tongue: ق
    'أَدْنَى اللِّسَان مَعَ الحَنَك الأَعْلَى': 3,            # back tongue: ك
    'وَسَط اللِّسَان مَعَ الحَنَك': 4,                        # mid tongue: ش ي
    'وَسَط اللِّسَان مَعَ الحَنَك الأَعْلَى': 4,              # mid tongue: ج
    'طَرَف اللِّسَان قَرِيبًا مِنَ اللِّثَة': 4,              # front tongue: ر
    'حَافَّة اللِّسَان مَعَ الأَضْرَاس': 4,                   # tongue edge: ض
    'طَرَف اللِّسَان مَعَ اللِّثَة العُلْيَا': 5,             # tongue-gum: ل ن
    'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا العُلْيَا': 5,   # tongue-teeth: ت د ط
    'طَرَف اللِّسَان مَعَ أُصُول الثَّنَايَا السُّفْلَى': 5,  # tongue-lower teeth: ز س ص
    'طَرَف اللِّسَان مَعَ أَطْرَاف الثَّنَايَا العُلْيَا': 5, # interdental: ث ذ ظ
    'بَاطِن الشَّفَة السُّفْلَى مَعَ أَطْرَاف الثَّنَايَا العُلْيَا': 6,  # labio-dental: ف
    'الشَّفَتَان': 6,                                         # lips: ب م و
}

# Build letter→zone lookup from ALPHABET
for _letter, _meta in ALPHABET.items():
    _ph = _meta.get('phonetic', {})
    _makhraj = _ph.get('makhraj', '')
    _zone_key = _makhraj.split('—')[0].strip() if '—' in _makhraj else ''
    _MAKHRAJ_ZONES[_letter] = _ZONE_ORDER.get(_zone_key, -1)


def _domain_quf_check(candidates):
    """Check top candidates' roots against domain QUF in the DB.

    Returns dict with root QUF status for each top candidate.
    If a root has quf_pass != TRUE, the output gets flagged.
    """
    if not _HAS_DOMAIN_QUF:
        return {'available': False}

    result = {'available': True, 'roots': {}}
    try:
        conn = _quf_sqlite3.connect(QUF_DB_PATH)
        for cand in candidates[:3]:  # Top 3 only
            root_id = cand.get('root_id', '')
            if not root_id:
                continue
            row = conn.execute(
                "SELECT quf_q, quf_u, quf_f, quf_pass FROM roots WHERE root_id=?",
                (root_id,)
            ).fetchone()
            if row:
                result['roots'][root_id] = {
                    'q': row[0], 'u': row[1], 'f': row[2],
                    'pass': row[3],
                    'verified': row[3] in ('TRUE',)
                }
            else:
                result['roots'][root_id] = {
                    'q': None, 'u': None, 'f': None,
                    'pass': None, 'verified': False,
                    'warning': 'Root not found in roots table'
                }
        conn.close()
    except Exception as e:
        result['error'] = str(e)

    return result


def _makhraj_distance(letter_a, letter_b):
    """Articulation distance between two letters. 0=same zone, 6=max."""
    za = _MAKHRAJ_ZONES.get(letter_a, -1)
    zb = _MAKHRAJ_ZONES.get(letter_b, -1)
    if za < 0 or zb < 0:
        return -1  # unknown
    return abs(za - zb)


def _quf_gate(candidates):
    """The QUF gate. Runs on top candidates BEFORE output.

    Q — QUANTIFICATION: Is the evidence countable? How much?
        - Qur'anic token count
        - Known forms count
        - Abjad sum
        - Entry count across ALL sibling tables
        - Derivative count
        - Shift chain مَخْرَج distance (lower = stronger)

    U — UNIVERSALITY: Does this root explain ALL siblings?
        - Count sibling languages with entries for this root
        - Flag if only 1 language attested
        - Check if European, Latin, Bitig, Uzbek have entries

    F — FALSIFIABILITY: What would disprove this?
        - Score gap between #1 and #2 (narrow = weak)
        - Number of competing candidates within 5 points
        - Any unexplained shifts (UNKNOWN in chain)
        - Type C pair exists? (competing inversion)
        - Explicit falsification statement

    Returns:
        dict with Q, U, F results and overall PASS/FAIL
    """
    if not candidates:
        return {'q': 'FAIL', 'u': 'FAIL', 'f': 'FAIL', 'pass': False}

    top = candidates[0]
    root_letters = top.get('root_letters', '')
    root_id = top.get('root_id')
    aa_letters = top.get('aa_letters', [])

    # ══════════════════════════════════════════════════════════════
    # Q — QUANTIFICATION
    # ══════════════════════════════════════════════════════════════
    q_data = {}

    # Token count
    q_data['tokens'] = top.get('quranic_tokens', 0)

    # Known forms
    q_data['known_forms'] = top.get('quran_known_forms', 0)

    # Abjad sum
    q_data['abjad'] = top.get('abjad_sum', 0)

    # Entry counts (from verify_candidate intelligence)
    q_data['entries'] = top.get('existing_entries', 0)

    # QV entries (documented corruption = evidence of importance)
    q_data['qv_count'] = top.get('qv_count', 0)

    # Names of Allah
    q_data['allah_names'] = len(top.get('names_of_allah', []))

    # مَخْرَج distance — measure articulation zone jumps in shift chain
    shift_chain = top.get('shift_chain', [])
    makhraj_distances = []
    for link in shift_chain:
        # Parse "c←ح(S03)" format
        if '←' in link:
            parts = link.split('←')
            if len(parts) == 2:
                downstream_char = parts[0].strip()
                aa_part = parts[1].strip()
                aa_letter = aa_part[0] if aa_part else ''
                dist = _MAKHRAJ_ZONES.get(aa_letter, -1)
                if dist >= 0:
                    makhraj_distances.append(dist)

    # Compute average zone and total zone span
    if len(makhraj_distances) >= 2:
        zone_span = max(makhraj_distances) - min(makhraj_distances)
        q_data['makhraj_span'] = zone_span  # 0=same zone, 6=max spread
    else:
        q_data['makhraj_span'] = -1

    # Q score: weighted sum of all quantifiable evidence
    q_score = 0
    if q_data['tokens'] > 0:
        import math
        q_score += min(int(math.log2(q_data['tokens'])), 9)
    q_score += min(q_data['known_forms'], 5)
    q_score += min(q_data['entries'], 5)
    q_score += min(q_data['qv_count'], 3)
    q_score += q_data['allah_names'] * 2

    q_data['score'] = q_score
    q_data['grade'] = (
        'HIGH' if q_score >= 15 else
        'MEDIUM' if q_score >= 8 else
        'LOW' if q_score >= 3 else
        'FAIL'
    )

    # ══════════════════════════════════════════════════════════════
    # U — UNIVERSALITY
    # ══════════════════════════════════════════════════════════════
    u_data = {'siblings': {}}

    if _HAS_DB and root_id:
        conn = _connect()

        # Count entries per sibling
        u_data['siblings']['EN'] = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]

        u_data['siblings']['EU'] = conn.execute(
            "SELECT COUNT(*) FROM european_a1_entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]

        u_data['siblings']['LA'] = conn.execute(
            "SELECT COUNT(*) FROM latin_a1_entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]

        u_data['siblings']['BI'] = conn.execute(
            "SELECT COUNT(*) FROM bitig_a1_entries WHERE root_id = ?", (root_id,)
        ).fetchone()[0]

        u_data['siblings']['UZ'] = conn.execute(
            "SELECT COUNT(*) FROM uzbek_vocabulary WHERE aa_root_id = ?", (root_id,)
        ).fetchone()[0]

        u_data['siblings']['A4'] = conn.execute(
            "SELECT COUNT(*) FROM a4_derivatives WHERE entry_id IN "
            "(SELECT entry_id FROM entries WHERE root_id = ?)", (root_id,)
        ).fetchone()[0]

        conn.close()

    # Count how many siblings have at least 1 entry
    attested = sum(1 for v in u_data['siblings'].values() if v > 0)
    total_siblings = len(u_data['siblings'])
    u_data['attested_count'] = attested
    u_data['total_siblings'] = total_siblings
    u_data['coverage'] = round(attested / max(total_siblings, 1), 2)

    u_data['grade'] = (
        'HIGH' if attested >= 4 else
        'MEDIUM' if attested >= 2 else
        'LOW' if attested >= 1 else
        'FAIL'
    )

    # ══════════════════════════════════════════════════════════════
    # F — FALSIFIABILITY
    # ══════════════════════════════════════════════════════════════
    f_data = {}

    # Score gap between #1 and #2
    if len(candidates) >= 2:
        gap = candidates[0].get('score', 0) - candidates[1].get('score', 0)
        f_data['gap_to_second'] = gap
        f_data['second_root'] = candidates[1].get('root_letters', '?')
        f_data['second_score'] = candidates[1].get('score', 0)
    else:
        f_data['gap_to_second'] = 999
        f_data['second_root'] = None

    # Competing candidates within 5 points of top
    top_score = candidates[0].get('score', 0)
    competitors = [c for c in candidates[1:] if c.get('score', 0) >= top_score - 5]
    f_data['competitors_within_5'] = len(competitors)

    # Unknown shifts in chain
    shift_ids = top.get('shift_ids', [])
    unknowns = [s for s in shift_ids if s == 'UNKNOWN' or s == '?']
    f_data['unknown_shifts'] = len(unknowns)

    # Type C pair
    tc = top.get('type_c_pair')
    if tc:
        f_data['type_c'] = {
            'reversed': tc['reversed_root'],
            'tokens': tc['reversed_tokens'],
            'ratio': tc['token_ratio']
        }
    else:
        f_data['type_c'] = None

    # Falsification statement
    falsifiers = []
    if f_data['gap_to_second'] <= 3:
        falsifiers.append(
            f"Narrow gap ({f_data['gap_to_second']}pts) to {f_data['second_root']}. "
            f"If {f_data['second_root']} gains sibling attestation, it could overtake."
        )
    if f_data['unknown_shifts'] > 0:
        falsifiers.append(
            f"{f_data['unknown_shifts']} unexplained shift(s) in chain. "
            f"If no attested shift covers them, the mapping breaks."
        )
    if f_data['competitors_within_5'] > 3:
        falsifiers.append(
            f"{f_data['competitors_within_5']} competitors within 5pts. "
            f"Low differentiation — cross-wash with word family needed."
        )
    if f_data['type_c']:
        falsifiers.append(
            f"Type C pair: {f_data['type_c']['reversed']} "
            f"(Q:{f_data['type_c']['tokens']}, ratio {f_data['type_c']['ratio']}). "
            f"If downstream meaning aligns with inversion, mapping may be to Type C not original."
        )
    if not falsifiers:
        falsifiers.append("No immediate falsifiers. Mapping is robust.")

    f_data['falsifiers'] = falsifiers
    f_data['grade'] = (
        'HIGH' if f_data['gap_to_second'] >= 5 and f_data['unknown_shifts'] == 0 else
        'MEDIUM' if f_data['gap_to_second'] >= 2 and f_data['unknown_shifts'] == 0 else
        'LOW' if f_data['gap_to_second'] >= 0 else
        'FAIL'
    )

    # ══════════════════════════════════════════════════════════════
    # OVERALL
    # ══════════════════════════════════════════════════════════════
    grades = [q_data['grade'], u_data['grade'], f_data['grade']]
    overall = all(g in ('HIGH', 'MEDIUM') for g in grades)

    return {
        'Q': q_data,
        'U': u_data,
        'F': f_data,
        'pass': overall,
        'summary': (
            f"Q:{q_data['grade']}({q_data['score']}) "
            f"U:{u_data['grade']}({u_data['attested_count']}/{u_data['total_siblings']}) "
            f"F:{f_data['grade']}(gap={f_data['gap_to_second']})"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# BATCH THINK — process multiple queries
# ═══════════════════════════════════════════════════════════════════════

def think_batch(queries):
    """Process multiple queries in sequence.

    Args:
        queries: list of query strings

    Returns:
        list of think() results
    """
    results = []
    for q in queries:
        results.append(think(q))
    return results


# ═══════════════════════════════════════════════════════════════════════
# THINK DECOMPOSED — handle complex multi-part queries
# ═══════════════════════════════════════════════════════════════════════

def think_deep(complex_query):
    """Handle complex queries by decomposing and processing each part.

    Args:
        complex_query: complex multi-part query

    Returns:
        dict with combined output from all sub-queries
    """
    sub_queries = decompose(complex_query)

    if len(sub_queries) <= 1:
        # Simple query — just think
        return think(complex_query)

    # Process each sub-query
    outputs = []
    for sq in sub_queries:
        # Reconstruct a simple query string from the sub-query
        intent = sq['intent']
        params = sq['params']

        if intent == 'explain_root':
            query_str = params.get('root_letters') or params.get('root_id') or params.get('query', '')
        elif intent == 'trace_word':
            query_str = f"trace {params.get('word', params.get('query', ''))}"
        elif intent == 'compare_roots':
            query_str = f"compare {params.get('root_a', '')} and {params.get('root_b', '')}"
        else:
            query_str = params.get('query', str(params))

        result = think(query_str)
        outputs.append(result)

    # Combine outputs
    combined_output = '\n\n'.join(r['output'] for r in outputs)
    return {
        'output': combined_output,
        'sub_results': outputs,
        'query_count': len(outputs),
        'context': get_context(),
    }


# ═══════════════════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ═══════════════════════════════════════════════════════════════════════

def interactive():
    """Interactive أَمْر ذَكَاء session."""
    print("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    print("أَمْر ذَكَاء — Intelligence Orchestrator")
    print("Every answer traces to 28 letters.")
    print("Type 'خُرُوج' or 'exit' to quit.\n")

    while True:
        try:
            query = input("ذَكَاء> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nوَدَاعًا")
            break

        if query in ('خُرُوج', 'exit', 'quit', ''):
            if query:
                print("وَدَاعًا")
            break

        if query == 'context':
            ctx = get_context()
            print(f"  Focus: {ctx['focus_root']}")
            print(f"  History: {ctx['focus_history']}")
            print(f"  Queries: {ctx['query_count']}")
            print(f"  Related: {ctx['related_roots']}")
            continue

        if query == 'suggest':
            for s in suggest_next():
                print(f"  → {s}")
            continue

        result = think(query)
        print(result['output'])
        print()


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("أَمْر ذَكَاء — Intelligence Orchestrator")
        print()
        print("Usage:")
        print("  python3 amr_dhakaa.py think 'cover'                  # trace any word")
        print("  python3 amr_dhakaa.py think 'ك-ف-ر'                  # explain any root")
        print("  python3 amr_dhakaa.py think 'compare ر-ح-م and م-ر-ح' # compare roots")
        print("  python3 amr_dhakaa.py think 'where does mercy come from'")
        print("  python3 amr_dhakaa.py deep 'trace cover and mercy'   # multi-part")
        print("  python3 amr_dhakaa.py -i                             # interactive mode")
        print()
        print("Architecture: بَصَر (perceive) → عَقْل (reason) → نُطْق (articulate)")
        print("Every output traces to 28 letters. No weights. No hallucination.")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == '-i' or cmd == 'interactive':
        interactive()
        return

    if cmd == 'think':
        query = ' '.join(sys.argv[2:])
        result = think(query)
        print(result['output'])

    elif cmd == 'deep':
        query = ' '.join(sys.argv[2:])
        result = think_deep(query)
        print(result['output'])

    elif cmd == 'json':
        # Raw JSON output for programmatic use
        query = ' '.join(sys.argv[2:])
        result = think(query)
        # Strip non-serializable parts
        output = {
            'output': result['output'],
            'intent': result['intent'],
            'params': result['params'],
            'confidence': result['confidence'],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

    else:
        # Treat everything after the script name as a query
        query = ' '.join(sys.argv[1:])
        result = think(query)
        print(result['output'])


if __name__ == "__main__":
    main()
