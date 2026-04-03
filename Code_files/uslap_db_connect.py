#!/usr/bin/env python3
"""
USLaP V4 — Central DB Connection
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

ALL tools MUST use this instead of raw sqlite3.connect().
Guarantees: PRAGMA foreign_keys = ON, WAL mode, row_factory.

Usage:
    from uslap_db_connect import connect
    conn = connect()             # default DB
    conn = connect(readonly=True) # read-only mode
"""

import sqlite3
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE, "uslap_database_v3.db")
SCHEMA_VERSION = 5  # V5: tasrif engine, trigger hardening, index expansion


def connect(db_path=None, readonly=False):
    """Return a connection with FK enforcement guaranteed.

    Args:
        db_path: Override DB path. Defaults to uslap_database_v3.db.
        readonly: If True, open in read-only mode (uri=file:...?mode=ro).

    Returns:
        sqlite3.Connection with foreign_keys=ON and WAL journal.
    """
    path = db_path or DB_PATH

    if readonly:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(path)

    # === MANDATORY ENFORCEMENT ===
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row

    # Verify FK is actually on (paranoia check)
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    if fk != 1:
        raise RuntimeError("PRAGMA foreign_keys failed to enable")

    return conn


def verify_schema_version(conn=None):
    """Check that the DB has V4 schema. Returns (version, ok)."""
    c = conn or connect(readonly=True)
    try:
        row = c.execute(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return row[0], row[0] >= SCHEMA_VERSION
        return 0, False
    except Exception:
        return 0, False
    finally:
        if conn is None:
            c.close()
