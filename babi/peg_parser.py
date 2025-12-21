from __future__ import annotations

from typing import Dict

import parsy
from parsy import Parser, eof, generate, regex, string

from . import peg_ast


def _build_spacing() -> Parser:
    space = regex(r"[ \t\n\r]+")

    @generate
    def comment():
        yield string("#")
        yield (regex(r"[^\n]*") | parsy.success(""))
        yield (string("\n") | eof)
        return None

    return (space | comment).many().map(lambda _: None)


def parse_peg(source: str) -> Dict:
    """Parse a PEG grammar into a JSON-serializable AST."""

    Spacing = _build_spacing()

    def tok(p: Parser) -> Parser:
        return p << Spacing

    IdentStart = regex(r"[A-Za-z_]")
    IdentCont = regex(r"[A-Za-z0-9_]")
    Identifier = tok((IdentStart + IdentCont.many().concat()).map(lambda s: s))

    def kw(s: str) -> Parser:
        return tok(string(s))

    LEFTARROW = kw("<-")
    SLASH = kw("/")
    AND = kw("&")
    NOT = kw("!")
    QUESTION = kw("?")
    STAR = kw("*")
    PLUS = kw("+")
    OPEN = kw("(")
    CLOSE = kw(")")
    DOT = kw(".")

    def unescape(c: str) -> str:
        if c == "n":
            return "\n"
        if c == "r":
            return "\r"
        if c == "t":
            return "\t"
        if c in "\\\"'":
            return c
        return c

    hex2 = regex(r"[0-9A-Fa-f]{2}").map(lambda h: chr(int(h, 16)))

    @generate
    def escape():
        yield string("\\")
        kind = yield (regex(r"[\\\"'nrt]") | string("x"))
        if kind == "x":
            ch = yield hex2
            return ch
        return unescape(kind)

    def quoted(quote: str) -> Parser:
        @generate
        def q():
            yield string(quote)
            chars = yield (
                escape
                | regex(r".").bind(
                    lambda ch: parsy.fail("quote") if ch == quote else parsy.success(ch)
                )
            ).many()
            yield string(quote)
            yield Spacing
            return peg_ast.literal("".join(chars))

        return q

    literal = quoted("'") | quoted('"')

    @generate
    def class_char():
        ch = yield (escape | regex(r".") )
        return ch

    @generate
    def char_class():
        yield string("[")
        neg = yield string("^").optional()

        @generate
        def item():
            a = yield (escape | regex(r"[^\]]"))
            dash = yield string("-").optional()
            if dash is None:
                return peg_ast.class_char(a)
            b = yield (escape | regex(r"[^\]]"))
            return peg_ast.class_range(a, b)

        parts = yield item.many()
        yield string("]")
        yield spacing
        return peg_ast.char_class(parts, negated=neg is not None)

    # Forward declarations
    Expression: Parser = parsy.forward_declaration()
    Sequence: Parser = parsy.forward_declaration()
    Prefix: Parser = parsy.forward_declaration()
    Suffix: Parser = parsy.forward_declaration()
    Primary: Parser = parsy.forward_declaration()

    @generate
    def primary_ref():
        name = yield identifier
        # Identifier !LEFTARROW
        la = yield string("<-").optional()
        if la is not None:
            return parsy.fail("rule-name-used-as-primary")
        return peg_ast.ref(name)

    grouped = (OPEN >> Expression << CLOSE)

    Primary.become(
        primary_ref
        | grouped
        | literal
        | char_class
        | DOT.result(peg_ast.dot())
    )

    @generate
    def suffix():
        p = yield Primary
        mod = yield (QUESTION | STAR | PLUS).optional()
        if mod is None:
            return p
        if mod == "?":
            return peg_ast.opt(p)
        if mod == "*":
            return peg_ast.star(p)
        return peg_ast.plus(p)

    Suffix.become(suffix)

    @generate
    def prefix():
        op = yield (AND | NOT).optional()
        s = yield Suffix
        if op is None:
            return s
        if op == "&":
            return peg_ast.andp(s)
        return peg_ast.notp(s)

    Prefix.become(prefix)

    Sequence.become(Prefix.many().map(lambda items: peg_ast.sequence(items)))

    @generate
    def expression():
        first = yield Sequence
        rest = yield (SLASH >> Sequence).many()
        if not rest:
            return first
        return peg_ast.choice([first, *rest])

    Expression.become(expression)

    @generate
    def definition():
        name = yield identifier
        yield LEFTARROW
        expr = yield Expression
        return peg_ast.rule(name, expr)

    grammar = spacing >> definition.many().bind(
        lambda defs: eof.result({"type": "grammar", "rules": defs})
        if defs
        else parsy.fail("empty-grammar")
    )

    return grammar.parse(source)
