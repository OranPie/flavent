from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.typecheck import check_program


def _check(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)


def test_stdlib_stack_push_pop_peek():
    src = """use collections.stack

fn f() -> Int = do:
  let s0 = stackEmpty()
  let s1 = stackPush(s0, 1)
  let s2 = stackPush(s1, 2)
  return match stackPop(s2):
    None -> 0
    Some(p) -> match p.value == 2:
      true -> match stackPeek(p.rest):
        None -> 0
        Some(x) -> x
      false -> 0

run()
"""
    _check(src)


def test_stdlib_stack_defaults_and_wrapper():
    src = """use stack
use collections.list

fn f() -> Int = do:
  let s0 = stackFromList(Cons(1, Cons(2, Nil)))
  let s1 = stackPushAll(s0, Cons(3, Cons(4, Nil)))
  let p0 = stackPopOr(stackEmpty(), 9)
  if p0.value == 9 and stackPeekOr(stackEmpty(), 8) == 8:
    return stackSize(s1)
  else:
    return 0

run()
"""
    _check(src)
