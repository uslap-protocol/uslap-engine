#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP Russian Batch Runner v1.0
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Runs USLaP_Engine v3.0 (dual-language) in DRY-RUN mode against a Russian word list.
NO writes to the master Excel file. Discovery only.

Output:
  - Batch Reports/RU_BATCH_REPORT_<timestamp>.json   (full machine-readable results)
  - Batch Reports/RU_BATCH_SUMMARY_<timestamp>.txt   (human-readable summary)

Usage:
  python3 batch_runner_ru.py                      # uses built-in 300-word list
  python3 batch_runner_ru.py my_words.txt         # uses your own word list (one word per line)

THREE-TIER OUTPUT SYSTEM:
  ALREADY_IN_LATTICE  — word already confirmed in A1_ЗАПИСИ (skip)
  CONFIRMED_HIGH      — score >= 8, Q+U pass, no R11 transposition
                        → review before writing to A1_ЗАПИСИ
  PENDING_REVIEW      — score 5–7, OR transposition flag, OR ORIG2/Kashgari candidate
                        → human judgment required
  AUTO_REJECTED       — score < 5 OR U-gate fail
                        → discard at current analysis level
  CLUSTER_BACKLOG     — words discovered via cluster expansion

NOTE: Russia has >50% Bitig (ORIG2) influence. Many words will route to
PENDING_REVIEW as ORIG2 candidates requiring Kashgari attestation.
This is EXPECTED — not a failure. The Bitig track is the primary discovery
pathway for Russian.
"""

import sys
import os
import json
import io
import contextlib
from datetime import datetime
from pathlib import Path

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
THIS_DIR     = Path(__file__).parent                                    # "Code_files/"
WORKSPACE    = Path("/Users/mmsetubal/Documents/USLaP workplace")
MASTER_FILE  = WORKSPACE / "USLaP_Final_Data_Consolidated_Master_v3.xlsx"
OUTPUT_DIR   = Path("/Users/mmsetubal/Documents/USLaP workplace/Batch Reports")

sys.path.insert(0, str(THIS_DIR))

# ─── SUPPRESS ENGINE STDOUT ───────────────────────────────────────────────────
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

# ─── RUSSIAN WORD LIST ────────────────────────────────────────────────────────
# ~300 Russian words selected for QUF discovery.
# Covers: governance, military, trade, nature, body, household, food, crafts,
# religion, animals, clothing, science, time, family, society.
# Mix of suspected ORIG1 (Arabic) and ORIG2 (Bitig/Turkic) origins.
# Words already in A1_ЗАПИСИ will be caught by DEDUP and reported as EXISTING.

RUSSIAN_WORD_LIST = [
    # ═══ GOVERNANCE + LAW ═══
    "закон", "власть", "правда", "суд", "правитель", "порядок",
    "держава", "престол", "вождь", "падишах", "султан", "эмир",
    "воевода", "дума", "указ", "ярлык", "грамота", "печать",
    "ханство", "улус", "бек", "мурза", "темник", "нойон",

    # ═══ MILITARY + WARFARE ═══
    "войско", "полк", "стража", "дозор", "засада",
    "кинжал", "сабля", "булат", "кольчуга", "щит",
    "знамя", "набег", "осада", "победа", "пленник",
    "десант", "гарнизон", "крепость", "бастион", "батарея",

    # ═══ TRADE + ECONOMY ═══
    "торговля", "цена", "долг", "прибыль", "рубль",
    "банк", "вексель", "процент", "залог", "пошлина",
    "лавка", "ярмарка", "барыш", "бакшиш", "дукат",
    "серебро", "золото", "жемчуг", "бирюза", "янтарь",

    # ═══ NATURE + GEOGRAPHY ═══
    "степь", "тайга", "тундра", "болото", "пустыня",
    "река", "озеро", "море", "гора", "долина",
    "камень", "глина", "песок", "соль", "нефть",
    "ветер", "буря", "гроза", "молния", "радуга",
    "лес", "поле", "сад", "роща", "овраг",

    # ═══ ANIMALS ═══
    "верблюд", "лошадь", "баран", "бык", "осёл",
    "соловей", "беркут", "сокол", "орёл", "журавль",
    "кабан", "барсук", "волк", "тигр", "рысь",
    "собака", "кошка", "ворон", "змея", "рыба",

    # ═══ BODY + HEALTH ═══
    "голова", "сердце", "кровь", "кость", "кожа",
    "глаз", "ухо", "рука", "нога", "палец",
    "кулак", "горло", "грудь", "живот", "спина",
    "рана", "лекарь", "врач", "больной", "яд",
    "бальзам", "мазь", "целитель", "жар", "смерть",

    # ═══ FOOD + DRINK ═══
    "плов", "лаваш", "шашлык", "хлеб", "мясо",
    "хурма", "нут", "рис", "мёд", "молоко",
    "чай", "вино", "сироп", "масло", "уксус",
    "перец", "тмин", "шафран", "корица", "имбирь",
    "йогурт", "каша", "суп", "соус", "лимон",

    # ═══ HOUSEHOLD + TOOLS ═══
    "ковёр", "диван", "табурет", "подушка", "зеркало",
    "кувшин", "чашка", "блюдо", "ложка", "нож",
    "самовар", "фонарь", "лампа", "свеча", "котёл",
    "замок", "ключ", "пила", "молоток", "топор",
    "балкон", "мансарда", "чердак", "подвал", "забор",

    # ═══ CLOTHING + TEXTILES ═══
    "кафтан", "чалма", "шаровары", "тулуп", "шуба",
    "платок", "пояс", "сапог", "войлок", "бархат",
    "шёлк", "хлопок", "парча", "тесьма", "нить",

    # ═══ RELIGION + FAITH ═══
    "намаз", "минбар", "хадж", "закят", "вакф",
    "муэдзин", "имам", "мулла", "дервиш", "суфий",
    "михраб", "масджид", "минарет", "купол", "мечеть",

    # ═══ SCIENCE + CRAFT ═══
    "алгебра", "цифра", "число", "мера", "весы",
    "зодчий", "каменщик", "гончар", "кузнец", "ткач",
    "чернила", "бумага", "книга", "печать", "буква",
    "астрономия", "химия", "геометрия", "медицина", "хирургия",

    # ═══ TIME + CALENDAR ═══
    "время", "час", "день", "ночь", "утро",
    "рассвет", "закат", "луна", "звезда", "солнце",
    "год", "месяц", "неделя", "пятница", "суббота",

    # ═══ FAMILY + SOCIETY ═══
    "отец", "мать", "брат", "сестра", "сын",
    "дочь", "жена", "муж", "семья", "род",
    "народ", "племя", "община", "сосед", "гость",
    "друг", "враг", "раб", "свободный", "мудрец",

    # ═══ ADDITIONAL HIGH-YIELD TERMS ═══
    # (suspected Arabic/Turkic that aren't in A1_ЗАПИСИ yet)
    "шахта", "маяк", "талант", "рецепт", "тюрбан",
    "гарем", "газета", "журнал", "автомат", "кибитка",
    "тархан", "курултай", "байрам", "аксакал", "батыр",
    "иман", "китаб", "джихад", "шариат", "фетва",
    "масло", "мастер", "ремесло", "рынок", "богатство",
    "душа", "разум", "совесть", "истина", "справедливость",
    "хозяин", "наместник", "посол", "договор", "мир",
    "казарма", "лазарет", "госпиталь", "аптека", "бальзам",
    "табак", "кальян", "хна", "мускус", "амбра",
    "арбалет", "пушка", "порох", "снаряд", "мушкет",
]

# Remove duplicates while preserving order
_seen = set()
RUSSIAN_WORD_LIST = [w for w in RUSSIAN_WORD_LIST if not (w in _seen or _seen.add(w))]


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
        "positional_score":    None,
        "transposition_flag":  False,
        "extra_consonants":    0,
        "q_gate":              None,
        "u_gate":              None,
        "f_gate":              None,
        "orig2_track":         getattr(result, 'orig2_track', False),
        "orig2_details":       None,
        "cognate_crossref":    None,   # v3.3: English↔Russian cognate data
        "compound_parts":      None,   # v3.4: compound word analysis (САМО+ВАР)
        "sem_review":          getattr(result, 'sem_review', False),  # v3.4
        "cluster_members":     result.cluster_members[:20],
        "log_lines":           result.log,
    }
    # v3.3: Cognate cross-reference data
    cog = getattr(result, 'cognate_crossref', None)
    if cog:
        rec["cognate_crossref"] = {
            "source":          cog.get('source', ''),
            "en_cousin":       cog.get('en_cousin', ''),
            "root_letters":    cog.get('root_letters', ''),
            "score":           cog.get('score', None),
            "phonetic_chain":  cog.get('phonetic_chain', ''),
            "variant_used":    cog.get('variant_used', ''),
            "word_form_used":  cog.get('word_form_used', ''),
            "entry_id":        cog.get('entry_id', None),
            "note":            cog.get('note', ''),
        }
    # v3.4: Compound parts analysis
    cp = getattr(result, 'compound_parts', None)
    if cp:
        rec["compound_parts"] = {
            "label":   cp.get('label', ''),
            "bridge":  cp.get('bridge', ''),
            "prefix":  cp.get('prefix'),  # dict or None
            "root":    cp.get('root'),     # dict or None
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
    Three-tier classification:
      ALREADY_IN_LATTICE — already in A1_ЗАПИСИ
      CONFIRMED_HIGH     — score >= 8, Q+U pass, no R11 transposition
      PENDING_REVIEW     — score 5–7, or transposition, or ORIG2 match
      AUTO_REJECTED      — score < 5, or U-gate fail, or no root at all
    """
    if result.existing_entry_id is not None:
        return "ALREADY_IN_LATTICE"

    # ORIG2 track: always PENDING_REVIEW (needs Kashgari verification)
    if getattr(result, 'orig2_track', False):
        return "PENDING_REVIEW"

    if result.confirmed_root is None:
        return "PENDING_REVIEW"

    score = result.confirmed_root.score
    q     = result.q_gate.passed if result.q_gate else False
    u     = result.u_gate.passed if result.u_gate else False
    trans = getattr(result.confirmed_root, 'transposition_flag', False)

    if score >= 8 and q and u and not trans:
        return "CONFIRMED_HIGH"

    if score >= 5 and (q or u):
        return "PENDING_REVIEW"

    return "AUTO_REJECTED"


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run_batch(word_list: list, output_dir: Path) -> dict:
    """
    Run engine in dry_run=True mode on every Russian word.
    Returns full results dict. Saves JSON + TXT to output_dir.
    """
    print("Importing USLaP_Engine (v3.0 dual-language)...")
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
    print(f"Engine ready (v3.0 — EN+RU dual-language).\n")

    # Buckets
    results_by_cat = {
        "ALREADY_IN_LATTICE": [],
        "CONFIRMED_HIGH":     [],
        "PENDING_REVIEW":     [],
        "AUTO_REJECTED":      [],
    }
    cluster_backlog = set()
    total = len(word_list)

    # Process loop
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

        # v3.3: cognate suffix
        cog_rec = rec.get("cognate_crossref")
        cog_s = ""
        if cog_rec and cog_rec.get("source") == "EN_PIPELINE":
            cog_s = f"  ↔{cog_rec['en_cousin']}→{cog_rec['root_letters']}(s{cog_rec.get('score','?')})"
        elif cog_rec and cog_rec.get("source") == "LATTICE_ENTRY":
            cog_s = f"  ↔LAT#{cog_rec.get('entry_id','?')}"

        # v3.4: compound suffix
        cp_rec = rec.get("compound_parts")
        cp_s = ""
        if cp_rec and cp_rec.get("label"):
            cp_s = f"  [{cp_rec['label']}]"

        if cat == "ALREADY_IN_LATTICE":
            print(f" ✓ EXISTING   #{result.existing_entry_id}")
        elif cat == "CONFIRMED_HIGH":
            print(f" ★ CONFIRMED  root={root:<12} score={score}/10{pos_s}{cog_s}{cp_s}")
        elif cat == "PENDING_REVIEW":
            if getattr(result, 'orig2_track', False):
                kd = getattr(result, 'orig2_details', {}) or {}
                kt = kd.get('kashgari_translit', '?')
                ka = kd.get('attestation_type', '?')
                print(f" ◆ ORIG2      Kashgari='{kt}' ({ka}) score={score}/10{cog_s}{cp_s}")
            elif result.confirmed_root is None:
                print(f" ~ PENDING    (no ORIG1 root, no ORIG2 match)")
            else:
                print(f" ~ PENDING    root={root:<12} score={score}/10{pos_s}{r11}{cog_s}{cp_s}")
        else:
            print(f" ✗ REJECTED   root={root:<12} score={score}/10{r11}{cp_s}")

    # Remove input + existing from cluster backlog
    input_upper = {w.upper() for w in word_list}
    existing_upper = {r["word"] for r in results_by_cat["ALREADY_IN_LATTICE"]}
    cluster_backlog -= input_upper
    cluster_backlog -= existing_upper

    # Build report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "run_date":         datetime.now().isoformat(),
        "engine_version":   "v3.0 (EN+RU dual-language + multi-candidate)",
        "language":         "Russian (RU)",
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

    # Save JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"RU_BATCH_REPORT_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON report saved: {json_path}")

    # Save TXT summary
    txt_path = output_dir / f"RU_BATCH_SUMMARY_{timestamp}.txt"
    _write_txt_summary(report, txt_path)
    print(f"  TXT summary saved: {txt_path}")

    return report


def _write_txt_summary(report: dict, path: Path):
    """Write a human-readable Russian batch summary."""
    s = report["summary"]
    lines = [
        "═" * 70,
        "  USLaP Russian Batch Runner v1.0 — Discovery Summary",
        "  بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "  Language: Russian (RU) — >50% ORIG2 (Bitig/Turkic) expected",
        "═" * 70,
        f"  Run date:       {report['run_date']}",
        f"  Engine:         {report.get('engine_version', 'v3.0')}",
        f"  Words run:      {report['total_words']}",
        "─" * 70,
        f"  ✓ Already in A1_ЗАПИСИ:   {s['already_in_lattice']:>4}  (no action needed)",
        f"  ★ CONFIRMED HIGH:          {s['confirmed_high']:>4}  ← review & write to A1_ЗАПИСИ",
        f"  ~ PENDING REVIEW:          {s['pending_review']:>4}  ← human QUF adjudication",
        f"  ✗ AUTO REJECTED:           {s['auto_rejected']:>4}  (U-gate fail or score < 5)",
        f"  + Cluster backlog:         {s['cluster_backlog']:>4}  (new words via root expansion)",
        "─" * 70,
        "",
        "  NOTE: High PENDING count is EXPECTED for Russian — many words are",
        "  ORIG2 (Bitig/Turkic) and need Kashgari attestation, not Q-gate.",
        "",
        "  ★ CONFIRMED HIGH — ORIG1 candidates (score ≥ 8, Q+U pass):",
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

    # Split PENDING into ORIG2 and others
    orig2_pending = [r for r in report["pending_review"] if r.get("orig2_track")]
    other_pending = [r for r in report["pending_review"] if not r.get("orig2_track")]

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
        if not q_ok:       flags.append("Q-FAIL")
        if not u_ok:       flags.append("U-FAIL")
        flag_s = "  " + " | ".join(flags) if flags else ""
        lines.append(f"  {rec['word']:<22} root={root:<12} score={score}/10{flag_s}")

    # Rejected
    lines += [
        "",
        f"  ✗ AUTO REJECTED — {len(report['auto_rejected'])} words:",
        "─" * 70,
    ]
    for rec in report["auto_rejected"]:
        root  = rec.get("root_letters") or "?"
        score = rec.get("score", "?")
        lines.append(f"  {rec['word']:<22} root={root:<12} score={score}/10")

    # Cluster backlog
    lines += [
        "",
        "  + CLUSTER BACKLOG — words discovered via root expansion:",
        "─" * 70,
    ]
    for w in sorted(report["cluster_backlog"]):
        lines.append(f"  {w}")

    lines += [
        "",
        "═" * 70,
        "  NEXT STEPS:",
        "  1. CONFIRMED_HIGH → verify ROOT_ID + QUR_MEANING → write to A1_ЗАПИСИ",
        "  2. ORIG2 matches → verify Kashgari attestation → write to BITIG_A1_ENTRIES",
        "  3. PENDING with Q-FAIL → check Kashgari corpus (ORIG2 track)",
        "  4. PENDING with ⚠R11 → recheck phonetic chain (transposition)",
        "  5. Cross-reference with English A1_ENTRIES for sibling entries",
        "  6. CLUSTER_BACKLOG → run batch_runner_ru again with these as input",
        "═" * 70,
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MASTER_FILE.exists():
        print(f"ERROR: Master file not found:\n  {MASTER_FILE}")
        sys.exit(1)

    # Word source: CLI arg (custom file) or built-in list
    if len(sys.argv) > 1:
        custom_file = Path(sys.argv[1])
        if not custom_file.exists():
            print(f"ERROR: Word file not found: {custom_file}")
            sys.exit(1)
        with open(custom_file, "r", encoding="utf-8") as f:
            word_list = [line.strip().lower() for line in f if line.strip()]
        print(f"Loaded {len(word_list)} words from {custom_file.name}")
    else:
        word_list = RUSSIAN_WORD_LIST
        print(f"Using built-in Russian word list: {len(word_list)} words")

    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Master file:      {MASTER_FILE.name}")
    print(f"Language:          Russian (RU) — ORIG1 + ORIG2 dual-track")
    print(f"Mode:             DRY RUN (no writes to Excel)\n")
    print("─" * 62)

    report = run_batch(word_list, OUTPUT_DIR)

    # Terminal summary
    s = report["summary"]
    print("\n" + "═" * 70)
    print("  RUSSIAN BATCH COMPLETE — THREE-TIER SUMMARY (v1.0)")
    print("═" * 70)
    print(f"  Words processed:       {report['total_words']}")
    print(f"  ✓ Already in lattice:  {s['already_in_lattice']}")
    print(f"  ★ CONFIRMED HIGH:      {s['confirmed_high']}  ← review & write to A1_ЗАПИСИ")
    print(f"  ~ PENDING REVIEW:      {s['pending_review']}  ← human QUF adjudication")
    print(f"  ✗ AUTO REJECTED:       {s['auto_rejected']}")
    print(f"  + Cluster backlog:     {s['cluster_backlog']}  ← bonus discoveries")
    print("═" * 70)
    print("\n  NOTE: For Russian, high PENDING is expected (>50% ORIG2/Bitig).")
    print("  ORIG2 matches need Kashgari attestation — NOT Q-gate.")
    print("  Open TXT summary for annotated review. JSON for machine-readable data.")
