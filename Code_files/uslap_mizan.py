#!/usr/bin/env python3
"""
USLaP MĪZĀN (al-Raḥmān layer) — Granular confidence scoring for Qur'an root mapping.

Q55:7-9: وَالسَّمَاءَ رَفَعَهَا وَوَضَعَ الْمِيزَانَ / أَلَّا تَطْغَوْا فِي الْمِيزَانِ /
وَأَقِيمُوا الْوَزْنَ بِالْقِسْطِ وَلَا تُخْسِرُوا الْمِيزَانَ
"He raised the heaven and set the BALANCE / so that you do not transgress the BALANCE /
and weigh with justice and do not fall short in the BALANCE"

Confidence levels:
    HIGH      — Known-form exact match (Strategy 0). Pre-mapped Qur'anic forms.
    MEDIUM_A  — Direct dictionary match on Level 0-2 candidate.
                Root found from bare normalized form, article-stripped, or suffix-stripped.
                Minimal morphological distance.
    MEDIUM_B  — Match after standard morphological stripping (Levels 3-5).
                Conjunction prefix, preposition prefix, verbal prefix/suffix.
                Standard Arabic inflection—reliable.
    MEDIUM_C  — Match after reconstruction or skeleton extraction (Level 5c-6).
                Hollow verb, defective verb, double-hamza collapse, consonant skeleton.
                Reconstruction required—correct but needs auditing.
    LOW       — Match via 3-letter subset (Level 7) or no-meaning fallback.
                Speculative—highest error rate.
    PARTICLE  — Functional word (no root).
    UNROOTED  — No match found.

Usage:
    python3 uslap_mizan.py rescore          # re-score all MEDIUM entries
    python3 uslap_mizan.py status           # show confidence distribution
    python3 uslap_mizan.py audit WORD       # show scoring trace for a word
    python3 uslap_mizan.py verify           # spot-check accuracy per grade
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys
import os

# Import compiler functions
sys.path.insert(0, os.path.dirname(__file__))
from uslap_compiler import (
    prepare_for_root, generate_root_candidates, strip_diacritics,
    normalize_alef, strip_consonant_skeleton, PARTICLES, classify_word,
    PRONOUN_SUFFIXES, GRAM_SUFFIXES
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")


def get_db():
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def generate_tagged_candidates(word):
    """
    Generate root candidates tagged with their cascade level.
    Returns list of (candidate, level) tuples where level is:
        0 = direct normalized
        1 = article stripped
        2 = suffix stripped
        3 = conjunction prefix stripped
        4 = preposition prefix stripped
        5 = verbal/morphological prefix stripped
        5.5 = double-hamza collapse
        6 = consonant skeleton
        7 = 3-letter subset
    """
    bare = prepare_for_root(word)
    bare_shad = prepare_for_root(word, expand_shadda=True)
    tagged = []
    seen = set()

    def add(c, level):
        if c and len(c) >= 2 and c not in seen:
            seen.add(c)
            tagged.append((c, level))

    # Level 0: Direct normalized forms
    add(bare, 0)
    if bare_shad != bare:
        add(bare_shad, 0)

    # Level 1: Strip definite article ال
    if bare_shad.startswith('ال') and len(bare_shad) > 3:
        after_al = bare_shad[2:]
        if len(after_al) >= 2 and after_al[0] == after_al[1]:
            add(after_al[1:], 1)
        add(after_al, 1)
    if bare.startswith('ال') and len(bare) > 3:
        add(bare[2:], 1)

    # Level 2: Strip suffix patterns
    bases_for_suffix = [(c, l) for c, l in tagged]
    for base, _ in bases_for_suffix:
        for suf in PRONOUN_SUFFIXES:
            if base.endswith(suf) and len(base) > len(suf) + 1:
                add(base[:-len(suf)], 2)
                break
        for suf in GRAM_SUFFIXES:
            if base.endswith(suf) and len(base) > len(suf) + 1:
                add(base[:-len(suf)], 2)
                break
        if base.endswith('ة') and len(base) > 2:
            add(base[:-1], 2)
        if base.endswith('ا') and len(base) > 3:
            add(base[:-1], 2)

    # Level 3: Conjunction prefix (و ف)
    if len(bare) > 3 and bare[0] in ('و', 'ف'):
        rest = bare[1:]
        add(rest, 3)
        if rest.startswith('ال') and len(rest) > 3:
            after_al = rest[2:]
            add(after_al, 3)
            rest_shad = bare_shad[1:] if len(bare_shad) > 3 and bare_shad[0] in ('و', 'ف') else rest
            if rest_shad.startswith('ال') and len(rest_shad) > 3:
                after_al_shad = rest_shad[2:]
                if len(after_al_shad) >= 2 and after_al_shad[0] == after_al_shad[1]:
                    add(after_al_shad[1:], 3)
        for suf in PRONOUN_SUFFIXES:
            if rest.endswith(suf) and len(rest) > len(suf) + 1:
                add(rest[:-len(suf)], 3)
                break
        for suf in GRAM_SUFFIXES:
            if rest.endswith(suf) and len(rest) > len(suf) + 1:
                add(rest[:-len(suf)], 3)
                break
        if rest.endswith('ة') and len(rest) > 2:
            add(rest[:-1], 3)
        if rest.endswith('ا') and len(rest) > 3:
            add(rest[:-1], 3)

    # Level 4: Preposition prefix (ب ك ل)
    for prep_base in [bare, bare[1:] if len(bare) > 3 and bare[0] in ('و', 'ف') else None]:
        if prep_base and len(prep_base) > 3 and prep_base[0] in ('ب', 'ك', 'ل'):
            rest = prep_base[1:]
            add(rest, 4)
            if rest.startswith('ال') and len(rest) > 3:
                add(rest[2:], 4)
            for suf in PRONOUN_SUFFIXES:
                if rest.endswith(suf) and len(rest) > len(suf) + 1:
                    add(rest[:-len(suf)], 4)
                    break
            if rest.endswith('ة') and len(rest) > 2:
                add(rest[:-1], 4)
            if rest.endswith('ا') and len(rest) > 3:
                add(rest[:-1], 4)
        if prep_base and prep_base.startswith('لل') and len(prep_base) > 3:
            add(prep_base[2:], 4)

    # Level 5: Verbal/morphological prefix stripping
    current_candidates = [(c, l) for c, l in tagged]
    for c, _ in current_candidates:
        stems = []
        if len(c) >= 4 and c[0] in ('ي', 'ت', 'ن', 'ا'):
            stems.append(c[1:])
            add(c[1:], 5)
        if len(c) >= 4 and c[0] == 'م':
            stems.append(c[1:])
            add(c[1:], 5)
        if len(c) >= 6 and c[:3] == 'است':
            stems.append(c[3:])
            add(c[3:], 5)
        if len(c) >= 5 and c[:3] == 'افت':
            stems.append(c[3:])
            add(c[3:], 5)
            if len(c) >= 5:
                stems.append(c[1] + c[3:])
                add(c[1] + c[3:], 5)
        if len(c) >= 5 and c[:2] == 'ان':
            stems.append(c[2:])
            add(c[2:], 5)

        # Level 5b: suffix from verbal stems
        for stem in stems:
            for suf in PRONOUN_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 1:
                    add(stem[:-len(suf)], 5)
                    break
            for suf in GRAM_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 1:
                    add(stem[:-len(suf)], 5)
                    break
            if stem.endswith('ة') and len(stem) > 2:
                add(stem[:-1], 5)
            if stem.endswith('ا') and len(stem) > 3:
                add(stem[:-1], 5)
            if len(stem) >= 5 and stem[:3] == 'ست':
                x_stem = stem[3:]
                add(x_stem, 5)
                for suf in PRONOUN_SUFFIXES:
                    if x_stem.endswith(suf) and len(x_stem) > len(suf) + 1:
                        add(x_stem[:-len(suf)], 5)
                        break
            if len(stem) >= 4 and stem[1] == 'ت':
                viii_stem = stem[0] + stem[2:]
                add(viii_stem, 5)
                for suf in PRONOUN_SUFFIXES + GRAM_SUFFIXES:
                    if viii_stem.endswith(suf) and len(viii_stem) > len(suf) + 1:
                        add(viii_stem[:-len(suf)], 5)
                        break

    # Level 5.5: Double-hamza collapse
    for c, _ in list(tagged):
        if 'ءء' in c:
            collapsed = c.replace('ءء', 'ء')
            add(collapsed, 5.5)
            if len(collapsed) >= 4:
                skel = strip_consonant_skeleton(collapsed)
                if skel != collapsed:
                    add(skel, 5.5)

    # Level 6: Consonant skeleton
    for c, _ in list(tagged):
        skel = strip_consonant_skeleton(c)
        if skel != c:
            add(skel, 6)

    # Level 7: 3-letter subsets
    for c, _ in list(tagged):
        if len(c) >= 4:
            add(c[:3], 7)
            add(c[1:4], 7)
        if len(c) >= 5:
            add(c[2:5], 7)
            add(c[:2] + c[3], 7)
            add(c[0] + c[2:4], 7)

    return tagged


def try_lookup_tagged(candidate, conn):
    """
    Try candidate against dictionary. Returns (root_hyph, meaning, method) or None.
    method describes HOW the match was found (for MĪZĀN audit trail).
    """
    # Direct lookup
    row = conn.execute(
        "SELECT root_hyphenated, root_meaning FROM root_translations "
        "WHERE root_unhyphenated = ?", (candidate,)
    ).fetchone()
    if row and row['root_meaning']:
        return (row['root_hyphenated'], row['root_meaning'], 'DIRECT')
    direct_hit = row

    # ا → أ at start
    if candidate.startswith('ا'):
        row = conn.execute(
            "SELECT root_hyphenated, root_meaning FROM root_translations "
            "WHERE root_unhyphenated = ?", ('أ' + candidate[1:],)
        ).fetchone()
        if row and row['root_meaning']:
            return (row['root_hyphenated'], row['root_meaning'], 'HAMZA_INITIAL')
        if not direct_hit:
            direct_hit = row

    # ء → أ anywhere
    if 'ء' in candidate:
        row = conn.execute(
            "SELECT root_hyphenated, root_meaning FROM root_translations "
            "WHERE root_unhyphenated = ?", (candidate.replace('ء', 'أ'),)
        ).fetchone()
        if row and row['root_meaning']:
            return (row['root_hyphenated'], row['root_meaning'], 'HAMZA_NORMALIZE')
        if not direct_hit:
            direct_hit = row

    # 2-letter reconstruction
    if len(candidate) == 2:
        for weak in ('و', 'ي'):
            trial = candidate[0] + weak + candidate[1]
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning FROM root_translations "
                "WHERE root_unhyphenated = ?", (trial,)
            ).fetchone()
            if row and row['root_meaning']:
                return (row['root_hyphenated'], row['root_meaning'], 'WEAK_2L_MEDIAL')
            if not direct_hit and row:
                direct_hit = row
            trial2 = weak + candidate
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning FROM root_translations "
                "WHERE root_unhyphenated = ?", (trial2,)
            ).fetchone()
            if row and row['root_meaning']:
                return (row['root_hyphenated'], row['root_meaning'], 'WEAK_2L_INITIAL')
            if not direct_hit and row:
                direct_hit = row
        trial_hamza = 'أ' + candidate
        row = conn.execute(
            "SELECT root_hyphenated, root_meaning FROM root_translations "
            "WHERE root_unhyphenated = ?", (trial_hamza,)
        ).fetchone()
        if row and row['root_meaning']:
            return (row['root_hyphenated'], row['root_meaning'], 'HAMZA_2L_INITIAL')
        if not direct_hit and row:
            direct_hit = row
        # 2-letter FINAL weak reconstruction: سم → سمو/سمي (defective root pattern)
        for weak in ('و', 'ي', 'ه'):
            trial_final = candidate + weak
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning FROM root_translations "
                "WHERE root_unhyphenated = ?", (trial_final,)
            ).fetchone()
            if row and row['root_meaning']:
                return (row['root_hyphenated'], row['root_meaning'], 'WEAK_2L_FINAL')
            if not direct_hit and row:
                direct_hit = row

    # Hollow verb reconstruction (3-letter with medial ا)
    if len(candidate) == 3 and candidate[1] == 'ا':
        for weak in ('و', 'ي'):
            trial = candidate[0] + weak + candidate[2]
            row = conn.execute(
                "SELECT root_hyphenated, root_meaning FROM root_translations "
                "WHERE root_unhyphenated = ?", (trial,)
            ).fetchone()
            if row and row['root_meaning']:
                return (row['root_hyphenated'], row['root_meaning'], 'HOLLOW_VERB')
            if not direct_hit and row:
                direct_hit = row
            if candidate[2] == 'ء':
                trial2 = candidate[0] + weak + 'أ'
                row = conn.execute(
                    "SELECT root_hyphenated, root_meaning FROM root_translations "
                    "WHERE root_unhyphenated = ?", (trial2,)
                ).fetchone()
                if row and row['root_meaning']:
                    return (row['root_hyphenated'], row['root_meaning'], 'HOLLOW_VERB_HAMZA')
                if not direct_hit and row:
                    direct_hit = row

    # Defective verb reconstruction (3-letter with final ا/ء)
    if len(candidate) == 3 and candidate[2] in ('ا', 'ء'):
        for weak in ('و', 'ي', 'ه'):
            trial = candidate[0] + candidate[1] + weak
            for t in set([trial, trial.replace('ء', 'أ')]):
                row = conn.execute(
                    "SELECT root_hyphenated, root_meaning FROM root_translations "
                    "WHERE root_unhyphenated = ?", (t,)
                ).fetchone()
                if row and row['root_meaning']:
                    return (row['root_hyphenated'], row['root_meaning'], 'DEFECTIVE_VERB')
                if not direct_hit and row:
                    direct_hit = row

    if direct_hit:
        return (direct_hit['root_hyphenated'], direct_hit['root_meaning'], 'NO_MEANING_FALLBACK')
    return None


def classify_confidence(level, method):
    """
    Map (candidate_level, lookup_method) to MĪZĀN confidence grade.

    The confidence is determined by BOTH:
    - How much stripping was needed (candidate level)
    - Whether reconstruction was needed inside try_lookup (method)
    """
    # Reconstruction methods always push to MEDIUM_C regardless of candidate level
    RECONSTRUCTION_METHODS = {
        'WEAK_2L_MEDIAL', 'WEAK_2L_INITIAL', 'WEAK_2L_FINAL',
        'HAMZA_2L_INITIAL',
        'HOLLOW_VERB', 'HOLLOW_VERB_HAMZA', 'DEFECTIVE_VERB'
    }

    if method == 'NO_MEANING_FALLBACK':
        return 'LOW'

    if method in RECONSTRUCTION_METHODS:
        return 'MEDIUM_C'

    # Candidate-level based classification
    if level <= 2:
        return 'MEDIUM_A'
    elif level <= 5:
        return 'MEDIUM_B'
    elif level <= 6:
        return 'MEDIUM_C'
    else:  # level 7
        return 'LOW'


def score_word(aa_word, stored_root_hyph, conn):
    """
    Determine the MĪZĀN confidence grade for a word with a known root.
    Returns (grade, match_method_detail) or ('MEDIUM', 'UNKNOWN') if can't determine.
    """
    if not stored_root_hyph:
        return ('UNROOTED', 'NO_ROOT')

    # Convert stored root from hyphenated to unhyphenated, normalize hamza
    stored_root = stored_root_hyph.replace('-', '')
    stored_root_norm = stored_root.replace('أ', 'ء').replace('إ', 'ء').replace('آ', 'اء')

    # Strategy 0: Check known_forms first (same as compiler's Strategy 0)
    bare_norm = prepare_for_root(aa_word)
    kf = conn.execute(
        "SELECT k.root_unhyphenated "
        "FROM quran_known_forms k "
        "WHERE k.bare_form = ?", (bare_norm,)
    ).fetchone()
    if not kf:
        kf = conn.execute(
            "SELECT k.root_unhyphenated "
            "FROM quran_known_forms k "
            "WHERE k.aa_form = ?", (aa_word,)
        ).fetchone()
    if kf:
        kf_norm = kf['root_unhyphenated'].replace('أ', 'ء').replace('إ', 'ء')
        if kf_norm == stored_root_norm:
            return ('HIGH', 'KNOWN_FORM')

    # Generate level-tagged candidates
    tagged = generate_tagged_candidates(aa_word)

    # Try each candidate in order — first match that yields the stored root wins
    for candidate, level in tagged:
        hit = try_lookup_tagged(candidate, conn)
        if hit:
            hit_root = hit[0].replace('-', '') if hit[0] else ''
            hit_root_norm = hit_root.replace('أ', 'ء').replace('إ', 'ء').replace('آ', 'اء')
            if hit_root_norm == stored_root_norm:
                grade = classify_confidence(level, hit[2])
                method_detail = f"L{level}:{hit[2]}"
                return (grade, method_detail)

    # If we get here, the stored root couldn't be reproduced by the cascade
    # This means it was likely assigned by a different method (manual, known_form, etc.)
    return ('MEDIUM', 'LEGACY_UNTRACED')


def rescore(batch_size=500, verbose=False):
    """Re-score all MEDIUM entries with granular confidence grades."""
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Count MEDIUM entries
    total = conn.execute(
        "SELECT COUNT(*) FROM quran_word_roots WHERE confidence = 'MEDIUM'"
    ).fetchone()[0]
    print(f"MĪZĀN RESCORE: {total} MEDIUM entries to classify")
    print("=" * 60)

    # Process in batches
    processed = 0
    grades = {'MEDIUM_A': 0, 'MEDIUM_B': 0, 'MEDIUM_C': 0, 'LOW': 0, 'MEDIUM': 0}

    cursor = conn.execute("""
        SELECT word_id, aa_word, root, confidence
        FROM quran_word_roots
        WHERE confidence = 'MEDIUM'
        ORDER BY word_id
    """)

    updates = []
    for row in cursor:
        word_id = row['word_id']
        aa_word = row['aa_word']
        stored_root = row['root']

        grade, method = score_word(aa_word, stored_root, conn)
        grades[grade] = grades.get(grade, 0) + 1
        updates.append((grade, method, word_id))

        processed += 1
        if processed % 5000 == 0:
            # Batch write
            conn.executemany(
                "UPDATE quran_word_roots SET confidence = ?, match_method = ? WHERE word_id = ?",
                updates
            )
            conn.commit()
            updates = []
            pct = processed / total * 100
            print(f"  [{processed:6d}/{total}] {pct:5.1f}%  A:{grades['MEDIUM_A']:5d} B:{grades['MEDIUM_B']:5d} C:{grades['MEDIUM_C']:5d} LOW:{grades['LOW']:4d} UNT:{grades.get('MEDIUM',0):4d}")

    # Final batch
    if updates:
        conn.executemany(
            "UPDATE quran_word_roots SET confidence = ?, match_method = ? WHERE word_id = ?",
            updates
        )
        conn.commit()

    print(f"\n  COMPLETE: {processed} words re-scored")
    print(f"\n  DISTRIBUTION:")
    for g in ['MEDIUM_A', 'MEDIUM_B', 'MEDIUM_C', 'LOW', 'MEDIUM']:
        if grades.get(g, 0) > 0:
            pct = grades[g] / total * 100
            print(f"    {g:12s} {grades[g]:6d}  ({pct:5.1f}%)")

    conn.close()


def status():
    """Show full confidence distribution."""
    conn = get_db()

    print("=" * 60)
    print("MĪZĀN CONFIDENCE DISTRIBUTION")
    print("=" * 60)

    rows = conn.execute("""
        SELECT confidence, COUNT(*) as cnt
        FROM quran_word_roots
        GROUP BY confidence
        ORDER BY
            CASE confidence
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM_A' THEN 2
                WHEN 'MEDIUM_B' THEN 3
                WHEN 'MEDIUM_C' THEN 4
                WHEN 'MEDIUM' THEN 5
                WHEN 'LOW' THEN 6
                WHEN 'PARTICLE' THEN 7
                WHEN 'UNROOTED' THEN 8
                ELSE 9
            END
    """).fetchall()

    total = sum(r['cnt'] for r in rows)
    rooted = sum(r['cnt'] for r in rows if r['confidence'] not in ('PARTICLE', 'UNROOTED'))

    for r in rows:
        pct = r['cnt'] / total * 100
        bar = '█' * int(pct / 2)
        print(f"  {r['confidence']:12s} {r['cnt']:6d}  ({pct:5.1f}%)  {bar}")

    print(f"\n  TOTAL: {total}")
    print(f"  ROOTED: {rooted} ({rooted/total*100:.1f}%)")
    print(f"  RELIABLE (HIGH+A+B): {sum(r['cnt'] for r in rows if r['confidence'] in ('HIGH','MEDIUM_A','MEDIUM_B'))}")

    # Match method breakdown
    print(f"\n  MATCH METHODS:")
    methods = conn.execute("""
        SELECT match_method, COUNT(*) as cnt
        FROM quran_word_roots
        WHERE match_method IS NOT NULL
        GROUP BY match_method
        ORDER BY cnt DESC
        LIMIT 20
    """).fetchall()
    for m in methods:
        print(f"    {m['match_method']:30s} {m['cnt']:6d}")

    conn.close()


def audit(word):
    """Show detailed scoring trace for a specific word."""
    conn = get_db()

    # Find the word
    rows = conn.execute("""
        SELECT word_id, surah, ayah, aa_word, root, root_meaning,
               confidence, match_method
        FROM quran_word_roots
        WHERE aa_word = ?
        LIMIT 5
    """, (word,)).fetchall()

    if not rows:
        # Try partial match
        rows = conn.execute("""
            SELECT word_id, surah, ayah, aa_word, root, root_meaning,
                   confidence, match_method
            FROM quran_word_roots
            WHERE aa_word LIKE ?
            LIMIT 5
        """, (f'%{word}%',)).fetchall()

    if not rows:
        print(f"NOT FOUND: {word}")
        conn.close()
        return

    for r in rows:
        print(f"\n{'='*60}")
        print(f"WORD:       {r['aa_word']}")
        print(f"LOCATION:   {r['surah']}:{r['ayah']}")
        print(f"ROOT:       {r['root']} ({r['root_meaning'] or 'no meaning'})")
        print(f"CONFIDENCE: {r['confidence']}")
        print(f"METHOD:     {r['match_method'] or 'not scored'}")

        # Show candidate cascade
        tagged = generate_tagged_candidates(r['aa_word'])
        print(f"\n  CANDIDATE CASCADE ({len(tagged)} candidates):")
        stored_root = r['root'].replace('-', '') if r['root'] else ''
        for i, (cand, level) in enumerate(tagged):
            hit = try_lookup_tagged(cand, conn)
            if hit:
                hit_root = hit[0].replace('-', '') if hit[0] else ''
                match_mark = " ← MATCH" if hit_root == stored_root else ""
                grade = classify_confidence(level, hit[2])
                print(f"    L{level:<4} {cand:15s} → {hit[0] or '??':10s} ({hit[2]:20s}) [{grade}]{match_mark}")
            else:
                print(f"    L{level:<4} {cand:15s} → (no match)")
            if i >= 30:
                print(f"    ... ({len(tagged) - 30} more candidates)")
                break

    conn.close()


def verify(sample_size=10):
    """Spot-check accuracy per grade — show random samples."""
    conn = get_db()

    for grade in ['MEDIUM_A', 'MEDIUM_B', 'MEDIUM_C', 'LOW']:
        print(f"\n{'='*60}")
        print(f"GRADE: {grade} (random {sample_size} samples)")
        print(f"{'='*60}")

        rows = conn.execute(f"""
            SELECT aa_word, root, root_meaning, match_method, surah, ayah
            FROM quran_word_roots
            WHERE confidence = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (grade, sample_size)).fetchall()

        for r in rows:
            print(f"  {r['aa_word']:20s} → {r['root']:10s} ({(r['root_meaning'] or '??')[:25]:25s}) [{r['match_method']}] @ {r['surah']}:{r['ayah']}")

    conn.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'rescore':
        verbose = '--verbose' in sys.argv or '-v' in sys.argv
        rescore(verbose=verbose)
    elif cmd == 'status':
        status()
    elif cmd == 'audit' and len(sys.argv) >= 3:
        audit(sys.argv[2])
    elif cmd == 'verify':
        size = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        verify(size)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
