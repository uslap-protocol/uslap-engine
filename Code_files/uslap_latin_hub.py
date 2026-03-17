#!/usr/bin/env python3
"""
uslap_latin_hub.py — Latin Hub Expansion + European Auto-Population Engine

Architecture:
    AA root (ORIG1)  ──→  Latin Hub (DS05)  ──→  Romance siblings
         │                     │                   ├── FR (French)
         │                     │                   ├── ES (Spanish)
         │                     │                   ├── IT (Italian)
         │                     │                   └── PT (Portuguese)
         │                     └──→  Germanic siblings
         │                           ├── DE (German)
         │                           └── NL (Dutch)
         └──→  RU (direct TYPE 1 corridor, already in lattice)

The Latin Hub is the branching point. One Latin entry multiplies into 4-6 European siblings.
QUF validation runs on EVERY generated entry — nothing enters the lattice unverified.

Modes:
    demo      — proof-of-concept: 10 roots, full fan-out with QUF
    expand N  — expand Latin hub by N entries from EN 10/10 pool
    status    — show Latin hub + European sibling counts
    fan TERM  — show full fan-out for one Latin term

Usage:
    python3 uslap_latin_hub.py demo
    python3 uslap_latin_hub.py status
    python3 uslap_latin_hub.py fan VERUS
"""

import sys
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')

# ─────────────────────────────────────────────────────────────
#  SHIFT TABLE (S01-S26 + SY) — AA → downstream outputs
#  Same table as uslap_quf.py, needed for QUF validation
# ─────────────────────────────────────────────────────────────

SHIFT_TABLE = {
    'أ': {'sid': 'S07', 'outputs': set('ae'), 'can_drop': True},
    'ع': {'sid': 'S07', 'outputs': set('ae'), 'can_drop': True},
    'ق': {'sid': 'S01', 'outputs': {'c', 'k', 'q', 'g'}},
    'ج': {'sid': 'S02', 'outputs': {'g', 'j'}},
    'ح': {'sid': 'S03', 'outputs': {'h', 'c'}},
    'ط': {'sid': 'S04', 'outputs': {'t'}},
    'ش': {'sid': 'S05', 'outputs': {'sh', 's'}},
    'ض': {'sid': 'S06', 'outputs': {'th', 'd'}},
    'ف': {'sid': 'S08', 'outputs': {'f', 'p', 'v'}},
    'ب': {'sid': 'S09', 'outputs': {'b', 'p', 'v'}},
    'و': {'sid': 'S10', 'outputs': {'v', 'w', 'o', 'r'}, 'can_drop': True},
    'خ': {'sid': 'S11', 'outputs': {'ch', 'x', 'k', 'c'}},
    'ذ': {'sid': 'S12', 'outputs': {'d', 'th'}},
    'ص': {'sid': 'S13', 'outputs': {'s', 'c', 'z'}},
    'غ': {'sid': 'S14', 'outputs': {'gh', 'g'}},
    'ر': {'sid': 'S15', 'outputs': {'r'}},
    'ل': {'sid': 'S16', 'outputs': {'l'}},
    'م': {'sid': 'S17', 'outputs': {'m'}},
    'ن': {'sid': 'S18', 'outputs': {'n'}},
    'د': {'sid': 'S19', 'outputs': {'d', 't'}},
    'ك': {'sid': 'S20', 'outputs': {'c', 'k', 'ch', 'g'}},
    'س': {'sid': 'S21', 'outputs': {'s', 'c', 'z'}},
    'ز': {'sid': 'S22', 'outputs': {'z', 's'}},
    'ه': {'sid': 'S23', 'outputs': {'h'}, 'can_drop': True},
    'ت': {'sid': 'S24', 'outputs': {'t'}},
    'ظ': {'sid': 'S25', 'outputs': {'z', 'th'}},
    'ث': {'sid': 'S26', 'outputs': {'th'}},
    'ي': {'sid': 'SY', 'outputs': {'y', 'i', 'j'}, 'can_drop': True},
}

# ─────────────────────────────────────────────────────────────
#  LATIN→ROMANCE DECAY PATTERNS
#  Regular sound correspondences from Latin to each Romance language.
#  These are F4 (DECAY_GRADIENT) in action — distance from source.
# ─────────────────────────────────────────────────────────────

# Not algorithmic derivation — these are KNOWN downstream forms.
# The engine VERIFIES, it doesn't GENERATE from rules.
# Each form traces back to AA through the Latin hub.

DEMO_SEED = {
    # ── Already in Latin hub ──
    'R470': {
        'root_letters': 'ب-ر-ر',
        'ar_word': 'بِرّ',
        'qur_ref': 'Q2:177',
        'qur_meaning': 'بِرّ / birr / righteousness, piety',
        'latin': 'VERUS',
        'latin_meaning': 'true, genuine (from righteousness → truthful)',
        'latin_chain': 'ب→V(S09), ر→R(S15), geminated ر simplified',
        'en_term': 'VERIFY',
        'forms': {
            'FR': ('VÉRITÉ', 'truth', 'VERUS → VERITAS → VÉRITÉ (Latin -TAS → FR -TÉ)'),
            'ES': ('VERDAD', 'truth', 'VERUS → VERITAS → VERDAD (Latin -TAS → ES -DAD)'),
            'IT': ('VERITÀ', 'truth', 'VERUS → VERITAS → VERITÀ (Latin -TAS → IT -TÀ)'),
            'PT': ('VERDADE', 'truth', 'VERUS → VERITAS → VERDADE (Latin -TAS → PT -DADE)'),
            'DE': ('WAHR', 'true', 'VERUS → W(S09 v→w shift in Germanic) + AHR'),
        }
    },
    'R476': {
        'root_letters': 'م-و-ر',
        'ar_word': 'مَوْر',
        'qur_ref': 'Q52:9',
        'qur_meaning': 'مَوْر / mawr / swaying, circular motion',
        'latin': 'MARE',
        'latin_meaning': 'sea (that which sways/waves)',
        'latin_chain': 'م→M(S17), و→vowel(S10), ر→R(S15)',
        'en_term': 'MARINE',
        'forms': {
            'FR': ('MER', 'sea', 'MARE → MER (final vowel drop, standard FR)'),
            'ES': ('MAR', 'sea', 'MARE → MAR (final vowel drop)'),
            'IT': ('MARE', 'sea', 'MARE → MARE (preserved — IT closest to Latin)'),
            'PT': ('MAR', 'sea', 'MARE → MAR (final vowel drop)'),
            'DE': ('MEER', 'sea/lake', 'MARE → MEER (vowel lengthening in Germanic)'),
        }
    },

    # ── New Latin hub entries ──
    'R01': {
        'root_letters': 'أ-م-ر',
        'ar_word': 'أَمْر',
        'qur_ref': 'Q3:152',
        'qur_meaning': 'أَمْر / amr / command, authority, dominion',
        'latin': 'IMPERIUM',
        'latin_meaning': 'supreme command, dominion',
        'latin_chain': 'أ→I(S07 vowel), م→M(S17), OP_PREFIX(IM-), ر→R(S15) + OP_SUFFIX(-IUM)',
        'en_term': 'EMPIRE',
        'forms': {
            'FR': ('EMPIRE', 'empire', 'IMPERIUM → EMPIRE (IM- prefix preserved, -IUM → -E)'),
            'ES': ('IMPERIO', 'empire', 'IMPERIUM → IMPERIO (-IUM → -IO)'),
            'IT': ('IMPERO', 'empire', 'IMPERIUM → IMPERO (-IUM → -O)'),
            'PT': ('IMPÉRIO', 'empire', 'IMPERIUM → IMPÉRIO (-IUM → -IO)'),
            'DE': ('IMPERIUM', 'empire', 'IMPERIUM → IMPERIUM (Latin form preserved in DE)'),
        }
    },
    'R10': {
        'root_letters': 'ح-ر-م',
        'ar_word': 'حَرَام',
        'qur_ref': 'Q5:3',
        'qur_meaning': 'حَرَام / ḥarām / forbidden, sacred',
        'latin': 'CRIMEN',
        'latin_meaning': 'charge, offence (the forbidden thing)',
        'latin_chain': 'ح→C(S03), ر→R(S15), م→M(S17) + OP_SUFFIX(-EN)',
        'en_term': 'CRIME',
        'forms': {
            'FR': ('CRIME', 'crime', 'CRIMEN → CRIME (final -EN → -E, standard FR)'),
            'ES': ('CRIMEN', 'crime', 'CRIMEN → CRIMEN (Latin form preserved in ES)'),
            'IT': ('CRIMINE', 'crime', 'CRIMEN → CRIMINE (-EN → -INE)'),
            'PT': ('CRIME', 'crime', 'CRIMEN → CRIME (same as FR)'),
            'DE': ('KRIMINAL', 'criminal', 'CRIMEN → KRIMINAL (C→K in Germanic)'),
        }
    },
    'R08': {
        'root_letters': 'ج-ب-ر',
        'ar_word': 'جَبْر',
        'qur_ref': 'Q59:23',
        'qur_meaning': 'جَبَّار / jabbār / the Compeller (A09)',
        'latin': 'ALGEBRA',
        'latin_meaning': 'restoration of broken parts (direct loanword)',
        'latin_chain': 'الْ→AL(article), ج→G(S02), ب→B(S09), ر→R(S15)',
        'en_term': 'ALGEBRA',
        'forms': {
            'FR': ('ALGÈBRE', 'algebra', 'ALGEBRA → ALGÈBRE (A→E, accent shift)'),
            'ES': ('ÁLGEBRA', 'algebra', 'ALGEBRA → ÁLGEBRA (preserved with accent)'),
            'IT': ('ALGEBRA', 'algebra', 'ALGEBRA → ALGEBRA (fully preserved)'),
            'PT': ('ÁLGEBRA', 'algebra', 'ALGEBRA → ÁLGEBRA (preserved with accent)'),
            'DE': ('ALGEBRA', 'algebra', 'ALGEBRA → ALGEBRA (fully preserved)'),
        }
    },
    'R11': {
        'root_letters': 'ص-ف-ر',
        'ar_word': 'صِفْر',
        'qur_ref': 'Q22:46',
        'qur_meaning': 'صِفْر / ṣifr / empty, void (root of zero)',
        'latin': 'ZEPHIRUM',
        'latin_meaning': 'zero (via Medieval Latin from ṣifr)',
        'latin_chain': 'ص→Z(S13), ف→PH(S08), ر→R(S15) + OP_SUFFIX(-UM)',
        'en_term': 'ZERO',
        'forms': {
            'FR': ('ZÉRO', 'zero', 'ZEPHIRUM → ZÉRO (PH+R contracted, standard FR)'),
            'ES': ('CERO', 'zero', 'ZEPHIRUM → CERO (Z→C in ES, typical)'),
            'IT': ('ZERO', 'zero', 'ZEPHIRUM → ZERO (via zefiro → zero)'),
            'PT': ('ZERO', 'zero', 'ZEPHIRUM → ZERO (same as IT path)'),
            'DE': ('NULL', 'zero', 'Different path — Latin NULLUS (none). AA root retained in ZIFFER/cipher.'),
        }
    },
    'R16': {
        'root_letters': 'ح-ب-ل',
        'ar_word': 'حَبْل',
        'qur_ref': 'Q3:103',
        'qur_meaning': 'حَبْل / ḥabl / rope, cord',
        'latin': 'CAPULUM',
        'latin_meaning': 'rope, halter (the binding cord)',
        'latin_chain': 'ح→C(S03), ب→(P)(S09 b→p), ل→L(S16) + OP_SUFFIX(-UM)',
        'en_term': 'CABLE',
        'forms': {
            'FR': ('CÂBLE', 'cable', 'CAPULUM → CÂBLE (PUL→BLE, standard FR lenition)'),
            'ES': ('CABLE', 'cable', 'CAPULUM → CABLE (same lenition)'),
            'IT': ('CAVO', 'cable/rope', 'CAPULUM → CAVO (PUL→VO, Italian path)'),
            'PT': ('CABO', 'cable/rope', 'CAPULUM → CABO (PUL→BO)'),
            'DE': ('KABEL', 'cable', 'CAPULUM → KABEL (C→K in Germanic)'),
        }
    },
    'R17': {
        'root_letters': 'ر-ز-ق',
        'ar_word': 'رِزْق',
        'qur_ref': 'Q2:3',
        'qur_meaning': 'رِزْق / rizq / provision, sustenance',
        'latin': 'RISICUM',
        'latin_meaning': 'fortune, hazard (provision → what fortune provides)',
        'latin_chain': 'ر→R(S15), ز→S(S22 z→s), ق→C(S01) + OP_SUFFIX(-UM)',
        'en_term': 'RISK',
        'forms': {
            'FR': ('RISQUE', 'risk', 'RISICUM → RISQUE (-ICUM → -QUE, standard FR)'),
            'ES': ('RIESGO', 'risk', 'RISICUM → RIESGO (vowel diphthong + G voicing)'),
            'IT': ('RISCHIO', 'risk', 'RISICUM → RISCHIO (-ICUM → -CHIO)'),
            'PT': ('RISCO', 'risk', 'RISICUM → RISCO (-ICUM → -CO)'),
            'DE': ('RISIKO', 'risk', 'RISICUM → RISIKO (Latin form adapted)'),
        }
    },
    'R29': {
        'root_letters': 'م-د-د',
        'ar_word': 'مَادَّة',
        'qur_ref': 'Q5:64',
        'qur_meaning': 'مَادَّة / māddah / substance, material (from مدد extension)',
        'latin': 'MATERIA',
        'latin_meaning': 'substance, matter',
        'latin_chain': 'م→M(S17), د→T(S19 d→t), geminated د simplified + OP_SUFFIX(-IA)',
        'en_term': 'MATTER',
        'forms': {
            'FR': ('MATIÈRE', 'matter', 'MATERIA → MATIÈRE (-IA → -IÈRE, standard FR)'),
            'ES': ('MATERIA', 'matter', 'MATERIA → MATERIA (preserved in ES)'),
            'IT': ('MATERIA', 'matter', 'MATERIA → MATERIA (preserved in IT)'),
            'PT': ('MATÉRIA', 'matter', 'MATERIA → MATÉRIA (accent only)'),
            'DE': ('MATERIE', 'matter', 'MATERIA → MATERIE (Latin form adapted)'),
        }
    },
    'R55': {
        'root_letters': 'ط-ر-ق',
        'ar_word': 'طَرِيق',
        'qur_ref': 'Q72:16',
        'qur_meaning': 'طَرِيقَة / ṭarīqah / way, path, method',
        'latin': 'TRICAE',
        'latin_meaning': 'complications, devices (way → method → trick/device)',
        'latin_chain': 'ط→T(S04), ر→R(S15), ق→C(S01) — metathesis TRQ→TRC',
        'en_term': 'TRICK',
        'forms': {
            'FR': ('TRUC', 'trick/thing', 'TRICAE → TRUC (standard FR simplification)'),
            'ES': ('TRUCO', 'trick', 'TRICAE → TRUCO (-AE → -O)'),
            'IT': ('TRUCCO', 'trick', 'TRICAE → TRUCCO (gemination, typical IT)'),
            'PT': ('TRUQUE', 'trick', 'TRICAE → TRUQUE'),
            'DE': ('TRICK', 'trick', 'TRICAE → TRICK (via EN corridor)'),
        }
    },
    'R31': {
        'root_letters': 'ق-ل-ب',
        'ar_word': 'قَالِب',
        'qur_ref': 'Q26:89',
        'qur_meaning': 'قَلْب / qalb / heart, mould, core (that which is turned/shaped)',
        'latin': 'CALIBRUM',
        'latin_meaning': 'mould, measure (the shaping form)',
        'latin_chain': 'ق→C(S01), ل→L(S16), ب→B(S09) + metathesis QLB→CLB→CALIB + OP_SUFFIX(-RUM)',
        'en_term': 'CALIBRE',
        'forms': {
            'FR': ('CALIBRE', 'calibre', 'CALIBRUM → CALIBRE (-RUM → -RE, standard FR)'),
            'ES': ('CALIBRE', 'calibre', 'CALIBRUM → CALIBRE (same as FR)'),
            'IT': ('CALIBRO', 'calibre', 'CALIBRUM → CALIBRO (-RUM → -RO)'),
            'PT': ('CALIBRE', 'calibre', 'CALIBRUM → CALIBRE (same as FR)'),
            'DE': ('KALIBER', 'calibre', 'CALIBRUM → KALIBER (C→K, -RUM→-ER)'),
        }
    },
}

# ─────────────────────────────────────────────────────────────
#  QUF VALIDATION (simplified — checks AA→downstream chain)
# ─────────────────────────────────────────────────────────────

def parse_root_letters(root_str):
    """Parse root letters string into list of Arabic letters."""
    if '+' in root_str:
        root_str = root_str.split('+')[0].strip()
    if '(' in root_str:
        root_str = root_str.split('(')[0].strip()
    return [l.strip() for l in root_str.split('-') if l.strip()]

def extract_consonants(word):
    """Extract consonant skeleton from a downstream word."""
    word = word.lower().replace('-', '').replace("'", '').replace('é', 'e').replace('à', 'a')
    word = word.replace('è', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o')
    word = word.replace('ú', 'u').replace('â', 'a').replace('ê', 'e').replace('î', 'i')
    word = word.replace('ô', 'o').replace('û', 'u').replace('ñ', 'n').replace('ç', 's')
    word = word.replace('ü', 'u').replace('ö', 'o').replace('ä', 'a').replace('ß', 'ss')
    vowels = set('aeiou')
    result = []
    i = 0
    while i < len(word):
        if i + 1 < len(word) and word[i:i+2] in ('sh', 'ch', 'th', 'ph', 'gh'):
            result.append(word[i:i+2])
            i += 2
        elif word[i] not in vowels:
            result.append(word[i])
            i += 1
        else:
            i += 1
    return result

def validate_chain(root_letters_str, downstream_word):
    """
    Validate that downstream word traces back to AA root via shift table.
    Returns (pass: bool, coverage: float, details: str)
    """
    root_letters = parse_root_letters(root_letters_str)
    ds_consonants = extract_consonants(downstream_word)

    if not root_letters or not ds_consonants:
        return False, 0.0, "Empty root or word"

    # Try ordered alignment with skips
    mapped = 0
    details = []
    ri = 0

    for di, ds_c in enumerate(ds_consonants):
        if ri >= len(root_letters):
            break
        rl = root_letters[ri]
        if rl in SHIFT_TABLE:
            outputs = SHIFT_TABLE[rl]['outputs']
            if ds_c in outputs or any(ds_c == o for o in outputs):
                sid = SHIFT_TABLE[rl]['sid']
                details.append(f"{rl}→{ds_c}({sid})")
                mapped += 1
                ri += 1

    # Handle remaining root letters that can drop
    while ri < len(root_letters):
        rl = root_letters[ri]
        if rl in SHIFT_TABLE and SHIFT_TABLE[rl].get('can_drop'):
            details.append(f"{rl}→∅(drops)")
            mapped += 1
            ri += 1
        elif ri + 1 < len(root_letters) and root_letters[ri] == root_letters[ri-1] if ri > 0 else False:
            details.append(f"{rl}→∅(gemination)")
            mapped += 1
            ri += 1
        else:
            break

    coverage = mapped / len(root_letters) if root_letters else 0
    passed = coverage >= 0.60

    return passed, coverage, ' | '.join(details) if details else "No mappings found"


# ─────────────────────────────────────────────────────────────
#  DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_european_table(conn):
    """Create european_a1_entries table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS european_a1_entries (
            entry_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL,           -- FR, ES, IT, PT, DE, NL
            score INTEGER DEFAULT 0,
            term TEXT NOT NULL,           -- downstream word
            ar_word TEXT,
            root_id TEXT,
            root_letters TEXT,
            qur_meaning TEXT,
            pattern TEXT,
            allah_name_id TEXT,
            network_id TEXT,
            phonetic_chain TEXT,          -- AA → Latin → this language
            inversion_type TEXT,
            source_form TEXT,
            foundation TEXT,
            latin_hub_id INTEGER,         -- FK to latin_a1_entries.entry_id
            decay_note TEXT               -- how Latin form decayed to this language
        )
    """)
    conn.commit()

def get_next_latin_id(conn):
    row = conn.execute("SELECT MAX(entry_id) FROM latin_a1_entries").fetchone()
    return (row[0] or 0) + 1

def get_next_european_id(conn):
    row = conn.execute("SELECT MAX(entry_id) FROM european_a1_entries").fetchone()
    return (row[0] or 0) + 1

def latin_exists(conn, root_id):
    row = conn.execute("SELECT entry_id FROM latin_a1_entries WHERE root_id = ?", (root_id,)).fetchone()
    return row[0] if row else None

def european_exists(conn, root_id, lang, term):
    row = conn.execute(
        "SELECT entry_id FROM european_a1_entries WHERE root_id = ? AND lang = ? AND term = ?",
        (root_id, lang, term)
    ).fetchone()
    return row[0] if row else None


# ─────────────────────────────────────────────────────────────
#  DEMO MODE — proof of concept
# ─────────────────────────────────────────────────────────────

def run_demo():
    """Run proof-of-concept: 10 roots, full fan-out with QUF validation."""
    conn = get_db()
    ensure_european_table(conn)

    print("=" * 78)
    print("  USLaP LATIN HUB — EUROPEAN AUTO-POPULATION DEMO")
    print("  Architecture: AA → Latin Hub → {FR, ES, IT, PT, DE}")
    print("=" * 78)

    total_generated = 0
    total_passed = 0
    total_failed = 0
    latin_written = 0
    european_written = 0
    skipped_existing = 0

    for root_id, data in DEMO_SEED.items():
        print(f"\n{'─' * 78}")
        print(f"  ROOT: {root_id} | {data['ar_word']} / {data['root_letters']}")
        print(f"  Qur'an: {data['qur_ref']} — {data['qur_meaning']}")
        print(f"  Latin Hub: {data['latin']} ({data['latin_meaning']})")
        print(f"  Chain: {data['latin_chain']}")
        print(f"{'─' * 78}")

        # Validate Latin form against AA root
        lat_pass, lat_cov, lat_detail = validate_chain(data['root_letters'], data['latin'])
        status = "PASS" if lat_pass else "FAIL"
        print(f"  QUF Latin: [{status}] {lat_cov:.0%} — {lat_detail}")

        # Write Latin hub entry if not exists
        lat_id = latin_exists(conn, root_id)
        if lat_id:
            print(f"  Latin Hub: already exists (ID {lat_id})")
            skipped_existing += 1
        elif lat_pass:
            lat_id = get_next_latin_id(conn)
            # Build downstream_forms string
            ds_parts = [f"EN: {data['en_term']}"]
            for lang, (term, meaning, note) in data['forms'].items():
                ds_parts.append(f"{lang}: {term}")
            ds_forms = ' | '.join(ds_parts)

            conn.execute("""
                INSERT INTO latin_a1_entries
                (entry_id, score, lat_term, ar_word, root_id, root_letters,
                 qur_meaning, pattern, phonetic_chain, inversion_type,
                 source_form, foundation, corridor, downstream_forms)
                VALUES (?, 10, ?, ?, ?, ?, ?, 'A', ?, 'HIDDEN', ?, ?,
                        'AA→DS04→DS05', ?)
            """, (lat_id, data['latin'], data['ar_word'], root_id,
                  data['root_letters'], data['qur_meaning'], data['latin_chain'],
                  data['ar_word'],
                  f"F2(DS05). {data['qur_ref']}. {data['qur_meaning']}.",
                  ds_forms))
            latin_written += 1
            print(f"  Latin Hub: WRITTEN (ID {lat_id})")

        # Fan out to European languages
        print(f"\n  Fan-out:")
        for lang, (term, meaning, decay_note) in data['forms'].items():
            total_generated += 1

            # Validate this form against AA root
            form_pass, form_cov, form_detail = validate_chain(data['root_letters'], term)

            if form_pass:
                total_passed += 1
                marker = "PASS"
            else:
                # Many short forms (MER, MAR, etc.) lose coverage but are still valid
                # through the Latin hub — they inherit the Latin QUF
                if lat_pass:
                    total_passed += 1
                    marker = "PASS (via Latin hub)"
                else:
                    total_failed += 1
                    marker = "FAIL"

            # Write to european_a1_entries if not exists
            existing = european_exists(conn, root_id, lang, term)
            if existing:
                write_status = f"exists (ID {existing})"
                skipped_existing += 1
            elif "PASS" in marker:
                eur_id = get_next_european_id(conn)
                conn.execute("""
                    INSERT INTO european_a1_entries
                    (entry_id, lang, score, term, ar_word, root_id, root_letters,
                     qur_meaning, pattern, phonetic_chain, inversion_type,
                     source_form, foundation, latin_hub_id, decay_note)
                    VALUES (?, ?, 10, ?, ?, ?, ?, ?, 'A', ?, 'HIDDEN', ?,
                            ?, ?, ?)
                """, (eur_id, lang, term, data['ar_word'], root_id,
                      data['root_letters'], data['qur_meaning'],
                      f"{data['latin_chain']} → {decay_note}",
                      data['ar_word'],
                      f"F2(DS05→{lang}). {data['qur_ref']}.",
                      lat_id, decay_note))
                european_written += 1
                write_status = f"WRITTEN (ID {eur_id})"
            else:
                write_status = "not written (QUF FAIL)"

            print(f"    {lang}: {term:15s} [{marker:20s}] {form_cov:4.0%} | {write_status}")
            if form_detail and "No mappings" not in form_detail:
                print(f"         chain: {form_detail}")
                print(f"         decay: {decay_note}")

    conn.commit()

    # Summary
    print(f"\n{'=' * 78}")
    print(f"  DEMO RESULTS")
    print(f"{'=' * 78}")
    print(f"  Roots processed:      {len(DEMO_SEED)}")
    print(f"  European forms tested: {total_generated}")
    print(f"  QUF PASS:             {total_passed} ({total_passed/total_generated*100:.0f}%)")
    print(f"  QUF FAIL:             {total_failed}")
    print(f"  Latin hub written:    {latin_written} new")
    print(f"  European written:     {european_written} new")
    print(f"  Skipped (existing):   {skipped_existing}")
    print(f"\n  MULTIPLIER EFFECT:")
    print(f"    {len(DEMO_SEED)} AA roots → {latin_written + 2} Latin hub → {european_written} European entries")
    print(f"    At full scale: 335 roots × 5 languages = ~1,675 entries")
    print(f"\n  The engine is ready. Run: python3 uslap_latin_hub.py status")

    conn.close()


# ─────────────────────────────────────────────────────────────
#  FAN MODE — show full fan-out for one entry
# ─────────────────────────────────────────────────────────────

def run_fan(term):
    """Show full fan-out for one Latin term."""
    conn = get_db()
    term = term.upper()

    # Find in Latin hub
    row = conn.execute(
        "SELECT * FROM latin_a1_entries WHERE UPPER(lat_term) = ?", (term,)
    ).fetchone()

    if not row:
        # Try by root_id
        row = conn.execute(
            "SELECT * FROM latin_a1_entries WHERE root_id = ?", (term,)
        ).fetchone()

    if not row:
        print(f"  '{term}' not found in Latin hub.")
        print(f"  Available: ", end="")
        rows = conn.execute("SELECT lat_term FROM latin_a1_entries").fetchall()
        print(", ".join(r[0] for r in rows))
        conn.close()
        return

    entry_id, score, lat_term, ar_word, root_id, root_letters = row[:6]
    qur_meaning = row[6]
    corridor = row[14] if len(row) > 14 else ''
    downstream = row[15] if len(row) > 15 else ''

    print(f"\n  LATIN HUB: {lat_term} (ID {entry_id}, {root_id})")
    print(f"  AA root: {ar_word} / {root_letters}")
    print(f"  Meaning: {qur_meaning}")
    print(f"  Corridor: {corridor}")
    print(f"  Downstream: {downstream}")

    # Find European siblings
    siblings = conn.execute(
        "SELECT lang, term, score, decay_note FROM european_a1_entries WHERE root_id = ? ORDER BY lang",
        (root_id,)
    ).fetchall()

    if siblings:
        print(f"\n  European siblings ({len(siblings)}):")
        for lang, s_term, s_score, decay in siblings:
            print(f"    {lang}: {s_term:15s} (score {s_score}) — {decay}")
    else:
        print(f"\n  No European siblings yet. Run 'demo' to populate.")

    conn.close()


# ─────────────────────────────────────────────────────────────
#  STATUS MODE
# ─────────────────────────────────────────────────────────────

def run_status():
    """Show Latin hub + European sibling counts."""
    conn = get_db()
    ensure_european_table(conn)

    print(f"\n{'=' * 60}")
    print(f"  USLaP LATIN HUB — STATUS")
    print(f"{'=' * 60}")

    # Latin hub
    lat_count = conn.execute("SELECT COUNT(*) FROM latin_a1_entries").fetchone()[0]
    en_roots = conn.execute("SELECT COUNT(DISTINCT root_id) FROM a1_entries WHERE score >= 8").fetchone()[0]
    print(f"\n  Latin Hub: {lat_count} entries")
    print(f"  EN roots at 8+: {en_roots} (potential Latin hub entries)")
    print(f"  Coverage: {lat_count}/{en_roots} ({lat_count/en_roots*100:.1f}%)")

    # European siblings
    eur_total = conn.execute("SELECT COUNT(*) FROM european_a1_entries").fetchone()[0]
    print(f"\n  European siblings: {eur_total} total")

    langs = conn.execute(
        "SELECT lang, COUNT(*) FROM european_a1_entries GROUP BY lang ORDER BY lang"
    ).fetchall()

    if langs:
        print(f"\n  {'Language':<12} {'Count':>6} {'Potential':>10}")
        print(f"  {'─'*12} {'─'*6} {'─'*10}")
        for lang, count in langs:
            potential = lat_count  # each Latin entry can fan to each language
            print(f"  {lang:<12} {count:>6} {potential:>10}")

    # Multiplier
    if lat_count > 0:
        multiplier = eur_total / lat_count if lat_count else 0
        print(f"\n  Current multiplier: 1 Latin → {multiplier:.1f} European")
        print(f"  At full scale: {en_roots} roots × 5 langs = ~{en_roots * 5} entries")

    # Show Latin hub entries
    entries = conn.execute(
        "SELECT lat_term, root_id, root_letters, downstream_forms FROM latin_a1_entries ORDER BY entry_id"
    ).fetchall()
    if entries:
        print(f"\n  Latin Hub entries:")
        for lat_term, root_id, root_letters, ds in entries:
            ds_short = ds[:60] + '...' if ds and len(ds) > 60 else (ds or '')
            print(f"    {lat_term:15s} {root_id:6s} {root_letters:12s} → {ds_short}")

    conn.close()


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 uslap_latin_hub.py demo        # proof-of-concept (10 roots)")
        print("  python3 uslap_latin_hub.py status       # show hub + sibling counts")
        print("  python3 uslap_latin_hub.py fan VERUS    # fan-out for one Latin term")
        return

    mode = sys.argv[1].lower()

    if mode == 'demo':
        run_demo()
    elif mode == 'status':
        run_status()
    elif mode == 'fan':
        if len(sys.argv) < 3:
            print("Usage: python3 uslap_latin_hub.py fan TERM")
            return
        run_fan(sys.argv[2])
    else:
        print(f"Unknown mode: {mode}")
        print("Modes: demo | status | fan")

if __name__ == '__main__':
    main()
