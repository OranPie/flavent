# `std.result`

## Overview
`Result[T, E]` for fallible operations.

Import:
```flavent
use std.result
```

## Type
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
