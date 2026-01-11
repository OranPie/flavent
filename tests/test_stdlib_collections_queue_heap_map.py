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


def test_stdlib_queue_pop_peek():
    src = """use collections.queue

fn f() -> Int = do:
  let q0 = queueEmpty()
  let q1 = queuePush(q0, 1)
  let q2 = queuePush(q1, 2)
  return match queuePop(q2):
    None -> 0
    Some(r) -> match r.value == 1:
      true -> match queuePeek(r.rest):
        None -> 0
        Some(x) -> x
      false -> 0

run()
"""
    _check(src)


def test_stdlib_heap_pop():
    src = """use collections.heap

fn f() -> Int = do:
  let h0 = heapEmpty()
  let h1 = heapInsert(3, h0)
  let h2 = heapInsert(1, h1)
  let h3 = heapInsert(2, h2)
  return match heapPop(h3):
    None -> 0
    Some(r) -> r.value

run()
"""
    _check(src)


def test_stdlib_map_put_get_remove():
    src = """use collections.map

fn f() -> Int = do:
  let m0 = mapEmpty()
  let m1 = mapPut(m0, "a", 1)
  let m2 = mapPut(m1, "b", 2)
  let m3 = mapPut(m2, "a", 3)
  return match mapGet(m3, "a"):
    None -> 0
    Some(v) -> match mapGet(mapRemove(m3, "a"), "a"):
      None -> v
      Some(_) -> 0

run()
"""
    _check(src)
