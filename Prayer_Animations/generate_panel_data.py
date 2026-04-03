#!/usr/bin/env python3
"""
generate_panel_data.py — Queries uslap_database_v3.db and outputs prayer_panels_data.js
Run: python3 generate_panel_data.py
Output: prayer_panels_data.js (loaded by all prayer animation HTML files)
"""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(__file__), '..', 'Code_files', 'uslap_database_v3.db')
OUT = os.path.join(os.path.dirname(__file__), 'prayer_panels_data.js')

def query(db, sql, params=()):
    cur = db.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def main():
    db = sqlite3.connect(DB)

    # ── NAFS LEVELS (universal) ──
    nafs = query(db, "SELECT nafs_id, arabic, transliteration, english, quranic_ref FROM nafs_architecture WHERE level >= 1 ORDER BY level")
    nafs_colors = ['#ff6b6b','#f9a825','#4ecdc4','#42a5f5','#66bb6a','#ce93d8','#e8e0d0']

    # ── SENSES (universal, Q17:36 order) ──
    senses = query(db, "SELECT sense_id, category, arabic, transliteration, english, quranic_ordering FROM sensory_architecture ORDER BY sense_id")
    sense_icons = {'SN01':'👂','SN02':'👁','SN03':'👅','SN04':'👃','SN05':'🤲','SN06':'💜','SN07':'🧠','SN08':'✨'}
    sense_colors = {'SN01':'#66bb6a','SN02':'#42a5f5','SN03':'#ff6b6b','SN04':'#f9a825','SN05':'#ce93d8','SN06':'#9c27b0','SN07':'#4ecdc4','SN08':'#d4af37'}

    # ── LIFECYCLE STAGES (universal) ──
    lifecycles = query(db, "SELECT life_id, arabic, transliteration, english FROM lifecycle_architecture ORDER BY stage_order")
    life_colors = {'LA01':'#8d6e63','LA02':'#90caf9','LA03':'#ef5350','LA04':'#ff7043','LA05':'#e0e0e0',
                   'LA06':'#ff8a80','LA07':'#ce93d8','LA08':'#66bb6a','LA09':'#78909c','LA10':'#ffd54f',
                   'LA11':'#4ecdc4','LA12':'#9e9e9e','LA13':'#616161','LA14':'#ffd54f'}

    # ── THERAPY COLOURS (universal) ──
    therapy_colours = query(db, "SELECT colour_id, colour_hex, temperament FROM therapy_prayer_map GROUP BY colour_id")
    # Hardcode the 4 primary colours with Arabic names from body_colour_therapy
    colour_map = {
        'CL001': {'name':'الأَحْمَر','en':'Red','hex':'#e53935','el':'النَّار / Fire','eff':'Heating + Gladdening'},
        'CL002': {'name':'الأَزْرَق','en':'Blue','hex':'#1e88e5','el':'المَاء / Water','eff':'Cooling + Calming'},
        'CL003': {'name':'الأَصْفَر','en':'Yellow','hex':'#fdd835','el':'الهَوَاء / Air','eff':'Stimulating + Purifying'},
        'CL004': {'name':'الأَخْضَر','en':'Green','hex':'#43a047','el':'الأَرْض / Earth','eff':'Stabilizing + Balancing'},
    }

    # ── PER-STAGE DATA ──
    # Prayer states (DB keys)
    prayer_states = ['QIYAM','RUKU','GOING_DOWN','SUJUD','JULOOS','TASHAHHUD','TASLEEM_R','TASLEEM_L']

    # Stage key mappings for each HTML file
    # PELVIS_3D uses: qiyam, qiyam_return, ruku, trans_sujud, sujud_1, sujud_2, juloos_1, tashahhud, tasleem_r, tasleem_mid, tasleem_l
    # FK uses: qiyam, ruku, qRet, gDn, sj1, jul1, sj2, tash, taslR, taslL
    # KINEBIOMECHANICS uses same as PELVIS_3D

    pelvis_map = {
        'qiyam':'QIYAM','qiyam_return':'QIYAM','ruku':'RUKU','trans_sujud':'GOING_DOWN',
        'sujud_1':'SUJUD','sujud_2':'SUJUD','juloos_1':'JULOOS','tashahhud':'TASHAHHUD',
        'tasleem_r':'TASLEEM_R','tasleem_mid':'TASLEEM_R','tasleem_l':'TASLEEM_L'
    }
    fk_map = {
        'qiyam':'QIYAM','ruku':'RUKU','qRet':'QIYAM','gDn':'GOING_DOWN',
        'sj1':'SUJUD','jul1':'JULOOS','sj2':'SUJUD','tash':'TASHAHHUD',
        'taslR':'TASLEEM_R','taslL':'TASLEEM_L'
    }

    # Sensory per state
    sensory_data = {}
    for state in prayer_states:
        rows = query(db, "SELECT sense_id, activation FROM sensory_prayer_map WHERE prayer_state=? ORDER BY sense_id", (state,))
        sensory_data[state] = [r['activation'] for r in rows]

    # Nafs per state
    nafs_data = {}
    for state in prayer_states:
        rows = query(db, "SELECT nafs_level, qalb_arabic, qalb_english, sadr_state FROM nafs_prayer_map WHERE prayer_state=?", (state,))
        if rows:
            r = rows[0]
            nafs_data[state] = {'l': r['nafs_level']-1, 'qAr': r['qalb_arabic'], 'qEn': r['qalb_english'], 'sadr': r['sadr_state']}

    # Therapy per state
    therapy_data = {}
    for state in prayer_states:
        rows = query(db, "SELECT colour_id, temperament, sound_cpm, therapeutic_note, quranic_ref FROM therapy_prayer_map WHERE prayer_state=?", (state,))
        if rows:
            r = rows[0]
            therapy_data[state] = {'cl': r['colour_id'], 'temp': r['temperament'], 'sound': r['sound_cpm'], 'note': r['therapeutic_note'], 'ref': r['quranic_ref']}

    # Heptad per state (H1-H7)
    heptad_data = {}
    for state in prayer_states:
        rows = query(db, "SELECT heptad, detail FROM heptad_prayer_map WHERE prayer_state=? ORDER BY heptad", (state,))
        heptad_data[state] = [r['detail'] for r in rows]

    # Qur'anic per stage (from heptad doesn't have it — use hardcoded from existing)
    # These are Hadith/Qur'an per prayer stage, not in a DB table yet
    quran_data = {
        'QIYAM':       {'ay':'يَا أَيُّهَا الَّذِينَ آمَنُوا ارْكَعُوا وَاسْجُدُوا وَاعْبُدُوا رَبَّكُمْ','ref':'Q22:77','tr':'O you who believe, bow and prostrate and worship your Lord'},
        'RUKU':        {'ay':'فَسَبِّحْ بِاسْمِ رَبِّكَ الْعَظِيمِ','ref':'Q56:74','tr':'So glorify the name of your Lord, the Most Great'},
        'GOING_DOWN':  {'ay':'وَخَرَّ رَاكِعًا وَأَنَابَ','ref':'Q38:24','tr':'And he fell down bowing and turned in repentance'},
        'SUJUD':       {'ay':'وَاسْجُدْ وَاقْتَرِبْ','ref':'Q96:19','tr':'Prostrate and draw near'},
        'JULOOS':      {'ay':'رَبِّ اغْفِرْ لِي','ref':'Hadith','tr':'My Lord, forgive me'},
        'TASHAHHUD':   {'ay':'التَّحِيَّاتُ لِلَّهِ','ref':'Hadith','tr':'All greetings are for Allah'},
        'TASLEEM_R':   {'ay':'وَالسَّلَامُ عَلَىٰ مَنِ اتَّبَعَ الْهُدَىٰ','ref':'Q20:47','tr':'And peace be upon he who follows guidance'},
        'TASLEEM_L':   {'ay':'سَلَامٌ قَوْلًا مِّن رَّبٍّ رَّحِيمٍ','ref':'Q36:58','tr':'Peace — a word from a Merciful Lord'},
    }

    # Formula per state (not in DB — from biomechanical analysis)
    formula_data = {
        'QIYAM':      {'ratio':'7 : 5','val':1.4,'bw':1.0,'label':'Kernel — axial gravity aligned','ref':'Q54:49'},
        'RUKU':       {'ratio':'11 : 5','val':2.2,'bw':1.2,'label':'Expansion — anterior moment','ref':'Q54:49'},
        'GOING_DOWN': {'ratio':'Transition','val':0,'bw':0.8,'label':'Deceleration — eccentric control','ref':'Q38:24'},
        'SUJUD':      {'ratio':'2 : 1','val':2.0,'bw':0.4,'label':'Inversion — 7-point distribution','ref':'Q96:19'},
        'JULOOS':     {'ratio':'7 : 5','val':1.4,'bw':0.6,'label':'Seated — pelvic redistribution','ref':'Q54:49'},
        'TASHAHHUD':  {'ratio':'Asymmetric','val':0,'bw':0.7,'label':'L/R differential load','ref':'Q54:49'},
        'TASLEEM_R':  {'ratio':'Rotational','val':0,'bw':0.7,'label':'Cervical torque R','ref':'Q20:47'},
        'TASLEEM_L':  {'ratio':'Rotational','val':0,'bw':0.7,'label':'Cervical torque L','ref':'Q36:58'},
    }

    # Nutrition per state (not in DB — from biomechanical analysis)
    nutr_data = {
        'QIYAM':      {'organ':'Stomach','state':'Gastric emptying optimised','nutr':'NA04','ar':'طَيِّبَات','effect':'Upright = gravity-aided emptying','ref':'Q5:4'},
        'RUKU':       {'organ':'Intestine','state':'Peristalsis stimulated','nutr':'NA04','ar':'طَيِّبَات','effect':'Compression = fold stimulation','ref':'Q5:88'},
        'GOING_DOWN': {'organ':'Abdomen','state':'Intra-abdominal pressure shift','nutr':'-','ar':'-','effect':'Visceral massage during descent','ref':'-'},
        'SUJUD':      {'organ':'Liver','state':'Hepatic portal drainage','nutr':'NA14','ar':'الْخَمْر','effect':'Inversion = bile + toxin flush','ref':'Q5:90'},
        'JULOOS':     {'organ':'Pelvis','state':'Pelvic floor relaxation','nutr':'NA17','ar':'إِلَّا مَا ذَكَّيْتُمْ','effect':'Colorectal alignment','ref':'Q5:3'},
        'TASHAHHUD':  {'organ':'Pelvis','state':'Insulin sensitivity window','nutr':'NA04','ar':'طَيِّبَات','effect':'Extended sit = metabolic settling','ref':'Q5:87'},
        'TASLEEM_R':  {'organ':'System','state':'Digestive baseline reset','nutr':'NA04','ar':'طَيِّبَات','effect':'Post-prayer system reset','ref':'Q5:4'},
        'TASLEEM_L':  {'organ':'System','state':'Absorption window open','nutr':'NA16','ar':'الْمَائِدَة','effect':'Cycle complete — provision sealed','ref':'Q5:114'},
    }

    # Lifecycle per state
    life_data = {
        'QIYAM':      {'stage':'LA11','detail':'Standing = peak strength phase (Q30:54)','ref':'Q30:54'},
        'RUKU':       {'stage':'LA06','detail':'Bow stretches the kaswa — flesh covering (Q23:14)','ref':'Q23:14'},
        'GOING_DOWN': {'stage':'LA07','detail':'Transition = transformation — خَلْقًا آخَرَ','ref':'Q23:14'},
        'SUJUD':      {'stage':'LA01','detail':'Forehead returns to clay origin (Q23:12)','ref':'Q23:12'},
        'JULOOS':     {'stage':'LA03','detail':'Seated = clinging/dependent phase','ref':'Q23:14'},
        'TASHAHHUD':  {'stage':'LA08','detail':'Testimony of Creator — أَحْسَنُ الْخَالِقِينَ','ref':'Q23:14'},
        'TASLEEM_R':  {'stage':'LA10','detail':'Salām = resurrection greeting (Q23:16)','ref':'Q23:16'},
        'TASLEEM_L':  {'stage':'LA10','detail':'Cycle complete — prayer sealed','ref':'Q23:16'},
    }

    # ── BUILD JS OUTPUT ──
    def build_stage_map(mapping, data_dict):
        """Map JS stage keys → DB prayer state → data"""
        result = {}
        for js_key, db_key in mapping.items():
            if db_key in data_dict:
                result[js_key] = data_dict[db_key]
        return result

    js = '// AUTO-GENERATED by generate_panel_data.py — DO NOT EDIT MANUALLY\n'
    js += '// Source: uslap_database_v3.db\n'
    js += '// Regenerate: python3 generate_panel_data.py\n\n'

    # Universal data
    js += '// ══ UNIVERSAL DATA (shared across all files) ══\n\n'

    # Nafs levels
    js += 'const PANEL_NAFS_LEVELS = [\n'
    for i, n in enumerate(nafs):
        js += f'  {{id:"{n["nafs_id"]}",ar:"{n["arabic"]}",en:"{n["english"]}",color:"{nafs_colors[i]}",ref:"{n["quranic_ref"]}"}},\n'
    js += '];\n\n'

    # Senses
    js += 'const PANEL_SENSES = [\n'
    for s in senses:
        sid = s['sense_id']
        js += f'  {{id:"{sid}",icon:"{sense_icons.get(sid,"?")}",name:"{s["transliteration"]}",color:"{sense_colors.get(sid,"#888")}"}},\n'
    js += '];\n\n'

    # Lifecycle stages
    js += 'const PANEL_LIFE_STAGES = [\n'
    for lc in lifecycles:
        lid = lc['life_id']
        js += f'  {{id:"{lid}",ar:"{lc["arabic"]}",en:"{lc["english"]}",color:"{life_colors.get(lid,"#888")}"}},\n'
    js += '];\n\n'

    # Therapy colours
    js += 'const PANEL_THER_COLOURS = ' + json.dumps(colour_map, ensure_ascii=False) + ';\n\n'

    # Heptad constants
    js += "const PANEL_H_COL = ['#e8e0d0','#4ecdc4','#f9a825','#ff6b6b','#42a5f5','#66bb6a','#ce93d8'];\n"
    js += "const PANEL_H_LBL = ['Body','Therapy','Formula','Nafs','Sensory','Nutrition','Lifecycle'];\n\n"

    # ── PELVIS_3D / KINEBIOMECHANICS stage-keyed data ──
    js += '// ══ PELVIS_3D + KINEBIOMECHANICS STAGE DATA ══\n\n'
    for name, data, mapping in [
        ('PELVIS_QUR', quran_data, pelvis_map),
        ('PELVIS_NAFS', nafs_data, pelvis_map),
        ('PELVIS_SENS', sensory_data, pelvis_map),
        ('PELVIS_THER', therapy_data, pelvis_map),
        ('PELVIS_FORM', formula_data, pelvis_map),
        ('PELVIS_NUTR', nutr_data, pelvis_map),
        ('PELVIS_LIFE', life_data, pelvis_map),
        ('PELVIS_HEPT', heptad_data, pelvis_map),
    ]:
        mapped = build_stage_map(mapping, data)
        js += f'const {name} = {json.dumps(mapped, ensure_ascii=False)};\n\n'

    # ── FK stage-keyed data ──
    js += '// ══ FK PROOF OF CONCEPT STAGE DATA ══\n\n'
    for name, data, mapping in [
        ('FK_QUR', quran_data, fk_map),
        ('FK_NAFS', nafs_data, fk_map),
        ('FK_SENS', sensory_data, fk_map),
        ('FK_THER', therapy_data, fk_map),
        ('FK_FORM', formula_data, fk_map),
        ('FK_NUTR', nutr_data, fk_map),
        ('FK_LIFE', life_data, fk_map),
        ('FK_HEPT', heptad_data, fk_map),
    ]:
        mapped = build_stage_map(mapping, data)
        js += f'const {name} = {json.dumps(mapped, ensure_ascii=False)};\n\n'

    db.close()

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(js)

    # Stats
    size = os.path.getsize(OUT)
    print(f'Generated {OUT} ({size:,} bytes)')
    print(f'  Nafs levels: {len(nafs)}')
    print(f'  Senses: {len(senses)}')
    print(f'  Lifecycle stages: {len(lifecycles)}')
    print(f'  Prayer states: {len(prayer_states)}')
    print(f'  PELVIS stage keys: {len(pelvis_map)}')
    print(f'  FK stage keys: {len(fk_map)}')

if __name__ == '__main__':
    main()
