#!/usr/bin/env python3
"""
USLaP Database Backup & Distribution System
============================================
al-Falaq (SEED) layer — protects and expands the lattice.

Unlike proprietary databases (Spanner: 5 replicas in locked DCs),
the USLaP lattice replicates through DISTRIBUTION:
  - Every clone = a new node
  - Every reader = a verifier
  - No secrets, no black boxes

Modes:
  python3 uslap_backup.py              # local backup (rotation of 5)
  python3 uslap_backup.py icloud       # + copy to iCloud Drive
  python3 uslap_backup.py jsonl        # + export human-readable JSONL
  python3 uslap_backup.py full         # local + iCloud + JSONL (all three)
  python3 uslap_backup.py github       # instructions for GitHub push
"""
import sqlite3, os, sys, shutil, glob, json
from datetime import datetime

# ── PATHS ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'uslap_database_v3.db')
BACKUP_DIR = os.path.join(SCRIPT_DIR, 'backups')
ICLOUD_DIR = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/USLaP_Backup')
JSONL_DIR = os.path.join(SCRIPT_DIR, 'exports')
MAX_BACKUPS = 5

# ── TABLES TO VERIFY ──
VERIFY_TABLES = [
    'a1_entries', 'a1_записи', 'a4_derivatives',
    'excel_data_consolidated', 'bitig_a1_entries',
    'persian_a1_mad_khil', 'term_nodes', 'term_dimensions',
    'chronology', 'child_schema'
]

# ── TABLES TO EXPORT (core lattice data, human-readable) ──
EXPORT_TABLES = [
    'a1_entries', 'a1_записи', 'persian_a1_mad_khil', 'bitig_a1_entries',
    'latin_a1_entries', 'child_schema', 'a2_names_of_allah',
    'a3_quran_refs', 'a4_derivatives', 'a5_cross_refs',
    'a6_country_names', 'chronology', 'm1_phonetic_shifts',
    'm2_detection_patterns', 'm3_scholars', 'm4_networks',
    'term_nodes', 'term_dimensions'
]


def create_backup():
    """Local backup with rotation and verification."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, f'uslap_v3_backup_{ts}.db')

    shutil.copy2(DB_PATH, dst)

    orig_size = os.path.getsize(DB_PATH)
    bak_size = os.path.getsize(dst)
    if orig_size != bak_size:
        print(f"  ERROR: Size mismatch! orig={orig_size}, backup={bak_size}")
        return None

    conn_orig = sqlite3.connect(DB_PATH)
    conn_bak = sqlite3.connect(dst)
    all_match = True
    total_rows = 0
    for tbl in VERIFY_TABLES:
        try:
            c1 = conn_orig.execute(f'SELECT COUNT(*) FROM [{tbl}]').fetchone()[0]
            c2 = conn_bak.execute(f'SELECT COUNT(*) FROM [{tbl}]').fetchone()[0]
            total_rows += c1
            if c1 != c2:
                print(f"  ERROR: {tbl} mismatch: orig={c1}, backup={c2}")
                all_match = False
            else:
                print(f"  {tbl}: {c1} rows OK")
        except Exception as e:
            print(f"  WARNING: {tbl}: {e}")

    conn_orig.close()
    conn_bak.close()

    if all_match:
        print(f"\n  LOCAL BACKUP VERIFIED: {os.path.basename(dst)}")
        print(f"  Size: {bak_size/1024:.0f} KB | Tables: {len(VERIFY_TABLES)} | Rows: {total_rows:,}")
    else:
        print(f"\n  WARNING: Backup has mismatches!")

    return dst


def rotate_backups():
    """Keep only MAX_BACKUPS most recent."""
    all_patterns = [
        os.path.join(BACKUP_DIR, 'uslap_v3_backup_*.db'),
        os.path.join(BACKUP_DIR, 'uslap_database_v3_FULL_backup_*.db')
    ]
    all_backups = []
    for pat in all_patterns:
        all_backups.extend(glob.glob(pat))
    all_backups = sorted(all_backups, key=os.path.getmtime, reverse=True)

    if len(all_backups) > MAX_BACKUPS:
        for f in all_backups[MAX_BACKUPS:]:
            os.remove(f)
            print(f"  Rotated out: {os.path.basename(f)}")

    remaining = sorted(all_backups[:MAX_BACKUPS], key=os.path.getmtime, reverse=True)
    print(f"\n  Backup inventory ({len(remaining)}/{MAX_BACKUPS}):")
    for f in remaining:
        sz = os.path.getsize(f) / 1024
        mt = datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M')
        print(f"    {os.path.basename(f):50s} {sz:>8.0f} KB  {mt}")


def backup_to_icloud():
    """Copy .db to iCloud Drive — survives laptop loss."""
    os.makedirs(ICLOUD_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(ICLOUD_DIR, f'uslap_v3_{ts}.db')

    # Also keep a "latest" copy for quick access
    latest = os.path.join(ICLOUD_DIR, 'uslap_v3_LATEST.db')

    shutil.copy2(DB_PATH, dst)
    shutil.copy2(DB_PATH, latest)

    # Rotate iCloud copies (keep 3)
    pattern = os.path.join(ICLOUD_DIR, 'uslap_v3_2*.db')
    ic_backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for f in ic_backups[3:]:
        os.remove(f)

    sz = os.path.getsize(dst) / 1024
    print(f"\n  iCLOUD BACKUP: {os.path.basename(dst)} ({sz:.0f} KB)")
    print(f"  Location: {ICLOUD_DIR}")
    print(f"  Latest:   uslap_v3_LATEST.db (always current)")
    print(f"  Copies:   {min(len(ic_backups), 3)}/3")


def export_jsonl():
    """
    Export lattice to JSONL — human-readable, git-friendly.
    Anyone with a text editor can read the lattice. No special tools.
    Every line = one row = independently verifiable.
    """
    os.makedirs(JSONL_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    total_rows = 0
    total_files = 0

    for tbl in EXPORT_TABLES:
        try:
            rows = conn.execute(f'SELECT * FROM [{tbl}]').fetchall()
            if not rows:
                continue

            fname = os.path.join(JSONL_DIR, f'{tbl}_{ts}.jsonl')
            with open(fname, 'w', encoding='utf-8') as f:
                for row in rows:
                    d = dict(row)
                    f.write(json.dumps(d, ensure_ascii=False) + '\n')

            total_rows += len(rows)
            total_files += 1
            print(f"  {tbl}: {len(rows)} rows")
        except Exception as e:
            print(f"  WARNING: {tbl}: {e}")

    conn.close()

    # Also create a manifest
    manifest = {
        'export_date': datetime.now().isoformat(),
        'db_source': DB_PATH,
        'db_size_kb': os.path.getsize(DB_PATH) / 1024,
        'tables_exported': total_files,
        'total_rows': total_rows,
        'format': 'JSONL (one JSON object per line)',
        'encoding': 'UTF-8',
        'architecture': 'Seven-Surah (KEY/KERNEL/SEED/NARRATIVE/COMPILER/INDEX/HANDLER)',
        'license': 'Open — no secrets, no black boxes. Q15:9.',
        'verification': 'Every phonetic chain is independently verifiable with a Quran and a dictionary.'
    }
    mf = os.path.join(JSONL_DIR, f'MANIFEST_{ts}.json')
    with open(mf, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n  JSONL EXPORT: {total_files} tables, {total_rows:,} rows")
    print(f"  Location: {JSONL_DIR}")
    print(f"  Manifest: MANIFEST_{ts}.json")


def github_instructions():
    """Print instructions for GitHub distribution."""
    print(f"""
  ══════════════════════════════════════════════════════════
  GITHUB DISTRIBUTION — Every clone = a new node
  ══════════════════════════════════════════════════════════

  The lattice is 12 MB — fits directly on GitHub (limit 100 MB).
  JSONL exports are even smaller — pure text, git-diff friendly.

  SETUP (one time):
    cd "{os.path.dirname(SCRIPT_DIR)}"
    git init
    git remote add origin https://github.com/YOUR_USERNAME/uslap-lattice.git

  PUSH (after each session):
    # Export fresh JSONL
    python3 {os.path.join(SCRIPT_DIR, 'uslap_backup.py')} jsonl

    # Stage exports + DB
    cd "{os.path.dirname(SCRIPT_DIR)}"
    git add Code_files/exports/ Code_files/uslap_database_v3.db
    git commit -m "Lattice update — $(date +%Y-%m-%d)"
    git push origin main

  WHY PUBLIC:
    - Spanner replicates to 5 locked data centres
    - USLaP replicates to every human who clones the repo
    - Every clone can independently verify every chain
    - No IAM, no paywall, no black box
    - Q15:9: the preservation is through distribution
  ══════════════════════════════════════════════════════════
""")


def print_summary():
    """Print overall SEED layer status."""
    conn = sqlite3.connect(DB_PATH)
    counts = {}
    for tbl in VERIFY_TABLES:
        try:
            c = conn.execute(f'SELECT COUNT(*) FROM [{tbl}]').fetchone()[0]
            counts[tbl] = c
        except:
            counts[tbl] = 0
    conn.close()

    # Check existing backups
    local_count = len(glob.glob(os.path.join(BACKUP_DIR, 'uslap_v3_backup_*.db')))
    icloud_exists = os.path.exists(os.path.join(ICLOUD_DIR, 'uslap_v3_LATEST.db'))
    jsonl_count = len(glob.glob(os.path.join(JSONL_DIR, '*.jsonl')))

    print(f"""
  ══ al-Falaq (SEED) STATUS ══
  DB size:     {os.path.getsize(DB_PATH)/1024:.0f} KB
  Core rows:   {sum(counts.values()):,}
  Local:       {local_count}/{MAX_BACKUPS} backups
  iCloud:      {'ACTIVE' if icloud_exists else 'NOT SET UP'}
  JSONL:       {jsonl_count} export files
  GitHub:      {'Run: python3 uslap_backup.py github' if jsonl_count == 0 else 'Ready for push'}
""")


# ── MAIN ──
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'local'

    print(f"══ USLaP SEED (al-Falaq) — {datetime.now().strftime('%Y-%m-%d %H:%M')} ══")
    print(f"Source: {DB_PATH}\n")

    if mode == 'local':
        dst = create_backup()
        if dst:
            rotate_backups()

    elif mode == 'icloud':
        dst = create_backup()
        if dst:
            rotate_backups()
        backup_to_icloud()

    elif mode == 'jsonl':
        export_jsonl()

    elif mode == 'full':
        dst = create_backup()
        if dst:
            rotate_backups()
        backup_to_icloud()
        export_jsonl()
        print_summary()

    elif mode == 'github':
        github_instructions()

    elif mode == 'status':
        print_summary()

    else:
        print(f"Unknown mode: {mode}")
        print("Modes: local | icloud | jsonl | full | github | status")
