from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .diagnostics import Diagnostic, EffectError, LowerError, ParseError, ResolveError, TypeError, format_diagnostic
from .bridge_audit import audit_bridge_usage, format_bridge_warnings
from .flm import FlmError, add_dependency, export_manifest, find_project_root, init_project, install, list_dependencies
from .lexer import lex
from .parser import parse_program
from .ast import node_to_dict
from .resolve import resolve_program_with_stdlib
from .lower import lower_resolved
from .hir import node_to_dict as hir_to_dict
from .typecheck import check_program


def _write_junit_report(
    out_path: Path,
    *,
    test_name: str,
    failure_message: str = "",
    details: str = "",
    system_out: str = "",
) -> None:
    has_failure = bool(failure_message)
    suite = ET.Element(
        "testsuite",
        name="flavent.check",
        tests="1",
        failures="1" if has_failure else "0",
        errors="0",
    )
    case = ET.SubElement(suite, "testcase", classname="flavent.check", name=test_name)
    if has_failure:
        failure = ET.SubElement(case, "failure", message=failure_message)
        if details:
            failure.text = details
    if system_out:
        out = ET.SubElement(case, "system-out")
        out.text = system_out

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(out_path, encoding="utf-8", xml_declaration=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="flavent")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_pkg = sub.add_parser("pkg")
    pkg_sub = p_pkg.add_subparsers(dest="pkg_cmd", required=True)

    p_pkg_init = pkg_sub.add_parser("init")
    p_pkg_init.add_argument("path", nargs="?", default=".")

    p_pkg_add = pkg_sub.add_parser("add")
    p_pkg_add.add_argument("name")
    p_pkg_add.add_argument("--git", default="")
    p_pkg_add.add_argument("--rev", default="")
    p_pkg_add.add_argument("--path", default="")
    p_pkg_add.add_argument("--dev", action="store_true")
    p_pkg_add.add_argument("--root", default="")

    p_pkg_list = pkg_sub.add_parser("list")
    p_pkg_list.add_argument("--root", default="")

    p_pkg_install = pkg_sub.add_parser("install")
    p_pkg_install.add_argument("--root", default="")

    p_pkg_export = pkg_sub.add_parser("export")
    p_pkg_export.add_argument("out")
    p_pkg_export.add_argument("--root", default="")

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
    p_check.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    p_check.add_argument("--report-junit", default="", help="Write JUnit XML report for check command")

    args = p.parse_args(argv)

    if args.cmd == "pkg":
        try:
            if args.pkg_cmd == "init":
                mf = init_project(Path(args.path))
                print(str(mf))
                return 0

            root = Path(args.root) if getattr(args, "root", "") else None
            if root is None:
                root = find_project_root(Path.cwd())
            if root is None:
                raise FlmError("not in a flm project (missing flm.json); pass --root or run `flavent pkg init`")

            if args.pkg_cmd == "add":
                add_dependency(
                    root,
                    name=args.name,
                    git=args.git or None,
                    rev=args.rev or None,
                    path=args.path or None,
                    dev=bool(args.dev),
                )
                print("OK")
                return 0

            if args.pkg_cmd == "list":
                for name, spec in list_dependencies(root):
                    print(f"{name}\t{json.dumps(spec, ensure_ascii=False)}")
                return 0

            if args.pkg_cmd == "install":
                install(root)
                print("OK")
                return 0

            if args.pkg_cmd == "export":
                export_manifest(root, out_path=Path(args.out))
                print("OK")
                return 0

            raise FlmError(f"unknown pkg subcommand: {args.pkg_cmd}")

        except FlmError as e:
            print(f"PkgError: {e}")
            return 2

    path = Path(args.file)
    src = path.read_text(encoding="utf-8")

    def _write_check_report(*, failure_message: str = "", details: str = "", system_out: str = "") -> None:
        if args.cmd != "check":
            return
        out = getattr(args, "report_junit", "")
        if not out:
            return
        try:
            _write_junit_report(
                Path(out),
                test_name=str(path),
                failure_message=failure_message,
                details=details,
                system_out=system_out,
            )
        except Exception as e:
            print(f"ReportError: failed to write JUnit report: {e}")

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
        proj_root = find_project_root(path)
        module_roots = None
        if proj_root is not None:
            module_roots = [proj_root / "src", proj_root / "vendor", proj_root]
        else:
            module_roots = [path.parent]
        res = resolve_program_with_stdlib(prog, use_stdlib=use_stdlib, module_roots=module_roots)
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
            warnings = format_bridge_warnings(report)
            if getattr(args, "bridge_warn", False) or getattr(args, "strict", False):
                for line in warnings:
                    print(line)
            if getattr(args, "strict", False) and warnings:
                msg = f"StrictCheckError: {len(warnings)} warning(s) found"
                print(msg)
                _write_check_report(failure_message=msg, details="\n".join(warnings))
                return 2
            _write_check_report(system_out="\n".join(warnings))

        print("OK")
        return 0

    except ParseError as e:
        msg = _fmt_err("ParseError", e)
        print(msg)
        _write_check_report(failure_message="ParseError", details=msg)
        return 2
    except ResolveError as e:
        msg = _fmt_err("ResolveError", e)
        print(msg)
        _write_check_report(failure_message="ResolveError", details=msg)
        return 2
    except LowerError as e:
        msg = _fmt_err("LowerError", e)
        print(msg)
        _write_check_report(failure_message="LowerError", details=msg)
        return 2
    except TypeError as e:
        msg = _fmt_err("TypeError", e)
        print(msg)
        _write_check_report(failure_message="TypeError", details=msg)
        return 2
    except EffectError as e:
        msg = _fmt_err("EffectError", e)
        print(msg)
        _write_check_report(failure_message="EffectError", details=msg)
        return 2
    except FlmError as e:
        msg = f"PkgError: {e}"
        print(msg)
        _write_check_report(failure_message="PkgError", details=msg)
        return 2
    except Exception as e:
        raise
