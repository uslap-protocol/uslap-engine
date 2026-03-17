#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP BITIG — al-Falaq (113) — SEED
قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ — "Say: I seek refuge in the Lord of the daybreak" (Q113:1)

The SEED splits open (فَلَق = to split/cleave), revealing what was hidden.
This tool manages the Bitig Restoration DB — ORIG2 entries, degradation tracking,
convergence mapping, and verification.

Commands:
    status              — Full Bitig DB status
    search TERM         — Search bitig_a1_entries + degradation + convergence
    degrade             — List all degradation cases (bitig_degradation_register)
    converge            — List all ORIG1+ORIG2 convergence points
    pending             — List PENDING_VERIFICATION entries
    verify ID           — Show verification criteria for a specific entry
    fields              — Semantic field distribution
    add                 — Interactive entry addition (prints template)
    scan                — Scan for potential new degradation/convergence cases

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
import sys
import os

DB_PATH = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_status():
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) FROM bitig_a1_entries").fetchone()[0]
    confirmed = conn.execute(
        "SELECT COUNT(*) FROM bitig_a1_entries WHERE status='CONFIRMED'"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM bitig_a1_entries WHERE status='PENDING_VERIFICATION'"
    ).fetchone()[0]
    degradation = conn.execute(
        "SELECT COUNT(*) FROM bitig_degradation_register"
    ).fetchone()[0]
    convergence = conn.execute(
        "SELECT COUNT(*) FROM bitig_convergence_register"
    ).fetchone()[0]
    conv_confirmed = conn.execute(
        "SELECT COUNT(*) FROM bitig_convergence_register WHERE status='CONFIRMED'"
    ).fetchone()[0]
    conv_candidate = conn.execute(
        "SELECT COUNT(*) FROM bitig_convergence_register WHERE status='CANDIDATE'"
    ).fetchone()[0]
    blacklist = conn.execute(
        "SELECT COUNT(*) FROM contamination_blacklist"
    ).fetchone()[0]

    # Semantic field breakdown
    fields = conn.execute(
        "SELECT semantic_field, COUNT(*) as c FROM bitig_a1_entries "
        "GROUP BY semantic_field ORDER BY c DESC"
    ).fetchall()

    # Degradation type breakdown
    deg_types = conn.execute(
        "SELECT degradation_type, COUNT(*) as c FROM bitig_degradation_register "
        "GROUP BY degradation_type ORDER BY c DESC LIMIT 10"
    ).fetchall()

    last_id = conn.execute(
        "SELECT MAX(entry_id) FROM bitig_a1_entries"
    ).fetchone()[0]

    print("═══════════════════════════════════════════════════════════")
    print("  BITIG RESTORATION DB — al-Falaq (SEED)")
    print("═══════════════════════════════════════════════════════════")
    print(f"  Total entries:        {total}")
    print(f"  CONFIRMED:            {confirmed}")
    print(f"  PENDING_VERIFICATION: {pending}")
    print(f"  Last entry_id:        {last_id}")
    print(f"  Degradation cases:    {degradation}")
    print(f"  Convergence points:   {convergence} ({conv_confirmed} confirmed, {conv_candidate} candidates)")
    print(f"  Blacklist entries:    {blacklist}")
    print()
    print("  SEMANTIC FIELDS:")
    for f in fields:
        bar = "█" * (f['c'] // 2) if f['c'] > 1 else "▏"
        print(f"    {f['semantic_field']:20s} {f['c']:3d}  {bar}")
    print()
    print("  TOP DEGRADATION TYPES:")
    for d in deg_types:
        print(f"    {d['degradation_type']:30s} {d['c']:2d}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_search(term):
    conn = get_conn()
    term_lower = term.lower()

    print(f"\n  Searching Bitig DB for: {term}")
    print("  " + "─" * 50)

    # Search bitig_a1_entries
    rows = conn.execute(
        "SELECT * FROM bitig_a1_entries "
        "WHERE LOWER(orig2_term) LIKE ? "
        "OR LOWER(downstream_forms) LIKE ? "
        "OR LOWER(notes) LIKE ? "
        "OR LOWER(kashgari_attestation) LIKE ?",
        (f"%{term_lower}%",) * 4
    ).fetchall()

    if rows:
        print(f"\n  BITIG_A1_ENTRIES ({len(rows)} hits):")
        for r in rows:
            print(f"    #{r['entry_id']:3d} | {r['orig2_term']:15s} | {r['semantic_field']:12s} | {r['status']}")
            if r['downstream_forms']:
                print(f"          ↳ {r['downstream_forms'][:80]}")
    else:
        print("\n  BITIG_A1_ENTRIES: no hits")

    # Search degradation register
    deg = conn.execute(
        "SELECT * FROM bitig_degradation_register "
        "WHERE LOWER(bitig_original) LIKE ? "
        "OR LOWER(downstream_form) LIKE ? "
        "OR LOWER(original_meaning) LIKE ? "
        "OR LOWER(degraded_meaning) LIKE ?",
        (f"%{term_lower}%",) * 4
    ).fetchall()

    if deg:
        print(f"\n  DEGRADATION_REGISTER ({len(deg)} hits):")
        for d in deg:
            print(f"    {d['deg_id']} | {d['bitig_original'][:20]:20s} → {d['downstream_form'][:20]:20s}")
            print(f"          {d['original_meaning'][:40]} → {d['degraded_meaning'][:40]}")
            print(f"          TYPE: {d['degradation_type']}")

    # Search convergence register
    conv = conn.execute(
        "SELECT * FROM bitig_convergence_register "
        "WHERE LOWER(orig2_term) LIKE ? "
        "OR LOWER(orig1_root) LIKE ? "
        "OR LOWER(shared_semantics) LIKE ?",
        (f"%{term_lower}%",) * 3
    ).fetchall()

    if conv:
        print(f"\n  CONVERGENCE_REGISTER ({len(conv)} hits):")
        for c in conv:
            print(f"    {c['conv_id']} | ORIG2: {c['orig2_term'][:20]:20s} ↔ ORIG1: {c['orig1_root'][:20]:20s}")
            print(f"          Shared: {c['shared_semantics'][:60]}")
            print(f"          Status: {c['status']} | Type: {c['convergence_type']}")

    # Search blacklist
    bl = conn.execute(
        "SELECT * FROM contamination_blacklist "
        "WHERE LOWER(contaminated_term) LIKE ? "
        "OR LOWER(correct_translation) LIKE ?",
        (f"%{term_lower}%",) * 2
    ).fetchall()

    if bl:
        print(f"\n  ⛔ BLACKLIST WARNINGS ({len(bl)} hits):")
        for b in bl:
            print(f"    {b['bl_id']}: {b['contaminated_term']}")
            print(f"      NEVER USE: \"{b['contaminated_translation']}\"")
            print(f"      CORRECT:   {b['correct_translation']}")

    if not rows and not deg and not conv and not bl:
        print("\n  No results found in any Bitig table.")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DEGRADE — List degradation cases
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_degrade():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM bitig_degradation_register ORDER BY deg_id"
    ).fetchall()

    print(f"\n  BITIG DEGRADATION REGISTER — {len(rows)} entries")
    print("  " + "═" * 70)

    for r in rows:
        orig = r['bitig_original'][:22]
        ds = r['downstream_form'][:22]
        print(f"  {r['deg_id']} | {orig:22s} → {ds:22s} | {r['degradation_type']}")

    # Type summary
    print("\n  TYPE SUMMARY:")
    types = conn.execute(
        "SELECT degradation_type, COUNT(*) as c "
        "FROM bitig_degradation_register GROUP BY degradation_type ORDER BY c DESC"
    ).fetchall()
    for t in types:
        print(f"    {t['degradation_type']:30s} × {t['c']}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERGE — List convergence points
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_converge():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM bitig_convergence_register ORDER BY conv_id"
    ).fetchall()

    print(f"\n  BITIG CONVERGENCE REGISTER — {len(rows)} entries")
    print("  " + "═" * 70)

    for r in rows:
        status_mark = "✓" if r['status'] == 'CONFIRMED' else "?"
        print(f"  {r['conv_id']} [{status_mark}] ORIG2: {r['orig2_term'][:18]:18s} ↔ ORIG1: {r['orig1_root'][:18]:18s}")
        print(f"       Semantics: {r['shared_semantics'][:60]}")
        print(f"       Match: {r['consonantal_match'][:60]}")
        print(f"       Type: {r['convergence_type']:20s}  Qur'an: {r['quranic_ref'] or 'N/A'}")
        print()

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PENDING — List entries needing verification
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_pending():
    conn = get_conn()
    rows = conn.execute(
        "SELECT entry_id, orig2_term, semantic_field, kashgari_attestation "
        "FROM bitig_a1_entries WHERE status='PENDING_VERIFICATION' "
        "ORDER BY semantic_field, entry_id"
    ).fetchall()

    print(f"\n  PENDING VERIFICATION — {len(rows)} entries")
    print("  " + "═" * 70)
    print(f"  {'ID':>4s} | {'ORIG2 TERM':15s} | {'FIELD':12s} | ATTESTATION SOURCE")
    print("  " + "─" * 70)

    current_field = None
    for r in rows:
        if r['semantic_field'] != current_field:
            current_field = r['semantic_field']
            print(f"\n  ── {current_field} ──")

        att = r['kashgari_attestation'] or ''
        # Extract source type from attestation
        if 'Kashgari' in att or 'Dīwān' in att:
            src = "Kashgari"
        elif 'ЭСТЯ' in att or 'Sevortyan' in att:
            src = "ЭСТЯ"
        elif 'Baskakov' in att or 'Баскаков' in att:
            src = "Baskakov"
        else:
            src = "Turkic-attested (generic)"

        print(f"  {r['entry_id']:4d} | {r['orig2_term']:15s} | {r['semantic_field']:12s} | {src}")

    # Verification criteria reminder
    print("\n  ── ORIG2 QUF GATE ──")
    print("  Q: Attested in Kashgari / Orkhon / Irk Bitig / Navoi / Talas")
    print("  U: Phonetic chain maps through M1 shifts (S01-S26)")
    print("  F: Direction ALWAYS Bitig → downstream")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY — Show verification details for one entry
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_verify(entry_id):
    conn = get_conn()
    r = conn.execute(
        "SELECT * FROM bitig_a1_entries WHERE entry_id = ?", (entry_id,)
    ).fetchone()

    if not r:
        print(f"  Entry #{entry_id} not found.")
        conn.close()
        return

    print(f"\n  VERIFICATION REPORT — #{r['entry_id']}")
    print("  " + "═" * 50)
    print(f"  Term:     {r['orig2_term']}")
    print(f"  Script:   {r['orig2_script'] or 'N/A'}")
    print(f"  Field:    {r['semantic_field']}")
    print(f"  Status:   {r['status']}")
    print(f"  Score:    {r['score']}")

    # Q gate
    att = r['kashgari_attestation'] or ''
    has_kashgari = 'Kashgari' in att or 'Dīwān' in att or 'Кашгари' in att
    has_orkhon = 'Orkhon' in att or 'Орхон' in att
    has_estya = 'ЭСТЯ' in att or 'Sevortyan' in att
    has_baskakov = 'Baskakov' in att or 'Баскаков' in att

    q_pass = has_kashgari or has_orkhon or has_estya or has_baskakov
    print(f"\n  Q GATE: {'PASS' if q_pass else 'FAIL'}")
    print(f"    Kashgari: {'✓' if has_kashgari else '✗'}")
    print(f"    Orkhon:   {'✓' if has_orkhon else '✗'}")
    print(f"    ЭСТЯ:     {'✓' if has_estya else '✗'}")
    print(f"    Baskakov:  {'✓' if has_baskakov else '✗'}")

    # U gate
    chain = r['phonetic_chain'] or ''
    u_pass = len(chain) > 5  # Has documented phonetic chain
    print(f"\n  U GATE: {'PASS' if u_pass else 'NEEDS DOCUMENTATION'}")
    print(f"    Chain: {chain[:80] if chain else 'Not documented'}")

    # F gate
    ds = r['downstream_forms'] or ''
    f_pass = len(ds) > 3  # Has documented downstream forms
    print(f"\n  F GATE: {'PASS' if f_pass else 'NEEDS DOCUMENTATION'}")
    print(f"    Downstream: {ds[:80] if ds else 'Not documented'}")

    # Check degradation
    deg = conn.execute(
        "SELECT * FROM bitig_degradation_register "
        "WHERE LOWER(bitig_original) LIKE ?",
        (f"%{r['orig2_term'].lower()}%",)
    ).fetchall()
    if deg:
        print(f"\n  DEGRADATION: {len(deg)} case(s)")
        for d in deg:
            print(f"    {d['deg_id']}: {d['degradation_type']}")

    # Check convergence
    conv = conn.execute(
        "SELECT * FROM bitig_convergence_register "
        "WHERE LOWER(orig2_term) LIKE ?",
        (f"%{r['orig2_term'].lower()}%",)
    ).fetchall()
    if conv:
        print(f"\n  CONVERGENCE: {len(conv)} point(s)")
        for c in conv:
            print(f"    {c['conv_id']}: ↔ {c['orig1_root']} ({c['convergence_type']})")

    overall = "PASS" if (q_pass and u_pass and f_pass) else "INCOMPLETE"
    print(f"\n  OVERALL: {overall}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# FIELDS — Semantic field distribution
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_fields():
    conn = get_conn()
    rows = conn.execute(
        "SELECT semantic_field, COUNT(*) as c, "
        "SUM(CASE WHEN status='CONFIRMED' THEN 1 ELSE 0 END) as confirmed, "
        "SUM(CASE WHEN status='PENDING_VERIFICATION' THEN 1 ELSE 0 END) as pending "
        "FROM bitig_a1_entries GROUP BY semantic_field ORDER BY c DESC"
    ).fetchall()

    print(f"\n  SEMANTIC FIELD DISTRIBUTION")
    print("  " + "═" * 60)
    print(f"  {'FIELD':20s} {'TOTAL':>5s} {'CONF':>5s} {'PEND':>5s}  CHART")
    print("  " + "─" * 60)

    for r in rows:
        conf_bar = "█" * (r['confirmed'] // 2)
        pend_bar = "░" * (r['pending'] // 2)
        print(f"  {r['semantic_field']:20s} {r['c']:5d} {r['confirmed']:5d} {r['pending']:5d}  {conf_bar}{pend_bar}")

    total = sum(r['c'] for r in rows)
    total_conf = sum(r['confirmed'] for r in rows)
    total_pend = sum(r['pending'] for r in rows)
    print("  " + "─" * 60)
    print(f"  {'TOTAL':20s} {total:5d} {total_conf:5d} {total_pend:5d}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ADD — Print entry template
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_add():
    conn = get_conn()
    last_id = conn.execute("SELECT MAX(entry_id) FROM bitig_a1_entries").fetchone()[0]
    next_id = (last_id or 0) + 1
    conn.close()

    print(f"\n  NEW BITIG ENTRY TEMPLATE — next_id: {next_id}")
    print("  " + "═" * 50)
    print(f"""
  INSERT INTO bitig_a1_entries (
    entry_id, score, orig2_term, orig2_script, root_letters,
    kashgari_attestation, ibn_sina_attestation, modern_reflexes,
    navoi_attestation, downstream_forms, phonetic_chain,
    semantic_field, dispersal_range, status, notes
  ) VALUES (
    {next_id},        -- entry_id
    0,                -- score (set after QUF)
    'TERM',           -- orig2_term (Bitig original)
    '𐰀𐰀𐰀',           -- orig2_script (Old Turkic if known)
    'X-X-X',          -- root_letters
    'Kashgari: ...',  -- kashgari_attestation (Q gate)
    NULL,             -- ibn_sina_attestation
    NULL,             -- modern_reflexes
    NULL,             -- navoi_attestation
    'RU: ...',        -- downstream_forms (F gate)
    'chain...',       -- phonetic_chain (U gate)
    'FIELD',          -- semantic_field (from: {', '.join(VALID_FIELDS)})
    NULL,             -- dispersal_range
    'CONFIRMED',      -- status
    'notes'           -- notes
  );""")


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN — Quick scan for potential new cases
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_scan():
    conn = get_conn()

    # Entries without degradation records that might have degradation
    print("\n  POTENTIAL UNDOCUMENTED DEGRADATION:")
    print("  " + "═" * 60)

    # Get all existing degradation originals
    existing_deg = set()
    for r in conn.execute("SELECT LOWER(bitig_original) FROM bitig_degradation_register"):
        existing_deg.add(r[0])

    # Check bitig entries with downstream forms for potential degradation
    entries = conn.execute(
        "SELECT entry_id, orig2_term, downstream_forms, semantic_field "
        "FROM bitig_a1_entries "
        "WHERE downstream_forms IS NOT NULL AND downstream_forms != '' "
        "ORDER BY entry_id"
    ).fetchall()

    undoc_count = 0
    for e in entries:
        term_lower = e['orig2_term'].lower()
        # Skip if already in degradation register
        if any(term_lower in d for d in existing_deg):
            continue
        # Flag entries in semantic fields that commonly show degradation
        if e['semantic_field'] in ('GOVERNANCE', 'MILITARY', 'DWELLING', 'PEOPLE'):
            undoc_count += 1
            if undoc_count <= 20:
                print(f"  #{e['entry_id']:3d} | {e['orig2_term']:15s} | {e['semantic_field']:12s} | {e['downstream_forms'][:40]}")

    if undoc_count > 20:
        print(f"  ... and {undoc_count - 20} more")
    elif undoc_count == 0:
        print("  No undocumented cases found in high-risk fields.")

    print(f"\n  Total unchecked in high-risk fields: {undoc_count}")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DISPERSAL — Show dispersal network stats
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_dispersal():
    conn = get_conn()

    print("\n  BITIG DISPERSAL NETWORK")
    print("  " + "═" * 60)

    total_edges = conn.execute("SELECT COUNT(*) FROM bitig_dispersal_edges").fetchone()[0]
    total_entries = conn.execute("SELECT COUNT(*) FROM bitig_a1_entries").fetchone()[0]

    print(f"  Total entries:    {total_entries}")
    print(f"  Total edges:      {total_edges}")
    print(f"  Avg connectivity: {total_edges/total_entries:.1f} edges/entry")

    print(f"\n  BY TARGET LANGUAGE:")
    for r in conn.execute(
        "SELECT target_language, COUNT(*) as cnt, "
        "SUM(CASE WHEN meaning_preserved=0 THEN 1 ELSE 0 END) as degraded "
        "FROM bitig_dispersal_edges GROUP BY target_language ORDER BY cnt DESC"
    ):
        pct_deg = (r['degraded'] * 100 // r['cnt']) if r['cnt'] else 0
        bar_ok = "█" * ((r['cnt'] - r['degraded']) // 3)
        bar_deg = "░" * (r['degraded'] // 3)
        print(f"    {r['target_language']:12s}: {r['cnt']:3d} edges ({r['degraded']:2d} degraded = {pct_deg}%)  {bar_ok}{bar_deg}")

    print(f"\n  BY DISPERSAL RANGE:")
    for r in conn.execute(
        "SELECT dispersal_range, COUNT(*) as cnt "
        "FROM bitig_a1_entries GROUP BY dispersal_range ORDER BY cnt DESC LIMIT 8"
    ):
        bar = "█" * (r['cnt'] // 3)
        print(f"    {r['dispersal_range']:30s}: {r['cnt']:3d}  {bar}")

    # Most connected entries
    print(f"\n  MOST CONNECTED ENTRIES:")
    for r in conn.execute(
        "SELECT orig2_term, COUNT(*) as edge_cnt "
        "FROM bitig_dispersal_edges GROUP BY bitig_entry_id "
        "ORDER BY edge_cnt DESC LIMIT 10"
    ):
        print(f"    {r['orig2_term']:20s}: {r['edge_cnt']} languages")

    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════

VALID_FIELDS = [
    "MILITARY", "GOVERNANCE", "DWELLING", "FOOD", "CLOTHING", "CRAFT",
    "TRADE", "EQUESTRIAN", "NATURE", "HOUSEHOLD", "PEOPLE", "LAND",
    "KINSHIP", "SCRIPT", "THEOLOGY", "COLOR", "TIME", "AGRICULTURE",
    "MEDICINE", "SOCIAL"
]

USAGE = """
USLaP BITIG — al-Falaq (SEED) — Bitig Restoration DB Manager

Usage:
  python3 uslap_bitig.py status              Full DB status
  python3 uslap_bitig.py search TERM         Search all Bitig tables
  python3 uslap_bitig.py degrade             List all degradation cases
  python3 uslap_bitig.py converge            List convergence points
  python3 uslap_bitig.py pending             List PENDING_VERIFICATION entries
  python3 uslap_bitig.py verify ID           Verification report for entry
  python3 uslap_bitig.py fields              Semantic field distribution
  python3 uslap_bitig.py add                 Print new entry template
  python3 uslap_bitig.py scan                Scan for undocumented cases
  python3 uslap_bitig.py dispersal           Dispersal network stats
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        cmd_status()
    elif cmd == "search" and len(sys.argv) > 2:
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "degrade":
        cmd_degrade()
    elif cmd == "converge":
        cmd_converge()
    elif cmd == "pending":
        cmd_pending()
    elif cmd == "verify" and len(sys.argv) > 2:
        cmd_verify(int(sys.argv[2]))
    elif cmd == "fields":
        cmd_fields()
    elif cmd == "add":
        cmd_add()
    elif cmd == "dispersal":
        cmd_dispersal()
    elif cmd == "scan":
        cmd_scan()
    else:
        print(USAGE)
