from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program


def test_resolve_minimal_program():
    src = """type Event.Start = {}\n\nfn solve(input: Str) -> Str = input\n\nsector main:\n  on Event.Start -> do:\n    stop()\n\nrun()\n"""
    prog = parse_program(lex("test.flv", src))
    res = resolve_program(prog)
    assert len(res.symbols) > 0

    # ensure main sector exists
    main_ids = [s.id for s in res.symbols if s.kind.name == "SECTOR" and s.name == "main"]
    assert main_ids


def test_resolve_name_not_found():
    src = """fn f(x: Int) = y\n"""
    prog = parse_program(lex("test.flv", src))
    try:
        resolve_program(prog)
        assert False, "expected resolution error"
    except Exception as e:
        assert "NameNotFound" in str(e)
