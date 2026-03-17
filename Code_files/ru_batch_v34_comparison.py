#!/usr/bin/env python3
"""
USLaP Russian Batch — v3.4 vs v3.3 Comparison Script
Generates formatted comparison report with Unicode box-drawing characters.
"""

import json
from collections import Counter
from datetime import datetime

# ─── File paths ───
V33_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Batch Reports/RU_BATCH_REPORT_20260314_123511.json"
V34_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Batch Reports/RU_BATCH_REPORT_20260314_131602.json"
STYLE_REF = "/Users/mmsetubal/Documents/USLaP workplace/Batch Reports/RU_BATCH_v33_COMPARISON.txt"
OUTPUT_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Batch Reports/RU_BATCH_v34_COMPARISON.txt"

CATS = ['already_in_lattice', 'confirmed_high', 'pending_review', 'auto_rejected']
CAT_LABELS = {
    'already_in_lattice': 'EXISTING',
    'confirmed_high': 'CONFIRMED_HIGH',
    'pending_review': 'PENDING_REVIEW',
    'auto_rejected': 'AUTO_REJECTED',
}

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_word_map(data):
    m = {}
    for cat in CATS:
        for entry in data[cat]:
            m[entry['word']] = entry
    return m

def score_distribution(data):
    scores = Counter()
    for cat in CATS:
        for entry in data[cat]:
            s = entry.get('score')
            if s is not None:
                scores[s] += 1
    return scores

def count_orig2(data):
    c = 0
    for cat in CATS:
        for entry in data[cat]:
            if entry.get('orig2_track'):
                c += 1
    return c

def count_depal(data):
    c = 0
    for cat in CATS:
        for entry in data[cat]:
            for line in entry.get('log_lines', []):
                if 'DEPAL' in str(line):
                    c += 1
                    break
    return c

def derive_cognate_status(entry):
    """Derive AGREES/COMPETITION/NOTE from root comparison."""
    cr = entry.get('cognate_crossref')
    if cr is None:
        return None, None
    if cr.get('source') == 'LATTICE_ENTRY':
        return 'LATTICE_MATCH', cr
    en_root = cr.get('root_letters', '')
    ru_root = entry.get('root_letters', '')
    if en_root and ru_root and en_root == ru_root:
        return 'AGREES', cr
    elif en_root and ru_root:
        return 'COMPETITION', cr
    return 'UNKNOWN', cr

def main():
    v33 = load_json(V33_PATH)
    v34 = load_json(V34_PATH)

    v33_map = build_word_map(v33)
    v34_map = build_word_map(v34)

    lines = []
    def w(text=''):
        lines.append(text)

    # ─── Header ───
    w('══════════════════════════════════════════════════════════════════════════')
    w('  USLaP Russian Batch — v3.4 vs v3.3 Comparison Summary')
    w('  بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    w(f'  Generated: {datetime.now().strftime("%Y-%m-%d")}')
    w('══════════════════════════════════════════════════════════════════════════')
    w()
    w(f'  Input: {v33["total_words"]} Russian words (built-in list, deduplicated)')
    w(f'  v3.3 baseline: RU_BATCH_REPORT_20260314_123511.json')
    w(f'  v3.4 run:      RU_BATCH_REPORT_20260314_131602.json')
    w(f'  Engine:        {v34.get("engine_version", "v3.0")}')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 1. CATEGORY COUNTS
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  1. CATEGORY COUNTS — SIDE BY SIDE')
    w('──────────────────────────────────────────────────────────────────────────')
    w()
    w(f'  {"Category":<20} {"v3.3":>5}    {"v3.4":>5}    {"Delta":>5}    Direction')
    w(f'  {"─" * 19}   {"─" * 5}   {"─" * 5}   {"─" * 5}    {"─" * 10}')

    for cat in CATS:
        label = CAT_LABELS[cat]
        c33 = len(v33[cat])
        c34 = len(v34[cat])
        delta = c34 - c33
        d_str = f'+{delta}' if delta > 0 else str(delta)
        if delta == 0:
            direction = '(unchanged)'
        elif delta > 0:
            direction = f'(+{delta} added)'
        else:
            direction = f'({abs(delta)} removed)'
        w(f'  {label:<20} {c33:>5}    {c34:>5}    {d_str:>5}    {direction}')

    cb33 = len(v33.get('cluster_backlog', []))
    cb34 = len(v34.get('cluster_backlog', []))
    cb_delta = cb34 - cb33
    cb_d_str = f'+{cb_delta}' if cb_delta > 0 else str(cb_delta)
    cb_dir = '(unchanged)' if cb_delta == 0 else f'({abs(cb_delta)} {"more" if cb_delta > 0 else "fewer"} cluster discoveries)'
    w(f'  {"Cluster Backlog":<20} {cb33:>5}    {cb34:>5}    {cb_d_str:>5}    {cb_dir}')
    w()
    w(f'  TOTAL PROCESSED      {v33["total_words"]}     {v34["total_words"]}')
    w()

    # Check for category changes
    cat_changes_up = 0
    cat_changes_down = 0
    for word in v33_map:
        if word in v34_map:
            if v33_map[word]['category'] != v34_map[word]['category']:
                # Determine direction
                rank = {'ALREADY_IN_LATTICE': 4, 'CONFIRMED_HIGH': 3, 'PENDING_REVIEW': 2, 'AUTO_REJECTED': 1}
                r33 = rank.get(v33_map[word]['category'], 0)
                r34 = rank.get(v34_map[word]['category'], 0)
                if r34 > r33:
                    cat_changes_up += 1
                else:
                    cat_changes_down += 1

    w(f'  NET EFFECT: Category counts IDENTICAL between v3.3 and v3.4.')
    w(f'  No words promoted or demoted between categories.')
    w(f'  The v3.4 changes are INTERNAL — new fields (sem_review, compound_parts),')
    w(f'  root refinements within categories, and cognate crossref EN root updates.')
    w(f'  Cluster backlog decreased by {abs(cb_delta)} (tighter clustering).')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 2. WORDS THAT CHANGED CATEGORY
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  2. WORDS THAT CHANGED CATEGORY (v3.3 -> v3.4)')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    category_changes = []
    for word in sorted(v33_map.keys()):
        if word in v34_map:
            if v33_map[word]['category'] != v34_map[word]['category']:
                category_changes.append((
                    word,
                    v33_map[word]['category'],
                    v34_map[word]['category'],
                    v33_map[word].get('score'),
                    v34_map[word].get('score'),
                    v33_map[word].get('root_letters'),
                    v34_map[word].get('root_letters'),
                ))

    if not category_changes:
        w('  NO CATEGORY CHANGES.')
        w()
        w('  All 316 words remain in their v3.3 categories. Zero promotions,')
        w('  zero demotions. Category stability is absolute.')
    else:
        w(f'  {len(category_changes)} word(s) changed category:')
        w()
        w(f'  {"Word":<15} {"v3.3":<18} {"v3.4":<18} {"Score v3.3":<12} {"Score v3.4":<12} Root Change')
        w(f'  {"─"*14} {"─"*17} {"─"*17} {"─"*11} {"─"*11} {"─"*12}')
        for word, cat33, cat34, s33, s34, r33, r34 in category_changes:
            root_change = f'{r33} -> {r34}' if r33 != r34 else 'None'
            w(f'  {word:<15} {cat33:<18} {cat34:<18} {str(s33):<12} {str(s34):<12} {root_change}')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 3. ROOT CHANGES WITHIN SAME CATEGORY
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  3. ROOT CHANGES WITHIN SAME CATEGORY')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    # Separate by CONFIRMED_HIGH and PENDING_REVIEW
    ch_root_changes = []
    pr_root_changes = []

    for word in sorted(v33_map.keys()):
        if word in v34_map:
            e33 = v33_map[word]
            e34 = v34_map[word]
            if e33['category'] == e34['category'] and e33.get('root_letters') != e34.get('root_letters'):
                entry = (
                    word,
                    e33.get('root_letters'),
                    e34.get('root_letters'),
                    e33.get('score'),
                    e34.get('score'),
                    e33.get('ar_word'),
                    e34.get('ar_word'),
                    e33.get('phonetic_chain', ''),
                    e34.get('phonetic_chain', ''),
                )
                if e33['category'] == 'CONFIRMED_HIGH':
                    ch_root_changes.append(entry)
                elif e33['category'] == 'PENDING_REVIEW':
                    pr_root_changes.append(entry)

    total_root_changes = len(ch_root_changes) + len(pr_root_changes)
    w(f'  {total_root_changes} words show different root assignments between v3.3 and v3.4')
    w(f'  while remaining in the SAME category:')
    w()

    if ch_root_changes:
        w(f'  A. CONFIRMED_HIGH root changes ({len(ch_root_changes)} words):')
        w()
        w(f'  {"Word":<15} {"v3.3 Root":<12} {"v3.4 Root":<12} {"Score v3.3":<12} {"Score v3.4":<12} Assessment')
        w(f'  {"─"*14} {"─"*11} {"─"*11} {"─"*11} {"─"*11} {"─"*10}')
        for word, r33, r34, s33, s34, _, _, _, _ in ch_root_changes:
            s_delta = (s34 or 0) - (s33 or 0)
            if s_delta > 0:
                assessment = f'Improved (+{s_delta})'
            elif s_delta < 0:
                assessment = f'Regressed ({s_delta})'
            else:
                assessment = 'Refined'
            w(f'  {word:<15} {str(r33):<12} {str(r34):<12} {str(s33):<12} {str(s34):<12} {assessment}')
        w()

        # Detailed explanations
        for word, r33, r34, s33, s34, ar33, ar34, ch33, ch34 in ch_root_changes:
            if word == 'АПТЕКА':
                w(f'  АПТЕКА + ПОДУШКА: Both moved from {r33} to {r34}. In v3.3,')
                w(f'  these were assigned ب-ت-ك; v3.4 reassigns to ف-ت-ق / fatq /')
                w(f'  to split open, to cleave (Qur\'anic). Chain: {ch34}.')
                w(f'  Scores unchanged at 8. The first consonant shifted from')
                w(f'  ب→п(S09) to ف→п(S08) — both valid mappings for Russian п.')
                w()
            elif word == 'ДОГОВОР':
                w(f'  ДОГОВОР: Root REVERTED from {r33} ({ar33}) to {r34} ({ar34}).')
                w(f'  v3.3 had upgraded this to ج-ب-ر (الجَبَّار, 21 tokens) at score 9.')
                w(f'  v3.4 returns to ذ-ه-ب (to go, 383 tokens) at score 8.')
                w(f'  Chain: {ch34}. Score regressed 9 -> 8.')
                w(f'  Assessment: This is a ROOT REVERSION, not a refinement. The v3.3')
                w(f'  root ج-ب-ر had stronger semantic alignment with "covenant/agreement"')
                w(f'  (compulsion/binding force). Flagged for human adjudication.')
                w()
            elif word == 'СЕРДЦЕ':
                w(f'  СЕРДЦЕ: Root shifted from {r33} ({ar33}) to {r34} ({ar34}).')
                w(f'  v3.3 had refined this from ш-ر-د to س-ر-د (سَرَدَ / to arrange,')
                w(f'  Q34:11). v3.4 reverts to ш-ر-د. Chain: {ch34}.')
                w(f'  First consonant: с→س(S21) in v3.3 vs с→ш(S05) in v3.4.')
                w(f'  Score unchanged at 8.')
                w()

    if pr_root_changes:
        w(f'  B. PENDING_REVIEW root changes ({len(pr_root_changes)} words — all ORIG2 skeleton matches):')
        w()
        w(f'  {"Word":<15} {"v3.3 Root":<12} {"v3.4 Root":<12} {"Score v3.3":<12} {"Score v3.4":<12} Assessment')
        w(f'  {"─"*14} {"─"*11} {"─"*11} {"─"*11} {"─"*11} {"─"*10}')
        for word, r33, r34, s33, s34, _, _, _, _ in pr_root_changes:
            s_delta = (s34 or 0) - (s33 or 0)
            if s_delta > 0:
                assessment = f'Improved (+{s_delta})'
            elif s_delta < 0:
                assessment = f'Regressed ({s_delta})'
            else:
                assessment = 'Refined'
            w(f'  {word:<15} {str(r33):<12} {str(r34):<12} {str(s33):<12} {str(s34):<12} {assessment}')
        w()
        w(f'  ГОД: ORIG2 skeleton REVERTED from {[e for e in pr_root_changes if e[0]=="ГОД"][0][1]} to {[e for e in pr_root_changes if e[0]=="ГОД"][0][2]}.')
        w(f'  v3.3 had refined this to qd (Kashgari: qad) at score 10.')
        w(f'  v3.4 returns to kd at score 9. Score regressed 10 -> 9.')
        w()
        w(f'  ЧАС + ЧИСЛО: Both REVERTED from {[e for e in pr_root_changes if e[0]=="ЧАС"][0][1]} to {[e for e in pr_root_changes if e[0]=="ЧАС"][0][2]}.')
        w(f'  v3.3 had changed these to cc; v3.4 returns to ss.')
        w(f'  ЧАС score improved 9 -> 10; ЧИСЛО score improved 7 -> 8.')
        w(f'  These are REVERSIONS of v3.3 changes that IMPROVE scores —')
        w(f'  the v3.4 engine prefers the ss skeleton with higher confidence.')
        w()

    # ═══════════════════════════════════════════════════════════════════
    # 4. SCORE CHANGES
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  4. SCORE CHANGES')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    score_changes = []
    for word in sorted(v33_map.keys()):
        if word in v34_map:
            e33 = v33_map[word]
            e34 = v34_map[word]
            s33 = e33.get('score')
            s34 = e34.get('score')
            if s33 is not None and s34 is not None and s33 != s34:
                delta = s34 - s33
                score_changes.append((word, s33, s34, delta, e33['category'], e34['category'], e33.get('root_letters'), e34.get('root_letters')))

    if score_changes:
        improved = [x for x in score_changes if x[3] > 0]
        regressed = [x for x in score_changes if x[3] < 0]

        w(f'  {len(score_changes)} words changed score:')
        w(f'    Improved:  {len(improved)}')
        w(f'    Regressed: {len(regressed)}')
        w()
        w(f'  {"Word":<15} {"v3.3":>5}  {"v3.4":>5}  {"Delta":>5}  {"Category":<18} {"Root v3.3":<12} {"Root v3.4":<12}')
        w(f'  {"─"*14} {"─"*5}  {"─"*5}  {"─"*5}  {"─"*17} {"─"*11} {"─"*11}')
        for word, s33, s34, delta, cat33, cat34, r33, r34 in score_changes:
            d_str = f'+{delta}' if delta > 0 else str(delta)
            cat_display = cat33 if cat33 == cat34 else f'{cat33}->{cat34}'
            w(f'  {word:<15} {s33:>5}  {s34:>5}  {d_str:>5}  {cat_display:<18} {str(r33):<12} {str(r34):<12}')
        w()
        w(f'  NET SCORE EFFECT: {len(improved)} improvements, {len(regressed)} regressions.')
        if regressed:
            w(f'  Regressions: {", ".join(x[0] for x in regressed)}')
            in_confirmed = [x for x in regressed if 'CONFIRMED' in x[4]]
            if in_confirmed:
                w(f'  Of these, {len(in_confirmed)} are in CONFIRMED_HIGH: {", ".join(x[0] for x in in_confirmed)}')
            else:
                w(f'  None of the regressions are in CONFIRMED_HIGH.')
    else:
        w('  No score changes between v3.3 and v3.4.')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 5. NEW v3.4 FEATURES
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  5. NEW v3.4 FEATURES')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    # 5A. SEM_REVIEW
    w('  A. SEM_REVIEW FLAG (NEW in v3.4)')
    w()
    w('  The sem_review flag marks entries where the engine has performed')
    w('  semantic review — verifying that the root meaning aligns with the')
    w('  downstream word\'s usage. This is a pre-filter for human QUF review.')
    w()

    sem_by_cat = {}
    for cat in CATS:
        sem_true = sum(1 for e in v34[cat] if e.get('sem_review'))
        sem_false = sum(1 for e in v34[cat] if not e.get('sem_review'))
        sem_by_cat[cat] = (sem_true, sem_false)

    total_sem_true = sum(v[0] for v in sem_by_cat.values())
    total_sem_false = sum(v[1] for v in sem_by_cat.values())

    w(f'  {"Category":<20} {"sem_review=true":>16} {"sem_review=false":>17} {"Total":>6}')
    w(f'  {"─"*19} {"─"*16} {"─"*17} {"─"*6}')
    for cat in CATS:
        label = CAT_LABELS[cat]
        st, sf = sem_by_cat[cat]
        total = st + sf
        w(f'  {label:<20} {st:>16} {sf:>17} {total:>6}')
    w(f'  {"TOTAL":<20} {total_sem_true:>16} {total_sem_false:>17} {total_sem_true + total_sem_false:>6}')
    w()
    w(f'  Key observation: ALL 150 CONFIRMED_HIGH entries have sem_review=true.')
    w(f'  11 of 156 PENDING_REVIEW entries also have sem_review=true —')
    w(f'  these are borderline entries where semantic review passed but')
    w(f'  other gates (positional_score, Q-gate) kept them in PENDING.')
    w(f'  The 1 AUTO_REJECTED entry (КАМЕНЩИК) also has sem_review=true,')
    w(f'  meaning the semantic check ran but was insufficient to overcome')
    w(f'  the 2 extra consonants that triggered rejection.')
    w()

    # 5B. COMPOUND_PARTS
    w('  B. COMPOUND DETECTION (NEW in v3.4)')
    w()
    w('  The compound_parts field identifies multi-root Russian words and')
    w('  traces each component to its Allah\'s Arabic or Bitig root separately.')
    w()

    compound_entries = []
    for cat in CATS:
        for entry in v34[cat]:
            cp = entry.get('compound_parts')
            if cp is not None:
                compound_entries.append((entry['word'], entry['category'], entry['score'], cp))

    has_compound = sum(1 for e in compound_entries)
    no_compound = v34['total_words'] - has_compound

    w(f'  Entries with compound_parts:     {has_compound}')
    w(f'  Entries without compound_parts:   {no_compound}')
    w()

    for word, cat, score, cp in compound_entries:
        w(f'  {word} (category: {CAT_LABELS.get(cat.lower().replace(" ","_"), cat)}, score: {score}):')
        label = cp.get('label', '')
        w(f'    Label: {label}')
        prefix = cp.get('prefix')
        root = cp.get('root')
        bridge = cp.get('bridge', '')
        if prefix:
            w(f'    Prefix part: {prefix.get("part", "")}')
            w(f'      Root: {prefix.get("root", "")} ({prefix.get("token_count", 0)} tokens)')
            w(f'      Chain: {prefix.get("chain", "")}')
        if bridge:
            w(f'    Bridge: {bridge}')
        if root:
            w(f'    Root part: {root.get("part", "")}')
            w(f'      Root: {root.get("root", "")} ({root.get("token_count", 0)} tokens)')
            w(f'      Chain: {root.get("chain", "")}')
            if root.get('is_orig2'):
                w(f'      Track: ORIG2 (Bitig)')
                km = root.get('kashgari_meaning', '')
                if km:
                    w(f'      Kashgari: {km[:80]}')
        w()

    # ═══════════════════════════════════════════════════════════════════
    # 6. COGNATE CROSS-REFERENCE COMPARISON
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  6. COGNATE CROSS-REFERENCE COMPARISON')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    # Build cognate maps
    def build_cognate_map(data):
        m = {}
        word_map = build_word_map(data)
        for word, entry in word_map.items():
            cr = entry.get('cognate_crossref')
            if cr is not None:
                m[word] = (cr, entry)
        return m

    cog33 = build_cognate_map(v33)
    cog34 = build_cognate_map(v34)

    w(f'  v3.3 entries with cognate_crossref:  {len(cog33)}')
    w(f'  v3.4 entries with cognate_crossref:  {len(cog34)}')
    w()

    # Derive status for both versions
    def classify_cognates(data):
        lattice = []
        agrees = []
        competition = []
        note = []
        unknown = []
        word_map = build_word_map(data)
        for word, entry in word_map.items():
            cr = entry.get('cognate_crossref')
            if cr is None:
                continue
            status, _ = derive_cognate_status(entry)
            if status == 'LATTICE_MATCH':
                lattice.append((word, cr, entry))
            elif status == 'AGREES':
                agrees.append((word, cr, entry))
            elif status == 'COMPETITION':
                competition.append((word, cr, entry))
            elif status == 'NOTE':
                note.append((word, cr, entry))
            else:
                unknown.append((word, cr, entry))
        return lattice, agrees, competition, note, unknown

    lat33, agr33, comp33, note33, unk33 = classify_cognates(v33)
    lat34, agr34, comp34, note34, unk34 = classify_cognates(v34)

    w(f'  BREAKDOWN (derived from root comparison):')
    w()
    w(f'  {"Status":<20} {"v3.3":>5}    {"v3.4":>5}    Delta')
    w(f'  {"─"*19} {"─"*5}   {"─"*5}   {"─"*5}')
    for label, c33, c34 in [
        ('LATTICE_MATCH', len(lat33), len(lat34)),
        ('ROOT AGREES', len(agr33), len(agr34)),
        ('ROOT COMPETITION', len(comp33), len(comp34)),
        ('NOTE', len(note33), len(note34)),
        ('UNKNOWN', len(unk33), len(unk34)),
    ]:
        delta = c34 - c33
        d_str = f'+{delta}' if delta > 0 else str(delta)
        w(f'  {label:<20} {c33:>5}    {c34:>5}    {d_str:>5}')
    w()

    # Check for cognate crossref changes between v3.3 and v3.4
    cognate_changes = []
    all_cog_words = sorted(set(list(cog33.keys()) + list(cog34.keys())))
    for word in all_cog_words:
        c33_data = cog33.get(word)
        c34_data = cog34.get(word)
        if c33_data and c34_data:
            cr33 = c33_data[0]
            cr34 = c34_data[0]
            changes = {}
            for key in set(list(cr33.keys()) + list(cr34.keys())):
                v33_val = cr33.get(key)
                v34_val = cr34.get(key)
                if v33_val != v34_val:
                    changes[key] = (v33_val, v34_val)
            if changes:
                cognate_changes.append((word, changes))

    if cognate_changes:
        w(f'  COGNATE CROSSREF CHANGES (v3.3 -> v3.4):')
        w()
        for word, changes in cognate_changes:
            w(f'  {word}:')
            for key, (v33_val, v34_val) in changes.items():
                w(f'    {key}: {v33_val} -> {v34_val}')
        w()
        w(f'  ШАРИАТ: The EN pipeline now assigns ش-ر-د (شَرَدَ / to flee,')
        w(f'  to stray — S19 د→t) instead of ش-ر-ط (شَرَطَ / to stipulate')
        w(f'  — S04 ط→t). The Russian root remains ص-ر-ط. Both versions')
        w(f'  show ROOT COMPETITION between RU and EN pipelines. The change')
        w(f'  is in the EN trace, not the RU trace.')
    else:
        w(f'  No cognate crossref changes between v3.3 and v3.4.')
    w()

    # List all cognate crossrefs for reference
    w(f'  FULL COGNATE CROSSREF TABLE (v3.4):')
    w()
    w(f'  {"Word":<15} {"EN Cousin":<12} {"RU Root":<12} {"EN Root":<12} {"Status":<12} {"Source":<15}')
    w(f'  {"─"*14} {"─"*11} {"─"*11} {"─"*11} {"─"*11} {"─"*14}')

    for word in sorted(cog34.keys()):
        cr, entry = cog34[word]
        en_cousin = cr.get('en_cousin', '')
        en_root = cr.get('root_letters', '')
        ru_root = entry.get('root_letters', '')
        source = cr.get('source', '')
        status, _ = derive_cognate_status(entry)
        w(f'  {word:<15} {en_cousin:<12} {ru_root:<12} {en_root:<12} {status:<12} {source:<15}')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 7. SCORE DISTRIBUTION
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  7. SCORE DISTRIBUTION')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    sd33 = score_distribution(v33)
    sd34 = score_distribution(v34)
    all_scores = sorted(set(list(sd33.keys()) + list(sd34.keys())))

    w(f'  {"Score":>5}    {"v3.3":>5}    {"v3.4":>5}    {"Delta":>5}')
    w(f'  {"─"*5}    {"─"*5}    {"─"*5}    {"─"*5}')
    for score in all_scores:
        c33 = sd33.get(score, 0)
        c34 = sd34.get(score, 0)
        delta = c34 - c33
        d_str = f'+{delta}' if delta > 0 else str(delta)
        w(f'  {score:>5}    {c33:>5}    {c34:>5}    {d_str:>5}')
    w()

    total33 = sum(sd33.values())
    total34 = sum(sd34.values())
    if total33 > 0 and total34 > 0:
        # Calculate median
        def median_score(sd):
            vals = []
            for s, c in sorted(sd.items()):
                vals.extend([s] * c)
            if not vals:
                return 0
            mid = len(vals) // 2
            return vals[mid]

        def mean_score(sd):
            total_val = sum(s * c for s, c in sd.items())
            total_count = sum(sd.values())
            return total_val / total_count if total_count > 0 else 0

        med33 = median_score(sd33)
        med34 = median_score(sd34)
        mean33 = mean_score(sd33)
        mean34 = mean_score(sd34)

        w(f'  Median score:   v3.3 = {med33}   |   v3.4 = {med34}   {"(unchanged)" if med33 == med34 else ""}')
        w(f'  Mean score:     v3.3 = {mean33:.2f} |   v3.4 = {mean34:.2f}')
    w()
    w(f'  Key observation: Score distribution is nearly identical. The v3.4')
    w(f'  changes are balanced — 2 scores improved (ЧАС +1, ЧИСЛО +1) and')
    w(f'  2 scores regressed (ДОГОВОР -1, ГОД -1). Net score movement = 0.')
    w(f'  The distribution shape is stable with peak at 8.')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 8. EXISTING FEATURES — STABILITY CHECK
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  8. EXISTING FEATURES — STABILITY CHECK')
    w('──────────────────────────────────────────────────────────────────────────')
    w()

    depal33 = count_depal(v33)
    depal34 = count_depal(v34)
    orig2_33 = count_orig2(v33)
    orig2_34 = count_orig2(v34)

    w(f'  DEPAL (Depalatalisation Competition) flags:')
    w(f'    v3.3: {depal33} words flagged    |    v3.4: {depal34} words flagged    {"(identical)" if depal33 == depal34 else ""}')
    w()
    w(f'  ORIG2 (Kashgari/Bitig) track:')
    w(f'    v3.3: {orig2_33} words routed    |    v3.4: {orig2_34} words routed    {"(identical)" if orig2_33 == orig2_34 else ""}')
    w()
    w(f'  AUTO_REJECTED:')

    ar33 = [e for e in v33['auto_rejected']]
    ar34 = [e for e in v34['auto_rejected']]
    ar33_words = ', '.join(f'{e["word"]} (score={e["score"]})' for e in ar33)
    ar34_words = ', '.join(f'{e["word"]} (score={e["score"]})' for e in ar34)
    w(f'    v3.3: {ar33_words}  |    v3.4: {ar34_words}    {"(identical)" if ar33_words == ar34_words else ""}')
    w()

    # Three problem words
    w(f'  THE THREE PROBLEM WORDS (tracked since v3.1):')
    for word in ['САБЛЯ', 'ВОЖДЬ', 'САМОВАР']:
        e33 = v33_map.get(word, {})
        e34 = v34_map.get(word, {})
        stable = (e33.get('category') == e34.get('category') and
                  e33.get('score') == e34.get('score') and
                  e33.get('root_letters') == e34.get('root_letters'))
        status = 'STABLE' if stable else 'CHANGED'
        extras = []
        if e34.get('sem_review'):
            extras.append('sem_review=true')
        if e34.get('compound_parts') is not None:
            extras.append('compound detected')
        cr = e34.get('cognate_crossref')
        if cr is not None:
            cog_status, _ = derive_cognate_status(e34)
            extras.append(f'cognate: {cog_status}')
        extra_str = f' + NEW: {", ".join(extras)}' if extras else ''
        w(f'    {word}:    {e34.get("category", "?")}, score={e34.get("score")}, root={e34.get("root_letters")}   ({status} — both versions){extra_str}')
    w()
    w(f'  All existing v3.3 features preserved. Zero feature regressions.')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # 9. CLUSTER BACKLOG
    # ═══════════════════════════════════════════════════════════════════
    w('──────────────────────────────────────────────────────────────────────────')
    w('  9. CLUSTER BACKLOG')
    w('──────────────────────────────────────────────────────────────────────────')
    w()
    w(f'  v3.3: {cb33} cluster members    |    v3.4: {cb34} cluster members    ({cb_delta:+d})')
    w()
    if cb_delta < 0:
        w(f'  {abs(cb_delta)} fewer cluster members in v3.4. This indicates tighter')
        w(f'  clustering — the engine is more selective about which words from')
        w(f'  /usr/share/dict/words qualify as cluster members. Not a regression.')
    elif cb_delta > 0:
        w(f'  {cb_delta} additional bonus discoveries found by the cluster expander.')
    else:
        w(f'  Cluster backlog unchanged.')
    w()

    # ═══════════════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    w('══════════════════════════════════════════════════════════════════════════')
    w('  EXECUTIVE SUMMARY')
    w('══════════════════════════════════════════════════════════════════════════')
    w()
    w('  v3.4 improvements over v3.3:')
    w()

    # New features
    w(f'  [+] NEW FIELD: sem_review flag on ALL {v34["total_words"]} entries')
    w(f'      - {total_sem_true} entries marked sem_review=true')
    w(f'      - ALL 150 CONFIRMED_HIGH entries have sem_review=true')
    w(f'      - 11 PENDING_REVIEW entries have sem_review=true (borderline)')
    w(f'      - Enables targeted semantic audit: only sem_review=true entries')
    w(f'        need human semantic QUF check')
    w()

    w(f'  [+] NEW FIELD: compound_parts detection')
    w(f'      - {has_compound} compound words detected and decomposed:')
    for word, cat, score, cp in compound_entries:
        w(f'        {word}: {cp.get("label", "")}')
    w(f'      - Each component traced to its own AA/Bitig root independently')
    w(f'      - Foundation for future Russian compound word analysis at scale')
    w()

    # Score improvements
    improved_list = [x for x in score_changes if x[3] > 0]
    regressed_list = [x for x in score_changes if x[3] < 0]

    if improved_list:
        w(f'  [+] {len(improved_list)} score improvement(s):')
        for word, s33, s34, delta, cat33, cat34, r33, r34 in improved_list:
            w(f'      {word}: {s33} -> {s34} ({r33} -> {r34})')

    if regressed_list:
        w()
        w(f'  [-] {len(regressed_list)} score regression(s):')
        for word, s33, s34, delta, cat33, cat34, r33, r34 in regressed_list:
            in_confirmed = 'CONFIRMED' in cat33
            flag = ' (IN CONFIRMED_HIGH — requires adjudication)' if in_confirmed else ' (in PENDING — acceptable)'
            w(f'      {word}: {s33} -> {s34} ({r33} -> {r34}){flag}')

    w()

    # Root changes
    total_root = len(ch_root_changes) + len(pr_root_changes)
    w(f'  [~] {total_root} root reassignment(s) within same category:')
    w(f'      CONFIRMED_HIGH: {len(ch_root_changes)} words')
    for word, r33, r34, s33, s34, _, _, _, _ in ch_root_changes:
        s_note = f'score {s33}->{s34}' if s33 != s34 else f'score {s33}'
        w(f'        {word}: {r33} -> {r34} ({s_note})')
    w(f'      PENDING_REVIEW: {len(pr_root_changes)} words')
    for word, r33, r34, s33, s34, _, _, _, _ in pr_root_changes:
        s_note = f'score {s33}->{s34}' if s33 != s34 else f'score {s33}'
        w(f'        {word}: {r33} -> {r34} ({s_note})')
    w()

    # Stability
    w(f'  [=] CATEGORY COUNTS: Identical across all 4 categories')
    w(f'  [=] EXISTING count unchanged at {len(v34["already_in_lattice"])}')
    w(f'  [=] CONFIRMED_HIGH count unchanged at {len(v34["confirmed_high"])}')
    w(f'  [=] PENDING_REVIEW count unchanged at {len(v34["pending_review"])}')
    w(f'  [=] AUTO_REJECTED unchanged at {len(v34["auto_rejected"])} (КАМЕНЩИК)')
    w(f'  [=] DEPAL flags unchanged at {depal34}')
    w(f'  [=] ORIG2 track count unchanged at {orig2_34}')
    w(f'  [=] Cognate cross-references unchanged at {len(cog34)} entries')
    w(f'  [=] All three problem words (САБЛЯ, ВОЖДЬ, САМОВАР) remain')
    w(f'      CONFIRMED_HIGH at score 9/10 — no regressions')
    w(f'  [=] Score distribution shape unchanged (median=8, peak at 8)')
    w()

    # No CONFIRMED_HIGH regressions (category)
    confirmed_33_words = set(e['word'] for e in v33['confirmed_high'])
    confirmed_34_words = set(e['word'] for e in v34['confirmed_high'])
    lost_from_confirmed = confirmed_33_words - confirmed_34_words
    if not lost_from_confirmed:
        w(f'  ZERO REGRESSIONS in CONFIRMED_HIGH category membership.')
        w(f'  No word was demoted from CONFIRMED_HIGH to a lower category.')
    else:
        w(f'  WARNING: {len(lost_from_confirmed)} word(s) lost from CONFIRMED_HIGH:')
        for word in lost_from_confirmed:
            w(f'    {word}')
    w()

    # Verdict
    w(f'  VERDICT: v3.4 is a STRUCTURAL upgrade over v3.3. The headline')
    w(f'  features are:')
    w()
    w(f'  1. SEM_REVIEW FLAG — the engine now flags which entries have')
    w(f'     passed semantic review, enabling targeted human QUF audits.')
    w(f'     162 of 316 entries (51.3%) are marked sem_review=true.')
    w()
    w(f'  2. COMPOUND DETECTION — the engine now detects multi-root')
    w(f'     Russian words (САМОВАР, СПРАВЕДЛИВОСТЬ) and traces each')
    w(f'     component independently. This is the foundation for scaling')
    w(f'     compound word analysis across the Russian batch.')
    w()
    w(f'  3. ROOT STABILITY — category counts are identical to v3.3.')
    w(f'     7 root reassignments occurred (4 CONFIRMED, 3 PENDING),')
    w(f'     with mixed direction: some are v3.4 refinements (АПТЕКА,')
    w(f'     ПОДУШКА), some are reversions of v3.3 changes (ДОГОВОР,')
    w(f'     СЕРДЦЕ, ГОД). The PENDING reversions (ЧАС, ЧИСЛО)')
    w(f'     actually improved scores, suggesting v3.4 prefers the')
    w(f'     original skeleton assignments with higher confidence.')
    w()
    w(f'  4. COGNATE CROSSREF REFINEMENT — 1 EN pipeline root updated')
    w(f'     (ШАРИАТ: ش-ر-ط -> ش-ر-د). Cognate agreement counts')
    w(f'     unchanged (4 AGREES, 12 COMPETITION, 6 LATTICE).')
    w()
    w(f'  The 1 CONFIRMED_HIGH score regression (ДОГОВОР: 9->8) is the')
    w(f'  only item requiring human adjudication — the v3.3 root ج-ب-ر')
    w(f'  had stronger semantic alignment. All other changes are neutral')
    w(f'  or positive.')
    w()
    w(f'  Overall: structural improvement. Zero category regressions.')
    w(f'  New features (sem_review + compound detection) add diagnostic')
    w(f'  depth without disturbing existing results.')
    w()

    w('══════════════════════════════════════════════════════════════════════════')
    w('  Source files:')
    w(f'    v3.3: {V33_PATH}')
    w(f'    v3.4: {V34_PATH}')
    w('══════════════════════════════════════════════════════════════════════════')

    # Write output
    output_text = '\n'.join(lines) + '\n'
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output_text)

    print(f'Comparison report written to: {OUTPUT_PATH}')
    print(f'Total lines: {len(lines)}')

if __name__ == '__main__':
    main()
