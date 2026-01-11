from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.lower import lower_resolved
from flavent.symbols import SymbolKind


def test_handler_symbol_is_from_resolution():
    src = """type Event.X = {}

on Event.X -> do:
  stop()

run()
"""
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)

    # main sector is synthesized; it must contain the top-level handler.
    sec = next(s for s in hir.sectors if True)
    h = sec.handlers[0]

    on = next(it for it in res.program.items if it.__class__.__name__ == "OnHandler")
    assert id(on) in res.handler_to_symbol
    assert h.sym == res.handler_to_symbol[id(on)]

    sym = next(s for s in res.symbols if s.id == h.sym)
    assert sym.kind == SymbolKind.HANDLER
