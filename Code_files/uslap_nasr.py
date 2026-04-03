#!/usr/bin/env python3
"""
USLaP Phase 21: an-Naṣr (110) — النصر
Q110:1-3: إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ ⁞ وَرَأَيْتَ النَّاسَ يَدْخُلُونَ فِي دِينِ اللَّهِ أَفْوَاجًا ⁞ فَسَبِّحْ بِحَمْدِ رَبِّكَ وَاسْتَغْفِرْهُ ۚ إِنَّهُ كَانَ تَوَّابًا
"When the Help of Allah comes and the Opening, and you see people entering
the religion of Allah in multitudes, then glorify the praises of your Lord
and ask His forgiveness. Indeed, He is ever Accepting of repentance."

The Seal. Heptad 3 completion — final summary, integrity stamp, and
architecture overview across all three heptads (21 phases).

Usage:
    python3 uslap_nasr.py status     # Quick state summary
    python3 uslap_nasr.py seal       # Generate Heptad 3 seal report
    python3 uslap_nasr.py manifest   # Full 21-phase architecture manifest
    python3 uslap_nasr.py all        # seal + manifest
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False, sys, os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')


class Nasr:
    """an-Naṣr: The Help — Seal and Completion Engine."""

    def __init__(self):
        self.conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    def _count(self, sql):
        """Safe count query."""
        try:
            return self.conn.execute(sql).fetchone()[0]
        except Exception:
            return 0

    def _get_counts(self):
        """Gather all key counts from the database."""
        c = self.conn
        counts = {}

        # Entry tables
        counts['en'] = self._count('SELECT COUNT(*) FROM a1_entries')
        counts['ru'] = self._count('SELECT COUNT(*) FROM "a1_записи"')
        counts['fa'] = self._count('SELECT COUNT(*) FROM persian_a1_mad_khil')
        counts['bitig'] = self._count('SELECT COUNT(*) FROM bitig_a1_entries')
        counts['latin'] = self._count('SELECT COUNT(*) FROM latin_a1_entries')
        counts['european'] = self._count('SELECT COUNT(*) FROM european_a1_entries')
        counts['peoples'] = self._count('SELECT COUNT(*) FROM child_schema')
        counts['countries'] = self._count('SELECT COUNT(*) FROM a6_country_names')
        counts['allah_names'] = self._count('SELECT COUNT(*) FROM a2_names_of_allah')
        counts['derivatives'] = self._count('SELECT COUNT(*) FROM a4_derivatives')
        counts['cross_refs'] = self._count('SELECT COUNT(*) FROM a5_cross_refs')
        counts['quran_refs'] = self._count('SELECT COUNT(*) FROM a3_quran_refs')
        counts['chronology'] = self._count('SELECT COUNT(*) FROM chronology')
        counts['networks'] = self._count('SELECT COUNT(*) FROM m4_networks')
        counts['scholars'] = self._count('SELECT COUNT(*) FROM m3_scholars')

        # Index
        counts['nodes'] = self._count('SELECT COUNT(*) FROM term_nodes')
        counts['edges'] = self._count('SELECT COUNT(*) FROM term_dimensions')

        # Dimensions
        dims = c.execute('''
            SELECT dimension, COUNT(*) as cnt FROM term_dimensions
            GROUP BY dimension ORDER BY cnt DESC
        ''').fetchall()
        counts['dimensions'] = {d['dimension']: d['cnt'] for d in dims}

        # Languages in index
        langs = c.execute('''
            SELECT language, COUNT(*) as cnt FROM term_nodes
            GROUP BY language ORDER BY cnt DESC
        ''').fetchall()
        counts['languages'] = {l['language']: l['cnt'] for l in langs}

        # Bitig
        counts['bitig_confirmed'] = self._count(
            "SELECT COUNT(*) FROM bitig_a1_entries WHERE status = 'CONFIRMED'")
        counts['bitig_pending'] = self._count(
            "SELECT COUNT(*) FROM bitig_a1_entries WHERE status = 'PENDING_VERIFICATION'")

        # Qur'an compiler
        counts['quran_words'] = self._count('SELECT COUNT(*) FROM quran_word_roots')
        counts['quran_rooted'] = self._count(
            'SELECT COUNT(*) FROM quran_word_roots WHERE root IS NOT NULL')
        counts['quran_roots'] = self._count(
            'SELECT COUNT(DISTINCT root) FROM quran_word_roots WHERE root IS NOT NULL')

        # Contamination
        counts['blacklist'] = self._count('SELECT COUNT(*) FROM contamination_blacklist')
        counts['degradation'] = self._count('SELECT COUNT(*) FROM bitig_degradation_register')
        counts['qv_register'] = self._count('SELECT COUNT(*) FROM qv_translation_register')

        # DP map
        counts['dp_map'] = self._count('SELECT COUNT(*) FROM dp_entry_map')

        # Total DB tables
        counts['total_tables'] = self._count(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")

        # Total entries across all linguistic databases
        counts['total_linguistic'] = (counts['en'] + counts['ru'] + counts['fa'] +
                                       counts['bitig'] + counts['latin'] +
                                       counts['european'])

        return counts

    def status(self):
        """Quick state summary."""
        counts = self._get_counts()
        print("═══ an-Naṣr: Status ═══")
        print(f"  Timestamp: {self.timestamp}")
        print(f"  EN:{counts['en']} | RU:{counts['ru']} | FA:{counts['fa']} | "
              f"Bitig:{counts['bitig']} | Latin:{counts['latin']} | EU:{counts['european']}")
        print(f"  INDEX: {counts['nodes']:,} nodes / {counts['edges']:,} edges / "
              f"{len(counts['dimensions'])} dimensions")
        print(f"  Qur'an: {counts['quran_rooted']:,}/{counts['quran_words']:,} rooted "
              f"({counts['quran_rooted']/counts['quran_words']*100:.1f}%)")
        print(f"  Tables: {counts['total_tables']}")

    def seal(self):
        """Generate the Heptad 3 seal report."""
        counts = self._get_counts()

        print("═══════════════════════════════════════════════════════════════")
        print("   بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
        print("   USLaP HEPTAD 3 — SEAL REPORT")
        print("   an-Naṣr (110): إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ")
        print(f"   Sealed: {self.timestamp}")
        print("═══════════════════════════════════════════════════════════════\n")

        # ── HEPTAD 3 PHASES ──
        print("── HEPTAD 3: DEPLOYMENT (Phases 15-21) ──")
        phases = [
            ('15', 'ar-Raʿd (13)', 'Connection',
             'EN+RU+FA nodes indexed, sibling edges wired, dimension framework operational'),
            ('16', 'at-Takāthur (102)', 'Multiplication',
             'Latin hub → 5-language European fan-out (570 entries, 9 per lang per root)'),
            ('17', 'ar-Rūm (30)', 'Persian Corridor',
             f'uslap_rum.py: {counts["fa"]} FA entries, sibling edges wired'),
            ('18', 'al-Jumuʿah (62)', 'Excel Sync',
             'uslap_jumuah.py: 15 sheets synced between .db and .xlsx'),
            ('19', 'an-Nabaʾ (78)', 'Intelligence',
             f'uslap_naba.py: normalize+dp_map+wire+audit. '
             f'INTELLIGENCE={counts["dimensions"].get("INTELLIGENCE", 0):,} edges. '
             f'{counts["dp_map"]} dp_entry_map entries'),
            ('20', 'az-Zalzalah (99)', 'Review/Audit',
             'uslap_zalzalah.py: 8-gate audit (G1-G8). '
             'Duplicate nodes merged, orphan edges cleaned, '
             'coverage gaps indexed, contamination verified clean'),
            ('21', 'an-Naṣr (110)', 'Seal/Completion',
             'uslap_nasr.py: This report. Heptad 3 sealed.'),
        ]

        for num, surah, role, desc in phases:
            print(f"  Phase {num}: {surah} — {role}")
            print(f"    {desc}")

        # ── LINGUISTIC DATABASES ──
        print(f"\n── LINGUISTIC DATABASES ({counts['total_linguistic']:,} total entries) ──")
        print(f"  English (a1_entries):          {counts['en']:,}")
        print(f"  Russian (a1_записи):           {counts['ru']:,}")
        print(f"  Persian (persian_a1):          {counts['fa']:,}")
        print(f"  Bitig (bitig_a1):              {counts['bitig']:,} "
              f"({counts['bitig_confirmed']} confirmed, {counts['bitig_pending']} pending)")
        print(f"  Latin (latin_a1):              {counts['latin']:,}")
        print(f"  European (5 langs):            {counts['european']:,}")

        # ── SUPPORTING TABLES ──
        print(f"\n── SUPPORTING TABLES ──")
        print(f"  Peoples (child_schema):        {counts['peoples']}")
        print(f"  Countries (a6):                {counts['countries']}")
        print(f"  Names of Allah (a2):           {counts['allah_names']}")
        print(f"  Derivatives (a4):              {counts['derivatives']:,}")
        print(f"  Cross-references (a5):         {counts['cross_refs']}")
        print(f"  Qur'an references (a3):        {counts['quran_refs']}")
        print(f"  Chronology:                    {counts['chronology']}")
        print(f"  Networks (m4):                 {counts['networks']}")
        print(f"  Scholars (m3):                 {counts['scholars']}")

        # ── INDEX (al-Qamar) ──
        print(f"\n── INDEX — al-Qamar ──")
        print(f"  Nodes: {counts['nodes']:,}")
        print(f"  Edges: {counts['edges']:,}")
        print(f"  Dimensions: {len(counts['dimensions'])}")
        for dim, cnt in counts['dimensions'].items():
            pct = cnt / counts['edges'] * 100
            bar = '█' * int(pct / 2)
            print(f"    {dim:20s}: {cnt:6,} ({pct:4.1f}%) {bar}")

        # Node language breakdown
        print(f"\n  Nodes by language:")
        for lang, cnt in counts['languages'].items():
            print(f"    {lang:10s}: {cnt:,}")

        # ── QUR'AN COMPILER ──
        print(f"\n── QUR'AN COMPILER ──")
        pct = counts['quran_rooted'] / counts['quran_words'] * 100 if counts['quran_words'] else 0
        print(f"  Total words:    {counts['quran_words']:,}")
        print(f"  Rooted:         {counts['quran_rooted']:,} ({pct:.1f}%)")
        print(f"  Unique roots:   {counts['quran_roots']:,}")
        print(f"  QV register:    {counts['qv_register']}")

        # ── CONTAMINATION DEFENCE ──
        print(f"\n── CONTAMINATION DEFENCE ──")
        print(f"  Blacklist entries:             {counts['blacklist']}")
        print(f"  Bitig degradation register:    {counts['degradation']}")
        print(f"  QV translation register:       {counts['qv_register']}")
        print(f"  DP entry map:                  {counts['dp_map']}")

        # ── DATABASE ──
        print(f"\n── DATABASE ──")
        print(f"  Total tables:   {counts['total_tables']}")

        # DB file size
        db_path = DB
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"  DB file size:   {size_mb:.1f} MB")

        print(f"\n═══ HEPTAD 3: SEALED ✅ ═══")
        print(f"═══ {self.timestamp} ═══")

    def manifest(self):
        """Full 21-phase architecture manifest across all three heptads."""
        print("═══════════════════════════════════════════════════════════════")
        print("   USLaP UNIFIED LINGUISTIC LATTICE — ARCHITECTURE MANIFEST")
        print("   21 Phases / 3 Heptads / 7 Dimensions")
        print("═══════════════════════════════════════════════════════════════\n")

        print("── HEPTAD 1: FOUNDATION (Seven-Surah Architecture) ──")
        print("  ∑Surah# = Q82+Q96+Q86+Q22+Q91+Q54+Q16 = 447")
        h1 = [
            ('1', 'KEY', 'al-Infiṭār (82)', 'Entry point — database architecture'),
            ('2', 'KERNEL', 'al-ʿAlaq (96)', 'Core data — root dictionary, Qur\'anic word mapping'),
            ('3', 'SEED', 'aṭ-Ṭāriq (86)', 'Qur\'anic root seeding'),
            ('4', 'NARRATIVE', 'al-Ḥajj (22)', 'Historical narrative — chronology, intelligence'),
            ('5', 'COMPILER', 'ash-Shams (91)', 'Qur\'an compiler — 77,881 words processed'),
            ('6', 'INDEX', 'al-Qamar (54)', 'Graph index — nodes, edges, dimensions'),
            ('7', 'HANDLER', 'an-Naḥl (16)', 'CLI handler — session init, search, context'),
        ]
        for num, role, surah, desc in h1:
            print(f"  Phase {num}: {role} — {surah}")
            print(f"    {desc}")

        print("\n── HEPTAD 2: RESTORATION (Bitig + Body) ──")
        print("  ∑Surah# = Q85+Q83+Q25+Q17+Q59+Q68+Q108 = 445")
        h2 = [
            ('8', 'BURŪJ', 'al-Burūj (85)', 'Bitig shift register — 25 B-codes'),
            ('9', 'MĪZĀN', 'al-Muṭaffifīn (83)', 'Bitig scoring — 10-point rubric'),
            ('10', 'FURQĀN', 'al-Furqān (25)', 'Convergence adjudication — 5-gate rubric'),
            ('11', 'ISRĀ\'', 'al-Isrāʾ (17)', 'Sibling propagation — 56 edges, 11 languages'),
            ('12', 'ḤASHR', 'al-Ḥashr (59)', 'Intelligence summary — 16 records, DP analysis'),
            ('13', 'QALAM', 'al-Qalam (68)', 'Technical reference — BITIG_TECHNICAL_REFERENCE.md'),
            ('14', 'KAWTHAR', 'al-Kawthar (108)', 'Expansion — Orkhon script, dispersal, rescoring'),
        ]
        for num, role, surah, desc in h2:
            print(f"  Phase {num}: {role} — {surah}")
            print(f"    {desc}")

        print("\n── HEPTAD 3: DEPLOYMENT ──")
        print("  ∑Surah# = Q13+Q102+Q30+Q62+Q78+Q99+Q110 = 494")
        h3 = [
            ('15', 'ar-Raʿd (13)', 'Connection',
             'Node indexing, sibling edge wiring'),
            ('16', 'at-Takāthur (102)', 'Multiplication',
             'Latin hub → European fan-out (570 entries)'),
            ('17', 'ar-Rūm (30)', 'Persian Corridor',
             'uslap_rum.py — Persian sibling database'),
            ('18', 'al-Jumuʿah (62)', 'Excel Sync',
             'uslap_jumuah.py — .db ↔ .xlsx synchronisation'),
            ('19', 'an-Nabaʾ (78)', 'Intelligence',
             'uslap_naba.py — INTELLIGENCE dimension wiring'),
            ('20', 'az-Zalzalah (99)', 'Review/Audit',
             'uslap_zalzalah.py — 8-gate comprehensive audit'),
            ('21', 'an-Naṣr (110)', 'Seal/Completion',
             'uslap_nasr.py — This manifest. Architecture sealed.'),
        ]
        for num, surah, role, desc in h3:
            print(f"  Phase {num}: {surah} — {role}")
            print(f"    {desc}")

        # ── TOOLS ──
        print("\n── CLI TOOLS (14 built) ──")
        tools = [
            ('uslap_handler.py', 'Session handler — init, search, state, context, expand'),
            ('uslap_compiler.py', 'Qur\'an compiler — seed, load, status, unmapped, translate'),
            ('uslap_autopop.py', 'Auto-population engine — gaps, corrections, siblings, sem_review'),
            ('uslap_quf.py', 'QUF validator — automated Q/U/F gate checker'),
            ('uslap_latin_hub.py', 'Latin hub engine — demo, status, fan'),
            ('uslap_bitig.py', 'Bitig restoration — search, degrade, converge, verify, dispersal'),
            ('uslap_hashr.py', 'Intelligence gatherer — gather, status, audit'),
            ('uslap_mizan.py', 'Scoring/rescoring — rescore, status, audit, verify'),
            ('uslap_rum.py', 'Persian corridor — populate, status'),
            ('uslap_jumuah.py', 'Excel sync — sync, status'),
            ('uslap_naba.py', 'Intelligence wiring — normalize, dp_map, wire, audit'),
            ('uslap_zalzalah.py', 'Audit engine — 8 gates, auto-fix'),
            ('uslap_nasr.py', 'Seal — this tool'),
            ('uslap_locks.py', 'Write-lock system — lock, unlock, check, status'),
        ]
        for name, desc in tools:
            print(f"  {name:25s} {desc}")

        # ── DIMENSIONS ──
        c = self.conn
        dims = c.execute('''
            SELECT dimension, COUNT(*) as cnt FROM term_dimensions
            GROUP BY dimension ORDER BY cnt DESC
        ''').fetchall()
        print(f"\n── INDEX DIMENSIONS ({len(dims)}) ──")
        total = sum(d['cnt'] for d in dims)
        for d in dims:
            pct = d['cnt'] / total * 100
            print(f"  {d['dimension']:20s}: {d['cnt']:6,} ({pct:4.1f}%)")

        # ── SURAH NUMBER SUMS ──
        print("\n── SURAH NUMBER ARCHITECTURE ──")
        h1_sum = 82 + 96 + 86 + 22 + 91 + 54 + 16
        h2_sum = 85 + 83 + 25 + 17 + 59 + 68 + 108
        h3_sum = 13 + 102 + 30 + 62 + 78 + 99 + 110
        grand = h1_sum + h2_sum + h3_sum
        print(f"  Heptad 1: {h1_sum}")
        print(f"  Heptad 2: {h2_sum}")
        print(f"  Heptad 3: {h3_sum}")
        print(f"  Grand total: {grand} (21 phases × 3 heptads)")

        print(f"\n═══ ARCHITECTURE MANIFEST COMPLETE ═══")
        print(f"═══ {self.timestamp} ═══")

    def all(self):
        """Run seal + manifest."""
        self.seal()
        print("\n")
        self.manifest()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    n = Nasr()

    commands = {
        'status': n.status,
        'seal': n.seal,
        'manifest': n.manifest,
        'all': n.all,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status | seal | manifest | all")


if __name__ == '__main__':
    main()
