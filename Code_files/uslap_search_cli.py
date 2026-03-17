#!/usr/bin/env python3
"""
USLaP Database Search CLI
Searches across all tables for keywords and returns only what is documented.
No content generation - reports only what exists in the database.
"""

import sqlite3
import sys
import argparse
from typing import List, Dict, Any

def search_all_tables(conn, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for keyword across all tables in the database.
    Returns a dictionary mapping table names to lists of matching rows.
    """
    cursor = conn.cursor()
    results = {}
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        # Get column names for this table
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if not columns:
            continue
        
        # Build search query across all text columns
        column_conditions = []
        for col in columns:
            column_conditions.append(f"{col} LIKE ?")
        
        # Search in all text columns
        where_clause = " OR ".join(column_conditions)
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        
        # Execute search with keyword parameter
        params = [f"%{keyword}%"] * len(columns)
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        if rows:
            # Convert to list of dictionaries
            table_results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                table_results.append(row_dict)
            results[table] = table_results
    
    return results

def format_results(results: Dict[str, List[Dict[str, Any]]], keyword: str) -> str:
    """Format search results for display."""
    if not results:
        return f"No results found for keyword: '{keyword}'"
    
    output = []
    output.append(f"=== SEARCH RESULTS FOR: '{keyword}' ===\n")
    
    for table, rows in results.items():
        output.append(f"\n--- {table.upper()} ({len(rows)} matches) ---")
        
        for i, row in enumerate(rows, 1):
            output.append(f"\nMatch {i}:")
            for key, value in row.items():
                if value is not None:
                    # Truncate long values for display
                    if isinstance(value, str) and len(value) > 200:
                        value = value[:197] + "..."
                    output.append(f"  {key}: {value}")
    
    return "\n".join(output)

def search_cross_reference(conn, keyword: str) -> str:
    """Specialized search for cross-reference relationships."""
    cursor = conn.cursor()
    
    # Search for entries by ENTRY_ID
    cursor.execute("""
        SELECT c.entry_id, c.shell_name, c.orig_root, c.parent_op, 
               GROUP_CONCAT(DISTINCT x.dp_ref) as dp_refs
        FROM child_schema c
        LEFT JOIN cross_reference x ON c.entry_id = x.entry_id
        WHERE c.entry_id LIKE ? OR c.shell_name LIKE ? OR c.orig_root LIKE ?
        GROUP BY c.entry_id
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    
    rows = cursor.fetchall()
    
    if not rows:
        return ""
    
    output = ["\n=== CROSS-REFERENCE RELATIONSHIPS ==="]
    for entry_id, shell_name, orig_root, parent_op, dp_refs in rows:
        output.append(f"\nENTRY: {entry_id}")
        output.append(f"  Shell: {shell_name}")
        output.append(f"  Origin: {orig_root}")
        output.append(f"  Parent Operation: {parent_op}")
        if dp_refs:
            output.append(f"  DP Codes: {dp_refs}")
    
    return "\n".join(output)

def search_operations_by_dp(conn, dp_code: str) -> str:
    """Find all entries and operations associated with a specific DP code."""
    cursor = conn.cursor()
    
    # Find entries with this DP code
    cursor.execute("""
        SELECT DISTINCT c.entry_id, c.shell_name, c.parent_op
        FROM child_schema c
        JOIN cross_reference x ON c.entry_id = x.entry_id
        WHERE x.dp_ref LIKE ?
    """, (f"%{dp_code}%",))
    
    entries = cursor.fetchall()
    
    # Find DP definition
    cursor.execute("SELECT * FROM dp_register WHERE dp_code LIKE ?", (f"%{dp_code}%",))
    dp_info = cursor.fetchone()
    
    output = []
    if dp_info:
        cursor.execute("PRAGMA table_info(dp_register)")
        columns = [row[1] for row in cursor.fetchall()]
        output.append("\n=== DP CODE DEFINITION ===")
        for i, col in enumerate(columns):
            if dp_info[i] is not None:
                output.append(f"{col}: {dp_info[i]}")
    
    if entries:
        output.append("\n=== ENTRIES USING THIS DP CODE ===")
        for entry_id, shell_name, parent_op in entries:
            output.append(f"\n{entry_id}: {shell_name}")
            output.append(f"  Parent Operation: {parent_op}")
    
    return "\n".join(output) if output else ""

def main():
    parser = argparse.ArgumentParser(
        description="USLaP Database Search CLI - Search across all tables for keywords",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "سَلْوَى"          # Search for Arabic text
  %(prog)s "DP08"             # Search for DP codes
  %(prog)s "UMD-OP1"          # Search for operation codes
  %(prog)s "SLV"              # Search for entry IDs
  %(prog)s "Berber"           # Search for terms
        """
    )
    
    parser.add_argument("keyword", help="Keyword to search for across all tables")
    parser.add_argument("--db", default="uslap_database_v3.db", 
                       help="Path to SQLite database (default: uslap_database_v3.db)")
    parser.add_argument("--cross-ref", action="store_true",
                       help="Show cross-reference relationships for matches")
    parser.add_argument("--dp-detail", action="store_true",
                       help="Show detailed DP code information when searching for DP codes")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    try:
        conn = sqlite3.connect(args.db)
        conn.text_factory = str  # Preserve UTF-8
        
        # Perform search
        results = search_all_tables(conn, args.keyword)
        
        # Display results
        print(format_results(results, args.keyword))
        
        # Show cross-reference relationships if requested
        if args.cross_ref or args.keyword.upper().startswith(('DP', 'UMD-')):
            cross_ref_info = search_cross_reference(conn, args.keyword)
            if cross_ref_info:
                print(cross_ref_info)
        
        # Show DP code detail if requested
        if args.dp_detail or args.keyword.upper().startswith('DP'):
            dp_info = search_operations_by_dp(conn, args.keyword)
            if dp_info:
                print(dp_info)
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()