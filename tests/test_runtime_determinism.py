from __future__ import annotations

import pytest

from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.runtime import Bridge, run_hir_program
from flavent.typecheck import check_program


class _CaptureConsoleBridge(Bridge):
    def __init__(self) -> None:
        self.lines: list[str] = []

    def call(self, name: str, args: list[object]) -> object:
        if name in {"consolePrint", "consolePrintln", "consolePrintErr", "consolePrintlnErr"}:
            s = str(args[0]) if args else ""
            self.lines.append(f"{name}:{s}")
            return None
        if name == "consoleFlush":
            return None
        if name == "consoleReadLine":
            return ""
        raise RuntimeError(f"unexpected bridge call: {name}")


def _compile(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)
    return hir, res


@pytest.mark.integration
def test_runtime_handler_execution_order_is_deterministic():
    src = """use consoleIO

type Event.Start = {}

sector main:
  on Event.Start -> do:
    call consoleIO.println("main-1")

  on Event.Start -> do:
    call consoleIO.println("main-2")

sector aux:
  on Event.Start -> do:
    call consoleIO.println("aux-1")

run()
"""

    hir, res = _compile(src)
    expected: list[str] | None = None
    for _ in range(30):
        bridge = _CaptureConsoleBridge()
        run_hir_program(hir, res, entry_event_type="Event.Start", bridge=bridge)
        if expected is None:
            expected = bridge.lines
        else:
            assert bridge.lines == expected

    assert expected == [
        "consolePrintln:main-1",
        "consolePrintln:main-2",
        "consolePrintln:aux-1",
    ]


@pytest.mark.integration
def test_runtime_await_receives_event_value_from_wait_queue():
    src = """use flvtest

type Event.Start = {}

sector main:
  on Event.Start as e -> do:
    let got = await Event.Start
    assertEq(got, e)?
    stop()

  on Event.Start as e -> do:
    emit e

run()
"""

    hir, res = _compile(src)
    run_hir_program(hir, res, entry_event_type="Event.Start", bridge=_CaptureConsoleBridge())


@pytest.mark.integration
def test_runtime_await_waiters_resume_fifo():
    src = """use consoleIO

type Event.Start = {}

sector main:
  on Event.Start as e -> do:
    call consoleIO.println("w1-wait")
    let _x = await Event.Start
    call consoleIO.println("w1-resume")

  on Event.Start as e -> do:
    call consoleIO.println("w2-wait")
    let _x = await Event.Start
    call consoleIO.println("w2-resume")

  on Event.Start as e -> do:
    call consoleIO.println("emit-1")
    emit e
    call consoleIO.println("emit-2")
    emit e

run()
"""

    hir, res = _compile(src)
    bridge = _CaptureConsoleBridge()
    run_hir_program(hir, res, entry_event_type="Event.Start", bridge=bridge)
    assert bridge.lines == [
        "consolePrintln:w1-wait",
        "consolePrintln:w2-wait",
        "consolePrintln:emit-1",
        "consolePrintln:w1-resume",
        "consolePrintln:emit-2",
        "consolePrintln:w2-resume",
    ]


@pytest.mark.integration
def test_runtime_mixed_event_types_dispatch_in_type_id_order():
    src = """use consoleIO

type Event.Start = {}
type Event.A = A | AX
type Event.B = B | BX

sector main:
  let handled = 0

  on Event.Start -> do:
    call consoleIO.println("seed")
    emit B()
    emit A()

  on Event.A as a -> do:
    call consoleIO.println("A")
    handled = handled + 1
    if handled >= 2:
      stop()

  on Event.B as b -> do:
    call consoleIO.println("B")
    handled = handled + 1
    if handled >= 2:
      stop()

run()
"""

    hir, res = _compile(src)
    bridge = _CaptureConsoleBridge()
    run_hir_program(hir, res, entry_event_type="Event.Start", bridge=bridge)
    assert bridge.lines == [
        "consolePrintln:seed",
        "consolePrintln:A",
        "consolePrintln:B",
    ]


@pytest.mark.integration
def test_runtime_repeated_ping_pong_emit_await_chain():
    src = """use flvtest

type Event.Ping = Ping | PingAlt
type Event.Pong = Pong | PongAlt

sector main:
  let cycles = 0

  on Event.Ping as e -> do:
    let _p = await Event.Pong
    cycles = cycles + 1
    if cycles < 20:
      emit Ping()
    else:
      assertEq(cycles, 20)?
      stop()

  on Event.Ping as e -> do:
    emit Pong()

run()
"""

    hir, res = _compile(src)
    for _ in range(10):
        run_hir_program(hir, res, entry_event_type="Event.Ping", bridge=_CaptureConsoleBridge())
