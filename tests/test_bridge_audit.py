import json

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.lower import lower_resolved
from flavent.typecheck import check_program
from flavent.bridge_audit import audit_bridge_usage


def test_bridge_audit_detects_bridge_calls():
    src = """use consoleIO
use time
use base64

// minimal sector to allow rpc/call
sector s:
  on Event.X -> do:
    call consoleIO.println("hi")
    let _t = rpc time.nowMillis()
    let _b = encode(b"hi")
    stop()

type Event.X = {}

run()
"""

    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)

    report = audit_bridge_usage(hir, res)
    # Must include at least one bridge sector call.
    counts = report["counts"]
    assert any(k.startswith("call:") or k.startswith("rpc:") for k in counts), json.dumps(report, indent=2)


def test_bridge_policy_rejects_direct_bridge_symbol_use_from_user_code():
    import pytest

    from flavent.diagnostics import EffectError

    src = """use bytelib

fn f() -> Int = _pyBytesLen(b"hi")
"""

    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    with pytest.raises(EffectError):
        check_program(hir, res)
