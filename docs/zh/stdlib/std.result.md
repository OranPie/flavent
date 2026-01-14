# `std.result`

## 概述
`Result[T, E]` 用于表达“可能失败”的操作。

导入：
```flavent
use std.result
```

## 类型
- `Result[T, E] = Ok(T) | Err(E)`

## API
- `isOk(r) -> Bool`
- `isErr(r) -> Bool`
- `unwrapOr(r, default) -> T`
- `unwrapOrErr(r, default) -> T`
- `toOption(r) -> Option[T]`
- `toOptionErr(r) -> Option[E]`
- `errOr(r, default) -> E`
- `unwrapOrEmptyStr(r: Result[Str, E]) -> Str`
- `isOkAndBool(r: Result[Bool, E]) -> Bool`
