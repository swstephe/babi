from __future__ import annotations

import parsy
from parsy import Parser, any_char, regex, seq, string

__all__ = ["parser"]

def _tag(name: str, value):
    return {"type": name, "value": value}

def _and(p: Parser) -> Parser:
    @Parser
    def and_parser(stream, index):
        res = p(stream, index)
        if res.status:
            return parsy.Result.success(index, True)
        return res
    return and_parser

def _not(p: Parser) -> Parser:
    return p.should_fail('not').result(True)

Grammar: Parser = parsy.forward_declaration()
Definition: Parser = parsy.forward_declaration()
Expression: Parser = parsy.forward_declaration()
Sequence: Parser = parsy.forward_declaration()
Prefix: Parser = parsy.forward_declaration()
Suffix: Parser = parsy.forward_declaration()
Primary: Parser = parsy.forward_declaration()
Identifier: Parser = parsy.forward_declaration()
IdentStart: Parser = parsy.forward_declaration()
IdentCont: Parser = parsy.forward_declaration()
Literal: Parser = parsy.forward_declaration()
SingleQuoted: Parser = parsy.forward_declaration()
DoubleQuoted: Parser = parsy.forward_declaration()
CharSingle: Parser = parsy.forward_declaration()
CharDouble: Parser = parsy.forward_declaration()
Escape: Parser = parsy.forward_declaration()
Hex: Parser = parsy.forward_declaration()
Class: Parser = parsy.forward_declaration()
ClassItem: Parser = parsy.forward_declaration()
Range: Parser = parsy.forward_declaration()
ClassChar: Parser = parsy.forward_declaration()
LEFTARROW: Parser = parsy.forward_declaration()
SLASH: Parser = parsy.forward_declaration()
AND: Parser = parsy.forward_declaration()
NOT: Parser = parsy.forward_declaration()
QUESTION: Parser = parsy.forward_declaration()
STAR: Parser = parsy.forward_declaration()
PLUS: Parser = parsy.forward_declaration()
OPEN: Parser = parsy.forward_declaration()
CLOSE: Parser = parsy.forward_declaration()
DOT: Parser = parsy.forward_declaration()
Spacing: Parser = parsy.forward_declaration()
Space: Parser = parsy.forward_declaration()
Comment: Parser = parsy.forward_declaration()
EndOfFile: Parser = parsy.forward_declaration()

Grammar.become((seq(Spacing, (Definition).at_least(1), EndOfFile).map(lambda xs: list(xs))).map(lambda v: _tag("Grammar", v)))
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

