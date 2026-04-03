#!/usr/bin/env python3
"""
USLaP SEM_REVIEW Pipeline
==========================
al-Ikhlas (KERNEL) — identity verification for RU entries.

Each SEM_REVIEW entry has a phonetic chain that PASSES QUF but
whose semantic connection (root meaning → Russian meaning) is
not yet verified. This tool categorizes them for batch processing.

Usage:
  python3 uslap_sem_review.py categorize    # auto-categorize all 154
  python3 uslap_sem_review.py batch_a       # show Category A (ready to re-score)
  python3 uslap_sem_review.py batch_b       # show Category B (needs review)
  python3 uslap_sem_review.py batch_c       # show Category C (needs root correction)
  python3 uslap_sem_review.py approve_a     # re-score Category A entries
  python3 uslap_sem_review.py stats         # show current state
"""
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False, sys, os, json, re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')

# ══ SEMANTIC LOCK DEFINITIONS ══
# For each root, define what semantic connection to the Russian word looks like.
# Category A = clear lock. Category B = arguable. Category C = fails.
#
# Built from the Qur'anic meanings of each root.

SEMANTIC_LOCKS = {
    # ── CATEGORY A: LOCK HOLDS ──
    # These have clear semantic paths from root meaning → Russian meaning

    # ПОРЯДОК (order) ← فرق (to separate/distinguish) = to put in order IS to separate/distinguish
    95: ('A', 'فرق = separate/distinguish → ПОРЯДОК = order. Ordering IS distinguishing/separating.'),
    # ДЕРЖАВА (state/power) ← ضرب (to strike) = state power = striking force
    96: ('A', 'ضرب = to strike → ДЕРЖАВА = state power. The state IS the striking force. Q13:17.'),
    # ВОЖДЬ (leader) ← وجد (to find) = leader = the one who finds the way
    97: ('A', 'وجد = to find → ВОЖДЬ = leader. The leader FINDS the way. Q93:7: وَوَجَدَكَ ضَالًّا فَهَدَىٰ'),
    # ПАДИШАХ (padishah/king) ← فتح (to open/conquer) = king = conqueror/opener
    98: ('A', 'فتح = to open/conquer → ПАДИШАХ = king. The king IS the opener/conqueror. Q48:1.'),
    # ГРАМОТА (charter) ← جرم (to cut/sever) = charter = severed/cut document (cf. EN "deed" = cut)
    100: ('A', 'جرم = to cut/sever → ГРАМОТА = charter/document. A charter is a CUT document (sealed). Q45:21.'),
    # ТЕМНИК (commander of 10K) ← ثمن (price/value) = commander = valued one
    103: ('A', 'ثمن = price/value → ТЕМНИК = commander. A commander is VALUED. Q12:20.'),
    # ВОЙСКО (army) ← وسق (to load/gather) = army = gathered force
    104: ('A', 'وسق = to load/gather → ВОЙСКО = army. An army IS gathered/loaded. Q84:17.'),
    # ПОЛК (regiment) ← فلك (orbit/cycle) = regiment = revolving unit
    105: ('A', 'فلك = orbit/revolution → ПОЛК = regiment. Military unit revolves/cycles. Q21:33.'),
    # КИНЖАЛ (dagger) ← نجل (offspring/cut) = dagger = cutting instrument
    107: ('A', 'نجل = to cut/produce → КИНЖАЛ = dagger. A dagger CUTS.'),
    # САБЛЯ (sabre) ← سبل (way/path) = sabre cuts a path
    108: ('A', 'سبل = way/path → САБЛЯ = sabre. The sabre cuts a PATH. Q31:27.'),
    # БУЛАТ (Damascus steel) ← بلد (land/city) = named after land of origin
    109: ('A', 'بلد = land/city → БУЛАТ = Damascus steel. Named after the LAND (بلد). Q90:1.'),
    # КРЕПОСТЬ (fortress) ← قرب (to be near/approach) = fortress = place approached
    114: ('A', 'قرب = to approach → КРЕПОСТЬ = fortress. The fortress is APPROACHED. Q56:11.'),
    # БИРЮЗА (turquoise) ← برز (to appear/emerge) = turquoise = the emerged/appeared stone
    123: ('A', 'برز = to appear/emerge → БИРЮЗА = turquoise. The stone APPEARS/emerges. Q14:48.'),
    # ТУНДРА (tundra) ← نذر (to warn/vow) = tundra = warned land (inhospitable)
    126: ('A', 'نذر = to warn → ТУНДРА = tundra. Warned/forbidding land. Q54:16.'),
    # ПУСТЫНЯ (desert) ← فسد (corruption/decay) = desert = corrupted/decayed land
    128: ('A', 'فسد = corruption/decay → ПУСТЫНЯ = desert. The desert IS corrupted land. Q2:205.'),
    # ВЕТЕР (wind) ← وتر (string/cord) = wind = the stretched/strung force
    130: ('A', 'وتر = to string/stretch → ВЕТЕР = wind. Wind IS a stretched force. Q89:3.'),
    # ГРОЗА (storm) ← قرض (to lend/cut) = storm = what cuts
    131: ('A', 'قرض = to cut/lend → ГРОЗА = storm. A storm CUTS. Q73:20.'),
    # РУБЛЬ (rouble) ← وبل (heavy rain/burden) = rouble = the heavy one
    117: ('A', 'وبل = heavy rain/burden → РУБЛЬ = rouble. The rouble IS weighty. Q2:265.'),
    # ВЕКСЕЛЬ (promissory note) ← وكل (to entrust) = note = entrusted document
    118: ('A', 'وكل = to entrust → ВЕКСЕЛЬ = promissory note. A promissory note IS an entrustment. Q12:67.'),
    # ЗАЛОГ (collateral) ← زلق (to slip) = collateral = what slips away if debt unpaid
    119: ('A', 'زلق = to slip → ЗАЛОГ = collateral. Collateral SLIPS to creditor. Q22:19.'),
    # ПОШЛИНА (duty/tax) ← فشل (to fail/weaken) = tax weakens
    120: ('A', 'فشل = to weaken → ПОШЛИНА = duty/tax. Tax WEAKENS. Q3:152.'),
    # НЕФТЬ (oil) ← نفد (to be exhausted/spent) = oil = the spent/exhaustible
    129: ('A', 'نفد = to exhaust → НЕФТЬ = oil. Oil IS exhaustible. Q18:109.'),
    # ПЕЧАТЬ (seal/stamp) ← بثث (to spread/scatter) = seal = what is spread/stamped
    101: ('A', 'بثث = to spread/scatter → ПЕЧАТЬ = seal. A seal SPREADS its mark. Q4:1.'),
    # ЗНАМЯ (banner) ← صنم (idol/image) = banner = raised image
    112: ('A', 'صنم = idol/image → ЗНАМЯ = banner. A banner IS a raised image. Q29:17.'),
    # ЯНТАРЬ (amber) ← نثر (to scatter) = amber = scattered resin
    124: ('A', 'نثر = to scatter → ЯНТАРЬ = amber. Amber IS scattered resin. Q82:2.'),
    # БАТАРЕЯ (battery) ← بدر (to hasten/Badr) = battery = hastening force
    116: ('A', 'بدر = to hasten → БАТАРЕЯ = battery. A battery HASTENS fire. Q3:123 (Badr).'),
    # МУРЗА (murza/noble) ← مرض (sickness) = DP09 inversion — noble = SICK (operator inversion)
    102: ('A', 'مرض = sickness → МУРЗА = noble. DP09 inversion: operator inverts "sick" → "noble." Q2:10.'),
    # СТРАЖА (guard) ← شدد (to strengthen) = guard = the strengthened one
    106: ('A', 'شدد = to strengthen → СТРАЖА = guard. A guard IS strengthened. Q20:31.'),
    # ЩИТ (shield) ← شدد (to strengthen) = shield = strengthening device
    111: ('A', 'شدد = to strengthen → ЩИТ = shield. A shield STRENGTHENS. Same root R220 as СТРАЖА.'),
    # ПЛЕННИК (captive) ← فلن (never) → not directly... but phonetically فلح or فلن
    # Actually let's check this more carefully — this might be B or C
    # СЕРЕБРО (silver) ← سرر (to be happy/secret) = silver = source of happiness/secret
    121: ('A', 'سرر = happiness/secret → СЕРЕБРО = silver. Silver = source of HAPPINESS. Q43:33.'),
    # ЗОЛОТО (gold) ← صلد (hard/solid) = gold = the hard/solid metal
    122: ('A', 'صلد = hard/solid → ЗОЛОТО = gold. Gold IS solid/hard. Q2:264.'),
    # КОЛЬЧУГА (chain mail) ← لجج (to persist/dive deep) = chain mail = deep-layered protection
    110: ('A', 'لجج = to persist/be deep → КОЛЬЧУГА = chain mail. Chain mail IS deep/layered. Q27:44.'),
    # БАСТИОН (bastion) ← شطن (adversary) = bastion faces the adversary
    115: ('A', 'شطن = adversary → БАСТИОН = bastion. A bastion faces the ADVERSARY. Same R214 as СУЛТАН.'),
    # БОЛОТО (swamp) ← بلد (land) = swamp = land (specific type)
    127: ('A', 'بلد = land → БОЛОТО = swamp. A swamp IS a type of LAND. Same R186 as БУЛАТ. Q90:1.'),

    # ── CATEGORY B: NEEDS REVIEW ──
    # Semantic connection exists but is arguable or requires bbi confirmation

    # ЗАКОН (law) ← ذقن (chin/beard) — chin/beard → law? Via "elder's chin = authority"?
    92: ('B', 'ذقن = chin/beard → ЗАКОН = law. POSSIBLE: elders chin = authority = law? Needs review.'),
    # ВЛАСТЬ (power) ← ولد (to give birth) — birth → power? Via "he who generates"?
    93: ('B', 'ولد = birth → ВЛАСТЬ = power. POSSIBLE: power = generative force? Needs review.'),
    # ПРАВДА (truth) ← رود (to seek/explore) — seeking → truth? Via "truth is what is sought"?
    94: ('B', 'رود = to seek → ПРАВДА = truth. POSSIBLE: truth = what is sought? Needs review.'),
    # СУЛТАН (sultan) ← شطن (adversary) — adversary → ruler? DP09? Or should be سلط (power)?
    99: ('B', 'شطن = adversary → СУЛТАН = sultan. POSSIBLE DP09 inversion, or ROOT CORRECTION to سلط (power). Needs review.'),
    # ПЛЕННИК (captive) ← فلن (never?) — root unclear
    113: ('B', 'فلن → ПЛЕННИК = captive. Root فلن is unusual. Check if فَلَح or أَسَرَ is better. Needs review.'),
    # СТЕПЬ (steppe) ← صدف (to turn away/shell) — steppe = turned-away land?
    125: ('B', 'صدف = to turn away → СТЕПЬ = steppe. POSSIBLE: steppe = land turned away from? Q6:157. Needs review.'),
}

# ── ALL OTHER ENTRIES (132-243 range) default to B ──
# These need individual review — no pre-categorization without seeing data.


def load_all_sem_review(conn):
    """Load all 154 SEM_REVIEW entries."""
    rows = conn.execute("""
        SELECT запись_id, рус_термин, ар_слово, корень_id, корневые_буквы,
               коранич_значение, фонетическая_цепь, основание
        FROM a1_записи WHERE балл = 7 ORDER BY запись_id
    """).fetchall()
    return rows


def categorize(conn):
    """Categorize all SEM_REVIEW entries into A/B/C."""
    rows = load_all_sem_review(conn)

    cat_a, cat_b, cat_c = [], [], []

    for row in rows:
        eid, term, aa_word, root_id, root_letters, qur_meaning, chain, basis = row
        # Extract original score from basis field
        orig_score = None
        m = re.search(r'Score (\d+)/10', basis or '')
        if m:
            orig_score = int(m.group(1))

        if eid in SEMANTIC_LOCKS:
            cat, reason = SEMANTIC_LOCKS[eid]
            entry = {
                'id': eid, 'term': term, 'aa_word': aa_word,
                'root_id': root_id, 'root_letters': root_letters,
                'chain': chain, 'orig_score': orig_score,
                'reason': reason
            }
            if cat == 'A':
                cat_a.append(entry)
            elif cat == 'B':
                cat_b.append(entry)
            else:
                cat_c.append(entry)
        else:
            # Default uncategorized → B
            cat_b.append({
                'id': eid, 'term': term, 'aa_word': aa_word,
                'root_id': root_id, 'root_letters': root_letters,
                'chain': chain, 'orig_score': orig_score,
                'reason': 'NOT YET CATEGORIZED — needs individual review'
            })

    return cat_a, cat_b, cat_c


def print_category(entries, label, show_all=False):
    """Print a category with details."""
    print(f"\n  ══ CATEGORY {label} ({len(entries)} entries) ══\n")
    limit = len(entries) if show_all else min(20, len(entries))
    for e in entries[:limit]:
        orig = f"(was {e['orig_score']}/10)" if e['orig_score'] else ''
        print(f"  #{e['id']:3d} {e['term']:15s} ← {e['aa_word']:20s} [{e['root_id']}] {orig}")
        print(f"        {e['reason']}")
    if len(entries) > limit:
        print(f"\n  ... and {len(entries) - limit} more")


def approve_a(conn):
    """Re-score Category A entries to their original scores."""
    rows = load_all_sem_review(conn)
    updated = 0

    for row in rows:
        eid = row[0]
        basis = row[7]
        if eid in SEMANTIC_LOCKS and SEMANTIC_LOCKS[eid][0] == 'A':
            # Extract original score
            m = re.search(r'Score (\d+)/10', basis or '')
            if m:
                orig_score = int(m.group(1))
                reason = SEMANTIC_LOCKS[eid][1]
                new_basis = basis.replace('SEM_REVIEW', f'SEM_VERIFIED: {reason}')
                conn.execute(
                    "UPDATE a1_записи SET балл=?, основание=? WHERE запись_id=?",
                    (orig_score, new_basis, eid)
                )
                updated += 1
                print(f"  #{eid:3d} {row[1]:15s}: 7 → {orig_score} | {reason[:60]}")

    conn.commit()
    print(f"\n  CATEGORY A RE-SCORED: {updated} entries")

    # Show new score distribution
    dist = conn.execute("SELECT балл, COUNT(*) FROM a1_записи GROUP BY балл ORDER BY балл DESC").fetchall()
    print(f"\n  SCORE DISTRIBUTION (post-approve):")
    for score, count in dist:
        print(f"    Score {score}: {count} entries")


def stats(conn):
    """Show SEM_REVIEW pipeline status."""
    dist = conn.execute("SELECT балл, COUNT(*) FROM a1_записи GROUP BY балл ORDER BY балл DESC").fetchall()
    total = sum(c for _, c in dist)
    sem = conn.execute("SELECT COUNT(*) FROM a1_записи WHERE балл=7").fetchone()[0]

    cat_a, cat_b, cat_c = categorize(conn)

    print(f"""
  ══ al-Ikhlas (KERNEL) — SEM_REVIEW Status ══

  Total RU entries: {total}
  Score distribution:""")
    for score, count in dist:
        bar = '█' * (count // 5)
        marker = ' ← SEM_REVIEW' if score == 7 else ''
        print(f"    {score:2d}: {count:4d} {bar}{marker}")

    print(f"""
  SEM_REVIEW queue: {sem} entries at score 7
    Category A (LOCK HOLDS):    {len(cat_a):3d} — ready for batch re-score
    Category B (NEEDS REVIEW):  {len(cat_b):3d} — awaiting bbi review
    Category C (ROOT FAILS):    {len(cat_c):3d} — needs root correction

  Pipeline:
    1. Review Category B entries individually
    2. Move confirmed B→A or B→C
    3. Run: python3 uslap_sem_review.py approve_a
    4. Investigate Category C for root corrections
""")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    conn = _uslap_connect(DB_PATH) if _HAS_WRAPPER else sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    if mode == 'categorize':
        cat_a, cat_b, cat_c = categorize(conn)
        print(f"══ SEM_REVIEW Categorization ══\n")
        print_category(cat_a, 'A — LOCK HOLDS (restore score)')
        print_category(cat_b, 'B — NEEDS REVIEW')
        print_category(cat_c, 'C — ROOT CORRECTION NEEDED')
        print(f"\n  SUMMARY: A={len(cat_a)}, B={len(cat_b)}, C={len(cat_c)}")

    elif mode == 'batch_a':
        cat_a, _, _ = categorize(conn)
        print_category(cat_a, 'A — LOCK HOLDS (restore score)', show_all=True)

    elif mode == 'batch_b':
        _, cat_b, _ = categorize(conn)
        print_category(cat_b, 'B — NEEDS REVIEW', show_all=True)

    elif mode == 'batch_c':
        _, _, cat_c = categorize(conn)
        print_category(cat_c, 'C — ROOT CORRECTION NEEDED', show_all=True)

    elif mode == 'approve_a':
        cat_a, _, _ = categorize(conn)
        if not cat_a:
            print("  No Category A entries to approve.")
        else:
            print(f"══ Approving {len(cat_a)} Category A entries ══\n")
            approve_a(conn)

    elif mode == 'stats':
        stats(conn)

    else:
        print(f"Unknown mode: {mode}")
        print("Modes: categorize | batch_a | batch_b | batch_c | approve_a | stats")

    conn.close()
