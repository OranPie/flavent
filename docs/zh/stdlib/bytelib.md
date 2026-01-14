# `bytelib`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use bytelib
```

## 类型
```flavent
type ByteArray = List[Int]
```

## 函数
```flavent
fn bytesLen(b: Bytes) -> Int = _pyBytesLen(b)
fn bytesGet(b: Bytes, i: Int) -> Int = _pyBytesGet(b, i)
fn bytesSlice(b: Bytes, start: Int, end: Int) -> Bytes = _pyBytesSlice(b, start, end)
fn bytesConcat(a: Bytes, b: Bytes) -> Bytes = _pyBytesConcat(a, b)
fn bytesFromByte(x: Int) -> Bytes = _pyBytesFromByte(x)
fn bytesFind(h: Bytes, needle: Bytes, start: Int) -> Int = do:
fn bytesStartsWith(h: Bytes, prefix: Bytes) -> Bool = do:
fn bytesEndsWith(h: Bytes, suffix: Bytes) -> Bool = do:
fn bytesToList(b: Bytes) -> List[Int] = _btToListAcc(b, 0, bytesLen(b))
fn bytesFromList(xs: List[Int]) -> Bytes = _btFromList(xs)
fn bytesConcatAll(xs: List[Bytes]) -> Bytes = match xs:
fn byteArrayEmpty() -> ByteArray = Nil
fn byteArrayPush(a: ByteArray, x: Int) -> ByteArray = append(a, Cons(x, Nil))
fn byteArrayToBytes(a: ByteArray) -> Bytes = bytesFromList(a)
fn bytesToByteArray(b: Bytes) -> ByteArray = bytesToList(b)
```

