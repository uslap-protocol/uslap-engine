#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر ARḌ — Operating Kernel (Layer 3)

Root: أ-ر-ض
Q2:22 الَّذِي جَعَلَ لَكُمُ الْأَرْضَ فِرَاشًا — who made for you the ground a bed

The ground layer: file system, process execution, environment, time.

File System (مِلَفَّات):
    اِقْرَأْ_مِلَفّ   — read file       root: ق-ر-أ + م-ل-ف
    اُكْتُبْ_مِلَفّ   — write file      root: ك-ت-ب + م-ل-ف
    أَضِفْ_مِلَفّ     — append to file   root: ض-ي-ف
    مِلَفَّات         — list dir         root: م-ل-ف
    مَوْجُود          — path exists      root: و-ج-د
    اِمْسَحْ          — delete file      root: م-س-ح
    اِنْقُلْ          — move/rename      root: ن-ق-ل
    اِنْسَخْ_مِلَفّ   — copy file        root: ن-س-خ
    مَسَار            — path operations  root: س-ي-ر

Process (عَمَلِيَّات):
    نَفِّذْ           — execute command  root: ن-ف-ذ
    بِيئَة            — environment var  root: ب-ي-أ

Time (وَقْت):
    وَقْت             — current time     root: و-ق-ت
    اِنْتَظِرْ        — sleep/wait       root: ن-ظ-ر
    قِسْ              — measure duration  root: ق-ي-س

System (نِظَام):
    مَسَار_حَالِي      — current dir
    مَسَار_بَيْت       — home dir
    مَسَار_مُطْلَق     — absolute path
"""

import sys
import os
import shutil
import subprocess
import time as _time
import glob as _glob
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════
# ARABIC ERROR
# ═══════════════════════════════════════════════════════════════════════

class خَطَأ_أَرْض(Exception):
    """ARḌ kernel error"""
    pass


# ═══════════════════════════════════════════════════════════════════════
# FILE SYSTEM — مِلَفَّات
# ═══════════════════════════════════════════════════════════════════════

def اِقْرَأْ_مِلَفّ(path, ترميز="utf-8"):
    """
    اِقْرَأْ مِلَفّ — Read file contents (root: ق-ر-أ + م-ل-ف)
    Q96:1 اقْرَأْ — READ

    Returns string contents of the file.

    Usage:
        كُنْ نَصّ ← اِقْرَأْ_مِلَفّ("data.txt")
    """
    try:
        with open(path, 'r', encoding=ترميز) as f:
            return f.read()
    except FileNotFoundError:
        raise خَطَأ_أَرْض(f'مِلَفّ غَيْر مَوْجُود: {path}')
    except PermissionError:
        raise خَطَأ_أَرْض(f'لَا صَلَاحِيَّة لِلقِرَاءَة: {path}')
    except UnicodeDecodeError:
        raise خَطَأ_أَرْض(f'خَطَأ تَرْمِيز: {path}')


def اُكْتُبْ_مِلَفّ(path, content, ترميز="utf-8"):
    """
    اُكْتُبْ مِلَفّ — Write to file (root: ك-ت-ب + م-ل-ف)
    Q96:4 عَلَّمَ بِالْقَلَمِ — taught by the pen

    Overwrites file. Creates parent dirs if needed.

    Usage:
        اُكْتُبْ_مِلَفّ("output.txt", "بِسْمِ اللَّهِ")
    """
    try:
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(path, 'w', encoding=ترميز) as f:
            f.write(str(content))
        return True
    except (PermissionError, OSError) as e:
        raise خَطَأ_أَرْض(f'لَا صَلَاحِيَّة لِلكِتَابَة: {path} ({e})')


def أَضِفْ_مِلَفّ(path, content, ترميز="utf-8"):
    """
    أَضِفْ مِلَفّ — Append to file (root: ض-ي-ف, add/host)

    Usage:
        أَضِفْ_مِلَفّ("log.txt", "سَطْر جَدِيد\\n")
    """
    try:
        with open(path, 'a', encoding=ترميز) as f:
            f.write(str(content))
        return True
    except PermissionError:
        raise خَطَأ_أَرْض(f'لَا صَلَاحِيَّة لِلكِتَابَة: {path}')


def سُطُور_مِلَفّ(path, ترميز="utf-8"):
    """
    سُطُور مِلَفّ — Read file as lines (root: س-ط-ر)

    Returns list of lines (stripped).

    Usage:
        كُنْ سُطُور ← سُطُور_مِلَفّ("data.txt")
    """
    text = اِقْرَأْ_مِلَفّ(path, ترميز)
    return text.splitlines()


def مِلَفَّات(path=".", نَمَط="*"):
    """
    مِلَفَّات — List directory contents (root: م-ل-ف)

    Args:
        path: Directory to list
        نَمَط: Glob pattern (default "*")

    Returns list of filenames.

    Usage:
        كُنْ ق ← مِلَفَّات(".")
        كُنْ ب ← مِلَفَّات(".", نَمَط="*.أمر")
    """
    full = os.path.join(path, نَمَط)
    return sorted(_glob.glob(full))


def مَوْجُود(path):
    """
    مَوْجُود — Check if path exists (root: و-ج-د, to find/exist)

    Usage:
        إِنْ مَوْجُود("data.txt"):
            اُكْتُبْ("مَوْجُود")
    """
    return os.path.exists(path)


def مِلَفّ_أَمْ_مُجَلَّد(path):
    """
    مِلَفّ أَمْ مُجَلَّد — Is it a file or directory?

    Returns "مِلَفّ", "مُجَلَّد", or "غَيْر_مَوْجُود"
    """
    if os.path.isfile(path):
        return "مِلَفّ"
    elif os.path.isdir(path):
        return "مُجَلَّد"
    return "غَيْر_مَوْجُود"


def حَجْم(path):
    """
    حَجْم — File size in bytes (root: ح-ج-م)

    Usage:
        كُنْ ح ← حَجْم("data.txt")
    """
    if not os.path.exists(path):
        raise خَطَأ_أَرْض(f'مِلَفّ غَيْر مَوْجُود: {path}')
    return os.path.getsize(path)


def اِمْسَحْ(path):
    """
    اِمْسَحْ — Delete file or empty directory (root: م-س-ح, to wipe)

    Usage:
        اِمْسَحْ("temp.txt")
    """
    if not os.path.exists(path):
        raise خَطَأ_أَرْض(f'مِلَفّ غَيْر مَوْجُود: {path}')
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        return True
    except PermissionError:
        raise خَطَأ_أَرْض(f'لَا صَلَاحِيَّة لِلحَذْف: {path}')
    except OSError as e:
        raise خَطَأ_أَرْض(f'خَطَأ حَذْف: {e}')


def اِنْقُلْ(مَصْدَر, هَدَف):
    """
    اِنْقُلْ — Move/rename file (root: ن-ق-ل, to transfer)

    Usage:
        اِنْقُلْ("old.txt", "new.txt")
    """
    if not os.path.exists(مَصْدَر):
        raise خَطَأ_أَرْض(f'مَصْدَر غَيْر مَوْجُود: {مَصْدَر}')
    try:
        shutil.move(مَصْدَر, هَدَف)
        return True
    except Exception as e:
        raise خَطَأ_أَرْض(f'خَطَأ نَقْل: {e}')


def اِنْسَخْ_مِلَفّ(مَصْدَر, هَدَف):
    """
    اِنْسَخْ مِلَفّ — Copy file (root: ن-س-خ)
    Q2:106 مَا نَنسَخْ مِنْ آيَةٍ

    Usage:
        اِنْسَخْ_مِلَفّ("original.txt", "backup.txt")
    """
    if not os.path.exists(مَصْدَر):
        raise خَطَأ_أَرْض(f'مَصْدَر غَيْر مَوْجُود: {مَصْدَر}')
    try:
        shutil.copy2(مَصْدَر, هَدَف)
        return True
    except Exception as e:
        raise خَطَأ_أَرْض(f'خَطَأ نَسْخ: {e}')


def أَنْشِئْ_مُجَلَّد(path):
    """
    أَنْشِئْ مُجَلَّد — Create directory (root: ن-ش-أ)

    Creates parent directories as needed.

    Usage:
        أَنْشِئْ_مُجَلَّد("output/reports")
    """
    os.makedirs(path, exist_ok=True)
    return True


# ═══════════════════════════════════════════════════════════════════════
# PATH OPERATIONS — مَسَار
# ═══════════════════════════════════════════════════════════════════════

def مَسَار_حَالِي():
    """مَسَار حَالِي — Current working directory (root: س-ي-ر)"""
    return os.getcwd()


def مَسَار_بَيْت():
    """مَسَار بَيْت — Home directory"""
    return os.path.expanduser('~')


def مَسَار_مُطْلَق(path):
    """مَسَار مُطْلَق — Absolute path"""
    return os.path.abspath(path)


def اِسْم_مِلَفّ(path):
    """اِسْم مِلَفّ — Filename from path"""
    return os.path.basename(path)


def مُجَلَّد_مِلَفّ(path):
    """مُجَلَّد مِلَفّ — Directory from path"""
    return os.path.dirname(path)


def اِمْتِدَاد(path):
    """اِمْتِدَاد — File extension"""
    return os.path.splitext(path)[1]


def صِلْ_مَسَار(*parts):
    """صِلْ مَسَار — Join path components"""
    return os.path.join(*parts)


# ═══════════════════════════════════════════════════════════════════════
# PROCESS EXECUTION — عَمَلِيَّات
# ═══════════════════════════════════════════════════════════════════════

def نَفِّذْ(أَمْر, مُهْلَة=30):
    """
    نَفِّذْ — Execute a shell command (root: ن-ف-ذ, penetrate/execute)

    Args:
        أَمْر: Command string to execute
        مُهْلَة: Timeout in seconds (default 30)

    Returns dict with:
        خُرُوج (stdout), خَطَأ (stderr), رَمْز (return code)

    Usage:
        كُنْ ن ← نَفِّذْ("ls -la")
        اُكْتُبْ(خُذْ(ن, "خُرُوج"))
    """
    try:
        result = subprocess.run(
            أَمْر, shell=True, capture_output=True, text=True,
            timeout=مُهْلَة
        )
        return {
            'خُرُوج': result.stdout,
            'خَطَأ': result.stderr,
            'رَمْز': result.returncode,
        }
    except subprocess.TimeoutExpired:
        raise خَطَأ_أَرْض(f'اِنْتِهَاء المُهْلَة ({مُهْلَة} ثَانِيَة): {أَمْر}')
    except Exception as e:
        raise خَطَأ_أَرْض(f'خَطَأ تَنْفِيذ: {e}')


def نَفِّذْ_أَمْر(أَمْر, مُهْلَة=30):
    """
    نَفِّذْ أَمْر — Execute and return just stdout (convenience).

    Usage:
        كُنْ نَصّ ← نَفِّذْ_أَمْر("date")
    """
    result = نَفِّذْ(أَمْر, مُهْلَة)
    if result['رَمْز'] != 0:
        raise خَطَأ_أَرْض(f'أَمْر فَشَل (رَمْز {result["رَمْز"]}): {result["خَطَأ"].strip()}')
    return result['خُرُوج'].strip()


# ═══════════════════════════════════════════════════════════════════════
# ENVIRONMENT — بِيئَة
# ═══════════════════════════════════════════════════════════════════════

def بِيئَة(اِسْم, قِيمَة_اِفْتِرَاضِيَّة=None):
    """
    بِيئَة — Get environment variable (root: ب-ي-أ)

    Usage:
        كُنْ مَسَار ← بِيئَة("PATH")
        كُنْ مُسْتَخْدِم ← بِيئَة("USER", "غَيْر_مَعْرُوف")
    """
    return os.environ.get(اِسْم, قِيمَة_اِفْتِرَاضِيَّة)


def اِجْعَلْ_بِيئَة(اِسْم, قِيمَة):
    """
    اِجْعَلْ بِيئَة — Set environment variable

    Usage:
        اِجْعَلْ_بِيئَة("MY_VAR", "value")
    """
    os.environ[اِسْم] = str(قِيمَة)
    return True


# ═══════════════════════════════════════════════════════════════════════
# TIME — وَقْت
# ═══════════════════════════════════════════════════════════════════════

def وَقْت():
    """
    وَقْت — Current timestamp (root: و-ق-ت)

    Returns seconds since epoch as float.

    Usage:
        كُنْ الآن ← وَقْت()
    """
    return _time.time()


def وَقْت_نَصّ(تَنْسِيق="%Y-%m-%d %H:%M:%S"):
    """
    وَقْت نَصّ — Current time as formatted string

    Usage:
        كُنْ ت ← وَقْت_نَصّ()
        اُكْتُبْ(ت)
    """
    return _time.strftime(تَنْسِيق)


def اِنْتَظِرْ(ثَوَانٍ):
    """
    اِنْتَظِرْ — Sleep/wait (root: ن-ظ-ر, to watch/wait)

    Usage:
        اِنْتَظِرْ(٢)
    """
    _time.sleep(ثَوَانٍ)


def قِسْ(دَالَّة):
    """
    قِسْ — Measure execution time (root: ق-ي-س, to measure)

    Returns (result, elapsed_seconds).

    Usage:
        كُنْ ن، ز ← قِسْ(مَضْرُوب، ١٠)
    """
    start = _time.time()
    result = دَالَّة()
    elapsed = _time.time() - start
    return result, elapsed


# ═══════════════════════════════════════════════════════════════════════
# JSON — تَنْسِيق
# ═══════════════════════════════════════════════════════════════════════

def اِقْرَأْ_جسن(path):
    """اِقْرَأْ JSON file, return dict/list."""
    text = اِقْرَأْ_مِلَفّ(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise خَطَأ_أَرْض(f'خَطَأ تَنْسِيق JSON: {e}')


def اُكْتُبْ_جسن(path, data):
    """اُكْتُبْ data as JSON file."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    اُكْتُبْ_مِلَفّ(path, text)
    return True


def مِنْ_جسن(text):
    """Parse JSON string to dict/list."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise خَطَأ_أَرْض(f'خَطَأ تَنْسِيق JSON: {e}')


def إِلَى_جسن(data):
    """Convert dict/list to JSON string."""
    return json.dumps(data, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# SYSTEM INFO — نِظَام
# ═══════════════════════════════════════════════════════════════════════

def نِظَام():
    """
    نِظَام — System info dict

    Returns: {"مِنَصَّة": platform, "مُسْتَخْدِم": user, "مَسَار": cwd}
    """
    return {
        'مِنَصَّة': sys.platform,
        'مُسْتَخْدِم': os.environ.get('USER', os.environ.get('USERNAME', '')),
        'مَسَار': os.getcwd(),
        'بَيْثُون': sys.version.split()[0],
    }


if __name__ == '__main__':
    print('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    print(f'ARḌ Kernel — أ-ر-ض')
    print()

    info = نِظَام()
    for k, v in info.items():
        print(f'  {k}: {v}')

    print()
    print(f'وَقْت: {وَقْت_نَصّ()}')
    print(f'مَسَار: {مَسَار_حَالِي()}')
    print(f'بَيْت: {مَسَار_بَيْت()}')

    print()
    amr_files = مِلَفَّات('.', نَمَط='*.أمر')
    print(f'مِلَفَّات .أمر: {len(amr_files)}')
    for f in amr_files:
        print(f'  {اِسْم_مِلَفّ(f)} ({حَجْم(f)} bytes)')
