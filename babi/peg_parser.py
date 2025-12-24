from __future__ import annotations

from parsy import (
    alt,
    eof,
    forward_declaration,
    peek,
    regex,
    seq,
    string,
)

from babi.peg_ast import (
    CharClass,
    Dot,
    EOF,
    Grammar,
    LiteralString,
    Node,
    Range,
    Reference,
)


class PEGParser:
    # ignore whitespace and comments
    space = regex(r"[ \t\n\r]+")
    comment = regex(r"#[^\n]*") << (string("\n") | eof)
    spacing = (space | comment).many().map(lambda _: None)

    # operators
    and_op = string("&") << spacing
    not_op = string("!") << spacing
    opt_op = string("?") << spacing
    star_op = string("*") << spacing
    plus_op = string("+") << spacing

    dot = (string(".") << spacing).map(lambda _: Dot())

    left_arrow = string("<-") << spacing
    slash = string("/") << spacing

    # literal strings
    escape = seq(string("\\"), regex(r"[\\\"'nrt]") | regex("x[A-Fa-f0-9]{2}")).concat()
    char_single = escape | regex(r"[^']")
    char_double = escape | regex(r'[^"]')
    single_quoted = string("'") >> char_single.many().concat() << string("'")
    double_quoted = string('"') >> char_double.many().concat() << string('"')
    literal = alt(single_quoted, double_quoted).map(LiteralString) << spacing

    # character class regular expressions
    class_char = escape | regex(r"[^\]]")
    range = seq(class_char << string("-"), class_char).combine(Range)
    class_item = alt(range, class_char)
    cc = seq(
        string("[") >> string("^").optional().map(lambda x: x is not None),
        class_item.many() << string("]")
    ).combine(
        lambda negated, parts: CharClass(parts, negated=negated)
    ) << spacing

    choice = forward_declaration()
    group = string("(") >> choice << string(")") << spacing
    identifier = (regex(r"[A-Za-z_][A-Za-z0-9_]*") << spacing)
    ref = identifier.map(Reference)
    atom = alt(dot, group, literal, cc, ref)
    node = seq(
        alt(and_op, not_op).optional(),
        atom,
        alt(opt_op, star_op, plus_op).optional(),
    ).combine(lambda p, a, s: Node(atom=a, prefix=p, suffix=s))
    sequence = (
        peek(identifier >> left_arrow).should_fail("new_definition") >> node
    ).at_least(1)
    choice.become(sequence.sep_by(slash))
    definition = seq(identifier << left_arrow, choice)
    parser = (spacing >> definition.at_least(1) << eof).map(dict)


def parse(source: str) -> Grammar:
    """
    Parse a PEG grammar into an AST representation.

    param: source: PEG grammar source code
    return: AST representation of the grammar
    """
    return PEGParser().parser.parse(source)
