# `flvtest`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use flvtest
```

## 函数
```flavent
fn fail(msg: Str) -> Result[Unit, Str] = Err(msg)
fn assertTrue(cond: Bool) -> Result[Unit, Str] = match cond:
fn assertEq[T](a: T, b: T) -> Result[Unit, Str] = match a == b:
```

