#!/usr/bin/env python3
"""
USLaP Qur'an Root-Map Generator
Phase 2 prototype — generates 3-layer output from root-mapped āyāt.

Usage:
    python3 uslap_rootmap.py render 1          # render sūrah 1
    python3 uslap_rootmap.py render 1:3        # render sūrah 1 āyah 3
    python3 uslap_rootmap.py render 1:1-7      # render sūrah 1 āyāt 1-7
    python3 uslap_rootmap.py stats              # show mapping statistics
    python3 uslap_rootmap.py corrections 1      # show QV corrections for sūrah
    python3 uslap_rootmap.py compare 1:2        # side-by-side comparison
    python3 uslap_rootmap.py export 1           # export sūrah as markdown file
    python3 uslap_rootmap.py export all         # export full Qur'an as markdown
    python3 uslap_rootmap.py export-json        # export full Qur'an as JSON
    python3 uslap_rootmap.py export-json 1      # export single sūrah as JSON
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")


def get_db():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def render_ayah(conn, surah, ayah):
    """Render a single āyah in 3-layer format."""
    row = conn.execute(
        "SELECT * FROM quran_ayat WHERE surah=? AND ayah=?", (surah, ayah)
    ).fetchone()
    if not row:
        return f"  Āyah {surah}:{ayah} — not yet in database.\n"

    words = conn.execute(
        "SELECT * FROM quran_word_roots WHERE surah=? AND ayah=? ORDER BY word_position",
        (surah, ayah)
    ).fetchall()

    lines = []
    lines.append(f"  ═══ {surah}:{ayah} ═══\n")

    # Layer 1: Arabic
    lines.append(f"  LAYER 1 — ARABIC:")
    lines.append(f"  {row['aa_text']}\n")

    # Layer 2: Root Translation
    lines.append(f"  LAYER 2 — ROOT TRANSLATION:")
    lines.append(f"  {row['root_translation']}\n")

    # Layer 2b: Common Translation (for comparison)
    if row['translator_text']:
        lines.append(f"  COMMON TRANSLATION:")
        lines.append(f"  {row['translator_text']}\n")

    # Layer 3: Root Map
    if words:
        lines.append(f"  LAYER 3 — ROOT MAP:")
        lines.append(f"  {'─' * 100}")
        lines.append(
            f"  {'#':<3} {'Arabic':<20} {'Root':<10} {'Form':<5} "
            f"{'Type':<9} {'Root Meaning':<40} {'QV':<6}"
        )
        lines.append(f"  {'─' * 100}")

        for w in words:
            root_str = w['root'] or "—"
            form_str = w['verb_form'] or "—"
            type_str = w['word_type'] or "—"
            meaning = (w['root_meaning'] or "—")[:38]
            qv = w['qv_ref'] or ""
            arabic = w['aa_word']

            lines.append(
                f"  {w['word_position']:<3} {arabic:<20} {root_str:<10} {form_str:<5} "
                f"{type_str:<9} {meaning:<40} {qv:<6}"
            )

        lines.append(f"  {'─' * 100}")

        # Flag QV corrections
        qv_words = [w for w in words if w['qv_ref']]
        if qv_words:
            lines.append(f"\n  ⚑ QV CORRECTIONS IN THIS ĀYAH:")
            for w in qv_words:
                qv_info = conn.execute(
                    "SELECT COMMON_MISTRANSLATION, CORRECT_TRANSLATION, CORRUPTION_TYPE "
                    "FROM qv_translation_register WHERE QV_ID=?",
                    (w['qv_ref'],)
                ).fetchone()
                if qv_info:
                    lines.append(
                        f"    {w['qv_ref']}: {w['aa_word']} — "
                        f"translators say \"{qv_info['COMMON_MISTRANSLATION']}\" → "
                        f"root says \"{qv_info['CORRECT_TRANSLATION']}\" "
                        f"[{qv_info['CORRUPTION_TYPE']}]"
                    )

    lines.append("")
    return "\n".join(lines)


def render_surah(conn, surah, ayah_start=None, ayah_end=None):
    """Render a range of āyāt from a sūrah."""
    if ayah_start and ayah_end:
        rows = conn.execute(
            "SELECT ayah FROM quran_ayat WHERE surah=? AND ayah BETWEEN ? AND ? ORDER BY ayah",
            (surah, ayah_start, ayah_end)
        ).fetchall()
    elif ayah_start:
        rows = conn.execute(
            "SELECT ayah FROM quran_ayat WHERE surah=? AND ayah=?",
            (surah, ayah_start)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT ayah FROM quran_ayat WHERE surah=? ORDER BY ayah",
            (surah,)
        ).fetchall()

    if not rows:
        print(f"  No āyāt found for sūrah {surah}.")
        return

    # Header
    total_words = conn.execute(
        "SELECT COUNT(*) as c FROM quran_word_roots WHERE surah=?", (surah,)
    ).fetchone()['c']
    total_qv = conn.execute(
        "SELECT COUNT(*) as c FROM quran_word_roots WHERE surah=? AND qv_ref IS NOT NULL",
        (surah,)
    ).fetchone()['c']

    print(f"\n  {'═' * 60}")
    print(f"  SŪRAH {surah} — ROOT-BASED TRANSLATION")
    print(f"  {len(rows)} āyāt | {total_words} words mapped | {total_qv} QV corrections")
    print(f"  {'═' * 60}\n")

    for r in rows:
        print(render_ayah(conn, surah, r['ayah']))


def show_stats(conn):
    """Show overall mapping statistics."""
    ayat_count = conn.execute("SELECT COUNT(*) as c FROM quran_ayat").fetchone()['c']
    word_count = conn.execute("SELECT COUNT(*) as c FROM quran_word_roots").fetchone()['c']
    qv_count = conn.execute(
        "SELECT COUNT(*) as c FROM quran_word_roots WHERE qv_ref IS NOT NULL"
    ).fetchone()['c']
    qv_register = conn.execute(
        "SELECT COUNT(*) as c FROM qv_translation_register"
    ).fetchone()['c']
    mapped_surahs = conn.execute(
        "SELECT DISTINCT surah FROM quran_ayat ORDER BY surah"
    ).fetchall()

    # Unique roots
    unique_roots = conn.execute(
        "SELECT COUNT(DISTINCT root) as c FROM quran_word_roots WHERE root IS NOT NULL"
    ).fetchone()['c']

    # QV breakdown
    qv_types = conn.execute(
        "SELECT qr.CORRUPTION_TYPE, COUNT(*) as c "
        "FROM quran_word_roots w JOIN qv_translation_register qr ON w.qv_ref = qr.QV_ID "
        "GROUP BY qr.CORRUPTION_TYPE ORDER BY c DESC"
    ).fetchall()

    print(f"\n  USLaP Root-Map Statistics")
    print(f"  {'─' * 40}")
    print(f"  Āyāt mapped:        {ayat_count} / 6,236")
    print(f"  Words mapped:        {word_count}")
    print(f"  Unique roots:        {unique_roots}")
    print(f"  QV corrections:      {qv_count} (in mapped āyāt)")
    print(f"  QV Register total:   {qv_register} terms")
    print(f"  Sūrahs started:      {', '.join(str(s['surah']) for s in mapped_surahs)}")
    print(f"  Coverage:            {ayat_count/6236*100:.1f}%")
    print(f"  {'─' * 40}")

    if qv_types:
        print(f"\n  QV Corrections by Type (in mapped āyāt):")
        for t in qv_types:
            print(f"    {t['CORRUPTION_TYPE']:<30} {t['c']}")

    # Word type breakdown
    word_types = conn.execute(
        "SELECT word_type, COUNT(*) as c FROM quran_word_roots "
        "GROUP BY word_type ORDER BY c DESC"
    ).fetchall()
    if word_types:
        print(f"\n  Word Types:")
        for t in word_types:
            print(f"    {t['word_type'] or 'UNKNOWN':<15} {t['c']}")


def show_corrections(conn, surah):
    """Show all QV corrections in a sūrah."""
    rows = conn.execute(
        "SELECT w.ayah, w.word_position, w.aa_word, w.qv_ref, w.correct_translation, "
        "w.common_translation, qr.CORRUPTION_TYPE, qr.ROOT "
        "FROM quran_word_roots w "
        "JOIN qv_translation_register qr ON w.qv_ref = qr.QV_ID "
        "WHERE w.surah=? ORDER BY w.ayah, w.word_position",
        (surah,)
    ).fetchall()

    if not rows:
        print(f"  No QV corrections in sūrah {surah}.")
        return

    print(f"\n  QV CORRECTIONS — SŪRAH {surah}")
    print(f"  {'─' * 90}")
    print(f"  {'Āyah':<6} {'Arabic':<18} {'Root':<10} {'Translators Say':<25} {'Root Says':<30} {'Type'}")
    print(f"  {'─' * 90}")

    for r in rows:
        common = r['common_translation'] or "—"
        correct = r['correct_translation'] or "—"
        ctype = r['CORRUPTION_TYPE'] or "—"
        print(
            f"  {r['ayah']:<6} {r['aa_word']:<18} {r['ROOT']:<10} "
            f"{common:<28} {correct:<32} {ctype}"
        )


def compare_ayah(conn, surah, ayah):
    """Side-by-side comparison of common vs root translation."""
    row = conn.execute(
        "SELECT * FROM quran_ayat WHERE surah=? AND ayah=?", (surah, ayah)
    ).fetchone()
    if not row:
        print(f"  Āyah {surah}:{ayah} not found.")
        return

    words = conn.execute(
        "SELECT * FROM quran_word_roots WHERE surah=? AND ayah=? ORDER BY word_position",
        (surah, ayah)
    ).fetchall()

    print(f"\n  COMPARISON — {surah}:{ayah}")
    print(f"  {'═' * 70}")
    print(f"  ARABIC:     {row['aa_text']}")
    print(f"  COMMON:     {row['translator_text']}")
    print(f"  ROOT-BASED: {row['root_translation']}")
    print(f"  {'═' * 70}")

    if words:
        print(f"\n  WORD-BY-WORD:")
        print(f"  {'Arabic':<18} {'Common':<25} {'Root-Based':<30}")
        print(f"  {'─' * 73}")
        for w in words:
            common = w['common_translation'] or "—"
            correct = w['correct_translation'] or "—"
            marker = " ⚑" if w['qv_ref'] else ""
            print(f"  {w['aa_word']:<18} {common:<25} {correct:<30}{marker}")


def export_surah(conn, surah):
    """Export sūrah as markdown file."""
    rows = conn.execute(
        "SELECT * FROM quran_ayat WHERE surah=? ORDER BY ayah", (surah,)
    ).fetchall()
    if not rows:
        print(f"  No data for sūrah {surah}.")
        return

    workspace = os.path.dirname(os.path.dirname(__file__))
    outpath = os.path.join(workspace, f"USLaP_Surah_{surah:03d}_RootMap.md")

    lines = []
    lines.append("# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\n")
    lines.append(f"# Sūrah {surah} — Root-Based Translation\n")
    lines.append("Generated by USLaP Root-Map Engine (Phase 2 Prototype)\n")
    lines.append("---\n")

    for row in rows:
        lines.append(f"## {surah}:{row['ayah']}\n")
        lines.append(f"**Arabic:** {row['aa_text']}\n")
        lines.append(f"**Root Translation:** {row['root_translation']}\n")
        lines.append(f"**Common Translation:** {row['translator_text']}\n")

        words = conn.execute(
            "SELECT * FROM quran_word_roots WHERE surah=? AND ayah=? ORDER BY word_position",
            (surah, row['ayah'])
        ).fetchall()

        if words:
            lines.append("| # | Arabic | Root | Form | Type | Root Meaning | Correct | Common | QV |")
            lines.append("|---|--------|------|------|------|-------------|---------|--------|----|")
            for w in words:
                lines.append(
                    f"| {w['word_position']} | {w['aa_word']} | {w['root'] or '—'} | "
                    f"{w['verb_form'] or '—'} | {w['word_type'] or '—'} | "
                    f"{(w['root_meaning'] or '—')[:35]} | {w['correct_translation'] or '—'} | "
                    f"{w['common_translation'] or '—'} | {w['qv_ref'] or ''} |"
                )

        # QV flags
        qv_words = [w for w in words if w['qv_ref']]
        if qv_words:
            lines.append(f"\n**QV Corrections:**")
            for w in qv_words:
                qv_info = conn.execute(
                    "SELECT COMMON_MISTRANSLATION, CORRECT_TRANSLATION, CORRUPTION_TYPE "
                    "FROM qv_translation_register WHERE QV_ID=?",
                    (w['qv_ref'],)
                ).fetchone()
                if qv_info:
                    lines.append(
                        f"- **{w['qv_ref']}** ({w['aa_word']}): "
                        f"translators say \"{qv_info['COMMON_MISTRANSLATION']}\" → "
                        f"root says \"{qv_info['CORRECT_TRANSLATION']}\" "
                        f"[{qv_info['CORRUPTION_TYPE']}]"
                    )

        lines.append("\n---\n")

    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Exported to: {outpath}")


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


def export_full_quran(conn):
    """Export the full Qur'an as a single markdown file."""
    import json
    workspace = os.path.dirname(os.path.dirname(__file__))
    outpath = os.path.join(workspace, "USLaP_Quran_Root_Translation_FULL.md")

    # Global stats
    total_words = conn.execute("SELECT COUNT(*) as c FROM quran_word_roots").fetchone()['c']
    rooted = conn.execute("SELECT COUNT(*) as c FROM quran_word_roots WHERE root IS NOT NULL AND root != '' AND word_type != 'PARTICLE'").fetchone()['c']
    particles = conn.execute("SELECT COUNT(*) as c FROM quran_word_roots WHERE word_type = 'PARTICLE'").fetchone()['c']
    coverage = round((rooted + particles) / total_words * 100, 1)
    qv_total = conn.execute("SELECT COUNT(*) as c FROM qv_translation_register").fetchone()['c']

    lines = []
    lines.append("# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\n")
    lines.append("# USLaP Qur'an Root Translation — Complete\n")
    lines.append("**Generated by the USLaP Unified Linguistic Lattice Root-Map Engine**\n")
    lines.append(f"- Total words: {total_words:,}")
    lines.append(f"- Root coverage: {coverage}%")
    lines.append(f"- QV Translation Register: {qv_total} entries")
    lines.append(f"- Translation method: Root-based (no translator contamination)\n")
    lines.append("---\n")

    for surah_num in range(1, 115):
        name = SURAH_NAMES.get(surah_num, f"Surah {surah_num}")
        ayat = conn.execute(
            "SELECT ayah, aa_text, root_translation FROM quran_ayat WHERE surah=? ORDER BY ayah",
            (surah_num,)
        ).fetchall()
        if not ayat:
            continue

        lines.append(f"\n## Surah {surah_num}: {name}\n")

        for row in ayat:
            lines.append(f"### {surah_num}:{row['ayah']}\n")
            lines.append(f"**{row['aa_text']}**\n")
            lines.append(f"{row['root_translation']}\n")

        lines.append("---\n")

    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Full Qur'an exported to: {outpath}")
    return outpath


def export_json(conn, surah_num=None):
    """Export as structured JSON for programmatic use."""
    import json
    workspace = os.path.dirname(os.path.dirname(__file__))

    data = {
        'metadata': {
            'title': "USLaP Qur'an Root Translation",
            'method': 'Root-based translation via USLaP Unified Linguistic Lattice',
            'generated': __import__('datetime').datetime.now().isoformat(),
            'qv_entries': conn.execute("SELECT COUNT(*) as c FROM qv_translation_register").fetchone()['c'],
        },
        'surahs': []
    }

    surah_range = [surah_num] if surah_num else range(1, 115)

    for s in surah_range:
        name = SURAH_NAMES.get(s, f"Surah {s}")
        ayat = conn.execute(
            "SELECT ayah, aa_text, root_translation, translator_text FROM quran_ayat WHERE surah=? ORDER BY ayah",
            (s,)
        ).fetchall()
        if not ayat:
            continue

        surah_data = {
            'number': s,
            'name': name,
            'ayat': []
        }

        for row in ayat:
            words = conn.execute(
                "SELECT word_position, aa_word, root, root_meaning, verb_form, word_type, "
                "correct_translation, common_translation, qv_ref, confidence "
                "FROM quran_word_roots WHERE surah=? AND ayah=? ORDER BY word_position",
                (s, row['ayah'])
            ).fetchall()

            ayah_data = {
                'ayah': row['ayah'],
                'aa_term': row['aa_text'],
                'root_translation': row['root_translation'],
                'common_translation': row['translator_text'],
                'words': []
            }

            for w in words:
                word_data = {
                    'position': w['word_position'],
                    'aa_term': w['aa_word'],
                    'root': w['root'],
                    'meaning': w['root_meaning'],
                    'verb_form': w['verb_form'],
                    'type': w['word_type'],
                    'confidence': w['confidence'],
                }
                if w['qv_ref']:
                    word_data['qv_ref'] = w['qv_ref']
                    word_data['correct'] = w['correct_translation']
                    word_data['contaminated'] = w['common_translation']
                ayah_data['words'].append(word_data)

            surah_data['ayat'].append(ayah_data)

        data['surahs'].append(surah_data)

    if surah_num:
        outpath = os.path.join(workspace, f"USLaP_Surah_{surah_num:03d}_RootMap.json")
    else:
        outpath = os.path.join(workspace, "USLaP_Quran_Root_Translation_FULL.json")

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  JSON exported to: {outpath}")
    return outpath


def parse_ref(ref_str):
    """Parse reference like '1', '1:3', '1:1-7'."""
    if ':' in ref_str:
        surah_str, ayah_str = ref_str.split(':', 1)
        surah = int(surah_str)
        if '-' in ayah_str:
            start, end = ayah_str.split('-', 1)
            return surah, int(start), int(end)
        return surah, int(ayah_str), None
    return int(ref_str), None, None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    conn = get_db()

    if cmd == "render":
        if len(sys.argv) < 3:
            print("  Usage: uslap_rootmap.py render <surah>[:<ayah>[-<ayah>]]")
            return
        surah, ayah_start, ayah_end = parse_ref(sys.argv[2])
        render_surah(conn, surah, ayah_start, ayah_end)

    elif cmd == "stats":
        show_stats(conn)

    elif cmd == "corrections":
        if len(sys.argv) < 3:
            print("  Usage: uslap_rootmap.py corrections <surah>")
            return
        show_corrections(conn, int(sys.argv[2]))

    elif cmd == "compare":
        if len(sys.argv) < 3:
            print("  Usage: uslap_rootmap.py compare <surah>:<ayah>")
            return
        surah, ayah, _ = parse_ref(sys.argv[2])
        if ayah is None:
            print("  Need specific āyah for comparison (e.g. 1:2)")
            return
        compare_ayah(conn, surah, ayah)

    elif cmd == "export":
        if len(sys.argv) < 3:
            print("  Usage: uslap_rootmap.py export <surah|all>")
            return
        if sys.argv[2] == "all":
            export_full_quran(conn)
        else:
            export_surah(conn, int(sys.argv[2]))

    elif cmd == "export-json":
        if len(sys.argv) >= 3:
            export_json(conn, int(sys.argv[2]))
        else:
            export_json(conn)

    else:
        print(f"  Unknown command: {cmd}")
        print(__doc__)

    conn.close()


if __name__ == "__main__":
    main()
