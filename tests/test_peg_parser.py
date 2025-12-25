from pathlib import Path

from parsy import ParseError

import pytest

from babi import peg_parser
from babi.peg_ast import (
    CharClass,
    Dot,
    EOF,
    LiteralString,
    Node,
    Range,
    Reference,
)

THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
GRAMMARS_DIR = ROOT_DIR / "grammars"


def test_cc():
    _parser = peg_parser.PEGParser().cc
    assert _parser.parse("[a]") == CharClass(["a"])
    assert _parser.parse("[a-f]") == CharClass([Range("a", "f")])
    assert _parser.parse("[X0-9a-fY]") == CharClass([
        "X",
        Range("0", "9"),
        Range("a", "f"),
        "Y"
    ])
    assert _parser.parse("[^a]") == CharClass(["a"], negated=True)
    assert _parser.parse("[^a-f]") == CharClass([Range("a", "f")], negated=True)


def test_choice():
    _parser = peg_parser.PEGParser().choice
    assert _parser.parse("abc") == [[Node(Reference("abc"))]]
    assert _parser.parse("(abc)") == [[Node([[Node(Reference("abc"))]])]]
    assert _parser.parse("'abc'") == [[Node(LiteralString("abc"))]]
    assert _parser.parse("[abc0-9]") == [[Node(CharClass(["a", "b", "c", Range("0", "9")]))]]
    assert _parser.parse(".+") == [[Node(Dot(), suffix="+")]]
    assert _parser.parse("&abc") == [[Node(Reference("abc"), prefix="&")]]
    assert _parser.parse("!abc") == [[Node(Reference("abc"), prefix="!")]]
    assert _parser.parse("abc?") == [[Node(Reference("abc"), suffix="?")]]
    assert _parser.parse("abc+") == [[Node(Reference("abc"), suffix="+")]]
    assert _parser.parse("abc *") == [[Node(Reference("abc"), suffix="*")]]
    assert _parser.parse("!a*") == [[Node(Reference("a"), prefix="!", suffix="*")]]
    assert _parser.parse("abc def") == [[Node(Reference("abc")), Node(Reference("def"))]]
    assert _parser.parse("abc / def") == [[Node(Reference("abc"))], [Node(Reference("def"))]]
    assert _parser.parse("abc / (def ghi)*") == [
        [Node(Reference("abc"))],
        [Node([[Node(Reference("def")), Node(Reference("ghi"))]], suffix="*")],
    ]


def test_comment():
    _parser = peg_parser.PEGParser().comment
    assert _parser.parse("# comment\n") == "# comment"
    assert _parser.parse("# comment") == "# comment"


def test_definition():
    _parser = peg_parser.PEGParser().definition
    assert _parser.parse("abc <- def") == ["abc", [[Node(Reference("def"))]]]


def test_escape():
    _parser = peg_parser.PEGParser().escape
    assert _parser.parse(r"\t") == r"\t"
    assert _parser.parse(r"\n") == r"\n"
    assert _parser.parse(r"\r") == r"\r"
    assert _parser.parse(r"\'") == r"\'"
    assert _parser.parse(r"\"") == r"\""
    assert _parser.parse(r"\\") == r"\\"
    assert _parser.parse(r"\x01") == r"\x01"


def test_grammar():
    assert peg_parser.parse("""\
    abc <- def
    q <- "'" ! ['] "'"
    """) == {
        "abc": [[Node(Reference("def"))]],
        "q": [[
            Node(LiteralString("'")),
            Node(CharClass(["'"]), prefix="!"),
            Node(LiteralString("'")),
        ]]
    }


def test_identifier():
    _parser = peg_parser.PEGParser().identifier
    assert _parser.parse("abc") == "abc"
    assert _parser.parse("_") == "_"
    assert _parser.parse("def_098  \t \n") == "def_098"
    with pytest.raises(ParseError):
        assert _parser.parse("1")


def test_left_arrow():
    _parser = peg_parser.PEGParser().left_arrow
    assert _parser.parse("<-") == "<-"
    assert _parser.parse("<-  \t \n") == "<-"


def test_literal():
    _parser = peg_parser.PEGParser().literal
    assert _parser.parse('"abc"') == LiteralString('abc')
    assert _parser.parse("'def'") == LiteralString('def')
    assert _parser.parse("'d\\'ef'") == LiteralString('d\\\'ef')
    assert _parser.parse("'d\\tef'") == LiteralString('d\\tef')


def test_node():
    _parser = peg_parser.PEGParser().node
    assert _parser.parse("abc") == Node(Reference("abc"))
    assert _parser.parse("(abc)") == Node([[Node(Reference("abc"))]])
    assert _parser.parse("'abc'") == Node(LiteralString("abc"))
    assert _parser.parse("[abc0-9]") == Node(CharClass(["a", "b", "c", Range("0", "9")]))
    assert _parser.parse(".+") == Node(Dot(), suffix="+")
    assert _parser.parse("&abc") == Node(Reference("abc"), prefix="&")
    assert _parser.parse("!abc") == Node(Reference("abc"), prefix="!")
    assert _parser.parse("abc?") == Node(Reference("abc"), suffix="?")
    assert _parser.parse("abc+") == Node(Reference("abc"), suffix="+")
    assert _parser.parse("abc *") == Node(Reference("abc"), suffix="*")
    assert _parser.parse("!a*") == Node(Reference("a"), prefix="!", suffix="*")


def test_peg_csv():
    peg = """\
    # csv parser in PEG
    grammar <- (record "\\n")+
    record <- field ("," field)*
    field <- quoted / unquoted
    unquoted <- ! [,\n]+
    quoted <- '"' (! '""' / ! ["\n])* '"'
    """
    assert peg_parser.parse(peg) == {
        "grammar": [[
            Node(
                [[Node(Reference("record")), Node(LiteralString("\\n"))]],
                suffix="+"
            )
        ]],
        "record": [[
            Node(Reference("field")),
            Node(
                [[Node(LiteralString(",")), Node(Reference("field"))]],
                suffix="*"
            )
        ]],
        "field": [
            [Node(Reference("quoted"))],
            [Node(Reference("unquoted"))],
        ],
        "unquoted": [[Node(CharClass([",", "\n"]), prefix="!", suffix="+")]],
        "quoted": [[
            Node(LiteralString('"')),
            Node([
                [Node(LiteralString('""'), prefix="!")],
                [Node(CharClass(['"', "\n"]), prefix="!")],
            ], suffix="*"),
            Node(LiteralString('"')),
        ]],
    }


def test_peg_example():
    peg = """\
    # a comment
    Expr    <- Sum
    Sum     <- Product (('+' / '-') Product)*
    Product <- Power (('*' / '/') Power)*
    Power <- Value ('^' Power)?
    Value <- [0-9]+ / '(' Expr ')'
    """
    assert peg_parser.parse(peg) == {
        "Expr": [[Node(Reference("Sum"))]],
        "Sum": [[
            Node(Reference("Product")),
            Node([[
                Node([
                    [Node(LiteralString("+"))],
                    [Node(LiteralString("-"))],
                ]),
                Node(Reference("Product"))
            ]], suffix="*")]],
        "Product": [[
            Node(Reference("Power")),
            Node([[
                Node([
                    [Node(LiteralString("*"))],
                    [Node(LiteralString("/"))],
                ]),
                Node(Reference("Power"))
            ]], suffix="*")]],
        "Power": [[
            Node(Reference("Value")),
            Node([[
                Node(LiteralString("^")),
                Node(Reference("Power")),
            ]], suffix="?")
        ]],
        "Value": [
            [Node(CharClass([Range("0", "9")]), suffix="+")],
            [
                Node(LiteralString("(")),
                Node(Reference("Expr")),
                Node(LiteralString(")"))
            ],
        ],
    }


def test_peg_peg():
    peg = (GRAMMARS_DIR / "peg.peg").read_text(encoding="utf-8")
    assert peg_parser.parse(peg) == {
        "Grammar": [[
            Node(Reference("Definition"), suffix="+"),
            Node(Dot(), prefix="!"),
        ]],
        "Definition": [[
            Node(Reference("Identifier")),
            Node(LiteralString("<-")),
            Node(Reference("Expression")),
        ]],
        "Expression": [[
            Node(Reference("Sequence")),
            Node([[
                Node(LiteralString("/")),
                Node(Reference("Sequence"))
            ]], suffix="*")
        ]],
        "Sequence": [[Node(Reference("Prefix"), suffix="*")]],
        "Prefix": [[
            Node([
                [Node(Reference("AND"))],
                [Node(Reference("NOT"))],
            ], suffix="?"),
            Node(Reference("Suffix")),
        ]],
        "Suffix": [[
            Node(Reference("Primary")),
            Node([
                [Node(Reference("QUESTION"))],
                [Node(Reference("STAR"))],
                [Node(Reference("PLUS"))],
            ], suffix="?")
        ]],
        "Primary": [
            [Node(Reference("Identifier")), Node(LiteralString("<-"), prefix="!")],
            [
                Node(LiteralString("(")),
                Node(Reference("Expression")),
                Node(LiteralString(")"))
            ],
            [Node(Reference("Literal"))],
            [Node(Reference("Class"))],
            [Node(Reference("DOT"))],
        ],
        "Identifier": [[
            Node(CharClass([Range("A", "Z"), Range("a", "z"), "_"])),
            Node(CharClass([Range("A", "Z"), Range("a", "z"), Range("0", "9"), "_"]), suffix="*"),
            Node(Reference("Spacing")),
        ]],
        "Literal": [[Node(Reference("SingleQuoted"))], [Node(Reference("DoubleQuoted"))]],
        "SingleQuoted": [[
            Node(LiteralString("'")),
            Node(Reference("CharSingle"), suffix="*"),
            Node(LiteralString("'")),
            Node(Reference("Spacing")),
        ]],
        "DoubleQuoted": [[
            Node(LiteralString('"')),
            Node(Reference("CharDouble"), suffix="*"),
            Node(LiteralString('"')),
            Node(Reference("Spacing")),
        ]],
        "CharSingle": [[Node(Reference("Escape"))], [Node([[
            Node(LiteralString("'"), prefix="!"),
            Node(Dot()),
        ]])]],
        "CharDouble": [[Node(Reference("Escape"))], [Node([[
            Node(LiteralString('"'), prefix="!"),
            Node(Dot()),
        ]])]],
        "Escape": [[
            Node(LiteralString("\\\\")),
            Node([
                [Node(CharClass(["'", '"', "\\\\", "n", "r", "t"]))],
                [
                    Node(LiteralString("x")),
                    Node(Reference("Hex")),
                    Node(Reference("Hex"))
                ]
            ]),
        ]],
        "Hex": [[Node(CharClass([Range("0", "9"), Range("A", "F"), Range("a", "f")]))]],
        "CharClass": [[
            Node(LiteralString("[")),
            Node(Reference("ClassItem"), suffix="*"),
            Node(LiteralString("]")),
            Node(Reference("Spacing")),
        ]],
        "ClassItem": [[Node(Reference("Range"))], [Node(Reference("ClassChar"))]],
        "Range": [[Node(Reference("ClassChar")), Node(LiteralString("-")), Node(Reference("ClassChar"))]],
        "ClassChar": [
            [Node(Reference("Escape"))], [
                Node([[
                    Node(LiteralString("]"), prefix="!"),
                    Node(Dot()),
                ]]),
            ]
        ],
        "Whitespace": [[Node(CharClass([" ", "\\t", "\\n", "\\r"]))]],
        "Spacing": [[
            Node([
                [Node(Reference("Whitespace"))],
                [Node(Reference("Comment"))]
            ], suffix="*"),
        ]],
        "Comment": [[
            Node(LiteralString("#")),
            Node([[Node(LiteralString("\\n"), prefix="!")]], suffix="*"),
            Node([
                [Node(LiteralString("\\n"))],
                [Node(Dot(), prefix="!")]
            ]),
        ]],
        "LEFTARROW": [[Node(LiteralString("<-")), Node(Reference("Spacing"))]],
        "SLASH": [[Node(LiteralString("/")), Node(Reference("Spacing"))]],
        "AND": [[Node(LiteralString("&")), Node(Reference("Spacing"))]],
        "NOT": [[Node(LiteralString("!")), Node(Reference("Spacing"))]],
        "QUESTION": [[Node(LiteralString("?")), Node(Reference("Spacing"))]],
        "STAR": [[Node(LiteralString("*")), Node(Reference("Spacing"))]],
        "PLUS": [[Node(LiteralString("+")), Node(Reference("Spacing"))]],
        "OPEN": [[Node(LiteralString("(")), Node(Reference("Spacing"))]],
        "CLOSE": [[Node(LiteralString(")")), Node(Reference("Spacing"))]],
        "DOT": [[Node(LiteralString(".")), Node(Reference("Spacing"))]],
    }



def test_sequence():
    _parser = peg_parser.PEGParser().sequence

    assert _parser.parse("abc") == [Node(Reference("abc"))]
    assert _parser.parse("(abc)") == [Node([[Node(Reference("abc"))]])]
    assert _parser.parse("'abc'") == [Node(LiteralString("abc"))]
    assert _parser.parse("[abc0-9]") == [Node(CharClass(["a", "b", "c", Range("0", "9")]))]
    assert _parser.parse(".+") == [Node(Dot(), suffix="+")]
    assert _parser.parse("&abc") == [Node(Reference("abc"), prefix="&")]
    assert _parser.parse("!abc") == [Node(Reference("abc"), prefix="!")]
    assert _parser.parse("abc?") == [Node(Reference("abc"), suffix="?")]
    assert _parser.parse("abc+") == [Node(Reference("abc"), suffix="+")]
    assert _parser.parse("abc *") == [Node(Reference("abc"), suffix="*")]
    assert _parser.parse("!a*") == [Node(Reference("a"), prefix="!", suffix="*")]
    assert _parser.parse("abc def") == [Node(Reference("abc")), Node(Reference("def"))]


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
