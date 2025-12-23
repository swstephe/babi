from __future__ import annotations

from parsy import (
    Parser,
    alt,
    any_char,
    eof,
    fail,
    forward_declaration,
    generate,
    regex,
    seq,
    string,
    success,
)

from babi.peg_ast import (
    CC,
    Definition,
    Dot,
    Expression,
    Grammar,
    Identifier,
    Range,
    Sequence,
    Term,
)


class PEGParser:
    # tokens
    space = regex(r"[ \t\n\r]+")
    comment = regex(r"#[^\n]*") << (string("\n") | eof)
    spacing = (space | comment).many().map(lambda _: None)

    left_arrow = string("<-") << spacing
    slash = string("/") << spacing

    escape = seq(string("\\"), regex(r"[\\\"'nrt]") | regex("x[A-Fa-f0-9]{2}")).concat()
    char_single = escape | regex(r"[^']")
    char_double = escape | regex(r'[^"]')
    single_quoted = string("'") >> char_single.many().concat() << string("'")
    double_quoted = string('"') >> char_double.many().concat() << string('"')
    literal = single_quoted | double_quoted

    class_char = escape | regex(r"[^\]]")
    range = seq(class_char << string("-"), class_char).combine(Range)
    class_item = alt(range, class_char)
    cc = seq(
        string("[") >> string("^").optional() | success(None),
        class_item.many() << string("]")
    ).combine(
        lambda negated, parts: CC(parts, negated=negated is not None)
    ) << spacing

    expression = forward_declaration()
    identifier = (regex(r"[A-Za-z_][A-Za-z0-9_]*") << spacing).map(Identifier)
    term = seq(
        alt(string("&"), string("!")).optional() << spacing,
        alt(
            identifier << left_arrow.should_fail("ref"),
            string(".").map(lambda _: Dot()),
            string("(") >> expression << string(")"),
            literal,
            cc,
        ),
        alt(string("?"), string("*"), string("+")).optional() << spacing,
    ).combine(lambda p, t, s: Term(term=t, prefix=p, suffix=s))
    sequence = term.sep_by(spacing).map(Sequence)
    expression.become(sequence.sep_by(slash).map(Expression))
    definition = seq(identifier << left_arrow, expression).combine(Definition)
    parser = (spacing >> definition.at_least(1) << eof).map(Grammar)


def parse(source: str) -> Grammar:
    """Parse a PEG grammar into a JSON-serializable AST."""
    return PEGParser().parser.parse(source)
