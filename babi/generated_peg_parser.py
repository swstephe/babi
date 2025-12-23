from __future__ import annotations

from parsy import (
    Parser,
    Result,
    any_char,
    forward_declaration,
    regex,
    seq,
    string,
    success,
)

__all__ = ["parser"]

def _tag(name: str, value):
    return {"type": name, "value": value}

def _and(p: Parser) -> Parser:
    @Parser
    def and_parser(stream, index):
        res = p(stream, index)
        if res.status:
            return Result.success(index, True)
        return res
    return and_parser

def _not(p: Parser) -> Parser:
    return p.should_fail('not').result(True)

Grammar = forward_declaration()
Definition = forward_declaration()
Expression = forward_declaration()
Sequence = forward_declaration()
Prefix = forward_declaration()
Suffix = forward_declaration()
Primary = forward_declaration()
Identifier = forward_declaration()
IdentStart = forward_declaration()
IdentCont = forward_declaration()
Literal = forward_declaration()
SingleQuoted = forward_declaration()
DoubleQuoted = forward_declaration()
CharSingle = forward_declaration()
CharDouble = forward_declaration()
Escape = forward_declaration()
Hex = forward_declaration()
Class = forward_declaration()
ClassItem = forward_declaration()
Range = forward_declaration()
ClassChar = forward_declaration()
LEFTARROW = forward_declaration()
SLASH = forward_declaration()
AND = forward_declaration()
NOT = forward_declaration()
QUESTION = forward_declaration()
STAR = forward_declaration()
PLUS = forward_declaration()
OPEN = forward_declaration()
CLOSE = forward_declaration()
DOT = forward_declaration()
Spacing = forward_declaration()
Space = forward_declaration()
Comment = forward_declaration()
EOF = forward_declaration()

Grammar.become((seq(Spacing, (Definition).at_least(1), EOF).map(lambda xs: list(xs))).map(lambda v: _tag("Grammar", v)))
Definition.become((seq(Identifier, LEFTARROW, Expression).map(lambda xs: list(xs))).map(lambda v: _tag("Definition", v)))
Expression.become((seq(Sequence, (seq(SLASH, Sequence).map(lambda xs: list(xs))).many()).map(lambda xs: list(xs))).map(lambda v: _tag("Expression", v)))
Sequence.become((seq((Prefix).many()).map(lambda xs: list(xs))).map(lambda v: _tag("Sequence", v)))
Prefix.become((seq((((seq(AND).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(NOT).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).optional(), Suffix).map(lambda xs: list(xs))).map(lambda v: _tag("Prefix", v)))
Suffix.become((seq(Primary, (((seq(QUESTION).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(STAR).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}) | (seq(PLUS).map(lambda xs: list(xs))).map(lambda v, i=2: {"alt": i, "value": v}))).optional()).map(lambda xs: list(xs))).map(lambda v: _tag("Suffix", v)))
Primary.become((((seq(Identifier, _not(LEFTARROW)).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(OPEN, Expression, CLOSE).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}) | (seq(Literal).map(lambda xs: list(xs))).map(lambda v, i=2: {"alt": i, "value": v}) | (seq(Class).map(lambda xs: list(xs))).map(lambda v, i=3: {"alt": i, "value": v}) | (seq(DOT).map(lambda xs: list(xs))).map(lambda v, i=4: {"alt": i, "value": v}))).map(lambda v: _tag("Primary", v)))
Identifier.become((seq(IdentStart, (IdentCont).many(), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("Identifier", v)))
IdentStart.become((seq(regex(r"[A-Za-z_]")).map(lambda xs: list(xs))).map(lambda v: _tag("IdentStart", v)))
IdentCont.become((seq(regex(r"[A-Za-z0-9_]")).map(lambda xs: list(xs))).map(lambda v: _tag("IdentCont", v)))
Literal.become((((seq(SingleQuoted).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(DoubleQuoted).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda v: _tag("Literal", v)))
SingleQuoted.become((seq(string("'"), (CharSingle).many(), string("'"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("SingleQuoted", v)))
DoubleQuoted.become((seq(string("\""), (CharDouble).many(), string("\""), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("DoubleQuoted", v)))
CharSingle.become((((seq(Escape).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(seq(_not(string("'")), any_char).map(lambda xs: list(xs))).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda v: _tag("CharSingle", v)))
CharDouble.become((((seq(Escape).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(seq(_not(string("\"")), any_char).map(lambda xs: list(xs))).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda v: _tag("CharDouble", v)))
Escape.become((seq(string("\\"), ((seq(regex(r"['"\\nrt]")).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(string("x"), Hex, Hex).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda xs: list(xs))).map(lambda v: _tag("Escape", v)))
Hex.become((seq(regex(r"[0-9A-Fa-f]")).map(lambda xs: list(xs))).map(lambda v: _tag("Hex", v)))
Class.become((seq(string("["), (ClassItem).many(), string("]"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("Class", v)))
ClassItem.become((((seq(Range).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(ClassChar).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda v: _tag("ClassItem", v)))
Range.become((seq(ClassChar, string("-"), ClassChar).map(lambda xs: list(xs))).map(lambda v: _tag("Range", v)))
ClassChar.become((((seq(Escape).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(seq(_not(string("]")), any_char).map(lambda xs: list(xs))).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda v: _tag("ClassChar", v)))
LEFTARROW.become((seq(string("<-"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("LEFTARROW", v)))
SLASH.become((seq(string("/"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("SLASH", v)))
AND.become((seq(string("&"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("AND", v)))
NOT.become((seq(string("!"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("NOT", v)))
QUESTION.become((seq(string("?"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("QUESTION", v)))
STAR.become((seq(string("*"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("STAR", v)))
PLUS.become((seq(string("+"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("PLUS", v)))
OPEN.become((seq(string("("), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("OPEN", v)))
CLOSE.become((seq(string(")"), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("CLOSE", v)))
DOT.become((seq(string("."), Spacing).map(lambda xs: list(xs))).map(lambda v: _tag("DOT", v)))
Spacing.become((seq((((seq(Space).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(Comment).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).many()).map(lambda xs: list(xs))).map(lambda v: _tag("Spacing", v)))
Space.become((seq(regex(r"[

]")).map(lambda xs: list(xs))).map(lambda v: _tag("Space", v)))
Comment.become((seq(string("#"), (seq(_not(string("
")), any_char).map(lambda xs: list(xs))).many(), ((seq(string("
")).map(lambda xs: list(xs))).map(lambda v, i=0: {"alt": i, "value": v}) | (seq(EndOfFile).map(lambda xs: list(xs))).map(lambda v, i=1: {"alt": i, "value": v}))).map(lambda xs: list(xs))).map(lambda v: _tag("Comment", v)))
EndOfFile.become((seq(_not(any_char)).map(lambda xs: list(xs))).map(lambda v: _tag("EndOfFile", v)))

parser: Parser = Grammar

