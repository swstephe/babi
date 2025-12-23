from parsy import ParseError

import pytest

from babi import peg_ast, peg_parser
from babi.peg_ast import (
    CC,
    Definition,
    Dot,
    Expression,
    Identifier,
    Grammar,
    Range,
    Sequence,
    Term,
)


def test_cc():
    _parser = peg_parser.PEGParser().cc
    assert _parser.parse("[a]") == CC(["a"])
    assert _parser.parse("[a-f]") == CC([Range("a", "f")])
    assert _parser.parse("[X0-9a-fY]") == CC([
        "X",
        Range("0", "9"),
        Range("a", "f"),
        "Y"
    ])
    assert _parser.parse("[^a]") == CC(["a"], negated=True)
    assert _parser.parse("[^a-f]") == CC([Range("a", "f")], negated=True)


def test_comment():
    _parser = peg_parser.PEGParser().comment
    assert _parser.parse("# comment\n") == "# comment"
    assert _parser.parse("# comment") == "# comment"


def test_definition():
    _parser = peg_parser.PEGParser().definition
    assert _parser.parse("abc <- def") == Definition(
        Identifier("abc"),
        Expression([
            Sequence([
                Term(Identifier("def"))
            ])
        ])
    )


def test_escape():
    _parser = peg_parser.PEGParser().escape
    assert _parser.parse(r"\t") == r"\t"
    assert _parser.parse(r"\n") == r"\n"
    assert _parser.parse(r"\r") == r"\r"
    assert _parser.parse(r"\'") == r"\'"
    assert _parser.parse(r"\"") == r"\""
    assert _parser.parse(r"\\") == r"\\"
    assert _parser.parse(r"\x01") == r"\x01"


def test_expression():
    _parser = peg_parser.PEGParser().expression
    assert _parser.parse("abc") == Expression([Sequence([Term(Identifier("abc"))])])
    assert _parser.parse("(abc)") == Expression([Sequence([Term(
        Expression([Sequence([
            Term(Identifier("abc"))
        ])])
    )])])
    assert _parser.parse("'abc'") == Expression([Sequence([Term("abc")])])
    assert _parser.parse("[abc0-9]") == Expression([Sequence([Term(CC(["a", "b", "c", Range("0", "9")]))])])
    assert _parser.parse(".+") == Expression([Sequence([Term(Dot(), suffix="+")])])
    assert _parser.parse("&abc") == Expression([Sequence([Term(Identifier("abc"), prefix="&")])])
    assert _parser.parse("!abc") == Expression([Sequence([Term(Identifier("abc"), prefix="!")])])
    assert _parser.parse("abc?") == Expression([Sequence([Term(Identifier("abc"), suffix="?")])])
    assert _parser.parse("abc+") == Expression([Sequence([Term(Identifier("abc"), suffix="+")])])
    assert _parser.parse("abc *") == Expression([Sequence([Term(Identifier("abc"), suffix="*")])])
    assert _parser.parse("!a*") == Expression([Sequence([Term(Identifier("a"), prefix="!", suffix="*")])])
    assert _parser.parse("abc def") == Expression([Sequence([
        Term(Identifier("abc")),
        Term(Identifier("def")),
    ])])
    assert _parser.parse("abc / def") == Expression([
        Sequence([Term(Identifier("abc"))]),
        Sequence([Term(Identifier("def"))]),
    ])
    assert _parser.parse("abc / (def ghi)*") == Expression([
        Sequence([Term(Identifier("abc"))]),
        Sequence([Term(
            Expression([Sequence([
                Term(peg_ast.Identifier("def")),
                Term(peg_ast.Identifier("ghi"))
            ])]),
            suffix="*")]),
    ])


def test_grammar():
    assert peg_parser.parse("""\
    abc <- def
    q <- "'" ! ['] "'"
    """) == Grammar([
        Definition(
            Identifier("abc"),
            Expression([
                Sequence([
                    Term(Identifier("def"))
                ])
            ])
        ),
        Definition(
            Identifier("q"),
            Expression([
                Sequence([
                    Term("'"),
                    Term(CC(["'"], negated=True)),
                    Term("'")
                ])
            ])
        ),
    ])


def test_identifier():
    _parser = peg_parser.PEGParser().identifier
    assert _parser.parse("abc") == Identifier("abc")
    assert _parser.parse("_") == Identifier("_")
    assert _parser.parse("def_098  \t \n") == Identifier("def_098")
    with pytest.raises(ParseError):
        assert _parser.parse("1")


def test_left_arrow():
    _parser = peg_parser.PEGParser().left_arrow
    assert _parser.parse("<-") == "<-"
    assert _parser.parse("<-  \t \n") == "<-"


def test_literal():
    _parser = peg_parser.PEGParser().literal
    assert _parser.parse('"abc"') == 'abc'
    assert _parser.parse("'def'") == 'def'
    assert _parser.parse("'d\\'ef'") == 'd\\\'ef'
    assert _parser.parse("'d\\tef'") == 'd\\tef'


def test_peg_csv():
    assert peg_parser.parse("""\
    # csv parser in PEG
    """) == Grammar([])
    # peg = """\
    # # csv parser in PEG
    # grammar <- (record "\n")+
    # record <- field ("," field)*
    # field <- quoted | unquoted
    # unquoted <- [^,\n]+
    # quoted <- '"' (!'""' | [^"\n])* '"'
    # """
    # peg = """\
    # # csv parser in PEG
    # quoted <- '"' (!'""' | [^"\n])* '"'
    # """
    # assert peg_parser.parse(peg) == Grammar([
    # ])


def test_peg_example():
    # Product <- Power (('*' / '/') Power)*
    # Power <- Value ('^' Power)?
    # Value <- [0-9]+ / '(' Expr ')'
    #
    peg = """\
    # a comment
    Expr    <- Sum
    Sum     <- Product (Product)
    """
    assert peg_parser.parse(peg) == Grammar([
        Definition(
            Identifier("Expr"),
            Expression([Sequence([Term(Identifier("Sum"))])])
        ),
        Definition(
            Identifier("Sum"),
            Expression([
                Sequence([
                    Term(Identifier("Product")),
                    Term(Expression([Sequence([Term(Identifier("Product"))])])),
                    # Term(
                    #     Expression([
                    #         Sequence([
                    #             Term(Expression([Sequence([Term("+")]), Sequence([Term("-")])])),
                    #             Term(Identifier("Product")),
                    #         ])
                    #     ]),
                    #     suffix="*"
                    # )
                ]),
            ])
        ),
        # Definition(
        #     Identifier("Product"),
        #     Expression([
        #         Sequence([Term(Identifier("Power"))]),
        #         Sequence([
        #             Term(Identifier("Power"), prefix=None, suffix="*"),
        #             Term(Identifier("Power"), prefix=None, suffix="/"),
        #         ])
        #     ])
        # ),
        # Definition(
        #     Identifier("Power"),
        #     Expression([
        #         Sequence([Term(Identifier("Value"))]),
        #         Sequence([
        #             Term(Identifier("Value"), prefix=None, suffix="^"),
        #             Term(Identifier("Power"), prefix=None, suffix=None),
        #         ])
        #     ])
        # ),
        # Definition(
        #     Identifier("Value"),
        #     Expression([
        #         Sequence([Term(peg_ast.Range("0", "9"))]),
        #         Sequence([
        #             Term(peg_ast.Identifier("Expr"), prefix=None, suffix=None),
        #         ])
        #     ])
        # )
    ])


def test_sequence():
    _parser = peg_parser.PEGParser().sequence

    assert _parser.parse("abc") == Sequence([Term(Identifier("abc"))])
    assert _parser.parse("(abc)") == Sequence([Term(
        Expression([Sequence([
            Term(Identifier("abc"))
        ])])
    )])
    assert _parser.parse("'abc'") == Sequence([Term("abc")])
    assert _parser.parse("[abc0-9]") == Sequence([Term(CC(["a", "b", "c", Range("0", "9")]))])
    assert _parser.parse(".+") == Sequence([Term(Dot(), suffix="+")])
    assert _parser.parse("&abc") == Sequence([Term(Identifier("abc"), prefix="&")])
    assert _parser.parse("!abc") == Sequence([Term(Identifier("abc"), prefix="!")])
    assert _parser.parse("abc?") == Sequence([Term(Identifier("abc"), suffix="?")])
    assert _parser.parse("abc+") == Sequence([Term(Identifier("abc"), suffix="+")])
    assert _parser.parse("abc *") == Sequence([Term(Identifier("abc"), suffix="*")])
    assert _parser.parse("!a*") == Sequence([Term(Identifier("a"), prefix="!", suffix="*")])
    assert _parser.parse("abc def") == Sequence([
        Term(Identifier("abc")),
        Term(Identifier("def")),
    ])


def test_slash():
    _parser = peg_parser.PEGParser().slash
    assert _parser.parse("/") == "/"
    assert _parser.parse("/ \t\n") == "/"


def test_space():
    _parser = peg_parser.PEGParser().space
    assert _parser.parse(" ") == " "
    assert _parser.parse(" \t \r\n \t ") == " \t \r\n \t "


def test_spacing():
    _parser = peg_parser.PEGParser().spacing
    assert _parser.parse("   # comment\n") is None
    assert _parser.parse("# comment  \t\n\r  ") is None


def test_term():
    _parser = peg_parser.PEGParser().term
    assert _parser.parse("abc") == Term(Identifier("abc"))
    assert _parser.parse("(abc)") == Term(Expression([Sequence([
        Term(Identifier("abc"))
    ])]))
    assert _parser.parse("'abc'") == Term("abc")
    assert _parser.parse("[abc0-9]") == Term(CC(["a", "b", "c", Range("0", "9")]))
    assert _parser.parse(".+") == Term(Dot(), suffix="+")
    assert _parser.parse("&abc") == Term(Identifier("abc"), prefix="&")
    assert _parser.parse("!abc") == Term(Identifier("abc"), prefix="!")
    assert _parser.parse("abc?") == Term(Identifier("abc"), suffix="?")
    assert _parser.parse("abc+") == Term(Identifier("abc"), suffix="+")
    assert _parser.parse("abc *") == Term(Identifier("abc"), suffix="*")
    assert _parser.parse("!a*") == Term(Identifier("a"), prefix="!", suffix="*")
