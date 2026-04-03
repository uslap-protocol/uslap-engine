#!/usr/bin/env python3
"""
USLaP Qur'an Root Translation — Audit Engine
Phase 5C: Generates audit reports for translation quality.
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')

SURAH_NAMES = {
    1: "Al-Fatiha", 2: "Al-Baqarah", 3: "Aal-Imran", 4: "An-Nisa", 5: "Al-Ma'idah",
    6: "Al-An'am", 7: "Al-A'raf", 8: "Al-Anfal", 9: "At-Tawbah", 10: "Yunus",
    11: "Hud", 12: "Yusuf", 13: "Ar-Ra'd", 14: "Ibrahim", 15: "Al-Hijr",
    16: "An-Nahl", 17: "Al-Isra", 18: "Al-Kahf", 19: "Maryam", 20: "Ta-Ha",
    21: "Al-Anbiya", 22: "Al-Hajj", 23: "Al-Mu'minun", 24: "An-Nur", 25: "Al-Furqan",
    26: "Ash-Shu'ara", 27: "An-Naml", 28: "Al-Qasas", 29: "Al-Ankabut", 30: "Ar-Rum",
    31: "Luqman", 32: "As-Sajdah", 33: "Al-Ahzab", 34: "Saba", 35: "Fatir",
    36: "Ya-Sin", 37: "As-Saffat", 38: "Sad", 39: "Az-Zumar", 40: "Ghafir",
    41: "Fussilat", 42: "Ash-Shura", 43: "Az-Zukhruf", 44: "Ad-Dukhan",
    45: "Al-Jathiyah", 46: "Al-Ahqaf", 47: "Muhammad", 48: "Al-Fath",
    49: "Al-Hujurat", 50: "Qaf", 51: "Adh-Dhariyat", 52: "At-Tur",
    53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahman", 56: "Al-Waqi'ah",
    57: "Al-Hadid", 58: "Al-Mujadila", 59: "Al-Hashr", 60: "Al-Mumtahanah",
    61: "As-Saff", 62: "Al-Jumu'ah", 63: "Al-Munafiqun", 64: "At-Taghabun",
    65: "At-Talaq", 66: "At-Tahrim", 67: "Al-Mulk", 68: "Al-Qalam",
    69: "Al-Haqqah", 70: "Al-Ma'arij", 71: "Nuh", 72: "Al-Jinn",
    73: "Al-Muzzammil", 74: "Al-Muddaththir", 75: "Al-Qiyamah", 76: "Al-Insan",
    77: "Al-Mursalat", 78: "An-Naba", 79: "An-Nazi'at", 80: "Abasa",
    81: "At-Takwir", 82: "Al-Infitar", 83: "Al-Mutaffifin", 84: "Al-Inshiqaq",
    85: "Al-Buruj", 86: "At-Tariq", 87: "Al-A'la", 88: "Al-Ghashiyah",
    89: "Al-Fajr", 90: "Al-Balad", 91: "Ash-Shams", 92: "Al-Layl",
    93: "Ad-Duha", 94: "Ash-Sharh", 95: "At-Tin", 96: "Al-Alaq",
    97: "Al-Qadr", 98: "Al-Bayyinah", 99: "Az-Zalzalah", 100: "Al-Adiyat",
    101: "Al-Qari'ah", 102: "At-Takathur", 103: "Al-Asr", 104: "Al-Humazah",
    105: "Al-Fil", 106: "Quraysh", 107: "Al-Ma'un", 108: "Al-Kawthar",
    109: "Al-Kafirun", 110: "An-Nasr", 111: "Al-Masad", 112: "Al-Ikhlas",
    113: "Al-Falaq", 114: "An-Nas",
}


def get_conn():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def global_stats(conn):
    """Generate global coverage and quality statistics."""
    stats = {}

    # Word-level stats
    total = conn.execute('SELECT COUNT(*) FROM quran_word_roots').fetchone()[0]
    rooted = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE word_type NOT IN ('PARTICLE','') AND root IS NOT NULL AND root != ''").fetchone()[0]
    particles = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE word_type = 'PARTICLE'").fetchone()[0]
    unrooted = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE (root IS NULL OR root = '') AND word_type != 'PARTICLE'").fetchone()[0]

    stats['total_words'] = total
    stats['rooted'] = rooted
    stats['particles'] = particles
    stats['unrooted'] = unrooted
    stats['coverage_pct'] = round((rooted + particles) / total * 100, 1)

    # Confidence distribution
    for conf in ['HIGH', 'MEDIUM', 'LOW', 'UNROOTED', 'PARTICLE']:
        cnt = conn.execute('SELECT COUNT(*) FROM quran_word_roots WHERE confidence = ?', (conf,)).fetchone()[0]
        stats[f'confidence_{conf.lower()}'] = cnt

    # Ayah-level stats
    total_ayat = conn.execute('SELECT COUNT(*) FROM quran_ayat').fetchone()[0]
    # Count gap-free from live word-level data (not stale translation cache)
    gap_free = conn.execute("""
        SELECT COUNT(*) FROM quran_ayat a
        WHERE NOT EXISTS (
            SELECT 1 FROM quran_word_roots w
            WHERE w.surah = a.surah AND w.ayah = a.ayah AND w.confidence = 'UNROOTED'
        )
    """).fetchone()[0]
    with_qv = conn.execute("SELECT COUNT(DISTINCT surah || ':' || ayah) FROM quran_word_roots WHERE qv_ref IS NOT NULL AND qv_ref != ''").fetchone()[0]

    stats['total_ayat'] = total_ayat
    stats['gap_free_ayat'] = gap_free
    stats['gap_free_pct'] = round(gap_free / total_ayat * 100, 1)
    stats['ayat_with_qv'] = with_qv

    # Root stats
    unique_roots = conn.execute("SELECT COUNT(DISTINCT root) FROM quran_word_roots WHERE root IS NOT NULL AND root != ''").fetchone()[0]
    stats['unique_roots'] = unique_roots

    # Verb form stats
    verb_forms = conn.execute("SELECT verb_form, COUNT(*) FROM quran_word_roots WHERE verb_form IS NOT NULL AND verb_form != '' GROUP BY verb_form ORDER BY COUNT(*) DESC").fetchall()
    stats['verb_forms'] = {vf: cnt for vf, cnt in verb_forms}

    # QV register
    qv_count = conn.execute('SELECT COUNT(*) FROM qv_translation_register').fetchone()[0]
    stats['qv_entries'] = qv_count

    # Known forms
    kf_count = conn.execute('SELECT COUNT(*) FROM quran_known_forms').fetchone()[0]
    stats['known_forms'] = kf_count

    return stats


def surah_report(conn, surah_num):
    """Generate audit report for a single surah."""
    report = {}
    name = SURAH_NAMES.get(surah_num, f'Surah {surah_num}')
    report['surah'] = surah_num
    report['name'] = name

    # Word stats for this surah
    total = conn.execute('SELECT COUNT(*) FROM quran_word_roots WHERE surah = ?', (surah_num,)).fetchone()[0]
    rooted = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE surah = ? AND word_type NOT IN ('PARTICLE','') AND root IS NOT NULL AND root != ''", (surah_num,)).fetchone()[0]
    particles = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE surah = ? AND word_type = 'PARTICLE'", (surah_num,)).fetchone()[0]
    unrooted = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE surah = ? AND (root IS NULL OR root = '') AND word_type != 'PARTICLE'", (surah_num,)).fetchone()[0]

    report['total_words'] = total
    report['rooted'] = rooted
    report['particles'] = particles
    report['unrooted'] = unrooted
    report['coverage_pct'] = round((rooted + particles) / total * 100, 1) if total > 0 else 0

    # Ayat stats
    ayat = conn.execute('SELECT COUNT(*) FROM quran_ayat WHERE surah = ?', (surah_num,)).fetchone()[0]
    gap_free = conn.execute("""
        SELECT COUNT(*) FROM quran_ayat a
        WHERE a.surah = ? AND NOT EXISTS (
            SELECT 1 FROM quran_word_roots w
            WHERE w.surah = a.surah AND w.ayah = a.ayah AND w.confidence = 'UNROOTED'
        )
    """, (surah_num,)).fetchone()[0]
    report['total_ayat'] = ayat
    report['gap_free_ayat'] = gap_free

    # Flag problematic ayat (those with gaps or many unrooted words)
    flagged = []
    ayat_rows = conn.execute('SELECT ayah, root_translation FROM quran_ayat WHERE surah = ? ORDER BY ayah', (surah_num,)).fetchall()
    for ayah_num, translation in ayat_rows:
        issues = []
        if '___' in (translation or ''):
            gap_count = translation.count('___')
            issues.append(f'{gap_count} gap(s)')

        # Check unrooted count in this ayah
        ur = conn.execute("SELECT COUNT(*) FROM quran_word_roots WHERE surah = ? AND ayah = ? AND (root IS NULL OR root = '') AND word_type != 'PARTICLE'", (surah_num, ayah_num)).fetchone()[0]
        if ur > 0:
            issues.append(f'{ur} unrooted')

        if issues:
            flagged.append({
                'ayah': ayah_num,
                'issues': ', '.join(issues),
                'translation': translation[:200] if translation else '(empty)'
            })

    report['flagged_ayat'] = flagged
    report['flagged_count'] = len(flagged)

    return report


def full_audit(conn):
    """Generate full audit across all surahs."""
    stats = global_stats(conn)

    surah_summaries = []
    for s in range(1, 115):
        sr = surah_report(conn, s)
        surah_summaries.append({
            'surah': s,
            'name': sr['name'],
            'coverage': sr['coverage_pct'],
            'ayat': sr['total_ayat'],
            'gap_free': sr['gap_free_ayat'],
            'flagged': sr['flagged_count'],
            'unrooted': sr['unrooted'],
        })

    return stats, surah_summaries


def print_audit_report():
    """Print formatted audit report to stdout."""
    conn = get_conn()
    stats, surah_summaries = full_audit(conn)

    print("=" * 70)
    print("USLaP QUR'AN ROOT TRANSLATION — AUDIT REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    print(f"\n--- GLOBAL STATISTICS ---")
    print(f"Total words:      {stats['total_words']:,}")
    print(f"Rooted:           {stats['rooted']:,} ({stats['rooted']/stats['total_words']*100:.1f}%)")
    print(f"Particles:        {stats['particles']:,} ({stats['particles']/stats['total_words']*100:.1f}%)")
    print(f"Unrooted:         {stats['unrooted']:,} ({stats['unrooted']/stats['total_words']*100:.1f}%)")
    print(f"Coverage:         {stats['coverage_pct']}%")
    print(f"")
    print(f"Total ayat:       {stats['total_ayat']:,}")
    print(f"Gap-free ayat:    {stats['gap_free_ayat']:,} ({stats['gap_free_pct']}%)")
    print(f"Ayat with QV:     {stats['ayat_with_qv']:,}")
    print(f"Unique roots:     {stats['unique_roots']:,}")
    print(f"QV entries:       {stats['qv_entries']}")
    print(f"Known forms:      {stats['known_forms']}")

    print(f"\n--- CONFIDENCE DISTRIBUTION ---")
    print(f"HIGH (known form):  {stats['confidence_high']:,}")
    print(f"MEDIUM (extracted): {stats['confidence_medium']:,}")
    print(f"UNROOTED:           {stats['confidence_unrooted']:,}")
    print(f"PARTICLE:           {stats['confidence_particle']:,}")

    print(f"\n--- TASRIF PATTERN DISTRIBUTION ---")
    for vf, cnt in sorted(stats['verb_forms'].items(), key=lambda x: -x[1]):
        print(f"  {vf:>14}: {cnt:,}")

    print(f"\n--- SURAH COVERAGE SUMMARY ---")
    print(f"{'#':>3} {'Name':<20} {'Cov%':>5} {'Ayat':>5} {'GapFr':>5} {'Flag':>5} {'Unrt':>5}")
    print("-" * 70)
    for s in surah_summaries:
        print(f"{s['surah']:>3} {s['name']:<20} {s['coverage']:>5.1f} {s['ayat']:>5} {s['gap_free']:>5} {s['flagged']:>5} {s['unrooted']:>5}")

    # Worst surahs by coverage
    worst = sorted(surah_summaries, key=lambda x: x['coverage'])[:10]
    print(f"\n--- 10 LOWEST COVERAGE SURAHS ---")
    for s in worst:
        print(f"  {s['surah']:>3}. {s['name']:<20} {s['coverage']:.1f}% ({s['unrooted']} unrooted)")

    conn.close()


def export_audit_json(output_path=None):
    """Export full audit as JSON."""
    conn = get_conn()
    stats, surah_summaries = full_audit(conn)

    data = {
        'generated': datetime.now().isoformat(),
        'global_stats': stats,
        'surah_summaries': surah_summaries,
    }

    if output_path is None:
        output_path = os.path.join(os.path.dirname(DB_PATH), '..', 'uslap_audit_report.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Audit exported to: {output_path}")
    conn.close()
    return output_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'json':
        export_audit_json()
    else:
        print_audit_report()
