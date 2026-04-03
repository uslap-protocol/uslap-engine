#!/usr/bin/env python3
"""
USLaP Phase 20: az-Zalzalah (99) — الزلزلة
Q99:1-2: إِذَا زُلْزِلَتِ الْأَرْضُ زِلْزَالَهَا ⁞ وَأَخْرَجَتِ الْأَرْضُ أَثْقَالَهَا
"When the earth is shaken with its earthquake, and the earth brings forth its burdens"

The Earthquake shakes everything to surface what is hidden.
Comprehensive audit of all Heptad 3 work (Phases 15-19).

8 audit gates:
  G1 — INTEGRITY:    Orphan edges, duplicate nodes, FK consistency
  G2 — COVERAGE:     Entry tables vs index nodes — are all entries indexed?
  G3 — SCORES:       Score distribution, sub-threshold entries, missing scores
  G4 — SIBLINGS:     Shared roots across EN/RU/FA/Bitig — coverage gaps
  G5 — DIMENSIONS:   Edge balance, missing dimensions per node
  G6 — SEQUENCES:    ID sequences vs actual max IDs — drift check
  G7 — INTELLIGENCE: DP mapping coverage, intel edge wiring
  G8 — CONTAMINATION: Blacklist terms in entry fields, F-GATE violations

Usage:
    python3 uslap_zalzalah.py status      # Summary of all 8 gates
    python3 uslap_zalzalah.py audit       # Full audit with findings
    python3 uslap_zalzalah.py fix         # Auto-fix safe issues (dupes, orphans)
    python3 uslap_zalzalah.py report      # Generate audit report
    python3 uslap_zalzalah.py all         # audit + fix + report
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False, sys, os
from collections import defaultdict

DB = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')


class Zalzalah:
    """az-Zalzalah: The Earthquake — Comprehensive Audit Engine."""

    def __init__(self):
        self.conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.findings = defaultdict(list)  # gate -> [finding_dicts]
        self.fixes_applied = []

    # ─────────────── G1: INTEGRITY ───────────────

    def g1_integrity(self):
        """Check orphan edges, duplicate nodes, FK consistency."""
        c = self.conn
        gate = 'G1_INTEGRITY'

        # 1a. Orphan edges (node_id not in term_nodes)
        orphans = c.execute('''
            SELECT COUNT(*) FROM term_dimensions td
            WHERE NOT EXISTS (SELECT 1 FROM term_nodes tn WHERE tn.node_id = td.node_id)
        ''').fetchone()[0]
        if orphans > 0:
            self.findings[gate].append({
                'check': 'orphan_edges',
                'severity': 'HIGH',
                'count': orphans,
                'detail': f'{orphans} edges reference non-existent nodes',
                'fixable': True
            })

        # 1b. Duplicate nodes (same term+language, case-insensitive)
        dupes = c.execute('''
            SELECT UPPER(term) as ut, UPPER(language) as ul, COUNT(*) as cnt,
                   GROUP_CONCAT(node_id) as ids
            FROM term_nodes
            GROUP BY ut, ul HAVING cnt > 1
        ''').fetchall()
        if dupes:
            self.findings[gate].append({
                'check': 'duplicate_nodes',
                'severity': 'MEDIUM',
                'count': len(dupes),
                'detail': f'{len(dupes)} duplicate node groups',
                'items': [(d['ut'], d['ul'], d['cnt'], d['ids']) for d in dupes],
                'fixable': True
            })

        # 1c. Edges with empty/null dimension
        bad_dims = c.execute('''
            SELECT COUNT(*) FROM term_dimensions
            WHERE dimension IS NULL OR dimension = ''
        ''').fetchone()[0]
        if bad_dims > 0:
            self.findings[gate].append({
                'check': 'null_dimensions',
                'severity': 'HIGH',
                'count': bad_dims,
                'detail': f'{bad_dims} edges with null/empty dimension',
                'fixable': True
            })

        # 1d. term_nodes with null term or language
        null_nodes = c.execute('''
            SELECT COUNT(*) FROM term_nodes
            WHERE term IS NULL OR term = '' OR language IS NULL OR language = ''
        ''').fetchone()[0]
        if null_nodes > 0:
            self.findings[gate].append({
                'check': 'null_node_fields',
                'severity': 'HIGH',
                'count': null_nodes,
                'detail': f'{null_nodes} nodes with null/empty term or language',
                'fixable': True
            })

        passed = len(self.findings[gate]) == 0
        return gate, passed

    # ─────────────── G2: COVERAGE ───────────────

    def g2_coverage(self):
        """Check that all entry tables have corresponding index nodes."""
        c = self.conn
        gate = 'G2_COVERAGE'

        tables = [
            ('a1_entries', 'entry_id', 'en_term', 'EN'),
            ('bitig_a1_entries', 'entry_id', 'orig2_term', 'BITIG'),
            ('persian_a1_mad_khil', 'madkhal_id_مَدخَل_entry_id',
             'v_zhe_f_rs__واژِهِ_فارسی_persian_term', 'FA'),
            ('european_a1_entries', 'entry_id', 'term', None),  # multi-lang
        ]

        for tbl, id_col, term_col, lang in tables:
            try:
                total = c.execute(f'SELECT COUNT(*) FROM [{tbl}]').fetchone()[0]
                if lang:
                    indexed = c.execute(f'''
                        SELECT COUNT(DISTINCT tn.node_id)
                        FROM term_nodes tn
                        WHERE tn.source_table = ? AND tn.language = ?
                    ''', (tbl, lang)).fetchone()[0]
                else:
                    indexed = c.execute(f'''
                        SELECT COUNT(DISTINCT tn.node_id)
                        FROM term_nodes tn
                        WHERE tn.source_table = ?
                    ''', (tbl,)).fetchone()[0]

                gap = total - indexed
                if gap > 0:
                    self.findings[gate].append({
                        'check': f'coverage_{tbl}',
                        'severity': 'MEDIUM' if gap < 10 else 'HIGH',
                        'count': gap,
                        'detail': f'{tbl}: {indexed}/{total} indexed ({gap} missing)',
                        'fixable': False
                    })
            except Exception as e:
                self.findings[gate].append({
                    'check': f'coverage_{tbl}',
                    'severity': 'LOW',
                    'count': 0,
                    'detail': f'{tbl}: error checking — {e}',
                    'fixable': False
                })

        # RU coverage — different source_table name check
        ru_total = c.execute('SELECT COUNT(*) FROM "a1_записи"').fetchone()[0]
        ru_indexed = c.execute('''
            SELECT COUNT(DISTINCT node_id) FROM term_nodes
            WHERE source_table = 'a1_записи' AND language = 'RU'
        ''').fetchone()[0]
        ru_gap = ru_total - ru_indexed
        if ru_gap > 0:
            self.findings[gate].append({
                'check': 'coverage_ru',
                'severity': 'MEDIUM' if ru_gap < 10 else 'HIGH',
                'count': ru_gap,
                'detail': f'a1_записи: {ru_indexed}/{ru_total} indexed ({ru_gap} missing)',
                'fixable': False
            })

        passed = len(self.findings[gate]) == 0
        return gate, passed

    # ─────────────── G3: SCORES ───────────────

    def g3_scores(self):
        """Score distributions and sub-threshold entries across all tables."""
        c = self.conn
        gate = 'G3_SCORES'

        # EN scores
        en_sub = c.execute(
            'SELECT COUNT(*) FROM a1_entries WHERE score < 7'
        ).fetchone()[0]
        if en_sub > 0:
            self.findings[gate].append({
                'check': 'en_sub_threshold',
                'severity': 'HIGH',
                'count': en_sub,
                'detail': f'{en_sub} EN entries below score 7',
                'fixable': False
            })

        # EN missing scores
        en_null = c.execute(
            'SELECT COUNT(*) FROM a1_entries WHERE score IS NULL'
        ).fetchone()[0]
        if en_null > 0:
            self.findings[gate].append({
                'check': 'en_null_scores',
                'severity': 'HIGH',
                'count': en_null,
                'detail': f'{en_null} EN entries with NULL score',
                'fixable': False
            })

        # RU scores (column is 'балл')
        ru_sub = c.execute(
            'SELECT COUNT(*) FROM "a1_записи" WHERE "балл" < 7'
        ).fetchone()[0]
        if ru_sub > 0:
            self.findings[gate].append({
                'check': 'ru_sub_threshold',
                'severity': 'MEDIUM',
                'count': ru_sub,
                'detail': f'{ru_sub} RU entries below score 7',
                'fixable': False
            })

        # FA scores
        fa_sub = c.execute(
            'SELECT COUNT(*) FROM persian_a1_mad_khil WHERE "номре_نُمره_score" < 7'
        ).fetchone()[0] if 'номре' in str(
            c.execute('PRAGMA table_info(persian_a1_mad_khil)').fetchall()
        ) else 0

        try:
            fa_sub = c.execute(
                'SELECT COUNT(*) FROM persian_a1_mad_khil WHERE "nomre_نُمره_score" < 7'
            ).fetchone()[0]
        except:
            try:
                fa_sub = c.execute(
                    'SELECT COUNT(*) FROM persian_a1_mad_khil WHERE score < 7'
                ).fetchone()[0]
            except:
                fa_sub = -1  # can't check

        if fa_sub > 0:
            self.findings[gate].append({
                'check': 'fa_sub_threshold',
                'severity': 'MEDIUM',
                'count': fa_sub,
                'detail': f'{fa_sub} FA entries below score 7',
                'fixable': False
            })

        # Bitig scores
        bitig_sub = c.execute(
            'SELECT COUNT(*) FROM bitig_a1_entries WHERE score < 7'
        ).fetchone()[0]
        if bitig_sub > 0:
            self.findings[gate].append({
                'check': 'bitig_sub_threshold',
                'severity': 'LOW',
                'count': bitig_sub,
                'detail': f'{bitig_sub} Bitig entries below score 7',
                'fixable': False
            })

        # European scores
        eu_sub = c.execute(
            'SELECT COUNT(*) FROM european_a1_entries WHERE score < 7'
        ).fetchone()[0]
        if eu_sub > 0:
            self.findings[gate].append({
                'check': 'eu_sub_threshold',
                'severity': 'LOW',
                'count': eu_sub,
                'detail': f'{eu_sub} European entries below score 7',
                'fixable': False
            })

        passed = len(self.findings[gate]) == 0
        return gate, passed

    # ─────────────── G4: SIBLINGS ───────────────

    def g4_siblings(self):
        """Check shared root coverage across sibling databases."""
        c = self.conn
        gate = 'G4_SIBLINGS'

        # Get all root_ids used in EN
        en_roots = set(r[0] for r in c.execute(
            'SELECT DISTINCT root_id FROM a1_entries WHERE root_id IS NOT NULL'
        ).fetchall())

        # Get RU root_ids
        ru_roots = set(r[0] for r in c.execute(
            'SELECT DISTINCT "корень_id" FROM "a1_записи" WHERE "корень_id" IS NOT NULL'
        ).fetchall())

        # Get FA root_ids
        try:
            fa_roots = set(r[0] for r in c.execute(
                'SELECT DISTINCT "r_she_id_ریشِه_root_id" FROM persian_a1_mad_khil '
                'WHERE "r_she_id_ریشِه_root_id" IS NOT NULL'
            ).fetchall())
        except:
            fa_roots = set()

        # Shared roots
        en_ru_shared = en_roots & ru_roots
        en_fa_shared = en_roots & fa_roots
        ru_fa_shared = ru_roots & fa_roots
        all_shared = en_roots & ru_roots & fa_roots

        # EN-only roots (no sibling coverage)
        en_only = en_roots - ru_roots - fa_roots
        ru_only = ru_roots - en_roots - fa_roots

        self.findings[gate].append({
            'check': 'root_coverage_report',
            'severity': 'INFO',
            'count': 0,
            'detail': (
                f'EN roots: {len(en_roots)} | RU roots: {len(ru_roots)} | FA roots: {len(fa_roots)}\n'
                f'    EN∩RU: {len(en_ru_shared)} | EN∩FA: {len(en_fa_shared)} | RU∩FA: {len(ru_fa_shared)}\n'
                f'    All three: {len(all_shared)}\n'
                f'    EN-only: {len(en_only)} | RU-only: {len(ru_only)}'
            ),
            'fixable': False
        })

        passed = True  # Informational gate
        return gate, passed

    # ─────────────── G5: DIMENSIONS ───────────────

    def g5_dimensions(self):
        """Edge balance and nodes with missing dimension coverage."""
        c = self.conn
        gate = 'G5_DIMENSIONS'

        # Dimension distribution
        dims = c.execute('''
            SELECT dimension, COUNT(*) as cnt FROM term_dimensions
            GROUP BY dimension ORDER BY cnt DESC
        ''').fetchall()

        total_edges = sum(d['cnt'] for d in dims)
        dim_report = ' | '.join(f'{d["dimension"]}:{d["cnt"]}' for d in dims)

        # Nodes with zero edges
        zero_edge = c.execute('''
            SELECT COUNT(*) FROM term_nodes tn
            WHERE NOT EXISTS (SELECT 1 FROM term_dimensions td WHERE td.node_id = tn.node_id)
        ''').fetchone()[0]

        if zero_edge > 0:
            self.findings[gate].append({
                'check': 'zero_edge_nodes',
                'severity': 'MEDIUM',
                'count': zero_edge,
                'detail': f'{zero_edge} nodes with zero edges (isolated)',
                'fixable': False
            })

        # Nodes with only 1 dimension type
        single_dim = c.execute('''
            SELECT COUNT(*) FROM (
                SELECT node_id, COUNT(DISTINCT dimension) as dims
                FROM term_dimensions GROUP BY node_id HAVING dims = 1
            )
        ''').fetchone()[0]

        self.findings[gate].append({
            'check': 'dimension_report',
            'severity': 'INFO',
            'count': 0,
            'detail': (
                f'Total edges: {total_edges:,}\n'
                f'    {dim_report}\n'
                f'    Isolated nodes (0 edges): {zero_edge}\n'
                f'    Single-dimension nodes: {single_dim}'
            ),
            'fixable': False
        })

        passed = zero_edge == 0
        return gate, passed

    # ─────────────── G6: SEQUENCES ───────────────

    def g6_sequences(self):
        """Check ID sequence drift — stored vs actual max IDs."""
        c = self.conn
        gate = 'G6_SEQUENCES'

        checks = [
            ('ROOT_ID', 'a1_entries', 'root_id', 'R'),
            ('EN_ENTRY', 'a1_entries', 'entry_id', ''),
            ('DERIV_ID', 'a4_derivatives', 'deriv_id', 'D'),
            ('XREF_ID', 'a5_cross_refs', 'xref_id', 'X'),
        ]

        for seq_name, table, col, prefix in checks:
            try:
                stored = c.execute(
                    'SELECT current_val FROM id_sequences WHERE seq_name = ?',
                    (seq_name,)
                ).fetchone()
                if not stored:
                    continue
                stored_val = stored['current_val']

                if prefix:
                    actual_max = c.execute(f'''
                        SELECT MAX(CAST(REPLACE({col}, ?, '') AS INTEGER))
                        FROM [{table}]
                    ''', (prefix,)).fetchone()[0] or 0
                else:
                    actual_max = c.execute(f'''
                        SELECT MAX(CAST({col} AS INTEGER)) FROM [{table}]
                    ''').fetchone()[0] or 0

                drift = stored_val - actual_max
                if drift < 0:
                    self.findings[gate].append({
                        'check': f'seq_drift_{seq_name}',
                        'severity': 'HIGH',
                        'count': abs(drift),
                        'detail': (f'{seq_name}: stored={stored_val} but '
                                   f'actual max={actual_max} (BEHIND by {abs(drift)})'),
                        'fixable': True
                    })
                elif drift > 20:
                    self.findings[gate].append({
                        'check': f'seq_gap_{seq_name}',
                        'severity': 'LOW',
                        'count': drift,
                        'detail': (f'{seq_name}: stored={stored_val}, '
                                   f'actual max={actual_max} (gap of {drift})'),
                        'fixable': False
                    })
            except Exception as e:
                self.findings[gate].append({
                    'check': f'seq_error_{seq_name}',
                    'severity': 'LOW',
                    'count': 0,
                    'detail': f'{seq_name}: check error — {e}',
                    'fixable': False
                })

        passed = not any(
            f['severity'] == 'HIGH' for f in self.findings[gate]
        )
        return gate, passed

    # ─────────────── G7: INTELLIGENCE ───────────────

    def g7_intelligence(self):
        """DP mapping coverage and intelligence edge wiring."""
        c = self.conn
        gate = 'G7_INTELLIGENCE'

        # dp_entry_map coverage
        dp_map_count = c.execute('SELECT COUNT(*) FROM dp_entry_map').fetchone()[0]
        dp_codes = c.execute(
            'SELECT DISTINCT dp_code FROM dp_entry_map'
        ).fetchall()
        dp_code_list = [d[0] for d in dp_codes]

        # INTELLIGENCE edges
        intel_edges = c.execute('''
            SELECT COUNT(*) FROM term_dimensions WHERE dimension = 'INTELLIGENCE'
        ''').fetchone()[0]

        # Nodes with INTELLIGENCE edges
        intel_nodes = c.execute('''
            SELECT COUNT(DISTINCT node_id) FROM term_dimensions
            WHERE dimension = 'INTELLIGENCE'
        ''').fetchone()[0]

        total_nodes = c.execute('SELECT COUNT(*) FROM term_nodes').fetchone()[0]
        intel_pct = (intel_nodes / total_nodes * 100) if total_nodes else 0

        # EN entries with inversion_type but no INTELLIGENCE edge
        en_inverted = c.execute('''
            SELECT COUNT(*) FROM a1_entries
            WHERE inversion_type IS NOT NULL AND inversion_type != ''
            AND inversion_type != 'NONE'
        ''').fetchone()[0]

        self.findings[gate].append({
            'check': 'intelligence_report',
            'severity': 'INFO',
            'count': 0,
            'detail': (
                f'DP map entries: {dp_map_count} across {len(dp_code_list)} codes\n'
                f'    DP codes: {", ".join(dp_code_list)}\n'
                f'    INTELLIGENCE edges: {intel_edges:,}\n'
                f'    Nodes with intel: {intel_nodes}/{total_nodes} ({intel_pct:.1f}%)\n'
                f'    EN entries with inversion_type: {en_inverted}'
            ),
            'fixable': False
        })

        passed = True
        return gate, passed

    # ─────────────── G8: CONTAMINATION ───────────────

    def g8_contamination(self):
        """Check for blacklisted terms in entry fields."""
        c = self.conn
        gate = 'G8_CONTAMINATION'

        # Load blacklist
        blacklist = c.execute(
            'SELECT bl_id, contaminated_term, contaminated_translation '
            'FROM contamination_blacklist'
        ).fetchall()

        contaminated = []

        # Check EN entries for contaminated terms in foundation_ref and source_form
        for bl in blacklist:
            term = bl['contaminated_term']
            wrong = bl['contaminated_translation']
            # Check if wrong translation appears in any EN entry field
            search_frag = wrong.lower()[:20] if wrong else ''
            if not search_frag:
                continue
            hits = c.execute('''
                SELECT entry_id, en_term, foundation_ref FROM a1_entries
                WHERE LOWER(foundation_ref) LIKE ?
                OR LOWER(source_form) LIKE ?
            ''', (f'%{search_frag}%', f'%{search_frag}%')).fetchall()
            if hits:
                contaminated.append({
                    'bl_id': bl['bl_id'],
                    'term': term,
                    'wrong': wrong,
                    'hits': len(hits)
                })

        # Check for banned terms in any entry
        banned_phrases = [
            ('loanword', 'BAN_LOAN'),
            ('borrowed from', 'BAN_BORROW'),
            ('cognate', 'BAN_COGNATE'),
            ('Proto-Indo-European', 'BAN_PIE'),
            ('Semitic language', 'BAN_SEMITIC'),
        ]

        # Exposure-context phrases: if the banned term appears alongside these,
        # it's being EXPOSED, not endorsed
        exposure_markers = ['dp0', 'dp1', 'dp2', 'recognised', 'claimed',
                            'labelled', 'phantom', 'refutation', 'obscures',
                            'erased', 'reattributed', 'corruption']

        for phrase, code in banned_phrases:
            # Check EN
            hits = c.execute('''
                SELECT entry_id, en_term, foundation_ref FROM a1_entries
                WHERE LOWER(foundation_ref) LIKE ? OR LOWER(source_form) LIKE ?
            ''', (f'%{phrase.lower()}%', f'%{phrase.lower()}%')).fetchall()

            # Filter out false positives (exposure context)
            real_hits = []
            for h in hits:
                fref = (h['foundation_ref'] or '').lower()
                if any(marker in fref for marker in exposure_markers):
                    continue  # DP-exposure context — not endorsing
                real_hits.append(h)

            if real_hits:
                self.findings[gate].append({
                    'check': f'banned_{code}',
                    'severity': 'HIGH',
                    'count': len(real_hits),
                    'detail': f'"{phrase}" found in {len(real_hits)} EN entries (non-exposure)',
                    'items': [(h['entry_id'], h['en_term']) for h in real_hits],
                    'fixable': False
                })
            elif hits:
                # All hits are exposure-context — report as INFO
                self.findings[gate].append({
                    'check': f'banned_{code}_exposure',
                    'severity': 'INFO',
                    'count': len(hits),
                    'detail': f'"{phrase}" in {len(hits)} entries (all DP-exposure context — OK)',
                    'fixable': False
                })

        if contaminated:
            self.findings[gate].append({
                'check': 'blacklist_contamination',
                'severity': 'HIGH',
                'count': len(contaminated),
                'detail': f'{len(contaminated)} blacklist terms found in entries',
                'items': contaminated,
                'fixable': False
            })

        passed = len(self.findings[gate]) == 0
        return gate, passed

    # ─────────────── G9: QUF ───────────────

    def g9_quf(self):
        """Check QUF stamp coverage and score-QUF mismatches."""
        c = self.conn
        gate = 'G9_QUF'

        stamp_tables = {
            'EN': ('a1_entries', 'score'),
            'RU': ('a1_записи', 'балл'),
            'EU': ('european_a1_entries', 'score'),
        }

        total_unstamped = 0
        total_mismatches = 0
        grand_pass = 0
        grand_validated = 0

        for label, (table, score_col) in stamp_tables.items():
            total = c.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            stamped = c.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE quf_date IS NOT NULL'
            ).fetchone()[0]
            unstamped = total - stamped
            total_unstamped += unstamped

            pass_count = c.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 1'
            ).fetchone()[0]
            fail_count = c.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND quf_date IS NOT NULL '
                f'AND quf_q NOT IN (\'ORIG2_SKIP\') AND quf_q IS NOT NULL'
            ).fetchone()[0]

            mismatches = c.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE quf_pass = 0 AND "{score_col}" >= 8 '
                f'AND quf_q NOT IN (\'ORIG2_SKIP\', \'ERROR\') AND quf_q IS NOT NULL '
                f'AND quf_date IS NOT NULL'
            ).fetchone()[0]

            validated = pass_count + fail_count
            grand_pass += pass_count
            grand_validated += validated
            total_mismatches += mismatches

        # Check unstamped
        if total_unstamped > 0:
            self.findings[gate].append({
                'check': 'unstamped_entries',
                'severity': 'HIGH',
                'count': total_unstamped,
                'detail': f'{total_unstamped} entries not yet QUF-stamped',
                'fixable': False
            })

        # Report pass rates
        pct = (grand_pass / grand_validated * 100) if grand_validated else 0
        self.findings[gate].append({
            'check': 'quf_pass_rate',
            'severity': 'INFO',
            'count': 0,
            'detail': f'QUF pass: {grand_pass}/{grand_validated} ({pct:.1f}%)',
            'fixable': False
        })

        # Report mismatches
        if total_mismatches > 0:
            self.findings[gate].append({
                'check': 'score_quf_mismatch',
                'severity': 'MEDIUM',
                'count': total_mismatches,
                'detail': f'{total_mismatches} entries with score≥8 but QUF fail (review needed)',
                'fixable': False
            })

        passed = total_unstamped == 0
        return gate, passed

    # ─────────────── COMMANDS ───────────────

    def status(self):
        """Quick summary — run all gates, show pass/fail."""
        print("═══ az-Zalzalah: Phase 20 Status ═══")
        print("Q99:1 — إِذَا زُلْزِلَتِ الْأَرْضُ زِلْزَالَهَا\n")

        gates = [
            self.g1_integrity, self.g2_coverage, self.g3_scores,
            self.g4_siblings, self.g5_dimensions, self.g6_sequences,
            self.g7_intelligence, self.g8_contamination, self.g9_quf,
        ]

        results = []
        for gate_fn in gates:
            gate_name, passed = gate_fn()
            results.append((gate_name, passed))

        total_findings = sum(len(v) for v in self.findings.values())
        high = sum(1 for v in self.findings.values()
                   for f in v if f['severity'] == 'HIGH')
        medium = sum(1 for v in self.findings.values()
                     for f in v if f['severity'] == 'MEDIUM')

        print("─── Gate Results ───")
        for name, passed in results:
            mark = '✅' if passed else '⚠️'
            finding_count = len(self.findings[name])
            info_only = all(f['severity'] == 'INFO' for f in self.findings[name])
            if finding_count == 0:
                print(f"  {mark} {name}: PASS")
            elif info_only:
                print(f"  {mark} {name}: PASS (info reported)")
            else:
                severities = [f['severity'] for f in self.findings[name]
                              if f['severity'] != 'INFO']
                print(f"  {mark} {name}: {', '.join(severities)} "
                      f"({finding_count} findings)")

        passed_count = sum(1 for _, p in results if p)
        print(f"\n─── Summary ───")
        print(f"  Gates: {passed_count}/9 passed")
        print(f"  Findings: {total_findings} total "
              f"(HIGH:{high}, MEDIUM:{medium})")

    def audit(self):
        """Full audit — run all gates with detailed findings."""
        print("═══ az-Zalzalah: Full Audit ═══\n")

        gates = [
            self.g1_integrity, self.g2_coverage, self.g3_scores,
            self.g4_siblings, self.g5_dimensions, self.g6_sequences,
            self.g7_intelligence, self.g8_contamination, self.g9_quf,
        ]

        for gate_fn in gates:
            gate_name, passed = gate_fn()
            mark = '✅' if passed else '⚠️'
            print(f"\n── {mark} {gate_name} ──")

            findings = self.findings[gate_name]
            if not findings:
                print("  No issues found.")
                continue

            for f in findings:
                sev = f['severity']
                icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🔵', 'INFO': 'ℹ️'}.get(sev, '•')
                print(f"  {icon} [{sev}] {f['check']}: {f['detail']}")
                if 'items' in f and f['items']:
                    for item in f['items'][:10]:
                        if isinstance(item, tuple):
                            print(f"      → {item}")
                        elif isinstance(item, dict):
                            print(f"      → {item}")

        # Summary
        total = sum(len(v) for v in self.findings.values())
        fixable = sum(1 for v in self.findings.values()
                      for f in v if f.get('fixable'))
        print(f"\n─── Audit Complete ───")
        print(f"  Total findings: {total}")
        print(f"  Auto-fixable: {fixable}")
        if fixable > 0:
            print(f"  Run 'fix' to auto-repair {fixable} issues.")

    def fix(self):
        """Auto-fix safe issues: duplicate nodes, orphan edges, null fields."""
        c = self.conn

        # Re-run integrity checks to populate findings
        if not self.findings:
            self.g1_integrity()

        print("═══ az-Zalzalah: Auto-Fix ═══\n")
        fixed_total = 0

        # Fix 1: Remove orphan edges
        orphans = c.execute('''
            SELECT COUNT(*) FROM term_dimensions td
            WHERE NOT EXISTS (SELECT 1 FROM term_nodes tn WHERE tn.node_id = td.node_id)
        ''').fetchone()[0]
        if orphans > 0:
            c.execute('''
                DELETE FROM term_dimensions
                WHERE NOT EXISTS (
                    SELECT 1 FROM term_nodes tn WHERE tn.node_id = term_dimensions.node_id
                )
            ''')
            print(f"  ✓ Removed {orphans} orphan edges")
            fixed_total += orphans

        # Fix 2: Deduplicate nodes (keep lowest node_id, remap edges)
        dupes = c.execute('''
            SELECT UPPER(term) as ut, UPPER(language) as ul, COUNT(*) as cnt,
                   MIN(node_id) as keep_id, GROUP_CONCAT(node_id) as all_ids
            FROM term_nodes
            GROUP BY ut, ul HAVING cnt > 1
        ''').fetchall()

        dupe_fixes = 0
        for d in dupes:
            keep_id = d['keep_id']
            all_ids = [int(x) for x in d['all_ids'].split(',')]
            remove_ids = [x for x in all_ids if x != keep_id]

            for rid in remove_ids:
                # Remap edges from duplicate to keeper
                c.execute('''
                    UPDATE term_dimensions SET node_id = ?
                    WHERE node_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM term_dimensions td2
                        WHERE td2.node_id = ? AND td2.dimension = term_dimensions.dimension
                        AND td2.target_table = term_dimensions.target_table
                        AND td2.target_id = term_dimensions.target_id
                    )
                ''', (keep_id, rid, keep_id))

                # Delete remaining duplicate edges
                c.execute('DELETE FROM term_dimensions WHERE node_id = ?', (rid,))

                # Delete duplicate node
                c.execute('DELETE FROM term_nodes WHERE node_id = ?', (rid,))
                dupe_fixes += 1

        if dupe_fixes > 0:
            print(f"  ✓ Merged {dupe_fixes} duplicate nodes")
            fixed_total += dupe_fixes

        # Fix 3: Remove edges with null dimension
        null_dims = c.execute('''
            DELETE FROM term_dimensions
            WHERE dimension IS NULL OR dimension = ''
        ''').rowcount
        if null_dims > 0:
            print(f"  ✓ Removed {null_dims} null-dimension edges")
            fixed_total += null_dims

        # Fix 4: Remove null-field nodes
        null_nodes = c.execute('''
            DELETE FROM term_nodes
            WHERE term IS NULL OR term = '' OR language IS NULL OR language = ''
        ''').rowcount
        if null_nodes > 0:
            print(f"  ✓ Removed {null_nodes} null-field nodes")
            fixed_total += null_nodes

        # Fix 5: Sync id_sequences to actual max values
        seq_fixes = self._fix_sequences()
        fixed_total += seq_fixes

        if fixed_total > 0:
            self.conn.commit()
            print(f"\n  Total fixes applied: {fixed_total}")
            self.fixes_applied.append(f'{fixed_total} issues fixed')
        else:
            print("  No fixes needed — all clean.")

        # Update FTS index
        try:
            c.execute('DELETE FROM term_search')
            c.execute('''
                INSERT INTO term_search(rowid, term, language, source_table)
                SELECT node_id, term, language, source_table FROM term_nodes
            ''')
            self.conn.commit()
            print("  ✓ FTS index rebuilt")
        except Exception:
            pass  # FTS rebuild is best-effort

    def _fix_sequences(self):
        """Fix id_sequence drift."""
        c = self.conn
        fixes = 0

        checks = [
            ('ROOT_ID', 'a1_entries', 'root_id', 'R'),
            ('EN_ENTRY', 'a1_entries', 'entry_id', ''),
            ('DERIV_ID', 'a4_derivatives', 'deriv_id', 'D'),
            ('XREF_ID', 'a5_cross_refs', 'xref_id', 'X'),
        ]

        for seq_name, table, col, prefix in checks:
            try:
                stored = c.execute(
                    'SELECT current_val FROM id_sequences WHERE seq_name = ?',
                    (seq_name,)
                ).fetchone()
                if not stored:
                    continue

                if prefix:
                    actual = c.execute(f'''
                        SELECT MAX(CAST(REPLACE({col}, ?, '') AS INTEGER))
                        FROM [{table}]
                    ''', (prefix,)).fetchone()[0] or 0
                else:
                    actual = c.execute(f'''
                        SELECT MAX(CAST({col} AS INTEGER)) FROM [{table}]
                    ''').fetchone()[0] or 0

                if stored['current_val'] < actual:
                    c.execute(
                        'UPDATE id_sequences SET current_val = ? WHERE seq_name = ?',
                        (actual, seq_name)
                    )
                    print(f"  ✓ {seq_name}: {stored['current_val']} → {actual}")
                    fixes += 1
            except Exception:
                pass

        return fixes

    def report(self):
        """Generate summary counts for the seal phase."""
        c = self.conn
        print("═══ az-Zalzalah: Audit Report ═══\n")

        # Entry counts
        print("── Entry Counts ──")
        tables = [
            ('EN (a1_entries)', 'SELECT COUNT(*) FROM a1_entries'),
            ('RU (a1_записи)', 'SELECT COUNT(*) FROM "a1_записи"'),
            ('FA (persian_a1)', 'SELECT COUNT(*) FROM persian_a1_mad_khil'),
            ('Bitig', 'SELECT COUNT(*) FROM bitig_a1_entries'),
            ('Latin', 'SELECT COUNT(*) FROM latin_a1_entries'),
            ('European', 'SELECT COUNT(*) FROM european_a1_entries'),
            ('Peoples', 'SELECT COUNT(*) FROM child_schema'),
            ('Countries', 'SELECT COUNT(*) FROM a6_country_names'),
            ('Names of Allah', 'SELECT COUNT(*) FROM a2_names_of_allah'),
            ('Derivatives', 'SELECT COUNT(*) FROM a4_derivatives'),
            ('Cross-refs', 'SELECT COUNT(*) FROM a5_cross_refs'),
            ('Qur\'an refs', 'SELECT COUNT(*) FROM a3_quran_refs'),
            ('Chronology', 'SELECT COUNT(*) FROM chronology'),
            ('Networks', 'SELECT COUNT(*) FROM m4_networks'),
            ('Scholars', 'SELECT COUNT(*) FROM m3_scholars'),
        ]

        total_entries = 0
        for label, sql in tables:
            try:
                cnt = c.execute(sql).fetchone()[0]
                total_entries += cnt
                print(f"  {label:25s}: {cnt:,}")
            except:
                print(f"  {label:25s}: ERROR")

        print(f"  {'TOTAL':25s}: {total_entries:,}")

        # Index counts
        print("\n── Index (al-Qamar) ──")
        nodes = c.execute('SELECT COUNT(*) FROM term_nodes').fetchone()[0]
        edges = c.execute('SELECT COUNT(*) FROM term_dimensions').fetchone()[0]
        print(f"  Nodes: {nodes:,}")
        print(f"  Edges: {edges:,}")

        # Dimension breakdown
        dims = c.execute('''
            SELECT dimension, COUNT(*) as cnt FROM term_dimensions
            GROUP BY dimension ORDER BY cnt DESC
        ''').fetchall()
        for d in dims:
            pct = d['cnt'] / edges * 100
            print(f"    {d['dimension']:20s}: {d['cnt']:6,} ({pct:4.1f}%)")

        # Node language breakdown
        print("\n── Nodes by Language ──")
        langs = c.execute('''
            SELECT language, COUNT(*) as cnt FROM term_nodes
            GROUP BY language ORDER BY cnt DESC
        ''').fetchall()
        for l in langs:
            print(f"  {l['language']:10s}: {l['cnt']:,}")

        # Bitig status
        print("\n── Bitig Restoration DB ──")
        statuses = c.execute('''
            SELECT status, COUNT(*) as cnt FROM bitig_a1_entries
            GROUP BY status ORDER BY cnt DESC
        ''').fetchall()
        for s in statuses:
            print(f"  {s['status']:25s}: {s['cnt']}")

        # Qur'an compiler
        print("\n── Qur'an Compiler ──")
        try:
            total_words = c.execute('SELECT COUNT(*) FROM quran_word_roots').fetchone()[0]
            rooted = c.execute(
                'SELECT COUNT(*) FROM quran_word_roots WHERE root IS NOT NULL'
            ).fetchone()[0]
            roots = c.execute(
                'SELECT COUNT(DISTINCT root) FROM quran_word_roots WHERE root IS NOT NULL'
            ).fetchone()[0]
            print(f"  Total words: {total_words:,}")
            print(f"  Rooted: {rooted:,} ({rooted/total_words*100:.1f}%)")
            print(f"  Unique roots: {roots:,}")
        except Exception as e:
            print(f"  Error: {e}")

        # Contamination
        print("\n── Contamination Watch ──")
        bl = c.execute('SELECT COUNT(*) FROM contamination_blacklist').fetchone()[0]
        bd = c.execute('SELECT COUNT(*) FROM bitig_degradation_register').fetchone()[0]
        qv = c.execute('SELECT COUNT(*) FROM qv_translation_register').fetchone()[0]
        print(f"  Blacklist entries: {bl}")
        print(f"  Degradation register: {bd}")
        print(f"  QV translation register: {qv}")

    def all(self):
        """Run full pipeline: audit → fix → report."""
        self.audit()
        print("\n" + "═" * 50)
        self.fix()
        print("\n" + "═" * 50)
        # Reset findings for clean report
        self.findings = defaultdict(list)
        self.report()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    z = Zalzalah()

    commands = {
        'status': z.status,
        'audit': z.audit,
        'fix': z.fix,
        'report': z.report,
        'all': z.all,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status | audit | fix | report | all")


if __name__ == '__main__':
    main()
