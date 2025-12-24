from __future__ import annotations
from typing import Literal

import msgspec

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

# The public AST is JSON-serializable (plain dict/list primitives).
# This module only centralizes the shape constructors.

type Identifier = str
type Atom = EOF | Dot | CharClass | LiteralString | Reference | Choice
type Sequence = list[Node]
type Choice = list[Sequence]
type Expression = Choice
type Grammar = dict[Identifier, Expression]


class Dot(msgspec.Struct, tag=True):
    pass


class EOF(msgspec.Struct, tag=True):
    pass


class Range(msgspec.Struct, tag=True):
    start: str
    end: str


class CharClass(msgspec.Struct, tag=True):
    parts: list[str | Range]
    negated: bool = False


class LiteralString(msgspec.Struct, tag=True):
    value: str


class Reference(msgspec.Struct, tag=True):
    name: Identifier


class Node(msgspec.Struct, tag=True):
    atom: Atom
    prefix: Literal['&', '!', None] = None
    suffix: Literal['?', '*', '+', None] = None
