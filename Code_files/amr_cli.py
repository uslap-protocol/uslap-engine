#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر CLI — Command Line Interface

Entry point: python3 amr_cli.py program.أمر

Modes:
  run     (default) — parse, emit Python, execute
  compile           — parse, emit Python to stdout
  check             — parse only, report errors
"""

import sys
import os
import argparse
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_lexer import tokenize_file, tokenize_source, LexerError
from amr_parser import parse_source, parse_file, print_ast, ParseError
from amr_emitter import emit_source, emit_file, EmitterError


# Arabic translations for common Python runtime errors
RUNTIME_ERROR_MAP = {
    'NameError': 'اِسْم غَيْر مُعَرَّف',          # undefined name
    'TypeError': 'خَطَأ فِي النَّوْع',              # type error
    'ValueError': 'خَطَأ فِي القِيمَة',             # value error
    'IndexError': 'فِهْرِس خَارِج المَدَى',         # index out of range
    'KeyError': 'مِفْتَاح غَيْر مَوْجُود',          # key not found
    'ZeroDivisionError': 'قِسْمَة عَلَى صِفْر',     # division by zero
    'FileNotFoundError': 'مِلَفّ غَيْر مَوْجُود',    # file not found
    'AttributeError': 'صِفَة غَيْر مَوْجُودَة',     # attribute not found
    'RecursionError': 'عُمْق التَّكْرَار تَجَاوَزَ الحَدّ',  # recursion limit
    'OperationalError': 'خَطَأ فِي اللَّوْح',             # sqlite operational error
    'خَطَأ_لَوْح': 'خَطَأ فِي اللَّوْح',                  # LAWH error
    'خَطَأ_أَرْض': 'خَطَأ فِي الأَرْض',                  # ARD error
    'خَطَأ_تَرْجَمَة': 'خَطَأ فِي التَّرْجَمَة',          # Translation error
}


def format_runtime_error(e):
    """Format a Python exception with Arabic error type."""
    err_type = type(e).__name__
    arabic_type = RUNTIME_ERROR_MAP.get(err_type, err_type)
    return f'{arabic_type}: {e}'


def run_file(filepath):
    """Parse, emit Python, and execute an أَمْر file."""
    if not os.path.exists(filepath):
        print(f'مِلَفّ غَيْر مَوْجُود: {filepath}', file=sys.stderr)
        return 1

    try:
        python_code = emit_file(filepath)
    except (LexerError, ParseError, EmitterError) as e:
        print(f'خَطَأ: {e}', file=sys.stderr)
        return 1

    # Write to temp file and execute
    code_dir = os.path.dirname(os.path.abspath(__file__))
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', dir=code_dir,
        delete=False, encoding='utf-8'
    ) as tmp:
        tmp.write(python_code)
        tmp_path = tmp.name

    try:
        # Execute the generated Python
        exec_globals = {'__name__': '__main__', '__file__': tmp_path}
        exec(compile(python_code, filepath, 'exec'), exec_globals)
        return 0
    except Exception as e:
        print(f'خَطَأ تَنْفِيذ: {format_runtime_error(e)}', file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_string(source):
    """Parse, emit, and execute أَمْر source from string."""
    try:
        python_code = emit_source(source)
    except (LexerError, ParseError, EmitterError) as e:
        print(f'خَطَأ: {e}', file=sys.stderr)
        return 1

    try:
        exec_globals = {'__name__': '__main__', '__file__': '<string>'}
        exec(compile(python_code, '<string>', 'exec'), exec_globals)
        return 0
    except Exception as e:
        print(f'خَطَأ تَنْفِيذ: {format_runtime_error(e)}', file=sys.stderr)
        return 1


def compile_file(filepath):
    """Parse and emit Python to stdout."""
    if not os.path.exists(filepath):
        print(f'مِلَفّ غَيْر مَوْجُود: {filepath}', file=sys.stderr)
        return 1

    try:
        python_code = emit_file(filepath)
        print(python_code)
        return 0
    except (LexerError, ParseError, EmitterError) as e:
        print(f'خَطَأ: {e}', file=sys.stderr)
        return 1


def check_file(filepath):
    """Parse only, report errors or success."""
    if not os.path.exists(filepath):
        print(f'مِلَفّ غَيْر مَوْجُود: {filepath}', file=sys.stderr)
        return 1

    try:
        tokens = tokenize_file(filepath)
        print(f'تَحْلِيل: {len(tokens)} tokens')

        from amr_parser import Parser
        parser = Parser(tokens)
        ast = parser.parse()
        print(f'تَحْلِيل: {len(ast.body)} statements')
        print('نَجَاح — no errors found')  # success
        return 0
    except (LexerError, ParseError) as e:
        print(f'خَطَأ: {e}', file=sys.stderr)
        return 1


def repl():
    """Interactive أَمْر REPL (Read-Evaluate-Print Loop)."""
    print('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    print('أَمْر v1.0 — اقْرَأْ')
    print('اُكْتُبْ "خُرُوج" لِلْخُرُوج')
    print()

    # Persistent execution environment
    exec_globals = {'__name__': '__main__', '__file__': '<repl>'}
    # Pre-load runtime
    runtime_code = (
        'import sys, os\n'
        'sys.path.insert(0, os.path.dirname(os.path.abspath("' +
        os.path.dirname(os.path.abspath(__file__)).replace('\\', '\\\\') +
        '")))\n'
        'sys.path.insert(0, "' +
        os.path.dirname(os.path.abspath(__file__)).replace('\\', '\\\\') +
        '")\n'
        'from amr_runtime import *\n'
    )
    exec(compile(runtime_code, '<repl-init>', 'exec'), exec_globals)

    # Multiline input state
    buffer = []
    in_block = False

    while True:
        try:
            prompt = '... ' if in_block else 'أمر> '
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print('\nوَدَاعًا')
            break

        # Exit commands
        if line.strip() in ('خُرُوج', 'exit', 'quit'):
            print('وَدَاعًا')
            break

        # Empty line ends a block
        if not line.strip() and in_block:
            source = '\n'.join(buffer)
            buffer = []
            in_block = False
        elif line.strip().endswith(':'):
            buffer.append(line)
            in_block = True
            continue
        elif in_block:
            buffer.append(line)
            continue
        else:
            source = line

        if not source.strip():
            continue

        try:
            python_code = emit_source(source)
            # Strip the boilerplate (already loaded in exec_globals)
            lines = python_code.split('\n')
            # Remove the import/setup lines
            code_lines = []
            skip = True
            for l in lines:
                if skip and (l.startswith('#') or l.startswith('import ') or
                             l.startswith('sys.') or l.startswith('from amr_') or
                             l.strip() == ''):
                    continue
                skip = False
                code_lines.append(l)
            clean_code = '\n'.join(code_lines)

            if clean_code.strip():
                exec(compile(clean_code, '<repl>', 'exec'), exec_globals)
        except (LexerError, ParseError, EmitterError) as e:
            print(f'خَطَأ: {e}', file=sys.stderr)
        except Exception as e:
            print(f'خَطَأ تَنْفِيذ: {format_runtime_error(e)}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='أَمْر — Root-Derived Programming Language CLI',
        epilog='بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
    )
    parser.add_argument('file', nargs='?', help='Path to .أمر source file')
    parser.add_argument('-c', '--compile', action='store_true',
                        help='Emit Python code to stdout (do not execute)')
    parser.add_argument('--check', action='store_true',
                        help='Parse only, report errors')
    parser.add_argument('-e', '--exec', dest='exec_str', metavar='CODE',
                        help='Execute أَمْر code from string')
    parser.add_argument('--ast', action='store_true',
                        help='Print AST (debug)')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Start interactive REPL')

    args = parser.parse_args()

    # REPL mode
    if args.interactive:
        return repl()

    # Execute from string
    if args.exec_str:
        if args.compile:
            try:
                python_code = emit_source(args.exec_str)
                print(python_code)
                return 0
            except (LexerError, ParseError, EmitterError) as e:
                print(f'خَطَأ: {e}', file=sys.stderr)
                return 1
        return run_string(args.exec_str)

    # No file and no other mode → REPL
    if not args.file:
        return repl()

    # AST debug mode
    if args.ast:
        try:
            ast = parse_file(args.file)
            print_ast(ast)
            return 0
        except (LexerError, ParseError) as e:
            print(f'خَطَأ: {e}', file=sys.stderr)
            return 1

    # Check mode
    if args.check:
        return check_file(args.file)

    # Compile mode
    if args.compile:
        return compile_file(args.file)

    # Default: run
    return run_file(args.file)


if __name__ == '__main__':
    sys.exit(main())
