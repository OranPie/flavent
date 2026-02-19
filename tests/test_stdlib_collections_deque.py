from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.lower import lower_resolved
from flavent.typecheck import check_program


def _check(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)


def test_stdlib_deque_push_pop_typecheck():
    src = """use collections.deque

fn f() -> Int = do:
  let d0 = dequeEmpty()
  let d1 = dequePushFront(d0, 1)
  let d2 = dequePushBack(d1, 2)
  return match dequePopFront(d2):
    None -> 0
    Some(p) -> match dequePopBack(p.rest):
      None -> 0
      Some(q) -> p.value + q.value

run()
"""
    _check(src)


def test_stdlib_deque_wrapper_typecheck():
    src = """use deque

fn f() -> Int = do:
  let d = dequeFromList(Cons(1, Cons(2, Nil)))
  return dequePeekFrontOr(d, 0) + dequePeekBackOr(d, 0)

run()
"""
    _check(src)
