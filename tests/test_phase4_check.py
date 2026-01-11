import pytest

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.lower import lower_resolved
from flavent.typecheck import check_program
from flavent.diagnostics import EffectError


def _check(src: str) -> None:
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)
    check_program(hir, res)


def test_check_ok_pure_fn_and_sector_rpc():
    src = """sector db:
  fn ping() -> Int = 1

sector web:
  fn@web main() -> Unit = do:
    let x = rpc db.ping()
    call db.ping()
    stop()

run()
"""
    _check(src)


def test_check_reject_direct_cross_sector_call():
    src = """sector db:
  let dummy = 0

fn@db ping() -> Int = 1

sector web:
  fn@web main() -> Unit = do:
    let x = ping()
    stop()

run()
"""
    with pytest.raises(EffectError):
        _check(src)


def test_check_reject_top_level_effect():
    src = """sector s:
  fn ping() -> Int = 1

let x = rpc s.ping()
run()
"""
    with pytest.raises(EffectError):
        _check(src)
