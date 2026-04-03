#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر PARSER — Recursive Descent Parser

Builds AST from token stream produced by amr_lexer.py.
Indentation-scoped (like Python).

Handles:
  - Function definition (اِعْمَلْ)
  - Conditionals (إِنْ / فَـ / أَوْ / وَإِلَّا)
  - Loops (كَرِّرْ / لِكُلِّ)
  - Variable declaration (كُنْ)
  - Return (اِرْجِعْ)
  - Break (قِفْ)
  - Try/raise (قِ / أَنْذِرْ)
  - Import (اِسْتَدْعِ)
  - Delete (اِحْذِفْ)
  - Pass/begin (اِبْدَأْ)
  - Expressions and function calls
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from amr_lexer import tokenize_source, tokenize_file, TokenType, Token, LexerError
    from amr_keywords import KEYWORDS
except ImportError:
    from Code_files.amr_lexer import tokenize_source, tokenize_file, TokenType, Token, LexerError
    from Code_files.amr_keywords import KEYWORDS


# ═══════════════════════════════════════════════════════════════════════
# AST NODE TYPES
# ═══════════════════════════════════════════════════════════════════════

class AST:
    """Base AST node."""
    pass


class Program(AST):
    def __init__(self, body):
        self.body = body  # list of statements

    def __repr__(self):
        return f'Program({len(self.body)} statements)'


class FuncDef(AST):
    """اِعْمَلْ name(params): body"""
    def __init__(self, name, params, body, line=0):
        self.name = name
        self.params = params  # list of parameter names (strings)
        self.body = body      # list of statements
        self.line = line

    def __repr__(self):
        return f'FuncDef({self.name}, params={self.params})'


class VarDecl(AST):
    """كُنْ name ← value"""
    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value  # expression AST
        self.line = line

    def __repr__(self):
        return f'VarDecl({self.name})'


class Assignment(AST):
    """name ← value  (without كُنْ)"""
    def __init__(self, target, value, line=0):
        self.target = target  # can be Name, Subscript, Attribute
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Assignment({self.target})'


class IfStmt(AST):
    """إِنْ condition: body [أَوْ condition: body]* [وَإِلَّا: body]"""
    def __init__(self, condition, body, elif_clauses=None, else_body=None, line=0):
        self.condition = condition
        self.body = body
        self.elif_clauses = elif_clauses or []  # list of (condition, body)
        self.else_body = else_body or []
        self.line = line

    def __repr__(self):
        return f'IfStmt(elifs={len(self.elif_clauses)}, has_else={bool(self.else_body)})'


class WhileLoop(AST):
    """كَرِّرْ condition: body"""
    def __init__(self, condition, body, line=0):
        self.condition = condition
        self.body = body
        self.line = line

    def __repr__(self):
        return f'WhileLoop()'


class ForLoop(AST):
    """لِكُلِّ var فِي iterable: body"""
    def __init__(self, var, iterable, body, line=0):
        self.var = var
        self.iterable = iterable
        self.body = body
        self.line = line

    def __repr__(self):
        return f'ForLoop({self.var})'


class ReturnStmt(AST):
    """اِرْجِعْ [value]"""
    def __init__(self, value=None, line=0):
        self.value = value
        self.line = line

    def __repr__(self):
        return f'ReturnStmt()'


class BreakStmt(AST):
    """قِفْ"""
    def __init__(self, line=0):
        self.line = line


class PassStmt(AST):
    """اِبْدَأْ"""
    def __init__(self, line=0):
        self.line = line


class DeleteStmt(AST):
    """اِحْذِفْ target"""
    def __init__(self, target, line=0):
        self.target = target
        self.line = line


class ImportStmt(AST):
    """اِسْتَدْعِ module [مِنْ name]"""
    def __init__(self, module, names=None, line=0):
        self.module = module
        self.names = names  # list of names to import, or None for whole module
        self.line = line


class TryStmt(AST):
    """قِ: body أَنْذِرْ: handler"""
    def __init__(self, body, handler_body, exc_name=None, line=0):
        self.body = body
        self.handler_body = handler_body
        self.exc_name = exc_name
        self.line = line


class RaiseStmt(AST):
    """أَنْذِرْ [exception]"""
    def __init__(self, value=None, line=0):
        self.value = value
        self.line = line


class ExprStmt(AST):
    """Expression used as a statement (e.g., function call)."""
    def __init__(self, expr, line=0):
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f'ExprStmt({self.expr})'


# Expression nodes

class BinOp(AST):
    """Binary operation: left op right"""
    def __init__(self, left, op, right, line=0):
        self.left = left
        self.op = op
        self.right = right
        self.line = line

    def __repr__(self):
        return f'BinOp({self.op})'


class UnaryOp(AST):
    """Unary operation: op operand"""
    def __init__(self, op, operand, line=0):
        self.op = op
        self.operand = operand
        self.line = line


class Compare(AST):
    """Comparison: left op right (chained)"""
    def __init__(self, left, ops, comparators, line=0):
        self.left = left
        self.ops = ops                # list of operator strings
        self.comparators = comparators  # list of expressions
        self.line = line

    def __repr__(self):
        return f'Compare({self.ops})'


class BoolOp(AST):
    """Boolean operation: وَ / لَا"""
    def __init__(self, op, values, line=0):
        self.op = op      # 'وَ' or 'أَوْ'
        self.values = values
        self.line = line


class NotOp(AST):
    """لَا expr"""
    def __init__(self, operand, line=0):
        self.operand = operand
        self.line = line


class FuncCall(AST):
    """name(args, kwargs)"""
    def __init__(self, func, args, line=0, kwargs=None):
        self.func = func    # expression (usually Name)
        self.args = args    # list of positional expressions
        self.kwargs = kwargs or []  # list of Kwarg nodes
        self.line = line

    def __repr__(self):
        return f'FuncCall({self.func})'


class Name(AST):
    """Variable reference."""
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

    def __repr__(self):
        return f'Name({self.name})'


class Num(AST):
    """Numeric literal."""
    def __init__(self, value, line=0):
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Num({self.value})'


class Str(AST):
    """String literal."""
    def __init__(self, value, line=0):
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Str({self.value!r})'


class ListLiteral(AST):
    """[elements]"""
    def __init__(self, elements, line=0):
        self.elements = elements
        self.line = line


class DictLiteral(AST):
    """{key: value, ...}"""
    def __init__(self, pairs, line=0):
        self.pairs = pairs  # list of (key_expr, val_expr)
        self.line = line


class TupleLiteral(AST):
    """(a, b, c)"""
    def __init__(self, elements, line=0):
        self.elements = elements
        self.line = line


class Kwarg(AST):
    """name=value keyword argument."""
    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Kwarg({self.name})'


class Subscript(AST):
    """obj[index]"""
    def __init__(self, obj, index, line=0):
        self.obj = obj
        self.index = index
        self.line = line


class Attribute(AST):
    """obj.attr"""
    def __init__(self, obj, attr, line=0):
        self.obj = obj
        self.attr = attr
        self.line = line


class Constant(AST):
    """حَقّ / بَاطِل / عَدَم"""
    def __init__(self, value, line=0):
        self.value = value  # True / False / None
        self.line = line


# ═══════════════════════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════════════════════

class ParseError(Exception):
    def __init__(self, message, line=0, col=0):
        self.line = line
        self.col = col
        super().__init__(f'خَطَأ تَحْلِيل سَطْر {line}:{col}: {message}')


# Map أَمْر comparison keywords to Python operators
COMPARISON_KEYWORDS = {
    'سَوَاء': '==',
    'فَوْقَ': '>',
    'دُونَ': '<',
}

# Map أَمْر boolean/constant keywords
CONSTANT_KEYWORDS = {
    'حَقّ': True,
    'بَاطِل': False,
    'عَدَم': None,
}


class Parser:
    """Recursive descent parser for أَمْر token streams."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None)

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, None)

    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, type_, value=None):
        tok = self.current()
        if tok.type != type_:
            # Special case: keyword used where identifier expected
            if type_ == TokenType.IDENTIFIER and tok.type == TokenType.KEYWORD:
                raise ParseError(
                    f'«{tok.value}» كَلِمَة مَحْجُوزَة — لَا يُمْكِن اِسْتِخْدَامُهَا كَاسْم مُتَغَيِّر '
                    f'(reserved keyword, cannot use as variable name)',
                    tok.line, tok.col
                )
            raise ParseError(
                f'مُتَوَقَّع {type_}، وَجَدْنَا {tok.type} ({tok.value!r})',
                tok.line, tok.col
            )
        if value is not None and tok.value != value:
            raise ParseError(
                f'مُتَوَقَّع {value!r}، وَجَدْنَا {tok.value!r}',
                tok.line, tok.col
            )
        return self.advance()

    def match(self, type_, value=None):
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value == value):
            return self.advance()
        return None

    def skip_newlines(self):
        while self.current().type == TokenType.NEWLINE:
            self.advance()

    def at_block_end(self):
        """Check if we're at a DEDENT, EOF, or a keyword that ends a block."""
        tok = self.current()
        return tok.type in (TokenType.DEDENT, TokenType.EOF)

    # ─── PROGRAM ──────────────────────────────────────────────────────

    def parse(self):
        """Parse the entire program."""
        self.skip_newlines()
        body = self.parse_block_body(top_level=True)
        return Program(body)

    def parse_block_body(self, top_level=False):
        """Parse a sequence of statements at the current indentation level."""
        stmts = []
        while True:
            self.skip_newlines()
            tok = self.current()
            if tok.type == TokenType.EOF:
                break
            if tok.type == TokenType.DEDENT and not top_level:
                break
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    def parse_indented_block(self):
        """Parse an indented block after a colon."""
        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        body = self.parse_block_body()
        if self.current().type == TokenType.DEDENT:
            self.advance()
        return body

    # ─── STATEMENTS ───────────────────────────────────────────────────

    def parse_statement(self):
        """Parse a single statement."""
        tok = self.current()

        if tok.type == TokenType.KEYWORD:
            kw = tok.value

            if kw == 'اِعْمَلْ':
                return self.parse_funcdef()
            elif kw == 'كُنْ':
                return self.parse_vardecl()
            elif kw == 'إِنْ':
                return self.parse_if()
            elif kw == 'كَرِّرْ':
                return self.parse_while()
            elif kw == 'لِكُلِّ':
                return self.parse_for()
            elif kw == 'اِرْجِعْ':
                return self.parse_return()
            elif kw == 'قِفْ':
                return self.parse_break()
            elif kw == 'اِبْدَأْ':
                return self.parse_pass()
            elif kw == 'اِحْذِفْ':
                return self.parse_delete()
            elif kw == 'اِسْتَدْعِ':
                return self.parse_import()
            elif kw == 'قِ':
                return self.parse_try()
            elif kw == 'أَنْذِرْ':
                return self.parse_raise()
            elif kw in CONSTANT_KEYWORDS:
                # Could be expression statement
                return self.parse_expr_or_assign()
            else:
                # Expression statement (keyword used as value, e.g. function call)
                return self.parse_expr_or_assign()

        elif tok.type in (TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING,
                          TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE):
            return self.parse_expr_or_assign()

        elif tok.type == TokenType.NEWLINE:
            self.advance()
            return None

        else:
            raise ParseError(f'رَمْز غَيْر مُتَوَقَّع: {tok.type} ({tok.value!r})', tok.line, tok.col)

    def parse_funcdef(self):
        """اِعْمَلْ name(params): body"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'اِعْمَلْ')
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value

        # Parameters
        params = []
        self.expect(TokenType.LPAREN)
        if self.current().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN)

        body = self.parse_indented_block()
        return FuncDef(name, params, body, line)

    def parse_vardecl(self):
        """كُنْ name ← value"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'كُنْ')
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value

        # Accept ← or =
        if self.match(TokenType.ARROW) or self.match(TokenType.ASSIGN):
            value = self.parse_expression()
        else:
            value = Constant(None, line)

        self.skip_newlines()
        return VarDecl(name, value, line)

    def parse_if(self):
        """إِنْ condition: body [أَوْ condition: body]* [وَإِلَّا: body]"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'إِنْ')
        condition = self.parse_expression()
        body = self.parse_indented_block()

        elif_clauses = []
        else_body = []

        while True:
            self.skip_newlines()
            tok = self.current()
            if tok.type == TokenType.KEYWORD and tok.value == 'أَوْ':
                self.advance()
                elif_cond = self.parse_expression()
                elif_body = self.parse_indented_block()
                elif_clauses.append((elif_cond, elif_body))
            elif tok.type == TokenType.KEYWORD and tok.value == 'وَإِلَّا':
                self.advance()
                else_body = self.parse_indented_block()
                break
            else:
                break

        return IfStmt(condition, body, elif_clauses, else_body, line)

    def parse_while(self):
        """كَرِّرْ condition: body"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'كَرِّرْ')
        condition = self.parse_expression()
        body = self.parse_indented_block()
        return WhileLoop(condition, body, line)

    def parse_for(self):
        """لِكُلِّ var فِي iterable: body"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'لِكُلِّ')
        var_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.KEYWORD, 'فِي')
        iterable = self.parse_expression()
        body = self.parse_indented_block()
        return ForLoop(var_tok.value, iterable, body, line)

    def parse_return(self):
        """اِرْجِعْ [value]"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'اِرْجِعْ')
        value = None
        if self.current().type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.DEDENT):
            value = self.parse_expression()
        self.skip_newlines()
        return ReturnStmt(value, line)

    def parse_break(self):
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'قِفْ')
        self.skip_newlines()
        return BreakStmt(line)

    def parse_pass(self):
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'اِبْدَأْ')
        self.skip_newlines()
        return PassStmt(line)

    def parse_delete(self):
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'اِحْذِفْ')
        target = self.parse_expression()
        self.skip_newlines()
        return DeleteStmt(target, line)

    def parse_import(self):
        """اِسْتَدْعِ module  or  مِنْ module اِسْتَدْعِ name"""
        line = self.current().line
        # Check for مِنْ ... اِسْتَدْعِ ... form
        if self.current().type == TokenType.KEYWORD and self.current().value == 'مِنْ':
            self.advance()
            module = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.KEYWORD, 'اِسْتَدْعِ')
            names = [self.expect(TokenType.IDENTIFIER).value]
            while self.match(TokenType.COMMA):
                names.append(self.expect(TokenType.IDENTIFIER).value)
            self.skip_newlines()
            return ImportStmt(module, names, line)
        else:
            self.expect(TokenType.KEYWORD, 'اِسْتَدْعِ')
            module = self.expect(TokenType.IDENTIFIER).value
            self.skip_newlines()
            return ImportStmt(module, None, line)

    def parse_try(self):
        """قِ: body أَنْذِرْ [exc]: handler"""
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'قِ')
        body = self.parse_indented_block()
        self.skip_newlines()

        exc_name = None
        handler_body = []
        if self.current().type == TokenType.KEYWORD and self.current().value == 'أَنْذِرْ':
            self.advance()
            # Optional exception variable
            if self.current().type == TokenType.IDENTIFIER:
                exc_name = self.current().value
                self.advance()
            handler_body = self.parse_indented_block()

        return TryStmt(body, handler_body, exc_name, line)

    def parse_raise(self):
        line = self.current().line
        self.expect(TokenType.KEYWORD, 'أَنْذِرْ')
        value = None
        if self.current().type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.DEDENT):
            value = self.parse_expression()
        self.skip_newlines()
        return RaiseStmt(value, line)

    def parse_expr_or_assign(self):
        """Parse expression, possibly followed by ← for assignment."""
        line = self.current().line
        expr = self.parse_expression()

        # Check for assignment
        if self.match(TokenType.ARROW) or self.match(TokenType.ASSIGN):
            value = self.parse_expression()
            self.skip_newlines()
            return Assignment(expr, value, line)

        self.skip_newlines()
        return ExprStmt(expr, line)

    # ─── EXPRESSIONS ──────────────────────────────────────────────────

    def parse_expression(self):
        """Parse a full expression (lowest precedence: boolean ops)."""
        return self.parse_bool_or()

    def parse_bool_or(self):
        """أَوْ (or) — but only when used as boolean operator in expressions."""
        left = self.parse_bool_and()
        # Note: أَوْ is also used for elif. In expression context,
        # it acts as boolean OR only if followed by an expression, not a colon.
        return left

    def parse_bool_and(self):
        """وَ (and)"""
        left = self.parse_bool_not()
        while (self.current().type == TokenType.KEYWORD and
               self.current().value == 'وَ' and
               # Make sure it's boolean AND, not just conjunction
               self.peek().type not in (TokenType.NEWLINE, TokenType.COLON, TokenType.EOF)):
            self.advance()
            right = self.parse_bool_not()
            left = BoolOp('وَ', [left, right], left.line if hasattr(left, 'line') else 0)
        return left

    def parse_bool_not(self):
        """لَا (not)"""
        if self.current().type == TokenType.KEYWORD and self.current().value == 'لَا':
            line = self.current().line
            self.advance()
            operand = self.parse_bool_not()
            return NotOp(operand, line)
        return self.parse_comparison()

    def parse_comparison(self):
        """Comparison: سَوَاء (==), فَوْقَ (>), دُونَ (<), and symbolic ops."""
        left = self.parse_addition()
        ops = []
        comparators = []

        while True:
            tok = self.current()
            op = None

            # Arabic keyword comparisons
            if tok.type == TokenType.KEYWORD and tok.value in COMPARISON_KEYWORDS:
                op = COMPARISON_KEYWORDS[tok.value]
                self.advance()
            # Symbolic comparisons
            elif tok.type == TokenType.OPERATOR and tok.value in ('==', '!=', '>', '<', '>=', '<='):
                op = tok.value
                self.advance()
            else:
                break

            right = self.parse_addition()
            ops.append(op)
            comparators.append(right)

        if ops:
            return Compare(left, ops, comparators,
                          left.line if hasattr(left, 'line') else 0)
        return left

    def parse_addition(self):
        """+ and -"""
        left = self.parse_multiplication()
        while self.current().type == TokenType.OPERATOR and self.current().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_multiplication()
            left = BinOp(left, op, right,
                        left.line if hasattr(left, 'line') else 0)
        return left

    def parse_multiplication(self):
        """*, /, %, **"""
        left = self.parse_unary()
        while self.current().type == TokenType.OPERATOR and self.current().value in ('*', '/', '%', '**'):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(left, op, right,
                        left.line if hasattr(left, 'line') else 0)
        return left

    def parse_unary(self):
        """Unary - and لَا"""
        if self.current().type == TokenType.OPERATOR and self.current().value == '-':
            line = self.current().line
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('-', operand, line)
        return self.parse_postfix()

    def _parse_call_arg(self, args, kwargs):
        """Parse a single function call argument (positional or keyword).
        Keyword args: identifier=value or identifier←value
        """
        # Check if this is a keyword argument: identifier followed by = or ←
        if (self.current().type == TokenType.IDENTIFIER and
            (self.peek().type == TokenType.ASSIGN or self.peek().type == TokenType.ARROW)):
            name = self.advance().value  # consume identifier
            self.advance()  # consume = or ←
            value = self.parse_expression()
            kwargs.append(Kwarg(name, value, value.line if hasattr(value, 'line') else 0))
        else:
            args.append(self.parse_expression())

    def parse_postfix(self):
        """Function calls, subscripts, attribute access."""
        expr = self.parse_atom()

        while True:
            if self.current().type == TokenType.LPAREN:
                # Function call — supports positional and keyword args
                line = self.current().line
                self.advance()
                args = []
                kwargs = []
                if self.current().type != TokenType.RPAREN:
                    self._parse_call_arg(args, kwargs)
                    while self.match(TokenType.COMMA):
                        if self.current().type == TokenType.RPAREN:
                            break
                        self._parse_call_arg(args, kwargs)
                self.expect(TokenType.RPAREN)
                expr = FuncCall(expr, args, line, kwargs)

            elif self.current().type == TokenType.LBRACKET:
                # Subscript
                line = self.current().line
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = Subscript(expr, index, line)

            elif self.current().type == TokenType.DOT:
                # Attribute access — keywords allowed as attribute names
                line = self.current().line
                self.advance()
                tok = self.current()
                if tok.type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
                    attr = self.advance().value
                else:
                    raise ParseError(
                        f'مُتَوَقَّع اِسْم بَعْد النُّقْطَة، وَجَدْنَا {tok.type} ({tok.value!r})',
                        tok.line, tok.col
                    )
                expr = Attribute(expr, attr, line)

            else:
                break

        return expr

    def parse_atom(self):
        """Parse atomic expressions."""
        tok = self.current()

        # Number
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Num(tok.value, tok.line)

        # String
        if tok.type == TokenType.STRING:
            self.advance()
            return Str(tok.value, tok.line)

        # Identifier
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Name(tok.value, tok.line)

        # Constants: حَقّ بَاطِل عَدَم
        if tok.type == TokenType.KEYWORD and tok.value in CONSTANT_KEYWORDS:
            self.advance()
            return Constant(CONSTANT_KEYWORDS[tok.value], tok.line)

        # Keyword used as function (e.g., اُكْتُبْ("hello"))
        if tok.type == TokenType.KEYWORD:
            self.advance()
            return Name(tok.value, tok.line)

        # Parenthesised expression or tuple
        if tok.type == TokenType.LPAREN:
            self.advance()
            if self.current().type == TokenType.RPAREN:
                self.advance()
                return TupleLiteral([], tok.line)
            expr = self.parse_expression()
            if self.current().type == TokenType.COMMA:
                # It's a tuple
                elements = [expr]
                while self.match(TokenType.COMMA):
                    if self.current().type == TokenType.RPAREN:
                        break
                    elements.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return TupleLiteral(elements, tok.line)
            self.expect(TokenType.RPAREN)
            return expr

        # List literal
        if tok.type == TokenType.LBRACKET:
            self.advance()
            elements = []
            if self.current().type != TokenType.RBRACKET:
                elements.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    if self.current().type == TokenType.RBRACKET:
                        break
                    elements.append(self.parse_expression())
            self.expect(TokenType.RBRACKET)
            return ListLiteral(elements, tok.line)

        # Dict literal
        if tok.type == TokenType.LBRACE:
            self.advance()
            pairs = []
            if self.current().type != TokenType.RBRACE:
                key = self.parse_expression()
                self.expect(TokenType.COLON)
                val = self.parse_expression()
                pairs.append((key, val))
                while self.match(TokenType.COMMA):
                    if self.current().type == TokenType.RBRACE:
                        break
                    key = self.parse_expression()
                    self.expect(TokenType.COLON)
                    val = self.parse_expression()
                    pairs.append((key, val))
            self.expect(TokenType.RBRACE)
            return DictLiteral(pairs, tok.line)

        raise ParseError(f'رَمْز غَيْر مُتَوَقَّع فِي التَّعْبِير: {tok.type} ({tok.value!r})',
                         tok.line, tok.col)


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def parse_source(source, filename='<input>'):
    """Parse source string into AST."""
    tokens = tokenize_source(source, filename)
    parser = Parser(tokens)
    return parser.parse()


def parse_file(filepath):
    """Parse a .أمر file into AST."""
    tokens = tokenize_file(filepath)
    parser = Parser(tokens)
    return parser.parse()


def print_ast(node, indent=0):
    """Pretty-print an AST tree."""
    prefix = '  ' * indent
    if isinstance(node, Program):
        print(f'{prefix}Program:')
        for stmt in node.body:
            print_ast(stmt, indent + 1)
    elif isinstance(node, FuncDef):
        print(f'{prefix}FuncDef: {node.name}({", ".join(node.params)})')
        for stmt in node.body:
            print_ast(stmt, indent + 1)
    elif isinstance(node, VarDecl):
        print(f'{prefix}VarDecl: {node.name} =')
        print_ast(node.value, indent + 1)
    elif isinstance(node, Assignment):
        print(f'{prefix}Assign:')
        print_ast(node.target, indent + 1)
        print_ast(node.value, indent + 1)
    elif isinstance(node, IfStmt):
        print(f'{prefix}If:')
        print_ast(node.condition, indent + 1)
        for s in node.body:
            print_ast(s, indent + 1)
        for cond, body in node.elif_clauses:
            print(f'{prefix}Elif:')
            print_ast(cond, indent + 1)
            for s in body:
                print_ast(s, indent + 1)
        if node.else_body:
            print(f'{prefix}Else:')
            for s in node.else_body:
                print_ast(s, indent + 1)
    elif isinstance(node, WhileLoop):
        print(f'{prefix}While:')
        print_ast(node.condition, indent + 1)
        for s in node.body:
            print_ast(s, indent + 1)
    elif isinstance(node, ForLoop):
        print(f'{prefix}For: {node.var} in')
        print_ast(node.iterable, indent + 1)
        for s in node.body:
            print_ast(s, indent + 1)
    elif isinstance(node, ReturnStmt):
        print(f'{prefix}Return:')
        if node.value:
            print_ast(node.value, indent + 1)
    elif isinstance(node, BreakStmt):
        print(f'{prefix}Break')
    elif isinstance(node, PassStmt):
        print(f'{prefix}Pass')
    elif isinstance(node, ExprStmt):
        print(f'{prefix}ExprStmt:')
        print_ast(node.expr, indent + 1)
    elif isinstance(node, FuncCall):
        print(f'{prefix}Call:')
        print_ast(node.func, indent + 1)
        for a in node.args:
            print_ast(a, indent + 1)
    elif isinstance(node, BinOp):
        print(f'{prefix}BinOp: {node.op}')
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, Compare):
        print(f'{prefix}Compare: {node.ops}')
        print_ast(node.left, indent + 1)
        for c in node.comparators:
            print_ast(c, indent + 1)
    elif isinstance(node, BoolOp):
        print(f'{prefix}BoolOp: {node.op}')
        for v in node.values:
            print_ast(v, indent + 1)
    elif isinstance(node, NotOp):
        print(f'{prefix}Not:')
        print_ast(node.operand, indent + 1)
    elif isinstance(node, UnaryOp):
        print(f'{prefix}Unary: {node.op}')
        print_ast(node.operand, indent + 1)
    elif isinstance(node, Name):
        print(f'{prefix}Name: {node.name}')
    elif isinstance(node, Num):
        print(f'{prefix}Num: {node.value}')
    elif isinstance(node, Str):
        print(f'{prefix}Str: {node.value!r}')
    elif isinstance(node, Constant):
        print(f'{prefix}Const: {node.value}')
    elif isinstance(node, ListLiteral):
        print(f'{prefix}List:')
        for e in node.elements:
            print_ast(e, indent + 1)
    elif isinstance(node, Subscript):
        print(f'{prefix}Subscript:')
        print_ast(node.obj, indent + 1)
        print_ast(node.index, indent + 1)
    elif isinstance(node, Attribute):
        print(f'{prefix}Attr: .{node.attr}')
        print_ast(node.obj, indent + 1)
    else:
        print(f'{prefix}{node}')


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
        ast = parse_source(test_code)
        print_ast(ast)
    except (ParseError, LexerError) as e:
        print(f'ERROR: {e}')
