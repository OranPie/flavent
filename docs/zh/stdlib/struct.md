# `struct`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use struct
```

## 类型
```flavent
type Endian = Little | Big
```

## 函数
```flavent
fn packB(v: Int) -> Bytes = bytesFromByte(u32And(v, 255))
fn packH(v: Int) -> Bytes = do:
fn packI(v: Int) -> Bytes = do:
fn unpackB(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn unpackH(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn unpackI(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn calcsize(fmt: Str) -> Result[Int, Str] = _stCalcAcc(fmt, 0, strLen(fmt), 0)
fn pack(fmt: Str, values: List[Int]) -> Result[Bytes, Str] = do:
fn unpackFrom(fmt: Str, b: Bytes, offset: Int) -> Result[List[Int], Str] = do:
fn unpack(fmt: Str, b: Bytes) -> Result[List[Int], Str] = unpackFrom(fmt, b, 0)
```

