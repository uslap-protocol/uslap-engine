#!/usr/bin/env python3
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import re

def extract_parent_ops(parent_op_str):
    """Extract individual parent operations from strings like 'UMD-RL1 + UMD-ST1'"""
    if not parent_op_str:
        return []
    # Split by various separators
    ops = re.split(r'[·,\+\s]+', str(parent_op_str))
    # Filter for operation codes (UMD- prefix)
    parent_ops = []
    for op in ops:
        op = op.strip()
        if op and re.match(r'^UMD-', op):
            parent_ops.append(op)
    return parent_ops

def extract_dp_codes(dp_string):
    """Extract individual DP codes from strings like 'DP08 · DP07 · DP11 · DP15'"""
    if not dp_string:
        return []
    # Split by various separators
    codes = re.split(r'[·,\s]+', str(dp_string))
    # Filter for DP codes (start with DP followed by digits or word)
    dp_codes = []
    for code in codes:
        code = code.strip()
        if code and (re.match(r'^DP\d+', code) or re.match(r'^DP-', code)):
            dp_codes.append(code)
    return dp_codes

def main():
    conn = _uslap_connect("uslap_database.db") if _HAS_WRAPPER else sqlite3.connect("uslap_database.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    # Test the extraction
    cursor.execute("SELECT entry_id, parent_op, dp_codes FROM child_schema")
    rows = cursor.fetchall()
    
    for entry_id, parent_op, dp_codes_str in rows:
        print(f"\n{entry_id}:")
        print(f"  parent_op: {parent_op}")
        print(f"  dp_codes_str: {dp_codes_str}")
        
        parent_ops = extract_parent_ops(parent_op)
        dp_codes = extract_dp_codes(dp_codes_str)
        
        print(f"  extracted parent_ops: {parent_ops}")
        print(f"  extracted dp_codes: {dp_codes}")
        
        # Check if parent ops exist in umd_operations
        for op in parent_ops:
            cursor.execute("SELECT op_id FROM umd_operations WHERE op_id = ?", (op,))
            exists = cursor.fetchone()
            print(f"    {op} exists in umd_operations: {bool(exists)}")
    
    conn.close()

if __name__ == "__main__":
    main()