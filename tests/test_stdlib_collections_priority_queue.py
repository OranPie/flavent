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


def test_stdlib_priority_queue_ordering():
    src = """use collections.priority_queue

fn f() -> Int = do:
  let q0 = priorityQueueEmpty()
  let q1 = priorityQueuePush(q0, 5, 50)
  let q2 = priorityQueuePush(q1, 1, 10)
  let q3 = priorityQueuePush(q2, 3, 30)
  return match priorityQueuePop(q3):
    None -> 0
    Some(p1) -> match priorityQueuePop(p1.rest):
      None -> 0
      Some(p2) -> match p1.value == 10 and p2.value == 30:
        true -> priorityQueuePeekOr(p2.rest, 0)
        false -> 0

run()
"""
    _check(src)


def test_stdlib_priority_queue_wrapper_and_defaults():
    src = """use priority_queue
use collections.list

fn f() -> Int = do:
  let xs = Cons({ priority = 2, value = 20 }, Cons({ priority = 1, value = 10 }, Nil))
  let q0 = priorityQueueFromList(xs)
  let p0 = priorityQueuePopOr(priorityQueueEmpty(), 9, 99)
  if p0.value == 99 and priorityQueuePeekPriority(q0) == Some(1):
    return priorityQueueSize(q0)
  else:
    return 0

run()
"""
    _check(src)
