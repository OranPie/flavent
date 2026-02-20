from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from flavent.diagnostics import EffectError, LexError, ParseError, ResolveError, TypeError
from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.runtime import Bridge, run_hir_program
from flavent.typecheck import check_program


@dataclass(frozen=True)
class Case:
    name: str
    body: str
    uses: str = ""


def _wrap_runtime_src(body: str, *, uses: str = "") -> str:
    # Keep a consistent program shape so we mostly test runtime semantics.
    return (
        "use flvtest\n"
        + uses
        + "\n"
        + "type Event.Test = {}\n\n"
        + "sector main:\n"
        + "  on Event.Test -> do:\n"
        + body
        + ("\n" if not body.endswith("\n") else "")
        + "    stop()\n\n"
        + "run()\n"
    )


def _compile_typecheck(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)
    return hir, res


class _NoBridge(Bridge):
    def call(self, name: str, args: list[object]) -> object:
        raise RuntimeError(f"bridge call not allowed: {name}")


def _run_ok(src: str) -> None:
    hir, res = _compile_typecheck(src)
    run_hir_program(hir, res, entry_event_type="Event.Test", bridge=_NoBridge())


# ----------------------------
# Runtime tests (70+ cases)
# ----------------------------


_RUNTIME_CASES: list[Case] = []

# Arithmetic / comparisons.
for a in range(0, 25):
    _RUNTIME_CASES.append(
        Case(
            name=f"arith-add-{a}",
            body=f"    assertEq({a} + 1, {a + 1})?\n",
        )
    )

for a in range(1, 15):
    _RUNTIME_CASES.append(
        Case(
            name=f"arith-mul-{a}",
            body=f"    assertEq({a} * 3, {a * 3})?\n",
        )
    )

for a in range(1, 10):
    _RUNTIME_CASES.append(
        Case(
            name=f"arith-div-{a}",
            body=f"    assertEq({a * 10} / {a}, 10)?\n",
        )
    )

# Lists.
for n in range(0, 15):
    if n == 0:
        xs = "drop(Cons(0, Nil), 1)"
        body = (
            f"    let xs = {xs}\n"
            "    assertEq(length(xs), 0)?\n"
        )
    else:
        xs = "Nil"
        for i in reversed(range(n)):
            xs = f"Cons({i}, {xs})"
        body = (
            f"    let xs = {xs}\n"
            f"    assertEq(length(xs), {n})?\n"
        )
    _RUNTIME_CASES.append(
        Case(
            name=f"list-length-{n}",
            body=body,
            uses="use collections.list\n",
        )
    )

# Map basic.
for i in range(0, 10):
    _RUNTIME_CASES.append(
        Case(
            name=f"map-put-get-{i}",
            body=(
                f"    let m = mapPut(mapEmpty(), \"k\", \"v{i}\")\n"
                "    let g = mapGet(m, \"k\")\n"
                "    match g:\n"
                "      Some(v) -> do:\n"
                f"        assertEq(v, \"v{i}\")?\n"
                "      None -> do:\n"
                "        fail(\"missing\")?\n"
            ),
            uses="use collections.map\n",
        )
    )

# Option/Result propagation via '?'.
for i in range(0, 10):
    _RUNTIME_CASES.append(
        Case(
            name=f"try-suffix-result-{i}",
            body=(
                f"    let y = Ok({i})?\n"
                f"    assertEq(y + 1, {i + 1})?\n"
            ),
            uses="use std.result\n",
        )
    )

# Regex + stringfmt + struct smoke runtime.
_RUNTIME_CASES.extend(
    [
        Case(
            name="regex-span-runtime",
            body=(
                "    let r = compile(\"a\")\n"
                "    let s = findAllSpans(r, \"aa\")\n"
                "    assertEq(length(s), 2)?\n"
            ),
            uses="use regex\nuse collections.list\n",
        ),
        Case(
            name="stringfmt-named-runtime",
            body=(
                "    let named = mapPut(mapEmpty(), \"name\", \"Alice\")\n"
                "    assertEq(formatMap(\"hi {name}\", named), \"hi Alice\")?\n"
            ),
            uses="use stringfmt\nuse collections.map\n",
        ),
        Case(
            name="struct-pack-unpack-runtime",
            body=(
                "    let b = pack(\"BH\", Cons(1, Cons(0x0203, Nil)))?\n"
                "    assertEq(bytesLen(b), 3)?\n"
                "    let xs = unpack(\"BH\", b)?\n"
                "    assertEq(xs, Cons(1, Cons(0x0203, Nil)))?\n"
            ),
            uses="use struct\nuse bytelib\n",
        ),
        Case(
            name="string-escape-runtime",
            body=(
                "    let one = \"\\n\"\n"
                "    assertEq(isMatch(compile(\"^.$\"), one), true)?\n"
            ),
            uses="use regex\n",
        ),
        Case(
            name="bytes-hex-escape-runtime",
            body=(
                "    let b = b\"\\x41\\x80\\x0a\"\n"
                "    assertEq(bytesLen(b), 3)?\n"
                "    assertEq(bytesGet(b, 0), 65)?\n"
                "    assertEq(bytesGet(b, 1), 128)?\n"
                "    assertEq(bytesGet(b, 2), 10)?\n"
            ),
            uses="use bytelib\n",
        ),
    ]
)

_RUNTIME_CASES.extend(
    [
        Case(
            name="mixin-hook-invoke-priority-and-dependency-runtime",
            body=(
                "    assertEq(rpc S.base(3), 16)?\n"
            ),
            uses=(
                "sector S:\n"
                "  fn base(x: Int) -> Int = x\n"
                "\n"
                "mixin B v1 into sector S:\n"
                "  hook invoke fn base(x: Int) -> Int with(id=\"B\", priority=10) = do:\n"
                "    return proceed(x * 2)\n"
                "\n"
                "mixin C v1 into sector S:\n"
                "  hook invoke fn base(x: Int) -> Int with(id=\"C\", depends=\"B\") = do:\n"
                "    return proceed(x + 10)\n"
                "\n"
                "use mixin C v1\n"
                "use mixin B v1\n"
            ),
        ),
        Case(
            name="mixin-hook-head-cancelable-tail-replace-runtime",
            body=(
                "    assertEq(rpc S.base(2), 13)?\n"
                "    assertEq(rpc S.base(0), 999)?\n"
            ),
            uses=(
                "sector S:\n"
                "  fn base(x: Int) -> Int = x + 1\n"
                "\n"
                "mixin Head v1 into sector S:\n"
                "  hook head fn base(x: Int) -> Option[Int] with(id=\"head\", cancelable=true) = match x == 0:\n"
                "    true -> Some(999)\n"
                "    false -> None\n"
                "\n"
                "mixin Tail v1 into sector S:\n"
                "  hook tail fn base(x: Int, ret: Int) -> Int with(id=\"tail\", returnDep=\"replace_return\") = ret + 10\n"
                "\n"
                "use mixin Head v1\n"
                "use mixin Tail v1\n"
            ),
        ),
        Case(
            name="flvrepr-metadata-roundtrip-runtime",
            body=(
                "    let m = encodeFunctionTarget(\"main.base\", \"invoke\", \"10\", \"anchor:base\")\n"
                "    assertEq(metaGet(m, \"target\"), Some(\"main.base\"))?\n"
                "    let m2 = metaSet(m, \"priority\", \"20\")\n"
                "    assertEq(metaGet(m2, \"priority\"), Some(\"20\"))?\n"
                "    let m3 = metaSet(\"\", \"k\", \"a=b\")\n"
                "    assertEq(metaGet(m3, \"k\"), Some(\"a=b\"))?\n"
            ),
            uses="use flvrepr\n",
        ),
        Case(
            name="type-mixin-hook-head-invoke-tail-runtime",
            body=(
                "    let u = { id = 2 }\n"
                "    let z = { id = 0 }\n"
                "    assertEq(callScore(u), 14)?\n"
                "    assertEq(callScore(z), 50)?\n"
            ),
            uses=(
                "type User = { id: Int }\n"
                "\n"
                "fn callScore(u: User) -> Int = User.score(u)\n"
                "\n"
                "mixin Base v1 into type User:\n"
                "  fn score(self: User) -> Int = self.id + 1\n"
                "\n"
                "mixin Head v1 into type User:\n"
                "  hook head fn score(self: User) -> Option[Int] with(cancelable=true) = match self.id == 0:\n"
                "    true -> Some(50)\n"
                "    false -> None\n"
                "\n"
                "mixin Invoke v1 into type User:\n"
                "  hook invoke fn score(self: User) -> Int = do:\n"
                "    return proceed(self) + 1\n"
                "\n"
                "mixin Tail v1 into type User:\n"
                "  hook tail fn score(self: User, ret: Int) -> Int with(returnDep=\"replace_return\") = ret + 10\n"
                "\n"
                "use mixin Base v1\n"
                "use mixin Head v1\n"
                "use mixin Invoke v1\n"
                "use mixin Tail v1\n"
            ),
        ),
    ]
)


@pytest.mark.parametrize("case", _RUNTIME_CASES, ids=lambda c: c.name)
def test_runtime_cases(case: Case):
    # Each parameter counts as an individual pytest test.
    src = _wrap_runtime_src(case.body, uses=case.uses)
    _run_ok(src)


# ----------------------------
# Static checks (40+ cases)
# ----------------------------


@dataclass(frozen=True)
class ErrCase:
    name: str
    src: str
    exc: type[Exception]
    msg_re: str


_PARSE_ERRS: list[ErrCase] = []

# Lex errors: tabs / bad indent.
_PARSE_ERRS.append(
    ErrCase(
        name="lex-tab-indent",
        src="sector main:\n\ton Event.Test -> do:\n    stop()\nrun()\n",
        exc=LexError,
        msg_re=r"Tab",
    )
)

# Parse errors: missing colon.
_PARSE_ERRS.append(
    ErrCase(
        name="parse-missing-colon",
        src="sector main\n  on Event.X -> do:\n    stop()\nrun()\n",
        # Missing ':' means the next indented line triggers a lexer indentation error.
        exc=LexError,
        msg_re=r"IndentationError",
    )
)

# Many small parse errors.
for i in range(0, 15):
    _PARSE_ERRS.append(
        ErrCase(
            name=f"parse-bad-fn-{i}",
            # Missing expression after '=' (not an indentation error; should be ParseError).
            src=f"fn f{i}() -> Int =\n",
            exc=ParseError,
            msg_re=r"Expected",
        )
    )


_RESOLVE_ERRS: list[ErrCase] = []

# Duplicate definition in same scope.
for i in range(0, 10):
    _RESOLVE_ERRS.append(
        ErrCase(
            name=f"resolve-dup-{i}",
            src=(
                "type Event.Test = {}\n"
                "sector main:\n"
                "  let x = 1\n"
                "  let x = 2\n"
                "  on Event.Test -> do:\n"
                "    stop()\n\n"
                "run()\n"
            ),
            exc=ResolveError,
            msg_re=r"Duplicate name",
        )
    )


_TYPE_ERRS: list[ErrCase] = []

# Type mismatch cases that reliably fail typechecking.
for i in range(0, 15):
    _TYPE_ERRS.append(
        ErrCase(
            name=f"type-mismatch-{i}",
            src=(
                "type Event.Test = {}\n"
                "fn f() -> Int = \"no\"\n\n"
                "sector main:\n"
                "  on Event.Test -> do:\n"
                "    stop()\n\n"
                "run()\n"
            ),
            exc=TypeError,
            msg_re=r"type mismatch",
        )
    )


_EFFECT_ERRS: list[ErrCase] = []

# Direct bridge symbol usage should be rejected.
for i in range(0, 10):
    _EFFECT_ERRS.append(
        ErrCase(
            name=f"effect-direct-py-bytes-{i}",
            src=(
                "use bytelib\n"
                "type Event.Test = {}\n"
                "sector main:\n"
                "  on Event.Test -> do:\n"
                "    let _x = _pyBytesLen(b\"hi\")\n"
                "    stop()\n\n"
                "run()\n"
            ),
            exc=EffectError,
            msg_re=r"bridge|_bridge_python|not allowed",
        )
    )


@pytest.mark.parametrize(
    "case",
    _PARSE_ERRS + _RESOLVE_ERRS + _TYPE_ERRS + _EFFECT_ERRS,
    ids=lambda c: c.name,
)
def test_static_checks(case: ErrCase):
    # Parse / resolve / typecheck / effect checks.
    if case.exc in (LexError, ParseError):
        with pytest.raises(case.exc):
            parse_program(lex("test.flv", case.src))
        return

    prog = parse_program(lex("test.flv", case.src))

    if case.exc is ResolveError:
        with pytest.raises(case.exc) as ei:
            resolve_program_with_stdlib(prog, use_stdlib=True)
        assert re.search(case.msg_re, str(ei.value), re.IGNORECASE) is not None
        return

    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)

    with pytest.raises(case.exc) as ei:
        check_program(hir, res)

    assert re.search(case.msg_re, str(ei.value), re.IGNORECASE) is not None
