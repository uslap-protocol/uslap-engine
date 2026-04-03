#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر EMITTER — AST → Python Source Code

Transforms the أَمْر AST into valid Python source code.
Each أَمْر keyword maps to its Python equivalent via KEYWORDS dict.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from amr_parser import (
        parse_source, parse_file, Program, FuncDef, VarDecl, Assignment,
        IfStmt, WhileLoop, ForLoop, ReturnStmt, BreakStmt, PassStmt,
        DeleteStmt, ImportStmt, TryStmt, RaiseStmt, ExprStmt,
        BinOp, UnaryOp, Compare, BoolOp, NotOp, FuncCall, Name, Num, Str,
        ListLiteral, DictLiteral, TupleLiteral, Subscript, Attribute,
        Constant, Kwarg, ParseError
    )
    from amr_lexer import LexerError
except ImportError:
    from Code_files.amr_parser import (
        parse_source, parse_file, Program, FuncDef, VarDecl, Assignment,
        IfStmt, WhileLoop, ForLoop, ReturnStmt, BreakStmt, PassStmt,
        DeleteStmt, ImportStmt, TryStmt, RaiseStmt, ExprStmt,
        BinOp, UnaryOp, Compare, BoolOp, NotOp, FuncCall, Name, Num, Str,
        ListLiteral, DictLiteral, TupleLiteral, Subscript, Attribute,
        Constant, Kwarg, ParseError
    )
    from Code_files.amr_lexer import LexerError


# ═══════════════════════════════════════════════════════════════════════
# EMITTER
# ═══════════════════════════════════════════════════════════════════════

class EmitterError(Exception):
    pass


class Emitter:
    """Transforms أَمْر AST into Python source code."""

    def __init__(self):
        self.indent_level = 0
        self.lines = []

    def indent(self):
        return '    ' * self.indent_level

    def emit_line(self, code):
        self.lines.append(f'{self.indent()}{code}')

    def emit(self, node):
        """Emit Python code for an AST node."""
        method = f'emit_{type(node).__name__}'
        handler = getattr(self, method, None)
        if handler is None:
            raise EmitterError(f'لَا مُعَالِج لِنَوْع العُقْدَة: {type(node).__name__}')
        return handler(node)

    # ─── PROGRAM ──────────────────────────────────────────────────────

    def emit_Program(self, node):
        # Prepend runtime import
        self.lines.append('# -*- coding: utf-8 -*-')
        self.lines.append('# Generated from أَمْر source')
        self.lines.append('import sys, os')
        self.lines.append('sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))')
        self.lines.append('from amr_runtime import *')
        self.lines.append('')

        for stmt in node.body:
            self.emit(stmt)

        return '\n'.join(self.lines)

    # ─── STATEMENTS ───────────────────────────────────────────────────

    def emit_FuncDef(self, node):
        params = ', '.join(node.params)
        self.emit_line(f'def {node.name}({params}):')
        self.indent_level += 1
        if not node.body:
            self.emit_line('pass')
        else:
            for stmt in node.body:
                self.emit(stmt)
        self.indent_level -= 1
        self.emit_line('')  # blank line after function

    def emit_VarDecl(self, node):
        val = self.emit_expr(node.value)
        self.emit_line(f'{node.name} = {val}')

    def emit_Assignment(self, node):
        target = self.emit_expr(node.target)
        val = self.emit_expr(node.value)
        self.emit_line(f'{target} = {val}')

    def emit_IfStmt(self, node):
        cond = self.emit_expr(node.condition)
        self.emit_line(f'if {cond}:')
        self.indent_level += 1
        if not node.body:
            self.emit_line('pass')
        else:
            for stmt in node.body:
                self.emit(stmt)
        self.indent_level -= 1

        for elif_cond, elif_body in node.elif_clauses:
            c = self.emit_expr(elif_cond)
            self.emit_line(f'elif {c}:')
            self.indent_level += 1
            if not elif_body:
                self.emit_line('pass')
            else:
                for stmt in elif_body:
                    self.emit(stmt)
            self.indent_level -= 1

        if node.else_body:
            self.emit_line('else:')
            self.indent_level += 1
            for stmt in node.else_body:
                self.emit(stmt)
            self.indent_level -= 1

    def emit_WhileLoop(self, node):
        cond = self.emit_expr(node.condition)
        self.emit_line(f'while {cond}:')
        self.indent_level += 1
        if not node.body:
            self.emit_line('pass')
        else:
            for stmt in node.body:
                self.emit(stmt)
        self.indent_level -= 1

    def emit_ForLoop(self, node):
        iterable = self.emit_expr(node.iterable)
        self.emit_line(f'for {node.var} in {iterable}:')
        self.indent_level += 1
        if not node.body:
            self.emit_line('pass')
        else:
            for stmt in node.body:
                self.emit(stmt)
        self.indent_level -= 1

    def emit_ReturnStmt(self, node):
        if node.value is not None:
            val = self.emit_expr(node.value)
            self.emit_line(f'return {val}')
        else:
            self.emit_line('return')

    def emit_BreakStmt(self, node):
        self.emit_line('break')

    def emit_PassStmt(self, node):
        self.emit_line('pass')

    def emit_DeleteStmt(self, node):
        target = self.emit_expr(node.target)
        self.emit_line(f'del {target}')

    def emit_ImportStmt(self, node):
        if node.names:
            names = ', '.join(node.names)
            self.emit_line(f'from {node.module} import {names}')
        else:
            self.emit_line(f'import {node.module}')

    def emit_TryStmt(self, node):
        self.emit_line('try:')
        self.indent_level += 1
        if not node.body:
            self.emit_line('pass')
        else:
            for stmt in node.body:
                self.emit(stmt)
        self.indent_level -= 1

        if node.exc_name:
            self.emit_line(f'except (ضَلَال, Exception) as {node.exc_name}:')
        else:
            self.emit_line('except (ضَلَال, Exception):')
        self.indent_level += 1
        if not node.handler_body:
            self.emit_line('pass')
        else:
            for stmt in node.handler_body:
                self.emit(stmt)
        self.indent_level -= 1

    def emit_RaiseStmt(self, node):
        if node.value is not None:
            val = self.emit_expr(node.value)
            self.emit_line(f'raise ضَلَال({val})')
        else:
            self.emit_line('raise')

    def emit_ExprStmt(self, node):
        expr = self.emit_expr(node.expr)
        self.emit_line(expr)

    # ─── EXPRESSIONS ──────────────────────────────────────────────────

    def emit_expr(self, node):
        """Emit an expression and return as string."""
        method = f'emit_expr_{type(node).__name__}'
        handler = getattr(self, method, None)
        if handler is None:
            raise EmitterError(f'لَا مُعَالِج لِتَعْبِير: {type(node).__name__}')
        return handler(node)

    def emit_expr_BinOp(self, node):
        left = self.emit_expr(node.left)
        right = self.emit_expr(node.right)
        return f'({left} {node.op} {right})'

    def emit_expr_UnaryOp(self, node):
        operand = self.emit_expr(node.operand)
        return f'({node.op}{operand})'

    def emit_expr_Compare(self, node):
        parts = [self.emit_expr(node.left)]
        for op, comp in zip(node.ops, node.comparators):
            parts.append(op)
            parts.append(self.emit_expr(comp))
        return f'({" ".join(parts)})'

    def emit_expr_BoolOp(self, node):
        py_op = 'and' if node.op == 'وَ' else 'or'
        parts = [self.emit_expr(v) for v in node.values]
        return f'({f" {py_op} ".join(parts)})'

    def emit_expr_NotOp(self, node):
        operand = self.emit_expr(node.operand)
        return f'(not {operand})'

    def emit_expr_FuncCall(self, node):
        func = self.emit_expr(node.func)
        parts = [self.emit_expr(a) for a in node.args]
        for kw in node.kwargs:
            parts.append(f'{kw.name}={self.emit_expr(kw.value)}')
        return f'{func}({", ".join(parts)})'

    def emit_expr_Name(self, node):
        return node.name

    def emit_expr_Num(self, node):
        return repr(node.value)

    def emit_expr_Str(self, node):
        return repr(node.value)

    def emit_expr_Constant(self, node):
        return repr(node.value)

    def emit_expr_ListLiteral(self, node):
        elements = ', '.join(self.emit_expr(e) for e in node.elements)
        return f'[{elements}]'

    def emit_expr_DictLiteral(self, node):
        pairs = ', '.join(
            f'{self.emit_expr(k)}: {self.emit_expr(v)}'
            for k, v in node.pairs
        )
        return f'{{{pairs}}}'

    def emit_expr_TupleLiteral(self, node):
        elements = ', '.join(self.emit_expr(e) for e in node.elements)
        if len(node.elements) == 1:
            return f'({elements},)'
        return f'({elements})'

    def emit_expr_Subscript(self, node):
        obj = self.emit_expr(node.obj)
        index = self.emit_expr(node.index)
        return f'{obj}[{index}]'

    def emit_expr_Attribute(self, node):
        obj = self.emit_expr(node.obj)
        return f'{obj}.{node.attr}'


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def emit_source(source, filename='<input>'):
    """Parse أَمْر source and emit Python code."""
    ast = parse_source(source, filename)
    emitter = Emitter()
    return emitter.emit(ast)


def emit_file(filepath):
    """Parse a .أمر file and emit Python code."""
    ast = parse_file(filepath)
    emitter = Emitter()
    return emitter.emit(ast)


if __name__ == '__main__':
    test_code = '''كُنْ س ← ٥
اُكْتُبْ(س + ١٠)
إِنْ س فَوْقَ ٣:
    اُكْتُبْ("كبير")
وَإِلَّا:
    اُكْتُبْ("صغير")

اِعْمَلْ مَضْرُوب(ن):
    إِنْ ن دُونَ ٢:
        اِرْجِعْ ١
    اِرْجِعْ ن * مَضْرُوب(ن - ١)

اُكْتُبْ(مَضْرُوب(٥))
'''
    try:
        python_code = emit_source(test_code)
        print('═══ GENERATED PYTHON ═══')
        print(python_code)
        print()
        print('═══ EXECUTION ═══')
        # We'll test execution after runtime is built
    except (EmitterError, ParseError, LexerError) as e:
        print(f'ERROR: {e}')
