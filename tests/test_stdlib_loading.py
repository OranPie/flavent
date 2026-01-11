import pytest

from flavent.diagnostics import ResolveError
from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.symbols import SymbolKind


def test_no_stdlib_rejects_option_result_types():
    src = """fn f() -> Option[Int] = None
fn g() -> Result[Int, Str] = Ok(1)
"""
    prog = parse_program(lex("test.flv", src))
    with pytest.raises(ResolveError):
        resolve_program_with_stdlib(prog, use_stdlib=False)


def test_stdlib_defines_option_result_and_ctors():
    src = """fn f() -> Option[Int] = None
fn g() -> Result[Int, Str] = Ok(1)
"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)

    opt = next(s for s in res.symbols if s.kind == SymbolKind.TYPE and s.name == "Option")
    res_ty = next(s for s in res.symbols if s.kind == SymbolKind.TYPE and s.name == "Result")

    assert opt.span.file.endswith("stdlib/std/option.flv")
    assert res_ty.span.file.endswith("stdlib/std/result.flv")

    ok_ctor = next(s for s in res.symbols if s.kind == SymbolKind.CTOR and s.name == "Ok")
    err_ctor = next(s for s in res.symbols if s.kind == SymbolKind.CTOR and s.name == "Err")
    some_ctor = next(s for s in res.symbols if s.kind == SymbolKind.CTOR and s.name == "Some")
    none_ctor = next(s for s in res.symbols if s.kind == SymbolKind.CTOR and s.name == "None")

    assert ok_ctor.span.file.endswith("stdlib/std/result.flv")
    assert err_ctor.span.file.endswith("stdlib/std/result.flv")
    assert some_ctor.span.file.endswith("stdlib/std/option.flv")
    assert none_ctor.span.file.endswith("stdlib/std/option.flv")

    assert ok_ctor.owner == res_ty.id
    assert err_ctor.owner == res_ty.id
    assert some_ctor.owner == opt.id
    assert none_ctor.owner == opt.id


def test_stdlib_polymorphic_fns_infer_at_callsite():
    src = """fn f() -> Int = unwrapOr(None, 0)
fn g() -> Str = unwrapOr(Some("x"), "y")
fn h() -> Bool = isOk(Ok(1))
"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)

    from flavent.lower import lower_resolved
    from flavent.typecheck import check_program

    hir = lower_resolved(res)
    check_program(hir, res)
