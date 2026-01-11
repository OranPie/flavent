from flavent.lexer import lex
from flavent.parser import parse_program


def test_parse_minimal_program():
    src = """type Event.Start = {}\n\nfn solve(input: Str) -> Str = input\n\nsector main:\n  on Event.Start -> do:\n    stop()\n\nrun()\n"""
    toks = lex("test.flv", src)
    prog = parse_program(toks)
    assert prog.run is not None
    assert len(prog.items) >= 2
