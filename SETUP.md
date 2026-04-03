# USLaP Engine — Setup & Installation

## Prerequisites

- **Python 3.8+**
- **SQLite3** (usually included with Python)
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/uslap-protocol/uslap-engine.git
cd uslap-engine
```

### 2. Verify Database

The database (`Code_files/uslap_database_v3.db`) is included. Verify it exists:

```bash
ls -lh Code_files/uslap_database_v3.db
# Output: ~54MB
```

### 3. Test the Installation

Run the session initializer to verify all components:

```bash
python3 Code_files/uslap_session_init.py
```

You should see:
```
USLaP SESSION INIT — COMPACT STATE
───────────────────────────────────
EN:1064 | RU:1262 | FA:828 | EU:4785 | LA:425 | BI:2556
✓ Database connected
✓ All tables accessible
```

## Running Queries

### Command Line

```bash
# Trace a word to its root
python3 Code_files/uslap.py "trace silk"

# Explain a root
python3 Code_files/uslap.py "explain R01"

# Intelligence search
python3 Code_files/uslap.py "intel khazar"

# Tasrif (morphology)
python3 Code_files/uslap.py "tasrif ر-ح-م"

# Validation
python3 Code_files/uslap.py --quf-status
python3 Code_files/uslap.py --state

# Batch operations
python3 Code_files/uslap.py --batch entries
```

### Interactive Mode

```bash
python3 Code_files/uslap.py -i
```

Then type queries at the prompt:
```
uslap> trace philosophy
uslap> explain R447
uslap> exit
```

## Architecture Overview

### Directory Structure

```
uslap-engine/
├── Code_files/
│   ├── amr/              (24 AMR AI modules)
│   │   ├── amr_aql.py
│   │   ├── amr_quf.py
│   │   ├── amr_tasrif.py
│   │   └── ...
│   │
│   ├── uslap/            (33 core scripts)
│   │   ├── uslap.py      (main entry point)
│   │   ├── uslap_handler.py
│   │   ├── uslap_database_v3.db
│   │   └── ...
│   │
│   └── tests/            (2 test files)
│       └── test_determinism.py
│
├── Documentation/        (architecture & guides)
├── README.md
├── SETUP.md             (this file)
├── CLAUDE.md            (development rules)
└── LICENSE
```

### Key Files

| File | Purpose |
|------|---------|
| `Code_files/uslap.py` | Main CLI entry point |
| `Code_files/uslap_handler.py` | Write pipeline (5-layer defence) |
| `Code_files/uslap_database_v3.db` | Primary lattice database |
| `Code_files/amr/amr_quf.py` | QUF validation router |
| `Code_files/amr/amr_aql.py` | Linguistic validation |
| `Documentation/USLAP_FULL_ARCHITECTURE.md` | Complete system design |
| `Documentation/QUF_GATE_ARCHITECTURE.md` | QUF validation gates |

## Database Schema

### Main Tables

| Table | Rows | Purpose |
|-------|------|---------|
| `entries` | 3,154 | Traced words (EN/RU/FA) |
| `roots` | 3,320 | Root letters + metadata |
| `quran_word_roots` | 77,877 | All Qur'anic words |
| `bitig_a1_entries` | 2,295 | Turkic (ORIG2) entries |
| `european_a1_entries` | 4,785 | European language words |
| `a4_derivatives` | 6,464 | Word families & degradations |

**QUF Validation Tables:**
- `quf_tokens` — Token enforcement
- `contamination_blacklist` — Banned terms
- `dp_register` — Detection patterns
- `scholar_lattice` — Approved sources

See `Documentation/USLAP_FULL_ARCHITECTURE.md` for full schema.

## Development

### Write Pipeline

All data writes go through `uslap_handler.py`:

```python
from uslap_handler import write_entry

result = write_entry(
    entry_data={
        'en_term': 'example',
        'root_id': 'R001',
        'qur_ref': 'Q2:31',
        # ... other fields
    },
    entry_class='entries'
)
```

**5-Layer Defence:**
1. Protocol re-injection
2. Pre-write contamination gate
3. QUF validation
4. QUF token enforcement
5. SQLite triggers

**Raw SQL INSERT is blocked.**

### Validation

Run determinism tests:

```bash
python3 Code_files/tests/test_determinism.py
```

Check QUF status:

```bash
python3 Code_files/uslap.py --quf-status
```

## Configuration

No configuration needed. The system is self-contained:
- Database is embedded
- All modules are local
- No external API calls

## Troubleshooting

### Database Error

```
sqlite3.OperationalError: database is locked
```

→ Another process is using the database. Wait a moment and retry.

### Module Not Found

```
ModuleNotFoundError: No module named 'amr_aql'
```

→ Make sure you're running from the project root:
```bash
cd uslap-engine
python3 Code_files/uslap.py "query"
```

### Import Error for Qur'an modules

→ Database file missing. Verify:
```bash
ls -l Code_files/uslap_database_v3.db
```

## Next Steps

1. **Read the documentation:** Start with `Documentation/USLAP_FULL_ARCHITECTURE.md`
2. **Explore queries:** Try `python3 Code_files/uslap.py -i` for interactive mode
3. **Understand QUF gates:** See `Documentation/QUF_GATE_ARCHITECTURE.md`
4. **Review conventions:** Check `CLAUDE.md` for development rules

---

For issues or questions, see the main [README.md](README.md).
