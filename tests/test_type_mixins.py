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


def _resolve(src: str, *, use_stdlib: bool = False):
    prog = parse_program(lex("test.flv", src))
    return resolve_program_with_stdlib(prog, use_stdlib=use_stdlib)


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


def test_type_mixin_hook_invoke_on_method():
    src = """type User = { id: Int }

mixin M v1 into type User:
  fn getId(self: User) -> Int = self.id

mixin Hook v1 into type User:
  hook invoke fn getId(self: User) -> Int with(id="H", at="anchor:getId") = do:
    return proceed(self)

use mixin M v1
use mixin Hook v1

fn f(u: User) -> Int = User.getId(u)
run()
"""
    _check(src, use_stdlib=True)


def test_type_mixin_hook_head_tail_on_method():
    src = """type User = { id: Int }

mixin M v1 into type User:
  fn score(self: User) -> Int = self.id

mixin H v1 into type User:
  hook head fn score(self: User) -> Option[Int] with(cancelable=true) = match self.id == 0:
    true -> Some(100)
    false -> None
  hook tail fn score(self: User, ret: Int) -> Int with(returnDep="replace_return") = ret + 1

use mixin M v1
use mixin H v1

fn f(u: User) -> Int = User.score(u)
run()
"""
    _check(src, use_stdlib=True)


def test_type_mixin_hook_missing_target_method_is_error():
    src = """type User = { id: Int }

mixin H v1 into type User:
  hook invoke fn missing(self: User) -> Int = do:
    return proceed(self)

use mixin H v1
run()
"""
    with pytest.raises(ResolveError, match="hook target method not found"):
        _check(src, use_stdlib=True)


def test_type_mixin_around_wraps_method():
    src = """type User = { id: Int }

mixin M v1 into type User:
  fn getId(self: User) -> Int = self.id

mixin A v1 into type User:
  around fn getId(self: User) -> Int:
    return proceed(self)

use mixin M v1
use mixin A v1

fn f(u: User) -> Int = User.getId(u)
run()
"""
    _check(src, use_stdlib=True)


def test_type_mixin_hook_plan_uses_public_method_target_name():
    src = """type User = { id: Int }

mixin M v1 into type User:
  fn getId(self: User) -> Int = self.id

mixin H v1 into type User:
  hook invoke fn getId(self: User) -> Int with(id="ID") = do:
    return proceed(self)

use mixin M v1
use mixin H v1
run()
"""
    res = _resolve(src, use_stdlib=False)
    plan = [p for p in res.mixin_hook_plan if p["owner_kind"] == "type"]
    assert any(p["target"] == "User.getId" and p["hook_id"] == "ID" for p in plan)


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
