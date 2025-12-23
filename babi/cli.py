from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import msgspec

from babi.codegen import generate_parser
from babi.peg_parser import parse_peg


@click.group()
def babi():
    pass


@babi.command(name="parse")
@click.argument("input")
def parse(input: str):
    """Parse a PEG grammar and emit AST JSON"""
    text = Path(input).read_text(encoding="utf-8")
    ast = parse_peg(text)
    try:
        sys.stdout.buffer.write(msgspec.json.encode(ast))
        sys.stdout.write("\n")
    except BrokenPipeError:
        return 0
    return 0


@babi.command()
@click.argument("input")
@click.option("--lang", type=click.Choice(["python", "ts"]), required=True)
def generate(input: str, lang: str):
    """Generate parser source code from a PEG grammar"""
    text = Path(input).read_text(encoding="utf-8")
    ast = parse_peg(text)
    out = generate_parser(ast=msgspec.to_builtins(ast), lang=lang)
    try:
        sys.stdout.write(out)
    except BrokenPipeError:
        return 0
    return 0


@babi.command()
@click.option("--repo-root", default=str(Path.cwd()), help="Repository root containing grammars/ and src/")
def selfhost(repo_root: str):
    """Generate babi/generated_peg_parser.py from grammars/peg.peg (self-hosting)"""
    repo_root = Path(repo_root)
    grammar_path = repo_root / "grammars" / "peg.peg"
    out_path = repo_root / "babi" / "generated_peg_parser.py"

    text = grammar_path.read_text(encoding="utf-8")
    ast = parse_peg(text)
    code = generate_parser(ast=msgspec.to_builtins(ast), lang="python")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(code, encoding="utf-8")
    tmp.replace(out_path)

    return 0


if __name__ == "__main__":
    main()


def main() -> None:
    babi()
