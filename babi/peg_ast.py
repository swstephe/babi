from __future__ import annotations

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]


# The public AST is JSON-serializable (plain dict/list primitives).
# This module only centralizes the shape constructors.

def rule(name: str, expr: Json) -> dict[str, Json]:
    return {"type": "rule", "name": name, "expr": expr}


def choice(alts: list[Json]) -> dict[str, Json]:
    return {"type": "choice", "alts": alts}


def sequence(items: list[Json]) -> dict[str, Json]:
    return {"type": "sequence", "items": items}


def andp(expr: Json) -> dict[str, Json]:
    return {"type": "and", "expr": expr}


def notp(expr: Json) -> dict[str, Json]:
    return {"type": "not", "expr": expr}


def opt(expr: Json) -> dict[str, Json]:
    return {"type": "opt", "expr": expr}


def star(expr: Json) -> dict[str, Json]:
    return {"type": "star", "expr": expr}


def plus(expr: Json) -> dict[str, Json]:
    return {"type": "plus", "expr": expr}


def ref(name: str) -> dict[str, Json]:
    return {"type": "ref", "name": name}


def literal(value: str) -> dict[str, Json]:
    return {"type": "literal", "value": value}


def char_class(parts: list[Json], negated: bool = False) -> dict[str, Json]:
    return {"type": "class", "negated": negated, "parts": parts}


def class_range(start: str, end: str) -> dict[str, Json]:
    return {"type": "range", "start": start, "end": end}


def class_char(ch: str) -> dict[str, Json]:
    return {"type": "char", "value": ch}


def dot() -> dict[str, Json]:
    return {"type": "dot"}
