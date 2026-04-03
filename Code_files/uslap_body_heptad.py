#!/usr/bin/env python3
"""
USLaP Body/Health Heptad — Seven-heptad architecture for the body lattice.

All heptads: ∑Surah# = 462 = 7 × الله = سَبْت (SEPTUPLE LOCK per heptad)

Heptad 1 (Body Structure):
  KEY:       Q82 al-Infiṭār    — body_architecture (created, proportioned, balanced)
  KERNEL:    Q96 al-ʿAlaq      — body_creation_stages (creation from clot)
  SEED:      Q86 al-Ṭāriq      — body_skeletal_map (backbone + ribs)
  NARRATIVE: Q22 al-Ḥajj       — body_movement_chains (bow and prostrate)
  COMPILER:  Q91 al-Shams      — body_diagnostics (nafs purification)
  INDEX:     Q75 al-Qiyāmah    — body_cross_refs (bones to fingertips)
  HANDLER:   Q10 Yūnus         — this CLI tool (healing for the breasts)

Heptad 2 (Therapy & Substance):
  KEY:       Q95 al-Tīn        — body_preservation (best of creation)
  KERNEL:    Q57 al-Ḥadīd      — body_chemistry (iron sent down)
  SEED:      Q16 al-Naḥl       — body_substances (bee + 18 substances)
  NARRATIVE: Q35 Fāṭir         — body_colour_therapy (varied hues)
  COMPILER:  Q76 al-Insān      — body_sound_therapy (silver vessels)
  INDEX:     Q105 al-Fīl       — body_extraction_intel (extraction ops)
  HANDLER:   Q78 al-Nabaʾ      — body_technical (great tidings)

Heptad 3 (بِقَدَرٍ — Formula Lattice):
  KEY:       Q87 al-Aʿlā       — formula_ratios (created, proportioned, destined)
  KERNEL:    Q97 al-Qadr        — formula_restoration (Night of Measure)
  SEED:      Q55 al-Raḥmān     — formula_undiscovered (by precise calculation)
  NARRATIVE: Q25 al-Furqān      — formula_scholars (determined precisely)
  COMPILER:  Q77 al-Mursalāt   — formula_concealment (to a known measure)
  INDEX:     Q36 Yā-Sīn        — formula_cross_refs (everything enumerated)
  HANDLER:   Q85 al-Burūj       — CLI tool (Preserved Tablet)

Heptad 4 (شِفَاء — Emotional-Mental Health):
  ∑Abjad = 2422 = 7 × 346
  KEY:       Q94 al-Sharḥ      — nafs_architecture (expand your breast)
  KERNEL:    Q50 Qāf           — qalb_states (closer than jugular vein)
  SEED:      Q114 al-Nās       — emotional_disorders (waswas in breasts)
  NARRATIVE: Q39 al-Zumar      — healing_protocols (despair not of mercy)
  COMPILER:  Q49 al-Ḥujurāt    — social_health (social health diagnostics)
  INDEX:     Q68 al-Qalam      — nafs_cross_refs (great character)
  HANDLER:   Q48 al-Fatḥ       — CLI tool (sakīnah/tranquility)

Heptad 5 (الحَواسّ — Sensory-Perceptual System):
  ∑Abjad = 2219 = 7 × 317
  KEY:       Q17 al-Isrā'      — sensory_architecture (night journey - sensory transcendence)
  KERNEL:    Q41 Fuṣṣilat      — perception_hierarchy (testimony of hearing/sight/skin)
  SEED:      Q46 al-Aḥqāf      — sensory_disorders (hearing the Qur'an - response)
  NARRATIVE: Q67 al-Mulk       — sensory_diagnostics (created hearing/sight/hearts)
  COMPILER:  Q90 al-Balad       — perception_contamination (eyes/tongue/lips)
  INDEX:     Q101 al-Qāriʿah   — sensory_cross_refs (the striking calamity)
  HANDLER:   Q100 al-ʿĀdiyāt  — CLI tool (kinesthetic perception)

Heptad 6 (طَعَام — Nutrition System):
  ∑Abjad = 1911 = 7² × 39 (DOUBLE 7-LOCK)
  KEY:       Q5  al-Māʾidah    — nutrition_architecture (ḥalāl/ḥarām food law)
  KERNEL:    Q80 ʿAbasa         — food_production_cycle (9-stage Q80:24-32)
  SEED:      Q56 al-Wāqiʿah    — agricultural_system (3 questions: crops, water, fire)
  NARRATIVE: Q37 al-Ṣāffāt     — food_contrasts (paradise vs. zaqqūm)
  COMPILER:  Q106 Quraysh       — nutrition_intelligence (food as weapon/provision)
  HANDLER:   Q71 Nūḥ            — CLI tool (rain→gardens→rivers)
  INDEX:     Q107 al-Māʿūn      — nutrition_cross_refs (feeding the poor)

Heptad 7 (حَيَاة وَمَوْت — Lifecycle: Life & Death):
  ∑Abjad = 3059 = 7 × 19 × 23 (7-LOCK + 19-SIGNAL)
  KEY:       Q23 al-Muʾminūn    — lifecycle_architecture (full creation cycle Q23:12-16)
  KERNEL:    Q79 al-Nāziʿāt     — death_mechanism (soul extraction by angels)
  SEED:      Q32 al-Sajdah      — spirit_infusion (rūḥ breathed into clay)
  NARRATIVE: Q84 al-Inshiqāq    — transition_states (sky splits, earth stretched)
  COMPILER:  Q102 al-Takāthur   — mortality_intelligence (graveyard visit)
  HANDLER:   Q53 al-Najm        — CLI tool (star/destiny)
  INDEX:     Q89 al-Fajr        — lifecycle_cross_refs (dawn/soul return)

Usage:
  python3 uslap_body_heptad.py status              # show all heptads + table counts
  python3 uslap_body_heptad.py build KEY            # build Q82 body_architecture
  python3 uslap_body_heptad.py build ALL            # build all H1 surahs in order
  python3 uslap_body_heptad.py search TERM          # search all body tables (H1-H7)
  python3 uslap_body_heptad.py verify               # verify QUF gates across all tables
  python3 uslap_body_heptad.py export               # export full body lattice as JSON
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import json
import os
import sys
import re
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')

# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

def create_body_architecture(cur):
    """KEY — Q82 al-Infiṭār: body architecture framework."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_architecture (
        arch_id TEXT PRIMARY KEY,
        section TEXT NOT NULL,
        component TEXT NOT NULL,
        arabic TEXT,
        function TEXT,
        quranic_ref TEXT,
        clinical_application TEXT,
        model_source TEXT,
        score INTEGER DEFAULT 7,
        status TEXT DEFAULT 'CONFIRMED'
    )''')


def create_body_creation_stages(cur):
    """KERNEL — Q96 al-ʿAlaq: embryological/creation stages."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_creation_stages (
        stage_id TEXT PRIMARY KEY,
        stage_order INTEGER NOT NULL,
        arabic TEXT NOT NULL,
        transliteration TEXT,
        english TEXT NOT NULL,
        quranic_ref TEXT NOT NULL,
        description TEXT,
        body_regions TEXT,
        score INTEGER DEFAULT 7,
        status TEXT DEFAULT 'CONFIRMED'
    )''')


def create_body_skeletal_map(cur):
    """SEED — Q86 al-Ṭāriq: skeletal structure map."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_skeletal_map (
        bone_id TEXT PRIMARY KEY,
        region TEXT NOT NULL,
        arabic TEXT,
        transliteration TEXT,
        english TEXT NOT NULL,
        bone_type TEXT,
        parent_bone TEXT,
        connected_joints TEXT,
        quranic_ref TEXT,
        clinical_notes TEXT,
        score INTEGER DEFAULT 7,
        status TEXT DEFAULT 'CONFIRMED',
        FOREIGN KEY (parent_bone) REFERENCES body_skeletal_map(bone_id)
    )''')


def create_body_movement_chains(cur):
    """NARRATIVE — Q22 al-Ḥajj: kinetic chains for prayer movement."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_movement_chains (
        chain_id TEXT PRIMARY KEY,
        prayer_state TEXT NOT NULL,
        chain_name TEXT NOT NULL,
        arabic TEXT,
        joints_involved TEXT NOT NULL,
        muscle_groups TEXT,
        force_direction TEXT,
        quranic_ref TEXT,
        ibn_sina_ref TEXT,
        clinical_notes TEXT,
        score INTEGER DEFAULT 7,
        status TEXT DEFAULT 'CONFIRMED',
        FOREIGN KEY (prayer_state) REFERENCES prayer_states(state_id)
    )''')


def create_body_diagnostics(cur):
    """COMPILER — Q91 al-Shams: diagnostic protocols."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_diagnostics (
        diag_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        arabic TEXT,
        transliteration TEXT,
        english TEXT NOT NULL,
        protocol TEXT,
        quranic_ref TEXT,
        treatment_hierarchy TEXT,
        contaminated_term TEXT,
        clean_term TEXT,
        score INTEGER DEFAULT 7,
        status TEXT DEFAULT 'CONFIRMED'
    )''')


def create_body_cross_refs(cur):
    """INDEX — Q75 al-Qiyāmah: cross-reference table connecting all body tables."""
    cur.execute('''CREATE TABLE IF NOT EXISTS body_cross_refs (
        xref_id TEXT PRIMARY KEY,
        source_table TEXT NOT NULL,
        source_id TEXT NOT NULL,
        target_table TEXT NOT NULL,
        target_id TEXT NOT NULL,
        relationship TEXT NOT NULL,
        notes TEXT
    )''')


# ═══════════════════════════════════════════════════════════════
# BUILD FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def build_key(cur):
    """Build KEY — Q82 al-Infiṭār: migrate BODY_ARCHITECTURE + RATIO_ARCHITECTURE."""
    create_body_architecture(cur)

    # Check if already populated
    count = cur.execute("SELECT COUNT(*) FROM body_architecture").fetchone()[0]
    if count > 0:
        print(f"  body_architecture already has {count} rows. Skipping migration.")
        return count

    # Migrate from excel_data_consolidated
    rows_ba = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'BODY_ARCHITECTURE'"
    ).fetchall()

    rows_ra = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'RATIO_ARCHITECTURE'"
    ).fetchall()

    arch_id = 0
    current_section = ''

    # Parse BODY_ARCHITECTURE
    for row in rows_ba:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or text.startswith('Model |'):
            continue  # skip bismillah and header
        if text.startswith('SECTION'):
            current_section = text.split(':')[1].strip() if ':' in text else text
            continue

        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 4:
            continue

        arch_id += 1
        aid = f"BA{arch_id:03d}"
        component = parts[1] if len(parts) > 1 else ''
        arabic = parts[2] if len(parts) > 2 else ''
        function = parts[3] if len(parts) > 3 else ''
        qref = parts[4] if len(parts) > 4 else ''
        clinical = parts[5] if len(parts) > 5 else ''

        cur.execute("""INSERT OR IGNORE INTO body_architecture
            (arch_id, section, component, arabic, function, quranic_ref, clinical_application, model_source, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'BODY_ARCHITECTURE', 8, 'CONFIRMED')""",
            (aid, current_section, component, arabic, function, qref, clinical))

    # Parse RATIO_ARCHITECTURE
    current_section = ''
    for row in rows_ra:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or text.startswith('Section |'):
            continue
        if text.startswith('SECTION'):
            current_section = text.split(':')[1].strip() if ':' in text else text
            continue

        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3:
            continue

        arch_id += 1
        aid = f"BA{arch_id:03d}"
        component = parts[1] if len(parts) > 1 else ''
        value_or_arabic = parts[2] if len(parts) > 2 else ''
        desc = parts[3] if len(parts) > 3 else ''
        qref = parts[4] if len(parts) > 4 else ''

        cur.execute("""INSERT OR IGNORE INTO body_architecture
            (arch_id, section, component, arabic, function, quranic_ref, clinical_application, model_source, score, status)
            VALUES (?, ?, ?, ?, ?, ?, NULL, 'RATIO_ARCHITECTURE', 7, 'CONFIRMED')""",
            (aid, current_section, component, value_or_arabic, desc, qref))

    final = cur.execute("SELECT COUNT(*) FROM body_architecture").fetchone()[0]

    # Update heptad meta
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_architecture',
        built_date = ? WHERE surah_role = 'KEY'""", (datetime.now().isoformat(),))

    print(f"  KEY (Q82) COMPLETE: body_architecture = {final} rows")
    return final


def build_kernel(cur):
    """Build KERNEL — Q96 al-ʿAlaq: creation stages from Qur'anic embryology."""
    create_body_creation_stages(cur)

    count = cur.execute("SELECT COUNT(*) FROM body_creation_stages").fetchone()[0]
    if count > 0:
        print(f"  body_creation_stages already has {count} rows. Skipping.")
        return count

    # Qur'anic embryological sequence — direct from Qur'an
    stages = [
        ('CS01', 1, 'تُرَاب', 'turāb', 'Dust/Earth', 'Q22:5, Q30:20, Q35:11',
         'Origin from dust — mineral composition of the body. هُوَ الَّذِي خَلَقَكُم مِّن تُرَابٍ / He created you from dust',
         'ALL'),
        ('CS02', 2, 'نُطْفَة', 'nuṭfah', 'Drop/Sperm-drop', 'Q16:4, Q22:5, Q23:13, Q36:77, Q75:37, Q76:2, Q80:19',
         'Seminal fluid stage. أَلَمْ يَكُ نُطْفَةً مِّن مَّنِيٍّ يُمْنَىٰ / Was he not a drop of fluid emitted?',
         'REPRODUCTIVE'),
        ('CS03', 3, 'عَلَقَة', 'ʿalaqah', 'Clinging clot', 'Q22:5, Q23:14, Q40:67, Q75:38, Q96:2',
         'Clinging/suspended form — implantation. خَلَقَ الْإِنسَانَ مِنْ عَلَقٍ / Created man from a clot',
         'UTERINE_WALL'),
        ('CS04', 4, 'مُضْغَة', 'muḍghah', 'Chewed lump', 'Q22:5, Q23:14',
         'Formed and unformed tissue mass. مُّخَلَّقَةٍ وَغَيْرِ مُخَلَّقَةٍ / formed and unformed',
         'EMBRYONIC_MASS'),
        ('CS05', 5, 'عِظَام', 'ʿiẓām', 'Bones', 'Q23:14, Q75:3',
         'Skeletal formation. فَخَلَقْنَا الْمُضْغَةَ عِظَامًا / We made the lump into bones',
         'SKELETAL'),
        ('CS06', 6, 'لَحْم', 'laḥm', 'Flesh/Muscle', 'Q23:14',
         'Flesh clothing bones. فَكَسَوْنَا الْعِظَامَ لَحْمًا / We clothed the bones with flesh',
         'MUSCULAR, SOFT_TISSUE'),
        ('CS07', 7, 'خَلْقًا آخَرَ', 'khalqan ākhar', 'Another creation', 'Q23:14',
         'Ensoulment — a new creation. ثُمَّ أَنشَأْنَاهُ خَلْقًا آخَرَ / Then We produced it as another creation',
         'ALL — ENSOULED'),
        ('CS08', 8, 'سَمْع', 'samʿ', 'Hearing', 'Q23:78, Q32:9, Q67:23, Q76:2',
         'Hearing faculty — always listed FIRST before sight. وَجَعَلَ لَكُمُ السَّمْعَ وَالْأَبْصَارَ / He made for you hearing and vision',
         'EAR, AUDITORY_NERVE'),
        ('CS09', 9, 'بَصَر', 'baṣar', 'Sight', 'Q23:78, Q32:9, Q67:23, Q76:2',
         'Vision faculty — always listed AFTER hearing. وَالْأَبْصَارَ وَالْأَفْئِدَةَ / and vision and hearts',
         'EYE, OPTIC_NERVE'),
        ('CS10', 10, 'فُؤَاد', 'fuʾād', 'Heart/Inner perception', 'Q23:78, Q32:9, Q67:23, Q76:2',
         'The inner organ of perception — always listed THIRD after hearing and sight. وَالْأَفْئِدَةَ قَلِيلًا مَّا تَشْكُرُونَ / and hearts — little do you give thanks',
         'HEART, COGNITIVE'),
    ]

    # Also migrate QURANIC_HEALTH_VERSES data
    qhv_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'QURANIC_HEALTH_VERSES'"
    ).fetchall()

    stage_id = 10
    for row in qhv_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or '|' not in text:
            continue
        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3 or parts[0].startswith('Verse') or parts[0].startswith('Category'):
            continue

        stage_id += 1
        sid = f"CS{stage_id:02d}"
        qref = parts[0] if len(parts) > 0 else ''
        arabic = parts[1] if len(parts) > 1 else ''
        eng = parts[2] if len(parts) > 2 else ''
        desc = parts[3] if len(parts) > 3 else ''
        regions = parts[4] if len(parts) > 4 else ''

        stages.append((sid, stage_id, arabic, '', eng, qref, desc, regions))

    for s in stages:
        cur.execute("""INSERT OR IGNORE INTO body_creation_stages
            (stage_id, stage_order, arabic, transliteration, english, quranic_ref, description, body_regions, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 8, 'CONFIRMED')""", s)

    final = cur.execute("SELECT COUNT(*) FROM body_creation_stages").fetchone()[0]
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_creation_stages',
        built_date = ? WHERE surah_role = 'KERNEL'""", (datetime.now().isoformat(),))

    print(f"  KERNEL (Q96) COMPLETE: body_creation_stages = {final} rows")
    return final


def build_seed(cur):
    """Build SEED — Q86 al-Ṭāriq: skeletal map from JOINT_NETWORK + body_edges."""
    create_body_skeletal_map(cur)

    count = cur.execute("SELECT COUNT(*) FROM body_skeletal_map").fetchone()[0]
    if count > 0:
        print(f"  body_skeletal_map already has {count} rows. Skipping.")
        return count

    # Migrate JOINT_NETWORK from excel_data_consolidated
    jn_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'JOINT_NETWORK'"
    ).fetchall()

    bone_id = 0
    current_region = ''
    for row in jn_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ'):
            continue
        if text.startswith('SECTION') or text.startswith('REGION'):
            current_region = text.split(':')[1].strip() if ':' in text else text
            continue

        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3:
            continue
        # Skip header rows
        if any(h in parts[0].lower() for h in ['joint', 'node', 'name', 'type']):
            continue

        bone_id += 1
        bid = f"BN{bone_id:03d}"
        name = parts[0] if len(parts) > 0 else ''
        arabic = parts[1] if len(parts) > 1 else ''
        bone_type = parts[2] if len(parts) > 2 else ''
        connected = parts[3] if len(parts) > 3 else ''
        qref = parts[4] if len(parts) > 4 else ''
        notes = parts[5] if len(parts) > 5 else ''

        cur.execute("""INSERT OR IGNORE INTO body_skeletal_map
            (bone_id, region, arabic, transliteration, english, bone_type, parent_bone, connected_joints, quranic_ref, clinical_notes, score, status)
            VALUES (?, ?, ?, NULL, ?, ?, NULL, ?, ?, ?, 7, 'CONFIRMED')""",
            (bid, current_region, arabic, name, bone_type, connected, qref, notes))

    # Also pull bone-type edges from body_edges
    bone_edges = cur.execute(
        "SELECT edge_id, from_node, to_node, name, arabic, side, properties FROM body_edges WHERE edge_type = 'BONE'"
    ).fetchall()

    for be in bone_edges:
        bone_id += 1
        bid = f"BN{bone_id:03d}"
        props = be[6] or ''
        cur.execute("""INSERT OR IGNORE INTO body_skeletal_map
            (bone_id, region, arabic, transliteration, english, bone_type, parent_bone, connected_joints, quranic_ref, clinical_notes, score, status)
            VALUES (?, 'FROM_BODY_EDGES', ?, NULL, ?, 'BONE', NULL, ?, 'Q86:5-7', ?, 7, 'CONFIRMED')""",
            (bid, be[4], be[3], f"{be[1]}→{be[2]}", props))

    final = cur.execute("SELECT COUNT(*) FROM body_skeletal_map").fetchone()[0]
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_skeletal_map',
        built_date = ? WHERE surah_role = 'SEED'""", (datetime.now().isoformat(),))

    print(f"  SEED (Q86) COMPLETE: body_skeletal_map = {final} rows")
    return final


def build_narrative(cur):
    """Build NARRATIVE — Q22 al-Ḥajj: movement chains from prayer_states + body_nodes."""
    create_body_movement_chains(cur)

    count = cur.execute("SELECT COUNT(*) FROM body_movement_chains").fetchone()[0]
    if count > 0:
        print(f"  body_movement_chains already has {count} rows. Skipping.")
        return count

    # Get all prayer states
    states = cur.execute("SELECT state_id, english, fk_angles, muscle_activations, force_lines FROM prayer_states").fetchall()

    chain_id = 0
    for st in states:
        state_id = st[0]
        state_name = st[1] or state_id
        fk_angles = st[2] or '{}'
        muscles = st[3] or '{}'
        force_lines = st[4] or '{}'

        # Primary kinetic chain for this prayer state
        chain_id += 1
        cid = f"MC{chain_id:03d}"

        # Parse joints from fk_angles
        try:
            angles = json.loads(fk_angles) if fk_angles.startswith('{') else {}
        except (json.JSONDecodeError, TypeError):
            angles = {}

        joints = ', '.join(angles.keys()) if angles else 'ALL'

        try:
            muscle_data = json.loads(muscles) if muscles.startswith('{') else {}
        except (json.JSONDecodeError, TypeError):
            muscle_data = {}

        muscle_groups = ', '.join(muscle_data.keys()) if muscle_data else ''

        cur.execute("""INSERT OR IGNORE INTO body_movement_chains
            (chain_id, prayer_state, chain_name, arabic, joints_involved, muscle_groups, force_direction, quranic_ref, ibn_sina_ref, clinical_notes, score, status)
            VALUES (?, ?, ?, NULL, ?, ?, 'gravity→ground', 'Q22:77', NULL, NULL, 7, 'CONFIRMED')""",
            (cid, state_id, f"Primary chain — {state_name}", joints, muscle_groups))

        # Contralateral chain (cross-body)
        chain_id += 1
        cid = f"MC{chain_id:03d}"
        cur.execute("""INSERT OR IGNORE INTO body_movement_chains
            (chain_id, prayer_state, chain_name, arabic, joints_involved, muscle_groups, force_direction, quranic_ref, ibn_sina_ref, clinical_notes, score, status)
            VALUES (?, ?, ?, 'خُطْوَة مُقابِلَة / khuṭwah muqābilah / contralateral step', ?, ?, 'cross-body diagonal', 'Q22:77', 'SC02: The body moves not as two halves but as a weaving', 'Assess opposite side for pain origin', 7, 'CONFIRMED')""",
            (cid, state_id, f"Contralateral chain — {state_name}", joints, muscle_groups))

    final = cur.execute("SELECT COUNT(*) FROM body_movement_chains").fetchone()[0]
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_movement_chains',
        built_date = ? WHERE surah_role = 'NARRATIVE'""", (datetime.now().isoformat(),))

    print(f"  NARRATIVE (Q22) COMPLETE: body_movement_chains = {final} rows")
    return final


def build_compiler(cur):
    """Build COMPILER — Q91 al-Shams: diagnostics from DIAGNOSTIC_PROTOCOLS + MEDICAL_FORMULAS + TREATMENT_HIERARCHY."""
    create_body_diagnostics(cur)

    count = cur.execute("SELECT COUNT(*) FROM body_diagnostics").fetchone()[0]
    if count > 0:
        print(f"  body_diagnostics already has {count} rows. Skipping.")
        return count

    diag_id = 0

    # Migrate DIAGNOSTIC_PROTOCOLS
    dp_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'DIAGNOSTIC_PROTOCOLS'"
    ).fetchall()

    for row in dp_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or '|' not in text:
            continue
        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3:
            continue
        if any(h in parts[0].lower() for h in ['protocol', 'category', 'number']):
            continue

        diag_id += 1
        did = f"DG{diag_id:03d}"
        cat = parts[0] if len(parts) > 0 else ''
        arabic = parts[1] if len(parts) > 1 else ''
        eng = parts[2] if len(parts) > 2 else ''
        protocol = parts[3] if len(parts) > 3 else ''
        qref = parts[4] if len(parts) > 4 else ''

        cur.execute("""INSERT OR IGNORE INTO body_diagnostics
            (diag_id, category, arabic, transliteration, english, protocol, quranic_ref, treatment_hierarchy, contaminated_term, clean_term, score, status)
            VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, NULL, NULL, 7, 'CONFIRMED')""",
            (did, cat, arabic, eng, protocol, qref))

    # Migrate MEDICAL_FORMULAS
    mf_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'MEDICAL_FORMULAS'"
    ).fetchall()

    for row in mf_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or '|' not in text:
            continue
        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3:
            continue
        if any(h in parts[0].lower() for h in ['formula', 'name', 'number']):
            continue

        diag_id += 1
        did = f"DG{diag_id:03d}"
        cur.execute("""INSERT OR IGNORE INTO body_diagnostics
            (diag_id, category, arabic, transliteration, english, protocol, quranic_ref, treatment_hierarchy, contaminated_term, clean_term, score, status)
            VALUES (?, 'FORMULA', ?, NULL, ?, ?, ?, NULL, NULL, NULL, 7, 'CONFIRMED')""",
            (did, parts[1] if len(parts) > 1 else '', parts[0], parts[2] if len(parts) > 2 else '', parts[3] if len(parts) > 3 else ''))

    # Migrate TREATMENT_HIERARCHY
    th_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'TREATMENT_HIERARCHY'"
    ).fetchall()

    for row in th_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or '|' not in text:
            continue
        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 2:
            continue
        if any(h in parts[0].lower() for h in ['level', 'tier', 'hierarchy']):
            continue

        diag_id += 1
        did = f"DG{diag_id:03d}"
        cur.execute("""INSERT OR IGNORE INTO body_diagnostics
            (diag_id, category, arabic, transliteration, english, protocol, quranic_ref, treatment_hierarchy, contaminated_term, clean_term, score, status)
            VALUES (?, 'TREATMENT_HIERARCHY', ?, NULL, ?, ?, ?, ?, NULL, NULL, 7, 'CONFIRMED')""",
            (did, parts[1] if len(parts) > 1 else '', parts[0],
             parts[2] if len(parts) > 2 else '', parts[3] if len(parts) > 3 else '',
             parts[0]))

    # Migrate TERMINOLOGY_RESTORATION
    tr_rows = cur.execute(
        "SELECT row_data FROM excel_data_consolidated WHERE source_sheet = 'TERMINOLOGY_RESTORATION'"
    ).fetchall()

    for row in tr_rows:
        text = row[0]
        if not text or text.startswith('بِسْمِ') or '|' not in text:
            continue
        parts = [p.strip() for p in text.split('|')]
        if len(parts) < 3:
            continue
        if any(h in parts[0].lower() for h in ['contaminated', 'modern', 'western']):
            continue

        diag_id += 1
        did = f"DG{diag_id:03d}"
        contaminated = parts[0] if len(parts) > 0 else ''
        clean = parts[1] if len(parts) > 1 else ''
        arabic = parts[2] if len(parts) > 2 else ''
        notes = parts[3] if len(parts) > 3 else ''

        cur.execute("""INSERT OR IGNORE INTO body_diagnostics
            (diag_id, category, arabic, transliteration, english, protocol, quranic_ref, treatment_hierarchy, contaminated_term, clean_term, score, status)
            VALUES (?, 'TERMINOLOGY_RESTORATION', ?, NULL, ?, ?, 'Q91:9', NULL, ?, ?, 7, 'CONFIRMED')""",
            (did, arabic, f"{contaminated} → {clean}", notes, contaminated, clean))

    final = cur.execute("SELECT COUNT(*) FROM body_diagnostics").fetchone()[0]
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_diagnostics',
        built_date = ? WHERE surah_role = 'COMPILER'""", (datetime.now().isoformat(),))

    print(f"  COMPILER (Q91) COMPLETE: body_diagnostics = {final} rows")
    return final


def build_index(cur):
    """Build INDEX — Q75 al-Qiyāmah: cross-references connecting all body tables."""
    create_body_cross_refs(cur)

    count = cur.execute("SELECT COUNT(*) FROM body_cross_refs").fetchone()[0]
    if count > 0:
        print(f"  body_cross_refs already has {count} rows. Skipping.")
        return count

    xref_id = 0

    # Link body_architecture → body_nodes (via linked_nodes column if populated, else by keyword match)
    arch_rows = cur.execute("SELECT arch_id, component, section FROM body_architecture").fetchall()
    node_rows = cur.execute("SELECT node_id, english FROM body_nodes").fetchall()

    for arch in arch_rows:
        for node in node_rows:
            # Simple keyword overlap check
            arch_words = set((arch[1] or '').lower().split() + (arch[2] or '').lower().split())
            node_words = set((node[1] or '').lower().split())
            if arch_words & node_words and len(arch_words & node_words) > 0:
                xref_id += 1
                xid = f"BX{xref_id:03d}"
                cur.execute("""INSERT OR IGNORE INTO body_cross_refs
                    (xref_id, source_table, source_id, target_table, target_id, relationship, notes)
                    VALUES (?, 'body_architecture', ?, 'body_nodes', ?, 'ARCHITECTURE_TO_NODE', ?)""",
                    (xid, arch[0], node[0], f"{arch[1]} ↔ {node[1]}"))

    # Link body_skeletal_map → body_nodes
    skel_rows = cur.execute("SELECT bone_id, english, connected_joints FROM body_skeletal_map").fetchall()
    for skel in skel_rows:
        for node in node_rows:
            conn = (skel[2] or '').lower()
            if node[0].lower() in conn or (node[1] or '').lower() in (skel[1] or '').lower():
                xref_id += 1
                xid = f"BX{xref_id:03d}"
                cur.execute("""INSERT OR IGNORE INTO body_cross_refs
                    (xref_id, source_table, source_id, target_table, target_id, relationship, notes)
                    VALUES (?, 'body_skeletal_map', ?, 'body_nodes', ?, 'SKELETON_TO_NODE', ?)""",
                    (xid, skel[0], node[0], f"{skel[1]} → {node[1]}"))

    # Link body_movement_chains → prayer_states
    mc_rows = cur.execute("SELECT chain_id, prayer_state FROM body_movement_chains").fetchall()
    for mc in mc_rows:
        xref_id += 1
        xid = f"BX{xref_id:03d}"
        cur.execute("""INSERT OR IGNORE INTO body_cross_refs
            (xref_id, source_table, source_id, target_table, target_id, relationship, notes)
            VALUES (?, 'body_movement_chains', ?, 'prayer_states', ?, 'CHAIN_TO_STATE', NULL)""",
            (xid, mc[0], mc[1]))

    # Link body_creation_stages → body_architecture (by body_regions)
    cs_rows = cur.execute("SELECT stage_id, body_regions, english FROM body_creation_stages").fetchall()
    for cs in cs_rows:
        regions = (cs[1] or '').lower()
        for arch in arch_rows:
            section_lower = (arch[2] or '').lower()
            if any(r in section_lower for r in regions.split(', ') if r and len(r) > 3):
                xref_id += 1
                xid = f"BX{xref_id:03d}"
                cur.execute("""INSERT OR IGNORE INTO body_cross_refs
                    (xref_id, source_table, source_id, target_table, target_id, relationship, notes)
                    VALUES (?, 'body_creation_stages', ?, 'body_architecture', ?, 'CREATION_TO_ARCHITECTURE', ?)""",
                    (xid, cs[0], arch[0], f"{cs[2]} → {arch[1]}"))

    final = cur.execute("SELECT COUNT(*) FROM body_cross_refs").fetchone()[0]
    cur.execute("""UPDATE body_heptad_meta SET
        status = 'COMPLETE', tables_built = 'body_cross_refs',
        built_date = ? WHERE surah_role = 'INDEX'""", (datetime.now().isoformat(),))

    print(f"  INDEX (Q75) COMPLETE: body_cross_refs = {final} rows")
    return final


# ═══════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_status():
    """Show heptad status and all table counts."""
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    print("=" * 72)
    print("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    print("BODY/HEALTH LATTICE — STATUS")
    print("All heptads: ∑Surah# = 462 = 7 × الله = سَبْت (per heptad)")
    print("=" * 72)

    # All heptads
    h1 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 1 ORDER BY surah_number").fetchall()
    h2 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 2 ORDER BY surah_number").fetchall()
    h3 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 3 ORDER BY surah_number").fetchall()
    h4 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 4 ORDER BY surah_number").fetchall()
    h5 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 5 ORDER BY surah_number").fetchall()
    h6 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 6 ORDER BY surah_number").fetchall()
    h7 = conn.execute("SELECT * FROM body_heptad_meta WHERE heptad = 7 ORDER BY surah_number").fetchall()

    for label, meta in [("HEPTAD 1 (Body Structure)", h1), ("HEPTAD 2 (Therapy & Substance)", h2), ("HEPTAD 3 (بِقَدَرٍ — Formula Lattice)", h3), ("HEPTAD 4 (شِفَاء — Emotional-Mental Health)", h4), ("HEPTAD 5 (الحَواسّ — Sensory-Perceptual)", h5), ("HEPTAD 6 (طَعَام — Nutrition System)", h6), ("HEPTAD 7 (حَيَاة وَمَوْت — Lifecycle)", h7)]:
        print(f"\n── {label} ──")
        print(f"{'Role':<14} {'Surah':<18} {'#':>4} {'Āyāt':>5} {'Abjad':>6} {'Status':<10} {'Tables Built'}")
        print("-" * 90)
        for m in meta:
            print(f"{m['surah_role']:<14} {m['surah_name_en']:<18} {m['surah_number']:>4} {m['ayat_count']:>5} {m['abjad_value']:>6} {m['status']:<10} {m['tables_built'] or '—'}")

    # Table counts — H1 + H2 + H3 + existing
    tables = [
        # H1
        ('body_heptad_meta', 'Heptad metadata (H1+H2+H3+H4+H5+H6+H7)'),
        ('body_architecture', 'H1 KEY Q82 — Architecture'),
        ('body_creation_stages', 'H1 KERNEL Q96 — Creation'),
        ('body_skeletal_map', 'H1 SEED Q86 — Skeleton'),
        ('body_movement_chains', 'H1 NARRATIVE Q22 — Movement'),
        ('body_diagnostics', 'H1 COMPILER Q91 — Diagnostics'),
        ('body_cross_refs', 'H1 INDEX Q75 — Cross-refs'),
        # H2
        ('body_preservation', 'H2 KEY Q95 — Preservation'),
        ('body_chemistry', 'H2 KERNEL Q57 — Chemistry'),
        ('body_substances', 'H2 SEED Q16 — Substances'),
        ('body_colour_therapy', 'H2 NARRATIVE Q35 — Colour'),
        ('body_sound_therapy', 'H2 COMPILER Q76 — Sound'),
        ('body_extraction_intel', 'H2 INDEX Q105 — Extraction'),
        ('body_technical', 'H2 HANDLER Q78 — Technical'),
        # H3
        ('formula_ratios', 'H3 KEY Q87 — Ratio Architecture'),
        ('formula_restoration', 'H3 KERNEL Q97 — Formula Restoration'),
        ('formula_undiscovered', 'H3 SEED Q55 — Undiscovered'),
        ('formula_scholars', 'H3 NARRATIVE Q25 — Scholars/Audit'),
        ('formula_concealment', 'H3 COMPILER Q77 — Concealment'),
        ('formula_cross_refs', 'H3 INDEX Q36 — Cross-refs'),
        # H4
        ('nafs_architecture', 'H4 KEY Q94 — Nafs Architecture'),
        ('qalb_states', 'H4 KERNEL Q50 — Qalb States'),
        ('emotional_disorders', 'H4 SEED Q114 — Disorders'),
        ('healing_protocols', 'H4 NARRATIVE Q39 — Healing'),
        ('social_health', 'H4 COMPILER Q49 — Social Health'),
        ('nafs_cross_refs', 'H4 INDEX Q68 — Cross-refs'),
        # H5
        ('sensory_architecture', 'H5 KEY Q17 — Sensory Architecture'),
        ('perception_hierarchy', 'H5 KERNEL Q41 — Perception Hierarchy'),
        ('sensory_disorders', 'H5 SEED Q46 — Sensory Disorders'),
        ('sensory_diagnostics', 'H5 NARRATIVE Q67 — Sensory Diagnostics'),
        ('perception_contamination', 'H5 COMPILER Q90 — Perception Contamination'),
        ('sensory_cross_refs', 'H5 INDEX Q101 — Cross-refs'),
        # H6
        ('nutrition_architecture', 'H6 KEY Q5 — Nutrition Architecture'),
        ('food_production_cycle', 'H6 KERNEL Q80 — Food Production Cycle'),
        ('agricultural_system', 'H6 SEED Q56 — Agricultural System'),
        ('food_contrasts', 'H6 NARRATIVE Q37 — Food Contrasts'),
        ('nutrition_intelligence', 'H6 COMPILER Q106 — Nutrition Intelligence'),
        ('nutrition_cross_refs', 'H6 INDEX Q107 — Cross-refs'),
        # H7
        ('lifecycle_architecture', 'H7 KEY Q23 — Lifecycle Architecture'),
        ('death_mechanism', 'H7 KERNEL Q79 — Death Mechanism'),
        ('spirit_infusion', 'H7 SEED Q32 — Spirit Infusion'),
        ('transition_states', 'H7 NARRATIVE Q84 — Transition States'),
        ('mortality_intelligence', 'H7 COMPILER Q102 — Mortality Intelligence'),
        ('lifecycle_cross_refs', 'H7 INDEX Q89 — Cross-refs'),
        # Existing
        ('body_nodes', 'Existing — Joints'),
        ('body_edges', 'Existing — Edges'),
        ('prayer_states', 'Existing — Prayer states'),
        ('prayer_transitions', 'Existing — Transitions'),
        ('pelvis_tissue', 'Existing — Pelvis tissue'),
    ]

    print(f"\n{'Table':<30} {'Rows':>6} {'Description'}")
    print("-" * 76)
    total = 0
    for tname, desc in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
        except Exception:
            cnt = 0
        total += cnt
        marker = " ✓" if cnt > 0 else ""
        print(f"{tname:<30} {cnt:>6} {desc}{marker}")

    print("-" * 76)
    print(f"{'TOTAL':<30} {total:>6}")

    # Completion
    all_meta = list(h1) + list(h2) + list(h3) + list(h4) + list(h5) + list(h6) + list(h7)
    complete = sum(1 for m in all_meta if m['status'] == 'COMPLETE')
    total_surahs = len(all_meta)
    print(f"\nHeptad completion: {complete}/{total_surahs} surahs ({complete*100//total_surahs if total_surahs else 0}%)")

    conn.close()


def cmd_build(role):
    """Build a specific surah's table(s)."""
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    role = role.upper()

    builders = {
        'KEY': build_key,
        'KERNEL': build_kernel,
        'SEED': build_seed,
        'NARRATIVE': build_narrative,
        'COMPILER': build_compiler,
        'INDEX': build_index,
    }

    if role == 'ALL':
        print("Building ALL surahs in order...\n")
        for r in ['KEY', 'KERNEL', 'SEED', 'NARRATIVE', 'COMPILER', 'INDEX']:
            builders[r](cur)
        # Mark HANDLER as complete (this tool IS the handler)
        cur.execute("""UPDATE body_heptad_meta SET
            status = 'COMPLETE', tables_built = 'uslap_body_heptad.py',
            built_date = ? WHERE surah_role = 'HANDLER'""", (datetime.now().isoformat(),))
        print(f"\n  HANDLER (Q10) COMPLETE: this CLI tool = شِفَاءٌ لِّمَا فِي الصُّدُورِ")
        conn.commit()
        conn.close()
        print("\n  ALL 7 SURAHS COMPLETE.")
        cmd_status()
        return
    elif role == 'HANDLER':
        cur.execute("""UPDATE body_heptad_meta SET
            status = 'COMPLETE', tables_built = 'uslap_body_heptad.py',
            built_date = ? WHERE surah_role = 'HANDLER'""", (datetime.now().isoformat(),))
        conn.commit()
        print(f"  HANDLER (Q10) COMPLETE: this CLI tool = شِفَاءٌ لِّمَا فِي الصُّدُورِ")
        conn.close()
        return
    elif role not in builders:
        print(f"Unknown role: {role}. Use: KEY, KERNEL, SEED, NARRATIVE, COMPILER, INDEX, HANDLER, ALL")
        conn.close()
        return

    builders[role](cur)
    conn.commit()
    conn.close()


def cmd_search(term):
    """Search all body tables for a term."""
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    term_like = f"%{term}%"
    found = 0

    tables_cols = [
        # H1
        ('body_architecture', ['arch_id', 'section', 'component', 'arabic', 'function', 'quranic_ref']),
        ('body_creation_stages', ['stage_id', 'arabic', 'english', 'quranic_ref', 'description']),
        ('body_skeletal_map', ['bone_id', 'region', 'arabic', 'english', 'quranic_ref']),
        ('body_movement_chains', ['chain_id', 'prayer_state', 'chain_name', 'joints_involved']),
        ('body_diagnostics', ['diag_id', 'category', 'arabic', 'english', 'contaminated_term', 'clean_term']),
        ('body_cross_refs', ['xref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # H2
        ('body_preservation', ['pres_id', 'concept', 'arabic', 'health_application', 'quranic_ref']),
        ('body_chemistry', ['chem_id', 'category', 'arabic', 'domain', 'health_impact', 'quranic_ref']),
        ('body_substances', ['sub_id', 'category', 'arabic', 'scientific_meaning', 'rejected_term', 'quranic_ref']),
        ('body_colour_therapy', ['colour_id', 'colour_name', 'arabic', 'medical_application', 'quranic_ref']),
        ('body_sound_therapy', ['sound_id', 'category', 'instrument', 'arabic', 'therapeutic_application', 'quranic_ref']),
        ('body_extraction_intel', ['extract_id', 'sector', 'metric', 'notes', 'quranic_ref']),
        ('body_technical', ['tech_id', 'category', 'item', 'details', 'quranic_ref']),
        # H3
        ('formula_ratios', ['ratio_id', 'category', 'content', 'divine_fraction', 'western_constant', 'quranic_ref']),
        ('formula_restoration', ['formula_id', 'domain', 'contaminated_formula', 'restored_formula_en', 'quranic_root', 'asb_scholar']),
        ('formula_undiscovered', ['undiscovered_id', 'category', 'domain', 'formula_en', 'quranic_root', 'description']),
        ('formula_scholars', ['scholar_id', 'category', 'term_or_scholar', 'arabic', 'root_letters', 'description']),
        ('formula_concealment', ['conceal_id', 'category', 'content', 'period', 'detection_pattern']),
        ('formula_cross_refs', ['fxref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # H4
        ('nafs_architecture', ['nafs_id', 'arabic', 'transliteration', 'english', 'root_letters', 'quranic_ref']),
        ('qalb_states', ['state_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('emotional_disorders', ['disorder_id', 'category', 'arabic', 'transliteration', 'english', 'western_equivalent']),
        ('healing_protocols', ['protocol_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('social_health', ['social_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('nafs_cross_refs', ['nxref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # H5
        ('sensory_architecture', ['sense_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('perception_hierarchy', ['hierarchy_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('sensory_disorders', ['disorder_id', 'category', 'arabic', 'transliteration', 'english', 'western_equivalent']),
        ('sensory_diagnostics', ['diag_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('perception_contamination', ['contam_id', 'category', 'arabic', 'transliteration', 'english', 'modern_mechanism']),
        ('sensory_cross_refs', ['sxref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # H6
        ('nutrition_architecture', ['nutr_id', 'category', 'arabic', 'english', 'ruling', 'quranic_ref']),
        ('food_production_cycle', ['cycle_id', 'category', 'arabic', 'english', 'scientific_process', 'quranic_ref']),
        ('agricultural_system', ['agri_id', 'category', 'arabic', 'english', 'divine_vs_human', 'quranic_ref']),
        ('food_contrasts', ['contrast_id', 'category', 'arabic', 'english', 'nutritional_status', 'quranic_ref']),
        ('nutrition_intelligence', ['intel_id', 'category', 'arabic', 'english', 'mechanism', 'quranic_ref']),
        ('nutrition_cross_refs', ['nxref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # H7
        ('lifecycle_architecture', ['life_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('death_mechanism', ['death_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('spirit_infusion', ['spirit_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('transition_states', ['trans_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('mortality_intelligence', ['mort_id', 'category', 'arabic', 'transliteration', 'english', 'quranic_ref']),
        ('lifecycle_cross_refs', ['lxref_id', 'source_table', 'source_id', 'target_table', 'target_id', 'relationship']),
        # Existing
        ('body_nodes', ['node_id', 'arabic', 'english', 'quranic_ref']),
        ('prayer_states', ['state_id', 'arabic', 'english']),
    ]

    print(f"Searching body lattice for: {term}\n")

    for tname, cols in tables_cols:
        try:
            conditions = " OR ".join(f"LOWER({c}) LIKE LOWER(?)" for c in cols)
            params = [term_like] * len(cols)
            rows = conn.execute(f"SELECT * FROM [{tname}] WHERE {conditions}", params).fetchall()
            if rows:
                print(f"  [{tname}] — {len(rows)} match(es):")
                for r in rows:
                    pk = r[0]
                    # Show first few meaningful columns
                    details = ' | '.join(str(r[c]) for c in cols[1:min(4, len(cols))] if r[c])
                    print(f"    {pk}: {details}")
                found += len(rows)
        except Exception:
            pass

    if found == 0:
        print("  No matches found in body lattice.")
    else:
        print(f"\n  Total: {found} matches across body lattice.")

    conn.close()


def cmd_verify():
    """Verify all body tables pass integrity + QUF checks."""
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    issues = []

    print("=" * 72)
    print("BODY LATTICE — QUF VERIFICATION")
    print("Q = Qur'anic attestation (2-tier: Q-DIRECT / Q-DERIVED)")
    print("U = Universal applicability (PASS / CONDITIONAL / N/A)")
    print("F = Falsifiable prediction (PASS / STRUCTURAL / PENDING)")
    print("=" * 72)

    # ── TABLE INTEGRITY ──
    print("\n── TABLE INTEGRITY ──")
    h1_tables = ['body_architecture', 'body_creation_stages', 'body_skeletal_map',
                 'body_movement_chains', 'body_diagnostics', 'body_cross_refs']
    h2_tables = ['body_preservation', 'body_chemistry', 'body_substances',
                 'body_colour_therapy', 'body_sound_therapy', 'body_extraction_intel',
                 'body_technical']
    h3_tables = ['formula_ratios', 'formula_restoration', 'formula_undiscovered',
                 'formula_scholars', 'formula_concealment', 'formula_cross_refs']
    h4_tables = ['nafs_architecture', 'qalb_states', 'emotional_disorders',
                 'healing_protocols', 'social_health', 'nafs_cross_refs']
    h5_tables = ['sensory_architecture', 'perception_hierarchy', 'sensory_disorders',
                 'sensory_diagnostics', 'perception_contamination', 'sensory_cross_refs']
    h6_tables = ['nutrition_architecture', 'food_production_cycle', 'agricultural_system',
                 'food_contrasts', 'nutrition_intelligence', 'nutrition_cross_refs']
    h7_tables = ['lifecycle_architecture', 'death_mechanism', 'spirit_infusion',
                 'transition_states', 'mortality_intelligence', 'lifecycle_cross_refs']
    all_tables = h1_tables + h2_tables + h3_tables + h4_tables + h5_tables + h6_tables + h7_tables

    for label, tlist in [("H1", h1_tables), ("H2", h2_tables), ("H3", h3_tables), ("H4", h4_tables), ("H5", h5_tables), ("H6", h6_tables), ("H7", h7_tables)]:
        for t in tlist:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
                if cnt == 0:
                    issues.append(f"EMPTY: {t}")
                else:
                    print(f"  {label} {t}: {cnt} rows")
            except Exception as e:
                issues.append(f"MISSING: {t} — {e}")

    # Heptad meta completeness
    meta = conn.execute("SELECT surah_role, heptad, status FROM body_heptad_meta").fetchall()
    for m in meta:
        if m['status'] != 'COMPLETE':
            issues.append(f"INCOMPLETE: H{m['heptad']} {m['surah_role']} = {m['status']}")

    # ── Q-GATE ──
    print("\n── Q-GATE (Qur'anic Attestation) ──")
    # H1 QUF tables (body_cross_refs has no QUF columns)
    h1_quf = ['body_architecture', 'body_creation_stages', 'body_skeletal_map',
              'body_movement_chains', 'body_diagnostics']
    h2_quf = ['body_preservation', 'body_chemistry', 'body_substances',
              'body_colour_therapy', 'body_sound_therapy', 'body_extraction_intel',
              'body_technical']
    # H3 QUF tables (formula_cross_refs has no QUF columns)
    h3_quf = ['formula_ratios', 'formula_restoration', 'formula_undiscovered',
              'formula_scholars', 'formula_concealment']
    # H4 QUF tables (nafs_cross_refs has no QUF columns)
    h4_quf = ['nafs_architecture', 'qalb_states', 'emotional_disorders',
              'healing_protocols', 'social_health']
    # H5 QUF tables (sensory_cross_refs has no QUF columns)
    h5_quf = ['sensory_architecture', 'perception_hierarchy', 'sensory_disorders',
              'sensory_diagnostics', 'perception_contamination']
    # H6 QUF tables (nutrition_cross_refs has no QUF columns)
    h6_quf = ['nutrition_architecture', 'food_production_cycle', 'agricultural_system',
              'food_contrasts', 'nutrition_intelligence']
    # H7 QUF tables (lifecycle_cross_refs has no QUF columns)
    h7_quf = ['lifecycle_architecture', 'death_mechanism', 'spirit_infusion',
              'transition_states', 'mortality_intelligence']
    quf_tables = h1_quf + h2_quf + h3_quf + h4_quf + h5_quf + h6_quf + h7_quf

    total_q = {'Q-DIRECT': 0, 'Q-DERIVED': 0, None: 0}
    for t in quf_tables:
        try:
            rows = conn.execute(f"SELECT q_gate, COUNT(*) as cnt FROM [{t}] GROUP BY q_gate").fetchall()
            parts = {r['q_gate']: r['cnt'] for r in rows}
            direct = parts.get('Q-DIRECT', 0)
            derived = parts.get('Q-DERIVED', 0)
            null = parts.get(None, 0)
            total = direct + derived + null
            total_q['Q-DIRECT'] += direct
            total_q['Q-DERIVED'] += derived
            total_q[None] += null
            pct = (direct + derived) * 100 // total if total > 0 else 0
            print(f"  {t:<30} DIRECT:{direct:>3}  DERIVED:{derived:>3}  NULL:{null:>3}  ({pct}% gated)")
            if null > 0:
                issues.append(f"Q-GATE NULL: {t} has {null} rows with no Q-gate")
        except Exception:
            pass

    grand_total = sum(total_q.values())
    gated = total_q['Q-DIRECT'] + total_q['Q-DERIVED']
    print(f"  {'TOTAL':<30} DIRECT:{total_q['Q-DIRECT']:>3}  DERIVED:{total_q['Q-DERIVED']:>3}  NULL:{total_q[None]:>3}  ({gated*100//grand_total if grand_total else 0}% gated)")

    # ── U-GATE ──
    print("\n── U-GATE (Universal Applicability) ──")
    total_u = {'PASS': 0, 'CONDITIONAL': 0, 'N/A': 0, None: 0}
    for t in quf_tables:
        try:
            rows = conn.execute(f"SELECT u_gate, COUNT(*) as cnt FROM [{t}] GROUP BY u_gate").fetchall()
            parts = {r['u_gate']: r['cnt'] for r in rows}
            p = parts.get('PASS', 0)
            c = parts.get('CONDITIONAL', 0)
            na = parts.get('N/A', 0)
            null = parts.get(None, 0)
            total_u['PASS'] += p
            total_u['CONDITIONAL'] += c
            total_u['N/A'] += na
            total_u[None] += null
            print(f"  {t:<30} PASS:{p:>3}  COND:{c:>3}  N/A:{na:>3}  NULL:{null:>3}")
            if null > 0:
                issues.append(f"U-GATE NULL: {t} has {null} rows with no U-gate")
        except Exception:
            pass

    print(f"  {'TOTAL':<30} PASS:{total_u['PASS']:>3}  COND:{total_u['CONDITIONAL']:>3}  N/A:{total_u['N/A']:>3}  NULL:{total_u[None]:>3}")

    # ── F-GATE ──
    print("\n── F-GATE (Falsifiable Prediction) ──")
    total_f = {'PASS': 0, 'STRUCTURAL': 0, 'PENDING': 0, None: 0}
    for t in quf_tables:
        try:
            rows = conn.execute(f"""SELECT
                CASE WHEN f_gate LIKE 'PASS%' THEN 'PASS' ELSE COALESCE(f_gate, 'NULL') END as fg,
                COUNT(*) as cnt FROM [{t}] GROUP BY fg""").fetchall()
            parts = {r['fg']: r['cnt'] for r in rows}
            p = parts.get('PASS', 0)
            s = parts.get('STRUCTURAL', 0)
            pend = parts.get('PENDING', 0)
            null = parts.get('NULL', 0)
            total_f['PASS'] += p
            total_f['STRUCTURAL'] += s
            total_f['PENDING'] += pend
            total_f[None] += null
            print(f"  {t:<30} PASS:{p:>3}  STRUCT:{s:>3}  PENDING:{pend:>3}  NULL:{null:>3}")
            if pend > 0:
                issues.append(f"F-GATE PENDING: {t} has {pend} rows needing falsifiable predictions")
        except Exception:
            pass

    print(f"  {'TOTAL':<30} PASS:{total_f['PASS']:>3}  STRUCT:{total_f['STRUCTURAL']:>3}  PENDING:{total_f['PENDING']:>3}  NULL:{total_f[None]:>3}")

    # ── COMPOSITE SCORE ──
    print("\n── COMPOSITE QUF SCORE ──")
    all_rows = sum(total_q.values())
    q_pass = total_q['Q-DIRECT'] + total_q['Q-DERIVED']
    u_pass = total_u['PASS'] + total_u['N/A']  # N/A = structurally universal
    f_pass = total_f['PASS'] + total_f['STRUCTURAL']  # STRUCTURAL = definitional, not a failure

    q_pct = q_pass * 100 // all_rows if all_rows else 0
    u_pct = u_pass * 100 // all_rows if all_rows else 0
    f_pct = f_pass * 100 // all_rows if all_rows else 0

    print(f"  Q: {q_pass}/{all_rows} ({q_pct}%) — {'PASS' if q_pct == 100 else 'GAPS'}")
    print(f"  U: {u_pass}/{all_rows} ({u_pct}%) — {'PASS' if u_pct >= 90 else 'REVIEW'}")
    print(f"  F: {f_pass}/{all_rows} ({f_pct}%) — {'PASS' if f_pct >= 85 else 'PENDING items remain'}")

    composite = (q_pct + u_pct + f_pct) // 3
    print(f"\n  COMPOSITE: {composite}%")

    # ── ISSUES ──
    if issues:
        print(f"\n── ISSUES ({len(issues)}) ──")
        for i in issues:
            print(f"  ! {i}")
    else:
        print("\n  ALL CHECKS PASSED ✓")

    conn.close()


def cmd_export():
    """Export body lattice as JSON."""
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    export = {}
    tables = [
        # H1
        'body_heptad_meta', 'body_architecture', 'body_creation_stages',
        'body_skeletal_map', 'body_movement_chains', 'body_diagnostics',
        'body_cross_refs',
        # H2
        'body_preservation', 'body_chemistry', 'body_substances',
        'body_colour_therapy', 'body_sound_therapy', 'body_extraction_intel',
        'body_technical',
        # H3
        'formula_ratios', 'formula_restoration', 'formula_undiscovered',
        'formula_scholars', 'formula_concealment', 'formula_cross_refs',
        # H4
        'nafs_architecture', 'qalb_states', 'emotional_disorders',
        'healing_protocols', 'social_health', 'nafs_cross_refs',
        # H5
        'sensory_architecture', 'perception_hierarchy', 'sensory_disorders',
        'sensory_diagnostics', 'perception_contamination', 'sensory_cross_refs',
        # H6
        'nutrition_architecture', 'food_production_cycle', 'agricultural_system',
        'food_contrasts', 'nutrition_intelligence', 'nutrition_cross_refs',
        # H7
        'lifecycle_architecture', 'death_mechanism', 'spirit_infusion',
        'transition_states', 'mortality_intelligence', 'lifecycle_cross_refs',
        # Existing
        'body_nodes', 'body_edges', 'prayer_states',
    ]

    for t in tables:
        try:
            rows = conn.execute(f"SELECT * FROM [{t}]").fetchall()
            export[t] = [dict(r) for r in rows]
        except Exception:
            export[t] = []

    conn.close()

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'body_lattice_export.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in export.values())
    print(f"Exported {total} rows across {len(export)} tables → {out_path}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'status':
        cmd_status()
    elif cmd == 'build' and len(sys.argv) >= 3:
        cmd_build(sys.argv[2])
    elif cmd == 'search' and len(sys.argv) >= 3:
        cmd_search(' '.join(sys.argv[2:]))
    elif cmd == 'verify':
        cmd_verify()
    elif cmd == 'export':
        cmd_export()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
