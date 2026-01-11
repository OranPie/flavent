import pytest

from flavent.diagnostics import ResolveError
from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.lower import lower_resolved
from flavent.typecheck import check_program


def _check(src: str, *, use_stdlib: bool = False):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=use_stdlib)
    hir = lower_resolved(res)
    check_program(hir, res)


def test_type_mixin_field_injection_record():
    src = """type User = { id: Int }

mixin Extra v1 into type User:
  age: Int

use mixin Extra v1

fn f(u: User) -> Int = u.age
run()
"""
    _check(src, use_stdlib=True)


def test_type_mixin_method_injection_type_dot_call():
    src = """type User = { id: Int }

mixin M v1 into type User:
  fn getId(self: User) -> Int = self.id

use mixin M v1

fn f(u: User) -> Int = User.getId(u)
run()
"""
    _check(src, use_stdlib=True)


def test_pattern_alias_in_match():
    src = """pattern IsOk = Ok(_)

fn f(x: Result[Int, Str]) -> Int = match x:
  IsOk -> 1
  Err(_) -> 0

run()
"""
    _check(src, use_stdlib=True)


def test_pattern_alias_cannot_bind_vars():
    src = """pattern Bad = Ok(x)
run()
"""
    with pytest.raises(ResolveError):
        _check(src, use_stdlib=True)
