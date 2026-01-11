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


def test_stdlib_misc_modules_typecheck():
    src = """use regex
use stringfmt
use enum
use consoleIO
use base64
use hashlib
use collections.map
use bytelib
use u32
use fslib
use statistics
use uuid
use glob
use tempfile

type Event.X = {}

sector s:
  on Event.X -> do:
    let r = compile("a+")
    let m = isMatch(r, "aaa")
    let _i = findFirst(r, "bbb")

    let r2 = compile("[a-z]+")
    let _m2 = isMatch(r2, "abc")

    let r3 = compile("[^0-9]+")
    let _m3 = isMatch(r3, "abc")

    let r4 = compile("\\\\d+")
    let _m4 = isMatch(r4, "123")

    let r5 = compile("[\\\\w_]+")
    let _m5 = isMatch(r5, "a_b")

    let r6 = compile("\\s+")
    let _m6 = isMatch(r6, " ")

    let r7 = compile("a|bc")
    let _m7 = isMatch(r7, "bc")

    let r8 = compile("(ab|cd)e")
    let _m8 = isMatch(r8, "cde")

    let s = surround("x", "[", "]")
    let t = concat3("a", "b", "c")
    call consoleIO.println(concat(s, t))

    let named = mapPut(mapEmpty(), "name", "Alice")
    let _mix = formatWith("hi {name} {} {0}", Cons("X", Nil), named)

    let info0 = enumInfoEmpty()
    let info1 = enumInfoAdd(info0, enumCase("A", 1))
    let _c = enumFindByTag(info1, 1)

    let info2 = enumInfoAddAuto(info1, "B")
    let _d = enumFindByName(info2, "A")
    let _next = enumNextTag(info2)

    let _b64 = encode(b"hi")
    let _raw = decode(_b64)
    let _h1 = md5Hex(b"hi")
    let _h2 = sha256Hex(b"hi")

    let _n = bytesLen(b"hi")
    let _b0 = bytesGet(b"hi", 0)
    let _sl = bytesSlice(b"hi", 0, 1)
    let _cat = bytesConcat(b"h", b"i")
    let _lst = bytesToList(b"hi")
    let _b2 = bytesFromList(Cons(104, Cons(105, Nil)))

    let a = wrap(0 - 1)
    let b = wrap(1)
    let _c0 = u32And(a, b)
    let _c1 = u32Or(a, b)
    let _c2 = u32Xor(a, b)
    let _c3 = u32Not(b)
    let _c4 = u32Shl(b, 3)
    let _c5 = u32Shr(a, 1)

    let _exists = rpc fslib.exists("/tmp")
    call fslib.mkdirs("/tmp/flavent_test")

    let xs = Cons(1.0, Cons(2.0, Cons(3.0, Nil)))
    let _m = mean(xs)
    let _md = median(xs)
    let _sd = stdev(xs)

    let u = rpc uuid.uuid4()
    let us = toString(u)
    let _pu = parse(us)

    let _paths = rpc glob.glob("/tmp/*")
    let _tf = rpc tempfile.mkstemp("flv_", ".tmp")
    let _td = rpc tempfile.mkdtemp("flv_")

    stop()

run()
"""
    _check(src)


def test_stdlib_math_transcendental_typecheck():
    src = """use math

fn f() -> Float = do:
  let a = sqrt(2.0)
  let b = ln(10.0)
  let c = log10(100.0)
  let d = exp(1.0)
  let e = sin(pi())
  let g = cos(0.0)
  let h = tan(0.0)
  let i = atan(1.0)
  let j = atan2(1.0, 1.0)
  return a + b + c + d + e + g + h + i + j

run()
"""
    _check(src)


def test_stdlib_math_expanded():
    src = """use math

fn f() -> Int = do:
  let a = gcdInt(48, 18)
  let b = lcmInt(6, 8)
  let c = signInt(0 - 2)
  let d = min3Int(3, 2, 1)
  let e = max3Int(1, 2, 3)
  let _even = isEven(4)
  let _odd = isOdd(5)
  return a + b + c + d + e

run()
"""
    _check(src)
