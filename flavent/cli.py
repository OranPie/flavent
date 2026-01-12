from __future__ import annotations

import argparse
import json
from pathlib import Path

from .diagnostics import Diagnostic, EffectError, LowerError, ParseError, ResolveError, TypeError, format_diagnostic
from .bridge_audit import audit_bridge_usage, format_bridge_warnings
from .lexer import lex
from .parser import parse_program
from .ast import node_to_dict
from .resolve import resolve_program_with_stdlib
from .lower import lower_resolved
from .hir import node_to_dict as hir_to_dict
from .typecheck import check_program


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="flavent")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_lex = sub.add_parser("lex")
    p_lex.add_argument("file")

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("file")

    p_resolve = sub.add_parser("resolve")
    p_resolve.add_argument("file")
    p_resolve.add_argument("--no-stdlib", action="store_true")

    p_hir = sub.add_parser("hir")
    p_hir.add_argument("file")
    p_hir.add_argument("--no-stdlib", action="store_true")

    p_check = sub.add_parser("check")
    p_check.add_argument("file")
    p_check.add_argument("--no-stdlib", action="store_true")
    p_check.add_argument("--bridge-report", default="", help="Write bridge usage report JSON to this path")
    p_check.add_argument("--bridge-warn", action="store_true", help="Print warnings for deprecated bridge shims")

    args = p.parse_args(argv)
    path = Path(args.file)
    src = path.read_text(encoding="utf-8")

    def _fmt_err(kind: str, e) -> str:
        try:
            s = Path(e.span.file).read_text(encoding="utf-8")
        except Exception:
            s = src
        msg = f"{kind}: {e.message}"
        return format_diagnostic(s, Diagnostic(message=msg, span=e.span))

    try:
        toks = lex(str(path), src)
        if args.cmd == "lex":
            for t in toks:
                print(f"{t.kind.name}\t{t.text!r}\t{t.span.line}:{t.span.col}")
            return 0

        prog = parse_program(toks)
        if args.cmd == "parse":
            print(json.dumps(node_to_dict(prog), indent=2, ensure_ascii=False))
            return 0

        use_stdlib = not getattr(args, "no_stdlib", False)
        res = resolve_program_with_stdlib(prog, use_stdlib=use_stdlib)
        if args.cmd == "resolve":
            out = {
                "program": node_to_dict(res.program),
                "symbols": [
                    {
                        "id": s.id,
                        "kind": s.kind.name,
                        "name": s.name,
                        "owner": s.owner,
                        "span": node_to_dict(s.span),
                        "data": s.data,
                    }
                    for s in res.symbols
                ],
                "ident_to_symbol": res.ident_to_symbol,
                "typename_to_symbol": res.typename_to_symbol,
                "handler_to_symbol": res.handler_to_symbol,
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0

        hir_prog = lower_resolved(res)
        if args.cmd == "hir":
            print(json.dumps(hir_to_dict(hir_prog), indent=2, ensure_ascii=False))
            return 0

        check_program(hir_prog, res)

        if args.cmd == "check":
            report = audit_bridge_usage(hir_prog, res)
            if getattr(args, "bridge_report", ""):
                Path(args.bridge_report).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            if getattr(args, "bridge_warn", False):
                for line in format_bridge_warnings(report):
                    print(line)

        print("OK")
        return 0

    except ParseError as e:
        print(_fmt_err("ParseError", e))
        return 2
    except ResolveError as e:
        print(_fmt_err("ResolveError", e))
        return 2
    except LowerError as e:
        print(_fmt_err("LowerError", e))
        return 2
    except TypeError as e:
        print(_fmt_err("TypeError", e))
        return 2
    except EffectError as e:
        print(_fmt_err("EffectError", e))
        return 2
    except Exception as e:
        raise
