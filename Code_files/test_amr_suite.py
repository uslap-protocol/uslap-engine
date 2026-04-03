#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP AMR AI — TEST SUITE
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Tests all AMR module public functions against DB data.
Zero test data from LLM — all from DB queries.

Usage:
    python3 test_amr_suite.py              # run all
    python3 test_amr_suite.py -v           # verbose
    python3 test_amr_suite.py TestTasrif   # single class
"""

import sys
import os
import unittest
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")


def _get_test_root():
    """Get a root from DB with high token count for testing."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT root, COUNT(*) as cnt FROM quran_word_roots "
        "WHERE root IS NOT NULL GROUP BY root ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row[0] if row else None


def _get_test_entry_id():
    """Get an entry_id from DB."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT entry_id FROM entries LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None


class TestDbConnect(unittest.TestCase):
    def test_import(self):
        from uslap_db_connect import DB_PATH, connect
        self.assertTrue(os.path.exists(DB_PATH))

    def test_connect(self):
        from uslap_db_connect import connect
        conn = connect()
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(fk, 1)
        conn.close()

    def test_readonly(self):
        from uslap_db_connect import connect
        conn = connect(readonly=True)
        self.assertIsNotNone(conn)
        conn.close()


class TestTasrif(unittest.TestCase):
    def test_import(self):
        from amr_tasrif import get_status, get_root_forms, get_pattern_info, get_broken_plurals, analyze_word
        self.assertTrue(callable(get_status))

    def test_status(self):
        from amr_tasrif import get_status
        s = get_status()
        self.assertIn('total_tokens', s)
        self.assertGreater(s['total_tokens'], 70000)
        self.assertGreater(s['verb_consonant_codes'], 0)
        self.assertGreater(s['noun_consonant_codes'], 0)

    def test_root_forms(self):
        from amr_tasrif import get_root_forms
        root = _get_test_root()
        forms = get_root_forms(root)
        self.assertIsInstance(forms, list)
        self.assertGreater(len(forms), 0)
        self.assertIn('word', forms[0])
        self.assertIn('ref', forms[0])

    def test_pattern_info(self):
        from amr_tasrif import get_pattern_info
        info, table = get_pattern_info('BASE')
        self.assertIsNotNone(info)
        self.assertEqual(table, 'noun_tasrif_patterns')

    def test_broken_plurals(self):
        from amr_tasrif import get_broken_plurals
        bp = get_broken_plurals()
        self.assertIsInstance(bp, dict)
        self.assertGreater(len(bp), 200)

    def test_unknown_pattern(self):
        from amr_tasrif import get_pattern_info
        info, table = get_pattern_info('NONEXISTENT_PATTERN')
        self.assertIsNone(info)


class TestBitigTasrif(unittest.TestCase):
    def test_import(self):
        from amr_bitig_tasrif import get_status, get_root_forms, get_pattern_info, check_harmony
        self.assertTrue(callable(get_status))

    def test_status(self):
        from amr_bitig_tasrif import get_status
        s = get_status()
        self.assertIsInstance(s, dict)
        self.assertGreater(len(s), 0)

    def test_has_bitig_alphabet(self):
        from amr_bitig_tasrif import _HAS_BITIG_ALPHABET
        self.assertTrue(_HAS_BITIG_ALPHABET)


class TestQuf(unittest.TestCase):
    def test_import(self):
        from amr_quf import validate, _connect
        self.assertTrue(callable(validate))

    def test_connect(self):
        from amr_quf import _connect
        conn = _connect()
        self.assertIsNotNone(conn)
        conn.close()

    def test_validate_dict(self):
        from amr_quf import validate
        # Get a real entry from DB
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM entries LIMIT 1").fetchone()
        conn.close()
        if row:
            result = validate(dict(row), domain='entries')
            self.assertIn('q', result)
            self.assertIn('u', result)
            self.assertIn('f', result)
            self.assertIn('pass', result)


class TestDhakaa(unittest.TestCase):
    def test_import(self):
        from amr_dhakaa import think
        self.assertTrue(callable(think))

    def test_think_trace(self):
        from amr_dhakaa import think
        r = think('trace silk')
        self.assertIn('output', r)
        self.assertGreater(len(r['output']), 50)
        self.assertEqual(r['intent'], 'trace_word')

    def test_think_state(self):
        from amr_dhakaa import think
        r = think('state')
        self.assertIn('output', r)
        self.assertIn('Roots', r['output'])

    def test_think_tasrif(self):
        from amr_dhakaa import think
        r = think('tasrif status')
        self.assertIn('output', r)
        self.assertEqual(r['intent'], 'tasrif')
        self.assertIn('STRUCTURAL', r['output'])

    def test_think_bitig_tasrif(self):
        from amr_dhakaa import think
        r = think('bitig tasrif status')
        self.assertIn('output', r)
        self.assertEqual(r['intent'], 'bitig_tasrif')

    def test_error_recovery(self):
        """think() should not crash on bad input."""
        from amr_dhakaa import think
        r = think('')
        self.assertIn('output', r)
        # Should return something, not crash


class TestBasar(unittest.TestCase):
    def test_import(self):
        from amr_basar import perceive
        self.assertTrue(callable(perceive))

    def test_perceive_trace(self):
        from amr_basar import perceive
        r = perceive('trace silk')
        self.assertEqual(r['intent'], 'trace_word')
        self.assertIn('query', r['params'])

    def test_perceive_tasrif(self):
        from amr_basar import perceive
        r = perceive('tasrif status')
        self.assertEqual(r['intent'], 'tasrif')

    def test_perceive_bitig_tasrif(self):
        from amr_basar import perceive
        r = perceive('bitig tasrif status')
        self.assertEqual(r['intent'], 'bitig_tasrif')

    def test_perceive_explain(self):
        from amr_basar import perceive
        root = _get_test_root()
        if root:
            r = perceive(f'explain {root}')
            self.assertEqual(r['intent'], 'explain_root')


class TestNutq(unittest.TestCase):
    def test_import(self):
        from amr_nutq import format_lattice_summary
        self.assertTrue(callable(format_lattice_summary))

    def test_lattice_summary(self):
        from amr_nutq import format_lattice_summary
        s = format_lattice_summary()
        self.assertIn('Roots', s)
        self.assertIn('Entries', s)


class TestAlphabet(unittest.TestCase):
    def test_import(self):
        from amr_alphabet import ABJAD
        self.assertEqual(len(ABJAD), 28)

    def test_abjad_values(self):
        from amr_alphabet import ABJAD
        # Alif = 1
        self.assertEqual(ABJAD.get('\u0627', 0), 1)


class TestKeywords(unittest.TestCase):
    def test_import(self):
        from amr_keywords import KEYWORDS
        self.assertGreater(len(KEYWORDS), 40)


class TestBitigAlphabet(unittest.TestCase):
    def test_import(self):
        from amr_bitig_alphabet import ALPHABET, HARMONY_PAIRS
        self.assertGreater(len(ALPHABET), 20)
        self.assertGreater(len(HARMONY_PAIRS), 0)


class TestPipelineIntegrity(unittest.TestCase):
    """End-to-end pipeline tests."""

    def test_determinism(self):
        """Same query twice = same output."""
        from amr_dhakaa import think
        r1 = think('trace silk')
        r2 = think('trace silk')
        self.assertEqual(r1['output'], r2['output'])

    def test_all_modules_import(self):
        """All 24 AMR modules must import without error."""
        modules = [
            'amr_dhakaa', 'amr_aql', 'amr_basar', 'amr_nutq', 'amr_quf',
            'amr_alphabet', 'amr_keywords', 'amr_tasrif', 'amr_bitig_tasrif',
            'amr_bitig_alphabet', 'amr_jism', 'amr_hisab', 'amr_tarikh',
            'amr_istakhbarat', 'amr_lawh', 'amr_tarjama', 'amr_uzbek', 'amr_ard',
            'amr_lexer', 'amr_parser', 'amr_emitter', 'amr_runtime', 'amr_cli',
            'amr_alphabet_i18n_export',
        ]
        for m in modules:
            try:
                __import__(m)
            except Exception as e:
                self.fail(f"{m} failed to import: {e}")

    def test_db_path_centralized(self):
        """Modules that define DB_PATH should get it from uslap_db_connect."""
        from uslap_db_connect import DB_PATH as central
        for mod_name in ['amr_quf', 'amr_tasrif', 'amr_bitig_tasrif',
                         'amr_tarikh', 'amr_hisab', 'amr_jism', 'amr_istakhbarat']:
            mod = __import__(mod_name)
            self.assertEqual(mod.DB_PATH, central,
                             f"{mod_name}.DB_PATH differs from central")


if __name__ == '__main__':
    unittest.main()
