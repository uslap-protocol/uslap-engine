#!/usr/bin/env python3
"""
USLaP DB/XLSX Sync Checker
Run at start of any session to detect drift between master xlsx and sqlite DB.
Usage: python3 uslap_sync_check.py [--fix]
"""
import sqlite3, openpyxl, os, sys, shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'uslap_database_v3.db')
XLSX_PATH = '/Users/mmsetubal/Documents/USLaP workplace/USLaP_Final_Data_Consolidated_Master_v3.xlsx'
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

SHEET_MAP = {
    'A1_ENTRIES': ('a1_entries', 'entry_id'),
    'A1_ЗАПИСИ': ('a1_записи', 'запись_id'),
    'A2_NAMES_OF_ALLAH': ('a2_names_of_allah', None),
    'A3_QURAN_REFS': ('a3_quran_refs', None),
    'A4_DERIVATIVES': ('a4_derivatives', None),
    'A5_CROSS_REFS': ('a5_cross_refs', None),
    'A6_COUNTRY_NAMES': ('a6_country_names', None),
    'BITIG_A1_ENTRIES': ('bitig_a1_entries', 'entry_id'),
    'CHILD_SCHEMA': ('child_schema', 'entry_id'),
    'CHRONOLOGY': ('chronology', None),
    'M1_PHONETIC_SHIFTS': ('m1_phonetic_shifts', None),
    'M2_DETECTION_PATTERNS': ('m2_detection_patterns', None),
    'M3_SCHOLARS': ('m3_scholars', None),
    'M4_NETWORKS': ('m4_networks', None),
    'UMD_OPERATIONS': ('umd_operations', 'op_id'),
    'SESSION_INDEX': ('session_index', 'id'),
    'ENGINE_QUEUE': ('engine_queue', None),
    'DP_REGISTER': ('dp_register', 'dp_code'),
}

# Known xlsx title/header patterns to skip
SKIP_PATTERNS = ['USLaP', 'Each row', 'DP01', 'ENTRY_ID', 'OP_ID', 'DP_CODE', 'ID']

def is_data_row(row):
    """Filter out xlsx title/header/instruction rows."""
    if row[0] is None:
        return False
    first = str(row[0]).strip()
    for pat in SKIP_PATTERNS:
        if first.startswith(pat) and len(first) > 20:
            return False
    if first in ('ENTRY_ID', 'OP_ID', 'DP_CODE', 'ID'):
        return False
    return True

def check_sync():
    xlsx_mod = datetime.fromtimestamp(os.path.getmtime(XLSX_PATH))
    db_mod = datetime.fromtimestamp(os.path.getmtime(DB_PATH))
    
    print(f"USLaP Sync Check — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  XLSX modified: {xlsx_mod.strftime('%Y-%m-%d %H:%M')}")
    print(f"  DB modified:   {db_mod.strftime('%Y-%m-%d %H:%M')}")
    if xlsx_mod > db_mod:
        print(f"  WARNING: xlsx is NEWER than DB by {(xlsx_mod - db_mod).seconds // 60} min")
    print()

    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    conn = sqlite3.connect(DB_PATH)
    
    drifted = []
    synced = []
    
    for sheet_name, (table_name, _) in SHEET_MAP.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        xlsx_rows = sum(1 for row in ws.iter_rows(min_row=2, values_only=True) if is_data_row(row))
        db_rows = conn.execute(f'SELECT COUNT(*) FROM [{table_name}]').fetchone()[0]
        delta = xlsx_rows - db_rows
        
        if delta == 0:
            synced.append(sheet_name)
        else:
            drifted.append((sheet_name, table_name, xlsx_rows, db_rows, delta))
            tag = 'xlsx AHEAD' if delta > 0 else 'DB AHEAD'
            print(f"  DRIFT: {sheet_name:25s} xlsx={xlsx_rows:>5d}  db={db_rows:>5d}  ({tag} by {abs(delta)})")
    
    wb.close()
    conn.close()
    
    if not drifted:
        print(f"  ALL {len(synced)} mapped sheets SYNCED")
    else:
        print(f"\n  Synced: {len(synced)}, Drifted: {len(drifted)}")
    
    return drifted

def backup_before_fix():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, f'uslap_database_v3_presync_{ts}.db')
    shutil.copy2(DB_PATH, dst)
    print(f"  Pre-sync backup: {dst}")
    return dst

if __name__ == '__main__':
    drifted = check_sync()
    if drifted and '--fix' in sys.argv:
        print("\n--fix flag detected. Manual sync required for safety.")
        print("Run the sync in a Claude session with xlsx inspection.")
    elif drifted:
        print("\nRun with --fix to attempt auto-sync (requires manual verification).")
