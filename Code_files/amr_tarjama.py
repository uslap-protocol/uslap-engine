#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر تَرْجَمَة — Root-Based Translation Engine

Root: ت-ر-ج-م (interpretation)

The first translation system that routes through ROOTS, not statistics.
Word → trace through time chain → find ROOT → fan out to ALL siblings.

Time chain (Uzbek-first):
  Kashgari (1072) → Navoi (1499) → Suleymanov/Shipova (modern) → today

Two originals:
  ORIG1 (AA, R###) → connects to EN, EU, LA, FA, RU
  ORIG2 (Bitig, root_letters) → connects to RU, HU, MN, Chuvash + downstream
"""

import sys
import os
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_uzbek import (
    detect_script, normalize, extract_consonants, strip_persian,
    strip_suffixes, to_all_scripts, cyrillic_to_latin, arabic_to_latin,
    latin_to_cyrillic, latin_to_arabic,
)
from amr_alphabet import compute_root_meaning, compute_root_meaning_text


# ═══════════════════════════════════════════════════════════════════════
# ERROR
# ═══════════════════════════════════════════════════════════════════════

class خَطَأ_تَرْجَمَة(Exception):
    """Translation engine error"""
    pass


# ═══════════════════════════════════════════════════════════════════════
# مُتَرْجِم — TRANSLATOR CLASS
# ═══════════════════════════════════════════════════════════════════════

class مُتَرْجِم:
    """
    Root-based translator.

    Usage:
        م = مُتَرْجِم()
        نَتِيجَة = م.تَرْجِمْ("kitob")
        نَتِيجَة = م.تَرْجِمْ("китоб")
        نَتِيجَة = م.تَرْجِمْ("كتاب")
        نَتِيجَة = م.تَرْجِمْ("cite")
    """

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'uslap_database_v3.db'
            )
        self._path = db_path
        self._conn = None

    def _connect(self):
        if self._conn is None:
            self._conn = _uslap_connect(self._path) if _HAS_WRAPPER else sqlite3.connect(self._path)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def أَغْلِقْ(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _q(self, sql, params=None):
        """Execute query, return list of dicts."""
        conn = self._connect()
        try:
            if params:
                rows = conn.execute(sql, params).fetchall()
            else:
                rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error:
            return []

    def _q1(self, sql, params=None):
        """Execute query, return first row as dict or None."""
        rows = self._q(sql, params)
        return rows[0] if rows else None

    # ─── Stage 1: تَعَرُّف — Recognition ─────────────────────────

    def _bi_morphological_decompose(self, word):
        """
        Decompose a word using BI tasrif tables.
        Strips suffixes from DB (bitig_*_tasrif), returns:
          [(stem, suffix, suffix_code, suffix_category, is_bi_native), ...]
        Ordered longest suffix first.
        """
        from amr_uzbek import get_bi_suffix_info
        latin = normalize(word).lower()
        results = []
        # Try stripping suffixes from longest to shortest
        # Load all known suffixes from DB
        from amr_uzbek import load_bi_suffixes_from_db
        all_suffixes = load_bi_suffixes_from_db()
        # Sort by length descending for greedy matching
        sorted_suffixes = sorted(all_suffixes.keys(), key=len, reverse=True)

        current = latin
        stripped_layers = []
        for _ in range(4):  # max 4 layers of suffix stacking
            found = False
            for suffix in sorted_suffixes:
                if current.endswith(suffix) and len(current) > len(suffix) + 1:
                    stem = current[:-len(suffix)]
                    info = all_suffixes[suffix]
                    stripped_layers.append((stem, suffix, info[0], info[1], info[3]))
                    current = stem
                    found = True
                    break
            if not found:
                break

        return stripped_layers

    def تَعَرَّفْ(self, word):
        """
        تَعَرُّف — Identify the root of a word.

        Search order: BITIG FIRST, then Uzbek, then AA/downstream.
        BI morphological analysis runs on every input.

        Returns dict with:
          root_id, root_letters, source_table, matched_term, orig_type,
          bi_morphology (if BI decomposition found)
        Or None if not found.
        """
        script = detect_script(word)
        latin = normalize(word)
        word_upper = word.upper() if script == 'latin' else word
        word_lower = word.lower() if script == 'latin' else word

        # ── BI MORPHOLOGICAL ANALYSIS (runs on every input) ──
        bi_morph = self._bi_morphological_decompose(word)

        # ── 0. BITIG DIRECT — Search bitig_a1 first ──
        # Try original word, then each stripped stem from morphological analysis
        bi_candidates = [latin]
        for stem, suffix, code, cat, native in bi_morph:
            if stem not in bi_candidates:
                bi_candidates.append(stem)

        for candidate in bi_candidates:
            row = self._q1(
                'SELECT entry_id, orig2_term, root_letters, root_id, '
                'downstream_forms, kashgari_attestation, navoi_attestation, '
                'tertiary_attestation, semantic_field '
                'FROM bitig_a1_entries WHERE LOWER(orig2_term) = LOWER(?) LIMIT 1',
                (candidate,)
            )
            if row:
                result = {
                    'root_id': row.get('root_id'),
                    'root_letters': row.get('root_letters', ''),
                    'source': 'bitig_a1',
                    'matched': row['orig2_term'],
                    'bitig_entry_id': row['entry_id'],
                    'downstream': row.get('downstream_forms', ''),
                    'kashgari': row.get('kashgari_attestation', ''),
                    'navoi': row.get('navoi_attestation', ''),
                    'tertiary': row.get('tertiary_attestation', ''),
                    'semantic_field': row.get('semantic_field', ''),
                    'orig': 'ORIG2',
                }
                if bi_morph and candidate != latin:
                    result['bi_morphology'] = bi_morph
                    result['stripped_from'] = word
                    result['stem'] = candidate
                return result

        # ── 1. BITIG DOWNSTREAM — search bitig downstream_forms ──
        rows = self._q(
            'SELECT entry_id, orig2_term, root_letters, downstream_forms, '
            'kashgari_attestation, navoi_attestation '
            'FROM bitig_a1_entries WHERE LOWER(downstream_forms) LIKE ? LIMIT 5',
            (f'%{latin}%',)
        )
        if rows:
            result = {
                'root_id': None,
                'root_letters': rows[0].get('root_letters', ''),
                'source': 'bitig_a1_downstream',
                'matched': rows[0]['orig2_term'],
                'downstream': rows[0].get('downstream_forms', ''),
                'kashgari': rows[0].get('kashgari_attestation', ''),
                'navoi': rows[0].get('navoi_attestation', ''),
                'orig': 'ORIG2',
            }
            if bi_morph:
                result['bi_morphology'] = bi_morph
            return result

        # ── 2. UZBEK VOCABULARY — direct lookup with suffix stripping ──
        uz_candidates = strip_suffixes(word)
        for candidate in uz_candidates:
            apo_variants = {candidate}
            if "'" in candidate:
                apo_variants.add(candidate.replace("'", "ʻ"))
                apo_variants.add(candidate.replace("'", ""))
            if "ʻ" in candidate:
                apo_variants.add(candidate.replace("ʻ", "'"))
                apo_variants.add(candidate.replace("ʻ", ""))
            for variant in apo_variants:
                for col in ('uz_latin', 'uz_cyrillic', 'uz_arabic'):
                    row = self._q1(
                        f'SELECT * FROM uzbek_vocabulary WHERE LOWER({col}) = LOWER(?) LIMIT 1',
                        (variant,)
                    )
                    if row:
                        result = {
                            'source': 'uzbek_vocabulary',
                            'matched': row.get('uz_latin', ''),
                            'uz_cyrillic': row.get('uz_cyrillic', ''),
                            'uz_arabic': row.get('uz_arabic', ''),
                            'uz_meaning': row.get('uz_meaning', ''),
                            'orig': row.get('orig_type', ''),
                            'amr_meaning': row.get('amr_meaning', ''),
                        }
                        if candidate != latin:
                            result['stripped_from'] = word
                            result['stem'] = candidate
                        if row.get('orig_type') == 'ORIG1':
                            result['root_id'] = row.get('aa_root_id')
                            result['root_letters'] = row.get('aa_root', '')
                        else:
                            result['root_id'] = None
                            result['root_letters'] = row.get('bitig_root', '')
                            result['kashgari'] = row.get('kashgari_form', '')
                        if bi_morph:
                            result['bi_morphology'] = bi_morph
                        return result

        # ── 3. AA ENTRIES — EN term lookup (ORIG1) ──
        for variant in (word, word_upper, word_lower, latin, latin.upper()):
            row = self._q1(
                'SELECT root_id, root_letters, en_term, aa_word FROM entries '
                'WHERE UPPER(en_term) = UPPER(?) LIMIT 1', (variant,)
            )
            if row and row.get('root_id'):
                return {
                    'root_id': row['root_id'],
                    'root_letters': row.get('root_letters', ''),
                    'source': 'entries',
                    'matched': row['en_term'],
                    'aa_word': row.get('aa_word', ''),
                    'orig': 'ORIG1',
                }

        # ── 4. AA WORD — Arabic script input (ORIG1) ──
        if script == 'aa_term':
            row = self._q1(
                'SELECT root_id, root_letters, en_term, aa_word FROM entries '
                'WHERE aa_word LIKE ? LIMIT 1', (f'%{word}%',)
            )
            if row and row.get('root_id'):
                return {
                    'root_id': row['root_id'],
                    'root_letters': row.get('root_letters', ''),
                    'source': 'entries',
                    'matched': row['aa_word'],
                    'aa_word': row.get('aa_word', ''),
                    'orig': 'ORIG1',
                }

        # ── 5. EUROPEAN / LATIN — downstream (ORIG1) ──
        for variant in (word, word_upper, word_lower, latin.upper()):
            row = self._q1(
                'SELECT root_id, root_letters, term, lang FROM european_a1_entries '
                'WHERE UPPER(term) = UPPER(?) LIMIT 1', (variant,)
            )
            if row and row.get('root_id'):
                return {
                    'root_id': row['root_id'],
                    'root_letters': row.get('root_letters', ''),
                    'source': 'european_a1',
                    'matched': row['term'],
                    'lang': row.get('lang', ''),
                    'orig': 'ORIG1',
                }
        for variant in (word, word_upper, latin.upper()):
            row = self._q1(
                'SELECT root_id, root_letters, lat_term, aa_word FROM latin_a1_entries '
                'WHERE UPPER(lat_term) = UPPER(?) LIMIT 1', (variant,)
            )
            if row and row.get('root_id'):
                return {
                    'root_id': row['root_id'],
                    'root_letters': row.get('root_letters', ''),
                    'source': 'latin_a1',
                    'matched': row['lat_term'],
                    'aa_word': row.get('aa_word', ''),
                    'orig': 'ORIG1',
                }

        # 7. Try "Persian" stripping
        for candidate in strip_persian(word):
            if candidate != latin:
                result = self.تَعَرَّفْ(candidate)
                if result:
                    result['stripped_from'] = word
                    return result

        # 8. Consonant-based fuzzy search in roots
        consonants = extract_consonants(word)
        if len(consonants) >= 2:
            # Try matching root_bare in roots table
            row = self._q1(
                'SELECT root_id, root_letters FROM roots '
                'WHERE root_bare = ? LIMIT 1', (consonants,)
            )
            if row:
                return {
                    'root_id': row['root_id'],
                    'root_letters': row['root_letters'],
                    'source': 'roots_fuzzy',
                    'matched': consonants,
                    'orig': 'ORIG1',
                    'fuzzy': True,
                }

        return None

    # ─── Stage 2: تَوْسِيع — Expansion ───────────────────────────

    def وَسِّعْ(self, root_id=None, root_letters=None, bitig_entry_id=None):
        """
        تَوْسِيع — Expand a root to all known siblings across all languages.

        Args:
            root_id: AA root ID (R###) or BI root ID (T_BITIG###)
            root_letters: consonant skeleton
            bitig_entry_id: direct bitig entry ID for cross-ref lookup

        Returns dict with all language forms.
        """
        result = {
            'جَذْر': {},
            'قُرْآن': {},
            'إِنْجِلِيزِي': [],
            'فَرَنْسِي': [],
            'إِسْبَانِي': [],
            'إِيطَالِي': [],
            'بُرْتُغَالِي': [],
            'أَلْمَانِي': [],
            'لَاتِينِي': [],
            'بِيتِيك': [],
            'رُوسِي': [],
            'فَارْسِي': [],
            'مُشْتَقَّات': [],
        }

        # AA Root info
        if root_id:
            root = self._q1(
                'SELECT root_id, root_letters, root_bare, primary_meaning, quran_tokens '
                'FROM roots WHERE root_id = ?', (root_id,)
            )
            if root:
                result['جَذْر'] = {
                    'root_id': root['root_id'],
                    'حُرُوف': root['root_letters'],
                    'bare': root.get('root_bare', ''),
                    'مَعْنَى': root.get('primary_meaning', ''),
                    'رُمُوز': root.get('quran_tokens', 0),
                }

        # EN entries
        if root_id:
            rows = self._q(
                'SELECT en_term, aa_word FROM entries WHERE root_id = ?', (root_id,)
            )
            for r in rows:
                if r.get('en_term'):
                    result['إِنْجِلِيزِي'].append(r['en_term'])
                if r.get('aa_word') and r['aa_word'] not in [x.get('aa_word') for x in [result['جَذْر']]]:
                    result['جَذْر']['aa_word'] = r['aa_word']

        # European entries
        if root_id:
            lang_map = {
                'FR': 'فَرَنْسِي', 'ES': 'إِسْبَانِي', 'IT': 'إِيطَالِي',
                'PT': 'بُرْتُغَالِي', 'DE': 'أَلْمَانِي',
            }
            rows = self._q(
                'SELECT term, lang FROM european_a1_entries WHERE root_id = ?', (root_id,)
            )
            for r in rows:
                lang_key = lang_map.get(r.get('lang', ''))
                if lang_key and r.get('term'):
                    result[lang_key].append(r['term'])

        # Latin entries
        if root_id:
            rows = self._q(
                'SELECT lat_term, aa_word FROM latin_a1_entries WHERE root_id = ?', (root_id,)
            )
            for r in rows:
                if r.get('lat_term'):
                    result['لَاتِينِي'].append(r['lat_term'])

        # Bitig entries — direct root_letters match
        if root_letters:
            bare = root_letters.replace('-', '')
            rows = self._q(
                'SELECT entry_id, orig2_term, root_letters, downstream_forms, '
                'kashgari_attestation, navoi_attestation '
                'FROM bitig_a1_entries WHERE root_letters = ? OR root_letters LIKE ?',
                (root_letters, f'%{bare}%')
            )
            for r in rows:
                bitig_entry = {
                    'term': r['orig2_term'],
                    'root': r.get('root_letters', ''),
                    'kashgari': r.get('kashgari_attestation', ''),
                    'navoi': r.get('navoi_attestation', ''),
                }
                result['بِيتِيك'].append(bitig_entry)
                ds = r.get('downstream_forms', '') or ''
                self._parse_downstream(ds, result)

        # ── CROSS-REF BRIDGE: BI <-> AA ──
        # Follow a5_cross_refs to find connected entries across tracks.
        # If we started from BI, find AA siblings. If from AA, find BI siblings.
        _visited_xrefs = set()

        # From BI → find AA entries via cross-refs
        if (root_letters or bitig_entry_id) and (not root_id or root_id.startswith('T_')):
            # We have BI data but no AA root_id — search cross-refs
            if bitig_entry_id:
                xrefs = self._q(
                    'SELECT to_entry_id, to_term, description FROM a5_cross_refs '
                    'WHERE from_bitig_id = ? AND to_entry_id IS NOT NULL',
                    (bitig_entry_id,)
                )
            else:
                xrefs = self._q(
                    'SELECT to_entry_id, to_term, description FROM a5_cross_refs '
                    'WHERE from_bitig_id IN '
                    '  (SELECT entry_id FROM bitig_a1_entries WHERE root_letters = ?) '
                    'AND to_entry_id IS NOT NULL',
                    (root_letters,)
                )
            for xr in xrefs:
                to_id = xr['to_entry_id']
                if to_id and to_id not in _visited_xrefs:
                    _visited_xrefs.add(to_id)
                    # Get the AA entry and its root
                    aa_entry = self._q1(
                        'SELECT root_id, en_term, ru_term, aa_word FROM entries WHERE entry_id = ?',
                        (to_id,)
                    )
                    if aa_entry and aa_entry.get('root_id'):
                        # Expand from this AA root too
                        aa_expansion = self.وَسِّعْ(root_id=aa_entry['root_id'])
                        for lang_key in ('إِنْجِلِيزِي', 'فَرَنْسِي', 'إِسْبَانِي',
                                         'إِيطَالِي', 'بُرْتُغَالِي', 'أَلْمَانِي',
                                         'لَاتِينِي', 'رُوسِي', 'فَارْسِي'):
                            for item in aa_expansion.get(lang_key, []):
                                if item not in result.get(lang_key, []):
                                    result.setdefault(lang_key, []).append(item)
                        # Merge root info if we don't have it
                        if not result.get('جَذْر') or not result['جَذْر'].get('root_id'):
                            if aa_expansion.get('جَذْر'):
                                result['جَذْر_AA'] = aa_expansion['جَذْر']

        # From AA → find BI entries via cross-refs
        if root_id and not result.get('بِيتِيك'):
            xrefs = self._q(
                'SELECT from_bitig_id, from_term FROM a5_cross_refs '
                'WHERE to_entry_id IN '
                '  (SELECT entry_id FROM entries WHERE root_id = ?) '
                'AND from_bitig_id IS NOT NULL',
                (root_id,)
            )
            for xr in xrefs:
                bi_id = xr['from_bitig_id']
                if bi_id:
                    bi_row = self._q1(
                        'SELECT orig2_term, root_letters, kashgari_attestation, '
                        'downstream_forms FROM bitig_a1_entries WHERE entry_id = ?',
                        (bi_id,)
                    )
                    if bi_row:
                        result['بِيتِيك'].append({
                            'term': bi_row['orig2_term'],
                            'root': bi_row.get('root_letters', ''),
                            'kashgari': bi_row.get('kashgari_attestation', ''),
                        })
                        ds = bi_row.get('downstream_forms', '') or ''
                        self._parse_downstream(ds, result)

        # Qur'anic attestation
        if root_id:
            qcount = self._q1(
                'SELECT COUNT(*) as cnt FROM quran_word_roots WHERE root_id = ?',
                (root_id,)
            )
            if qcount:
                result['قُرْآن']['عَدَد'] = qcount.get('cnt', 0)

        return result

    def _parse_downstream(self, downstream_text, result):
        """Parse pipe-separated downstream_forms into language buckets."""
        if not downstream_text:
            return

        parts = downstream_text.split('|')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract language code and content: "RU: word (details)"
            match = re.match(r'^([A-Z]{2}):\s*(.+)', part)
            if match:
                lang = match.group(1)
                content = match.group(2).strip()
                # Extract the first word/phrase before parentheses
                word_match = re.match(r'([^\(]+)', content)
                word = word_match.group(1).strip() if word_match else content

                if lang == 'RU':
                    if word not in result.get('رُوسِي', []):
                        result.setdefault('رُوسِي', []).append(word)
                elif lang == 'FA':
                    if word not in result.get('فَارْسِي', []):
                        result.setdefault('فَارْسِي', []).append(word)
                elif lang == 'EN':
                    if word not in result.get('إِنْجِلِيزِي', []):
                        result['إِنْجِلِيزِي'].append(word)
                elif lang == 'UZ':
                    result.setdefault('أُزْبَكِي', []).append(word)
                elif lang == 'HU':
                    result.setdefault('مَجَرِي', []).append(word)
                elif lang == 'MN':
                    # MN = same ORIG2 continuum, NOT a separate language
                    # "Mongolian" = غ-و-ل (ghoul) operator label (DP17)
                    result.setdefault('بِيتِيك_شَرْقِي', []).append(word)  # Eastern ORIG2
                elif lang == 'TR':
                    result.setdefault('تُرْكِي', []).append(word)
                elif lang == 'AZ':
                    result.setdefault('أَذَرِي', []).append(word)
                elif lang == 'KK':
                    result.setdefault('قَازَاقِي', []).append(word)
                elif lang == 'TT':
                    result.setdefault('تَتَرِي', []).append(word)

    # ─── Stage 3: تَرْجِمْ — Full Pipeline ────────────────────────

    def تَرْجِمْ(self, word):
        """
        Full translation pipeline: word → root → all siblings.

        Returns dict with:
          input, script, root, all language siblings, uzbek multi-script
        """
        script = detect_script(word)

        # Stage 1: Recognition
        recognition = self.تَعَرَّفْ(word)
        if recognition is None:
            return {
                'input': word,
                'script': script,
                'found': False,
                'message': 'لَمْ يُعْثَر عَلَى جَذْر',
            }

        # Stage 2: Expansion
        expansion = self.وَسِّعْ(
            root_id=recognition.get('root_id'),
            root_letters=recognition.get('root_letters'),
            bitig_entry_id=recognition.get('bitig_entry_id'),
        )

        # Stage 3: Assemble result
        result = {
            'input': word,
            'script': script,
            'found': True,
            'orig': recognition.get('orig', ''),
            'source': recognition.get('source', ''),
            'matched': recognition.get('matched', ''),
        }

        # Merge expansion
        result.update(expansion)

        # Preserve Uzbek vocabulary fields (recognition has priority over expansion)
        if recognition.get('source') == 'uzbek_vocabulary':
            result['uz_meaning'] = recognition.get('uz_meaning', '')
            result['uz_cyrillic'] = recognition.get('uz_cyrillic', '')
            result['uz_arabic'] = recognition.get('uz_arabic', '')
            result['amr_meaning'] = recognition.get('amr_meaning', '')
            result['root_letters'] = recognition.get('root_letters', '')
            if recognition.get('kashgari'):
                result['كَاشْغَرِي'] = recognition['kashgari']

        # Add Uzbek multi-script if we have a Latin form
        latin_form = normalize(word)
        if latin_form:
            result['أُزْبَكِي_سِكْرِبْت'] = to_all_scripts(latin_form)

        # Add Kashgari/Navoi attestation if from Bitig
        if recognition.get('kashgari'):
            result['كَاشْغَرِي'] = recognition['kashgari']
        if recognition.get('navoi'):
            result['نَوَائِي'] = recognition['navoi']

        return result

    def جُذُور_مُشْتَرَكَة(self, word1, word2):
        """
        Check if two words share the same root.
        Returns True/False and the shared root if found.
        """
        r1 = self.تَعَرَّفْ(word1)
        r2 = self.تَعَرَّفْ(word2)

        if r1 is None or r2 is None:
            return False, None

        # Compare root_id
        if r1.get('root_id') and r2.get('root_id') and r1['root_id'] == r2['root_id']:
            return True, r1['root_id']

        # Compare root_letters
        if r1.get('root_letters') and r2.get('root_letters'):
            rl1 = r1['root_letters'].replace('-', '')
            rl2 = r2['root_letters'].replace('-', '')
            if rl1 == rl2:
                return True, r1['root_letters']

        return False, None

    # ─── Stage 4: حِسَاب — Compute meanings from letter values ────

    def اُحْسُبْ_مَعَانِي(self, dry_run=False):
        """
        حِسَاب مَعَانِي الجُذُور — Compute ALL root meanings from letter values.

        Uses amr_alphabet to derive meaning from each letter's abjad value
        and semantic tendency. Populates:
          1. roots.primary_meaning (all 1,680 roots)
          2. entries.qur_meaning (all entries via their root)

        Returns dict with counts.
        """
        conn = self._connect()
        cursor = conn.cursor()

        # Step 1: Compute and populate roots.primary_meaning
        roots = self._q('SELECT root_id, root_letters FROM roots WHERE root_letters IS NOT NULL')
        root_count = 0
        for root in roots:
            rl = root.get('root_letters', '')
            if not rl:
                continue
            meaning = compute_root_meaning_text(rl)
            if meaning:
                if not dry_run:
                    cursor.execute(
                        'UPDATE roots SET primary_meaning = ? WHERE root_id = ?',
                        (meaning, root['root_id'])
                    )
                root_count += 1

        # Step 2: Populate entries.qur_meaning from root_letters
        entries = self._q(
            'SELECT entry_id, root_letters FROM entries '
            'WHERE root_letters IS NOT NULL'
        )
        entry_count = 0
        for entry in entries:
            rl = entry.get('root_letters', '')
            if not rl:
                continue
            meaning = compute_root_meaning_text(rl)
            if meaning:
                if not dry_run:
                    cursor.execute(
                        'UPDATE entries SET qur_meaning = ? WHERE entry_id = ?',
                        (meaning, entry['entry_id'])
                    )
                entry_count += 1

        if not dry_run:
            conn.commit()

        return {
            'roots_computed': root_count,
            'roots_total': len(roots),
            'entries_computed': entry_count,
            'entries_total': len(entries),
        }


# ═══════════════════════════════════════════════════════════════════════
# MODULE-LEVEL CONVENIENCE
# ═══════════════════════════════════════════════════════════════════════

_DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')
_المُتَرْجِم = None

def تَرْجِمْ(word):
    """Module-level translate function using default DB."""
    global _المُتَرْجِم
    if _المُتَرْجِم is None:
        _المُتَرْجِم = مُتَرْجِم(_DEFAULT_DB)
    return _المُتَرْجِم.تَرْجِمْ(word)

def جُذُور_مُشْتَرَكَة(word1, word2):
    """Check if two words share a root."""
    global _المُتَرْجِم
    if _المُتَرْجِم is None:
        _المُتَرْجِم = مُتَرْجِم(_DEFAULT_DB)
    return _المُتَرْجِم.جُذُور_مُشْتَرَكَة(word1, word2)


# ═══════════════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════════════

def display_result(result):
    """Pretty-print a translation result."""
    if not result.get('found'):
        print(f"  ❌ {result['input']} → {result.get('message', 'not found')}")
        return

    print(f"  input: {result['input']} ({result['script']})")
    print(f"  orig: {result['orig']} | source: {result['source']} | matched: {result['matched']}")

    root = result.get('جَذْر', {})
    if root:
        print(f"  جَذْر: {root.get('root_id', '')} {root.get('حُرُوف', '')} — {root.get('مَعْنَى', '')}")
        if root.get('رُمُوز'):
            print(f"  قُرْآن: {root['رُمُوز']} tokens")

    scripts = result.get('أُزْبَكِي_سِكْرِبْت', {})
    if scripts:
        print(f"  أُزْبَكِي: lat={scripts.get('latin','')} cyr={scripts.get('cyrillic','')} ar={scripts.get('aa_term','')}")

    for key in ['إِنْجِلِيزِي', 'فَرَنْسِي', 'إِسْبَانِي', 'إِيطَالِي',
                'بُرْتُغَالِي', 'أَلْمَانِي', 'لَاتِينِي', 'رُوسِي',
                'فَارْسِي', 'مَجَرِي', 'مُنْغُولِي', 'تُرْكِي', 'أُزْبَكِي',
                'أَذَرِي', 'قَازَاقِي', 'تَتَرِي']:
        vals = result.get(key, [])
        if vals:
            if isinstance(vals[0], dict):
                terms = [v.get('term', '') for v in vals]
                print(f"  {key}: {', '.join(terms)}")
            else:
                print(f"  {key}: {', '.join(str(v) for v in vals)}")

    if result.get('كَاشْغَرِي'):
        print(f"  كَاشْغَرِي: {result['كَاشْغَرِي'][:100]}")
    if result.get('نَوَائِي'):
        print(f"  نَوَائِي: {result['نَوَائِي'][:100]}")


# ═══════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    print('أَمْر تَرْجَمَة — Root-Based Translation Engine')
    print()

    م = مُتَرْجِم()

    # Test 1: English → root → all
    print("═══ Test 1: EN 'CITE' ═══")
    r = م.تَرْجِمْ("CITE")
    display_result(r)
    print()

    # Test 2: EN 'EMPIRE'
    print("═══ Test 2: EN 'EMPIRE' ═══")
    r = م.تَرْجِمْ("EMPIRE")
    display_result(r)
    print()

    # Test 3: Bitig word
    print("═══ Test 3: Bitig 'ordu' ═══")
    r = م.تَرْجِمْ("ordu")
    display_result(r)
    print()

    # Test 4: Bitig 'bitig'
    print("═══ Test 4: Bitig 'bitig' ═══")
    r = م.تَرْجِمْ("bitig")
    display_result(r)
    print()

    # Test 5: Bitig 'qağan'
    print("═══ Test 5: Bitig 'qağan' ═══")
    r = م.تَرْجِمْ("qağan")
    display_result(r)
    print()

    # Test 6: French
    print("═══ Test 6: FR 'CITER' ═══")
    r = م.تَرْجِمْ("CITER")
    display_result(r)
    print()

    # Test 7: Shared root check
    print("═══ Test 7: Shared root? 'CITE' + 'SCRIPT' ═══")
    shared, root = م.جُذُور_مُشْتَرَكَة("CITE", "SCRIPT")
    print(f"  Shared root: {shared} → {root}")
    print()

    # Test 8: Shared root — different languages
    print("═══ Test 8: Shared root? 'EMPIRE' + 'ADMIRAL' ═══")
    shared, root = م.جُذُور_مُشْتَرَكَة("EMPIRE", "ADMIRAL")
    print(f"  Shared root: {shared} → {root}")

    م.أَغْلِقْ()
