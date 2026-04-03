#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر RUNTIME — Built-in Functions and DB Integration

Layer 2: ل-و-ح / LAWḤ (preserved tablet) — the storage engine
Layer 3: أ-ر-ض / ARḌ (the ground) — the operating kernel

Built-in functions:
  اُكْتُبْ (print)   — ك-ت-ب root: write/inscribe
  اِقْرَأْ (input)   — ق-ر-أ root: read/recite (Q96:1)
  خُذْ (get)         — أ-خ-ذ root: take/seize
  اِفْتَحْ (open)    — ف-ت-ح root: open
  أَغْلِقْ (close)   — غ-ل-ق root: close/lock
  اِبْحَثْ (search)  — ب-ح-ث root: investigate
  صِلْ (join)        — و-ص-ل root: connect
  اِقْطَعْ (split)   — ق-ط-ع root: cut/sever
  اِنْسَخْ (copy)    — ن-س-خ root: copy
  بَدِّلْ (replace)  — ب-د-ل root: substitute
  اُحْسُبْ (compute) — ح-س-ب root: reckon
  أَرْسِلْ (send)    — ر-س-ل root: send
  اِقْبَلْ (receive) — ق-ب-ل root: accept
  اِجْعَلْ (set)     — ج-ع-ل root: make/place
  اِحْذِفْ (delete)  — ح-ذ-ف root: remove

  DB integration:
  لَوْح (lawh)       — query uslap_database_v3.db
"""

import sys
import os
import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False


# ═══════════════════════════════════════════════════════════════════════
# ARABIC EXCEPTION CLASS
# ═══════════════════════════════════════════════════════════════════════

class ضَلَال(Exception):
    """ضَلَال — Error/Exception (root: ض-ل-ل, displacement)
    Q1:7 وَلَا الضَّالِّينَ — not those who went astray.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════
# CORE BUILT-INS
# ═══════════════════════════════════════════════════════════════════════

def اُكْتُبْ(*args, **kwargs):
    """اُكْتُبْ — print/write (root: ك-ت-ب)"""
    print(*args, **kwargs)


def اِقْرَأْ(prompt=''):
    """اِقْرَأْ — read input (root: ق-ر-أ, Q96:1)"""
    return input(prompt)


def خُذْ(collection, index=None, default=None):
    """خُذْ — get/take (root: أ-خ-ذ)"""
    if index is not None:
        if isinstance(collection, dict):
            return collection.get(index, default)
        elif isinstance(collection, (list, tuple, str)):
            try:
                return collection[index]
            except (IndexError, KeyError):
                return default
    return collection


def اِفْتَحْ(path, mode='r', encoding='utf-8'):
    """اِفْتَحْ — open file (root: ف-ت-ح)"""
    return open(path, mode=mode, encoding=encoding)


def أَغْلِقْ(obj):
    """أَغْلِقْ — close (root: غ-ل-ق)"""
    if hasattr(obj, 'close'):
        obj.close()


def صِلْ(separator, items):
    """صِلْ — join/connect (root: و-ص-ل)"""
    return separator.join(str(i) for i in items)


def اِقْطَعْ(text, separator=None):
    """اِقْطَعْ — split/slice (root: ق-ط-ع)"""
    if separator is None:
        return text.split()
    return text.split(separator)


def اِنْسَخْ(obj):
    """اِنْسَخْ — copy (root: ن-س-خ)"""
    if isinstance(obj, list):
        return obj[:]
    elif isinstance(obj, dict):
        return dict(obj)
    elif isinstance(obj, set):
        return set(obj)
    return obj


def بَدِّلْ(text, old, new):
    """بَدِّلْ — replace/substitute (root: ب-د-ل)"""
    return text.replace(old, new)


def اُحْسُبْ(expression):
    """اُحْسُبْ — compute/calculate (root: ح-س-ب)"""
    if isinstance(expression, str):
        return eval(expression)
    return expression


def أَرْسِلْ(message, destination=None):
    """أَرْسِلْ — send (root: ر-س-ل)"""
    if destination is None:
        sys.stdout.write(str(message))
        sys.stdout.flush()
    else:
        raise NotImplementedError('Network sending not yet implemented')


def اِقْبَلْ(source=None):
    """اِقْبَلْ — receive/accept (root: ق-ب-ل)"""
    if source is None:
        return sys.stdin.readline().rstrip('\n')
    raise NotImplementedError('Network receiving not yet implemented')


def اِجْعَلْ(collection, key, value):
    """اِجْعَلْ — set/assign (root: ج-ع-ل)"""
    if isinstance(collection, dict):
        collection[key] = value
    elif isinstance(collection, list):
        collection[key] = value
    return collection


def اِحْذِفْ(collection, key):
    """اِحْذِفْ — delete/remove (root: ح-ذ-ف)"""
    if isinstance(collection, dict):
        return collection.pop(key, None)
    elif isinstance(collection, list):
        return collection.pop(key)


def اِبْحَثْ(text, pattern):
    """اِبْحَثْ — search/find (root: ب-ح-ث)"""
    if isinstance(text, str):
        return pattern in text
    elif isinstance(text, (list, tuple)):
        return pattern in text
    elif isinstance(text, dict):
        return pattern in text
    return False


# ═══════════════════════════════════════════════════════════════════════
# TYPE CONVERSION HELPERS
# ═══════════════════════════════════════════════════════════════════════

def عَدَد(value):
    """Convert to integer (root: ع-د-د)"""
    return int(value)


def كَسْر(value):
    """Convert to float (root: ك-س-ر)"""
    return float(value)


def كَلِمَة(value):
    """Convert to string (root: ك-ل-م)"""
    return str(value)


def صَفّ(*args):
    """Create list (root: ص-ف-ف)"""
    if len(args) == 1 and hasattr(args[0], '__iter__') and not isinstance(args[0], str):
        return list(args[0])
    return list(args)


def زَوْج(*args):
    """Create tuple (root: ز-و-ج)"""
    if len(args) == 1 and hasattr(args[0], '__iter__') and not isinstance(args[0], str):
        return tuple(args[0])
    return tuple(args)


def جَمْع(**kwargs):
    """Create dict (root: ج-م-ع)"""
    return dict(**kwargs)


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def طُول(obj):
    """Length — ط-و-ل root (height/length)"""
    return len(obj)


def مَدَى(*args):
    """Range — م-د-ى root (extent/scope)"""
    return range(*args)


# ═══════════════════════════════════════════════════════════════════════
# DATABASE INTEGRATION — لَوْح / LAWḤ (the preserved tablet)
# ═══════════════════════════════════════════════════════════════════════

# Locate the database
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')


def لَوْح(query, params=None):
    """
    لَوْح — Query the preserved tablet (uslap_database_v3.db)
    Root: ل-و-ح
    Q85:22 فِي لَوْحٍ مَّحْفُوظٍ — in a preserved tablet

    Usage:
        نَتَائِج ← لَوْح("SELECT * FROM roots WHERE root_id = ?", ("R001",))
        لِكُلِّ صَف فِي نَتَائِج:
            اُكْتُبْ(صَف)
    """
    if not os.path.exists(_DB_PATH):
        raise FileNotFoundError(f'Database not found: {_DB_PATH}')

    conn = _uslap_connect(_DB_PATH) if _HAS_WRAPPER else sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        cmd = query.strip().upper()
        if cmd.startswith('SELECT') or cmd.startswith('PRAGMA'):
            rows = cursor.fetchall()
            # Convert to list of dicts for easy access
            result = []
            for row in rows:
                result.append(dict(row))
            return result
        else:
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()


def جَدَاوِل():
    """
    جَدَاوِل — List all tables in the tablet
    Root: ج-د-ل (table/schedule)
    """
    rows = لَوْح("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r['name'] for r in rows]


# ═══════════════════════════════════════════════════════════════════════
# LAWḤ STORAGE ENGINE (Layer 2)
# ═══════════════════════════════════════════════════════════════════════

from amr_lawh import لَوْح_مَحْفُوظ, اللَّوْح


# ═══════════════════════════════════════════════════════════════════════
# ARḌ OPERATING KERNEL (Layer 3)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# تَرْجَمَة TRANSLATION ENGINE (Layer 4)
# ═══════════════════════════════════════════════════════════════════════

from amr_tarjama import تَرْجِمْ, جُذُور_مُشْتَرَكَة, مُتَرْجِم
from amr_uzbek import (
    detect_script as كَشْف_خَطّ,
    latin_to_cyrillic as لَاتِينِي_إِلَى_سِيرِيلِي,
    cyrillic_to_latin as سِيرِيلِي_إِلَى_لَاتِينِي,
    arabic_to_latin as عَرَبِي_إِلَى_لَاتِينِي,
    latin_to_arabic as لَاتِينِي_إِلَى_عَرَبِي,
    to_all_scripts as كُلّ_الخُطُوط,
    normalize as تَطْبِيع,
)


from amr_ard import (
    # File system
    اِقْرَأْ_مِلَفّ, اُكْتُبْ_مِلَفّ, أَضِفْ_مِلَفّ, سُطُور_مِلَفّ,
    مِلَفَّات, مَوْجُود, مِلَفّ_أَمْ_مُجَلَّد, حَجْم,
    اِمْسَحْ, اِنْقُلْ, اِنْسَخْ_مِلَفّ, أَنْشِئْ_مُجَلَّد,
    # Path
    مَسَار_حَالِي, مَسَار_بَيْت, مَسَار_مُطْلَق,
    اِسْم_مِلَفّ, مُجَلَّد_مِلَفّ, اِمْتِدَاد, صِلْ_مَسَار,
    # Process
    نَفِّذْ_أَمْر,
    # Environment
    بِيئَة, اِجْعَلْ_بِيئَة,
    # Time
    وَقْت, وَقْت_نَصّ, اِنْتَظِرْ,
    # JSON
    اِقْرَأْ_جسن, اُكْتُبْ_جسن, مِنْ_جسن, إِلَى_جسن,
    # System
    نِظَام,
    # Error
    خَطَأ_أَرْض,
)


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

حَقّ = True
بَاطِل = False
عَدَم = None


if __name__ == '__main__':
    اُكْتُبْ('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    اُكْتُبْ(f'Runtime loaded. DB path: {_DB_PATH}')
    اُكْتُبْ(f'DB exists: {os.path.exists(_DB_PATH)}')

    if os.path.exists(_DB_PATH):
        tables = جَدَاوِل()
        اُكْتُبْ(f'Tables in لَوْح: {len(tables)}')
        for t in tables[:10]:
            اُكْتُبْ(f'  - {t}')
