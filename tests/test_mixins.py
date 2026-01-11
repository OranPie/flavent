import pytest

from flavent.diagnostics import ParseError, ResolveError
from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib


def _resolve(src: str):
    prog = parse_program(lex("test.flv", src))
    return resolve_program_with_stdlib(prog, use_stdlib=False)


def test_resolve_mixin_conflict_accepts_kw_mixin():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  around fn foo(x: Int) -> Int:
    return proceed(x)

mixin B v1 into sector S:
  around fn foo(x: Int) -> Int:
    return proceed(x)

resolve mixin-conflict:
  prefer A v1 over B v1

use mixin A v1
use mixin B v1
run()
"""
    _resolve(src)


def test_mixin_around_signature_mismatch_is_error():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  around fn foo(x: Str) -> Int:
    return proceed(x)

use mixin A v1
run()
"""
    with pytest.raises(ResolveError):
        _resolve(src)


def test_mixin_proceed_rewrite_in_if_for_blocks():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  around fn foo(x: Int) -> Int:
    if true:
      return proceed(x)
    else:
      for y in (1, 2):
        proceed(y)
      return proceed(x)

use mixin A v1
run()
"""
    _resolve(src)


def test_mixin_unknown_mixin_is_error():
    src = """sector S:
  fn foo(x: Int) -> Int = x

use mixin Missing v1
run()
"""
    with pytest.raises(ResolveError):
        _resolve(src)


def test_mixin_ambiguous_add_conflict_requires_resolve_rule():
    src = """sector S:
  let x = 0

mixin A v1 into sector S:
  fn f() -> Int = 1

mixin B v1 into sector S:
  fn f() -> Int = 2

use mixin A v1
use mixin B v1
run()
"""
    with pytest.raises(ResolveError):
        _resolve(src)


def test_mixin_add_conflict_resolved_by_prefer():
    src = """sector S:
  let x = 0

mixin A v1 into sector S:
  fn f() -> Int = 1

mixin B v1 into sector S:
  fn f() -> Int = 2

resolve mixin-conflict:
  prefer A v1 over B v1

use mixin A v1
use mixin B v1
run()
"""
    _resolve(src)
