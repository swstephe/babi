from __future__ import annotations
from typing import Literal

import msgspec

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

# The public AST is JSON-serializable (plain dict/list primitives).
# This module only centralizes the shape constructors.


class Dot(msgspec.Struct, tag=True):
    pass


class Range(msgspec.Struct, tag=True):
    start: str
    end: str


class CC(msgspec.Struct, tag=True):
    parts: list[str | Range]
    negated: bool = False


class Identifier(msgspec.Struct, tag=True):
    identifier: str


class Term(msgspec.Struct, tag=True):
    term: Identifier | Expression | CC | Dot | str
    prefix: Literal['&', '!', None] = None
    suffix: Literal['?', '*', '+', None] = None


class Sequence(msgspec.Struct, tag=True):
    expressions: list[Term]


class Expression(msgspec.Struct, tag=True):
    sequences: list[Sequence]


class Definition(msgspec.Struct, tag=True):
    identifier: Identifier
    expression: Expression


class Grammar(msgspec.Struct, tag=True):
    definitions: list[Definition]
