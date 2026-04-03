#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر LAWḤ — Persistent Storage Engine (Layer 2)

Root: ل-و-ح
Q85:22 فِي لَوْحٍ مَّحْفُوظٍ — in a preserved tablet

Structured read/write interface to SQLite databases.
Wraps raw SQL with Arabic-named operations:

    لَوْح       — the tablet (connection manager)
    صَحِيفَة    — a page/table (schema definition)
    سَطْر       — a row/line (record)
    عَمُود      — a column/pillar

Operations:
    اِكْتِبْ    — write/inscribe (INSERT)         root: ك-ت-ب
    اِقْرَأْ    — read (SELECT)                    root: ق-ر-أ  Q96:1
    بَدِّلْ     — replace/update (UPDATE)          root: ب-د-ل
    اِمْحُ      — erase (DELETE)                   root: م-ح-و
    أَنْشِئْ    — create (CREATE TABLE)            root: ن-ش-أ
    عُدَّ       — count                            root: ع-د-د
    اِبْحَثْ    — search/find                      root: ب-ح-ث
"""

import sys
import os
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import json
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════
# ARABIC ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════

class خَطَأ_لَوْح(Exception):
    """LAWḤ storage error (root: خ-ط-أ)"""
    pass


# Map sqlite3 errors to Arabic
_SQL_ERROR_MAP = {
    'no such table': 'صَحِيفَة غَيْر مَوْجُودَة (table not found)',
    'no such column': 'عَمُود غَيْر مَوْجُود (column not found)',
    'table already exists': 'صَحِيفَة مَوْجُودَة بِالفِعْل (table exists)',
    'UNIQUE constraint failed': 'قَيْد التَّفَرُّد مُنْتَهَك (unique violation)',
    'NOT NULL constraint failed': 'قَيْد غَيْر فَارِغ مُنْتَهَك (NOT NULL violation)',
    'FOREIGN KEY constraint failed': 'قَيْد المِفْتَاح الخَارِجِي مُنْتَهَك (FK violation)',
    'near': 'خَطَأ فِي الصِّيَاغَة (syntax error)',
    'CONTAMINATION SHIELD': 'دِرْع التَّلَوُّث: مُصْطَلَح مَحْظُور (contamination blocked)',
    'database is locked': 'اللَّوْح مُقْفَل (database locked)',
    'disk I/O error': 'خَطَأ قِرَاءَة/كِتَابَة (I/O error)',
}


def _wrap_sql_error(e):
    """Convert sqlite3 error to Arabic خَطَأ_لَوْح."""
    msg = str(e)
    for pattern, arabic in _SQL_ERROR_MAP.items():
        if pattern in msg:
            return خَطَأ_لَوْح(f'{arabic}: {msg}')
    return خَطَأ_لَوْح(f'خَطَأ قَاعِدَة البَيَانَات: {msg}')


# ═══════════════════════════════════════════════════════════════════════
# لَوْح — THE TABLET (Connection Manager)
# ═══════════════════════════════════════════════════════════════════════

class لَوْح_مَحْفُوظ:
    """
    لَوْح مَحْفُوظ — Preserved Tablet (Database Connection Manager)

    Q85:22 فِي لَوْحٍ مَّحْفُوظٍ — in a preserved tablet

    Usage:
        كُنْ ل ← لَوْح_مَحْفُوظ("path/to/db.db")
        ل.أَنْشِئْ("users", {"name": "TEXT", "age": "INTEGER"})
        ل.اِكْتِبْ("users", {"name": "أحمد", "age": 30})
        كُنْ نَتَائِج ← ل.اِقْرَأْ("users")
    """

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'uslap_database_v3.db'
            )
        self._path = db_path
        self._conn = None

    def _connect(self):
        """Get or create connection."""
        if self._conn is None:
            self._conn = _uslap_connect(self._path) if _HAS_WRAPPER else sqlite3.connect(self._path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _exec(self, sql, params=None):
        """Execute SQL with Arabic error wrapping."""
        conn = self._connect()
        try:
            if params:
                return conn.execute(sql, params)
            return conn.execute(sql)
        except sqlite3.Error as e:
            raise _wrap_sql_error(e)

    def _exec_commit(self, sql, params=None):
        """Execute SQL, commit, return cursor. Arabic errors."""
        cursor = self._exec(sql, params)
        self._conn.commit()
        return cursor

    def أَغْلِقْ(self):
        """أَغْلِقْ — Close the tablet (root: غ-ل-ق)"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, *args):
        self.أَغْلِقْ()

    @contextmanager
    def مُعَامَلَة(self):
        """
        مُعَامَلَة — Transaction (root: ع-م-ل, same as اِعْمَلْ)
        Atomic block: all writes succeed or all fail.

        Usage:
            مَعَ ل.مُعَامَلَة():
                ل.اِكْتِبْ(...)
                ل.اِكْتِبْ(...)
        """
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    # ─── أَنْشِئْ — CREATE ─────────────────────────────────────────

    def أَنْشِئْ(self, table_name, columns, if_not_exists=True):
        """
        أَنْشِئْ — Create a table/page (root: ن-ش-أ, origination)

        Args:
            table_name: Name of the table (صَحِيفَة)
            columns: dict of {column_name: column_type}
                     Types: "TEXT", "INTEGER", "REAL", "BLOB"
            if_not_exists: Skip if table already exists

        Usage:
            ل.أَنْشِئْ("entries", {
                "id": "INTEGER PRIMARY KEY",
                "word": "TEXT NOT NULL",
                "root": "TEXT",
                "meaning": "TEXT"
            })
        """
        exists = "IF NOT EXISTS " if if_not_exists else ""
        col_defs = ', '.join(f'[{name}] {typ}' for name, typ in columns.items())
        sql = f'CREATE TABLE {exists}[{table_name}] ({col_defs})'
        self._exec_commit(sql)
        return True

    # ─── اِكْتِبْ — WRITE/INSERT ──────────────────────────────────

    def اِكْتِبْ(self, table_name, data):
        """
        اِكْتِبْ — Write/inscribe a record (root: ك-ت-ب)
        Q2:282 وَاكْتُبُوهُ — and write it

        Args:
            table_name: Target table
            data: dict of {column: value} OR list of dicts for batch

        Returns:
            Row ID of last inserted row, or count for batch.

        Usage:
            ل.اِكْتِبْ("entries", {"word": "كِتَاب", "root": "ك-ت-ب"})
            ل.اِكْتِبْ("entries", [{"word": "قَلَم"}, {"word": "نُور"}])
        """
        # ═══ QUF GATE — validate before write ═══
        try:
            from amr_quf import validate as _quf_validate
            _quf_data = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
            _quf_result = _quf_validate(_quf_data, domain=table_name)
            if not _quf_result['pass']:
                _evidence = '; '.join(_quf_result.get('evidence', [])[:3])
                raise ValueError(f"QUF BLOCKED: {_evidence}")
        except ImportError:
            pass  # amr_quf not available — contamination triggers still protect

        if isinstance(data, list):
            # Batch insert
            if not data:
                return 0
            keys = list(data[0].keys())
            placeholders = ', '.join(['?'] * len(keys))
            cols = ', '.join(f'[{k}]' for k in keys)
            sql = f'INSERT INTO [{table_name}] ({cols}) VALUES ({placeholders})'
            rows = [tuple(row.get(k) for k in keys) for row in data]
            try:
                conn = self._connect()
                conn.executemany(sql, rows)
                conn.commit()
            except sqlite3.Error as e:
                raise _wrap_sql_error(e)
            return len(rows)
        else:
            # Single insert
            keys = list(data.keys())
            values = [data[k] for k in keys]
            placeholders = ', '.join(['?'] * len(keys))
            cols = ', '.join(f'[{k}]' for k in keys)
            sql = f'INSERT INTO [{table_name}] ({cols}) VALUES ({placeholders})'
            cursor = self._exec_commit(sql, values)
            return cursor.lastrowid

    # ─── اِقْرَأْ — READ/SELECT ───────────────────────────────────

    def اِقْرَأْ(self, table_name, where=None, params=None, columns=None,
                order=None, limit=None, quf_filter=True,
                # Arabic parameter aliases
                شَرْط=None, مُعَامِلَات=None, أَعْمِدَة=None,
                تَرْتِيب=None, حَدّ=None, مُوَثَّق=True):
        """
        اِقْرَأْ — Read from the tablet (root: ق-ر-أ)
        Q96:1 اقْرَأْ — READ

        Args:
            table_name: Source table
            where: WHERE clause (string) or None for all
            params: Parameters for WHERE clause (tuple)
            columns: List of column names, or None for all
            order: ORDER BY clause
            limit: Maximum rows
            quf_filter: If True (default), only return QUF-verified rows
                        (quf_pass='TRUE' or 'PENDING'). Set False for raw access.
            مُوَثَّق: Arabic alias for quf_filter (موثق = verified/documented)

        Returns:
            List of dicts.

        Usage:
            كُنْ كُل ← ل.اِقْرَأْ("roots")                    # verified only
            كُنْ خَام ← ل.اِقْرَأْ("roots", quf_filter=False)  # all rows (raw)
            كُنْ بَعْض ← ل.اِقْرَأْ("roots", where="root_bare LIKE ?", params=("%كتب%",))
        """
        # Resolve Arabic aliases
        where = where or شَرْط
        params = params or مُعَامِلَات
        columns = columns or أَعْمِدَة
        order = order or تَرْتِيب
        limit = limit or حَدّ
        quf_filter = quf_filter and مُوَثَّق  # Both must be True

        cols = '*'
        if columns:
            cols = ', '.join(f'[{c}]' for c in columns)

        sql = f'SELECT {cols} FROM [{table_name}]'

        # QUF gate: only return verified data by default
        quf_clause = None
        if quf_filter:
            # Check if table has quf_pass column
            try:
                col_info = self._exec(f'PRAGMA table_info([{table_name}])').fetchall()
                has_quf = any(c['name'] == 'quf_pass' for c in col_info)
                if has_quf:
                    quf_clause = "quf_pass IN ('TRUE', 'PENDING')"
            except:
                pass

        # Build WHERE
        if where and quf_clause:
            sql += f' WHERE ({where}) AND {quf_clause}'
        elif where:
            sql += f' WHERE {where}'
        elif quf_clause:
            sql += f' WHERE {quf_clause}'

        if order:
            sql += f' ORDER BY {order}'
        if limit:
            sql += f' LIMIT {limit}'

        rows = self._exec(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ─── بَدِّلْ — UPDATE ──────────────────────────────────────────

    def بَدِّلْ(self, table_name, data, where=None, params=None,
               شَرْط=None, مُعَامِلَات=None):
        """
        بَدِّلْ — Replace/update records (root: ب-د-ل)
        Q2:211 وَمَن يُبَدِّلْ نِعْمَةَ اللَّهِ

        Args:
            table_name: Target table
            data: dict of {column: new_value}
            where: WHERE clause (required — no blanket updates)
            params: Parameters for WHERE clause

        Returns:
            Number of rows updated.

        Usage:
            ل.بَدِّلْ("entries", {"meaning": "book"}, where="word = ?", params=("كِتَاب",))
        """
        where = where or شَرْط
        params = params or مُعَامِلَات

        set_parts = []
        set_values = []
        for k, v in data.items():
            set_parts.append(f'[{k}] = ?')
            set_values.append(v)

        sql = f'UPDATE [{table_name}] SET {", ".join(set_parts)} WHERE {where}'

        all_params = set_values
        if params:
            all_params.extend(params)

        cursor = self._exec_commit(sql, all_params)
        return cursor.rowcount

    # ─── اِمْحُ — DELETE ──────────────────────────────────────────

    def اِمْحُ(self, table_name, where=None, params=None,
              شَرْط=None, مُعَامِلَات=None):
        """
        اِمْحُ — Erase records (root: م-ح-و)
        Q13:39 يَمْحُو اللَّهُ مَا يَشَاءُ — Allah erases what He wills

        Args:
            table_name: Target table
            where: WHERE clause (required — no blanket deletes)
            params: Parameters for WHERE clause

        Returns:
            Number of rows deleted.

        Usage:
            ل.اِمْحُ("temp", where="id = ?", params=(42,))
        """
        where = where or شَرْط
        params = params or مُعَامِلَات

        sql = f'DELETE FROM [{table_name}] WHERE {where}'
        cursor = self._exec_commit(sql, params)
        return cursor.rowcount

    # ─── عُدَّ — COUNT ─────────────────────────────────────────────

    def عُدَّ(self, table_name, where=None, params=None, quf_filter=True,
             شَرْط=None, مُعَامِلَات=None, مُوَثَّق=True):
        """
        عُدَّ — Count records (root: ع-د-د)
        Q72:28 وَأَحْصَى كُلَّ شَيْءٍ عَدَدًا

        Usage:
            كُنْ م ← ل.عُدَّ("roots")                    # verified only
            كُنْ ن ← ل.عُدَّ("roots", quf_filter=False)  # all rows
        """
        where = where or شَرْط
        params = params or مُعَامِلَات
        quf_filter = quf_filter and مُوَثَّق

        quf_clause = None
        if quf_filter:
            try:
                col_info = self._exec(f'PRAGMA table_info([{table_name}])').fetchall()
                if any(c['name'] == 'quf_pass' for c in col_info):
                    quf_clause = "quf_pass IN ('TRUE', 'PENDING')"
            except:
                pass

        sql = f'SELECT COUNT(*) as cnt FROM [{table_name}]'
        if where and quf_clause:
            sql += f' WHERE ({where}) AND {quf_clause}'
        elif where:
            sql += f' WHERE {where}'
        elif quf_clause:
            sql += f' WHERE {quf_clause}'

        row = self._exec(sql, params).fetchone()
        return row['cnt']

    # ─── اِبْحَثْ — SEARCH ────────────────────────────────────────

    def اِبْحَثْ(self, table_name, text, columns=None, limit=50, quf_filter=True,
                أَعْمِدَة=None, حَدّ=None, مُوَثَّق=True):
        """
        اِبْحَثْ — Search/investigate (root: ب-ح-ث)
        Q5:31 يَبْحَثُ فِي الْأَرْضِ — investigating in the ground

        Full-text search across specified columns (or all TEXT columns).
        By default only searches QUF-verified rows.

        Usage:
            كُنْ نَتَائِج ← ل.اِبْحَثْ("entries", "كتب")           # verified only
            كُنْ كُل ← ل.اِبْحَثْ("entries", "كتب", quf_filter=False) # all rows
        """
        columns = columns or أَعْمِدَة
        limit = حَدّ if حَدّ is not None else limit
        quf_filter = quf_filter and مُوَثَّق

        if columns is None:
            col_info = self._exec(f'PRAGMA table_info([{table_name}])').fetchall()
            columns = [c['name'] for c in col_info
                       if 'TEXT' in (c['type'] or '').upper()
                       and not c['name'].startswith('quf_')]

        if not columns:
            return []

        conditions = ' OR '.join(
            f'[{col}] LIKE ?' for col in columns
        )
        params = tuple(f'%{text}%' for _ in columns)

        quf_clause = None
        if quf_filter:
            try:
                all_cols = self._exec(f'PRAGMA table_info([{table_name}])').fetchall()
                if any(c['name'] == 'quf_pass' for c in all_cols):
                    quf_clause = "quf_pass IN ('TRUE', 'PENDING')"
            except:
                pass

        if quf_clause:
            sql = f'SELECT * FROM [{table_name}] WHERE ({conditions}) AND {quf_clause} LIMIT {limit}'
        else:
            sql = f'SELECT * FROM [{table_name}] WHERE {conditions} LIMIT {limit}'

        rows = self._exec(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ─── جَدَاوِل — LIST TABLES ───────────────────────────────────

    def جَدَاوِل(self):
        """
        جَدَاوِل — List all tables/pages in the tablet
        Root: ج-د-ل
        """
        rows = self._exec(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r['name'] for r in rows]

    # ─── أَعْمِدَة — LIST COLUMNS ─────────────────────────────────

    def أَعْمِدَة(self, table_name):
        """
        أَعْمِدَة — List columns/pillars of a table
        Root: ع-م-د (pillar/support)
        """
        rows = self._exec(f'PRAGMA table_info([{table_name}])').fetchall()
        return [{'name': r['name'], 'type': r['type'],
                 'notnull': bool(r['notnull']),
                 'pk': bool(r['pk'])} for r in rows]

    # ─── Raw SQL (still available) ─────────────────────────────────

    def نَفِّذْ(self, sql, params=None):
        """
        نَفِّذْ — Execute raw SQL (root: ن-ف-ذ, penetrate/execute)
        For queries that don't fit the structured API.
        """
        cursor = self._exec(sql, params)

        cmd = sql.strip().upper()
        if cmd.startswith('SELECT') or cmd.startswith('PRAGMA'):
            return [dict(r) for r in cursor.fetchall()]
        else:
            self._conn.commit()
            return cursor.rowcount

    # ─── نَسْخ — EXPORT ────────────────────────────────────────────

    def نَسْخ(self, table_name, path, format='json'):
        """
        نَسْخ — Copy/export table data (root: ن-س-خ)
        Q2:106 مَا نَنسَخْ مِنْ آيَةٍ

        Exports table to JSON or CSV.
        """
        rows = self.اِقْرَأْ(table_name)

        if format == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
        elif format == 'csv':
            import csv
            if not rows:
                return 0
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return len(rows)

    # ─── حَمْل — IMPORT ───────────────────────────────────────────

    def حَمْل(self, table_name, path, format='json'):
        """
        حَمْل — Load/import data into table (root: ح-م-ل, carry/load)

        Reads JSON or CSV and inserts into table.
        """
        if format == 'json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif format == 'csv':
            import csv
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            raise ValueError(f'Unknown format: {format}')

        if data:
            return self.اِكْتِبْ(table_name, data)
        return 0


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE — module-level tablet instance for the USLaP DB
# ═══════════════════════════════════════════════════════════════════════

_DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')
اللَّوْح = لَوْح_مَحْفُوظ(_DEFAULT_DB)


if __name__ == '__main__':
    print('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    print(f'LAWḤ Engine — DB: {_DEFAULT_DB}')
    print(f'DB exists: {os.path.exists(_DEFAULT_DB)}')
    print()

    if os.path.exists(_DEFAULT_DB):
        ل = لَوْح_مَحْفُوظ(_DEFAULT_DB)
        tables = ل.جَدَاوِل()
        print(f'جَدَاوِل (tables): {len(tables)}')

        # Count roots
        count = ل.عُدَّ('roots')
        print(f'جُذُور (roots): {count}')

        # Search
        results = ل.اِبْحَثْ('roots', 'كتب', columns=['root_bare'])
        print(f'بَحْث "كتب": {len(results)} results')
        for r in results:
            print(f'  {r}')

        # Read with filter
        rows = ل.اِقْرَأْ('roots', columns=['root_id', 'root_letters'],
                          where='quran_tokens > ?', params=(500,), limit=5)
        print(f'\nTop roots (>500 tokens): {len(rows)}')
        for r in rows:
            print(f'  {r["root_id"]}: {r["root_letters"]}')

        ل.أَغْلِقْ()
