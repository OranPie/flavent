# `asciilib`

## 概述
（本页可自由编辑，生成器只会更新标记的 API 区块。）

用于 ASCII 与 bytes 的互转，以及一些常用字节序列（如 CRLF）。

## 导入
```flavent
use asciilib
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn crlfBytes() -> Bytes = bytesFromList(Cons(13, Cons(10, Nil)))
fn asciiFromBytes(b: Bytes) -> Str = _asciiFromBytesAcc(b, 0, bytesLen(b), "")
fn asciiToBytes(s: Str) -> Bytes = bytesFromList(_asciiCodesAcc(s, 0, strLen(s), Nil))
```
<!-- AUTO-GEN:END FUNCTIONS -->
