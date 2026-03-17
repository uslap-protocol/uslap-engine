#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP Batch Runner v2.0
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Runs USLaP_Engine in DRY-RUN mode against a word list.
NO writes to the master Excel file. Discovery only.

Output:
  - Batch Reports/BATCH_REPORT_<timestamp>.json   (full machine-readable results)
  - Batch Reports/BATCH_SUMMARY_<timestamp>.txt   (human-readable summary)

Usage:
  python3 batch_runner.py                      # uses built-in 500-word list
  python3 batch_runner.py my_words.txt         # uses your own word list (one word per line)

THREE-TIER OUTPUT SYSTEM (v2 — corrected per USLaP_BATCH_ENGINE_PROTOCOL):
  ALREADY_IN_LATTICE  — word already confirmed in lattice (skip — no action needed)
  CONFIRMED_HIGH      — score >= 8, Q+U pass, no R11 transposition flag
                        → highest-confidence candidates, review before writing to A1_ENTRIES
  PENDING_REVIEW      — score 5–7, OR transposition flag detected (R11),
                        OR no ORIG1 root found (possible ORIG2 / Kashgari candidate)
                        → human judgment required before any write
  AUTO_REJECTED       — score < 5 OR U-gate fail (consonant(s) unaccounted for)
                        → discard; not a lattice candidate at current analysis level
  CLUSTER_BACKLOG     — words discovered via cluster expansion of CONFIRMED_HIGH roots
                        (engine found these, not in your input list — bonus discoveries)

Key improvements over v1:
  - R11 transposition detection: roots assigned via semantic pull, not phonetic order,
    are automatically demoted to PENDING_REVIEW regardless of score.
  - N15 skeleton priority (R09): C/G/K-R-N pattern forces ق-ر-ن check first.
  - M-prefix parallel path (R08a): words starting with M also tested with مُ stripped.
  - Token count weight reduced (was 3 pts, now 1 pt) — eliminates semantic-first bias.
  - Positional fidelity now contributes 2 pts — correct consonant ORDER rewarded.
"""

import sys
import os
import json
import io
import contextlib
from datetime import datetime
from pathlib import Path

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
# "Code files " has a trailing space — this script lives inside it
THIS_DIR     = Path(__file__).parent                                    # "Code_files/"
WORKSPACE    = Path("/Users/mmsetubal/Documents/USLaP workplace")
MASTER_FILE  = WORKSPACE / "USLaP_Final_Data_Consolidated_Master_v3.xlsx"
OUTPUT_DIR   = Path("/Users/mmsetubal/Documents/USLaP workplace/Batch Reports")

# Add this folder to sys.path so we can import USLaP_Engine
sys.path.insert(0, str(THIS_DIR))

# ─── SUPPRESS ENGINE STDOUT ───────────────────────────────────────────────────
# The engine prints detailed logs per word. In batch mode we suppress this
# and only capture the structured ProcessResult.
class _Suppress:
    """Context manager: silence stdout from engine, capture to string."""
    def __enter__(self):
        self._buf = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self._buf)
        self._redirect.__enter__()
        return self
    def __exit__(self, *args):
        self._redirect.__exit__(*args)
    def text(self):
        return self._buf.getvalue()

# ─── 500 COMMON ENGLISH WORDS (content words only) ───────────────────────────
# Curated from Oxford 3000. Function words excluded (engine already filters them).
# Covers: law, governance, nature, body, family, time, science, society, trade.
# These are prioritised for QUF discovery — they carry high civilisational weight.

WORD_LIST_500 = [
    # GOVERNANCE + LAW
    "rule","govern","law","order","judge","court","justice","crime","punish",
    "king","queen","lord","master","servant","minister","council","senate",
    "nation","state","power","authority","command","control","force","guard",
    "prison","exile","rebel","conquer","empire","colony","treaty","border",
    "tax","tribute","debt","coin","market","trade","merchant","contract",

    # NATURE + COSMOS
    "star","sun","moon","cloud","rain","wind","storm","thunder","lightning",
    "river","sea","ocean","mountain","desert","valley","plain","island","cave",
    "earth","fire","water","air","stone","rock","sand","dust","ice","snow",
    "gold","silver","iron","copper","lead","salt","oil","glass","clay",
    "tree","root","branch","leaf","flower","fruit","seed","grain","corn",
    "forest","field","garden","harvest","soil","shadow","light","dark",

    # BODY + MEDICINE
    "head","face","eye","ear","nose","mouth","tongue","tooth","jaw","neck",
    "shoulder","arm","hand","finger","chest","heart","lung","liver","kidney",
    "stomach","blood","bone","skin","muscle","nerve","brain","spine","heel",
    "wound","fever","cure","medicine","doctor","patient","pain","death",
    "birth","grow","breathe","sleep","dream","wake","hunger","thirst",

    # FAMILY + SOCIETY
    "father","mother","brother","sister","son","daughter","child","family",
    "husband","wife","marriage","widow","orphan","elder","youth","ancestor",
    "tribe","clan","village","city","people","crowd","stranger","neighbor",
    "friend","enemy","guest","host","servant","slave","soldier","priest",

    # FAITH + RITUAL
    "prayer","fast","pilgrimage","sacrifice","offering","altar","temple",
    "sign","miracle","prophet","messenger","angel","spirit","soul","mercy",
    "grace","blessing","curse","judgment","heaven","paradise","fire","torment",
    "faith","trust","peace","truth","wisdom","knowledge","reason","conscience",

    # TIME + CYCLE
    "year","month","week","season","morning","evening","night","dawn","dusk",
    "past","present","future","moment","hour","age","era","generation","century",
    "beginning","end","return","repeat","cycle","calendar","feast","fast",

    # SCIENCE + CRAFT
    "number","count","measure","weight","balance","scale","ratio","angle",
    "circle","square","triangle","center","point","line","surface","volume",
    "medicine","surgery","fever","poison","antidote","herb","compound","formula",
    "metal","forge","weapon","armor","shield","sword","arrow","bow","spear",
    "ship","sail","navigation","compass","horizon","current","anchor","port",
    "road","bridge","gate","wall","tower","palace","prison","market","temple",
    "ink","paper","book","script","seal","letter","word","name","language",

    # TRADE + ECONOMY
    "price","value","profit","loss","interest","loan","pledge","property",
    "buy","sell","exchange","barter","warehouse","caravan","merchant","journey",
    "silk","cotton","wool","leather","spice","pepper","sugar","honey","grain",
    "measure","standard","weight","balance","account","register","archive",

    # COMMON VERBS (high QUF potential)
    "create","form","shape","build","destroy","break","open","close","give",
    "take","bring","send","carry","move","turn","rise","fall","enter","leave",
    "speak","hear","see","know","think","remember","forget","learn","teach",
    "rule","judge","punish","reward","protect","attack","defend","gather",
    "divide","separate","connect","cover","reveal","hide","mark","name","call",

    # QUALITIES + CONDITIONS
    "holy","sacred","pure","clean","corrupt","evil","good","right","wrong",
    "strong","weak","brave","coward","wise","foolish","rich","poor","free","slave",
    "near","far","high","low","deep","shallow","large","small","full","empty",
    "sharp","heavy","light","hard","soft","rough","smooth","clear","dark",
    "new","ancient","first","last","same","different","true","false","certain",

    # MOVEMENT + CONFLICT
    "war","battle","victory","defeat","conquest","siege","retreat","escape",
    "march","advance","surrender","peace","alliance","rebellion","revolution",
    "migration","exile","refuge","settlement","frontier","territory","domain",

    # ADDITIONAL HIGH-PRIORITY TERMS
    "origin","source","root","branch","decay","corruption","restoration",
    "revelation","scripture","verse","chapter","recitation","preservation",
    "throne","crown","scepter","robe","banner","seal","ring","chain",
    "martyr","witness","testimony","covenant","promise","oath","vow",
    "treasury","archive","register","record","history","tradition","custom",
    "census","survey","map","route","distance","direction","boundary",
    "mission","message","envoy","ambassador","spy","agent","network",
    "algebra","algorithm","cipher","secret","code","key","puzzle","riddle",
]

# Remove duplicates while preserving order
seen = set()
WORD_LIST_500 = [w for w in WORD_LIST_500 if not (w in seen or seen.add(w))]


# ─── RESULT SERIALISER ────────────────────────────────────────────────────────

def serialise_result(word: str, result) -> dict:
    """Convert ProcessResult to JSON-safe dict."""
    rec = {
        "word":                word.upper(),
        "existing_entry_id":   result.existing_entry_id,
        "category":            _categorise(result),
        "score":               None,
        "root_letters":        None,
        "ar_word":             None,
        "phonetic_chain":      None,
        "positional_score":    None,   # R11: consonant order fidelity (0.0–1.0)
        "transposition_flag":  False,  # R11: True = consonant order inverted
        "extra_consonants":    0,      # Coverage: word consonants not in root
        "q_gate":              None,
        "u_gate":              None,
        "f_gate":              None,
        "orig2_track":         getattr(result, 'orig2_track', False),
        "orig2_details":       None,
        "cluster_members":     result.cluster_members[:20],
        "log_lines":           result.log,
    }
    # ORIG2 details
    if getattr(result, 'orig2_track', False) and getattr(result, 'orig2_details', None):
        rec["orig2_details"] = {
            "kashgari_translit":  result.orig2_details.get('kashgari_translit', ''),
            "kashgari_meaning":   result.orig2_details.get('kashgari_meaning', ''),
            "kashgari_line":      result.orig2_details.get('kashgari_line', 0),
            "attestation_type":   result.orig2_details.get('attestation_type', ''),
            "skeleton":           result.orig2_details.get('skeleton', ''),
            "all_hits":           result.orig2_details.get('all_hits', 0),
            "bitig_warnings":     result.orig2_details.get('bitig_warnings', []),
        }
    if result.confirmed_root:
        rec["root_letters"]       = result.confirmed_root.letters
        rec["ar_word"]            = result.confirmed_root.ar_word
        rec["score"]              = result.confirmed_root.score
        rec["phonetic_chain"]     = result.confirmed_root.phonetic_chain
        rec["positional_score"]   = getattr(result.confirmed_root, 'positional_score',   None)
        rec["transposition_flag"] = getattr(result.confirmed_root, 'transposition_flag', False)
        rec["extra_consonants"]   = getattr(result.confirmed_root, 'extra_consonants',   0)
    if result.q_gate:
        rec["q_gate"] = {
            "passed":          result.q_gate.passed,
            "token_count":     result.q_gate.details.get("token_count", 0),
            "ar_word":         result.q_gate.details.get("ar_word", ""),
            "verse":           result.q_gate.details.get("verse", ""),
            "orig2_candidate": result.q_gate.details.get("orig2_candidate", False),
        }
    if result.u_gate:
        rec["u_gate"] = {
            "passed":          result.u_gate.passed,
            "phonetic_chain":  result.u_gate.details.get("phonetic_chain", ""),
        }
    if result.f_gate:
        rec["f_gate"] = {
            "passed":      result.f_gate.passed,
            "ds_code":     result.f_gate.details.get("ds_code", ""),
            "network_id":  result.f_gate.details.get("network_id", ""),
            "dp_codes":    result.f_gate.details.get("dp_codes", []),
        }
    return rec


def _categorise(result) -> str:
    """
    Three-tier classification (v2.2):
      ALREADY_IN_LATTICE — already confirmed
      CONFIRMED_HIGH     — score >= 8, Q+U pass, no R11 transposition
      PENDING_REVIEW     — score 5–7, or transposition, or no ORIG1 root,
                           or ORIG2 Kashgari match (always needs human review)
      AUTO_REJECTED      — score < 5, or U-gate fail, or no root at all
    """
    if result.existing_entry_id is not None:
        return "ALREADY_IN_LATTICE"

    # ORIG2 track: always PENDING_REVIEW (human must verify Kashgari attestation)
    if getattr(result, 'orig2_track', False):
        return "PENDING_REVIEW"

    if result.confirmed_root is None:
        # No ORIG1 root AND no ORIG2 match — flag as PENDING_REVIEW for manual check
        return "PENDING_REVIEW"

    score = result.confirmed_root.score
    q     = result.q_gate.passed if result.q_gate else False
    u     = result.u_gate.passed if result.u_gate else False
    trans = getattr(result.confirmed_root, 'transposition_flag', False)

    # CONFIRMED_HIGH: strong phonetic + gate evidence, no transposition
    if score >= 8 and q and u and not trans:
        return "CONFIRMED_HIGH"

    # PENDING_REVIEW: partial evidence — needs human QUF adjudication
    if score >= 5 and (q or u):
        return "PENDING_REVIEW"

    # AUTO_REJECTED: insufficient evidence or consonant accounting failure
    return "AUTO_REJECTED"


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run_batch(word_list: list, output_dir: Path) -> dict:
    """
    Run engine in dry_run=True mode on every word in word_list.
    Returns full results dict. Saves JSON + TXT to output_dir.
    """
    # — Import engine (suppress its startup prints)
    print("Importing USLaP_Engine...")
    with _Suppress():
        from USLaP_Engine import USLaPEngine

    print(f"Initialising engine with master file...")
    with _Suppress() as s:
        try:
            engine = USLaPEngine(master_file=str(MASTER_FILE), skip_reports=True)
        except Exception as e:
            print(f"\nERROR: Engine init failed: {e}")
            print(s.text())
            sys.exit(1)
    print(f"Engine ready.\n")

    # — Buckets (three-tier v2)
    results_by_cat = {
        "ALREADY_IN_LATTICE": [],
        "CONFIRMED_HIGH":     [],
        "PENDING_REVIEW":     [],
        "AUTO_REJECTED":      [],
    }
    cluster_backlog = set()  # words discovered via cluster expansion
    total = len(word_list)

    # — Process loop
    for i, word in enumerate(word_list, 1):
        pct = (i / total) * 100
        print(f"  [{i:>3}/{total}] {pct:>5.1f}%  {word:<20}", end="", flush=True)

        with _Suppress():
            try:
                result = engine.process(word, dry_run=True)
            except Exception as e:
                print(f" ERROR: {e}")
                continue

        rec  = serialise_result(word, result)
        cat  = rec["category"]
        results_by_cat[cat].append(rec)

        # Collect cluster discoveries
        for candidate in result.cluster_members:
            if isinstance(candidate, str):
                cluster_backlog.add(candidate.upper())

        # Inline status
        root  = rec.get("root_letters", "?")
        score = rec.get("score", "?")
        trans = rec.get("transposition_flag", False)
        pos   = rec.get("positional_score")
        pos_s = f"  pos={pos:.2f}" if pos is not None else ""
        r11   = "  ⚠R11" if trans else ""

        if cat == "ALREADY_IN_LATTICE":
            print(f" ✓ EXISTING   #{result.existing_entry_id}")
        elif cat == "CONFIRMED_HIGH":
            print(f" ★ CONFIRMED  root={root:<12} score={score}/10{pos_s}")
        elif cat == "PENDING_REVIEW":
            if getattr(result, 'orig2_track', False):
                # ORIG2 (Kashgari) match found
                kd = getattr(result, 'orig2_details', {}) or {}
                kt = kd.get('kashgari_translit', '?')
                ka = kd.get('attestation_type', '?')
                print(f" ◆ ORIG2      Kashgari='{kt}' ({ka}) score={score}/10")
            elif result.confirmed_root is None:
                print(f" ~ PENDING    (no ORIG1 root, no ORIG2 match)")
            else:
                print(f" ~ PENDING    root={root:<12} score={score}/10{pos_s}{r11}")
        else:
            print(f" ✗ REJECTED   root={root:<12} score={score}/10{r11}")

    # — Remove input words and already-existing terms from cluster backlog
    input_upper = {w.upper() for w in word_list}
    existing_upper = {r["word"] for r in results_by_cat["ALREADY_IN_LATTICE"]}
    cluster_backlog -= input_upper
    cluster_backlog -= existing_upper

    # — Build final report (three-tier v2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "run_date":         datetime.now().isoformat(),
        "engine_version":   "v2.0 (R09/R10/R11/R08a)",
        "master_file":      str(MASTER_FILE),
        "total_words":      total,
        "summary": {
            "already_in_lattice": len(results_by_cat["ALREADY_IN_LATTICE"]),
            "confirmed_high":     len(results_by_cat["CONFIRMED_HIGH"]),
            "pending_review":     len(results_by_cat["PENDING_REVIEW"]),
            "auto_rejected":      len(results_by_cat["AUTO_REJECTED"]),
            "cluster_backlog":    len(cluster_backlog),
        },
        "already_in_lattice": results_by_cat["ALREADY_IN_LATTICE"],
        "confirmed_high":     results_by_cat["CONFIRMED_HIGH"],
        "pending_review":     results_by_cat["PENDING_REVIEW"],
        "auto_rejected":      results_by_cat["AUTO_REJECTED"],
        "cluster_backlog":    sorted(cluster_backlog),
    }

    # — Save JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"BATCH_REPORT_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON report saved: {json_path}")

    # — Save human-readable TXT summary
    txt_path = output_dir / f"BATCH_SUMMARY_{timestamp}.txt"
    _write_txt_summary(report, txt_path)
    print(f"  TXT summary saved: {txt_path}")

    return report


def _write_txt_summary(report: dict, path: Path):
    """Write a human-readable summary TXT (three-tier v2)."""
    s = report["summary"]
    lines = [
        "═" * 70,
        "  USLaP Batch Runner v2.0 — Discovery Summary",
        "  بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "═" * 70,
        f"  Run date:       {report['run_date']}",
        f"  Engine:         {report.get('engine_version', 'v2.0')}",
        f"  Words run:      {report['total_words']}",
        "─" * 70,
        f"  ✓ Already in lattice:  {s['already_in_lattice']:>4}  (no action needed)",
        f"  ★ CONFIRMED HIGH:      {s['confirmed_high']:>4}  ← review & write to A1_ENTRIES",
        f"  ~ PENDING REVIEW:      {s['pending_review']:>4}  ← human QUF adjudication required",
        f"  ✗ AUTO REJECTED:       {s['auto_rejected']:>4}  (U-gate fail or score < 5)",
        f"  + Cluster backlog:     {s['cluster_backlog']:>4}  (new words found via root expansion)",
        "─" * 70,
        "",
        "  ★ CONFIRMED HIGH — review these first (score ≥ 8, Q+U pass, no R11 transposition):",
        "─" * 70,
    ]
    for rec in report["confirmed_high"]:
        root   = rec.get("root_letters", "?")
        score  = rec.get("score", "?")
        chain  = rec.get("phonetic_chain", "?") or "—"
        tokens = rec.get("q_gate", {}).get("token_count", "?") if rec.get("q_gate") else "?"
        pos    = rec.get("positional_score")
        pos_s  = f"  pos={pos:.2f}" if pos is not None else ""
        net    = rec.get("f_gate", {}).get("network_id", "") if rec.get("f_gate") else ""
        net_s  = f"  [{net}]" if net else ""
        lines.append(
            f"  {rec['word']:<22} root={root:<12} score={score}/10  tokens={tokens}{pos_s}{net_s}"
        )
        lines.append(f"    chain: {chain}")

    # Split PENDING into ORIG2 matches and regular PENDING
    orig2_pending  = [r for r in report["pending_review"] if r.get("orig2_track")]
    other_pending  = [r for r in report["pending_review"] if not r.get("orig2_track")]

    if orig2_pending:
        lines += [
            "",
            f"  ◆ ORIG2 (KASHGARI) MATCHES — {len(orig2_pending)} words attested in Bitig:",
            "─" * 70,
        ]
        for rec in orig2_pending:
            od    = rec.get("orig2_details", {}) or {}
            kt    = od.get("kashgari_translit", "?")
            km    = od.get("kashgari_meaning", "?")
            kl    = od.get("kashgari_line", "?")
            ka    = od.get("attestation_type", "?")
            score = rec.get("score", "?")
            warns = od.get("bitig_warnings", [])
            warn_s = f"  ⚠ {'; '.join(warns)}" if warns else ""
            # Truncate meaning to 50 chars
            km_short = km[:50] + "..." if len(km) > 50 else km
            lines.append(
                f"  {rec['word']:<20} Kashgari='{kt}' ({ka}, line {kl}) score={score}/10{warn_s}"
            )
            lines.append(f"    meaning: \"{km_short}\"")

    lines += [
        "",
        f"  ~ PENDING REVIEW — {len(other_pending)} words need human QUF adjudication:",
        "─" * 70,
    ]
    for rec in other_pending:
        root  = rec.get("root_letters") or "NO ORIG1 ROOT"
        score = rec.get("score", "?")
        trans = rec.get("transposition_flag", False)
        q_ok  = rec.get("q_gate", {}).get("passed", False) if rec.get("q_gate") else False
        u_ok  = rec.get("u_gate", {}).get("passed", False) if rec.get("u_gate") else False
        flags = []
        if trans:          flags.append("⚠R11-TRANSPOSITION")
        if not q_ok:       flags.append("Q-FAIL (no ORIG1 or ORIG2)")
        if not u_ok:       flags.append("U-FAIL")
        flag_s = "  " + " | ".join(flags) if flags else ""
        lines.append(f"  {rec['word']:<22} root={root:<12} score={score}/10{flag_s}")

    lines += [
        "",
        "  + CLUSTER BACKLOG — words discovered via root expansion",
        "    (not in input list — found by the engine itself):",
        "─" * 70,
    ]
    for w in sorted(report["cluster_backlog"]):
        lines.append(f"  {w}")

    lines += [
        "",
        "═" * 70,
        "  NEXT STEPS:",
        "  1. Take CONFIRMED_HIGH entries → confirm ROOT_ID + QUR_MEANING manually",
        "  2. Run engine.process(word, dry_run=False) for approved CONFIRMED_HIGH words",
        "  3. For PENDING_REVIEW with Q-FAIL: check Kashgari corpus (ORIG2 track)",
        "  4. For PENDING_REVIEW with ⚠R11: recheck phonetic chain — transposition likely",
        "  5. CLUSTER_BACKLOG: run batch_runner again with these as input for next cycle",
        "═" * 70,
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Check output dir exists
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check master file
    if not MASTER_FILE.exists():
        print(f"ERROR: Master file not found:\n  {MASTER_FILE}")
        sys.exit(1)

    # Word source: CLI arg (custom file) or built-in list
    if len(sys.argv) > 1 and sys.argv[1] not in ("--dry-summary",):
        custom_file = Path(sys.argv[1])
        if not custom_file.exists():
            print(f"ERROR: Word file not found: {custom_file}")
            sys.exit(1)
        with open(custom_file, "r", encoding="utf-8") as f:
            word_list = [line.strip().lower() for line in f
                         if line.strip() and line.strip().isalpha()]
        print(f"Loaded {len(word_list)} words from {custom_file.name}")
    else:
        word_list = WORD_LIST_500
        print(f"Using built-in word list: {len(word_list)} words")

    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Master file:      {MASTER_FILE.name}")
    print(f"Mode:             DRY RUN (no writes to Excel)\n")
    print("─" * 62)

    report = run_batch(word_list, OUTPUT_DIR)

    # — Print terminal summary
    s = report["summary"]
    print("\n" + "═" * 70)
    print("  BATCH COMPLETE — THREE-TIER SUMMARY (v2)")
    print("═" * 70)
    print(f"  Words processed:       {report['total_words']}")
    print(f"  ✓ Already in lattice:  {s['already_in_lattice']}")
    print(f"  ★ CONFIRMED HIGH:      {s['confirmed_high']}  ← review & write to A1_ENTRIES")
    print(f"  ~ PENDING REVIEW:      {s['pending_review']}  ← human QUF adjudication")
    print(f"  ✗ AUTO REJECTED:       {s['auto_rejected']}")
    print(f"  + Cluster backlog:     {s['cluster_backlog']}  ← bonus discoveries")
    print("═" * 70)
    print("\n  Open the TXT summary for the full annotated review list.")
    print("  Open the JSON report for machine-readable detail.")
    print("  PENDING_REVIEW with Q-FAIL → check Kashgari corpus (ORIG2 track).")
    print("  PENDING_REVIEW with ⚠R11  → recheck phonetic chain (transposition).")
