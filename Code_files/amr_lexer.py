#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر LEXER — RTL Tokeniser for the أَمْر Programming Language

Layer 1: أ-م-ر / AMR (commands) — the programming language
Reads .أمر files (UTF-8). Produces token stream.

Token types:
  KEYWORD    — one of the 42 أَمْر keywords from amr_keywords.py
  IDENTIFIER — user-defined names (Arabic script)
  NUMBER     — Arabic numerals (٠١٢٣٤٥٦٧٨٩) or Western digits
  STRING     — quoted strings (single or double quotes, « » guillemets)
  OPERATOR   — arithmetic, comparison, assignment operators
  NEWLINE    — end of logical line
  INDENT     — indentation level (spaces at start of line)
  DEDENT     — decrease in indentation
  LPAREN / RPAREN / LBRACKET / RBRACKET / LBRACE / RBRACE
  COMMA      — ، or ,
  COLON      — : or ؛
  DOT        — .
  ASSIGN     — = or ←
  ARROW      — ←
  COMMENT    — # comments (discarded)
  EOF        — end of file
"""

import sys
import os

# Import keywords - handle both module and direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from amr_keywords import KEYWORDS
except ImportError:
    from Code_files.amr_keywords import KEYWORDS


# ═══════════════════════════════════════════════════════════════════════
# TOKEN TYPES
# ═══════════════════════════════════════════════════════════════════════

class TokenType:
    KEYWORD    = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    NUMBER     = 'NUMBER'
    STRING     = 'STRING'
    OPERATOR   = 'OPERATOR'
    NEWLINE    = 'NEWLINE'
    INDENT     = 'INDENT'
    DEDENT     = 'DEDENT'
    LPAREN     = 'LPAREN'
    RPAREN     = 'RPAREN'
    LBRACKET   = 'LBRACKET'
    RBRACKET   = 'RBRACKET'
    LBRACE     = 'LBRACE'
    RBRACE     = 'RBRACE'
    COMMA      = 'COMMA'
    COLON      = 'COLON'
    DOT        = 'DOT'
    ASSIGN     = 'ASSIGN'
    ARROW      = 'ARROW'
    EOF        = 'EOF'


class Token:
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type_, value, line=0, col=0):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, L{self.line}:{self.col})'


# ═══════════════════════════════════════════════════════════════════════
# CHARACTER SETS
# ═══════════════════════════════════════════════════════════════════════

# Arabic-Indic digits ٠١٢٣٤٥٦٧٨٩ → 0-9
ARABIC_DIGITS = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
}

# Characters that can appear in identifiers:
# ONLY actual AA letters (0621-064A) and diacritics (064B-0652) that
# appear in roots and words. Nothing else.
# NO operator-encoded waqf signs, NO punctuation, NO digits.
def is_aa_letter(ch):
    """Check if character is an AA letter or diacritic used in words.

    Accepted ranges (WHITELIST):
      0621-064A  AA letters (hamza through yaa)
      064B-0652  Arabic diacritics (fathatan through sukun)
      0653-0655  Maddah, hamza above/below (used in Qur'anic orthography)
      0670       Superscript alef (dagger alef)
      0671       Alef wasla
      ـ (0640)   Tatweel (kashida, used in display)
      _ (005F)   Underscore (programming convention)

    EXCLUDED:
      0600-0620  Operator-assigned: Basmala sign, date marks, footnotes
      060C       Arabic comma
      061B       Arabic semicolon
      061F       Arabic question mark
      0656-066F  Operator waqf signs, subscript alef variants
      0660-0669  Arabic-Indic digits (handled separately)
      066A-066F  Percent, asterisk, operator additions
      0670+      Waqf marks, sajdah marks, rub el hizb, etc.
      06D6-06ED  Qur'anic annotation signs (ALL operator additions)
      06F0-06F9  Extended Arabic-Indic digits
      0750+      All supplement/extended blocks (operator expansions)
      FB50+      Presentation forms (display variants, not letters)
      FE70+      Presentation forms B
    """
    cp = ord(ch)
    return (
        (0x0621 <= cp <= 0x064A) or   # AA letters: hamza through yaa
        (0x064B <= cp <= 0x0655) or   # Diacritics: fathatan through hamza below
        cp == 0x0670 or               # Superscript alef (dagger alef)
        cp == 0x0671 or               # Alef wasla
        cp == 0x0640 or               # Tatweel
        ch == '_'                      # Programming underscore
    )

def is_digit(ch):
    """Check if character is a digit (Arabic-Indic or Western)."""
    return ch in ARABIC_DIGITS or ch.isdigit()

def is_identifier_start(ch):
    """Check if character can start an identifier."""
    return is_aa_letter(ch)

def is_identifier_char(ch):
    """Check if character can continue an identifier."""
    return is_aa_letter(ch) or is_digit(ch)


# Operators
OPERATORS = {
    '+', '-', '*', '/', '%', '**',
    '←',      # assignment arrow
    '÷',      # division alternative
}

# Multi-char operators that start with a single char
OPERATOR_STARTS = {'+', '-', '*', '/', '%', '←', '÷', '>', '<', '!', '='}


# ═══════════════════════════════════════════════════════════════════════
# KEYWORD SET (for fast lookup)
# ═══════════════════════════════════════════════════════════════════════

KEYWORD_SET = set(KEYWORDS.keys())


# ═══════════════════════════════════════════════════════════════════════
# LEXER
# ═══════════════════════════════════════════════════════════════════════

class LexerError(Exception):
    def __init__(self, message, line=0, col=0, source=None):
        self.line = line
        self.col = col
        self.source = source
        # Build contextual error
        context = ''
        if source:
            lines = source.split('\n')
            if 0 < line <= len(lines):
                src_line = lines[line - 1]
                context = f'\n  {src_line}\n  {" " * max(0, col - 1)}↑'
        super().__init__(f'خَطَأ قِرَاءَة سَطْر {line}:{col}: {message}{context}')


class Lexer:
    """RTL-aware tokeniser for أَمْر source code."""

    def __init__(self, source, filename='<input>'):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self.indent_stack = [0]  # stack of indentation levels

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return '\0'

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_comment(self):
        """Skip from # to end of line."""
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
            self.col += 1

    def read_string(self, quote_char):
        """Read a quoted string literal."""
        start_line = self.line
        start_col = self.col
        self.advance()  # consume opening quote
        result = []
        # Handle matching close quote for guillemets
        close_char = '»' if quote_char == '«' else quote_char

        while self.pos < len(self.source):
            ch = self.peek()
            if ch == close_char:
                self.advance()  # consume closing quote
                return Token(TokenType.STRING, ''.join(result), start_line, start_col)
            elif ch == '\\':
                self.advance()
                esc = self.advance()
                escape_map = {'n': '\n', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                result.append(escape_map.get(esc, esc))
            elif ch == '\n' and quote_char != '«':
                raise LexerError('كَلِمَة غَيْر مُغْلَقَة (unterminated string)', start_line, start_col, self.source)
            else:
                result.append(self.advance())

        raise LexerError('كَلِمَة غَيْر مُغْلَقَة (unterminated string)', start_line, start_col, self.source)

    def read_number(self):
        """Read a numeric literal (Arabic-Indic or Western digits)."""
        start_line = self.line
        start_col = self.col
        result = []
        has_dot = False

        while self.pos < len(self.source):
            ch = self.peek()
            if ch in ARABIC_DIGITS:
                result.append(ARABIC_DIGITS[ch])
                self.advance()
            elif ch.isdigit():
                result.append(ch)
                self.advance()
            elif ch == '.' and not has_dot:
                # Check next char is a digit
                next_ch = self.peek(1)
                if is_digit(next_ch) or next_ch in ARABIC_DIGITS:
                    has_dot = True
                    result.append('.')
                    self.advance()
                else:
                    break
            elif ch == '_':
                # Allow _ as digit separator
                self.advance()
            else:
                break

        num_str = ''.join(result)
        if has_dot:
            return Token(TokenType.NUMBER, float(num_str), start_line, start_col)
        else:
            return Token(TokenType.NUMBER, int(num_str), start_line, start_col)

    def read_identifier_or_keyword(self):
        """Read an identifier or keyword."""
        start_line = self.line
        start_col = self.col
        result = []

        while self.pos < len(self.source) and is_identifier_char(self.peek()):
            result.append(self.advance())

        word = ''.join(result)

        # Check if it's a keyword
        if word in KEYWORD_SET:
            return Token(TokenType.KEYWORD, word, start_line, start_col)
        else:
            return Token(TokenType.IDENTIFIER, word, start_line, start_col)

    def tokenize(self):
        """Tokenise the entire source into a list of tokens."""
        tokens = []
        at_line_start = True

        while self.pos < len(self.source):
            ch = self.peek()

            # Handle start of line: measure indentation
            if at_line_start:
                indent = 0
                while self.pos < len(self.source) and self.peek() == ' ':
                    self.advance()
                    indent += 1
                # Skip tabs (count as 4 spaces)
                while self.pos < len(self.source) and self.peek() == '\t':
                    self.advance()
                    indent += 4

                at_line_start = False

                # Skip blank lines and comment-only lines
                if self.pos >= len(self.source) or self.peek() == '\n':
                    if self.pos < len(self.source):
                        self.advance()
                        at_line_start = True
                    continue
                if self.peek() == '#':
                    self.skip_comment()
                    if self.pos < len(self.source) and self.peek() == '\n':
                        self.advance()
                        at_line_start = True
                    continue

                # Emit INDENT/DEDENT tokens
                current_indent = self.indent_stack[-1]
                if indent > current_indent:
                    self.indent_stack.append(indent)
                    tokens.append(Token(TokenType.INDENT, indent, self.line, 1))
                elif indent < current_indent:
                    while self.indent_stack[-1] > indent:
                        self.indent_stack.pop()
                        tokens.append(Token(TokenType.DEDENT, indent, self.line, 1))
                    if self.indent_stack[-1] != indent:
                        raise LexerError(
                            f'خَلَل فِي المَسَافَة (indentation): مُتَوَقَّع {self.indent_stack[-1]}، وَجَدْنَا {indent}',
                            self.line, 1, self.source)

                continue  # re-enter loop to process first non-space char

            ch = self.peek()

            # Skip spaces (not at line start)
            if ch == ' ' or ch == '\t':
                self.advance()
                continue

            # Newline
            if ch == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.col))
                self.advance()
                at_line_start = True
                continue

            # Carriage return (skip, handle \r\n)
            if ch == '\r':
                self.advance()
                continue

            # Comment
            if ch == '#':
                self.skip_comment()
                continue

            # String literals
            if ch in ('"', "'", '«'):
                tokens.append(self.read_string(ch))
                continue

            # Numbers
            if is_digit(ch) or ch in ARABIC_DIGITS:
                tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if is_identifier_start(ch):
                tokens.append(self.read_identifier_or_keyword())
                continue

            # Delimiters
            if ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.line, self.col))
                self.advance()
                continue
            if ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.line, self.col))
                self.advance()
                continue
            if ch == '[':
                tokens.append(Token(TokenType.LBRACKET, '[', self.line, self.col))
                self.advance()
                continue
            if ch == ']':
                tokens.append(Token(TokenType.RBRACKET, ']', self.line, self.col))
                self.advance()
                continue
            if ch == '{':
                tokens.append(Token(TokenType.LBRACE, '{', self.line, self.col))
                self.advance()
                continue
            if ch == '}':
                tokens.append(Token(TokenType.RBRACE, '}', self.line, self.col))
                self.advance()
                continue

            # Comma (Arabic or Latin)
            if ch in ('،', ','):
                tokens.append(Token(TokenType.COMMA, ch, self.line, self.col))
                self.advance()
                continue

            # Colon
            if ch == ':':
                tokens.append(Token(TokenType.COLON, ':', self.line, self.col))
                self.advance()
                continue
            if ch == '؛':
                tokens.append(Token(TokenType.COLON, '؛', self.line, self.col))
                self.advance()
                continue

            # Dot
            if ch == '.':
                tokens.append(Token(TokenType.DOT, '.', self.line, self.col))
                self.advance()
                continue

            # Assignment arrow
            if ch == '←':
                tokens.append(Token(TokenType.ARROW, '←', self.line, self.col))
                self.advance()
                continue

            # Assignment =
            if ch == '=':
                if self.peek(1) == '=':
                    tokens.append(Token(TokenType.OPERATOR, '==', self.line, self.col))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.ASSIGN, '=', self.line, self.col))
                    self.advance()
                continue

            # Operators
            if ch == '+':
                tokens.append(Token(TokenType.OPERATOR, '+', self.line, self.col))
                self.advance()
                continue
            if ch == '-':
                tokens.append(Token(TokenType.OPERATOR, '-', self.line, self.col))
                self.advance()
                continue
            if ch == '*':
                if self.peek(1) == '*':
                    tokens.append(Token(TokenType.OPERATOR, '**', self.line, self.col))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.OPERATOR, '*', self.line, self.col))
                    self.advance()
                continue
            if ch == '/':
                tokens.append(Token(TokenType.OPERATOR, '/', self.line, self.col))
                self.advance()
                continue
            if ch == '÷':
                tokens.append(Token(TokenType.OPERATOR, '/', self.line, self.col))
                self.advance()
                continue
            if ch == '%':
                tokens.append(Token(TokenType.OPERATOR, '%', self.line, self.col))
                self.advance()
                continue
            if ch == '!':
                if self.peek(1) == '=':
                    tokens.append(Token(TokenType.OPERATOR, '!=', self.line, self.col))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.OPERATOR, '!', self.line, self.col))
                    self.advance()
                continue
            if ch == '>':
                if self.peek(1) == '=':
                    tokens.append(Token(TokenType.OPERATOR, '>=', self.line, self.col))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.OPERATOR, '>', self.line, self.col))
                    self.advance()
                continue
            if ch == '<':
                if self.peek(1) == '=':
                    tokens.append(Token(TokenType.OPERATOR, '<=', self.line, self.col))
                    self.advance()
                    self.advance()
                else:
                    tokens.append(Token(TokenType.OPERATOR, '<', self.line, self.col))
                    self.advance()
                continue

            # Unknown character — skip with warning
            raise LexerError(f'حَرْف غَيْر مَعْرُوف: {ch!r} (U+{ord(ch):04X})', self.line, self.col, self.source)

        # Emit remaining DEDENTs
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, 0, self.line, self.col))

        # Final NEWLINE if not present
        if tokens and tokens[-1].type != TokenType.NEWLINE:
            tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.col))

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def tokenize_source(source, filename='<input>'):
    """Tokenise source string, return list of Token objects."""
    lexer = Lexer(source, filename)
    return lexer.tokenize()


def tokenize_file(filepath):
    """Tokenise a .أمر file, return list of Token objects."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return tokenize_source(source, filepath)


if __name__ == '__main__':
    # Test with inline أَمْر code
    test_code = '''# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
كُنْ س ← ٥
كُنْ رِسَالَة ← "بِسْمِ اللَّهِ"
اُكْتُبْ(رِسَالَة)
إِنْ س فَوْقَ ٣:
    اُكْتُبْ("حَقّ")
وَإِلَّا:
    اُكْتُبْ("بَاطِل")
'''
    try:
        tokens = tokenize_source(test_code)
        for tok in tokens:
            print(tok)
        print(f'\nTotal tokens: {len(tokens)}')
    except LexerError as e:
        print(f'LEXER ERROR: {e}')
