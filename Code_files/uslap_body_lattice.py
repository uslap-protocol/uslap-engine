#!/usr/bin/env python3
"""
USLaP Body Lattice — builds the digital body using the same architecture as the linguistic lattice.

Tables:
  body_nodes        = joints/anatomical points (like a1_entries)
  body_edges        = bones/ligaments/muscles/nerves/force_lines (like term_edges)
  prayer_states     = complete position snapshots (like entry rows with all dimensions)
  prayer_transitions = cascaded movement between states (like the narrative/chronology)

Usage:
  python3 uslap_body_lattice.py build     # create tables + populate
  python3 uslap_body_lattice.py status    # show counts
  python3 uslap_body_lattice.py state ID  # show one prayer state in detail
  python3 uslap_body_lattice.py export    # export body lattice as JSON for the animation
"""

import sqlite3, json, os, sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')


# ═══════════════════════════════════════════════════════════════
# SCHEMA
# ═══════════════════════════════════════════════════════════════

def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS body_nodes (
        node_id TEXT PRIMARY KEY,
        arabic TEXT,
        transliteration TEXT,
        english TEXT,
        node_type TEXT,
        fk_chain TEXT,
        fk_segment TEXT,
        parent_node TEXT,
        bone_length_mm REAL,
        bone_length_px INTEGER,
        neutral_angle REAL,
        min_angle REAL,
        max_angle REAL,
        quranic_ref TEXT,
        notes TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS body_edges (
        edge_id TEXT PRIMARY KEY,
        from_node TEXT,
        to_node TEXT,
        edge_type TEXT,
        name TEXT,
        arabic TEXT,
        side TEXT,
        properties TEXT,
        FOREIGN KEY (from_node) REFERENCES body_nodes(node_id),
        FOREIGN KEY (to_node) REFERENCES body_nodes(node_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS prayer_states (
        state_id TEXT PRIMARY KEY,
        arabic TEXT,
        transliteration TEXT,
        english TEXT,
        root_letters TEXT,
        quranic_tokens INTEGER,
        fk_angles TEXT,
        ligament_states TEXT,
        muscle_activations TEXT,
        eye_data TEXT,
        force_lines TEXT,
        ibn_sina_spine TEXT,
        joint_angles_display TEXT,
        validation_rules TEXT,
        stage_number INTEGER
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS prayer_transitions (
        trans_id TEXT PRIMARY KEY,
        from_state TEXT,
        to_state TEXT,
        cascade_delays TEXT,
        duration_sec REAL,
        description TEXT,
        FOREIGN KEY (from_state) REFERENCES prayer_states(state_id),
        FOREIGN KEY (to_state) REFERENCES prayer_states(state_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS pelvis_tissue (
        tissue_id TEXT PRIMARY KEY,
        tissue_type TEXT,
        name TEXT,
        arabic TEXT,
        side TEXT,
        origin_ref TEXT,
        insertion_ref TEXT,
        color TEXT,
        width REAL,
        deep INTEGER,
        state_per_pose TEXT,
        notes TEXT
    )''')


# ═══════════════════════════════════════════════════════════════
# NODE DATA — joints as lattice nodes
# Each node: (id, arabic, translit, english, type, fk_chain, fk_segment,
#             parent, bone_mm, bone_px, neutral_angle, min, max, quran_ref, notes)
# ═══════════════════════════════════════════════════════════════

NODES = [
    # Main FK chain: toe → ankle → knee → hip → midSpine → shoulder → head
    ('J01','إِصْبَع القَدَم','iṣbaʿ al-qadam','Toe','joint','main','—',
     None, 0, 0, None, None, None, None, 'FK chain root — ground contact in sujud + qiyam'),

    ('J02','كَعْب','kaʿb','Ankle','joint','main','foot',
     'J01', 250, 45, 270, 240, 350, 'Q5:6',
     'Wudu verse: وَأَرْجُلَكُمْ إِلَى الْكَعْبَيْنِ — wash feet to the ankles'),

    ('J03','رُكْبَة','rukbah','Knee','joint','main','shin',
     'J02', 430, 125, 0, -10, 160, None,
     'From ر-ك-ب (to ride/mount). Ground contact in sujud'),

    ('J04','وَرِك','warik','Hip','joint','main','thigh',
     'J03', 430, 125, 0, -30, 140, None,
     'Primary pivot for ruku. Deepest flexion in sujud'),

    ('J05','فَقَار','faqār','Mid-Spine','joint','main','lBack',
     'J04', 250, 65, 0, -15, 120, None,
     'Lumbar region. 5 vertebrae. Ibn Sina distributed flexion point'),

    ('J06','كَتِف','katif','Shoulder','joint','main','uBack',
     'J05', 250, 65, 0, -10, 140, None,
     'Thoracic endpoint. Arm chain branches here'),

    ('J07','رَأْس','raʾs','Head','joint','main','neck',
     'J06', 200, 50, 5, -30, 170, 'Q19:4',
     'قَالَ رَبِّ إِنِّي وَهَنَ الْعَظْمُ مِنِّي وَاشْتَعَلَ الرَّأْسُ شَيْبًا — Forehead contact in sujud'),

    # Arm FK chain: shoulder → elbow → wrist
    ('J08','مِرْفَق','mirfaq','Elbow','joint','arm','uArm',
     'J06', 300, 80, 170, 0, 270, 'Q5:6',
     'Wudu verse: وَأَيْدِيَكُمْ إِلَى الْمَرَافِقِ — wash hands to the elbows'),

    ('J09','مِعْصَم','miʿṣam','Wrist','joint','arm','fArm',
     'J08', 250, 90, 50, -30, 270, None,
     'Palm contact in sujud. Tashahhud index finger pointing. Length includes hand to fingertip'),

    # Additional anatomical nodes (not in FK chain but important for edges)
    ('J10','جَبْهَة','jabhah','Forehead','contact','—','—',
     'J07', 0, 0, None, None, None, 'Q9:35',
     'يَوْمَ يُحْمَىٰ عَلَيْهَا — sujud contact, mark of the believers (Q48:29)'),

    ('J11','أَنْف','anf','Nose','contact','—','—',
     'J07', 0, 0, None, None, None, 'Q5:45',
     'Sujud contact — forehead AND nose on ground'),

    ('J12','كَفّ','kaff','Palm','contact','—','—',
     'J09', 0, 0, None, None, None, None,
     'Sujud contact — palms flat on ground. Tashahhud on thighs'),

    ('J13','عَقِب','ʿaqib','Heel','contact','—','—',
     'J02', 0, 0, None, None, None, None,
     'Juloos — sitting on left heel'),

    ('J14','ظَهْر','ẓahr','Back (full)','region','—','—',
     None, 0, 0, None, None, None, 'Q94:3',
     'الَّذِي أَنقَضَ ظَهْرَكَ — the spine as a complete unit'),

    ('J15','صَدْر','ṣadr','Chest','region','—','—',
     None, 0, 0, None, None, None, 'Q94:1',
     'أَلَمْ نَشْرَحْ لَكَ صَدْرَكَ — chest expansion during qiyam breathing'),

    ('J16','عَيْن','ʿayn','Eye','organ','—','—',
     'J07', 0, 0, None, None, None, 'Q5:45',
     'Complete exercise system: convergence (sujud), lateral sweep (tasleem)'),
]


# ═══════════════════════════════════════════════════════════════
# EDGE DATA — connections between nodes (typed by dimension)
# ═══════════════════════════════════════════════════════════════

EDGES = [
    # === BONE edges (structural skeleton) ===
    ('B01','J01','J02','BONE','Foot (metatarsals)','عَظْم القَدَم',None,None),
    ('B02','J02','J03','BONE','Shin (tibia/fibula)','ظُنْبُوب',None,None),
    ('B03','J03','J04','BONE','Thigh (femur)','فَخِذ',None,None),
    ('B04','J04','J05','BONE','Lower Back (lumbar spine)','فَقَرَات قَطَنِيَّة',None,None),
    ('B05','J05','J06','BONE','Upper Back (thoracic spine)','فَقَرَات صَدْرِيَّة',None,None),
    ('B06','J06','J07','BONE','Neck (cervical spine)','فَقَرَات عُنُقِيَّة',None,None),
    ('B07','J06','J08','BONE','Upper Arm (humerus)','عَضُد',None,None),
    ('B08','J08','J09','BONE','Forearm (radius/ulna)','سَاعِد',None,None),

    # === LIGAMENT edges (17 ligaments from existing file) ===
    ('L01','J03','J04','LIGAMENT','Hamstrings','أَوتار المَأبِض','back',None),
    ('L02','J04','J06','LIGAMENT','Supraspinous Lig.','رِبَاط فَوْق الشَّوْكِيّ','back',None),
    ('L03','J04','J05','LIGAMENT','Interspinous Lig.','رِبَاط بَيْن الشَّوْكِيّ','back',None),
    ('L04','J04','J06','LIGAMENT','Post. Longitudinal Lig.','رِبَاط طُولِيّ خَلْفِيّ','back',None),
    ('L05','J05','J06','LIGAMENT','Ligamentum Flavum','رِبَاط أَصْفَر','back',None),
    ('L06','J03','J03','LIGAMENT','ACL','رِبَاط صَلِيبِيّ أَمَامِيّ','joint',None),
    ('L07','J03','J03','LIGAMENT','PCL','رِبَاط صَلِيبِيّ خَلْفِيّ','joint',None),
    ('L08','J03','J03','LIGAMENT','MCL (Knee)','رِبَاط جَانِبِيّ إِنْسِيّ','joint',None),
    ('L09','J02','J02','LIGAMENT','Ankle (ATFL)','رِبَاط كَاحِلِيّ','joint',None),
    ('L10','J04','J04','LIGAMENT','Iliofemoral (Hip)','رِبَاط حَرْقَفِيّ فَخِذِيّ','joint',None),
    ('L11','J06','J06','LIGAMENT','Glenohumeral (Shoulder)','رِبَاط كَتِفِيّ','joint',None),
    ('L12','J09','J09','LIGAMENT','Wrist Dorsal','رِبَاط مِعْصَمِيّ','joint',None),
    ('L13','J06','J07','LIGAMENT','Cervical / Alar Lig.','رِبَاط عُنُقِيّ','back',None),
    ('L14','J03','J04','LIGAMENT','Quadriceps','عَضَلَة رُبَاعِيَّة','front',None),
    ('L15','J04','J06','LIGAMENT','Erector Spinae','عَضَلَة نَاصِبَة الصُّلْب','front',None),
    ('L16','J04','J04','LIGAMENT','Gluteus Maximus','عَضَلَة أَلْوِيَّة','joint',None),
    ('L17','J04','J04','LIGAMENT','Hip External Rotators','دَوَّارَات خَارِجِيَّة','joint',None),

    # === MUSCLE edges (10 muscle groups) ===
    ('M01','J04','J06','MUSCLE','Erector Spinae','عَضَلَة نَاصِبَة الصُّلْب','back',
     '{"role":"spinal extension","ibn_sina":"maintains flat back in ruku"}'),
    ('M02','J03','J04','MUSCLE','Quadriceps','عَضَلَة رُبَاعِيَّة','front',
     '{"role":"knee extension","ibn_sina":"standing stability"}'),
    ('M03','J03','J04','MUSCLE','Hamstrings','أَوتار المَأبِض','back',
     '{"role":"knee flexion + hip extension","ibn_sina":"controls descent in ruku"}'),
    ('M04','J04','J04','MUSCLE','Gluteus Maximus','عَضَلَة أَلْوِيَّة','back',
     '{"role":"hip extension","ibn_sina":"rising from ruku + sujud"}'),
    ('M05','J06','J08','MUSCLE','Deltoid','عَضَلَة دَالِيَّة','front',
     '{"role":"shoulder movement","ibn_sina":"arm placement in sujud"}'),
    ('M06','J04','J06','MUSCLE','Rectus Abdominis','عَضَلَة مُسْتَقِيمَة بَطْنِيَّة','front',
     '{"role":"trunk flexion","ibn_sina":"core stabilization in all positions"}'),
    ('M07','J06','J07','MUSCLE','Neck Flexors','عَضَلَات عُنُقِيَّة','front',
     '{"role":"head positioning","ibn_sina":"bilateral — cervical control"}'),
    ('M08','J05','J06','MUSCLE','Intercostal (expander)','عَضَلَات وَرْبِيَّة','front',
     '{"role":"rib expansion during inhalation","ibn_sina":"breathing cycle"}'),
    ('M09','J05','J06','MUSCLE','Intercostal (compressor)','عَضَلَات وَرْبِيَّة','front',
     '{"role":"rib compression during exhalation","ibn_sina":"breathing cycle"}'),
    ('M10','J02','J03','MUSCLE','Gastrocnemius','عَضَلَة السَّاق','back',
     '{"role":"plantarflexion","ibn_sina":"balance in qiyam, dorsiflexion control in sujud"}'),

    # === FORCE LINE edges (4 myofascial chains) ===
    ('F01','J07','J02','FORCE_LINE','Dorsal Axial','خَطّ ظَهْرِيّ','back',
     '{"color":"#4488ff","path":"head→shoulder→spine→hip→knee→ankle","role":"conductor — posterior chain"}'),
    ('F02','J06','J09','FORCE_LINE','Ventral Upper','خَطّ بَطْنِيّ عُلْوِيّ','front',
     '{"color":"#ff5555","path":"shoulder→elbow→wrist","role":"curl line — anterior upper"}'),
    ('F03','J04','J01','FORCE_LINE','Ventral Lower','خَطّ بَطْنِيّ سُفْلِيّ','front',
     '{"color":"#44cc88","path":"hip→knee→ankle→toe","role":"step line — anterior lower"}'),
    ('F04','J07','J04','FORCE_LINE','Spiral','خَطّ لَوْلَبِيّ','cross',
     '{"color":"#d4af37","path":"head→opposite hip (cross-body)","role":"rotation — tasleem"}'),
]


# ═══════════════════════════════════════════════════════════════
# PRAYER STATE DATA — each position as a complete lattice entry
# ═══════════════════════════════════════════════════════════════

STATES = {
    'QIYAM': {
        'arabic':'قِيَام','translit':'Qiyām','english':'Standing',
        'root':'ق-و-م','tokens':660,'stage':1,
        'fk': {'foot':270,'shin':0,'thigh':0,'lBack':0,'uBack':0,'neck':5,'uArm':170,'fArm':50,'rX':0.55,'headTurn':0,'finger':'fist'},
        'ligaments': {
            'hamstrings':'rest','supraspinous':'rest','interspinous':'rest',
            'postLong':'rest','ligFlavum':'rest','acl':'rest','pcl':'rest',
            'mcl':'rest','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'rest','wristDorsal':'rest','cervical':'rest',
            'quadriceps':'rest','erectorSpinae':'rest','gluteus':'rest','hipRotators':'rest',
        },
        'muscles': {
            'Erector Spinae':0.3,'Quadriceps':0.2,'Hamstrings':0.1,'Gluteus':0.1,
            'Deltoid':0.1,'Rectus Abdominis':0.1,'Neck Flexors':0.1,
            'Intercostal (exp)':0.4,'Intercostal (comp)':0.3,'Gastrocnemius':0.2,
        },
        'eye': {'gazeAngle':-45,'convergence':0.3,'lateralAngle':0,
                'label':'Place of Prostration','arabic':'نَظَرٌ إِلَى مَوْضِعِ السُّجُود',
                'muscle':'Inferior rectus'},
        'force': {'dorsal':0.3,'ventral_upper':0.1,'ventral_lower':0.1,'spiral':0.0},
        'spine': {'lumbar':0,'thoracic':0,'cervical':0,'atlantoaxial':0,'note':'Erect — all neutral'},
        'angles': {'Hip':'180° (neutral)','Knee':'180° (ext)','Spine':'0° (erect)',
                   'Neck':'5° flex','Ankle':'90°','Shoulder':'0° (adducted)'},
        'validation': {'feet_on_ground':True,'back_erect':True,'gaze_at_sujud_spot':True},
    },
    'RUKU': {
        'arabic':'رُكُوع','translit':'Rukūʿ','english':'Bowing',
        'root':'ر-ك-ع','tokens':13,'stage':2,
        'fk': {'foot':270,'shin':0,'thigh':0,'lBack':88,'uBack':90,'neck':88,'uArm':220,'fArm':230,'rX':0.35,'headTurn':0,'finger':'open'},
        'ligaments': {
            'hamstrings':'stretch','supraspinous':'stretch','interspinous':'stretch',
            'postLong':'stretch','ligFlavum':'stretch','acl':'rest','pcl':'rest',
            'mcl':'rest','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'rest','wristDorsal':'rest','cervical':'rest',
            'quadriceps':'engage','erectorSpinae':'engage','gluteus':'rest','hipRotators':'rest',
        },
        'muscles': {
            'Erector Spinae':0.8,'Quadriceps':0.4,'Hamstrings':0.6,'Gluteus':0.7,
            'Deltoid':0.3,'Rectus Abdominis':0.2,'Neck Flexors':0.6,
            'Intercostal (exp)':0.3,'Intercostal (comp)':0.5,'Gastrocnemius':0.3,
        },
        'eye': {'gazeAngle':-80,'convergence':0.6,'lateralAngle':0,
                'label':'Place of Prostration','arabic':'نَظَرٌ إِلَى مَوْضِعِ السُّجُود',
                'muscle':'Inferior rectus (strong)'},
        'force': {'dorsal':0.9,'ventral_upper':0.2,'ventral_lower':0.7,'spiral':0.1},
        'spine': {'lumbar':20,'thoracic':15,'cervical':10,'atlantoaxial':15,'note':'Sequential engagement — flat back'},
        'angles': {'Hip':'90° flex','Knee':'180° (ext)','Spine':'0° (FLAT)',
                   'Neck':'Neutral (in-line)','Ankle':'90°','Shoulder':'90° flex'},
        'validation': {'legs_straight':True,'back_flat':True,'hands_on_knees':True,'gaze_at_sujud_spot':True},
    },
    'SUJUD': {
        'arabic':'سُجُود','translit':'Sujūd','english':'Prostration',
        'root':'س-ج-د','tokens':92,'stage':5,
        'fk': {'foot':345,'shin':108,'thigh':335,'lBack':115,'uBack':135,'neck':160,'uArm':45,'fArm':180,'rX':0.20,'headTurn':0,'finger':'open'},
        'ligaments': {
            'hamstrings':'stretch','supraspinous':'stretch','interspinous':'stretch',
            'postLong':'stretch','ligFlavum':'stretch','acl':'stretch','pcl':'stretch',
            'mcl':'stretch','ankleATFL':'stretch','iliofemoral':'stretch',
            'glenohumeral':'stretch','wristDorsal':'stretch','cervical':'stretch',
            'quadriceps':'rest','erectorSpinae':'rest','gluteus':'rest','hipRotators':'rest',
        },
        'muscles': {
            'Erector Spinae':0.2,'Quadriceps':0.1,'Hamstrings':0.3,'Gluteus':0.2,
            'Deltoid':0.7,'Rectus Abdominis':0.6,'Neck Flexors':0.8,
            'Intercostal (exp)':0.2,'Intercostal (comp)':0.7,'Gastrocnemius':0.3,
        },
        'eye': {'gazeAngle':-90,'convergence':1.0,'lateralAngle':0,
                'label':'Nose Tip','arabic':'نَظَرٌ إِلَى طَرَفِ الْأَنْفِ',
                'muscle':'Medial rectus (maximum)'},
        'force': {'dorsal':0.2,'ventral_upper':0.8,'ventral_lower':0.8,'spiral':0.6},
        'spine': {'lumbar':30,'thoracic':35,'cervical':25,'atlantoaxial':30,'note':'Max flexion — algorithmic reset'},
        'angles': {'Hip':'>120° flex','Knee':'~160° flex','Spine':'30° flex',
                   'Neck':'45° flex','Ankle':'Dorsiflexed','Shoulder':'120° flex'},
        'validation': {'contacts_7':True,'forehead_on_ground':True,'nose_on_ground':True,
                       'palms_on_ground':True,'knees_on_ground':True,'toes_on_ground':True,
                       'elbows_raised':True,'thighs_off_abdomen':True},
    },
    'JULOOS': {
        'arabic':'جُلُوس','translit':'Julūs','english':'Sitting',
        'root':'ج-ل-س','tokens':3,'stage':6,
        'fk': {'foot':290,'shin':95,'thigh':325,'lBack':358,'uBack':0,'neck':5,'uArm':165,'fArm':120,'rX':0.35,'headTurn':0,'finger':'fist'},
        'ligaments': {
            'hamstrings':'return','supraspinous':'return','interspinous':'return',
            'postLong':'return','ligFlavum':'return','acl':'rest','pcl':'rest',
            'mcl':'stretch','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'return','wristDorsal':'return','cervical':'return',
            'quadriceps':'rest','erectorSpinae':'engage','gluteus':'rest','hipRotators':'stretch',
        },
        'muscles': {
            'Erector Spinae':0.4,'Quadriceps':0.3,'Hamstrings':0.2,'Gluteus':0.8,
            'Deltoid':0.1,'Rectus Abdominis':0.2,'Neck Flexors':0.1,
            'Intercostal (exp)':0.4,'Intercostal (comp)':0.3,'Gastrocnemius':0.6,
        },
        'eye': {'gazeAngle':-20,'convergence':0.4,'lateralAngle':0,
                'label':'Forward / Lap','arabic':'نَظَرٌ إِلَى الْحِجْرِ',
                'muscle':'Inferior rectus (moderate)'},
        'force': {'dorsal':0.4,'ventral_upper':0.2,'ventral_lower':0.9,'spiral':0.1},
        'spine': {'lumbar':10,'thoracic':5,'cervical':0,'atlantoaxial':5,'note':'Near-erect sitting'},
        'angles': {'Hip':'90° flex + rot','Knee':'~155° flex','Spine':'0° (erect)',
                   'Neck':'5° flex','Ankle':'Plantarflexed','Shoulder':'0° (rest)'},
        'validation': {'back_erect':True,'sitting_on_left_foot':True,'right_foot_dorsiflexed':True,
                       'hands_on_thighs':True},
    },
    'TASHAHHUD': {
        'arabic':'تَشَهُّد','translit':'Tashahhud','english':'Testimony (Sitting)',
        'root':'ش-ه-د','tokens':160,'stage':8,
        'fk': {'foot':290,'shin':95,'thigh':325,'lBack':358,'uBack':0,'neck':5,'uArm':165,'fArm':120,'rX':0.35,'headTurn':0,'finger':'index'},
        'ligaments': {
            'hamstrings':'return','supraspinous':'return','interspinous':'return',
            'postLong':'return','ligFlavum':'return','acl':'rest','pcl':'rest',
            'mcl':'stretch','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'return','wristDorsal':'return','cervical':'rest',
            'quadriceps':'rest','erectorSpinae':'rest','gluteus':'rest','hipRotators':'stretch',
        },
        'muscles': {
            'Erector Spinae':0.4,'Quadriceps':0.3,'Hamstrings':0.2,'Gluteus':0.8,
            'Deltoid':0.1,'Rectus Abdominis':0.2,'Neck Flexors':0.1,
            'Intercostal (exp)':0.4,'Intercostal (comp)':0.3,'Gastrocnemius':0.6,
        },
        'eye': {'gazeAngle':-15,'convergence':0.8,'lateralAngle':0,
                'label':'Index Finger','arabic':'نَظَرٌ إِلَى السَّبَّابَةِ',
                'muscle':'Medial rectus + ciliary'},
        'force': {'dorsal':0.4,'ventral_upper':0.2,'ventral_lower':0.9,'spiral':0.1},
        'spine': {'lumbar':10,'thoracic':5,'cervical':0,'atlantoaxial':5,'note':'Sitting — testimony'},
        'angles': {'Hip':'90° flex + rot','Knee':'~155° flex','Spine':'0° (erect)',
                   'Neck':'5° flex','Ankle':'Plantarflexed','Shoulder':'0° (rest)'},
        'validation': {'index_finger_raised':True,'gaze_at_finger':True,'back_erect':True},
    },
    'TASLEEM_R': {
        'arabic':'تَسْلِيم يَمِين','translit':'Taslīm (Right)','english':'Salutation Right',
        'root':'س-ل-م','tokens':157,'stage':9,
        'fk': {'foot':290,'shin':95,'thigh':325,'lBack':358,'uBack':0,'neck':5,'uArm':165,'fArm':120,'rX':0.35,'headTurn':80,'finger':'fist'},
        'ligaments': {
            'hamstrings':'rest','supraspinous':'rest','interspinous':'rest',
            'postLong':'rest','ligFlavum':'rest','acl':'rest','pcl':'rest',
            'mcl':'stretch','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'rest','wristDorsal':'rest','cervical':'stretch',
            'quadriceps':'rest','erectorSpinae':'rest','gluteus':'rest','hipRotators':'stretch',
        },
        'muscles': {
            'Erector Spinae':0.3,'Quadriceps':0.3,'Hamstrings':0.2,'Gluteus':0.7,
            'Deltoid':0.1,'Rectus Abdominis':0.1,'Neck Flexors':0.7,
            'Intercostal (exp)':0.4,'Intercostal (comp)':0.3,'Gastrocnemius':0.5,
        },
        'eye': {'gazeAngle':0,'convergence':0.2,'lateralAngle':80,
                'label':'Right Shoulder','arabic':'السَّلَامُ عَلَيْكُمْ (يَمِين)',
                'muscle':'Lateral rectus R + Medial rectus L'},
        'force': {'dorsal':0.3,'ventral_upper':0.3,'ventral_lower':0.5,'spiral':0.8},
        'spine': {'lumbar':0,'thoracic':0,'cervical':0,'atlantoaxial':0,'note':'Atlas-occipital rotation 60° R'},
        'angles': {'Hip':'90° flex + rot','Knee':'~155° flex','Spine':'0° (erect)',
                   'Neck':'~80° R rotation','Ankle':'Plantarflexed','Shoulder':'0° (rest)'},
        'validation': {'head_turned_right':True,'gaze_at_right_shoulder':True},
    },
    'TASLEEM_L': {
        'arabic':'تَسْلِيم يَسَار','translit':'Taslīm (Left)','english':'Salutation Left',
        'root':'س-ل-م','tokens':157,'stage':11,
        'fk': {'foot':290,'shin':95,'thigh':325,'lBack':358,'uBack':0,'neck':5,'uArm':165,'fArm':120,'rX':0.35,'headTurn':-80,'finger':'fist'},
        'ligaments': {
            'hamstrings':'rest','supraspinous':'rest','interspinous':'rest',
            'postLong':'rest','ligFlavum':'rest','acl':'rest','pcl':'rest',
            'mcl':'stretch','ankleATFL':'rest','iliofemoral':'rest',
            'glenohumeral':'rest','wristDorsal':'rest','cervical':'stretch',
            'quadriceps':'rest','erectorSpinae':'rest','gluteus':'rest','hipRotators':'stretch',
        },
        'muscles': {
            'Erector Spinae':0.3,'Quadriceps':0.3,'Hamstrings':0.2,'Gluteus':0.7,
            'Deltoid':0.1,'Rectus Abdominis':0.1,'Neck Flexors':0.7,
            'Intercostal (exp)':0.4,'Intercostal (comp)':0.3,'Gastrocnemius':0.5,
        },
        'eye': {'gazeAngle':0,'convergence':0.2,'lateralAngle':-80,
                'label':'Left Shoulder','arabic':'السَّلَامُ عَلَيْكُمْ (يَسَار)',
                'muscle':'Lateral rectus L + Medial rectus R'},
        'force': {'dorsal':0.3,'ventral_upper':0.3,'ventral_lower':0.5,'spiral':0.8},
        'spine': {'lumbar':0,'thoracic':0,'cervical':0,'atlantoaxial':0,'note':'Atlas-occipital rotation 60° L'},
        'angles': {'Hip':'90° flex + rot','Knee':'~155° flex','Spine':'0° (erect)',
                   'Neck':'~80° L rotation','Ankle':'Plantarflexed','Shoulder':'0° (rest)'},
        'validation': {'head_turned_left':True,'gaze_at_left_shoulder':True},
    },
    'GOING_DOWN': {
        'arabic':'اِنْتِقَال','translit':'Intiqāl','english':'Going Down (Transition)',
        'root':'ن-ق-ل','tokens':0,'stage':4,
        'fk': {'foot':280,'shin':30,'thigh':350,'lBack':40,'uBack':55,'neck':50,'uArm':130,'fArm':150,'rX':0.32,'headTurn':0,'finger':'open'},
        'ligaments': {
            'hamstrings':'stretch','supraspinous':'stretch','interspinous':'stretch',
            'postLong':'stretch','ligFlavum':'stretch','acl':'stretch','pcl':'stretch',
            'mcl':'stretch','ankleATFL':'stretch','iliofemoral':'stretch',
            'glenohumeral':'stretch','wristDorsal':'stretch','cervical':'stretch',
            'quadriceps':'engage','erectorSpinae':'engage','gluteus':'engage','hipRotators':'rest',
        },
        'muscles': {
            'Erector Spinae':0.5,'Quadriceps':0.7,'Hamstrings':0.5,'Gluteus':0.6,
            'Deltoid':0.4,'Rectus Abdominis':0.5,'Neck Flexors':0.4,
            'Intercostal (exp)':0.3,'Intercostal (comp)':0.5,'Gastrocnemius':0.5,
        },
        'eye': {'gazeAngle':-70,'convergence':0.6,'lateralAngle':0,
                'label':'Transitioning Down','arabic':'الِانْتِقَال',
                'muscle':'Inferior rectus + medial rectus'},
        'force': {'dorsal':0.5,'ventral_upper':0.5,'ventral_lower':0.5,'spiral':0.3},
        'spine': {'lumbar':15,'thoracic':20,'cervical':15,'atlantoaxial':20,'note':'All segments engaged'},
        'angles': {'Hip':'120° flex','Knee':'90° flex','Spine':'20° flex',
                   'Neck':'15° flex','Ankle':'75° dorsiflex','Shoulder':'45° flex'},
        'validation': {'controlled_descent':True},
    },
}


# ═══════════════════════════════════════════════════════════════
# TRANSITION DATA — cascaded movement between states
# ═══════════════════════════════════════════════════════════════

TRANSITIONS = [
    ('T01','QIYAM','RUKU',
     {'foot':0,'shin':0,'thigh':0,'lBack':0,'uBack':0.10,'neck':0.15,'uArm':0.05,'fArm':0.18},
     2.0,'Hip leads, spine follows, arms reach last'),

    ('T02','RUKU','QIYAM',
     {'foot':0,'shin':0,'thigh':0.05,'lBack':0,'uBack':0.12,'neck':0.18,'uArm':0.08,'fArm':0.2},
     2.0,'Spine rises first, head follows'),

    ('T03','QIYAM','GOING_DOWN',
     {'foot':0.1,'shin':0,'thigh':0,'lBack':0.15,'uBack':0.2,'neck':0.25,'uArm':0.1,'fArm':0.2},
     1.5,'Knees bend first, body descends in wave'),

    ('T04','GOING_DOWN','SUJUD',
     {'foot':0.05,'shin':0.05,'thigh':0.1,'lBack':0.1,'uBack':0.15,'neck':0.2,'uArm':0.1,'fArm':0.15},
     1.5,'Hands reach ground, forehead follows last'),

    ('T05','SUJUD','JULOOS',
     {'foot':0.05,'shin':0,'thigh':0,'lBack':0.05,'uBack':0.1,'neck':0.02,'uArm':0.08,'fArm':0.12},
     2.0,'Head rises first (neck leads), trunk follows'),

    ('T06','JULOOS','SUJUD',
     {'foot':0.05,'shin':0,'thigh':0,'lBack':0.08,'uBack':0.12,'neck':0.18,'uArm':0.08,'fArm':0.15},
     2.0,'Direct lean forward from sitting into second sujud — no intermediate ascent'),

    ('T07','JULOOS','TASHAHHUD',
     {'foot':0,'shin':0,'thigh':0,'lBack':0,'uBack':0,'neck':0,'uArm':0,'fArm':0.1},
     1.0,'Minimal transition — same sitting position, finger raises'),

    ('T08','TASHAHHUD','TASLEEM_R',
     {'foot':0,'shin':0,'thigh':0,'lBack':0,'uBack':0,'neck':0,'uArm':0,'fArm':0},
     1.5,'Head turns right — cervical rotation'),

    ('T09','TASLEEM_R','TASLEEM_L',
     {'foot':0,'shin':0,'thigh':0,'lBack':0,'uBack':0,'neck':0,'uArm':0,'fArm':0},
     2.0,'Head sweeps through center to left'),
]


# ═══════════════════════════════════════════════════════════════
# PELVIS TISSUE DATA — ligaments, muscles, skin for 3D pelvis
# Each: (id, type, name, arabic, side, origin_ref, insertion_ref,
#        color, width, deep, state_per_pose, notes)
# ═══════════════════════════════════════════════════════════════

PELVIS_TISSUE = [
    # ===== HIP JOINT LIGAMENTS =====
    ('PLG01','LIGAMENT','Iliofemoral','رِبَاط حَرْقَفِيّ فَخِذِيّ','bilateral',
     '{"b":"iliac","i":4}','{"b":"femur","p":"head"}','#ff6b6b',2.5,0,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'stretch','iftirash':'stretch','tawarruk':'stretch',
                 'goingDown':'stretch','tasleem_r':'rest','tasleem_l':'rest'}),
     'Y-ligament — strongest hip ligament, resists hyperextension'),

    ('PLG02','LIGAMENT','Pubofemoral','رِبَاط عَانِيّ فَخِذِيّ','bilateral',
     '{"b":"iliac","i":11}','{"b":"femur","p":"head"}','#ff5252',2.0,0,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'stretch','tasleem_r':'rest','tasleem_l':'rest'}),
     'Resists abduction and extension'),

    ('PLG03','LIGAMENT','Ischiofemoral','رِبَاط وَرِكِيّ فَخِذِيّ','bilateral',
     '{"b":"iliac","i":9}','{"b":"femur","p":"head"}','#e84040',2.0,1,
     json.dumps({'qiyam':'rest','ruku':'stretch','sujud':'stretch','iftirash':'engage','tawarruk':'engage',
                 'goingDown':'stretch','tasleem_r':'rest','tasleem_l':'rest'}),
     'Posterior — resists internal rotation and flexion'),

    # ===== SI JOINT LIGAMENTS =====
    ('PLG04','LIGAMENT','Anterior Sacroiliac','رِبَاط عَجُزِيّ حَرْقَفِيّ أَمَامِيّ','bilateral',
     '{"b":"sacrum","i_R":2,"i_L":3}','{"b":"iliac","i":12}','#ff8a80',2.0,0,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'Stabilizes SI joint anteriorly'),

    ('PLG05','LIGAMENT','Posterior Sacroiliac','رِبَاط عَجُزِيّ حَرْقَفِيّ خَلْفِيّ','bilateral',
     '{"b":"sacrum","i_R":1,"i_L":0}','{"b":"iliac","i":0}','#ff8a80',2.5,1,
     json.dumps({'qiyam':'rest','ruku':'stretch','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'Strongest SI ligament — resists nutation'),

    # ===== PELVIC FLOOR SUPPORT =====
    ('PLG06','LIGAMENT','Sacrotuberous','رِبَاط عَجُزِيّ حَدَبِيّ','bilateral',
     '{"b":"sacrum","i_R":9,"i_L":8}','{"b":"iliac","i":10}','#ef5350',3.0,0,
     json.dumps({'qiyam':'rest','ruku':'stretch','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'stretch','tasleem_r':'rest','tasleem_l':'rest'}),
     'Long diagonal — sacrum to ischial tuberosity. Supports pelvic floor'),

    ('PLG07','LIGAMENT','Sacrospinous','رِبَاط عَجُزِيّ شَوْكِيّ','bilateral',
     '{"b":"sacrum","i_R":9,"i_L":8}','{"b":"iliac","i":9}','#ef5350',2.0,1,
     json.dumps({'qiyam':'rest','ruku':'stretch','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'Converts greater sciatic notch to foramen'),

    # ===== OTHER LIGAMENTS =====
    ('PLG08','LIGAMENT','Inguinal','رِبَاط أُرْبِيّ','bilateral',
     '{"b":"iliac","i":4}','{"b":"iliac","i":11}','#ff7043',2.0,0,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'rest','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'ASIS to pubic symphysis — floor of inguinal canal'),

    ('PLG09','LIGAMENT','Iliolumbar','رِبَاط حَرْقَفِيّ قَطَنِيّ','bilateral',
     '{"b":"l5","i_R":10,"i_L":9}','{"b":"iliac","i":2}','#ff9e80',2.5,0,
     json.dumps({'qiyam':'rest','ruku':'stretch','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'L5 transverse process to iliac crest'),

    ('PLG10','LIGAMENT','Anterior Longitudinal','رِبَاط طُولِيّ أَمَامِيّ','midline',
     '{"b":"l5","i":3}','{"b":"sacrum","i":3}','#ffab91',2.0,0,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'stretch','iftirash':'rest','tawarruk':'rest',
                 'goingDown':'rest','tasleem_r':'rest','tasleem_l':'rest'}),
     'L5 anterior to sacrum anterior'),

    ('PLG11','LIGAMENT','Obturator Membrane','غِشَاء سَادّ','bilateral',
     '{"b":"iliac","i":5}','{"b":"iliac","i":8}','#ff8a65',1.5,1,
     json.dumps({'qiyam':'rest','ruku':'rest','sujud':'rest','iftirash':'engage','tawarruk':'engage',
                 'goingDown':'rest','tasleem_r':'engage','tasleem_l':'engage'}),
     'Spans obturator foramen — attachment for obturator muscles'),

    # ===== MUSCLES =====
    ('PMS01','MUSCLE','Gluteus Maximus','عَضَلَة أَلْوِيَّة كُبْرَى','bilateral',
     '{"b":"iliac","i":[1],"sacrum_i":[1]}','{"b":"femur","p":"trochanter"}','#ff9800',0,0,
     json.dumps({'qiyam':0.1,'ruku':0.7,'sujud':0.2,'iftirash':0.8,'tawarruk':0.7,
                 'goingDown':0.6,'tasleem_r':0.7,'tasleem_l':0.7}),
     'Largest gluteal — hip extension, external rotation. Rising from ruku/sujud'),

    ('PMS02','MUSCLE','Gluteus Medius','عَضَلَة أَلْوِيَّة وُسْطَى','bilateral',
     '{"b":"iliac","i":[2,3]}','{"b":"femur","p":"trochanter"}','#ffa726',0,0,
     json.dumps({'qiyam':0.2,'ruku':0.3,'sujud':0.4,'iftirash':0.3,'tawarruk':0.4,
                 'goingDown':0.5,'tasleem_r':0.4,'tasleem_l':0.4}),
     'Hip abductor — pelvic stability in single-leg phases'),

    ('PMS03','MUSCLE','Piriformis','عَضَلَة كُمَّثْرِيَّة','bilateral',
     '{"b":"sacrum","i":[6,5]}','{"b":"femur","p":"trochanter"}','#fb8c00',0,1,
     json.dumps({'qiyam':0.1,'ruku':0.2,'sujud':0.6,'iftirash':0.4,'tawarruk':0.5,
                 'goingDown':0.3,'tasleem_r':0.5,'tasleem_l':0.5}),
     'Deep external rotator — critical in sitting positions'),

    ('PMS04','MUSCLE','Psoas Major','عَضَلَة قَطَنِيَّة كُبْرَى','bilateral',
     '{"b":"l5","i":[1,5]}','{"b":"femur","p":"head"}','#f57c00',0,1,
     json.dumps({'qiyam':0.1,'ruku':0.3,'sujud':0.1,'iftirash':0.2,'tawarruk':0.2,
                 'goingDown':0.4,'tasleem_r':0.2,'tasleem_l':0.2}),
     'Hip flexor — L5 to lesser trochanter. Controls descent'),

    ('PMS05','MUSCLE','Obturator Internus','عَضَلَة سَادَّة دَاخِلِيَّة','bilateral',
     '{"b":"iliac","i":[5,8]}','{"b":"femur","p":"trochanter"}','#ef6c00',0,1,
     json.dumps({'qiyam':0.1,'ruku':0.1,'sujud':0.3,'iftirash':0.5,'tawarruk':0.6,
                 'goingDown':0.2,'tasleem_r':0.6,'tasleem_l':0.6}),
     'Deep rotator — active in sitting (external rotation)'),

    ('PMS06','MUSCLE','Pelvic Floor','قَاع الحَوْض','midline',
     '{"b":"iliac","i":[11]}','{"b":"coccyx","i":2}','#e65100',0,1,
     json.dumps({'qiyam':0.2,'ruku':0.3,'sujud':0.5,'iftirash':0.6,'tawarruk':0.7,
                 'goingDown':0.4,'tasleem_r':0.7,'tasleem_l':0.7}),
     'Hammock: pubis to coccyx. Supports pelvic organs'),

    # ===== SKIN =====
    ('PSK01','SKIN','Pelvis Skin Envelope','جِلْد الحَوْض','bilateral',
     '{"verts":8,"upper_ring":"iliac_crest","lower_ring":"ischium"}',
     '{"faces":6}','#deb887',0,0,
     json.dumps({'all_poses':0.08}),
     'Outer envelope — very low opacity, wraps all structures'),

    # ===== NERVES (Arrow / السَّهْم — signal projection, SC02 Bow-String-Arrow) =====
    ('PNR01','NERVE','S1 Root','جَذْر عَصَبِيّ س١','bilateral',
     '{"b":"sacrum","i":1}','{"b":"iliac","i":8}','#00e5ff',1.5,0,
     json.dumps({'all_poses':'active'}),
     'Sacral nerve root S1 — exits posterior foramen'),
    ('PNR02','NERVE','S3 Root','جَذْر عَصَبِيّ س٣','bilateral',
     '{"b":"sacrum","i":5}','{"b":"iliac","i":9}','#00e5ff',1.2,0,
     json.dumps({'all_poses':'active'}),
     'Sacral nerve root S3 — exits mid-sacrum foramen'),
    ('PNR03','NERVE','S5 Root','جَذْر عَصَبِيّ س٥','bilateral',
     '{"b":"sacrum","i":9}','{"b":"iliac","i":10}','#00e5ff',1.0,0,
     json.dumps({'all_poses':'active'}),
     'Sacral nerve root S5 — exits lower sacrum foramen'),
    ('PNR04','NERVE','Sciatic','عِرْق النَّسَا','bilateral',
     '{"b":"iliac","i":9}','{"b":"femur","p":"knee"}','#00e5ff',2.5,0,
     json.dumps({'all_poses':'active'}),
     'Sciatic nerve — largest nerve in body. Ischium → trochanter → knee. Siyah Principle diagnostic'),
    ('PNR05','NERVE','Femoral','عَصَب فَخِذِيّ','bilateral',
     '{"b":"l5","i":2}','{"b":"femur","p":"head"}','#4dd0e1',1.8,0,
     json.dumps({'all_poses':'active'}),
     'Femoral nerve — L5 anterior → ASIS → femoral head'),

    # ===== TEXTILE LINES (Living Textile / النَّسِيج الحَيّ — Q23:14) =====
    ('PTX01','TEXTILE_WARP','Central Warp','الصَّدَا المَرْكَزِيّ','midline',
     '{"b":"l5","i":5}','{"b":"coccyx","i":2}','#c9a84c',1.5,0,
     json.dumps({'all_poses':'load_bearing'}),
     'Warp / الصَّدَا — longitudinal load-bearing (primary postural direction)'),
    ('PTX02','TEXTILE_WARP','Lateral Warp','الصَّدَا الجانِبِيّ','bilateral',
     '{"b":"iliac","i":2}','{"b":"iliac","i":10}','#c9a84c',1.5,0,
     json.dumps({'all_poses':'load_bearing'}),
     'Warp / الصَّدَا — lateral longitudinal line along iliac wing'),
    ('PTX03','TEXTILE_WEFT','Upper Weft','اللُّحْمَة العُلْوِيَّة','midline',
     '{"b":"lIliac","i":0}','{"b":"rIliac","i":0}','#90ee90',1.5,0,
     json.dumps({'all_poses':'cross_stabilise'}),
     'Weft / اللُّحْمَة — transverse cross-stabilisation at SI level'),
    ('PTX04','TEXTILE_WEFT','Lower Weft','اللُّحْمَة السُّفْلِيَّة','midline',
     '{"b":"lIliac","i":10}','{"b":"rIliac","i":10}','#90ee90',1.5,0,
     json.dumps({'all_poses':'cross_stabilise'}),
     'Weft / اللُّحْمَة — transverse cross-stabilisation at ischium level'),
    ('PTX05','TEXTILE_BIAS','Bias R→L','القَطْع المائِل ي←ش','midline',
     '{"b":"rIliac","i":1}','{"b":"lIliac","i":10}','#00ced1',1.5,0,
     json.dumps({'all_poses':'force_distribute'}),
     'Bias / القَطْع المائِل — diagonal 45° force distribution'),
    ('PTX06','TEXTILE_BIAS','Bias L→R','القَطْع المائِل ش←ي','midline',
     '{"b":"lIliac","i":1}','{"b":"rIliac","i":10}','#00ced1',1.5,0,
     json.dumps({'all_poses':'force_distribute'}),
     'Bias / القَطْع المائِل — diagonal 45° force distribution'),

    # ===== FORCE LINES (خُطُوط القُوَّة — SC02 BODY_ARCHITECTURE Section 3) =====
    ('PFL01','FORCE_LINE','Dorsal Axial','المِحْوَر الظَّهْرِي','midline',
     '{"b":"l5","i":8}','{"b":"coccyx","i":2}','#ffffff',3.0,0,
     json.dumps({'all_poses':'stable_conductor'}),
     'Dorsal Axial Warp — the STABLE CONDUCTOR. L5 → sacrum → coccyx → (heel). SC02 Ibn Sīnā'),
    ('PFL02','FORCE_LINE','Ventral Lower','الخَطّ البَطْنِي السُّفْلِي','bilateral',
     '{"b":"iliac","i":4}','{"b":"femur","p":"knee"}','#4ecdc4',2.5,0,
     json.dumps({'all_poses':'step_line'}),
     'Ventral Lower — the "step line". ASIS → hip → knee. Contralateral with Dorsal Axial'),
    ('PFL03','FORCE_LINE','Lateral','خَطّ جانِبِي','bilateral',
     '{"b":"iliac","i":2}','{"b":"femur","p":"latCondyle"}','#f9a825',2.0,0,
     json.dumps({'all_poses':'side_stabilise'}),
     'Lateral Line — iliac crest → trochanter → lateral knee'),
    ('PFL04','FORCE_LINE','Spiral','خَطّ حَلَزُونِي','bilateral',
     '{"b":"iliac","i":1}','{"b":"femur","p":"medCondyle"}','#e040fb',2.0,0,
     json.dumps({'all_poses':'cross_body'}),
     'Spiral Line — cross-body diagonal. Contralateral pattern for gait'),
    ('PFL05','FORCE_LINE','Sagittal Anterior','خَطّ السَّهْمِي الأَمامِي','midline',
     '{"b":"l5","i":3}','{"b":"iliac","i":11}','#ff9e80',2.0,0,
     json.dumps({'all_poses':'front_line'}),
     'Sagittal Anterior — front line. L5 anterior → pubis'),

    # ===== MUQARNAS FASCIA MESH (المُقَرْنَصَات — Q30:30 fiṭrah) =====
    ('PMQ01','MUQARNAS','Iliac Wing Mesh','الشَّبَكَة الرَّابِطَة','bilateral',
     '{"corners":["iliac:1","iliac:3","iliac:9","iliac:11"]}',
     '{"cols":5,"rows":11,"ratio":"11:5"}','#e040fb',0.5,0,
     json.dumps({'all_poses':'load_bearing_network'}),
     'Fascia mesh on iliac wing — 11:5 cell grid. Each cell = muqarnas load-bearing unit. SC02'),
    ('PMQ02','MUQARNAS','Sacrum Mesh','شَبَكَة العَجُز','midline',
     '{"corners":["sacrum:0","sacrum:1","sacrum:8","sacrum:9"]}',
     '{"cols":3,"rows":7}','#e040fb',0.5,0,
     json.dumps({'all_poses':'load_bearing_network'}),
     'Fascia mesh on sacrum — subdivided grid. الشَّبَكَة الرَّابِطَة / al-Shabakah al-Rābiṭah'),
]


# ═══════════════════════════════════════════════════════════════
# BUILD
# ═══════════════════════════════════════════════════════════════

def populate(cur):
    # Nodes
    for n in NODES:
        cur.execute('''INSERT OR REPLACE INTO body_nodes
            (node_id,arabic,transliteration,english,node_type,fk_chain,fk_segment,
             parent_node,bone_length_mm,bone_length_px,neutral_angle,min_angle,max_angle,
             quranic_ref,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', n)

    # Edges
    for e in EDGES:
        cur.execute('''INSERT OR REPLACE INTO body_edges
            (edge_id,from_node,to_node,edge_type,name,arabic,side,properties)
            VALUES (?,?,?,?,?,?,?,?)''', e)

    # Prayer states
    for sid, s in STATES.items():
        cur.execute('''INSERT OR REPLACE INTO prayer_states
            (state_id,arabic,transliteration,english,root_letters,quranic_tokens,
             fk_angles,ligament_states,muscle_activations,eye_data,force_lines,
             ibn_sina_spine,joint_angles_display,validation_rules,stage_number)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (sid, s['arabic'], s['translit'], s['english'], s['root'], s['tokens'],
             json.dumps(s['fk']), json.dumps(s['ligaments']), json.dumps(s['muscles']),
             json.dumps(s['eye']), json.dumps(s['force']), json.dumps(s['spine']),
             json.dumps(s['angles']), json.dumps(s['validation']), s['stage']))

    # Transitions
    for t in TRANSITIONS:
        cur.execute('''INSERT OR REPLACE INTO prayer_transitions
            (trans_id,from_state,to_state,cascade_delays,duration_sec,description)
            VALUES (?,?,?,?,?,?)''',
            (t[0], t[1], t[2], json.dumps(t[3]), t[4], t[5]))

    # Pelvis tissue
    for pt in PELVIS_TISSUE:
        cur.execute('''INSERT OR REPLACE INTO pelvis_tissue
            (tissue_id,tissue_type,name,arabic,side,origin_ref,insertion_ref,
             color,width,deep,state_per_pose,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', pt)


def build():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    create_tables(cur)
    populate(cur)
    conn.commit()
    conn.close()
    print("Body lattice built successfully.")
    status()


def status():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    tables = ['body_nodes','body_edges','prayer_states','prayer_transitions','pelvis_tissue']
    print("\n═══ BODY LATTICE STATUS ═══")
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            c = cur.fetchone()[0]
            print(f"  {t}: {c} rows")
        except:
            print(f"  {t}: NOT FOUND")

    # Edge breakdown
    try:
        cur.execute("SELECT edge_type, COUNT(*) FROM body_edges GROUP BY edge_type ORDER BY edge_type")
        print("\n  Edge breakdown:")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]}")
    except:
        pass

    # Node types
    try:
        cur.execute("SELECT node_type, COUNT(*) FROM body_nodes GROUP BY node_type")
        print("\n  Node types:")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]}")
    except:
        pass

    # Quranic refs
    try:
        cur.execute("SELECT COUNT(*) FROM body_nodes WHERE quranic_ref IS NOT NULL")
        qr = cur.fetchone()[0]
        print(f"\n  Nodes with Qur'anic refs: {qr}")
    except:
        pass

    conn.close()


def show_state(state_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM prayer_states WHERE state_id=?", (state_id.upper(),))
    row = cur.fetchone()
    if not row:
        print(f"State '{state_id}' not found.")
        conn.close()
        return
    cols = [d[0] for d in cur.description]
    print(f"\n═══ {row[0]} — {row[1]} / {row[2]} / {row[3]} ═══")
    print(f"  Root: {row[4]} ({row[5]} Qur'anic tokens)")
    print(f"  Stage #: {row[14]}")
    for i, col in enumerate(cols):
        if col in ('fk_angles','ligament_states','muscle_activations','eye_data',
                    'force_lines','ibn_sina_spine','joint_angles_display','validation_rules'):
            data = json.loads(row[i]) if row[i] else {}
            print(f"\n  {col}:")
            for k, v in data.items():
                print(f"    {k}: {v}")
    conn.close()


def export_json():
    """Export body lattice as JSON for the animation frontend."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    out = {'nodes':[],'edges':[],'states':[],'transitions':[],'pelvis_tissue':[]}

    cur.execute("SELECT * FROM body_nodes")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        out['nodes'].append(dict(zip(cols, row)))

    cur.execute("SELECT * FROM body_edges")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        if d.get('properties'):
            d['properties'] = json.loads(d['properties'])
        out['edges'].append(d)

    cur.execute("SELECT * FROM prayer_states")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        for k in ('fk_angles','ligament_states','muscle_activations','eye_data',
                   'force_lines','ibn_sina_spine','joint_angles_display','validation_rules'):
            if d.get(k):
                d[k] = json.loads(d[k])
        out['states'].append(d)

    cur.execute("SELECT * FROM prayer_transitions")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        if d.get('cascade_delays'):
            d['cascade_delays'] = json.loads(d['cascade_delays'])
        out['transitions'].append(d)

    # Pelvis tissue
    try:
        cur.execute("SELECT * FROM pelvis_tissue")
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            for k in ('state_per_pose',):
                if d.get(k):
                    d[k] = json.loads(d[k])
            out['pelvis_tissue'].append(d)
    except:
        pass  # table may not exist in older DBs

    conn.close()

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'Prayer_Animations', 'body_lattice_data.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Exported to {os.path.abspath(outpath)}")
    print(f"  {len(out['nodes'])} nodes, {len(out['edges'])} edges, "
          f"{len(out['states'])} states, {len(out['transitions'])} transitions")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 uslap_body_lattice.py [build|status|state ID|export]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == 'build':
        build()
    elif cmd == 'status':
        status()
    elif cmd == 'state' and len(sys.argv) > 2:
        show_state(sys.argv[2])
    elif cmd == 'export':
        build()  # ensure latest data
        export_json()
    else:
        print("Unknown command. Use: build | status | state ID | export")
