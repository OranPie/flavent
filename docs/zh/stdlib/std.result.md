# `std.result`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use std.result
```

## 函数
```flavent
fn unwrapOrEmptyStr[E](r: Result[Str, E]) -> Str = unwrapOr(r, "")
fn isOkAndBool[E](r: Result[Bool, E]) -> Bool = match r:
```

