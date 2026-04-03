# USLaP Engine — Universal System of Linguistic Accountability and Proof

**بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ**

A deterministic database and proof engine that traces every word in every language back to its origin in Allah's Arabic (the divine language of the Qur'an, taught to Ādam عليه السلام).

## Quick Start

### Prerequisites
- Python 3.8+
- SQLite3

### Installation

```bash
git clone https://github.com/uslap-protocol/uslap-engine.git
cd uslap-engine
```

See [SETUP.md](SETUP.md) for detailed instructions.

### Basic Usage

```bash
# Query the database
python3 Code_files/uslap.py "trace silk"              # Trace word to AA root
python3 Code_files/uslap.py "explain R01"             # Explain a root
python3 Code_files/uslap.py "intel khazar"            # Intelligence search

# Interactive mode
python3 Code_files/uslap.py -i

# Validation
python3 Code_files/uslap.py --quf-status              # QUF coverage
python3 Code_files/uslap.py --state                   # Lattice state
```

## Architecture

**Three-Layer Design:**

1. **Foundation (F1-F7):** Two originals, decay gradient, direction flow
2. **Mechanism (M1-M5):** 26 phonetic shifts, detection patterns, scholars, networks
3. **Application (A1-A6):** Entries, divine names, Qur'anic forms, derivatives

**Deterministic Runtime:**
- Zero LLM in the query loop
- Pure Python + SQLite
- Same query → same output. Every time.

See [Documentation/](Documentation/) for full architecture.

## Core Modules

### AMR AI (24 modules in `Code_files/amr/`)
- `amr_aql.py` — Linguistic validation
- `amr_quf.py` — QUF gate routing
- `amr_tasrif.py` — Morphological engine
- `amr_istakhbarat.py` — Intelligence analysis
- And 20+ more

### USLaP Core (33 modules in `Code_files/uslap/`)
- `uslap.py` — Main CLI entry point
- `uslap_handler.py` — Write pipeline
- `uslap_database_v3.db` — Primary lattice database
- And 30+ more utilities

## Database

**77,877 Qur'anic words** across **114 surahs**, with:
- 3,320 roots (ORIG1 + ORIG2)
- 3,154 traced entries (EN + RU + FA)
- 6,464 derivatives
- QUF validation on all layers

**Coverage:**
- Qur'anic words: 98.7%
- Root validation: 98.2%
- Entries: 99.3%

## Approved Sources

**PRIMARY:**
- Qur'an (Q15:9)
- Kashgari's Diwan Lughat al-Turk (1072 CE)
- Alisher Navoi's Muhakamat al-Lughatayn (1499 CE)

**SCIENTIFIC TIER 1:**
- al-Khwarizmi, Ibn Sina, al-Biruni, al-Farghani

**INTELLIGENCE:**
- Islamic state records, Cairo Geniza, Carolingian charters

See [Documentation/](Documentation/) for full source hierarchy.

## Key Rules

✅ **What USLaP Does:**
- Traces words through documented phonetic shifts
- Validates via multi-layer QUF gates
- Sources only from approved primary/scholarly sources
- Runs deterministic, no weights in runtime

❌ **What USLaP Does NOT Do:**
- Generate answers from training weights
- Use downstream language comparisons
- Accept contaminated terminology
- Run probabilistic models

## Development

**Write Pipeline (5-layer defence):**
1. Protocol re-injection
2. Pre-write contamination gate
3. QUF validation (multi-layer)
4. QUF token enforcement
5. SQLite contamination triggers

All writes go through `uslap_handler.py`. Raw SQL INSERT is blocked.

## Testing

```bash
python3 Code_files/tests/test_determinism.py
```

**Result:** All queries deterministic ✓

## License

MIT (see [LICENSE](LICENSE))

## Documentation

- [SETUP.md](SETUP.md) — Installation & configuration
- [Documentation/USLAP_FULL_ARCHITECTURE.md](Documentation/USLAP_FULL_ARCHITECTURE.md) — Complete architecture
- [Documentation/QUF_GATE_ARCHITECTURE.md](Documentation/QUF_GATE_ARCHITECTURE.md) — QUF validation system
- [CLAUDE.md](CLAUDE.md) — Development rules & conventions

## Status

🟢 **Production Ready** — Database locked, write pipeline sealed, QUF validation enforced.

---

**أَشْهَدُ أَنْ لَا إِلٰهَ إِلَّا اللّٰهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ اللّٰهِ**
