#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر بَصَر — PERCEPTION ENGINE

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Root: ب-ص-ر — to see, perceive, discern
Q67:4 يَنقَلِبْ إِلَيْكَ ٱلْبَصَرُ — the vision returns to you

The بَصَر perceives. It understands what the user MEANS.

Input layer of the أَمْر AI. Takes raw user input and produces
structured intent that the عَقْل can reason about and the نُطْق can articulate.

Functions:
  perceive(user_input)       → structured intent + parameters
  decompose(complex_query)   → ordered sub-queries
  detect_root(word, lang)    → root_id via DB + shift reversal
  track_context(history)     → current focus root/topic
  classify_input(text)       → input type classification
"""

import sys
import os
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from uslap_db_connect import connect as _connect
    _HAS_DB = True
except ImportError:
    _HAS_DB = False

try:
    from amr_aql import (
        deduce_meaning, reverse_trace, expand_root, relate_roots,
        hypothesise, verify_candidate, extract_consonants
    )
    _HAS_AQL = True
except ImportError:
    _HAS_AQL = False

from amr_alphabet import ABJAD


# ═══════════════════════════════════════════════════════════════════════
# INPUT TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

# Intent patterns — what the user is asking for
INTENT_PATTERNS = {
    # Root operations
    'explain_root': [
        r'explain\s+(?:root\s+)?([A-Z]\d+|[\u0621-\u064A][\-\u0621-\u064A]+)',
        r'what\s+(?:does|is)\s+(?:root\s+)?([A-Z]\d+|[\u0621-\u064A][\-\u0621-\u064A]+)',
        r'tell\s+me\s+about\s+(?:root\s+)?([A-Z]\d+|[\u0621-\u064A][\-\u0621-\u064A]+)',
    ],
    'trace_word': [
        r'trace\s+(?:the\s+word\s+)?["\']?(\w+)["\']?',
        r'where\s+does\s+["\']?(\w+)["\']?\s+come\s+from',
        r'root\s+of\s+["\']?(\w+)["\']?',
        r'find\s+root\s+(?:for\s+)?["\']?(\w+)["\']?',
    ],
    'compare_roots': [
        r'compare\s+([\u0621-\u064A][\-\u0621-\u064A]+)\s+(?:and|vs|with|to)\s+([\u0621-\u064A][\-\u0621-\u064A]+)',
        r'relate\s+([\u0621-\u064A][\-\u0621-\u064A]+)\s+(?:and|to|with)\s+([\u0621-\u064A][\-\u0621-\u064A]+)',
        r'([\u0621-\u064A][\-\u0621-\u064A]+)\s+vs\s+([\u0621-\u064A][\-\u0621-\u064A]+)',
    ],
    'search_lattice': [
        r'search\s+(?:for\s+)?["\']?(.+?)["\']?$',
        r'find\s+(?:entry\s+)?["\']?(.+?)["\']?$',
        r'look\s+up\s+["\']?(.+?)["\']?$',
    ],
    'get_entry': [
        r'(?:show|get|display)\s+entry\s+([A-Z]{2}\d+)',
        r'entry\s+([A-Z]{2}\d+)',
    ],
    'lattice_state': [
        r'(?:show\s+)?(?:lattice\s+)?state',
        r'(?:show\s+)?(?:lattice\s+)?summary',
        r'how\s+many',
        r'current\s+state',
    ],
    'report': [
        r'(?:generate|create|make)\s+(?:a\s+)?report\s+(?:for\s+)?([A-Z]\d+|[\u0621-\u064A][\-\u0621-\u064A]+)',
        r'intelligence\s+(?:on|for|about)\s+([A-Z]\d+|[\u0621-\u064A][\-\u0621-\u064A]+)',
    ],
    # Domain reasoning intents
    'explain_body': [
        r'(?:what\s+(?:does|is)\s+)?(?:root\s+)?(.+?)\s+(?:in|for)\s+(?:the\s+)?body',
        r'body\s+(?:of|for)\s+(.+)',
        r'(?:which|what)\s+(?:root|organ|system)\s+governs?\s+(?:the\s+)?(.+)',
        r'(?:heal|cure|therapy)\s+(?:for\s+)?(.+)',
    ],
    'body_system': [
        r'(?:show|explain|describe)\s+(?:the\s+)?(?:body\s+)?(heart|nafs|sensory|skeletal|nutrition|prayer|lifecycle|therapy|architecture|diagnostic)\s*(?:system)?',
        r'(heart|nafs|sensory|skeletal|nutrition|prayer|lifecycle)\s+(?:system|lattice|map)',
    ],
    'explain_formula': [
        r'(?:what\s+)?formula(?:s)?\s+(?:for|of|using)\s+(.+)',
        r'(?:show|explain)\s+formula\s+(.+)',
        r'ratio(?:s)?\s+(?:for|of|in)\s+(.+)',
    ],
    'explain_history': [
        r'(?:when|how)\s+was\s+(.+?)\s+deployed',
        r'timeline\s+(?:of|for)\s+(.+)',
        r'(?:show|explain)\s+era\s+(\d+)',
        r'(?:deployment|history)\s+(?:of|for)\s+(.+)',
    ],
    'naming_op': [
        r'(?:how\s+was\s+)?(.+?)\s+renamed',
        r'naming\s+(?:operation|inversion)\s+(?:of|for)\s+(.+)',
        r'(?:original|real)\s+name\s+(?:of|for)\s+(.+)',
    ],
    'explain_intel': [
        r'(?:what\s+)?(?:intelligence|intel)\s+(?:on|for|about)?\s*(.+)',
        r'confession(?:s)?\s+(?:about|for|on)?\s*(.+)',
        r'extraction\s+(?:of|for|in)?\s*(.+)',
        r'(?:who|what)\s+confessed\s+(?:about\s+)?(.+)',
    ],
    'batch_operation': [
        r'batch\s+(.+)',
        r'process\s+all\s+(.+)',
    ],
    # QUF operations
    'quf_validate': [
        r'quf\s+(?:validate\s+)?(?:entry\s+)?(\d+)',
        r'validate\s+(?:entry\s+)?(\d+)',
        r'quf\s+(\w+)\s+(\d+)',
        r'quf\s+([\w_]+)',
    ],
    'quf_status': [
        r'quf\s+status',
        r'quf\s+coverage',
        r'coverage',
    ],
    # Detection patterns
    'explain_detection': [
        r'(?:what\s+is\s+)?(?:detection\s+pattern\s+)?(DP\d+)',
        r'(?:explain\s+)?(DP\d+)',
        r'detection\s+(?:pattern\s+)?(.+)',
    ],
    # Keywords
    'explain_keyword': [
        r'keyword\s+([\u0621-\u064A]+)',
        r'(?:explain\s+)?keyword\s+(\w+)',
    ],
    # Bitig tasrif MUST come before tasrif (longer prefix match)
    'bitig_tasrif': [
        r'bitig\s+tasrif\s+status',
        r'bitig\s+tasrif\s+pattern\s+(\w+)',
        r'bitig\s+tasrif\s+harmony\s+(.+)',
        r'bitig\s+tasrif\s+compound\s+(.+)',
        r'bitig\s+tasrif\s+analyze\s+(.+)',
        r'bitig\s+tasrif\s+(\w+)',
    ],
    # AA Tasrif (must NOT match "bitig tasrif")
    'tasrif': [
        r'(?<!bitig\s)tasrif\s+status',
        r'(?<!bitig\s)tasrif\s+broken_plurals',
        r'(?<!bitig\s)tasrif\s+pattern\s+(\w+)',
        r'(?<!bitig\s)tasrif\s+([\u0621-\u064A][\-\u0621-\u064A]+)',
        r'(?<!bitig\s)tasrif\s+(\w[\-\w]+)',
    ],
}


def classify_input(text):
    """Classify user input into an intent type.

    Args:
        text: raw user input string

    Returns:
        dict with:
            intent: intent name
            params: extracted parameters
            confidence: HIGH/MEDIUM/LOW
    """
    text = text.strip()

    # Direct root input (just AA letters with hyphens)
    if re.match(r'^[\u0621-\u064A][\-\u0621-\u064A]+$', text):
        return {
            'intent': 'explain_root',
            'params': {'root_letters': text},
            'confidence': 'HIGH',
        }

    # Direct root_id input
    if re.match(r'^[RT]\d+$', text):
        return {
            'intent': 'explain_root',
            'params': {'root_id': text},
            'confidence': 'HIGH',
        }

    # Direct entry_id input
    if re.match(r'^(EN|RU|FA|EU|BI|LA|UZ)\d+$', text):
        return {
            'intent': 'get_entry',
            'params': {'entry_id': text},
            'confidence': 'HIGH',
        }

    # Try pattern matching
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                params = {}
                if intent == 'compare_roots':
                    params = {'root_a': groups[0], 'root_b': groups[1]}
                elif groups:
                    params = {'query': groups[0]}
                return {
                    'intent': intent,
                    'params': params,
                    'confidence': 'HIGH',
                }

    # Fallback: if it's a single word, try tracing it
    if re.match(r'^[a-zA-Z]+$', text):
        return {
            'intent': 'trace_word',
            'params': {'word': text.lower(), 'language': 'en'},
            'confidence': 'MEDIUM',
        }

    # Single Cyrillic word
    if re.match(r'^[а-яА-ЯёЁ]+$', text):
        return {
            'intent': 'trace_word',
            'params': {'word': text.lower(), 'language': 'ru'},
            'confidence': 'MEDIUM',
        }

    # Arabic word (not root format)
    if re.match(r'^[\u0621-\u064A\u0640-\u065F]+$', text):
        return {
            'intent': 'search_lattice',
            'params': {'query': text},
            'confidence': 'MEDIUM',
        }

    # Fallback: general search
    return {
        'intent': 'search_lattice',
        'params': {'query': text},
        'confidence': 'LOW',
    }


# ═══════════════════════════════════════════════════════════════════════
# PERCEIVE — main perception function
# ═══════════════════════════════════════════════════════════════════════

def perceive(user_input):
    """Understand what the user MEANS from their input.

    This is the primary entry point for the بَصَر.

    Args:
        user_input: raw text from user

    Returns:
        dict with:
            intent: what the user wants
            params: extracted parameters
            confidence: HIGH/MEDIUM/LOW
            enriched: additional context from DB
            sub_queries: if decomposed into parts
    """
    classification = classify_input(user_input)

    result = {
        'raw_input': user_input,
        'intent': classification['intent'],
        'params': classification['params'],
        'confidence': classification['confidence'],
        'enriched': {},
        'sub_queries': [],
    }

    # Enrich with DB context
    _enrich(result)

    return result


def _enrich(result):
    """Add DB context to a classified input."""
    if not _HAS_DB:
        return

    intent = result['intent']
    params = result['params']
    conn = _connect()

    try:
        if intent == 'explain_root':
            root_ref = params.get('root_id') or params.get('root_letters') or params.get('query')
            if root_ref:
                # Check if root exists
                row = None
                if root_ref.startswith('R') or root_ref.startswith('T'):
                    row = conn.execute(
                        "SELECT root_id, root_letters, quran_tokens, primary_meaning FROM roots WHERE root_id = ?",
                        (root_ref,)
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT root_id, root_letters, quran_tokens, primary_meaning FROM roots WHERE root_letters = ?",
                        (root_ref,)
                    ).fetchone()
                if row:
                    result['enriched'] = {
                        'root_found': True,
                        'root_id': row['root_id'],
                        'root_letters': row['root_letters'],
                        'quran_tokens': row['quran_tokens'],
                        'primary_meaning': row['primary_meaning'],
                    }
                else:
                    result['enriched'] = {'root_found': False}

        elif intent == 'trace_word':
            word = params.get('word') or params.get('query', '')
            lang = params.get('language', 'en')
            # Check if word already exists as an entry
            if lang == 'en':
                row = conn.execute(
                    "SELECT entry_id, root_id, en_term FROM entries WHERE LOWER(en_term) = ? LIMIT 1",
                    (word.lower(),)
                ).fetchone()
            elif lang == 'ru':
                row = conn.execute(
                    "SELECT entry_id, root_id, ru_term FROM entries WHERE LOWER(ru_term) = ? LIMIT 1",
                    (word.lower(),)
                ).fetchone()
            else:
                row = None

            if row:
                result['enriched'] = {
                    'existing_entry': True,
                    'entry_id': row['entry_id'],
                    'root_id': row['root_id'],
                }
            else:
                result['enriched'] = {'existing_entry': False}

        elif intent == 'get_entry':
            entry_id = params.get('entry_id') or params.get('query', '')
            row = conn.execute(
                "SELECT entry_id, en_term, root_id, root_letters FROM entries WHERE entry_id = ?",
                (entry_id,)
            ).fetchone()
            if row:
                result['enriched'] = {
                    'entry_found': True,
                    'entry_id': row['entry_id'],
                    'en_term': row['en_term'],
                    'root_id': row['root_id'],
                    'root_letters': row['root_letters'],
                }
            else:
                result['enriched'] = {'entry_found': False}

        elif intent == 'search_lattice':
            query = params.get('query', '')
            # Quick search across entries
            hits = conn.execute(
                "SELECT entry_id, en_term, root_id FROM entries "
                "WHERE LOWER(en_term) LIKE ? OR LOWER(ru_term) LIKE ? "
                "OR LOWER(fa_term) LIKE ? LIMIT 5",
                (f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%')
            ).fetchall()
            result['enriched'] = {
                'hit_count': len(hits),
                'hits': [dict(h) for h in hits],
            }

    except Exception:
        pass
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════
# DECOMPOSE — break complex queries into sub-queries
# ═══════════════════════════════════════════════════════════════════════

def decompose(complex_query):
    """Break a complex query into ordered sub-queries.

    Examples:
        "trace 'cover' and compare it with 'market'" →
            [trace_word('cover'), trace_word('market'), compare_roots(...)]

        "explain ك-ف-ر and show all European downstream" →
            [explain_root('ك-ف-ر'), search_european(root_id)]

    Args:
        complex_query: user's full query text

    Returns:
        list of sub-query dicts, each with intent + params
    """
    sub_queries = []

    # Split on 'and', 'then', 'also', commas
    parts = re.split(r'\s+(?:and|then|also|,)\s+', complex_query, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if part:
            classification = classify_input(part)
            sub_queries.append(classification)

    # If only one part and it's complex, try to detect compound intents
    if len(sub_queries) == 1 and sub_queries[0]['confidence'] == 'LOW':
        # Try word-by-word
        words = complex_query.split()
        # Look for multiple root/word references
        roots_found = []
        words_found = []
        for w in words:
            if re.match(r'^[\u0621-\u064A][\-\u0621-\u064A]+$', w):
                roots_found.append(w)
            elif re.match(r'^[RT]\d+$', w):
                roots_found.append(w)
            elif re.match(r'^[a-zA-Z]{2,}$', w) and w.lower() not in (
                'the', 'and', 'or', 'is', 'what', 'how', 'why', 'show',
                'get', 'find', 'trace', 'compare', 'explain', 'search'
            ):
                words_found.append(w)

        if len(roots_found) == 2:
            sub_queries = [{
                'intent': 'compare_roots',
                'params': {'root_a': roots_found[0], 'root_b': roots_found[1]},
                'confidence': 'MEDIUM',
            }]
        elif len(roots_found) == 1:
            sub_queries = [{
                'intent': 'explain_root',
                'params': {'root_letters': roots_found[0]},
                'confidence': 'MEDIUM',
            }]

    return sub_queries


# ═══════════════════════════════════════════════════════════════════════
# DETECT ROOT — find root for any word in any language
# ═══════════════════════════════════════════════════════════════════════

def detect_root(word, language='auto'):
    """Detect the AA root of any word in any language.

    Pipeline:
    1. Auto-detect language if needed
    2. Check DB for existing entry
    3. If not found, run reverse shift via عَقْل
    4. Return best candidate with provenance

    Args:
        word: input word in any language
        language: 'en', 'ru', 'fa', 'auto' (auto-detect)

    Returns:
        dict with:
            word, language, root_id, root_letters, confidence,
            source (DB or COMPUTED), shift_chain
    """
    # Auto-detect language
    if language == 'auto':
        language = _detect_language(word)

    result = {
        'word': word,
        'language': language,
        'root_id': None,
        'root_letters': None,
        'confidence': None,
        'source': None,
        'shift_chain': [],
    }

    # Step 1: Check DB for existing entry
    if _HAS_DB:
        conn = _connect()
        row = None

        if language == 'en':
            row = conn.execute(
                "SELECT entry_id, root_id, root_letters, phonetic_chain FROM entries "
                "WHERE LOWER(en_term) = ? LIMIT 1",
                (word.lower(),)
            ).fetchone()
        elif language == 'ru':
            row = conn.execute(
                "SELECT entry_id, root_id, root_letters, phonetic_chain FROM entries "
                "WHERE LOWER(ru_term) = ? LIMIT 1",
                (word.lower(),)
            ).fetchone()
        elif language == 'fa':
            row = conn.execute(
                "SELECT entry_id, root_id, root_letters, phonetic_chain FROM entries "
                "WHERE LOWER(fa_term) = ? LIMIT 1",
                (word.lower(),)
            ).fetchone()

        # Check European
        if not row:
            row = conn.execute(
                "SELECT entry_id, root_id FROM european_a1_entries "
                "WHERE LOWER(term) = ? LIMIT 1",
                (word.lower(),)
            ).fetchone()

        # Check Bitig
        if not row:
            row = conn.execute(
                "SELECT entry_id, root_id FROM bitig_a1_entries "
                "WHERE LOWER(term) = ? LIMIT 1",
                (word.lower(),)
            ).fetchone()

        # Check Uzbek
        if not row:
            row = conn.execute(
                "SELECT id, aa_root_id FROM uzbek_vocabulary "
                "WHERE LOWER(latin_form) = ? OR LOWER(cyrillic_form) = ? LIMIT 1",
                (word.lower(), word.lower())
            ).fetchone()
            if row:
                result['root_id'] = row['aa_root_id']
                result['source'] = 'DB_UZBEK'
                # Get root letters
                if result['root_id']:
                    root_row = conn.execute(
                        "SELECT root_letters FROM roots WHERE root_id = ?",
                        (result['root_id'],)
                    ).fetchone()
                    if root_row:
                        result['root_letters'] = root_row['root_letters']
                result['confidence'] = 'HIGH'
                conn.close()
                return result

        if row:
            row = dict(row)
            result['root_id'] = row['root_id']
            result['root_letters'] = row.get('root_letters', '')
            result['source'] = 'DB'
            result['confidence'] = 'HIGH'
            if row.get('phonetic_chain'):
                result['shift_chain'] = row['phonetic_chain'].split(',')

            # Get root_letters if we have root_id but not letters
            if result['root_id'] and not result['root_letters']:
                root_row = conn.execute(
                    "SELECT root_letters FROM roots WHERE root_id = ?",
                    (result['root_id'],)
                ).fetchone()
                if root_row:
                    result['root_letters'] = root_row['root_letters']

            conn.close()
            return result

        conn.close()

    # Step 2: Run reverse shift via عَقْل
    if _HAS_AQL:
        candidates = hypothesise(word, language)
        if candidates:
            top = candidates[0]
            result['root_letters'] = top['root_letters']
            result['root_id'] = top.get('root_id')
            result['source'] = 'COMPUTED'
            result['shift_chain'] = top['shift_chain']
            if top.get('verified'):
                result['confidence'] = 'HIGH' if top.get('quranic_tokens', 0) > 50 else 'MEDIUM'
            else:
                result['confidence'] = 'LOW'

    return result


def _detect_language(word):
    """Auto-detect language from script."""
    if re.match(r'^[\u0621-\u064A\u0640-\u065F]+$', word):
        return 'ar'
    if re.match(r'^[а-яА-ЯёЁ]+$', word):
        return 'ru'
    if re.match(r'^[\u0600-\u06FF]+$', word):
        return 'fa'  # Could also be Arabic — FA has same script range
    return 'en'


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT TRACKER — maintain focus across a session
# ═══════════════════════════════════════════════════════════════════════

class ContextTracker:
    """Tracks the user's focus root/topic across a session.

    Maintains:
        - Current focus root(s)
        - Recent queries
        - Related roots discovered
        - Pending operations
    """

    def __init__(self):
        self.focus_roots = []       # stack of root_ids/letters currently in focus
        self.recent_queries = []    # last N queries
        self.related_roots = set()  # roots discovered during session
        self.pending_ops = []       # operations waiting for user confirmation
        self.max_history = 20

    def update(self, perception_result):
        """Update context with a new perception result.

        Args:
            perception_result: dict from perceive()
        """
        self.recent_queries.append({
            'input': perception_result['raw_input'],
            'intent': perception_result['intent'],
            'params': perception_result['params'],
        })
        if len(self.recent_queries) > self.max_history:
            self.recent_queries.pop(0)

        # Update focus roots
        enriched = perception_result.get('enriched', {})
        root_id = enriched.get('root_id')
        root_letters = enriched.get('root_letters')

        if root_id:
            if root_id not in self.focus_roots:
                self.focus_roots.append(root_id)
            if len(self.focus_roots) > 5:
                self.focus_roots.pop(0)

        if root_letters:
            self.related_roots.add(root_letters)

    def get_current_focus(self):
        """Get the current focus root."""
        return self.focus_roots[-1] if self.focus_roots else None

    def get_context_summary(self):
        """Get a summary of current context."""
        return {
            'focus_root': self.get_current_focus(),
            'focus_history': list(self.focus_roots),
            'query_count': len(self.recent_queries),
            'related_roots': list(self.related_roots),
            'pending_ops': len(self.pending_ops),
        }

    def suggest_next(self):
        """Suggest what the user might want to do next.

        Based on current context, suggest relevant follow-up operations.
        """
        suggestions = []
        focus = self.get_current_focus()

        if focus:
            suggestions.append(f"expand {focus} — view full downstream tree")
            suggestions.append(f"report {focus} — generate intelligence report")

        if len(self.focus_roots) >= 2:
            suggestions.append(
                f"compare {self.focus_roots[-1]} {self.focus_roots[-2]} — structural comparison"
            )

        if not focus:
            suggestions.append("Type any word to trace its root")
            suggestions.append("Type a root (e.g. ك-ف-ر) to explain it")

        return suggestions


# Global tracker instance
_tracker = ContextTracker()


def track_context(perception_result):
    """Update the global context tracker."""
    _tracker.update(perception_result)
    return _tracker.get_context_summary()


def get_context():
    """Get current context state."""
    return _tracker.get_context_summary()


def suggest_next():
    """Get suggestions for next action."""
    return _tracker.suggest_next()


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("أَمْر بَصَر — Perception Engine")
        print()
        print("Usage:")
        print("  python3 amr_basar.py perceive 'explain ك-ف-ر'   # full perception")
        print("  python3 amr_basar.py classify 'cover'           # classify input")
        print("  python3 amr_basar.py detect cover               # detect root")
        print("  python3 amr_basar.py detect cover en            # detect with language")
        print("  python3 amr_basar.py decompose 'trace X and Y'  # decompose query")
        sys.exit(0)

    cmd = sys.argv[1]
    arg = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''

    if cmd == 'perceive':
        result = perceive(arg)
        print(f"\nPERCEPTION: '{arg}'")
        print(f"  INTENT:     {result['intent']}")
        print(f"  PARAMS:     {result['params']}")
        print(f"  CONFIDENCE: {result['confidence']}")
        if result['enriched']:
            print(f"  ENRICHED:   {result['enriched']}")
        if result['sub_queries']:
            print(f"  SUB-QUERIES: {len(result['sub_queries'])}")

    elif cmd == 'classify':
        result = classify_input(arg)
        print(f"\nCLASSIFICATION: '{arg}'")
        print(f"  INTENT:     {result['intent']}")
        print(f"  PARAMS:     {result['params']}")
        print(f"  CONFIDENCE: {result['confidence']}")

    elif cmd == 'detect':
        parts = arg.split()
        word = parts[0] if parts else ''
        lang = parts[1] if len(parts) > 1 else 'auto'
        result = detect_root(word, lang)
        print(f"\nROOT DETECTION: '{word}' ({result['language']})")
        print(f"  ROOT_ID:    {result['root_id']}")
        print(f"  ROOT:       {result['root_letters']}")
        print(f"  SOURCE:     {result['source']}")
        print(f"  CONFIDENCE: {result['confidence']}")
        if result['shift_chain']:
            print(f"  CHAIN:      {' | '.join(str(s) for s in result['shift_chain'])}")

    elif cmd == 'decompose':
        results = decompose(arg)
        print(f"\nDECOMPOSITION: '{arg}'")
        print(f"  SUB-QUERIES: {len(results)}")
        for i, sq in enumerate(results):
            print(f"  [{i+1}] {sq['intent']} ({sq['confidence']}): {sq['params']}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# QUF GATE — Called by amr_quf.py router
# ═══════════════════════════════════════════════════════════════════════

def detection_quf(data: dict) -> dict:
    """
    DETECTION QUF — L9.
    Handles multiple table schemas:
    - qv_translation_register: ROOT, CORRUPTION_TYPE, CORRECT_TRANSLATION, COMMON_MISTRANSLATION
    - dp_register: dp_code, name, class, mechanism, qur_anchor
    - disputed_words: various columns
    - contamination_blacklist: contaminated_term, contaminated_translation
    - phonetic_reversal: various columns
    """
    GRADE_ORDER = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'FAIL': 1, 'PENDING': 0}

    # Unified field extraction across table schemas
    root = (data.get('ROOT', '') or data.get('root', '') or
            data.get('root_letters', '') or '')
    corruption_type = (data.get('CORRUPTION_TYPE', '') or data.get('corruption_type', '') or
                       data.get('class', '') or '')
    correct = (data.get('CORRECT_TRANSLATION', '') or data.get('correct_form', '') or
               data.get('mechanism', '') or '')
    wrong = (data.get('COMMON_MISTRANSLATION', '') or data.get('corrupted_form', '') or
             data.get('contaminated_translation', '') or '')
    ayat_count = data.get('AYAT_COUNT', 0) or data.get('ayat_count', 0) or 0
    dp_id = (data.get('dp_id', '') or data.get('DP_ID', '') or
             data.get('dp_code', '') or '')
    qur_anchor = (data.get('qur_anchor', '') or data.get('qur_ref', '') or '')
    name = data.get('name', '') or data.get('contaminated_term', '') or ''
    status = data.get('status', '') or ''
    example = data.get('example', '') or ''

    # Q: evidence counted
    q_items = sum([bool(root) or bool(name), bool(corruption_type),
                   int(ayat_count) > 0 or bool(qur_anchor), bool(dp_id)])
    q = 'HIGH' if q_items >= 3 else ('MEDIUM' if q_items >= 2 else ('LOW' if q_items >= 1 else 'FAIL'))
    q_ev = [f'root/name={bool(root or name)}, type={str(corruption_type)[:20]}, qur={bool(qur_anchor)}, dp={dp_id}']

    # U: pattern documented with examples/mechanism
    valid_types = {'ROOT_FLATTENED', 'ACTION_TO_ETHNIC', 'ATTRIBUTE_TO_GENERIC',
                   'SCOPE_NARROWED', 'ROOT_REPLACED', 'ROOT_INVERTED',
                   'LINGUISTIC', 'CIVILISATION', 'COVENANTAL'}
    type_valid = any(vt in str(corruption_type).upper() for vt in valid_types) if corruption_type else False
    has_mechanism = bool(correct) or bool(example)
    confirmed = str(status).upper() == 'CONFIRMED'

    if (type_valid and has_mechanism) or confirmed:
        u = 'HIGH'
    elif type_valid or has_mechanism:
        u = 'MEDIUM'
    else:
        u = 'LOW'
    u_ev = [f'Valid type: {type_valid}, mechanism: {has_mechanism}, confirmed: {confirmed}']

    # F: verifiable — qur_anchor or washed≠corrupted or distinct_from documented
    distinct = data.get('distinct_from', '') or ''
    if qur_anchor and (correct or distinct):
        f = 'HIGH'
        f_ev = [f'Quranic anchor + mechanism/distinction documented']
    elif correct and wrong and str(correct).strip() != str(wrong).strip():
        f = 'HIGH'
        f_ev = [f'Washed ({str(correct)[:20]}) != corrupted ({str(wrong)[:20]})']
    elif qur_anchor or correct:
        f = 'MEDIUM'
        f_ev = [f'Partial: qur_anchor={bool(qur_anchor)}, mechanism={bool(correct)}']
    else:
        f = 'LOW'
        f_ev = [f'No Quranic anchor or mechanism documented']

    passes = all(GRADE_ORDER.get(g, 0) >= 3 for g in [q, u, f])
    return {
        'q': q, 'u': u, 'f': f, 'pass': passes,
        'q_evidence': q_ev, 'u_evidence': u_ev, 'f_evidence': f_ev,
    }


if __name__ == "__main__":
    main()
