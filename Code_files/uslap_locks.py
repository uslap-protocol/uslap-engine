#!/usr/bin/env python3
"""
USLaP Write-Lock Manager — prevents concurrent agent conflicts on shared DB tables.

Usage:
    python3 uslap_locks.py status                     # show all locks + table map
    python3 uslap_locks.py lock AGENT TABLE OPERATION  # acquire lock
    python3 uslap_locks.py unlock AGENT TABLE          # release lock
    python3 uslap_locks.py check TABLE                 # check if table is locked
    python3 uslap_locks.py force-unlock TABLE          # emergency unlock (bbi only)
    python3 uslap_locks.py domains                     # show agent domain ownership

Rules:
    - EXCLUSIVE tables: only the owner agent writes. No lock needed.
    - SHARED tables: agent MUST acquire lock before writing. Lock blocks other agents.
    - Locks auto-expire after 60 minutes (stale lock protection).
    - Only one agent can hold a lock on a given table at a time.
"""

import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uslap_database_v3.db")
STALE_MINUTES = 60  # locks older than this are considered stale


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def status():
    """Show all active locks and table ownership map."""
    conn = get_db()

    # Active locks
    locks = conn.execute("""
        SELECT w.lock_id, w.table_name, w.agent_id, a.agent_name,
               w.locked_at, w.operation,
               CAST((julianday('now') - julianday(w.locked_at)) * 24 * 60 AS INTEGER) as minutes_held
        FROM write_locks w
        JOIN agent_domains a ON w.agent_id = a.agent_id
        WHERE w.status = 'ACTIVE'
        ORDER BY w.locked_at
    """).fetchall()

    print("=" * 70)
    print("USLaP WRITE-LOCK STATUS")
    print("=" * 70)

    if locks:
        print(f"\n  ACTIVE LOCKS ({len(locks)}):")
        for l in locks:
            stale = " *** STALE" if l['minutes_held'] > STALE_MINUTES else ""
            print(f"    [{l['lock_id']}] {l['table_name']} <- {l['agent_id']} ({l['minutes_held']}m){stale}")
            print(f"         Operation: {l['operation']}")
    else:
        print("\n  NO ACTIVE LOCKS — all tables available")

    # Shared table map
    shared = conn.execute("""
        SELECT DISTINCT t.table_name
        FROM table_ownership t
        WHERE t.access_level = 'SHARED'
        ORDER BY t.table_name
    """).fetchall()

    print(f"\n  SHARED TABLES ({len(shared)}) — require lock before writing:")
    for s in shared:
        lock = conn.execute("""
            SELECT agent_id, operation FROM write_locks
            WHERE table_name = ? AND status = 'ACTIVE'
        """, (s['table_name'],)).fetchone()

        if lock:
            print(f"    {s['table_name']:30s} LOCKED by {lock['agent_id']} ({lock['operation']})")
        else:
            print(f"    {s['table_name']:30s} AVAILABLE")

    conn.close()


def lock(agent_id, table_name, operation):
    """Acquire a write lock on a shared table."""
    conn = get_db()

    # Check table is registered
    ownership = conn.execute(
        "SELECT access_level FROM table_ownership WHERE table_name = ? AND owner_agent = ?",
        (table_name, agent_id)
    ).fetchone()

    if not ownership:
        # Check if table exists but belongs to another agent exclusively
        other = conn.execute(
            "SELECT owner_agent, access_level FROM table_ownership WHERE table_name = ?",
            (table_name,)
        ).fetchone()
        if other and other['access_level'] == 'EXCLUSIVE':
            print(f"DENIED: {table_name} is EXCLUSIVE to {other['owner_agent']}. {agent_id} cannot write.")
            conn.close()
            return False
        elif not other:
            print(f"WARNING: {table_name} not in ownership registry. Registering as SHARED.")
            conn.execute(
                "INSERT INTO table_ownership (table_name, owner_agent, access_level) VALUES (?, ?, 'SHARED')",
                (table_name, agent_id)
            )

    # Clean stale locks first
    conn.execute("""
        UPDATE write_locks SET status = 'RELEASED', released_at = datetime('now')
        WHERE status = 'ACTIVE'
        AND CAST((julianday('now') - julianday(locked_at)) * 24 * 60 AS INTEGER) > ?
    """, (STALE_MINUTES,))

    # Check for existing active lock
    existing = conn.execute("""
        SELECT agent_id, operation, locked_at,
               CAST((julianday('now') - julianday(locked_at)) * 24 * 60 AS INTEGER) as minutes_held
        FROM write_locks
        WHERE table_name = ? AND status = 'ACTIVE'
    """, (table_name,)).fetchone()

    if existing:
        if existing['agent_id'] == agent_id:
            print(f"ALREADY LOCKED: {table_name} is already locked by {agent_id} ({existing['operation']})")
            conn.close()
            return True
        else:
            print(f"BLOCKED: {table_name} is locked by {existing['agent_id']} ({existing['minutes_held']}m ago)")
            print(f"         Operation: {existing['operation']}")
            print(f"         Wait for unlock or ask bbi to force-unlock.")
            conn.close()
            return False

    # Acquire lock
    conn.execute("""
        INSERT INTO write_locks (table_name, agent_id, operation) VALUES (?, ?, ?)
    """, (table_name, agent_id, operation))
    conn.commit()
    print(f"LOCKED: {table_name} <- {agent_id} ({operation})")
    conn.close()
    return True


def unlock(agent_id, table_name):
    """Release a write lock."""
    conn = get_db()

    existing = conn.execute("""
        SELECT lock_id, agent_id FROM write_locks
        WHERE table_name = ? AND status = 'ACTIVE'
    """, (table_name,)).fetchone()

    if not existing:
        print(f"NO LOCK: {table_name} is not locked.")
        conn.close()
        return

    if existing['agent_id'] != agent_id:
        print(f"DENIED: {table_name} is locked by {existing['agent_id']}, not {agent_id}. Use force-unlock.")
        conn.close()
        return

    conn.execute("""
        UPDATE write_locks SET status = 'RELEASED', released_at = datetime('now')
        WHERE lock_id = ?
    """, (existing['lock_id'],))
    conn.commit()
    print(f"UNLOCKED: {table_name} (was held by {agent_id})")
    conn.close()


def check(table_name):
    """Check if a table is locked and by whom."""
    conn = get_db()

    existing = conn.execute("""
        SELECT agent_id, operation, locked_at,
               CAST((julianday('now') - julianday(locked_at)) * 24 * 60 AS INTEGER) as minutes_held
        FROM write_locks
        WHERE table_name = ? AND status = 'ACTIVE'
    """, (table_name,)).fetchone()

    if existing:
        stale = " (STALE)" if existing['minutes_held'] > STALE_MINUTES else ""
        print(f"LOCKED: {table_name} <- {existing['agent_id']} ({existing['minutes_held']}m){stale}")
        print(f"  Operation: {existing['operation']}")
    else:
        # Check ownership
        owners = conn.execute(
            "SELECT owner_agent, access_level FROM table_ownership WHERE table_name = ?",
            (table_name,)
        ).fetchall()
        if owners:
            if owners[0]['access_level'] == 'EXCLUSIVE':
                print(f"EXCLUSIVE: {table_name} belongs to {owners[0]['owner_agent']} (no lock needed for owner)")
            else:
                print(f"AVAILABLE: {table_name} is SHARED and currently unlocked")
        else:
            print(f"UNREGISTERED: {table_name} is not in the ownership registry")
    conn.close()


def force_unlock(table_name):
    """Emergency unlock — bbi override only."""
    conn = get_db()
    result = conn.execute("""
        UPDATE write_locks SET status = 'RELEASED', released_at = datetime('now')
        WHERE table_name = ? AND status = 'ACTIVE'
    """, (table_name,))
    conn.commit()
    if result.rowcount > 0:
        print(f"FORCE-UNLOCKED: {table_name} ({result.rowcount} lock(s) released)")
    else:
        print(f"NO LOCK: {table_name} was not locked")
    conn.close()


def domains():
    """Show agent domain ownership."""
    conn = get_db()

    agents = conn.execute("SELECT * FROM agent_domains ORDER BY agent_id").fetchall()

    print("=" * 70)
    print("AGENT DOMAIN OWNERSHIP")
    print("=" * 70)

    for a in agents:
        print(f"\n  {a['agent_id']}: {a['agent_name']}")
        print(f"  {a['description']}")

        exclusive = conn.execute(
            "SELECT table_name, notes FROM table_ownership WHERE owner_agent = ? AND access_level = 'EXCLUSIVE' ORDER BY table_name",
            (a['agent_id'],)
        ).fetchall()

        shared = conn.execute(
            "SELECT table_name, notes FROM table_ownership WHERE owner_agent = ? AND access_level = 'SHARED' ORDER BY table_name",
            (a['agent_id'],)
        ).fetchall()

        if exclusive:
            print(f"  EXCLUSIVE ({len(exclusive)} tables):")
            for t in exclusive:
                print(f"    - {t['table_name']:35s} {t['notes'] or ''}")

        if shared:
            print(f"  SHARED ({len(shared)} tables) — lock required:")
            for t in shared:
                print(f"    - {t['table_name']:35s} {t['notes'] or ''}")

    conn.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        status()
    elif cmd == "lock" and len(sys.argv) >= 5:
        lock(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    elif cmd == "unlock" and len(sys.argv) >= 4:
        unlock(sys.argv[2], sys.argv[3])
    elif cmd == "check" and len(sys.argv) >= 3:
        check(sys.argv[2])
    elif cmd == "force-unlock" and len(sys.argv) >= 3:
        force_unlock(sys.argv[2])
    elif cmd == "domains":
        domains()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
