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


def test_mixin_hook_invoke_dependency_resolves_call_stack():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin B v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="B", priority=10) = do:
    return proceed(x * 2)

mixin C v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="C", depends="B") = do:
    return proceed(x + 10)

use mixin C v1
use mixin B v1
run()
"""
    _resolve(src)


def test_mixin_hook_unknown_dependency_is_error():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", depends="Missing") = do:
    return proceed(x)

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="Unknown hook dependency"):
        _resolve(src)


def test_mixin_hook_locator_anchor_mismatch_is_error():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", at="anchor:bar") = do:
    return proceed(x)

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="locator mismatch"):
        _resolve(src)


def test_mixin_hook_rejects_unknown_option_key():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(unknown="x") = do:
    return proceed(x)

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="Unknown hook option"):
        _resolve(src)


def test_mixin_hook_head_cancelable_requires_option_return():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook head fn foo(x: Int) -> Int with(cancelable=true) = x

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="cancelable=true requires return type Option"):
        _resolve(src)


def test_mixin_hook_head_cancelable_option_type_must_match_target_return():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook head fn foo(x: Int) -> Option[Str] with(cancelable=true) = None

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="must match target return type"):
        _resolve(src)


def test_mixin_hook_tail_returndep_requires_matching_prev_return_param_type():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook tail fn foo(x: Int, ret: Str) -> Int with(returnDep="use_return") = x

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="extra return parameter type matching target return type"):
        _resolve(src)


def test_mixin_hook_tail_returndep_rejects_invalid_value():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook tail fn foo(x: Int) -> Int with(returnDep="later") = x

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="returnDep must be one of"):
        _resolve(src)


def test_mixin_hook_plan_records_resolved_depth_order():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin B v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="B", priority=10) = do:
    return proceed(x * 2)

mixin C v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="C", depends="B") = do:
    return proceed(x + 10)

use mixin C v1
use mixin B v1
run()
"""
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo"]
    assert [p["hook_id"] for p in plan] == ["B", "C"]
    assert [p["depth"] for p in plan] == [0, 1]
    assert all(p["owner_kind"] == "sector" for p in plan)


def test_mixin_hook_duplicate_id_conflict_prefer_keeps_preferred():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="X", conflict="prefer", priority=1) = do:
    return proceed(x + 1)

mixin B v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="X", conflict="prefer", priority=10) = do:
    return proceed(x + 2)

use mixin A v1
use mixin B v1
run()
"""
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo" and p["hook_id"] == "X"]
    assert len(plan) == 1
    assert plan[0]["mixin_key"] == "B@v1"
    assert plan[0]["conflict_policy"] == "prefer"


def test_mixin_hook_duplicate_id_conflict_drop_removes_hooks():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="X", conflict="drop") = do:
    return proceed(x + 1)

mixin B v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="X", conflict="drop") = do:
    return proceed(x + 2)

use mixin A v1
use mixin B v1
run()
"""
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo"]
    assert len(plan) == 2
    assert all(p["status"] == "dropped" for p in plan)
    assert all(p["drop_reason"] == "duplicate_drop" for p in plan)


def test_mixin_hook_conflict_option_rejects_invalid_value():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(conflict="merge") = do:
    return proceed(x)

use mixin A v1
run()
"""
    with pytest.raises(ResolveError, match="hook conflict must be one of"):
        _resolve(src)


def test_mixin_hook_non_strict_unknown_dependency_is_dropped():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", depends="Missing", strict=false) = do:
    return proceed(x)

use mixin A v1
run()
"""
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo" and p["hook_id"] == "A"]
    assert len(plan) == 1
    assert plan[0]["status"] == "dropped"
    assert plan[0]["drop_reason"].startswith("unknown_dependency:")


def test_mixin_hook_non_strict_locator_mismatch_is_dropped():
    src = """sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", at="anchor:nope", strict=false) = do:
    return proceed(x)

use mixin A v1
run()
"""
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo" and p["hook_id"] == "A"]
    assert len(plan) == 1
    assert plan[0]["status"] == "dropped"
    assert plan[0]["drop_reason"] == "locator_mismatch"


@pytest.mark.parametrize(
    ("strict_opt", "expect_error"),
    [
        ("", True),
        (", strict=true", True),
        (", strict=false", False),
    ],
)
def test_mixin_hook_dependency_strict_mode_matrix(strict_opt: str, expect_error: bool):
    src = f"""sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", depends="Missing"{strict_opt}) = do:
    return proceed(x)

use mixin A v1
run()
"""
    if expect_error:
        with pytest.raises(ResolveError, match="Unknown hook dependency"):
            _resolve(src)
        return
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo" and p["hook_id"] == "A"]
    assert len(plan) == 1
    assert plan[0]["status"] == "dropped"
    assert plan[0]["drop_reason"].startswith("unknown_dependency:")


@pytest.mark.parametrize(
    ("strict_opt", "expect_error"),
    [
        ("", True),
        (", strict=true", True),
        (", strict=false", False),
    ],
)
def test_mixin_hook_locator_strict_mode_matrix(strict_opt: str, expect_error: bool):
    src = f"""sector S:
  fn foo(x: Int) -> Int = x

mixin A v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="A", at="anchor:nope"{strict_opt}) = do:
    return proceed(x)

use mixin A v1
run()
"""
    if expect_error:
        with pytest.raises(ResolveError, match="locator mismatch"):
            _resolve(src)
        return
    res = _resolve(src)
    plan = [p for p in res.mixin_hook_plan if p["target"] == "S.foo" and p["hook_id"] == "A"]
    assert len(plan) == 1
    assert plan[0]["status"] == "dropped"
    assert plan[0]["drop_reason"] == "locator_mismatch"
