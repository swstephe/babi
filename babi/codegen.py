from __future__ import annotations
from typing import Literal

Languages = Literal["python", "ts"]


def generate_parser(*, ast: dict, lang: Languages) -> str:
    if ast.get("type") != "grammar":
        raise ValueError("expected grammar AST")
    rules = ast.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("grammar has no rules")

    if lang == "python":
        return _generate_python(ast)
    if lang == "ts":
        return _generate_ts(ast)
    raise ValueError(f"unknown lang: {lang}")


def _collect_rules(ast: dict) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for r in ast["rules"]:
        if not isinstance(r, dict) or r.get("type") != "rule":
            continue
        out.append((r["name"], r["expr"]))
    if not out:
        raise ValueError("no rule definitions")
    return out


def _generate_python(ast: dict) -> str:
    rules = _collect_rules(ast)
    rule_names = [name for name, _ in rules]
    start = rule_names[0]

    lines: list[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("import parsy")
    lines.append("from parsy import Parser, any_char, generate, regex, seq, string")
    lines.append("")
    lines.append("__all__ = [\"parser\"]")
    lines.append("")
    lines.append("def _tag(name: str, value):")
    lines.append("    return {\"type\": name, \"value\": value}")
    lines.append("")
    lines.append("def _and(p: Parser) -> Parser:")
    lines.append("    @Parser")
    lines.append("    def and_parser(stream, index):")
    lines.append("        res = p(stream, index)")
    lines.append("        if res.status:")
    lines.append("            return parsy.Result.success(index, True)")
    lines.append("        return res")
    lines.append("    return and_parser")
    lines.append("")
    lines.append("def _not(p: Parser) -> Parser:")
    lines.append("    return p.should_fail('not').result(True)")
    lines.append("")

    for name in rule_names:
        lines.append(f"{name}: Parser = parsy.forward_declaration()")
    lines.append("")

    def emit_expr(e: dict) -> str:
        t = e.get("type")
        if t == "ref":
            return e["name"]
        if t == "literal":
            s = e["value"].replace("\\", "\\\\").replace('"', '\\"')
            return f"string(\"{s}\")"
        if t == "dot":
            return "any_char"
        if t == "class":
            parts = e.get("parts", [])
            neg = bool(e.get("negated"))
            pat = ""
            for p in parts:
                if p.get("type") == "char":
                    v = p["value"]
                    if v in r"\\^-[]":
                        v = "\\" + v
                    pat += v
                elif p.get("type") == "range":
                    a = p["start"]
                    b = p["end"]
                    for x in (a, b):
                        pass
                    if a in r"\\^-[]":
                        a = "\\" + a
                    if b in r"\\^-[]":
                        b = "\\" + b
                    pat += f"{a}-{b}"
                else:
                    raise ValueError(f"unknown class part: {p}")
            if neg:
                pat = "^" + pat
            # Use regex for single-char class
            return f"regex(r\"[{pat}]\")"
        if t == "sequence":
            items = [emit_expr(x) for x in e.get("items", [])]
            if not items:
                return "parsy.success([])"
            return f"seq({', '.join(items)}).map(lambda xs: list(xs))"
        if t == "choice":
            alts = [emit_expr(x) for x in e.get("alts", [])]
            # Tag which alternative matched
            tagged = [f"({a}).map(lambda v, i={i}: {{\"alt\": i, \"value\": v}})" for i, a in enumerate(alts)]
            return "(" + " | ".join(tagged) + ")"
        if t == "and":
            inner = emit_expr(e["expr"])
            return f"_and({inner})"
        if t == "not":
            inner = emit_expr(e["expr"])
            return f"_not({inner})"
        if t == "opt":
            inner = emit_expr(e["expr"])
            return f"({inner}).optional()"
        if t == "star":
            inner = emit_expr(e["expr"])
            return f"({inner}).many()"
        if t == "plus":
            inner = emit_expr(e["expr"])
            return f"({inner}).at_least(1)"
        raise ValueError(f"unknown expr type: {t}")

    for name, expr in rules:
        rhs = emit_expr(expr)
        lines.append(f"{name}.become(({rhs}).map(lambda v: _tag(\"{name}\", v)))")

    lines.append("")
    lines.append(f"parser: Parser = {start}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _generate_ts(ast: dict) -> str:
    rules = _collect_rules(ast)
    rule_names = [name for name, _ in rules]
    start = rule_names[0]

    lines: list[str] = []
    lines.append("import * as P from 'parsimmon';")
    lines.append("")
    lines.append("type Json = null | boolean | number | string | Json[] | { [k: string]: Json };")
    lines.append("")
    lines.append("const _tag = (name: string, value: Json): Json => ({ type: name, value });")
    lines.append("")

    for name in rule_names:
        lines.append(f"const {name}: P.Parser<Json> = P.lazy(() => _{name});")
    lines.append("")

    def emit_expr(e: Dict) -> str:
        t = e.get("type")
        if t == "ref":
            return e["name"]
        if t == "literal":
            s = (
                e["value"]
                .replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("$", "\\$")
            )
            return f"P.string(`{s}`)"
        if t == "dot":
            return "P.any"
        if t == "class":
            parts = e.get("parts", [])
            neg = bool(e.get("negated"))
            pat = ""
            for p in parts:
                if p.get("type") == "char":
                    v = p["value"]
                    if v in r"\\^-[]":
                        v = "\\" + v
                    pat += v
                elif p.get("type") == "range":
                    a = p["start"]
                    b = p["end"]
                    if a in r"\\^-[]":
                        a = "\\" + a
                    if b in r"\\^-[]":
                        b = "\\" + b
                    pat += f"{a}-{b}"
                else:
                    raise ValueError(f"unknown class part: {p}")
            if neg:
                pat = "^" + pat
            return f"P.regex(/[{pat}]/)"
        if t == "sequence":
            items = [emit_expr(x) for x in e.get("items", [])]
            if not items:
                return "P.succeed([] as Json[])"
            return f"P.seqMap({', '.join(items)}, (...xs) => xs as Json[])"
        if t == "choice":
            alts = [emit_expr(x) for x in e.get("alts", [])]
            tagged = [f"({a}).map(value => ({{ alt: {i}, value }} as Json))" for i, a in enumerate(alts)]
            return f"P.alt({', '.join(tagged)})"
        if t == "and":
            inner = emit_expr(e["expr"])
            return f"P.lookahead({inner}).result(true as Json)"
        if t == "not":
            inner = emit_expr(e["expr"])
            return f"P.notFollowedBy({inner}).result(true as Json)"
        if t == "opt":
            inner = emit_expr(e["expr"])
            return f"({inner}).fallback(null as Json)"
        if t == "star":
            inner = emit_expr(e["expr"])
            return f"({inner}).many()"
        if t == "plus":
            inner = emit_expr(e["expr"])
            return f"({inner}).atLeast(1)"
        raise ValueError(f"unknown expr type: {t}")

    for name, expr in rules:
        rhs = emit_expr(expr)
        lines.append(f"const _{name}: P.Parser<Json> = ({rhs}).map(v => _tag('{name}', v as Json));")

    lines.append("")
    lines.append(f"export const parser: P.Parser<Json> = {start};")
    lines.append("")
    return "\n".join(lines) + "\n"
