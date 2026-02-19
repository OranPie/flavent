import pytest

from flavent.diagnostics import ResolveError
from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.resolve import resolve_program_with_stdlib


def test_resolve_minimal_program():
    src = """type Event.Start = {}\n\nfn solve(input: Str) -> Str = input\n\nsector main:\n  on Event.Start -> do:\n    stop()\n\nrun()\n"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program(prog)
    assert len(res.symbols) > 0

    # ensure main sector exists
    main_ids = [s.id for s in res.symbols if s.kind.name == "SECTOR" and s.name == "main"]
    assert main_ids


def test_resolve_name_not_found():
    src = """fn f(x: Int) = y\n"""
    prog = parse_program(lex("test.flv", src))
    try:
        resolve_program(prog)
        assert False, "expected resolution error"
    except Exception as e:
        assert "NameNotFound" in str(e)


def test_resolve_duplicate_import_ok_and_namespaced_disambiguation():
    src = """use std.option
use std.result

fn f() -> Int = std.option.unwrapOr(None, 0)
fn g() -> Int = std.result.unwrapOrErr(Ok(1), 0)

run()
"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=False)
    assert len(res.symbols) > 0


def test_resolve_ambiguous_unqualified_usage_errors_at_use_site():
    src = """use testns.a
use testns.b

fn f() -> Int = foo()

run()
"""
    prog = parse_program(lex("test.flv", src))
    try:
        resolve_program_with_stdlib(prog, use_stdlib=False)
        assert False, "expected resolution error"
    except Exception as e:
        assert "NameAmbiguity" in str(e)


def test_resolve_namespaced_usage_with_stdlib_modules():
    src = """use std.option
use std.result

fn f() -> Int = std.option.unwrapOr(None, 0)
fn g() -> Str = std.option.unwrapOr(Some("x"), "y")
fn h() -> Bool = std.result.isOk(Ok(1))

run()
"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=False)
    assert len(res.symbols) > 0


def test_resolve_default_discard_binding_allows_repeated_underscore():
    src = """fn f() -> Int = do:
  let _ = 1
  let _ = 2
  return 0

run()
"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=False)
    assert len(res.symbols) > 0


def test_resolve_discard_binding_cannot_be_referenced():
    src = """fn f() -> Int = do:
  let _ = 1
  return _

run()
"""
    prog = parse_program(lex("test.flv", src))
    with pytest.raises(ResolveError, match="NameNotFound: _"):
        resolve_program_with_stdlib(prog, use_stdlib=False)


def test_resolve_flvdiscard_config_overrides_default_name(tmp_path):
    (tmp_path / "flvdiscard").write_text("drop\n", encoding="utf-8")

    ok_src = """fn f() -> Int = do:
  let drop = 1
  let drop = 2
  return 0

run()
"""
    ok_prog = parse_program(lex(str(tmp_path / "main_ok.flv"), ok_src))
    res = resolve_program_with_stdlib(ok_prog, use_stdlib=False, module_roots=[tmp_path])
    assert len(res.symbols) > 0

    bad_src = """fn f() -> Int = do:
  let _ = 1
  let _ = 2
  return 0

run()
"""
    bad_prog = parse_program(lex(str(tmp_path / "main_bad.flv"), bad_src))
    with pytest.raises(ResolveError, match="Duplicate name in same scope: _"):
        resolve_program_with_stdlib(bad_prog, use_stdlib=False, module_roots=[tmp_path])
